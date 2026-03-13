"""Async database engine and session factory.

Integrated with Sanic lifecycle hooks. Does not import Sanic at module
level to allow testing without a running app.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _ensure_async_url(url: str) -> str:
    """Ensure the URL uses the asyncpg driver (Railway provides plain postgresql://)."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


async def create_db_engine(database_url: str, **kwargs: Any) -> AsyncEngine:
    """Create an async SQLAlchemy engine."""
    return create_async_engine(_ensure_async_url(database_url), **kwargs)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory with expire_on_commit=False."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def setup_db(app: Any, loop: Any) -> None:
    """Sanic before_server_start listener: create engine and session factory.

    Stores session factory on app.ctx.db and engine on app.ctx.db_engine.
    """
    settings = app.ctx.settings
    engine = await create_db_engine(settings.DATABASE_URL, echo=(settings.LOG_LEVEL == "debug"))
    app.ctx.db_engine = engine
    app.ctx.db = create_session_factory(engine)


async def teardown_db(app: Any, loop: Any) -> None:
    """Sanic after_server_stop listener: dispose engine."""
    engine = getattr(app.ctx, "db_engine", None)
    if engine is not None:
        await engine.dispose()
