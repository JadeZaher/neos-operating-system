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
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("agent_sessions"):
        raise RuntimeError(
            "agent_sessions is missing; apply the initial schema before this migration"
        )
    columns = {column["name"] for column in inspector.get_columns("agent_sessions")}
    if "ecosystem_ids" not in columns:
        op.add_column(
            "agent_sessions",
            sa.Column("ecosystem_ids", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("agent_sessions"):
        return
    columns = {column["name"] for column in inspector.get_columns("agent_sessions")}
    if "ecosystem_ids" in columns:
        op.drop_column("agent_sessions", "ecosystem_ids")
