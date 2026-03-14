"""Shared messaging query helpers for use across views."""

from __future__ import annotations

from sqlalchemy import func, select

from neos_agent.db.models import (
    Conversation,
    ConversationLink,
    ConversationParticipant,
)


async def get_entity_discussions(db, entity_type: str, entity_id):
    """Get conversations linked to a governance entity, with participant counts."""
    links_result = await db.execute(
        select(ConversationLink, Conversation)
        .join(Conversation, ConversationLink.conversation_id == Conversation.id)
        .where(
            ConversationLink.entity_type == entity_type,
            ConversationLink.entity_id == entity_id,
        )
    )
    discussions = []
    for link, convo in links_result.all():
        count_result = await db.execute(
            select(func.count()).where(
                ConversationParticipant.conversation_id == convo.id
            )
        )
        discussions.append({
            "conversation": convo,
            "participant_count": count_result.scalar() or 0,
        })
    return discussions
