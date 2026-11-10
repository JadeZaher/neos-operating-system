"""Ecosystem cross-link admins: Lead Link (internal) and Rep Link (external)."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import GUID, TimestampMixin, Base


class EcosystemAdmin(TimestampMixin, Base):
    """One cross-link held by a member. A person may hold internal and external together."""

    __tablename__ = "ecosystem_admins"
    __table_args__ = (
        UniqueConstraint("ecosystem_id", "member_id", "designation", name="uq_ecosystem_admin_designation"),
        Index("ix_ecosystem_admins_ecosystem_id", "ecosystem_id"),
        Index("ix_ecosystem_admins_member_id", "member_id"),
        CheckConstraint("designation IN ('internal', 'external')", name="ck_ecosystem_admin_designation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id", ondelete="CASCADE"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    designation: Mapped[str] = mapped_column(String(20), nullable=False)  # internal (Lead Link) | external (Rep Link)
    appointed_by_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
