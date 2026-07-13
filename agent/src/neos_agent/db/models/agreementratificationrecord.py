"""NEOS model: AgreementRatificationRecord."""

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


class AgreementRatificationRecord(TimestampMixin, Base):
    __tablename__ = "agreement_ratification_records"
    __table_args__ = (Index("ix_agreement_ratification_records_agreement_id", "agreement_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    participant: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    agreement: Mapped[Agreement] = relationship(back_populates="ratification_records")
