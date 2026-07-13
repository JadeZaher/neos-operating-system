"""NEOS model: RepairAgreementRecord."""

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


class RepairAgreementRecord(TimestampMixin, Base):
    """Binding repair commitment arising from conflict resolution."""
    __tablename__ = "repair_agreement_records"
    __table_args__ = (Index("ix_repair_agreements_conflict_case_id", "conflict_case_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conflict_case_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conflict_cases.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    commitments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    responsible_party: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    checkin_30_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    checkin_30_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checkin_60_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    checkin_60_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checkin_90_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    checkin_90_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    conflict_case: Mapped["ConflictCase"] = relationship(back_populates="repair_agreements")
