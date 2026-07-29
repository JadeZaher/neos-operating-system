"""Agent tokens for MCP access.

Revision ID: l4e8b2d6f3a1
Revises: k2f7a4c8e1b5
Create Date: 2026-07-28 00:00:00.000000

agent_tokens: bearer tokens for a logged-in user's own agents (MCP). Each
token is bound to the auth session it was minted from, so logout/revocation
kills the agent's access — authority is always session-scoped.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "l4e8b2d6f3a1"
down_revision = "k2f7a4c8e1b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("auth_session_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["auth_session_id"], ["auth_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_agent_tokens_user_id", "agent_tokens", ["user_id"])
    op.create_index("ix_agent_tokens_auth_session_id", "agent_tokens", ["auth_session_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_tokens_auth_session_id", table_name="agent_tokens")
    op.drop_index("ix_agent_tokens_user_id", table_name="agent_tokens")
    op.drop_table("agent_tokens")
