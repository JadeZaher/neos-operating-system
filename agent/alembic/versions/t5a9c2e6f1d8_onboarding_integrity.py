"""Onboarding integrity (reserved skeleton; the G-Onboard lane fills in upgrade/downgrade).

Revision ID: t5a9c2e6f1d8
Revises: s3e8b1d7c4a2
Create Date: 2026-11-01 15:00:00.000000

Reserved by the coordinator so parallel lanes keep a single head: alembic/AGENTS.md
"Parallel work: reserve revisions in a chain". Left empty, it is a no-op.
"""

from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision = "t5a9c2e6f1d8"
down_revision = "s3e8b1d7c4a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
