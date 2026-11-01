"""Logout must end the session even when an agent token references it (FK made the old delete fail silently)."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.auth import auth_api_bp
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import AgentToken, AuthSession, Base, Ecosystem, Member, User

SECRET = "test-secret-for-logout-1234567890abcdef"
ECO = uuid.UUID("0000000f-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_logout_ends_a_session_an_agent_token_references():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    now = datetime.now(timezone.utc)
    async with factory() as db:
        db.add_all([Ecosystem(id=ECO, name="Oasis", status="active"), User(id=user_id, display_name="Ada")])
        await db.flush()
        db.add_all([
            Member(id=uuid.uuid4(), ecosystem_id=ECO, user_id=user_id, member_id="MEM-ADA", display_name="Ada",
                   current_status="active", role="user"),
            AuthSession(id=session_id, user_id=user_id, expires_at=now + timedelta(days=1)),
        ])
        await db.flush()
        db.add(AgentToken(user_id=user_id, auth_session_id=session_id, label="laptop agent",
                          token_hash="b" * 64, expires_at=now + timedelta(days=1)))
        await db.commit()

    app = Sanic(f"test-logout-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock(SESSION_SECRET=SECRET)
    app.ctx.db = factory
    app.blueprint(auth_api_bp)
    cookies = {"neos_session": make_session_cookie(str(session_id), SECRET)}

    _, before = await app.asgi_client.get("/api/v1/auth/me", cookies=cookies)
    assert before.status == 200
    _, out = await app.asgi_client.post("/api/v1/auth/logout", cookies=cookies)
    assert out.status == 200
    _, after = await app.asgi_client.get("/api/v1/auth/me", cookies=cookies)
    assert after.status == 401
    await engine.dispose()
