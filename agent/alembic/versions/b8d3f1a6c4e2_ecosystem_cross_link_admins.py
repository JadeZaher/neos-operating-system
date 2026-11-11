"""Ecosystem cross-link admins (Lead Link / Rep Link).

Additive. Creates `ecosystem_admins` when missing and, for each ecosystem that
has an owner role, a co_creator, or a domain steward, inserts that person's
internal and external links if those rows are absent. Existing links are left
alone. A second upgrade inserts nothing new. Downgrade drops the table only;
the audit rows in `member_status_transitions` stay.
"""
from alembic import op
import sqlalchemy as sa

revision = "b8d3f1a6c4e2"
down_revision = "z6f0c4e8b2d5"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "ecosystem_admins" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "ecosystem_admins",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("ecosystem_id", sa.Uuid(), sa.ForeignKey("ecosystems.id", ondelete="CASCADE"), nullable=False),
            sa.Column("member_id", sa.Uuid(), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False),
            sa.Column("designation", sa.String(20), nullable=False),
            sa.Column("appointed_by_member_id", sa.Uuid(), sa.ForeignKey("members.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.CheckConstraint("designation IN ('internal', 'external')", name="ck_ecosystem_admin_designation"),
            sa.UniqueConstraint("ecosystem_id", "member_id", "designation", name="uq_ecosystem_admin_designation"),
        )
        op.create_index("ix_ecosystem_admins_ecosystem_id", "ecosystem_admins", ["ecosystem_id"])
        op.create_index("ix_ecosystem_admins_member_id", "ecosystem_admins", ["member_id"])
    from neos_agent.services.ecosystem_admins import backfill_admins
    backfill_admins(bind)


def downgrade():
    bind = op.get_bind()
    if "ecosystem_admins" in sa.inspect(bind).get_table_names():
        op.drop_index("ix_ecosystem_admins_member_id", table_name="ecosystem_admins")
        op.drop_index("ix_ecosystem_admins_ecosystem_id", table_name="ecosystem_admins")
        op.drop_table("ecosystem_admins")
