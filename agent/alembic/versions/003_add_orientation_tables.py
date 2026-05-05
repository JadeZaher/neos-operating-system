"""Add orientation journey map, ethos user access, and user journey progress tables.

Revision ID: 003_orientation_tables
Revises: 002_add_oauth
Create Date: 2026-05-04 00:00:00.000000
"""
from alembic import op

revision = "003_orientation_tables"
down_revision = "002_add_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS journey_maps (
        id UUID PRIMARY KEY,
        slug VARCHAR(200) NOT NULL,
        title VARCHAR(500) NOT NULL,
        description TEXT,
        ecosystem_id UUID REFERENCES ecosystems(id),
        sector_alignment JSONB,
        role_types JSONB,
        min_alignment_score INTEGER,
        content_sequence JSONB NOT NULL DEFAULT '[]',
        exit_package JSONB,
        step_count INTEGER NOT NULL DEFAULT 0,
        is_default BOOLEAN NOT NULL DEFAULT FALSE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_journey_maps_slug ON journey_maps(slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_journey_maps_ecosystem_id ON journey_maps(ecosystem_id)")

    op.execute("""
    CREATE TABLE IF NOT EXISTS ethos_user_access (
        id UUID PRIMARY KEY,
        member_id UUID NOT NULL REFERENCES members(id),
        ecosystem_id UUID NOT NULL REFERENCES ecosystems(id),
        role_in_ethos VARCHAR(100),
        access_level VARCHAR(50) NOT NULL DEFAULT 'member',
        granted_at TIMESTAMP NOT NULL DEFAULT NOW(),
        granted_by UUID,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ethos_user_access_member_ecosystem ON ethos_user_access(member_id, ecosystem_id)")

    op.execute("""
    CREATE TABLE IF NOT EXISTS user_journey_progress (
        id UUID PRIMARY KEY,
        member_id UUID NOT NULL REFERENCES members(id),
        ecosystem_id UUID NOT NULL REFERENCES ecosystems(id),
        journey_map_id UUID NOT NULL REFERENCES journey_maps(id),
        orientation_path VARCHAR(20) NOT NULL DEFAULT 'explorer',
        current_step INTEGER NOT NULL DEFAULT 0,
        completed_steps JSONB DEFAULT '[]',
        step_responses JSONB DEFAULT '{}',
        status VARCHAR(20) NOT NULL DEFAULT 'not_started',
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        was_recommended BOOLEAN NOT NULL DEFAULT TRUE,
        misalignment_flags JSONB DEFAULT '[]',
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_journey_progress_member_ecosystem ON user_journey_progress(member_id, ecosystem_id)")


def downgrade() -> None:
    for table in ["user_journey_progress", "ethos_user_access", "journey_maps"]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
