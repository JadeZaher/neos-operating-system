"""Proposal CRUD views with ACT (Advice-Consent-Test) process tabs.

Blueprint: proposals_bp, url_prefix="/dashboard/proposals"

Manages the full lifecycle of governance proposals through the three
ACT phases: Advice gathering, Consent rounds, and Test periods.
Each phase has its own SSE-driven tab for real-time updates.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func, or_

from neos_agent.db.models import (
    Proposal,
    AdviceLog,
    AdviceEntry,
    ConsentRecord,
    ConsentParticipant,
    TestReport,
)
from neos_agent.messaging.queries import get_entity_discussions
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, get_scoped_entity, validate_ecosystem_id

logger = logging.getLogger(__name__)

proposals_bp = Blueprint("proposals", url_prefix="/dashboard/proposals")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_filters(stmt, request: Request, eco_ids=None):
    """Apply optional query-param filters to a Proposal select statement."""
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
        stmt = stmt.where(Proposal.affected_domain.ilike(f"%{domain}%"))

    urgency = request.args.get("urgency")
    if urgency:
        stmt = stmt.where(Proposal.urgency == urgency)

    search = request.args.get("q")
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Proposal.title.ilike(pattern),
                Proposal.proposal_id.ilike(pattern),
                Proposal.proposer.ilike(pattern),
            )
        )

    return stmt


# ---------------------------------------------------------------------------
# Routes — List / Create
# ---------------------------------------------------------------------------

@proposals_bp.get("/")
async def list_proposals(request: Request):
    """GET /dashboard/proposals -- list proposals with filtering."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = select(Proposal).order_by(Proposal.created_at.desc())
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            proposals = result.scalars().all()
    except Exception:
        logger.exception("Failed to load proposals list")
        proposals = []
        total = 0

    content = await render(
        "dashboard/proposals/list.html",
        request=request,
        proposals=proposals,
        total=total,
        offset=offset,
        limit=limit,
        filters=dict(request.args),
        active_page="proposals",
    )
    return html(content)


@proposals_bp.get("/new")
async def create_form(request: Request):
    """GET /dashboard/proposals/new -- render create form."""
    content = await render("dashboard/proposals/form.html", request=request, proposal=None, active_page="proposals")
    return html(content)


@proposals_bp.post("/")
async def create_proposal(request: Request):
    """POST /dashboard/proposals -- create proposal from form data."""
    form = request.form
    ecosystem_id = validate_ecosystem_id(form.get("ecosystem_id"), request)
    if ecosystem_id is None:
        content = await render(
            "dashboard/proposals/form.html",
            request=request,
            proposal=None,
            error="Invalid or unauthorized ecosystem.",
        )
        return html(content, status=400)
    try:
        async with request.app.ctx.db() as session:
            proposal = Proposal(
                id=uuid.uuid4(),
                ecosystem_id=ecosystem_id,
                proposal_id=form.get("proposal_id", ""),
                type=form.get("type", "operational"),
                decision_type=form.get("decision_type"),
                title=form.get("title", ""),
                version="1.0",
                status="draft",
                proposer=form.get("proposer"),
                affected_domain=form.get("affected_domain"),
                urgency=form.get("urgency", "standard"),
                proposed_change=form.get("proposed_change"),
                rationale=form.get("rationale"),
                created_date=date.today(),
            )

            # Parse advice/consent deadlines if provided
            advice_deadline = form.get("advice_deadline")
            if advice_deadline:
                try:
                    proposal.advice_deadline = date.fromisoformat(advice_deadline)
                except ValueError:
                    pass

            consent_deadline = form.get("consent_deadline")
            if consent_deadline:
                try:
                    proposal.consent_deadline = date.fromisoformat(consent_deadline)
                except ValueError:
                    pass

            proposal.test_duration = form.get("test_duration")

            session.add(proposal)
            await session.commit()
            proposal_id = proposal.id
    except Exception:
        logger.exception("Failed to create proposal")
        content = await render(
            "dashboard/proposals/form.html",
            request=request,
            proposal=None,
            error="Failed to create proposal. Please check your input and try again.",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/proposals/{proposal_id}")


# ---------------------------------------------------------------------------
# Routes — Detail
# ---------------------------------------------------------------------------

@proposals_bp.get("/<proposal_id:uuid>")
async def detail(request: Request, proposal_id: uuid.UUID):
    """GET /dashboard/proposals/{proposal_id} -- detail with ACT tabs."""
    try:
        async with request.app.ctx.db() as session:
            proposal = await get_scoped_entity(session, Proposal, proposal_id, request)
            if proposal is None:
                content = await render(
                    "dashboard/proposals/detail.html",
                    request=request,
                    proposal=None,
                    error="Proposal not found.",
                )
                return html(content, status=404)
    except Exception:
        logger.exception("Failed to load proposal detail")
        content = await render(
            "dashboard/proposals/detail.html",
            request=request,
            proposal=None,
            error="Failed to load proposal.",
        )
        return html(content, status=500)

    discussions = []
    try:
        async with request.app.ctx.db() as session:
            discussions = await get_entity_discussions(session, "proposal", proposal_id)
    except Exception:
        pass

    content = await render("dashboard/proposals/detail.html", request=request, proposal=proposal, discussions=discussions, active_page="proposals")
    return html(content)


# ---------------------------------------------------------------------------
# Routes — Advice phase (A in ACT)
# ---------------------------------------------------------------------------

@proposals_bp.get("/<proposal_id:uuid>/advice")
async def advice_tab(request: Request, proposal_id: uuid.UUID):
    """GET /dashboard/proposals/{proposal_id}/advice -- htmx advice tab fragment."""
    try:
        async with request.app.ctx.db() as session:
            proposal = await get_scoped_entity(session, Proposal, proposal_id, request)
            if proposal is None:
                return html("<div>Proposal not found.</div>")

            # Load advice logs and entries
            logs_result = await session.execute(
                select(AdviceLog)
                .where(AdviceLog.proposal_id == proposal_id)
                .order_by(AdviceLog.created_at.desc())
            )
            advice_logs = logs_result.scalars().all()

            # Gather all entries across logs
            all_entries = []
            for log in advice_logs:
                entries_result = await session.execute(
                    select(AdviceEntry)
                    .where(AdviceEntry.advice_log_id == log.id)
                    .order_by(AdviceEntry.date.desc())
                )
                entries = entries_result.scalars().all()
                all_entries.extend(entries)
    except Exception:
        logger.exception("Failed to load advice data")
        return html("<div>Failed to load advice data.</div>")

    fragment = await render(
        "dashboard/proposals/_advice_tab.html",
        request=request,
        proposal=proposal,
        advice_logs=advice_logs,
        advice_entries=all_entries,
    )
    return html(fragment)


@proposals_bp.post("/<proposal_id:uuid>/advice")
async def submit_advice(request: Request, proposal_id: uuid.UUID):
    """POST /dashboard/proposals/{proposal_id}/advice -- submit advice entry."""
    form = request.form
    try:
        async with request.app.ctx.db() as session:
            proposal = await get_scoped_entity(session, Proposal, proposal_id, request)
            if proposal is None:
                return html(
                    await render(
                        "dashboard/proposals/detail.html",
                        request=request,
                        proposal=None,
                        error="Proposal not found.",
                    ),
                    status=404,
                )

            # Ensure an advice log exists for this proposal
            log_result = await session.execute(
                select(AdviceLog)
                .where(AdviceLog.proposal_id == proposal_id)
                .order_by(AdviceLog.created_at.desc())
                .limit(1)
            )
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
                advisor=form.get("advisor", ""),
                role=form.get("role"),
                ethos=form.get("ethos"),
                date=date.today(),
                advice_text=form.get("advice_text", ""),
                integration_status="pending",
            )
            session.add(entry)
            await session.commit()
    except Exception:
        logger.exception("Failed to submit advice entry")
        return html(
            await render(
                "dashboard/proposals/detail.html",
                request=request,
                proposal=None,
                error="Failed to submit advice.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/proposals/{proposal_id}")


# ---------------------------------------------------------------------------
# Routes — Consent phase (C in ACT)
# ---------------------------------------------------------------------------

@proposals_bp.get("/<proposal_id:uuid>/consent")
async def consent_tab(request: Request, proposal_id: uuid.UUID):
    """GET /dashboard/proposals/{proposal_id}/consent -- htmx consent tab fragment."""
    try:
        async with request.app.ctx.db() as session:
            proposal = await get_scoped_entity(session, Proposal, proposal_id, request)
            if proposal is None:
                return html("<div>Proposal not found.</div>")

            # Load consent records and participants
            records_result = await session.execute(
                select(ConsentRecord)
                .where(ConsentRecord.proposal_id == proposal_id)
                .order_by(ConsentRecord.created_at.desc())
            )
            consent_records = records_result.scalars().all()

            # Gather participants per record
            all_participants = []
            for record in consent_records:
                participants_result = await session.execute(
                    select(ConsentParticipant)
                    .where(ConsentParticipant.consent_record_id == record.id)
                    .order_by(ConsentParticipant.created_at.asc())
                )
                participants = participants_result.scalars().all()
                all_participants.extend(participants)
    except Exception:
        logger.exception("Failed to load consent data")
        return html("<div>Failed to load consent data.</div>")

    fragment = await render(
        "dashboard/proposals/_consent_tab.html",
        request=request,
        proposal=proposal,
        consent_records=consent_records,
        consent_participants=all_participants,
    )
    return html(fragment)


@proposals_bp.post("/<proposal_id:uuid>/consent")
async def record_consent(request: Request, proposal_id: uuid.UUID):
    """POST /dashboard/proposals/{proposal_id}/consent -- record consent position."""
    form = request.form
    try:
        async with request.app.ctx.db() as session:
            proposal = await get_scoped_entity(session, Proposal, proposal_id, request)
            if proposal is None:
                return html(
                    await render(
                        "dashboard/proposals/detail.html",
                        request=request,
                        proposal=None,
                        error="Proposal not found.",
                    ),
                    status=404,
                )

            # Ensure a consent record exists
            record_result = await session.execute(
                select(ConsentRecord)
                .where(ConsentRecord.proposal_id == proposal_id)
                .order_by(ConsentRecord.created_at.desc())
                .limit(1)
            )
            consent_record = record_result.scalar_one_or_none()

            if consent_record is None:
                consent_record = ConsentRecord(
                    id=uuid.uuid4(),
                    proposal_id=proposal_id,
                    consent_mode=form.get("consent_mode", "consent"),
                    facilitator=form.get("facilitator"),
                    date=date.today(),
                    quorum_required=form.get("quorum_required"),
                    quorum_met=False,
                    outcome="pending",
                )
                session.add(consent_record)
                await session.flush()

            # Record participant position
            participant = ConsentParticipant(
                id=uuid.uuid4(),
                consent_record_id=consent_record.id,
                name=form.get("name", ""),
                role=form.get("role"),
                ethos=form.get("ethos"),
                position=form.get("position", ""),
                reason=form.get("reason"),
            )
            session.add(participant)
            await session.commit()
    except Exception:
        logger.exception("Failed to record consent position")
        return html(
            await render(
                "dashboard/proposals/detail.html",
                request=request,
                proposal=None,
                error="Failed to record consent position.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/proposals/{proposal_id}")


# ---------------------------------------------------------------------------
# Routes — Test phase (T in ACT)
# ---------------------------------------------------------------------------

@proposals_bp.get("/<proposal_id:uuid>/test")
async def test_tab(request: Request, proposal_id: uuid.UUID):
    """GET /dashboard/proposals/{proposal_id}/test -- htmx test tab fragment."""
    try:
        async with request.app.ctx.db() as session:
            proposal = await get_scoped_entity(session, Proposal, proposal_id, request)
            if proposal is None:
                return html("<div>Proposal not found.</div>")

            reports_result = await session.execute(
                select(TestReport)
                .where(TestReport.proposal_id == proposal_id)
                .order_by(TestReport.created_at.desc())
            )
            test_reports = reports_result.scalars().all()
    except Exception:
        logger.exception("Failed to load test data")
        return html("<div>Failed to load test data.</div>")

    fragment = await render(
        "dashboard/proposals/_test_tab.html",
        request=request,
        proposal=proposal,
        test_reports=test_reports,
    )
    return html(fragment)


# ---------------------------------------------------------------------------
# Routes — Phase transition
# ---------------------------------------------------------------------------

@proposals_bp.post("/<proposal_id:uuid>/phase")
async def phase_transition(request: Request, proposal_id: uuid.UUID):
    """POST /dashboard/proposals/{proposal_id}/phase -- ACT phase transition.

    Requires form field: new_phase (draft, advice, consent, test, ratified, archived).
    """
    form = request.form
    new_phase = form.get("new_phase")

    if not new_phase:
        return html(
            await render(
                "dashboard/proposals/detail.html",
                request=request,
                proposal=None,
                error="new_phase is required for phase transition.",
            ),
            status=400,
        )

    try:
        async with request.app.ctx.db() as session:
            proposal = await get_scoped_entity(session, Proposal, proposal_id, request)
            if proposal is None:
                return html(
                    await render(
                        "dashboard/proposals/detail.html",
                        request=request,
                        proposal=None,
                        error="Proposal not found.",
                    ),
                    status=404,
                )

            old_phase = proposal.status
            proposal.status = new_phase
            await session.commit()

            logger.info(
                "Proposal %s phase: %s -> %s",
                proposal_id, old_phase, new_phase,
            )
    except Exception:
        logger.exception("Failed to transition proposal phase")
        return html(
            await render(
                "dashboard/proposals/detail.html",
                request=request,
                proposal=None,
                error="Failed to update proposal phase.",
            ),
            status=500,
        )

    return redirect(f"/dashboard/proposals/{proposal_id}")
