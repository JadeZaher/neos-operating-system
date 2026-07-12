"""Shared messaging query helpers for use across views."""

from __future__ import annotations

from sqlalchemy import func, select

from neos_agent.db.models import (
    Conversation,
    ConversationLink,
    ConversationParticipant,
)


async def _find_existing_dm(db, member_a_id, member_b_id, ecosystem_id):
    """Return the existing DM conversation between two members, or None."""
    stmt = (
        select(Conversation)
        .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
        .where(Conversation.type == "dm")
        .where(Conversation.ecosystem_id == ecosystem_id)
        .where(ConversationParticipant.member_id.in_([member_a_id, member_b_id]))
    )
    result = await db.execute(stmt)
    convos = result.scalars().unique().all()
    for convo in convos:
        participant_result = await db.execute(
            select(ConversationParticipant.member_id)
            .where(ConversationParticipant.conversation_id == convo.id)
        )
        member_ids = {row[0] for row in participant_result.all()}
        if member_ids == {member_a_id, member_b_id}:
            return convo
    return None


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
