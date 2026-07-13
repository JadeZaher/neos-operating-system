"""NEOS model: UserJourneyProgress."""

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


class UserJourneyProgress(TimestampMixin, Base):
    """Tracks a member's progress through a journey map."""
    __tablename__ = "user_journey_progress"
    __table_args__ = (
        Index("ix_user_journey_progress_member_ecosystem", "member_id", "ecosystem_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    journey_map_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("journey_maps.id"), nullable=False)
    orientation_path: Mapped[str] = mapped_column(String(20), nullable=False, default="explorer")  # ready | explorer
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_steps: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)  # list of step indices
    step_responses: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)  # step_key -> response data
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")  # not_started | in_progress | complete | opted_out
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    was_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    misalignment_flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
