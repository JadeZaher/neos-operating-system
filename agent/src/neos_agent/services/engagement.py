"""Owner-scoped community activity and notification policy."""
from __future__ import annotations

import base64
import json
import re
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError

from neos_agent.api.errors import ApiError
from neos_agent.db.models import (
    Agreement, AuthSession, CircleMembership, Collaboration, Conversation, ConversationParticipant, Domain, Ecosystem,
    Member, Proposal, SharesNeeds, Team, TeamMembership, User,
)
from neos_agent.db.models.engagement import (
    EngagementEvent, EngagementInboxItem, EngagementPreference, EngagementPushDevice,
    EngagementSubscription, NotificationContact,
)

CHANNELS = frozenset(("in_app", "email", "push", "sms"))
FREQUENCIES = ("immediate", "daily", "weekly")
FAMILIES = frozenset(("governance", "opportunities", "collaboration", "messages", "community"))
SCOPE_MODELS = {"ecosystem": Ecosystem, "domain": Domain, "team": Team, "proposal": Proposal,
                "agreement": Agreement, "share": SharesNeeds, "collaboration": Collaboration,
                "conversation": Conversation}
REASONS = {"community": "You belong to this community.", "follow": "You follow this community or item.",
           "direct": "You participate in this conversation."}


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def stamp(value):
    return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if value else None


def as_uuid(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ApiError(400, "A valid resource identifier is required") from None


def parse_time(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ApiError(400, "Use an ISO8601 date with a time zone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError()
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        raise ApiError(400, "Use an ISO8601 date with a time zone") from None


def cursor_for(row, field="created_at"):
    body = json.dumps([stamp(getattr(row, field)), str(row.id)], separators=(",", ":"))
    return base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")


def decode_cursor(value):
    if not value:
        return None
    try:
        if len(value) > 200:
            raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))
        if not isinstance(data, list) or len(data) != 2:
            raise ValueError()
        moment = parse_time(data[0])
        if moment is None:
            raise ValueError()
        return moment, as_uuid(data[1])
    except (ValueError, TypeError, UnicodeError, ApiError):
        raise ApiError(400, "Invalid page cursor") from None


def after_cursor(statement, model, cursor, field="created_at"):
    decoded = decode_cursor(cursor)
    if decoded:
        moment, ident = decoded
        column = getattr(model, field)
        statement = statement.where(or_(column < moment, and_(column == moment, model.id < ident)))
    return statement


async def active_members(session, user_id):
    user = await session.get(User, user_id)
    if user is None or user.disabled_at is not None:
        return []
    return list((await session.scalars(select(Member).where(
        Member.user_id == user_id, Member.current_status == "active"))).all())


def ecosystem_ids(record):
    values = [getattr(record, "ecosystem_id", None), *(getattr(record, "shared_ecosystem_ids", None) or [])]
    result = set()
    for value in values:
        try:
            if value:
                result.add(uuid.UUID(str(value)))
        except (ValueError, TypeError):
            continue
    return result


async def scope_record(session, user_id, kind, ident):
    if not isinstance(kind, str) or kind not in SCOPE_MODELS:
        raise ApiError(400, "Unsupported subscription scope")
    user = await session.get(User, user_id)
    if user is None or user.disabled_at is not None:
        raise ApiError(404, "Resource not found")
    own = await active_members(session, user_id)
    own_ids, ecosystems = {row.id for row in own}, {row.ecosystem_id for row in own}
    record = await session.get(SCOPE_MODELS[kind], ident)
    if record is None:
        raise ApiError(404, "Resource not found")
    if kind == "share":
        from neos_agent.services.exchange import load_viewer, load_visible
        record = await load_visible(session, await load_viewer(session, user_id), ident)
        if record.hidden_at is not None or record.status == "withdrawn":
            raise ApiError(404, "Resource not found")
    elif kind == "collaboration":
        from neos_agent.services.exchange import load_viewer, load_collaboration
        record, _ = await load_collaboration(session, await load_viewer(session, user_id), ident)
    elif kind == "conversation":
        from neos_agent.services.member_messaging import require_participant
        record, _, _ = await require_participant(session, user_id, ident)
    elif kind == "ecosystem":
        if ident not in ecosystems or record.status != "active":
            raise ApiError(404, "Resource not found")
    elif not ecosystem_ids(record).intersection(ecosystems):
        raise ApiError(404, "Resource not found")
    if kind == "domain":
        participant = await session.scalar(select(CircleMembership.id).where(
            CircleMembership.domain_id == ident, CircleMembership.member_id.in_(own_ids),
            CircleMembership.status == "active").limit(1))
        if record.status != "active" or (not participant and record.steward_id not in own_ids):
            raise ApiError(404, "Resource not found")
    if kind == "team":
        participant = await session.scalar(select(TeamMembership.id).where(
            TeamMembership.team_id == ident, TeamMembership.member_id.in_(own_ids)).limit(1))
        if not record.is_active or not participant:
            raise ApiError(404, "Resource not found")
    return record


async def event_scopes(session, event):
    model = SCOPE_MODELS.get(event.source_kind)
    record = await session.get(model, event.source_id) if model else None
    if record is None:
        return set()
    scopes = {(event.source_kind, event.source_id)}
    ecosystems = ecosystem_ids(record)
    if event.source_kind == "ecosystem":
        ecosystems.add(record.id)
    if event.source_kind == "collaboration":
        for ident in (record.source_domain_id, record.target_domain_id):
            domain = await session.get(Domain, ident)
            if domain:
                scopes.add(("domain", domain.id))
                ecosystems.update(ecosystem_ids(domain))
    if event.source_kind == "conversation":
        ecosystems.update((await session.scalars(select(Member.ecosystem_id).join(
            ConversationParticipant, ConversationParticipant.member_id == Member.id).where(
            ConversationParticipant.conversation_id == record.id, Member.current_status == "active"))).all())
    domain_id = getattr(record, "domain_id", None) if event.source_kind == "share" else None
    if domain_id:
        scopes.add(("domain", domain_id))
    # A producer can bind a real structured domain/team; never infer from human labels.
    for kind, ident in (("domain", event.domain_id), ("team", event.team_id)):
        if ident:
            scoped = await session.get(SCOPE_MODELS[kind], ident)
            if scoped and (ecosystem_ids(scoped) & ecosystems):
                scopes.add((kind, ident))
    scopes.update(("ecosystem", ident) for ident in ecosystems)
    return scopes


def source_label(kind, record):
    if kind == "conversation":
        return record.title or "Conversation"
    return (getattr(record, "title", None) or getattr(record, "name", None)
            or getattr(record, "domain_id", None) or "Community update")


def source_url(kind, ident):
    if kind == "share":
        return "/discover?post=" + str(ident)
    if kind == "conversation":
        return "/messaging?conversation=" + str(ident)
    if kind == "team":
        return "/teams"
    paths = {"ecosystem": "/ethos/", "domain": "/domains/", "team": "/teams/",
             "proposal": "/proposals/", "agreement": "/agreements/",
             "share": "/discover/shares-needs/", "collaboration": "/discover/collaborations/",
             "conversation": "/messaging/"}
    return paths[kind] + str(ident)


async def event_view(session, user_id, event, *, community=False):
    if community and (event.family == "messages" or event.audience_user_ids is not None):
        return None
    if event.audience_user_ids is not None and str(user_id) not in event.audience_user_ids:
        return None
    try:
        record = await scope_record(session, user_id, event.source_kind, event.source_id)
    except ApiError:
        return None
    scopes = await event_scopes(session, event)
    own = await active_members(session, user_id)
    accessible = {row.ecosystem_id for row in own}
    contexts = sorted((ident for kind, ident in scopes if kind == "ecosystem" and ident in accessible), key=str)
    context = event.ecosystem_id if event.ecosystem_id in contexts else (contexts[0] if contexts else None)
    eco = await session.get(Ecosystem, context) if context else None
    summary = {"governance": "A governance process changed.",
               "opportunities": "An opportunity in your community changed.",
               "collaboration": "A collaboration changed.",
               "messages": "You have a new conversation update.",
               "community": "Participation in this group changed."}.get(event.family, "Community activity")
    return {"id": str(event.id), "event_type": event.event_type, "family": event.family,
            "source_kind": event.source_kind, "source_id": str(event.source_id),
            "ecosystem_id": str(context) if context else None, "ecosystem_name": eco.name if eco else None,
            "title": "Conversation update" if event.family == "messages" else source_label(event.source_kind, record), "summary": summary,
            "url": source_url(event.source_kind, event.source_id), "occurred_at": stamp(event.occurred_at)}


async def record_event(session, *, event_key, family, event_type, source_kind, source_id,
                       ecosystem_id=None, actor_user_id=None, domain_id=None, team_id=None,
                       audience_user_ids=None):
    if family not in FAMILIES or source_kind not in SCOPE_MODELS or not event_key or len(event_key) > 255:
        raise ValueError("Invalid engagement event")
    if family == "messages" and (source_kind != "conversation" or audience_user_ids is None):
        raise ValueError("Message events require a private recipient audience")
    existing = await session.scalar(select(EngagementEvent).where(EngagementEvent.event_key == event_key))
    if existing:
        return existing
    values = dict(id=uuid.uuid4(), event_key=event_key, family=family, event_type=event_type,
        source_kind=source_kind, source_id=source_id, ecosystem_id=ecosystem_id, actor_user_id=actor_user_id,
        domain_id=domain_id, team_id=team_id,
        audience_user_ids=sorted({str(value) for value in audience_user_ids}) if audience_user_ids is not None else None,
        occurred_at=utcnow(), created_at=utcnow(), fanout_complete=False)
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    insert = pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
    await session.execute(insert(EngagementEvent).values(**values).on_conflict_do_nothing(index_elements=["event_key"]))
    return await session.scalar(select(EngagementEvent).where(EngagementEvent.event_key == event_key))


async def get_preference(session, user_id, *, create=False):
    row = await session.get(EngagementPreference, user_id)
    if row is None and create:
        row = EngagementPreference(user_id=user_id, timezone="UTC", email_enabled=False, push_enabled=False,
                                   sms_enabled=False, direct_messages=True, channel_enabled_at={})
        try:
            async with session.begin_nested():
                session.add(row)
                await session.flush()
        except IntegrityError:
            row = await session.get(EngagementPreference, user_id, populate_existing=True)
    return row


def preference_payload(row):
    return {"timezone": row.timezone if row else "UTC", "quiet_start": row.quiet_start if row else None,
            "quiet_end": row.quiet_end if row else None, "paused_until": stamp(row.paused_until) if row else None,
            **{channel + "_enabled": bool(getattr(row, channel + "_enabled", False)) for channel in ("email", "push", "sms")},
            "direct_messages": bool(row.direct_messages) if row else True}


async def update_preference(session, user_id, data, capabilities):
    if not isinstance(data, dict) or set(data) - set(preference_payload(None)):
        raise ApiError(400, "Unknown preference fields")
    for key in ("email_enabled", "push_enabled", "sms_enabled", "direct_messages"):
        if key in data and type(data[key]) is not bool:
            raise ApiError(400, "Channel preferences must be true or false")
    row = await get_preference(session, user_id, create=True)
    timezone_name = data.get("timezone", row.timezone)
    try:
        if not isinstance(timezone_name, str) or len(timezone_name) > 80:
            raise ValueError()
        ZoneInfo(timezone_name)
    except (ValueError, ZoneInfoNotFoundError):
        raise ApiError(400, "Choose a valid time zone") from None
    quiet = [data.get(key, getattr(row, key)) for key in ("quiet_start", "quiet_end")]
    if bool(quiet[0]) != bool(quiet[1]) or any(value is not None and
       (not isinstance(value, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value)) for value in quiet):
        raise ApiError(400, "Quiet hours require a start and end in HH:MM")
    for channel in ("email", "push", "sms"):
        key = channel + "_enabled"
        if data.get(key) is True and not getattr(row, key):
            if capabilities.get("channels", {}).get(channel, {}).get("state") != "ready":
                raise ApiError(409, "Configure and verify this channel before enabling it")
            row.channel_enabled_at = {**(row.channel_enabled_at or {}), channel: stamp(utcnow())}
    row.timezone, row.quiet_start, row.quiet_end = timezone_name, *quiet
    for key, value in data.items():
        setattr(row, key, parse_time(value) if key == "paused_until" else value)
    await session.flush()
    return preference_payload(row)


async def matching_subscriptions(session, user_id, event):
    scopes = await event_scopes(session, event)
    rows = (await session.scalars(select(EngagementSubscription).where(
        EngagementSubscription.user_id == user_id))).all()
    matched = []
    for row in rows:
        if (row.scope_kind, row.scope_id) not in scopes:
            continue
        try:
            await scope_record(session, user_id, row.scope_kind, row.scope_id)
        except ApiError:
            continue
        matched.append(row)
    return matched


async def delivery_candidates(session, user_id, event):
    if await event_view(session, user_id, event) is None:
        return []
    preference = await get_preference(session, user_id)
    matches = await matching_subscriptions(session, user_id, event)
    if any(row.muted for row in matches):
        return []
    if event.actor_user_id == user_id:
        return []
    is_direct = event.family == "messages"
    qualified = [row for row in matches if event.family in (row.event_families or [])]
    if matches:
        visible = any("in_app" in (row.channels or []) for row in qualified)
    elif is_direct:
        visible = event.audience_user_ids is not None and str(user_id) in event.audience_user_ids
    else:
        scopes = await event_scopes(session, event)
        own = await active_members(session, user_id)
        visible = any(("ecosystem", row.ecosystem_id) in scopes for row in own)
    if is_direct and preference is not None and not preference.direct_messages:
        visible = False
    candidates = ([{"channel": "in_app", "frequency": "immediate",
        "reason": "direct" if is_direct else "follow" if matches else "community"}] if visible else [])
    if preference is None:
        return candidates
    for channel in ("email", "push", "sms"):
        enabled = (preference.channel_enabled_at or {}).get(channel)
        if not getattr(preference, channel + "_enabled") or not enabled or event.occurred_at < parse_time(enabled):
            continue
        matching = [row for row in qualified if channel in (row.channels or []) and
                    (row.created_at is None or event.occurred_at >= row.created_at)]
        if not matching:
            continue
        if channel == "push":
            eligible = await session.scalar(select(EngagementPushDevice.id).join(
                AuthSession, AuthSession.id == EngagementPushDevice.auth_session_id).where(
                EngagementPushDevice.user_id == user_id, EngagementPushDevice.enabled.is_(True),
                AuthSession.user_id == user_id, AuthSession.expires_at > datetime.now(timezone.utc)).limit(1))
        else:
            eligible = await session.scalar(select(NotificationContact.id).where(
                NotificationContact.user_id == user_id, NotificationContact.channel == channel,
                NotificationContact.revoked_at.is_(None), NotificationContact.suppressed_at.is_(None),
                NotificationContact.verified_at.is_not(None)).limit(1))
        if eligible:
            frequency = min((row.frequency for row in matching), key=FREQUENCIES.index)
            candidates.append({"channel": channel, "frequency": frequency, "reason": "follow"})
    return candidates


async def fanout_pending(session, *, limit=50):
    events = (await session.scalars(select(EngagementEvent).where(
        EngagementEvent.fanout_complete.is_(False)).order_by(EngagementEvent.created_at, EngagementEvent.id)
        .limit(min(max(limit, 1), 50)).with_for_update(skip_locked=True))).all()
    count = 0
    for event in events:
        statement = select(User.id).where(User.disabled_at.is_(None))
        if event.audience_user_ids is not None:
            statement = statement.where(User.id.in_([as_uuid(value) for value in event.audience_user_ids]))
        else:
            scopes = await event_scopes(session, event)
            ecos = [ident for kind, ident in scopes if kind == "ecosystem"]
            scope_filters = [and_(EngagementSubscription.scope_kind == kind,
                                 EngagementSubscription.scope_id == ident) for kind, ident in scopes]
            followers = select(EngagementSubscription.user_id).where(or_(*scope_filters)) if scope_filters else select(User.id).where(False)
            statement = statement.where(or_(User.id.in_(select(Member.user_id).where(
                Member.ecosystem_id.in_(ecos), Member.current_status == "active")), User.id.in_(followers)))
        if event.fanout_cursor:
            statement = statement.where(User.id > as_uuid(event.fanout_cursor))
        recipients = list((await session.scalars(statement.order_by(User.id).limit(101))).all())
        for user_id in recipients[:100]:
            candidates = await delivery_candidates(session, user_id, event)
            in_app = next((item for item in candidates if item["channel"] == "in_app"), None)
            if candidates:
                try:
                    async with session.begin_nested():
                        session.add(EngagementInboxItem(user_id=user_id, event_id=event.id,
                            reason_code=(in_app or candidates[0])["reason"], in_app_visible=in_app is not None,
                            created_at=event.occurred_at))
                        await session.flush()
                        count += 1
                except IntegrityError:
                    pass
            event.fanout_cursor = str(user_id)
        event.fanout_complete = len(recipients) <= 100
    await session.flush()
    return {"events": len(events), "inbox_items": count}


async def subscription_payload(session, user_id, row):
    try:
        record = await scope_record(session, user_id, row.scope_kind, row.scope_id)
    except ApiError:
        return None
    return {"id": str(row.id), "scope_kind": row.scope_kind, "scope_id": str(row.scope_id),
            "scope_label": source_label(row.scope_kind, record), "event_families": row.event_families,
            "channels": row.channels, "frequency": row.frequency, "muted": row.muted}


async def save_subscription(session, user_id, data):
    allowed = {"scope_kind", "scope_id", "event_families", "channels", "frequency", "muted"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ApiError(400, "Unknown subscription fields")
    kind, ident = data.get("scope_kind"), as_uuid(data.get("scope_id"))
    await scope_record(session, user_id, kind, ident)
    families, channels = data.get("event_families", []), data.get("channels", [])
    muted, frequency = data.get("muted", False), data.get("frequency", "daily")
    if type(muted) is not bool or frequency not in FREQUENCIES:
        raise ApiError(400, "Invalid subscription frequency or mute setting")
    if not isinstance(families, list) or not all(isinstance(x, str) for x in families) or set(families) - FAMILIES:
        raise ApiError(400, "Choose supported event categories")
    if not isinstance(channels, list) or not all(isinstance(x, str) for x in channels) or set(channels) - CHANNELS:
        raise ApiError(400, "Choose supported delivery channels")
    if not muted and (not families or not channels):
        raise ApiError(400, "Choose at least one category and channel")
    await session.execute(select(User.id).where(User.id == user_id).with_for_update())
    row = await session.scalar(select(EngagementSubscription).where(EngagementSubscription.user_id == user_id,
        EngagementSubscription.scope_kind == kind, EngagementSubscription.scope_id == ident).with_for_update())
    if row is None:
        count = await session.scalar(select(func.count(EngagementSubscription.id)).where(
            EngagementSubscription.user_id == user_id))
        if count >= 100:
            raise ApiError(409, "Manage an existing subscription before adding another")
        row = EngagementSubscription(user_id=user_id, scope_kind=kind, scope_id=ident,
                                     created_at=utcnow(), updated_at=utcnow())
        try:
            async with session.begin_nested():
                row.event_families, row.channels, row.frequency, row.muted = sorted(set(families)), sorted(set(channels)), frequency, muted
                session.add(row)
                await session.flush()
        except IntegrityError:
            row = await session.scalar(select(EngagementSubscription).where(EngagementSubscription.user_id == user_id,
                EngagementSubscription.scope_kind == kind, EngagementSubscription.scope_id == ident).with_for_update())
    if (set(families) - set(row.event_families or []) or set(channels) - set(row.channels or [])
            or (row.muted and not muted)):
        # Conservative consent boundary: widening resets activation for this entire follow.
        row.created_at = utcnow()
    row.event_families, row.channels, row.frequency, row.muted = sorted(set(families)), sorted(set(channels)), frequency, muted
    await session.flush()
    return await subscription_payload(session, user_id, row)


async def scope_options(session, user_id, kind, query="", ident=None):
    if not isinstance(kind, str) or kind not in SCOPE_MODELS:
        raise ApiError(400, "Unsupported subscription scope")
    model, query = SCOPE_MODELS[kind], query.strip()[:100]
    if ident:
        record = await scope_record(session, user_id, kind, as_uuid(ident))
        return [{"scope_kind": kind, "scope_id": str(record.id), "label": source_label(kind, record),
                 "ecosystem_id": str(getattr(record, "ecosystem_id", "")) or None}]
    label = getattr(model, "title", None)
    if label is None:
        label = getattr(model, "name", None)
    statement = select(model).order_by(model.id)
    own = await active_members(session, user_id)
    own_ids, eco_ids = [row.id for row in own], [row.ecosystem_id for row in own]
    if kind == "ecosystem":
        statement = statement.where(model.id.in_(eco_ids))
    elif kind in ("proposal", "agreement", "domain", "team"):
        from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
        statement = restrict_to_ecosystems(statement, model, eco_ids)
    elif kind == "conversation":
        statement = statement.where(model.id.in_(select(ConversationParticipant.conversation_id).where(
            ConversationParticipant.member_id.in_(own_ids))))
    elif kind == "share":
        from neos_agent.services.exchange import load_viewer, visible_clause
        statement = statement.where(visible_clause(await load_viewer(session, user_id)))
    elif kind == "collaboration":
        from neos_agent.services.exchange import load_viewer, collaboration_visible_clause
        statement = statement.where(collaboration_visible_clause(await load_viewer(session, user_id)))
    if query and label is not None:
        safe = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(label.ilike("%" + safe + "%", escape="\\"))
    items = []
    # Bound discovery scans while advancing through inaccessible candidates.
    for record in (await session.scalars(statement.limit(500))).all():
        try:
            await scope_record(session, user_id, kind, record.id)
        except ApiError:
            continue
        items.append({"scope_kind": kind, "scope_id": str(record.id), "label": source_label(kind, record),
                      "ecosystem_id": str(getattr(record, "ecosystem_id", "")) or None})
        if len(items) == 30:
            break
    return items


async def activity_page(session, user_id, *, ecosystem_id=None, cursor=None, limit=20):
    statement = select(EngagementEvent).where(EngagementEvent.family != "messages",
        EngagementEvent.audience_user_ids.is_(None))
    statement = after_cursor(statement, EngagementEvent, cursor)
    rows = (await session.scalars(statement.order_by(
        EngagementEvent.created_at.desc(), EngagementEvent.id.desc()).limit(500))).all()
    items, last = [], None
    for row in rows:
        last = row
        if ecosystem_id and ("ecosystem", ecosystem_id) not in await event_scopes(session, row):
            continue
        payload = await event_view(session, user_id, row, community=True)
        if payload:
            items.append(payload)
        if len(items) >= limit:
            break
    return {"items": items, "next_cursor": cursor_for(last) if last and (len(items) == limit or len(rows) == 500) else None}


async def inbox_page(session, user_id, *, unread=False, cursor=None, limit=20):
    statement = select(EngagementInboxItem).where(EngagementInboxItem.user_id == user_id,
                                                EngagementInboxItem.in_app_visible.is_(True))
    if unread:
        statement = statement.where(EngagementInboxItem.read_at.is_(None))
    statement = after_cursor(statement, EngagementInboxItem, cursor)
    rows = (await session.scalars(statement.order_by(
        EngagementInboxItem.created_at.desc(), EngagementInboxItem.id.desc()).limit(500))).all()
    items, last = [], None
    for row in rows:
        last = row
        event = await session.get(EngagementEvent, row.event_id)
        payload = await event_view(session, user_id, event) if event else None
        if payload:
            items.append({**payload, "inbox_id": str(row.id), "read_at": stamp(row.read_at),
                          "reason": REASONS.get(row.reason_code, "You follow this item.")})
        if len(items) >= limit:
            break
    unread_rows = (await session.scalars(select(EngagementInboxItem).where(
        EngagementInboxItem.user_id == user_id, EngagementInboxItem.in_app_visible.is_(True),
        EngagementInboxItem.read_at.is_(None))
        .order_by(EngagementInboxItem.created_at.desc()).limit(1001))).all()
    count = 0
    for row in unread_rows[:1000]:
        event = await session.get(EngagementEvent, row.event_id)
        if event and await event_view(session, user_id, event):
            count += 1
    return {"items": items, "next_cursor": cursor_for(last) if last and (len(items) == limit or len(rows) == 500) else None,
            "unread_count": count, "unread_count_is_lower_bound": len(unread_rows) > 1000}


async def mark_inbox(session, user_id, identifiers, *, read=True):
    rows = (await session.scalars(select(EngagementInboxItem).where(
        EngagementInboxItem.user_id == user_id, EngagementInboxItem.in_app_visible.is_(True),
        EngagementInboxItem.id.in_(identifiers)).with_for_update())).all()
    if len(rows) != len(set(identifiers)):
        raise ApiError(404, "Update not found")
    results = []
    for row in rows:
        event = await session.get(EngagementEvent, row.event_id)
        payload = await event_view(session, user_id, event) if event else None
        if payload is None:
            raise ApiError(404, "Update not found")
        row.read_at = utcnow() if read else None
        results.append({**payload, "inbox_id": str(row.id), "read_at": stamp(row.read_at),
                        "reason": REASONS.get(row.reason_code, "You follow this item.")})
    await session.flush()
    return results
