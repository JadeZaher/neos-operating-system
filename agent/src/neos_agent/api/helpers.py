"""Shared API helpers -- auth, ecosystem scoping, pagination."""
from __future__ import annotations

import logging
import re
import uuid

from sanic import json
from sanic.request import Request
from sqlalchemy import or_, cast, String, Text, select, text, literal

logger = logging.getLogger(__name__)


def require_auth(request: Request):
    """Return (member, None) or (None, 401_response)."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def require_admin(request: Request):
    """Return (member, None) if member has admin profile, or (None, 403_response)."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    if member.profile not in ("co_creator", "builder"):
        return None, json({"error": "Admin access required"}, status=403)
    return member, None


# Per-ecosystem role tiers, ordered by privilege.
ROLE_RANK = {"user": 0, "mod": 1, "admin": 2, "owner": 3}


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
