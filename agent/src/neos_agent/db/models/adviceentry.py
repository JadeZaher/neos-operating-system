"""NEOS model: AdviceEntry."""

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


class AdviceEntry(TimestampMixin, Base):
    __tablename__ = "advice_entries"
    __table_args__ = (Index("ix_advice_entries_advice_log_id", "advice_log_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    advice_log_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("advice_logs.id"), nullable=False)
    advisor: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ethos: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advice_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposer_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    integration_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    advice_log: Mapped[AdviceLog] = relationship(back_populates="entries")
