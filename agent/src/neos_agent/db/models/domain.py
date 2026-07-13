"""NEOS model: Domain."""

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


class Domain(TimestampMixin, Base):
    __tablename__ = "domains"
    __table_args__ = (Index("ix_domains_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    shared_ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # additional ecosystems for cross-ecosystem work
    domain_id: Mapped[str] = mapped_column(String(100), nullable=False)  # business key
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_steward: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    steward_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    parent_domain_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metric_definitions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    elements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSONB for complex elements
    version_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    ecosystem: Mapped[Ecosystem] = relationship(back_populates="domains")
    domain_elements: Mapped[list[DomainElement]] = relationship(back_populates="domain")
    domain_metrics: Mapped[list[DomainMetric]] = relationship(back_populates="domain")
