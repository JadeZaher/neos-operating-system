"""JSON API blueprint for member management.

Blueprint: members_api_bp, url_prefix="/api/v1/members"

Manages member lifecycle including creation, status transitions,
and onboarding state queries.
Returns JSON responses only.
"""

from __future__ import annotations

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
    User,
)
from neos_agent.db.course_models import (
    Course,
    Quiz,
    QuizProgress,
    QuizResult,
    UserBadge,
    UserTag,
)
from neos_agent.api.helpers import require_auth, get_ecosystem_ids, apply_ecosystem_filter, serialize_shared_ecosystem_ids

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
    skills_offered: list | dict | None = None
    skills_needed: list | dict | None = None
    interests: list | dict | None = None
    kyc_status: str | None = None
    last_governance_activity_date: _dt.date | None = None
    notes: str | None = None
    privacy: dict | None = None
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


class MemberProfileResponse(MemberDetail):
    user_id: uuid.UUID
    username: str | None = None
    user_display_name: str | None = None
    profile_picture: str | None = None
    quiz_summary: dict
    badges: list
    tags: list


class MemberCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    display_name: str
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    skills_offered: list | dict | None = None
    skills_needed: list | dict | None = None
    interests: list | dict | None = None
    notes: str | None = None


class MemberUpdateRequest(BaseModel):
    display_name: str | None = None
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    skills_offered: list | dict | None = None
    skills_needed: list | dict | None = None
    interests: list | dict | None = None
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    notes: str | None = None
    privacy: dict | None = None


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



def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


def _member_to_list_item(m: Member, user: User | None = None) -> dict:
    return MemberListItem(
        id=m.id,
        member_id=m.member_id,
        display_name=m.display_name,
        current_status=m.current_status,
        profile=m.profile,
        phone=user.phone if user else None,
        profile_picture=user.profile_picture if user else None,
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


def _member_to_detail(m: Member, ob: MemberOnboarding | None = None, user: User | None = None) -> dict:
    return MemberDetail(
        id=m.id,
        member_id=m.member_id,
        display_name=m.display_name,
        current_status=m.current_status,
        profile=m.profile,
        phone=user.phone if user else None,
        profile_picture=user.profile_picture if user else None,
        onboarding_status=m.onboarding_status,
        created_at=m.created_at,
        ecosystem_id=m.ecosystem_id,
        did=user.did if user else None,
        skills_offered=m.skills_offered,
        skills_needed=m.skills_needed,
        interests=m.interests,
        kyc_status=m.kyc_status,
        last_governance_activity_date=m.last_governance_activity_date,
        notes=m.notes,
        privacy=m.privacy,
        updated_at=m.updated_at,
        onboarding=_onboarding_snapshot(ob),
    ).model_dump(mode="json")


def _member_to_profile(
    m: Member,
    ob: MemberOnboarding | None,
    user: User | None,
    quiz_summary: dict,
    badges: list,
    tags: list,
) -> dict:
    return MemberProfileResponse(
        id=m.id,
        member_id=m.member_id,
        display_name=m.display_name,
        current_status=m.current_status,
        profile=m.profile,
        phone=user.phone if user else None,
        profile_picture=user.profile_picture if user else None,
        onboarding_status=m.onboarding_status,
        created_at=m.created_at,
        ecosystem_id=m.ecosystem_id,
        did=user.did if user else None,
        skills_offered=m.skills_offered,
        skills_needed=m.skills_needed,
        interests=m.interests,
        kyc_status=m.kyc_status,
        last_governance_activity_date=m.last_governance_activity_date,
        notes=m.notes,
        privacy=m.privacy,
        updated_at=m.updated_at,
        onboarding=_onboarding_snapshot(ob),
        user_id=user.id if user else m.user_id,
        username=user.username if user else None,
        user_display_name=user.display_name if user else None,
        quiz_summary=quiz_summary,
        badges=badges,
        tags=tags,
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
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(Member).order_by(Member.created_at.desc())

        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Member, eco_ids)

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

        stmt = stmt.options(selectinload(Member.user)).offset(offset).limit(per_page)
        result = await session.execute(stmt)
        members = result.scalars().all()

    return json({
        "items": [_member_to_list_item(m, user=m.user) for m in members],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@members_api_bp.get("/<member_id:uuid>")
async def get_member(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id -- Member detail with onboarding status."""
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(Member)
            .options(selectinload(Member.onboarding), selectinload(Member.user))
            .where(Member.id == member_id)
        )
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Member, eco_ids)

        result = await session.execute(stmt)
        m = result.scalar_one_or_none()

    if m is None:
        return json({"error": "Member not found"}, status=404)

    return json(_member_to_detail(m, ob=m.onboarding, user=m.user))


@members_api_bp.get("/<member_id:uuid>/profile")
async def get_member_profile(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id/profile -- Enriched member profile.

    Returns the full member + user schema plus quiz progress summary,
    earned badges, and profile tags inline.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(Member)
            .options(selectinload(Member.onboarding), selectinload(Member.user))
            .where(Member.id == member_id)
        )
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Member, eco_ids)

        result = await session.execute(stmt)
        m = result.scalar_one_or_none()

        if m is None:
            return json({"error": "Member not found"}, status=404)

        # Fetch all quiz results for this member
        results_stmt = select(QuizResult).where(QuizResult.member_id == member_id)
        quiz_results = (await session.execute(results_stmt)).scalars().all()

        # Fetch in-progress quiz records
        progress_stmt = select(QuizProgress).where(QuizProgress.member_id == member_id)
        quiz_progress_rows = (await session.execute(progress_stmt)).scalars().all()

        # Fetch published quizzes scoped to this member's ecosystem.
        # A quiz belongs to this ecosystem if quiz.ecosystem_id matches directly,
        # or if it belongs to a course in this ecosystem.
        quizzes_stmt = (
            select(Quiz)
            .outerjoin(Quiz.course)
            .where(Quiz.is_published.is_(True))
            .where(
                or_(
                    Quiz.ecosystem_id == m.ecosystem_id,
                    Course.ecosystem_id == m.ecosystem_id,
                )
            )
        )
        published_quizzes = (await session.execute(quizzes_stmt)).scalars().unique().all()

        # Fetch badges and tags
        badges_stmt = select(UserBadge).where(UserBadge.member_id == member_id)
        badges = (await session.execute(badges_stmt)).scalars().all()

        tags_stmt = select(UserTag).where(UserTag.member_id == member_id)
        tags = (await session.execute(tags_stmt)).scalars().all()

    # Build quiz summary
    completed_ids = {r.quiz_id for r in quiz_results}
    in_progress_ids = {p.quiz_id for p in quiz_progress_rows} - completed_ids
    passed_ids = {r.quiz_id for r in quiz_results if r.is_passed}
    total_available = len(published_quizzes)
    not_started = max(0, total_available - len(completed_ids) - len(in_progress_ids))

    # Best score per quiz (highest score among all attempts)
    best_scores: dict[uuid.UUID, tuple[float | None, bool | None, _dt.datetime | None]] = {}
    for r in quiz_results:
        existing = best_scores.get(r.quiz_id)
        if existing is None or (r.score is not None and (existing[0] is None or r.score > existing[0])):
            best_scores[r.quiz_id] = (r.score, r.is_passed, r.completed_at)

    quiz_list = []
    for q in published_quizzes:
        if q.id in completed_ids:
            best = best_scores.get(q.id, (None, None, None))
            quiz_list.append({
                "quiz_id": str(q.id),
                "quiz_title": q.title,
                "status": "completed",
                "score": best[0],
                "is_passed": best[1],
                "completed_at": best[2].isoformat() if best[2] else None,
            })
        elif q.id in in_progress_ids:
            quiz_list.append({
                "quiz_id": str(q.id),
                "quiz_title": q.title,
                "status": "in_progress",
                "score": None,
                "is_passed": None,
                "completed_at": None,
            })
        else:
            quiz_list.append({
                "quiz_id": str(q.id),
                "quiz_title": q.title,
                "status": "not_started",
                "score": None,
                "is_passed": None,
                "completed_at": None,
            })

    quiz_summary = {
        "total_available": total_available,
        "completed": len(completed_ids),
        "passed": len(passed_ids),
        "in_progress": len(in_progress_ids),
        "not_started": not_started,
        "quizzes": quiz_list,
    }

    badges_list = [
        {
            "id": str(b.id),
            "badge_key": b.badge_key,
            "badge_name": b.badge_name,
            "badge_description": b.badge_description,
            "badge_category": b.badge_category,
            "badge_icon": b.badge_icon,
            "strength": b.strength,
            "earned_at": b.earned_at.isoformat() if b.earned_at else None,
        }
        for b in badges
    ]

    tags_list = [
        {
            "id": str(t.id),
            "tag_key": t.tag_key,
            "tag_value": t.tag_value,
            "tag_category": t.tag_category,
            "data_type": t.data_type,
            "numeric_value": t.numeric_value,
        }
        for t in tags
    ]

    return json(
        _member_to_profile(
            m,
            ob=m.onboarding,
            user=m.user,
            quiz_summary=quiz_summary,
            badges=badges_list,
            tags=tags_list,
        )
    )


@members_api_bp.post("/")
async def create_member(request: Request):
    """POST /api/v1/members -- Create a new member.

    Accepts JSON: MemberCreateRequest
    Returns JSON: MemberDetail with 201 status.
    """
    auth_member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = MemberCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    member_id_str = f"MEM-{short_id}"

    user = getattr(request.ctx, "user", None)

    async with request.app.ctx.db() as session:
        new_member = Member(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            user_id=user.id if user else auth_member.user_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            member_id=member_id_str,
            display_name=create_req.display_name,
            current_status="active",
            profile=create_req.profile,
            skills_offered=create_req.skills_offered,
            skills_needed=create_req.skills_needed,
            interests=create_req.interests,
            notes=create_req.notes,
        )
        session.add(new_member)
        await session.commit()
        await session.refresh(new_member)

    return json(_member_to_detail(new_member, user=user), status=201)


@members_api_bp.put("/<member_id:uuid>")
async def update_member(request: Request, member_id: uuid.UUID):
    """PUT /api/v1/members/:id -- Update non-None fields of a member."""
    auth_member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = MemberUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(Member).options(selectinload(Member.user)).where(Member.id == member_id)
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Member, eco_ids)

        result = await session.execute(stmt)
        m = result.scalar_one_or_none()
        if m is None:
            return json({"error": "Member not found"}, status=404)

        update_data = update_req.model_dump(exclude_none=True)
        if "shared_ecosystem_ids" in update_data:
            update_data["shared_ecosystem_ids"] = serialize_shared_ecosystem_ids(
                update_req.shared_ecosystem_ids
            )
        # phone and profile_picture live on User, not Member
        user_fields = {}
        for field in ("phone", "profile_picture"):
            if field in update_data:
                user_fields[field] = update_data.pop(field)
        for field, value in update_data.items():
            setattr(m, field, value)
        if user_fields and m.user:
            for field, value in user_fields.items():
                setattr(m.user, field, value)

        await session.commit()
        await session.refresh(m)

    return json(_member_to_detail(m, user=m.user))


@members_api_bp.post("/<member_id:uuid>/status")
async def member_status_transition(request: Request, member_id: uuid.UUID):
    """POST /api/v1/members/:id/status -- Status transition.

    Accepts JSON: StatusTransitionRequest
    Records a MemberStatusTransition and updates current_status.
    """
    auth_member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        req = StatusTransitionRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(Member).options(selectinload(Member.user)).where(Member.id == member_id)
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Member, eco_ids)

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

    return json(_member_to_detail(m, user=m.user))


@members_api_bp.get("/<member_id:uuid>/onboarding")
async def get_member_onboarding(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id/onboarding -- Onboarding checklist state."""
    auth_member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        # Verify member exists and is accessible
        m_stmt = select(Member.id).where(Member.id == member_id)
        if eco_ids:
            m_stmt = apply_ecosystem_filter(m_stmt, Member, eco_ids)
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
