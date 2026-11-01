"""Races on PostgreSQL: two declarations never both stand, two exit confirmations never both write.

Each test holds the competing transaction open in its own session, sends one request through the real
blueprint, waits until PostgreSQL shows that request waiting on a lock, then commits the competitor.
Needs NEOS_TEST_POSTGRES_URL (a disposable database); runs in a throwaway schema. Rules:
src/neos_agent/api/AGENTS.md "Emergency and exit".
"""

from __future__ import annotations

import asyncio
import os
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.api.emergency import ACTIVE_STATES, JUST_DECLARED
from neos_agent.db.models import Base, EmergencyState, ExitRecord, Member, MemberStatusTransition

from . import test_emergency as emergency_flows
from . import test_exit_flows as exit_flows

pytestmark = pytest.mark.skipif(
    not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)",
)


@pytest_asyncio.fixture
async def pg():
    url = os.environ["NEOS_TEST_POSTGRES_URL"]
    schema = f"race_{uuid.uuid4().hex[:12]}"
    admin = create_async_engine(url)
    async with admin.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield SimpleNamespace(admin=admin, db=async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False))
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()


async def _request_waits_on_a_lock(admin, timeout: float = 10.0) -> bool:
    """True once a backend in this database waits on a lock: the request reached the contested row."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        async with admin.connect() as conn:
            waiting = await conn.scalar(text(
                "SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock' AND datname = current_database()"
            ))
        if waiting:
            return True
        await asyncio.sleep(0.05)
    return False


async def test_a_declaration_racing_another_gets_409_and_one_emergency_stands(pg):
    await emergency_flows._seed(pg.db)
    env = SimpleNamespace(app=emergency_flows._app(pg.db), db=pg.db)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with pg.db() as rival:  # a declaration inserted but not yet committed: invisible to the request's check
        rival.add(EmergencyState(id=uuid.uuid4(), ecosystem_id=emergency_flows.OASIS, state="pending",
                                 declared_at=now, declared_by="Cy", actions_log=[]))
        await rival.flush()
        racing = asyncio.create_task(emergency_flows._declare(env, "ben"))
        assert await _request_waits_on_a_lock(pg.admin)  # its insert waits on the unique index
        await rival.commit()
    response = await racing
    assert (response.status, response.json["error"]) == (409, JUST_DECLARED)
    async with pg.db() as session:
        live = await session.scalar(select(func.count()).select_from(EmergencyState).where(
            EmergencyState.ecosystem_id == emergency_flows.OASIS, EmergencyState.state.in_(ACTIVE_STATES),
        ))
    assert live == 1


async def test_two_confirmations_of_one_exit_record_one_departure(pg):
    await exit_flows._seed(pg.db)
    env = SimpleNamespace(app=exit_flows._app(pg.db), db=pg.db)
    filed = await exit_flows._file(env, "ben")
    exit_id = uuid.UUID(filed.json["id"])
    assert (await exit_flows._move(env, "ada", str(exit_id), "unwinding")).status == 200
    ben = exit_flows._row("ben")
    async with pg.db() as first:  # Ada's confirmation, mid-flight: it holds the exit row
        record = (await first.execute(select(ExitRecord).where(ExitRecord.id == exit_id).with_for_update())).scalar_one()
        record.status, record.completed_date = "completed", date.today()
        (await first.get(Member, ben)).current_status = "exited"
        first.add(MemberStatusTransition(id=uuid.uuid4(), member_id=ben, from_status="active", to_status="exited",
                                         date=date.today(), trigger="exit_completed"))
        await first.flush()
        second = asyncio.create_task(exit_flows._move(env, "ari", str(exit_id), "completed"))
        assert await _request_waits_on_a_lock(pg.admin)
        await first.commit()
    response = await second
    assert response.status == 409, response.text  # it re-read the row after Ada's commit
    async with pg.db() as session:
        transitions = await session.scalar(select(func.count()).select_from(MemberStatusTransition).where(
            MemberStatusTransition.member_id == ben,
        ))
    assert transitions == 1
