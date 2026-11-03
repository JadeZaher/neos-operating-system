"""Transactional occurrence producers for community activity."""
from __future__ import annotations

import uuid

from sqlalchemy import select

from neos_agent.db.models import Conversation, ConversationParticipant, Member
from neos_agent.services.engagement import record_event


async def source_event(session, source, *, kind, family, action, actor_user_id=None, occurrence_id=None):
    """Record one validated mutation occurrence without committing."""
    scope = getattr(source, "ecosystem_id", None)
    return await record_event(
        session, event_key=f"{kind}:{source.id}:{action}:{occurrence_id or uuid.uuid4()}",
        family=family, event_type=f"{kind}.{action}", source_kind=kind, source_id=source.id,
        ecosystem_id=scope, actor_user_id=actor_user_id,
        domain_id=source.id if kind == "domain" else getattr(source, "domain_id", None),
        team_id=source.id if kind == "team" else getattr(source, "team_id", None),
    )


async def message_event(session, message):
    """Record recipient-only activity shared by all message producers."""
    conversation = await session.get(Conversation, message.conversation_id)
    if conversation is None:
        return None
    sender_user_id = await session.scalar(select(Member.user_id).where(Member.id == message.sender_id))
    recipients = set((await session.scalars(
        select(Member.user_id).join(ConversationParticipant, ConversationParticipant.member_id == Member.id)
        .where(ConversationParticipant.conversation_id == conversation.id,
               Member.user_id.is_not(None), Member.current_status == "active")
    )).all())
    recipients.discard(sender_user_id)
    return await record_event(
        session, event_key=f"message:{message.id}", family="messages", event_type="conversation.message",
        source_kind="conversation", source_id=conversation.id,
        ecosystem_id=conversation.ecosystem_id, actor_user_id=sender_user_id,
        audience_user_ids=sorted(str(user_id) for user_id in recipients),
    )
