"""JSON API blueprint for voluntary exit: self-filed, steward-completed handoff, and a portable record.

Blueprint: exit_api_bp, url_prefix="/api/v1/exit". Who may do what and why:
api/AGENTS.md "Emergency and exit".
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from datetime import timedelta, timezone

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import and_, func, select

from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import (
    apply_ecosystem_name_filter, build_search_filter, get_authorized_ecosystem_ids, get_ecosystem_ids,
    parse_pagination, serialize_shared_ecosystem_ids,
)
from neos_agent.api.policy import can_steward_exit, is_active_member_in, is_exit_leaver
from neos_agent.api.schemas.exit import ExitCreateRequest, ExitDetail, ExitListItem, ExitStatusRequest
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.db.models import (
    AdviceEntry, AdviceLog, Agreement, AgreementMemberConsent, ConsentParticipant, ConsentRecord, Ecosystem,
    ExitRecord, Member, MemberStatusTransition, Proposal, TestReport,
)

logger = logging.getLogger(__name__)

exit_api_bp = Blueprint("exit_api", url_prefix="/api/v1/exit")

# Handoff length by exit type; the skill caps it at 30 days and allows a 7-day urgent exit.
HANDOFF_DAYS = {"standard": 30, "urgent": 7}
OPEN_STATUSES = ("declared", "cooling_off", "unwinding")  # cooling_off: legacy rows, treated as declared
EXITED = "exited"
PORTABLE_RECORD_FORMAT = "neos-portable-record/1"

# State table: status -> {next status: who may make the move}.
EXIT_MOVES = {
    "declared": {"unwinding": "steward", "completed": "steward", "cancelled": "leaver"},
    "cooling_off": {"unwinding": "steward", "completed": "steward", "cancelled": "leaver"},
    "unwinding": {"completed": "steward", "cancelled": "leaver"},
}
EXIT_STATUSES = ("declared", "cooling_off", "unwinding", "completed", "cancelled")
NEXT_STEP = {
    "declared": "Filed. A steward starts the handoff of roles and commitments; it ends by the handoff date at the latest.",
    "cooling_off": "Filed. A steward starts the handoff of roles and commitments; it ends by the handoff date at the latest.",
    "unwinding": "Handoff in progress. A steward confirms the departure once roles and commitments are handed over.",
    "completed": "Departure confirmed. The member has left this ecosystem.",
    "cancelled": "Withdrawn by the member. Nothing changed.",
}
LEAVER_ONLY = "Only the person leaving can withdraw their exit."
STEWARD_ONLY = "A steward of this ecosystem (not the person leaving) starts the handoff and confirms the departure."


def _today() -> _dt.date:
    return _dt.datetime.now(timezone.utc).date()


def _list_fields(record: ExitRecord, member_name: str | None) -> dict:
    return {
        "id": record.id, "ecosystem_id": record.ecosystem_id, "member_id": record.member_id,
        "member_name": member_name, "exit_type": record.exit_type, "status": record.status,
        "reason": record.departure_notice or None, "declared_date": record.declared_date,
        "target_completion_date": record.target_completion_date, "completed_date": record.completed_date,
        "created_at": record.created_at,
    }


def _list_item(record: ExitRecord, member_name: str | None) -> dict:
    return ExitListItem(**_list_fields(record, member_name)).model_dump(mode="json")


def allowed_next(record: ExitRecord, caller: Member | None) -> list[str]:
    """The moves this caller may make now, in table order."""
    moves = EXIT_MOVES.get(record.status, {})
    allowed = []
    for status, who in moves.items():
        if (who == "leaver" and is_exit_leaver(caller, record)) or (who == "steward" and can_steward_exit(caller, record)):
            allowed.append(status)
    return allowed


def to_detail(record: ExitRecord, member_name: str | None, caller: Member | None) -> dict:
    """The detail payload: the record, the next step and what the caller may do."""
    return ExitDetail(
        **_list_fields(record, member_name),
        coordinator_id=record.coordinator_id,
        commitment_inventory=record.commitment_inventory,
        unwinding_status=record.unwinding_status,
        data_export_requested=bool(record.data_export_requested),
        data_export_completed=record.data_export_completed,
        departure_notice=record.departure_notice,
        re_entry_eligible=record.re_entry_eligible,
        notes=record.notes,
        updated_at=record.updated_at,
        handoff_max_days=HANDOFF_DAYS["standard"],
        next_step=NEXT_STEP.get(record.status, ""),
        caller_is_leaver=is_exit_leaver(caller, record),
        allowed_next=allowed_next(record, caller),
    ).model_dump(mode="json")


async def _member_name(session, member_id) -> str | None:
    return await session.scalar(select(Member.display_name).where(Member.id == member_id))


async def load_visible_exit(session, request: Request, exit_id: uuid.UUID) -> ExitRecord:
    """In the caller's authorized ecosystems, or the caller's own exit (readable after they have left)."""
    try:
        return await get_scoped_or_404(session, request, ExitRecord, exit_id, label="Exit record")
    except ApiError:
        record = await session.get(ExitRecord, exit_id)
        if record is not None and is_exit_leaver(await caller_in(session, request, record.ecosystem_id), record):
            return record
        raise


async def _load_for_update(session, request: Request, exit_id: uuid.UUID) -> ExitRecord:
    """Row-locked load in the caller's scope: concurrent moves run one after another, so one transition row each."""
    record = (await session.execute(restrict_to_ecosystems(
        select(ExitRecord).where(ExitRecord.id == exit_id), ExitRecord, get_authorized_ecosystem_ids(request),
    ).with_for_update())).scalar_one_or_none()
    if record is None:
        raise ApiError(404, "Exit record not found")
    return record


async def _detail_response(session, request: Request, record: ExitRecord) -> dict:
    caller = await caller_in(session, request, record.ecosystem_id)
    return to_detail(record, await _member_name(session, record.member_id), caller)


@exit_api_bp.get("/")
@authenticated
async def list_exits(request: Request):
    """GET /api/v1/exit -- paginated list (status, exit_type, q), with the leaver's name and reason."""
    page = parse_pagination(request)
    async with request.app.ctx.db() as session:
        stmt = restrict_to_ecosystems(select(ExitRecord), ExitRecord, get_ecosystem_ids(request))
        stmt = apply_ecosystem_name_filter(stmt, ExitRecord, request)
        if status := request.args.get("status"):
            stmt = stmt.where(ExitRecord.status == status)
        if exit_type := request.args.get("exit_type"):
            stmt = stmt.where(ExitRecord.exit_type == exit_type)
        if search := request.args.get("q"):
            stmt = stmt.where(build_search_filter(ExitRecord, search, ExitRecord.departure_notice))
        total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = (await session.execute(
            stmt.add_columns(Member.display_name)
            .outerjoin(Member, Member.id == ExitRecord.member_id)
            .order_by(ExitRecord.created_at.desc())
            .offset(page.offset).limit(page.per_page)
        )).all()
    return json({
        "items": [_list_item(record, name) for record, name in rows],
        "total": total,
        "page": page.page,
        "per_page": page.per_page,
    })


@exit_api_bp.get("/<exit_id:uuid>")
@authenticated
async def get_exit(request: Request, exit_id: uuid.UUID):
    """GET /api/v1/exit/:id -- detail with the next step and the caller's allowed moves."""
    async with request.app.ctx.db() as session:
        record = await load_visible_exit(session, request, exit_id)
        return json(await _detail_response(session, request, record))


@exit_api_bp.post("/")
@authenticated
async def create_exit(request: Request):
    """POST /api/v1/exit {ecosystem_id, exit_type, reason} -- the caller files their OWN exit."""
    try:
        create_req = ExitCreateRequest(**(request.json or {}))
    except Exception:
        raise ApiError(400, "Choose the ecosystem you are leaving.")
    if create_req.exit_type not in HANDOFF_DAYS:
        raise ApiError(400, "Choose a standard (30-day) or urgent (7-day) handoff.")
    today = _today()
    async with request.app.ctx.db() as session:
        leaver = await caller_in(session, request, create_req.ecosystem_id)
        if create_req.member_id is not None and (leaver is None or create_req.member_id != leaver.id):
            raise ApiError(403, "You can only file your own exit.", {"code": "EXIT_SELF_ONLY"})
        if not is_active_member_in(leaver, create_req.ecosystem_id):
            raise ApiError(403, "Only an active member of this ecosystem can file an exit from it.")
        open_exit = await session.scalar(select(ExitRecord.id).where(
            ExitRecord.member_id == leaver.id, ExitRecord.status.in_(OPEN_STATUSES),
        ))
        if open_exit is not None:
            raise ApiError(409, "You already have an exit in progress here.", {"exit_id": str(open_exit)})
        record = ExitRecord(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            member_id=leaver.id,
            exit_type=create_req.exit_type,
            status="declared",
            declared_date=today,
            target_completion_date=today + timedelta(days=HANDOFF_DAYS[create_req.exit_type]),
            commitment_inventory=[],
            unwinding_status={},
            departure_notice=(create_req.reason or "").strip(),
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return json(to_detail(record, leaver.display_name, leaver), status=201)


async def _mark_exited(session, member_id: uuid.UUID, exit_id: uuid.UUID, today: _dt.date) -> None:
    """The leaver's membership becomes `exited` (outside the participating set, so no further consent asks)."""
    leaver = await session.get(Member, member_id)
    if leaver is None or leaver.current_status == EXITED:
        return
    session.add(MemberStatusTransition(
        id=uuid.uuid4(), member_id=leaver.id, from_status=leaver.current_status, to_status=EXITED,
        date=today, trigger="exit_completed", notes=f"Exit {exit_id} confirmed by a steward.",
    ))
    leaver.current_status = EXITED


@exit_api_bp.post("/<exit_id:uuid>/status")
@authenticated
async def status_transition(request: Request, exit_id: uuid.UUID):
    """POST /api/v1/exit/:id/status {new_status} -- moves from EXIT_MOVES; never a free-text status."""
    try:
        status_req = ExitStatusRequest(**(request.json or {}))
    except Exception:
        raise ApiError(400, "Say which status the exit should move to.")
    new_status = status_req.new_status
    if new_status not in EXIT_STATUSES:
        raise ApiError(400, "That is not an exit status.", {"allowed": list(EXIT_STATUSES)})
    today = _today()
    async with request.app.ctx.db() as session:
        record = await _load_for_update(session, request, exit_id)
        caller = await caller_in(session, request, record.ecosystem_id)
        who = EXIT_MOVES.get(record.status, {}).get(new_status)
        if who == "leaver" and not is_exit_leaver(caller, record):
            raise ApiError(403, LEAVER_ONLY)
        if who == "steward" and not can_steward_exit(caller, record):
            raise ApiError(403, STEWARD_ONLY)
        if who is None:
            raise ApiError(409, f"An exit that is {record.status} cannot move to {new_status}.",
                           {"allowed_next": allowed_next(record, caller)})
        old_status = record.status
        record.status = new_status
        if new_status == "unwinding" and record.coordinator_id is None:
            record.coordinator_id = caller.id
        if new_status == "completed":
            record.completed_date = today
            await _mark_exited(session, record.member_id, record.id, today)
        await session.commit()
        await session.refresh(record)
        logger.info("Exit %s status: %s -> %s", exit_id, old_status, new_status)
        return json(await _detail_response(session, request, record))


# --- Portable record ----------------------------------------------------------


def _unlinked_under_name(member_column, name_column, member: Member, name: str):
    """Rows with no member id under the member's current name in their ecosystem: left out and counted, never guessed."""
    return and_(
        member_column.is_(None),
        func.lower(func.trim(name_column)) == name,
        Proposal.ecosystem_id == member.ecosystem_id,
    )


async def build_portable_record(session, user_id: uuid.UUID, *, generated_at: _dt.datetime) -> dict:
    """The person's own governance record across every membership, as plain JSON.

    Advice, consent and test rows are matched on their member-id columns only; rows without one are
    counted in `omitted` (api/AGENTS.md "Emergency and exit").
    """
    rows = (await session.execute(
        select(Member, Ecosystem.name).join(Ecosystem, Ecosystem.id == Member.ecosystem_id)
        .where(Member.user_id == user_id).order_by(Member.created_at)
    )).all()
    memberships, proposals, advice, positions, agreements, reports, omitted = [], [], [], [], [], [], []
    for member, ecosystem_name in rows:
        memberships.append({
            "ecosystem_id": str(member.ecosystem_id), "ecosystem": ecosystem_name, "member_key": member.member_id,
            "display_name": member.display_name, "role": member.role, "status": member.current_status,
            "joined_at": member.created_at.isoformat() if member.created_at else None,
        })
        for proposal in (await session.execute(
            select(Proposal).where(Proposal.proposer_member_id == member.id).order_by(Proposal.created_at)
        )).scalars():
            proposals.append({"ecosystem": ecosystem_name, "proposal_id": proposal.proposal_id,
                              "title": proposal.title, "status": proposal.status})
        for consent, agreement in (await session.execute(
            select(AgreementMemberConsent, Agreement).join(Agreement, Agreement.id == AgreementMemberConsent.agreement_id)
            .where(AgreementMemberConsent.member_id == member.id).order_by(AgreementMemberConsent.attested_at)
        )).all():
            agreements.append({
                "ecosystem": ecosystem_name, "agreement_id": agreement.agreement_id, "title": agreement.title,
                "version": consent.agreement_version, "attested_at": consent.attested_at.isoformat(),
                "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
            })
        for report, proposal in (await session.execute(
            select(TestReport, Proposal).join(Proposal, Proposal.id == TestReport.proposal_id)
            .where(TestReport.reporter_member_id == member.id).order_by(TestReport.created_at)
        )).all():
            reports.append({"ecosystem": ecosystem_name, "proposal_id": proposal.proposal_id, "proposal": proposal.title,
                            "outcome": report.outcome, "observations": report.observations})

        name = (member.display_name or "").strip().lower()
        advice_from = (
            select(AdviceEntry, Proposal).join(AdviceLog, AdviceLog.id == AdviceEntry.advice_log_id)
            .join(Proposal, Proposal.id == AdviceLog.proposal_id)
        )
        positions_from = (
            select(ConsentParticipant, Proposal)
            .join(ConsentRecord, ConsentRecord.id == ConsentParticipant.consent_record_id)
            .join(Proposal, Proposal.id == ConsentRecord.proposal_id)
        )
        for entry, proposal in (await session.execute(advice_from.where(
            AdviceEntry.member_id == member.id
        ).order_by(AdviceEntry.created_at))).all():
            advice.append({"ecosystem": ecosystem_name, "proposal_id": proposal.proposal_id, "proposal": proposal.title,
                           "date": entry.date.isoformat() if entry.date else None, "advice": entry.advice_text})
        for participant, proposal in (await session.execute(positions_from.where(
            ConsentParticipant.member_id == member.id
        ).order_by(ConsentParticipant.created_at))).all():
            positions.append({"ecosystem": ecosystem_name, "proposal_id": proposal.proposal_id,
                              "proposal": proposal.title, "position": participant.position,
                              "reason": participant.reason, "round": participant.round})
        if name:
            unlinked = sum([
                len((await session.execute(advice_from.where(
                    _unlinked_under_name(AdviceEntry.member_id, AdviceEntry.advisor, member, name)))).all()),
                len((await session.execute(positions_from.where(
                    _unlinked_under_name(ConsentParticipant.member_id, ConsentParticipant.name, member, name)))).all()),
            ])
            if unlinked:
                omitted.append({"ecosystem": ecosystem_name, "rows": unlinked, "reason": (
                    "Older advice or consent entries were recorded under a name only, not linked to your "
                    "membership. A name can belong to someone else, so they are left out."
                )})
    return {
        "format": PORTABLE_RECORD_FORMAT,
        "generated_at": generated_at.isoformat(),
        "memberships": memberships,
        "proposals_authored": proposals,
        "advice_given": advice,
        "consent_positions": positions,
        "test_reports_filed": reports,
        "agreements_consented": agreements,
        "omitted": omitted,
    }


@exit_api_bp.get("/<exit_id:uuid>/portable-record")
@authenticated
async def portable_record(request: Request, exit_id: uuid.UUID):
    """GET /api/v1/exit/:id/portable-record -- the leaver's own record as JSON; marks the export, never the status."""
    now = _dt.datetime.now(timezone.utc).replace(tzinfo=None)
    async with request.app.ctx.db() as session:
        record = await session.get(ExitRecord, exit_id)
        caller = await caller_in(session, request, record.ecosystem_id) if record is not None else None
        if record is None or not is_exit_leaver(caller, record):
            if record is not None and record.ecosystem_id in get_authorized_ecosystem_ids(request):
                raise ApiError(403, "Only the person leaving can download their portable record.")
            raise ApiError(404, "Exit record not found")
        payload = await build_portable_record(session, caller.user_id, generated_at=now)
        payload["exit"] = {
            "id": str(record.id), "ecosystem_id": str(record.ecosystem_id), "status": record.status,
            "exit_type": record.exit_type,
            "declared_date": record.declared_date.isoformat() if record.declared_date else None,
            "handoff_ends": record.target_completion_date.isoformat() if record.target_completion_date else None,
        }
        record.data_export_requested = True
        record.data_export_completed = now.date()
        await session.commit()
    return json(payload)
