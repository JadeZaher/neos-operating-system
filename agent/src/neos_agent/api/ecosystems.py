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

from neos_agent.db.models import Domain, Ecosystem, Member, User
from neos_agent.db.course_models import Quiz, QuizResult

from .helpers import require_auth
from .schemas import (
    EcosystemCreateRequest,
    EcosystemDetail,
    EcosystemSummary,
    EcosystemUpdateRequest,
)

logger = logging.getLogger(__name__)

ecosystems_api_bp = Blueprint("ecosystems_api", url_prefix="/api/v1/ecosystems")


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
async def list_ecosystems(request: Request):
    """List ecosystems the authenticated member belongs to.

    Optional query params: ?status=, ?q= (search name/description), ?page=, ?per_page=
    Returns JSON: {"ecosystems": [...], "total": N, "page": N, "per_page": N}
    """
    member, err = require_auth(request)
    if err:
        return err

    status_filter = request.args.get("status")
    search_query = request.args.get("q")
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as db:
        eco_ids = await _get_member_ecosystem_ids(db, member)
        if not eco_ids:
            return json({"ecosystems": [], "total": 0, "page": page, "per_page": per_page})

        base_query = select(Ecosystem).where(Ecosystem.id.in_(eco_ids))

        if status_filter:
            base_query = base_query.where(Ecosystem.status == status_filter)

        if search_query:
            pattern = f"%{search_query}%"
            base_query = base_query.where(
                Ecosystem.name.ilike(pattern) | Ecosystem.description.ilike(pattern)
            )

        # Get total count before pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Apply pagination
        paginated_query = base_query.offset(offset).limit(per_page)
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
async def get_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Return detail for a specific ecosystem.

    Verifies the member belongs to this ecosystem or it is public.
    Returns JSON: EcosystemDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        # Check access: member belongs to ecosystem or it's public
        eco_ids = await _get_member_ecosystem_ids(db, member)
        if ecosystem_id not in eco_ids and eco.visibility != "public":
            return json({"error": "Access denied"}, status=403)

        count = await _get_member_count(db, eco.id)
        detail = _ecosystem_to_detail(eco, count)

    return json(detail.model_dump(mode="json"))


@ecosystems_api_bp.post("/")
async def create_ecosystem(request: Request):
    """Create a new ecosystem and add the current member to it.

    Accepts JSON: EcosystemCreateRequest
    Returns JSON: EcosystemDetail with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = EcosystemCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    # Sanitize website URL
    website = create_req.website
    if website and not website.startswith("https://"):
        if website.startswith("http://"):
            website = "https://" + website[7:]
        elif not website.startswith("https://"):
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
        db.add(eco)
        await db.flush()

        # Add the creating member to this ecosystem
        user = getattr(request.ctx, "user", None)
        mid = f"did-{user.did[-12:]}" if user and user.did else f"usr-{str(member.id)[:12]}"
        new_member = Member(
            ecosystem_id=eco.id,
            user_id=user.id if user else member.user_id,
            member_id=mid,
            display_name=member.display_name,
            current_status="active",
        )
        db.add(new_member)
        await db.commit()

        detail = _ecosystem_to_detail(eco, 1)

    return json(detail.model_dump(mode="json"), status=201)


@ecosystems_api_bp.put("/<ecosystem_id:uuid>")
async def update_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Update an existing ecosystem.

    Verifies the member belongs to this ecosystem.
    Accepts JSON: EcosystemUpdateRequest
    Returns JSON: EcosystemDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = EcosystemUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        # Verify membership
        eco_ids = await _get_member_ecosystem_ids(db, member)
        if ecosystem_id not in eco_ids:
            return json({"error": "Access denied"}, status=403)

        # Verify steward role: must be steward of any domain in this ecosystem
        # Resolve the authenticated user to a member id within this ecosystem
        member_row = await db.execute(
            select(Member.id).where(
                Member.user_id == member.user_id,
                Member.ecosystem_id == ecosystem_id,
            ).limit(1)
        )
        local_member_id = member_row.scalar_one_or_none()

        is_steward = False
        if local_member_id is not None:
            steward_check = await db.execute(
                select(Domain.id).where(
                    Domain.ecosystem_id == ecosystem_id,
                    Domain.steward_id == local_member_id,
                ).limit(1)
            )
            is_steward = steward_check.scalar_one_or_none() is not None

        if not is_steward:
            # Also allow if member is the only member (ecosystem creator)
            member_count = await _get_member_count(db, ecosystem_id)
            if member_count > 1:
                return json(
                    {"error": "Only ecosystem stewards can update ecosystem settings"},
                    status=403,
                )

        # Update fields that are not None
        update_data = update_req.model_dump(exclude_none=True)
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
    """Join an ecosystem.

    Creates an active member record for the authenticated user (auto-approved).
    Returns JSON: {"status": "joined", "message": "..."}
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        # Check if already a member
        user = getattr(request.ctx, "user", None)
        user_id = user.id if user else member.user_id
        existing = await db.execute(
            select(Member.id).where(
                Member.ecosystem_id == ecosystem_id,
                Member.user_id == user_id,
            ).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            return json({"error": "Already a member of this ecosystem"}, status=409)

        # Auto-approve: create an active member record immediately
        mid = f"did-{user.did[-12:]}" if user and user.did else f"usr-{str(member.id)[:12]}"
        new_member = Member(
            ecosystem_id=ecosystem_id,
            user_id=user_id,
            member_id=mid,
            display_name=member.display_name,
            current_status="active",
            onboarding_status="complete",
        )
        db.add(new_member)
        await db.commit()

    return json({
        "status": "joined",
        "message": f"Welcome to {eco.name}! You are now an active member.",
    }, status=201)


# --- Ecosystem Quiz Endpoints ---


@ecosystems_api_bp.get("/<ecosystem_id:uuid>/quizzes")
async def list_ecosystem_quizzes(request: Request, ecosystem_id: uuid.UUID):
    """List quizzes assigned to an ecosystem.

    Returns JSON: {"quizzes": [...]}
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

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
async def assign_quiz_to_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Assign a quiz to an ecosystem.

    Accepts JSON: {"quiz_id": "...", "is_entry_quiz": true/false}
    Returns JSON: {"status": "assigned", "quiz_id": "...", "is_entry_quiz": ...}
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    quiz_id_str = body.get("quiz_id")
    is_entry_quiz = body.get("is_entry_quiz", False)

    if not quiz_id_str:
        return json({"error": "quiz_id is required"}, status=400)

    try:
        quiz_id = uuid.UUID(quiz_id_str)
    except ValueError:
        return json({"error": "Invalid quiz_id"}, status=400)

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        # Verify membership
        eco_ids = await _get_member_ecosystem_ids(db, member)
        if ecosystem_id not in eco_ids:
            return json({"error": "Access denied"}, status=403)

        quiz = await db.get(Quiz, quiz_id)
        if quiz is None:
            return json({"error": "Quiz not found"}, status=404)

        # If marking as entry quiz, clear any existing entry quiz for this ecosystem
        if is_entry_quiz:
            existing_entry = await db.execute(
                select(Quiz).where(
                    Quiz.ecosystem_id == ecosystem_id,
                    Quiz.is_entry_quiz == True,  # noqa: E712
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


@ecosystems_api_bp.get("/<ecosystem_id:uuid>/quiz-results")
async def ecosystem_quiz_results(request: Request, ecosystem_id: uuid.UUID):
    """View quiz results for all quizzes assigned to this ecosystem.

    Returns JSON: {"results": [...]}
    Each result includes member display_name and quiz title.
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        # Verify membership
        eco_ids = await _get_member_ecosystem_ids(db, member)
        if ecosystem_id not in eco_ids:
            return json({"error": "Access denied"}, status=403)

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
