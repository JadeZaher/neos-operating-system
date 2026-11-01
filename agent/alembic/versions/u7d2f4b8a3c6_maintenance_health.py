"""Maintenance and health: the audit self-assessment flag; review and sunset dates agreements lack.

Revision ID: u7d2f4b8a3c6
Revises: t5a9c2e6f1d8
Create Date: 2026-11-01 15:00:00.000000

Schema: `governance_health_audits.self_assessment` (boolean, default false), added only when missing
(create_all databases already have it). It marks an audit a steward recorded of their own ecosystem
because no member who is not a steward could (owner decision 2026-11-01, policy.can_record_audit).

Data (both kinds of database, Python over sa.table columns, only NULLs are filled, so a rerun is safe):
- Agreements in force (active, under_review) with no review date get one: the per-type interval
  (REVIEW_INTERVAL_MONTHS, frozen here) from the date they came into force (ratification, else creation).
  When that date is already past, the first review is due 30 days after the migration instead, so years of
  unscheduled agreements do not all turn up overdue on the first page load (the r6c1e8a4f2d7 rule).
- Agreements in sunset with no sunset date get one: 60 days (the framework's notice) after the sunset
  ceremony, else after the row's last update, else after the migration date. Archiving is offered after it.
The four study agreements stuck under review need nothing: they can now be finished with findings.

Downgrade drops the column; the filled dates stay (they are not distinguishable from set ones).
Rationale: alembic/AGENTS.md "u7d2f4b8a3c6".
"""

from __future__ import annotations

import calendar
import datetime as dt

from alembic import op
import sqlalchemy as sa

revision = "u7d2f4b8a3c6"
down_revision = "t5a9c2e6f1d8"
branch_labels = None
depends_on = None

# Frozen copy of api/agreement_vocabulary.REVIEW_INTERVAL_MONTHS at this revision.
REVIEW_INTERVAL_MONTHS = {"space": 12, "access": 6, "organizational": 24, "uaf": 12, "culture_code": 12}
DEFAULT_REVIEW_INTERVAL_MONTHS = 12
FIRST_REVIEW_GRACE_DAYS = 30
SUNSET_NOTICE_DAYS = 60

_agreements = sa.table(
    "agreements",
    sa.column("id"), sa.column("type", sa.String), sa.column("status", sa.String),
    sa.column("review_date", sa.Date), sa.column("sunset_date", sa.Date),
    sa.column("ratification_date", sa.Date), sa.column("created_date", sa.Date),
    sa.column("created_at", sa.DateTime), sa.column("updated_at", sa.DateTime),
)
_ceremonies = sa.table(
    "agreement_ceremonies", sa.column("agreement_id"), sa.column("stage", sa.String), sa.column("completed_at", sa.DateTime),
)


def _add_months(day: dt.date, months: int) -> dt.date:
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


def _as_date(value) -> dt.date | None:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:  # SQLite may hand back text
        return dt.datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def upgrade(*, today: dt.date | None = None) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    today = today or dt.datetime.now(dt.UTC).date()

    if "governance_health_audits" in tables:
        columns = {column["name"] for column in inspector.get_columns("governance_health_audits")}
        if "self_assessment" not in columns:
            op.add_column("governance_health_audits",
                          sa.Column("self_assessment", sa.Boolean(), nullable=False, server_default=sa.false()))

    if "agreements" not in tables:
        return

    unscheduled = bind.execute(sa.select(
        _agreements.c.id, _agreements.c.type, _agreements.c.ratification_date, _agreements.c.created_date,
        _agreements.c.created_at,
    ).where(_agreements.c.status.in_(("active", "under_review")), _agreements.c.review_date.is_(None))).all()
    for row in unscheduled:
        base = _as_date(row.ratification_date) or _as_date(row.created_date) or _as_date(row.created_at) or today
        due = _add_months(base, REVIEW_INTERVAL_MONTHS.get(row.type or "", DEFAULT_REVIEW_INTERVAL_MONTHS))
        if due <= today:
            due = today + dt.timedelta(days=FIRST_REVIEW_GRACE_DAYS)
        bind.execute(_agreements.update().where(_agreements.c.id == row.id).values(review_date=due))

    ending = bind.execute(sa.select(_agreements.c.id, _agreements.c.updated_at).where(
        _agreements.c.status == "sunset", _agreements.c.sunset_date.is_(None),
    )).all()
    has_ceremonies = "agreement_ceremonies" in tables
    for row in ending:
        started = None
        if has_ceremonies:
            started = _as_date(bind.execute(sa.select(sa.func.max(_ceremonies.c.completed_at)).where(
                _ceremonies.c.agreement_id == row.id, _ceremonies.c.stage == "sunset",
            )).scalar())
        start = started or _as_date(row.updated_at) or today
        bind.execute(_agreements.update().where(_agreements.c.id == row.id).values(
            sunset_date=start + dt.timedelta(days=SUNSET_NOTICE_DAYS)))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "governance_health_audits" not in inspector.get_table_names():
        return
    if "self_assessment" in {column["name"] for column in inspector.get_columns("governance_health_audits")}:
        with op.batch_alter_table("governance_health_audits") as batch:
            batch.drop_column("self_assessment")
