"""Add agreement_versions table for version history and rollback.

Stores immutable snapshots of agreement state before each edit,
enabling full audit trail and rollback to any prior version.

Revision ID: 007_add_agreement_versions
Revises: 006_add_users_table
Create Date: 2026-05-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "007_add_agreement_versions"
down_revision = "006_add_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agreement_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agreement_id", UUID(as_uuid=True), sa.ForeignKey("agreements.id"), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("text", sa.Text, nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("proposer", sa.String(255), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("hierarchy_level", sa.String(50), nullable=False, server_default="domain"),
        sa.Column("affected_parties", sa.JSON, nullable=True),
        sa.Column("review_date", sa.Date, nullable=True),
        sa.Column("sunset_date", sa.Date, nullable=True),
        sa.Column("ratification_date", sa.Date, nullable=True),
        sa.Column("version_fingerprint", sa.String(64), nullable=True),
        sa.Column("change_reason", sa.String(500), nullable=True),
        sa.Column("changed_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_agreement_versions_agreement_id", "agreement_versions", ["agreement_id"])


def downgrade() -> None:
    op.drop_index("ix_agreement_versions_agreement_id")
    op.drop_table("agreement_versions")
