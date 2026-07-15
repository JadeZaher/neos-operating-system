"""NEOS model: SharesNeeds."""

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
# SHARES & NEEDS (1 model)
# ========================

class SharesNeeds(TimestampMixin, Base):
    """A domain-level declaration of what resources/skills are shared or needed.

    Used for cross-ecosystem discovery and collaboration matching.
    """
    __tablename__ = "shares_needs"
    __table_args__ = (
        Index("ix_shares_needs_domain_id", "domain_id"),
        Index("ix_shares_needs_ecosystem_id", "ecosystem_id"),
        Index("ix_shares_needs_type", "type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # "share" | "need"
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # technology, resources, skills, knowledge, infrastructure, funding, space, labor, other
    capacity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # availability level
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")  # public, ecosystem, private
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, fulfilled, withdrawn


# ========================
# COLLABORATIONS (1 model)
# ========================
