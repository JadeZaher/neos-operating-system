"""JSON API blueprint for conflict case management.

Blueprint: conflicts_api_bp, url_prefix="/api/v1/conflicts"

Manages conflict cases through reporting, triage, resolution,
and repair agreement tracking with 30/60/90-day check-ins.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import re
import uuid
import datetime as _dt
from typing import Optional

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    ConflictCase,
    RepairAgreementRecord,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class RepairAgreementSchema(BaseModel):
    id: uuid.UUID
    title: str
    commitments: dict | None = None
    responsible_party: str | None = None
    status: str
    checkin_30_date: _dt.date | None = None
    checkin_30_notes: str | None = None
    checkin_60_date: _dt.date | None = None
    checkin_60_notes: str | None = None
    checkin_90_date: _dt.date | None = None
    checkin_90_notes: str | None = None
    completed_date: _dt.date | None = None
    created_at: _dt.datetime


class ConflictListItem(BaseModel):
    id: uuid.UUID
    case_id: str
    title: str
    status: str
    severity: str | None = None
    scope: str | None = None
    tier: int | None = None
    urgency: str | None = None
    safety_flag: bool = False
    domain: str | None = None
    created_at: _dt.datetime


class ConflictDetail(ConflictListItem):
    ecosystem_id: uuid.UUID
    description: str | None = None
    reporter_id: uuid.UUID | None = None
    root_cause_category: str | None = None
    parties: dict | None = None
    facilitator_id: uuid.UUID | None = None
    triage_notes: str | None = None
    resolution_summary: str | None = None
    resolved_date: _dt.date | None = None
    updated_at: _dt.datetime
    repair_agreements: list[RepairAgreementSchema] = []


class ConflictCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    title: str
    description: str | None = None
    reporter_id: uuid.UUID | None = None
    severity: str | None = None
    scope: str | None = None
    tier: int | None = None
    root_cause_category: str | None = None
    urgency: str | None = None
    safety_flag: bool = False
    parties: dict | None = None
    domain: str | None = None


class ConflictUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    severity: str | None = None
    scope: str | None = None
    tier: int | None = None
    root_cause_category: str | None = None
    urgency: str | None = None
    safety_flag: bool | None = None
    parties: dict | None = None
    facilitator_id: uuid.UUID | None = None
    domain: str | None = None
    triage_notes: str | None = None
    resolution_summary: str | None = None
    resolved_date: _dt.date | None = None


class RepairCreateRequest(BaseModel):
    title: str
    commitments: dict | None = None
    responsible_party: str | None = None
    checkin_30_date: _dt.date | None = None
    checkin_60_date: _dt.date | None = None
    checkin_90_date: _dt.date | None = None


class RepairUpdateRequest(BaseModel):
    title: str | None = None
    commitments: dict | None = None
    responsible_party: str | None = None
    status: str | None = None
    checkin_30_date: _dt.date | None = None
    checkin_30_notes: str | None = None
    checkin_60_date: _dt.date | None = None
    checkin_60_notes: str | None = None
    checkin_90_date: _dt.date | None = None
    checkin_90_notes: str | None = None
    completed_date: _dt.date | None = None


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

conflicts_api_bp = Blueprint("conflicts_api", url_prefix="/api/v1/conflicts")


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


def _conflict_to_list_item(c: ConflictCase) -> dict:
    return ConflictListItem(
        id=c.id,
        case_id=c.case_id,
        title=c.title,
        status=c.status,
        severity=c.severity,
        scope=c.scope,
        tier=c.tier,
        urgency=c.urgency,
        safety_flag=c.safety_flag,
        domain=c.domain,
        created_at=c.created_at,
    ).model_dump(mode="json")


def _repair_to_schema(r: RepairAgreementRecord) -> RepairAgreementSchema:
    return RepairAgreementSchema(
        id=r.id,
        title=r.title,
        commitments=r.commitments,
        responsible_party=r.responsible_party,
        status=r.status,
        checkin_30_date=r.checkin_30_date,
        checkin_30_notes=r.checkin_30_notes,
        checkin_60_date=r.checkin_60_date,
        checkin_60_notes=r.checkin_60_notes,
        checkin_90_date=r.checkin_90_date,
        checkin_90_notes=r.checkin_90_notes,
        completed_date=r.completed_date,
        created_at=r.created_at,
    )


def _conflict_to_detail(c: ConflictCase) -> dict:
    return ConflictDetail(
        id=c.id,
        case_id=c.case_id,
        title=c.title,
        status=c.status,
        severity=c.severity,
        scope=c.scope,
        tier=c.tier,
        urgency=c.urgency,
        safety_flag=c.safety_flag,
        domain=c.domain,
        created_at=c.created_at,
        ecosystem_id=c.ecosystem_id,
        description=c.description,
        reporter_id=c.reporter_id,
        root_cause_category=c.root_cause_category,
        parties=c.parties,
        facilitator_id=c.facilitator_id,
        triage_notes=c.triage_notes,
        resolution_summary=c.resolution_summary,
        resolved_date=c.resolved_date,
        updated_at=c.updated_at,
        repair_agreements=[
            _repair_to_schema(r) for r in (c.repair_agreements or [])
        ],
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@conflicts_api_bp.get("/")
async def list_conflicts(request: Request):
    """GET /api/v1/conflicts -- Paginated conflict list with filtering.

    Query params: status, severity, urgency,
    q (search case_id/title), page (default 1), per_page (default 25, max 100).
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(ConflictCase).order_by(ConflictCase.created_at.desc())

        if eco_ids:
            stmt = stmt.where(ConflictCase.ecosystem_id.in_(eco_ids))

        status = request.args.get("status")
        if status:
            stmt = stmt.where(ConflictCase.status == status)

        severity = request.args.get("severity")
        if severity:
            stmt = stmt.where(ConflictCase.severity == severity)

        urgency = request.args.get("urgency")
        if urgency:
            stmt = stmt.where(ConflictCase.urgency == urgency)

        search = request.args.get("q")
        if search:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(
                or_(
                    ConflictCase.case_id.ilike(pattern),
                    ConflictCase.title.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        conflicts = result.scalars().all()

    return json({
        "items": [_conflict_to_list_item(c) for c in conflicts],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@conflicts_api_bp.get("/<conflict_id:uuid>")
async def get_conflict(request: Request, conflict_id: uuid.UUID):
    """GET /api/v1/conflicts/:id -- Conflict detail with repair agreements."""
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(ConflictCase)
            .options(selectinload(ConflictCase.repair_agreements))
            .where(ConflictCase.id == conflict_id)
        )
        if eco_ids:
            stmt = stmt.where(ConflictCase.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        c = result.scalar_one_or_none()

    if c is None:
        return json({"error": "Conflict case not found"}, status=404)

    return json(_conflict_to_detail(c))


@conflicts_api_bp.post("/")
async def create_conflict(request: Request):
    """POST /api/v1/conflicts -- Create a new conflict case.

    Accepts JSON: ConflictCreateRequest
    Returns JSON: ConflictDetail with 201 status.
    """
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = ConflictCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    case_id_str = f"CONF-{short_id}"

    async with request.app.ctx.db() as session:
        conflict = ConflictCase(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            case_id=case_id_str,
            title=create_req.title,
            description=create_req.description,
            reporter_id=create_req.reporter_id,
            status="reported",
            severity=create_req.severity,
            scope=create_req.scope,
            tier=create_req.tier,
            root_cause_category=create_req.root_cause_category,
            urgency=create_req.urgency,
            safety_flag=create_req.safety_flag,
            parties=create_req.parties,
            domain=create_req.domain,
        )
        session.add(conflict)
        await session.commit()

        # Reload with relationships
        stmt = (
            select(ConflictCase)
            .options(selectinload(ConflictCase.repair_agreements))
            .where(ConflictCase.id == conflict.id)
        )
        result = await session.execute(stmt)
        conflict = result.scalar_one()

    return json(_conflict_to_detail(conflict), status=201)


@conflicts_api_bp.put("/<conflict_id:uuid>")
async def update_conflict(request: Request, conflict_id: uuid.UUID):
    """PUT /api/v1/conflicts/:id -- Update conflict (triage, resolve).

    Accepts JSON: ConflictUpdateRequest (only non-None fields applied).
    """
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = ConflictUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(ConflictCase).where(ConflictCase.id == conflict_id)
        if eco_ids:
            stmt = stmt.where(ConflictCase.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        c = result.scalar_one_or_none()
        if c is None:
            return json({"error": "Conflict case not found"}, status=404)

        update_data = update_req.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(c, field, value)

        await session.commit()

        # Reload with relationships
        stmt = (
            select(ConflictCase)
            .options(selectinload(ConflictCase.repair_agreements))
            .where(ConflictCase.id == c.id)
        )
        result = await session.execute(stmt)
        c = result.scalar_one()

    return json(_conflict_to_detail(c))


@conflicts_api_bp.post("/<conflict_id:uuid>/repair")
async def create_repair_agreement(request: Request, conflict_id: uuid.UUID):
    """POST /api/v1/conflicts/:id/repair -- Create a repair agreement.

    Accepts JSON: RepairCreateRequest
    Returns JSON: RepairAgreementSchema with 201 status.
    """
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = RepairCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        # Verify conflict exists and is accessible
        c_stmt = select(ConflictCase.id).where(ConflictCase.id == conflict_id)
        if eco_ids:
            c_stmt = c_stmt.where(ConflictCase.ecosystem_id.in_(eco_ids))
        if await session.scalar(c_stmt) is None:
            return json({"error": "Conflict case not found"}, status=404)

        repair = RepairAgreementRecord(
            id=uuid.uuid4(),
            conflict_case_id=conflict_id,
            title=create_req.title,
            commitments=create_req.commitments,
            responsible_party=create_req.responsible_party,
            status="active",
            checkin_30_date=create_req.checkin_30_date,
            checkin_60_date=create_req.checkin_60_date,
            checkin_90_date=create_req.checkin_90_date,
        )
        session.add(repair)
        await session.commit()
        await session.refresh(repair)

    schema = _repair_to_schema(repair)
    return json(schema.model_dump(mode="json"), status=201)


@conflicts_api_bp.put("/<conflict_id:uuid>/repair/<repair_id:uuid>")
async def update_repair_agreement(
    request: Request, conflict_id: uuid.UUID, repair_id: uuid.UUID
):
    """PUT /api/v1/conflicts/:id/repair/:repair_id -- Update repair agreement.

    Accepts JSON: RepairUpdateRequest (checkin notes, status updates).
    """
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = RepairUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        # Verify conflict exists and is accessible
        c_stmt = select(ConflictCase.id).where(ConflictCase.id == conflict_id)
        if eco_ids:
            c_stmt = c_stmt.where(ConflictCase.ecosystem_id.in_(eco_ids))
        if await session.scalar(c_stmt) is None:
            return json({"error": "Conflict case not found"}, status=404)

        stmt = select(RepairAgreementRecord).where(
            RepairAgreementRecord.id == repair_id,
            RepairAgreementRecord.conflict_case_id == conflict_id,
        )
        result = await session.execute(stmt)
        repair = result.scalar_one_or_none()
        if repair is None:
            return json({"error": "Repair agreement not found"}, status=404)

        update_data = update_req.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(repair, field, value)

        await session.commit()
        await session.refresh(repair)

    schema = _repair_to_schema(repair)
    return json(schema.model_dump(mode="json"))
