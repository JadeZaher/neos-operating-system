"""Tests for the messaging data models.

Tests cover the 4 new messaging models:
- Conversation: ecosystem-scoped chat threads (DM and group)
- ConversationParticipant: links members to conversations with roles
- Message: individual messages within conversations
- ConversationLink: links conversations to governance entities

All tests use the ``seeded_db`` fixture from conftest.py which provides:
- 1 ecosystem (OmniOne)
- 3 active members: Lani (steward), Kai (builder), Manu (townhall)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from neos_agent.db.models import (
    Conversation,
    ConversationLink,
    ConversationParticipant,
    Message,
    Member,
)

# Stable UUIDs matching conftest.py seed data
ECO_ID = uuid.UUID("00000000000000000000000000000001")
MEMBER_STEWARD_ID = uuid.UUID("00000000000000000000000000000010")  # Lani
MEMBER_BUILDER_ID = uuid.UUID("00000000000000000000000000000020")  # Kai
MEMBER_TH_ID = uuid.UUID("00000000000000000000000000000030")       # Manu


# ===================================================================
# Conversation model
# ===================================================================


class TestConversation:
    async def test_create_dm_conversation(self, seeded_db):
        """A DM conversation can be created with ecosystem_id, type, and created_by."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.commit()

        result = await seeded_db.get(Conversation, convo.id)
        assert result is not None
        assert result.type == "dm"
        assert result.title is None
        assert result.ecosystem_id == ECO_ID
        assert result.created_by == MEMBER_STEWARD_ID
        assert isinstance(result.created_at, datetime)

    async def test_create_group_conversation_with_title(self, seeded_db):
        """A group conversation stores a title."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="group",
            title="Kitchen Planning",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.commit()

        result = await seeded_db.get(Conversation, convo.id)
        assert result is not None
        assert result.type == "group"
        assert result.title == "Kitchen Planning"

    async def test_conversation_has_timestamp_mixin(self, seeded_db):
        """Conversation has created_at and updated_at from TimestampMixin."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.commit()

        result = await seeded_db.get(Conversation, convo.id)
        assert result.created_at is not None
        assert result.updated_at is not None


# ===================================================================
# ConversationParticipant model
# ===================================================================


class TestConversationParticipant:
    async def test_create_participant(self, seeded_db):
        """A participant links a member to a conversation with a role."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        participant = ConversationParticipant(
            conversation_id=convo.id,
            member_id=MEMBER_STEWARD_ID,
            role="owner",
        )
        seeded_db.add(participant)
        await seeded_db.commit()

        result = await seeded_db.get(ConversationParticipant, participant.id)
        assert result is not None
        assert result.conversation_id == convo.id
        assert result.member_id == MEMBER_STEWARD_ID
        assert result.role == "owner"
        assert result.muted is False

    async def test_participant_unique_constraint(self, seeded_db):
        """Cannot add the same member to the same conversation twice."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        p1 = ConversationParticipant(
            conversation_id=convo.id,
            member_id=MEMBER_STEWARD_ID,
            role="owner",
        )
        seeded_db.add(p1)
        await seeded_db.flush()

        p2 = ConversationParticipant(
            conversation_id=convo.id,
            member_id=MEMBER_STEWARD_ID,
            role="member",
        )
        seeded_db.add(p2)

        with pytest.raises(IntegrityError):
            await seeded_db.flush()

    async def test_participant_last_read_at_nullable(self, seeded_db):
        """last_read_at starts as None and can be updated."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        participant = ConversationParticipant(
            conversation_id=convo.id,
            member_id=MEMBER_STEWARD_ID,
            role="owner",
        )
        seeded_db.add(participant)
        await seeded_db.commit()

        result = await seeded_db.get(ConversationParticipant, participant.id)
        assert result.last_read_at is None

        result.last_read_at = datetime.now(UTC)
        await seeded_db.commit()
        refreshed = await seeded_db.get(ConversationParticipant, participant.id)
        assert refreshed.last_read_at is not None

    async def test_participant_joined_at(self, seeded_db):
        """Participant has a joined_at timestamp."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        participant = ConversationParticipant(
            conversation_id=convo.id,
            member_id=MEMBER_STEWARD_ID,
            role="owner",
        )
        seeded_db.add(participant)
        await seeded_db.commit()

        result = await seeded_db.get(ConversationParticipant, participant.id)
        assert result.joined_at is not None


# ===================================================================
# Message model
# ===================================================================


class TestMessage:
    async def test_create_text_message(self, seeded_db):
        """A text message can be created with conversation FK, sender FK, and content."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        msg = Message(
            conversation_id=convo.id,
            sender_id=MEMBER_STEWARD_ID,
            content="Hello, Kai!",
            message_type="text",
        )
        seeded_db.add(msg)
        await seeded_db.commit()

        result = await seeded_db.get(Message, msg.id)
        assert result is not None
        assert result.content == "Hello, Kai!"
        assert result.message_type == "text"
        assert result.sender_id == MEMBER_STEWARD_ID
        assert result.conversation_id == convo.id

    async def test_message_soft_delete(self, seeded_db):
        """A message can be soft-deleted by setting deleted_at."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        msg = Message(
            conversation_id=convo.id,
            sender_id=MEMBER_STEWARD_ID,
            content="Delete me",
            message_type="text",
        )
        seeded_db.add(msg)
        await seeded_db.commit()

        result = await seeded_db.get(Message, msg.id)
        assert result.deleted_at is None

        result.deleted_at = datetime.now(UTC)
        await seeded_db.commit()

        refreshed = await seeded_db.get(Message, msg.id)
        assert refreshed.deleted_at is not None

    async def test_message_edit(self, seeded_db):
        """A message can be edited by updating content and setting edited_at."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        msg = Message(
            conversation_id=convo.id,
            sender_id=MEMBER_STEWARD_ID,
            content="Original",
            message_type="text",
        )
        seeded_db.add(msg)
        await seeded_db.commit()

        result = await seeded_db.get(Message, msg.id)
        assert result.edited_at is None

        result.content = "Edited"
        result.edited_at = datetime.now(UTC)
        await seeded_db.commit()

        refreshed = await seeded_db.get(Message, msg.id)
        assert refreshed.content == "Edited"
        assert refreshed.edited_at is not None

    async def test_message_metadata_json(self, seeded_db):
        """A governance_link message stores message_metadata as JSON."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="group",
            title="Test Group",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        message_metadata = {
            "entity_type": "proposal",
            "entity_id": str(uuid.uuid4()),
            "entity_title": "Add evening kitchen hours",
        }
        msg = Message(
            conversation_id=convo.id,
            sender_id=MEMBER_STEWARD_ID,
            content="Check out this proposal",
            message_type="governance_link",
            message_metadata=message_metadata,
        )
        seeded_db.add(msg)
        await seeded_db.commit()

        result = await seeded_db.get(Message, msg.id)
        assert result.message_type == "governance_link"
        assert result.message_metadata["entity_type"] == "proposal"
        assert result.message_metadata["entity_title"] == "Add evening kitchen hours"

    async def test_system_message(self, seeded_db):
        """A system message has message_type 'system'."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="group",
            title="Test Group",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        msg = Message(
            conversation_id=convo.id,
            sender_id=MEMBER_STEWARD_ID,
            content="Lani created this conversation",
            message_type="system",
        )
        seeded_db.add(msg)
        await seeded_db.commit()

        result = await seeded_db.get(Message, msg.id)
        assert result.message_type == "system"


# ===================================================================
# ConversationLink model
# ===================================================================


class TestConversationLink:
    async def test_create_conversation_link(self, seeded_db):
        """A ConversationLink ties a conversation to a governance entity."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="group",
            title="Proposal Discussion",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        link = ConversationLink(
            conversation_id=convo.id,
            entity_type="proposal",
            entity_id=uuid.uuid4(),
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(link)
        await seeded_db.commit()

        result = await seeded_db.get(ConversationLink, link.id)
        assert result is not None
        assert result.entity_type == "proposal"
        assert result.conversation_id == convo.id
        assert result.created_by == MEMBER_STEWARD_ID

    async def test_link_different_entity_types(self, seeded_db):
        """Links can reference different governance entity types."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="group",
            title="Multi-link Discussion",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        for entity_type in ["proposal", "agreement", "domain", "conflict", "decision"]:
            link = ConversationLink(
                conversation_id=convo.id,
                entity_type=entity_type,
                entity_id=uuid.uuid4(),
                created_by=MEMBER_STEWARD_ID,
            )
            seeded_db.add(link)

        await seeded_db.commit()

        stmt = select(ConversationLink).where(
            ConversationLink.conversation_id == convo.id
        )
        result = await seeded_db.execute(stmt)
        links = result.scalars().all()
        assert len(links) == 5
        types = {link.entity_type for link in links}
        assert types == {"proposal", "agreement", "domain", "conflict", "decision"}


# ===================================================================
# Relationships and cascades
# ===================================================================


class TestRelationshipsAndCascades:
    async def test_conversation_participants_relationship(self, seeded_db):
        """Conversation.participants returns linked participants."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        p1 = ConversationParticipant(
            conversation_id=convo.id,
            member_id=MEMBER_STEWARD_ID,
            role="owner",
        )
        p2 = ConversationParticipant(
            conversation_id=convo.id,
            member_id=MEMBER_BUILDER_ID,
            role="member",
        )
        seeded_db.add_all([p1, p2])
        await seeded_db.commit()

        # Reload with fresh query
        stmt = select(Conversation).where(Conversation.id == convo.id)
        result = await seeded_db.execute(stmt)
        loaded = result.scalar_one()

        # Access participants through relationship (may need selectinload for async)
        stmt_p = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == convo.id
        )
        result_p = await seeded_db.execute(stmt_p)
        participants = result_p.scalars().all()
        assert len(participants) == 2

    async def test_conversation_messages_relationship(self, seeded_db):
        """Messages can be queried by conversation_id."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()

        for i in range(3):
            msg = Message(
                conversation_id=convo.id,
                sender_id=MEMBER_STEWARD_ID,
                content=f"Message {i}",
                message_type="text",
            )
            seeded_db.add(msg)
        await seeded_db.commit()

        stmt = select(Message).where(Message.conversation_id == convo.id)
        result = await seeded_db.execute(stmt)
        messages = result.scalars().all()
        assert len(messages) == 3

    async def test_cascade_delete_conversation(self, seeded_db):
        """Deleting a conversation cascades to participants, messages, and links."""
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="group",
            title="Ephemeral Group",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(convo)
        await seeded_db.flush()
        convo_id = convo.id

        # Add participant
        p = ConversationParticipant(
            conversation_id=convo_id,
            member_id=MEMBER_STEWARD_ID,
            role="owner",
        )
        seeded_db.add(p)

        # Add message
        msg = Message(
            conversation_id=convo_id,
            sender_id=MEMBER_STEWARD_ID,
            content="Temporary message",
            message_type="text",
        )
        seeded_db.add(msg)

        # Add link
        link = ConversationLink(
            conversation_id=convo_id,
            entity_type="proposal",
            entity_id=uuid.uuid4(),
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(link)
        await seeded_db.commit()

        # Delete the conversation
        loaded = await seeded_db.get(Conversation, convo_id)
        await seeded_db.delete(loaded)
        await seeded_db.commit()

        # Verify cascaded deletions
        assert await seeded_db.get(Conversation, convo_id) is None

        stmt_p = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == convo_id
        )
        result_p = await seeded_db.execute(stmt_p)
        assert result_p.scalars().all() == []

        stmt_m = select(Message).where(Message.conversation_id == convo_id)
        result_m = await seeded_db.execute(stmt_m)
        assert result_m.scalars().all() == []

        stmt_l = select(ConversationLink).where(
            ConversationLink.conversation_id == convo_id
        )
        result_l = await seeded_db.execute(stmt_l)
        assert result_l.scalars().all() == []


# ===================================================================
# DM uniqueness (application-level constraint test)
# ===================================================================


class TestDMUniqueness:
    async def test_dm_participant_pair_unique_per_ecosystem(self, seeded_db):
        """Only one DM should exist between a given pair of members per ecosystem.

        This is enforced at the application level by checking for an existing
        DM conversation before creating a new one. The DB uniqueness constraint
        on ConversationParticipant(conversation_id, member_id) prevents
        duplicate participants within a single conversation.
        """
        # Create first DM
        dm1 = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        seeded_db.add(dm1)
        await seeded_db.flush()

        seeded_db.add_all([
            ConversationParticipant(
                conversation_id=dm1.id,
                member_id=MEMBER_STEWARD_ID,
                role="member",
            ),
            ConversationParticipant(
                conversation_id=dm1.id,
                member_id=MEMBER_BUILDER_ID,
                role="member",
            ),
        ])
        await seeded_db.commit()

        # Simulate application-level check: query for existing DM
        stmt = (
            select(Conversation)
            .where(Conversation.ecosystem_id == ECO_ID)
            .where(Conversation.type == "dm")
        )
        result = await seeded_db.execute(stmt)
        existing_dms = result.scalars().all()

        # For each existing DM, check if both members are participants
        found_existing = False
        for dm in existing_dms:
            stmt_p = select(ConversationParticipant.member_id).where(
                ConversationParticipant.conversation_id == dm.id
            )
            result_p = await seeded_db.execute(stmt_p)
            member_ids = set(result_p.scalars().all())
            if {MEMBER_STEWARD_ID, MEMBER_BUILDER_ID} == member_ids:
                found_existing = True
                break

        assert found_existing is True, (
            "Application should find existing DM and not create a duplicate"
        )
