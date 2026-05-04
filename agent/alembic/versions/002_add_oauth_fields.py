"""Add OAuth fields to members table.

Revision ID: 002_add_oauth
Revises: 001_add_courses
Create Date: 2026-05-04 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "002_add_oauth"
down_revision = "001_add_courses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("members", sa.Column("oauth_provider", sa.String(50), nullable=True))
    op.add_column("members", sa.Column("oauth_id", sa.String(255), nullable=True))
    op.create_index("ix_members_oauth_id", "members", ["oauth_id"])


def downgrade() -> None:
    op.drop_index("ix_members_oauth_id", table_name="members")
    op.drop_column("members", "oauth_id")
    op.drop_column("members", "oauth_provider")
