"""NEOS model: TestSuccessCriterion."""

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


class TestSuccessCriterion(TimestampMixin, Base):
    __tablename__ = "test_success_criteria"
    __table_args__ = (Index("ix_test_success_criteria_test_report_id", "test_report_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    test_report_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("test_reports.id"), nullable=False)
    criterion: Mapped[str] = mapped_column(String(500), nullable=False)
    met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    test_report: Mapped[TestReport] = relationship(back_populates="success_criteria")


# ========================
# MEMORY (4 models)
# ========================
