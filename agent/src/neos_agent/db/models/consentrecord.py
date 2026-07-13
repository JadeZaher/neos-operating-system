"""NEOS model: ConsentRecord."""

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


class ConsentRecord(TimestampMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (Index("ix_consent_records_proposal_id", "proposal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("proposals.id"), nullable=False)
    consent_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    weighting_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    facilitator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    quorum_required: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quorum_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    escalation_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    final_proposal_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    proposal: Mapped[Proposal] = relationship(back_populates="consent_records")
    participants: Mapped[list[ConsentParticipant]] = relationship(back_populates="consent_record")
    integration_rounds: Mapped[list[ConsentIntegrationRound]] = relationship(back_populates="consent_record")
