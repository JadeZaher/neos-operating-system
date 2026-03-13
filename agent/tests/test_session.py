"""Tests for neos_agent.db.session."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from neos_agent.db.session import create_db_engine, create_session_factory


@pytest_asyncio.fixture
async def engine():
    """Create an in-memory SQLite engine for testing."""
    eng = await create_db_engine("sqlite+aiosqlite://")
    yield eng
    await eng.dispose()


@pytest.mark.asyncio
async def test_create_db_engine_returns_engine():
    """create_db_engine returns an AsyncEngine."""
    engine = await create_db_engine("sqlite+aiosqlite://")
    assert isinstance(engine, AsyncEngine)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_session_factory_returns_callable(engine: AsyncEngine):
    """create_session_factory returns a callable session maker."""
    factory = create_session_factory(engine)
    assert callable(factory)


@pytest.mark.asyncio
async def test_session_factory_produces_session(engine: AsyncEngine):
    """Session factory creates working AsyncSession instances."""
    factory = create_session_factory(engine)
    async with factory() as session:
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1"))
        row = result.scalar()
        assert row == 1


@pytest.mark.asyncio
async def test_session_expire_on_commit_false(engine: AsyncEngine):
    """Session factory is configured with expire_on_commit=False."""
    factory = create_session_factory(engine)
    # expire_on_commit is set on the factory's kw, not the session object
    assert factory.kw.get("expire_on_commit") is False


@pytest.mark.asyncio
async def test_setup_db_attaches_to_app(engine: AsyncEngine):
    """setup_db stores session factory and engine on app.ctx."""
    from unittest.mock import MagicMock
    from neos_agent.db.session import setup_db

    app = MagicMock()
    app.ctx = MagicMock()
    app.ctx.settings = MagicMock()
    app.ctx.settings.DATABASE_URL = "sqlite+aiosqlite://"
    app.ctx.settings.LOG_LEVEL = "info"

    await setup_db(app, None)

    assert app.ctx.db_engine is not None
    assert app.ctx.db is not None
    # Clean up
    await app.ctx.db_engine.dispose()


@pytest.mark.asyncio
async def test_teardown_db_disposes_engine():
    """teardown_db disposes the engine on app.ctx."""
    from unittest.mock import MagicMock, AsyncMock
    from neos_agent.db.session import teardown_db

    mock_engine = AsyncMock()
    app = MagicMock()
    app.ctx.db_engine = mock_engine

    await teardown_db(app, None)

    mock_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_teardown_db_handles_no_engine():
    """teardown_db gracefully handles missing engine."""
    from unittest.mock import MagicMock
    from neos_agent.db.session import teardown_db

    app = MagicMock()
    app.ctx.db_engine = None

    # Should not raise
    await teardown_db(app, None)
