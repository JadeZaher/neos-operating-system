"""NEOS model: ComplianceSummary."""

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


# ========================
# COMPLIANCE SUMMARY (1 model)
# ========================

class ComplianceSummary(TimestampMixin, Base):
    """AI-generated compliance summary for an ecosystem, regenerated on a 30-day cycle."""
    __tablename__ = "compliance_summaries"
    __table_args__ = (
        Index("ix_compliance_summaries_ecosystem_id", "ecosystem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # structured compliance metrics
    agreement_coverage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # which agreements are compliant
    domain_health: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # domain-level compliance
    flagged_issues: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # items needing attention


# ========================
# PUSH NOTIFICATIONS (1 model)
# ========================
