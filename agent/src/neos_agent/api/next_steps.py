"""JSON API for "what is waiting for me" and "what happens next here"; see api/AGENTS.md "Next steps (G-Next)".

Blueprint: next_steps_api_bp (no prefix: /api/v1/me/next-steps and /api/v1/explain/<kind>/<id>).
Both read services/next_steps.py, the same source as the assistant's what_needs_me and explain_status.
"""

from __future__ import annotations

import uuid

from sanic import Blueprint, json
from sanic.request import Request

from neos_agent.api.guards import authenticated, caller_user_id
from neos_agent.api.helpers import get_authorized_ecosystem_ids
from neos_agent.services.next_steps import explain, waiting_for

next_steps_api_bp = Blueprint("next_steps_api")


@next_steps_api_bp.get("/api/v1/me/next-steps")
@authenticated
async def my_next_steps(request: Request):
    """GET /api/v1/me/next-steps -- the caller's items in every ecosystem they are active in (the queue and the bell)."""
    async with request.app.ctx.db() as session:
        items = await waiting_for(session, caller_user_id(request), get_authorized_ecosystem_ids(request))
    return json({"items": items, "count": len(items)})


@next_steps_api_bp.get("/api/v1/explain/<kind:str>/<record_id:uuid>")
@authenticated
async def explain_status(request: Request, kind: str, record_id: uuid.UUID):
    """GET /api/v1/explain/<kind>/<id> -- state, next step, who decides, by when; 404 where the detail page 404s."""
    async with request.app.ctx.db() as session:
        return json(await explain(session, request, kind, record_id))
