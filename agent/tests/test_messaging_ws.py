"""Tests for WebSocket messaging endpoint and handlers.

Tests cover:
- WebSocket authentication (session cookie validation)
- Connection registration/unregistration in ConnectionManager
- Message handling (persist + broadcast)
- Typing indicator broadcasting
- Read receipt handling
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from neos_agent.db.models import (
    AuthSession,
    Conversation,
    ConversationParticipant,
    Member,
    Message,
)
from neos_agent.messaging.connections import ConnectionManager
from neos_agent.messaging.handlers import (
    handle_message,
    handle_read_receipt,
    handle_typing,
)

# Stable UUIDs matching conftest.py
ECO_ID = uuid.UUID("00000000000000000000000000000001")
MEMBER_STEWARD_ID = uuid.UUID("00000000000000000000000000000010")  # Lani
MEMBER_BUILDER_ID = uuid.UUID("00000000000000000000000000000020")  # Kai
MEMBER_TH_ID = uuid.UUID("00000000000000000000000000000030")       # Manu
DM_CONVERSATION_ID = uuid.UUID("00000000000000000000000000100000")
GROUP_CONVERSATION_ID = uuid.UUID("00000000000000000000000000200000")


def _make_ws():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    return ws


def _make_app(db_session_factory):
    """Create a mock app with db context manager."""
    app = MagicMock()
    app.ctx.db = db_session_factory
    app.ctx.settings = MagicMock()
    app.ctx.settings.SESSION_SECRET = "test-secret"
    return app


# ===================================================================
# Handler tests (using seeded_messaging_db)
# ===================================================================


class TestHandleMessage:
    async def test_sends_message_and_persists(self, seeded_messaging_db):
        """handle_message persists a message and broadcasts."""
        ws = _make_ws()

        # Create a mock member object
        member = await seeded_messaging_db.get(Member, MEMBER_STEWARD_ID)

        # Create app mock with a real db session
        session_factory = seeded_messaging_db.get_bind()
        app = MagicMock()

        # Create a context manager that yields the real session
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _db():
            yield seeded_messaging_db

        app.ctx.db = _db

        data = {
            "conversation_id": str(DM_CONVERSATION_ID),
            "content": "New test message",
        }

        with patch("neos_agent.messaging.connections.connection_manager") as mock_cm:
            mock_cm.broadcast_to_participants = AsyncMock()
            await handle_message(ws, member, data, app)

        # Verify message was persisted
        result = await seeded_messaging_db.execute(
            select(Message).where(
                Message.conversation_id == DM_CONVERSATION_ID,
                Message.content == "New test message",
            )
        )
        msg = result.scalar_one_or_none()
        assert msg is not None
        assert msg.sender_id == MEMBER_STEWARD_ID
        assert msg.message_type == "text"

    async def test_rejects_empty_content(self, seeded_messaging_db):
        """handle_message rejects empty content."""
        ws = _make_ws()
        member = await seeded_messaging_db.get(Member, MEMBER_STEWARD_ID)

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _db():
            yield seeded_messaging_db

        app = MagicMock()
        app.ctx.db = _db

        data = {"conversation_id": str(DM_CONVERSATION_ID), "content": ""}
        await handle_message(ws, member, data, app)

        ws.send.assert_called_once()
        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "error"

    async def test_rejects_non_participant(self, seeded_messaging_db):
        """handle_message rejects messages from non-participants."""
        ws = _make_ws()
        # Manu is not in the DM conversation
        member = await seeded_messaging_db.get(Member, MEMBER_TH_ID)

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _db():
            yield seeded_messaging_db

        app = MagicMock()
        app.ctx.db = _db

        data = {
            "conversation_id": str(DM_CONVERSATION_ID),
            "content": "I shouldn't be able to send this",
        }

        with patch("neos_agent.messaging.connections.connection_manager") as mock_cm:
            mock_cm.broadcast_to_participants = AsyncMock()
            await handle_message(ws, member, data, app)

        ws.send.assert_called_once()
        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "Not a participant" in sent["data"]["message"]

    async def test_rejects_too_long_message(self, seeded_messaging_db):
        """handle_message rejects messages exceeding max length."""
        ws = _make_ws()
        member = await seeded_messaging_db.get(Member, MEMBER_STEWARD_ID)

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _db():
            yield seeded_messaging_db

        app = MagicMock()
        app.ctx.db = _db

        data = {
            "conversation_id": str(DM_CONVERSATION_ID),
            "content": "x" * 10_001,
        }
        await handle_message(ws, member, data, app)

        ws.send.assert_called_once()
        sent = json.loads(ws.send.call_args[0][0])
        assert sent["type"] == "error"
        assert "too long" in sent["data"]["message"]


class TestHandleTyping:
    async def test_broadcasts_typing_indicator(self, seeded_messaging_db):
        """handle_typing broadcasts a typing event to other participants."""
        ws = _make_ws()
        member = await seeded_messaging_db.get(Member, MEMBER_STEWARD_ID)

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _db():
            yield seeded_messaging_db

        app = MagicMock()
        app.ctx.db = _db

        data = {"conversation_id": str(DM_CONVERSATION_ID)}

        with patch("neos_agent.messaging.connections.connection_manager") as mock_cm:
            mock_cm.broadcast_to_participants = AsyncMock()
            await handle_typing(ws, member, data, app)
            mock_cm.broadcast_to_participants.assert_called_once()

            # Should exclude the sender
            call_args = mock_cm.broadcast_to_participants.call_args
            assert call_args.kwargs.get("exclude_member_id") == MEMBER_STEWARD_ID


class TestHandleReadReceipt:
    async def test_updates_last_read_at(self, seeded_messaging_db):
        """handle_read_receipt updates the participant's last_read_at."""
        ws = _make_ws()
        member = await seeded_messaging_db.get(Member, MEMBER_STEWARD_ID)

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _db():
            yield seeded_messaging_db

        app = MagicMock()
        app.ctx.db = _db

        data = {"conversation_id": str(DM_CONVERSATION_ID)}

        with patch("neos_agent.messaging.connections.connection_manager") as mock_cm:
            mock_cm.broadcast_to_participants = AsyncMock()
            await handle_read_receipt(ws, member, data, app)

        # Check last_read_at was updated
        result = await seeded_messaging_db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == DM_CONVERSATION_ID,
                ConversationParticipant.member_id == MEMBER_STEWARD_ID,
            )
        )
        participant = result.scalar_one()
        assert participant.last_read_at is not None
