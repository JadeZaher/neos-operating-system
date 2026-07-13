"""NEOS model: AmendmentRecord."""

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


class AmendmentRecord(TimestampMixin, Base):
    __tablename__ = "amendment_records"
    __table_args__ = (Index("ix_amendment_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    amendment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    parent_agreement_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    amendment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    proposed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    act_level_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    consent_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    new_agreement_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="proposed")

    agreement: Mapped[Agreement] = relationship(back_populates="amendment_records", foreign_keys=[parent_agreement_id])
