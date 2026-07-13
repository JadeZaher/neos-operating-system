"""NEOS model: GovernanceHealthAudit."""

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


class GovernanceHealthAudit(TimestampMixin, Base):
    """Periodic governance health assessment (Layer VII)."""
    __tablename__ = "governance_health_audits"
    __table_args__ = (Index("ix_governance_health_audits_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    audit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    audit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    auditor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    capture_risk_indicators: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    overall_health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    next_audit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Extended audit fields (Layer VII governance-health-audit spec)
    audit_scope: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audit_period_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    audit_period_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    auditor_ids: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    overall_health: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    indicator_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    triggered_safeguards: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    structured_recommendations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    trigger_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    next_audit_due: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


# ========================
# EMERGENCY (1 model)
# ========================
