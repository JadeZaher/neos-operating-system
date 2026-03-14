"""WebSocket message type handlers for the messaging system.

Each handler processes a specific message type received over WebSocket:
- message: persist and broadcast a new message
- typing: broadcast typing indicator (no persistence)
- read_receipt: update last_read_at and broadcast receipt
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from neos_agent.db.models import (
    Conversation,
    ConversationParticipant,
    Message,
)

logger = logging.getLogger(__name__)

# Rate limiting: track last message time per member
_last_message_times: dict[uuid.UUID, list[float]] = {}
MAX_MESSAGES_PER_SECOND = 10
MAX_MESSAGE_LENGTH = 10_000


async def _get_participant_ids(db: AsyncSession, conversation_id: uuid.UUID) -> list[uuid.UUID]:
    """Get all member IDs participating in a conversation."""
    result = await db.execute(
        select(ConversationParticipant.member_id).where(
            ConversationParticipant.conversation_id == conversation_id
        )
    )
    return list(result.scalars().all())


async def _verify_membership(
    db: AsyncSession, conversation_id: uuid.UUID, member_id: uuid.UUID
) -> bool:
    """Check if a member is a participant in the conversation."""
    result = await db.execute(
        select(ConversationParticipant.id).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.member_id == member_id,
        )
    )
    return result.scalar_one_or_none() is not None


def _check_rate_limit(member_id: uuid.UUID) -> bool:
    """Return True if the member is within rate limits."""
    now = datetime.utcnow().timestamp()
    times = _last_message_times.get(member_id, [])
    # Keep only times within the last second
    times = [t for t in times if now - t < 1.0]
    _last_message_times[member_id] = times
    return len(times) < MAX_MESSAGES_PER_SECOND


async def handle_message(ws, member, data: dict, app) -> None:
    """Handle a new message: validate, persist, broadcast.

    Expected data: {"conversation_id": "...", "content": "..."}
    """
    from neos_agent.messaging.connections import connection_manager

    conversation_id_str = data.get("conversation_id")
    content = data.get("content", "").strip()

    if not conversation_id_str or not content:
        await ws.send('{"type":"error","data":{"message":"Missing conversation_id or content"}}')
        return

    if len(content) > MAX_MESSAGE_LENGTH:
        await ws.send('{"type":"error","data":{"message":"Message too long (max 10000 chars)"}}')
        return

    if not _check_rate_limit(member.id):
        await ws.send('{"type":"error","data":{"message":"Rate limit exceeded"}}')
        return

    try:
        conversation_id = uuid.UUID(conversation_id_str)
    except ValueError:
        await ws.send('{"type":"error","data":{"message":"Invalid conversation_id"}}')
        return

    async with app.ctx.db() as db:
        # Verify membership
        if not await _verify_membership(db, conversation_id, member.id):
            await ws.send('{"type":"error","data":{"message":"Not a participant"}}')
            return

        # Check member status (exited members can't send)
        if member.current_status == "exited":
            await ws.send('{"type":"error","data":{"message":"You have exited this ecosystem"}}')
            return

        # Persist message
        msg = Message(
            conversation_id=conversation_id,
            sender_id=member.id,
            content=content,
            message_type="text",
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)

        # Track rate limit
        now = datetime.utcnow().timestamp()
        _last_message_times.setdefault(member.id, []).append(now)

        # Build broadcast payload
        payload = {
            "type": "message",
            "data": {
                "id": str(msg.id),
                "conversation_id": str(conversation_id),
                "sender_id": str(member.id),
                "sender_name": member.display_name,
                "content": msg.content,
                "message_type": "text",
                "created_at": msg.created_at.isoformat(),
            },
        }

        # Broadcast to all participants
        participant_ids = await _get_participant_ids(db, conversation_id)
        await connection_manager.broadcast_to_participants(
            participant_ids, payload, exclude_member_id=None
        )


async def handle_typing(ws, member, data: dict, app) -> None:
    """Handle typing indicator: broadcast to participants (no persistence).

    Expected data: {"conversation_id": "..."}
    """
    from neos_agent.messaging.connections import connection_manager

    conversation_id_str = data.get("conversation_id")
    if not conversation_id_str:
        return

    try:
        conversation_id = uuid.UUID(conversation_id_str)
    except ValueError:
        return

    async with app.ctx.db() as db:
        if not await _verify_membership(db, conversation_id, member.id):
            return

        participant_ids = await _get_participant_ids(db, conversation_id)
        payload = {
            "type": "typing",
            "data": {
                "conversation_id": str(conversation_id),
                "member_id": str(member.id),
                "member_name": member.display_name,
            },
        }
        await connection_manager.broadcast_to_participants(
            participant_ids, payload, exclude_member_id=member.id
        )


async def handle_read_receipt(ws, member, data: dict, app) -> None:
    """Handle read receipt: update last_read_at, broadcast to participants.

    Expected data: {"conversation_id": "..."}
    """
    from neos_agent.messaging.connections import connection_manager

    conversation_id_str = data.get("conversation_id")
    if not conversation_id_str:
        return

    try:
        conversation_id = uuid.UUID(conversation_id_str)
    except ValueError:
        return

    async with app.ctx.db() as db:
        # Update last_read_at
        result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.member_id == member.id,
            )
        )
        participant = result.scalar_one_or_none()
        if not participant:
            return

        participant.last_read_at = datetime.utcnow()
        await db.commit()

        # Broadcast read receipt
        participant_ids = await _get_participant_ids(db, conversation_id)
        payload = {
            "type": "read_receipt",
            "data": {
                "conversation_id": str(conversation_id),
                "member_id": str(member.id),
                "read_at": participant.last_read_at.isoformat(),
            },
        }
        await connection_manager.broadcast_to_participants(
            participant_ids, payload, exclude_member_id=member.id
        )
