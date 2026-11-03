"""Consent-aware delivery, contact verification and durable notification work."""
from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from html import escape
import logging
import re
import secrets
import uuid
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import and_, delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError

from neos_agent.api.errors import ApiError
from neos_agent.db.models import AuthSession, User
from neos_agent.db.models.engagement import (
    EngagementEvent, EngagementInboxItem, EngagementPreference, EngagementPushDevice,
    NotificationChallenge, NotificationConsumption, NotificationContact, NotificationDelivery,
    NotificationRateLimit, NotificationWebhookReceipt,
)
from neos_agent.services.engagement_providers import (
    ProviderTransport, SendResult, configured_channels, setting, validate_push_destination,
)

logger = logging.getLogger(__name__)
LEASE_SECONDS = 90
MAX_ATTEMPTS = 5
MAX_EVENT_AGE = timedelta(days=8)
PENDING_STATES = ("pending", "retry_wait", "blocked_configuration")


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def naive(value):
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value and value.tzinfo else value


def iso(value):
    return naive(value).isoformat() + "Z" if value else None


def _secret(settings):
    value = setting(settings, "ENGAGEMENT_SIGNING_SECRET")
    if len(value) < 32:
        raise ApiError(503, "Notification signing configuration is pending")
    return value.encode()


def destination_hash(channel, value):
    return hashlib.sha256(f"{channel}:{value}".encode()).hexdigest()


def normalize_destination(channel, value):
    if not isinstance(value, str):
        raise ApiError(400, "Enter a valid email address or phone number")
    value = value.strip()
    if channel == "sms":
        if not re.fullmatch(r"\+[1-9][0-9]{7,14}", value):
            raise ApiError(400, "Use an international phone number beginning with +")
        return value
    if channel != "email" or len(value) > 254 or value.count("@") != 1 or any(c.isspace() for c in value):
        raise ApiError(400, "Enter a valid email address")
    local, domain = value.rsplit("@", 1)
    try:
        domain = domain.encode("idna").decode("ascii").lower()
    except UnicodeError as error:
        raise ApiError(400, "Enter a valid email address") from error
    if (not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}", local)
            or local.startswith(".") or local.endswith(".") or ".." in local
            or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,63}", domain)
            or ".." in domain):
        raise ApiError(400, "Enter a valid email address")
    return f"{local.lower()}@{domain}"


def contact_dto(contact):
    if contact.channel == "email":
        local, domain = contact.destination.rsplit("@", 1)
        masked = local[:1] + "***@" + domain
    else:
        masked = "+" + "*" * max(4, len(contact.destination) - 5) + contact.destination[-4:]
    return {"id": str(contact.id), "channel": contact.channel, "masked_destination": masked,
            "verified": bool(contact.verified_at and not contact.revoked_at),
            "suppressed": bool(contact.suppressed_at)}


async def current_contact(session, user_id, channel):
    return (await session.execute(select(NotificationContact).where(
        NotificationContact.user_id == user_id, NotificationContact.channel == channel,
        NotificationContact.revoked_at.is_(None),
    ).order_by(NotificationContact.generation.desc()).limit(1))).scalar_one_or_none()


async def active_devices(session, user_id, now=None):
    now = now or utcnow()
    return list((await session.execute(select(EngagementPushDevice).join(
        AuthSession, EngagementPushDevice.auth_session_id == AuthSession.id,
    ).where(EngagementPushDevice.user_id == user_id, EngagementPushDevice.enabled.is_(True),
            AuthSession.user_id == user_id, AuthSession.expires_at > now.replace(tzinfo=timezone.utc))
        .order_by(EngagementPushDevice.id))).scalars())


async def get_capabilities(session, user_id, settings):
    configured = configured_channels(settings)
    contacts = list((await session.execute(select(NotificationContact).where(
        NotificationContact.user_id == user_id, NotificationContact.revoked_at.is_(None),
    ))).scalars())
    channels = {"in_app": {"state": "ready", "reason": "Updates are available in the application."}}
    for channel, (ready, state) in configured.items():
        reason = "Provider setup is pending." if state == "pending_setup" else "External delivery is not activated."
        if ready:
            contact = next((row for row in contacts if row.channel == channel), None)
            if channel == "push":
                state = "ready" if await active_devices(session, user_id) else "needs_verification"
                reason = "Browser push is ready." if state == "ready" else "Enable notifications on this device."
            elif contact and contact.suppressed_at:
                state, reason = "suppressed", "Delivery to this destination is suppressed."
                if contact.suppression_reason == "unsubscribe":
                    reason = "You unsubscribed. Verify this destination again to resubscribe."
            elif contact and contact.verified_at:
                state, reason = "ready", "Your verified destination is ready."
            else:
                state, reason = "needs_verification", "Add and verify your own destination."
        channels[channel] = {"state": state, "reason": reason}
        if channel in {"email", "sms"}:
            channels[channel]["can_verify"] = bool(ready and (
                state != "suppressed" or (contact and contact.suppression_reason == "unsubscribe")))
        if channel == "push" and ready:
            channels[channel]["public_key"] = setting(settings, "VAPID_PUBLIC_KEY")
    return {"external_delivery_enabled": bool(setting(settings, "ENGAGEMENT_EXTERNAL_ENABLED", False)),
            "channels": channels, "contacts": [contact_dto(row) for row in contacts]}


async def _quota(session, bucket, limit, now=None):
    now = now or utcnow()
    window = now.replace(minute=0, second=0, microsecond=0)
    key = f"{window.isoformat()}:{bucket}"
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise ApiError(503, "Notification quotas require a supported database")
    statement = insert(NotificationRateLimit).values(
        id=uuid.uuid4(), bucket_key=key, window_start=window, count=1,
    ).on_conflict_do_update(
        index_elements=["bucket_key"], set_={"count": NotificationRateLimit.count + 1},
        where=NotificationRateLimit.count < limit,
    ).returning(NotificationRateLimit.count)
    if (await session.execute(statement)).scalar_one_or_none() is None:
        raise ApiError(429, "Too many verification attempts. Please try again later.")


async def _owner_lock(session, user_id):
    user = (await session.execute(select(User).where(User.id == user_id).with_for_update())).scalar_one_or_none()
    if not user or user.disabled_at:
        raise ApiError(401, "Authentication required")
    return user


async def _disable_channel(session, user_id, channel, now=None):
    now = now or utcnow()
    await session.execute(update(EngagementPreference).where(EngagementPreference.user_id == user_id)
                          .values(**{f"{channel}_enabled": False}))
    await session.execute(update(NotificationDelivery).where(
        NotificationDelivery.user_id == user_id, NotificationDelivery.channel == channel,
        NotificationDelivery.state.in_(PENDING_STATES + ("claimed",)),
        NotificationDelivery.attempt_started_at.is_(None),
    ).values(state="suppressed", error_code="channel_disabled", claim_token=None, lease_expires_at=None))


async def request_contact(factory, user_id, channel, destination, settings, transport):
    destination = normalize_destination(channel, destination)
    if not configured_channels(settings)[channel][0]:
        raise ApiError(503, "This notification channel is awaiting provider setup or activation")
    signing_secret = _secret(settings)
    now = utcnow()
    fingerprint = destination_hash(channel, destination)
    code = f"{secrets.randbelow(1000000):06d}"
    contact_id, challenge_id = uuid.uuid4(), uuid.uuid4()
    async with factory() as session:
        await _owner_lock(session, user_id)
        await _quota(session, f"request:user:{user_id}:{channel}", 5, now)
        await _quota(session, f"request:destination:{fingerprint}", 3, now)
        await _quota(session, f"request:global:{channel}", 100, now)
        suppressed = (await session.execute(select(NotificationContact.id).where(
            NotificationContact.channel == channel, NotificationContact.destination_hash == fingerprint,
            NotificationContact.suppressed_at.is_not(None),
            or_(NotificationContact.user_id != user_id, NotificationContact.suppression_reason != "unsubscribe"),
        ).limit(1))).scalar_one_or_none()
        if suppressed:
            await session.commit()
            raise ApiError(409, "Delivery to this destination is suppressed")
        generation = (await session.execute(select(func.max(NotificationContact.generation)).where(
            NotificationContact.user_id == user_id, NotificationContact.channel == channel,
        ))).scalar_one_or_none() or 0
        await session.execute(update(NotificationContact).where(
            NotificationContact.user_id == user_id, NotificationContact.channel == channel,
            NotificationContact.revoked_at.is_(None),
        ).values(revoked_at=now))
        await _disable_channel(session, user_id, channel, now)
        contact = NotificationContact(id=contact_id, user_id=user_id, channel=channel,
            destination=destination, destination_hash=fingerprint, generation=generation + 1)
        challenge = NotificationChallenge(id=challenge_id, contact_id=contact_id,
            token_hash=hmac.new(signing_secret, f"{challenge_id}:{code}".encode(), hashlib.sha256).hexdigest(),
            expires_at=now + timedelta(minutes=10))
        session.add(contact)
        await session.flush()
        session.add(challenge)
        await session.commit()
    if channel == "sms":
        result = await transport.start_sms_verification(destination)
    else:
        payload = {"from": settings.RESEND_FROM, "to": [destination], "subject": "Verify your NEOS email",
            "text": f"Your NEOS verification code is {code}. It expires in 10 minutes. If you did not request this, ignore this message.",
            "html": f"<p>Your NEOS verification code is <strong>{code}</strong>.</p><p>It expires in 10 minutes. If you did not request this, ignore this message.</p>"}
        if setting(settings, "RESEND_REPLY_TO"):
            payload["reply_to"] = settings.RESEND_REPLY_TO
        result = await transport.send("email", payload, f"neos-verification-{challenge_id}")
    async with factory() as session:
        challenge = await session.get(NotificationChallenge, challenge_id)
        contact = await session.get(NotificationContact, contact_id)
        superseded = bool(contact.revoked_at)
        if result.state == "accepted" and contact and not contact.revoked_at:
            challenge.provider_verification_id = result.provider_id
        else:
            challenge.used_at = utcnow()
        await session.commit()
        dto = contact_dto(contact)
    if result.state != "accepted":
        raise ApiError(503, "Verification could not be confirmed. Please try again later.")
    if superseded:
        raise ApiError(409, "A newer destination replaced this verification request")
    return {"contact": dto, "challenge_id": str(challenge_id), "status": "verification_pending"}


async def verify_contact(factory, user_id, contact_id, challenge_id, code, settings, transport):
    if not isinstance(code, str) or not re.fullmatch(r"[0-9]{6}", code):
        raise ApiError(400, "Enter the six-digit verification code")
    now = utcnow()
    verified = False
    async with factory() as session:
        await _owner_lock(session, user_id)
        await _quota(session, f"guess:user:{user_id}", 20, now)
        contact = (await session.execute(select(NotificationContact).where(
            NotificationContact.id == contact_id, NotificationContact.user_id == user_id,
        ).with_for_update())).scalar_one_or_none()
        challenge = (await session.execute(select(NotificationChallenge).where(
            NotificationChallenge.id == challenge_id, NotificationChallenge.contact_id == contact_id,
        ).with_for_update())).scalar_one_or_none()
        valid = (contact and not contact.revoked_at and not contact.suppressed_at
                 and challenge and not challenge.used_at and challenge.expires_at > now and challenge.attempts < 5)
        if valid and configured_channels(settings)[contact.channel][0]:
            challenge.attempts += 1
            if contact.channel == "email":
                actual = hmac.new(_secret(settings), f"{challenge.id}:{code}".encode(), hashlib.sha256).hexdigest()
                verified = hmac.compare_digest(actual, challenge.token_hash)
            elif challenge.provider_verification_id:
                verified = await transport.check_sms_verification(challenge.provider_verification_id, code)
            if verified:
                contact.verified_at = now
                challenge.used_at = now
            elif challenge.attempts >= 5:
                challenge.used_at = now
        await session.commit()
        dto = contact_dto(contact) if contact else None
    if not verified:
        raise ApiError(400, "Verification code is invalid, expired, or unavailable")
    return dto


async def revoke_contact(session, user_id, contact_id):
    await _owner_lock(session, user_id)
    contact = await session.get(NotificationContact, contact_id)
    if not contact or contact.user_id != user_id:
        raise ApiError(404, "Contact not found")
    contact.revoked_at = utcnow()
    await session.execute(update(NotificationChallenge).where(NotificationChallenge.contact_id == contact.id)
                          .values(used_at=utcnow()))
    await _disable_channel(session, user_id, contact.channel)


async def register_push(session, user_id, auth_session_id, body, settings):
    if not configured_channels(settings)["push"][0]:
        raise ApiError(503, "Push setup or activation is pending")
    keys = body.get("keys")
    if not isinstance(keys, dict):
        raise ApiError(400, "A browser push subscription is required")
    try:
        await validate_push_destination(body.get("endpoint"), keys.get("p256dh"), keys.get("auth"))
    except (ValueError, OSError) as error:
        raise ApiError(400, "This browser push endpoint is not supported") from error
    auth = await session.get(AuthSession, auth_session_id)
    if not auth or auth.user_id != user_id or naive(auth.expires_at) <= utcnow():
        raise ApiError(401, "A current browser session is required")
    await _owner_lock(session, user_id)
    existing = (await session.execute(select(EngagementPushDevice).where(
        EngagementPushDevice.endpoint == body["endpoint"],
    ).with_for_update())).scalar_one_or_none()
    if existing and existing.user_id != user_id:
        raise ApiError(409, "This browser subscription belongs to another account. Reset browser notifications first.")
    if existing:
        existing.p256dh_key, existing.auth_key = keys["p256dh"], keys["auth"]
        existing.auth_session_id, existing.enabled = auth_session_id, True
        device = existing
    else:
        device = EngagementPushDevice(id=uuid.uuid4(), user_id=user_id, auth_session_id=auth_session_id,
            endpoint=body["endpoint"], p256dh_key=keys["p256dh"], auth_key=keys["auth"])
        session.add(device)
    await session.flush()
    return {"id": str(device.id), "status": "subscribed"}


async def disable_user_devices(session, user_id, auth_session_id=None):
    statement = update(EngagementPushDevice).where(EngagementPushDevice.user_id == user_id)
    if auth_session_id is not None:
        statement = statement.where(EngagementPushDevice.auth_session_id == auth_session_id)
    await session.execute(statement.values(enabled=False))


def unsubscribe_token(contact_id, settings):
    raw = uuid.UUID(str(contact_id)).bytes
    signature = hmac.new(_secret(settings), b"unsubscribe:" + raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(raw + signature).decode().rstrip("=")


def read_unsubscribe_token(token, settings):
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{64}", token):
        raise ApiError(400, "Invalid unsubscribe link")
    raw = base64.urlsafe_b64decode(token)
    expected = hmac.new(_secret(settings), b"unsubscribe:" + raw[:16], hashlib.sha256).digest()
    if not hmac.compare_digest(raw[16:], expected):
        raise ApiError(400, "Invalid unsubscribe link")
    return uuid.UUID(bytes=raw[:16])


async def unsubscribe_contact(session, token, settings):
    contact_id = read_unsubscribe_token(token, settings)
    contact = (await session.execute(select(NotificationContact).where(
        NotificationContact.id == contact_id,
    ).with_for_update())).scalar_one_or_none()
    if contact:
        contact.suppressed_at = contact.suppressed_at or utcnow()
        contact.suppression_reason = contact.suppression_reason or "unsubscribe"
        if not contact.revoked_at:
            await _disable_channel(session, contact.user_id, contact.channel)
    return {"status": "unsubscribed"}


def quiet_until(preference, value):
    value = max(naive(value), naive(preference.paused_until)) if preference.paused_until else naive(value)
    if not preference.quiet_start or not preference.quiet_end or preference.quiet_start == preference.quiet_end:
        return value
    zone = ZoneInfo(preference.timezone)
    start, end = preference.quiet_start, preference.quiet_end
    candidate = value
    for _ in range(24 * 60 + 1):
        wall = candidate.replace(tzinfo=timezone.utc).astimezone(zone).strftime("%H:%M")
        quiet = start <= wall < end if start < end else wall >= start or wall < end
        if not quiet:
            return candidate
        candidate = candidate.replace(second=0, microsecond=0) + timedelta(minutes=1)
    return candidate


def cadence_due(preference, frequency, now=None):
    now = now or utcnow()
    if frequency == "immediate":
        return quiet_until(preference, now)
    zone = ZoneInfo(preference.timezone)
    local = now.replace(tzinfo=timezone.utc).astimezone(zone)
    target = local.replace(hour=9, minute=0, second=0, microsecond=0)
    if frequency == "weekly":
        target += timedelta(days=(-target.weekday()) % 7)
        if target <= local:
            target += timedelta(days=7)
    elif target <= local:
        target += timedelta(days=1)
    return quiet_until(preference, target.astimezone(timezone.utc).replace(tzinfo=None))


async def queue_deliveries(session, settings, *, limit=100, now=None):
    from neos_agent.services.engagement import delivery_candidates
    now = now or utcnow()
    count = 0
    for channel, (ready, _) in configured_channels(settings).items():
        if not ready:
            continue
        if channel == "push":
            consumed = exists(select(NotificationConsumption.id).join(
                NotificationDelivery, NotificationConsumption.delivery_id == NotificationDelivery.id,
            ).where(
                NotificationConsumption.user_id == EngagementInboxItem.user_id,
                NotificationConsumption.event_id == EngagementInboxItem.event_id,
                NotificationConsumption.channel == channel,
                NotificationDelivery.device_id == EngagementPushDevice.id,
            ))
            query = select(EngagementInboxItem, EngagementEvent, EngagementPreference, EngagementPushDevice).join(
                EngagementEvent, EngagementInboxItem.event_id == EngagementEvent.id,
            ).join(EngagementPreference, EngagementPreference.user_id == EngagementInboxItem.user_id).join(
                EngagementPushDevice, EngagementPushDevice.user_id == EngagementInboxItem.user_id,
            ).join(AuthSession, AuthSession.id == EngagementPushDevice.auth_session_id).where(
                EngagementPushDevice.enabled.is_(True), AuthSession.user_id == EngagementInboxItem.user_id,
                AuthSession.expires_at > now.replace(tzinfo=timezone.utc),
            )
        else:
            consumed = exists(select(NotificationConsumption.id).where(
                NotificationConsumption.user_id == EngagementInboxItem.user_id,
                NotificationConsumption.event_id == EngagementInboxItem.event_id,
                NotificationConsumption.channel == channel, NotificationConsumption.target_key == "",
            ))
            query = select(EngagementInboxItem, EngagementEvent, EngagementPreference).join(
                EngagementEvent, EngagementInboxItem.event_id == EngagementEvent.id,
            ).join(EngagementPreference, EngagementPreference.user_id == EngagementInboxItem.user_id)
        query = query.where(
            getattr(EngagementPreference, f"{channel}_enabled").is_(True),
            EngagementEvent.occurred_at > now - MAX_EVENT_AGE, ~consumed,
        ).order_by(EngagementInboxItem.created_at, EngagementInboxItem.id).limit(max(1, limit // 3))
        rows = (await session.execute(query)).all()
        for values in rows:
            item, event, preference = values[:3]
            device = values[3] if channel == "push" else None
            target_key = str(device.id) if device else ""
            owner = (await session.execute(select(EngagementPreference).where(
                EngagementPreference.user_id == item.user_id,
            ).with_for_update(skip_locked=True))).scalar_one_or_none()
            if owner is None:
                continue
            exists_now = (await session.execute(select(NotificationConsumption.id).where(
                NotificationConsumption.user_id == item.user_id, NotificationConsumption.event_id == event.id,
                NotificationConsumption.channel == channel, NotificationConsumption.target_key == target_key,
            ))).scalar_one_or_none()
            if exists_now:
                continue
            candidates = await delivery_candidates(session, item.user_id, event)
            selected = next((entry for entry in candidates if entry["channel"] == channel), None)
            frequency = selected["frequency"] if selected else "immediate"
            allowed = bool(selected) and not (frequency != "immediate" and item.read_at)
            contact = await current_contact(session, item.user_id, channel) if channel != "push" else None
            due = cadence_due(preference, frequency, now)
            is_digest = frequency != "immediate" and allowed
            key = (f"{item.user_id}:{channel}:{target_key}:{frequency}:{due.isoformat()}"
                   if is_digest else f"{item.user_id}:{channel}:{target_key}:{event.id}")
            base_key = key
            key_match = NotificationDelivery.delivery_key == base_key
            if is_digest:
                key_match = or_(key_match, NotificationDelivery.delivery_key.startswith(base_key + ":part:", autoescape=True))
            delivery = (await session.execute(select(NotificationDelivery).where(
                key_match,
            ).order_by(NotificationDelivery.delivery_key.desc()).limit(1).with_for_update())).scalar_one_or_none()
            if delivery and (delivery.first_attempt_at or delivery.frozen_payload is not None
                             or delivery.attempt_started_at or delivery.state not in PENDING_STATES
                             or len(delivery.event_ids) >= 50):
                if not is_digest:
                    continue
                part = int(delivery.delivery_key.rsplit(":part:", 1)[1]) if delivery.delivery_key != base_key else 0
                key = f"{base_key}:part:{part + 1:010d}"
                delivery = None
            try:
                async with session.begin_nested():
                    if delivery is None:
                        delivery = NotificationDelivery(id=uuid.uuid4(), delivery_key=key, user_id=item.user_id,
                            channel=channel, contact_id=contact.id if contact else None, device_id=device.id if device else None,
                            event_ids=[str(event.id)], state="pending" if allowed else "suppressed", due_at=due,
                            error_code=None if allowed else "not_currently_subscribed")
                        session.add(delivery)
                        await session.flush()
                    else:
                        delivery.event_ids = [*delivery.event_ids, str(event.id)]
                    session.add(NotificationConsumption(id=uuid.uuid4(), user_id=item.user_id, event_id=event.id,
                        channel=channel, target_key=target_key, delivery_id=delivery.id))
                    await session.flush()
                count += 1
            except IntegrityError:
                continue
    return count


async def recover_expired_claims(session, *, now=None):
    now = now or utcnow()
    rows = list((await session.execute(select(NotificationDelivery).where(
        NotificationDelivery.state.in_(("claimed", "sending")),
        NotificationDelivery.lease_expires_at <= now,
    ).with_for_update(skip_locked=True).limit(100))).scalars())
    for row in rows:
        if row.attempt_started_at is None:
            row.state = "retry_wait"
        elif row.channel == "email" and row.first_attempt_at and now - row.first_attempt_at < timedelta(hours=23):
            row.state = "retry_wait"
        else:
            row.state = "ambiguous"
        row.error_code = "expired_lease_after_attempt" if row.attempt_started_at else "expired_lease"
        row.claim_token = None
        row.lease_expires_at = None
        row.due_at = now
    return len(rows)


async def claim_delivery(session, *, now=None):
    now = now or utcnow()
    row = (await session.execute(select(NotificationDelivery).where(
        NotificationDelivery.state.in_(PENDING_STATES), NotificationDelivery.due_at <= now,
    ).order_by(NotificationDelivery.due_at, NotificationDelivery.id)
        .with_for_update(skip_locked=True).limit(1))).scalar_one_or_none()
    if row is None:
        return None
    token = secrets.token_hex(24)
    result = await session.execute(update(NotificationDelivery).where(
        NotificationDelivery.id == row.id, NotificationDelivery.state.in_(PENDING_STATES),
    ).values(state="claimed", claim_token=token, lease_expires_at=now + timedelta(seconds=LEASE_SECONDS)))
    if result.rowcount != 1:
        return None
    return row.id, token


async def _delivery_eligibility(session, delivery, settings, now):
    from neos_agent.services.engagement import delivery_candidates, event_view
    user = await session.get(User, delivery.user_id)
    preference = await session.get(EngagementPreference, delivery.user_id)
    if not user or user.disabled_at or not preference or not getattr(preference, f"{delivery.channel}_enabled"):
        return "suppressed", "channel_or_account_disabled", None
    if not configured_channels(settings)[delivery.channel][0]:
        return "blocked_configuration", "channel_not_ready", None
    later = quiet_until(preference, now)
    if later > now:
        return "retry_wait", "quiet_or_paused", later
    contact = None
    if delivery.channel == "push":
        device = await session.get(EngagementPushDevice, delivery.device_id)
        if not device or device.user_id != delivery.user_id or not device.enabled or not device.auth_session_id:
            return "suppressed", "device_revoked", None
        auth = await session.get(AuthSession, device.auth_session_id)
        if not auth or auth.user_id != delivery.user_id or naive(auth.expires_at) <= now:
            return "suppressed", "device_session_expired", None
    else:
        contact = await session.get(NotificationContact, delivery.contact_id)
        current = await current_contact(session, delivery.user_id, delivery.channel)
        if (not contact or not current or current.id != contact.id or contact.user_id != delivery.user_id
                or contact.revoked_at or contact.suppressed_at or not contact.verified_at):
            return "suppressed", "contact_changed_or_unavailable", None
    for event_id in delivery.event_ids:
        event = await session.get(EngagementEvent, uuid.UUID(event_id))
        if not event or event.occurred_at <= now - MAX_EVENT_AGE or not await event_view(session, delivery.user_id, event):
            return "suppressed", "source_no_longer_available", None
        candidates = await delivery_candidates(session, delivery.user_id, event)
        candidate = next((entry for entry in candidates if entry["channel"] == delivery.channel), None)
        if candidate is None:
            return "suppressed", "subscription_changed", None
    if not delivery.event_ids:
        return "suppressed", "empty_delivery", None
    return "ready", None, None


async def _freeze_payload(session, delivery, settings):
    base = settings.ENGAGEMENT_PUBLIC_URL.rstrip("/")
    url = f"{base}/updates"
    count = len(delivery.event_ids)
    text = f"You have {count} new community update{'s' if count != 1 else ''} on NEOS. Open your updates: {url}"
    if delivery.channel == "email":
        contact = await session.get(NotificationContact, delivery.contact_id)
        unsubscribe = (settings.ENGAGEMENT_API_PUBLIC_URL.rstrip("/") + "/api/v1/engagement/unsubscribe?token="
                       + unsubscribe_token(contact.id, settings))
        body = {"from": settings.RESEND_FROM, "to": [contact.destination], "subject": "Your NEOS community updates",
                "text": text + f"\nYou received this because you enabled email updates for your subscriptions.\nPreferences: {base}/settings/notifications\nUnsubscribe: {unsubscribe}",
                "html": f'<p>You have {count} new community updates.</p><p><a href="{escape(url, quote=True)}">Open your updates</a></p><p>You enabled email for your subscriptions.</p><p><a href="{escape(base + "/settings/notifications", quote=True)}">Preferences</a> · <a href="{escape(unsubscribe, quote=True)}">Unsubscribe</a></p>',
                "headers": {"List-Unsubscribe": f"<{unsubscribe}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"}}
        if setting(settings, "RESEND_REPLY_TO"):
            body["reply_to"] = settings.RESEND_REPLY_TO
    elif delivery.channel == "sms":
        contact = await session.get(NotificationContact, delivery.contact_id)
        body = {"To": contact.destination, "MessagingServiceSid": settings.TWILIO_MESSAGING_SERVICE_SID,
                "Body": text + " Reply STOP to unsubscribe.",
                "StatusCallback": settings.ENGAGEMENT_API_PUBLIC_URL.rstrip("/") + "/api/v1/engagement/webhooks/twilio"}
    else:
        device = await session.get(EngagementPushDevice, delivery.device_id)
        body = {"subscription": {"endpoint": device.endpoint, "keys": {"p256dh": device.p256dh_key, "auth": device.auth_key}},
                "data": {"title": "NEOS community updates", "body": "You have new updates in your communities.", "url": "/updates"}}
    return {"provider_body": body, "event_ids": list(delivery.event_ids),
            "contact_id": str(delivery.contact_id) if delivery.contact_id else None,
            "device_id": str(delivery.device_id) if delivery.device_id else None}


async def prepare_attempt(factory, delivery_id, claim_token, settings, *, now=None):
    now = now or utcnow()
    async with factory() as session:
        delivery = (await session.execute(select(NotificationDelivery).where(
            NotificationDelivery.id == delivery_id, NotificationDelivery.claim_token == claim_token,
            NotificationDelivery.state == "claimed",
        ).with_for_update())).scalar_one_or_none()
        if delivery is None or delivery.lease_expires_at <= now:
            return None
        if not delivery.first_attempt_at:
            from neos_agent.services.engagement import delivery_candidates
            unread_manifest = []
            for event_id in delivery.event_ids:
                event = await session.get(EngagementEvent, uuid.UUID(event_id))
                candidates = await delivery_candidates(session, delivery.user_id, event) if event else []
                candidate = next((entry for entry in candidates if entry["channel"] == delivery.channel), None)
                item = (await session.execute(select(EngagementInboxItem).where(
                    EngagementInboxItem.user_id == delivery.user_id,
                    EngagementInboxItem.event_id == uuid.UUID(event_id),
                ))).scalar_one_or_none()
                if candidate and candidate["frequency"] != "immediate" and (not item or item.read_at):
                    continue
                unread_manifest.append(event_id)
            delivery.event_ids = unread_manifest
        state, error, later = await _delivery_eligibility(session, delivery, settings, now)
        if state != "ready":
            delivery.state, delivery.error_code = state, error
            delivery.claim_token, delivery.lease_expires_at = None, None
            delivery.due_at = later or now + timedelta(minutes=15)
            await session.commit()
            return None
        if delivery.attempt_count >= MAX_ATTEMPTS:
            delivery.state, delivery.error_code = "dead", "attempt_limit"
            delivery.claim_token, delivery.lease_expires_at = None, None
            await session.commit()
            return None
        if delivery.first_attempt_at and delivery.channel == "email" and now - delivery.first_attempt_at >= timedelta(hours=23):
            delivery.state, delivery.error_code = "ambiguous", "provider_idempotency_window_elapsed"
            delivery.claim_token, delivery.lease_expires_at = None, None
            await session.commit()
            return None
        if delivery.frozen_payload is None:
            delivery.frozen_payload = await _freeze_payload(session, delivery, settings)
        delivery.state = "sending"
        delivery.attempt_count += 1
        delivery.attempt_started_at = now
        delivery.first_attempt_at = delivery.first_attempt_at or now
        delivery.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
        result = {"channel": delivery.channel, "payload": delivery.frozen_payload["provider_body"],
                  "key": f"neos-delivery-{delivery.id}"}
        await session.commit()
        return result


async def finish_attempt(factory, delivery_id, claim_token, result, *, now=None):
    now = now or utcnow()
    async with factory() as session:
        row = (await session.execute(select(NotificationDelivery).where(
            NotificationDelivery.id == delivery_id, NotificationDelivery.claim_token == claim_token,
            NotificationDelivery.state == "sending",
        ).with_for_update())).scalar_one_or_none()
        if row is None:
            return False
        row.error_code = result.error_code
        if result.state == "accepted":
            row.state, row.accepted_at, row.provider_message_id = "accepted", now, result.provider_id
        elif result.state == "blocked_configuration":
            row.state, row.due_at = "blocked_configuration", now + timedelta(minutes=15)
        elif result.state == "retryable":
            row.state = "retry_wait" if row.attempt_count < MAX_ATTEMPTS else "dead"
            row.attempt_started_at = None
            row.due_at = now + timedelta(seconds=max(result.retry_after, min(3600, 30 * 2 ** row.attempt_count)))
        elif result.state == "ambiguous":
            if row.channel == "email" and now - row.first_attempt_at < timedelta(hours=23) and row.attempt_count < MAX_ATTEMPTS:
                row.state, row.due_at = "retry_wait", now + timedelta(seconds=60 * 2 ** row.attempt_count)
            else:
                row.state = "ambiguous"
        else:
            row.state = "dead"
        if result.error_code == "push_endpoint_expired" and row.device_id:
            await session.execute(update(EngagementPushDevice).where(EngagementPushDevice.id == row.device_id).values(enabled=False))
        row.claim_token, row.lease_expires_at = None, None
        await session.commit()
        return True


async def dispatch_one(factory, settings, transport):
    async with factory() as session:
        claim = await claim_delivery(session)
        await session.commit()
    if claim is None:
        return False
    delivery_id, token = claim
    attempt = await prepare_attempt(factory, delivery_id, token, settings)
    if attempt is None:
        return True
    timeout = min(30, max(1, float(setting(settings, "ENGAGEMENT_SEND_TIMEOUT_SECONDS", 15)))) + 5
    try:
        result = await asyncio.wait_for(transport.send(attempt["channel"], attempt["payload"], attempt["key"]), timeout)
    except asyncio.CancelledError:
        raise
    except Exception:
        result = SendResult("ambiguous", error_code="transport_uncertain")
    await finish_attempt(factory, delivery_id, token, result)
    return True


async def run_engagement_cycle(factory, settings, transport, *, stop_event=None):
    from neos_agent.services.engagement import fanout_pending
    async with factory() as session:
        await fanout_pending(session, limit=25)
        await recover_expired_claims(session)
        await queue_deliveries(session, settings, limit=100)
        await session.execute(delete(NotificationRateLimit).where(NotificationRateLimit.window_start < utcnow() - timedelta(days=2)))
        await session.execute(delete(NotificationChallenge).where(NotificationChallenge.expires_at < utcnow() - timedelta(days=7)))
        await session.commit()
    for _ in range(10):
        if stop_event is not None and stop_event.is_set():
            break
        if not await dispatch_one(factory, settings, transport):
            break


async def run_engagement_loop(app):
    stop_event = getattr(app.ctx, "engagement_stop", None)
    if stop_event is None:
        stop_event = app.ctx.engagement_stop = asyncio.Event()
    timeout = min(30, max(1, float(setting(app.ctx.settings, "ENGAGEMENT_SEND_TIMEOUT_SECONDS", 15))))
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5), follow_redirects=False) as client:
        transport = ProviderTransport(app.ctx.settings, client)
        app.ctx.engagement_transport = transport
        try:
            while not stop_event.is_set():
                try:
                    cycle = asyncio.create_task(run_engagement_cycle(
                        app.ctx.db, app.ctx.settings, transport, stop_event=stop_event))
                    try:
                        await asyncio.shield(cycle)
                    except asyncio.CancelledError:
                        stop_event.set()
                        await cycle
                        raise
                except asyncio.CancelledError:
                    raise
                except Exception as error:
                    logger.error("Engagement worker cycle failed (%s)", type(error).__name__)
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=min(30, max(1,
                        float(setting(app.ctx.settings, "ENGAGEMENT_WORKER_INTERVAL_SECONDS", 15)))))
                except asyncio.TimeoutError:
                    pass
        finally:
            app.ctx.engagement_transport = None


async def _receipt_once(session, provider, key):
    try:
        async with session.begin_nested():
            session.add(NotificationWebhookReceipt(id=uuid.uuid4(), provider=provider, receipt_key=f"{provider}:{key}"))
            await session.flush()
        return True
    except IntegrityError:
        return False


async def apply_resend_webhook(session, payload, receipt_id):
    event_type = payload.get("type")
    data = payload.get("data")
    provider_id = data.get("email_id") if isinstance(data, dict) else None
    if not isinstance(provider_id, str):
        return {"status": "accepted"}
    delivery = (await session.execute(select(NotificationDelivery).where(
        NotificationDelivery.provider_message_id == provider_id, NotificationDelivery.channel == "email",
    ).with_for_update())).scalar_one_or_none()
    if delivery is None:
        challenge = (await session.execute(select(NotificationChallenge).where(
            NotificationChallenge.provider_verification_id == provider_id,
        ))).scalar_one_or_none()
        if challenge is None:
            raise ApiError(503, "Delivery receipt is not available yet")
        if not await _receipt_once(session, "resend", receipt_id):
            return {"status": "accepted"}
        if event_type in {"email.bounced", "email.complained", "email.suppressed"}:
            contact = await session.get(NotificationContact, challenge.contact_id)
            if contact:
                contact.suppressed_at, contact.suppression_reason = utcnow(), event_type
                challenge.used_at = utcnow()
        return {"status": "accepted"}
    if not await _receipt_once(session, "resend", receipt_id):
        return {"status": "accepted"}
    now = utcnow()
    if event_type == "email.delivered" and delivery.state not in {"suppressed", "dead"}:
        delivery.state, delivery.delivered_at = "delivered", now
    elif event_type in {"email.bounced", "email.complained", "email.suppressed"}:
        contact = await session.get(NotificationContact, delivery.contact_id)
        if contact:
            contact.suppressed_at = contact.suppressed_at or now
            contact.suppression_reason = event_type
            await session.execute(update(NotificationDelivery).where(
                NotificationDelivery.contact_id == contact.id, NotificationDelivery.state.in_(PENDING_STATES + ("claimed",)),
                NotificationDelivery.attempt_started_at.is_(None),
            ).values(state="suppressed", error_code="destination_suppressed"))
        delivery.state, delivery.error_code = "suppressed", event_type
    elif event_type == "email.failed" and delivery.state not in {"delivered", "suppressed"}:
        delivery.state, delivery.error_code = "dead", "email_failed"
    return {"status": "accepted"}


async def apply_twilio_webhook(session, form):
    sid = form.get("MessageSid")
    if not isinstance(sid, str) or not re.fullmatch(r"SM[0-9a-fA-F]{32}", sid):
        return {"status": "accepted"}
    status = str(form.get("MessageStatus") or "").lower()
    opt_out = str(form.get("OptOutType") or "").upper()
    receipt_key = f"{sid}:{status}:{opt_out}"
    now = utcnow()
    if opt_out == "STOP":
        if not await _receipt_once(session, "twilio", receipt_key):
            return {"status": "accepted"}
        try:
            destination = normalize_destination("sms", form.get("From"))
        except ApiError:
            return {"status": "accepted"}
        fingerprint = destination_hash("sms", destination)
        contacts = list((await session.execute(select(NotificationContact).where(
            NotificationContact.channel == "sms", NotificationContact.destination_hash == fingerprint,
        ).with_for_update())).scalars())
        for contact in contacts:
            contact.suppressed_at, contact.suppression_reason = contact.suppressed_at or now, "sms_stop"
            if not contact.revoked_at:
                await _disable_channel(session, contact.user_id, "sms")
        return {"status": "accepted"}
    if opt_out == "START":
        if not await _receipt_once(session, "twilio", receipt_key):
            return {"status": "accepted"}
        try:
            destination = normalize_destination("sms", form.get("From"))
        except ApiError:
            return {"status": "accepted"}
        contacts = list((await session.execute(select(NotificationContact).where(
            NotificationContact.channel == "sms",
            NotificationContact.destination_hash == destination_hash("sms", destination),
            NotificationContact.suppression_reason == "sms_stop",
        ).with_for_update())).scalars())
        for contact in contacts:
            contact.suppressed_at = contact.suppression_reason = contact.verified_at = None
            await _disable_channel(session, contact.user_id, "sms")
        return {"status": "accepted"}
    delivery = (await session.execute(select(NotificationDelivery).where(
        NotificationDelivery.provider_message_id == sid, NotificationDelivery.channel == "sms",
    ).with_for_update())).scalar_one_or_none()
    if delivery is None:
        raise ApiError(503, "Delivery receipt is not available yet")
    if not await _receipt_once(session, "twilio", receipt_key):
        return {"status": "accepted"}
    if delivery:
        if status == "delivered" and delivery.state not in {"suppressed", "dead"}:
            delivery.state, delivery.delivered_at = "delivered", now
        elif status in {"failed", "undelivered"} and delivery.state != "delivered":
            delivery.state, delivery.error_code = "dead", f"sms_{status}"
    return {"status": "accepted"}
