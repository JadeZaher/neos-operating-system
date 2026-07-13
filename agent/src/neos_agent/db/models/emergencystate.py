"""NEOS model: EmergencyState."""

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
# EMERGENCY (1 model)
# ========================

class EmergencyState(TimestampMixin, Base):
    """Circuit breaker state tracking for an ecosystem (Layer VIII).

    State machine:  closed -> open -> half_open -> closed
    - open: emergency declared, authority active
    - half_open: Recovery state (mandatory, cannot be skipped). 30-day window
      for post-emergency review and decision ratification per SKILL.md
      section E step 3.  closed_at must be NULL; half_open_entered_at set.
    - closed: normal governance fully restored.  Must have been in half_open
      prior (no direct open->closed path allowed).
    """
    __tablename__ = "emergency_states"
    __table_args__ = (
        Index("ix_emergency_states_ecosystem_id", "ecosystem_id"),
        CheckConstraint(
            "state IN ('open', 'half_open', 'closed')",
            name="ck_emergency_states_valid_state",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="closed")
    declared_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    declared_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    criteria_met: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    auto_revert_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    half_open_entered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    recovery_entered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    pre_authorized_roles: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    actions_log: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    post_review_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ========================
# EXIT & PORTABILITY (1 model)
# ========================
