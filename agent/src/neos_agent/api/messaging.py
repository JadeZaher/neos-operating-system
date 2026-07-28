"""JSON API blueprint for messaging.

Blueprint: messaging_api_bp, url_prefix="/api/v1/messaging"

Provides REST endpoints for initial data loading of conversations and messages.
Real-time delivery is handled by the WebSocket at /messaging/ws.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid
import datetime as _dt

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from neos_agent.api.schemas.messaging import (
    ConversationDetailSchema, ConversationSummary, CreateConversationRequest,
    MemberPickerItem, MessageSchema, ParticipantSummary,
)
from neos_agent.db.models import (
    Conversation,
    ConversationParticipant,
    Member,
    Message,
)
from neos_agent.api.helpers import require_auth, get_ecosystem_ids

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

messaging_api_bp = Blueprint("messaging_api", url_prefix="/api/v1/messaging")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



async def _get_current_member_id(session, member_or_did, eco_ids: list[uuid.UUID]) -> uuid.UUID | None:
    """Resolve the authenticated member to a member id within the active ecosystems."""
    ids = await _get_current_member_ids(session, member_or_did, eco_ids)
    return ids[0] if ids else None


async def _get_current_member_ids(session, member_or_did, eco_ids: list[uuid.UUID]) -> list[uuid.UUID]:
    """Resolve the authenticated member to ALL their member ids within the given ecosystems.

    A user holds one Member row per ecosystem. Messaging must operate across all of
    them — resolving a single arbitrary row hides conversations and people from the
    user's other ecosystems.
    """
    from neos_agent.db.models import User
    if isinstance(member_or_did, str):
        if not member_or_did:
            return []
        # DID string — resolve via User table
        user_result = await session.execute(
            select(User.id).where(User.did == member_or_did).limit(1)
        )
        user_id = user_result.scalar_one_or_none()
        if not user_id:
            return []
        stmt = select(Member.id).where(Member.user_id == user_id)
    elif hasattr(member_or_did, "user_id") and member_or_did.user_id:
        stmt = select(Member.id).where(Member.user_id == member_or_did.user_id)
    elif hasattr(member_or_did, "id"):
        # No user_id — look up by member ID directly
        return [member_or_did.id]
    else:
        return []
    if eco_ids:
        stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _load_participants(session, conversation_id: uuid.UUID) -> list[ParticipantSummary]:
    """Load participants for a conversation with member display names."""
    stmt = (
        select(Member.id, Member.display_name, ConversationParticipant.role)
        .join(Member, Member.id == ConversationParticipant.member_id)
        .where(ConversationParticipant.conversation_id == conversation_id)
    )
    result = await session.execute(stmt)
    return [
        ParticipantSummary(id=row.id, display_name=row.display_name, role=row.role)
        for row in result.all()
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@messaging_api_bp.get("/conversations")
async def list_conversations(request: Request):
    """GET /api/v1/messaging/conversations -- List conversations for current member.

    Returns JSON: {"conversations": [ConversationSummary]}
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_ids = await _get_current_member_ids(session, member, eco_ids)
        if not member_ids:
            return json({"conversations": []})

        # Get conversation ids for ALL of the user's member rows (one per ecosystem)
        cp_stmt = (
            select(ConversationParticipant.conversation_id, ConversationParticipant.last_read_at)
            .where(ConversationParticipant.member_id.in_(member_ids))
        )
        cp_result = await session.execute(cp_stmt)
        participant_rows = cp_result.all()

        if not participant_rows:
            return json({"conversations": []})

        conv_ids = list({row.conversation_id for row in participant_rows})
        # Own read state per conversation: most recent last_read across own member rows
        last_read_map: dict[uuid.UUID, _dt.datetime] = {}
        for row in participant_rows:
            if row.last_read_at is None:
                continue
            prev = last_read_map.get(row.conversation_id)
            if prev is None or row.last_read_at > prev:
                last_read_map[row.conversation_id] = row.last_read_at

        # Load conversations
        conv_stmt = (
            select(Conversation)
            .where(Conversation.id.in_(conv_ids))
        )
        conv_result = await session.execute(conv_stmt)
        conversations = list(conv_result.scalars().all())

        # For each conversation: last message, unread count, participants
        summaries = []
        for conv in conversations:
            # Last message
            last_msg_stmt = (
                select(Message.content, Message.created_at)
                .where(Message.conversation_id == conv.id)
                .where(Message.deleted_at.is_(None))
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_msg_result = await session.execute(last_msg_stmt)
            last_msg = last_msg_result.one_or_none()

            # Unread count (exclude messages sent from any of the user's own member rows)
            last_read = last_read_map.get(conv.id)
            unread_stmt = (
                select(func.count(Message.id))
                .where(Message.conversation_id == conv.id)
                .where(Message.deleted_at.is_(None))
                .where(Message.sender_id.notin_(member_ids))
            )
            if last_read is not None:
                unread_stmt = unread_stmt.where(Message.created_at > last_read)
            unread_result = await session.execute(unread_stmt)
            unread_count = unread_result.scalar() or 0

            # Participants
            participants = await _load_participants(session, conv.id)

            summaries.append(ConversationSummary(
                id=conv.id,
                type=conv.type,
                title=conv.title,
                last_message=last_msg.content if last_msg else None,
                last_message_at=last_msg.created_at if last_msg else None,
                unread_count=unread_count,
                participants=participants,
            ))

        # Sort by last message timestamp desc (conversations with no messages last)
        summaries.sort(
            key=lambda s: s.last_message_at or _dt.datetime.min,
            reverse=True,
        )

    return json({
        "conversations": [s.model_dump(mode="json") for s in summaries],
    })


@messaging_api_bp.get("/conversations/<conversation_id:uuid>")
async def get_conversation(request: Request, conversation_id: uuid.UUID):
    """GET /api/v1/messaging/conversations/:id -- Conversation detail with recent messages.

    Returns JSON: ConversationDetailSchema
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_ids = await _get_current_member_ids(session, member, eco_ids)
        if not member_ids:
            return json({"error": "Member not found"}, status=404)

        # Verify participation via any of the user's member rows
        participant_check = await session.execute(
            select(ConversationParticipant.id)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .where(ConversationParticipant.member_id.in_(member_ids))
        )
        if participant_check.scalar_one_or_none() is None:
            return json({"error": "Conversation not found"}, status=404)

        # Load conversation
        conv = await session.get(Conversation, conversation_id)
        if conv is None:
            return json({"error": "Conversation not found"}, status=404)

        # Participants
        participants = await _load_participants(session, conversation_id)

        # Total message count
        total_stmt = (
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
            .where(Message.deleted_at.is_(None))
        )
        total = (await session.execute(total_stmt)).scalar() or 0

        # Last 50 messages with sender names
        SenderMember = aliased(Member)
        msg_stmt = (
            select(Message, SenderMember.display_name)
            .join(SenderMember, SenderMember.id == Message.sender_id)
            .where(Message.conversation_id == conversation_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .limit(50)
        )
        msg_result = await session.execute(msg_stmt)
        msg_rows = msg_result.all()

        messages = [
            MessageSchema(
                id=msg.id,
                sender_id=msg.sender_id,
                sender_name=sender_name,
                content=msg.content,
                message_type=msg.message_type,
                created_at=msg.created_at,
                edited_at=msg.edited_at,
            )
            for msg, sender_name in reversed(msg_rows)  # chronological order
        ]

        detail = ConversationDetailSchema(
            id=conv.id,
            type=conv.type,
            title=conv.title,
            participants=participants,
            messages=messages,
            total_messages=total,
        )

    return json(detail.model_dump(mode="json"))


@messaging_api_bp.post("/conversations")
async def create_conversation(request: Request):
    """POST /api/v1/messaging/conversations -- Create a conversation.

    Accepts JSON: CreateConversationRequest
    Returns JSON: ConversationDetailSchema with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = CreateConversationRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    # Normalize type: accept "direct" as alias for "dm"
    if create_req.type == "direct":
        create_req.type = "dm"
    if create_req.type not in ("dm", "group"):
        return json({"error": "type must be 'dm' or 'group'"}, status=400)

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member, eco_ids)
        if member_id is None:
            return json({"error": "Member not found"}, status=404)

        # Create conversation
        conv = Conversation(
            id=uuid.uuid4(),
            ecosystem_id=eco_ids[0] if eco_ids else member.ecosystem_id,
            type=create_req.type,
            title=create_req.title,
            created_by=member_id,
        )
        session.add(conv)
        await session.flush()

        # Add creator as owner
        session.add(ConversationParticipant(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            member_id=member_id,
            role="owner",
        ))

        # Add other participants
        for pid in create_req.participant_ids:
            if pid == member_id:
                continue  # skip if creator included themselves
            session.add(ConversationParticipant(
                id=uuid.uuid4(),
                conversation_id=conv.id,
                member_id=pid,
                role="member",
            ))

        await session.commit()

        # Build response
        participants = await _load_participants(session, conv.id)

        detail = ConversationDetailSchema(
            id=conv.id,
            type=conv.type,
            title=conv.title,
            participants=participants,
            messages=[],
            total_messages=0,
        )

    return json(detail.model_dump(mode="json"), status=201)


@messaging_api_bp.post("/conversations/<conversation_id:uuid>/messages")
async def send_message(request: Request, conversation_id: uuid.UUID):
    """POST /api/v1/messaging/conversations/:id/messages -- Send a message (REST fallback).

    Accepts JSON: {"content": "..."}
    Returns JSON: MessageSchema with 201 status.

    This is the REST alternative to WebSocket message sending, ensuring
    messages can be sent even when WebSocket connections fail.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    content = (body.get("content") or "").strip()
    if not content:
        return json({"error": "content is required"}, status=400)
    if len(content) > 10_000:
        return json({"error": "Message too long (max 10000 chars)"}, status=400)

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_ids = await _get_current_member_ids(session, member, eco_ids)
        if not member_ids:
            return json({"error": "Member not found"}, status=404)

        # Verify participation and resolve WHICH of the user's member rows is in this conversation
        participant_row = (await session.execute(
            select(ConversationParticipant.member_id)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .where(ConversationParticipant.member_id.in_(member_ids))
        )).first()
        if participant_row is None:
            return json({"error": "Not a participant"}, status=403)
        member_id = participant_row.member_id

        # Persist message
        msg = Message(
            conversation_id=conversation_id,
            sender_id=member_id,
            content=content,
            message_type="text",
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        # Resolve sender display name
        sender_result = await session.execute(
            select(Member.display_name).where(Member.id == member_id)
        )
        sender_name = sender_result.scalar() or "Unknown"

        # Broadcast to connected WebSocket clients
        try:
            from neos_agent.messaging.connections import connection_manager
            participant_ids_result = await session.execute(
                select(ConversationParticipant.member_id)
                .where(ConversationParticipant.conversation_id == conversation_id)
            )
            participant_ids = list(participant_ids_result.scalars().all())

            payload = {
                "type": "message",
                "data": {
                    "id": str(msg.id),
                    "conversation_id": str(conversation_id),
                    "sender_id": str(member_id),
                    "sender_name": sender_name,
                    "content": msg.content,
                    "message_type": "text",
                    "created_at": msg.created_at.isoformat(),
                },
            }
            await connection_manager.broadcast_to_participants(
                participant_ids, payload, exclude_member_id=member_id
            )
        except Exception:
            logger.debug("WS broadcast failed (non-fatal)")

        result = MessageSchema(
            id=msg.id,
            sender_id=member_id,
            sender_name=sender_name,
            content=msg.content,
            message_type="text",
            created_at=msg.created_at,
            edited_at=msg.edited_at,
        )

    return json(result.model_dump(mode="json"), status=201)


@messaging_api_bp.get("/conversations/<conversation_id:uuid>/messages")
async def list_messages(request: Request, conversation_id: uuid.UUID):
    """GET /api/v1/messaging/conversations/:id/messages -- Paginated message history.

    Query params: page (default 1), per_page (default 50)
    Returns JSON: {"messages": [MessageSchema], "total": N}
    """
    member, err = require_auth(request)
    if err:
        return err

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))
    offset = (page - 1) * per_page

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_ids = await _get_current_member_ids(session, member, eco_ids)
        if not member_ids:
            return json({"error": "Member not found"}, status=404)

        # Verify participation via any of the user's member rows
        participant_check = await session.execute(
            select(ConversationParticipant.id)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .where(ConversationParticipant.member_id.in_(member_ids))
        )
        if participant_check.scalar_one_or_none() is None:
            return json({"error": "Conversation not found"}, status=404)

        # Total count
        total_stmt = (
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
            .where(Message.deleted_at.is_(None))
        )
        total = (await session.execute(total_stmt)).scalar() or 0

        # Paginated messages
        SenderMember = aliased(Member)
        msg_stmt = (
            select(Message, SenderMember.display_name)
            .join(SenderMember, SenderMember.id == Message.sender_id)
            .where(Message.conversation_id == conversation_id)
            .where(Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        msg_result = await session.execute(msg_stmt)
        msg_rows = msg_result.all()

        messages = [
            MessageSchema(
                id=msg.id,
                sender_id=msg.sender_id,
                sender_name=sender_name,
                content=msg.content,
                message_type=msg.message_type,
                created_at=msg.created_at,
                edited_at=msg.edited_at,
            )
            for msg, sender_name in reversed(msg_rows)
        ]

    return json({"messages": [m.model_dump(mode="json") for m in messages], "total": total})


@messaging_api_bp.get("/search")
async def search_messages(request: Request):
    """GET /api/v1/messaging/search -- Search messages across conversations.

    Query param: q (search content ILIKE)
    Scoped to conversations the member participates in.
    Returns JSON: {"messages": [MessageSchema]}
    """
    member, err = require_auth(request)
    if err:
        return err

    query = request.args.get("q", "").strip()
    if not query:
        return json({"messages": []})

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member, eco_ids)
        if member_id is None:
            return json({"messages": []})

        # Get conversation ids the member participates in
        conv_ids_stmt = (
            select(ConversationParticipant.conversation_id)
            .where(ConversationParticipant.member_id == member_id)
        )
        conv_ids_result = await session.execute(conv_ids_stmt)
        conv_ids = [row[0] for row in conv_ids_result.all()]

        if not conv_ids:
            return json({"messages": []})

        pattern = f"%{query}%"
        SenderMember = aliased(Member)
        msg_stmt = (
            select(Message, SenderMember.display_name)
            .join(SenderMember, SenderMember.id == Message.sender_id)
            .where(Message.conversation_id.in_(conv_ids))
            .where(Message.deleted_at.is_(None))
            .where(Message.content.ilike(pattern))
            .order_by(Message.created_at.desc())
            .limit(50)
        )
        msg_result = await session.execute(msg_stmt)
        msg_rows = msg_result.all()

        messages = [
            MessageSchema(
                id=msg.id,
                sender_id=msg.sender_id,
                sender_name=sender_name,
                content=msg.content,
                message_type=msg.message_type,
                created_at=msg.created_at,
                edited_at=msg.edited_at,
            )
            for msg, sender_name in msg_rows
        ]

    return json({"messages": [m.model_dump(mode="json") for m in messages]})


@messaging_api_bp.get("/members")
async def list_members_for_picker(request: Request):
    """GET /api/v1/messaging/members -- Member picker for starting conversations.

    Returns members across ALL ecosystems the user belongs to (not just the
    currently UI-selected ones — scoping to the selection hid most users).
    Excludes all of the user's own member rows.
    Returns JSON: {"members": [MemberPickerItem]}
    """
    member, err = require_auth(request)
    if err:
        return err

    from neos_agent.db.models import Ecosystem
    from neos_agent.api.helpers import get_authorized_ecosystem_ids

    eco_ids = get_authorized_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        own_ids = await _get_current_member_ids(session, member, [])

        stmt = (
            select(Member.id, Member.display_name, Member.profile, Member.role,
                   Member.ecosystem_id, Ecosystem.name.label("ecosystem_name"))
            .outerjoin(Ecosystem, Ecosystem.id == Member.ecosystem_id)
        )
        if eco_ids:
            stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))

        # Exclude every member row belonging to the current user
        if own_ids:
            stmt = stmt.where(Member.id.notin_(own_ids))

        stmt = stmt.order_by(Member.display_name)
        result = await session.execute(stmt)
        rows = result.all()

        members = [
            MemberPickerItem(
                id=row.id,
                display_name=row.display_name,
                profile=row.profile,
                ecosystem_id=row.ecosystem_id,
                ecosystem_name=row.ecosystem_name,
                role=row.role,
            )
            for row in rows
        ]

    return json({"members": [m.model_dump(mode="json") for m in members]})
