"""NEOS model: DecisionRecord."""

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
# MEMORY (4 models)
# ========================

class DecisionRecord(TimestampMixin, Base):
    __tablename__ = "decision_records"
    __table_args__ = (Index("ix_decision_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    shared_ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # additional ecosystems for cross-ecosystem work
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    holding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ratio_decidendi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    obiter_dicta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deliberation_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_skill: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_layer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    artifact_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    artifact_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    precedent_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    overruled_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    superseded_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    related_records: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    recorder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recorder_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verification_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    dissent_records: Mapped[list[DecisionDissentRecord]] = relationship(back_populates="decision_record")
    participants: Mapped[list[DecisionParticipant]] = relationship(back_populates="decision_record")
    semantic_tags: Mapped[list[DecisionSemanticTag]] = relationship(back_populates="decision_record")
