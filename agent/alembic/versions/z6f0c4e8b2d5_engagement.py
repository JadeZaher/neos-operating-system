"""Add owner-scoped community engagement and durable delivery tables."""
from alembic import op
import sqlalchemy as sa

revision = "z6f0c4e8b2d5"
down_revision = "y5e9b3d7a1c4"
branch_labels = None
depends_on = None


def _uuid(name, target=None, *, primary=False, nullable=False, index=False, ondelete=None):
    constraints = [sa.ForeignKey(target, ondelete=ondelete)] if target else []
    return sa.Column(name, sa.Uuid(), *constraints, primary_key=primary, nullable=nullable, index=index)


def _text(name, size, *, nullable=False, unique=False, index=False, default=None):
    return sa.Column(name, sa.String(size), nullable=nullable, unique=unique, index=index, server_default=default)


def _date(name, *, nullable=True, default=False):
    return sa.Column(name, sa.DateTime(), nullable=nullable, server_default=sa.func.now() if default else None)


def _bool(name):
    return sa.Column(name, sa.Boolean(), nullable=False)


def _json(name, *, nullable=False):
    return sa.Column(name, sa.JSON(), nullable=nullable)


def _times():
    return [_date("created_at", nullable=False, default=True), _date("updated_at", nullable=False, default=True)]


def _tables():
    metadata = sa.MetaData()
    for external in ("users", "ecosystems", "auth_sessions"):
        sa.Table(external, metadata, _uuid("id", primary=True))
    return [
        sa.Table("engagement_preferences", metadata,
            _uuid("user_id", "users.id", primary=True), _text("timezone", 80),
            _text("quiet_start", 5, nullable=True), _text("quiet_end", 5, nullable=True),
            _date("paused_until"), _bool("email_enabled"), _bool("push_enabled"), _bool("sms_enabled"),
            _json("channel_enabled_at"), _bool("direct_messages"), *_times()),
        sa.Table("engagement_subscriptions", metadata,
            _uuid("id", primary=True), _uuid("user_id", "users.id", index=True),
            _text("scope_kind", 30), _uuid("scope_id"), _json("event_families"), _json("channels"),
            _text("frequency", 20), _bool("muted"), *_times(),
            sa.UniqueConstraint("user_id", "scope_kind", "scope_id", name="uq_engagement_subscription_scope")),
        sa.Table("engagement_events", metadata,
            _uuid("id", primary=True), _text("event_key", 255, unique=True), _text("family", 30),
            _text("event_type", 100), _uuid("actor_user_id", "users.id", nullable=True),
            _uuid("ecosystem_id", "ecosystems.id", nullable=True), _text("source_kind", 30), _uuid("source_id"),
            _uuid("domain_id", nullable=True), _uuid("team_id", nullable=True),
            sa.Column("audience_user_ids", sa.JSON(none_as_null=True), nullable=True), _date("occurred_at", nullable=False),
            _text("fanout_cursor", 40, nullable=True), sa.Column("fanout_complete", sa.Boolean(), nullable=False, index=True),
            _date("created_at", nullable=False, default=True),
            sa.Index("ix_engagement_event_scope_date", "ecosystem_id", "occurred_at", "id")),
        sa.Table("engagement_inbox_items", metadata,
            _uuid("id", primary=True), _uuid("user_id", "users.id"), _uuid("event_id", "engagement_events.id"),
            _text("reason_code", 100), sa.Column("in_app_visible", sa.Boolean(), server_default=sa.true(), nullable=False),
            _date("read_at"), _date("created_at", nullable=False),
            sa.UniqueConstraint("user_id", "event_id", name="uq_engagement_inbox_event"),
            sa.Index("ix_engagement_inbox_owner_read", "user_id", "read_at", "created_at")),
        sa.Table("notification_contacts", metadata,
            _uuid("id", primary=True), _uuid("user_id", "users.id", index=True), _text("channel", 20),
            _text("destination", 320), _text("destination_hash", 64, index=True),
            sa.Column("generation", sa.Integer(), nullable=False), _date("verified_at"), _date("revoked_at"),
            _date("suppressed_at"), _text("suppression_reason", 80, nullable=True), _date("created_at", nullable=False),
            sa.UniqueConstraint("user_id", "channel", "generation", name="uq_notification_contact_generation")),
        sa.Table("notification_challenges", metadata,
            _uuid("id", primary=True), _uuid("contact_id", "notification_contacts.id", index=True),
            _text("token_hash", 128), _date("expires_at", nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False), _date("used_at"),
            _text("provider_verification_id", 100, nullable=True), _date("created_at", nullable=False)),
        sa.Table("engagement_push_devices", metadata,
            _uuid("id", primary=True), _uuid("user_id", "users.id", index=True),
            _uuid("auth_session_id", "auth_sessions.id", nullable=True, ondelete="SET NULL"),
            _text("endpoint", 2048, unique=True), _text("p256dh_key", 255), _text("auth_key", 255),
            _bool("enabled"), *_times()),
        sa.Table("notification_deliveries", metadata,
            _uuid("id", primary=True), _text("delivery_key", 512, unique=True),
            _uuid("user_id", "users.id", index=True), _text("channel", 20),
            _uuid("contact_id", "notification_contacts.id", nullable=True),
            _uuid("device_id", "engagement_push_devices.id", nullable=True),
            _json("event_ids"), _text("state", 40), _date("due_at", nullable=False),
            sa.Column("attempt_count", sa.Integer(), nullable=False), _text("claim_token", 64, nullable=True),
            _date("lease_expires_at"), _date("attempt_started_at"), _date("first_attempt_at"),
            _date("accepted_at"), _date("delivered_at"), _text("provider_message_id", 255, nullable=True, index=True),
            _json("frozen_payload", nullable=True), _text("error_code", 100, nullable=True), *_times(),
            sa.Index("ix_notification_delivery_due", "state", "due_at")),
        sa.Table("notification_consumptions", metadata,
            _uuid("id", primary=True), _uuid("user_id", "users.id"), _uuid("event_id", "engagement_events.id"),
            _text("channel", 20), _text("target_key", 80, default=""),
            _uuid("delivery_id", "notification_deliveries.id", index=True), _date("created_at", nullable=False),
            sa.UniqueConstraint("user_id", "event_id", "channel", "target_key", name="uq_notification_consumption_event")),
        sa.Table("notification_webhook_receipts", metadata,
            _uuid("id", primary=True), _text("provider", 30), _text("receipt_key", 255, unique=True),
            _date("received_at", nullable=False)),
        sa.Table("notification_rate_limits", metadata,
            _uuid("id", primary=True), _text("bucket_key", 512, unique=True),
            sa.Column("window_start", sa.DateTime(), nullable=False, index=True),
            sa.Column("count", sa.Integer(), nullable=False)),
    ]


def upgrade():
    for table in _tables():
        table.create(op.get_bind(), checkfirst=True)


def downgrade():
    for table in reversed(_tables()):
        table.drop(op.get_bind(), checkfirst=True)
