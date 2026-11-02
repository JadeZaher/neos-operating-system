"""Disabled account rejection precedes MCP token liveness updates."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
import uuid

import pytest

pytest.importorskip("mcp.server.fastmcp")
from neos_agent import mcp_server  # noqa: E402


async def test_disabled_token_owner_is_refused_without_network_or_logging_private_data(monkeypatch):
    token = SimpleNamespace(id=uuid.uuid4(), user_id=uuid.uuid4(), auth_session_id=uuid.uuid4(), revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1), last_used_at=None)
    user = SimpleNamespace(id=token.user_id, disabled_at=datetime.now())
    session = SimpleNamespace(scalar=AsyncMock(side_effect=[token, token.auth_session_id]), get=AsyncMock(return_value=user), commit=AsyncMock())
    class Context:
        async def __aenter__(self):
            return session
        async def __aexit__(self, *_):
            return False
    monkeypatch.setattr(mcp_server, "_db", lambda: lambda: Context())
    context = SimpleNamespace(request_context=SimpleNamespace(request=SimpleNamespace(headers={"authorization": "Bearer fixture-only-token"})))
    with pytest.raises(ValueError, match="owner no longer exists"):
        await mcp_server._caller(context)
    assert token.last_used_at is None
    session.commit.assert_not_awaited()
