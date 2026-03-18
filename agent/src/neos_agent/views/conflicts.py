"""Conflict resolution views for the NEOS dashboard (Layer VI).

Blueprint: conflicts_bp, url_prefix="/dashboard/conflicts"

Handles escalation triage, conflict case management, NVC dialogue tracking,
harm circles, and repair agreements. Supports AI-guided facilitation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func, or_

from neos_agent.db.models import ConflictCase, RepairAgreementRecord
from neos_agent.messaging.queries import get_entity_discussions
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id, escape_like

logger = logging.getLogger(__name__)

conflicts_bp = Blueprint("conflicts", url_prefix="/dashboard/conflicts")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to a ConflictCase select statement."""
    if eco_ids:
        stmt = stmt.where(ConflictCase.ecosystem_id.in_(eco_ids))

    status = request.args.get("status")
    if status:
        stmt = stmt.where(ConflictCase.status == status)

    severity = request.args.get("severity")
    if severity:
        stmt = stmt.where(ConflictCase.severity == severity)

    tier = request.args.get("tier")
    if tier:
        try:
            stmt = stmt.where(ConflictCase.tier == int(tier))
        except (ValueError, TypeError):
            pass

    search = request.args.get("q")
    if search:
        pattern = f"%{escape_like(search)}%"
        stmt = stmt.where(
            or_(
                ConflictCase.case_id.ilike(pattern),
                ConflictCase.triage_notes.ilike(pattern),
            )
        )

    return stmt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@conflicts_bp.get("/")
async def list_conflicts(request: Request):
    """GET /dashboard/conflicts -- list conflict cases with filtering."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(ConflictCase).order_by(ConflictCase.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            conflicts = result.scalars().all()
    except Exception:
        logger.exception("Failed to load conflicts list")
        conflicts = []
        total = 0

    content = await render(
        "dashboard/conflicts/list.html",
        request=request,
        conflicts=conflicts,
        total=total,
        offset=offset,
        limit=limit,
        filters=dict(request.args),
        active_page="conflicts",
    )
    return html(content)


@conflicts_bp.get("/new")
async def create_form(request: Request):
    """GET /dashboard/conflicts/new -- render triage/intake form."""
    content = await render(
        "dashboard/conflicts/form.html",
        request=request,
        conflict=None,
        active_page="conflicts",
    )
    return html(content)


@conflicts_bp.post("/")
async def create_conflict(request: Request):
    """POST /dashboard/conflicts -- create conflict case from triage form."""
    form = request.form
    eco_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if eco_id is None:
        content = await render(
            "dashboard/conflicts/form.html",
            request=request,
            conflict=None,
            active_page="conflicts",
            error="Invalid or unauthorised ecosystem.",
        )
        return html(content, status=403)
    try:
        case_id = f"CONF-{uuid.uuid4().hex[:8].upper()}"
        async with request.app.ctx.db() as session:
            conflict = ConflictCase(
                id=uuid.uuid4(),
                ecosystem_id=eco_id,
                case_id=case_id,
                title=form.get("triage_notes", "")[:100] or "Untitled conflict",
                status="open",
                severity=form.get("severity", "medium"),
                scope=form.get("scope", "interpersonal"),
                tier=int(form.get("tier", 1)),
                safety_flag=form.get("safety_flag") == "on",
                parties=[],
                triage_notes=form.get("triage_notes"),
            )
            session.add(conflict)
            await session.commit()
            new_id = conflict.id
    except Exception:
        logger.exception("Failed to create conflict case")
        content = await render(
            "dashboard/conflicts/form.html",
            request=request,
            conflict=None,
            error="Failed to create conflict case.",
            active_page="conflicts",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/conflicts/{new_id}")


@conflicts_bp.get("/<conflict_uuid:uuid>")
async def detail(request: Request, conflict_uuid: uuid.UUID):
    """GET /dashboard/conflicts/{id} -- conflict detail view."""
    try:
        async with request.app.ctx.db() as session:
            conflict = await get_scoped_entity(session, ConflictCase, conflict_uuid, request)
            if conflict is None:
                content = await render(
                    "dashboard/conflicts/detail.html",
                    request=request,
                    conflict=None,
                    error="Conflict case not found.",
                    active_page="conflicts",
                )
                return html(content, status=404)

            # Load repair agreements linked to this conflict
            repairs_result = await session.execute(
                select(RepairAgreementRecord)
                .where(RepairAgreementRecord.conflict_case_id == conflict_uuid)
                .order_by(RepairAgreementRecord.created_at.desc())
            )
            repairs = repairs_result.scalars().all()
    except Exception:
        logger.exception("Failed to load conflict detail")
        content = await render(
            "dashboard/conflicts/detail.html",
            request=request,
            conflict=None,
            error="Failed to load conflict case.",
            active_page="conflicts",
        )
        return html(content, status=500)

    discussions = []
    try:
        async with request.app.ctx.db() as session:
            discussions = await get_entity_discussions(session, "conflict", conflict_uuid)
    except Exception:
        pass

    content = await render(
        "dashboard/conflicts/detail.html",
        request=request,
        conflict=conflict,
        repairs=repairs,
        discussions=discussions,
        active_page="conflicts",
    )
    return html(content)


@conflicts_bp.post("/<conflict_uuid:uuid>/status")
async def status_transition(request: Request, conflict_uuid: uuid.UUID):
    """POST /dashboard/conflicts/{id}/status -- transition conflict status."""
    form = request.form
    new_status = form.get("new_status")

    if not new_status:
        return html(
            await render(
                "dashboard/conflicts/detail.html",
                request=request,
                conflict=None,
                error="new_status is required.",
                active_page="conflicts",
            ),
            status=400,
        )

    try:
        async with request.app.ctx.db() as session:
            conflict = await get_scoped_entity(session, ConflictCase, conflict_uuid, request)
            if conflict is None:
                return html(
                    await render(
                        "dashboard/conflicts/detail.html",
                        request=request,
                        conflict=None,
                        error="Conflict case not found.",
                        active_page="conflicts",
                    ),
                    status=404,
                )

            old_status = conflict.status
            conflict.status = new_status

            if new_status == "resolved":
                conflict.resolution_summary = form.get("resolution_summary", "")
                conflict.resolved_date = datetime.utcnow().date()

            await session.commit()
            logger.info(
                "Conflict %s status: %s -> %s",
                conflict_uuid, old_status, new_status,
            )
    except Exception:
        logger.exception("Failed to transition conflict status")
        return html(
            await render(
                "dashboard/conflicts/detail.html",
                request=request,
                conflict=None,
                error="Failed to update status.",
                active_page="conflicts",
            ),
            status=500,
        )

    return redirect(f"/dashboard/conflicts/{conflict_uuid}")


@conflicts_bp.get("/filter")
async def filter_conflicts(request: Request):
    """GET /dashboard/conflicts/filter -- htmx filtered conflict list fragment."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(ConflictCase).order_by(ConflictCase.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            conflicts = result.scalars().all()
    except Exception:
        logger.exception("Failed to filter conflicts")
        conflicts = []
        total = 0

    fragment = await render(
        "dashboard/conflicts/_list_rows.html",
        request=request,
        conflicts=conflicts,
        total=total,
        offset=offset,
        limit=limit,
    )
    return html(fragment)
