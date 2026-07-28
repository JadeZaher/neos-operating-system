"""An ecosystem's accountable approval of a proposed collaboration."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class CollaborationApproval(TimestampMixin, Base):
    """Records the local approval needed before a collaboration activates."""

    __tablename__ = "collaboration_approvals"
    __table_args__ = (
        UniqueConstraint("collaboration_id", "ecosystem_id", name="uq_collaboration_approval_ecosystem"),
        Index("ix_collaboration_approvals_collaboration_id", "collaboration_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    collaboration_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("collaborations.id"), nullable=False
    )
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ecosystems.id"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
