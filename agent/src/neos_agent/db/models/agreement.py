"""NEOS model: Agreement."""

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
# AGREEMENTS (4 models)
# ========================

class Agreement(TimestampMixin, Base):
    __tablename__ = "agreements"
    __table_args__ = (Index("ix_agreements_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    shared_ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # additional ecosystems for cross-ecosystem work
    agreement_id: Mapped[str] = mapped_column(String(100), nullable=False)  # business key
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    proposer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    affected_parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hierarchy_level: Mapped[str] = mapped_column(String(50), nullable=False, default="domain")
    parent_agreement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("agreements.id"), nullable=True
    )
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sunset_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ratification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    version_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    requires_explicit_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    prerequisite_scopes: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    prerequisite_domain_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    alignment_points: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    # ACT gate policy declared at the agreement level:
    # {"min_advice_rounds": int, "consent_required": bool,
    #  "consent_quorum": int|None, "test_cases": [str]}
    act_policy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    ecosystem: Mapped[Ecosystem] = relationship(back_populates="agreements")
    parent_agreement: Mapped[Optional[Agreement]] = relationship(remote_side="Agreement.id")
    ratification_records: Mapped[list[AgreementRatificationRecord]] = relationship(back_populates="agreement")
    ceremonies: Mapped[list["AgreementCeremony"]] = relationship(
        back_populates="agreement", order_by="AgreementCeremony.created_at"
    )
    amendment_records: Mapped[list[AmendmentRecord]] = relationship(
        back_populates="agreement", foreign_keys="AmendmentRecord.parent_agreement_id"
    )
    review_records: Mapped[list[ReviewRecord]] = relationship(back_populates="agreement")
    versions: Mapped[list["AgreementVersion"]] = relationship(back_populates="agreement", order_by="AgreementVersion.created_at.desc()")
