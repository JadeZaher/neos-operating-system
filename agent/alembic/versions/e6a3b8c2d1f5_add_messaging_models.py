"""add messaging models

Revision ID: e6a3b8c2d1f5
Revises: d5f3b9c2e1a4
Create Date: 2026-03-13 12:00:00.000000

Creates 4 tables for the Chat & Direct Messaging System:
- conversations: ecosystem-scoped chat threads (DM or group)
- conversation_participants: member-to-conversation links with roles
- messages: individual messages within conversations
- conversation_links: ties conversations to governance entities
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6a3b8c2d1f5'
down_revision: Union[str, None] = 'd5f3b9c2e1a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- conversations --
    op.create_table(
        'conversations',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('ecosystem_id', sa.Uuid(), sa.ForeignKey('ecosystems.id'), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_by', sa.Uuid(), sa.ForeignKey('members.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_conversations_ecosystem_id', 'conversations', ['ecosystem_id'])

    # -- conversation_participants --
    op.create_table(
        'conversation_participants',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('conversation_id', sa.Uuid(), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('member_id', sa.Uuid(), sa.ForeignKey('members.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('muted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('conversation_id', 'member_id', name='uq_conversation_member'),
    )
    op.create_index('ix_conversation_participants_member_id', 'conversation_participants', ['member_id'])

    # -- messages --
    op.create_table(
        'messages',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('conversation_id', sa.Uuid(), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('sender_id', sa.Uuid(), sa.ForeignKey('members.id'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(20), nullable=False, server_default='text'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'])

    # -- conversation_links --
    op.create_table(
        'conversation_links',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('conversation_id', sa.Uuid(), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Uuid(), nullable=False),
        sa.Column('created_by', sa.Uuid(), sa.ForeignKey('members.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_conversation_links_entity', 'conversation_links', ['entity_type', 'entity_id'])


def downgrade() -> None:
    op.drop_index('ix_conversation_links_entity', table_name='conversation_links')
    op.drop_table('conversation_links')

    op.drop_index('ix_messages_conversation_created', table_name='messages')
    op.drop_table('messages')

    op.drop_index('ix_conversation_participants_member_id', table_name='conversation_participants')
    op.drop_table('conversation_participants')

    op.drop_index('ix_conversations_ecosystem_id', table_name='conversations')
    op.drop_table('conversations')
