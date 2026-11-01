"""Migration o7c3e9a5d2f8: per-member rows move to the member row of their own ecosystem; 'objection' blocks.

Runs the whole ``upgrade()`` on a create_all schema: always on SQLite, and on
PostgreSQL (in a throwaway schema) when NEOS_TEST_POSTGRES_URL names a
disposable database. The ranking rule is alembic/AGENTS.md "Data revisions".
"""

from __future__ import annotations

import importlib.util
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.db.models import (
    Base, ConsentParticipant, ConsentRecord, Ecosystem, EthosUserAccess, JourneyMap, Member, Proposal, User,
    UserJourneyProgress,
)

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions"
    / "o7c3e9a5d2f8_rekey_member_rows_and_objection_positions.py"
)

ECO_A = uuid.UUID(int=0xA)
ECO_B = uuid.UUID(int=0xB)
STEWARD_GRANTER = uuid.UUID(int=0x5E)
JOURNEY_B = uuid.UUID(int=0x1B)
SAME_TIME = datetime(2026, 10, 1, 12, 0, 0)
DELETED = "deleted"

# user key -> ecosystems they hold a member row in
USERS = {
    "mover": (ECO_A, ECO_B),
    "orphan": (ECO_A,),
    "keeper": (ECO_A, ECO_B),
    "legacy_wins": (ECO_A, ECO_B),
    "current_wins": (ECO_A, ECO_B),
    "tie": (ECO_A, ECO_B),
}


def _row(user: str, ecosystem: uuid.UUID) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"rekey.{user}.{ecosystem.int}")


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"rekey.row.{key}")


# (key, stored member row, ecosystem, status, completed steps, current step, expected member row or DELETED)
PROGRESS = [
    ("P-MOVE", _row("mover", ECO_A), ECO_B, "in_progress", [0], 1, _row("mover", ECO_B)),
    ("P-MOVER-OWN", _row("mover", ECO_A), ECO_A, "in_progress", [], 0, _row("mover", ECO_A)),  # already right
    ("P-ORPHAN", _row("orphan", ECO_A), ECO_B, "in_progress", [0], 1, _row("orphan", ECO_A)),  # no row in B
    ("P-KEEP", _row("keeper", ECO_B), ECO_B, "in_progress", [0], 1, _row("keeper", ECO_B)),
    ("P-LW-LEGACY", _row("legacy_wins", ECO_A), ECO_B, "complete", [0, 1, 2], 3, _row("legacy_wins", ECO_B)),
    ("P-LW-CURRENT", _row("legacy_wins", ECO_B), ECO_B, "in_progress", [0], 1, DELETED),
    ("P-CW-LEGACY", _row("current_wins", ECO_A), ECO_B, "in_progress", [0], 1, DELETED),
    ("P-CW-CURRENT", _row("current_wins", ECO_B), ECO_B, "in_progress", [0, 1, 2], 3, _row("current_wins", ECO_B)),
    ("P-TIE-OLD-KEY", _row("tie", ECO_A), ECO_B, "in_progress", [0], 1, DELETED),
    ("P-TIE-NEW-KEY", _row("tie", ECO_B), ECO_B, "in_progress", [0], 1, _row("tie", ECO_B)),  # equal: target row wins
]
# (key, stored member row, role, granted_by, expected (member row, granted_by) or DELETED); all in ecosystem B
ACCESS = [
    ("A-MOVE", _row("mover", ECO_A), "member", _row("mover", ECO_A), (_row("mover", ECO_B), _row("mover", ECO_B))),
    ("A-ORPHAN", _row("orphan", ECO_A), "member", _row("orphan", ECO_A), (_row("orphan", ECO_A), _row("orphan", ECO_A))),
    ("A-STEWARD-LEGACY", _row("legacy_wins", ECO_A), "steward", STEWARD_GRANTER,
     (_row("legacy_wins", ECO_B), STEWARD_GRANTER)),
    ("A-MEMBER-CURRENT", _row("legacy_wins", ECO_B), "member", _row("legacy_wins", ECO_B), DELETED),
    ("A-TIE-LEGACY", _row("tie", ECO_A), "member", _row("tie", ECO_A), DELETED),
    ("A-TIE-CURRENT", _row("tie", ECO_B), "member", _row("tie", ECO_B), (_row("tie", ECO_B), _row("tie", ECO_B))),
]
# stored position -> position after the upgrade
POSITIONS = {
    "objection": "object", " Objection ": "object", "OBJECTION": "object",
    "object": "object", "consent": "consent", "objections": "objections", None: None,
}


def _migration():
    spec = importlib.util.spec_from_file_location("migration_o7c3e9a5d2f8", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _seed(factory) -> None:
    async with factory() as session:
        session.add_all([Ecosystem(id=ECO_A, name="A", status="active"), Ecosystem(id=ECO_B, name="B", status="active")])
        for user in USERS:
            session.add(User(id=uuid.uuid5(uuid.NAMESPACE_DNS, f"rekey.{user}"), display_name=user))
        await session.flush()
        for user, ecosystems in USERS.items():
            session.add_all([
                Member(
                    id=_row(user, eco), ecosystem_id=eco, user_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"rekey.{user}"),
                    member_id=f"MEM-{user}-{eco.int}", display_name=user, current_status="active",
                )
                for eco in ecosystems
            ])
        session.add(JourneyMap(id=JOURNEY_B, slug="welcome", title="Welcome", ecosystem_id=ECO_B, content_sequence=[]))
        proposal = Proposal(
            id=_id("proposal"), ecosystem_id=ECO_B, proposal_id="PROP-REKEY", type="policy", title="T",
            version="1.0", status="consent",
        )
        session.add(proposal)
        await session.flush()
        session.add_all([
            UserJourneyProgress(
                id=_id(key), member_id=member, ecosystem_id=eco, journey_map_id=JOURNEY_B, status=status,
                completed_steps=steps, current_step=current, updated_at=SAME_TIME,
            )
            for key, member, eco, status, steps, current, _ in PROGRESS
        ])
        session.add_all([
            EthosUserAccess(
                id=_id(key), member_id=member, ecosystem_id=ECO_B, role_in_ethos=role, access_level="member",
                granted_by=granted_by, granted_at=SAME_TIME,
            )
            for key, member, role, granted_by, _ in ACCESS
        ])
        record = ConsentRecord(id=_id("consent"), proposal_id=proposal.id, consent_mode="consent")
        session.add(record)
        await session.flush()
        session.add_all([
            ConsentParticipant(id=_id(f"position-{stored}"), consent_record_id=record.id, name=str(stored), position=stored)
            for stored in POSITIONS
        ])
        await session.commit()


async def _upgrade_and_read(engine) -> tuple[dict, dict, dict]:
    migration = _migration()

    def upgrade(sync_conn):
        with Operations.context(MigrationContext.configure(sync_conn)):
            migration.upgrade()

    async with engine.begin() as conn:
        await conn.run_sync(upgrade)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        progress = {row.id: row.member_id for row in (await session.execute(sa.select(UserJourneyProgress))).scalars()}
        access = {
            row.id: (row.member_id, row.granted_by)
            for row in (await session.execute(sa.select(EthosUserAccess))).scalars()
        }
        positions = {row.id: row.position for row in (await session.execute(sa.select(ConsentParticipant))).scalars()}
    return progress, access, positions


def _assert_rekeyed(progress: dict, access: dict, positions: dict) -> None:
    assert progress == {_id(key): expected for key, *_, expected in PROGRESS if expected != DELETED}
    assert access == {_id(key): expected for key, *_, expected in ACCESS if expected != DELETED}
    assert positions == {_id(f"position-{stored}"): after for stored, after in POSITIONS.items()}


async def test_upgrade_rekeys_rows_keeps_the_most_advanced_and_normalizes_objections_on_sqlite():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _seed(async_sessionmaker(engine, class_=AsyncSession))
        _assert_rekeyed(*await _upgrade_and_read(engine))
        # A second run finds nothing mis-keyed and changes nothing.
        _assert_rekeyed(*await _upgrade_and_read(engine))
    finally:
        await engine.dispose()


@pytest.mark.skipif(not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
async def test_upgrade_rekeys_rows_keeps_the_most_advanced_and_normalizes_objections_on_postgres():
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(
        os.environ["NEOS_TEST_POSTGRES_URL"],
        connect_args={"server_settings": {"search_path": schema}},
    )
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
        await _seed(async_sessionmaker(engine, class_=AsyncSession))
        _assert_rekeyed(*await _upgrade_and_read(engine))
    finally:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()
