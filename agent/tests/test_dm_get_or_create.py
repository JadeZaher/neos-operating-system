"""Direct threads are one per unordered participant pair.

POST /api/v1/messaging/conversations with type "dm" returns the existing thread
(200) or creates one (201). A lost race hits the pair-key unique index and
returns the winner. Existing duplicate rows are not deleted or merged.
"""

from __future__ import annotations

import asyncio
import importlib.util
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import neos_agent.db.course_models  # noqa: F401
from neos_agent.db.models import Base, Conversation, ConversationParticipant, Ecosystem, Member, User
from neos_agent.messaging.queries import dm_pair_key
from neos_agent.services.member_messaging import _direct_pair, open_thread

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "c1a9e4b7d2f6_dm_pair_key.py"
ECO = uuid.UUID("0000000d-0000-0000-0000-000000000001")


def _ids(name: str) -> tuple[uuid.UUID, uuid.UUID]:
    return (
        uuid.uuid5(uuid.NAMESPACE_DNS, f"dm-pair.{name}.user"),
        uuid.uuid5(uuid.NAMESPACE_DNS, f"dm-pair.{name}.member"),
    )


ADA_USER, ADA = _ids("ada")
BEN_USER, BEN = _ids("ben")
CAI_USER, CAI = _ids("cai")


def _migration():
    spec = importlib.util.spec_from_file_location("migration_c1a9e4b7d2f6", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _run(engine, step: str) -> None:
    migration = _migration()

    def run(sync_conn):
        with Operations.context(MigrationContext.configure(sync_conn)):
            getattr(migration, step)()

    async with engine.begin() as conn:
        await conn.run_sync(run)


async def _people(session: AsyncSession) -> None:
    session.add(Ecosystem(id=ECO, name="Harbor", status="active", visibility="public"))
    for user_id, member_id, name in (
        (ADA_USER, ADA, "Ada"), (BEN_USER, BEN, "Ben"), (CAI_USER, CAI, "Cai"),
    ):
        session.add(User(id=user_id, display_name=name))
    await session.flush()
    for user_id, member_id, name in (
        (ADA_USER, ADA, "Ada"), (BEN_USER, BEN, "Ben"), (CAI_USER, CAI, "Cai"),
    ):
        session.add(Member(
            id=member_id, ecosystem_id=ECO, user_id=user_id, member_id=f"MEM-{name.upper()}",
            display_name=name, current_status="active", role="user",
        ))
    await session.commit()


async def _open(session, creator_id, recipient_id, *, kind="dm", title=None):
    creator = await session.get(Member, creator_id)
    recipient = await session.get(Member, recipient_id)
    others = [recipient]
    if kind == "group":
        others = [recipient, await session.get(Member, CAI if recipient_id != CAI else BEN)]
    return await open_thread(session, (creator, others, kind, title))


@pytest.fixture
async def factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'dm.db'}", poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    made = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with made() as session:
        await _people(session)
    yield made
    await engine.dispose()


async def test_repeating_a_direct_thread_returns_the_same_row(factory):
    async with factory() as session:
        first = await _open(session, ADA, BEN)
        await session.commit()
        first_id = first.id
    async with factory() as session:
        again = await _open(session, ADA, BEN)
        assert again.id == first_id
        assert session.info["reused_dm"] is True
        swapped = await _open(session, BEN, ADA)
        assert swapped.id == first_id
        assert await session.scalar(select(func.count(Conversation.id))) == 1


async def test_a_group_is_a_new_thread_every_time(factory):
    async with factory() as session:
        first = await _open(session, ADA, BEN, kind="group", title="Harbor")
        second = await _open(session, ADA, BEN, kind="group", title="Harbor")
        await session.commit()
        assert first.id != second.id
        assert session.info["reused_dm"] is False
        assert await session.scalar(select(func.count(Conversation.id)).where(Conversation.type == "group")) == 2


async def test_legacy_duplicates_stay_and_the_oldest_is_reused(factory):
    older = uuid.uuid4()
    newer = uuid.uuid4()
    async with factory() as session:
        for conversation_id, created_at in (
            (older, datetime(2024, 1, 1)),
            (newer, datetime(2024, 6, 1)),
        ):
            session.add(Conversation(
                id=conversation_id, ecosystem_id=ECO, type="dm", created_by=ADA, created_at=created_at,
            ))
            await session.flush()
            session.add_all([
                ConversationParticipant(conversation_id=conversation_id, member_id=ADA, role="owner"),
                ConversationParticipant(conversation_id=conversation_id, member_id=BEN, role="member"),
            ])
        await session.commit()
    async with factory() as session:
        reused = await _open(session, BEN, ADA)
        await session.commit()
        assert reused.id == older
        assert await session.scalar(select(func.count(Conversation.id))) == 2
        keys = list((await session.scalars(select(Conversation.dm_pair_key))).all())
        assert keys == [None, None]


async def test_a_lost_insert_returns_the_row_that_won_the_pair_key(factory, monkeypatch):
    async with factory() as session:
        winner = await _open(session, ADA, BEN)
        await session.commit()
        winner_id = winner.id

    calls = {"n": 0}
    real = _direct_pair

    async def miss_once(session, creator_id, recipient_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return await real(session, creator_id, recipient_id)

    monkeypatch.setattr("neos_agent.services.member_messaging._direct_pair", miss_once)
    async with factory() as session:
        found = await _open(session, ADA, BEN)
        assert found.id == winner_id
        assert session.info["reused_dm"] is True
        assert await session.scalar(select(func.count(Conversation.id))) == 1


async def test_two_concurrent_opens_leave_one_direct_thread(factory):
    async def open_as(creator_id, recipient_id):
        async with factory() as session:
            conversation = await _open(session, creator_id, recipient_id)
            await session.commit()
            return conversation.id

    first, second = await asyncio.gather(open_as(ADA, BEN), open_as(BEN, ADA))
    assert first == second
    async with factory() as session:
        assert await session.scalar(select(func.count(Conversation.id))) == 1
        stored = await session.scalar(select(Conversation.dm_pair_key))
    assert stored == dm_pair_key(ADA, BEN)


async def test_pair_key_migration_keeps_duplicate_rows_and_can_run_twice(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'mig.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # The model already has the column. Rebuild the table the way a database looks before this revision:
        # no pair key, and therefore no unique constraint that would refuse the legacy duplicates below.
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        await conn.execute(text(
            "CREATE TABLE conversations_legacy ("
            "id CHAR(32) NOT NULL PRIMARY KEY, ecosystem_id CHAR(32) NOT NULL, type VARCHAR(20) NOT NULL, "
            "title VARCHAR(255), created_by CHAR(32) NOT NULL, "
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, "
            "updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL)"
        ))
        await conn.execute(text(
            "INSERT INTO conversations_legacy (id, ecosystem_id, type, title, created_by, created_at, updated_at) "
            "SELECT id, ecosystem_id, type, title, created_by, created_at, updated_at FROM conversations"
        ))
        await conn.execute(text("DROP TABLE conversations"))
        await conn.execute(text("ALTER TABLE conversations_legacy RENAME TO conversations"))
        await conn.execute(text("CREATE INDEX ix_conversations_ecosystem_id ON conversations (ecosystem_id)"))
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        await _people(session)
    # The column is gone, so these legacy duplicates are inserted as the table looks before the revision.
    async with engine.begin() as conn:
        created = datetime(2024, 1, 1)
        for offset in (0, 1):
            conversation_id = uuid.uuid4().hex
            await conn.execute(text(
                "INSERT INTO conversations (id, ecosystem_id, type, created_by, created_at, updated_at) "
                "VALUES (:id, :eco, 'dm', :by, :at, :at)"
            ), {"id": conversation_id, "eco": ECO.hex, "by": ADA.hex, "at": created + timedelta(days=offset)})
            for member_id in (ADA, BEN):
                await conn.execute(text(
                    "INSERT INTO conversation_participants "
                    "(id, conversation_id, member_id, role, joined_at, muted, created_at, updated_at) "
                    "VALUES (:id, :conversation, :member, 'member', :at, 0, :at, :at)"
                ), {"id": uuid.uuid4().hex, "conversation": conversation_id, "member": member_id.hex,
                    "at": created + timedelta(days=offset)})
        before = await conn.scalar(text("SELECT count(*) FROM conversations"))

    await _run(engine, "upgrade")
    await _run(engine, "upgrade")
    async with engine.connect() as conn:
        columns = {row[1] for row in (await conn.execute(text("PRAGMA table_info(conversations)"))).all()}
        indexes = {row[1] for row in (await conn.execute(text("PRAGMA index_list(conversations)"))).all()}
        remaining = await conn.scalar(text("SELECT count(*) FROM conversations"))
        keys = (await conn.execute(text("SELECT dm_pair_key FROM conversations"))).all()
    assert "dm_pair_key" in columns
    assert "uq_conversations_dm_pair_key" in indexes
    assert remaining == before == 2
    assert keys == [(None,), (None,)]

    key = dm_pair_key(ADA, BEN)
    async with engine.begin() as conn:
        await conn.execute(text(
            "INSERT INTO conversations (id, ecosystem_id, type, created_by, dm_pair_key, created_at, updated_at) "
            "VALUES (:id, :eco, 'dm', :by, :key, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ), {"id": uuid.uuid4().hex, "eco": ECO.hex, "by": ADA.hex, "key": key})
    with pytest.raises(IntegrityError):
        async with engine.begin() as conn:
            await conn.execute(text(
                "INSERT INTO conversations (id, ecosystem_id, type, created_by, dm_pair_key, created_at, updated_at) "
                "VALUES (:id, :eco, 'dm', :by, :key, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ), {"id": uuid.uuid4().hex, "eco": ECO.hex, "by": BEN.hex, "key": key})
    await _run(engine, "downgrade")
    async with engine.connect() as conn:
        columns = {row[1] for row in (await conn.execute(text("PRAGMA table_info(conversations)"))).all()}
        remaining = await conn.scalar(text("SELECT count(*) FROM conversations"))
    assert "dm_pair_key" not in columns
    assert remaining == 3
    await engine.dispose()
