"""JSON API blueprint for domain management.

Blueprint: domains_api_bp, url_prefix="/api/v1/domains"

Manages governance domains including their elements, metrics,
and stewardship assignments.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import re
import uuid
import datetime as _dt
from typing import Optional

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.api.schemas.domains import (
    DomainCreateRequest,
    DomainDetail,
    DomainElementSchema,
    DomainListItem,
    DomainMetricSchema,
    DomainUpdateRequest,
)
from neos_agent.db.models import (
    Domain,
    DomainElement,
    DomainMetric,
    Member,
)
from neos_agent.db.course_models import Quiz, QuizResult
from neos_agent.api.helpers import require_auth, get_ecosystem_ids, apply_ecosystem_filter, apply_ecosystem_name_filter, serialize_shared_ecosystem_ids, build_search_filter
from neos_agent.services.fingerprint import generate_fingerprint

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

domains_api_bp = Blueprint("domains_api", url_prefix="/api/v1/domains")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


def _domain_to_list_item(d: Domain) -> dict:
    return DomainListItem(
        id=d.id,
        domain_id=d.domain_id,
        version=d.version,
        status=d.status,
        purpose=d.purpose,
        current_steward=d.current_steward,
        parent_domain_id=d.parent_domain_id,
        created_at=d.created_at,
        version_fingerprint=d.version_fingerprint,
    ).model_dump(mode="json")


def _domain_to_detail(d: Domain) -> dict:
    return DomainDetail(
        id=d.id,
        domain_id=d.domain_id,
        version=d.version,
        status=d.status,
        purpose=d.purpose,
        current_steward=d.current_steward,
        parent_domain_id=d.parent_domain_id,
        created_at=d.created_at,
        version_fingerprint=d.version_fingerprint,
        ecosystem_id=d.ecosystem_id,
        steward_id=d.steward_id,
        created_by=d.created_by,
        metric_definitions=d.metric_definitions,
        elements=d.elements,
        updated_at=d.updated_at,
        domain_elements=[
            DomainElementSchema(
                id=e.id,
                element_name=e.element_name,
                element_value=e.element_value,
            )
            for e in (d.domain_elements or [])
        ],
        domain_metrics=[
            DomainMetricSchema(
                id=m.id,
                metric=m.metric,
                target=m.target,
                measurement_method=m.measurement_method,
            )
            for m in (d.domain_metrics or [])
        ],
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@domains_api_bp.get("/")
async def list_domains(request: Request):
    """GET /api/v1/domains -- Paginated domain list with filtering.

    Query params: status, q (search domain_id/purpose),
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
        stmt = select(Domain).order_by(Domain.created_at.desc())

        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Domain, eco_ids)
        stmt = apply_ecosystem_name_filter(stmt, Domain, request)

        status = request.args.get("status")
        if status:
            stmt = stmt.where(Domain.status == status)

        search = request.args.get("q")
        if search:
            stmt = stmt.where(build_search_filter(
                Domain, search, Domain.domain_id, Domain.purpose
            ))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        domains = result.scalars().all()

    return json({
        "items": [_domain_to_list_item(d) for d in domains],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@domains_api_bp.get("/<domain_id:uuid>")
async def get_domain(request: Request, domain_id: uuid.UUID):
    """GET /api/v1/domains/:id -- Domain detail with elements and metrics."""
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(Domain)
            .options(
                selectinload(Domain.domain_elements),
                selectinload(Domain.domain_metrics),
            )
            .where(Domain.id == domain_id)
        )
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Domain, eco_ids)

        result = await session.execute(stmt)
        d = result.scalar_one_or_none()

    if d is None:
        return json({"error": "Domain not found"}, status=404)

    return json(_domain_to_detail(d))


@domains_api_bp.post("/")
async def create_domain(request: Request):
    """POST /api/v1/domains -- Create a new domain.

    Accepts JSON: DomainCreateRequest
    Returns JSON: DomainDetail with 201 status.
    """
    auth_member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = DomainCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    domain_id_str = f"DOM-{short_id}"

    async with request.app.ctx.db() as session:
        domain = Domain(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            domain_id=domain_id_str,
            version="1.0",
            status="active",
            purpose=create_req.purpose,
            current_steward=create_req.current_steward,
            steward_id=create_req.steward_id,
            parent_domain_id=create_req.parent_domain_id,
            created_by=create_req.created_by,
            metric_definitions=create_req.metric_definitions,
            elements=create_req.elements,
        )
        domain.version_fingerprint = generate_fingerprint(
            domain.domain_id, domain.purpose or "", domain.version, domain.status
        )
        session.add(domain)
        await session.commit()

        # Reload with relationships
        stmt = (
            select(Domain)
            .options(
                selectinload(Domain.domain_elements),
                selectinload(Domain.domain_metrics),
            )
            .where(Domain.id == domain.id)
        )
        result = await session.execute(stmt)
        domain = result.scalar_one()

    return json(_domain_to_detail(domain), status=201)


@domains_api_bp.put("/<domain_id:uuid>")
async def update_domain(request: Request, domain_id: uuid.UUID):
    """PUT /api/v1/domains/:id -- Update non-None fields of a domain."""
    auth_member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = DomainUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(Domain).where(Domain.id == domain_id)
        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, Domain, eco_ids)

        result = await session.execute(stmt)
        d = result.scalar_one_or_none()
        if d is None:
            return json({"error": "Domain not found"}, status=404)

        update_data = update_req.model_dump(exclude_none=True)
        if "shared_ecosystem_ids" in update_data:
            update_data["shared_ecosystem_ids"] = serialize_shared_ecosystem_ids(
                update_req.shared_ecosystem_ids
            )
        for field, value in update_data.items():
            setattr(d, field, value)

        d.version_fingerprint = generate_fingerprint(
            d.domain_id, d.purpose or "", d.version, d.status
        )

        await session.commit()

        # Reload with relationships
        stmt = (
            select(Domain)
            .options(
                selectinload(Domain.domain_elements),
                selectinload(Domain.domain_metrics),
            )
            .where(Domain.id == d.id)
        )
        result = await session.execute(stmt)
        d = result.scalar_one()

    return json(_domain_to_detail(d))


# ---------------------------------------------------------------------------
# Domain Quiz Management
# ---------------------------------------------------------------------------


@domains_api_bp.get("/<domain_id_q:uuid>/quizzes")
async def list_domain_quizzes(request: Request, domain_id_q: uuid.UUID):
    """GET /api/v1/domains/:id/quizzes -- List quizzes assigned to this domain."""
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        stmt = (
            select(Quiz)
            .where(Quiz.domain_id == domain_id_q)
            .order_by(Quiz.is_entry_quiz.desc(), Quiz.created_at.desc())
        )
        result = await session.execute(stmt)
        quizzes = result.scalars().all()

    items = []
    for q in quizzes:
        items.append({
            "id": str(q.id),
            "title": q.title,
            "description": q.description,
            "mode": q.mode,
            "is_published": q.is_published,
            "is_entry_quiz": q.is_entry_quiz,
            "time_limit": q.time_limit,
            "passing_score": q.passing_score,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })

    return json({"items": items, "total": len(items)})


@domains_api_bp.post("/<domain_id_a:uuid>/quizzes/assign")
async def assign_quiz_to_domain(request: Request, domain_id_a: uuid.UUID):
    """POST /api/v1/domains/:id/quizzes/assign -- Assign a quiz to this domain.

    Accepts JSON: {"quiz_id": "...", "is_entry_quiz": true/false}
    """
    auth_member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    quiz_id_str = body.get("quiz_id")
    is_entry = body.get("is_entry_quiz", False)

    if not quiz_id_str:
        return json({"error": "quiz_id is required"}, status=400)

    try:
        quiz_id = uuid.UUID(quiz_id_str)
    except ValueError:
        return json({"error": "Invalid quiz_id"}, status=400)

    async with request.app.ctx.db() as session:
        domain = await session.get(Domain, domain_id_a)
        if domain is None:
            return json({"error": "Domain not found"}, status=404)

        quiz = await session.get(Quiz, quiz_id)
        if quiz is None:
            return json({"error": "Quiz not found"}, status=404)

        if is_entry:
            from sqlalchemy import update
            await session.execute(
                update(Quiz)
                .where(Quiz.domain_id == domain_id_a, Quiz.is_entry_quiz == True)
                .values(is_entry_quiz=False)
            )

        quiz.domain_id = domain_id_a
        quiz.is_entry_quiz = is_entry
        await session.commit()

    return json({"success": True, "quiz_id": str(quiz_id), "domain_id": str(domain_id_a)})


@domains_api_bp.get("/<domain_id_r:uuid>/quiz-results")
async def domain_quiz_results(request: Request, domain_id_r: uuid.UUID):
    """GET /api/v1/domains/:id/quiz-results -- View quiz results for domain quizzes."""
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        quiz_stmt = select(Quiz.id, Quiz.title).where(Quiz.domain_id == domain_id_r)
        quiz_rows = await session.execute(quiz_stmt)
        quiz_map = {row.id: row.title for row in quiz_rows}

        if not quiz_map:
            return json({"items": [], "total": 0})

        result_stmt = (
            select(QuizResult)
            .where(QuizResult.quiz_id.in_(list(quiz_map.keys())))
            .order_by(QuizResult.created_at.desc())
        )
        results = (await session.execute(result_stmt)).scalars().all()

        member_ids = list({r.member_id for r in results if r.member_id})
        member_names: dict[uuid.UUID, str] = {}
        if member_ids:
            m_rows = await session.execute(
                select(Member.id, Member.display_name).where(Member.id.in_(member_ids))
            )
            for m in m_rows:
                member_names[m.id] = m.display_name

        items = []
        for r in results:
            items.append({
                "id": str(r.id),
                "quiz_id": str(r.quiz_id),
                "quiz_title": quiz_map.get(r.quiz_id, "Unknown"),
                "member_id": str(r.member_id) if r.member_id else None,
                "member_name": member_names.get(r.member_id) if r.member_id else None,
                "score": r.score,
                "passed": r.passed,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

    return json({"items": items, "total": len(items)})
