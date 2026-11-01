"""Migration s3e8b1d7c4a2 (G-Exchange): exchange columns, category/visibility fixes, authorless and exited posts.

Runs the real upgrade()/downgrade() on a seeded schema whose new columns were dropped first (a pre-migration
database): on SQLite (only the columns SQLite can drop, i.e. those without a foreign key; the others stand for a
create_all database), and on PostgreSQL (throwaway schema, every column) when NEOS_TEST_POSTGRES_URL names a
disposable database; see alembic/AGENTS.md "Data revisions".
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
from neos_agent.db.models import Base, Collaboration, Domain, Ecosystem, Member, SharesNeeds, User

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "s3e8b1d7c4a2_exchange_integrity.py"
ECO = uuid.UUID(int=0xE0)
DOMAIN, OTHER_DOMAIN = uuid.UUID(int=0xD0), uuid.UUID(int=0xD1)
ACTIVE_AUTHOR, EXITED_AUTHOR = uuid.UUID(int=0xA1), uuid.UUID(int=0xA2)
STARTED = dt.date(2026, 3, 1)
CREATED = dt.datetime(2026, 5, 10, 8, 0, 0)
TODAY = dt.date(2026, 11, 1)  # the migration date the runs below pass (its default is the UTC date)
LONG_AGO = dt.date(2025, 3, 1)  # started + 365 days is already past on TODAY: A10's 30-day grace
NEW_COLUMNS = {
    "shares_needs": ("status_reason", "status_changed_by_member_id", "status_changed_at", "fulfilled_by_member_id",
                     "hidden_at", "hidden_by_member_id", "hidden_reason"),
    "collaborations": ("proposed_by_member_id", "ended_by_member_id", "end_reason", "ended_at",
                       "reviewed_by_member_id", "review_note", "reviewed_at"),
}
WITHOUT_FOREIGN_KEY = {"status_reason", "status_changed_at", "hidden_at", "hidden_reason", "end_reason", "ended_at",
                       "review_note", "reviewed_at"}
# post key -> (author, category, visibility, status) before, and (category, visibility, status, reason) after
POSTS = {
    "skill": ((ACTIVE_AUTHOR, "skill", "public", "active"), ("skills", "public", "active", None)),
    "resource": ((ACTIVE_AUTHOR, " Resource ", "public", "active"), ("resources", "public", "active", None)),
    "blank": ((ACTIVE_AUTHOR, "  ", "public", "active"), (None, "public", "active", None)),
    "case": ((ACTIVE_AUTHOR, "Technology", "public", "active"), ("technology", "public", "active", None)),
    "free-text": ((ACTIVE_AUTHOR, "gardening", "public", "active"), ("gardening", "public", "active", None)),
    "private": ((ACTIVE_AUTHOR, "skills", "private", "active"), ("skills", "domain", "active", None)),
    "no-author": ((None, "space", "public", "active"), ("space", "public", "withdrawn",
                                                        "No author on record (legacy post)")),
    "no-author-closed": ((None, "space", "public", "fulfilled"), ("space", "public", "fulfilled", None)),
    "exited": ((EXITED_AUTHOR, "labor", "ecosystem", "active"), ("labor", "ecosystem", "withdrawn", "author left")),
    "exited-closed": ((EXITED_AUTHOR, "labor", "public", "withdrawn"), ("labor", "public", "withdrawn", None)),
}


def _id(key: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"exchange-mig.{key}")


async def _seed(factory) -> None:
    async with factory() as session:
        session.add(Ecosystem(id=ECO, name="Oasis", status="active"))
        session.add_all([User(id=_id("u1"), display_name="Ada"), User(id=_id("u2"), display_name="Bo")])
        await session.flush()
        session.add_all([
            Member(id=ACTIVE_AUTHOR, ecosystem_id=ECO, user_id=_id("u1"), member_id="M-1", display_name="Ada",
                   current_status="active"),
            Member(id=EXITED_AUTHOR, ecosystem_id=ECO, user_id=_id("u2"), member_id="M-2", display_name="Bo",
                   current_status="exited"),
            Domain(id=DOMAIN, ecosystem_id=ECO, domain_id="DOM-1", status="active"),
            Domain(id=OTHER_DOMAIN, ecosystem_id=ECO, domain_id="DOM-2", status="active"),
        ])
        await session.flush()
        for key, ((author, category, visibility, status), _) in POSTS.items():
            session.add(SharesNeeds(id=_id(key), ecosystem_id=ECO, domain_id=DOMAIN, author_member_id=author,
                                    type="need", title=key, category=category, visibility=visibility, status=status))
        session.add_all([
            Collaboration(id=_id("started"), source_domain_id=DOMAIN, target_domain_id=OTHER_DOMAIN, title="a",
                          status="active", started_date=STARTED),
            Collaboration(id=_id("unstarted"), source_domain_id=DOMAIN, target_domain_id=OTHER_DOMAIN, title="b",
                          status="active", created_at=CREATED),
            Collaboration(id=_id("dated"), source_domain_id=DOMAIN, target_domain_id=OTHER_DOMAIN, title="c",
                          status="active", started_date=STARTED, review_date=dt.date(2026, 12, 1)),
            Collaboration(id=_id("proposed"), source_domain_id=DOMAIN, target_domain_id=OTHER_DOMAIN, title="d",
                          status="proposed"),
            Collaboration(id=_id("long-ago"), source_domain_id=DOMAIN, target_domain_id=OTHER_DOMAIN, title="e",
                          status="active", started_date=LONG_AGO),
        ])
        await session.commit()


def _module():
    spec = importlib.util.spec_from_file_location("migration_s3e8b1d7c4a2", MIGRATION_PATH)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def _run(sync_conn, step: str) -> None:
    with Operations.context(MigrationContext.configure(sync_conn)):
        getattr(_module(), step)(**({"today": TODAY} if step == "upgrade" else {}))


def _drop_new_columns(sync_conn, columns) -> None:
    for table, names in NEW_COLUMNS.items():
        for name in names:
            if name in columns:
                sync_conn.execute(sa.text(f"ALTER TABLE {table} DROP COLUMN {name}"))


def _columns(sync_conn, table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(sync_conn).get_columns(table)}


def _read(sync_conn) -> tuple[dict, dict, set]:
    posts = {row.id: row for row in sync_conn.execute(sa.text(
        "SELECT id, category, visibility, status, status_reason FROM shares_needs"))}
    reviews = {row.id: row.review_date for row in sync_conn.execute(sa.text("SELECT id, review_date FROM collaborations"))}
    columns = {f"{t}.{c}" for t in NEW_COLUMNS for c in _columns(sync_conn, t)}
    return posts, reviews, columns


def _key(value) -> str:
    return str(value).replace("-", "").lower()


def _assert_migrated(posts, reviews, columns) -> None:
    assert {f"{t}.{c}" for t, names in NEW_COLUMNS.items() for c in names} <= columns
    by_id = {_key(post_id): row for post_id, row in posts.items()}
    got = {key: tuple(getattr(by_id[_key(_id(key))], f) for f in ("category", "visibility", "status", "status_reason"))
           for key in POSTS}
    assert got == {key: after for key, (_, after) in POSTS.items()}
    review = {_key(cid): str(value)[:10] if value else None for cid, value in reviews.items()}
    assert review[_key(_id("started"))] == str(STARTED + dt.timedelta(days=365))
    assert review[_key(_id("unstarted"))] == str(CREATED.date() + dt.timedelta(days=365))
    assert review[_key(_id("dated"))] == "2026-12-01"  # a review date already set is kept
    assert review[_key(_id("proposed"))] is None  # set on activation, not before
    # A10: a year-old collaboration would be due the day this deploys; it gets the migration date + 30 days instead.
    assert review[_key(_id("long-ago"))] == str(TODAY + dt.timedelta(days=30))


async def _upgrade(engine, drop) -> tuple:
    def step(sync_conn):
        _drop_new_columns(sync_conn, drop)
        _run(sync_conn, "upgrade")
        return _read(sync_conn)

    async with engine.begin() as conn:
        return await conn.run_sync(step)


async def test_upgrade_adds_columns_and_fixes_posts_on_sqlite():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _seed(async_sessionmaker(engine, class_=AsyncSession))
        _assert_migrated(*await _upgrade(engine, WITHOUT_FOREIGN_KEY))
        _assert_migrated(*await _upgrade(engine, set()))  # rerun / create_all database: nothing changes
    finally:
        await engine.dispose()


@pytest.mark.skipif(not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
async def test_upgrade_and_downgrade_on_postgres():
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(os.environ["NEOS_TEST_POSTGRES_URL"],
                                 connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
        await _seed(async_sessionmaker(engine, class_=AsyncSession))
        every_column = {name for names in NEW_COLUMNS.values() for name in names}
        _assert_migrated(*await _upgrade(engine, every_column))

        def foreign_keys(sync_conn) -> set[str]:
            return {fk["constrained_columns"][0] for t in NEW_COLUMNS for fk in sa.inspect(sync_conn).get_foreign_keys(t)}

        async with engine.begin() as conn:
            assert {"status_changed_by_member_id", "fulfilled_by_member_id", "hidden_by_member_id",
                    "proposed_by_member_id", "ended_by_member_id", "reviewed_by_member_id"} <= await conn.run_sync(foreign_keys)
            await conn.run_sync(lambda c: _run(c, "downgrade"))
            remaining = await conn.run_sync(lambda c: {f"{t}.{n}" for t in NEW_COLUMNS for n in _columns(c, t)})
        assert not remaining & {f"{t}.{c}" for t, names in NEW_COLUMNS.items() for c in names}
        _, _, columns = await _upgrade(engine, set())  # and up again (the reasons went with the columns)
        assert {f"{t}.{c}" for t, names in NEW_COLUMNS.items() for c in names} <= columns
    finally:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()
