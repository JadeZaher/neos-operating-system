"""Link proposals to their governing agreement for ACT gate inheritance.

Revision ID: k2f7a4c8e1b5
Revises: j3c9e5f7a1b4
Create Date: 2026-07-28 00:00:00.000000

proposals.governing_agreement_id points at the agreement (typically the
ecosystem's decision-making protocol) whose declared ACT gates apply when
the proposal does not declare its own act_policy.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "k2f7a4c8e1b5"
down_revision = "j3c9e5f7a1b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("proposals", sa.Column("governing_agreement_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_proposals_governing_agreement_id_agreements",
        "proposals", "agreements", ["governing_agreement_id"], ["id"],
    )
    op.create_index(
        "ix_proposals_governing_agreement_id",
        "proposals", ["governing_agreement_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_proposals_governing_agreement_id", table_name="proposals")
    op.drop_constraint(
        "fk_proposals_governing_agreement_id_agreements", "proposals", type_="foreignkey"
    )
    op.drop_column("proposals", "governing_agreement_id")
