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
from typing import Optional, cast

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    Ecosystem,
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
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import require_admin, get_ecosystem_ids, apply_ecosystem_name_filter, parse_pagination, serialize_shared_ecosystem_ids, build_search_filter
from neos_agent.api.policy import (
    MEMBER_PROFILES,
    assignable_roles,
    can_assign_role,
    can_choose_own_profile,
    can_grant_profile,
    has_role_at_least,
    is_steward,
)
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.services.member_lifecycle import JOINED, caller_member_moves, move_member, place_member  # G-Onboard
from neos_agent.services.member_lifecycle import PROFILE_GRANT, ROLE_GRANT, grant_record  # FX-Onboard
from neos_agent.api.policy import can_read_onboarding_record  # FX-Onboard
from neos_agent.api.schemas.members import (
    MemberCreateRequest,
    MemberRole,
    MemberDetail,
    MemberListItem,
    MemberProfileResponse,
    MemberUpdateRequest,
    ProfileGrantRequest,
    RoleGrantSchema,
    RoleUpdateRequest,
    OnboardingChecklistItem,
    OnboardingSnapshot,
    StatusTransitionRequest,
)

logger = logging.getLogger(__name__)


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
        ecosystem_id=m.ecosystem_id,
        member_id=m.member_id,
        display_name=m.display_name,
        current_status=m.current_status,
        role=cast(MemberRole, m.role),
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
        role=cast(MemberRole, m.role),
        profile=m.profile,
        phone=user.phone if user else None,
        profile_picture=user.profile_picture if user else None,
        onboarding_status=m.onboarding_status,
        created_at=m.created_at,
        ecosystem_id=m.ecosystem_id,
        shared_ecosystem_ids=m.shared_ecosystem_ids,
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
        role=cast(MemberRole, m.role),
        profile=m.profile,
        phone=user.phone if user else None,
        profile_picture=user.profile_picture if user else None,
        onboarding_status=m.onboarding_status,
        created_at=m.created_at,
        ecosystem_id=m.ecosystem_id,
        shared_ecosystem_ids=m.shared_ecosystem_ids,
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


ROLE_GRANT_DENIED = "You can give only roles below your own, and only an owner can make someone an owner"
PROFILE_GRANT_ONLY = ("Co-creator and builder profiles carry administration rights, so you cannot choose them "
                      "yourself: an owner of the ecosystem grants them")
PROFILE_GRANT_DENIED = ("Only someone who could make this member an admin (an owner, or the founder before there "
                        "is one) can change their profile, and never their own")
ROLE_GRANT_TRIGGER = ROLE_GRANT  # one spelling with member_lifecycle (an exit's reset is recorded the same way)
PROFILE_GRANT_TRIGGER = PROFILE_GRANT
_ROLE_PREFIX = "role:"
_PROFILE_PREFIX = "profile:"
# Recorded grants shown as the member's role history: trigger -> (kind, status prefix).
_GRANT_KINDS = {ROLE_GRANT_TRIGGER: ("role", _ROLE_PREFIX), PROFILE_GRANT_TRIGGER: ("profile", _PROFILE_PREFIX)}
_STATUS_LENGTH = 50  # member_status_transitions.from_status / to_status


async def _ecosystem_has_owner(session, ecosystem_id: uuid.UUID) -> bool:
    """Whether any member row in the ecosystem is an owner (ends the founder bootstrap)."""
    return bool(await session.scalar(
        select(func.count(Member.id)).where(Member.ecosystem_id == ecosystem_id, Member.role == "owner")
    ))


async def _bootstrap_context(session, ecosystem_id: uuid.UUID) -> dict:
    """policy kwargs: whether the ecosystem has an owner and, while it has none, its founder (the oldest member row)."""
    if await _ecosystem_has_owner(session, ecosystem_id):
        return {"ecosystem_has_owner": True, "founder_id": None}
    founder_id = await session.scalar(
        select(Member.id).where(Member.ecosystem_id == ecosystem_id)
        .order_by(Member.created_at.asc(), Member.id.asc()).limit(1)
    )
    return {"ecosystem_has_owner": False, "founder_id": founder_id}


def _grant_record(member: Member, actor: Member, trigger: str, old: str | None, new: str | None) -> MemberStatusTransition:
    """A recorded role or profile grant; the granter is stored by member id and named when read."""
    return grant_record(member, trigger, old, new, actor=actor)


async def _role_history(session, member_id: uuid.UUID) -> list[dict]:
    """Recorded role and profile grants for a member, newest first, each naming the granter as they are called now."""
    rows = (await session.execute(
        select(MemberStatusTransition)
        .where(MemberStatusTransition.member_id == member_id, MemberStatusTransition.trigger.in_(list(_GRANT_KINDS)))
        .order_by(MemberStatusTransition.created_at.desc())
    )).scalars().all()
    actor_ids = {row.actor_member_id for row in rows if row.actor_member_id is not None}
    names = dict((await session.execute(
        select(Member.id, Member.display_name).where(Member.id.in_(actor_ids))
    )).all()) if actor_ids else {}
    history = []
    for row in rows:
        kind, prefix = _GRANT_KINDS[row.trigger]
        history.append(RoleGrantSchema(
            kind=kind, from_role=row.from_status.removeprefix(prefix), to_role=row.to_status.removeprefix(prefix),
            date=row.date, granted_by=names.get(row.actor_member_id),
        ).model_dump(mode="json"))
    return history


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@members_api_bp.get("/")
@authenticated
async def list_members(request: Request):
    """GET /api/v1/members -- Paginated member list with filtering.

    Query params: status, profile, q (search display_name/member_id), joined_since (YYYY-MM-DD),
    page (default 1), per_page (default 25, max 100).
    """
    eco_ids = get_ecosystem_ids(request)
    page_request = parse_pagination(request)
    page, per_page = page_request.page, page_request.per_page
    joined_since = request.args.get("joined_since")
    try:
        joined_since_date = _dt.date.fromisoformat(joined_since) if joined_since else None
    except ValueError:
        raise ApiError(400, "joined_since must be a date (YYYY-MM-DD)") from None

    async with request.app.ctx.db() as session:
        stmt = select(Member).order_by(Member.created_at.desc())

        stmt = restrict_to_ecosystems(stmt, Member, eco_ids)
        stmt = apply_ecosystem_name_filter(stmt, Member, request)

        status = request.args.get("status")
        if status:
            stmt = stmt.where(Member.current_status == status)
        if joined_since_date is not None:
            stmt = stmt.where(Member.created_at >= _dt.datetime.combine(joined_since_date, _dt.time.min))

        profile = request.args.get("profile")
        if profile:
            stmt = stmt.where(Member.profile == profile)

        search = request.args.get("q")
        if search:
            stmt = stmt.where(build_search_filter(
                Member, search, Member.display_name, Member.member_id
            ))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.options(selectinload(Member.user)).offset(page_request.offset).limit(per_page)
        result = await session.execute(stmt)
        members = result.scalars().all()

    return json({
        "items": [_member_to_list_item(m, user=m.user) for m in members],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@members_api_bp.get("/<member_id:uuid>")
@authenticated
async def get_member(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id -- Member detail with onboarding status."""
    async with request.app.ctx.db() as session:
        m = await get_scoped_or_404(
            session, request, Member, member_id,
            options=(selectinload(Member.onboarding), selectinload(Member.user)),
            label="Member",
        )

    return json(_member_to_detail(m, ob=m.onboarding, user=m.user))


@members_api_bp.get("/<member_id:uuid>/profile")
@authenticated
async def get_member_profile(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id/profile -- Enriched member profile.

    Returns the full member + user schema plus quiz progress summary,
    earned badges, and profile tags inline.
    """
    async with request.app.ctx.db() as session:
        m = await get_scoped_or_404(
            session, request, Member, member_id,
            options=(selectinload(Member.onboarding), selectinload(Member.user)),
            label="Member",
        )

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

        caller = await caller_in(session, request, m.ecosystem_id)
        bootstrap = await _bootstrap_context(session, m.ecosystem_id)
        grantable = assignable_roles(caller, m, **bootstrap)
        grantable_profiles = (
            [profile for profile in MEMBER_PROFILES if profile != m.profile]
            if can_grant_profile(caller, m, **bootstrap) else []
        )
        role_history = await _role_history(session, m.id)
        ecosystem_name = await session.scalar(select(Ecosystem.name).where(Ecosystem.id == m.ecosystem_id))  # G-Onboard
        member_moves = await caller_member_moves(session, m, caller=caller, ecosystem_name=ecosystem_name or "")

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

    payload = _member_to_profile(
        m,
        ob=m.onboarding,
        user=m.user,
        quiz_summary=quiz_summary,
        badges=badges_list,
        tags=tags_list,
    )
    payload["caller_assignable_roles"] = grantable
    payload["caller_grantable_profiles"] = grantable_profiles
    payload["caller_is_self"] = caller is not None and caller.id == m.id
    payload["role_history"] = role_history
    payload["caller_member_moves"] = member_moves  # G-Onboard: policy.MEMBER_MOVES for this caller, with words
    return json(payload)


@members_api_bp.post("/")
@authenticated
async def create_member(request: Request):
    """POST /api/v1/members -- Create the caller's own membership row (a join with profile details).

    Accepts JSON: MemberCreateRequest. Placed through member_lifecycle.place_member like a join: the
    agreement gate decides active or pending_consent, one transition is recorded, an existing row is a
    409 (it was a unique-violation 500). Returns JSON: MemberDetail with 201 status.
    """
    auth_member = request.ctx.member

    body = request.json or {}
    try:
        create_req = MemberCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    if create_req.ecosystem_id not in get_ecosystem_ids(request):
        raise ApiError(403, "Access denied: ecosystem not in scope")
    if not can_choose_own_profile(None, create_req.profile):  # the new row is the caller's own
        raise ApiError(403, PROFILE_GRANT_ONLY)

    user = getattr(request.ctx, "user", None)

    async with request.app.ctx.db() as session:
        ecosystem = await session.get(Ecosystem, create_req.ecosystem_id)
        if ecosystem is None:
            raise ApiError(404, "Ecosystem not found")
        placement = await place_member(
            session, user_id=user.id if user else auth_member.user_id, ecosystem=ecosystem,
            display_name=create_req.display_name, member_key=f"MEM-{uuid.uuid4().hex[:8].upper()}", trigger=JOINED,
        )
        if not placement.created:  # a pending or returning row joins through POST /ecosystems/:id/join (rolled back)
            raise ApiError(409, f"You already have a membership in {ecosystem.name}.", {"code": "ALREADY_MEMBER"})
        new_member = placement.member
        new_member.shared_ecosystem_ids = serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids)
        new_member.profile = create_req.profile
        new_member.skills_offered = create_req.skills_offered
        new_member.skills_needed = create_req.skills_needed
        new_member.interests = create_req.interests
        new_member.notes = create_req.notes
        await session.commit()
        await session.refresh(new_member)

    return json(_member_to_detail(new_member, user=user), status=201)


@members_api_bp.put("/<member_id:uuid>")
@authenticated
async def update_member(request: Request, member_id: uuid.UUID):
    """PUT /api/v1/members/:id -- Update the caller's OWN member profile.

    Binding rule: a member can only edit their own profile. Governance
    actions on other members live on dedicated endpoints (PUT /members/:id/role,
    POST /members/:id/status) — never through profile edits.
    """
    body = request.json or {}
    try:
        update_req = MemberUpdateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        m = await get_scoped_or_404(
            session, request, Member, member_id,
            options=(selectinload(Member.user),),
            label="Member",
        )

        # Self-service only: profile content belongs to the member alone.
        req_user = getattr(request.ctx, "user", None)
        if req_user is None or m.user_id != req_user.id:
            raise ApiError(
                403,
                "Members can only edit their own profile. "
                "Governance actions use PUT /members/:id/role or POST /members/:id/status.",
            )

        update_data = update_req.model_dump(exclude_none=True)
        if "profile" in update_data and not can_choose_own_profile(m, update_data["profile"]):
            raise ApiError(403, PROFILE_GRANT_ONLY)
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


@members_api_bp.put("/<member_id:uuid>/role")
@authenticated
async def update_member_role(request: Request, member_id: uuid.UUID):
    """PUT /api/v1/members/:id/role -- Set a member's per-ecosystem role tier (owner decision).

    Only roles below your own rank, to members below it; only an owner makes an owner;
    you may step yourself down; the founder bootstraps while the ecosystem has no owner.
    Every change is recorded as a MemberStatusTransition (trigger "role_grant", the granter's member id).
    """
    body = request.json or {}
    try:
        role_req = RoleUpdateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    user = getattr(request.ctx, "user", None)

    async with request.app.ctx.db() as session:
        m = await get_scoped_or_404(
            session, request, Member, member_id,
            options=(selectinload(Member.user),),
            label="Member",
        )

        caller = await caller_in(session, request, m.ecosystem_id)
        if not can_assign_role(caller, m, role_req.role, **await _bootstrap_context(session, m.ecosystem_id)):
            raise ApiError(403, ROLE_GRANT_DENIED)

        old_role = m.role
        if old_role != role_req.role:
            m.role = role_req.role
            session.add(_grant_record(m, caller, ROLE_GRANT_TRIGGER, old_role, role_req.role))
        await session.commit()
        await session.refresh(m)
        logger.info("Member %s role: %s -> %s (by user %s)", member_id, old_role, role_req.role, getattr(user, "id", None))

    return json(_member_to_detail(m, user=m.user))


@members_api_bp.put("/<member_id:uuid>/profile-grant")
@authenticated
async def grant_member_profile(request: Request, member_id: uuid.UUID):
    """PUT /api/v1/members/:id/profile-grant -- Set another member's profile, including co_creator/builder.

    Those two confer administration of the member's ecosystem (and, on a home-ecosystem row, platform
    admin), so members never choose them (PUT /members/:id refuses): policy.can_grant_profile read on
    caller_in for the member's ecosystem (whoever may make the member an admin there; never yourself).
    Recorded like a role grant (trigger "profile_grant"); a no-op writes nothing.
    """
    try:
        grant_req = ProfileGrantRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        m = await get_scoped_or_404(
            session, request, Member, member_id, options=(selectinload(Member.user),), label="Member",
        )
        caller = await caller_in(session, request, m.ecosystem_id)
        if not can_grant_profile(caller, m, **await _bootstrap_context(session, m.ecosystem_id)):
            raise ApiError(403, PROFILE_GRANT_DENIED)
        if m.profile != grant_req.profile:
            session.add(_grant_record(m, caller, PROFILE_GRANT_TRIGGER, m.profile, grant_req.profile))
            m.profile = grant_req.profile
        await session.commit()
        await session.refresh(m)

    return json(_member_to_detail(m, user=m.user))


@members_api_bp.post("/<member_id:uuid>/status")
@authenticated
async def member_status_transition(request: Request, member_id: uuid.UUID):
    """POST /api/v1/members/:id/status -- A steward's move from policy.MEMBER_MOVES (member_lifecycle.move_member).

    Accepts JSON: {"status", "notes"?}; `trigger` is ignored (it is always "steward_move"). 403 unless an
    active steward who outranks the member (never yourself); 400 with `allowed` off the table (exiting: the
    exit flow); 409 CONSENT_REQUIRED confirming a newcomer with agreements left. Recorded with the actor.
    """
    body = request.json or {}
    try:
        req = StatusTransitionRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        m = await get_scoped_or_404(
            session, request, Member, member_id,
            options=(selectinload(Member.user),),
            label="Member",
        )
        await session.refresh(m, with_for_update=True)  # two stewards moving at once run one after the other

        caller = await caller_in(session, request, m.ecosystem_id)
        old_status = m.current_status
        await move_member(session, m, req.status, caller=caller, notes=req.notes)
        await session.commit()
        await session.refresh(m)

        logger.info("Member %s status: %s -> %s", member_id, old_status, req.status)

    return json(_member_to_detail(m, user=m.user))


@members_api_bp.get("/<member_id:uuid>/onboarding")
@authenticated
async def get_member_onboarding(request: Request, member_id: uuid.UUID):
    """GET /api/v1/members/:id/onboarding -- Onboarding checklist state."""
    async with request.app.ctx.db() as session:
        target = await get_scoped_or_404(session, request, Member, member_id, label="Member")
        if not can_read_onboarding_record(await caller_in(session, request, target.ecosystem_id), target):
            raise ApiError(404, "Member not found")  # FX-Onboard A8: positions and objections are not public

        stmt = select(MemberOnboarding).where(MemberOnboarding.member_id == member_id)
        result = await session.execute(stmt)
        ob = result.scalar_one_or_none()

    if ob is None:
        raise ApiError(404, "No onboarding record found")

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


# G-Onboard: POST /members/:id/resend-invite was removed: it answered "Invite re-sent" and delivered nothing (review L2).
