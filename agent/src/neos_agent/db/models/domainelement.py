"""NEOS model: DomainElement."""

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


class DomainElement(TimestampMixin, Base):
    __tablename__ = "domain_elements"
    __table_args__ = (Index("ix_domain_elements_domain_id", "domain_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    element_name: Mapped[str] = mapped_column(String(100), nullable=False)
    element_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    domain: Mapped[Domain] = relationship(back_populates="domain_elements")
