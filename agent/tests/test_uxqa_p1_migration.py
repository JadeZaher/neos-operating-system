"""Migration n6a1d4f8b2c5 backfills: proposal author links and domain names.

The SQLite test drives the portable backfill paths (the proposer SQL and the
row-by-row domain-name fallback) on a create_all schema. The PostgreSQL test
runs the whole ``upgrade()`` (DDL plus the ``split_part`` backfill production
uses) against a pre-migration copy of the schema in a throwaway schema; it runs
only when NEOS_TEST_POSTGRES_URL names a disposable database.
"""

from __future__ import annotations

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
from neos_agent.db.models import Base, Domain, Ecosystem, Member, Proposal, User

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / "n6a1d4f8b2c5_proposal_author_and_domain_name.py"
)

ECO_A = uuid.UUID(int=0xA)
ECO_B = uuid.UUID(int=0xB)
ADA_A, BEN_1, BEN_2, CY, ADA_B = (uuid.UUID(int=n) for n in (0xA1, 0xB1, 0xB2, 0xC1, 0xA2))


def _migration():
    spec = importlib.util.spec_from_file_location("migration_n6a1d4f8b2c5", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _proposal(key: str, ecosystem_id: uuid.UUID, proposer: str | None, linked: uuid.UUID | None = None) -> Proposal:
    return Proposal(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, key), ecosystem_id=ecosystem_id, proposal_id=key,
        type="policy", title=key, version="1.0", status="draft", proposer=proposer,
        proposer_member_id=linked,
    )


def _domain(key: str, purpose: str | None, name: str | None = None) -> Domain:
    return Domain(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, key), ecosystem_id=ECO_A, domain_id=key,
        version="1.0", status="active", purpose=purpose, name=name,
    )


# (proposal key, ecosystem, proposer text, pre-existing link, expected link)
PROPOSALS = [
    ("P-UNIQUE", ECO_A, "  ada ", None, ADA_A),  # case and whitespace insensitive
    ("P-AMBIGUOUS", ECO_A, "Ben", None, None),  # two members share the name
    ("P-UNKNOWN", ECO_A, "Zed", None, None),
    ("P-BLANK", ECO_A, "  ", None, None),
    ("P-NONE", ECO_A, None, None, None),
    ("P-OTHER-ECO", ECO_B, "Ada", None, ADA_B),  # never links across ecosystems
    ("P-LINKED", ECO_A, "Ada", CY, CY),  # an existing link is never overwritten
]
# (domain key, purpose, existing name, expected name)
DOMAINS = [
    ("D-PREFIX", "Newcomer Garden — a shared garden", None, "Newcomer Garden"),
    ("D-NO-SEPARATOR", "Just a purpose", None, None),
    ("D-TOO-LONG", ("x" * 121) + " — too long to be a name", None, None),
    ("D-NAMED", "Other — something", "Kept", "Kept"),
    ("D-NO-PURPOSE", None, None, None),
]


async def _seed(factory, *, with_existing_values: bool) -> None:
    async with factory() as session:
        session.add_all([Ecosystem(id=ECO_A, name="A", status="active"), Ecosystem(id=ECO_B, name="B", status="active")])
        members = ((ADA_A, ECO_A, "Ada"), (BEN_1, ECO_A, "Ben"), (BEN_2, ECO_A, "ben"), (CY, ECO_A, "Cy"), (ADA_B, ECO_B, "Ada"))
        session.add_all([User(id=member_id, display_name=name) for member_id, _, name in members])
        await session.flush()
        session.add_all([
            Member(
                id=member_id, ecosystem_id=eco, user_id=member_id, member_id=f"MEM-{member_id.int:x}",
                display_name=name, current_status="active",
            )
            for member_id, eco, name in members
        ])
        await session.flush()
        session.add_all([
            _proposal(key, eco, proposer, linked if with_existing_values else None)
            for key, eco, proposer, linked, _ in PROPOSALS
        ])
        session.add_all([
            _domain(key, purpose, name if with_existing_values else None)
            for key, purpose, name, _ in DOMAINS
        ])
        await session.commit()


async def _results(conn) -> tuple[dict, dict]:
    links = {row.proposal_id: row.proposer_member_id for row in (await conn.execute(
        sa.text("SELECT proposal_id, proposer_member_id FROM proposals")
    ))}
    names = {row.domain_id: row.name for row in (await conn.execute(sa.text("SELECT domain_id, name FROM domains")))}
    return links, names


def _as_uuid(value) -> uuid.UUID | None:
    return None if value is None else uuid.UUID(str(value))


@pytest.mark.asyncio
async def test_backfill_links_only_unambiguous_authors_and_derives_domain_names():
    migration = _migration()
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed(async_sessionmaker(engine, class_=AsyncSession), with_existing_values=True)

    def backfill(sync_conn):
        with Operations.context(MigrationContext.configure(sync_conn)):
            sync_conn.execute(sa.text(migration._BACKFILL_PROPOSER_SQL))
            migration._backfill_domain_names_portably()

    async with engine.begin() as conn:
        await conn.run_sync(backfill)
        links, names = await _results(conn)
    await engine.dispose()

    assert {key: _as_uuid(links[key]) for key, *_ in PROPOSALS} == {key: expected for key, *_, expected in PROPOSALS}
    assert {key: names[key] for key, *_ in DOMAINS} == {key: expected for key, *_, expected in DOMAINS}


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
async def test_full_upgrade_backfills_on_postgres():
    migration = _migration()
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(
        os.environ["NEOS_TEST_POSTGRES_URL"],
        connect_args={"server_settings": {"search_path": schema}},
    )
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
        await _seed(async_sessionmaker(engine, class_=AsyncSession), with_existing_values=False)
        async with engine.begin() as conn:
            # Back to the m5f9c3e7a2b4 shape (the FK and index go with the column).
            await conn.execute(sa.text("ALTER TABLE proposals DROP COLUMN proposer_member_id"))
            await conn.execute(sa.text("ALTER TABLE domains DROP COLUMN name"))

            def upgrade(sync_conn):
                with Operations.context(MigrationContext.configure(sync_conn)):
                    migration.upgrade()

            await conn.run_sync(upgrade)
            links, names = await _results(conn)

        fresh = {"P-LINKED": ADA_A}  # no pre-existing link before the column exists
        assert {key: _as_uuid(links[key]) for key, *_ in PROPOSALS} == {
            key: fresh.get(key, expected) for key, *_, expected in PROPOSALS
        }
        fresh_names = {"D-NAMED": "Other"}  # no stored name before the column exists
        assert {key: names[key] for key, *_ in DOMAINS} == {
            key: fresh_names.get(key, expected) for key, *_, expected in DOMAINS
        }
    finally:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()
