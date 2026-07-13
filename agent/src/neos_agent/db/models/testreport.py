"""NEOS model: TestReport."""

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


class TestReport(TimestampMixin, Base):
    __tablename__ = "test_reports"
    __table_args__ = (Index("ix_test_reports_proposal_id", "proposal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("proposals.id"), nullable=False)
    test_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    test_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    midpoint_checkin_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    revert_procedure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    midpoint_findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extension_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    modifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    agreement_registry_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    success_criteria_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    proposal: Mapped[Proposal] = relationship(back_populates="test_reports")
    success_criteria: Mapped[list[TestSuccessCriterion]] = relationship(back_populates="test_report")
