"""JSON API blueprint for proposal management (ACT process).

Blueprint: proposals_api_bp, url_prefix="/api/v1/proposals"

Manages the full lifecycle of governance proposals through the three
ACT phases: Advice gathering, Consent rounds, and Test periods.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid
import datetime as _dt

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    Agreement,
    ConsentParticipant,
    ConsentRecord,
    Member,
    Proposal,
    TestReport,
    TestSuccessCriterion,
)
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import apply_ecosystem_name_filter, build_search_filter, get_ecosystem_ids, parse_pagination, serialize_shared_ecosystem_ids
from neos_agent.api.policy import can_manage_proposal, can_participate, is_proposal_author
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.services.act_gates import (
    MANAGE_DENIED,
    ActOutcome,
    consent_position,
    normalize_act_policy,
    proposal_gate_status,
    transition_proposal,
)
from neos_agent.api.schemas.proposals import (
    AdviceEntryCreateRequest,
    AdviceEntrySchema,
    AdviceLogSchema,
    ConsentParticipantSchema,
    ConsentPositionRequest,
    ConsentRecordSchema,
    ProposalCreateRequest,
    ProposalDetail,
    ProposalListItem,
    ProposalUpdateRequest,
    TestReportCreateRequest,
    TestReportSchema,
    TestSuccessCriterionSchema,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

proposals_api_bp = Blueprint("proposals_api", url_prefix="/api/v1/proposals")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _escape_like(value: str) -> str:
    """Escape special characters for SQL LIKE patterns."""
    return value.replace("%", "\\%").replace("_", "\\_")


# Manage rule: see api/AGENTS.md "Proposal authorship and manage rule" (MANAGE_DENIED lives with the engine).
SELF_ADVICE_DENIED = "The proposer gathers advice and cannot advise their own proposal"


def _attach_caller_flags(payload: dict, caller: Member | None, proposal: Proposal) -> None:
    """Caller standing in the proposal's ecosystem: participate vs manage."""
    payload["caller_role"] = caller.role if caller else None
    payload["caller_can_conduct"] = can_participate(caller, proposal)
    payload["caller_can_manage"] = can_manage_proposal(caller, proposal)
    payload["caller_is_proposer"] = is_proposal_author(caller, proposal)


def _detail_options() -> tuple:
    """Eager loads the detail payload reads (async sessions cannot lazy-load)."""
    return (
        selectinload(Proposal.advice_logs).selectinload(AdviceLog.entries),
        selectinload(Proposal.consent_records).selectinload(ConsentRecord.participants),
        selectinload(Proposal.test_reports).selectinload(TestReport.success_criteria),
    )


async def _reload_for_detail(session, proposal_id: uuid.UUID) -> Proposal:
    """The proposal with every relationship the detail payload reads."""
    statement = select(Proposal).where(Proposal.id == proposal_id).options(*_detail_options())
    return (await session.execute(statement)).scalar_one()


def _apply_filters(stmt, request: Request, eco_ids: list[uuid.UUID]):
    """Apply query-param filters to a Proposal select statement (no ecosystems -> no rows)."""
    stmt = restrict_to_ecosystems(stmt, Proposal, eco_ids)
    stmt = apply_ecosystem_name_filter(stmt, Proposal, request)

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
        stmt = stmt.where(build_search_filter(
            Proposal, search, Proposal.title, Proposal.proposal_id
        ))

    return stmt




def _proposal_to_list_item(p: Proposal) -> ProposalListItem:
    """Convert a Proposal ORM instance to a ProposalListItem schema."""
    return ProposalListItem(
        id=p.id,
        ecosystem_id=p.ecosystem_id,
        proposal_id=p.proposal_id,
        type=p.type,
        decision_type=p.decision_type,
        title=p.title,
        version=p.version,
        status=p.status,
        proposer=p.proposer,
        proposer_member_id=getattr(p, "proposer_member_id", None),
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
        proposer_member_id=getattr(p, "proposer_member_id", None),
        affected_domain=p.affected_domain,
        urgency=p.urgency,
        created_at=p.created_at,
        ecosystem_id=p.ecosystem_id,
        shared_ecosystem_ids=p.shared_ecosystem_ids,
        co_sponsors=p.co_sponsors,
        impacted_parties=p.impacted_parties,
        proposed_change=p.proposed_change,
        rationale=p.rationale,
        created_date=p.created_date,
        advice_deadline=p.advice_deadline,
        consent_deadline=p.consent_deadline,
        test_duration=p.test_duration,
        updated_at=p.updated_at,
        act_policy=p.act_policy,
        governing_agreement_id=p.governing_agreement_id,
        advice_logs=[_advice_log_to_schema(log) for log in p.advice_logs],
        consent_records=[_consent_record_to_schema(cr) for cr in p.consent_records],
        test_reports=[_test_report_to_schema(tr) for tr in p.test_reports],
    )


async def _attach_gate_context(session, proposal: Proposal, payload: dict) -> None:
    """Attach the effective ACT gates, policy, and governing-agreement brief."""
    gates = await proposal_gate_status(session, proposal)
    payload["gates"] = gates
    # act_policy = the effective policy (own declaration, inherited, or
    # default); own_act_policy = what is actually stored on the proposal
    # (None means it inherits). gates.policy_source says which applies.
    payload["own_act_policy"] = payload.get("act_policy")
    payload["act_policy"] = gates["policy"]
    if proposal.governing_agreement_id:
        agreement = await session.scalar(
            select(Agreement).where(Agreement.id == proposal.governing_agreement_id)
        )
        if agreement is not None:
            payload["governing_agreement"] = {
                "id": str(agreement.id),
                "agreement_id": agreement.agreement_id,
                "title": agreement.title,
            }


async def _proposal_detail_payload(session, proposal: Proposal, caller: Member | None,
                                   outcome: ActOutcome | None = None) -> dict:
    """Detail JSON: effective gates and governing agreement, the ACT outcome when one ran, caller standing."""
    payload = _proposal_to_detail(proposal).model_dump(mode="json")
    await _attach_gate_context(session, proposal, payload)
    if outcome is not None:
        outcome.attach(payload)
    _attach_caller_flags(payload, caller, proposal)
    return payload


async def _validate_governing_agreement(session, proposal_ecosystem_id: uuid.UUID, agreement_id: uuid.UUID | None) -> str | None:
    """The governing agreement must exist in the proposal's own ecosystem."""
    if agreement_id is None:
        return None
    agreement = await session.scalar(select(Agreement).where(Agreement.id == agreement_id))
    if agreement is None:
        return "Governing agreement not found"
    if agreement.ecosystem_id != proposal_ecosystem_id:
        return "The governing agreement must belong to the proposal's ecosystem"
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@proposals_api_bp.get("/")
@authenticated
async def list_proposals(request: Request):
    """GET /api/v1/proposals -- Paginated proposal list with filtering.

    Query params: phase, type, domain, urgency, q, page (default 1), per_page (default 25, max 100).
    Returns JSON: {"items": [...], "total": N, "page": P, "per_page": PP}
    """
    page = parse_pagination(request)  # default 25 like every other list (was 20), on purpose

    async with request.app.ctx.db() as session:
        stmt = select(Proposal).order_by(Proposal.created_at.desc())
        stmt = _apply_filters(stmt, request, get_ecosystem_ids(request))
        total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        proposals = (await session.execute(stmt.offset(page.offset).limit(page.per_page))).scalars().all()

    items = [_proposal_to_list_item(p).model_dump(mode="json") for p in proposals]
    return json({"items": items, "total": total, "page": page.page, "per_page": page.per_page})


@proposals_api_bp.get("/<proposal_id:uuid>")
@authenticated
async def get_proposal(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id -- Proposal detail with nested relationships, gates and caller standing."""
    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(
            session, request, Proposal, proposal_id, options=_detail_options(), label="Proposal",
        )
        caller = await caller_in(session, request, proposal.ecosystem_id)
        return json(await _proposal_detail_payload(session, proposal, caller))


@proposals_api_bp.post("/")
@authenticated
async def create_proposal(request: Request):
    """POST /api/v1/proposals -- Create a new proposal.

    Accepts JSON: ProposalCreateRequest
    Returns JSON: ProposalDetail with 201 status.
    """
    body = request.json or {}
    try:
        create_req = ProposalCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    if create_req.ecosystem_id not in get_ecosystem_ids(request):
        raise ApiError(403, "Access denied to this ecosystem")

    proposal_id_str = f"PROP-{uuid.uuid4().hex[:8].upper()}"

    async with request.app.ctx.db() as session:
        link_error = await _validate_governing_agreement(
            session, create_req.ecosystem_id, create_req.governing_agreement_id
        )
        if link_error:
            raise ApiError(400, link_error)
        # The caller is the author; the proposer text may still name someone
        # else (proposing on their behalf) and defaults to the caller's name.
        author = await caller_in(session, request, create_req.ecosystem_id)
        proposer_text = (create_req.proposer or "").strip() or (author.display_name if author else None)
        proposal = Proposal(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            proposal_id=proposal_id_str,
            type=create_req.type,
            decision_type=create_req.decision_type,
            title=create_req.title,
            version="1.0",
            status="draft",
            proposer=proposer_text,
            proposer_member_id=author.id if author else None,
            affected_domain=create_req.affected_domain,
            urgency=create_req.urgency or "standard",
            proposed_change=create_req.proposed_change,
            rationale=create_req.rationale,
            created_date=_dt.date.today(),
            advice_deadline=create_req.advice_deadline,
            # Gates stay undeclared (NULL) unless the request declares them —
            # undeclared proposals inherit from the governing agreement.
            act_policy=normalize_act_policy(create_req.act_policy.model_dump()) if create_req.act_policy else None,
            governing_agreement_id=create_req.governing_agreement_id,
        )
        session.add(proposal)
        await session.commit()

        proposal = await _reload_for_detail(session, proposal.id)
        return json(await _proposal_detail_payload(session, proposal, author), status=201)


@proposals_api_bp.put("/<proposal_id:uuid>")
@authenticated
async def update_proposal(request: Request, proposal_id: uuid.UUID):
    """PUT /api/v1/proposals/:id -- Update non-None fields of a proposal.

    Accepts JSON: ProposalUpdateRequest
    Returns JSON: ProposalDetail
    """
    body = request.json or {}
    try:
        update_req = ProposalUpdateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        if not can_manage_proposal(caller, proposal):
            raise ApiError(403, MANAGE_DENIED)

        # Update non-None fields. act_policy / governing_agreement_id use
        # explicit-null semantics: present-and-null CLEARS the declaration so
        # the proposal inherits its gates from the governing agreement.
        update_data = update_req.model_dump(exclude_none=True)
        if ("act_policy" in body or "governing_agreement_id" in body) and proposal.status not in {"draft", "advice"}:
            raise ApiError(409, "ACT gates can only be redeclared while the proposal is in draft or advice")
        if "act_policy" in body:
            update_data["act_policy"] = (
                normalize_act_policy(update_req.act_policy.model_dump())
                if update_req.act_policy else None
            )
        if "governing_agreement_id" in body:
            link_error = await _validate_governing_agreement(
                session, proposal.ecosystem_id, update_req.governing_agreement_id
            )
            if link_error:
                raise ApiError(400, link_error)
            update_data["governing_agreement_id"] = update_req.governing_agreement_id
        if "shared_ecosystem_ids" in update_data:
            update_data["shared_ecosystem_ids"] = serialize_shared_ecosystem_ids(
                update_req.shared_ecosystem_ids
            )
        for field, value in update_data.items():
            setattr(proposal, field, value)

        await session.commit()

        proposal = await _reload_for_detail(session, proposal_id)
        return json(await _proposal_detail_payload(session, proposal, caller))


@proposals_api_bp.post("/<proposal_id:uuid>/status")
@authenticated
async def transition_status(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/status -- Manual ACT move through the transition engine.

    Accepts JSON: {"status": "advice"}
    Moves and gates: services/act_gates.py PROPOSAL_LIFECYCLE (any status may move to withdrawn).
    Returns JSON: ProposalDetail plus auto_transitions (and decision_record_id when minted).
    """
    body = request.json or {}
    new_status = body.get("status")
    if not new_status:
        raise ApiError(400, "\"status\" field is required")

    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        current = proposal.status
        outcome = await transition_proposal(session, proposal, to=new_status, caller=caller)
        await session.commit()

        logger.info("Proposal %s status: %s -> %s", proposal_id, current, outcome.status)

        proposal = await _reload_for_detail(session, proposal_id)
        return json(await _proposal_detail_payload(session, proposal, caller, outcome))


@proposals_api_bp.get("/<proposal_id:uuid>/advice")
@authenticated
async def get_advice(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id/advice -- Advice logs with entries.

    Returns JSON: {"advice_logs": [...]}
    """
    async with request.app.ctx.db() as session:
        await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        stmt = (
            select(AdviceLog)
            .where(AdviceLog.proposal_id == proposal_id)
            .options(selectinload(AdviceLog.entries))
            .order_by(AdviceLog.created_at.desc())
        )
        logs = (await session.execute(stmt)).scalars().all()

    return json({"advice_logs": [_advice_log_to_schema(log).model_dump(mode="json") for log in logs]})


@proposals_api_bp.post("/<proposal_id:uuid>/advice")
@authenticated
async def submit_advice(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/advice -- Add an advice entry.

    If no AdviceLog exists for this proposal, creates one first.
    Accepts JSON: AdviceEntryCreateRequest
    Returns JSON: AdviceLogSchema plus gates and auto_transitions, 201.
    """
    body = request.json or {}
    try:
        create_req = AdviceEntryCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None
    advice_text = (create_req.content or "").strip()
    if not advice_text:
        # A blank entry would still count toward the advice gate and could
        # auto-advance the proposal.
        raise ApiError(400, "Advice text is required")

    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        if is_proposal_author(caller, proposal):
            raise ApiError(409, SELF_ADVICE_DENIED)
        # Advisor identity comes from the caller, never the request body. A
        # shared-ecosystem advisor has no row here, so use their session member.
        advisor_name = (caller or request.ctx.member).display_name

        # Find or create advice log. ``new_round`` opens a fresh round —
        # rounds are the unit the declared advice gate counts.
        log_stmt = (
            select(AdviceLog)
            .where(AdviceLog.proposal_id == proposal_id)
            .order_by(AdviceLog.created_at.desc())
            .limit(1)
        )
        advice_log = (await session.execute(log_stmt)).scalar_one_or_none()

        if advice_log is None or create_req.new_round:
            advice_log = AdviceLog(
                id=uuid.uuid4(),
                proposal_id=proposal_id,
                advice_window_start=_dt.date.today(),
                advice_window_end=proposal.advice_deadline,
                urgency=proposal.urgency,
            )
            session.add(advice_log)
            await session.flush()

        session.add(AdviceEntry(
            id=uuid.uuid4(),
            advice_log_id=advice_log.id,
            advisor=advisor_name,
            role=create_req.role,
            ethos=create_req.ethos,
            date=_dt.date.today(),
            advice_text=advice_text,
            integration_status="pending",
        ))
        await session.flush()

        outcome = await transition_proposal(session, proposal, caller=caller)
        await session.commit()

        stmt = (
            select(AdviceLog)
            .where(AdviceLog.id == advice_log.id)
            .options(selectinload(AdviceLog.entries))
        )
        advice_log = (await session.execute(stmt)).scalar_one()

    payload = _advice_log_to_schema(advice_log).model_dump(mode="json")
    return json(outcome.attach(payload, gates=True), status=201)


@proposals_api_bp.get("/<proposal_id:uuid>/consent")
@authenticated
async def get_consent(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id/consent -- Consent records with participants.

    Returns JSON: {"consent_records": [...]}
    """
    async with request.app.ctx.db() as session:
        await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.proposal_id == proposal_id)
            .options(selectinload(ConsentRecord.participants))
            .order_by(ConsentRecord.created_at.desc())
        )
        records = (await session.execute(stmt)).scalars().all()

    return json({"consent_records": [_consent_record_to_schema(cr).model_dump(mode="json") for cr in records]})


@proposals_api_bp.post("/<proposal_id:uuid>/consent")
@authenticated
async def submit_consent(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/consent -- Record the caller's consent position.

    If no ConsentRecord exists for this proposal, creates one first. The
    participant is always the caller; the body's member_name is ignored.
    Accepts JSON: ConsentPositionRequest
    Returns JSON: ConsentRecordSchema plus gates and auto_transitions, 201.
    """
    body = request.json or {}
    try:
        create_req = ConsentPositionRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        # Same identity rule as advice: a shared-ecosystem participant uses their session member.
        participant_name = (caller or request.ctx.member).display_name

        cr_stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.proposal_id == proposal_id)
            .order_by(ConsentRecord.created_at.desc())
            .limit(1)
        )
        consent_record = (await session.execute(cr_stmt)).scalar_one_or_none()

        if consent_record is None:
            consent_record = ConsentRecord(
                id=uuid.uuid4(),
                proposal_id=proposal_id,
                consent_mode="consent",
                date=_dt.date.today(),
                quorum_met=False,
                outcome="pending",
            )
            session.add(consent_record)
            await session.flush()

        session.add(ConsentParticipant(
            id=uuid.uuid4(),
            consent_record_id=consent_record.id,
            name=participant_name,
            position=consent_position(create_req.position),
            reason=create_req.objection_text,
        ))
        await session.flush()

        outcome = await transition_proposal(session, proposal, caller=caller)
        await session.commit()

        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.id == consent_record.id)
            .options(selectinload(ConsentRecord.participants))
        )
        consent_record = (await session.execute(stmt)).scalar_one()

    payload = _consent_record_to_schema(consent_record).model_dump(mode="json")
    return json(outcome.attach(payload, gates=True), status=201)


@proposals_api_bp.get("/<proposal_id:uuid>/test")
@authenticated
async def get_test_reports(request: Request, proposal_id: uuid.UUID):
    """GET /api/v1/proposals/:id/test -- Test reports with success criteria.

    Returns JSON: {"test_reports": [...]}
    """
    async with request.app.ctx.db() as session:
        await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        stmt = (
            select(TestReport)
            .where(TestReport.proposal_id == proposal_id)
            .options(selectinload(TestReport.success_criteria))
            .order_by(TestReport.created_at.desc())
        )
        reports = (await session.execute(stmt)).scalars().all()

    return json({"test_reports": [_test_report_to_schema(tr).model_dump(mode="json") for tr in reports]})


@proposals_api_bp.post("/<proposal_id:uuid>/test")
@authenticated
async def submit_test_report(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/test -- Submit a test report.

    Accepts JSON: TestReportCreateRequest
    Returns JSON: TestReportSchema plus gates, auto_transitions (and decision_record_id when minted), 201.
    """
    body = request.json or {}
    try:
        create_req = TestReportCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)

        report = TestReport(
            id=uuid.uuid4(),
            proposal_id=proposal_id,
            test_start_date=_dt.date.today(),
            observations=create_req.observations,
            outcome=create_req.outcome,
        )
        session.add(report)
        await session.flush()

        for sc in create_req.success_criteria:
            session.add(TestSuccessCriterion(
                id=uuid.uuid4(),
                test_report_id=report.id,
                criterion=sc.criterion,
                met=sc.met,
                evidence=sc.evidence,
            ))
        await session.flush()

        outcome = await transition_proposal(session, proposal, caller=caller)
        await session.commit()

        stmt = (
            select(TestReport)
            .where(TestReport.id == report.id)
            .options(selectinload(TestReport.success_criteria))
        )
        report = (await session.execute(stmt)).scalar_one()

    payload = _test_report_to_schema(report).model_dump(mode="json")
    return json(outcome.attach(payload, gates=True), status=201)
