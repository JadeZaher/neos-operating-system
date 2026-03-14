"""Decision record browsing and search views for the NEOS dashboard.

Blueprint: decisions_bp, url_prefix="/dashboard/decisions"

Provides read-only browsing and full-text search over the governance
decision registry (Layer IX memory trace). Decision records are the
permanent institutional memory of the ecosystem.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, html
from sanic.request import Request
from sqlalchemy import select, func, or_

from neos_agent.db.models import (
    DecisionRecord,
    DecisionDissentRecord,
    DecisionParticipant,
    DecisionSemanticTag,
)
from neos_agent.views._rendering import render, html_fragment, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity

logger = logging.getLogger(__name__)

decisions_bp = Blueprint("decisions", url_prefix="/dashboard/decisions")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to a DecisionRecord select."""
    if eco_ids:
        stmt = stmt.where(DecisionRecord.ecosystem_id.in_(eco_ids))

    status = request.args.get("status")
    if status:
        stmt = stmt.where(DecisionRecord.status == status)

    domain = request.args.get("domain")
    if domain:
        stmt = stmt.where(DecisionRecord.domain.ilike(f"%{domain}%"))

    source_layer = request.args.get("source_layer")
    if source_layer:
        try:
            stmt = stmt.where(DecisionRecord.source_layer == int(source_layer))
        except ValueError:
            pass

    precedent_level = request.args.get("precedent_level")
    if precedent_level:
        stmt = stmt.where(DecisionRecord.precedent_level == precedent_level)

    artifact_type = request.args.get("artifact_type")
    if artifact_type:
        stmt = stmt.where(DecisionRecord.artifact_type == artifact_type)

    search = request.args.get("q")
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                DecisionRecord.record_id.ilike(pattern),
                DecisionRecord.holding.ilike(pattern),
                DecisionRecord.ratio_decidendi.ilike(pattern),
                DecisionRecord.domain.ilike(pattern),
                DecisionRecord.source_skill.ilike(pattern),
            )
        )

    return stmt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@decisions_bp.get("/")
async def browse_decisions(request: Request):
    """GET /dashboard/decisions -- browse decisions with filtering."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(DecisionRecord).order_by(DecisionRecord.date.desc().nulls_last())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            decisions = result.scalars().all()
    except Exception:
        logger.exception("Failed to load decisions")
        decisions = []
        total = 0

    content = await render(
        "dashboard/decisions/list.html",
        request=request,
        decisions=decisions,
        total=total,
        offset=offset,
        limit=limit,
        filters=dict(request.args),
        active_page="decisions",
    )
    return html(content)


@decisions_bp.get("/search")
async def search_view(request: Request):
    """GET /dashboard/decisions/search -- render search page."""
    offset, limit = parse_pagination(request)
    content = await render(
        "dashboard/decisions/list.html",
        request=request,
        decisions=[],
        total=0,
        offset=offset,
        limit=limit,
        filters={},
        search_mode=True,
    )
    return html(content)


@decisions_bp.get("/search/results")
async def search_results(request: Request):
    """GET /dashboard/decisions/search/results -- htmx search results fragment."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(DecisionRecord).order_by(DecisionRecord.date.desc().nulls_last())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            decisions = result.scalars().all()
    except Exception:
        logger.exception("Failed to search decisions")
        decisions = []
        total = 0

    fragment = await render(
        "dashboard/decisions/_list_rows.html",
        request=request,
        decisions=decisions,
        total=total,
        offset=offset,
        limit=limit,
    )
    return html_fragment(fragment)


@decisions_bp.get("/<decision_id:uuid>")
async def detail(request: Request, decision_id: uuid.UUID):
    """GET /dashboard/decisions/{decision_id} -- decision detail view."""
    try:
        async with request.app.ctx.db() as session:
            decision = await get_scoped_entity(session, DecisionRecord, decision_id, request)
            if decision is None:
                content = await render(
                    "dashboard/decisions/detail.html",
                    request=request,
                    decision=None,
                    error="Decision record not found.",
                )
                return html(content, status=404)

            # Load dissent records
            dissents_result = await session.execute(
                select(DecisionDissentRecord)
                .where(DecisionDissentRecord.decision_record_id == decision_id)
            )
            dissents = dissents_result.scalars().all()

            # Load participants
            participants_result = await session.execute(
                select(DecisionParticipant)
                .where(DecisionParticipant.decision_record_id == decision_id)
            )
            participants = participants_result.scalars().all()

            # Load semantic tags
            tags_result = await session.execute(
                select(DecisionSemanticTag)
                .where(DecisionSemanticTag.decision_record_id == decision_id)
            )
            tags = tags_result.scalars().all()
    except Exception:
        logger.exception("Failed to load decision detail")
        content = await render(
            "dashboard/decisions/detail.html",
            request=request,
            decision=None,
            error="Failed to load decision record.",
        )
        return html(content, status=500)

    content = await render(
        "dashboard/decisions/detail.html",
        request=request,
        decision=decision,
        dissents=dissents,
        participants=participants,
        semantic_tags=tags,
    )
    return html(content)
