"""UX-QA pass 02 (ACT lifecycle), lane 2: opening a conversation clears its unread badge.

Drives the real messaging blueprint over an in-memory SQLite DB as two members
of one DM, through the same REST calls the client makes: the conversation list
(badge), the conversation detail and the paginated message history (reads),
and the REST send.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest_asyncio
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.api.errors import register_api_errors
from neos_agent.api.messaging import messaging_api_bp
from neos_agent.db.models import (
    Base,
    Conversation,
    ConversationParticipant,
    Ecosystem,
    Member,
    Message,
    User,
)

ECO = uuid.UUID("0000000b-0000-0000-0000-000000000001")
DM = uuid.UUID("0000000b-0000-0000-0000-0000000000c1")
PEOPLE = {
    key: SimpleNamespace(
        user_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"uxqa-p2.{key}.user"),
        member_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"uxqa-p2.{key}.member"),
        name=name,
    )
    for key, name in (("ada", "Ada"), ("ben", "Ben"))
}


async def _seed(session: AsyncSession) -> None:
    session.add(Ecosystem(id=ECO, name="Oasis", status="active"))
    for p in PEOPLE.values():
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for key, p in PEOPLE.items():
        session.add(Member(
            id=p.member_id, ecosystem_id=ECO, user_id=p.user_id, member_id=f"MEM-{key.upper()}",
            display_name=p.name, current_status="active", role="user",
        ))
    await session.flush()
    session.add(Conversation(id=DM, ecosystem_id=ECO, type="dm", created_by=PEOPLE["ben"].member_id))
    await session.flush()
    for p in PEOPLE.values():
        session.add(ConversationParticipant(conversation_id=DM, member_id=p.member_id, role="member"))
    # Earlier than anything sent during the test, so later sends are strictly newer.
    session.add(Message(
        conversation_id=DM, sender_id=PEOPLE["ben"].member_id, content="Can you look at the lending rules?",
        created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
    ))
    await session.commit()


def _create_app() -> Sanic:
    """Blueprint app; the x-test-as header picks who is signed in."""
    app = Sanic(f"test-uxqa-p2-msg-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        p = PEOPLE[who]
        request.ctx.member = Member(
            id=p.member_id, ecosystem_id=ECO, user_id=p.user_id, member_id="MEM-AUTH",
            display_name=p.name, current_status="active", role="user",
        )
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = [ECO]
        request.ctx.authorized_ecosystem_ids = [ECO]

    app.blueprint(messaging_api_bp)
    return app


@pytest_asyncio.fixture
async def app():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await _seed(session)
    app = _create_app()
    app.ctx.db = session_factory
    yield app
    await engine.dispose()


async def _call(app: Sanic, method: str, who: str, url: str, **kwargs):
    _, resp = await getattr(app.asgi_client, method)(url, headers={"x-test-as": who}, **kwargs)
    assert resp.status in (200, 201), resp.text
    return resp.json


async def _unread(app: Sanic, who: str) -> int:
    body = await _call(app, "get", who, "/api/v1/messaging/conversations")
    (conversation,) = [c for c in body["conversations"] if c["id"] == str(DM)]
    return conversation["unread_count"]


async def test_opening_a_conversation_clears_its_unread_badge(app):
    assert await _unread(app, "ada") == 1

    await _call(app, "get", "ada", f"/api/v1/messaging/conversations/{DM}")
    assert await _unread(app, "ada") == 0

    # Her own reply is never unread to her.
    await _call(app, "post", "ada", f"/api/v1/messaging/conversations/{DM}/messages", json={"content": "On it"})
    assert await _unread(app, "ada") == 0

    # Ben's next message is unread again until she opens the history.
    await _call(app, "post", "ben", f"/api/v1/messaging/conversations/{DM}/messages", json={"content": "Thanks"})
    assert await _unread(app, "ada") == 1
    await _call(app, "get", "ada", f"/api/v1/messaging/conversations/{DM}/messages")
    assert await _unread(app, "ada") == 0


async def test_reading_is_per_member(app):
    await _call(app, "post", "ada", f"/api/v1/messaging/conversations/{DM}/messages", json={"content": "On it"})
    await _call(app, "get", "ada", f"/api/v1/messaging/conversations/{DM}")

    # Ada opening the DM does not mark Ada's reply read for Ben.
    assert await _unread(app, "ben") == 1
