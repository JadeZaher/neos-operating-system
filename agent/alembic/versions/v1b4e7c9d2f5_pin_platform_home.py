"""Pin the platform home ecosystem by id (G-Authority, owner decision 2026-11-01).

Revision ID: v1b4e7c9d2f5
Revises: u7d2f4b8a3c6
Create Date: 2026-11-01 17:30:00.000000

At request time the platform home is an id only (PLATFORM_HOME_ECOSYSTEM_ID, else the app_settings row
"platform_home_ecosystem_id" = {"ecosystem_id": "<uuid>"}), never a name: names are editable, so a rename
must not move platform admin. This revision writes that row ONCE, resolving the home the way sign-up
placement does today: SIGNUP_DEFAULT_ECOSYSTEM_SLUG from the environment (an ecosystem id or a name slug),
else the slug "omnione"; of the matching ecosystems the OLDEST (created_at, then founded_date with nulls
last, then id). Nothing matches: it inserts nothing (fail closed), and nobody is a platform admin until
PLATFORM_HOME_ECOSYSTEM_ID is set. A row already present is left as it is (idempotent).

A fresh database built by create_all + stamp (alembic/env.py "fresh databases") skips this revision; the
server pins the OmniOne it founds on an empty database itself (main.init_db). Downgrade deletes the row,
whatever it holds; see alembic/AGENTS.md "v1b4e7c9d2f5".
"""

from __future__ import annotations

import os
import re
import uuid

from alembic import op
import sqlalchemy as sa

revision = "v1b4e7c9d2f5"
down_revision = "u7d2f4b8a3c6"
branch_labels = None
depends_on = None

SETTING_KEY = "platform_home_ecosystem_id"
DEFAULT_SLUG = "omnione"

_app_settings = sa.table(
    "app_settings",
    sa.column("id", sa.Uuid()),
    sa.column("key", sa.String()),
    sa.column("value", sa.JSON()),
)
_ecosystems = sa.table(
    "ecosystems",
    sa.column("id"), sa.column("name"), sa.column("created_at"), sa.column("founded_date"),
)


def _slug(value: str) -> str:
    """Lowercase, hyphen-joined form of a name (api/auth._slug as of this revision)."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _as_uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None


def _oldest_first(row) -> tuple:
    """Sign-up's order: created_at, then founded_date (nulls last), then id."""
    return (row.created_at, row.founded_date is None, str(row.founded_date or ""), _as_uuid(row.id).int)


def resolve_home(bind, configured: str) -> uuid.UUID | None:
    """The oldest ecosystem whose id equals `configured` or whose name slugs like it (default "omnione")."""
    wanted = configured.strip() or DEFAULT_SLUG
    wanted_id, wanted_slug = _as_uuid(wanted), _slug(wanted)
    rows = bind.execute(sa.select(_ecosystems.c.id, _ecosystems.c.name, _ecosystems.c.created_at,
                                  _ecosystems.c.founded_date)).all()
    matches = [row for row in rows if _as_uuid(row.id) == wanted_id or _slug(row.name or "") == wanted_slug]
    return _as_uuid(min(matches, key=_oldest_first).id) if matches else None


def upgrade() -> None:
    bind = op.get_bind()
    tables = sa.inspect(bind).get_table_names()
    if "app_settings" not in tables or "ecosystems" not in tables:
        return
    if bind.execute(sa.select(_app_settings.c.key).where(_app_settings.c.key == SETTING_KEY)).first() is not None:
        return
    home_id = resolve_home(bind, os.environ.get("SIGNUP_DEFAULT_ECOSYSTEM_SLUG", ""))
    if home_id is None:
        return  # fail closed: no pin, so nobody is a platform admin until PLATFORM_HOME_ECOSYSTEM_ID is set
    bind.execute(sa.insert(_app_settings).values(id=uuid.uuid4(), key=SETTING_KEY, value={"ecosystem_id": str(home_id)}))


def downgrade() -> None:
    bind = op.get_bind()
    if "app_settings" in sa.inspect(bind).get_table_names():
        bind.execute(sa.delete(_app_settings).where(_app_settings.c.key == SETTING_KEY))
