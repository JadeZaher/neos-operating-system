"""Agreement CRUD views for the NEOS dashboard.

Blueprint: agreements_bp, url_prefix="/dashboard/agreements"

Handles listing, creation, detail, editing, status transitions,
and amendment history for governance agreements. Supports both
full-page HTML rendering and htmx filtered fragments.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func, or_

from neos_agent.db.models import (
    Agreement,
    AmendmentRecord,
    ReviewRecord,
    AgreementRatificationRecord,
)
from neos_agent.messaging.queries import get_entity_discussions
from neos_agent.views._rendering import render, html_fragment, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id

logger = logging.getLogger(__name__)

agreements_bp = Blueprint("agreements", url_prefix="/dashboard/agreements")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to an Agreement select statement."""
    if eco_ids:
        stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

    agreement_type = request.args.get("type")
    if agreement_type:
        stmt = stmt.where(Agreement.type == agreement_type)

    status = request.args.get("status")
    if status:
        stmt = stmt.where(Agreement.status == status)

    domain = request.args.get("domain")
    if domain:
        stmt = stmt.where(Agreement.domain.ilike(f"%{domain}%"))

    search = request.args.get("q")
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Agreement.title.ilike(pattern),
                Agreement.agreement_id.ilike(pattern),
            )
        )

    return stmt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@agreements_bp.get("/")
async def list_agreements(request: Request):
    """GET /dashboard/agreements -- list agreements with optional filtering."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(Agreement).order_by(Agreement.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            # Total count for pagination
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            # Paginated results
            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            agreements = result.scalars().all()
    except Exception:
        logger.exception("Failed to load agreements list")
        agreements = []
        total = 0

    content = await render(
        "dashboard/agreements/list.html",
        request=request,
        agreements=agreements,
        total=total,
        offset=offset,
        limit=limit,
        filters=dict(request.args),
        active_page="agreements",
    )
    return html(content)


@agreements_bp.get("/new")
async def create_form(request: Request):
    """GET /dashboard/agreements/new -- render create form."""
    content = await render("dashboard/agreements/form.html", request=request, agreement=None)
    return html(content)


@agreements_bp.post("/")
async def create_agreement(request: Request):
    """POST /dashboard/agreements -- create agreement from form data."""
    form = request.form
    eco_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if eco_id is None:
        content = await render(
            "dashboard/agreements/form.html",
            request=request,
            agreement=None,
            error="Invalid or unauthorized ecosystem.",
        )
        return html(content, status=403)
    try:
        async with request.app.ctx.db() as session:
            agreement = Agreement(
                id=uuid.uuid4(),
                ecosystem_id=eco_id,
                agreement_id=form.get("agreement_id", ""),
                type=form.get("type", "operational"),
                title=form.get("title", ""),
                version=form.get("version", "1.0"),
                status="draft",
                proposer=form.get("proposer"),
                domain=form.get("domain"),
                text=form.get("text"),
                hierarchy_level=form.get("hierarchy_level", "domain"),
                created_date=date.today(),
            )
            session.add(agreement)
            await session.commit()
            agreement_id = agreement.id
    except Exception:
        logger.exception("Failed to create agreement")
        content = await render(
            "dashboard/agreements/form.html",
            request=request,
            agreement=None,
            error="Failed to create agreement. Please check your input and try again.",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/agreements/{agreement_id}")


@agreements_bp.get("/<agreement_id:uuid>")
async def detail(request: Request, agreement_id: uuid.UUID):
    """GET /dashboard/agreements/{agreement_id} -- detail view."""
    try:
        async with request.app.ctx.db() as session:
            agreement = await get_scoped_entity(session, Agreement, agreement_id, request)
            if agreement is None:
                content = await render(
                    "dashboard/agreements/detail.html",
                    request=request,
                    agreement=None,
                    error="Agreement not found.",
                )
                return html(content, status=404)
    except Exception:
        logger.exception("Failed to load agreement detail")
        content = await render(
            "dashboard/agreements/detail.html",
            request=request,
            agreement=None,
            error="Failed to load agreement.",
        )
        return html(content, status=500)

    discussions = []
    try:
        async with request.app.ctx.db() as session:
            discussions = await get_entity_discussions(session, "agreement", agreement_id)
    except Exception:
        pass

    content = await render("dashboard/agreements/detail.html", request=request, agreement=agreement, discussions=discussions)
    return html(content)


@agreements_bp.get("/<agreement_id:uuid>/edit")
async def edit_form(request: Request, agreement_id: uuid.UUID):
    """GET /dashboard/agreements/{agreement_id}/edit -- render edit form."""
    try:
        async with request.app.ctx.db() as session:
            agreement = await get_scoped_entity(session, Agreement, agreement_id, request)
            if agreement is None:
                return html(
                    await render(
                        "dashboard/agreements/form.html",
                        request=request,
                        agreement=None,
                        error="Agreement not found.",
                    ),
                    status=404,
                )
    except Exception:
        logger.exception("Failed to load agreement for editing")
        return html(
            await render(
                "dashboard/agreements/form.html",
                request=request,
                agreement=None,
                error="Failed to load agreement.",
            ),
            status=500,
        )

    content = await render("dashboard/agreements/form.html", request=request, agreement=agreement)
    return html(content)


@agreements_bp.post("/<agreement_id:uuid>")
async def update_agreement(request: Request, agreement_id: uuid.UUID):
    """POST /dashboard/agreements/{agreement_id} -- update agreement."""
    form = request.form
    try:
        async with request.app.ctx.db() as session:
            agreement = await get_scoped_entity(session, Agreement, agreement_id, request)
            if agreement is None:
                return html(
                    await render(
                        "dashboard/agreements/detail.html",
                        request=request,
                        agreement=None,
                        error="Agreement not found.",
                    ),
                    status=404,
                )

            # Update mutable fields
            if form.get("title"):
                agreement.title = form.get("title")
            if form.get("type"):
                agreement.type = form.get("type")
            if form.get("domain"):
                agreement.domain = form.get("domain")
            if form.get("text"):
                agreement.text = form.get("text")
            if form.get("hierarchy_level"):
                agreement.hierarchy_level = form.get("hierarchy_level")
            if form.get("version"):
                agreement.version = form.get("version")
            if form.get("review_date"):
                agreement.review_date = date.fromisoformat(form.get("review_date"))
            if form.get("sunset_date"):
                agreement.sunset_date = date.fromisoformat(form.get("sunset_date"))

            await session.commit()
    except Exception:
        logger.exception("Failed to update agreement")
        return html(
            await render(
                "dashboard/agreements/form.html",
                request=request,
                agreement=None,
                error="Failed to update agreement.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/agreements/{agreement_id}")


@agreements_bp.post("/<agreement_id:uuid>/status")
async def status_transition(request: Request, agreement_id: uuid.UUID):
    """POST /dashboard/agreements/{agreement_id}/status -- transition status.

    Requires form fields: new_status, reason.
    """
    form = request.form
    new_status = form.get("new_status")
    reason = form.get("reason", "")

    if not new_status:
        return html(
            await render(
                "dashboard/agreements/detail.html",
                request=request,
                agreement=None,
                error="new_status is required for status transition.",
            ),
            status=400,
        )

    try:
        async with request.app.ctx.db() as session:
            agreement = await get_scoped_entity(session, Agreement, agreement_id, request)
            if agreement is None:
                return html(
                    await render(
                        "dashboard/agreements/detail.html",
                        request=request,
                        agreement=None,
                        error="Agreement not found.",
                    ),
                    status=404,
                )

            old_status = agreement.status
            agreement.status = new_status

            # If ratifying, set ratification date
            if new_status == "ratified" and agreement.ratification_date is None:
                agreement.ratification_date = date.today()

            await session.commit()
            logger.info(
                "Agreement %s status: %s -> %s (reason: %s)",
                agreement_id, old_status, new_status, reason,
            )
    except Exception:
        logger.exception("Failed to transition agreement status")
        return html(
            await render(
                "dashboard/agreements/detail.html",
                request=request,
                agreement=None,
                error="Failed to update agreement status.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/agreements/{agreement_id}")


@agreements_bp.get("/<agreement_id:uuid>/history")
async def history(request: Request, agreement_id: uuid.UUID):
    """GET /dashboard/agreements/{agreement_id}/history -- amendment history."""
    try:
        async with request.app.ctx.db() as session:
            agreement = await get_scoped_entity(session, Agreement, agreement_id, request)
            if agreement is None:
                return html(
                    await render(
                        "dashboard/agreements/detail.html",
                        request=request,
                        agreement=None,
                        error="Agreement not found.",
                    ),
                    status=404,
                )

            # Load amendments
            amendments_result = await session.execute(
                select(AmendmentRecord)
                .where(AmendmentRecord.parent_agreement_id == agreement_id)
                .order_by(AmendmentRecord.date.desc())
            )
            amendments = amendments_result.scalars().all()

            # Load reviews
            reviews_result = await session.execute(
                select(ReviewRecord)
                .where(ReviewRecord.agreement_id == agreement_id)
                .order_by(ReviewRecord.date.desc())
            )
            reviews = reviews_result.scalars().all()

            # Load ratification records
            ratifications_result = await session.execute(
                select(AgreementRatificationRecord)
                .where(AgreementRatificationRecord.agreement_id == agreement_id)
                .order_by(AgreementRatificationRecord.date.desc())
            )
            ratifications = ratifications_result.scalars().all()
    except Exception:
        logger.exception("Failed to load agreement history")
        return html(
            await render(
                "dashboard/agreements/detail.html",
                request=request,
                agreement=None,
                error="Failed to load agreement history.",
            ),
            status=500,
        )

    content = await render(
        "dashboard/agreements/detail.html",
        request=request,
        agreement=agreement,
        amendments=amendments,
        reviews=reviews,
        ratifications=ratifications,
        show_history=True,
    )
    return html(content)


@agreements_bp.get("/filter")
async def filter_agreements(request: Request):
    """GET /dashboard/agreements/filter -- htmx filtered agreement list fragment."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(Agreement).order_by(Agreement.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            agreements = result.scalars().all()
    except Exception:
        logger.exception("Failed to filter agreements")
        agreements = []
        total = 0

    fragment = await render(
        "dashboard/agreements/_list_rows.html",
        request=request,
        agreements=agreements,
        total=total,
        offset=offset,
        limit=limit,
    )
    return html_fragment(fragment)
