"""add_chat_history_fields

Revision ID: d5f3b9c2e1a4
Revises: c4f2a8b1d3e7
Create Date: 2026-03-13 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5f3b9c2e1a4'
down_revision: Union[str, None] = 'c4f2a8b1d3e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('agent_sessions', sa.Column('title', sa.String(200), nullable=True))
    op.add_column('agent_sessions', sa.Column('archived', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_agent_sessions_member_history', 'agent_sessions', ['member_id', 'updated_at'])


def downgrade() -> None:
    op.drop_index('ix_agent_sessions_member_history', table_name='agent_sessions')
    op.drop_column('agent_sessions', 'archived')
    op.drop_column('agent_sessions', 'title')
