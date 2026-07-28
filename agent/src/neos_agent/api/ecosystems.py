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

from .helpers import _escape_like, require_auth
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
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    except (ValueError, TypeError):
        return json({"error": "Invalid pagination parameters"}, status=400)
    offset = (page - 1) * per_page

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

    Creates a pending member when agreement consent is a participation gate.
    The member becomes active after attesting to each required agreement.
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

        # A gate is evaluated only after a member identity exists so consent is
        # self-attested, auditable, and bound to this ecosystem membership.
        mid = f"did-{user.did[-12:]}" if user and user.did else f"usr-{str(member.id)[:12]}"
        new_member = Member(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            user_id=user_id,
            member_id=mid,
            display_name=member.display_name,
            current_status="pending_consent",
            onboarding_status="agreement_consent_required",
        )
        db.add(new_member)
        await db.flush()
        missing = await missing_agreement_consents(
            db, new_member.id, ecosystem_id, "ecosystem"
        )
        if not missing:
            new_member.current_status = "active"
            new_member.onboarding_status = "complete"
        await db.commit()

        eco_name = eco.name

    if missing:
        return json({
            "status": "consent_required",
            "message": f"Consent to the ecosystem agreements before participating in {eco_name}.",
            "required_agreements": [
                {"id": str(agreement.id), "title": agreement.title, "version": agreement.version}
                for agreement in missing
            ],
        }, status=201)
    return json({
        "status": "joined",
        "message": f"Welcome to {eco_name}! You are now an active member.",
        "required_agreements": [],
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


@ecosystems_api_bp.post("/<ecosystem_id:uuid>/quizzes/unassign")
async def unassign_quiz_from_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Unassign a quiz from an ecosystem.

    Accepts JSON: {"quiz_id": "..."}
    Clears the quiz's ecosystem_id and is_entry_quiz flag.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    quiz_id_str = body.get("quiz_id")
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

        eco_ids = await _get_member_ecosystem_ids(db, member)
        if ecosystem_id not in eco_ids:
            return json({"error": "Access denied"}, status=403)

        quiz = await db.get(Quiz, quiz_id)
        if quiz is None or quiz.ecosystem_id != ecosystem_id:
            return json({"error": "Quiz not found in this ecosystem"}, status=404)

        quiz.ecosystem_id = None
        quiz.is_entry_quiz = False
        await db.commit()

    return json({"status": "unassigned", "quiz_id": str(quiz_id)})


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


# ---------------------------------------------------------------------------
# Shares & Needs — Ecosystem-scoped
# ---------------------------------------------------------------------------


@ecosystems_api_bp.get("/<ecosystem_id:uuid>/shares-needs")
async def list_ecosystem_shares_needs(request: Request, ecosystem_id: uuid.UUID):
    """GET /api/v1/ecosystems/:id/shares-needs -- List shares & needs for this ecosystem.

    Returns all items (not just public/active) so members can manage them.
    Query params: type, category, status
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        eco_ids = await _get_member_ecosystem_ids(db, member)
        if ecosystem_id not in eco_ids:
            return json({"error": "Access denied"}, status=403)

        filters = [SharesNeeds.ecosystem_id == ecosystem_id]
        type_filter = request.args.get("type")
        if type_filter:
            filters.append(SharesNeeds.type == type_filter)
        category_filter = request.args.get("category")
        if category_filter:
            filters.append(SharesNeeds.category == category_filter)
        status_filter = request.args.get("status")
        if status_filter:
            filters.append(SharesNeeds.status == status_filter)

        stmt = (
            select(SharesNeeds)
            .where(*filters)
            .order_by(SharesNeeds.created_at.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()

        # Bulk-load domain names
        domain_ids = list({r.domain_id for r in rows if r.domain_id})
        domain_names: dict[uuid.UUID, str] = {}
        if domain_ids:
            d_rows = await db.execute(
                select(Domain.id, Domain.domain_id).where(Domain.id.in_(domain_ids))
            )
            for d in d_rows.all():
                domain_names[d.id] = d.domain_id

        items = [
            {
                "id": str(r.id),
                "ecosystem_id": str(r.ecosystem_id),
                "domain_id": str(r.domain_id),
                "domain_name": domain_names.get(r.domain_id),
                "type": r.type,
                "title": r.title,
                "description": r.description,
                "category": r.category,
                "capacity": r.capacity,
                "tags": r.tags if isinstance(r.tags, list) else [],
                "visibility": r.visibility,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    return json({"items": items})
