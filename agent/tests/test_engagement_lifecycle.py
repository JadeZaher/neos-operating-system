"""Background shutdown drains transactions before real application teardown."""
import asyncio
from types import SimpleNamespace
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

import neos_agent.db.course_models  # noqa: F401
from neos_agent.config import Settings
from neos_agent.db.models import Base, Ecosystem
from neos_agent.services import engagement_delivery as delivery


async def test_repeated_app_shutdown_drains_worker_before_database_disposal(tmp_path, monkeypatch):
    from neos_agent.db import session as database
    from neos_agent.main import create_app

    url = "sqlite+aiosqlite:///" + (tmp_path / "lifecycle.db").as_posix()
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(Ecosystem.__table__.insert().values(
            id=uuid.uuid4(), name="Lifecycle fixture", status="active"))
        await connection.execute(text("CREATE TABLE lifecycle_marker (id INTEGER PRIMARY KEY)"))
    await engine.dispose()
    state = {"started": asyncio.Event(), "closed": False, "teardowns": 0}
    transports = []

    async def held_transaction(factory, settings, transport, *, stop_event):
        transports.append(transport)
        async with factory() as session:
            await session.execute(text("INSERT INTO lifecycle_marker DEFAULT VALUES"))
            state["started"].set()
            await stop_event.wait()
            await session.commit()
        state["closed"] = True

    original_teardown = database.teardown_db

    async def checked_teardown(app, loop):
        assert state["closed"]
        assert app.ctx.engagement_task.done() and app.ctx.cron_task.done()
        assert app.ctx.engagement_transport is None
        assert transports[-1].client.is_closed
        state["teardowns"] += 1
        await original_teardown(app, loop)

    monkeypatch.setattr(delivery, "run_engagement_cycle", held_transaction)
    monkeypatch.setattr(database, "teardown_db", checked_teardown)
    app = create_app(Settings(_env_file=None, DATABASE_URL=url,
        SESSION_SECRET="lifecycle-test-secret-0123456789abcdef", NEOS_CORE_PATH=str(tmp_path / "no-skills"),
        SIGNUP_DEFAULT_ECOSYSTEM_SLUG="", CORS_ORIGINS="*"))
    app.config.HTTP_AUTO_HEAD = False
    app.config.HTTP_AUTO_OPTIONS = False
    app.config.CORS = False

    @app.on_response
    async def wait_for_worker_write(request, response):
        await asyncio.wait_for(state["started"].wait(), timeout=5)

    for count in (1, 2):
        state.update(started=asyncio.Event(), closed=False)
        _, response = await asyncio.wait_for(app.asgi_client.get("/api/v1/health"), timeout=15)
        assert response.status == 200
        assert state["teardowns"] == count
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                assert await connection.scalar(text("SELECT count(*) FROM lifecycle_marker")) == count
                await connection.execute(text("UPDATE lifecycle_marker SET id = id"))
        finally:
            await engine.dispose()


async def test_stop_during_cycle_prevents_following_delivery_attempts(db_session, monkeypatch):
    from neos_agent.services import engagement
    from sqlalchemy.ext.asyncio import async_sessionmaker

    stopped = asyncio.Event()
    attempts = []

    async def no_op(*args, **kwargs):
        return None

    async def first_attempt(*args):
        attempts.append(True)
        stopped.set()
        return True

    monkeypatch.setattr(engagement, "fanout_pending", no_op)
    monkeypatch.setattr(delivery, "recover_expired_claims", no_op)
    monkeypatch.setattr(delivery, "queue_deliveries", no_op)
    monkeypatch.setattr(delivery, "dispatch_one", first_attempt)
    factory = async_sessionmaker(db_session.bind, expire_on_commit=False)
    await delivery.run_engagement_cycle(factory, SimpleNamespace(), None, stop_event=stopped)
    assert len(attempts) == 1


async def test_stop_wakes_worker_interval_without_waiting_for_next_poll(monkeypatch):
    completed = asyncio.Event()

    async def cycle(*args, **kwargs):
        completed.set()

    monkeypatch.setattr(delivery, "run_engagement_cycle", cycle)
    app = SimpleNamespace(ctx=SimpleNamespace(settings=SimpleNamespace(ENGAGEMENT_WORKER_INTERVAL_SECONDS=30),
        db=None, engagement_stop=asyncio.Event()))
    worker = asyncio.create_task(delivery.run_engagement_loop(app))
    await asyncio.wait_for(completed.wait(), timeout=5)
    app.ctx.engagement_stop.set()
    await asyncio.wait_for(worker, timeout=1)
    assert app.ctx.engagement_transport is None
