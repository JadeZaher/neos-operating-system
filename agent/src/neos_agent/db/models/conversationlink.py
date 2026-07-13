"""NEOS model: ConversationLink."""

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


class ConversationLink(TimestampMixin, Base):
    """Links a conversation to a governance entity (proposal, agreement, etc.)."""
    __tablename__ = "conversation_links"
    __table_args__ = (
        Index("ix_conversation_links_entity", "entity_type", "entity_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conversations.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "proposal" | "agreement" | "domain" | "conflict" | "decision"
    entity_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="links")


# ========================
# CIRCLE MEMBERSHIP (1 model)
# ========================
