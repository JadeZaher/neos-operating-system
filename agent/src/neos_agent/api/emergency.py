"""JSON API blueprint for emergency state management.

Blueprint: emergency_api_bp, url_prefix="/api/v1/emergency"

Circuit breaker state visualization, emergency declaration,
auto-reversion timer display, and resolution.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import re
import uuid
import datetime as _dt
from datetime import timedelta, timezone
from typing import Optional

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import EmergencyState
from neos_agent.api.helpers import require_auth, get_ecosystem_ids

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class EmergencyListItem(BaseModel):
    id: uuid.UUID
    state: str
    declared_at: _dt.datetime | None = None
    declared_by: str | None = None
    auto_revert_at: _dt.datetime | None = None
    closed_at: _dt.datetime | None = None
    post_review_status: str | None = None
    created_at: _dt.datetime


class EmergencyDetail(EmergencyListItem):
    ecosystem_id: uuid.UUID
    criteria_met: dict | list | None = None
    half_open_entered_at: _dt.datetime | None = None
    recovery_entered_at: _dt.datetime | None = None
    pre_authorized_roles: dict | list | None = None
    actions_log: dict | list | None = None
    notes: str | None = None
    updated_at: _dt.datetime


class EmergencyDeclareRequest(BaseModel):
    ecosystem_id: uuid.UUID
    declared_by: str
    reason: str | None = None
    auto_revert_days: int = 30


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

emergency_api_bp = Blueprint("emergency_api", url_prefix="/api/v1/emergency")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _emergency_to_list_item(e: EmergencyState) -> dict:
    return EmergencyListItem(
        id=e.id,
        state=e.state,
        declared_at=e.declared_at,
        declared_by=e.declared_by,
        auto_revert_at=e.auto_revert_at,
        closed_at=e.closed_at,
        post_review_status=e.post_review_status,
        created_at=e.created_at,
    ).model_dump(mode="json")


def _emergency_to_detail(e: EmergencyState) -> dict:
    return EmergencyDetail(
        id=e.id,
        state=e.state,
        declared_at=e.declared_at,
        declared_by=e.declared_by,
        auto_revert_at=e.auto_revert_at,
        closed_at=e.closed_at,
        post_review_status=e.post_review_status,
        created_at=e.created_at,
        ecosystem_id=e.ecosystem_id,
        criteria_met=e.criteria_met,
        half_open_entered_at=e.half_open_entered_at,
        recovery_entered_at=e.recovery_entered_at,
        pre_authorized_roles=e.pre_authorized_roles,
        actions_log=e.actions_log,
        notes=e.notes,
        updated_at=e.updated_at,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@emergency_api_bp.get("/")
async def list_emergencies(request: Request):
    """GET /api/v1/emergency -- current emergency state + paginated history.

    Returns the most recent emergency as "current" plus a paginated list
    of all emergency events.
    Query params: page (default 1), per_page (default 25, max 100).
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        base_stmt = select(EmergencyState).order_by(
            EmergencyState.declared_at.desc()
        )
        if eco_ids:
            base_stmt = base_stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))

        # Current (most recent) emergency
        current_stmt = base_stmt.limit(1)
        current_result = await session.execute(current_stmt)
        current_state = current_result.scalar_one_or_none()

        # Paginated history
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        history_stmt = base_stmt.offset(offset).limit(per_page)
        history_result = await session.execute(history_stmt)
        history = history_result.scalars().all()

    return json({
        "current": _emergency_to_detail(current_state) if current_state else None,
        "items": [_emergency_to_list_item(e) for e in history],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@emergency_api_bp.get("/<emergency_id:uuid>")
async def get_emergency(request: Request, emergency_id: uuid.UUID):
    """GET /api/v1/emergency/:id -- emergency event detail."""
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(EmergencyState).where(EmergencyState.id == emergency_id)
        if eco_ids:
            stmt = stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        state = result.scalar_one_or_none()

    if state is None:
        return json({"error": "Emergency record not found"}, status=404)

    return json(_emergency_to_detail(state))


@emergency_api_bp.post("/declare")
async def declare_emergency(request: Request):
    """POST /api/v1/emergency/declare -- declare a new emergency.

    Accepts JSON: EmergencyDeclareRequest
    Creates a circuit breaker OPEN state with configurable auto-revert.
    Returns JSON: EmergencyDetail with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = EmergencyDeclareRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    now = _dt.datetime.now(timezone.utc).replace(tzinfo=None)

    async with request.app.ctx.db() as session:
        state = EmergencyState(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            state="open",
            declared_by=create_req.declared_by,
            declared_at=now,
            notes=create_req.reason or "",
            auto_revert_at=now + timedelta(days=create_req.auto_revert_days),
            pre_authorized_roles=[],
            actions_log=[],
        )
        session.add(state)
        await session.commit()

        # Reload for response
        stmt = select(EmergencyState).where(EmergencyState.id == state.id)
        result = await session.execute(stmt)
        state = result.scalar_one()

    return json(_emergency_to_detail(state), status=201)


@emergency_api_bp.post("/<emergency_id:uuid>/resolve")
async def resolve_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/resolve — begin Recovery (open → half_open).

    Transitions the emergency from 'open' to 'half_open' (NOT to 'closed').
    The half_open Recovery state is mandatory per NEOS Principle 4 and
    emergency-reversion SKILL.md section E step 3.  During Recovery:
    - Emergency authority ceases immediately.
    - Crisis decisions must be ratified through normal ACT process within 30 days.
    - Post-emergency review must be scheduled within 14 days.
    - Use POST /complete-recovery to finalize (half_open → closed).

    Returns 409 if the emergency is not in 'open' state.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(EmergencyState).where(EmergencyState.id == emergency_id)
        if eco_ids:
            stmt = stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        state = result.scalar_one_or_none()

        if state is None:
            return json({"error": "Emergency record not found"}, status=404)

        if state.state != "open":
            return json(
                {"error": f"Cannot resolve: emergency is in '{state.state}' state, must be 'open'"},
                status=409,
            )

        now = _dt.datetime.now(timezone.utc).replace(tzinfo=None)
        state.state = "half_open"
        state.half_open_entered_at = now
        # Recovery window: 30 days per SKILL.md section E step 3.
        # auto_revert_at is repurposed as the recovery deadline for
        # decision ratification.
        state.auto_revert_at = now + timedelta(days=30)

        # Append reversion audit note to actions_log
        log = state.actions_log or []
        if isinstance(log, dict):
            log = []
        log.append({
            "action": "half_open_transition",
            "timestamp": now.isoformat(),
            "trigger": "manual_resolve",
            "actor": member.member_id if hasattr(member, "member_id") else str(member.id),
            "note": (
                "Emergency authority ceased. Recovery state entered. "
                "30-day ratification window started. "
                "Post-emergency review must be scheduled within 14 days."
            ),
        })
        state.actions_log = log

        await session.commit()
        await session.refresh(state)

        logger.info(
            "Emergency %s transitioned open→half_open (Recovery started, deadline %s)",
            emergency_id,
            state.auto_revert_at,
        )

    return json(_emergency_to_detail(state))


@emergency_api_bp.post("/<emergency_id:uuid>/complete-recovery")
async def complete_recovery(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/complete-recovery — finalize recovery (half_open → closed).

    Requires that a post-emergency review has been recorded (post_review_status
    must be 'complete') per emergency-reversion SKILL.md section E steps 8-10.
    Returns 409 if the emergency is not in 'half_open' state, or if the required
    post-emergency review has not been completed.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(EmergencyState).where(EmergencyState.id == emergency_id)
        if eco_ids:
            stmt = stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        state = result.scalar_one_or_none()

        if state is None:
            return json({"error": "Emergency record not found"}, status=404)

        if state.state != "half_open":
            return json(
                {"error": f"Cannot complete recovery: emergency is in '{state.state}' state, must be 'half_open'"},
                status=409,
            )

        # The post-emergency review is MANDATORY per SKILL.md section E step 8.
        # It must be Complete before we allow half_open→closed.
        if state.post_review_status != "complete":
            return json(
                {"error": "Post-emergency review must be complete before closing recovery. Set post_review_status='complete' first."},
                status=409,
            )

        now = _dt.datetime.now(timezone.utc).replace(tzinfo=None)
        state.state = "closed"
        state.closed_at = now

        # Append closure audit note
        log = state.actions_log or []
        if isinstance(log, dict):
            log = []
        log.append({
            "action": "recovery_completed",
            "timestamp": now.isoformat(),
            "actor": member.member_id if hasattr(member, "member_id") else str(member.id),
            "note": "Recovery completed. Circuit breaker returned to closed state. Normal governance fully restored.",
        })
        state.actions_log = log

        await session.commit()
        await session.refresh(state)

        logger.info("Emergency %s recovery completed (half_open→closed)", emergency_id)

    return json(_emergency_to_detail(state))
