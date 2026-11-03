"""Delivery lifecycle contracts with fake transports and persisted state."""
from datetime import datetime, timedelta, timezone
import re
from types import SimpleNamespace
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from neos_agent.api.errors import ApiError
from neos_agent.db.models import AuthSession, User
from neos_agent.db.models.engagement import (
    EngagementEvent, EngagementInboxItem, EngagementPreference, EngagementPushDevice,
    NotificationChallenge, NotificationContact, NotificationDelivery, NotificationConsumption,
    NotificationRateLimit, NotificationWebhookReceipt,
)
from neos_agent.services import engagement_delivery as delivery
from neos_agent.services.engagement_providers import SendResult


@pytest.fixture
def settings():
    return SimpleNamespace(ENGAGEMENT_EXTERNAL_ENABLED=True, ENGAGEMENT_EMAIL_ENABLED=True,
        ENGAGEMENT_PUSH_ENABLED=True, ENGAGEMENT_SMS_ENABLED=True,
        ENGAGEMENT_PUBLIC_URL="https://neos.example", ENGAGEMENT_API_PUBLIC_URL="https://api.neos.example",
        ENGAGEMENT_SIGNING_SECRET="s" * 40, RESEND_API_KEY="test-only", RESEND_FROM="NEOS <updates@example.test>",
        RESEND_REPLY_TO="", RESEND_WEBHOOK_SECRET="test-only", VAPID_PUBLIC_KEY="test-only",
        VAPID_PRIVATE_KEY="test-only", VAPID_SUBJECT="mailto:operator@example.test",
        TWILIO_ACCOUNT_SID="AC" + "a" * 32, TWILIO_API_KEY_SID="SK" + "a" * 32,
        TWILIO_API_KEY_SECRET="test-only", TWILIO_AUTH_TOKEN="test-only",
        TWILIO_MESSAGING_SERVICE_SID="MG" + "a" * 32, TWILIO_VERIFY_SERVICE_SID="VA" + "a" * 32,
        ENGAGEMENT_SEND_TIMEOUT_SECONDS=2)


class FakeTransport:
    def __init__(self, result=None):
        self.result = result or SendResult("accepted", "provider-test")
        self.sends = []
        self.approved = False

    async def send(self, channel, payload, key):
        self.sends.append((channel, payload, key))
        return self.result

    async def start_sms_verification(self, destination):
        self.sends.append(("verify", destination, None))
        return SendResult("accepted", "VE-test")

    async def check_sms_verification(self, provider_id, code):
        return self.approved


@pytest_asyncio.fixture
async def owner_factory(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    owner = uuid.uuid4()
    async with factory() as session:
        session.add(User(id=owner, display_name="Synthetic owner", username="delivery-test"))
        await session.commit()
    return owner, factory


def submitted_code(transport):
    return re.search(r"code is ([0-9]{6})", transport.sends[-1][1]["text"]).group(1)


async def seed_delivery(owner_factory, *, channel="email", frequency="daily", event_count=1, read=False):
    owner, factory = owner_factory
    now = delivery.utcnow()
    event_ids = [uuid.uuid4() for _ in range(event_count)]
    contact_id, delivery_id = uuid.uuid4(), uuid.uuid4()
    destination = "member@example.test" if channel == "email" else "+15555550123"
    async with factory() as session:
        session.add(EngagementPreference(user_id=owner, timezone="UTC", email_enabled=True, sms_enabled=True,
            push_enabled=True, channel_enabled_at={channel: (now - timedelta(days=1)).isoformat() + "Z"}))
        contact = NotificationContact(id=contact_id, user_id=owner, channel=channel,
            destination=destination,
            destination_hash=delivery.destination_hash(channel, destination), generation=1, verified_at=now)
        session.add(contact)
        for event_id in event_ids:
            session.add(EngagementEvent(id=event_id, event_key=str(event_id), family="governance",
                event_type="proposal.stage", source_kind="proposal", source_id=uuid.uuid4(), occurred_at=now))
        await session.flush()
        for event_id in event_ids:
            session.add(EngagementInboxItem(id=uuid.uuid4(), user_id=owner, event_id=event_id,
                reason_code="following", read_at=now if read else None))
        row = NotificationDelivery(id=delivery_id, user_id=owner, delivery_key=str(delivery_id),
            channel=channel, contact_id=contact_id, event_ids=[str(value) for value in event_ids], due_at=now, state="pending")
        session.add(row)
        await session.commit()
    return delivery_id, contact_id, event_ids


def allow_sources(monkeypatch, channel="email", frequency="daily"):
    from neos_agent.services import engagement
    async def view(session, user_id, event, **kwargs):
        return {"title": "Private title must not enter external body", "url": "/proposals/source"} if event else None
    async def candidates(session, user_id, event):
        return [{"channel": channel, "frequency": frequency, "reason": "following"}]
    monkeypatch.setattr(engagement, "event_view", view)
    monkeypatch.setattr(engagement, "delivery_candidates", candidates)


async def test_capabilities_without_keys_and_without_device(owner_factory, settings):
    owner, factory = owner_factory
    settings.RESEND_API_KEY = ""
    async with factory() as session:
        result = await delivery.get_capabilities(session, owner, settings)
    assert result["channels"]["in_app"]["state"] == "ready"
    assert result["channels"]["email"]["state"] == "pending_setup"
    assert result["channels"]["push"]["state"] == "needs_verification"
    assert result["contacts"] == []


async def test_disabled_verification_makes_zero_sends(owner_factory, settings):
    owner, factory = owner_factory
    settings.ENGAGEMENT_EXTERNAL_ENABLED = False
    transport = FakeTransport()
    with pytest.raises(ApiError) as error:
        await delivery.request_contact(factory, owner, "email", "member@example.test", settings, transport)
    assert error.value.status == 503 and transport.sends == []
    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(NotificationContact)) == 0


async def test_email_verification_one_use_and_not_notification_consent(owner_factory, settings):
    owner, factory = owner_factory
    transport = FakeTransport()
    requested = await delivery.request_contact(factory, owner, "email", "Member@Example.test", settings, transport)
    assert requested["status"] == "verification_pending" and "code" not in requested
    code = submitted_code(transport)
    contact_id, challenge_id = uuid.UUID(requested["contact"]["id"]), uuid.UUID(requested["challenge_id"])
    result = await delivery.verify_contact(factory, owner, contact_id, challenge_id, code, settings, transport)
    assert result["verified"] and result["masked_destination"] == "m***@example.test"
    async with factory() as session:
        challenge = await session.get(NotificationChallenge, challenge_id)
        assert challenge.token_hash != code and challenge.used_at
        preference = await session.get(EngagementPreference, owner)
        assert preference is None or not preference.email_enabled
    with pytest.raises(ApiError):
        await delivery.verify_contact(factory, owner, contact_id, challenge_id, code, settings, transport)


async def test_replacement_invalidates_old_challenge_and_preserves_unverified_new_contact(owner_factory, settings):
    owner, factory = owner_factory
    transport = FakeTransport()
    first = await delivery.request_contact(factory, owner, "email", "a@example.test", settings, transport)
    first_code = submitted_code(transport)
    second = await delivery.request_contact(factory, owner, "email", "b@example.test", settings, transport)
    with pytest.raises(ApiError):
        await delivery.verify_contact(factory, owner, uuid.UUID(first["contact"]["id"]),
            uuid.UUID(first["challenge_id"]), first_code, settings, transport)
    async with factory() as session:
        assert (await session.get(NotificationContact, uuid.UUID(first["contact"]["id"]))).revoked_at
        assert not (await session.get(NotificationContact, uuid.UUID(second["contact"]["id"]))).verified_at


async def test_destination_quota_survives_new_contacts(owner_factory, settings):
    owner, factory = owner_factory
    transport = FakeTransport()
    for _ in range(3):
        await delivery.request_contact(factory, owner, "email", "same@example.test", settings, transport)
    with pytest.raises(ApiError) as error:
        await delivery.request_contact(factory, owner, "email", "same@example.test", settings, transport)
    assert error.value.status == 429 and len(transport.sends) == 3


async def test_guess_limit_persists_failed_attempts(owner_factory, settings):
    owner, factory = owner_factory
    transport = FakeTransport()
    requested = await delivery.request_contact(factory, owner, "email", "member@example.test", settings, transport)
    code = submitted_code(transport)
    bad = "000000" if code != "000000" else "999999"
    contact_id, challenge_id = uuid.UUID(requested["contact"]["id"]), uuid.UUID(requested["challenge_id"])
    for _ in range(5):
        with pytest.raises(ApiError):
            await delivery.verify_contact(factory, owner, contact_id, challenge_id, bad, settings, transport)
    with pytest.raises(ApiError):
        await delivery.verify_contact(factory, owner, contact_id, challenge_id, code, settings, transport)
    async with factory() as session:
        challenge = await session.get(NotificationChallenge, challenge_id)
        assert challenge.attempts == 5 and challenge.used_at


async def test_sms_requires_real_provider_approval(owner_factory, settings):
    owner, factory = owner_factory
    transport = FakeTransport()
    requested = await delivery.request_contact(factory, owner, "sms", "+15555550123", settings, transport)
    args = (factory, owner, uuid.UUID(requested["contact"]["id"]), uuid.UUID(requested["challenge_id"]), "123456", settings, transport)
    with pytest.raises(ApiError):
        await delivery.verify_contact(*args)
    transport.approved = True
    assert (await delivery.verify_contact(*args))["verified"]


def test_quiet_hours_cross_midnight_and_dst():
    preference = SimpleNamespace(timezone="America/Denver", quiet_start="22:00", quiet_end="08:00", paused_until=None)
    spring = datetime(2026, 3, 8, 7, 30)
    assert delivery.quiet_until(preference, spring) == datetime(2026, 3, 8, 14, 0)
    autumn = datetime(2026, 11, 1, 7, 30)
    assert delivery.quiet_until(preference, autumn) == datetime(2026, 11, 1, 15, 0)
    preference.paused_until = datetime(2026, 11, 3, 18, 0)
    assert delivery.quiet_until(preference, autumn) == preference.paused_until


def test_daily_weekly_use_local_nine_am():
    preference = SimpleNamespace(timezone="America/Denver", quiet_start=None, quiet_end=None, paused_until=None)
    monday = datetime(2026, 11, 2, 15, 0)
    assert delivery.cadence_due(preference, "daily", monday) == datetime(2026, 11, 2, 16, 0)
    assert delivery.cadence_due(preference, "weekly", monday) == datetime(2026, 11, 2, 16, 0)
    assert delivery.cadence_due(preference, "weekly", datetime(2026, 11, 2, 17)) == datetime(2026, 11, 9, 16)


async def test_all_read_digest_is_suppressed_without_send(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch)
    row_id, _, _ = await seed_delivery(owner_factory, event_count=2, read=True)
    _, factory = owner_factory
    transport = FakeTransport()
    assert await delivery.dispatch_one(factory, settings, transport)
    assert transport.sends == []
    async with factory() as session:
        row = await session.get(NotificationDelivery, row_id)
        assert row.state == "suppressed" and row.event_ids == []


async def test_mixed_digest_freezes_only_unread_items(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch)
    row_id, _, ids = await seed_delivery(owner_factory, event_count=2)
    owner, factory = owner_factory
    async with factory() as session:
        item = await session.scalar(select(EngagementInboxItem).where(EngagementInboxItem.event_id == ids[0]))
        item.read_at = delivery.utcnow()
        await session.commit()
    transport = FakeTransport()
    await delivery.dispatch_one(factory, settings, transport)
    assert len(transport.sends) == 1
    assert "1 new community update" in transport.sends[0][1]["text"]
    assert "Private title" not in str(transport.sends)
    async with factory() as session:
        row = await session.get(NotificationDelivery, row_id)
        assert row.event_ids == [str(ids[1])] and row.state == "accepted" and row.delivered_at is None


async def test_ambiguous_email_retry_keeps_payload_and_idempotency_key(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch)
    row_id, _, ids = await seed_delivery(owner_factory)
    _, factory = owner_factory
    transport = FakeTransport(SendResult("ambiguous", error_code="synthetic_timeout"))
    await delivery.dispatch_one(factory, settings, transport)
    async with factory() as session:
        row = await session.get(NotificationDelivery, row_id)
        row.due_at = delivery.utcnow() - timedelta(seconds=1)
        item = await session.scalar(select(EngagementInboxItem).where(EngagementInboxItem.event_id == ids[0]))
        item.read_at = delivery.utcnow()
        await session.commit()
    transport.result = SendResult("accepted", "provider-retry")
    await delivery.dispatch_one(factory, settings, transport)
    assert len(transport.sends) == 2 and transport.sends[0] == transport.sends[1]


async def test_contact_revoked_before_retry_prevents_send(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch)
    row_id, contact_id, _ = await seed_delivery(owner_factory)
    _, factory = owner_factory
    transport = FakeTransport(SendResult("ambiguous", error_code="synthetic_timeout"))
    await delivery.dispatch_one(factory, settings, transport)
    async with factory() as session:
        (await session.get(NotificationContact, contact_id)).revoked_at = delivery.utcnow()
        (await session.get(NotificationDelivery, row_id)).due_at = delivery.utcnow() - timedelta(seconds=1)
        await session.commit()
    await delivery.dispatch_one(factory, settings, transport)
    assert len(transport.sends) == 1
    async with factory() as session:
        assert (await session.get(NotificationDelivery, row_id)).state == "suppressed"


async def test_expired_started_sms_lease_is_ambiguous_and_stale_owner_cannot_finish(owner_factory, settings):
    row_id, _, _ = await seed_delivery(owner_factory, channel="sms")
    _, factory = owner_factory
    now = delivery.utcnow()
    async with factory() as session:
        row = await session.get(NotificationDelivery, row_id)
        row.state, row.claim_token = "sending", "old-owner"
        row.attempt_started_at = row.first_attempt_at = now - timedelta(minutes=2)
        row.lease_expires_at = now - timedelta(seconds=1)
        await session.commit()
    async with factory() as session:
        assert await delivery.recover_expired_claims(session) == 1
        await session.commit()
    assert not await delivery.finish_attempt(factory, row_id, "old-owner", SendResult("accepted", "late"))
    async with factory() as session:
        assert await delivery.claim_delivery(session) is None
        assert (await session.get(NotificationDelivery, row_id)).state == "ambiguous"


async def test_email_uncertain_retry_stops_before_provider_window(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch)
    row_id, _, _ = await seed_delivery(owner_factory)
    _, factory = owner_factory
    async with factory() as session:
        row = await session.get(NotificationDelivery, row_id)
        row.first_attempt_at = delivery.utcnow() - timedelta(hours=24)
        row.attempt_started_at = row.first_attempt_at
        await session.commit()
    transport = FakeTransport()
    await delivery.dispatch_one(factory, settings, transport)
    assert not transport.sends
    async with factory() as session:
        assert (await session.get(NotificationDelivery, row_id)).state == "ambiguous"


async def test_unsubscribe_is_contact_bound_idempotent_and_tamper_safe(owner_factory, settings):
    owner, factory = owner_factory
    row_id, contact_id, _ = await seed_delivery(owner_factory)
    token = delivery.unsubscribe_token(contact_id, settings)
    assert delivery.read_unsubscribe_token(token, settings) == contact_id
    with pytest.raises(ApiError):
        delivery.read_unsubscribe_token(("A" if token[0] != "A" else "B") + token[1:], settings)
    async with factory() as session:
        await delivery.unsubscribe_contact(session, token, settings)
        await delivery.unsubscribe_contact(session, token, settings)
        await session.commit()
        assert not (await session.get(EngagementPreference, owner)).email_enabled
        assert (await session.get(NotificationDelivery, row_id)).state == "suppressed"


async def test_old_contact_bounce_does_not_suppress_replacement(owner_factory, settings):
    owner, factory = owner_factory
    row_id, old_id, _ = await seed_delivery(owner_factory)
    replacement_id = uuid.uuid4()
    async with factory() as session:
        (await session.get(NotificationContact, old_id)).revoked_at = delivery.utcnow()
        session.add(NotificationContact(id=replacement_id, user_id=owner, channel="email",
            destination="new@example.test", destination_hash=delivery.destination_hash("email", "new@example.test"),
            generation=2, verified_at=delivery.utcnow()))
        row = await session.get(NotificationDelivery, row_id)
        row.state, row.provider_message_id = "accepted", "email-old"
        await session.commit()
    event = {"type": "email.complained", "data": {"email_id": "email-old"}}
    async with factory() as session:
        await delivery.apply_resend_webhook(session, event, "receipt-1")
        await delivery.apply_resend_webhook(session, event, "receipt-1")
        await session.commit()
        assert (await session.get(NotificationContact, old_id)).suppressed_at
        assert not (await session.get(NotificationContact, replacement_id)).suppressed_at
        assert (await session.get(EngagementPreference, owner)).email_enabled
        assert await session.scalar(select(func.count()).select_from(NotificationWebhookReceipt)) == 1


async def test_receipt_arriving_before_send_result_is_retryable_not_consumed(owner_factory):
    _, factory = owner_factory
    async with factory() as session:
        with pytest.raises(ApiError) as error:
            await delivery.apply_resend_webhook(session, {"type": "email.delivered", "data": {"email_id": "not-yet-saved"}}, "early")
        assert error.value.status == 503
        assert await session.scalar(select(func.count()).select_from(NotificationWebhookReceipt)) == 0


async def test_stop_suppresses_exact_number_and_start_does_not_reenable(owner_factory):
    owner, factory = owner_factory
    _, contact_id, _ = await seed_delivery(owner_factory, channel="sms")
    async with factory() as session:
        await delivery.apply_twilio_webhook(session, {"MessageSid": "SM" + "a" * 32,
            "From": "+15555550123", "OptOutType": "STOP"})
        await session.commit()
        assert (await session.get(NotificationContact, contact_id)).suppressed_at
        assert not (await session.get(EngagementPreference, owner)).sms_enabled


async def test_logout_revokes_only_bound_device_session(owner_factory):
    owner, factory = owner_factory
    auth_ids = [uuid.uuid4(), uuid.uuid4()]
    device_ids = [uuid.uuid4(), uuid.uuid4()]
    async with factory() as session:
        for index in range(2):
            session.add(AuthSession(id=auth_ids[index], user_id=owner, expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
        await session.flush()
        for index in range(2):
            session.add(EngagementPushDevice(id=device_ids[index], user_id=owner, auth_session_id=auth_ids[index],
                endpoint=f"https://fcm.googleapis.com/send/{index}", p256dh_key="test", auth_key="test"))
        await session.flush()
        await delivery.disable_user_devices(session, owner, auth_session_id=auth_ids[0])
        await session.commit()
        assert not (await session.get(EngagementPushDevice, device_ids[0])).enabled
        assert (await session.get(EngagementPushDevice, device_ids[1])).enabled


async def test_queue_deduplicates_same_event_and_keeps_channel_consumption_separate(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch, frequency="immediate")
    row_id, _, ids = await seed_delivery(owner_factory)
    owner, factory = owner_factory
    async with factory() as session:
        await session.delete(await session.get(NotificationDelivery, row_id))
        preference = await session.get(EngagementPreference, owner)
        preference.sms_enabled = preference.push_enabled = False
        assert await delivery.queue_deliveries(session, settings) == 1
        assert await delivery.queue_deliveries(session, settings) == 0
        await session.commit()
        rows = list((await session.scalars(select(NotificationConsumption))).all())
        assert len(rows) == 1 and rows[0].channel == "email" and rows[0].target_key == ""


async def test_two_devices_have_independent_consumption_and_dispatch_bindings(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch, channel="push", frequency="immediate")
    row_id, _, ids = await seed_delivery(owner_factory)
    owner, factory = owner_factory
    async with factory() as session:
        await session.delete(await session.get(NotificationDelivery, row_id))
        preference = await session.get(EngagementPreference, owner)
        preference.email_enabled = preference.sms_enabled = False
        preference.channel_enabled_at = {"push": (delivery.utcnow() - timedelta(days=1)).isoformat() + "Z"}
        for index in range(2):
            auth_id = uuid.uuid4()
            session.add(AuthSession(id=auth_id, user_id=owner, expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
            await session.flush()
            session.add(EngagementPushDevice(id=uuid.uuid4(), user_id=owner, auth_session_id=auth_id,
                endpoint=f"https://fcm.googleapis.com/send/device-{index}", p256dh_key="test", auth_key="test"))
        await session.flush()
        assert await delivery.queue_deliveries(session, settings) == 2
        assert await delivery.queue_deliveries(session, settings) == 0
        await session.commit()
        rows = list((await session.scalars(select(NotificationConsumption))).all())
        assert len(rows) == 2 and len({row.target_key for row in rows}) == 2


@pytest.mark.parametrize("freeze_first_batch", [False, True])
async def test_digest_overflow_consumes_every_event_and_unblocks_later_user(owner_factory, settings, monkeypatch, freeze_first_batch):
    from neos_agent.services import engagement
    owner, factory = owner_factory
    other = uuid.uuid4()
    now = delivery.utcnow()
    event_ids = [uuid.uuid4() for _ in range(84)]

    async def candidates(session, user_id, event):
        return [{"channel": "email", "frequency": "daily" if user_id == owner else "immediate", "reason": "following"}]

    monkeypatch.setattr(engagement, "delivery_candidates", candidates)
    async with factory() as session:
        session.add(User(id=other, display_name="Later recipient", username="later-recipient"))
        await session.flush()
        for recipient in (owner, other):
            session.add(EngagementPreference(user_id=recipient, timezone="UTC", email_enabled=True))
            session.add(NotificationContact(id=uuid.uuid4(), user_id=recipient, channel="email",
                destination=f"{recipient}@example.test",
                destination_hash=delivery.destination_hash("email", f"{recipient}@example.test"), generation=1, verified_at=now))
        for event_id in event_ids:
            session.add(EngagementEvent(id=event_id, event_key=str(event_id), family="governance",
                event_type="proposal.stage", source_kind="proposal", source_id=uuid.uuid4(), occurred_at=now))
        await session.flush()
        for index, event_id in enumerate(event_ids):
            session.add(EngagementInboxItem(id=uuid.uuid4(), user_id=owner if index < 83 else other,
                event_id=event_id, reason_code="following", created_at=now + timedelta(microseconds=index)))
        await session.commit()

    counts = []
    frozen_id = None
    frozen_manifest = None
    for iteration in range(4):
        async with factory() as session:
            counts.append(await delivery.queue_deliveries(session, settings, now=now))
            if freeze_first_batch and iteration == 0:
                frozen = (await session.scalars(select(NotificationDelivery))).one()
                frozen_id, frozen_manifest = frozen.id, list(frozen.event_ids)
                frozen.first_attempt_at = now
                frozen.frozen_payload = {"event_ids": frozen_manifest, "provider_body": {"text": "Frozen"}}
                frozen.state = "retry_wait"
            await session.commit()
    assert counts == [33, 33, 18, 0]
    async with factory() as session:
        rows = list((await session.scalars(select(NotificationDelivery))).all())
        digests = [row for row in rows if row.user_id == owner]
        immediate = [row for row in rows if row.user_id == other]
        assert sorted(len(row.event_ids) for row in digests) == [33, 50]
        if freeze_first_batch:
            frozen = await session.get(NotificationDelivery, frozen_id)
            assert len(frozen_manifest) == 33
            assert frozen.event_ids == frozen_manifest
            assert frozen.frozen_payload == {"event_ids": frozen_manifest, "provider_body": {"text": "Frozen"}}
        assert {row.due_at for row in digests} == {delivery.cadence_due(
            await session.get(EngagementPreference, owner), "daily", now)}
        assert len(immediate) == 1 and immediate[0].due_at == now
        manifest = [event_id for row in rows for event_id in row.event_ids]
        assert len(manifest) == len(set(manifest)) == 84
        assert set(manifest) == {str(event_id) for event_id in event_ids}
        consumption = list((await session.scalars(select(NotificationConsumption))).all())
        assert len(consumption) == 84
        by_id = {row.id: row for row in rows}
        assert all(str(row.event_id) in by_id[row.delivery_id].event_ids for row in consumption)


async def test_signed_webhooks_use_raw_body_and_reject_tampering(owner_factory, settings):
    import base64
    import hashlib
    import hmac
    import json
    import time
    from neos_agent.api.engagement_delivery import resend_webhook
    row_id, _, _ = await seed_delivery(owner_factory)
    _, factory = owner_factory
    async with factory() as session:
        row = await session.get(NotificationDelivery, row_id)
        row.state, row.provider_message_id = "accepted", "signed-email"
        await session.commit()
    raw_key = b"synthetic webhook secret value!!"
    settings.RESEND_WEBHOOK_SECRET = "whsec_" + base64.b64encode(raw_key).decode()
    raw = json.dumps({"type": "email.delivered", "data": {"email_id": "signed-email"}}).encode()
    stamp, receipt = str(int(time.time())), "msg_synthetic"
    signature = base64.b64encode(hmac.new(raw_key, receipt.encode() + b"." + stamp.encode() + b"." + raw, hashlib.sha256).digest()).decode()
    request = SimpleNamespace(body=raw, headers={"svix-id": receipt, "svix-timestamp": stamp, "svix-signature": "v1," + signature},
        app=SimpleNamespace(ctx=SimpleNamespace(settings=settings, db=factory)))
    response = await resend_webhook(request)
    assert response.status == 200
    request.body = raw.replace(b"delivered", b"bounced")
    with pytest.raises(ApiError):
        await resend_webhook(request)
    async with factory() as session:
        assert (await session.get(NotificationDelivery, row_id)).state == "delivered"
        assert await session.scalar(select(func.count()).select_from(NotificationWebhookReceipt)) == 1


async def test_twilio_signature_uses_configured_url_not_untrusted_host(owner_factory, settings):
    from twilio.request_validator import RequestValidator
    from neos_agent.api.engagement_delivery import twilio_webhook
    _, factory = owner_factory
    _, contact_id, _ = await seed_delivery(owner_factory, channel="sms")
    form = {"MessageSid": "SM" + "b" * 32, "From": "+15555550123", "OptOutType": "STOP"}
    url = settings.ENGAGEMENT_API_PUBLIC_URL + "/api/v1/engagement/webhooks/twilio"
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    request = SimpleNamespace(body=b"synthetic", form=form, query_string="", headers={
        "X-Twilio-Signature": validator.compute_signature("https://attacker.test/callback", form), "Host": "attacker.test"},
        app=SimpleNamespace(ctx=SimpleNamespace(settings=settings, db=factory)))
    with pytest.raises(ApiError):
        await twilio_webhook(request)
    request.headers["X-Twilio-Signature"] = validator.compute_signature(url, form)
    assert (await twilio_webhook(request)).status == 200
    async with factory() as session:
        assert (await session.get(NotificationContact, contact_id)).suppressed_at


async def test_unsubscribe_get_only_renders_confirmation(owner_factory, settings):
    from neos_agent.api.engagement_delivery import unsubscribe_preview
    owner, factory = owner_factory
    _, contact_id, _ = await seed_delivery(owner_factory)
    token = delivery.unsubscribe_token(contact_id, settings)
    request = SimpleNamespace(args={"token": token}, app=SimpleNamespace(ctx=SimpleNamespace(settings=settings, db=factory)))
    response = await unsubscribe_preview(request)
    assert response.status == 200 and b"Unsubscribe" in response.body
    async with factory() as session:
        assert (await session.get(EngagementPreference, owner)).email_enabled
        assert not (await session.get(NotificationContact, contact_id)).suppressed_at


async def test_pause_defers_and_source_revocation_suppresses(owner_factory, settings, monkeypatch):
    allow_sources(monkeypatch)
    row_id, _, _ = await seed_delivery(owner_factory)
    owner, factory = owner_factory
    pause = delivery.utcnow() + timedelta(days=1)
    async with factory() as session:
        (await session.get(EngagementPreference, owner)).paused_until = pause
        await session.commit()
    transport = FakeTransport()
    await delivery.dispatch_one(factory, settings, transport)
    assert not transport.sends
    async with factory() as session:
        row = await session.get(NotificationDelivery, row_id)
        assert row.state == "retry_wait" and row.due_at == pause
        (await session.get(EngagementPreference, owner)).paused_until = None
        row.due_at = delivery.utcnow() - timedelta(seconds=1)
        await session.commit()
    from neos_agent.services import engagement
    async def revoked(*args, **kwargs):
        return None
    monkeypatch.setattr(engagement, "event_view", revoked)
    await delivery.dispatch_one(factory, settings, transport)
    assert not transport.sends
    async with factory() as session:
        assert (await session.get(NotificationDelivery, row_id)).state == "suppressed"


async def test_explicit_self_resubscribe_requires_new_verification_and_enable(owner_factory, settings):
    owner, factory = owner_factory
    _, contact_id, _ = await seed_delivery(owner_factory)
    token = delivery.unsubscribe_token(contact_id, settings)
    async with factory() as session:
        await delivery.unsubscribe_contact(session, token, settings)
        await session.commit()
        capability = await delivery.get_capabilities(session, owner, settings)
        assert capability["channels"]["email"]["can_verify"]
    transport = FakeTransport()
    requested = await delivery.request_contact(factory, owner, "email", "member@example.test", settings, transport)
    new_id = uuid.UUID(requested["contact"]["id"])
    assert new_id != contact_id and not requested["contact"]["verified"]
    async with factory() as session:
        assert not (await session.get(EngagementPreference, owner)).email_enabled
        assert not (await session.get(NotificationContact, new_id)).verified_at
        await delivery.unsubscribe_contact(session, token, settings)
        await session.commit()
        assert not (await session.get(NotificationContact, new_id)).suppressed_at


async def test_signed_start_requires_reverification_and_does_not_enable_sms(owner_factory):
    owner, factory = owner_factory
    _, contact_id, _ = await seed_delivery(owner_factory, channel="sms")
    async with factory() as session:
        await delivery.apply_twilio_webhook(session, {"MessageSid": "SM" + "c" * 32,
            "From": "+15555550123", "OptOutType": "STOP"})
        await delivery.apply_twilio_webhook(session, {"MessageSid": "SM" + "d" * 32,
            "From": "+15555550123", "OptOutType": "START"})
        await session.commit()
        contact = await session.get(NotificationContact, contact_id)
        assert not contact.suppressed_at and not contact.verified_at
        assert not (await session.get(EngagementPreference, owner)).sms_enabled
