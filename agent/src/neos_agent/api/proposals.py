"""JSON API blueprint for proposal management (ACT process).

Blueprint: proposals_api_bp, url_prefix="/api/v1/proposals"

Manages the full lifecycle of governance proposals through the three
ACT phases: Advice gathering, Consent rounds, and Test periods.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import uuid
from datetime import date, datetime

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    ConsentParticipant,
    ConsentRecord,
    Proposal,
    TestReport,
    TestSuccessCriterion,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas (kept here to avoid merge conflicts with schemas.py)
# ---------------------------------------------------------------------------


class ProposalListItem(BaseModel):
    id: uuid.UUID
    proposal_id: str
    type: str
    decision_type: str | None = None
    title: str
    version: str
    status: str
    proposer: str | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    created_at: datetime


class AdviceEntrySchema(BaseModel):
    id: uuid.UUID
    advisor: str
    role: str | None = None
    ethos: str | None = None
    advice_type: str | None = None
    content: str | None = None
    concerns: str | None = None
    date: date | None = None


class AdviceLogSchema(BaseModel):
    id: uuid.UUID
    advice_window_start: date | None = None
    advice_window_end: date | None = None
    urgency: str | None = None
    summary: str | None = None
    proposer_modifications: str | None = None
    entries: list[AdviceEntrySchema] = []


class ConsentParticipantSchema(BaseModel):
    id: uuid.UUID
    member_name: str
    position: str | None = None
    objection_text: str | None = None
    integration_attempted: bool | None = None
    integration_outcome: str | None = None
    date: date | None = None


class ConsentRecordSchema(BaseModel):
    id: uuid.UUID
    consent_mode: str
    weighting_model: str | None = None
    facilitator: str | None = None
    date: date | None = None
    quorum_required: str | None = None
    quorum_met: bool = False
    outcome: str | None = None
    escalation_level: str | None = None
    participants: list[ConsentParticipantSchema] = []


class TestSuccessCriterionSchema(BaseModel):
    id: uuid.UUID
    criterion: str | None = None
    metric: str | None = None
    baseline: str | None = None
    target: str | None = None
    actual: str | None = None
    met: bool | None = None


class TestReportSchema(BaseModel):
    id: uuid.UUID
    test_start_date: date | None = None
    test_end_date: date | None = None
    outcome: str | None = None
    observations: str | None = None
    midpoint_findings: str | None = None
    modifications: str | None = None
    next_action: str | None = None
    success_criteria_summary: str | None = None
    success_criteria: list[TestSuccessCriterionSchema] = []


class ProposalDetail(ProposalListItem):
    ecosystem_id: uuid.UUID
    co_sponsors: list[str] | None = None
    impacted_parties: list[str] | None = None
    proposed_change: str | None = None
    rationale: str | None = None
    created_date: date | None = None
    advice_deadline: date | None = None
    consent_deadline: date | None = None
    test_duration: str | None = None
    updated_at: datetime
    advice_logs: list[AdviceLogSchema] = []
    consent_records: list[ConsentRecordSchema] = []
    test_reports: list[TestReportSchema] = []


class ProposalCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    type: str
    title: str
    decision_type: str | None = None
    proposer: str | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    proposed_change: str | None = None
    rationale: str | None = None
    advice_deadline: date | None = None


class ProposalUpdateRequest(BaseModel):
    title: str | None = None
    proposed_change: str | None = None
    rationale: str | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    advice_deadline: date | None = None
    consent_deadline: date | None = None


class AdviceEntryCreateRequest(BaseModel):
    advisor: str
    role: str | None = None
    ethos: str | None = None
    advice_type: str | None = None
    content: str | None = None
    concerns: str | None = None


class ConsentPositionRequest(BaseModel):
    member_name: str
    position: str
    objection_text: str | None = None


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

proposals_api_bp = Blueprint("proposals_api", url_prefix="/api/v1/proposals")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Valid status transitions: current_status -> set of allowed next statuses
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"advice", "withdrawn"},
    "advice": {"consent", "withdrawn"},
    "consent": {"test", "withdrawn"},
    "test": {"ratified", "withdrawn"},
}


def _escape_like(value: str) -> str:
    """Escape special characters for SQL LIKE patterns."""
    return value.replace("%", "\\%").replace("_", "\\_")


def _get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    """Extract selected ecosystem IDs from cookie or auth context."""
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


def _apply_filters(stmt, request: Request, eco_ids: list[uuid.UUID] | None = None):
    """Apply query-param filters to a Proposal select statement."""
    if eco_ids:
        stmt = stmt.where(Proposal.ecosystem_id.in_(eco_ids))

    phase = request.args.get("phase")
    if phase:
        stmt = stmt.where(Proposal.status == phase)

    proposal_type = request.args.get("type")
    if proposal_type:
        stmt = stmt.where(Proposal.type == proposal_type)

    domain = request.args.get("domain")
    if domain:
        stmt = stmt.where(
            Proposal.affected_domain.ilike(f"%{_escape_like(domain)}%")
        )

    urgency = request.args.get("urgency")
    if urgency:
        stmt = stmt.where(Proposal.urgency == urgency)

    search = request.args.get("q")
    if search:
        pattern = f"%{_escape_like(search)}%"
        stmt = stmt.where(
            or_(
                Proposal.title.ilike(pattern),
                Proposal.proposal_id.ilike(pattern),
                Proposal.proposer.ilike(pattern),
            )
        )

    return stmt


def _require_auth(request: Request):
    """Return the authenticated member or None with a 401 JSON response."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def _proposal_to_list_item(p: Proposal) -> ProposalListItem:
    """Convert a Proposal ORM instance to a ProposalListItem schema."""
    return ProposalListItem(
        id=p.id,
        proposal_id=p.proposal_id,
        type=p.type,
        decision_type=p.decision_type,
        title=p.title,
        version=p.version,
        status=p.status,
        proposer=p.proposer,
        affected_domain=p.affected_domain,
        urgency=p.urgency,
        created_at=p.created_at,
    )


def _advice_entry_to_schema(e: AdviceEntry) -> AdviceEntrySchema:
    """Convert an AdviceEntry ORM instance to schema."""
    return AdviceEntrySchema(
        id=e.id,
        advisor=e.advisor,
        role=e.role,
        ethos=e.ethos,
        advice_type=getattr(e, "advice_type", None),
        content=e.advice_text,
        concerns=None,
        date=e.date,
    )


def _advice_log_to_schema(log: AdviceLog) -> AdviceLogSchema:
    """Convert an AdviceLog ORM instance (with entries loaded) to schema."""
    return AdviceLogSchema(
        id=log.id,
        advice_window_start=log.advice_window_start,
        advice_window_end=log.advice_window_end,
        urgency=log.urgency,
        summary=log.summary,
        proposer_modifications=log.proposer_modifications,
        entries=[_advice_entry_to_schema(e) for e in log.entries],
    )


def _consent_participant_to_schema(cp: ConsentParticipant) -> ConsentParticipantSchema:
    """Convert a ConsentParticipant ORM instance to schema."""
    return ConsentParticipantSchema(
        id=cp.id,
        member_name=cp.name,
        position=cp.position,
        objection_text=cp.reason,
        integration_attempted=None,
        integration_outcome=None,
        date=None,
    )


def _consent_record_to_schema(cr: ConsentRecord) -> ConsentRecordSchema:
    """Convert a ConsentRecord ORM instance (with participants loaded) to schema."""
    return ConsentRecordSchema(
        id=cr.id,
        consent_mode=cr.consent_mode,
        weighting_model=cr.weighting_model,
        facilitator=cr.facilitator,
        date=cr.date,
        quorum_required=cr.quorum_required,
        quorum_met=cr.quorum_met,
        outcome=cr.outcome,
        escalation_level=cr.escalation_level,
        participants=[_consent_participant_to_schema(cp) for cp in cr.participants],
    )


def _test_criterion_to_schema(tc: TestSuccessCriterion) -> TestSuccessCriterionSchema:
    """Convert a TestSuccessCriterion ORM instance to schema."""
    return TestSuccessCriterionSchema(
        id=tc.id,
        criterion=tc.criterion,
        metric=None,
        baseline=None,
        target=None,
        actual=None,
        met=tc.met,
    )


def _test_report_to_schema(tr: TestReport) -> TestReportSchema:
    """Convert a TestReport ORM instance (with criteria loaded) to schema."""
    return TestReportSchema(
        id=tr.id,
        test_start_date=tr.test_start_date,
        test_end_date=tr.test_end_date,
        outcome=tr.outcome,
        observations=tr.observations,
        midpoint_findings=tr.midpoint_findings,
        modifications=tr.modifications,
        next_action=tr.next_action,
        success_criteria_summary=tr.success_criteria_summary,
        success_criteria=[_test_criterion_to_schema(tc) for tc in tr.success_criteria],
    )


def _proposal_to_detail(p: Proposal) -> ProposalDetail:
    """Convert a Proposal ORM instance (with relationships loaded) to ProposalDetail."""
    return ProposalDetail(
        id=p.id,
        proposal_id=p.proposal_id,
        type=p.type,
        decision_type=p.decision_type,
        title=p.title,
        version=p.version,
        status=p.status,
        proposer=p.proposer,
        affected_domain=p.affected_domain,
        urgency=p.urgency,
        created_at=p.created_at,
        ecosystem_id=p.ecosystem_id,
        co_sponsors=p.co_sponsors,
        impacted_parties=p.impacted_parties,
        proposed_change=p.proposed_change,
        rationale=p.rationale,
        created_date=p.created_date,
        advice_deadline=p.advice_deadline,
        consent_deadline=p.consent_deadline,
        test_duration=p.test_duration,
        updated_at=p.updated_at,
        advice_logs=[_advice_log_to_schema(log) for log in p.advice_logs],
        consent_records=[_consent_record_to_schema(cr) for cr in p.consent_records],
        test_reports=[_test_report_to_schema(tr) for tr in p.test_reports],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@proposals_api_bp.get("/")
async def list_proposals(request: Request):
    """GET /api/v1/proposals -- Paginated proposal list with filtering.

    Query params: phase, type, domain, urgency, q, page (default 1), per_page (default 20).
    Returns JSON: {"items": [...], "total": N, "page": P, "per_page": PP}
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 20)), 100)
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(Proposal).order_by(Proposal.created_at.desc())
        stmt = _apply_filters(stmt, request, eco_ids=eco_ids or None)

        # Total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        # Paginate
        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        proposals = result.scalars().all()

    items = [_proposal_to_list_item(p).model_dump(mode="json") for p in proposals]
    return json({"items": items, "total": total, "page": page, "per_page": per_page})


@proposals_api_bp.get("/<proposal_id:uuid>")
async def get_proposal(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id -- Proposal detail with nested relationships.

    Eager-loads advice_logs.entries, consent_records.participants,
    test_reports.success_criteria.
    """
    member, err = _require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        stmt = (
            select(Proposal)
            .where(Proposal.id == proposal_id)
            .options(
                selectinload(Proposal.advice_logs).selectinload(AdviceLog.entries),
                selectinload(Proposal.consent_records).selectinload(
                    ConsentRecord.participants
                ),
                selectinload(Proposal.test_reports).selectinload(
                    TestReport.success_criteria
                ),
            )
        )

        # Scope to selected ecosystems
        eco_ids = _get_ecosystem_ids(request)
        if eco_ids:
            stmt = stmt.where(Proposal.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        proposal = result.scalar_one_or_none()

    if proposal is None:
        return json({"error": "Proposal not found"}, status=404)

    detail = _proposal_to_detail(proposal)
    return json(detail.model_dump(mode="json"))


@proposals_api_bp.post("/")
async def create_proposal(request: Request):
    """POST /api/v1/proposals -- Create a new proposal.

    Accepts JSON: ProposalCreateRequest
    Returns JSON: ProposalDetail with 201 status.
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = ProposalCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    # Verify ecosystem access
    eco_ids = _get_ecosystem_ids(request)
    if eco_ids and create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied to this ecosystem"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    proposal_id_str = f"PROP-{short_id}"

    async with request.app.ctx.db() as session:
        proposal = Proposal(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            proposal_id=proposal_id_str,
            type=create_req.type,
            decision_type=create_req.decision_type,
            title=create_req.title,
            version="1.0",
            status="draft",
            proposer=create_req.proposer,
            affected_domain=create_req.affected_domain,
            urgency=create_req.urgency or "standard",
            proposed_change=create_req.proposed_change,
            rationale=create_req.rationale,
            created_date=date.today(),
            advice_deadline=create_req.advice_deadline,
        )
        session.add(proposal)
        await session.commit()
        await session.refresh(proposal)

        # Re-load with relationships for the detail response
        stmt = (
            select(Proposal)
            .where(Proposal.id == proposal.id)
            .options(
                selectinload(Proposal.advice_logs).selectinload(AdviceLog.entries),
                selectinload(Proposal.consent_records).selectinload(
                    ConsentRecord.participants
                ),
                selectinload(Proposal.test_reports).selectinload(
                    TestReport.success_criteria
                ),
            )
        )
        result = await session.execute(stmt)
        proposal = result.scalar_one()

    detail = _proposal_to_detail(proposal)
    return json(detail.model_dump(mode="json"), status=201)


@proposals_api_bp.put("/<proposal_id:uuid>")
async def update_proposal(request: Request, proposal_id: uuid.UUID):
    """PUT /api/v1/proposals/:id -- Update non-None fields of a proposal.

    Accepts JSON: ProposalUpdateRequest
    Returns JSON: ProposalDetail
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = ProposalUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        # Scope to selected ecosystems
        eco_ids = _get_ecosystem_ids(request)
        stmt = select(Proposal).where(Proposal.id == proposal_id)
        if eco_ids:
            stmt = stmt.where(Proposal.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        proposal = result.scalar_one_or_none()
        if proposal is None:
            return json({"error": "Proposal not found"}, status=404)

        # Update non-None fields
        update_data = update_req.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(proposal, field, value)

        await session.commit()

        # Re-load with relationships
        stmt = (
            select(Proposal)
            .where(Proposal.id == proposal_id)
            .options(
                selectinload(Proposal.advice_logs).selectinload(AdviceLog.entries),
                selectinload(Proposal.consent_records).selectinload(
                    ConsentRecord.participants
                ),
                selectinload(Proposal.test_reports).selectinload(
                    TestReport.success_criteria
                ),
            )
        )
        result = await session.execute(stmt)
        proposal = result.scalar_one()

    detail = _proposal_to_detail(proposal)
    return json(detail.model_dump(mode="json"))


@proposals_api_bp.post("/<proposal_id:uuid>/status")
async def transition_status(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/status -- Transition proposal status.

    Accepts JSON: {"status": "advice"}
    Valid transitions: draft->advice, advice->consent, consent->test,
    test->ratified, any->withdrawn.
    Returns JSON: ProposalDetail
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    new_status = body.get("status")
    if not new_status:
        return json({"error": "\"status\" field is required"}, status=400)

    async with request.app.ctx.db() as session:
        eco_ids = _get_ecosystem_ids(request)
        stmt = select(Proposal).where(Proposal.id == proposal_id)
        if eco_ids:
            stmt = stmt.where(Proposal.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        proposal = result.scalar_one_or_none()
        if proposal is None:
            return json({"error": "Proposal not found"}, status=404)

        current = proposal.status

        # Validate transition
        if new_status == "withdrawn":
            pass  # Any status can transition to withdrawn
        else:
            allowed = _VALID_TRANSITIONS.get(current, set())
            if new_status not in allowed:
                return json(
                    {
                        "error": f"Invalid transition from '{current}' to '{new_status}'",
                        "allowed": sorted(
                            _VALID_TRANSITIONS.get(current, set()) | {"withdrawn"}
                        ),
                    },
                    status=400,
                )

        proposal.status = new_status
        await session.commit()

        logger.info(
            "Proposal %s status: %s -> %s", proposal_id, current, new_status
        )

        # Re-load with relationships
        stmt = (
            select(Proposal)
            .where(Proposal.id == proposal_id)
            .options(
                selectinload(Proposal.advice_logs).selectinload(AdviceLog.entries),
                selectinload(Proposal.consent_records).selectinload(
                    ConsentRecord.participants
                ),
                selectinload(Proposal.test_reports).selectinload(
                    TestReport.success_criteria
                ),
            )
        )
        result = await session.execute(stmt)
        proposal = result.scalar_one()

    detail = _proposal_to_detail(proposal)
    return json(detail.model_dump(mode="json"))


@proposals_api_bp.get("/<proposal_id:uuid>/advice")
async def get_advice(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id/advice -- Advice logs with entries.

    Returns JSON: {"advice_logs": [...]}
    """
    member, err = _require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        # Verify proposal exists and is accessible
        eco_ids = _get_ecosystem_ids(request)
        p_stmt = select(Proposal.id).where(Proposal.id == proposal_id)
        if eco_ids:
            p_stmt = p_stmt.where(Proposal.ecosystem_id.in_(eco_ids))
        if await session.scalar(p_stmt) is None:
            return json({"error": "Proposal not found"}, status=404)

        stmt = (
            select(AdviceLog)
            .where(AdviceLog.proposal_id == proposal_id)
            .options(selectinload(AdviceLog.entries))
            .order_by(AdviceLog.created_at.desc())
        )
        result = await session.execute(stmt)
        logs = result.scalars().all()

    schemas = [_advice_log_to_schema(log).model_dump(mode="json") for log in logs]
    return json({"advice_logs": schemas})


@proposals_api_bp.post("/<proposal_id:uuid>/advice")
async def submit_advice(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/advice -- Add an advice entry.

    If no AdviceLog exists for this proposal, creates one first.
    Accepts JSON: AdviceEntryCreateRequest
    Returns JSON: AdviceLogSchema
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = AdviceEntryCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        # Verify proposal exists and is accessible
        eco_ids = _get_ecosystem_ids(request)
        p_stmt = select(Proposal).where(Proposal.id == proposal_id)
        if eco_ids:
            p_stmt = p_stmt.where(Proposal.ecosystem_id.in_(eco_ids))
        result = await session.execute(p_stmt)
        proposal = result.scalar_one_or_none()
        if proposal is None:
            return json({"error": "Proposal not found"}, status=404)

        # Find or create advice log
        log_stmt = (
            select(AdviceLog)
            .where(AdviceLog.proposal_id == proposal_id)
            .order_by(AdviceLog.created_at.desc())
            .limit(1)
        )
        log_result = await session.execute(log_stmt)
        advice_log = log_result.scalar_one_or_none()

        if advice_log is None:
            advice_log = AdviceLog(
                id=uuid.uuid4(),
                proposal_id=proposal_id,
                advice_window_start=date.today(),
                advice_window_end=proposal.advice_deadline,
                urgency=proposal.urgency,
            )
            session.add(advice_log)
            await session.flush()

        # Create the advice entry
        entry = AdviceEntry(
            id=uuid.uuid4(),
            advice_log_id=advice_log.id,
            advisor=create_req.advisor,
            role=create_req.role,
            ethos=create_req.ethos,
            date=date.today(),
            advice_text=create_req.content,
            integration_status="pending",
        )
        session.add(entry)
        await session.commit()

        # Re-load log with entries
        stmt = (
            select(AdviceLog)
            .where(AdviceLog.id == advice_log.id)
            .options(selectinload(AdviceLog.entries))
        )
        result = await session.execute(stmt)
        advice_log = result.scalar_one()

    schema = _advice_log_to_schema(advice_log)
    return json(schema.model_dump(mode="json"), status=201)


@proposals_api_bp.get("/<proposal_id:uuid>/consent")
async def get_consent(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id/consent -- Consent records with participants.

    Returns JSON: {"consent_records": [...]}
    """
    member, err = _require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        # Verify proposal exists and is accessible
        eco_ids = _get_ecosystem_ids(request)
        p_stmt = select(Proposal.id).where(Proposal.id == proposal_id)
        if eco_ids:
            p_stmt = p_stmt.where(Proposal.ecosystem_id.in_(eco_ids))
        if await session.scalar(p_stmt) is None:
            return json({"error": "Proposal not found"}, status=404)

        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.proposal_id == proposal_id)
            .options(selectinload(ConsentRecord.participants))
            .order_by(ConsentRecord.created_at.desc())
        )
        result = await session.execute(stmt)
        records = result.scalars().all()

    schemas = [
        _consent_record_to_schema(cr).model_dump(mode="json") for cr in records
    ]
    return json({"consent_records": schemas})


@proposals_api_bp.post("/<proposal_id:uuid>/consent")
async def submit_consent(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/consent -- Submit a consent position.

    If no ConsentRecord exists for this proposal, creates one first.
    Accepts JSON: ConsentPositionRequest
    Returns JSON: ConsentRecordSchema
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = ConsentPositionRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        # Verify proposal exists and is accessible
        eco_ids = _get_ecosystem_ids(request)
        p_stmt = select(Proposal).where(Proposal.id == proposal_id)
        if eco_ids:
            p_stmt = p_stmt.where(Proposal.ecosystem_id.in_(eco_ids))
        result = await session.execute(p_stmt)
        proposal = result.scalar_one_or_none()
        if proposal is None:
            return json({"error": "Proposal not found"}, status=404)

        # Find or create consent record
        cr_stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.proposal_id == proposal_id)
            .order_by(ConsentRecord.created_at.desc())
            .limit(1)
        )
        cr_result = await session.execute(cr_stmt)
        consent_record = cr_result.scalar_one_or_none()

        if consent_record is None:
            consent_record = ConsentRecord(
                id=uuid.uuid4(),
                proposal_id=proposal_id,
                consent_mode="consent",
                date=date.today(),
                quorum_met=False,
                outcome="pending",
            )
            session.add(consent_record)
            await session.flush()

        # Record participant position
        participant = ConsentParticipant(
            id=uuid.uuid4(),
            consent_record_id=consent_record.id,
            name=create_req.member_name,
            position=create_req.position,
            reason=create_req.objection_text,
        )
        session.add(participant)
        await session.commit()

        # Re-load record with participants
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.id == consent_record.id)
            .options(selectinload(ConsentRecord.participants))
        )
        result = await session.execute(stmt)
        consent_record = result.scalar_one()

    schema = _consent_record_to_schema(consent_record)
    return json(schema.model_dump(mode="json"), status=201)


@proposals_api_bp.get("/<proposal_id:uuid>/test")
async def get_test_reports(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id/test -- Test reports with success criteria.

    Returns JSON: {"test_reports": [...]}
    """
    member, err = _require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        # Verify proposal exists and is accessible
        eco_ids = _get_ecosystem_ids(request)
        p_stmt = select(Proposal.id).where(Proposal.id == proposal_id)
        if eco_ids:
            p_stmt = p_stmt.where(Proposal.ecosystem_id.in_(eco_ids))
        if await session.scalar(p_stmt) is None:
            return json({"error": "Proposal not found"}, status=404)

        stmt = (
            select(TestReport)
            .where(TestReport.proposal_id == proposal_id)
            .options(selectinload(TestReport.success_criteria))
            .order_by(TestReport.created_at.desc())
        )
        result = await session.execute(stmt)
        reports = result.scalars().all()

    schemas = [_test_report_to_schema(tr).model_dump(mode="json") for tr in reports]
    return json({"test_reports": schemas})
