"""NEOS model: JourneyMap."""

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
# ORIENTATION & JOURNEY MAP (3 models)
# ========================

class JourneyMap(TimestampMixin, Base):
    """A configurable orientation journey for new or existing members."""
    __tablename__ = "journey_maps"
    __table_args__ = (
        Index("ix_journey_maps_slug", "slug"),
        Index("ix_journey_maps_ecosystem_id", "ecosystem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ecosystem_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=True)
    sector_alignment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # list of sector strings
    role_types: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # list of role type strings
    min_alignment_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_sequence: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)  # list of JourneyStep objects
    exit_package: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # docs, tools, next_steps
    step_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
