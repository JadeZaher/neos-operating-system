"""Emergency handling views for the NEOS dashboard (Layer VIII).

Blueprint: emergency_bp, url_prefix="/dashboard/emergency"

Circuit breaker state visualization, emergency declaration management,
auto-reversion timer display, and emergency action logging.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func

from neos_agent.db.models import EmergencyState
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id, escape_like

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


@emergency_bp.post("/declare")
async def declare_emergency(request: Request):
    """POST /dashboard/emergency/declare -- declare a new emergency.

    Creates a circuit breaker OPEN state with a 30-day auto-revert.
    """
    form = request.form
    eco_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if eco_id is None:
        content = await render(
            "dashboard/emergency/dashboard.html",
            request=request,
            active_page="emergency",
            error="Invalid or unauthorised ecosystem.",
        )
        return html(content, status=403)
    try:
        now = datetime.utcnow()
        auto_revert_days = int(form.get("auto_revert_days", 30))

        async with request.app.ctx.db() as session:
            state = EmergencyState(
                id=uuid.uuid4(),
                ecosystem_id=eco_id,
                state="open",
                declared_by=form.get("declared_by"),
                declared_at=now,
                notes=form.get("reason", ""),
                auto_revert_at=now + timedelta(days=auto_revert_days),
                pre_authorized_roles=[],
                actions_log=[],
            )
            session.add(state)
            await session.commit()
            new_id = state.id
    except Exception:
        logger.exception("Failed to declare emergency")
        content = await render(
            "dashboard/emergency/dashboard.html",
            request=request,
            current_state=None,
            history=[],
            error="Failed to declare emergency.",
            active_page="emergency",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/emergency/{new_id}")


@emergency_bp.post("/<emergency_id:uuid>/resolve")
async def resolve_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /dashboard/emergency/{id}/resolve -- resolve (close) an emergency."""
    form = request.form
    try:
        async with request.app.ctx.db() as session:
            state = await get_scoped_entity(session, EmergencyState, emergency_id, request)
            if state is None:
                return html(
                    await render(
                        "dashboard/emergency/dashboard.html",
                        request=request,
                        current_state=None,
                        history=[],
                        error="Emergency record not found.",
                        active_page="emergency",
                    ),
                    status=404,
                )

            state.state = "closed"
            state.closed_at = datetime.utcnow()
            await session.commit()
            logger.info("Emergency %s resolved", emergency_id)
    except Exception:
        logger.exception("Failed to resolve emergency")
        return html(
            await render(
                "dashboard/emergency/dashboard.html",
                request=request,
                current_state=None,
                history=[],
                error="Failed to resolve emergency.",
                active_page="emergency",
            ),
            status=500,
        )

    return redirect("/dashboard/emergency")
