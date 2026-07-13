"""NEOS model: ExitRecord."""

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
# EXIT & PORTABILITY (1 model)
# ========================

class ExitRecord(TimestampMixin, Base):
    """Voluntary departure tracking (Layer X)."""
    __tablename__ = "exit_records"
    __table_args__ = (Index("ix_exit_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    shared_ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # additional ecosystems for cross-ecosystem work
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    exit_type: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="declared")
    declared_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    coordinator_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    commitment_inventory: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    unwinding_status: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    data_export_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_export_completed: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    departure_notice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    re_entry_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ========================
# SESSIONS (1 model)
# ========================
