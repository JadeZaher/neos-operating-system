"""NEOS model: DecisionDissentRecord."""

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


class DecisionDissentRecord(TimestampMixin, Base):
    __tablename__ = "decision_dissent_records"
    __table_args__ = (Index("ix_decision_dissent_records_decision_record_id", "decision_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("decision_records.id"), nullable=False)
    objector: Mapped[str] = mapped_column(String(255), nullable=False)
    objection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    decision_record: Mapped[DecisionRecord] = relationship(back_populates="dissent_records")
