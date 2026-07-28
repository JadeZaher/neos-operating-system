"""Immutable ledger of alignment changes earned through agreement consent."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class MemberAlignmentEvent(TimestampMixin, Base):
    """Records the exact consent event responsible for an alignment delta."""

    __tablename__ = "member_alignment_events"
    __table_args__ = (
        UniqueConstraint(
            "agreement_consent_id", "event_kind",
            name="uq_alignment_event_consent_kind",
        ),
        Index("ix_member_alignment_events_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    agreement_consent_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("agreement_member_consents.id"), nullable=False
    )
    event_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1")
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
