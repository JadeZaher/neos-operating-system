"""Domain CRUD views for the NEOS dashboard.

Blueprint: domains_bp, url_prefix="/dashboard/domains"

Manages domains — the 11-element structural units that define
authority boundaries within an ecosystem. Each domain has a
steward, purpose, metrics, and delegated authority scope.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func, or_

from neos_agent.db.models import Domain, DomainElement, DomainMetric
from neos_agent.messaging.queries import get_entity_discussions
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id, escape_like

logger = logging.getLogger(__name__)

domains_bp = Blueprint("domains", url_prefix="/dashboard/domains")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to a Domain select statement."""
    if eco_ids:
        stmt = stmt.where(Domain.ecosystem_id.in_(eco_ids))

    status = request.args.get("status")
    if status:
        stmt = stmt.where(Domain.status == status)

    delegator = request.args.get("delegator")
    if delegator:
        stmt = stmt.where(Domain.created_by.ilike(f"%{escape_like(delegator)}%"))

    steward = request.args.get("steward")
    if steward:
        stmt = stmt.where(
            or_(
                Domain.current_steward.ilike(f"%{escape_like(steward)}%"),
                Domain.domain_id.ilike(f"%{escape_like(steward)}%"),
            )
        )

    search = request.args.get("q")
    if search:
        pattern = f"%{escape_like(search)}%"
        stmt = stmt.where(
            or_(
                Domain.domain_id.ilike(pattern),
                Domain.purpose.ilike(pattern),
                Domain.current_steward.ilike(pattern),
            )
        )

    return stmt


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@domains_bp.get("/")
async def list_domains(request: Request):
    """GET /dashboard/domains -- list domains with optional filtering."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(Domain).order_by(Domain.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            domains = result.scalars().all()
    except Exception:
        logger.exception("Failed to load domains list")
        domains = []
        total = 0

    content = await render(
        "dashboard/domains/list.html",
        request=request,
        domains=domains,
        total=total,
        offset=offset,
        limit=limit,
        filters=dict(request.args),
        active_page="domains",
    )
    return html(content)


@domains_bp.get("/new")
async def create_form(request: Request):
    """GET /dashboard/domains/new -- render create form."""
    content = await render("dashboard/domains/form.html", request=request, domain=None, active_page="domains")
    return html(content)


@domains_bp.post("/")
async def create_domain(request: Request):
    """POST /dashboard/domains -- create domain from form data."""
    form = request.form
    eco_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if eco_id is None:
        content = await render(
            "dashboard/domains/form.html",
            request=request,
            domain=None,
            error="Invalid or unauthorized ecosystem.",
        )
        return html(content, status=403)
    try:
        async with request.app.ctx.db() as session:
            domain = Domain(
                id=uuid.uuid4(),
                ecosystem_id=eco_id,
                domain_id=form.get("domain_id", ""),
                version=form.get("version", "1.0"),
                status="active",
                purpose=form.get("purpose"),
                current_steward=form.get("current_steward"),
                created_by=form.get("created_by"),
            )

            # Link steward by member UUID if provided
            steward_id = form.get("steward_id")
            if steward_id:
                try:
                    domain.steward_id = uuid.UUID(steward_id)
                except ValueError:
                    pass

            # Link parent domain if provided
            parent_id = form.get("parent_domain_id")
            if parent_id:
                try:
                    domain.parent_domain_id = uuid.UUID(parent_id)
                except ValueError:
                    pass

            session.add(domain)
            await session.commit()
            domain_id = domain.id
    except Exception:
        logger.exception("Failed to create domain")
        content = await render(
            "dashboard/domains/form.html",
            request=request,
            domain=None,
            error="Failed to create domain. Please check your input and try again.",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/domains/{domain_id}")


@domains_bp.get("/<domain_id:uuid>")
async def detail(request: Request, domain_id: uuid.UUID):
    """GET /dashboard/domains/{domain_id} -- detail view with 11 elements."""
    try:
        async with request.app.ctx.db() as session:
            domain = await get_scoped_entity(session, Domain, domain_id, request)
            if domain is None:
                content = await render(
                    "dashboard/domains/detail.html",
                    request=request,
                    domain=None,
                    error="Domain not found.",
                )
                return html(content, status=404)

            # Load related elements and metrics
            elements_result = await session.execute(
                select(DomainElement)
                .where(DomainElement.domain_id == domain_id)
                .order_by(DomainElement.element_name)
            )
            elements = elements_result.scalars().all()

            metrics_result = await session.execute(
                select(DomainMetric)
                .where(DomainMetric.domain_id == domain_id)
            )
            metrics = metrics_result.scalars().all()
    except Exception:
        logger.exception("Failed to load domain detail")
        content = await render(
            "dashboard/domains/detail.html",
            request=request,
            domain=None,
            error="Failed to load domain.",
        )
        return html(content, status=500)

    discussions = []
    try:
        async with request.app.ctx.db() as session:
            discussions = await get_entity_discussions(session, "domain", domain_id)
    except Exception:
        pass

    content = await render(
        "dashboard/domains/detail.html",
        request=request,
        domain=domain,
        elements=elements,
        metrics=metrics,
        discussions=discussions,
        active_page="domains",
    )
    return html(content)


@domains_bp.get("/<domain_id:uuid>/edit")
async def edit_form(request: Request, domain_id: uuid.UUID):
    """GET /dashboard/domains/{domain_id}/edit -- render edit form."""
    try:
        async with request.app.ctx.db() as session:
            domain = await get_scoped_entity(session, Domain, domain_id, request)
            if domain is None:
                return html(
                    await render(
                        "dashboard/domains/form.html",
                        request=request,
                        domain=None,
                        error="Domain not found.",
                    ),
                    status=404,
                )
    except Exception:
        logger.exception("Failed to load domain for editing")
        return html(
            await render(
                "dashboard/domains/form.html",
                request=request,
                domain=None,
                error="Failed to load domain.",
            ),
            status=500,
        )

    content = await render("dashboard/domains/form.html", request=request, domain=domain, active_page="domains")
    return html(content)


@domains_bp.put("/<domain_id:uuid>")
async def update_domain(request: Request, domain_id: uuid.UUID):
    """PUT /dashboard/domains/{domain_id} -- update domain."""
    form = request.form
    try:
        async with request.app.ctx.db() as session:
            domain = await get_scoped_entity(session, Domain, domain_id, request)
            if domain is None:
                return html(
                    await render(
                        "dashboard/domains/detail.html",
                        request=request,
                        domain=None,
                        error="Domain not found.",
                    ),
                    status=404,
                )

            if form.get("purpose"):
                domain.purpose = form.get("purpose")
            if form.get("current_steward"):
                domain.current_steward = form.get("current_steward")
            if form.get("status"):
                domain.status = form.get("status")
            if form.get("version"):
                domain.version = form.get("version")
            if form.get("created_by"):
                domain.created_by = form.get("created_by")

            steward_id = form.get("steward_id")
            if steward_id:
                try:
                    domain.steward_id = uuid.UUID(steward_id)
                except ValueError:
                    pass

            parent_id = form.get("parent_domain_id")
            if parent_id:
                try:
                    domain.parent_domain_id = uuid.UUID(parent_id)
                except ValueError:
                    pass

            await session.commit()
    except Exception:
        logger.exception("Failed to update domain")
        return html(
            await render(
                "dashboard/domains/form.html",
                request=request,
                domain=None,
                error="Failed to update domain.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/domains/{domain_id}")


@domains_bp.post("/<domain_id:uuid>")
async def update_domain_post(request: Request, domain_id: uuid.UUID):
    """POST /dashboard/domains/{id} — delegates to PUT for HTML form compat."""
    return await update_domain(request, domain_id)
