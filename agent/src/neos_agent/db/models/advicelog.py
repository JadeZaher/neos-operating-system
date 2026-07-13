"""NEOS model: AdviceLog."""

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


class AdviceLog(TimestampMixin, Base):
    __tablename__ = "advice_logs"
    __table_args__ = (Index("ix_advice_logs_proposal_id", "proposal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("proposals.id"), nullable=False)
    advice_window_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advice_window_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposer_modifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    proposal: Mapped[Proposal] = relationship(back_populates="advice_logs")
    entries: Mapped[list[AdviceEntry]] = relationship(back_populates="advice_log")
    non_respondents: Mapped[list[AdviceNonRespondent]] = relationship(back_populates="advice_log")
