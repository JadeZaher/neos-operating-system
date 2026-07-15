"""NEOS model: CtcHandoff (Charting-the-Course → NEOS Den readiness).

Minimal handoff record tracking whether a member is marked ready for the
NEOS Den. See db/models/AGENTS.md.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class CtcHandoff(TimestampMixin, Base):
    __tablename__ = "ctc_handoff"
    __table_args__ = (UniqueConstraint("member_id", name="uq_ctc_handoff_member"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    ready_for_neos_den: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
