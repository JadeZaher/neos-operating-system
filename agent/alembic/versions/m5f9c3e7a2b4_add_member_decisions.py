"""Member decisions — the user-owned decision substrate.

Revision ID: m5f9c3e7a2b4
Revises: l4e8b2d6f3a1
Create Date: 2026-07-28 00:00:00.000000

member_decisions: one member's personal decision about a subject
(agreement | proposal | share | need), doubling as a follow-up task with a
personal state. Distinct from decision_records (the ecosystem artifact
ledger minted by completed ACT processes) — these rows belong to their
owning member. subject_id is polymorphic and validated in the API layer,
so it carries no DB-level FK.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "m5f9c3e7a2b4"
down_revision = "l4e8b2d6f3a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "member_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ecosystem_id", sa.Uuid(), nullable=False),
        sa.Column("member_id", sa.Uuid(), nullable=False),
        sa.Column("subject_type", sa.String(length=20), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=500), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["ecosystem_id"], ["ecosystems.id"]),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_member_decisions_member_id", "member_decisions", ["member_id"])
    op.create_index("ix_member_decisions_subject", "member_decisions", ["subject_type", "subject_id"])


def downgrade() -> None:
    op.drop_index("ix_member_decisions_subject", table_name="member_decisions")
    op.drop_index("ix_member_decisions_member_id", table_name="member_decisions")
    op.drop_table("member_decisions")
