"""NEOS model: ReviewRecord."""

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


class ReviewRecord(TimestampMixin, Base):
    __tablename__ = "review_records"
    __table_args__ = (Index("ix_review_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    review_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    agreement_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_body: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    evaluation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    follow_up_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    agreement: Mapped[Agreement] = relationship(back_populates="review_records")


# ========================
# ACT PROCESS (10 models)
# ========================
