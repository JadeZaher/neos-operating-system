"""NEOS model: ConsentIntegrationRound."""

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


class ConsentIntegrationRound(TimestampMixin, Base):
    __tablename__ = "consent_integration_rounds"
    __table_args__ = (Index("ix_consent_integration_rounds_consent_record_id", "consent_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    consent_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("consent_records.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    modifications_made: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    consent_record: Mapped[ConsentRecord] = relationship(back_populates="integration_rounds")
    objections_addressed: Mapped[list[ConsentObjectionAddressed]] = relationship(back_populates="integration_round")
