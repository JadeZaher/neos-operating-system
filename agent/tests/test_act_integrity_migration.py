"""Migration p8d4f1b6e3a9: the ACT integrity columns are added only where missing, on SQLite and PostgreSQL.

SQLite starts from a hand-built pre-migration shape (it cannot drop a column a foreign key
uses); PostgreSQL drops the seven columns from a create_all schema in a throwaway schema and
runs only when NEOS_TEST_POSTGRES_URL names a disposable database. Rule: alembic/AGENTS.md.
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
from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy.orm import Session

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    Base,
    ConsentParticipant,
    ConsentRecord,
    DecisionRecord,
    Ecosystem,
    Member,
    Proposal,
    User,
)

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "p8d4f1b6e3a9_act_integrity.py"
COLUMNS = {
    ("consent_participants", "member_id"),
    ("advice_entries", "member_id"),
    ("test_reports", "reporter_member_id"),
    ("proposals", "amends_agreement_id"),
    ("proposals", "registered_agreement_id"),
    ("member_status_transitions", "actor_member_id"),
    ("proposals", "ratified_text"),
}


def _migration():
    spec = importlib.util.spec_from_file_location("migration_p8d4f1b6e3a9", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(sync_conn, step: str) -> None:
    with Operations.context(MigrationContext.configure(sync_conn)):
        getattr(_migration(), step)()


def _present(sync_conn) -> set[tuple[str, str]]:
    inspector = sa.inspect(sync_conn)
    return {(table, column) for table, column in COLUMNS
            if column in {c["name"] for c in inspector.get_columns(table)}}


def _foreign_keys(sync_conn) -> set[tuple[str, str, str]]:
    inspector = sa.inspect(sync_conn)
    return {
        (table, fk["constrained_columns"][0], fk["referred_table"])
        for table in {t for t, _ in COLUMNS}
        for fk in inspector.get_foreign_keys(table)
        if (table, fk["constrained_columns"][0]) in COLUMNS
    }


@pytest.mark.asyncio
async def test_sqlite_adds_missing_columns_once_and_downgrades():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        for table in ("members", "agreements", "consent_participants", "advice_entries", "test_reports", "proposals",
                      "member_status_transitions"):
            await conn.execute(sa.text(f"CREATE TABLE {table} (id CHAR(32) PRIMARY KEY)"))
        await conn.execute(sa.text("INSERT INTO proposals (id) VALUES ('legacy')"))

        await conn.run_sync(_run, "upgrade")
        assert await conn.run_sync(_present) == COLUMNS
        await conn.run_sync(_run, "upgrade")  # a second run is a no-op, not a duplicate-column error
        legacy = (await conn.execute(sa.text("SELECT amends_agreement_id, ratified_text FROM proposals"))).one()
        assert tuple(legacy) == (None, None)  # no backfill without the columns it reads

        await conn.run_sync(_run, "downgrade")
        assert await conn.run_sync(_present) == set()
    await engine.dispose()


ECO_A, ECO_B = uuid.UUID(int=0xA), uuid.UUID(int=0xB)
ADA, BEN_1, BEN_2, ADA_B, CY = (uuid.UUID(int=n) for n in (0xA1, 0xB1, 0xB2, 0xA2, 0xC1))
# (row name, already owned by, expected owner after the backfill); seeded as consent positions AND advice entries
LEGACY_ROWS = [
    (" ada ", None, ADA),  # unique in the proposal's ecosystem (Ada in B does not count), case and space insensitive
    ("Ben", None, None),  # two members share the name: stays unowned
    ("Zed", None, None),  # nobody has it
    ("Cy", ADA, ADA),  # an existing owner is never replaced
]


def _seed_legacy_positions(sync_conn) -> dict[tuple[str, str], uuid.UUID]:
    """Members in two ecosystems, one proposal in A, its consent and advice rows; returns ids by (kind, name)."""
    people = ((ADA, ECO_A, "Ada"), (BEN_1, ECO_A, "Ben"), (BEN_2, ECO_A, "ben"), (CY, ECO_A, "Cy"), (ADA_B, ECO_B, "Ada"))
    with Session(bind=sync_conn) as session:
        session.add_all([Ecosystem(id=ECO_A, name="A", status="active"), Ecosystem(id=ECO_B, name="B", status="active")])
        session.add_all([User(id=member_id, display_name=name) for member_id, _, name in people])
        session.flush()
        session.add_all([
            Member(id=member_id, ecosystem_id=eco, user_id=member_id, member_id=f"MEM-{member_id.int:x}",
                   display_name=name, current_status="active")
            for member_id, eco, name in people
        ])
        proposal = Proposal(id=uuid.uuid4(), ecosystem_id=ECO_A, proposal_id="P", type="policy", title="P",
                            version="1.0", status="consent")
        session.add(proposal)
        session.flush()
        record = ConsentRecord(id=uuid.uuid4(), proposal_id=proposal.id, consent_mode="consent")
        log = AdviceLog(id=uuid.uuid4(), proposal_id=proposal.id)
        session.add_all([record, log])
        session.flush()
        ids = {}
        for name, owner, _ in LEGACY_ROWS:
            position = ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name=name, position="consent",
                                          member_id=owner)
            advice = AdviceEntry(id=uuid.uuid4(), advice_log_id=log.id, advisor=name, advice_text="Advice",
                                 member_id=owner)
            session.add_all([position, advice])
            ids["consent", name], ids["advice", name] = position.id, advice.id
        session.commit()
    return ids


_ROW_MODELS = {"consent": ConsentParticipant, "advice": AdviceEntry}


def _owners(sync_conn, ids: dict[tuple[str, str], uuid.UUID]) -> dict[tuple[str, str], uuid.UUID | None]:
    """Each seeded row's member_id, read through the model so SQLite and PostgreSQL agree on the type."""
    with Session(bind=sync_conn) as session:
        return {key: session.get(_ROW_MODELS[key[0]], row_id).member_id for key, row_id in ids.items()}


def _expected_owners(**overrides: uuid.UUID) -> dict[tuple[str, str], uuid.UUID | None]:
    """The same rule for positions and advice: a unique name links, a shared or unknown one stays NULL."""
    return {(kind, name): overrides.get(name.strip(), owner) for kind in _ROW_MODELS for name, _, owner in LEGACY_ROWS}


@pytest.mark.asyncio
async def test_sqlite_backfill_owns_only_unambiguous_legacy_positions_and_advice():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        ids = await conn.run_sync(_seed_legacy_positions)
        await conn.run_sync(_run, "upgrade")
        assert await conn.run_sync(_owners, ids) == _expected_owners()
    await engine.dispose()


HOLDING = "{title} — ratified after completing the ACT process. {text}"
# (status, title now, proposed_change now, decision record holding or None, expected ratified_text)
RATIFIED_ROWS = {
    "edited after ratifying": ("ratified", "Hours", "Never closes", HOLDING.format(title="Hours", text="Open till nine"),
                               "Open till nine"),
    "no decision record": ("ratified", "Rota", "Weekly rota", None, "Weekly rota"),
    "title edited since": ("ratified", "Renamed", "Live text",
                           HOLDING.format(title="Original", text="Old text"), "Live text"),
    "not ratified": ("consent", "Draft", "Still moving", None, None),
}


def _seed_ratified_proposals(sync_conn, ecosystem_id: uuid.UUID) -> dict[str, uuid.UUID]:
    """Proposals ratified before the column existed (and one still in consent); returns ids by case."""
    with Session(bind=sync_conn) as session:
        ids = {}
        for case, (status, title, change, holding, _) in RATIFIED_ROWS.items():
            proposal = Proposal(id=uuid.uuid4(), ecosystem_id=ecosystem_id, proposal_id=case, type="policy",
                                title=title, version="1.0", status=status, proposed_change=change)
            session.add(proposal)
            session.flush()
            if holding is not None:
                session.add(DecisionRecord(id=uuid.uuid4(), ecosystem_id=ecosystem_id, record_id=f"DEC-{case}",
                                           holding=holding, source_proposal_id=proposal.id, status="active"))
            ids[case] = proposal.id
        session.commit()
    return ids


def _ratified_texts(sync_conn, ids: dict[str, uuid.UUID]) -> dict[str, str | None]:
    with Session(bind=sync_conn) as session:
        return {case: session.get(Proposal, proposal_id).ratified_text for case, proposal_id in ids.items()}


@pytest.mark.asyncio
async def test_sqlite_backfill_registers_the_text_as_ratified_not_as_edited_since():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_seed_legacy_positions)  # the ecosystems
        ids = await conn.run_sync(_seed_ratified_proposals, ECO_B)
        await conn.run_sync(_run, "upgrade")
        assert await conn.run_sync(_ratified_texts, ids) == {case: row[-1] for case, row in RATIFIED_ROWS.items()}
    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlite_create_all_database_is_left_alone():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        before = await conn.run_sync(_foreign_keys)
        await conn.run_sync(_run, "upgrade")
        assert await conn.run_sync(_present) == COLUMNS
        assert await conn.run_sync(_foreign_keys) == before
    await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
async def test_postgres_upgrade_adds_columns_with_foreign_keys_and_downgrades():
    schema = f"mig_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(
        os.environ["NEOS_TEST_POSTGRES_URL"],
        connect_args={"server_settings": {"search_path": schema}},
    )
    try:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
            ids = await conn.run_sync(_seed_legacy_positions)
            ratified = await conn.run_sync(_seed_ratified_proposals, ECO_B)
            for table, column in sorted(COLUMNS):  # back to the o7c3e9a5d2f8 shape
                await conn.execute(sa.text(f'ALTER TABLE {table} DROP COLUMN "{column}"'))
            assert await conn.run_sync(_present) == set()

            await conn.run_sync(_run, "upgrade")
            assert await conn.run_sync(_present) == COLUMNS
            assert await conn.run_sync(_foreign_keys) == {
                ("consent_participants", "member_id", "members"),
                ("advice_entries", "member_id", "members"),
                ("test_reports", "reporter_member_id", "members"),
                ("proposals", "amends_agreement_id", "agreements"),
                ("proposals", "registered_agreement_id", "agreements"),
                ("member_status_transitions", "actor_member_id", "members"),
            }
            assert await conn.run_sync(_ratified_texts, ratified) == {case: row[-1] for case, row in RATIFIED_ROWS.items()}
            # The dropped columns took Cy's prior owner with them, so the "Cy" rows are backfilled to Cy (unique name).
            assert await conn.run_sync(_owners, ids) == _expected_owners(Cy=CY)
            await conn.run_sync(_run, "upgrade")  # idempotent on PostgreSQL too

            await conn.run_sync(_run, "downgrade")
            assert await conn.run_sync(_present) == set()
    finally:
        async with engine.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()
