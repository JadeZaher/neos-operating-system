"""JSON API blueprint for messaging.

Blueprint: messaging_api_bp, url_prefix="/api/v1/messaging"

Provides REST endpoints for initial data loading of conversations and messages.
Real-time delivery is handled by the WebSocket at /messaging/ws.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import uuid
from datetime import datetime

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from neos_agent.db.models import (
    Conversation,
    ConversationParticipant,
    Member,
    Message,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class ParticipantSummary(BaseModel):
    id: uuid.UUID
    display_name: str
    role: str = "member"


class ConversationSummary(BaseModel):
    id: uuid.UUID
    type: str
    title: str | None = None
    last_message: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0
    participants: list[ParticipantSummary] = []


class MessageSchema(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    content: str
    message_type: str
    created_at: datetime
    edited_at: datetime | None = None


class ConversationDetailSchema(BaseModel):
    id: uuid.UUID
    type: str
    title: str | None = None
    participants: list[ParticipantSummary] = []
    messages: list[MessageSchema] = []
    total_messages: int = 0


class CreateConversationRequest(BaseModel):
    type: str  # "dm" or "group"
    title: str | None = None
    participant_ids: list[uuid.UUID]


class MemberPickerItem(BaseModel):
    id: uuid.UUID
    display_name: str
    profile: str | None = None


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

messaging_api_bp = Blueprint("messaging_api", url_prefix="/api/v1/messaging")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_auth(request: Request):
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def _get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    cookie = request.cookies.get("neos_selected_ecosystems")
    if cookie:
        try:
            ids = json_module.loads(cookie)
            return [uuid.UUID(i) for i in ids if i]
        except (json_module.JSONDecodeError, ValueError):
            pass
    member = getattr(request.ctx, "member", None)
    if member:
        return [member.ecosystem_id]
    return []


async def _get_current_member_id(session, did: str, eco_ids: list[uuid.UUID]) -> uuid.UUID | None:
    """Resolve the authenticated DID to a member id within the active ecosystems."""
    stmt = select(Member.id).where(Member.did == did)
    if eco_ids:
        stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))
    result = await session.execute(stmt.limit(1))
    return result.scalar_one_or_none()


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
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member.did, eco_ids)
        if member_id is None:
            return json({"conversations": []})

        # Get conversation ids for this member
        cp_stmt = (
            select(ConversationParticipant.conversation_id, ConversationParticipant.last_read_at)
            .where(ConversationParticipant.member_id == member_id)
        )
        cp_result = await session.execute(cp_stmt)
        participant_rows = cp_result.all()

        if not participant_rows:
            return json({"conversations": []})

        conv_ids = [row.conversation_id for row in participant_rows]
        last_read_map = {row.conversation_id: row.last_read_at for row in participant_rows}

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

            # Unread count
            last_read = last_read_map.get(conv.id)
            unread_stmt = (
                select(func.count(Message.id))
                .where(Message.conversation_id == conv.id)
                .where(Message.deleted_at.is_(None))
                .where(Message.sender_id != member_id)
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
            key=lambda s: s.last_message_at or datetime.min,
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
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member.did, eco_ids)
        if member_id is None:
            return json({"error": "Member not found"}, status=404)

        # Verify participation
        participant_check = await session.execute(
            select(ConversationParticipant.id)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .where(ConversationParticipant.member_id == member_id)
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
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = CreateConversationRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    if create_req.type not in ("dm", "group"):
        return json({"error": "type must be 'dm' or 'group'"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member.did, eco_ids)
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


@messaging_api_bp.get("/conversations/<conversation_id:uuid>/messages")
async def list_messages(request: Request, conversation_id: uuid.UUID):
    """GET /api/v1/messaging/conversations/:id/messages -- Paginated message history.

    Query params: page (default 1), per_page (default 50)
    Returns JSON: {"messages": [MessageSchema], "total": N}
    """
    member, err = _require_auth(request)
    if err:
        return err

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))
    offset = (page - 1) * per_page

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member.did, eco_ids)
        if member_id is None:
            return json({"error": "Member not found"}, status=404)

        # Verify participation
        participant_check = await session.execute(
            select(ConversationParticipant.id)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .where(ConversationParticipant.member_id == member_id)
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
    member, err = _require_auth(request)
    if err:
        return err

    query = request.args.get("q", "").strip()
    if not query:
        return json({"messages": []})

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member.did, eco_ids)
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

    Returns all members in the member's ecosystems (excluding self).
    Returns JSON: {"members": [MemberPickerItem]}
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        member_id = await _get_current_member_id(session, member.did, eco_ids)

        stmt = select(Member.id, Member.display_name, Member.profile)
        if eco_ids:
            stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))

        # Exclude self
        if member_id is not None:
            stmt = stmt.where(Member.id != member_id)

        stmt = stmt.order_by(Member.display_name)
        result = await session.execute(stmt)
        rows = result.all()

        members = [
            MemberPickerItem(id=row.id, display_name=row.display_name, profile=row.profile)
            for row in rows
        ]

    return json({"members": [m.model_dump(mode="json") for m in members]})
