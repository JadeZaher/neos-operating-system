"""Member directory views for the NEOS dashboard.

Blueprint: members_bp, url_prefix="/dashboard/members"

Manages the Steward directory — listing, creation, detail, editing,
and lifecycle status transitions for ecosystem members. Supports
filtering by status, profile type, AZPO, and text search.
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
    Member,
    MemberOnboarding,
    MemberStatusTransition,
)
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id

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
        pattern = f"%{search}%"
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


def _parse_comma_list(raw: str | None) -> list[str] | None:
    """Parse a comma-separated string into a list of trimmed non-empty strings."""
    if not raw:
        return None
    items = [s.strip() for s in raw.split(",") if s.strip()]
    return items if items else None


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
    """POST /dashboard/members -- create member from form data."""
    form = request.form
    eco_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if eco_id is None:
        content = await render(
            "dashboard/members/form.html",
            request=request,
            member=None,
            error="Invalid or unauthorized ecosystem.",
        )
        return html(content, status=403)
    try:
        async with request.app.ctx.db() as session:
            member = Member(
                id=uuid.uuid4(),
                ecosystem_id=eco_id,
                member_id=form.get("member_id", ""),
                display_name=form.get("display_name", ""),
                current_status="prospective",
                profile=form.get("profile"),
                phone=form.get("phone"),
                notes=form.get("notes"),
            )
            session.add(member)
            await session.commit()
            member_id = member.id
    except Exception:
        logger.exception("Failed to create member")
        content = await render(
            "dashboard/members/form.html",
            request=request,
            member=None,
            error="Failed to create member. Please check your input and try again.",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/members/{member_id}")


@members_bp.get("/<member_id:uuid>")
async def detail(request: Request, member_id: uuid.UUID):
    """GET /dashboard/members/{member_id} -- detail view with lifecycle, roles, AZPO."""
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
        transitions=transitions,
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
    """PUT /dashboard/members/{member_id} -- update member (own profile only)."""
    if not _is_own_profile(request, member_id):
        return redirect(f"/dashboard/members/{member_id}")
    form = request.form
    try:
        async with request.app.ctx.db() as session:
            member = await get_scoped_entity(session, Member, member_id, request)
            if member is None:
                return html(
                    await render(
                        "dashboard/members/detail.html",
                        request=request,
                        member=None,
                        error="Member not found.",
                    ),
                    status=404,
                )

            if form.get("display_name"):
                member.display_name = form.get("display_name")
            if form.get("profile"):
                member.profile = form.get("profile")
            if form.get("phone"):
                member.phone = form.get("phone")
            if form.get("notes"):
                member.notes = form.get("notes")
            if form.get("onboarding_status"):
                member.onboarding_status = form.get("onboarding_status")
            if form.get("kyc_status"):
                member.kyc_status = form.get("kyc_status")

            # Skills and interests — always set (allows clearing)
            member.skills_offered = _parse_comma_list(form.get("skills_offered"))
            member.skills_needed = _parse_comma_list(form.get("skills_needed"))
            member.interests = _parse_comma_list(form.get("interests"))

            await session.commit()
    except Exception:
        logger.exception("Failed to update member")
        return html(
            await render(
                "dashboard/members/form.html",
                request=request,
                member=None,
                error="Failed to update member.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/members/{member_id}")


@members_bp.post("/<member_id:uuid>")
async def update_member_post(request: Request, member_id: uuid.UUID):
    """POST /dashboard/members/{id} -- delegates to PUT handler for HTML form compatibility."""
    return await update_member(request, member_id)


@members_bp.post("/<member_id:uuid>/status")
async def status_transition(request: Request, member_id: uuid.UUID):
    """POST /dashboard/members/{member_id}/status -- lifecycle status transition.

    Requires form fields: new_status. Optional: trigger, notes.
    Valid statuses: prospective, onboarding, active, inactive, exiting, exited.
    """
    form = request.form
    new_status = form.get("new_status")
    trigger = form.get("trigger", "")
    notes = form.get("notes", "")

    if not new_status:
        return html(
            await render(
                "dashboard/members/detail.html",
                request=request,
                member=None,
                error="new_status is required for status transition.",
            ),
            status=400,
        )

    try:
        async with request.app.ctx.db() as session:
            member = await get_scoped_entity(session, Member, member_id, request)
            if member is None:
                return html(
                    await render(
                        "dashboard/members/detail.html",
                        request=request,
                        member=None,
                        error="Member not found.",
                    ),
                    status=404,
                )

            old_status = member.current_status

            # Record the transition
            transition = MemberStatusTransition(
                id=uuid.uuid4(),
                member_id=member_id,
                from_status=old_status,
                to_status=new_status,
                date=date.today(),
                trigger=trigger,
                notes=notes,
            )
            session.add(transition)

            member.current_status = new_status
            await session.commit()

            logger.info(
                "Member %s status: %s -> %s (trigger: %s)",
                member_id, old_status, new_status, trigger,
            )
    except Exception:
        logger.exception("Failed to transition member status")
        return html(
            await render(
                "dashboard/members/detail.html",
                request=request,
                member=None,
                error="Failed to update member status.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/members/{member_id}")
