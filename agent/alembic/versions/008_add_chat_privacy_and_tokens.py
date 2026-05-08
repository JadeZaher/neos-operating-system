"""Add privacy, share_token, and total_tokens_used to agent_sessions.

Enables chat session sharing (private/ecosystem/public) with URL-safe
share tokens, and tracks cumulative token usage per session.

Revision ID: 008_add_chat_privacy_and_tokens
Revises: 007_add_agreement_versions
Create Date: 2026-05-08 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "008_add_chat_privacy_and_tokens"
down_revision = "007_add_agreement_versions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_sessions", sa.Column("privacy", sa.String(20), nullable=False, server_default="private"))
    op.add_column("agent_sessions", sa.Column("share_token", sa.String(64), nullable=True))
    op.add_column("agent_sessions", sa.Column("total_tokens_used", sa.Integer, nullable=False, server_default="0"))
    op.create_unique_constraint("uq_agent_sessions_share_token", "agent_sessions", ["share_token"])


def downgrade() -> None:
    op.drop_constraint("uq_agent_sessions_share_token", "agent_sessions")
    op.drop_column("agent_sessions", "total_tokens_used")
    op.drop_column("agent_sessions", "share_token")
    op.drop_column("agent_sessions", "privacy")
