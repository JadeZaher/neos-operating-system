"""NEOS model: CircleMembership."""

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
# CIRCLE MEMBERSHIP (1 model)
# ========================

class CircleMembership(TimestampMixin, Base):
    """Links a member to a domain (circle) with a specific role."""
    __tablename__ = "circle_memberships"
    __table_args__ = (
        UniqueConstraint("domain_id", "member_id", name="uq_circle_domain_member"),
        Index("ix_circle_memberships_member_id", "member_id"),
        Index("ix_circle_memberships_domain_id", "domain_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")  # steward, delegate, member
    joined_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")


# ========================
# SHARES & NEEDS (1 model)
# ========================
