"""Conflict resolution views for the NEOS dashboard (Layer VI).

Blueprint: conflicts_bp, url_prefix="/dashboard/conflicts"

Read-only: a case shows only to the people `policy.can_view_conflict` allows (404 otherwise);
writes are retired (410). See api/AGENTS.md "Legacy dashboard (views/)".
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, html
from sanic.request import Request
from sqlalchemy import select, or_

from neos_agent.api import policy
from neos_agent.api.guards import caller_in
from neos_agent.db.models import ConflictCase, RepairAgreementRecord
from neos_agent.messaging.queries import get_entity_discussions
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, escape_like, retired_write

logger = logging.getLogger(__name__)

conflicts_bp = Blueprint("conflicts", url_prefix="/dashboard/conflicts")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to a ConflictCase select statement; an empty scope matches nothing."""
    stmt = stmt.where(ConflictCase.ecosystem_id.in_(eco_ids or []))

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


async def _visible_page(session, request: Request) -> tuple[list, int, int, int]:
    """The filtered cases the caller may read (same rule as the API), one page of them, and the total."""
    offset, limit = parse_pagination(request)
    stmt = _apply_filters(
        select(ConflictCase).order_by(ConflictCase.created_at.desc()), request,
        eco_ids=get_selected_ecosystem_ids(request),
    )
    cases = (await session.execute(stmt)).scalars().all()
    callers = {eco_id: await caller_in(session, request, eco_id) for eco_id in {c.ecosystem_id for c in cases}}
    visible = [case for case in cases if policy.can_view_conflict(callers[case.ecosystem_id], case)]
    return visible[offset:offset + limit], len(visible), offset, limit


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@conflicts_bp.get("/")
async def list_conflicts(request: Request):
    """GET /dashboard/conflicts -- the cases the caller may read, filtered."""
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            conflicts, total, offset, limit = await _visible_page(session, request)
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
    """POST /dashboard/conflicts -- retired (410): writes happen in the app."""
    return retired_write(request, "/conflicts/new")


@conflicts_bp.get("/<conflict_uuid:uuid>")
async def detail(request: Request, conflict_uuid: uuid.UUID):
    """GET /dashboard/conflicts/{id} -- conflict detail view."""
    try:
        async with request.app.ctx.db() as session:
            conflict = await get_scoped_entity(session, ConflictCase, conflict_uuid, request)
            if conflict is not None and not policy.can_view_conflict(
                await caller_in(session, request, conflict.ecosystem_id), conflict,
            ):
                conflict = None  # not a reader: indistinguishable from a missing case
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
    """POST /dashboard/conflicts/{id}/status -- retired (410): writes happen in the app."""
    return retired_write(request, f"/conflicts/{conflict_uuid}")


@conflicts_bp.get("/filter")
async def filter_conflicts(request: Request):
    """GET /dashboard/conflicts/filter -- htmx fragment of the cases the caller may read."""
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            conflicts, total, offset, limit = await _visible_page(session, request)
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
