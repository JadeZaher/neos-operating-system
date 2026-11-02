"""JSON API blueprint for ecosystem management.

Blueprint: ecosystems_api_bp, url_prefix="/api/v1/ecosystems"

All endpoints require authentication via the neos_session cookie.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import Domain, Ecosystem, Member, SharesNeeds, User
from neos_agent.db.course_models import Quiz, QuizResult
from neos_agent.services.fingerprint import generate_fingerprint
from neos_agent.services.agreement_consent import missing_agreement_consents
from neos_agent.services.member_lifecycle import JOINED, place_member, placement_payload  # G-Onboard

from .errors import ApiError
from .guards import authenticated, caller_in, caller_user_id
from .helpers import _escape_like, parse_pagination, require_auth_user
from .policy import can_administer_ecosystem, can_manage_onboarding, can_update_ecosystem
from .schemas import (
    EcosystemCreateRequest,
    EcosystemDetail,
    EcosystemStewardItem,
    EcosystemSummary,
    EcosystemUpdateRequest,
)

logger = logging.getLogger(__name__)

ecosystems_api_bp = Blueprint("ecosystems_api", url_prefix="/api/v1/ecosystems")


@ecosystems_api_bp.get("/<ecosystem_id:uuid>/join-gates")
async def ecosystem_join_gates(request: Request, ecosystem_id: uuid.UUID):
    _, unauthenticated = require_auth_user(request)
    if unauthenticated:
        return unauthenticated
    from neos_agent.services.join_gates import join_gate_summary
    async with request.app.ctx.db() as session:
        ecosystem = await session.get(Ecosystem, ecosystem_id)
        member = await caller_in(session, request, ecosystem_id)
        if ecosystem is None or (ecosystem.visibility != "public" and member is None):
            raise ApiError(404, "Ecosystem not found")
        summary = await join_gate_summary(session, ecosystem_id=ecosystem_id, member=member, user_id=caller_user_id(request))
        if member is not None and member.current_status == "active":
            summary.update(eligible=True, status="ready", grandfathered=True)
        return json({"join_gates": summary, "membership_status": member.current_status if member else None})


# --- Helpers ---


async def _get_member_ecosystem_ids(db, member_or_user) -> list[uuid.UUID]:
    """Return all ecosystem_ids for a member (by user_id or member object)."""
    if hasattr(member_or_user, "user_id") and member_or_user.user_id:
        result = await db.execute(
            select(Member.ecosystem_id).where(Member.user_id == member_or_user.user_id)
        )
    elif hasattr(member_or_user, "id"):
        result = await db.execute(
            select(Member.ecosystem_id).where(Member.id == member_or_user.id)
        )
    else:
        return []
    return list(result.scalars().all())


async def _get_member_count(db, ecosystem_id: uuid.UUID) -> int:
    """Return the number of members in an ecosystem."""
    result = await db.execute(
        select(func.count(Member.id)).where(Member.ecosystem_id == ecosystem_id)
    )
    return result.scalar() or 0


async def _ecosystem_as_member_or_error(db, request: Request, ecosystem_id: uuid.UUID) -> tuple[Ecosystem, Member]:
    """The ecosystem and the caller's row in it; a private ecosystem the caller is outside of is a 404, a public one a 403."""
    eco = await db.get(Ecosystem, ecosystem_id)
    if eco is None:
        raise ApiError(404, "Ecosystem not found")
    caller = await caller_in(db, request, ecosystem_id)
    if caller is None:
        if eco.visibility != "public":
            raise ApiError(404, "Ecosystem not found")
        raise ApiError(403, "Access denied")
    return eco, caller


def _ecosystem_to_summary(eco: Ecosystem, count: int) -> EcosystemSummary:
    """Convert an Ecosystem ORM instance to an EcosystemSummary schema."""
    return EcosystemSummary(
        id=eco.id,
        name=eco.name,
        description=eco.description,
        status=eco.status,
        logo_url=eco.logo_url,
        location=eco.location,
        member_count=count,
    )


def _ecosystem_to_detail(eco: Ecosystem, count: int) -> EcosystemDetail:
    """Convert an Ecosystem ORM instance to an EcosystemDetail schema."""
    tags = eco.tags if isinstance(eco.tags, list) else None
    return EcosystemDetail(
        uaf_agreement_id=eco.uaf_agreement_id,
        id=eco.id,
        name=eco.name,
        description=eco.description,
        status=eco.status,
        logo_url=eco.logo_url,
        location=eco.location,
        member_count=count,
        website=eco.website,
        founded_date=eco.founded_date,
        tags=tags,
        contact_email=eco.contact_email,
        governance_summary=eco.governance_summary,
        visibility=eco.visibility,
    )



# --- Endpoints ---


@ecosystems_api_bp.get("/")
@authenticated
async def list_ecosystems(request: Request):
    """List ecosystems the authenticated member belongs to.

    Optional query params: ?status=, ?q= (search name/description), ?page=, ?per_page=
    Returns JSON: {"ecosystems": [...], "total": N, "page": N, "per_page": N}
    """
    member = request.ctx.member

    status_filter = request.args.get("status")
    search_query = request.args.get("q")
    page_request = parse_pagination(request)
    page, per_page = page_request.page, page_request.per_page

    async with request.app.ctx.db() as db:
        eco_ids = await _get_member_ecosystem_ids(db, member)
        if not eco_ids:
            return json({"ecosystems": [], "total": 0, "page": page, "per_page": per_page})

        base_query = select(Ecosystem).where(Ecosystem.id.in_(eco_ids))

        if status_filter:
            base_query = base_query.where(Ecosystem.status == status_filter)

        if search_query:
            pattern = f"%{_escape_like(search_query)}%"
            base_query = base_query.where(
                Ecosystem.name.ilike(pattern) | Ecosystem.description.ilike(pattern)
            )

        # Get total count before pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Apply pagination
        paginated_query = base_query.offset(page_request.offset).limit(per_page)
        result = await db.execute(paginated_query)
        ecosystems = list(result.scalars().all())

        summaries = []
        for eco in ecosystems:
            count = await _get_member_count(db, eco.id)
            summaries.append(_ecosystem_to_summary(eco, count))

    return json({
        "ecosystems": [s.model_dump(mode="json") for s in summaries],
        "total": total_count,
        "page": page,
        "per_page": per_page,
    })


@ecosystems_api_bp.get("/<ecosystem_id:uuid>")
@authenticated
async def get_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Return detail for a specific ecosystem.

    Opens for a member or when public; a private ecosystem the caller is outside of is a 404.
    Includes steward contacts (admin/owner members) and the caller's role.
    Returns JSON: EcosystemDetail
    """
    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        caller = await caller_in(db, request, ecosystem_id)
        if eco is None or (caller is None and eco.visibility != "public"):
            raise ApiError(404, "Ecosystem not found")

        count = await _get_member_count(db, eco.id)
        detail = _ecosystem_to_detail(eco, count)

        # Stewards: members holding admin/owner tier in this ecosystem.
        # Public-safe minimal projection — same exposure level as contact_email.
        steward_rows = (await db.execute(
            select(Member.id, Member.display_name, Member.role)
            .where(
                Member.ecosystem_id == ecosystem_id,
                Member.role.in_(("admin", "owner")),
                Member.current_status == "active",
            )
            .order_by(Member.display_name)
        )).all()
        detail.stewards = [
            EcosystemStewardItem(id=row.id, display_name=row.display_name, role=row.role)
            for row in steward_rows
        ]

        # Caller's own role tier in this ecosystem (drives role-management UI gating)
        detail.caller_role = caller.role if caller else None

    return json(detail.model_dump(mode="json"))


@ecosystems_api_bp.post("/")
@authenticated
async def create_ecosystem(request: Request):
    """Create a new ecosystem and add the current member to it.

    Accepts JSON: EcosystemCreateRequest
    Returns JSON: EcosystemDetail with 201 status.
    """
    member = request.ctx.member

    body = request.json or {}
    try:
        create_req = EcosystemCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    # Sanitize website URL
    website = create_req.website
    if website and not website.startswith("https://"):
        if website.startswith("http://"):
            website = "https://" + website[7:]
        else:
            website = "https://" + website

    async with request.app.ctx.db() as db:
        eco = Ecosystem(
            id=uuid.uuid4(),
            name=create_req.name,
            description=create_req.description,
            status="active",
            location=create_req.location,
            website=website,
            logo_url=create_req.logo_url,
            founded_date=create_req.founded_date,
            tags=create_req.tags,
            contact_email=create_req.contact_email,
            governance_summary=create_req.governance_summary,
            visibility=create_req.visibility,
        )
        if create_req.uaf_agreement_id is not None:
            raise ApiError(400, "Create the ecosystem first, then create and ratify its UAF before linking it in ecosystem settings")
        db.add(eco)
        await db.flush()

        # Add the creating member to this ecosystem as steward
        user = getattr(request.ctx, "user", None)
        mid = f"did-{user.did[-12:]}" if user and user.did else f"usr-{str(member.id)[:12]}"
        new_member = Member(
            ecosystem_id=eco.id,
            user_id=user.id if user else member.user_id,
            member_id=mid,
            display_name=member.display_name,
            current_status="active",
            profile="co_creator",
        )
        db.add(new_member)
        await db.flush()

        # Create a default governance domain with the creator as steward
        short_id = uuid.uuid4().hex[:8].upper()
        default_domain = Domain(
            id=uuid.uuid4(),
            ecosystem_id=eco.id,
            domain_id=f"DOM-{short_id}",
            version="1.0",
            status="active",
            purpose=f"Core governance domain for {eco.name}",
            current_steward=new_member.display_name,
            steward_id=new_member.id,
            created_by=new_member.display_name,
        )
        default_domain.version_fingerprint = generate_fingerprint(
            default_domain.domain_id, default_domain.purpose or "", default_domain.version, default_domain.status
        )
        db.add(default_domain)
        await db.commit()

        detail = _ecosystem_to_detail(eco, 1)

    return json(detail.model_dump(mode="json"), status=201)


@ecosystems_api_bp.put("/<ecosystem_id:uuid>")
@authenticated
async def update_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Update an existing ecosystem.

    Verifies the member belongs to this ecosystem.
    Accepts JSON: EcosystemUpdateRequest
    Returns JSON: EcosystemDetail
    """
    body = request.json or {}
    try:
        update_req = EcosystemUpdateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as db:
        eco, caller = await _ecosystem_as_member_or_error(db, request, ecosystem_id)

        stewards_a_domain = await db.scalar(
            select(Domain.id).where(
                Domain.ecosystem_id == ecosystem_id,
                Domain.steward_id == caller.id,
            ).limit(1)
        ) is not None
        member_count = await _get_member_count(db, ecosystem_id)
        if not can_update_ecosystem(caller, stewards_a_domain=stewards_a_domain, member_count=member_count):
            raise ApiError(403, "Only ecosystem stewards can update ecosystem settings")

        # Update fields that are not None
        update_data = update_req.model_dump(exclude_none=True)
        if "uaf_agreement_id" in body:
            from neos_agent.services.matching import validate_uaf_reference
            if not can_administer_ecosystem(caller, ecosystem_id):
                raise ApiError(403, "Only this ecosystem's stewards can link or clear its ratified UAF")
            await validate_uaf_reference(db, ecosystem_id, update_req.uaf_agreement_id)
            update_data["uaf_agreement_id"] = update_req.uaf_agreement_id
        for field, value in update_data.items():
            # Sanitize website URL
            if field == "website" and value and not value.startswith("https://"):
                if value.startswith("http://"):
                    value = "https://" + value[7:]
                else:
                    value = "https://" + value
            setattr(eco, field, value)

        await db.commit()
        await db.refresh(eco)

        count = await _get_member_count(db, eco.id)
        detail = _ecosystem_to_detail(eco, count)

    return json(detail.model_dump(mode="json"))


@ecosystems_api_bp.post("/<ecosystem_id:uuid>/join")
async def request_join_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Join an ecosystem, heal a pending row with nothing left to consent to, or return after leaving.

    member_lifecycle.place_member (one transition per move): 201 for a new row, 200 for an existing one;
    a private or unknown ecosystem is 404; see api/AGENTS.md "Onboarding (G-Onboard)".
    """
    user, unauthenticated = require_auth_user(request)
    if unauthenticated:
        return unauthenticated
    member = getattr(request.ctx, "member", None)
    user_id = user.id
    member_key = f"did-{user.did[-12:]}" if user.did else f"usr-{str(user.id)[:12]}"

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            raise ApiError(404, "Ecosystem not found")
        placement = await place_member(db, user_id=user_id, ecosystem=eco, display_name=user.display_name or (member.display_name if member else "Member"),
                                       member_key=member_key, trigger=JOINED)
        payload = placement_payload(placement, eco.name)
        await db.commit()

    return json(payload, status=201 if placement.created else 200)


# --- Ecosystem Quiz Endpoints ---

ONBOARDING_STEWARDS_ONLY = "Only an active steward of this ecosystem can change its onboarding"
QUIZ_OTHER_ECOSYSTEM = "That quiz belongs to another ecosystem"


async def _onboarding_steward_or_error(db, request: Request, ecosystem_id: uuid.UUID) -> Member:
    """The caller's row when they may manage this ecosystem's onboarding (policy.can_manage_onboarding), else 404/403."""
    _eco, caller = await _ecosystem_as_member_or_error(db, request, ecosystem_id)
    if not can_manage_onboarding(caller, ecosystem_id):
        raise ApiError(403, ONBOARDING_STEWARDS_ONLY)
    return caller


@ecosystems_api_bp.get("/<ecosystem_id:uuid>/quizzes")
@authenticated
async def list_ecosystem_quizzes(request: Request, ecosystem_id: uuid.UUID):
    """List quizzes assigned to an ecosystem.

    Returns JSON: {"quizzes": [...]}
    """
    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            raise ApiError(404, "Ecosystem not found")

        result = await db.execute(
            select(Quiz)
            .where(Quiz.ecosystem_id == ecosystem_id)
            .order_by(Quiz.is_entry_quiz.desc(), Quiz.created_at.desc())
        )
        quizzes = result.scalars().all()

    return json({
        "quizzes": [
            {
                "id": str(q.id),
                "title": q.title,
                "description": q.description,
                "mode": q.mode,
                "is_published": q.is_published,
                "is_entry_quiz": q.is_entry_quiz,
                "passing_score": q.passing_score,
                "allow_retakes": q.allow_retakes,
                "visibility": q.visibility,
            }
            for q in quizzes
        ]
    })


@ecosystems_api_bp.post("/<ecosystem_id:uuid>/quizzes/assign")
@authenticated
async def assign_quiz_to_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Assign a quiz to an ecosystem.

    Accepts JSON: {"quiz_id": "...", "is_entry_quiz": true/false}
    Returns JSON: {"status": "assigned", "quiz_id": "...", "is_entry_quiz": ...}
    """
    body = request.json or {}
    quiz_id_str = body.get("quiz_id")
    is_entry_quiz = body.get("is_entry_quiz", False)

    if not quiz_id_str:
        raise ApiError(400, "quiz_id is required")

    try:
        quiz_id = uuid.UUID(quiz_id_str)
    except ValueError:
        raise ApiError(400, "Invalid quiz_id") from None

    async with request.app.ctx.db() as db:
        steward = await _onboarding_steward_or_error(db, request, ecosystem_id)

        quiz = await db.get(Quiz, quiz_id, with_for_update=True)
        if quiz is None:
            raise ApiError(404, "Quiz not found")
        if quiz.ecosystem_id not in (None, ecosystem_id):  # never take another ecosystem's quiz
            raise ApiError(403, QUIZ_OTHER_ECOSYSTEM)
        if quiz.ecosystem_id is None:  # FX-Onboard A9: a shared quiz stays shared; this ecosystem gets its own copy
            from neos_agent.api.quizzes import copy_quiz
            quiz = copy_quiz(quiz, ecosystem_id=ecosystem_id, domain_id=None, created_by=steward.id)
            db.add(quiz)
            quiz_id = quiz.id

        quiz.domain_id = None
        quiz.team_id = None
        # If marking as entry quiz, clear any existing entry quiz for this ecosystem
        if is_entry_quiz:
            existing_entry = await db.execute(
                select(Quiz).where(
                    Quiz.ecosystem_id == ecosystem_id,
                    Quiz.is_entry_quiz == True,  # noqa: E712
                    Quiz.domain_id.is_(None), Quiz.team_id.is_(None),
                )
            )
            for eq in existing_entry.scalars().all():
                eq.is_entry_quiz = False

        quiz.ecosystem_id = ecosystem_id
        quiz.is_entry_quiz = bool(is_entry_quiz)
        await db.commit()

    return json({
        "status": "assigned",
        "quiz_id": str(quiz_id),
        "is_entry_quiz": bool(is_entry_quiz),
    })


@ecosystems_api_bp.post("/<ecosystem_id:uuid>/quizzes/unassign")
@authenticated
async def unassign_quiz_from_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Unassign a quiz from an ecosystem.

    Accepts JSON: {"quiz_id": "..."}
    Clears the quiz's ecosystem_id and is_entry_quiz flag.
    """
    body = request.json or {}
    quiz_id_str = body.get("quiz_id")
    if not quiz_id_str:
        raise ApiError(400, "quiz_id is required")

    try:
        quiz_id = uuid.UUID(quiz_id_str)
    except ValueError:
        raise ApiError(400, "Invalid quiz_id") from None

    async with request.app.ctx.db() as db:
        await _onboarding_steward_or_error(db, request, ecosystem_id)

        quiz = await db.get(Quiz, quiz_id)
        if quiz is None or quiz.ecosystem_id != ecosystem_id:
            raise ApiError(404, "Quiz not found in this ecosystem")

        quiz.ecosystem_id = None
        quiz.is_entry_quiz = False
        await db.commit()

    return json({"status": "unassigned", "quiz_id": str(quiz_id)})


@ecosystems_api_bp.get("/<ecosystem_id:uuid>/quiz-results")
@authenticated
async def ecosystem_quiz_results(request: Request, ecosystem_id: uuid.UUID):
    """View quiz results for all quizzes assigned to this ecosystem.

    Returns JSON: {"results": [...]}
    Each result includes member display_name and quiz title.
    """
    async with request.app.ctx.db() as db:
        await _onboarding_steward_or_error(db, request, ecosystem_id)  # members' scores are for its stewards

        # Get all quizzes for this ecosystem
        quiz_result = await db.execute(
            select(Quiz.id, Quiz.title).where(Quiz.ecosystem_id == ecosystem_id)
        )
        quiz_rows = quiz_result.all()
        if not quiz_rows:
            return json({"results": []})

        quiz_ids = [r[0] for r in quiz_rows]
        quiz_titles = {r[0]: r[1] for r in quiz_rows}

        # Get all results for these quizzes
        results_query = await db.execute(
            select(QuizResult)
            .where(QuizResult.quiz_id.in_(quiz_ids))
            .order_by(QuizResult.completed_at.desc())
        )
        results = results_query.scalars().all()

        # Collect member IDs and fetch display names
        member_ids = list({r.member_id for r in results})
        member_names: dict[uuid.UUID, str] = {}
        if member_ids:
            member_rows = await db.execute(
                select(Member.id, Member.display_name).where(Member.id.in_(member_ids))
            )
            for mid, dname in member_rows.all():
                member_names[mid] = dname or "Unknown"

    return json({
        "results": [
            {
                "id": str(r.id),
                "quiz_id": str(r.quiz_id),
                "quiz_title": quiz_titles.get(r.quiz_id, "Unknown"),
                "member_id": str(r.member_id),
                "member_name": member_names.get(r.member_id, "Unknown"),
                "score": r.score,
                "is_passed": r.is_passed,
                "time_spent": r.time_spent,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in results
        ]
    })


# ---------------------------------------------------------------------------
# Shares & Needs — Ecosystem-scoped
# ---------------------------------------------------------------------------


@ecosystems_api_bp.get("/<ecosystem_id:uuid>/shares-needs")
@authenticated
async def list_ecosystem_shares_needs(request: Request, ecosystem_id: uuid.UUID):
    """GET /api/v1/ecosystems/:id/shares-needs -- for ACTIVE members there, every status under the one visibility
    rule (G-Exchange; a pending or exited row reads nothing here). Query params: type, category, status.
    """
    from neos_agent.api.guards import caller_user_id  # G-Exchange
    from neos_agent.api.policy import is_active_member_in  # G-Exchange
    from neos_agent.services import exchange  # G-Exchange

    async with request.app.ctx.db() as db:
        _, caller = await _ecosystem_as_member_or_error(db, request, ecosystem_id)
        if not is_active_member_in(caller, ecosystem_id):
            raise ApiError(403, "Only an active member of this ecosystem can list its shares and needs.")
        viewer = await exchange.load_viewer(db, caller_user_id(request))
        filters = [SharesNeeds.ecosystem_id == ecosystem_id, exchange.visible_clause(viewer)]
        for name in ("type", "category", "status"):
            if request.args.get(name):
                filters.append(getattr(SharesNeeds, name) == request.args.get(name))
        rows = (await db.execute(
            select(SharesNeeds).where(*filters).order_by(SharesNeeds.created_at.desc(), SharesNeeds.id)
        )).scalars().all()
        items = await exchange.publication_payloads(db, rows, viewer)

    return json({"items": items})
