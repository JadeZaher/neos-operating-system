"""Auditable governance-ceremony record for an agreement lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ._base import Base, GUID, TimestampMixin


class AgreementCeremony(TimestampMixin, Base):
    """Records the advice, consent, test, and activation ceremonies."""

    __tablename__ = "agreement_ceremonies"
    __table_args__ = (Index("ix_agreement_ceremonies_agreement_id", "agreement_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_by_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=True
    )
    outcome: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    agreement: Mapped["Agreement"] = relationship(back_populates="ceremonies")
