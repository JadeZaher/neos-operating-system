"""Durable community activity, preferences and notification delivery records."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func, true
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class EngagementPreference(TimestampMixin, Base):
    __tablename__ = "engagement_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), primary_key=True)
    timezone: Mapped[str] = mapped_column(String(80), default="UTC", nullable=False)
    quiet_start: Mapped[str | None] = mapped_column(String(5))
    quiet_end: Mapped[str | None] = mapped_column(String(5))
    paused_until: Mapped[datetime | None] = mapped_column(DateTime)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    channel_enabled_at: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    direct_messages: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EngagementSubscription(TimestampMixin, Base):
    __tablename__ = "engagement_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "scope_kind", "scope_id", name="uq_engagement_subscription_scope"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    scope_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    scope_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    event_families: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    channels: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), default="daily", nullable=False)
    muted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EngagementEvent(Base):
    __tablename__ = "engagement_events"
    __table_args__ = (Index("ix_engagement_event_scope_date", "ecosystem_id", "occurred_at", "id"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    event_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    family: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("users.id"))
    ecosystem_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("ecosystems.id"))
    source_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    domain_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    team_id: Mapped[uuid.UUID | None] = mapped_column(GUID())
    audience_user_ids: Mapped[list | None] = mapped_column(JSON(none_as_null=True))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    fanout_cursor: Mapped[str | None] = mapped_column(String(40))
    fanout_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)


class EngagementInboxItem(Base):
    __tablename__ = "engagement_inbox_items"
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_engagement_inbox_event"), Index("ix_engagement_inbox_owner_read", "user_id", "read_at", "created_at"))
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("engagement_events.id"), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    in_app_visible: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NotificationContact(Base):
    __tablename__ = "notification_contacts"
    __table_args__ = (UniqueConstraint("user_id", "channel", "generation", name="uq_notification_contact_generation"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    destination: Mapped[str] = mapped_column(String(320), nullable=False)
    destination_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    generation: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    suppressed_at: Mapped[datetime | None] = mapped_column(DateTime)
    suppression_reason: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NotificationChallenge(Base):
    __tablename__ = "notification_challenges"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("notification_contacts.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    provider_verification_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class EngagementPushDevice(TimestampMixin, Base):
    __tablename__ = "engagement_push_devices"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    auth_session_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("auth_sessions.id", ondelete="SET NULL"))
    endpoint: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    p256dh_key: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_key: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NotificationDelivery(TimestampMixin, Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (Index("ix_notification_delivery_due", "state", "due_at"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    delivery_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("notification_contacts.id"))
    device_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("engagement_push_devices.id"))
    event_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    state: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    claim_token: Mapped[str | None] = mapped_column(String(64))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    attempt_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    first_attempt_at: Mapped[datetime | None] = mapped_column(DateTime)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), index=True)
    frozen_payload: Mapped[dict | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String(100))


class NotificationConsumption(Base):
    __tablename__ = "notification_consumptions"
    __table_args__ = (UniqueConstraint("user_id", "event_id", "channel", "target_key", name="uq_notification_consumption_event"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("engagement_events.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    target_key: Mapped[str] = mapped_column(String(80), default="", server_default="", nullable=False)
    delivery_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("notification_deliveries.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NotificationWebhookReceipt(Base):
    __tablename__ = "notification_webhook_receipts"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    receipt_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NotificationRateLimit(Base):
    __tablename__ = "notification_rate_limits"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    bucket_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    window_start: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
