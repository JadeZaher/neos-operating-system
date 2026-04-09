"""JSON API blueprint for emergency state management.

Blueprint: emergency_api_bp, url_prefix="/api/v1/emergency"

Circuit breaker state visualization, emergency declaration,
auto-reversion timer display, and resolution.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import re
import uuid
import datetime as _dt
from datetime import timedelta
from typing import Optional

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import EmergencyState

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


def _require_auth(request: Request):
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def _get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    cookie = request.cookies.get("neos_selected_ecosystems")
    if cookie:
        try:
            ids = json_module.loads(cookie)
            return [uuid.UUID(i) for i in ids if i]
        except (json_module.JSONDecodeError, ValueError):
            pass
    member = getattr(request.ctx, "member", None)
    if member:
        return [member.ecosystem_id]
    return []


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
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

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
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

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
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = EmergencyDeclareRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    now = _dt.datetime.utcnow()

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
    """POST /api/v1/emergency/:id/resolve -- resolve (close) an emergency.

    Returns JSON: EmergencyDetail
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(EmergencyState).where(EmergencyState.id == emergency_id)
        if eco_ids:
            stmt = stmt.where(EmergencyState.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        state = result.scalar_one_or_none()

        if state is None:
            return json({"error": "Emergency record not found"}, status=404)

        state.state = "closed"
        state.closed_at = _dt.datetime.utcnow()

        await session.commit()
        await session.refresh(state)

        logger.info("Emergency %s resolved", emergency_id)

    return json(_emergency_to_detail(state))
