"""NEOS model: ConsentObjectionAddressed."""

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


class ConsentObjectionAddressed(TimestampMixin, Base):
    __tablename__ = "consent_objections_addressed"
    __table_args__ = (Index("ix_consent_objections_addressed_integration_round_id", "integration_round_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    integration_round_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("consent_integration_rounds.id"), nullable=False)
    objector: Mapped[str] = mapped_column(String(255), nullable=False)
    objection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    integration_round: Mapped[ConsentIntegrationRound] = relationship(back_populates="objections_addressed")
