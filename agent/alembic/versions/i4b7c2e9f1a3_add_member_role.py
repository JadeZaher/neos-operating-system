"""Add per-ecosystem role tiers to members.

Revision ID: i4b7c2e9f1a3
Revises: h9d6e2f4a1b3
Create Date: 2026-07-28 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "i4b7c2e9f1a3"
down_revision = "h9d6e2f4a1b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "members",
        sa.Column("role", sa.Text(), nullable=False, server_default="user"),
    )
    op.create_check_constraint(
        "ck_members_role_tier",
        "members",
        "role IN ('user', 'mod', 'admin', 'owner')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_members_role_tier", "members", type_="check")
    op.drop_column("members", "role")
