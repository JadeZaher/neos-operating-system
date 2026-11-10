"""Ecosystem directory views for NEOS.

Blueprint: ecosystems_bp, url_prefix="/ecosystems"

Public search/browse page for ecosystem discovery, plus authenticated
CRUD for creating and editing ecosystems.
"""

from __future__ import annotations

import logging
import uuid
from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func, or_

from neos_agent.db.models import Ecosystem, Member
from neos_agent.services.member_lifecycle import counts_as_member
from neos_agent.views._rendering import render, parse_pagination, escape_like, retired_write

logger = logging.getLogger(__name__)

ecosystems_bp = Blueprint("ecosystems", url_prefix="/ecosystems")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_auth(request: Request):
    """Return a redirect response if the user is not authenticated, else None."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return redirect("/auth/login")
    return None


def _get_filters(request: Request) -> dict:
    """Extract scalar filter values from request args."""
    return {
        "q": request.args.get("q", ""),
        "status": request.args.get("status", ""),
        "visibility": request.args.get("visibility", ""),
    }


def _apply_filters(stmt, request: Request):
    """Apply optional query-param filters to an Ecosystem select statement."""
    status = request.args.get("status")
    if status:
        stmt = stmt.where(Ecosystem.status == status)

    visibility = request.args.get("visibility")
    if visibility:
        stmt = stmt.where(Ecosystem.visibility == visibility)

    search = request.args.get("q")
    if search:
        pattern = f"%{escape_like(search)}%"
        stmt = stmt.where(
            or_(
                Ecosystem.name.ilike(pattern),
                Ecosystem.description.ilike(pattern),
                Ecosystem.location.ilike(pattern),
            )
        )

    return stmt


def _member_count_subquery():
    """Correlated count of active (consented) members. Pending, suspended, and departed rows are excluded."""
    return (
        select(func.count(Member.id))
        .where(Member.ecosystem_id == Ecosystem.id, counts_as_member())
        .correlate(Ecosystem)
        .scalar_subquery()
        .label("member_count")
    )


# ---------------------------------------------------------------------------
# Public Routes (no auth required)
# ---------------------------------------------------------------------------

@ecosystems_bp.get("/")
async def list_ecosystems(request: Request):
    """GET /ecosystems -- public search/browse page."""
    offset, limit = parse_pagination(request)
    member_count = _member_count_subquery()
    filters = _get_filters(request)

    try:
        async with request.app.ctx.db() as session:
            stmt = (
                select(Ecosystem, member_count)
                .order_by(Ecosystem.created_at.desc())
            )

            # Public visitors only see public ecosystems
            authed = getattr(request.ctx, "member", None)
            if not authed:
                stmt = stmt.where(Ecosystem.visibility == "public")

            stmt = _apply_filters(stmt, request)

            # Count query
            count_base = select(Ecosystem.id)
            if not authed:
                count_base = count_base.where(Ecosystem.visibility == "public")
            count_base = _apply_filters(count_base, request)
            count_stmt = select(func.count()).select_from(count_base.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            rows = result.all()

            ecosystems = []
            for row in rows:
                eco = row[0]
                eco._member_count = row[1]
                ecosystems.append(eco)
    except Exception:
        logger.exception("Failed to load ecosystems list")
        ecosystems = []
        total = 0

    selected_ids = [
        str(sid) for sid in
        getattr(getattr(request, "ctx", None), "selected_ecosystem_ids", [])
    ]

    content = await render(
        "ecosystems/list.html",
        request=request,
        ecosystems=ecosystems,
        total=total,
        offset=offset,
        limit=limit,
        filters=filters,
        selected_ids=selected_ids,
        active_page="ecosystems",
    )
    return html(content)


@ecosystems_bp.get("/<ecosystem_id:uuid>")
async def detail(request: Request, ecosystem_id: uuid.UUID):
    """GET /ecosystems/{id} -- public detail page."""
    member_count = _member_count_subquery()

    try:
        async with request.app.ctx.db() as session:
            result = await session.execute(
                select(Ecosystem, member_count).where(Ecosystem.id == ecosystem_id)
            )
            row = result.one_or_none()

            if row is None:
                content = await render(
                    "ecosystems/detail.html",
                    request=request,
                    ecosystem=None,
                    error="Ecosystem not found.",
                    active_page="ecosystems",
                )
                return html(content, status=404)

            ecosystem = row[0]
            ecosystem._member_count = row[1]

            # Check visibility for unauthenticated users
            authed = getattr(request.ctx, "member", None)
            if not authed and ecosystem.visibility != "public":
                content = await render(
                    "ecosystems/detail.html",
                    request=request,
                    ecosystem=None,
                    error="Ecosystem not found.",
                    active_page="ecosystems",
                )
                return html(content, status=404)

            content = await render(
                "ecosystems/detail.html",
                request=request,
                ecosystem=ecosystem,
                active_page="ecosystems",
            )
    except Exception:
        logger.exception("Failed to load ecosystem detail")
        content = await render(
            "ecosystems/detail.html",
            request=request,
            ecosystem=None,
            error="Failed to load ecosystem.",
            active_page="ecosystems",
        )
        return html(content, status=500)

    return html(content)


# ---------------------------------------------------------------------------
# Authenticated Routes
# ---------------------------------------------------------------------------

@ecosystems_bp.get("/new")
async def create_form(request: Request):
    """GET /ecosystems/new -- render create form (auth required)."""
    denied = _require_auth(request)
    if denied:
        return denied

    content = await render("ecosystems/form.html", request=request, ecosystem=None, active_page="ecosystems")
    return html(content)


@ecosystems_bp.post("/")
async def create_ecosystem(request: Request):
    """POST /ecosystems -- retired (410): writes happen in the app."""
    return retired_write(request, "/ecosystems/new")


@ecosystems_bp.get("/<ecosystem_id:uuid>/edit")
async def edit_form(request: Request, ecosystem_id: uuid.UUID):
    """GET /ecosystems/{id}/edit -- render edit form (auth required)."""
    denied = _require_auth(request)
    if denied:
        return denied

    try:
        async with request.app.ctx.db() as session:
            ecosystem = await session.get(Ecosystem, ecosystem_id)
            if ecosystem is None:
                return html(
                    await render(
                        "ecosystems/form.html",
                        request=request,
                        ecosystem=None,
                        error="Ecosystem not found.",
                        active_page="ecosystems",
                    ),
                    status=404,
                )

            # Verify the user is a member of this ecosystem
            member = request.ctx.member
            if not member:
                return redirect("/auth/login")

            from neos_agent.db.models import Member as MemberModel
            member_check = await session.execute(
                select(MemberModel).where(
                    MemberModel.did == member.did,
                    MemberModel.ecosystem_id == ecosystem_id,
                    MemberModel.current_status == "active",
                )
            )
            if member_check.scalar_one_or_none() is None:
                content = await render(
                    "ecosystems/form.html",
                    request=request,
                    ecosystem=None,
                    error="You do not have permission to edit this ecosystem.",
                    active_page="ecosystems",
                )
                return html(content, status=403)

            content = await render("ecosystems/form.html", request=request, ecosystem=ecosystem, active_page="ecosystems")
    except Exception:
        logger.exception("Failed to load ecosystem for editing")
        return html(
            await render(
                "ecosystems/form.html",
                request=request,
                ecosystem=None,
                error="Failed to load ecosystem.",
                active_page="ecosystems",
            ),
            status=500,
        )

    return html(content)


@ecosystems_bp.put("/<ecosystem_id:uuid>")
async def update_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """PUT /ecosystems/{id} -- retired (410): writes happen in the app."""
    return retired_write(request, f"/ecosystems/{ecosystem_id}/edit")


# POST handler for HTML form method override (browsers only send GET/POST)
@ecosystems_bp.post("/<ecosystem_id:uuid>")
async def update_ecosystem_post(request: Request, ecosystem_id: uuid.UUID):
    """POST /ecosystems/{id} -- retired (410): writes happen in the app."""
    return retired_write(request, f"/ecosystems/{ecosystem_id}/edit")
