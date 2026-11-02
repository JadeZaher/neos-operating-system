"""Explicit node support authority and immutable public interventions."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, DDL, ForeignKey, Index, JSON, String, event, func
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID


class NodeAdmin(Base):
    __tablename__ = "node_admins"
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)


class NodeAdminAction(Base):
    __tablename__ = "node_admin_actions"
    __table_args__ = (Index("ix_node_admin_actions_created", "created_at"), Index("ix_node_admin_actions_target", "resource_type", "resource_id"))
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    reason: Mapped[str] = mapped_column(String(120), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="ui")
    changed_fields: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    safe_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True)


class NodeAdminSnapshot(Base):
    __tablename__ = "node_admin_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    action_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    operation: Mapped[str] = mapped_column(String(40), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)


SQLITE_IMMUTABLE = (
    "CREATE TRIGGER IF NOT EXISTS node_admin_actions_no_update BEFORE UPDATE ON node_admin_actions BEGIN SELECT RAISE(ABORT, 'Public support audit is append-only'); END",
    "CREATE TRIGGER IF NOT EXISTS node_admin_actions_no_delete BEFORE DELETE ON node_admin_actions BEGIN SELECT RAISE(ABORT, 'Public support audit is append-only'); END",
)
POSTGRES_IMMUTABLE = (
    "CREATE OR REPLACE FUNCTION neos_support_audit_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Public support audit is append-only'; END $$",
    "CREATE TRIGGER node_admin_actions_immutable BEFORE UPDATE OR DELETE ON node_admin_actions FOR EACH ROW EXECUTE FUNCTION neos_support_audit_immutable()",
)
for statement in SQLITE_IMMUTABLE:
    event.listen(NodeAdminAction.__table__, "after_create", DDL(statement).execute_if(dialect="sqlite"))
for statement in POSTGRES_IMMUTABLE:
    event.listen(NodeAdminAction.__table__, "after_create", DDL(statement).execute_if(dialect="postgresql"))
for operation in ("UPDATE", "DELETE"):
    event.listen(NodeAdminSnapshot.__table__, "after_create", DDL(
        f"CREATE TRIGGER IF NOT EXISTS node_admin_snapshots_no_{operation.lower()} BEFORE {operation} ON node_admin_snapshots BEGIN SELECT RAISE(ABORT, 'Support archives are append-only'); END"
    ).execute_if(dialect="sqlite"))
event.listen(NodeAdminSnapshot.__table__, "after_create", DDL(
    POSTGRES_IMMUTABLE[0]
).execute_if(dialect="postgresql"))
event.listen(NodeAdminSnapshot.__table__, "after_create", DDL(
    "CREATE TRIGGER node_admin_snapshots_immutable BEFORE UPDATE OR DELETE ON node_admin_snapshots FOR EACH ROW EXECUTE FUNCTION neos_support_audit_immutable()"
).execute_if(dialect="postgresql"))
