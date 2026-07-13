"""NEOS model: PushSubscription."""

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
# PUSH NOTIFICATIONS (1 model)
# ========================

class PushSubscription(TimestampMixin, Base):
    """Web Push subscription for PWA notifications."""
    __tablename__ = "push_subscriptions"
    __table_args__ = (
        Index("ix_push_subscriptions_member_id", "member_id"),
        UniqueConstraint("member_id", "endpoint", name="uq_push_subscription_member_endpoint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh_key: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_key: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notification_types: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # which types user wants


# ========================
# ORIENTATION & JOURNEY MAP (3 models)
# ========================
