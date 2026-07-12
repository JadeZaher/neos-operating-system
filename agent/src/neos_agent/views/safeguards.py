"""Governance safeguards & health monitoring views (Layer VII).

Blueprint: safeguards_bp, url_prefix="/dashboard/safeguards"

AI-powered capture risk detection, governance health metrics,
and audit trail viewing.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func

from neos_agent.db.models import GovernanceHealthAudit
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id, escape_like

logger = logging.getLogger(__name__)

safeguards_bp = Blueprint("safeguards", url_prefix="/dashboard/safeguards")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply ecosystem scoping and optional filters to a query."""
    if eco_ids:
        stmt = stmt.where(GovernanceHealthAudit.ecosystem_id.in_(eco_ids))
    return stmt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@safeguards_bp.get("/")
async def dashboard(request: Request):
    """GET /dashboard/safeguards -- safeguards overview with health metrics."""
    eco_ids = get_selected_ecosystem_ids(request)
    try:
        async with request.app.ctx.db() as session:
            # Get the latest audit
            latest_stmt = select(GovernanceHealthAudit).order_by(
                GovernanceHealthAudit.audit_date.desc()
            )
            latest_stmt = _apply_filters(latest_stmt, request, eco_ids)
            latest_stmt = latest_stmt.limit(1)
            latest_result = await session.execute(latest_stmt)
            latest_audit = latest_result.scalar_one_or_none()

            # Get recent audits for trend
            recent_stmt = select(GovernanceHealthAudit).order_by(
                GovernanceHealthAudit.audit_date.desc()
            )
            recent_stmt = _apply_filters(recent_stmt, request, eco_ids)
            recent_stmt = recent_stmt.limit(10)
            recent_result = await session.execute(recent_stmt)
            recent_audits = recent_result.scalars().all()

            # Total audits count
            count_base = select(func.count()).select_from(GovernanceHealthAudit)
            count_base = _apply_filters(count_base, request, eco_ids)
            total = await session.scalar(count_base) or 0
    except Exception:
        logger.exception("Failed to load safeguards dashboard")
        latest_audit = None
        recent_audits = []
        total = 0

    content = await render(
        "dashboard/safeguards/dashboard.html",
        request=request,
        latest_audit=latest_audit,
        recent_audits=recent_audits,
        total=total,
        active_page="safeguards",
    )
    return html(content)


@safeguards_bp.get("/audits")
async def list_audits(request: Request):
    """GET /dashboard/safeguards/audits -- list all governance health audits."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(GovernanceHealthAudit).order_by(
                GovernanceHealthAudit.audit_date.desc()
            )
            stmt = _apply_filters(stmt, request, eco_ids)
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            audits = result.scalars().all()
    except Exception:
        logger.exception("Failed to load audits list")
        audits = []
        total = 0

    content = await render(
        "dashboard/safeguards/audits.html",
        request=request,
        audits=audits,
        total=total,
        offset=offset,
        limit=limit,
        active_page="safeguards",
    )
    return html(content)


@safeguards_bp.get("/audits/<audit_id:uuid>")
async def audit_detail(request: Request, audit_id: uuid.UUID):
    """GET /dashboard/safeguards/audits/{id} -- audit detail."""
    try:
        async with request.app.ctx.db() as session:
            audit = await get_scoped_entity(session, GovernanceHealthAudit, audit_id, request)
            if audit is None:
                content = await render(
                    "dashboard/safeguards/dashboard.html",
                    request=request,
                    latest_audit=None,
                    recent_audits=[],
                    error="Audit not found.",
                    active_page="safeguards",
                )
                return html(content, status=404)
    except Exception:
        logger.exception("Failed to load audit detail")
        content = await render(
            "dashboard/safeguards/dashboard.html",
            request=request,
            latest_audit=None,
            recent_audits=[],
            error="Failed to load audit.",
            active_page="safeguards",
        )
        return html(content, status=500)

    content = await render(
        "dashboard/safeguards/audit_detail.html",
        request=request,
        audit=audit,
        active_page="safeguards",
    )
    return html(content)


@safeguards_bp.post("/audits")
async def request_audit(request: Request):
    """POST /dashboard/safeguards/audits -- request a new governance health audit.

    Creates a pending audit record. The AI agent fills in the results
    asynchronously via the chat/tool interface.
    """
    form = request.form
    eco_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if eco_id is None:
        content = await render(
            "dashboard/safeguards/dashboard.html",
            request=request,
            active_page="safeguards",
            error="Invalid or unauthorised ecosystem.",
        )
        return html(content, status=403)
    try:
        async with request.app.ctx.db() as session:
            audit_id = f"AUDIT-{uuid.uuid4().hex[:8].upper()}"
            audit = GovernanceHealthAudit(
                id=uuid.uuid4(),
                ecosystem_id=eco_id,
                audit_id=audit_id,
                audit_date=date.today(),
                auditor=form.get("auditor", "AI Governance Agent"),
                capture_risk_indicators={},
                overall_health_score=None,
                findings="Audit requested. AI analysis pending.",
                recommendations={},
                status="draft",
            )
            session.add(audit)
            await session.commit()
            new_id = audit.id
    except Exception:
        logger.exception("Failed to create audit")
        content = await render(
            "dashboard/safeguards/dashboard.html",
            request=request,
            latest_audit=None,
            recent_audits=[],
            error="Failed to create audit.",
            active_page="safeguards",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/safeguards/audits/{new_id}")
