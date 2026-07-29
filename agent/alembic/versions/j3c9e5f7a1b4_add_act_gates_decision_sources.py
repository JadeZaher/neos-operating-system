"""Add ACT gate policies and decision-record source links.

Revision ID: j3c9e5f7a1b4
Revises: i4b7c2e9f1a3
Create Date: 2026-07-28 00:00:00.000000

- proposals.act_policy / agreements.act_policy: per-record ACT gate
  declarations (min advice rounds, consent requirement/quorum, test cases).
- decision_records.source_proposal_id / source_agreement_id: relational
  links from a decision artifact back to the proposal or agreement whose
  completed ACT process produced it. Agreement-produced artifacts carry
  artifact_type "commitment".
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "j3c9e5f7a1b4"
down_revision = "i4b7c2e9f1a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("proposals", sa.Column("act_policy", sa.JSON(), nullable=True))
    op.add_column("agreements", sa.Column("act_policy", sa.JSON(), nullable=True))

    op.add_column("decision_records", sa.Column("source_proposal_id", sa.Uuid(), nullable=True))
    op.add_column("decision_records", sa.Column("source_agreement_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_decision_records_source_proposal_id_proposals",
        "decision_records", "proposals", ["source_proposal_id"], ["id"],
    )
    op.create_foreign_key(
        "fk_decision_records_source_agreement_id_agreements",
        "decision_records", "agreements", ["source_agreement_id"], ["id"],
    )
    op.create_index(
        "ix_decision_records_source_proposal_id",
        "decision_records", ["source_proposal_id"],
    )
    op.create_index(
        "ix_decision_records_source_agreement_id",
        "decision_records", ["source_agreement_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_decision_records_source_agreement_id", table_name="decision_records")
    op.drop_index("ix_decision_records_source_proposal_id", table_name="decision_records")
    op.drop_constraint(
        "fk_decision_records_source_agreement_id_agreements", "decision_records", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_decision_records_source_proposal_id_proposals", "decision_records", type_="foreignkey"
    )
    op.drop_column("decision_records", "source_agreement_id")
    op.drop_column("decision_records", "source_proposal_id")
    op.drop_column("agreements", "act_policy")
    op.drop_column("proposals", "act_policy")
