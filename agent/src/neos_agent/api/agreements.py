"""JSON API blueprint for agreement management.

Blueprint: agreements_api_bp, url_prefix="/api/v1/agreements"

All endpoints require authentication via the neos_session cookie.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import re
import uuid
import datetime as _dt

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    Agreement,
    AgreementCeremony,
    AgreementMemberConsent,
    AgreementRatificationRecord,
    AgreementVersion,
    AmendmentRecord,
    Domain,
    Member,
    MemberAlignmentEvent,
    Proposal,
    ReviewRecord,
)

from .agreement_vocabulary import (
    AGREEMENT_STATUSES,
    AGREEMENT_TYPES,
    SUNSET_NOTICE_DAYS,
    canonical_agreement_status,
    canonical_agreement_type,
    default_review_date,
)
from neos_agent.services import dates
from .errors import ApiError, get_scoped_or_404
from .guards import authenticated, caller_in, reachable_ecosystem_ids
from .helpers import get_ecosystem_ids, get_authorized_ecosystem_ids, apply_ecosystem_name_filter, build_search_filter, parse_pagination, serialize_shared_ecosystem_ids
from .policy import can_conduct_agreement_ceremony, can_register_agreement, is_active_member_in
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.services.agreement_consent import (
    agreement_consent_summary,
    missing_agreement_consents,
    synchronize_agreement_requirements,
)
from neos_agent.services.act_gates import (
    AGREEMENT_LIFECYCLE,
    EVIDENCED_CEREMONIES,
    ActOutcome,
    TransitionRefused,
    advance_agreement,
    agreement_gate_status,
    apply_agreement_move,
    normalize_act_policy,
    resolve_proposal_policy,
)
from neos_agent.services.fingerprint import generate_fingerprint
from .schemas import (
    AgreementCeremonyEvidenceRequest,
    AgreementCeremonySchema,
    AgreementConsentRequest,
    AgreementConsentWithdrawalRequest,
    AgreementCreateRequest,
    AgreementDetail,
    AgreementHistoryResponse,
    AgreementListItem,
    AgreementUpdateRequest,
    AgreementMemberConsentSchema,
    AgreementConsentSummary,
    AgreementVersionSchema,
    AmendmentRecordSchema,
    RatificationRecordSchema,
    ReviewRecordSchema,
)

logger = logging.getLogger(__name__)

agreements_api_bp = Blueprint("agreements_api", url_prefix="/api/v1/agreements")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _escape_like(value: str) -> str:
    """Escape SQL LIKE/ILIKE wildcard characters."""
    return re.sub(r"([%_\\])", r"\\\1", value)


def _apply_filters(stmt, request: Request, eco_ids: list[uuid.UUID]):
    """Apply query-param filters to an Agreement select statement (no ecosystems -> no rows)."""
    stmt = restrict_to_ecosystems(stmt, Agreement, eco_ids)

    stmt = apply_ecosystem_name_filter(stmt, Agreement, request)

    agreement_type = request.args.get("type")
    if agreement_type:
        try:
            stmt = stmt.where(Agreement.type == canonical_agreement_type(agreement_type))
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    status = request.args.get("status")
    if status:
        try:
            stmt = stmt.where(Agreement.status == canonical_agreement_status(status))
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    domain = request.args.get("domain")
    if domain:
        stmt = stmt.where(Agreement.domain.ilike(f"%{_escape_like(domain)}%"))

    search = request.args.get("q")
    if search:
        stmt = stmt.where(build_search_filter(
            Agreement, search, Agreement.title, Agreement.agreement_id
        ))

    return stmt


def _utcnow() -> _dt.datetime:
    """Naive UTC now — governance timestamp columns are TIMESTAMP WITHOUT TIME ZONE.

    asyncpg refuses tz-aware datetimes for those columns ("can't subtract
    offset-naive and offset-aware datetimes"), which 500s any endpoint that
    writes datetime.now(UTC) directly. Mirrors api/emergency.py::_utcnow.
    """
    return _dt.datetime.now(_dt.UTC).replace(tzinfo=None)


def _agreement_to_list_item(a: Agreement) -> dict:
    """Convert an Agreement ORM instance to a serialisable dict."""
    return AgreementListItem(
        id=a.id,
        agreement_id=a.agreement_id,
        ecosystem_id=a.ecosystem_id,
        type=a.type,
        title=a.title,
        version=a.version,
        status=a.status,
        proposer=a.proposer,
        domain=a.domain,
        hierarchy_level=a.hierarchy_level,
        review_date=a.review_date,
        sunset_date=a.sunset_date,
        created_at=a.created_at,
        review_overdue=review_overdue(a),
    ).model_dump(mode="json")


def review_overdue(a: Agreement, now: _dt.datetime | None = None) -> bool:
    """The registry's visible flag: in force and its review date has passed (services/dates); it never invalidates it."""
    return a.status in IN_FORCE_STATUSES and dates.date_passed(a.review_date, now)


def _agreement_to_detail(a: Agreement) -> dict:
    """Convert an Agreement ORM instance (with ratification_records loaded)
    to a serialisable AgreementDetail dict."""
    ratifications = [
        RatificationRecordSchema(
            id=r.id,
            participant=r.participant,
            role=r.role,
            position=r.position,
            date=r.date,
        )
        for r in (a.ratification_records or [])
    ]
    ceremonies = [
        AgreementCeremonySchema(
            id=ceremony.id,
            stage=ceremony.stage,
            outcome=ceremony.outcome,
            evidence=ceremony.evidence,
            completed_at=ceremony.completed_at,
        ).model_dump(mode="json")
        for ceremony in (getattr(a, "ceremonies", None) or [])
    ]
    data = AgreementDetail(
        id=a.id,
        agreement_id=a.agreement_id,
        type=a.type,
        title=a.title,
        version=a.version,
        status=a.status,
        proposer=a.proposer,
        domain=a.domain,
        hierarchy_level=a.hierarchy_level,
        review_date=a.review_date,
        sunset_date=a.sunset_date,
        created_at=a.created_at,
        ecosystem_id=a.ecosystem_id,
        shared_ecosystem_ids=a.shared_ecosystem_ids,
        text=a.text,
        affected_parties=a.affected_parties,
        parent_agreement_id=a.parent_agreement_id,
        ratification_date=a.ratification_date,
        created_date=a.created_date,
        updated_at=a.updated_at,
        ratification_records=[r.model_dump(mode="json") for r in ratifications],
        ceremonies=ceremonies,
        requires_explicit_consent=getattr(a, "requires_explicit_consent", True),
        prerequisite_scopes=getattr(a, "prerequisite_scopes", None) or [],
        prerequisite_domain_ids=getattr(a, "prerequisite_domain_ids", None) or [],
        alignment_points=getattr(a, "alignment_points", 5),
    ).model_dump(mode="json")
    data["version_fingerprint"] = a.version_fingerprint
    data["act_policy"] = normalize_act_policy(getattr(a, "act_policy", None))
    return data


def _detail_options() -> tuple:
    """Eager loads the detail payload reads (async sessions cannot lazy-load)."""
    return (selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))


async def _reload_for_detail(db, agreement_id: uuid.UUID) -> Agreement:
    """The agreement with every relationship the detail payload reads."""
    statement = select(Agreement).options(*_detail_options()).where(Agreement.id == agreement_id)
    return (await db.execute(statement)).scalar_one()


async def _registered_from_proposal(db, agreement: Agreement) -> dict | None:
    """{id, proposal_id, title} of the ratified proposal that created this agreement (it passed the ACT gates), else None.

    An amending proposal is not its origin: the amended agreement ran its own process first.
    """
    proposal = await db.scalar(select(Proposal).where(
        Proposal.registered_agreement_id == agreement.id, Proposal.amends_agreement_id.is_(None),
    ).order_by(Proposal.created_at).limit(1))
    if proposal is None:
        return None
    return {"id": str(proposal.id), "proposal_id": proposal.proposal_id, "title": proposal.title}


async def _agreement_detail_payload(db, agreement: Agreement, caller: Member | None,
                                    outcome: ActOutcome | None = None) -> dict:
    """Detail plus consent progress, gates, the ACT outcome when one ran, and the caller's attestation."""
    payload = _agreement_to_detail(agreement)
    summary = await agreement_consent_summary(db, agreement)
    payload["consent_summary"] = AgreementConsentSummary(**summary).model_dump(mode="json")
    payload["gates"] = await agreement_gate_status(db, agreement)
    if outcome is not None:
        outcome.attach(payload)
    payload["registered_from_proposal"] = await _registered_from_proposal(db, agreement)
    payload["caller_role"] = caller.role if caller else None
    payload["caller_can_conduct"] = can_conduct_agreement_ceremony(caller, agreement)
    payload.update(_review_fields(agreement, caller))
    # "Propose a change": an in-force agreement changes only through a ratified amending proposal.
    payload["caller_can_propose_change"] = caller is not None and agreement.status in IN_FORCE_STATUSES
    if caller is None:
        return payload
    consent = await db.scalar(select(AgreementMemberConsent).where(
        AgreementMemberConsent.agreement_id == agreement.id,
        AgreementMemberConsent.member_id == caller.id,
        AgreementMemberConsent.agreement_version == agreement.version,
    ))
    if consent is None:
        return payload
    awarded = await db.scalar(
        select(func.coalesce(func.sum(MemberAlignmentEvent.delta), 0)).where(
            MemberAlignmentEvent.agreement_consent_id == consent.id
        )
    )
    payload["current_member_consent"] = AgreementMemberConsentSchema(
        id=consent.id,
        member_id=consent.member_id,
        agreement_version=consent.agreement_version,
        attested_at=consent.attested_at,
        withdrawn_at=consent.withdrawn_at,
        alignment_awarded=int(awarded or 0),
    ).model_dump(mode="json")
    return payload


async def _validate_prerequisite_domains(db, ecosystem_id: uuid.UUID, domain_ids: list[uuid.UUID]) -> str | None:
    """Ensure scoped gates only reference domains in the agreement's ecosystem."""
    if not domain_ids:
        return None
    found = set((await db.execute(select(Domain.id).where(
        Domain.ecosystem_id == ecosystem_id,
        Domain.id.in_(domain_ids),
    ))).scalars().all())
    if found != set(domain_ids):
        return "Prerequisite domains must belong to the agreement ecosystem"
    return None


def _bump_version(agreement: Agreement) -> None:
    """Increment the minor version number (e.g. 1.0 -> 1.1)."""
    parts = agreement.version.split(".")
    if len(parts) == 2:
        major, minor = parts
        try:
            agreement.version = f"{major}.{int(minor) + 1}"
        except ValueError:
            agreement.version = agreement.version + ".1"
    else:
        agreement.version = agreement.version + ".1"


def _snapshot_agreement(agreement: Agreement, change_reason: str | None = None, changed_by: str | None = None) -> AgreementVersion:
    """Create an immutable snapshot of the current agreement state."""
    return AgreementVersion(
        id=uuid.uuid4(),
        agreement_id=agreement.id,
        version=agreement.version,
        status=agreement.status,
        title=agreement.title,
        text=agreement.text,
        type=agreement.type,
        proposer=agreement.proposer,
        domain=agreement.domain,
        hierarchy_level=agreement.hierarchy_level,
        affected_parties=agreement.affected_parties,
        review_date=agreement.review_date,
        sunset_date=agreement.sunset_date,
        ratification_date=agreement.ratification_date,
        version_fingerprint=agreement.version_fingerprint,
        change_reason=change_reason,
        changed_by=changed_by,
        requires_explicit_consent=agreement.requires_explicit_consent,
        prerequisite_scopes=agreement.prerequisite_scopes,
        prerequisite_domain_ids=agreement.prerequisite_domain_ids,
        alignment_points=agreement.alignment_points,
    )


def _regenerate_fingerprint(agreement: Agreement) -> None:
    """Fingerprint the current title, text, version and status."""
    agreement.version_fingerprint = generate_fingerprint(
        agreement.title, agreement.text, agreement.version, agreement.status
    )


CEREMONY_DENIED = "Only an active ecosystem steward (admin or owner) may conduct this ceremony"
REGISTER_DENIED = "Only an active ecosystem steward can register a ratified proposal as an agreement"
# Agreements in force: proposals may be governed by or amend them.
IN_FORCE_STATUSES = ("active", "under_review")
# Fields members attest to: only a change to these is a new version (consent is bound to the version).
VERSIONED_FIELDS = ("title", "text")
# Proposal type -> agreement type for a newly registered agreement.
_AGREEMENT_TYPE_FOR_PROPOSAL = {"policy": "policy", "operational": "operational", "resource": "resource",
                                "structural": "organizational"}


# G-Maint: how an agreement review ends (framework agreement-review E.3-5); services/AGENTS.md "Maintenance and health".
EDITABLE_STATUSES = ("draft", "advice")
REVIEW_OUTCOMES = {"active": "renewed", "sunset": "sunset"}
FINDINGS_REQUIRED = ("Write the review's findings (at least 8 characters): what the review found and why it "
                     "ends this way.")
REVIEW_DATE_INVALID = "The next review date must be a date (YYYY-MM-DD) later than today."
ROLLBACK_IN_FORCE = "An agreement in force changes through a proposal (Propose a change), not a rollback."
ROLLBACK_LOCKED = "Only a draft, or an agreement in its advice stage, can be rolled back."
# The terms a rollback restores; never status, review_date or sunset_date (those move only through ceremonies).
ROLLBACK_FIELDS = ("title", "text", "type", "proposer", "domain", "hierarchy_level", "affected_parties",
                   "requires_explicit_consent", "prerequisite_scopes", "prerequisite_domain_ids", "alignment_points")


def ends_review(agreement: Agreement, to: str | None) -> bool:
    """`to` concludes a review in progress: renew (back in force) or sunset; its findings are the evidence (the
    lifecycle table asks no gate of either move: api/AGENTS.md "Maintenance and health (G-Maint)")."""
    return agreement.status == "under_review" and to in REVIEW_OUTCOMES


# FX-Maint: one row lock for every surface (REST, MCP, chat) and the archive gate's own words; api/AGENTS.md
# "Maintenance and health (G-Maint)" > "One move at a time".
AGREEMENT_CHANGED = ("This agreement changed while you were acting: it is now {status}. Reload it to see what "
                     "happened, then decide again.")


def sunset_not_ended(agreement: Agreement) -> TransitionRefused:
    """409 for archiving before the sunset's notice period has run."""
    ends = agreement.sunset_date.isoformat() if agreement.sunset_date else None
    return TransitionRefused(409, f"Its sunset runs until {ends}: it can be archived once that day has ended "
                             "everywhere.", {"code": "SUNSET_NOT_ENDED", "sunset_date": ends})


def gate_refusal(agreement: Agreement, move, gates: dict) -> TransitionRefused | None:
    """Why `move`'s gate refuses it now (the sunset's end, or a declared ACT gate), else None."""
    if move.gate is None or gates[move.gate]["met"]:
        return None
    if move.gate == "sunset_ended":
        return sunset_not_ended(agreement)
    return TransitionRefused(
        409,
        f"The {move.gate} gate is not satisfied — the conditions declared in the agreement's ACT policy must be met first",
        {"gates": gates},
    )


async def lock_for_move(db, agreement: Agreement) -> None:
    """Take the agreement row FOR UPDATE before a ceremony; 409 AGREEMENT_CHANGED when another move landed first."""
    locked = await db.scalar(select(Agreement.status).where(Agreement.id == agreement.id).with_for_update())
    if locked != agreement.status:
        raise TransitionRefused(409, AGREEMENT_CHANGED.format(status=locked),
                                {"code": "AGREEMENT_CHANGED", "status": locked})


def review_outcome_refusal(agreement: Agreement, to: str | None, findings: str | None,
                           next_review_date: _dt.date | None, now: _dt.datetime | None = None) -> TransitionRefused | None:
    """Why ending this review would be refused (no findings, a next review date not after today), else None."""
    if not ends_review(agreement, to):
        return None
    if len((findings or "").strip()) < 8:
        return TransitionRefused(400, FINDINGS_REQUIRED, {"code": "FINDINGS_REQUIRED"})
    if to == "active" and next_review_date is not None and next_review_date <= dates.aoe_today(now):
        return TransitionRefused(400, REVIEW_DATE_INVALID, {"code": "REVIEW_DATE_INVALID"})
    return None


def sunset_ends_on(agreement: Agreement, now: _dt.datetime | None = None) -> _dt.date:
    """When a sunset started now would end: the notice period from today, or a later date already set."""
    notice_end = dates.aoe_today(now) + _dt.timedelta(days=SUNSET_NOTICE_DAYS)
    return max(notice_end, agreement.sunset_date) if agreement.sunset_date else notice_end


def parse_review_date(value) -> _dt.date | None:
    """A next review date from a request (YYYY-MM-DD or empty); anything else is 400 REVIEW_DATE_INVALID."""
    if value in (None, ""):
        return None
    try:
        return _dt.date.fromisoformat(str(value).strip())
    except ValueError:
        raise ApiError(400, REVIEW_DATE_INVALID, {"code": "REVIEW_DATE_INVALID"}) from None


def _review_fields(agreement: Agreement, caller: Member | None) -> dict:
    """Detail fields for the review dialog and the registry flag (C1-C3)."""
    reviewing = agreement.status == "under_review"
    return {
        "review_overdue": review_overdue(agreement),
        "default_next_review_date": (default_review_date(agreement.type, dates.aoe_today()).isoformat()
                                     if reviewing else None),
        "sunset_ends_on": sunset_ends_on(agreement).isoformat() if reviewing else None,
        "caller_can_rollback": agreement.status in EDITABLE_STATUSES and is_active_member_in(caller, agreement.ecosystem_id),
    }


def _record_review(db, agreement: Agreement, to: str, *, caller: Member, findings: str,
                   next_review_date: _dt.date | None) -> None:
    """Write the ReviewRecord for a finished review and move the dates: renew sets the next review, sunset its end."""
    now = dates.utc_now()
    due = agreement.review_date
    if to == "active":
        agreement.review_date = next_review_date or default_review_date(agreement.type, dates.aoe_today(now))
    else:
        agreement.sunset_date = sunset_ends_on(agreement, now)
    db.add(ReviewRecord(
        id=uuid.uuid4(), ecosystem_id=agreement.ecosystem_id, review_id=f"REV-{uuid.uuid4().hex[:8].upper()}",
        agreement_id=agreement.id, agreement_version=agreement.version,
        review_type="scheduled" if dates.date_passed(due, now) else "requested",
        trigger=(f"Review date {due.isoformat()}" if due else "No review date was set"),
        review_body={"conducted_by": caller.display_name, "member_id": str(caller.id)},
        date=dates.utc_today(now),
        evaluation={"findings": findings, "due_date": due.isoformat() if due else None,
                    "on_time": None if due is None else not dates.date_passed(due, now)},
        outcome=REVIEW_OUTCOMES[to],
        next_review_date=agreement.review_date if to == "active" else None,
    ))


async def transition_agreement(db, agreement: Agreement, *, to: str | None = None, caller: Member | None,
                               evidence: str | None = None, next_review_date: _dt.date | None = None) -> ActOutcome:
    """Conduct the ceremony to `to` (steward rule, table, evidence, gate), then the automatic cascade.

    Shared by REST, MCP and the chat tool. Snapshots the version before each change and
    regenerates the fingerprint; the caller commits. Moves and gates:
    services/act_gates.py AGREEMENT_LIFECYCLE. Ending a review (renew or sunset) needs findings
    (`evidence`) and writes a ReviewRecord.
    """
    moved, minted = None, None
    if to is not None:
        if not can_conduct_agreement_ceremony(caller, agreement):
            raise TransitionRefused(403, CEREMONY_DENIED)
        await lock_for_move(db, agreement)
        move = AGREEMENT_LIFECYCLE.manual_move(agreement.status, to)
        if move is None:
            raise TransitionRefused(
                400,
                f"Invalid transition: {agreement.status} -> {to}",
                {"allowed": AGREEMENT_LIFECYCLE.manual_targets(agreement.status)},
            )
        evidence = (evidence or "").strip()
        refusal = review_outcome_refusal(agreement, to, evidence, next_review_date)
        if refusal is not None:
            raise refusal
        concludes_review = ends_review(agreement, to)
        if to in EVIDENCED_CEREMONIES and len(evidence) < 8:
            raise TransitionRefused(400, f"Documented evidence is required for the {to} ceremony")
        if move.gate is not None:
            refused = gate_refusal(agreement, move, await agreement_gate_status(db, agreement))
            if refused is not None:
                raise refused
        db.add(_snapshot_agreement(
            agreement,
            change_reason=f"Status transition: {agreement.status} -> {to}",
            changed_by=caller.display_name,
        ))
        moved = f"{agreement.status}->{to}"
        minted = await apply_agreement_move(db, agreement, move, caller=caller, evidence=evidence)
        if concludes_review:
            _record_review(db, agreement, to, caller=caller, findings=evidence, next_review_date=next_review_date)
        _regenerate_fingerprint(agreement)

    outcome = await advance_agreement(db, agreement, caller=caller)
    if outcome.auto_transitions:
        db.add(_snapshot_agreement(
            agreement,
            change_reason="Auto-advanced by ACT gate engine: " + ", ".join(outcome.auto_transitions),
            changed_by="ACT gate engine",
        ))
        _regenerate_fingerprint(agreement)
    outcome.moved = moved
    outcome.decision_record_id = outcome.decision_record_id or minted
    return outcome


async def _consent_gate_scope(db, request: Request) -> list[uuid.UUID]:
    """Active plus pending-consent ecosystems: a newcomer reads and consents from the consent gate."""
    return await reachable_ecosystem_ids(db, request, include_pending=True)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@agreements_api_bp.get("/vocabulary")
@authenticated
async def agreement_vocabulary(request: Request):
    """GET /api/v1/agreements/vocabulary -- canonical filter and form values."""
    return json({
        "types": sorted(AGREEMENT_TYPES),
        "statuses": sorted(AGREEMENT_STATUSES),
    })


@agreements_api_bp.get("/")
@authenticated
async def list_agreements(request: Request):
    """GET /api/v1/agreements -- paginated list with filters.

    Query params: type, status, domain, q, page (default 1), per_page (default 25, max 100).
    Returns JSON: {"items": [...], "total": N, "page": P, "per_page": PP}
    """
    page = parse_pagination(request)

    async with request.app.ctx.db() as db:
        stmt = select(Agreement).order_by(Agreement.created_at.desc())
        try:
            stmt = _apply_filters(stmt, request, get_ecosystem_ids(request))
        except ValueError as exc:
            raise ApiError(400, str(exc)) from None

        total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        agreements = (await db.execute(stmt.offset(page.offset).limit(page.per_page))).scalars().all()

    return json({
        "items": [_agreement_to_list_item(a) for a in agreements],
        "total": total,
        "page": page.page,
        "per_page": page.per_page,
    })


@agreements_api_bp.get("/<agreement_id:uuid>")
@authenticated
async def get_agreement(request: Request, agreement_id: uuid.UUID):
    """GET /api/v1/agreements/:id -- detail with ratification records.

    Scoped to active and pending-consent ecosystems (owned or shared).
    Returns JSON: AgreementDetail
    """
    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, options=_detail_options(), label="Agreement",
            ecosystem_ids=await _consent_gate_scope(db, request),
        )
        caller = await caller_in(db, request, agreement.ecosystem_id)
        return json(await _agreement_detail_payload(db, agreement, caller))


@agreements_api_bp.post("/")
@authenticated
async def create_agreement(request: Request):
    """POST /api/v1/agreements -- create a new agreement.

    Accepts JSON: AgreementCreateRequest
    Returns JSON: AgreementDetail with 201 status.
    """
    body = request.json or {}
    try:
        create_req = AgreementCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    # Authorized ecosystems are the caller's active memberships (policy.is_active_member_in).
    if create_req.ecosystem_id not in get_authorized_ecosystem_ids(request):
        raise ApiError(403, "Access denied: ecosystem not in scope")

    agreement_id_str = f"AGR-{uuid.uuid4().hex[:8].upper()}"

    async with request.app.ctx.db() as db:
        domain_error = await _validate_prerequisite_domains(
            db, create_req.ecosystem_id, create_req.prerequisite_domain_ids
        )
        if domain_error:
            raise ApiError(400, domain_error)
        agreement = Agreement(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            shared_ecosystem_ids=serialize_shared_ecosystem_ids(create_req.shared_ecosystem_ids),
            agreement_id=agreement_id_str,
            type=create_req.type,
            title=create_req.title,
            version="1.0",
            status="draft",
            proposer=create_req.proposer,
            domain=create_req.domain,
            text=create_req.text,
            hierarchy_level=create_req.hierarchy_level,
            affected_parties=create_req.affected_parties,
            review_date=create_req.review_date or default_review_date(create_req.type, dates.aoe_today()),
            sunset_date=create_req.sunset_date,
            created_date=dates.utc_today(),
            requires_explicit_consent=create_req.requires_explicit_consent,
            prerequisite_scopes=create_req.prerequisite_scopes,
            prerequisite_domain_ids=[str(domain_id) for domain_id in create_req.prerequisite_domain_ids],
            alignment_points=create_req.alignment_points,
            act_policy=normalize_act_policy(
                create_req.act_policy.model_dump() if create_req.act_policy else None
            ),
        )
        _regenerate_fingerprint(agreement)
        db.add(agreement)
        await db.flush()
        await synchronize_agreement_requirements(db, agreement)
        await db.commit()

        agreement = await _reload_for_detail(db, agreement.id)
        caller = await caller_in(db, request, agreement.ecosystem_id)
        return json(await _agreement_detail_payload(db, agreement, caller), status=201)


@agreements_api_bp.put("/<agreement_id:uuid>")
@authenticated
async def update_agreement(request: Request, agreement_id: uuid.UUID):
    """PUT /api/v1/agreements/:id -- update an agreement.

    Accepts JSON: AgreementUpdateRequest (only non-None fields are applied).
    Returns JSON: AgreementDetail
    """
    body = request.json or {}
    try:
        update_req = AgreementUpdateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, options=_detail_options(), label="Agreement",
        )
        actor = await caller_in(db, request, agreement.ecosystem_id)
        if not is_active_member_in(actor, agreement.ecosystem_id):
            raise ApiError(403, "Only an active ecosystem member may edit an agreement")

        if agreement.status not in EDITABLE_STATUSES:
            raise ApiError(409, "Only draft or advice agreements can be edited; reopen governance before changing agreement terms.")

        if update_req.prerequisite_domain_ids is not None:
            domain_error = await _validate_prerequisite_domains(
                db, agreement.ecosystem_id, update_req.prerequisite_domain_ids
            )
            if domain_error:
                raise ApiError(400, domain_error)

        # Save snapshot of current state before applying changes
        change_reason = body.get("change_reason", "Manual edit")
        db.add(_snapshot_agreement(agreement, change_reason=change_reason, changed_by=actor.display_name))

        update_data = update_req.model_dump(exclude_none=True)
        if "act_policy" in update_data:
            update_data["act_policy"] = normalize_act_policy(
                update_req.act_policy.model_dump() if update_req.act_policy else None
            )
        if "shared_ecosystem_ids" in update_data:
            update_data["shared_ecosystem_ids"] = serialize_shared_ecosystem_ids(
                update_req.shared_ecosystem_ids
            )
        if "prerequisite_domain_ids" in update_data:
            update_data["prerequisite_domain_ids"] = [
                str(domain_id) for domain_id in update_req.prerequisite_domain_ids or []
            ]
        text_changed = any(
            field in update_data and update_data[field] != getattr(agreement, field) for field in VERSIONED_FIELDS
        )
        for field, value in update_data.items():
            setattr(agreement, field, value)

        if text_changed:
            _bump_version(agreement)
        await synchronize_agreement_requirements(db, agreement)
        _regenerate_fingerprint(agreement)

        await db.commit()
        await db.refresh(agreement)

        agreement = await _reload_for_detail(db, agreement.id)
        return json(await _agreement_detail_payload(db, agreement, actor))


@agreements_api_bp.post("/<agreement_id:uuid>/status")
@authenticated
async def status_transition(request: Request, agreement_id: uuid.UUID):
    """POST /api/v1/agreements/:id/status -- conduct a status ceremony.

    Each transition is recorded as a governance ceremony. Advice, consent, and
    test are mandatory before activation; activation also needs test evidence.
    Returns JSON: AgreementDetail plus auto_transitions (and decision_record_id when minted).
    """
    body = request.json or {}
    new_status = body.get("status")
    if not new_status:
        raise ApiError(400, "\"status\" field is required")
    try:
        new_status = canonical_agreement_status(new_status)
    except ValueError as exc:
        raise ApiError(400, str(exc)) from None
    next_review_date = parse_review_date(body.get("next_review_date"))

    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, options=_detail_options(), label="Agreement",
        )
        actor = await caller_in(db, request, agreement.ecosystem_id)
        old_status = agreement.status
        outcome = await transition_agreement(
            db, agreement, to=new_status, caller=actor, evidence=body.get("evidence"),
            next_review_date=next_review_date,
        )
        await db.commit()
        await db.refresh(agreement)

        logger.info("Agreement %s status: %s -> %s", agreement_id, old_status, new_status)

        agreement = await _reload_for_detail(db, agreement.id)
        return json(await _agreement_detail_payload(db, agreement, actor, outcome))


@agreements_api_bp.post("/<agreement_id:uuid>/ceremonies")
@authenticated
async def record_ceremony_evidence(request: Request, agreement_id: uuid.UUID):
    """POST /api/v1/agreements/:id/ceremonies -- record an advice round or test evidence.

    Advice rounds (stage "advice", outcome "round") and test-case evidence
    (stage "test", outcome "evidence") are the measurable units of the ACT
    gates declared at the agreement level. When a recording completes the
    declared conditions the status advances automatically.
    Accepts JSON: {"stage": "advice"|"test", "note": "..."}
    Returns JSON: AgreementDetail with 201 status.
    """
    try:
        evidence_request = AgreementCeremonyEvidenceRequest(**(request.json or {}))
    except Exception as exc:
        raise ApiError(400, f"Invalid request: {exc}") from None

    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, options=_detail_options(), label="Agreement",
        )
        actor = await caller_in(db, request, agreement.ecosystem_id)
        if not is_active_member_in(actor, agreement.ecosystem_id):
            raise ApiError(403, "Only an active ecosystem member may record ceremony evidence")

        stage = evidence_request.stage
        if agreement.status != stage:
            raise ApiError(
                409,
                f"Evidence for the {stage} stage can only be recorded while the agreement is in {stage} (current: {agreement.status})",
            )

        db.add(AgreementCeremony(
            id=uuid.uuid4(),
            agreement_id=agreement.id,
            stage=stage,
            completed_by_member_id=actor.id,
            outcome={"advice": "round", "test": "evidence"}[stage],
            evidence=evidence_request.note.strip(),
            completed_at=_utcnow(),
        ))

        outcome = await transition_agreement(db, agreement, caller=actor)
        await db.commit()

        agreement = await _reload_for_detail(db, agreement.id)
        return json(await _agreement_detail_payload(db, agreement, actor, outcome), status=201)


CONSENT_NOT_OPEN = "Agreement consent opens during the consent ceremony"
CONSENT_OPEN_STATUSES = ("consent", "test", "active", "under_review")


async def record_member_consent(db, agreement: Agreement, actor: Member, attestation: str) -> AgreementMemberConsent:
    """Attest `actor` to the current version: the consent row, its alignment-ledger credit, membership activation.

    Shared by REST and MCP so both write the ledger; `actor` is the caller's row, already row-locked
    by REST. The caller then runs the cascade (transition_agreement) and commits.
    """
    if agreement.status not in CONSENT_OPEN_STATUSES:
        raise TransitionRefused(409, CONSENT_NOT_OPEN)
    consent = await db.scalar(select(AgreementMemberConsent).where(
        AgreementMemberConsent.agreement_id == agreement.id,
        AgreementMemberConsent.member_id == actor.id,
        AgreementMemberConsent.agreement_version == agreement.version,
    ).with_for_update())
    now = _utcnow()
    if consent is None:
        consent = AgreementMemberConsent(
            id=uuid.uuid4(), agreement_id=agreement.id, member_id=actor.id,
            agreement_version=agreement.version, attestation=attestation,
            attested_at=now,
        )
        db.add(consent)
        await db.flush()
    else:
        consent.attestation = attestation
        consent.attested_at = now
        if consent.withdrawn_at is not None:
            consent.revision += 1
        consent.withdrawn_at = None
        consent.withdrawal_reason = None

    previous_delta = await db.scalar(
        select(func.coalesce(func.sum(MemberAlignmentEvent.delta), 0)).where(
            MemberAlignmentEvent.agreement_consent_id == consent.id
        )
    )
    delta = max(0, agreement.alignment_points - int(previous_delta or 0))
    if delta:
        db.add(MemberAlignmentEvent(
            id=uuid.uuid4(), member_id=actor.id, ecosystem_id=agreement.ecosystem_id,
            agreement_consent_id=consent.id, event_kind=f"state:{consent.revision}",
            delta=delta, recorded_at=now,
        ))
        actor.agreement_alignment_score += delta
    actor.last_governance_activity_date = now.date()
    if actor.current_status == "pending_consent":
        pending = await missing_agreement_consents(
            db, actor.id, agreement.ecosystem_id, "ecosystem"
        )
        if not pending:  # G-Onboard: consent activates (owner decision), recorded as one transition
            from neos_agent.services.member_lifecycle import CONSENT_ACTIVATED, record_transition
            record_transition(db, actor, "active", trigger=CONSENT_ACTIVATED, notes=f"Consented to {agreement.title}")
    return consent


async def register_ratified_proposal(db, proposal: Proposal, *, caller: Member | None) -> Agreement:
    """A steward turns a ratified proposal into registry text: amend `amends_agreement_id`, else a new agreement.

    Amending writes an AmendmentRecord and a new version (members re-attest, consent is per version).
    The text is the one captured at ratification (`ratified_text`). Row-locks the proposal (and the
    amended agreement) so concurrent requests register once. Links the proposal to the agreement;
    the caller commits. See api/AGENTS.md "Ratified is not registered".
    """
    if not can_register_agreement(caller, proposal):
        raise ApiError(403, REGISTER_DENIED)
    await db.refresh(proposal, with_for_update=True)  # a concurrent register waits here, then sees the link
    if proposal.status != "ratified":
        raise ApiError(409, "Only a ratified proposal can be registered as an agreement")
    if proposal.registered_agreement_id is not None:
        raise ApiError(409, "This proposal is already registered", {"agreement_id": str(proposal.registered_agreement_id)})
    text = (proposal.ratified_text or "").strip()
    if not text:
        raise ApiError(409, "No text was captured when this proposal was ratified, so there is nothing to register")

    if proposal.amends_agreement_id is not None:
        agreement = await db.scalar(
            select(Agreement).where(Agreement.id == proposal.amends_agreement_id).with_for_update()
        )
        if agreement is None or agreement.ecosystem_id != proposal.ecosystem_id:
            raise ApiError(409, "The agreement this proposal amends no longer exists")
        if agreement.status not in IN_FORCE_STATUSES:
            raise ApiError(409, f"The agreement this proposal amends is no longer in force ({agreement.status})")
        db.add(_snapshot_agreement(
            agreement, change_reason=f"Amended by ratified proposal {proposal.proposal_id}",
            changed_by=caller.display_name,
        ))
        previous_version, previous_text = agreement.version, agreement.text
        agreement.text = text
        _bump_version(agreement)
        _regenerate_fingerprint(agreement)
        db.add(AmendmentRecord(
            id=uuid.uuid4(), ecosystem_id=agreement.ecosystem_id,
            amendment_id=f"AMD-{uuid.uuid4().hex[:8].upper()}", parent_agreement_id=agreement.id,
            parent_agreement_version=previous_version, amendment_type="proposal",
            proposed_by=proposal.proposer, date=dates.utc_today(),
            changes={"proposal_id": proposal.proposal_id, "text": {"from": previous_text, "to": text}},
            rationale=proposal.rationale, act_level_used="act-process",
            new_agreement_version=agreement.version, status="ratified",
        ))
        await synchronize_agreement_requirements(db, agreement)
    else:
        policy, _source = await resolve_proposal_policy(db, proposal)
        agreement = Agreement(
            id=uuid.uuid4(), ecosystem_id=proposal.ecosystem_id, shared_ecosystem_ids=proposal.shared_ecosystem_ids,
            agreement_id=f"AGR-{uuid.uuid4().hex[:8].upper()}",
            type=_AGREEMENT_TYPE_FOR_PROPOSAL.get(proposal.type, "policy"), title=proposal.title,
            version="1.0", status="active", proposer=proposal.proposer, domain=proposal.affected_domain,
            text=text, hierarchy_level="domain", created_date=dates.utc_today(),
            ratification_date=dates.utc_today(), requires_explicit_consent=True, prerequisite_scopes=[],
            review_date=default_review_date(_AGREEMENT_TYPE_FOR_PROPOSAL.get(proposal.type, "policy"), dates.aoe_today()),
            prerequisite_domain_ids=[], alignment_points=5, act_policy=policy,
        )
        _regenerate_fingerprint(agreement)
        db.add(agreement)
        await db.flush()
        db.add(_snapshot_agreement(
            agreement, change_reason=f"Registered from ratified proposal {proposal.proposal_id}",
            changed_by=caller.display_name,
        ))
        await synchronize_agreement_requirements(db, agreement)
    db.add(AgreementCeremony(
        id=uuid.uuid4(), agreement_id=agreement.id, stage=agreement.status,
        completed_by_member_id=caller.id, outcome="registered",
        evidence=f"Registered from ratified proposal {proposal.proposal_id} (decision DEC-{proposal.proposal_id})",
        completed_at=_utcnow(),
    ))
    proposal.registered_agreement_id = agreement.id
    await db.flush()
    return agreement


async def _locked_caller(db, request: Request, agreement: Agreement) -> Member | None:
    """The caller's row in the agreement's ecosystem, row-locked: consent changes their alignment score."""
    caller = await caller_in(db, request, agreement.ecosystem_id)
    if caller is not None:
        await db.refresh(caller, with_for_update=True)
    return caller


@agreements_api_bp.post("/<agreement_id:uuid>/consent")
@authenticated
async def attest_agreement_consent(request: Request, agreement_id: uuid.UUID):
    """Record the caller's explicit acceptance of the current agreement version."""
    try:
        consent_request = AgreementConsentRequest(**(request.json or {}))
    except Exception as exc:
        raise ApiError(400, f"Invalid request: {exc}") from None

    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, options=_detail_options(), label="Agreement",
            ecosystem_ids=await _consent_gate_scope(db, request),
        )
        if agreement.status not in CONSENT_OPEN_STATUSES:
            raise ApiError(409, CONSENT_NOT_OPEN)

        actor = await _locked_caller(db, request, agreement)
        if actor is None:
            raise ApiError(403, "Only an ecosystem member may attest agreement consent")

        await record_member_consent(db, agreement, actor, consent_request.attestation)

        # A completed consent ceremony advances the agreement automatically
        # (and mints the commitment artifact if the test gate is already met).
        outcome = await transition_agreement(db, agreement, caller=actor)
        await db.commit()
        await db.refresh(agreement)

        payload = await _agreement_detail_payload(db, agreement, actor, outcome)
        return json(payload, status=201)


@agreements_api_bp.delete("/<agreement_id:uuid>/consent")
@authenticated
async def withdraw_agreement_consent(request: Request, agreement_id: uuid.UUID):
    """Withdraw the caller's personal consent and reverse its alignment credit."""
    try:
        withdrawal = AgreementConsentWithdrawalRequest(**(request.json or {}))
    except Exception as exc:
        raise ApiError(400, f"Invalid request: {exc}") from None

    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, options=_detail_options(), label="Agreement",
            ecosystem_ids=await _consent_gate_scope(db, request),
        )
        actor = await _locked_caller(db, request, agreement)
        if actor is None:
            raise ApiError(403, "Only an ecosystem member may withdraw agreement consent")
        consent = await db.scalar(select(AgreementMemberConsent).where(
            AgreementMemberConsent.agreement_id == agreement.id,
            AgreementMemberConsent.member_id == actor.id,
            AgreementMemberConsent.agreement_version == agreement.version,
            AgreementMemberConsent.withdrawn_at.is_(None),
        ).with_for_update())
        if consent is None:
            raise ApiError(404, "No current agreement consent to withdraw")

        current_delta = int(await db.scalar(
            select(func.coalesce(func.sum(MemberAlignmentEvent.delta), 0)).where(
                MemberAlignmentEvent.agreement_consent_id == consent.id
            )
        ) or 0)
        now = _utcnow()
        consent.revision += 1
        consent.withdrawn_at = now
        consent.withdrawal_reason = withdrawal.reason
        if current_delta:
            db.add(MemberAlignmentEvent(
                id=uuid.uuid4(), member_id=actor.id, ecosystem_id=agreement.ecosystem_id,
                agreement_consent_id=consent.id, event_kind=f"state:{consent.revision}",
                delta=-current_delta, recorded_at=now,
            ))
            actor.agreement_alignment_score = max(0, actor.agreement_alignment_score - current_delta)
        actor.last_governance_activity_date = now.date()
        pending = await missing_agreement_consents(
            db, actor.id, agreement.ecosystem_id, "ecosystem"
        )
        if pending:  # G-Onboard: withdrawing a membership consent demotes (owner default), recorded as one transition
            from neos_agent.services.member_lifecycle import CONSENT_WITHDRAWN, record_transition
            record_transition(db, actor, "pending_consent", trigger=CONSENT_WITHDRAWN,
                              notes=f"Withdrew consent to {agreement.title}")
        await db.commit()
        await db.refresh(agreement)
        return json(await _agreement_detail_payload(db, agreement, actor))


@agreements_api_bp.get("/<agreement_id:uuid>/history")
@authenticated
async def get_history(request: Request, agreement_id: uuid.UUID):
    """GET /api/v1/agreements/:id/history -- amendment and review history.

    Returns JSON: AgreementHistoryResponse
    """
    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, label="Agreement",
            ecosystem_ids=await _consent_gate_scope(db, request),
        )
        can_rollback = _review_fields(agreement, await caller_in(db, request, agreement.ecosystem_id))["caller_can_rollback"]

        amend_result = await db.execute(
            select(AmendmentRecord)
            .where(AmendmentRecord.parent_agreement_id == agreement_id)
            .order_by(AmendmentRecord.date.desc())
        )
        amendments = amend_result.scalars().all()

        review_result = await db.execute(
            select(ReviewRecord)
            .where(ReviewRecord.agreement_id == agreement_id)
            .order_by(ReviewRecord.date.desc())
        )
        reviews = review_result.scalars().all()

        # Versions (capped at 50 most recent)
        version_result = await db.execute(
            select(AgreementVersion)
            .where(AgreementVersion.agreement_id == agreement_id)
            .order_by(AgreementVersion.created_at.desc())
            .limit(50)
        )
        versions = version_result.scalars().all()

    response = AgreementHistoryResponse(
        amendments=[
            AmendmentRecordSchema(
                id=a.id,
                amendment_id=a.amendment_id,
                amendment_type=a.amendment_type,
                proposed_by=a.proposed_by,
                date=a.date,
                changes=a.changes,
                rationale=a.rationale,
                status=a.status,
                new_agreement_version=a.new_agreement_version,
                created_at=a.created_at,
            )
            for a in amendments
        ],
        reviews=[
            ReviewRecordSchema(
                id=r.id,
                review_id=r.review_id,
                review_type=r.review_type,
                trigger=r.trigger,
                date=r.date,
                outcome=r.outcome,
                next_review_date=r.next_review_date,
                created_at=r.created_at,
                agreement_version=r.agreement_version,
                findings=(r.evaluation or {}).get("findings") if isinstance(r.evaluation, dict) else None,
                conducted_by=(r.review_body or {}).get("conducted_by") if isinstance(r.review_body, dict) else None,
                on_time=(r.evaluation or {}).get("on_time") if isinstance(r.evaluation, dict) else None,
            )
            for r in reviews
        ],
        versions=[
            AgreementVersionSchema(
                id=v.id,
                agreement_id=v.agreement_id,
                version=v.version,
                status=v.status,
                title=v.title,
                text=v.text,
                type=v.type,
                proposer=v.proposer,
                domain=v.domain,
                hierarchy_level=v.hierarchy_level,
                affected_parties=v.affected_parties,
                review_date=v.review_date,
                sunset_date=v.sunset_date,
                ratification_date=v.ratification_date,
                version_fingerprint=v.version_fingerprint,
                change_reason=v.change_reason,
                changed_by=v.changed_by,
                created_at=v.created_at,
            )
            for v in versions
        ],
    )

    return json({**response.model_dump(mode="json"), "caller_can_rollback": can_rollback})


@agreements_api_bp.post("/<agreement_id:uuid>/rollback/<version_id:uuid>")
@authenticated
async def rollback_agreement(request: Request, agreement_id: uuid.UUID, version_id: uuid.UUID):
    """POST /api/v1/agreements/:id/rollback/:version_id -- restore an earlier draft's terms.

    Only where editing is allowed (draft or advice, by an active member there); an agreement in
    force changes through a proposal, so anything else is 409 ROLLBACK_LOCKED. Restores the terms,
    never the status, review date or sunset date; the version moves forward only when title or text changes.
    Returns JSON: AgreementDetail
    """
    async with request.app.ctx.db() as db:
        agreement = await get_scoped_or_404(
            db, request, Agreement, agreement_id, options=_detail_options(), label="Agreement",
        )
        actor = await caller_in(db, request, agreement.ecosystem_id)
        if not is_active_member_in(actor, agreement.ecosystem_id):
            raise ApiError(403, "Only an active ecosystem member may roll back an agreement draft")
        if agreement.status not in EDITABLE_STATUSES:
            message = ROLLBACK_IN_FORCE if agreement.status in IN_FORCE_STATUSES else ROLLBACK_LOCKED
            raise ApiError(409, message, {"code": "ROLLBACK_LOCKED"})

        target_version = (await db.execute(
            select(AgreementVersion).where(
                AgreementVersion.id == version_id,
                AgreementVersion.agreement_id == agreement_id,
            )
        )).scalar_one_or_none()
        if target_version is None:
            raise ApiError(404, "Version not found")

        db.add(_snapshot_agreement(
            agreement,
            change_reason=f"Rollback to version {target_version.version}",
            changed_by=actor.display_name,
        ))

        text_changed = any(getattr(target_version, field) != getattr(agreement, field) for field in VERSIONED_FIELDS)
        for field in ROLLBACK_FIELDS:
            setattr(agreement, field, getattr(target_version, field))
        if text_changed:
            _bump_version(agreement)
        _regenerate_fingerprint(agreement)
        await synchronize_agreement_requirements(db, agreement)

        await db.commit()

        logger.info("Agreement %s rolled back to version %s by %s", agreement_id, target_version.version, actor.display_name)

        agreement = await _reload_for_detail(db, agreement.id)
        return json(await _agreement_detail_payload(db, agreement, actor))
