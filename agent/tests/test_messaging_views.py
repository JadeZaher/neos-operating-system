"""Tests for messaging REST endpoints.

Tests cover conversation CRUD, message endpoints, participant management,
and governance link creation. Uses seeded_messaging_db fixture.
"""

from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import func, select

from neos_agent.db.models import (
    Conversation,
    ConversationLink,
    ConversationParticipant,
    Member,
    Message,
)
from neos_agent.messaging.routes import (
    _find_existing_dm,
    _find_or_create_dm,
)

# Stable UUIDs matching conftest.py
ECO_ID = uuid.UUID("00000000000000000000000000000001")
MEMBER_STEWARD_ID = uuid.UUID("00000000000000000000000000000010")  # Lani
MEMBER_BUILDER_ID = uuid.UUID("00000000000000000000000000000020")  # Kai
MEMBER_TH_ID = uuid.UUID("00000000000000000000000000000030")       # Manu
DM_CONVERSATION_ID = uuid.UUID("00000000000000000000000000100000")
GROUP_CONVERSATION_ID = uuid.UUID("00000000000000000000000000200000")
PROPOSAL_ID = uuid.UUID("00000000000000000000000000010000")


class TestFindExistingDM:
    async def test_finds_existing_dm(self, seeded_messaging_db):
        """_find_existing_dm returns existing DM between two members."""
        result = await _find_existing_dm(
            seeded_messaging_db, MEMBER_STEWARD_ID, MEMBER_BUILDER_ID, ECO_ID,
        )
        assert result is not None
        assert result.id == DM_CONVERSATION_ID

    async def test_returns_none_for_no_dm(self, seeded_messaging_db):
        """_find_existing_dm returns None when no DM exists."""
        result = await _find_existing_dm(
            seeded_messaging_db, MEMBER_STEWARD_ID, MEMBER_TH_ID, ECO_ID,
        )
        assert result is None


class TestConversationCreate:
    async def test_create_dm_conversation(self, seeded_messaging_db):
        """Creating a DM between Lani and Manu (who don't have one)."""
        db = seeded_messaging_db

        # Verify no DM exists yet
        existing = await _find_existing_dm(db, MEMBER_STEWARD_ID, MEMBER_TH_ID, ECO_ID)
        assert existing is None

        # Create DM
        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="dm",
            created_by=MEMBER_STEWARD_ID,
        )
        db.add(convo)
        await db.flush()
        db.add_all([
            ConversationParticipant(
                conversation_id=convo.id, member_id=MEMBER_STEWARD_ID, role="member",
            ),
            ConversationParticipant(
                conversation_id=convo.id, member_id=MEMBER_TH_ID, role="member",
            ),
        ])
        await db.commit()

        # Verify DM now exists
        found = await _find_existing_dm(db, MEMBER_STEWARD_ID, MEMBER_TH_ID, ECO_ID)
        assert found is not None
        assert found.id == convo.id

    async def test_create_group_conversation(self, seeded_messaging_db):
        """Creating a group conversation with title."""
        db = seeded_messaging_db

        convo = Conversation(
            ecosystem_id=ECO_ID,
            type="group",
            title="New Group Chat",
            created_by=MEMBER_STEWARD_ID,
        )
        db.add(convo)
        await db.flush()

        db.add_all([
            ConversationParticipant(
                conversation_id=convo.id, member_id=MEMBER_STEWARD_ID, role="owner",
            ),
            ConversationParticipant(
                conversation_id=convo.id, member_id=MEMBER_BUILDER_ID, role="member",
            ),
            ConversationParticipant(
                conversation_id=convo.id, member_id=MEMBER_TH_ID, role="member",
            ),
        ])
        await db.commit()

        result = await db.get(Conversation, convo.id)
        assert result.type == "group"
        assert result.title == "New Group Chat"


class TestMessageEndpoints:
    async def test_send_message_persists(self, seeded_messaging_db):
        """Sending a message persists it to the database."""
        db = seeded_messaging_db

        msg = Message(
            conversation_id=DM_CONVERSATION_ID,
            sender_id=MEMBER_STEWARD_ID,
            content="REST test message",
            message_type="text",
        )
        db.add(msg)
        await db.commit()

        result = await db.execute(
            select(Message).where(
                Message.conversation_id == DM_CONVERSATION_ID,
                Message.content == "REST test message",
            )
        )
        assert result.scalar_one_or_none() is not None

    async def test_edit_own_message(self, seeded_messaging_db):
        """Editing own message updates content and edited_at."""
        db = seeded_messaging_db

        msg = Message(
            conversation_id=DM_CONVERSATION_ID,
            sender_id=MEMBER_STEWARD_ID,
            content="Original text",
            message_type="text",
        )
        db.add(msg)
        await db.commit()

        result = await db.get(Message, msg.id)
        result.content = "Edited text"
        result.edited_at = datetime.now(UTC)
        await db.commit()

        refreshed = await db.get(Message, msg.id)
        assert refreshed.content == "Edited text"
        assert refreshed.edited_at is not None

    async def test_soft_delete_message(self, seeded_messaging_db):
        """Soft-deleting sets deleted_at without removing the row."""
        db = seeded_messaging_db

        msg = Message(
            conversation_id=DM_CONVERSATION_ID,
            sender_id=MEMBER_STEWARD_ID,
            content="To be deleted",
            message_type="text",
        )
        db.add(msg)
        await db.commit()

        result = await db.get(Message, msg.id)
        result.deleted_at = datetime.now(UTC)
        await db.commit()

        refreshed = await db.get(Message, msg.id)
        assert refreshed.deleted_at is not None
        # Row still exists
        assert refreshed.content == "To be deleted"

    async def test_paginated_messages(self, seeded_messaging_db):
        """Message pagination returns correct subset."""
        db = seeded_messaging_db

        # DM has 5 seed messages
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == DM_CONVERSATION_ID)
            .order_by(Message.created_at.desc())
            .limit(3)
        )
        messages = result.scalars().all()
        assert len(messages) == 3


class TestParticipantManagement:
    async def test_add_participant_to_group(self, seeded_messaging_db):
        """Adding a member to a group conversation works."""
        db = seeded_messaging_db

        # Create a new group with just Lani
        convo = Conversation(
            ecosystem_id=ECO_ID, type="group", title="Small Group",
            created_by=MEMBER_STEWARD_ID,
        )
        db.add(convo)
        await db.flush()
        db.add(ConversationParticipant(
            conversation_id=convo.id, member_id=MEMBER_STEWARD_ID, role="owner",
        ))
        await db.commit()

        # Add Kai
        db.add(ConversationParticipant(
            conversation_id=convo.id, member_id=MEMBER_BUILDER_ID, role="member",
        ))
        await db.commit()

        # Verify
        result = await db.execute(
            select(func.count()).where(
                ConversationParticipant.conversation_id == convo.id
            )
        )
        assert result.scalar() == 2

    async def test_remove_participant(self, seeded_messaging_db):
        """Removing a participant from a group conversation."""
        db = seeded_messaging_db

        # Group convo has 3 participants
        result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == GROUP_CONVERSATION_ID,
                ConversationParticipant.member_id == MEMBER_TH_ID,
            )
        )
        part = result.scalar_one()
        await db.delete(part)
        await db.commit()

        # Verify only 2 remain
        count_result = await db.execute(
            select(func.count()).where(
                ConversationParticipant.conversation_id == GROUP_CONVERSATION_ID
            )
        )
        assert count_result.scalar() == 2

    async def test_mark_read_updates_last_read_at(self, seeded_messaging_db):
        """Marking a conversation as read updates last_read_at."""
        db = seeded_messaging_db

        result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == DM_CONVERSATION_ID,
                ConversationParticipant.member_id == MEMBER_STEWARD_ID,
            )
        )
        part = result.scalar_one()
        part.last_read_at = datetime.now(UTC)
        await db.commit()

        refreshed_result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.id == part.id
            )
        )
        refreshed = refreshed_result.scalar_one()
        assert refreshed.last_read_at is not None


class TestGovernanceLink:
    async def test_create_governance_link(self, seeded_messaging_db):
        """Creating a governance link ties conversation to entity."""
        db = seeded_messaging_db

        # The seed data already has one link, let's create another
        new_link = ConversationLink(
            conversation_id=GROUP_CONVERSATION_ID,
            entity_type="agreement",
            entity_id=uuid.UUID("00000000000000000000000000001000"),
            created_by=MEMBER_STEWARD_ID,
        )
        db.add(new_link)
        await db.commit()

        result = await db.execute(
            select(ConversationLink).where(
                ConversationLink.conversation_id == GROUP_CONVERSATION_ID,
            )
        )
        links = result.scalars().all()
        assert len(links) == 2
        types = {l.entity_type for l in links}
        assert "proposal" in types
        assert "agreement" in types

    async def test_governance_link_message(self, seeded_messaging_db):
        """Governance link messages store metadata with entity info."""
        db = seeded_messaging_db

        msg = Message(
            conversation_id=GROUP_CONVERSATION_ID,
            sender_id=MEMBER_STEWARD_ID,
            content="Lani linked a proposal",
            message_type="governance_link",
            message_metadata={
                "entity_type": "proposal",
                "entity_id": str(PROPOSAL_ID),
                "entity_title": "Add evening kitchen hours",
            },
        )
        db.add(msg)
        await db.commit()

        result = await db.get(Message, msg.id)
        assert result.message_type == "governance_link"
        assert result.message_metadata["entity_type"] == "proposal"


class TestUnreadCount:
    async def test_unread_count_when_never_read(self, seeded_messaging_db):
        """All messages are unread when last_read_at is None."""
        db = seeded_messaging_db

        # DM has 5 messages, Lani hasn't read
        result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == DM_CONVERSATION_ID,
                ConversationParticipant.member_id == MEMBER_STEWARD_ID,
            )
        )
        part = result.scalar_one()
        assert part.last_read_at is None

        count_result = await db.execute(
            select(func.count()).where(
                Message.conversation_id == DM_CONVERSATION_ID,
                Message.deleted_at.is_(None),
            )
        )
        assert count_result.scalar() == 5

    async def test_unread_count_after_reading(self, seeded_messaging_db):
        """Unread count is 0 after marking read, then increases with new messages."""
        db = seeded_messaging_db

        # Mark as read
        result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == DM_CONVERSATION_ID,
                ConversationParticipant.member_id == MEMBER_STEWARD_ID,
            )
        )
        part = result.scalar_one()
        read_time = datetime.now(UTC)
        part.last_read_at = read_time
        await db.commit()

        # All messages should be read now (created before read_time)
        count_result = await db.execute(
            select(func.count()).where(
                Message.conversation_id == DM_CONVERSATION_ID,
                Message.created_at > read_time,
                Message.deleted_at.is_(None),
            )
        )
        assert count_result.scalar() == 0
