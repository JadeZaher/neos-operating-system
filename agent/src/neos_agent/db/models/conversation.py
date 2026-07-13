"""NEOS model: Conversation."""

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
# MESSAGING (4 models)
# ========================

class Conversation(TimestampMixin, Base):
    """An ecosystem-scoped conversation thread (DM or group)."""
    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # "dm" | "group"
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)

    # Relationships
    participants: Mapped[list["ConversationParticipant"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    links: Mapped[list["ConversationLink"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
