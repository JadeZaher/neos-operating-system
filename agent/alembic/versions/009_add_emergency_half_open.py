"""Add half_open_entered_at column and state CHECK constraint to emergency_states.

Enforces the mandatory Half-Open Recovery state per NEOS Principle 4 and
emergency-reversion SKILL.md: circuit breaker must transition open->half_open->closed
- no direct open->closed path is allowed.

Changes:
- Idempotently ensure the `emergency_states` table exists. (Prior alembic
  migrations did not create it; environments that bootstrapped via
  ``Base.metadata.create_all`` already have it, but plain `alembic upgrade`
  on a fresh database does not. This migration tolerates both.)
- Add `half_open_entered_at` (DateTime, nullable) - timestamp when Recovery started.
- Normalise any pre-existing rows whose `state` value is outside the
  vocabulary (`open`, `half_open`, `closed`) by mapping legacy `resolved`
  to `closed` and unknown values to `closed`, so the CHECK constraint
  installs cleanly on populated databases.
- Add CHECK constraint `ck_emergency_states_valid_state` ensuring state is one of
  'open', 'half_open', or 'closed'.

Revision ID: 009_add_emergency_half_open
Revises: 008_add_chat_privacy_and_tokens
Create Date: 2026-06-10 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "009_add_emergency_half_open"
down_revision = "008_add_chat_privacy_and_tokens"
branch_labels = None
depends_on = None


_VALID_STATES = ("open", "half_open", "closed")


def _table_exists(bind: sa.engine.Connection, name: str) -> bool:
    inspector = sa.inspect(bind)
    return name in inspector.get_table_names()


def _column_exists(bind: sa.engine.Connection, table: str, column: str) -> bool:
    inspector = sa.inspect(bind)
    return any(c["name"] == column for c in inspector.get_columns(table))


def _constraint_exists(
    bind: sa.engine.Connection, table: str, name: str
) -> bool:
    inspector = sa.inspect(bind)
    try:
        return any(
            c.get("name") == name
            for c in inspector.get_check_constraints(table)
        )
    except NotImplementedError:
        # SQLite reflection may not expose check constraints; assume
        # absent and let CREATE either succeed or be a no-op on retry.
        return False


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Ensure the parent table exists. Prior alembic history did not
    #    create `emergency_states`; environments bootstrapped via
    #    `Base.metadata.create_all` already have it. This migration must
    #    work in both worlds, so we recreate the table from scratch
    #    only when missing (idempotent and matches models.py exactly).
    if not _table_exists(bind, "emergency_states"):
        op.create_table(
            "emergency_states",
            sa.Column("id", sa.CHAR(32), primary_key=True, nullable=False),
            sa.Column("ecosystem_id", sa.CHAR(32), sa.ForeignKey("ecosystems.id"), nullable=False),
            sa.Column("state", sa.String(50), nullable=False, server_default="closed"),
            sa.Column("declared_at", sa.DateTime(), nullable=True),
            sa.Column("declared_by", sa.String(255), nullable=True),
            sa.Column("criteria_met", sa.JSON(), nullable=True),
            sa.Column("auto_revert_at", sa.DateTime(), nullable=True),
            sa.Column("recovery_entered_at", sa.DateTime(), nullable=True),
            sa.Column("closed_at", sa.DateTime(), nullable=True),
            sa.Column("pre_authorized_roles", sa.JSON(), nullable=True),
            sa.Column("actions_log", sa.JSON(), nullable=True),
            sa.Column("post_review_status", sa.String(50), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_emergency_states_ecosystem_id",
            "emergency_states",
            ["ecosystem_id"],
        )

    # 2. Add half_open_entered_at column if not already present.
    if not _column_exists(bind, "emergency_states", "half_open_entered_at"):
        op.add_column(
            "emergency_states",
            sa.Column(
                "half_open_entered_at",
                sa.DateTime(),
                nullable=True,
            ),
        )

    # 3. Normalise any pre-existing rows whose `state` value is outside
    #    the new vocabulary. Without this step, populated production
    #    databases (which historically allowed e.g. 'resolved') would
    #    fail the CHECK constraint addition.
    op.execute(
        sa.text(
            "UPDATE emergency_states SET state = 'closed' "
            "WHERE state = 'resolved'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE emergency_states SET state = 'closed' "
            "WHERE state NOT IN ('open', 'half_open', 'closed')"
        )
    )

    # 4. Install the CHECK constraint. Skip if already there to keep the
    #    migration idempotent across re-runs.
    if not _constraint_exists(
        bind, "emergency_states", "ck_emergency_states_valid_state"
    ):
        op.create_check_constraint(
            "ck_emergency_states_valid_state",
            "emergency_states",
            "state IN ('open', 'half_open', 'closed')",
        )


def downgrade() -> None:
    # Best-effort reversal. Recovery rows already in `half_open` cannot
    # be returned to a pre-half_open world cleanly; we leave their data
    # untouched and only drop the new structural elements. Rolling back
    # in a populated environment is therefore inherently lossy and
    # operator-attended.
    bind = op.get_bind()

    if _constraint_exists(
        bind, "emergency_states", "ck_emergency_states_valid_state"
    ):
        op.drop_constraint(
            "ck_emergency_states_valid_state",
            "emergency_states",
            type_="check",
        )

    if _column_exists(bind, "emergency_states", "half_open_entered_at"):
        op.drop_column("emergency_states", "half_open_entered_at")
