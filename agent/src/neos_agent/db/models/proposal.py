"""NEOS model: Proposal."""

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
# ACT PROCESS (10 models)
# ========================

class Proposal(TimestampMixin, Base):
    __tablename__ = "proposals"
    __table_args__ = (Index("ix_proposals_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    shared_ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # additional ecosystems for cross-ecosystem work
    proposal_id: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    proposer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    co_sponsors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    affected_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    impacted_parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    proposed_change: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advice_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    consent_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    test_duration: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_proposals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    synergy_check: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # ACT gate policy declared at the proposal level:
    # {"min_advice_rounds": int, "consent_required": bool,
    #  "consent_quorum": int|None, "test_cases": [str]}
    # NULL means the gates are inherited from the governing agreement
    # (governing_agreement_id), falling back to engine defaults.
    act_policy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    governing_agreement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("agreements.id"), nullable=True
    )

    ecosystem: Mapped[Ecosystem] = relationship(back_populates="proposals")
    advice_logs: Mapped[list[AdviceLog]] = relationship(back_populates="proposal")
    consent_records: Mapped[list[ConsentRecord]] = relationship(back_populates="proposal")
    test_reports: Mapped[list[TestReport]] = relationship(back_populates="proposal")
