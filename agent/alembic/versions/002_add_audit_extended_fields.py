"""Add extended fields to governance_health_audits.

Revision ID: 002_audit_extended
Revises: 001_add_courses
Create Date: 2026-05-11 00:00:00.000000

Adds 10 new columns to governance_health_audits for the Layer VII
governance-health-audit spec: audit_scope, audit_period_start/end,
auditor_ids, overall_health, indicator_scores, triggered_safeguards,
structured_recommendations, trigger_type, next_audit_due.
"""
from alembic import op
import sqlalchemy as sa

revision = "002_audit_extended"
down_revision = "008_add_chat_privacy_and_tokens"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE governance_health_audits
        ADD COLUMN IF NOT EXISTS audit_scope VARCHAR(255),
        ADD COLUMN IF NOT EXISTS audit_period_start DATE,
        ADD COLUMN IF NOT EXISTS audit_period_end DATE,
        ADD COLUMN IF NOT EXISTS auditor_ids JSONB,
        ADD COLUMN IF NOT EXISTS overall_health VARCHAR(50),
        ADD COLUMN IF NOT EXISTS indicator_scores JSONB,
        ADD COLUMN IF NOT EXISTS triggered_safeguards JSONB,
        ADD COLUMN IF NOT EXISTS structured_recommendations JSONB,
        ADD COLUMN IF NOT EXISTS trigger_type VARCHAR(100),
        ADD COLUMN IF NOT EXISTS next_audit_due DATE
    """)


def downgrade():
    op.execute("""
    ALTER TABLE governance_health_audits
        DROP COLUMN IF EXISTS audit_scope,
        DROP COLUMN IF EXISTS audit_period_start,
        DROP COLUMN IF EXISTS audit_period_end,
        DROP COLUMN IF EXISTS auditor_ids,
        DROP COLUMN IF EXISTS overall_health,
        DROP COLUMN IF EXISTS indicator_scores,
        DROP COLUMN IF EXISTS triggered_safeguards,
        DROP COLUMN IF EXISTS structured_recommendations,
        DROP COLUMN IF EXISTS trigger_type,
        DROP COLUMN IF EXISTS next_audit_due
    """)
