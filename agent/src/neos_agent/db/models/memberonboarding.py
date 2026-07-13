"""NEOS model: MemberOnboarding."""

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


class MemberOnboarding(TimestampMixin, Base):
    __tablename__ = "member_onboarding"
    __table_args__ = (Index("ix_member_onboarding_member_id", "member_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    facilitator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mentor_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    uaf_version_consented: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    consent_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cooling_off_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cooling_off_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    section_consents: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    checklist_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    completion_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    member: Mapped[Member] = relationship(back_populates="onboarding", foreign_keys=[member_id])
