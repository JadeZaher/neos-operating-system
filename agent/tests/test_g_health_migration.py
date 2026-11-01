"""G-Maint migration u7d2f4b8a3c6 and the UTC session pin (alembic/AGENTS.md "Data revisions").

The revision runs on SQLite always and on PostgreSQL when NEOS_TEST_POSTGRES_URL names a disposable database
(a throwaway schema, as tests/test_uxqa_p1_migration.py). The UTC pin test needs PostgreSQL: it gives the
database a non-UTC default (the study DB runs America/Denver) and checks an engine from db/session.py still
reads and writes UTC.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import os
import uuid
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.db.models import Base
from neos_agent.db.session import create_db_engine

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "u7d2f4b8a3c6_maintenance_health.py"
TODAY = dt.date(2026, 11, 1)
ECO = uuid.UUID(int=0xE1)
PG_URL = os.environ.get("NEOS_TEST_POSTGRES_URL")
needs_postgres = pytest.mark.skipif(not PG_URL, reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")


def _migration():
    spec = importlib.util.spec_from_file_location("migration_u7d2f4b8a3c6", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# key -> (type, status, review_date, sunset_date, ratification_date, updated_at, sunset ceremony day, expected)
AGREEMENTS = {
    "recent": ("organizational", "active", None, None, TODAY - dt.timedelta(days=30), None, None,
               ("review", dt.date(2028, 10, 2))),  # 24 months after it came into force
    "old": ("access", "active", None, None, TODAY - dt.timedelta(days=400), None, None,
            ("review", TODAY + dt.timedelta(days=30))),  # its first review would be long past: 30 days' grace
    "set": ("organizational", "under_review", dt.date(2026, 10, 28), None, None, None, None,
            ("review", dt.date(2026, 10, 28))),  # already dated: untouched
    "draft": ("organizational", "draft", None, None, None, None, None, ("review", None)),  # not in force
    "ending": ("organizational", "sunset", None, None, None, dt.datetime(2026, 10, 30, 9), TODAY - dt.timedelta(days=11),
               ("sunset", TODAY + dt.timedelta(days=49))),  # 60 days after the sunset ceremony
    "ending-legacy": ("organizational", "sunset", None, None, None, dt.datetime(2026, 10, 21, 9), None,
                      ("sunset", dt.date(2026, 12, 20))),  # no ceremony: 60 days after its last update
}
IDS = {key: uuid.uuid5(uuid.NAMESPACE_DNS, f"g-maint-migration.{key}") for key in AGREEMENTS}


def _seed(conn) -> None:
    conn.execute(Base.metadata.tables["ecosystems"].insert().values(id=ECO, name="Eco", status="active", visibility="public"))
    agreements, ceremonies = Base.metadata.tables["agreements"], Base.metadata.tables["agreement_ceremonies"]
    for key, (type_, status, review, sunset, ratified, updated, ceremony, _) in AGREEMENTS.items():
        conn.execute(agreements.insert().values(
            id=IDS[key], ecosystem_id=ECO, agreement_id=f"AGR-{key}", type=type_, title=key, version="1.0",
            status=status, hierarchy_level="domain", review_date=review, sunset_date=sunset, ratification_date=ratified,
            requires_explicit_consent=True, alignment_points=5,
            created_at=dt.datetime(2025, 1, 1), updated_at=updated or dt.datetime(2026, 1, 1),
        ))
        if ceremony:
            conn.execute(ceremonies.insert().values(
                id=uuid.uuid4(), agreement_id=IDS[key], stage="sunset", outcome="moved",
                completed_at=dt.datetime.combine(ceremony, dt.time(15, 0)),
                created_at=dt.datetime(2026, 1, 1), updated_at=dt.datetime(2026, 1, 1),
            ))


def _results(conn) -> dict:
    agreements = Base.metadata.tables["agreements"]
    rows = {row.id: row for row in conn.execute(sa.select(agreements.c.id, agreements.c.review_date, agreements.c.sunset_date))}
    found = {}
    for key, spec in AGREEMENTS.items():
        field = spec[-1][0]
        value = getattr(rows[IDS[key]], f"{field}_date")
        found[key] = (field, value if isinstance(value, dt.date) or value is None else dt.date.fromisoformat(str(value)))
    return found


def _expected() -> dict:
    return {key: spec[-1] for key, spec in AGREEMENTS.items()}


def _columns(conn) -> set[str]:
    return {column["name"] for column in sa.inspect(conn).get_columns("governance_health_audits")}


def _run(conn, step: str) -> None:
    migration = _migration()
    with Operations.context(MigrationContext.configure(conn)):
        migration.upgrade(today=TODAY) if step == "upgrade" else migration.downgrade()


def _exercise(conn) -> None:
    """The whole revision on a pre-migration schema: column added, dates filled, rerun idempotent, downgrade drops it."""
    _seed(conn)
    _run(conn, "upgrade")
    assert "self_assessment" in _columns(conn)
    assert _results(conn) == _expected()
    _run(conn, "upgrade")  # rerun: the column exists and nothing is NULL any more
    assert _results(conn) == _expected()
    _run(conn, "downgrade")
    assert "self_assessment" not in _columns(conn)


def test_the_revision_on_sqlite():
    engine = sa.create_engine("sqlite://")
    with engine.begin() as conn:
        Base.metadata.create_all(conn)
        conn.execute(sa.text("ALTER TABLE governance_health_audits DROP COLUMN self_assessment"))
        _exercise(conn)


@pytest.mark.asyncio
@needs_postgres
async def test_the_revision_on_postgres():
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(PG_URL, connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(sa.text("ALTER TABLE governance_health_audits DROP COLUMN self_assessment"))
            await conn.run_sync(_exercise)
    finally:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()


SET_DENVER = ("DO $$ BEGIN EXECUTE format('ALTER DATABASE %I SET timezone TO %L', current_database(), "
              "'America/Denver'); END $$")
RESET = "DO $$ BEGIN EXECUTE format('ALTER DATABASE %I RESET timezone', current_database()); END $$"


@pytest.mark.asyncio
@needs_postgres
async def test_sessions_read_and_write_utc_on_a_database_whose_default_is_not_utc():
    admin = create_async_engine(PG_URL)
    async with admin.begin() as conn:
        await conn.execute(sa.text(SET_DENVER))
    plain, pinned = create_async_engine(PG_URL), await create_db_engine(PG_URL)
    try:
        async with plain.connect() as conn:
            assert await conn.scalar(sa.text("SHOW timezone")) == "America/Denver"  # the study DB's setting
            local_now = await conn.scalar(sa.text("SELECT now()::timestamp"))
        async with pinned.begin() as conn:
            assert await conn.scalar(sa.text("SHOW timezone")) == "UTC"
            await conn.execute(sa.text("CREATE TEMP TABLE stamped (at timestamp DEFAULT now())"))
            await conn.execute(sa.text("INSERT INTO stamped DEFAULT VALUES"))
            stamped = await conn.scalar(sa.text("SELECT at FROM stamped"))
        utc_now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
        assert abs(stamped - utc_now) < dt.timedelta(minutes=5)  # server_default=now() is naive UTC
        assert abs(local_now - utc_now) > dt.timedelta(hours=5)  # unpinned, it would be Denver wall time
    finally:
        async with admin.begin() as conn:
            await conn.execute(sa.text(RESET))
        for engine in (plain, pinned, admin):
            await engine.dispose()
