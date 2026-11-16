"""Shared messaging query helpers for use across views."""

from __future__ import annotations

from sqlalchemy import func, select

from neos_agent.db.models import (
    Conversation,
    ConversationLink,
    ConversationParticipant,
)


def dm_pair_key(member_a_id, member_b_id) -> str:
    """Stable key for one unordered pair of member ids. Groups and legacy rows leave it unset."""
    left, right = sorted((str(member_a_id), str(member_b_id)))
    return f"{left}:{right}"


async def _find_existing_dm(db, member_a_id, member_b_id, ecosystem_id=None):
    """The oldest direct thread whose participants are exactly this pair, or None.

    ``ecosystem_id`` narrows the search when given. Duplicate legacy rows are left in place;
    the oldest one is the thread later creates reuse.
    """
    pair = {member_a_id, member_b_id}
    stmt = (
        select(Conversation)
        .join(ConversationParticipant, ConversationParticipant.conversation_id == Conversation.id)
        .where(Conversation.type == "dm")
        .where(ConversationParticipant.member_id.in_(list(pair)))
        .order_by(Conversation.created_at.asc(), Conversation.id.asc())
    )
    if ecosystem_id is not None:
        stmt = stmt.where(Conversation.ecosystem_id == ecosystem_id)
    seen = set()
    for convo in (await db.execute(stmt)).scalars():
        if convo.id in seen:
            continue
        seen.add(convo.id)
        member_ids = set((await db.scalars(
            select(ConversationParticipant.member_id).where(ConversationParticipant.conversation_id == convo.id)
        )).all())
        if member_ids == pair:
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
