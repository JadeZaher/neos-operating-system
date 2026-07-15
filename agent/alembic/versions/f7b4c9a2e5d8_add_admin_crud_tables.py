"""add admin CRUD tables + merge heads

Revision ID: f7b4c9a2e5d8
Revises: 002_audit_extended, 002_add_ecosystem_ids, 009_add_emergency_half_open
Create Date: 2026-07-15 00:00:00.000000

Merges the three previously divergent alembic heads into one, and creates the
tables backing the admin CRUD surfaces and the participation-consent gate:
- badge_definitions: admin-managed badge catalog
- teams / team_members: ecosystem working groups + membership
- quiz_assignments: quizzes assigned to individual members
- app_settings: generic key/value settings (e.g. ctc_map)
- ctc_handoff: NEOS Den readiness per member
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7b4c9a2e5d8'
down_revision: Union[str, Sequence[str], None] = (
    '002_audit_extended',
    '002_add_ecosystem_ids',
    '009_add_emergency_half_open',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- badge_definitions --
    op.create_table(
        'badge_definitions',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('ecosystem_id', sa.Uuid(), sa.ForeignKey('ecosystems.id'), nullable=True),
        sa.Column('badge_key', sa.String(255), nullable=False),
        sa.Column('badge_name', sa.String(255), nullable=False),
        sa.Column('badge_description', sa.Text(), nullable=True),
        sa.Column('badge_category', sa.String(100), nullable=True),
        sa.Column('badge_icon', sa.String(255), nullable=True),
        sa.Column('strength', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('ecosystem_id', 'badge_key', name='uq_badge_definition_ecosystem_key'),
    )
    op.create_index('ix_badge_definitions_ecosystem_id', 'badge_definitions', ['ecosystem_id'])

    # -- teams --
    op.create_table(
        'teams',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('ecosystem_id', sa.Uuid(), sa.ForeignKey('ecosystems.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_teams_ecosystem_id', 'teams', ['ecosystem_id'])

    # -- team_members --
    op.create_table(
        'team_members',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('team_id', sa.Uuid(), sa.ForeignKey('teams.id'), nullable=False),
        sa.Column('member_id', sa.Uuid(), sa.ForeignKey('members.id'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='member'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('team_id', 'member_id', name='uq_team_member'),
    )
    op.create_index('ix_team_members_member_id', 'team_members', ['member_id'])

    # -- quiz_assignments --
    op.create_table(
        'quiz_assignments',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('quiz_id', sa.Uuid(), sa.ForeignKey('quizzes.id'), nullable=False),
        sa.Column('member_id', sa.Uuid(), sa.ForeignKey('members.id'), nullable=False),
        sa.Column('ecosystem_id', sa.Uuid(), sa.ForeignKey('ecosystems.id'), nullable=True),
        sa.Column('assigned_by', sa.Uuid(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='assigned'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('quiz_id', 'member_id', name='uq_quiz_assignment'),
    )
    op.create_index('ix_quiz_assignments_member_id', 'quiz_assignments', ['member_id'])

    # -- app_settings --
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('key', name='uq_app_settings_key'),
    )

    # -- ctc_handoff --
    op.create_table(
        'ctc_handoff',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('member_id', sa.Uuid(), sa.ForeignKey('members.id'), nullable=False),
        sa.Column('ready_for_neos_den', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('member_id', name='uq_ctc_handoff_member'),
    )


def downgrade() -> None:
    op.drop_table('ctc_handoff')
    op.drop_table('app_settings')
    op.drop_index('ix_quiz_assignments_member_id', table_name='quiz_assignments')
    op.drop_table('quiz_assignments')
    op.drop_index('ix_team_members_member_id', table_name='team_members')
    op.drop_table('team_members')
    op.drop_index('ix_teams_ecosystem_id', table_name='teams')
    op.drop_table('teams')
    op.drop_index('ix_badge_definitions_ecosystem_id', table_name='badge_definitions')
    op.drop_table('badge_definitions')
