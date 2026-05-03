"""Shared API helpers -- auth, ecosystem scoping, pagination."""
from __future__ import annotations

import uuid

from sanic import json
from sanic.request import Request


def require_auth(request: Request):
    """Return (member, None) or (None, 401_response)."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    """Return the middleware-authorized ecosystem IDs from request context."""
    return getattr(request.ctx, "selected_ecosystem_ids", [])
