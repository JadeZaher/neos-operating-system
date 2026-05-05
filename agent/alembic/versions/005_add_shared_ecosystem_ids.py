"""Add shared_ecosystem_ids JSON column to all entity tables for cross-ecosystem work.

Revision ID: 005_add_shared_ecosystem_ids
Revises: 004_add_member_privacy
Create Date: 2026-05-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "005_add_shared_ecosystem_ids"
down_revision = "004_add_member_privacy"
branch_labels = None
depends_on = None

TABLES = [
    "members",
    "domains",
    "agreements",
    "proposals",
    "decision_records",
    "conflict_cases",
    "exit_records",
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("shared_ecosystem_ids", sa.JSON(), nullable=True))


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "shared_ecosystem_ids")
