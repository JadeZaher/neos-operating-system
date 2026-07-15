"""NEOS model: BadgeDefinition (admin-managed badge catalog).

Distinct from UserBadge (db/course_models.py), which is an *earned* badge award.
This is the catalog of definable badges admins create; awards reference it by
badge_key. See db/models/AGENTS.md.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class BadgeDefinition(TimestampMixin, Base):
    __tablename__ = "badge_definitions"
    __table_args__ = (
        UniqueConstraint("ecosystem_id", "badge_key", name="uq_badge_definition_ecosystem_key"),
        Index("ix_badge_definitions_ecosystem_id", "ecosystem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("ecosystems.id"), nullable=True
    )  # null = global/cross-ecosystem badge
    badge_key: Mapped[str] = mapped_column(String(255), nullable=False)  # business key
    badge_name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    badge_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    badge_icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # emoji or short token
    strength: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
