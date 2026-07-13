"""NEOS model: DecisionParticipant."""

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


class DecisionParticipant(TimestampMixin, Base):
    __tablename__ = "decision_participants"
    __table_args__ = (Index("ix_decision_participants_decision_record_id", "decision_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("decision_records.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    decision_record: Mapped[DecisionRecord] = relationship(back_populates="participants")
