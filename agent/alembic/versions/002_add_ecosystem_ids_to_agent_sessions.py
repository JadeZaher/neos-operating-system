"""Add ecosystem_ids column to agent_sessions.

Revision ID: 002_add_ecosystem_ids
Revises: 001_add_courses
Create Date: 2026-04-12 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = "002_add_ecosystem_ids"
down_revision = "001_add_courses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_sessions",
        sa.Column("ecosystem_ids", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_sessions", "ecosystem_ids")
