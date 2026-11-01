"""ACT integrity: who holds each position, advice, report and grant; which agreement a proposal amends or became; the text it was ratified with.

Revision ID: p8d4f1b6e3a9
Revises: o7c3e9a5d2f8
Create Date: 2026-10-31 21:00:00.000000

Six nullable foreign keys and one text column, each added only when missing
(create_all databases already have them); then consent_participants.member_id
and advice_entries.member_id are backfilled where exactly one member of the
proposal's ecosystem has the row's name, and already-ratified proposals get
their ratified text. The
downgrade drops the columns, backfilled values included. Rationale:
alembic/AGENTS.md "p8d4f1b6e3a9".
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "p8d4f1b6e3a9"
down_revision = "o7c3e9a5d2f8"
branch_labels = None
depends_on = None

# (table, column, referenced table, ondelete)
COLUMNS = (
    ("consent_participants", "member_id", "members", "SET NULL"),
    ("advice_entries", "member_id", "members", "SET NULL"),
    ("test_reports", "reporter_member_id", "members", "SET NULL"),
    ("proposals", "amends_agreement_id", "agreements", None),
    ("proposals", "registered_agreement_id", "agreements", None),
    ("member_status_transitions", "actor_member_id", "members", "SET NULL"),
)
TEXT_COLUMNS = (("proposals", "ratified_text"),)


def _backfill_members_sql(table: str, name: str, parent: str, parent_key: str) -> str:
    """Set `table`.member_id to the one member of the proposal's ecosystem named `name` (via `parent`).

    Portable (PostgreSQL + SQLite) correlated subqueries; ambiguous or unknown names stay NULL.
    """
    matching = f"""
    FROM members m, {parent} r, proposals p
    WHERE r.id = {table}.{parent_key}
      AND p.id = r.proposal_id
      AND m.ecosystem_id = p.ecosystem_id
      AND lower(trim(m.display_name)) = lower(trim({table}.{name}))
"""
    return f"""
UPDATE {table}
SET member_id = (SELECT m.id {matching})
WHERE member_id IS NULL
  AND {name} IS NOT NULL
  AND trim({name}) <> ''
  AND (SELECT count(*) {matching}) = 1
"""


BACKFILL_CONSENT_MEMBERS_SQL = _backfill_members_sql("consent_participants", "name", "consent_records", "consent_record_id")
BACKFILL_ADVICE_MEMBERS_SQL = _backfill_members_sql("advice_entries", "advisor", "advice_logs", "advice_log_id")

# Ratified before this column existed: the decision record minted at ratification holds
# "<title> — ratified after completing the ACT process. <proposed_change>" (act_gates.record_proposal_decision).
_HOLDING_PREFIX = "proposals.title || ' — ratified after completing the ACT process. '"
BACKFILL_RATIFIED_FROM_DECISION_SQL = f"""
UPDATE proposals
SET ratified_text = (
    SELECT substr(d.holding, length({_HOLDING_PREFIX}) + 1)
    FROM decision_records d
    WHERE d.source_proposal_id = proposals.id
      AND substr(d.holding, 1, length({_HOLDING_PREFIX})) = {_HOLDING_PREFIX}
    ORDER BY d.created_at
    LIMIT 1
)
WHERE status = 'ratified' AND ratified_text IS NULL
"""
# No matching decision record (title edited since, or an older format): the live text is all there is.
BACKFILL_RATIFIED_FROM_PROPOSAL_SQL = """
UPDATE proposals
SET ratified_text = nullif(trim(proposed_change), '')
WHERE status = 'ratified' AND ratified_text IS NULL
"""


def _foreign_key_name(table: str, column: str) -> str:
    return f"fk_{table}_{column}"


def _columns(inspector, table: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    postgres = bind.dialect.name == "postgresql"
    for table, column, referenced, ondelete in COLUMNS:
        if table not in tables or column in _columns(inspector, table):
            continue
        op.add_column(table, sa.Column(column, sa.Uuid(), nullable=True))
        # SQLite cannot add a constraint to an existing table; the column alone is enough there.
        if postgres:
            op.create_foreign_key(
                _foreign_key_name(table, column), table, referenced, [column], ["id"], ondelete=ondelete,
            )
    for table, column in TEXT_COLUMNS:
        if table in tables and column not in _columns(inspector, table):
            op.add_column(table, sa.Column(column, sa.Text(), nullable=True))
    # Also on create_all databases: legacy rows there have NULL too. Ownership never falls back to names.
    if {"consent_participants", "consent_records", "proposals", "members"} <= tables:
        op.execute(BACKFILL_CONSENT_MEMBERS_SQL)
    if {"advice_entries", "advice_logs", "proposals", "members"} <= tables:
        op.execute(BACKFILL_ADVICE_MEMBERS_SQL)
    if "proposals" in tables and {"status", "title", "proposed_change"} <= _columns(sa.inspect(bind), "proposals"):
        if "decision_records" in tables and {"holding", "source_proposal_id"} <= _columns(inspector, "decision_records"):
            op.execute(BACKFILL_RATIFIED_FROM_DECISION_SQL)
        op.execute(BACKFILL_RATIFIED_FROM_PROPOSAL_SQL)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    for table, column in TEXT_COLUMNS:
        if table in tables and column in _columns(inspector, table):
            op.drop_column(table, column)
    for table, column, _referenced, _ondelete in reversed(COLUMNS):
        if table not in tables or column not in _columns(inspector, table):
            continue
        for foreign_key in inspector.get_foreign_keys(table):
            if foreign_key.get("constrained_columns") == [column] and foreign_key.get("name"):
                op.drop_constraint(foreign_key["name"], table, type_="foreignkey")
        op.drop_column(table, column)
