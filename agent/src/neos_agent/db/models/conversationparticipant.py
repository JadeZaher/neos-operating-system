"""NEOS model: ConversationParticipant."""

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


class ConversationParticipant(TimestampMixin, Base):
    """Links a member to a conversation with a role and read tracking."""
    __tablename__ = "conversation_participants"
    __table_args__ = (
        UniqueConstraint("conversation_id", "member_id", name="uq_conversation_member"),
        Index("ix_conversation_participants_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conversations.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")  # "owner" | "admin" | "member"
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="participants")
