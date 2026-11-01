"""JSON API blueprint for conflict case management.

Blueprint: conflicts_api_bp, url_prefix="/api/v1/conflicts"

Cases move reported -> triaged -> in progress -> resolved -> closed. The reporter is
the caller; a case is readable by its reporter, facilitator, named parties and triage
stewards only; see api/AGENTS.md "Conflict care".
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import ConflictCase, Member, RepairAgreementRecord
from neos_agent.api import policy
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import (
    apply_ecosystem_name_filter,
    build_search_filter,
    get_authorized_ecosystem_ids,
    get_ecosystem_ids,
    parse_pagination,
    serialize_shared_ecosystem_ids,
)
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.services import dates
from neos_agent.api.schemas.conflicts import (
    ConflictCreateRequest,
    ConflictDetail,
    ConflictListItem,
    ConflictUpdateRequest,
    RepairAgreementSchema,
    RepairCreateRequest,
    RepairUpdateRequest,
)

logger = logging.getLogger(__name__)

# Case lifecycle table: each stage's allowed moves.
CONFLICT_MOVES: dict[str, tuple[str, ...]] = {
    "reported": ("triaged", "closed"),
    "triaged": ("in_progress", "resolved", "closed"),
    "in_progress": ("resolved", "closed"),
    "resolved": ("in_progress", "closed"),
    "closed": (),
}
# A status outside the table (a stray writer; revision r6c1e8a4f2d7 normalized the legacy ones):
# shown as "Needs a steward to review", and triage may put it at any stage.
UNKNOWN_STATUS_MOVES: tuple[str, ...] = ("triaged", "in_progress", "resolved", "closed")
# Fields the reporter may still correct; every other field is a triage decision.
REPORTER_EDITABLE_FIELDS = frozenset({"title", "description", "domain"})
# Repair follow-up: check-in offsets in days, and the status that ends a repair.
REPAIR_CHECKIN_DAYS = (30, 60, 90)
REPAIR_FULFILLED = "fulfilled"

REPAIR_NEEDS_CONFIRMATION = "Both parties must confirm before a repair agreement is marked fulfilled"
RESOLUTION_SUMMARY_REQUIRED = "Say how the case was resolved before marking it resolved"
TRIAGE_DENIED = "Only a steward of this ecosystem or the case facilitator can do that"

conflicts_api_bp = Blueprint("conflicts_api", url_prefix="/api/v1/conflicts")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def allowed_moves(status: str | None) -> tuple[str, ...]:
    """The table's moves for `status`; an unrecognized status may move to any stage (steward review)."""
    return CONFLICT_MOVES.get(status, UNKNOWN_STATUS_MOVES)


def _tier_label(tier: int | None) -> str:
    return {1: "facilitated conversation", 2: "mediation", 3: "formal circle"}.get(tier or 0, "chosen process")


def conflict_stage(case: ConflictCase, facilitator_name: str | None = None) -> dict[str, str]:
    """Stage, what happens next and who decides, for the case's current status."""
    who = facilitator_name or "The facilitator"
    if case.status == "reported":
        waiting = f"{facilitator_name} or a steward" if facilitator_name else "a steward of this ecosystem"
        urgent = " It is flagged as a safety concern, so it should be looked at first." if case.safety_flag else ""
        return {
            "stage": "Reported",
            "next_step": f"Waiting for {waiting} to triage it. Nobody has picked it up yet.{urgent}",
            "decided_by": "A steward of this ecosystem",
        }
    if case.status == "triaged":
        return {
            "stage": "Triaged",
            "next_step": f"{who} starts the {_tier_label(case.tier)} and moves the case to in progress.",
            "decided_by": "The facilitator or a steward",
        }
    if case.status == "in_progress":
        return {
            "stage": "In progress",
            "next_step": f"{who} works with the people involved toward a resolution, then records how it ended.",
            "decided_by": "The facilitator or a steward",
        }
    if case.status == "resolved":
        return {
            "stage": "Resolved",
            "next_step": "Repair check-ins at 30, 60 and 90 days follow up on any repair agreement; a steward closes the case when they are done.",
            "decided_by": "The facilitator or a steward",
        }
    if case.status == "closed":
        return {"stage": "Closed", "next_step": "Nothing further is needed.", "decided_by": "A steward of this ecosystem"}
    status = (case.status or "no status").replace("_", " ")
    return {
        "stage": "Needs a steward to review",
        "next_step": f"This case has a status from an older version (\"{status}\"). A steward of this ecosystem "
                     "checks it and moves it to the right stage.",
        "decided_by": "A steward of this ecosystem",
    }


def next_checkin(repair: RepairAgreementRecord, today: _dt.date | None = None) -> tuple[_dt.date | None, bool]:
    """The earliest scheduled check-in with no notes yet and whether it is past due; none once fulfilled."""
    today = today or dates.aoe_today()  # FX-Maint (F18): the one date rule, as the queue's Clock
    if repair.status == REPAIR_FULFILLED:
        return None, False
    for days in REPAIR_CHECKIN_DAYS:
        date = getattr(repair, f"checkin_{days}_date")
        if date is not None and not getattr(repair, f"checkin_{days}_notes"):
            return date, date < today
    return None, False


def _conflict_to_list_item(c: ConflictCase, caller: Member | None) -> dict:
    return ConflictListItem(
        id=c.id,
        ecosystem_id=c.ecosystem_id,
        case_id=c.case_id,
        title=c.title,
        status=c.status,
        severity=c.severity,
        scope=c.scope,
        tier=c.tier,
        urgency=c.urgency,
        safety_flag=c.safety_flag,
        domain=c.domain,
        created_at=c.created_at,
        caller_is_reporter=caller is not None and caller.id == c.reporter_id,
        **conflict_stage(c),
    ).model_dump(mode="json")


def _repair_to_schema(r: RepairAgreementRecord) -> RepairAgreementSchema:
    next_date, overdue = next_checkin(r)
    return RepairAgreementSchema(
        id=r.id,
        title=r.title,
        commitments=r.commitments,
        responsible_party=r.responsible_party,
        status=r.status,
        checkin_30_date=r.checkin_30_date,
        checkin_30_notes=r.checkin_30_notes,
        checkin_60_date=r.checkin_60_date,
        checkin_60_notes=r.checkin_60_notes,
        checkin_90_date=r.checkin_90_date,
        checkin_90_notes=r.checkin_90_notes,
        completed_date=r.completed_date,
        created_at=r.created_at,
        next_checkin_date=next_date,
        next_checkin_overdue=overdue,
    )


async def _member_names(session, *member_ids) -> dict[uuid.UUID, str]:
    ids = [member_id for member_id in member_ids if member_id is not None]
    if not ids:
        return {}
    rows = await session.execute(select(Member.id, Member.display_name).where(Member.id.in_(ids)))
    return {member_id: name for member_id, name in rows.all()}


async def _party_record(session, ecosystem_id: uuid.UUID, member_ids: list[uuid.UUID]) -> dict:
    """`parties` for storage: member ids (they authorize) plus display labels; every id must be a member of the ecosystem."""
    unique = list(dict.fromkeys(member_ids))
    rows = (await session.execute(select(Member.id, Member.display_name).where(
        Member.id.in_(unique), Member.ecosystem_id == ecosystem_id,
    ))).all()
    if len(rows) != len(unique):
        raise ApiError(400, "Every person involved must be a member of this ecosystem")
    names = dict(rows)
    return {"member_ids": [str(i) for i in unique], "labels": [names[i] for i in unique]}


def _party_names(case: ConflictCase, names: dict[uuid.UUID, str]) -> list[str]:
    """Display names for the case page: current member names, then legacy free-text labels."""
    stored = case.parties
    if isinstance(stored, dict):
        ids = [i for i in stored.get("member_ids") or [] if isinstance(i, str)]
        labels = stored.get("labels") or []
        return [names.get(uuid.UUID(i), labels[n] if n < len(labels) else i) for n, i in enumerate(ids)] + (
            [str(l) for l in labels[len(ids):]] if len(labels) > len(ids) else [])
    if isinstance(stored, list):
        return [str(item) for item in stored]
    return []


async def _conflict_to_detail(session, c: ConflictCase, caller: Member | None) -> dict:
    party_ids = [uuid.UUID(i) for i in policy.conflict_party_ids(c)]
    names = await _member_names(session, c.reporter_id, c.facilitator_id, *party_ids)
    facilitator_name = names.get(c.facilitator_id)
    can_triage = policy.can_triage_conflict(caller, c)
    return ConflictDetail(
        id=c.id,
        case_id=c.case_id,
        title=c.title,
        status=c.status,
        severity=c.severity,
        scope=c.scope,
        tier=c.tier,
        urgency=c.urgency,
        safety_flag=c.safety_flag,
        domain=c.domain,
        created_at=c.created_at,
        ecosystem_id=c.ecosystem_id,
        description=c.description,
        reporter_id=c.reporter_id,
        reporter_name=names.get(c.reporter_id),
        root_cause_category=c.root_cause_category,
        party_names=_party_names(c, names),
        facilitator_id=c.facilitator_id,
        facilitator_name=facilitator_name,
        triage_notes=c.triage_notes,
        resolution_summary=c.resolution_summary,
        resolved_date=c.resolved_date,
        updated_at=c.updated_at,
        caller_is_reporter=caller is not None and caller.id == c.reporter_id,
        caller_can_triage=can_triage,
        allowed_next=list(allowed_moves(c.status)) if can_triage else [],
        repair_agreements=[_repair_to_schema(r) for r in (c.repair_agreements or [])],
        **conflict_stage(c, facilitator_name),
    ).model_dump(mode="json")


async def load_visible_case(session, request: Request, conflict_id: uuid.UUID) -> tuple[ConflictCase, Member]:
    """The case and the caller's row in its ecosystem; a case the caller may not read is "not found"."""
    case = await get_scoped_or_404(
        session, request, ConflictCase, conflict_id,
        options=(selectinload(ConflictCase.repair_agreements),), label="Conflict case",
    )
    caller = await caller_in(session, request, case.ecosystem_id)
    if not policy.can_view_conflict(caller, case):
        raise ApiError(404, "Conflict case not found")
    return case, caller


async def _reload(session, case_id: uuid.UUID) -> ConflictCase:
    return (await session.execute(
        select(ConflictCase).options(selectinload(ConflictCase.repair_agreements)).where(ConflictCase.id == case_id)
    )).scalar_one()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@conflicts_api_bp.get("/")
@authenticated
async def list_conflicts(request: Request):
    """GET /api/v1/conflicts -- the cases the caller may read, filtered and paginated.

    Query params: status, severity, urgency, q (search case_id/title), page, per_page.
    """
    page = parse_pagination(request)

    async with request.app.ctx.db() as session:
        stmt = select(ConflictCase).order_by(ConflictCase.created_at.desc())
        stmt = restrict_to_ecosystems(stmt, ConflictCase, get_ecosystem_ids(request))
        stmt = apply_ecosystem_name_filter(stmt, ConflictCase, request)

        for column, name in (
            (ConflictCase.status, "status"),
            (ConflictCase.severity, "severity"),
            (ConflictCase.urgency, "urgency"),
        ):
            value = request.args.get(name)
            if value:
                stmt = stmt.where(column == value)

        search = request.args.get("q")
        if search:
            stmt = stmt.where(build_search_filter(ConflictCase, search, ConflictCase.title, ConflictCase.case_id))

        cases = (await session.execute(stmt)).scalars().all()

        # Readability depends on parties named inside JSON, so it is decided per case here (case volume is small).
        user_id = getattr(getattr(request.ctx, "user", None), "id", None) or request.ctx.member.user_id
        rows = (await session.execute(select(Member).where(
            Member.user_id == user_id,
            Member.ecosystem_id.in_({case.ecosystem_id for case in cases}),
        ))).scalars().all()
        caller_by_ecosystem = {row.ecosystem_id: row for row in rows}
        visible = [
            case for case in cases
            if policy.can_view_conflict(caller_by_ecosystem.get(case.ecosystem_id), case)
        ]

    window = visible[page.offset:page.offset + page.per_page]
    return json({
        "items": [_conflict_to_list_item(case, caller_by_ecosystem.get(case.ecosystem_id)) for case in window],
        "total": len(visible),
        "page": page.page,
        "per_page": page.per_page,
    })


@conflicts_api_bp.get("/<conflict_id:uuid>")
@authenticated
async def get_conflict(request: Request, conflict_id: uuid.UUID):
    """GET /api/v1/conflicts/:id -- case detail with repair agreements, stage and next step."""
    async with request.app.ctx.db() as session:
        case, caller = await load_visible_case(session, request, conflict_id)
        return json(await _conflict_to_detail(session, case, caller))


@conflicts_api_bp.post("/")
@authenticated
async def create_conflict(request: Request):
    """POST /api/v1/conflicts -- report a case; the reporter is the signed-in member, never a body field."""
    try:
        create_req = ConflictCreateRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        reporter = await caller_in(session, request, create_req.ecosystem_id)
        if not policy.is_active_member_in(reporter, create_req.ecosystem_id):
            raise ApiError(403, "Only active members of this ecosystem can report a conflict")

        parties = await _party_record(session, create_req.ecosystem_id, create_req.party_member_ids) if create_req.party_member_ids else None
        conflict = ConflictCase(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            case_id=f"CONF-{uuid.uuid4().hex[:8].upper()}",
            title=create_req.title,
            description=create_req.description,
            reporter_id=reporter.id,
            status="reported",
            severity=create_req.severity,
            scope=create_req.scope,
            tier=create_req.tier,
            root_cause_category=create_req.root_cause_category,
            urgency=create_req.urgency,
            safety_flag=create_req.safety_flag,
            parties=parties,
            domain=create_req.domain,
        )
        session.add(conflict)
        await session.commit()
        conflict = await _reload(session, conflict.id)
        return json(await _conflict_to_detail(session, conflict, reporter), status=201)


@conflicts_api_bp.put("/<conflict_id:uuid>")
@authenticated
async def update_conflict(request: Request, conflict_id: uuid.UUID):
    """PUT /api/v1/conflicts/:id -- triage and move a case (steward or facilitator); the reporter may correct text or withdraw."""
    try:
        update_req = ConflictUpdateRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e
    changes = update_req.model_dump(exclude_none=True)

    async with request.app.ctx.db() as session:
        case, caller = await load_visible_case(session, request, conflict_id)

        if not policy.can_triage_conflict(caller, case):
            is_reporter = caller.id == case.reporter_id
            withdraws = changes.keys() == {"status"} and changes["status"] == "closed"
            corrects = bool(changes) and set(changes) <= REPORTER_EDITABLE_FIELDS
            if not (is_reporter and (withdraws or corrects)):
                raise ApiError(403, TRIAGE_DENIED)

        new_status = changes.get("status")
        if new_status is not None and new_status != case.status:
            if new_status not in allowed_moves(case.status):
                raise ApiError(409, f"A {case.status.replace('_', ' ')} case cannot move to {new_status.replace('_', ' ')}",
                               {"allowed": list(allowed_moves(case.status))})
            if new_status == "resolved":
                summary = changes.get("resolution_summary") or case.resolution_summary
                if not (summary or "").strip():
                    raise ApiError(400, RESOLUTION_SUMMARY_REQUIRED)
                case.resolved_date = dates.utc_today()
        elif new_status == case.status:
            changes.pop("status")

        facilitator_id = changes.get("facilitator_id")
        if facilitator_id is not None:
            facilitator = await session.get(Member, facilitator_id)
            if not policy.is_active_member_in(facilitator, case.ecosystem_id) or policy.is_conflict_party(facilitator, case):
                raise ApiError(400, "The facilitator must be an active member of this ecosystem who is not a party to the case")

        if "party_member_ids" in changes:
            changes["parties"] = await _party_record(session, case.ecosystem_id, changes.pop("party_member_ids"))
        if "shared_ecosystem_ids" in changes:
            changes["shared_ecosystem_ids"] = serialize_shared_ecosystem_ids(update_req.shared_ecosystem_ids)
        for field, value in changes.items():
            setattr(case, field, value)

        await session.commit()
        case = await _reload(session, case.id)
        return json(await _conflict_to_detail(session, case, caller))


@conflicts_api_bp.post("/<conflict_id:uuid>/repair")
@authenticated
async def create_repair_agreement(request: Request, conflict_id: uuid.UUID):
    """POST /api/v1/conflicts/:id/repair -- record a repair agreement; 30/60/90-day check-ins default from today."""
    try:
        create_req = RepairCreateRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        case, caller = await load_visible_case(session, request, conflict_id)
        if not policy.can_triage_conflict(caller, case):
            raise ApiError(403, TRIAGE_DENIED)

        commitments_data = create_req.commitments
        if isinstance(commitments_data, list):
            commitments_data = {
                "items": commitments_data,
                "parties": create_req.parties,
                "review_date": str(create_req.review_date) if create_req.review_date else None,
                "facilitator_notes": create_req.facilitator_notes,
            }
        elif isinstance(commitments_data, dict):
            if create_req.parties:
                commitments_data["parties"] = create_req.parties
            if create_req.review_date:
                commitments_data["review_date"] = str(create_req.review_date)
            if create_req.facilitator_notes:
                commitments_data["facilitator_notes"] = create_req.facilitator_notes

        today = dates.utc_today()
        scheduled = {
            days: getattr(create_req, f"checkin_{days}_date") or today + _dt.timedelta(days=days)
            for days in REPAIR_CHECKIN_DAYS
        }
        repair = RepairAgreementRecord(
            id=uuid.uuid4(),
            conflict_case_id=conflict_id,
            title=create_req.title,
            commitments=commitments_data,
            responsible_party=create_req.responsible_party,
            status="active",
            checkin_30_date=scheduled[30],
            checkin_60_date=scheduled[60],
            checkin_90_date=scheduled[90],
        )
        session.add(repair)
        await session.commit()
        await session.refresh(repair)

    return json(_repair_to_schema(repair).model_dump(mode="json"), status=201)


@conflicts_api_bp.put("/<conflict_id:uuid>/repair/<repair_id:uuid>")
@authenticated
async def update_repair_agreement(request: Request, conflict_id: uuid.UUID, repair_id: uuid.UUID):
    """PUT /api/v1/conflicts/:id/repair/:repair_id -- record check-in notes; fulfilling needs the parties' confirmation."""
    try:
        update_req = RepairUpdateRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        case, caller = await load_visible_case(session, request, conflict_id)
        if not policy.can_triage_conflict(caller, case):
            raise ApiError(403, TRIAGE_DENIED)

        repair = (await session.execute(select(RepairAgreementRecord).where(
            RepairAgreementRecord.id == repair_id,
            RepairAgreementRecord.conflict_case_id == conflict_id,
        ))).scalar_one_or_none()
        if repair is None:
            raise ApiError(404, "Repair agreement not found")

        changes = update_req.model_dump(exclude_none=True)
        confirmed = changes.pop("confirmed_by_parties", False)
        if changes.get("status") == REPAIR_FULFILLED and repair.status != REPAIR_FULFILLED:
            if not confirmed:
                raise ApiError(400, REPAIR_NEEDS_CONFIRMATION)
            repair.completed_date = dates.utc_today()
            repair.commitments = {**(repair.commitments or {}), "confirmed_by_parties_on": str(repair.completed_date)}
        for field, value in changes.items():
            setattr(repair, field, value)

        await session.commit()
        await session.refresh(repair)

    return json(_repair_to_schema(repair).model_dump(mode="json"))
