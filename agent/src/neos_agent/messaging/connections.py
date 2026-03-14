"""WebSocket connection manager for real-time messaging.

Tracks active WebSocket connections per member and provides methods
to send messages to individual members or broadcast to conversation
participants.
"""

from __future__ import annotations

import json
import logging
import uuid

logger = logging.getLogger(__name__)


class ConnectionManager:
    """In-memory registry of active WebSocket connections keyed by member_id.

    A member can have multiple connections (multiple browser tabs).
    """

    def __init__(self):
        self._connections: dict[uuid.UUID, set] = {}

    def register(self, member_id: uuid.UUID, ws) -> None:
        """Add a WebSocket connection for a member."""
        if member_id not in self._connections:
            self._connections[member_id] = set()
        self._connections[member_id].add(ws)
        logger.debug("Registered WS for member %s (%d total)", member_id, len(self._connections[member_id]))

    def unregister(self, member_id: uuid.UUID, ws) -> None:
        """Remove a WebSocket connection for a member."""
        conns = self._connections.get(member_id)
        if conns is None:
            return
        conns.discard(ws)
        if not conns:
            del self._connections[member_id]
            logger.debug("Member %s fully disconnected", member_id)

    def is_online(self, member_id: uuid.UUID) -> bool:
        """Check if a member has any active connections."""
        return member_id in self._connections and len(self._connections[member_id]) > 0

    def get_online_count(self) -> int:
        """Return the number of distinct online members."""
        return len(self._connections)

    async def send_to_member(self, member_id: uuid.UUID, payload: dict) -> None:
        """Send a JSON payload to all connections for a member."""
        conns = self._connections.get(member_id)
        if not conns:
            return
        data = json.dumps(payload, default=str)
        for ws in list(conns):
            try:
                await ws.send(data)
            except Exception:
                logger.debug("Failed to send to member %s, removing stale connection", member_id)
                conns.discard(ws)

    async def broadcast_to_participants(
        self,
        participant_member_ids: list[uuid.UUID],
        payload: dict,
        exclude_member_id: uuid.UUID | None = None,
    ) -> None:
        """Send a JSON payload to all online participants of a conversation.

        Args:
            participant_member_ids: List of member UUIDs who are in the conversation.
            payload: The message payload to send.
            exclude_member_id: Optional member to exclude (typically the sender).
        """
        for mid in participant_member_ids:
            if mid == exclude_member_id:
                continue
            await self.send_to_member(mid, payload)


# Module-level singleton instance
connection_manager = ConnectionManager()
