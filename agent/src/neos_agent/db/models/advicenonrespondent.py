"""NEOS model: AdviceNonRespondent."""

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


class AdviceNonRespondent(TimestampMixin, Base):
    __tablename__ = "advice_non_respondents"
    __table_args__ = (Index("ix_advice_non_respondents_advice_log_id", "advice_log_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    advice_log_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("advice_logs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notified_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    follow_up_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    advice_log: Mapped[AdviceLog] = relationship(back_populates="non_respondents")
