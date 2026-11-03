"""Actual PostgreSQL queue/event locking and migration checks on disposable local schemas."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import importlib.util
import os
from pathlib import Path
from urllib.parse import urlsplit
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import func, inspect, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from alembic.migration import MigrationContext
from alembic.operations import Operations

import neos_agent.db.course_models  # noqa: F401
from neos_agent.db.models import Base
from neos_agent.db.models.engagement import EngagementEvent, EngagementInboxItem, NotificationDelivery
from neos_agent.services import engagement as service
from .test_engagement_core import make_event, seed_world


async def test_persisted_untargeted_event_appears_in_activity(postgres_engagement):
    from .test_engagement_core import assert_untargeted_event_appears_in_activity
    factory, ids, _ = postgres_engagement
    await assert_untargeted_event_appears_in_activity(factory, ids)


@pytest_asyncio.fixture
async def postgres_engagement():
    url = os.environ.get("NEOS_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set NEOS_TEST_POSTGRES_URL to a disposable local PostgreSQL database")
    if not url.startswith("postgresql+asyncpg://") or urlsplit(url).hostname not in ("localhost", "127.0.0.1", "::1"):
        pytest.fail("Engagement race tests require a disposable local PostgreSQL database")
    schema = "engagement_race_" + uuid.uuid4().hex
    admin = create_async_engine(url)
    async with admin.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        ids = await seed_world(factory)
        yield factory, ids, engine
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin.dispose()


async def test_two_workers_fanout_once_with_skip_locked(postgres_engagement):
    factory, ids, _ = postgres_engagement
    async with factory() as session:
        await make_event(session, ids)
        await session.commit()

    async def worker():
        async with factory() as session:
            result = await service.fanout_pending(session)
            await asyncio.sleep(0.05)
            await session.commit()
            return result
    results = await asyncio.gather(worker(), worker())
    assert sum(result["events"] for result in results) == 1
    async with factory() as session:
        rows = (await session.scalars(select(EngagementInboxItem))).all()
        assert {row.user_id for row in rows} == {ids["peer"], ids["dual"]}
        assert len(rows) == 2


async def test_concurrent_occurrence_ingestion_has_single_record(postgres_engagement):
    factory, ids, _ = postgres_engagement
    barrier = asyncio.Event()
    ready = 0

    async def writer():
        nonlocal ready
        async with factory() as session:
            ready += 1
            if ready == 2:
                barrier.set()
            await barrier.wait()
            row = await make_event(session, ids, key="same-persisted-occurrence")
            await session.commit()
            return row.id
    identities = await asyncio.gather(writer(), writer())
    assert identities[0] == identities[1]
    async with factory() as session:
        assert await session.scalar(select(func.count(EngagementEvent.id))) == 1


async def test_claim_race_and_expired_started_sms_is_not_resent(postgres_engagement):
    from neos_agent.services.engagement_delivery import claim_delivery, finish_attempt, recover_expired_claims
    from neos_agent.services.engagement_providers import SendResult
    factory, ids, _ = postgres_engagement
    now = service.utcnow()
    delivery_id = uuid.uuid4()
    async with factory() as session:
        session.add(NotificationDelivery(id=delivery_id, delivery_key="sms-race", user_id=ids["peer"],
            channel="sms", event_ids=[], state="pending", due_at=now - timedelta(seconds=1)))
        await session.commit()

    async def claim():
        async with factory() as session:
            result = await claim_delivery(session, now=now)
            await asyncio.sleep(0.05)
            await session.commit()
            return result
    results = await asyncio.gather(claim(), claim())
    claims = [result for result in results if result is not None]
    assert len(claims) == 1
    _, token = claims[0]
    async with factory() as session:
        row = await session.get(NotificationDelivery, delivery_id)
        row.state = "sending"
        row.attempt_started_at = now
        row.first_attempt_at = now
        row.lease_expires_at = now + timedelta(seconds=1)
        await session.commit()
    async with factory() as session:
        assert await recover_expired_claims(session, now=now + timedelta(seconds=2)) == 1
        await session.commit()
    async with factory() as session:
        assert await claim_delivery(session, now=now + timedelta(seconds=3)) is None
        assert (await session.get(NotificationDelivery, delivery_id)).state == "ambiguous"
    assert await finish_attempt(factory, delivery_id, token, SendResult("accepted", provider_id="late-worker")) is False


async def test_migration_is_repeatable_and_preserves_existing_records(postgres_engagement):
    factory, ids, engine = postgres_engagement
    path = Path(__file__).resolve().parents[1] / "alembic/versions/z6f0c4e8b2d5_engagement.py"
    module_spec = importlib.util.spec_from_file_location("engagement_migration", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    async with factory() as session:
        await make_event(session, ids)
        await session.commit()

    def upgrade(connection):
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
            module.upgrade()
        columns = {column["name"] for column in inspect(connection).get_columns("notification_consumptions")}
        assert "target_key" in columns
        foreign = inspect(connection).get_foreign_keys("engagement_push_devices")
        assert any(key["referred_table"] == "auth_sessions" and key["options"].get("ondelete") == "SET NULL" for key in foreign)
    async with engine.begin() as connection:
        await connection.run_sync(upgrade)
    async with factory() as session:
        assert await session.scalar(select(func.count(EngagementEvent.id))) == 1


async def test_frozen_migration_creates_missing_tables_compatible_with_models(postgres_engagement):
    factory, ids, engine = postgres_engagement
    path = Path(__file__).resolve().parents[1] / "alembic/versions/z6f0c4e8b2d5_engagement.py"
    module_spec = importlib.util.spec_from_file_location("engagement_migration_fresh", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)

    def recreate(connection):
        with Operations.context(MigrationContext.configure(connection)):
            module.downgrade()
            module.upgrade()
            module.upgrade()
        for table in module._tables():
            actual = {column["name"] for column in inspect(connection).get_columns(table.name)}
            assert actual == set(Base.metadata.tables[table.name].columns.keys())
    async with engine.begin() as connection:
        await connection.run_sync(recreate)
    async with factory() as session:
        event = await make_event(session, ids)
        await session.commit()
        assert await session.get(EngagementEvent, event.id)
