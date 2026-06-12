"""JSON API blueprint for emergency state management.

Blueprint: emergency_api_bp, url_prefix="/api/v1/emergency"

State machine (enforced at this layer AND the DB CHECK constraint):
    closed -> open       via POST /declare
    open -> half_open    via POST /:id/resolve and the cron auto-revert
    half_open -> closed  via POST /:id/complete-recovery (requires review)
Any other transition is rejected with HTTP 409.
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from datetime import timedelta, timezone
from typing import Any

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.api.helpers import get_ecosystem_ids, require_auth
from neos_agent.db.models import EmergencyState

logger = logging.getLogger(__name__)


STATE_OPEN = "open"
STATE_HALF_OPEN = "half_open"
STATE_CLOSED = "closed"
ACTIVE_STATES = (STATE_OPEN, STATE_HALF_OPEN)
RECOVERY_WINDOW_DAYS = 30


def _now_naive_utc() -> _dt.datetime:
    """Naive-UTC wall clock (matches legacy tz-naive columns)."""
    return _dt.datetime.now(timezone.utc).replace(tzinfo=None)


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


emergency_api_bp = Blueprint("emergency_api", url_prefix="/api/v1/emergency")


def _actor_label(member: Any) -> str:
    if hasattr(member, "member_id") and member.member_id is not None:
        return str(member.member_id)
    if hasattr(member, "id") and member.id is not None:
        return str(member.id)
    return "unknown"


def _append_action(state: EmergencyState, entry: dict) -> None:
    log = state.actions_log or []
    if isinstance(log, dict):
        log = []
    log.append(entry)
    state.actions_log = log


def _emergency_to_list_item(e: EmergencyState) -> dict:
    return EmergencyListItem(
        id=e.id, state=e.state, declared_at=e.declared_at,
        declared_by=e.declared_by, auto_revert_at=e.auto_revert_at,
        closed_at=e.closed_at, post_review_status=e.post_review_status,
        created_at=e.created_at,
    ).model_dump(mode="json")


def _emergency_to_detail(e: EmergencyState) -> dict:
    return EmergencyDetail(
        id=e.id, state=e.state, declared_at=e.declared_at,
        declared_by=e.declared_by, auto_revert_at=e.auto_revert_at,
        closed_at=e.closed_at, post_review_status=e.post_review_status,
        created_at=e.created_at, ecosystem_id=e.ecosystem_id,
        criteria_met=e.criteria_met,
        half_open_entered_at=e.half_open_entered_at,
        recovery_entered_at=e.recovery_entered_at,
        pre_authorized_roles=e.pre_authorized_roles,
        actions_log=e.actions_log, notes=e.notes, updated_at=e.updated_at,
    ).model_dump(mode="json")


@emergency_api_bp.get("/")
async def list_emergencies(request: Request):
    """GET /api/v1/emergency -- current emergency state + paginated history."""
    member, err = require_auth(request)
    if err:
        return err
    eco_ids = get_ecosystem_ids(request)
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page
    async with request.app.ctx.db() as session:
        base_stmt = select(EmergencyState).order_by(EmergencyState.declared_at.desc())
        if eco_ids:
            base_stmt = base_stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))
        current_result = await session.execute(base_stmt.limit(1))
        current_state = current_result.scalar_one_or_none()
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = await session.scalar(count_stmt) or 0
        history_result = await session.execute(base_stmt.offset(offset).limit(per_page))
        history = history_result.scalars().all()
    payload = dict()
    payload["current"] = _emergency_to_detail(current_state) if current_state else None
    payload["items"] = [_emergency_to_list_item(e) for e in history]
    payload["total"] = total
    payload["page"] = page
    payload["per_page"] = per_page
    return json(payload)


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
        not_found = dict()
        not_found["error"] = "Emergency record not found"
        return json(not_found, status=404)
    return json(_emergency_to_detail(state))


@emergency_api_bp.post("/declare")
async def declare_emergency(request: Request):
    """POST /api/v1/emergency/declare -- declare a new emergency.

    Rejects with 409 if an active emergency (state in open or half_open)
    already exists for the target ecosystem. Symmetric with the
    governance_tools.declare_emergency invariant.
    """
    member, err = require_auth(request)
    if err:
        return err
    body = request.json or {}
    try:
        create_req = EmergencyDeclareRequest(**body)
    except Exception as e:
        bad = dict()
        bad["error"] = "Invalid request: " + str(e)
        return json(bad, status=400)
    eco_ids = get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        denied = dict()
        denied["error"] = "Access denied: ecosystem not in scope"
        return json(denied, status=403)
    now = _now_naive_utc()
    async with request.app.ctx.db() as session:
        active_stmt = select(EmergencyState).where(
            EmergencyState.ecosystem_id == create_req.ecosystem_id,
            EmergencyState.state.in_(ACTIVE_STATES),
        ).limit(1)
        active_result = await session.execute(active_stmt)
        if active_result.scalar_one_or_none() is not None:
            conflict = dict()
            conflict["error"] = (
                "An emergency is already active for this ecosystem. "
                "Resolve or complete recovery before declaring a new one."
            )
            return json(conflict, status=409)
        declared_action = dict()
        declared_action["action"] = "declared"
        declared_action["timestamp"] = now.isoformat()
        declared_action["actor"] = _actor_label(member)
        declared_action["note"] = (
            "Emergency declared. Circuit breaker OPEN. "
            "Auto-revert in " + str(create_req.auto_revert_days) + " days."
        )
        state = EmergencyState(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            state=STATE_OPEN,
            declared_by=create_req.declared_by,
            declared_at=now,
            notes=create_req.reason or "",
            auto_revert_at=now + timedelta(days=create_req.auto_revert_days),
            pre_authorized_roles=[],
            actions_log=[declared_action],
        )
        session.add(state)
        await session.commit()
        stmt = select(EmergencyState).where(EmergencyState.id == state.id)
        result = await session.execute(stmt)
        state = result.scalar_one()
    return json(_emergency_to_detail(state), status=201)


@emergency_api_bp.post("/<emergency_id:uuid>/resolve")
async def resolve_emergency(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/resolve -- begin Recovery (open -> half_open).

    Transitions open -> half_open (NOT closed). Mandatory per NEOS
    Principle 4 / SKILL.md section E step 3. Row-locked via
    SELECT FOR UPDATE so concurrent cron auto-revert and manual
    resolve cannot double-transition the same row.
    Returns 409 if the emergency is not in 'open' state.
    """
    member, err = require_auth(request)
    if err:
        return err
    eco_ids = get_ecosystem_ids(request)
    async with request.app.ctx.db() as session:
        stmt = select(EmergencyState).where(EmergencyState.id == emergency_id).with_for_update()
        if eco_ids:
            stmt = stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))
        result = await session.execute(stmt)
        state = result.scalar_one_or_none()
        if state is None:
            not_found = dict()
            not_found["error"] = "Emergency record not found"
            return json(not_found, status=404)
        if state.state != STATE_OPEN:
            conflict = dict()
            conflict["error"] = (
                "Cannot resolve: emergency is in '" + state.state +
                "' state, must be '" + STATE_OPEN + "'"
            )
            return json(conflict, status=409)
        now = _now_naive_utc()
        state.state = STATE_HALF_OPEN
        state.half_open_entered_at = now
        state.auto_revert_at = now + timedelta(days=RECOVERY_WINDOW_DAYS)
        action = dict()
        action["action"] = "half_open_transition"
        action["timestamp"] = now.isoformat()
        action["trigger"] = "manual_resolve"
        action["actor"] = _actor_label(member)
        action["note"] = (
            "Emergency authority ceased. Recovery state entered. "
            "30-day ratification window started. "
            "Post-emergency review must be scheduled within 14 days."
        )
        _append_action(state, action)
        await session.commit()
        await session.refresh(state)
        logger.info(
            "Emergency %s transitioned open->half_open (Recovery started, deadline %s)",
            emergency_id, state.auto_revert_at,
        )
    return json(_emergency_to_detail(state))


@emergency_api_bp.post("/<emergency_id:uuid>/complete-recovery")
async def complete_recovery(request: Request, emergency_id: uuid.UUID):
    """POST /api/v1/emergency/:id/complete-recovery -- finalize (half_open -> closed).

    Requires post_review_status == 'complete' per SKILL.md section E
    steps 8-10. Row-locked. Returns 409 if state is not half_open or
    review is incomplete.
    """
    member, err = require_auth(request)
    if err:
        return err
    eco_ids = get_ecosystem_ids(request)
    async with request.app.ctx.db() as session:
        stmt = select(EmergencyState).where(EmergencyState.id == emergency_id).with_for_update()
        if eco_ids:
            stmt = stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))
        result = await session.execute(stmt)
        state = result.scalar_one_or_none()
        if state is None:
            not_found = dict()
            not_found["error"] = "Emergency record not found"
            return json(not_found, status=404)
        if state.state != STATE_HALF_OPEN:
            conflict = dict()
            conflict["error"] = (
                "Cannot complete recovery: emergency is in '" + state.state +
                "' state, must be '" + STATE_HALF_OPEN + "'"
            )
            return json(conflict, status=409)
        if state.post_review_status != "complete":
            review_err = dict()
            review_err["error"] = (
                "Post-emergency review must be complete before closing recovery. "
                "Set post_review_status='complete' first."
            )
            return json(review_err, status=409)
        now = _now_naive_utc()
        state.state = STATE_CLOSED
        state.closed_at = now
        action = dict()
        action["action"] = "recovery_completed"
        action["timestamp"] = now.isoformat()
        action["actor"] = _actor_label(member)
        action["note"] = (
            "Recovery completed. Circuit breaker returned to closed state. "
            "Normal governance fully restored."
        )
        _append_action(state, action)
        await session.commit()
        await session.refresh(state)
        logger.info("Emergency %s recovery completed (half_open->closed)", emergency_id)
    return json(_emergency_to_detail(state))
