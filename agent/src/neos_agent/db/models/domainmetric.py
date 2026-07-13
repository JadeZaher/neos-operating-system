"""NEOS model: DomainMetric."""

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


class DomainMetric(TimestampMixin, Base):
    __tablename__ = "domain_metrics"
    __table_args__ = (Index("ix_domain_metrics_domain_id", "domain_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    measurement_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    domain: Mapped[Domain] = relationship(back_populates="domain_metrics")


# ========================
# AGREEMENTS (4 models)
# ========================
