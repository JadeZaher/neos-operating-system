"""JSON API blueprint for member management.

Blueprint: members_api_bp, url_prefix="/api/v1/members"

Manages member lifecycle including creation, status transitions,
and onboarding state queries.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import re
import uuid
import datetime as _dt
from typing import Optional

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    Member,
    MemberOnboarding,
    MemberStatusTransition,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class MemberListItem(BaseModel):
    id: uuid.UUID
    member_id: str
    display_name: str
    current_status: str
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    onboarding_status: str | None = None
    created_at: _dt.datetime


class MemberDetail(MemberListItem):
    ecosystem_id: uuid.UUID
    did: str | None = None
    skills_offered: dict | None = None
    skills_needed: dict | None = None
    interests: dict | None = None
    kyc_status: str | None = None
    last_governance_activity_date: _dt.date | None = None
    notes: str | None = None
    updated_at: _dt.datetime
    onboarding: OnboardingSnapshot | None = None


class OnboardingSnapshot(BaseModel):
    id: uuid.UUID
    facilitator: str | None = None
    completion_percentage: int | None = 0
    consent_date: _dt.date | None = None
    cooling_off_start: _dt.date | None = None
    cooling_off_end: _dt.date | None = None


# Rebuild MemberDetail now that OnboardingSnapshot is defined
MemberDetail.model_rebuild()


class MemberCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    display_name: str
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    skills_offered: dict | None = None
    skills_needed: dict | None = None
    interests: dict | None = None
    notes: str | None = None


class MemberUpdateRequest(BaseModel):
    display_name: str | None = None
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    skills_offered: dict | None = None
    skills_needed: dict | None = None
    interests: dict | None = None
    notes: str | None = None


class StatusTransitionRequest(BaseModel):
    status: str
    trigger: str | None = None
    notes: str | None = None


class OnboardingChecklistItem(BaseModel):
    id: uuid.UUID
    facilitator: str | None = None
    mentor_id: uuid.UUID | None = None
    uaf_version_consented: str | None = None
    consent_date: _dt.date | None = None
    cooling_off_start: _dt.date | None = None
    cooling_off_end: _dt.date | None = None
    section_consents: dict | None = None
    checklist_items: dict | None = None
    completion_percentage: int | None = 0


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

members_api_bp = Blueprint("members_api", url_prefix="/api/v1/members")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_auth(request: Request):
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def _get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    cookie = request.cookies.get("neos_selected_ecosystems")
    if cookie:
        try:
            ids = json_module.loads(cookie)
            return [uuid.UUID(i) for i in ids if i]
        except (json_module.JSONDecodeError, ValueError):
            pass
    member = getattr(request.ctx, "member", None)
    if member:
        return [member.ecosystem_id]
    return []


def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


def _member_to_list_item(m: Member) -> dict:
    return MemberListItem(
        id=m.id,
        member_id=m.member_id,
        display_name=m.display_name,
        current_status=m.current_status,
        profile=m.profile,
        phone=m.phone,
        profile_picture=m.profile_picture,
        onboarding_status=m.onboarding_status,
        created_at=m.created_at,
    ).model_dump(mode="json")


def _onboarding_snapshot(ob: MemberOnboarding | None) -> OnboardingSnapshot | None:
    if ob is None:
        return None
    return OnboardingSnapshot(
        id=ob.id,
        facilitator=ob.facilitator,
        completion_percentage=ob.completion_percentage,
        consent_date=ob.consent_date,
        cooling_off_start=ob.cooling_off_start,
        cooling_off_end=ob.cooling_off_end,
    )


def _member_to_detail(m: Member, ob: MemberOnboarding | None = None) -> dict:
    return MemberDetail(
        id=m.id,
        member_id=m.member_id,
        display_name=m.display_name,
        current_status=m.current_status,
        profile=m.profile,
        phone=m.phone,
        profile_picture=m.profile_picture,
        onboarding_status=m.onboarding_status,
        created_at=m.created_at,
        ecosystem_id=m.ecosystem_id,
        did=m.did,
        skills_offered=m.skills_offered,
        skills_needed=m.skills_needed,
        interests=m.interests,
        kyc_status=m.kyc_status,
        last_governance_activity_date=m.last_governance_activity_date,
        notes=m.notes,
        updated_at=m.updated_at,
        onboarding=_onboarding_snapshot(ob),
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@members_api_bp.get("/")
async def list_members(request: Request):
    """GET /api/v1/members -- Paginated member list with filtering.

    Query params: status, profile, q (search display_name/member_id),
    page (default 1), per_page (default 25, max 100).
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(Member).order_by(Member.created_at.desc())

        if eco_ids:
            stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))

        status = request.args.get("status")
        if status:
            stmt = stmt.where(Member.current_status == status)

        profile = request.args.get("profile")
        if profile:
            stmt = stmt.where(Member.profile == profile)

        search = request.args.get("q")
        if search:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(
                or_(
                    Member.display_name.ilike(pattern),
                    Member.member_id.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        members = result.scalars().all()

    return json({
        "items": [_member_to_list_item(m) for m in members],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@members_api_bp.get("/<member_id:uuid>")
async def get_member(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id -- Member detail with onboarding status."""
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(Member)
            .options(selectinload(Member.onboarding))
            .where(Member.id == member_id)
        )
        if eco_ids:
            stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        m = result.scalar_one_or_none()

    if m is None:
        return json({"error": "Member not found"}, status=404)

    return json(_member_to_detail(m, ob=m.onboarding))


@members_api_bp.post("/")
async def create_member(request: Request):
    """POST /api/v1/members -- Create a new member.

    Accepts JSON: MemberCreateRequest
    Returns JSON: MemberDetail with 201 status.
    """
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = MemberCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    member_id_str = f"MEM-{short_id}"

    async with request.app.ctx.db() as session:
        new_member = Member(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            member_id=member_id_str,
            display_name=create_req.display_name,
            current_status="prospective",
            profile=create_req.profile,
            phone=create_req.phone,
            profile_picture=create_req.profile_picture,
            skills_offered=create_req.skills_offered,
            skills_needed=create_req.skills_needed,
            interests=create_req.interests,
            notes=create_req.notes,
        )
        session.add(new_member)
        await session.commit()
        await session.refresh(new_member)

    return json(_member_to_detail(new_member), status=201)


@members_api_bp.put("/<member_id:uuid>")
async def update_member(request: Request, member_id: uuid.UUID):
    """PUT /api/v1/members/:id -- Update non-None fields of a member."""
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = MemberUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(Member).where(Member.id == member_id)
        if eco_ids:
            stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return json({"error": "Member not found"}, status=404)

        update_data = update_req.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(m, field, value)

        await session.commit()
        await session.refresh(m)

    return json(_member_to_detail(m))


@members_api_bp.post("/<member_id:uuid>/status")
async def member_status_transition(request: Request, member_id: uuid.UUID):
    """POST /api/v1/members/:id/status -- Status transition.

    Accepts JSON: StatusTransitionRequest
    Records a MemberStatusTransition and updates current_status.
    """
    auth_member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        req = StatusTransitionRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(Member).where(Member.id == member_id)
        if eco_ids:
            stmt = stmt.where(Member.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return json({"error": "Member not found"}, status=404)

        old_status = m.current_status

        transition = MemberStatusTransition(
            id=uuid.uuid4(),
            member_id=m.id,
            from_status=old_status,
            to_status=req.status,
            date=_dt.date.today(),
            trigger=req.trigger,
            notes=req.notes,
        )
        session.add(transition)
        m.current_status = req.status
        await session.commit()
        await session.refresh(m)

        logger.info("Member %s status: %s -> %s", member_id, old_status, req.status)

    return json(_member_to_detail(m))


@members_api_bp.get("/<member_id:uuid>/onboarding")
async def get_member_onboarding(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id/onboarding -- Onboarding checklist state."""
    auth_member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        # Verify member exists and is accessible
        m_stmt = select(Member.id).where(Member.id == member_id)
        if eco_ids:
            m_stmt = m_stmt.where(Member.ecosystem_id.in_(eco_ids))
        if await session.scalar(m_stmt) is None:
            return json({"error": "Member not found"}, status=404)

        stmt = select(MemberOnboarding).where(MemberOnboarding.member_id == member_id)
        result = await session.execute(stmt)
        ob = result.scalar_one_or_none()

    if ob is None:
        return json({"error": "No onboarding record found"}, status=404)

    data = OnboardingChecklistItem(
        id=ob.id,
        facilitator=ob.facilitator,
        mentor_id=ob.mentor_id,
        uaf_version_consented=ob.uaf_version_consented,
        consent_date=ob.consent_date,
        cooling_off_start=ob.cooling_off_start,
        cooling_off_end=ob.cooling_off_end,
        section_consents=ob.section_consents,
        checklist_items=ob.checklist_items,
        completion_percentage=ob.completion_percentage,
    )
    return json(data.model_dump(mode="json"))
