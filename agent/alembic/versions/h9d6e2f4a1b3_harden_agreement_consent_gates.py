"""Harden agreement consent, lifecycle evidence, and participation gates.

Revision ID: h9d6e2f4a1b3
Revises: g8c5d1e4f2a7
Create Date: 2026-07-27 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "h9d6e2f4a1b3"
down_revision = "g8c5d1e4f2a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agreements",
        sa.Column("requires_explicit_consent", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.execute("UPDATE agreements SET requires_explicit_consent = true")
    op.add_column("agreements", sa.Column("prerequisite_scopes", sa.JSON(), nullable=True))
    op.add_column("agreements", sa.Column("prerequisite_domain_ids", sa.JSON(), nullable=True))
    op.add_column(
        "agreements",
        sa.Column("alignment_points", sa.Integer(), nullable=False, server_default="5"),
    )

    op.add_column("members", sa.Column("agreement_alignment_score", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("collaborations", sa.Column("required_agreement_ids", sa.JSON(), nullable=True))

    op.add_column("agreement_ratification_records", sa.Column("member_id", sa.Uuid(), nullable=True))
    op.add_column("agreement_ratification_records", sa.Column("agreement_version", sa.String(length=20), nullable=True))
    op.add_column("agreement_ratification_records", sa.Column("objection_text", sa.Text(), nullable=True))
    op.add_column("agreement_ratification_records", sa.Column("withdrawn_at", sa.DateTime(), nullable=True))
    op.add_column(
        "agreement_ratification_records",
        sa.Column("alignment_awarded", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_foreign_key(
        "fk_agreement_ratification_records_member_id_members",
        "agreement_ratification_records", "members", ["member_id"], ["id"],
    )
    op.create_index(
        "ix_agreement_ratification_records_member_id",
        "agreement_ratification_records", ["member_id"],
    )
    op.create_unique_constraint(
        "uq_agreement_member_version_consent",
        "agreement_ratification_records", ["agreement_id", "member_id", "agreement_version"],
    )

    for column, type_ in (
        ("requires_explicit_consent", sa.Boolean()),
        ("prerequisite_scopes", sa.JSON()),
        ("prerequisite_domain_ids", sa.JSON()),
        ("alignment_points", sa.Integer()),
    ):
        op.add_column("agreement_versions", sa.Column(column, type_, nullable=True))
    op.execute("UPDATE agreement_versions SET requires_explicit_consent = true WHERE requires_explicit_consent IS NULL")
    op.execute("UPDATE agreement_versions SET alignment_points = 5 WHERE alignment_points IS NULL")
    op.alter_column("agreement_versions", "requires_explicit_consent", nullable=False)
    op.alter_column("agreement_versions", "alignment_points", nullable=False)

    op.create_table(
        "agreement_ceremonies",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("agreement_id", sa.Uuid(), sa.ForeignKey("agreements.id"), nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("completed_by_member_id", sa.Uuid(), sa.ForeignKey("members.id"), nullable=True),
        sa.Column("outcome", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agreement_ceremonies_agreement_id", "agreement_ceremonies", ["agreement_id"])

    op.create_table(
        "agreement_member_consents",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("agreement_id", sa.Uuid(), sa.ForeignKey("agreements.id"), nullable=False),
        sa.Column("member_id", sa.Uuid(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("agreement_version", sa.String(length=20), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("attestation", sa.Text(), nullable=False),
        sa.Column("attested_at", sa.DateTime(), nullable=False),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=True),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("agreement_id", "member_id", "agreement_version", name="uq_agreement_member_consent_version"),
    )
    op.create_index("ix_agreement_member_consents_member_id", "agreement_member_consents", ["member_id"])

    op.create_table(
        "agreement_requirements",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("agreement_id", sa.Uuid(), sa.ForeignKey("agreements.id"), nullable=False),
        sa.Column("target_kind", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("enforcement", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("agreement_id", "target_kind", "target_id", name="uq_agreement_requirement_target"),
    )
    op.create_index("ix_agreement_requirements_target", "agreement_requirements", ["target_kind", "target_id"])

    op.create_table(
        "collaboration_approvals",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("collaboration_id", sa.Uuid(), sa.ForeignKey("collaborations.id"), nullable=False),
        sa.Column("ecosystem_id", sa.Uuid(), sa.ForeignKey("ecosystems.id"), nullable=False),
        sa.Column("member_id", sa.Uuid(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("collaboration_id", "ecosystem_id", name="uq_collaboration_approval_ecosystem"),
    )
    op.create_index(
        "ix_collaboration_approvals_collaboration_id", "collaboration_approvals", ["collaboration_id"]
    )

    op.create_table(
        "member_alignment_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("member_id", sa.Uuid(), sa.ForeignKey("members.id"), nullable=False),
        sa.Column("ecosystem_id", sa.Uuid(), sa.ForeignKey("ecosystems.id"), nullable=False),
        sa.Column("agreement_consent_id", sa.Uuid(), sa.ForeignKey("agreement_member_consents.id"), nullable=False),
        sa.Column("event_kind", sa.String(length=50), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("formula_version", sa.String(length=20), nullable=False, server_default="1"),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("agreement_consent_id", "event_kind", name="uq_alignment_event_consent_kind"),
    )
    op.create_index("ix_member_alignment_events_member_id", "member_alignment_events", ["member_id"])

    # Normalize historical aliases so every existing row is selectable in the
    # canonical UI vocabulary and eligible for lifecycle enforcement.
    op.execute("UPDATE agreements SET type = 'uaf' WHERE type = 'universal_field'")
    op.execute("UPDATE agreement_versions SET type = 'uaf' WHERE type = 'universal_field'")
    op.execute("UPDATE agreements SET status = 'active' WHERE status = 'ratified'")
    op.execute("UPDATE agreement_versions SET status = 'active' WHERE status = 'ratified'")


def downgrade() -> None:
    op.drop_index("ix_member_alignment_events_member_id", table_name="member_alignment_events")
    op.drop_table("member_alignment_events")
    op.drop_index("ix_agreement_requirements_target", table_name="agreement_requirements")
    op.drop_table("agreement_requirements")
    op.drop_index("ix_collaboration_approvals_collaboration_id", table_name="collaboration_approvals")
    op.drop_table("collaboration_approvals")
    op.drop_index("ix_agreement_member_consents_member_id", table_name="agreement_member_consents")
    op.drop_table("agreement_member_consents")
    op.drop_index("ix_agreement_ceremonies_agreement_id", table_name="agreement_ceremonies")
    op.drop_table("agreement_ceremonies")

    for column in ("alignment_points", "prerequisite_domain_ids", "prerequisite_scopes", "requires_explicit_consent"):
        op.drop_column("agreement_versions", column)
    op.drop_constraint("uq_agreement_member_version_consent", "agreement_ratification_records", type_="unique")
    op.drop_index("ix_agreement_ratification_records_member_id", table_name="agreement_ratification_records")
    op.drop_constraint("fk_agreement_ratification_records_member_id_members", "agreement_ratification_records", type_="foreignkey")
    for column in ("alignment_awarded", "withdrawn_at", "objection_text", "agreement_version", "member_id"):
        op.drop_column("agreement_ratification_records", column)
    op.drop_column("collaborations", "required_agreement_ids")
    op.drop_column("members", "agreement_alignment_score")
    for column in ("alignment_points", "prerequisite_domain_ids", "prerequisite_scopes", "requires_explicit_consent"):
        op.drop_column("agreements", column)
