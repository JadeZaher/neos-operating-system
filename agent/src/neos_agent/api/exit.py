"""JSON API blueprint for exit process management.

Blueprint: exit_api_bp, url_prefix="/api/v1/exit"

Handles voluntary exit initiation, commitment unwinding tracker,
status transitions, and exit process listing.
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
from sqlalchemy import func, or_, select

from neos_agent.db.models import ExitRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class ExitListItem(BaseModel):
    id: uuid.UUID
    exit_type: str
    status: str
    member_id: uuid.UUID
    declared_date: _dt.date | None = None
    target_completion_date: _dt.date | None = None
    completed_date: _dt.date | None = None
    created_at: _dt.datetime


class ExitDetail(ExitListItem):
    ecosystem_id: uuid.UUID
    coordinator_id: uuid.UUID | None = None
    commitment_inventory: dict | None = None
    unwinding_status: dict | None = None
    data_export_requested: bool = False
    data_export_completed: _dt.date | None = None
    departure_notice: str | None = None
    re_entry_eligible: bool = True
    notes: str | None = None
    updated_at: _dt.datetime


class ExitCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    member_id: uuid.UUID
    exit_type: str = "standard"
    reason: str | None = None


class ExitStatusRequest(BaseModel):
    new_status: str


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

exit_api_bp = Blueprint("exit_api", url_prefix="/api/v1/exit")


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


def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


def _exit_to_list_item(r: ExitRecord) -> dict:
    return ExitListItem(
        id=r.id,
        exit_type=r.exit_type,
        status=r.status,
        member_id=r.member_id,
        declared_date=r.declared_date,
        target_completion_date=r.target_completion_date,
        completed_date=r.completed_date,
        created_at=r.created_at,
    ).model_dump(mode="json")


def _exit_to_detail(r: ExitRecord) -> dict:
    return ExitDetail(
        id=r.id,
        exit_type=r.exit_type,
        status=r.status,
        member_id=r.member_id,
        declared_date=r.declared_date,
        target_completion_date=r.target_completion_date,
        completed_date=r.completed_date,
        created_at=r.created_at,
        ecosystem_id=r.ecosystem_id,
        coordinator_id=r.coordinator_id,
        commitment_inventory=r.commitment_inventory,
        unwinding_status=r.unwinding_status,
        data_export_requested=r.data_export_requested,
        data_export_completed=r.data_export_completed,
        departure_notice=r.departure_notice,
        re_entry_eligible=r.re_entry_eligible,
        notes=r.notes,
        updated_at=r.updated_at,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@exit_api_bp.get("/")
async def list_exits(request: Request):
    """GET /api/v1/exit -- paginated list with filters.

    Query params: status, exit_type, q (search departure_notice),
    page (default 1), per_page (default 25, max 100).
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(ExitRecord).order_by(ExitRecord.created_at.desc())

        if eco_ids:
            stmt = stmt.where(ExitRecord.ecosystem_id.in_(eco_ids))

        status = request.args.get("status")
        if status:
            stmt = stmt.where(ExitRecord.status == status)

        exit_type = request.args.get("exit_type")
        if exit_type:
            stmt = stmt.where(ExitRecord.exit_type == exit_type)

        search = request.args.get("q")
        if search:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(ExitRecord.departure_notice.ilike(pattern))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        exits = result.scalars().all()

    return json({
        "items": [_exit_to_list_item(r) for r in exits],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@exit_api_bp.get("/<exit_id:uuid>")
async def get_exit(request: Request, exit_id: uuid.UUID):
    """GET /api/v1/exit/:id -- exit process detail with unwinding tracker."""
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(ExitRecord).where(ExitRecord.id == exit_id)
        if eco_ids:
            stmt = stmt.where(ExitRecord.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

    if record is None:
        return json({"error": "Exit record not found"}, status=404)

    return json(_exit_to_detail(record))


@exit_api_bp.post("/")
async def create_exit(request: Request):
    """POST /api/v1/exit -- initiate an exit process.

    Accepts JSON: ExitCreateRequest
    Returns JSON: ExitDetail with 201 status.
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = ExitCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    now = _dt.datetime.utcnow()
    cooling_days = 30 if create_req.exit_type == "standard" else 7

    async with request.app.ctx.db() as session:
        record = ExitRecord(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            member_id=create_req.member_id,
            exit_type=create_req.exit_type,
            status="declared",
            declared_date=now.date(),
            target_completion_date=(now + timedelta(days=cooling_days)).date(),
            commitment_inventory=[],
            unwinding_status={},
            departure_notice=create_req.reason or "",
        )
        session.add(record)
        await session.commit()

        # Reload for response
        stmt = select(ExitRecord).where(ExitRecord.id == record.id)
        result = await session.execute(stmt)
        record = result.scalar_one()

    return json(_exit_to_detail(record), status=201)


@exit_api_bp.post("/<exit_id:uuid>/status")
async def status_transition(request: Request, exit_id: uuid.UUID):
    """POST /api/v1/exit/:id/status -- transition exit status.

    Accepts JSON: {"new_status": "..."}
    Returns JSON: ExitDetail
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        status_req = ExitStatusRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(ExitRecord).where(ExitRecord.id == exit_id)
        if eco_ids:
            stmt = stmt.where(ExitRecord.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        record = result.scalar_one_or_none()

        if record is None:
            return json({"error": "Exit record not found"}, status=404)

        old_status = record.status
        record.status = status_req.new_status

        if status_req.new_status == "completed":
            record.completed_date = _dt.datetime.utcnow().date()

        await session.commit()
        await session.refresh(record)

        logger.info(
            "Exit %s status: %s -> %s",
            exit_id, old_status, status_req.new_status,
        )

    return json(_exit_to_detail(record))
