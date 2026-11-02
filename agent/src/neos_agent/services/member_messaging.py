"""Member messaging shared by REST and operator tools; see services/AGENTS.md."""
from __future__ import annotations

import datetime as dt
import uuid
import logging

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import aliased

from neos_agent.api.errors import ApiError
from neos_agent.api.schemas.messaging import MessageSchema, ParticipantSummary
from neos_agent.db.models import Conversation, ConversationLink, ConversationParticipant, Ecosystem, Member, Message

logger = logging.getLogger(__name__)


async def active_rows(session, user_id):
    return list((await session.scalars(select(Member).where(
        Member.user_id == user_id, Member.current_status == "active",
    ).order_by(Member.created_at, Member.id))).all()) if user_id else []


def listed_participation(selected_ids, active_ids):
    answers = select(ConversationLink.conversation_id).where(ConversationLink.entity_type == "share_need")
    return or_(ConversationParticipant.member_id.in_(selected_ids), and_(
        ConversationParticipant.member_id.in_(active_ids), ConversationParticipant.conversation_id.in_(answers),
    ))


async def participants(session, conversation_id):
    rows = (await session.execute(select(Member.id, Member.display_name, ConversationParticipant.role)
        .join(Member, Member.id == ConversationParticipant.member_id)
        .where(ConversationParticipant.conversation_id == conversation_id))).all()
    return [ParticipantSummary(id=row.id, display_name=row.display_name, role=row.role).model_dump(mode="json") for row in rows]


async def recipient_binding(session, conversation_id, sender_id):
    rows = (await session.execute(select(Member.id, Member.user_id, Member.display_name)
        .join(ConversationParticipant, ConversationParticipant.member_id == Member.id)
        .where(ConversationParticipant.conversation_id == conversation_id, Member.id != sender_id)
        .order_by(Member.id))).all()
    return [{"member_id": str(row.id), "user_id": str(row.user_id), "name": row.display_name} for row in rows]


async def require_participant(session, user_id, conversation_id, *, lock=False):
    own = await active_rows(session, user_id)
    ids = [row.id for row in own]
    query = select(Conversation).where(Conversation.id == conversation_id, Conversation.id.in_(
        select(ConversationParticipant.conversation_id).where(ConversationParticipant.member_id.in_(ids)),
    ))
    conversation = await session.scalar(query.with_for_update() if lock else query)
    if conversation is None:
        raise ApiError(404, "Conversation not found")
    participant_ids = set((await session.scalars(select(ConversationParticipant.member_id).where(
        ConversationParticipant.conversation_id == conversation_id, ConversationParticipant.member_id.in_(ids),
    ))).all())
    actor = next(row for row in own if row.id in participant_ids)
    return conversation, actor, ids


def message_payload(message, sender_name):
    return MessageSchema(id=message.id, sender_id=message.sender_id, sender_name=sender_name, content=message.content,
        message_type=message.message_type, created_at=message.created_at, edited_at=message.edited_at).model_dump(mode="json")


async def mark_read(session, conversation_id, member_ids):
    newest = await session.scalar(select(func.max(Message.created_at)).where(
        Message.conversation_id == conversation_id, Message.deleted_at.is_(None),
    ))
    if newest is not None:
        await session.execute(update(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id, ConversationParticipant.member_id.in_(member_ids),
            or_(ConversationParticipant.last_read_at.is_(None), ConversationParticipant.last_read_at < newest),
        ).values(last_read_at=newest).execution_options(synchronize_session=False))


async def read_thread(session, user_id, conversation_id, *, page=1, limit=50):
    conversation, actor, own_ids = await require_participant(session, user_id, conversation_id)
    limit, page = max(1, min(int(limit), 50)), max(1, int(page))
    sender = aliased(Member)
    rows = (await session.execute(select(Message, sender.display_name).join(sender, sender.id == Message.sender_id)
        .where(Message.conversation_id == conversation_id, Message.deleted_at.is_(None))
        .order_by(Message.created_at.desc(), Message.id.desc()).offset((page - 1) * limit).limit(limit))).all()
    total = await session.scalar(select(func.count(Message.id)).where(
        Message.conversation_id == conversation_id, Message.deleted_at.is_(None))) or 0
    await mark_read(session, conversation_id, own_ids)
    return {"id": str(conversation.id), "type": conversation.type, "title": conversation.title,
        "participants": await participants(session, conversation_id),
        "messages": [message_payload(message, name) for message, name in reversed(rows)], "total_messages": total,
        "page": page, "per_page": limit}


async def listed_ids(session, user_id, ecosystem_ids):
    own = await active_rows(session, user_id)
    scope = {str(value) for value in ecosystem_ids or []}
    selected_ids = [row.id for row in own if str(row.ecosystem_id) in scope]
    ids = [row.id for row in own]
    rows = (await session.execute(select(ConversationParticipant.conversation_id, ConversationParticipant.last_read_at)
        .where(listed_participation(selected_ids, ids)))).all()
    return rows, ids


async def list_threads(session, user_id, ecosystem_ids, *, limit=50, page=1):
    participation, own_ids = await listed_ids(session, user_id, ecosystem_ids)
    ids = list({row.conversation_id for row in participation})
    watermarks = {}
    for row in participation:
        if row.last_read_at and row.last_read_at > watermarks.get(row.conversation_id, dt.datetime.min):
            watermarks[row.conversation_id] = row.last_read_at
    results = []
    for conversation in (await session.scalars(select(Conversation).where(Conversation.id.in_(ids)))).all():
        last = (await session.execute(select(Message.content, Message.created_at).where(
            Message.conversation_id == conversation.id, Message.deleted_at.is_(None),
        ).order_by(Message.created_at.desc(), Message.id.desc()).limit(1))).one_or_none()
        unread = select(func.count(Message.id)).where(Message.conversation_id == conversation.id,
            Message.deleted_at.is_(None), Message.sender_id.notin_(own_ids))
        if watermarks.get(conversation.id):
            unread = unread.where(Message.created_at > watermarks[conversation.id])
        results.append({"id": str(conversation.id), "type": conversation.type, "title": conversation.title,
            "last_message": last.content if last else None, "last_message_at": last.created_at.isoformat() if last else None,
            "unread_count": await session.scalar(unread) or 0, "participants": await participants(session, conversation.id)})
    results.sort(key=lambda row: row["last_message_at"] or "", reverse=True)
    if limit is None:
        return results
    size, number = max(1, min(int(limit), 100)), max(1, int(page))
    return results[(number - 1) * size:number * size]


async def search_thread_messages(session, user_id, ecosystem_ids, query, *, limit=50, page=1):
    if not isinstance(query, str) or not query.strip():
        return []
    participation, _ = await listed_ids(session, user_id, ecosystem_ids)
    sender = aliased(Member)
    escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    size, number = max(1, min(int(limit), 50)), max(1, int(page))
    rows = (await session.execute(select(Message, sender.display_name).join(sender, sender.id == Message.sender_id)
        .where(Message.conversation_id.in_([row.conversation_id for row in participation]), Message.deleted_at.is_(None),
               Message.content.ilike(f"%{escaped}%", escape="\\"))
        .order_by(Message.created_at.desc(), Message.id.desc()).offset((number - 1) * size).limit(size))).all()
    return [{**message_payload(message, name), "conversation_id": str(message.conversation_id)} for message, name in rows]


async def find_recipients(session, user_id, *, query="", limit=50):
    own = await active_rows(session, user_id)
    ecosystems = {row.ecosystem_id for row in own}
    statement = select(Member, Ecosystem.name).join(Ecosystem, Ecosystem.id == Member.ecosystem_id).where(
        Member.ecosystem_id.in_(ecosystems), Member.user_id != user_id, Member.current_status == "active",
    )
    if query:
        escaped = str(query).strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(Member.display_name.ilike(f"%{escaped}%", escape="\\"))
    statement = statement.order_by(Member.display_name, Member.id)
    if limit is not None:
        statement = statement.limit(max(1, min(int(limit), 100)))
    rows = (await session.execute(statement)).all()
    return [{"id": str(row.id), "display_name": row.display_name, "profile": row.profile, "role": row.role,
             "ecosystem_id": str(row.ecosystem_id), "ecosystem_name": name} for row, name in rows]


async def prepare_thread(session, user_id, ecosystem_id, participant_ids, *, type="dm", title=None):
    own = await active_rows(session, user_id)
    creator = next((row for row in own if row.ecosystem_id == ecosystem_id), None)
    if creator is None:
        raise ApiError(403, "An active membership in this ecosystem is required to start a conversation.")
    kind = "dm" if type == "direct" else type
    if kind not in {"dm", "group"}:
        raise ApiError(400, "type must be 'dm' or 'group'")
    try:
        ids = set(uuid.UUID(str(value)) for value in participant_ids) - {row.id for row in own}
    except (TypeError, ValueError):
        raise ApiError(400, "Choose members from the member picker.")
    if not ids or len(ids) > 20 or (kind == "dm" and len(ids) != 1):
        raise ApiError(400, "A direct conversation needs one other member; a group needs 1 to 20.")
    recipients = list((await session.scalars(select(Member).where(Member.id.in_(ids), Member.current_status == "active",
        Member.ecosystem_id.in_({row.ecosystem_id for row in own})))).all())
    if len(recipients) != len(ids):
        raise ApiError(404, "A selected member is unavailable in your ecosystems.")
    if title is not None and (not isinstance(title, str) or len(title) > 255):
        raise ApiError(400, "Keep the conversation title to 255 characters.")
    return creator, sorted(recipients, key=lambda row: str(row.id)), kind, title


async def open_thread(session, prepared):
    creator, recipients, kind, title = prepared
    conversation = Conversation(id=uuid.uuid4(), ecosystem_id=creator.ecosystem_id, type=kind, title=title, created_by=creator.id)
    session.add(conversation)
    await session.flush()
    for member, role in [(creator, "owner"), *((row, "member") for row in recipients)]:
        session.add(ConversationParticipant(id=uuid.uuid4(), conversation_id=conversation.id, member_id=member.id, role=role))
    await session.flush()
    return conversation


async def prepare_message(session, user_id, conversation_id, content):
    if not isinstance(content, str) or not content.strip():
        raise ApiError(400, "content is required")
    if len(content) > 10_000:
        raise ApiError(400, "Message too long (max 10000 chars)")
    conversation, sender, _ = await require_participant(session, user_id, conversation_id, lock=True)
    return conversation, sender, content.strip()


async def post_message(session, prepared):
    conversation, sender, content = prepared
    message = Message(id=uuid.uuid4(), conversation_id=conversation.id, sender_id=sender.id, content=content, message_type="text")
    session.add(message)
    await session.flush()
    await session.refresh(message)
    payload = message_payload(message, sender.display_name)
    ids = list((await session.scalars(select(ConversationParticipant.member_id).where(
        ConversationParticipant.conversation_id == conversation.id))).all())
    session.info.setdefault("member_message_events", []).append((ids, sender.id,
        {"type": "message", "data": {**payload, "conversation_id": str(conversation.id)}}))
    return payload


async def broadcast_committed(session):
    events = getattr(session, "info", {}).pop("member_message_events", [])
    if not events:
        return
    from neos_agent.messaging.connections import connection_manager
    for recipients, sender_id, payload in events:
        try:
            await connection_manager.broadcast_to_participants(recipients, payload, exclude_member_id=sender_id)
        except Exception:
            logger.debug("Messaging delivery notification unavailable", exc_info=True)
