"""Emergency co-signing: pending/withdrawn states, declarer and co-signer rows, the requested timer.

Revision ID: q2a7c5e9d1b3
Revises: p8d4f1b6e3a9
Create Date: 2026-10-31 21:00:01.000000

Widens ck_emergency_states_valid_state to ('pending', 'open', 'half_open',
'closed', 'withdrawn'), adds five nullable columns, and adds the partial unique
index uq_emergency_states_one_live (one pending/open/half_open row per ecosystem),
first retiring any duplicate live rows (KEEP_ORDER). Inspect-before-alter, so it
is a no-op on a create_all schema built from the current models; SQLite rebuilds
the table through batch mode (it cannot alter a CHECK in place). Independent of
p8d4f1b6e3a9's columns. Rationale: api/AGENTS.md "Emergency and exit",
alembic/AGENTS.md "q2a7c5e9d1b3".
"""

from __future__ import annotations

import datetime as dt
import uuid
from collections import defaultdict

import sqlalchemy as sa
from alembic import op

revision = "q2a7c5e9d1b3"
down_revision = "p8d4f1b6e3a9"
branch_labels = None
depends_on = None

TABLE = "emergency_states"
STATE_CHECK = "ck_emergency_states_valid_state"
WIDE_STATES = "state IN ('pending', 'open', 'half_open', 'closed', 'withdrawn')"
NARROW_STATES = "state IN ('open', 'half_open', 'closed')"
NEW_COLUMNS = (
    ("declared_by_member_id", sa.Uuid),
    ("co_signer_member_id", sa.Uuid),
    ("co_signed_by", lambda: sa.String(255)),
    ("co_signed_at", sa.DateTime),
    ("authority_days", sa.Integer),
)
LIVE_INDEX = "uq_emergency_states_one_live"
LIVE_STATES = ("pending", "open", "half_open")
LIVE_WHERE = "state IN ('pending', 'open', 'half_open')"
# Which duplicate stays live: authority in effect, then Recovery, then a pending declaration; latest declared wins ties.
KEEP_ORDER = {"open": 0, "half_open": 1, "pending": 2}
RETIRED_STATE = {"open": "closed", "half_open": "closed", "pending": "withdrawn"}

_emergencies = sa.table(
    TABLE, sa.column("id"), sa.column("ecosystem_id"), sa.column("state"), sa.column("declared_at", sa.DateTime),
    sa.column("created_at", sa.DateTime), sa.column("closed_at", sa.DateTime), sa.column("actions_log", sa.JSON),
)


def _state_check_sql(bind) -> str | None:
    """The stored CHECK text for the state column, or None when the table has none (or the dialect cannot say)."""
    try:
        checks = sa.inspect(bind).get_check_constraints(TABLE)
    except NotImplementedError:
        return None
    for check in checks:
        if check.get("name") == STATE_CHECK or "half_open" in (check.get("sqltext") or ""):
            return check.get("sqltext") or ""
    return None


def _has_live_index(bind) -> bool:
    return LIVE_INDEX in {index["name"] for index in sa.inspect(bind).get_indexes(TABLE)}


def _retire_duplicate_live_rows(bind) -> None:
    """Leave one live row per ecosystem (KEEP_ORDER); the others close (or withdraw, if pending) with a log entry."""
    rows = bind.execute(sa.select(_emergencies).where(_emergencies.c.state.in_(LIVE_STATES))).all()
    by_ecosystem = defaultdict(list)
    for row in rows:
        by_ecosystem[str(row.ecosystem_id)].append(row)
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    oldest = dt.datetime.min
    for live in by_ecosystem.values():
        live.sort(key=lambda r: (r.declared_at or oldest, r.created_at or oldest, str(r.id)), reverse=True)
        live.sort(key=lambda r: KEEP_ORDER[r.state])  # stable: latest first within each state
        kept, *duplicates = live
        for row in duplicates:
            log = list(row.actions_log) if isinstance(row.actions_log, list) else []
            log.append({"action": "superseded", "timestamp": now.isoformat(), "note": (
                f"Closed by a system update: an ecosystem has one live emergency at a time, and {uuid.UUID(str(kept.id))} "
                "stays live."
            )})
            bind.execute(_emergencies.update().where(_emergencies.c.id == row.id).values(
                state=RETIRED_STATE[row.state], closed_at=now, actions_log=log,
            ))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(TABLE)}
    missing = [(name, factory) for name, factory in NEW_COLUMNS if name not in existing]
    check_sql = _state_check_sql(bind)
    widen = check_sql is None or "pending" not in check_sql or "withdrawn" not in check_sql
    if missing or widen:
        with op.batch_alter_table(TABLE) as batch:
            for name, factory in missing:
                batch.add_column(sa.Column(name, factory(), nullable=True))
            if widen:
                if check_sql is not None:
                    batch.drop_constraint(STATE_CHECK, type_="check")
                batch.create_check_constraint(STATE_CHECK, WIDE_STATES)
    if not _has_live_index(bind):
        _retire_duplicate_live_rows(bind)
        op.create_index(LIVE_INDEX, TABLE, ["ecosystem_id"], unique=True,
                        postgresql_where=sa.text(LIVE_WHERE), sqlite_where=sa.text(LIVE_WHERE))


def downgrade() -> None:
    """Lossy: pending declarations become closed and withdrawn ones closed, so the narrow CHECK holds; drops the index."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return
    if _has_live_index(bind):
        op.drop_index(LIVE_INDEX, table_name=TABLE)
    op.execute(sa.text(f"UPDATE {TABLE} SET state = 'closed' WHERE state IN ('pending', 'withdrawn')"))
    existing = {column["name"] for column in inspector.get_columns(TABLE)}
    with op.batch_alter_table(TABLE) as batch:
        if _state_check_sql(bind) is not None:
            batch.drop_constraint(STATE_CHECK, type_="check")
        batch.create_check_constraint(STATE_CHECK, NARROW_STATES)
        for name, _ in reversed(NEW_COLUMNS):
            if name in existing:
                batch.drop_column(name)
