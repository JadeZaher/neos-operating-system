"""NEOS model: EthosUserAccess."""

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


class EthosUserAccess(TimestampMixin, Base):
    """Access record for a member within an ecosystem's Ethos layer."""
    __tablename__ = "ethos_user_access"
    __table_args__ = (
        Index("ix_ethos_user_access_member_ecosystem", "member_id", "ecosystem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    role_in_ethos: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # steward, member, observer
    access_level: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    granted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
