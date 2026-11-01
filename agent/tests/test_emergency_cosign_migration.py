"""Migration q2a7c5e9d1b3: emergency_states learns pending/withdrawn, the co-signer columns and one live row per ecosystem.

Runs ``upgrade()`` on the pre-revision table shape and on a create_all schema (where it must be a
no-op): always on SQLite (batch rebuild), and on PostgreSQL in a throwaway schema when
NEOS_TEST_POSTGRES_URL names a disposable database. Rules: alembic/AGENTS.md.
"""

from __future__ import annotations

import importlib.util
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.db.models import Base

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "q2a7c5e9d1b3_emergency_cosign.py"
ECOSYSTEM = uuid.UUID(int=0xE)
SECOND = uuid.UUID(int=0xF)  # two open duplicates: the later declaration stays live
QUIET = uuid.UUID(int=0x10)  # no emergency yet
LEGACY_ROW = uuid.UUID(int=0x1)
RECOVERY_DUPLICATE = uuid.UUID(int=0x2)  # in Recovery beside an open one: the open one stays live
SECOND_OLDER, SECOND_NEWER = uuid.UUID(int=0x3), uuid.UUID(int=0x4)
NEW_COLUMNS = {"declared_by_member_id", "co_signer_member_id", "co_signed_by", "co_signed_at", "authority_days"}
LIVE_INDEX = "uq_emergency_states_one_live"


def _migration():
    spec = importlib.util.spec_from_file_location("migration_q2a7c5e9d1b3", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _legacy_tables(metadata: sa.MetaData) -> None:
    """The table as revision 009 left it: three states, no co-signer columns."""
    sa.Table("ecosystems", metadata, sa.Column("id", sa.Uuid, primary_key=True), sa.Column("name", sa.String(255)))
    sa.Table(
        "emergency_states", metadata,
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("ecosystem_id", sa.Uuid, sa.ForeignKey("ecosystems.id"), nullable=False),
        sa.Column("state", sa.String(50), nullable=False, server_default="closed"),
        sa.Column("declared_at", sa.DateTime), sa.Column("declared_by", sa.String(255)),
        sa.Column("auto_revert_at", sa.DateTime), sa.Column("half_open_entered_at", sa.DateTime),
        sa.Column("closed_at", sa.DateTime), sa.Column("actions_log", sa.JSON), sa.Column("notes", sa.Text),
        sa.Column("post_review_status", sa.String(50)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("state IN ('open', 'half_open', 'closed')", name="ck_emergency_states_valid_state"),
    )


def _run(sync_conn, step: str) -> None:
    with Operations.context(MigrationContext.configure(sync_conn)):
        getattr(_migration(), step)()


EMERGENCY_STATES = sa.table(
    "emergency_states", sa.column("id", sa.Uuid), sa.column("ecosystem_id", sa.Uuid), sa.column("state"),
    sa.column("actions_log", sa.JSON),
)


def _insert(sync_conn, row_id: uuid.UUID, state: str, ecosystem: uuid.UUID = ECOSYSTEM) -> None:
    sync_conn.execute(EMERGENCY_STATES.insert().values(id=row_id, ecosystem_id=ecosystem, state=state, actions_log=[]))


def _refused(sync_conn, state: str, ecosystem: uuid.UUID = ECOSYSTEM) -> None:
    with pytest.raises(sa.exc.IntegrityError):
        with sync_conn.begin_nested():
            _insert(sync_conn, uuid.uuid4(), state, ecosystem)


def _states(sync_conn) -> dict:
    rows = sync_conn.execute(sa.text("SELECT id, state, closed_at, actions_log FROM emergency_states")).all()
    return {uuid.UUID(str(row_id)): (state, closed_at is not None, log) for row_id, state, closed_at, log in rows}


def _assert_upgraded(sync_conn) -> None:
    inspector = sa.inspect(sync_conn)
    assert NEW_COLUMNS <= {column["name"] for column in inspector.get_columns("emergency_states")}
    assert LIVE_INDEX in {index["name"] for index in inspector.get_indexes("emergency_states")}
    legacy = sync_conn.execute(sa.text("SELECT state, notes FROM emergency_states WHERE declared_by = 'Ada'")).one()
    assert tuple(legacy) == ("open", "Flood")  # the existing row survived the rebuild
    _insert(sync_conn, uuid.uuid4(), "withdrawn")
    _insert(sync_conn, uuid.uuid4(), "pending", QUIET)
    _refused(sync_conn, "pending", QUIET)   # one live row per ecosystem
    _refused(sync_conn, "pending")          # beside the open one
    _refused(sync_conn, "resolved", SECOND)  # not a state


def _assert_duplicates_retired(sync_conn) -> None:
    """Duplicates that predate the index close deterministically, each with a note saying why."""
    states = _states(sync_conn)
    assert {row: states[row][:2] for row in (LEGACY_ROW, RECOVERY_DUPLICATE, SECOND_OLDER, SECOND_NEWER)} == {
        LEGACY_ROW: ("open", False), RECOVERY_DUPLICATE: ("closed", True),
        SECOND_OLDER: ("closed", True), SECOND_NEWER: ("open", False),
    }
    log = states[RECOVERY_DUPLICATE][2]
    log = json.loads(log) if isinstance(log, str) else log
    assert log[-1]["action"] == "superseded" and str(LEGACY_ROW) in log[-1]["note"]


def _legacy_flow(sync_conn) -> None:
    metadata = sa.MetaData()
    _legacy_tables(metadata)
    metadata.create_all(sync_conn)
    sync_conn.execute(metadata.tables["ecosystems"].insert(), [
        {"id": ECOSYSTEM, "name": "Oasis"}, {"id": SECOND, "name": "Delta"}, {"id": QUIET, "name": "Quiet"},
    ])
    table = metadata.tables["emergency_states"]
    sync_conn.execute(table.insert().values(
        id=LEGACY_ROW, ecosystem_id=ECOSYSTEM, state="open", declared_by="Ada", notes="Flood",
        declared_at=datetime(2026, 10, 1), actions_log=[{"action": "declared"}],
    ))
    sync_conn.execute(table.insert(), [  # the old dashboard never stopped a second declaration
        {"id": RECOVERY_DUPLICATE, "ecosystem_id": ECOSYSTEM, "state": "half_open",
         "declared_at": datetime(2026, 10, 20), "actions_log": [{"action": "declared"}]},
        {"id": SECOND_OLDER, "ecosystem_id": SECOND, "state": "open", "declared_at": datetime(2026, 10, 2),
         "actions_log": None},
        {"id": SECOND_NEWER, "ecosystem_id": SECOND, "state": "open", "declared_at": datetime(2026, 10, 3),
         "actions_log": None},
    ])
    with pytest.raises(sa.exc.IntegrityError):  # the old CHECK refuses the new state
        with sync_conn.begin_nested():
            sync_conn.execute(table.insert().values(id=uuid.uuid4(), ecosystem_id=ECOSYSTEM, state="pending"))
    _run(sync_conn, "upgrade")
    _assert_duplicates_retired(sync_conn)
    _assert_upgraded(sync_conn)
    before = _states(sync_conn)
    _run(sync_conn, "upgrade")  # a second run finds nothing to do
    assert _states(sync_conn) == before
    _run(sync_conn, "downgrade")
    assert sync_conn.execute(sa.text("SELECT count(*) FROM emergency_states WHERE state = 'pending'")).scalar() == 0
    assert LIVE_INDEX not in {index["name"] for index in sa.inspect(sync_conn).get_indexes("emergency_states")}
    _run(sync_conn, "upgrade")
    assert NEW_COLUMNS <= {c["name"] for c in sa.inspect(sync_conn).get_columns("emergency_states")}
    assert LIVE_INDEX in {index["name"] for index in sa.inspect(sync_conn).get_indexes("emergency_states")}


def _create_all_flow(sync_conn) -> None:
    Base.metadata.create_all(sync_conn)
    _run(sync_conn, "upgrade")  # already the current shape (index included): no-op
    inspector = sa.inspect(sync_conn)
    assert NEW_COLUMNS <= {column["name"] for column in inspector.get_columns("emergency_states")}
    assert [index["name"] for index in inspector.get_indexes("emergency_states")].count(LIVE_INDEX) == 1


async def _in_fresh_database(url: str, flow, **engine_args) -> None:
    engine = create_async_engine(url, **engine_args)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(flow)
    finally:
        await engine.dispose()


@pytest.mark.parametrize("flow", [_legacy_flow, _create_all_flow])
async def test_upgrade_on_sqlite(flow):
    await _in_fresh_database("sqlite+aiosqlite://", flow)


@pytest.mark.skipif(not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
@pytest.mark.parametrize("flow", [_legacy_flow, _create_all_flow])
async def test_upgrade_on_postgres(flow):
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    url = os.environ["NEOS_TEST_POSTGRES_URL"]
    admin = create_async_engine(url)
    async with admin.begin() as conn:
        await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
    try:
        await _in_fresh_database(url, flow, connect_args={"server_settings": {"search_path": schema}})
    finally:
        async with admin.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()
