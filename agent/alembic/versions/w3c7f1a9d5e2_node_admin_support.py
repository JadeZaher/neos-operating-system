"""Explicit node administrators and public support audit; see alembic/AGENTS.md."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "w3c7f1a9d5e2"
down_revision = "v1b4e7c9d2f5"
branch_labels = None
depends_on = None

def upgrade():
    from neos_agent.db.models import NodeAdmin, NodeAdminAction, NodeAdminSnapshot
    from neos_agent.db.models.nodeadmin import POSTGRES_IMMUTABLE, SQLITE_IMMUTABLE
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    for model in (NodeAdmin, NodeAdminAction, NodeAdminSnapshot):
        if model.__tablename__ not in tables:
            model.__table__.create(bind)
    if "node_admin_actions" in tables:
        if bind.dialect.name == "postgresql":
            bind.execute(sa.text("DROP TRIGGER IF EXISTS node_admin_actions_immutable ON node_admin_actions"))
        for statement in POSTGRES_IMMUTABLE if bind.dialect.name == "postgresql" else SQLITE_IMMUTABLE:
            bind.execute(sa.text(statement))
    columns = {c["name"] for c in sa.inspect(bind).get_columns("proposals")}
    for name in ("support_created_by_user_id", "support_action_id"):
        if name not in columns:
            op.add_column("proposals", sa.Column(name, sa.Uuid(), nullable=True))
    if "disabled_at" not in {c["name"] for c in sa.inspect(bind).get_columns("users")}:
        op.add_column("users", sa.Column("disabled_at", sa.DateTime(), nullable=True))
    if "owner_user_id" not in {c["name"] for c in sa.inspect(bind).get_columns("agent_sessions")}:
        op.add_column("agent_sessions", sa.Column("owner_user_id", sa.Uuid(), nullable=True))
        if bind.dialect.name == "postgresql":
            op.create_foreign_key("fk_agent_sessions_owner_user", "agent_sessions", "users", ["owner_user_id"], ["id"])
    sessions = sa.table("agent_sessions", sa.column("id", sa.Uuid()), sa.column("member_id", sa.Uuid()), sa.column("owner_user_id", sa.Uuid()))
    members = sa.table("members", sa.column("id", sa.Uuid()), sa.column("user_id", sa.Uuid()))
    bind.execute(sessions.update().where(sessions.c.owner_user_id.is_(None), sessions.c.member_id.is_not(None)).values(
        owner_user_id=sa.select(members.c.user_id).where(members.c.id == sessions.c.member_id).scalar_subquery()))


def downgrade():
    bind = op.get_bind()
    if "node_admin_snapshots" in sa.inspect(bind).get_table_names():
        op.drop_table("node_admin_snapshots")
    if "node_admin_actions" in sa.inspect(bind).get_table_names():
        op.drop_table("node_admin_actions")
    if "node_admins" in sa.inspect(bind).get_table_names():
        op.drop_table("node_admins")
    if bind.dialect.name == "postgresql":
        bind.execute(sa.text("DROP FUNCTION IF EXISTS neos_support_audit_immutable()"))
    columns = {c["name"] for c in sa.inspect(bind).get_columns("proposals")}
    for name in ("support_action_id", "support_created_by_user_id"):
        if name in columns:
            op.drop_column("proposals", name)
    if "owner_user_id" in {c["name"] for c in sa.inspect(bind).get_columns("agent_sessions")}:
        if bind.dialect.name == "postgresql":
            op.drop_constraint("fk_agent_sessions_owner_user", "agent_sessions", type_="foreignkey")
        op.drop_column("agent_sessions", "owner_user_id")
    bind.execute(sa.text("DELETE FROM app_settings WHERE key = 'node_admin_bootstrap_complete'"))
    if "disabled_at" in {c["name"] for c in sa.inspect(bind).get_columns("users")}:
        op.drop_column("users", "disabled_at")
