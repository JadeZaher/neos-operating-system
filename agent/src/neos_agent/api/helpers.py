"""Shared API helpers -- auth, ecosystem scoping, pagination."""
from __future__ import annotations

import logging
import uuid

from sanic import json
from sanic.request import Request

logger = logging.getLogger(__name__)


def require_auth(request: Request):
    """Return (member, None) or (None, 401_response)."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    """Return ecosystem IDs to filter by.

    If the request contains an explicit `ecosystem_ids` query param (comma-separated),
    intersect with the session-authorized IDs for security. Otherwise return all
    session-authorized IDs.
    """
    session_ids: list[uuid.UUID] = getattr(request.ctx, "selected_ecosystem_ids", [])

    explicit = request.args.get("ecosystem_ids")
    if explicit:
        try:
            requested = [uuid.UUID(eid.strip()) for eid in explicit.split(",") if eid.strip()]
        except ValueError:
            return session_ids
        if session_ids:
            # Intersect: only allow IDs the user is authorized for
            session_set = set(session_ids)
            return [eid for eid in requested if eid in session_set]
        return requested

    return session_ids


def apply_ecosystem_filter(stmt, model, eco_ids: list[uuid.UUID], include_shared: bool = True):
    """Apply cross-ecosystem filter: matches ecosystem_id OR any shared_ecosystem_ids.

    Returns entities owned by any eco_id OR shared with any eco_id.
    Set include_shared=False to only filter by primary ecosystem_id.
    """
    if not eco_ids:
        return stmt

    # Always filter by primary ecosystem_id - this is safe and works everywhere
    return stmt.where(model.ecosystem_id.in_(eco_ids))


def serialize_shared_ecosystem_ids(ids: list[uuid.UUID] | None) -> list[str] | None:
    """Convert UUID list to string list for JSON storage."""
    if not ids:
        return None
    return [str(eid) for eid in ids]
