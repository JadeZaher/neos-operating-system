"""Tests for the WebSocket ConnectionManager.

The ConnectionManager tracks active WebSocket connections per member
and provides methods to send messages to individual members or broadcast
to all participants of a conversation.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from neos_agent.messaging.connections import ConnectionManager


MEMBER_A = uuid.UUID("00000000000000000000000000000010")
MEMBER_B = uuid.UUID("00000000000000000000000000000020")
MEMBER_C = uuid.UUID("00000000000000000000000000000030")


def _make_ws():
    """Create a mock WebSocket with async send."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    return ws


class TestRegisterUnregister:
    def test_register_adds_connection(self):
        mgr = ConnectionManager()
        ws = _make_ws()
        mgr.register(MEMBER_A, ws)
        assert mgr.is_online(MEMBER_A)

    def test_unregister_removes_connection(self):
        mgr = ConnectionManager()
        ws = _make_ws()
        mgr.register(MEMBER_A, ws)
        mgr.unregister(MEMBER_A, ws)
        assert not mgr.is_online(MEMBER_A)

    def test_unregister_last_connection_removes_member(self):
        mgr = ConnectionManager()
        ws = _make_ws()
        mgr.register(MEMBER_A, ws)
        mgr.unregister(MEMBER_A, ws)
        assert MEMBER_A not in mgr._connections

    def test_multiple_connections_per_member(self):
        """A member can have multiple tabs/connections open."""
        mgr = ConnectionManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        mgr.register(MEMBER_A, ws1)
        mgr.register(MEMBER_A, ws2)
        assert mgr.is_online(MEMBER_A)

        # Remove one — still online
        mgr.unregister(MEMBER_A, ws1)
        assert mgr.is_online(MEMBER_A)

        # Remove last — offline
        mgr.unregister(MEMBER_A, ws2)
        assert not mgr.is_online(MEMBER_A)

    def test_unregister_unknown_member_no_error(self):
        """Unregistering a member who isn't registered is a no-op."""
        mgr = ConnectionManager()
        ws = _make_ws()
        mgr.unregister(MEMBER_A, ws)  # should not raise

    def test_unregister_unknown_ws_no_error(self):
        """Unregistering a ws that isn't in the set is a no-op."""
        mgr = ConnectionManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        mgr.register(MEMBER_A, ws1)
        mgr.unregister(MEMBER_A, ws2)  # ws2 was never registered
        assert mgr.is_online(MEMBER_A)


class TestSendToMember:
    async def test_send_to_member_sends_to_all_connections(self):
        mgr = ConnectionManager()
        ws1 = _make_ws()
        ws2 = _make_ws()
        mgr.register(MEMBER_A, ws1)
        mgr.register(MEMBER_A, ws2)

        await mgr.send_to_member(MEMBER_A, {"type": "message", "data": "hello"})

        ws1.send.assert_called_once()
        ws2.send.assert_called_once()

    async def test_send_to_offline_member_no_error(self):
        """Sending to a member with no connections is a no-op."""
        mgr = ConnectionManager()
        await mgr.send_to_member(MEMBER_A, {"type": "message"})  # no raise

    async def test_send_serializes_as_json(self):
        mgr = ConnectionManager()
        ws = _make_ws()
        mgr.register(MEMBER_A, ws)

        await mgr.send_to_member(MEMBER_A, {"type": "test", "count": 42})

        sent = ws.send.call_args[0][0]
        import json
        parsed = json.loads(sent)
        assert parsed["type"] == "test"
        assert parsed["count"] == 42


class TestBroadcastToConversation:
    async def test_broadcast_sends_to_all_online_participants(self):
        mgr = ConnectionManager()
        ws_a = _make_ws()
        ws_b = _make_ws()
        mgr.register(MEMBER_A, ws_a)
        mgr.register(MEMBER_B, ws_b)

        participant_ids = [MEMBER_A, MEMBER_B, MEMBER_C]
        await mgr.broadcast_to_participants(
            participant_ids, {"type": "message"}, exclude_member_id=None,
        )

        ws_a.send.assert_called_once()
        ws_b.send.assert_called_once()
        # MEMBER_C is offline — no error

    async def test_broadcast_excludes_sender(self):
        mgr = ConnectionManager()
        ws_a = _make_ws()
        ws_b = _make_ws()
        mgr.register(MEMBER_A, ws_a)
        mgr.register(MEMBER_B, ws_b)

        participant_ids = [MEMBER_A, MEMBER_B]
        await mgr.broadcast_to_participants(
            participant_ids, {"type": "message"}, exclude_member_id=MEMBER_A,
        )

        ws_a.send.assert_not_called()
        ws_b.send.assert_called_once()


class TestOnlineCount:
    def test_online_count_empty(self):
        mgr = ConnectionManager()
        assert mgr.get_online_count() == 0

    def test_online_count_tracks_members(self):
        mgr = ConnectionManager()
        mgr.register(MEMBER_A, _make_ws())
        mgr.register(MEMBER_B, _make_ws())
        assert mgr.get_online_count() == 2

    def test_online_count_multiple_tabs_counted_once(self):
        mgr = ConnectionManager()
        mgr.register(MEMBER_A, _make_ws())
        mgr.register(MEMBER_A, _make_ws())
        assert mgr.get_online_count() == 1
