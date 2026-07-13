"""NEOS model: Collaboration."""

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
# COLLABORATIONS (1 model)
# ========================

class Collaboration(TimestampMixin, Base):
    """A cross-domain or cross-ecosystem collaboration agreement.

    Links two domains that have matched shares/needs and agreed to collaborate.
    """
    __tablename__ = "collaborations"
    __table_args__ = (
        Index("ix_collaborations_source_domain_id", "source_domain_id"),
        Index("ix_collaborations_target_domain_id", "target_domain_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    source_domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    target_domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="proposed")  # proposed, active, completed, dissolved
    engagement_tier: Mapped[str] = mapped_column(String(50), nullable=False, default="cooperate")  # observe, cooperate, federate, integrate
    terms: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # collaboration-specific terms
    linked_shares_needs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # IDs of matched shares/needs
    started_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    version_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


# ========================
# COMPLIANCE SUMMARY (1 model)
# ========================
