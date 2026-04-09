"""JSON API blueprint for domain management.

Blueprint: domains_api_bp, url_prefix="/api/v1/domains"

Manages governance domains including their elements, metrics,
and stewardship assignments.
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
    Domain,
    DomainElement,
    DomainMetric,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class DomainElementSchema(BaseModel):
    id: uuid.UUID
    element_name: str
    element_value: dict | None = None


class DomainMetricSchema(BaseModel):
    id: uuid.UUID
    metric: str
    target: str | None = None
    measurement_method: str | None = None


class DomainListItem(BaseModel):
    id: uuid.UUID
    domain_id: str
    version: str
    status: str
    purpose: str | None = None
    current_steward: str | None = None
    parent_domain_id: uuid.UUID | None = None
    created_at: _dt.datetime


class DomainDetail(DomainListItem):
    ecosystem_id: uuid.UUID
    steward_id: uuid.UUID | None = None
    created_by: str | None = None
    metric_definitions: dict | None = None
    elements: dict | None = None
    updated_at: _dt.datetime
    domain_elements: list[DomainElementSchema] = []
    domain_metrics: list[DomainMetricSchema] = []


class DomainCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    purpose: str | None = None
    current_steward: str | None = None
    steward_id: uuid.UUID | None = None
    parent_domain_id: uuid.UUID | None = None
    created_by: str | None = None
    metric_definitions: dict | None = None
    elements: dict | None = None


class DomainUpdateRequest(BaseModel):
    status: str | None = None
    purpose: str | None = None
    current_steward: str | None = None
    steward_id: uuid.UUID | None = None
    parent_domain_id: uuid.UUID | None = None
    metric_definitions: dict | None = None
    elements: dict | None = None


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

domains_api_bp = Blueprint("domains_api", url_prefix="/api/v1/domains")


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


def _domain_to_list_item(d: Domain) -> dict:
    return DomainListItem(
        id=d.id,
        domain_id=d.domain_id,
        version=d.version,
        status=d.status,
        purpose=d.purpose,
        current_steward=d.current_steward,
        parent_domain_id=d.parent_domain_id,
        created_at=d.created_at,
    ).model_dump(mode="json")


def _domain_to_detail(d: Domain) -> dict:
    return DomainDetail(
        id=d.id,
        domain_id=d.domain_id,
        version=d.version,
        status=d.status,
        purpose=d.purpose,
        current_steward=d.current_steward,
        parent_domain_id=d.parent_domain_id,
        created_at=d.created_at,
        ecosystem_id=d.ecosystem_id,
        steward_id=d.steward_id,
        created_by=d.created_by,
        metric_definitions=d.metric_definitions,
        elements=d.elements,
        updated_at=d.updated_at,
        domain_elements=[
            DomainElementSchema(
                id=e.id,
                element_name=e.element_name,
                element_value=e.element_value,
            )
            for e in (d.domain_elements or [])
        ],
        domain_metrics=[
            DomainMetricSchema(
                id=m.id,
                metric=m.metric,
                target=m.target,
                measurement_method=m.measurement_method,
            )
            for m in (d.domain_metrics or [])
        ],
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@domains_api_bp.get("/")
async def list_domains(request: Request):
    """GET /api/v1/domains -- Paginated domain list with filtering.

    Query params: status, q (search domain_id/purpose),
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
        stmt = select(Domain).order_by(Domain.created_at.desc())

        if eco_ids:
            stmt = stmt.where(Domain.ecosystem_id.in_(eco_ids))

        status = request.args.get("status")
        if status:
            stmt = stmt.where(Domain.status == status)

        search = request.args.get("q")
        if search:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(
                or_(
                    Domain.domain_id.ilike(pattern),
                    Domain.purpose.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        domains = result.scalars().all()

    return json({
        "items": [_domain_to_list_item(d) for d in domains],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@domains_api_bp.get("/<domain_id:uuid>")
async def get_domain(request: Request, domain_id: uuid.UUID):
    """GET /api/v1/domains/:id -- Domain detail with elements and metrics."""
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(Domain)
            .options(
                selectinload(Domain.domain_elements),
                selectinload(Domain.domain_metrics),
            )
            .where(Domain.id == domain_id)
        )
        if eco_ids:
            stmt = stmt.where(Domain.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        d = result.scalar_one_or_none()

    if d is None:
        return json({"error": "Domain not found"}, status=404)

    return json(_domain_to_detail(d))


@domains_api_bp.post("/")
async def create_domain(request: Request):
    """POST /api/v1/domains -- Create a new domain.

    Accepts JSON: DomainCreateRequest
    Returns JSON: DomainDetail with 201 status.
    """
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = DomainCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    domain_id_str = f"DOM-{short_id}"

    async with request.app.ctx.db() as session:
        domain = Domain(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            domain_id=domain_id_str,
            version="1.0",
            status="active",
            purpose=create_req.purpose,
            current_steward=create_req.current_steward,
            steward_id=create_req.steward_id,
            parent_domain_id=create_req.parent_domain_id,
            created_by=create_req.created_by,
            metric_definitions=create_req.metric_definitions,
            elements=create_req.elements,
        )
        session.add(domain)
        await session.commit()

        # Reload with relationships
        stmt = (
            select(Domain)
            .options(
                selectinload(Domain.domain_elements),
                selectinload(Domain.domain_metrics),
            )
            .where(Domain.id == domain.id)
        )
        result = await session.execute(stmt)
        domain = result.scalar_one()

    return json(_domain_to_detail(domain), status=201)


@domains_api_bp.put("/<domain_id:uuid>")
async def update_domain(request: Request, domain_id: uuid.UUID):
    """PUT /api/v1/domains/:id -- Update non-None fields of a domain."""
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = DomainUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(Domain).where(Domain.id == domain_id)
        if eco_ids:
            stmt = stmt.where(Domain.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        d = result.scalar_one_or_none()
        if d is None:
            return json({"error": "Domain not found"}, status=404)

        update_data = update_req.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(d, field, value)

        await session.commit()

        # Reload with relationships
        stmt = (
            select(Domain)
            .options(
                selectinload(Domain.domain_elements),
                selectinload(Domain.domain_metrics),
            )
            .where(Domain.id == d.id)
        )
        result = await session.execute(stmt)
        d = result.scalar_one()

    return json(_domain_to_detail(d))
