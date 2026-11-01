"""Migration r6c1e8a4f2d7: repair check-ins get scheduled, legacy statuses become stages, the placeholder goes.

Runs the real ``upgrade()`` on a create_all schema: always on SQLite, and on PostgreSQL (throwaway
schema) when NEOS_TEST_POSTGRES_URL names a disposable database; see alembic/AGENTS.md "Data revisions".
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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.db.models import Base, ConflictCase, Ecosystem, GovernanceHealthAudit, Member, RepairAgreementRecord, User

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "r6c1e8a4f2d7_conflict_care.py"
ECO = uuid.UUID(int=0xC)
CASE = uuid.UUID(int=0xCA)
CREATED = dt.datetime(2026, 9, 1, 9, 0, 0)  # its 30-day check-in is long past
RECENT = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(days=10)
# status written by an older version -> the stage it must end up at (unknown ones stay for a steward)
STATUSES = {"open": "reported", "in_mediation": "in_progress", "escalated": "in_progress",
            "triaged": "triaged", "paused": "paused"}
PLACEHOLDER = "Audit requested. AI analysis pending."


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"care-mig.{key}")


async def _seed(factory) -> None:
    async with factory() as session:
        session.add(Ecosystem(id=ECO, name="Oasis", status="active"))
        await session.flush()
        for key, name in (("dee", "Dee"), ("twin1", "Sam"), ("twin2", " sam ")):
            session.add(User(id=_id(f"user-{key}"), display_name=name))
        await session.flush()
        for key, name in (("dee", "Dee"), ("twin1", "Sam"), ("twin2", " sam ")):
            session.add(Member(id=_id(f"member-{key}"), ecosystem_id=ECO, user_id=_id(f"user-{key}"),
                               member_id=f"M-{key}", display_name=name, current_status="active"))
        session.add(ConflictCase(id=CASE, ecosystem_id=ECO, case_id="CONF-1", title="t",
                                 parties={"respondent": " DEE ", "witness": "Sam", "other": "Nobody"}))
        session.add(ConflictCase(id=_id("listcase"), ecosystem_id=ECO, case_id="CONF-2", title="t", parties=["dee"]))
        session.add_all([ConflictCase(id=_id(f"status-{old}"), ecosystem_id=ECO, case_id=f"CONF-{old}", title="t",
                                      status=old) for old in STATUSES])
        await session.flush()
        session.add_all([
            RepairAgreementRecord(id=_id("unscheduled"), conflict_case_id=CASE, title="a", status="active", created_at=CREATED),
            RepairAgreementRecord(id=_id("recent"), conflict_case_id=CASE, title="r", status="active", created_at=RECENT),
            RepairAgreementRecord(id=_id("fulfilled"), conflict_case_id=CASE, title="b", status="fulfilled", created_at=CREATED),
            RepairAgreementRecord(id=_id("own-dates"), conflict_case_id=CASE, title="c", status="active", created_at=CREATED,
                                  checkin_30_date=dt.date(2026, 9, 5)),
            GovernanceHealthAudit(id=_id("placeholder"), ecosystem_id=ECO, audit_id="A-1", status="draft", findings=PLACEHOLDER),
            GovernanceHealthAudit(id=_id("written"), ecosystem_id=ECO, audit_id="A-2", status="draft", findings="Real notes"),
        ])
        await session.commit()


async def _upgrade_and_read(engine):
    spec = importlib.util.spec_from_file_location("migration_r6c1e8a4f2d7", MIGRATION_PATH)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    def upgrade(sync_conn):
        sync_conn.execute(sa.text("DROP INDEX IF EXISTS ix_conflict_cases_reporter_id"))  # a pre-migration database lacks it
        with Operations.context(MigrationContext.configure(sync_conn)):
            migration.upgrade()
        return {i["name"] for i in sa.inspect(sync_conn).get_indexes("conflict_cases")}

    async with engine.begin() as conn:
        indexes = await conn.run_sync(upgrade)
    async with async_sessionmaker(engine, class_=AsyncSession)() as session:
        repairs = {r.id: (r.checkin_30_date, r.checkin_60_date, r.checkin_90_date)
                   for r in (await session.execute(sa.select(RepairAgreementRecord))).scalars()}
        findings = {a.id: a.findings for a in (await session.execute(sa.select(GovernanceHealthAudit))).scalars()}
        cases = (await session.execute(sa.select(ConflictCase))).scalars().all()
    parties = {c.id: c.parties for c in cases}
    statuses = {c.id: c.status for c in cases}
    return indexes, repairs, findings, parties, statuses


def _check_ins(start: dt.date) -> tuple[dt.date, dt.date, dt.date]:
    return tuple(start + dt.timedelta(days=days) for days in (30, 60, 90))


def _assert_migrated(indexes, repairs, findings, parties, statuses) -> None:
    assert "ix_conflict_cases_reporter_id" in indexes
    # An old repair is followed up from the migration date, not shown overdue three times over.
    assert repairs[_id("unscheduled")] == _check_ins(dt.datetime.now(dt.timezone.utc).date())
    assert repairs[_id("recent")] == _check_ins(RECENT.date())
    assert {old: statuses[_id(f"status-{old}")] for old in STATUSES} == STATUSES
    assert repairs[_id("fulfilled")] == (None, None, None)
    assert repairs[_id("own-dates")] == (dt.date(2026, 9, 5), None, None)
    assert findings == {_id("placeholder"): None, _id("written"): "Real notes"}
    dee = str(_id("member-dee"))
    # Dee matches one member; "Sam" matches two (ambiguous) and "Nobody" none, so both stay non-authorizing labels.
    assert parties[CASE] == {"member_ids": [dee], "labels": ["Dee", "Sam", "Nobody"]}
    assert parties[_id("listcase")] == {"member_ids": [dee], "labels": ["Dee"]}


async def test_upgrade_schedules_check_ins_and_clears_placeholder_on_sqlite():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _seed(async_sessionmaker(engine, class_=AsyncSession))
        _assert_migrated(*await _upgrade_and_read(engine))
        _assert_migrated(*await _upgrade_and_read(engine))  # idempotent
    finally:
        await engine.dispose()


@pytest.mark.skipif(not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
async def test_upgrade_schedules_check_ins_and_clears_placeholder_on_postgres():
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(os.environ["NEOS_TEST_POSTGRES_URL"], connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
        await _seed(async_sessionmaker(engine, class_=AsyncSession))
        _assert_migrated(*await _upgrade_and_read(engine))
    finally:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()
