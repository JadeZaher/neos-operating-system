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
from neos_agent.api.policy import can_manage_proposal, can_participate, can_register_agreement, is_proposal_author
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.services.act_gates import (
    MANAGE_DENIED,
    ActOutcome,
    consent_position,
    current_position,
    created_after_newest,
    normalize_act_policy,
    proposal_gate_status,
    proposal_next_moves,
    record_consent_position,
    transition_proposal,
    withdraw_consent_position,
)
from neos_agent.api.agreements import register_ratified_proposal
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
    StatusTransitionRequest,
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
ADVICE_CLOSED = "Advice can only be given while the proposal is in advice"
TEST_CLOSED = "Test reports can only be filed while the proposal is in test"
# ProposalForm offers exactly these; see api/AGENTS.md "One gate vocabulary".
DECISION_TYPES = ("consent", "consensus")
# Agreements a proposal may be governed by or amend: those in force.
IN_FORCE_AGREEMENT_STATUSES = ("active", "under_review")
# Members decide on the text from consent on; see api/AGENTS.md "ACT integrity (G-ACT)".
EDITABLE_STAGES = frozenset({"draft", "advice"})
PROPOSAL_LOCKED = ("A proposal can only be edited in draft or advice: members decide on its text from consent on. "
                   "Send it back for revision to change it")


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
        member_id=e.member_id,
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
        member_id=cp.member_id,
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
        reporter_member_id=tr.reporter_member_id,
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
        amends_agreement_id=p.amends_agreement_id,
        registered_agreement_id=p.registered_agreement_id,
        advice_logs=[_advice_log_to_schema(log) for log in _oldest_first(p.advice_logs)],
        consent_records=[_consent_record_to_schema(cr) for cr in _oldest_first(p.consent_records)],
        test_reports=[_test_report_to_schema(tr) for tr in _oldest_first(p.test_reports)],
    )


def _oldest_first(rows: list) -> list:
    """Sub-records in creation order, so the last consent record is the one the gate reads."""
    return sorted(rows, key=lambda row: row.created_at or _dt.datetime.min)


async def _agreement_brief(session, agreement_id: uuid.UUID | None) -> dict | None:
    """id, key, title, status and version of a linked agreement (None when unlinked or gone)."""
    if agreement_id is None:
        return None
    agreement = await session.scalar(select(Agreement).where(Agreement.id == agreement_id))
    if agreement is None:
        return None
    return {
        "id": str(agreement.id),
        "agreement_id": agreement.agreement_id,
        "title": agreement.title,
        "status": agreement.status,
        "version": agreement.version,
    }


async def _attach_gate_context(session, proposal: Proposal, payload: dict) -> None:
    """Attach the effective ACT gates, policy, and the governing / amended / registered agreement briefs."""
    gates = await proposal_gate_status(session, proposal)
    payload["gates"] = gates
    # act_policy = the effective policy (own declaration, inherited, or
    # default); own_act_policy = what is actually stored on the proposal
    # (None means it inherits). gates.policy_source says which applies.
    payload["own_act_policy"] = payload.get("act_policy")
    payload["act_policy"] = gates["policy"]
    for key in ("governing_agreement", "amends_agreement", "registered_agreement"):
        brief = await _agreement_brief(session, getattr(proposal, f"{key}_id"))
        if brief is not None:
            payload[key] = brief


async def _attach_reporter_names(session, payload: dict) -> None:
    """Name each test report's reporter (one IN query)."""
    ids = {report["reporter_member_id"] for report in payload["test_reports"] if report.get("reporter_member_id")}
    if not ids:
        return
    names = dict((await session.execute(
        select(Member.id, Member.display_name).where(Member.id.in_([uuid.UUID(i) for i in ids]))
    )).all())
    for report in payload["test_reports"]:
        if report.get("reporter_member_id"):
            report["reporter_name"] = names.get(uuid.UUID(report["reporter_member_id"]))


async def _caller_position(session, proposal: Proposal, caller: Member | None) -> dict | None:
    """The caller's position in the latest consent record, as the consent tab shows it."""
    row = await current_position(session, proposal, caller)
    return None if row is None else {"position": consent_position(row.position), "reason": row.reason}


async def _proposal_detail_payload(session, proposal: Proposal, caller: Member | None,
                                   outcome: ActOutcome | None = None) -> dict:
    """Detail JSON: gates and linked agreements, the ACT outcome when one ran, caller standing, position and moves."""
    payload = _proposal_to_detail(proposal).model_dump(mode="json")
    await _attach_gate_context(session, proposal, payload)
    await _attach_reporter_names(session, payload)
    if outcome is not None:
        outcome.attach(payload)
    _attach_caller_flags(payload, caller, proposal)
    payload["allowed_next"] = proposal_next_moves(proposal, payload["gates"], caller)
    payload["caller_position"] = await _caller_position(session, proposal, caller)
    payload["caller_can_register"] = (
        proposal.status == "ratified"
        and proposal.registered_agreement_id is None
        and can_register_agreement(caller, proposal)
    )
    return payload


async def _validate_linked_agreement(session, proposal_ecosystem_id: uuid.UUID, agreement_id: uuid.UUID | None,
                                     label: str) -> str | None:
    """A governing or amended agreement must exist in the proposal's own ecosystem and be in force."""
    if agreement_id is None:
        return None
    agreement = await session.scalar(select(Agreement).where(Agreement.id == agreement_id))
    if agreement is None:
        return f"{label} not found"
    if agreement.ecosystem_id != proposal_ecosystem_id:
        return f"The {label.lower()} must belong to the proposal's ecosystem"
    if agreement.status not in IN_FORCE_AGREEMENT_STATUSES:
        return f"The {label.lower()} must be in force (active); this one is {agreement.status}"
    return None


def _validate_decision_type(decision_type: str | None) -> None:
    """Only the modes the engine applies; the old advice/autocratic labels decided nothing."""
    if decision_type is not None and decision_type not in DECISION_TYPES:
        raise ApiError(400, "Decision type must be consent or consensus", {"allowed": list(DECISION_TYPES)})


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

    _validate_decision_type(create_req.decision_type)

    async with request.app.ctx.db() as session:
        for agreement_id, label in ((create_req.governing_agreement_id, "Governing agreement"),
                                    (create_req.amends_agreement_id, "Amended agreement")):
            link_error = await _validate_linked_agreement(session, create_req.ecosystem_id, agreement_id, label)
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
            amends_agreement_id=create_req.amends_agreement_id,
        )
        session.add(proposal)
        await session.commit()

        proposal = await _reload_for_detail(session, proposal.id)
        return json(await _proposal_detail_payload(session, proposal, author), status=201)


@proposals_api_bp.put("/<proposal_id:uuid>")
@authenticated
async def update_proposal(request: Request, proposal_id: uuid.UUID):
    """PUT /api/v1/proposals/:id -- Update non-None fields of a proposal (only in draft or advice; 409 after).

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
        if proposal.status not in EDITABLE_STAGES and _changes_anything(proposal, update_data, body):
            raise ApiError(409, PROPOSAL_LOCKED, {"status": proposal.status})
        _validate_decision_type(update_req.decision_type)
        if "act_policy" in body:
            update_data["act_policy"] = (
                normalize_act_policy(update_req.act_policy.model_dump())
                if update_req.act_policy else None
            )
        for name, label in (("governing_agreement_id", "Governing agreement"),
                            ("amends_agreement_id", "Amended agreement")):
            if name not in body:
                continue
            value = getattr(update_req, name)
            if value != getattr(proposal, name):
                link_error = await _validate_linked_agreement(session, proposal.ecosystem_id, value, label)
                if link_error:
                    raise ApiError(400, link_error)
            update_data[name] = value
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

    Accepts JSON: {"status": "advice", "note": "..."} (the note is required to send a proposal back).
    Moves and gates: services/act_gates.py PROPOSAL_LIFECYCLE (non-terminal statuses may move to withdrawn).
    Returns JSON: ProposalDetail plus auto_transitions (and decision_record_id when minted).
    """
    body = request.json or {}
    if not body.get("status"):
        raise ApiError(400, "\"status\" field is required")
    try:
        move_req = StatusTransitionRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None
    new_status = move_req.status

    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        current = proposal.status
        outcome = await transition_proposal(session, proposal, to=new_status, caller=caller, note=move_req.note)
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
        if proposal.status != "advice":
            raise ApiError(409, ADVICE_CLOSED, {"status": proposal.status})
        # Advisor identity comes from the caller, never the request body. A
        # shared-ecosystem advisor has no row here, so use their session member.
        advisor = caller or request.ctx.member
        advisor_name = advisor.display_name

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
                **await created_after_newest(session, AdviceLog, proposal_id),
            )
            session.add(advice_log)
            await session.flush()

        session.add(AdviceEntry(
            id=uuid.uuid4(),
            advice_log_id=advice_log.id,
            advisor=advisor_name,
            member_id=advisor.id,
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
    """POST /api/v1/proposals/:id/consent -- Record or change the caller's consent position.

    One position per member, owned by member id: a second call replaces the first. The
    participant is always the caller's row in the proposal's ecosystem (403 otherwise); a
    body member_name is ignored. Only while the proposal is in consent.
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
        # The caller's own row in the proposal's ecosystem (can_participate, 403 otherwise; no shared-ecosystem fallback).
        record, outcome = await record_consent_position(
            session, proposal, member=caller, position=create_req.position, reason=create_req.objection_text,
        )
        await session.commit()
        payload = await _consent_record_payload(session, record.id)
    return json(outcome.attach(payload, gates=True), status=201)


@proposals_api_bp.delete("/<proposal_id:uuid>/consent")
@authenticated
async def withdraw_consent(request: Request, proposal_id: uuid.UUID):
    """DELETE /api/v1/proposals/:id/consent -- Withdraw the caller's own position (lifts their objection).

    The row stays in the record as "withdrawn". Returns JSON: ConsentRecordSchema plus gates and auto_transitions.
    """
    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        record, outcome = await withdraw_consent_position(session, proposal, member=caller)
        await session.commit()
        payload = await _consent_record_payload(session, record.id)
    return json(outcome.attach(payload, gates=True))


async def _consent_record_payload(session, record_id: uuid.UUID) -> dict:
    """One consent record with its participants, serialized."""
    statement = select(ConsentRecord).where(ConsentRecord.id == record_id).options(selectinload(ConsentRecord.participants))
    record = (await session.execute(statement)).scalar_one()
    return _consent_record_to_schema(record).model_dump(mode="json")


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
        if proposal.status != "test":
            raise ApiError(409, TEST_CLOSED, {"status": proposal.status})

        report = TestReport(
            id=uuid.uuid4(),
            proposal_id=proposal_id,
            test_start_date=_dt.date.today(),
            observations=create_req.observations,
            outcome=(create_req.outcome or "").strip().lower(),
            reporter_member_id=(caller or request.ctx.member).id,
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


@proposals_api_bp.post("/<proposal_id:uuid>/register-agreement")
@authenticated
async def register_agreement(request: Request, proposal_id: uuid.UUID):
    """POST /api/v1/proposals/:id/register-agreement -- A steward registers a ratified proposal as an agreement.

    Amends `amends_agreement_id` (new text, new version) when set, else creates an active agreement.
    Returns JSON: ProposalDetail with `registered_agreement`, 201.
    """
    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
        agreement = await register_ratified_proposal(session, proposal, caller=caller)
        await session.commit()
        logger.info("Proposal %s registered as agreement %s", proposal_id, agreement.agreement_id)
        proposal = await _reload_for_detail(session, proposal_id)
        return json(await _proposal_detail_payload(session, proposal, caller), status=201)


_GATE_FIELDS = ("act_policy", "governing_agreement_id", "amends_agreement_id", "decision_type")


def _changes_anything(proposal: Proposal, update_data: dict, body: dict) -> bool:
    """True when the PUT would change a stored value (the edit form resends unchanged fields)."""
    if any(_gate_field_changed(proposal, name, body) for name in _GATE_FIELDS):
        return True
    return any(_differs(getattr(proposal, name), value)
               for name, value in update_data.items() if name not in _GATE_FIELDS)


def _differs(stored, sent) -> bool:
    """Compare as the form round-trips values: trimmed text, string ids, empty == unset."""
    def normal(value):
        if isinstance(value, str):
            value = value.strip()
        if isinstance(value, list):
            value = [str(item) for item in value]
        return None if value in ("", []) else value
    return normal(stored) != normal(sent)


def _gate_field_changed(proposal: Proposal, name: str, body: dict) -> bool:
    """True when the body changes a gate field (an unchanged resend from the edit form is not a change)."""
    if name not in body:
        return False
    sent, stored = body[name], getattr(proposal, name)
    if name == "decision_type":
        return sent is not None and sent != stored
    if name == "act_policy":
        sent_policy = normalize_act_policy(sent) if sent is not None else None
        stored_policy = normalize_act_policy(stored) if stored is not None else None
        return sent_policy != stored_policy
    return (str(sent) if sent else None) != (str(stored) if stored else None)
