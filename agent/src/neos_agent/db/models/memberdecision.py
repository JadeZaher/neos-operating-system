"""NEOS model: MemberDecision.

One member's personal decision about a subject (agreement, proposal, share,
or need) — the user-owned decision substrate. Distinct from DecisionRecord
(the ecosystem artifact ledger minted by completed ACT processes): a
MemberDecision belongs to its owning member and doubles as a follow-up task
with a personal state. Only the owning member may see or edit it.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class MemberDecision(TimestampMixin, Base):
    __tablename__ = "member_decisions"
    __table_args__ = (
        Index("ix_member_decisions_member_id", "member_id"),
        Index("ix_member_decisions_subject", "subject_type", "subject_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)  # the OWNER
    subject_type: Mapped[str] = mapped_column(String(20), nullable=False)  # agreement | proposal | share | need
    # Polymorphic subject — validated in the API layer (no DB FK).
    subject_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    decision: Mapped[str] = mapped_column(String(500), nullable=False)  # what they decided
    # intended | in_progress | done | follow_up | dropped
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="intended")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
