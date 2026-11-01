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
    text,
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
    """Circuit breaker state for an ecosystem (Layer VIII); see api/AGENTS.md "Emergency and exit".

    pending -> open (co-signed) -> half_open (Recovery) -> closed; pending -> withdrawn.
    """
    __tablename__ = "emergency_states"
    __table_args__ = (
        Index("ix_emergency_states_ecosystem_id", "ecosystem_id"),
        # One live emergency per ecosystem, enforced by the database (concurrent declarations); q2a7c5e9d1b3.
        Index(
            "uq_emergency_states_one_live", "ecosystem_id", unique=True,
            postgresql_where=text("state IN ('pending', 'open', 'half_open')"),
            sqlite_where=text("state IN ('pending', 'open', 'half_open')"),
        ),
        CheckConstraint(
            "state IN ('pending', 'open', 'half_open', 'closed', 'withdrawn')",
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
    # Who opened it (member rows, not display text) and the timer the declarer asked for; added by q2a7c5e9d1b3.
    declared_by_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    co_signer_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    co_signed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    co_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    authority_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


# ========================
# EXIT & PORTABILITY (1 model)
# ========================
