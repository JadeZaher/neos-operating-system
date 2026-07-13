"""NEOS model: AgentSession."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import JSON, TypeDecorator, CHAR
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from ._base import Base, GUID, TimestampMixin


# ========================
# SESSIONS (1 model)
# ========================

class AgentSession(TimestampMixin, Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (
        Index("ix_agent_sessions_ecosystem_id", "ecosystem_id"),
        Index("ix_agent_sessions_member_history", "member_id", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, doc="All selected ecosystem UUIDs at session creation")
    member_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    skill_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    privacy: Mapped[str] = mapped_column(String(20), nullable=False, default="private", doc="private | ecosystem | public")
    share_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, doc="URL-safe token for shared links")
    total_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ========================
# AUTH (2 models)
# ========================
