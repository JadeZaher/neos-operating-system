"""Shared API helpers -- auth, ecosystem scoping, pagination."""
from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass

from sanic import json
from sanic.request import Request
from sqlalchemy import or_, cast, String, Text, select, text, literal

from neos_agent.api.errors import ApiError
from neos_agent.api.policy import PROFILE_ADMINS, is_platform_admin
from neos_agent.api.policy import ROLE_RANK  # re-exported; policy.py is the single definition

logger = logging.getLogger(__name__)


def require_auth(request: Request):
    """Return (member, None) or (None, 401_response)."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


# Platform-admin gate: only for platform-wide resources; see api/AGENTS.md "Platform admin (G-Authority)".
def require_admin(request: Request):
    """(the caller's home-ecosystem admin row, None) when request.ctx.platform_admin, else (None, 401/403 response)."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    if not getattr(request.ctx, "platform_admin", False):
        return None, json({"error": "Admin access required"}, status=403)
    return getattr(request.ctx, "platform_admin_member", None) or member, None


# G-Authority

# The app_settings key that pins the platform home by id (written by migration v1b4e7c9d2f5; never via the API).
PLATFORM_HOME_SETTING_KEY = "platform_home_ecosystem_id"


def _as_uuid(value) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value).strip()) if value not in (None, "") else None
    except ValueError:
        return None


async def home_ecosystem_id(session, settings) -> uuid.UUID | None:
    """The pinned platform home: PLATFORM_HOME_ECOSYSTEM_ID, else the app_settings pin; an existing ecosystem's id or None. Never a name."""
    from neos_agent.db.models import AppSetting, Ecosystem

    configured = getattr(settings, "PLATFORM_HOME_ECOSYSTEM_ID", "")
    home_id = _as_uuid(configured) if isinstance(configured, str) else None
    if isinstance(configured, str) and configured.strip() and home_id is None:
        logger.warning("PLATFORM_HOME_ECOSYSTEM_ID=%r is not a UUID; using the pinned home", configured)
    if home_id is None:
        pinned = await session.scalar(select(AppSetting.value).where(AppSetting.key == PLATFORM_HOME_SETTING_KEY))
        home_id = _as_uuid(pinned.get("ecosystem_id")) if isinstance(pinned, dict) else None
    if home_id is None or await session.scalar(select(Ecosystem.id).where(Ecosystem.id == home_id)) is None:
        return None  # fail closed: nobody is a platform admin
    return home_id


async def platform_admin_row(session, settings, user_id: uuid.UUID):
    """The user's row that makes them a platform admin (policy.is_platform_admin), else None."""
    from neos_agent.db.models import Member

    candidates = (await session.scalars(select(Member).where(
        Member.user_id == user_id,
        Member.profile.in_(PROFILE_ADMINS),
        Member.current_status == "active",
    ))).all()
    if not candidates:
        return None  # most users hold no admin profile anywhere, so the home is never looked up
    home_id = await home_ecosystem_id(session, settings)
    return next((row for row in candidates if is_platform_admin(row, home_id)), None)


async def require_ecosystem_role(request: Request, ecosystem_id: uuid.UUID, min_role: str):
    """Return (member, None) if the caller's Member row in `ecosystem_id` meets
    `min_role`, or (None, 401/403_response).

    Re-queries Member by (ctx.user.id, ecosystem_id) — request.ctx.member is an
    arbitrary single row and must not be trusted for per-ecosystem role checks.
    """
    user = getattr(request.ctx, "user", None)
    if user is None:
        return None, json({"error": "Authentication required"}, status=401)

    from neos_agent.db.models import Member

    async with request.app.ctx.db() as session:
        caller = await session.scalar(
            select(Member).where(
                Member.user_id == user.id,
                Member.ecosystem_id == ecosystem_id,
            )
        )

    if caller is None or ROLE_RANK.get(caller.role, 0) < ROLE_RANK[min_role]:
        return None, json(
            {"error": f"Ecosystem role '{min_role}' or higher required"},
            status=403,
        )
    return caller, None


def get_authorized_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    """Return ALL authorized ecosystem IDs for the current user.

    Use this for detail/single-resource endpoints where the user should be able
    to access any resource they're authorized for, regardless of which ecosystems
    are currently selected in the UI.
    """
    return getattr(request.ctx, "authorized_ecosystem_ids", [])


def get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    """Return ecosystem IDs to filter by.

    If the request contains an explicit `ecosystem_ids` query param (comma-separated),
    intersect with ALL authorized IDs (not just cookie-selected) for security.
    Otherwise return the cookie-selected IDs as the default scope.
    """
    session_ids: list[uuid.UUID] = getattr(request.ctx, "selected_ecosystem_ids", [])
    authorized_ids: list[uuid.UUID] = getattr(request.ctx, "authorized_ecosystem_ids", [])

    explicit = request.args.get("ecosystem_ids")
    if explicit:
        try:
            requested = [uuid.UUID(eid.strip()) for eid in explicit.split(",") if eid.strip()]
        except ValueError:
            return session_ids
        # Intersect with ALL authorized ecosystems (not just cookie-selected)
        auth_set = set(authorized_ids)
        return [eid for eid in requested if eid in auth_set]

    return session_ids


def apply_ecosystem_filter(stmt, model, eco_ids: list[uuid.UUID], include_shared: bool = True):
    """Apply cross-ecosystem filter: matches ecosystem_id OR any shared_ecosystem_ids.

    Returns entities owned by any eco_id OR shared with any eco_id.
    Set include_shared=False to only filter by primary ecosystem_id.
    """
    if not eco_ids:
        return stmt

    primary_match = model.ecosystem_id.in_(eco_ids)

    if not include_shared or not hasattr(model, "shared_ecosystem_ids"):
        return stmt.where(primary_match)

    # Also match if any of eco_ids appear in the shared_ecosystem_ids JSON array.
    # shared_ecosystem_ids is stored as JSON (not JSONB), so we cast to text
    # and check if any UUID string appears in it.
    shared_text = cast(model.shared_ecosystem_ids, Text)
    shared_conditions = [shared_text.contains(str(eid)) for eid in eco_ids]

    return stmt.where(or_(primary_match, *shared_conditions))


def apply_ecosystem_name_filter(stmt, model, request: Request):
    """Filter by ecosystem name (ILIKE contains match).

    Joins the Ecosystem table and filters by name. Works with any model
    that has an ecosystem_id FK and an 'ecosystem' relationship.
    """
    from neos_agent.db.models import Ecosystem

    eco_name = request.args.get("ecosystem_name")
    if not eco_name:
        return stmt

    pattern = f"%{_escape_like(eco_name)}%"
    return stmt.where(model.ecosystem_id.in_(
        select(Ecosystem.id).where(Ecosystem.name.ilike(pattern))
    ))


def build_search_filter(model, search: str, *extra_columns):
    """Build an OR filter across model columns + ecosystem name.

    Usage: stmt = stmt.where(build_search_filter(Agreement, search, Agreement.title, Agreement.agreement_id))
    Automatically includes ecosystem name matching via a subquery.
    """
    from neos_agent.db.models import Ecosystem

    pattern = f"%{_escape_like(search)}%"
    conditions = [col.ilike(pattern) for col in extra_columns]
    # Also match if the search term matches the ecosystem name
    conditions.append(model.ecosystem_id.in_(
        select(Ecosystem.id).where(Ecosystem.name.ilike(pattern))
    ))
    return or_(*conditions)


def _escape_like(value: str) -> str:
    """Escape SQL LIKE/ILIKE wildcard characters."""
    return re.sub(r"([%_\\])", r"\\\1", value)


def serialize_shared_ecosystem_ids(ids: list[uuid.UUID] | None) -> list[str] | None:
    """Convert UUID list to string list for JSON storage."""
    if not ids:
        return None
    return [str(eid) for eid in ids]


# Value object: a validated page request.
@dataclass(frozen=True)
class Page:
    """A 1-based page number and page size; `offset` is derived so it cannot drift."""

    page: int
    per_page: int

    @property
    def offset(self) -> int:
        """Rows to skip before this page."""
        return (self.page - 1) * self.per_page


_SQL_BIGINT_MAX = 2**63 - 1


# Parser: reject non-integers (400), clamp integers into range.
def parse_pagination(request: Request, default: int = 25, cap: int = 100) -> Page:
    """?page and ?per_page as a Page; see api/AGENTS.md "Handler contracts"."""
    page = max(1, _integer_query_arg(request, "page", 1))
    per_page = min(cap, max(1, _integer_query_arg(request, "per_page", default)))
    if (page - 1) * per_page > _SQL_BIGINT_MAX:
        raise ApiError(400, "Query parameter 'page' is out of range")
    return Page(page=page, per_page=per_page)


def _integer_query_arg(request: Request, name: str, default: int) -> int:
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        raise ApiError(400, f"Query parameter '{name}' must be a whole number") from None
