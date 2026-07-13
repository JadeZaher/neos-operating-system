"""NEOS model: AgreementVersion."""

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


class AgreementVersion(TimestampMixin, Base):
    """Immutable snapshot of an agreement before each edit, enabling rollback."""
    __tablename__ = "agreement_versions"
    __table_args__ = (Index("ix_agreement_versions_agreement_id", "agreement_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    proposer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hierarchy_level: Mapped[str] = mapped_column(String(50), nullable=False, default="domain")
    affected_parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sunset_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ratification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    version_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    changed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    agreement: Mapped[Agreement] = relationship(back_populates="versions")
