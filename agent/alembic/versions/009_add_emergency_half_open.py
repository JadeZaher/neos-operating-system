"""Add half_open_entered_at column and state CHECK constraint to emergency_states.

Enforces the mandatory Half-Open Recovery state per NEOS Principle 4 and
emergency-reversion SKILL.md: circuit breaker must transition open→half_open→closed
— no direct open→closed path is allowed.

Changes:
- Add half_open_entered_at (DateTime, nullable) — timestamp when Recovery started.
- Add CHECK constraint ck_emergency_states_valid_state ensuring state is one of
  'open', 'half_open', or 'closed'.

Revision ID: 009_add_emergency_half_open
Revises: 008_add_chat_privacy_and_tokens
Create Date: 2026-06-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "009_add_emergency_half_open"
down_revision = "008_add_chat_privacy_and_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "emergency_states",
        sa.Column("half_open_entered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_emergency_states_valid_state",
        "emergency_states",
        "state IN ('open', 'half_open', 'closed')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_emergency_states_valid_state",
        "emergency_states",
        type_="check",
    )
    op.drop_column("emergency_states", "half_open_entered_at")
