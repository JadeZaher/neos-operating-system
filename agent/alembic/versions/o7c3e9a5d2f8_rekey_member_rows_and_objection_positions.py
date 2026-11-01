"""Re-key orientation progress and ethos access onto each ecosystem's member row; store 'objection' as 'object'.

Revision ID: o7c3e9a5d2f8
Revises: n6a1d4f8b2c5
Create Date: 2026-10-31 18:00:00.000000

Rows of user_journey_progress and ethos_user_access were written for the
caller's DEFAULT member row, which can belong to another ecosystem than the
row's own ecosystem_id; the handlers now key them on the caller's row in that
ecosystem (guards.caller_in). Each such row moves to the same user's member row
in the row's ecosystem. A row whose user holds no member row there is left
untouched. When the target row already has rows, the group (every row of that
user for that ecosystem) keeps only its most advanced row, on the target row;
the rest of the group is deleted. Ranking rule: alembic/AGENTS.md "Data
revisions". A self-granted access row (granted_by = its old member) stays
self-granted.

consent_participants.position 'objection' (any case, surrounding spaces)
becomes 'object', the value the consent gate blocks on.

Downgrade is a no-op: re-keyed rows, dropped duplicates and normalized
positions are not restored (the old keys were the defect).
"""

from __future__ import annotations

import json
from collections import defaultdict

from alembic import op
import sqlalchemy as sa


revision = "o7c3e9a5d2f8"
down_revision = "n6a1d4f8b2c5"
branch_labels = None
depends_on = None


PROGRESS_STATUS_RANK = {"complete": 3, "in_progress": 2, "opted_out": 1}
ACCESS_ROLE_RANK = {"steward": 3, "member": 2, "observer": 1}

# Portable (PostgreSQL + SQLite).
_NORMALIZE_OBJECTIONS_SQL = """
UPDATE consent_participants
SET position = 'object'
WHERE lower(trim(position)) = 'objection'
"""

_members = sa.table("members", sa.column("id"), sa.column("user_id"), sa.column("ecosystem_id"))
_progress = sa.table(
    "user_journey_progress",
    sa.column("id"), sa.column("member_id"), sa.column("ecosystem_id"), sa.column("status"),
    sa.column("completed_steps", sa.JSON), sa.column("current_step"), sa.column("updated_at"),
)
_access = sa.table(
    "ethos_user_access",
    sa.column("id"), sa.column("member_id"), sa.column("ecosystem_id"), sa.column("role_in_ethos"),
    sa.column("access_level"), sa.column("granted_at"), sa.column("granted_by"),
)


def _completed_step_count(value) -> int:
    """Length of the completed_steps JSON list, whatever form the driver returns."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return 0
    return len(value) if isinstance(value, list) else 0


def _word_rank(ranks: dict[str, int], value: str | None) -> int:
    return ranks.get((value or "").strip().lower(), 0)


def _progress_rank(row) -> tuple:
    """Most advanced first: status, completed steps, current step, latest update, already on the target row."""
    return (
        _word_rank(PROGRESS_STATUS_RANK, row.status),
        _completed_step_count(row.completed_steps),
        row.current_step or 0,
        (row.updated_at is not None, row.updated_at),
        row.member_id == row.target_member_id,
    )


def _access_rank(row) -> tuple:
    """Strongest grant first: role, access level, already on the target row (ties keep the earliest grant)."""
    return (
        _word_rank(ACCESS_ROLE_RANK, row.role_in_ethos),
        _word_rank(ACCESS_ROLE_RANK, row.access_level),
        row.member_id == row.target_member_id,
    )


def _earliest_grant_first(row) -> tuple:
    return (row.granted_at is None, row.granted_at, row.id)


def _rows_with_target(bind, table) -> list:
    """Every row whose owner's user also holds a member row in the row's ecosystem, with that row's id."""
    owner = _members.alias("owner")
    target = _members.alias("target")
    return bind.execute(
        sa.select(*table.c, target.c.id.label("target_member_id")).select_from(
            table.join(owner, owner.c.id == table.c.member_id).join(
                target,
                sa.and_(target.c.user_id == owner.c.user_id, target.c.ecosystem_id == table.c.ecosystem_id),
            )
        )
    ).all()


def _rekey(bind, table, rank, *, order=None, self_granted: bool = False) -> None:
    """Keep each mis-keyed group's best row on the target member row; delete the rest of the group."""
    groups = defaultdict(list)
    for row in _rows_with_target(bind, table):
        groups[row.target_member_id].append(row)
    for target_member_id, group in groups.items():
        if all(row.member_id == target_member_id for row in group):
            continue  # already keyed on this ecosystem's row
        ordered = sorted(group, key=order) if order else group
        winner = max(ordered, key=rank)  # max keeps the first of equals, so `order` breaks ties
        losers = [row.id for row in group if row.id != winner.id]
        if losers:
            bind.execute(sa.delete(table).where(table.c.id.in_(losers)))
        if winner.member_id != target_member_id:
            values = {"member_id": target_member_id}
            if self_granted and winner.granted_by == winner.member_id:
                values["granted_by"] = target_member_id
            bind.execute(sa.update(table).where(table.c.id == winner.id).values(**values))


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "user_journey_progress" in tables:
        _rekey(bind, _progress, _progress_rank, order=lambda row: row.id)
    if "ethos_user_access" in tables:
        _rekey(bind, _access, _access_rank, order=_earliest_grant_first, self_granted=True)
    if "consent_participants" in tables:
        op.execute(_NORMALIZE_OBJECTIONS_SQL)


def downgrade() -> None:
    pass  # data-only revision; see the docstring
