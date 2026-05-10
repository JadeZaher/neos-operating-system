"""JSON API blueprint for governance safeguards & health monitoring.

Blueprint: safeguards_api_bp, url_prefix="/api/v1/safeguards"

AI-powered capture risk detection, governance health metrics,
and audit trail management.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import re
import uuid
import datetime as _dt
from typing import Optional

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import GovernanceHealthAudit
from neos_agent.api.helpers import require_auth, get_ecosystem_ids, apply_ecosystem_filter, apply_ecosystem_name_filter, build_search_filter
from neos_agent.api.schemas.safeguards import AuditCreateRequest, AuditDetail, AuditListItem, HealthSummary

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

safeguards_api_bp = Blueprint("safeguards_api", url_prefix="/api/v1/safeguards")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _audit_to_list_item(a: GovernanceHealthAudit) -> dict:
    return AuditListItem(
        id=a.id,
        audit_id=a.audit_id,
        audit_date=a.audit_date,
        auditor=a.auditor,
        overall_health_score=a.overall_health_score,
        status=a.status,
        created_at=a.created_at,
    ).model_dump(mode="json")


def _audit_to_detail(a: GovernanceHealthAudit) -> dict:
    return AuditDetail(
        id=a.id,
        audit_id=a.audit_id,
        audit_date=a.audit_date,
        auditor=a.auditor,
        overall_health_score=a.overall_health_score,
        status=a.status,
        created_at=a.created_at,
        ecosystem_id=a.ecosystem_id,
        capture_risk_indicators=a.capture_risk_indicators,
        findings=a.findings,
        recommendations=a.recommendations,
        next_audit_date=a.next_audit_date,
        updated_at=a.updated_at,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@safeguards_api_bp.get("/")
async def health_summary(request: Request):
    """GET /api/v1/safeguards -- latest audit + health metrics summary.

    Returns the most recent audit details and aggregate counts
    across all selected ecosystems.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        base_stmt = select(GovernanceHealthAudit).order_by(
            GovernanceHealthAudit.audit_date.desc()
        )
        if eco_ids:
            base_stmt = apply_ecosystem_filter(base_stmt, GovernanceHealthAudit, eco_ids)

        # Latest audit
        latest_stmt = base_stmt.limit(1)
        latest_result = await session.execute(latest_stmt)
        latest_audit = latest_result.scalar_one_or_none()

        # Total count across all selected ecosystems
        count_base = select(func.count()).select_from(base_stmt.subquery())
        total = await session.scalar(count_base) or 0

    summary = HealthSummary(
        latest_audit=_audit_to_detail(latest_audit) if latest_audit else None,
        total_audits=total,
        latest_health_score=latest_audit.overall_health_score if latest_audit else None,
    )

    return json(summary.model_dump(mode="json"))


@safeguards_api_bp.get("/audits")
async def list_audits(request: Request):
    """GET /api/v1/safeguards/audits -- paginated audit list.

    Query params: status, q, page (default 1), per_page (default 25, max 100).
    Lists audits across all selected ecosystems.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(GovernanceHealthAudit).order_by(
            GovernanceHealthAudit.audit_date.desc()
        )
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, GovernanceHealthAudit, eco_ids)
        stmt = apply_ecosystem_name_filter(stmt, GovernanceHealthAudit, request)

        status = request.args.get("status")
        if status:
            stmt = stmt.where(GovernanceHealthAudit.status == status)

        search = request.args.get("q")
        if search:
            stmt = stmt.where(build_search_filter(
                GovernanceHealthAudit, search,
                GovernanceHealthAudit.auditor, GovernanceHealthAudit.audit_id,
            ))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        audits = result.scalars().all()

    return json({
        "items": [_audit_to_list_item(a) for a in audits],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@safeguards_api_bp.get("/audits/<audit_id:uuid>")
async def get_audit(request: Request, audit_id: uuid.UUID):
    """GET /api/v1/safeguards/audits/:id -- audit detail."""
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(GovernanceHealthAudit).where(
            GovernanceHealthAudit.id == audit_id
        )
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, GovernanceHealthAudit, eco_ids)

        result = await session.execute(stmt)
        audit = result.scalar_one_or_none()

    if audit is None:
        return json({"error": "Audit not found"}, status=404)

    return json(_audit_to_detail(audit))


@safeguards_api_bp.post("/audits")
async def request_audit(request: Request):
    """POST /api/v1/safeguards/audits -- request a new governance health audit.

    Accepts JSON: AuditCreateRequest
    Creates a pending audit record. The AI agent fills in results asynchronously.
    Returns JSON: AuditDetail with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = AuditCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    audit_id_str = f"AUDIT-{short_id}"

    async with request.app.ctx.db() as session:
        audit = GovernanceHealthAudit(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            audit_id=audit_id_str,
            audit_date=_dt.date.today(),
            auditor=create_req.auditor,
            capture_risk_indicators={},
            overall_health_score=None,
            findings="Audit requested. AI analysis pending.",
            recommendations={},
            status="draft",
        )
        session.add(audit)
        await session.commit()

        # Reload for response
        stmt = select(GovernanceHealthAudit).where(
            GovernanceHealthAudit.id == audit.id
        )
        result = await session.execute(stmt)
        audit = result.scalar_one()

    return json(_audit_to_detail(audit), status=201)
