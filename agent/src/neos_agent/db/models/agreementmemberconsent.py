"""Version-bound, self-attested agreement participation consent."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class AgreementMemberConsent(TimestampMixin, Base):
    """A member's personal acceptance of one agreement version."""

    __tablename__ = "agreement_member_consents"
    __table_args__ = (
        UniqueConstraint(
            "agreement_id", "member_id", "agreement_version",
            name="uq_agreement_member_consent_version",
        ),
        Index("ix_agreement_member_consents_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    agreement_version: Mapped[str] = mapped_column(String(20), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    attestation: Mapped[str] = mapped_column(Text, nullable=False)
    attested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    withdrawn_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    withdrawal_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
