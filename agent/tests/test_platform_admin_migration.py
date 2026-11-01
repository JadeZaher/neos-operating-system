"""Migration v1b4e7c9d2f5 (G-Authority): pin the platform home ecosystem by id, once.

Runs the real upgrade()/downgrade() on a create_all schema, on SQLite and (throwaway schema) on PostgreSQL when
NEOS_TEST_POSTGRES_URL names a disposable database; see alembic/AGENTS.md "v1b4e7c9d2f5".
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.db.models import AppSetting, Base, Ecosystem

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "v1b4e7c9d2f5_pin_platform_home.py"
KEY = "platform_home_ecosystem_id"
OLD, MIDDLE, LATER = datetime(2026, 1, 1), datetime(2026, 2, 1), datetime(2026, 10, 15)
SEEDED_TOGETHER = datetime(2026, 10, 31, 12, 35, 13)  # a seed inserts every ecosystem in one transaction


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"platform-home-mig.{key}")


REAL = ("real", "OmniOne", OLD, None)
SQUAT = ("squat", "omnione", LATER, None)
RIVER = ("river", "Riverbank", MIDDLE, None)
FRESH = ("fresh", "Fresh Start", LATER, None)

# (ecosystems as (key, name, created_at, founded_date), SIGNUP_DEFAULT_ECOSYSTEM_SLUG, pin already there, pinned key)
SCENARIOS = [
    pytest.param([SQUAT, REAL, RIVER], "", None, "real", id="the oldest 'omnione' wins over a later squatter"),
    pytest.param([("late", "OMNIONE", SEEDED_TOGETHER, date(2026, 9, 1)), ("early", "OmniOne", SEEDED_TOGETHER, date(2026, 5, 4))],
                 "", None, "early", id="equal created_at: the earlier founded_date wins, as at sign-up"),
    pytest.param([REAL, RIVER], "riverbank", None, "river", id="the configured sign-up slug"),
    pytest.param([REAL, RIVER], str(_id("river")), None, "river", id="the configured sign-up id"),
    pytest.param([RIVER, FRESH], "", None, None, id="nothing matches: no pin (fail closed)"),
    pytest.param([REAL, RIVER], "", "river", "river", id="an existing pin is never changed"),
]
POSTGRES = os.environ.get("NEOS_TEST_POSTGRES_URL")
BACKENDS = [
    pytest.param("sqlite", id="sqlite"),
    pytest.param("postgresql", id="postgresql",
                 marks=pytest.mark.skipif(not POSTGRES, reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")),
]


def _migration():
    spec = importlib.util.spec_from_file_location("migration_v1b4e7c9d2f5", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.asynccontextmanager
async def _engine(backend: str):
    """A create_all database: in-memory SQLite, or a throwaway schema on the disposable PostgreSQL."""
    if backend == "sqlite":
        engine = create_async_engine("sqlite+aiosqlite://", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        try:
            yield engine
        finally:
            await engine.dispose()
        return
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(POSTGRES, connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()


async def _run(engine, step: str) -> None:
    migration = _migration()

    def run(sync_conn):
        with Operations.context(MigrationContext.configure(sync_conn)):
            getattr(migration, step)()

    async with engine.begin() as conn:
        await conn.run_sync(run)


async def _settings(engine) -> dict[str, dict]:
    """Every app_settings row as key -> value (JSON text on SQLite, decoded on PostgreSQL)."""
    async with engine.connect() as conn:
        rows = (await conn.execute(sa.text("SELECT key, value FROM app_settings"))).all()
    return {key: json.loads(value) if isinstance(value, str) else value for key, value in rows}


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("ecosystems, signup_slug, existing_pin, expected", SCENARIOS)
async def test_upgrade_pins_the_home_once_and_downgrade_removes_only_the_pin(
    monkeypatch, backend, ecosystems, signup_slug, existing_pin, expected,
):
    monkeypatch.setenv("SIGNUP_DEFAULT_ECOSYSTEM_SLUG", signup_slug)
    async with _engine(backend) as engine:
        async with async_sessionmaker(engine, class_=AsyncSession)() as session:
            for key, name, created_at, founded in ecosystems:
                session.add(Ecosystem(id=_id(key), name=name, status="active", founded_date=founded,
                                      created_at=created_at, updated_at=created_at))
                await session.flush()
            session.add(AppSetting(key="ctc_map", value={"kept": True}))
            if existing_pin:
                session.add(AppSetting(key=KEY, value={"ecosystem_id": str(_id(existing_pin))}))
            await session.commit()

        await _run(engine, "upgrade")
        first = await _settings(engine)
        await _run(engine, "upgrade")  # idempotent: a second run finds the row and leaves it
        second = await _settings(engine)
        await _run(engine, "downgrade")
        after_downgrade = await _settings(engine)

    pinned = {KEY: {"ecosystem_id": str(_id(expected))}} if expected else {}
    assert first == second == {"ctc_map": {"kept": True}, **pinned}
    assert after_downgrade == {"ctc_map": {"kept": True}}
