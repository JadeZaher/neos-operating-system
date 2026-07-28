"""Participation gates declared by a governance agreement."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class AgreementRequirement(TimestampMixin, Base):
    """Applies a consented agreement as a participation prerequisite."""

    __tablename__ = "agreement_requirements"
    __table_args__ = (
        UniqueConstraint(
            "agreement_id", "target_kind", "target_id",
            name="uq_agreement_requirement_target",
        ),
        Index("ix_agreement_requirements_target", "target_kind", "target_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    target_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    enforcement: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
