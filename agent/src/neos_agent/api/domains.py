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
    DomainParticipantSchema,
    DomainUpdateRequest,
)
from neos_agent.db.models import (
    DecisionRecord,
    Domain,
    CircleMembership,
    DomainElement,
    DomainMetric,
    Member,
    SharesNeeds,
)
from neos_agent.db.course_models import Quiz, QuizResult
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import get_ecosystem_ids, apply_ecosystem_name_filter, parse_pagination, serialize_shared_ecosystem_ids, build_search_filter
from neos_agent.api.policy import can_create_domain, can_edit_domain, is_domain_steward, is_profile_admin
from neos_agent.api.policy import can_change_domain_authority, is_active_member_in  # G-Maint
from neos_agent.api.policy import can_manage_onboarding  # domain quiz results
from neos_agent.services import dates  # G-Maint
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.services.fingerprint import generate_fingerprint
from neos_agent.services.agreement_consent import missing_agreement_consents

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


# Naming and caller flags: see api/AGENTS.md "Domain naming and participation flags".
NAME_SEPARATOR = " — "
MAX_DERIVED_NAME = 120
CREATE_DENIED = "Only an ecosystem steward (moderator or above) can create a domain"
EDIT_DENIED = "Only this domain's steward or an ecosystem steward can edit this domain"
# G-Maint (C10): who holds a domain and whether it continues are the delegating body's call, recorded with a reason.
AUTHORITY_DENIED = ("Only a steward of this ecosystem who does not steward this domain can change its steward or "
                    "status (a domain's own steward cannot hand it on or end it alone).")
REASON_REQUIRED = "Give a reason for changing the domain's steward or status (at least 8 characters); it is recorded."
AUTHORITY_FIELDS = {"steward_id": "role-transfer", "status": "role-sunset"}
# FX-Maint: the shown steward name follows steward_id (api/AGENTS.md "Domain steward and status").
NEW_STEWARD_INVALID = "The steward must be an active member of this ecosystem."
STEWARD_NAME_FOLLOWS = ("The steward's name follows the member chosen as steward: choose a member as the new steward "
                        "(with a reason) instead of typing a name.")


def domain_display_name(d) -> str:
    """name -> the purpose's leading "Name — " segment -> the generated domain_id."""
    name = (getattr(d, "name", None) or "").strip()
    if name:
        return name
    purpose = d.purpose or ""
    if NAME_SEPARATOR in purpose:
        head = purpose.split(NAME_SEPARATOR, 1)[0].strip()
        if 1 <= len(head) <= MAX_DERIVED_NAME:
            return head
    return d.domain_id


def _clean_name(value: str | None) -> str | None:
    return (value or "").strip() or None


# Loader options shared by every handler that serializes a full domain.
_DETAIL_OPTIONS = (selectinload(Domain.domain_elements), selectinload(Domain.domain_metrics))


def _domain_to_list_item(d: Domain, *, is_participant: bool = False, is_steward: bool = False,
                         steward_name: str | None = None) -> dict:
    return DomainListItem(
        id=d.id,
        ecosystem_id=d.ecosystem_id,
        domain_id=d.domain_id,
        name=getattr(d, "name", None),
        display_name=domain_display_name(d),
        version=d.version,
        status=d.status,
        purpose=d.purpose,
        current_steward=steward_name or d.current_steward,  # FX-Maint: the steward_id member's name when set
        parent_domain_id=d.parent_domain_id,
        created_at=d.created_at,
        version_fingerprint=d.version_fingerprint,
        caller_is_participant=is_participant,
        caller_is_steward=is_steward,
    ).model_dump(mode="json")


def _domain_to_detail(
    d: Domain,
    *,
    is_participant: bool = False,
    is_steward: bool = False,
    can_edit: bool = False,
    participants: list[DomainParticipantSchema] | None = None,
    steward_name: str | None = None,
) -> dict:
    participants = participants or []
    return DomainDetail(
        id=d.id,
        domain_id=d.domain_id,
        name=getattr(d, "name", None),
        display_name=domain_display_name(d),
        version=d.version,
        status=d.status,
        purpose=d.purpose,
        current_steward=steward_name or d.current_steward,  # FX-Maint: the steward_id member's name when set
        parent_domain_id=d.parent_domain_id,
        created_at=d.created_at,
        version_fingerprint=d.version_fingerprint,
        caller_is_participant=is_participant,
        caller_is_steward=is_steward,
        caller_can_edit=can_edit,
        participants=participants,
        participant_count=len(participants),
        ecosystem_id=d.ecosystem_id,
        shared_ecosystem_ids=d.shared_ecosystem_ids,
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


async def _domain_detail_payload(session, request: Request, d: Domain) -> dict:
    """Detail JSON plus the caller's standing and the active participant roster."""
    caller = await caller_in(session, request, d.ecosystem_id)
    rows = (await session.execute(
        select(CircleMembership.member_id, CircleMembership.role, Member.display_name)
        .join(Member, Member.id == CircleMembership.member_id)
        .where(CircleMembership.domain_id == d.id, CircleMembership.status == "active")
        .order_by(Member.display_name)
    )).all()
    participants = [
        DomainParticipantSchema(member_id=row.member_id, display_name=row.display_name, role=row.role)
        for row in rows
    ]
    payload = _domain_to_detail(
        d,
        is_participant=caller is not None and any(p.member_id == caller.id for p in participants),
        is_steward=is_domain_steward(caller, d),
        can_edit=can_edit_domain(caller, d),
        participants=participants,
        steward_name=(await _steward_names(session, [d])).get(d.steward_id),
    )
    # FX-Maint: the form offers the steward and status fields only to who may change them (with a reason).
    payload["caller_can_change_authority"] = can_change_domain_authority(caller, d)
    return payload


async def _steward_names(session, domains) -> dict:
    """steward_id -> that member's display name: what members see as a domain's steward follows steward_id."""
    ids = {d.steward_id for d in domains if d.steward_id is not None}
    if not ids:
        return {}
    return dict((await session.execute(select(Member.id, Member.display_name).where(Member.id.in_(ids)))).all())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@domains_api_bp.get("/")
@authenticated
async def list_domains(request: Request):
    """GET /api/v1/domains -- Paginated domain list with filtering.

    Query params: status, q (search name/domain_id/purpose),
    page (default 1), per_page (default 25, max 100).
    Items carry caller_is_participant / caller_is_steward; the envelope
    carries caller_can_create (mod+ in a scoped ecosystem).
    """
    member = request.ctx.member

    eco_ids = get_ecosystem_ids(request)
    page_request = parse_pagination(request)
    page, per_page = page_request.page, page_request.per_page

    async with request.app.ctx.db() as session:
        stmt = select(Domain).order_by(Domain.created_at.desc())

        stmt = restrict_to_ecosystems(stmt, Domain, eco_ids)
        stmt = apply_ecosystem_name_filter(stmt, Domain, request)

        status = request.args.get("status")
        if status:
            stmt = stmt.where(Domain.status == status)

        search = request.args.get("q")
        if search:
            stmt = stmt.where(build_search_filter(
                Domain, search, Domain.name, Domain.domain_id, Domain.purpose
            ))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(page_request.offset).limit(per_page)
        result = await session.execute(stmt)
        domains = result.scalars().all()

        # Caller standing: one query for the caller's member rows, one IN
        # query for their active participation across this page.
        caller_rows = []
        if member.user_id is not None:
            caller_rows = (await session.scalars(
                select(Member).where(Member.user_id == member.user_id)
            )).all()
        caller_member_ids = {row.id for row in caller_rows}
        participating: set[uuid.UUID] = set()
        if caller_member_ids and domains:
            participating = set((await session.execute(
                select(CircleMembership.domain_id).where(
                    CircleMembership.domain_id.in_([d.id for d in domains]),
                    CircleMembership.member_id.in_(caller_member_ids),
                    CircleMembership.status == "active",
                )
            )).scalars())
        scope = set(eco_ids)
        caller_can_create = any(
            row.ecosystem_id in scope and can_create_domain(row)
            for row in caller_rows
        )
        steward_names = await _steward_names(session, domains)

    return json({
        "items": [
            _domain_to_list_item(
                d,
                is_participant=d.id in participating,
                is_steward=d.steward_id is not None and d.steward_id in caller_member_ids,
                steward_name=steward_names.get(d.steward_id),
            )
            for d in domains
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "caller_can_create": caller_can_create,
    })


@domains_api_bp.get("/<domain_id:uuid>")
@authenticated
async def get_domain(request: Request, domain_id: uuid.UUID):
    """GET /api/v1/domains/:id -- Domain detail with elements and metrics."""
    async with request.app.ctx.db() as session:
        d = await get_scoped_or_404(session, request, Domain, domain_id, options=_DETAIL_OPTIONS, label="Domain")
        payload = await _domain_detail_payload(session, request, d)

    return json(payload)


@domains_api_bp.post("/")
@authenticated
async def create_domain(request: Request):
    """POST /api/v1/domains -- Create a new domain.

    Accepts JSON: DomainCreateRequest
    Returns JSON: DomainDetail with 201 status.
    """
    body = request.json or {}
    try:
        create_req = DomainCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    if create_req.ecosystem_id not in get_ecosystem_ids(request):
        raise ApiError(403, "Access denied: ecosystem not in scope")

    async with request.app.ctx.db() as session:
        if not can_create_domain(await caller_in(session, request, create_req.ecosystem_id)):
            raise ApiError(403, CREATE_DENIED)
        steward_name = create_req.current_steward
        if create_req.steward_id is not None:  # FX-Maint: the shown name follows the chosen member
            steward = await session.get(Member, create_req.steward_id)
            if not is_active_member_in(steward, create_req.ecosystem_id):
                raise ApiError(400, NEW_STEWARD_INVALID, {"code": "STEWARD_INVALID", "field": "steward_id"})
            steward_name = steward.display_name

    short_id = uuid.uuid4().hex[:8].upper()
    domain_id_str = f"DOM-{short_id}"

    async with request.app.ctx.db() as session:
        domain = Domain(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            domain_id=domain_id_str,
            name=_clean_name(create_req.name),
            version="1.0",
            status="active",
            purpose=create_req.purpose,
            current_steward=steward_name,
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
        domain = (await session.execute(
            select(Domain).options(*_DETAIL_OPTIONS).where(Domain.id == domain.id)
        )).scalar_one()
        payload = await _domain_detail_payload(session, request, domain)

    return json(payload, status=201)


async def _authority_records(session, d: Domain, caller: Member | None, update_data: dict,
                             reason: str | None) -> list[DecisionRecord]:
    """Changing the steward or status: policy.can_change_domain_authority plus a reason; one DecisionRecord per change.

    A new steward must be an active member of the domain's ecosystem; `current_steward` follows their name.
    """
    changes = {field: update_data[field] for field in AUTHORITY_FIELDS
               if field in update_data and update_data[field] != getattr(d, field)}
    if not changes:
        return []
    if not can_change_domain_authority(caller, d):
        raise ApiError(403, AUTHORITY_DENIED, {"code": "DOMAIN_AUTHORITY_DENIED"})
    reason = (reason or "").strip()
    if len(reason) < 8:
        raise ApiError(400, REASON_REQUIRED, {"code": "REASON_REQUIRED"})
    label = domain_display_name(d)
    records = []
    if "steward_id" in changes:
        new_steward = await session.get(Member, changes["steward_id"])
        if not is_active_member_in(new_steward, d.ecosystem_id):
            raise ApiError(400, NEW_STEWARD_INVALID, {"code": "STEWARD_INVALID", "field": "steward_id"})
        old_name = await session.scalar(select(Member.display_name).where(Member.id == d.steward_id)) if d.steward_id else None
        update_data["current_steward"] = new_steward.display_name
        holding = f"Stewardship of the domain “{label}” moved from {old_name or 'nobody'} to {new_steward.display_name}."
        records.append(("steward_id", holding))
    if "status" in changes:
        records.append(("status", f"The domain “{label}” changed status from {d.status} to {changes['status']}."))
    return [DecisionRecord(
        id=uuid.uuid4(), ecosystem_id=d.ecosystem_id, record_id=f"DEC-DOM-{uuid.uuid4().hex[:8].upper()}",
        date=dates.utc_today(), holding=holding, ratio_decidendi=reason,
        deliberation_summary=f"Recorded by {caller.display_name}, a steward of the ecosystem, when the domain was edited.",
        source_skill=AUTHORITY_FIELDS[field], source_layer=2, artifact_type="domain", artifact_reference=d.domain_id,
        domain=label, precedent_level="domain", status="active", recorder=caller.display_name,
        recorder_role="ecosystem steward",
    ) for field, holding in records]


@domains_api_bp.put("/<domain_id:uuid>")
@authenticated
async def update_domain(request: Request, domain_id: uuid.UUID):
    """PUT /api/v1/domains/:id -- Update non-None fields of a domain."""
    body = request.json or {}
    try:
        update_req = DomainUpdateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        d = await get_scoped_or_404(session, request, Domain, domain_id, label="Domain")

        caller = await caller_in(session, request, d.ecosystem_id)
        if not can_edit_domain(caller, d):
            raise ApiError(403, EDIT_DENIED)

        update_data = update_req.model_dump(exclude_none=True, exclude={"reason"})
        if "current_steward" in update_data:  # FX-Maint: never a free-text rename of who members see as steward
            shown = (await _steward_names(session, [d])).get(d.steward_id) or d.current_steward
            if (update_data.pop("current_steward") or "").strip() != (shown or "").strip():
                raise ApiError(400, STEWARD_NAME_FOLLOWS, {"code": "STEWARD_NAME_FOLLOWS", "field": "current_steward"})
        records = await _authority_records(session, d, caller, update_data, update_req.reason)
        if "name" in body:
            # Present-and-empty (or null) clears the name back to the derived label.
            update_data["name"] = _clean_name(update_req.name)
        if "shared_ecosystem_ids" in update_data:
            update_data["shared_ecosystem_ids"] = serialize_shared_ecosystem_ids(
                update_req.shared_ecosystem_ids
            )
        for field, value in update_data.items():
            setattr(d, field, value)

        d.version_fingerprint = generate_fingerprint(
            d.domain_id, d.purpose or "", d.version, d.status
        )
        session.add_all(records)

        await session.commit()

        # Reload with relationships
        d = (await session.execute(
            select(Domain).options(*_DETAIL_OPTIONS).where(Domain.id == d.id)
        )).scalar_one()
        payload = await _domain_detail_payload(session, request, d)

    return json(payload)


# ---------------------------------------------------------------------------
# Domain participation
# ---------------------------------------------------------------------------


@domains_api_bp.post("/<domain_id:uuid>/participation")
@authenticated
async def join_domain_participation(request: Request, domain_id: uuid.UUID):
    """Join a domain after satisfying its ecosystem's agreement gates."""
    body = request.json or {}
    role = body.get("role", "member")
    if role != "member":
        raise ApiError(403, "Participation grants member access; stewardship roles require a separate governance action")

    async with request.app.ctx.db() as session:
        domain = await get_scoped_or_404(session, request, Domain, domain_id, label="Domain")
        local_member = await caller_in(session, request, domain.ecosystem_id)
        if local_member is None or local_member.current_status != "active":
            raise ApiError(403, "Active ecosystem membership is required for domain participation")

        missing = await missing_agreement_consents(
            session, local_member.id, domain.ecosystem_id, "domain", domain.id
        )
        if missing:
            raise ApiError(409, "Agreement consent is required before domain participation", {
                "required_agreements": [
                    {"id": str(agreement.id), "title": agreement.title, "version": agreement.version}
                    for agreement in missing
                ],
            })

        participation = await session.scalar(select(CircleMembership).where(
            CircleMembership.domain_id == domain.id,
            CircleMembership.member_id == local_member.id,
        ))
        if participation is None:
            participation = CircleMembership(
                id=uuid.uuid4(), domain_id=domain.id, member_id=local_member.id,
                role=role, status="active", joined_date=_dt.date.today(),
            )
            session.add(participation)
        else:
            participation.status = "active"
        await session.commit()

    return json({
        "status": "joined",
        "domain_id": str(domain_id),
        "member_id": str(local_member.id),
        "role": role,
    }, status=201)


# ---------------------------------------------------------------------------
# Domain Quiz Management
# ---------------------------------------------------------------------------


@domains_api_bp.get("/<domain_id_q:uuid>/quizzes")
@authenticated
async def list_domain_quizzes(request: Request, domain_id_q: uuid.UUID):
    """GET /api/v1/domains/:id/quizzes -- List quizzes assigned to this domain."""
    async with request.app.ctx.db() as session:
        await get_scoped_or_404(session, request, Domain, domain_id_q, label="Domain")
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
@authenticated
async def assign_quiz_to_domain(request: Request, domain_id_a: uuid.UUID):
    """POST /api/v1/domains/:id/quizzes/assign -- Assign a quiz to this domain.

    Accepts JSON: {"quiz_id": "...", "is_entry_quiz": true/false}
    """
    body = request.json or {}
    quiz_id_str = body.get("quiz_id")
    is_entry = body.get("is_entry_quiz", False)

    if not quiz_id_str:
        raise ApiError(400, "quiz_id is required")

    try:
        quiz_id = uuid.UUID(quiz_id_str)
    except ValueError:
        raise ApiError(400, "Invalid quiz_id") from None

    async with request.app.ctx.db() as session:
        domain = await get_scoped_or_404(session, request, Domain, domain_id_a, label="Domain")
        from neos_agent.api.quizzes import copy_quiz, quiz_steward_or_error  # FX-Onboard A2/A9
        steward = await quiz_steward_or_error(session, request, domain.ecosystem_id)

        quiz = await session.get(Quiz, quiz_id, with_for_update=True)
        if quiz is None:
            raise ApiError(404, "Quiz not found")
        if quiz.ecosystem_id not in (None, domain.ecosystem_id):  # never take another ecosystem's quiz
            raise ApiError(403, "That quiz belongs to another ecosystem")
        if quiz.ecosystem_id is None:  # a shared quiz stays shared: the domain gets its own copy
            quiz = copy_quiz(quiz, ecosystem_id=domain.ecosystem_id, domain_id=domain_id_a, created_by=steward.id)
            session.add(quiz)
            quiz_id = quiz.id

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


@domains_api_bp.post("/<domain_id_u:uuid>/quizzes/unassign")
@authenticated
async def unassign_quiz_from_domain(request: Request, domain_id_u: uuid.UUID):
    """POST /api/v1/domains/:id/quizzes/unassign -- Unassign a quiz from this domain.

    Accepts JSON: {"quiz_id": "..."}
    """
    body = request.json or {}
    quiz_id_str = body.get("quiz_id")
    if not quiz_id_str:
        raise ApiError(400, "quiz_id is required")

    try:
        quiz_id = uuid.UUID(quiz_id_str)
    except ValueError:
        raise ApiError(400, "Invalid quiz_id") from None

    async with request.app.ctx.db() as session:
        domain = await get_scoped_or_404(session, request, Domain, domain_id_u, label="Domain")
        from neos_agent.api.quizzes import quiz_steward_or_error  # FX-Onboard A2
        await quiz_steward_or_error(session, request, domain.ecosystem_id)

        quiz = await session.get(Quiz, quiz_id, with_for_update=True)
        if quiz is None or quiz.domain_id != domain_id_u:
            raise ApiError(404, "Quiz not found in this domain")

        quiz.domain_id = None
        quiz.is_entry_quiz = False
        await session.commit()

    return json({"success": True, "quiz_id": str(quiz_id)})


@domains_api_bp.get("/<domain_id_r:uuid>/quiz-results")
@authenticated
async def domain_quiz_results(request: Request, domain_id_r: uuid.UUID):
    """GET /api/v1/domains/:id/quiz-results -- the domain's quiz results: all of them for its ecosystem's stewards, else your own."""
    async with request.app.ctx.db() as session:
        domain = await get_scoped_or_404(session, request, Domain, domain_id_r, label="Domain")
        caller = await caller_in(session, request, domain.ecosystem_id)
        if caller is None:
            return json({"items": [], "total": 0})
        quiz_stmt = select(Quiz.id, Quiz.title).where(Quiz.domain_id == domain_id_r)
        quiz_rows = await session.execute(quiz_stmt)
        quiz_map = {row.id: row.title for row in quiz_rows}

        if not quiz_map:
            return json({"items": [], "total": 0})

        result_stmt = (
            select(QuizResult)
            .where(QuizResult.quiz_id.in_(list(quiz_map.keys())))
            .order_by(QuizResult.completed_at.desc())
        )
        if not can_manage_onboarding(caller, domain.ecosystem_id):  # results carry names: members see only their own
            result_stmt = result_stmt.where(QuizResult.member_id == caller.id)
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
                "passed": r.is_passed,
                "created_at": r.completed_at.isoformat() if r.completed_at else None,
            })

    return json({"items": items, "total": len(items)})


# ---------------------------------------------------------------------------
# Shares & Needs — Domain-scoped
# ---------------------------------------------------------------------------


@domains_api_bp.get("/<domain_id_sn:uuid>/shares-needs")
@authenticated
async def list_domain_shares_needs(request: Request, domain_id_sn: uuid.UUID):
    """GET /api/v1/domains/:id/shares-needs -- every status, under the one visibility rule (G-Exchange).

    Query params: type, category, status. Hidden posts appear only for their author and the ecosystem's stewards.
    """
    from neos_agent.api.guards import caller_user_id  # G-Exchange
    from neos_agent.services import exchange  # G-Exchange (it imports this module)

    async with request.app.ctx.db() as session:
        domain = await get_scoped_or_404(session, request, Domain, domain_id_sn, label="Domain")
        viewer = await exchange.load_viewer(session, caller_user_id(request))
        filters = [SharesNeeds.domain_id == domain.id, exchange.visible_clause(viewer)]
        for name in ("type", "category", "status"):
            if request.args.get(name):
                filters.append(getattr(SharesNeeds, name) == request.args.get(name))
        rows = (await session.execute(
            select(SharesNeeds).where(*filters).order_by(SharesNeeds.created_at.desc(), SharesNeeds.id)
        )).scalars().all()
        items = await exchange.publication_payloads(session, rows, viewer)

    return json({"items": items})
