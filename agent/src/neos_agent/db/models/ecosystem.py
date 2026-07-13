"""NEOS model: Ecosystem."""

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
# CORE (8 models)
# ========================

class Ecosystem(TimestampMixin, Base):
    __tablename__ = "ecosystems"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uaf_agreement_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    # Directory fields
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    founded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    governance_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")

    # Relationships
    members: Mapped[list[Member]] = relationship(back_populates="ecosystem")
    domains: Mapped[list[Domain]] = relationship(back_populates="ecosystem")
    agreements: Mapped[list[Agreement]] = relationship(back_populates="ecosystem")
    proposals: Mapped[list[Proposal]] = relationship(back_populates="ecosystem")
