"""The session-cleanup cron keeps expired sessions an agent token still points to (production FK violation, 2026-11-01)."""
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import neos_agent.db.course_models  # noqa: F401  registers tables the models reference, as main.init_db does
from neos_agent.db.models import AgentToken, AuthChallenge, AuthSession, User
from neos_agent.services.cron import _cleanup_expired_sessions


@pytest.mark.asyncio
async def test_cleanup_removes_expired_rows_but_keeps_sessions_agent_tokens_reference(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    referenced, unreferenced, live = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with factory() as db:
        db.add(User(id=user_id, display_name="Ada"))
        await db.flush()
        db.add_all([
            AuthSession(id=referenced, user_id=user_id, expires_at=now - timedelta(days=2)),
            AuthSession(id=unreferenced, user_id=user_id, expires_at=now - timedelta(days=2)),
            AuthSession(id=live, user_id=user_id, expires_at=now + timedelta(days=2)),
        ])
        await db.flush()
        db.add(AgentToken(user_id=user_id, auth_session_id=referenced, label="laptop agent",
                          token_hash="a" * 64, expires_at=now - timedelta(days=1)))
        db.add(AuthChallenge(did="did:example:ada", challenge="c" * 32, expires_at=now - timedelta(hours=1)))
        await db.commit()

    await _cleanup_expired_sessions(SimpleNamespace(ctx=SimpleNamespace(db=factory)))

    async with factory() as db:
        remaining = set((await db.scalars(select(AuthSession.id))).all())
        challenges = (await db.scalars(select(AuthChallenge.id))).all()
    assert remaining == {referenced, live}
    assert challenges == []
