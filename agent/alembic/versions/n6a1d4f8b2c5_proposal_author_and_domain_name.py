"""Proposal authorship link and domain names.

Revision ID: n6a1d4f8b2c5
Revises: m5f9c3e7a2b4
Create Date: 2026-10-31 00:00:00.000000

proposals.proposer_member_id links a proposal to the member who authored it
(the manage rule in api/proposals.py keys on it). Backfilled only where the
free-text proposer matches exactly one member's display name in the same
ecosystem; everything else stays NULL (steward-managed).

domains.name gives a domain a human name. Backfilled from the purpose's
leading "Name — description" segment when that segment is 1-120 characters.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "n6a1d4f8b2c5"
down_revision = "m5f9c3e7a2b4"
branch_labels = None
depends_on = None


NAME_SEPARATOR = " — "
MAX_BACKFILLED_NAME = 120

# Portable (PostgreSQL + SQLite): correlated subqueries instead of UPDATE ... FROM.
_BACKFILL_PROPOSER_SQL = """
UPDATE proposals
SET proposer_member_id = (
    SELECT m.id FROM members m
    WHERE m.ecosystem_id = proposals.ecosystem_id
      AND lower(trim(m.display_name)) = lower(trim(proposals.proposer))
)
WHERE proposer_member_id IS NULL
  AND proposer IS NOT NULL
  AND trim(proposer) <> ''
  AND (
    SELECT count(*) FROM members m2
    WHERE m2.ecosystem_id = proposals.ecosystem_id
      AND lower(trim(m2.display_name)) = lower(trim(proposals.proposer))
  ) = 1
"""

_BACKFILL_DOMAIN_NAME_PG_SQL = f"""
UPDATE domains
SET name = btrim(split_part(purpose, '{NAME_SEPARATOR}', 1))
WHERE name IS NULL
  AND strpos(purpose, '{NAME_SEPARATOR}') > 0
  AND char_length(btrim(split_part(purpose, '{NAME_SEPARATOR}', 1)))
      BETWEEN 1 AND {MAX_BACKFILLED_NAME}
"""


def _backfill_domain_names_portably() -> None:
    """Row-by-row fallback for non-PostgreSQL dialects (domains is a small table)."""
    bind = op.get_bind()
    domains = sa.table(
        "domains", sa.column("id"), sa.column("purpose"), sa.column("name")
    )
    rows = bind.execute(
        sa.select(domains.c.id, domains.c.purpose).where(
            domains.c.name.is_(None), domains.c.purpose.is_not(None)
        )
    ).all()
    for domain_row_id, purpose in rows:
        if NAME_SEPARATOR not in purpose:
            continue
        head = purpose.split(NAME_SEPARATOR, 1)[0].strip()
        if 1 <= len(head) <= MAX_BACKFILLED_NAME:
            bind.execute(
                sa.update(domains).where(domains.c.id == domain_row_id).values(name=head)
            )


def upgrade() -> None:
    op.add_column("proposals", sa.Column("proposer_member_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_proposals_proposer_member_id_members",
        "proposals",
        "members",
        ["proposer_member_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_proposals_proposer_member_id", "proposals", ["proposer_member_id"]
    )
    op.execute(_BACKFILL_PROPOSER_SQL)

    op.add_column("domains", sa.Column("name", sa.String(length=200), nullable=True))
    if op.get_context().dialect.name == "postgresql":
        op.execute(_BACKFILL_DOMAIN_NAME_PG_SQL)
    else:
        _backfill_domain_names_portably()


def downgrade() -> None:
    op.drop_column("domains", "name")
    op.drop_index("ix_proposals_proposer_member_id", table_name="proposals")
    op.drop_constraint(
        "fk_proposals_proposer_member_id_members", "proposals", type_="foreignkey"
    )
    op.drop_column("proposals", "proposer_member_id")
