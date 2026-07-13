"""NEOS model: ConflictCase."""

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
# CONFLICT & REPAIR (3 models)
# ========================

class ConflictCase(TimestampMixin, Base):
    """A reported conflict or harm requiring governance process."""
    __tablename__ = "conflict_cases"
    __table_args__ = (Index("ix_conflict_cases_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    shared_ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # additional ecosystems for cross-ecosystem work
    case_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reporter_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="reported")
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    root_cause_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    safety_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    facilitator_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    triage_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    repair_agreements: Mapped[list["RepairAgreementRecord"]] = relationship(back_populates="conflict_case")
