"""Tests for the chat SSE handler and session management.

Covers:
- POST /chat/message returns text/event-stream
- POST /chat/message rejects empty messages with 400
- GET /chat/history returns welcome state for empty session
- Session creation on first message
- Session persistence (messages saved to context)
- Session pruning (over 50 messages pruned)
- HTML fragment renderers: agent message, tool indicator, transition
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from neos_agent.db.models import AgentSession, Base, Ecosystem
from neos_agent.views.chat import (
    chat_bp,
    render_agent_message,
    render_system_message,
    render_tool_indicator,
    render_transition_indicator,
    render_user_message,
    get_or_create_session,
    save_session,
    _MAX_MESSAGES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_engine():
    """In-memory SQLite engine with all tables created."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_factory(db_engine):
    """Session factory bound to the in-memory engine."""
    return async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )


@pytest_asyncio.fixture
async def seed_ecosystem(db_factory):
    """Insert a default ecosystem and return its id."""
    eco_id = uuid.uuid4()
    async with db_factory() as session:
        eco = Ecosystem(id=eco_id, name="TestEco", status="active")
        session.add(eco)
        await session.commit()
    return eco_id


def _create_test_app(db_factory, name_suffix: str = "") -> Sanic:
    """Build a minimal Sanic app wired to the chat blueprint."""
    app = Sanic(f"test-chat-{uuid.uuid4().hex[:8]}{name_suffix}")
    app.blueprint(chat_bp)

    # Settings stub
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.CLAUDE_MODEL = "claude-sonnet-4-20250514"
    app.ctx.settings = settings
    app.ctx.db = db_factory
    app.ctx.skills = None

    return app


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_returns_sse(db_factory, seed_ecosystem):
    """POST /chat/message returns text/event-stream content type."""
    app = _create_test_app(db_factory)

    # Mock the anthropic client so no real API call is made.
    # The stream context manager needs careful mocking.
    mock_stream_cm = AsyncMock()
    mock_stream_cm.__aenter__ = AsyncMock(return_value=mock_stream_cm)
    mock_stream_cm.__aexit__ = AsyncMock(return_value=False)
    # Simulate an empty async iterator (no events)
    mock_stream_cm.__aiter__ = lambda self: self
    mock_stream_cm.__anext__ = AsyncMock(side_effect=StopAsyncIteration)

    with patch("neos_agent.views.chat.get_or_create_session") as mock_goc:
        mock_session = MagicMock(spec=AgentSession)
        mock_session.skill_name = None
        mock_session.context = {"messages": []}
        mock_session.id = uuid.uuid4()
        mock_goc.return_value = mock_session

        with patch.dict("sys.modules", {"anthropic": MagicMock()}):
            import sys
            mock_anthropic = sys.modules["anthropic"]
            mock_client_instance = AsyncMock()
            mock_client_instance.messages.stream.return_value = mock_stream_cm
            mock_anthropic.AsyncAnthropic.return_value = mock_client_instance
            mock_anthropic.NOT_GIVEN = object()

            with patch("neos_agent.views.chat.save_session", new_callable=AsyncMock):
                _, response = await app.asgi_client.post(
                    "/chat/message",
                    json={"message": "Hello agent"},
                )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_send_message_empty_rejected(db_factory, seed_ecosystem):
    """POST /chat/message with empty message returns 400."""
    app = _create_test_app(db_factory)
    _, response = await app.asgi_client.post(
        "/chat/message",
        json={"message": ""},
    )
    assert response.status_code == 400
    data = response.json
    assert "error" in data


@pytest.mark.asyncio
async def test_send_message_missing_body(db_factory, seed_ecosystem):
    """POST /chat/message with no JSON body returns 400."""
    app = _create_test_app(db_factory)
    _, response = await app.asgi_client.post(
        "/chat/message",
        json={"message": "   "},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_history_empty_session(db_factory, seed_ecosystem):
    """GET /chat/history without session_id returns welcome state."""
    app = _create_test_app(db_factory)
    _, response = await app.asgi_client.get("/chat/history")
    assert response.status_code == 200
    data = response.json
    assert data["messages"] == []
    assert data["welcome"] is True


@pytest.mark.asyncio
async def test_history_nonexistent_session(db_factory, seed_ecosystem):
    """GET /chat/history with unknown session_id returns welcome state."""
    app = _create_test_app(db_factory)
    fake_id = str(uuid.uuid4())
    _, response = await app.asgi_client.get(f"/chat/history?session_id={fake_id}")
    assert response.status_code == 200
    data = response.json
    assert data["messages"] == []
    assert data["welcome"] is True


# ---------------------------------------------------------------------------
# Session management tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_session_creation(db_factory, seed_ecosystem):
    """get_or_create_session creates a new session when none exists."""
    app = MagicMock()
    app.ctx.db = db_factory

    session_id = str(uuid.uuid4())
    agent_session = await get_or_create_session(session_id, app)

    assert agent_session is not None
    assert agent_session.status == "active"
    assert agent_session.context == {"messages": []}


@pytest.mark.asyncio
async def test_session_persistence(db_factory, seed_ecosystem):
    """Messages are saved to session context via save_session."""
    app = MagicMock()
    app.ctx.db = db_factory

    session_id = str(uuid.uuid4())
    agent_session = await get_or_create_session(session_id, app)

    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]
    await save_session(agent_session, messages, app)

    # Reload and verify
    from neos_agent.views.chat import load_session
    reloaded = await load_session(session_id, app)
    assert reloaded is not None
    assert reloaded.context is not None
    assert len(reloaded.context["messages"]) == 2
    assert reloaded.context["messages"][0]["content"] == "hello"


@pytest.mark.asyncio
async def test_session_prune(db_factory, seed_ecosystem):
    """save_session prunes message list to _MAX_MESSAGES."""
    app = MagicMock()
    app.ctx.db = db_factory

    session_id = str(uuid.uuid4())
    agent_session = await get_or_create_session(session_id, app)

    # Create more messages than the limit
    messages = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg-{i}"}
        for i in range(_MAX_MESSAGES + 20)
    ]
    await save_session(agent_session, messages, app)

    from neos_agent.views.chat import load_session
    reloaded = await load_session(session_id, app)
    assert reloaded is not None
    stored_messages = reloaded.context["messages"]
    assert len(stored_messages) == _MAX_MESSAGES
    # Should keep the *last* _MAX_MESSAGES
    assert stored_messages[0]["content"] == f"msg-{20}"


# ---------------------------------------------------------------------------
# HTML renderer tests
# ---------------------------------------------------------------------------

def test_render_agent_message():
    """render_agent_message produces correct HTML structure."""
    html = render_agent_message("Hello world")
    assert "bg-neos-primary" in html
    assert ">A</div>" in html
    assert "Hello world" in html


def test_render_agent_message_with_id():
    """render_agent_message includes optional id attribute."""
    html = render_agent_message("test", message_id="msg-123")
    assert 'id="msg-123"' in html


def test_render_agent_message_escapes_html():
    """render_agent_message escapes dangerous HTML."""
    html = render_agent_message("<script>alert('xss')</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_user_message():
    """render_user_message produces user-styled HTML."""
    html = render_user_message("My question")
    assert "bg-neos-primary" in html
    assert "My question" in html


def test_render_system_message_typing():
    """render_system_message typing includes typing-indicator id."""
    html = render_system_message("typing", "Thinking...")
    assert 'id="typing-indicator"' in html
    assert "text-neos-muted" in html
    assert "Thinking..." in html


def test_render_system_message_error():
    """render_system_message error does not include typing-indicator id."""
    html = render_system_message("error", "Something failed")
    assert "typing-indicator" not in html
    assert "text-red-600" in html


def test_render_tool_indicator():
    """render_tool_indicator shows tool name and status."""
    html = render_tool_indicator("lookup_agreement", "running")
    assert "lookup_agreement" in html
    assert "border-yellow-400" in html
    assert "font-mono" in html


def test_render_tool_indicator_with_args():
    """render_tool_indicator includes args when provided."""
    html = render_tool_indicator("search", "success", args={"query": "test"})
    assert "text-neos-muted" in html
    assert "test" in html


def test_render_transition_indicator():
    """render_transition_indicator shows skill name."""
    html = render_transition_indicator("agreement-creation")
    assert "agreement-creation" in html
    assert "text-neos-primary" in html
    assert "Skill transition:" in html
