"""Conflict and audit care: schedule repair check-ins, drop the permanent "AI analysis pending" text.

Revision ID: r6c1e8a4f2d7
Revises: q2a7c5e9d1b3
Create Date: 2026-10-31 21:00:02.000000

Active repair agreements with no check-in dates get 30/60/90 days after their creation, or after
the migration date when the first of those is already past (so old repairs do not all turn up
overdue at once). Legacy conflict statuses become the API's stages (LEGACY_CONFLICT_STAGES).
Draft audits whose findings are the old placeholder "Audit requested. AI analysis pending." lose that text (a draft with no findings reads as
"not written yet"). Legacy free-text conflict parties become member ids only when exactly one
member of the case's ecosystem has that display name (case and surrounding space ignored); the
rest stay as non-authorizing labels (parties = {"member_ids": [...], "labels": [...]}), because
display names are user-editable and must never grant access. An index on conflict_cases.reporter_id serves "my reports". No new columns,
so it does not depend on any other lane's schema.

Downgrade is a no-op for the data (dates, statuses, cleared text and converted parties are not restored) and
drops the index. Rationale: alembic/AGENTS.md "r6c1e8a4f2d7".
"""

from __future__ import annotations

import datetime as dt
import uuid

from alembic import op
import sqlalchemy as sa

revision = "r6c1e8a4f2d7"
down_revision = "q2a7c5e9d1b3"
branch_labels = None
depends_on = None

REPORTER_INDEX = "ix_conflict_cases_reporter_id"
PLACEHOLDER_FINDINGS = "Audit requested. AI analysis pending."
CHECKIN_DAYS = (30, 60, 90)
# Statuses older writers stored -> the stage in api/conflicts.CONFLICT_MOVES: the legacy dashboard wrote
# open/in_progress/escalated/resolved, the demo seed in_mediation/escalated (both mid-process).
LEGACY_CONFLICT_STAGES = {"open": "reported", "in_mediation": "in_progress", "escalated": "in_progress"}

_repairs = sa.table(
    "repair_agreement_records",
    sa.column("id"), sa.column("status"), sa.column("created_at", sa.DateTime),
    sa.column("checkin_30_date", sa.Date), sa.column("checkin_60_date", sa.Date), sa.column("checkin_90_date", sa.Date),
)
_cases = sa.table(
    "conflict_cases", sa.column("id"), sa.column("ecosystem_id"), sa.column("parties", sa.JSON),
    sa.column("status", sa.String),
)
_members = sa.table("members", sa.column("id"), sa.column("ecosystem_id"), sa.column("display_name"))
_audits = sa.table("governance_health_audits", sa.column("findings"), sa.column("status"))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "repair_agreement_records" in tables:
        unscheduled = bind.execute(sa.select(_repairs.c.id, _repairs.c.created_at).where(
            _repairs.c.status == "active",
            _repairs.c.checkin_30_date.is_(None),
            _repairs.c.checkin_60_date.is_(None),
            _repairs.c.checkin_90_date.is_(None),
        )).all()
        today = dt.datetime.now(dt.timezone.utc).date()
        for repair_id, created_at in unscheduled:
            start = created_at.date() if created_at else today
            if start + dt.timedelta(days=CHECKIN_DAYS[0]) < today:
                start = today  # its first check-in is already past: follow up from now instead
            bind.execute(_repairs.update().where(_repairs.c.id == repair_id).values(**{
                f"checkin_{days}_date": start + dt.timedelta(days=days) for days in CHECKIN_DAYS
            }))

    if "governance_health_audits" in tables:
        bind.execute(_audits.update().where(
            _audits.c.status == "draft", _audits.c.findings == PLACEHOLDER_FINDINGS,
        ).values(findings=None))

    if "conflict_cases" in tables:
        for legacy, stage in LEGACY_CONFLICT_STAGES.items():
            bind.execute(_cases.update().where(_cases.c.status == legacy).values(status=stage))

    if {"conflict_cases", "members"} <= tables:
        _convert_legacy_parties(bind)

    if "conflict_cases" in tables:
        existing = {index["name"] for index in inspector.get_indexes("conflict_cases")}
        if REPORTER_INDEX not in existing:
            op.create_index(REPORTER_INDEX, "conflict_cases", ["reporter_id"])


def _free_text_parties(parties) -> list[str] | None:
    """Names in a legacy parties blob (list items or dict values); None when already converted or empty."""
    if isinstance(parties, dict):
        if "member_ids" in parties:
            return None
        names = [value for value in parties.values() if isinstance(value, str)]
    elif isinstance(parties, list):
        names = [item for item in parties if isinstance(item, str)]
    else:
        return None
    return [name.strip() for name in names if name.strip()] or None


def _convert_legacy_parties(bind) -> None:
    """Match each legacy name to the one member of the case's ecosystem with that name; keep the rest as labels."""
    for case_id, ecosystem_id, parties in bind.execute(sa.select(_cases.c.id, _cases.c.ecosystem_id, _cases.c.parties)).all():
        names = _free_text_parties(parties)
        if names is None:
            continue
        member_ids: list[str] = []
        labels: list[str] = []
        unmatched: list[str] = []
        for name in names:
            matches = bind.execute(sa.select(_members.c.id, _members.c.display_name).where(
                _members.c.ecosystem_id == ecosystem_id,
                sa.func.lower(sa.func.trim(_members.c.display_name)) == name.lower(),
            )).all()
            matched_id = str(uuid.UUID(str(matches[0][0]))) if len(matches) == 1 else None  # dashed form, as the API stores it
            if matched_id and matched_id not in member_ids:
                member_ids.append(matched_id)
                labels.append(matches[0][1])
            else:
                unmatched.append(name)
        bind.execute(_cases.update().where(_cases.c.id == case_id).values(
            parties={"member_ids": member_ids, "labels": labels + unmatched},
        ))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "conflict_cases" in inspector.get_table_names():
        if REPORTER_INDEX in {index["name"] for index in inspector.get_indexes("conflict_cases")}:
            op.drop_index(REPORTER_INDEX, table_name="conflict_cases")
