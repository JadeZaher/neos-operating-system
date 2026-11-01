"""Emergency handling views for the NEOS dashboard (Layer VIII).

Blueprint: emergency_bp, url_prefix="/dashboard/emergency"

Circuit breaker state visualization, emergency declaration management,
auto-reversion timer display, and emergency action logging.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, html
from sanic.request import Request
from sqlalchemy import select

from neos_agent.db.models import EmergencyState
from neos_agent.views._rendering import render, get_selected_ecosystem_ids, get_scoped_entity, retired_write

logger = logging.getLogger(__name__)

emergency_bp = Blueprint("emergency", url_prefix="/dashboard/emergency")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply ecosystem scoping and optional filters to a query."""
    if eco_ids:
        stmt = stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))
    return stmt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@emergency_bp.get("/")
async def dashboard(request: Request):
    """GET /dashboard/emergency -- emergency status overview."""
    eco_ids = get_selected_ecosystem_ids(request)
    try:
        async with request.app.ctx.db() as session:
            # Get the current (most recent) emergency state
            current_stmt = select(EmergencyState).order_by(
                EmergencyState.declared_at.desc()
            )
            current_stmt = _apply_filters(current_stmt, request, eco_ids)
            current_stmt = current_stmt.limit(1)
            current_result = await session.execute(current_stmt)
            current_state = current_result.scalar_one_or_none()

            # Get history of all emergency events
            history_stmt = select(EmergencyState).order_by(
                EmergencyState.declared_at.desc()
            )
            history_stmt = _apply_filters(history_stmt, request, eco_ids)
            history_stmt = history_stmt.limit(20)
            history_result = await session.execute(history_stmt)
            history = history_result.scalars().all()
    except Exception:
        logger.exception("Failed to load emergency dashboard")
        current_state = None
        history = []

    content = await render(
        "dashboard/emergency/dashboard.html",
        request=request,
        current_state=current_state,
        history=history,
        active_page="emergency",
    )
    return html(content)


@emergency_bp.get("/<emergency_id:uuid>")
async def detail(request: Request, emergency_id: uuid.UUID):
    """GET /dashboard/emergency/{id} -- emergency event detail."""
    try:
        async with request.app.ctx.db() as session:
            state = await get_scoped_entity(session, EmergencyState, emergency_id, request)
            if state is None:
                content = await render(
                    "dashboard/emergency/dashboard.html",
                    request=request,
                    current_state=None,
                    history=[],
                    error="Emergency record not found.",
                    active_page="emergency",
                )
                return html(content, status=404)
    except Exception:
        logger.exception("Failed to load emergency detail")
        content = await render(
            "dashboard/emergency/dashboard.html",
            request=request,
            current_state=None,
            history=[],
            error="Failed to load emergency record.",
            active_page="emergency",
        )
        return html(content, status=500)

    content = await render(
        "dashboard/emergency/detail.html",
        request=request,
        state=state,
        active_page="emergency",
    )
    return html(content)


# Legacy write routes: they skipped the co-signer and jumped open -> closed past Recovery.
LEGACY_WRITE_REFUSAL = (
    "Emergencies are declared, co-signed, ended and closed in the NEOS app, "
    "which requires a co-signer and a Recovery review. Nothing was changed here."
)


@emergency_bp.post("/declare")
async def declare_emergency(request: Request):
    """POST /dashboard/emergency/declare -- retired (410); see LEGACY_WRITE_REFUSAL."""
    return retired_write(request, "/emergency", LEGACY_WRITE_REFUSAL)


@emergency_bp.post("/<emergency_id:uuid>/resolve")
async def resolve_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /dashboard/emergency/{id}/resolve -- retired (410): it used to skip Recovery."""
    return retired_write(request, f"/emergency/{emergency_id}", LEGACY_WRITE_REFUSAL)
