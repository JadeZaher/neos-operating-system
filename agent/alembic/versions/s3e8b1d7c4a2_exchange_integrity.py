"""Shares, needs and collaborations integrity (G-Exchange); see alembic/AGENTS.md "s3e8b1d7c4a2".

Revision ID: s3e8b1d7c4a2
Revises: r6c1e8a4f2d7
Create Date: 2026-11-01 15:00:00.000000

Schema (each column only when missing, so create_all databases are safe; SQLite gets the bare column, PostgreSQL
also the foreign key, ON DELETE SET NULL):
- shares_needs: status_reason, status_changed_by_member_id, status_changed_at, fulfilled_by_member_id (the
  responder a fulfilled post names), hidden_at, hidden_by_member_id, hidden_reason (moderation is a restorable hide).
- collaborations: proposed_by_member_id, ended_by_member_id, end_reason, ended_at, and the last recorded review:
  reviewed_by_member_id, review_note, reviewed_at (FX-Exchange).

Data (both kinds of database, portable statements over typed sa.table columns):
- categories: blank -> NULL; case/space variants of the vocabulary -> the vocabulary; "skill" -> "skills",
  "resource" -> "resources" (DomainDetail used to send the singulars). Other free text is left as it is.
- visibility "private" (retired) -> "domain", its narrowest successor.
- active posts with no author (legacy) -> withdrawn, "No author on record (legacy post)": nobody can answer them.
- active posts whose author has exited -> withdrawn, "author left" (as api/exit.py now does at exit).
- active collaborations without a review date -> started_date (else created date) + 365 days; when that is already
  past, the migration date + 30 days (as u7d2f4b8a3c6 does for agreements), so year-old collaborations are not all
  due the day this deploys.

The downgrade drops the columns; the data rewrites are not restored (the old values are not kept).
"""

from __future__ import annotations

import datetime as dt

from alembic import op
import sqlalchemy as sa

revision = "s3e8b1d7c4a2"
down_revision = "r6c1e8a4f2d7"
branch_labels = None
depends_on = None

MEMBER_COLUMNS = (  # (table, column): nullable member id, SET NULL on member delete
    ("shares_needs", "status_changed_by_member_id"),
    ("shares_needs", "fulfilled_by_member_id"),
    ("shares_needs", "hidden_by_member_id"),
    ("collaborations", "proposed_by_member_id"),
    ("collaborations", "ended_by_member_id"),
    ("collaborations", "reviewed_by_member_id"),
)
TEXT_COLUMNS = (("shares_needs", "status_reason"), ("shares_needs", "hidden_reason"), ("collaborations", "end_reason"),
                ("collaborations", "review_note"))
TIME_COLUMNS = (("shares_needs", "status_changed_at"), ("shares_needs", "hidden_at"), ("collaborations", "ended_at"),
                ("collaborations", "reviewed_at"))

CATEGORIES = ("technology", "resources", "skills", "knowledge", "infrastructure", "funding", "space", "labor", "other")
CATEGORY_ALIASES = {"skill": "skills", "resource": "resources"}
NO_AUTHOR = "No author on record (legacy post)"
AUTHOR_LEFT = "author left"
REVIEW_AFTER_DAYS = 365
FIRST_REVIEW_GRACE_DAYS = 30  # a backfilled review date already past moves to the migration date + this

shares_needs = sa.table(
    "shares_needs", sa.column("id", sa.Uuid()), sa.column("author_member_id", sa.Uuid()),
    sa.column("category", sa.String()), sa.column("visibility", sa.String()), sa.column("status", sa.String()),
    sa.column("status_reason", sa.Text()), sa.column("status_changed_by_member_id", sa.Uuid()),
    sa.column("status_changed_at", sa.DateTime()),
)
members = sa.table("members", sa.column("id", sa.Uuid()), sa.column("current_status", sa.String()))
collaborations = sa.table(
    "collaborations", sa.column("id", sa.Uuid()), sa.column("status", sa.String()),
    sa.column("started_date", sa.Date()), sa.column("review_date", sa.Date()), sa.column("created_at", sa.DateTime()),
)


def _columns(bind, table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def _add_columns(bind, tables: set[str]) -> None:
    postgres = bind.dialect.name == "postgresql"
    for table, column in MEMBER_COLUMNS:
        if table in tables and column not in _columns(bind, table):
            op.add_column(table, sa.Column(column, sa.Uuid(), nullable=True))
            if postgres:  # SQLite cannot add a constraint to an existing table; the column alone is enough there.
                op.create_foreign_key(f"fk_{table}_{column}", table, "members", [column], ["id"], ondelete="SET NULL")
    for group, column_type in ((TEXT_COLUMNS, sa.Text()), (TIME_COLUMNS, sa.DateTime())):
        for table, column in group:
            if table in tables and column not in _columns(bind, table):
                op.add_column(table, sa.Column(column, column_type, nullable=True))


def _fix_posts(bind, now: dt.datetime) -> None:
    category = sa.func.lower(sa.func.trim(shares_needs.c.category))
    bind.execute(sa.update(shares_needs).where(
        shares_needs.c.category.isnot(None), sa.func.trim(shares_needs.c.category) == "").values(category=None))
    bind.execute(sa.update(shares_needs).where(
        category.in_(CATEGORIES), shares_needs.c.category != category).values(category=category))
    for alias, canonical in CATEGORY_ALIASES.items():
        bind.execute(sa.update(shares_needs).where(category == alias).values(category=canonical))
    bind.execute(sa.update(shares_needs).where(shares_needs.c.visibility == "private").values(visibility="domain"))
    bind.execute(sa.update(shares_needs).where(
        shares_needs.c.status == "active", shares_needs.c.author_member_id.is_(None),
    ).values(status="withdrawn", status_reason=NO_AUTHOR, status_changed_at=now))
    exited = sa.select(members.c.id).where(members.c.current_status == "exited")
    bind.execute(sa.update(shares_needs).where(
        shares_needs.c.status == "active", shares_needs.c.author_member_id.in_(exited),
    ).values(status="withdrawn", status_reason=AUTHOR_LEFT, status_changed_at=now,
             status_changed_by_member_id=shares_needs.c.author_member_id))


def _date_review(bind, today: dt.date) -> None:
    rows = bind.execute(sa.select(collaborations.c.id, collaborations.c.started_date, collaborations.c.created_at).where(
        collaborations.c.status == "active", collaborations.c.review_date.is_(None))).all()
    for row in rows:
        start = row.started_date or (row.created_at.date() if row.created_at else today)
        due = start + dt.timedelta(days=REVIEW_AFTER_DAYS)
        if due <= today:
            due = today + dt.timedelta(days=FIRST_REVIEW_GRACE_DAYS)
        bind.execute(sa.update(collaborations).where(collaborations.c.id == row.id).values(review_date=due))


def upgrade(*, today: dt.date | None = None) -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    _add_columns(bind, tables)
    now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    if {"shares_needs", "members"} <= tables:
        _fix_posts(bind, now)
    if "collaborations" in tables:
        _date_review(bind, today or now.date())


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    for table, column in TEXT_COLUMNS + TIME_COLUMNS:
        if table in tables and column in _columns(bind, table):
            op.drop_column(table, column)
    for table, column in reversed(MEMBER_COLUMNS):
        if table not in tables or column not in _columns(bind, table):
            continue
        for foreign_key in sa.inspect(bind).get_foreign_keys(table):
            if foreign_key.get("constrained_columns") == [column] and foreign_key.get("name"):
                op.drop_constraint(foreign_key["name"], table, type_="foreignkey")
        op.drop_column(table, column)
