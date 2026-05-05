"""Add privacy JSON column to members table.

Revision ID: 004_add_member_privacy
Revises: 003_orientation_tables
Create Date: 2026-05-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "004_add_member_privacy"
down_revision = "003_orientation_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('members', sa.Column('privacy', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('members', 'privacy')
