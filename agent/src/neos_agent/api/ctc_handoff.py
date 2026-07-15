"""JSON API blueprint for Charting-the-Course -> NEOS Den handoff readiness.

Blueprint: ctc_handoff_api_bp, url_prefix="/api/v1/admin/ctc-handoff"

Tracks whether a member has been marked ready to graduate from CTC into the
NEOS Den. Members without a row are absent from the list and default to
not-ready on the frontend.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.db.models import CtcHandoff, Member
from neos_agent.api.helpers import require_admin
from neos_agent.api.schemas.ctc_handoff import CtcHandoffItem, CtcHandoffSetRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

ctc_handoff_api_bp = Blueprint("ctc_handoff_api", url_prefix="/api/v1/admin/ctc-handoff")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_item(row: CtcHandoff) -> dict:
    return CtcHandoffItem(
        member_id=row.member_id,
        ready_for_neos_den=row.ready_for_neos_den,
        updated_at=row.updated_at,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@ctc_handoff_api_bp.get("/")
async def list_ctc_handoff(request: Request):
    """GET /api/v1/admin/ctc-handoff -- List all CTC handoff records."""
    admin, err = require_admin(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        stmt = select(CtcHandoff)
        rows = (await session.execute(stmt)).scalars().all()

    items = [_to_item(row) for row in rows]

    return json({"items": items, "total": len(items)})


@ctc_handoff_api_bp.post("/<member_id:uuid>")
async def set_ctc_handoff(request: Request, member_id: uuid.UUID):
    """POST /api/v1/admin/ctc-handoff/:member_id -- Upsert handoff readiness.

    Accepts JSON: CtcHandoffSetRequest
    """
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        set_req = CtcHandoffSetRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        target_member = await session.get(Member, member_id)
        if target_member is None:
            return json({"error": "Member not found"}, status=404)

        stmt = select(CtcHandoff).where(CtcHandoff.member_id == member_id)
        row = (await session.execute(stmt)).scalar_one_or_none()

        if row is None:
            row = CtcHandoff(
                member_id=member_id,
                ready_for_neos_den=set_req.ready_for_neos_den,
                updated_by=admin.id,
            )
            session.add(row)
        else:
            row.ready_for_neos_den = set_req.ready_for_neos_den
            row.updated_by = admin.id

        await session.commit()
        await session.refresh(row)

    return json(_to_item(row))
