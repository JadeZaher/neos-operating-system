"""Member directory views for the NEOS dashboard.

Blueprint: members_bp, url_prefix="/dashboard/members"

Manages the Steward directory — listing, creation, detail, editing,
and lifecycle status transitions for ecosystem members. Supports
filtering by status, profile type, ETHOS, and text search.

ASYNC SESSION SAFETY NOTES:
- request.ctx.member (current_user) is loaded in auth middleware and is DETACHED
  from its session. Only column attributes are safe to access.
- In route handlers, open a new session to load the target member. Eagerly load
  all relationships needed by the template using session.refresh() before exiting
  the session block.
- Templates must use ``{% if X is defined and X %}`` guards for optional relationships.
"""

from __future__ import annotations

import logging
import uuid
from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func, or_

from neos_agent.db.models import (
    Member,
    MemberOnboarding,
    MemberStatusTransition,
)
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, escape_like, retired_write
from neos_agent.views.onboarding import UAF_SECTIONS

logger = logging.getLogger(__name__)

members_bp = Blueprint("members", url_prefix="/dashboard/members")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to a Member select statement."""
    if eco_ids:
        stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))

    status = request.args.get("status")
    if status:
        stmt = stmt.where(Member.current_status == status)

    profile = request.args.get("profile")
    if profile:
        stmt = stmt.where(Member.profile == profile)

    # Text search across name and member_id
    search = request.args.get("q")
    if search:
        pattern = f"%{escape_like(search)}%"
        stmt = stmt.where(
            or_(
                Member.display_name.ilike(pattern),
                Member.member_id.ilike(pattern),
            )
        )

    return stmt


def _is_own_profile(request: Request, member_id: uuid.UUID) -> bool:
    """Check if the logged-in user owns the profile being accessed."""
    current_user = getattr(request.ctx, "member", None)
    if current_user is None:
        return False
    return current_user.id == member_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@members_bp.get("/")
async def member_directory(request: Request):
    """GET /dashboard/members -- member directory with filtering and search."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(Member).order_by(Member.display_name.asc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            members = result.scalars().all()
    except Exception:
        logger.exception("Failed to load member directory")
        members = []
        total = 0

    content = await render(
        "dashboard/members/list.html",
        request=request,
        members=members,
        total=total,
        offset=offset,
        limit=limit,
        filters=dict(request.args),
        active_page="members",
    )
    return html(content)


@members_bp.get("/new")
async def create_form(request: Request):
    """GET /dashboard/members/new -- render create form."""
    content = await render("dashboard/members/form.html", request=request, member=None, active_page="members")
    return html(content)


@members_bp.post("/")
async def create_member(request: Request):
    """POST /dashboard/members -- retired (410): writes happen in the app."""
    return retired_write(request, "/members/new")


@members_bp.get("/<member_id:uuid>")
async def detail(request: Request, member_id: uuid.UUID):
    """GET /dashboard/members/{member_id} -- detail view with lifecycle, roles, ETHOS."""
    try:
        async with request.app.ctx.db() as session:
            member = await get_scoped_entity(session, Member, member_id, request)
            if member is None:
                content = await render(
                    "dashboard/members/detail.html",
                    request=request,
                    member=None,
                    error="Member not found.",
                )
                return html(content, status=404)

            # Eagerly load relationships to avoid async lazy-load errors in templates
            await session.refresh(member, ["ecosystem", "onboarding"])
            ecosystem = member.ecosystem

            # Load onboarding record
            onboarding_result = await session.execute(
                select(MemberOnboarding)
                .where(MemberOnboarding.member_id == member_id)
            )
            onboarding = onboarding_result.scalar_one_or_none()

            # Load status transition history
            transitions_result = await session.execute(
                select(MemberStatusTransition)
                .where(MemberStatusTransition.member_id == member_id)
                .order_by(MemberStatusTransition.date.desc())
            )
            transitions = transitions_result.scalars().all()
    except Exception:
        logger.exception("Failed to load member detail")
        content = await render(
            "dashboard/members/detail.html",
            request=request,
            member=None,
            error="Failed to load member details.",
        )
        return html(content, status=500)

    content = await render(
        "dashboard/members/detail.html",
        request=request,
        member=member,
        ecosystem=ecosystem,
        onboarding=onboarding,
        status_transitions=transitions,
        uaf_sections=UAF_SECTIONS,
        is_own_profile=_is_own_profile(request, member_id),
        active_page="members",
    )
    return html(content)


@members_bp.get("/<member_id:uuid>/edit")
async def edit_form(request: Request, member_id: uuid.UUID):
    """GET /dashboard/members/{member_id}/edit -- render edit form (own profile only)."""
    if not _is_own_profile(request, member_id):
        return redirect(f"/dashboard/members/{member_id}")
    try:
        async with request.app.ctx.db() as session:
            member = await get_scoped_entity(session, Member, member_id, request)
            if member is None:
                return html(
                    await render(
                        "dashboard/members/form.html",
                        request=request,
                        member=None,
                        error="Member not found.",
                    ),
                    status=404,
                )
    except Exception:
        logger.exception("Failed to load member for editing")
        return html(
            await render(
                "dashboard/members/form.html",
                request=request,
                member=None,
                error="Failed to load member.",
            ),
            status=500,
        )

    content = await render("dashboard/members/form.html", request=request, member=member, active_page="members")
    return html(content)


@members_bp.put("/<member_id:uuid>")
async def update_member(request: Request, member_id: uuid.UUID):
    """PUT /dashboard/members/{member_id} -- retired (410): writes happen in the app."""
    return retired_write(request, f"/members/{member_id}/edit")


@members_bp.post("/<member_id:uuid>")
async def update_member_post(request: Request, member_id: uuid.UUID):
    """POST /dashboard/members/{id} -- retired (410): writes happen in the app."""
    return retired_write(request, f"/members/{member_id}/edit")


@members_bp.post("/<member_id:uuid>/status")
async def status_transition(request: Request, member_id: uuid.UUID):
    """POST /dashboard/members/{member_id}/status -- retired (410): writes happen in the app."""
    return retired_write(request, f"/members/{member_id}")


@members_bp.post("/<member_id:uuid>/onboarding/consent")
async def onboarding_consent(request: Request, member_id: uuid.UUID):
    """POST /dashboard/members/{member_id}/onboarding/consent -- retired (410): writes happen in the app."""
    return retired_write(request, f"/onboarding/{member_id}/ceremony")


@members_bp.post("/<member_id:uuid>/onboarding/finalize")
async def onboarding_finalize(request: Request, member_id: uuid.UUID):
    """POST /dashboard/members/{member_id}/onboarding/finalize -- retired (410): writes happen in the app."""
    return retired_write(request, f"/onboarding/{member_id}/ceremony")
