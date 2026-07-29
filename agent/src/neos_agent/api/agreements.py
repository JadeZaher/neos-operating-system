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
    ReviewRecord,
)

from .agreement_vocabulary import (
    AGREEMENT_STATUSES,
    AGREEMENT_TYPES,
    canonical_agreement_status,
    canonical_agreement_type,
)
from .helpers import require_auth, get_ecosystem_ids, get_authorized_ecosystem_ids, apply_ecosystem_filter, apply_ecosystem_name_filter, build_search_filter, serialize_shared_ecosystem_ids
from neos_agent.services.agreement_consent import (
    agreement_consent_summary,
    missing_agreement_consents,
    synchronize_agreement_requirements,
)
from neos_agent.services.act_gates import (
    agreement_gate_status,
    maybe_auto_advance_agreement,
    normalize_act_policy,
    record_agreement_commitment,
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


def _apply_filters(stmt, request: Request, eco_ids: list[uuid.UUID] | None = None):
    """Apply optional query-param filters to an Agreement select statement."""
    if eco_ids:
        stmt = apply_ecosystem_filter(stmt, Agreement, eco_ids)

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
    ).model_dump(mode="json")


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


async def _agreement_detail_payload(db, agreement: Agreement, user_id: uuid.UUID | None) -> dict:
    """Add consent progress and the authenticated member's attestation to detail."""
    payload = _agreement_to_detail(agreement)
    summary = await agreement_consent_summary(db, agreement)
    payload["consent_summary"] = AgreementConsentSummary(**summary).model_dump(mode="json")
    payload["gates"] = await agreement_gate_status(db, agreement)
    if user_id is None:
        return payload

    member = await db.scalar(select(Member).where(
        Member.user_id == user_id,
        Member.ecosystem_id == agreement.ecosystem_id,
    ))
    if member is None:
        payload["caller_role"] = None
        payload["caller_can_conduct"] = False
        return payload
    payload["caller_role"] = member.role
    payload["caller_can_conduct"] = (
        member.current_status == "active" and member.role in {"admin", "owner"}
    )
    consent = await db.scalar(select(AgreementMemberConsent).where(
        AgreementMemberConsent.agreement_id == agreement.id,
        AgreementMemberConsent.member_id == member.id,
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


# Valid status transitions: current -> allowed targets (ACT lifecycle)
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"advice"},
    "advice": {"consent"},
    "consent": {"test"},
    "test": {"active"},
    "active": {"under_review"},
    "under_review": {"sunset", "active"},
    "sunset": {"archived"},
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@agreements_api_bp.get("/vocabulary")
async def agreement_vocabulary(request: Request):
    """GET /api/v1/agreements/vocabulary -- canonical filter and form values."""
    _member, err = require_auth(request)
    if err:
        return err
    return json({
        "types": sorted(AGREEMENT_TYPES),
        "statuses": sorted(AGREEMENT_STATUSES),
    })


@agreements_api_bp.get("/")
async def list_agreements(request: Request):
    """GET /api/v1/agreements -- paginated list with filters.

    Query params: type, status, domain, q, page (default 1), per_page (default 25, max 100).
    Returns JSON: {"items": [...], "total": N, "page": P, "per_page": PP}
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as db:
        stmt = select(Agreement).order_by(Agreement.created_at.desc())
        try:
            stmt = _apply_filters(stmt, request, eco_ids=eco_ids)
        except ValueError as exc:
            return json({"error": str(exc)}, status=400)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await db.execute(stmt)
        agreements = result.scalars().all()

    return json({
        "items": [_agreement_to_list_item(a) for a in agreements],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@agreements_api_bp.get("/<agreement_id:uuid>")
async def get_agreement(request: Request, agreement_id: uuid.UUID):
    """GET /api/v1/agreements/:id -- detail with ratification records.

    Verifies ecosystem ownership.
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_authorized_ecosystem_ids(request)

    async with request.app.ctx.db() as db:
        if not eco_ids:
            eco_ids = list((await db.execute(select(Member.ecosystem_id).where(
                Member.user_id == member.user_id,
                Member.current_status.in_({"active", "pending_consent"}),
            ))).scalars().all())
        if not eco_ids:
            return json({"error": "Access denied"}, status=403)
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        return json(await _agreement_detail_payload(db, agreement, getattr(member, "user_id", None)))


@agreements_api_bp.post("/")
async def create_agreement(request: Request):
    """POST /api/v1/agreements -- create a new agreement.

    Accepts JSON: AgreementCreateRequest
    Returns JSON: AgreementDetail with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = AgreementCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    # Verify the ecosystem_id is in the member's scope
    eco_ids = get_authorized_ecosystem_ids(request)
    if create_req.ecosystem_id not in eco_ids:
        return json({"error": "Access denied: ecosystem not in scope"}, status=403)

    short_id = uuid.uuid4().hex[:8].upper()
    agreement_id_str = f"AGR-{short_id}"

    async with request.app.ctx.db() as db:
        domain_error = await _validate_prerequisite_domains(
            db, create_req.ecosystem_id, create_req.prerequisite_domain_ids
        )
        if domain_error:
            return json({"error": domain_error}, status=400)
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
            review_date=create_req.review_date,
            sunset_date=create_req.sunset_date,
            created_date=_dt.date.today(),
            requires_explicit_consent=create_req.requires_explicit_consent,
            prerequisite_scopes=create_req.prerequisite_scopes,
            prerequisite_domain_ids=[str(domain_id) for domain_id in create_req.prerequisite_domain_ids],
            alignment_points=create_req.alignment_points,
            act_policy=normalize_act_policy(
                create_req.act_policy.model_dump() if create_req.act_policy else None
            ),
        )
        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )
        db.add(agreement)
        await db.flush()
        await synchronize_agreement_requirements(db, agreement)
        await db.commit()

        # Reload with ratification records for response
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

        return json(await _agreement_detail_payload(db, agreement, getattr(member, "user_id", None)), status=201)


@agreements_api_bp.put("/<agreement_id:uuid>")
async def update_agreement(request: Request, agreement_id: uuid.UUID):
    """PUT /api/v1/agreements/:id -- update an agreement.

    Accepts JSON: AgreementUpdateRequest (only non-None fields are applied).
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = AgreementUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    eco_ids = get_authorized_ecosystem_ids(request)
    if not eco_ids:
        return json({"error": "Access denied"}, status=403)

    async with request.app.ctx.db() as db:
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        actor = await db.scalar(select(Member).where(
            Member.user_id == member.user_id,
            Member.ecosystem_id == agreement.ecosystem_id,
            Member.current_status == "active",
        ))
        if actor is None:
            return json({"error": "Only an active ecosystem member may edit an agreement"}, status=403)

        if agreement.status not in {"draft", "advice"}:
            return json(
                {"error": "Only draft or advice agreements can be edited; reopen governance before changing agreement terms."},
                status=409,
            )

        if update_req.prerequisite_domain_ids is not None:
            domain_error = await _validate_prerequisite_domains(
                db, agreement.ecosystem_id, update_req.prerequisite_domain_ids
            )
            if domain_error:
                return json({"error": domain_error}, status=400)

        # Save snapshot of current state before applying changes
        change_reason = body.get("change_reason", "Manual edit")
        snapshot = _snapshot_agreement(agreement, change_reason=change_reason, changed_by=member.display_name)
        db.add(snapshot)

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
        for field, value in update_data.items():
            setattr(agreement, field, value)

        # Bump version
        _bump_version(agreement)
        await synchronize_agreement_requirements(db, agreement)

        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )

        await db.commit()
        await db.refresh(agreement)

        # Re-load with ratification records
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

        return json(await _agreement_detail_payload(db, agreement, getattr(member, "user_id", None)))


@agreements_api_bp.post("/<agreement_id:uuid>/status")
async def status_transition(request: Request, agreement_id: uuid.UUID):
    """POST /api/v1/agreements/:id/status -- transition agreement status.

    Each transition is recorded as a governance ceremony. Advice, consent, and
    test are mandatory before activation; activation also needs test evidence.
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    new_status = body.get("status")
    if not new_status:
        return json({"error": "\"status\" field is required"}, status=400)
    try:
        new_status = canonical_agreement_status(new_status)
    except ValueError as exc:
        return json({"error": str(exc)}, status=400)

    eco_ids = get_authorized_ecosystem_ids(request)
    if not eco_ids:
        return json({"error": "Access denied"}, status=403)

    async with request.app.ctx.db() as db:
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        actor = await db.scalar(select(Member).where(
            Member.user_id == member.user_id,
            Member.ecosystem_id == agreement.ecosystem_id,
        ).with_for_update())
        if actor is None or actor.current_status != "active" or actor.role not in {"admin", "owner"}:
            return json({"error": "Only an active ecosystem steward (admin or owner) may conduct this ceremony"}, status=403)

        allowed = _VALID_TRANSITIONS.get(agreement.status, set())
        if new_status not in allowed:
            return json(
                {"error": f"Invalid transition: {agreement.status} -> {new_status}"},
                status=400,
            )

        ceremony_evidence = (body.get("evidence") or "").strip()
        if new_status in {"advice", "consent", "test", "active"} and len(ceremony_evidence) < 8:
            return json({"error": f"Documented evidence is required for the {new_status} ceremony"}, status=400)

        # ACT gates: forward moves require the conditions declared at the
        # agreement level. draft->advice opens the process and has no gate.
        gate_key = {"consent": "advice", "test": "consent", "active": "test"}.get(new_status)
        if gate_key:
            gates = await agreement_gate_status(db, agreement)
            if not gates[gate_key]["met"]:
                return json(
                    {
                        "error": f"The {gate_key} gate is not satisfied — the conditions declared in the agreement's ACT policy must be met first",
                        "gates": gates,
                    },
                    status=409,
                )
        # Snapshot before status change
        snapshot = _snapshot_agreement(
            agreement,
            change_reason=f"Status transition: {agreement.status} -> {new_status}",
            changed_by=actor.display_name,
        )
        db.add(snapshot)

        old_status = agreement.status
        agreement.status = new_status
        if new_status == "active" and agreement.ratification_date is None:
            agreement.ratification_date = _dt.date.today()

        db.add(AgreementCeremony(
            id=uuid.uuid4(),
            agreement_id=agreement.id,
            stage=new_status,
            completed_by_member_id=actor.id,
            outcome={"advice": "opened", "consent": "opened", "test": "started", "active": "passed"}.get(new_status, "completed"),
            evidence=ceremony_evidence or None,
            completed_at=_utcnow(),
        ))

        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )

        # Activation produces the agreement's commitment decision artifact.
        if new_status == "active":
            await record_agreement_commitment(db, agreement)

        # Cascade through any further gates now satisfied, recording each
        # automatic transition as a system ceremony.
        advance = await maybe_auto_advance_agreement(db, agreement, actor_member_id=actor.id)
        if advance["transitions"]:
            db.add(_snapshot_agreement(
                agreement,
                change_reason="Auto-advanced by ACT gate engine: " + ", ".join(advance["transitions"]),
                changed_by="ACT gate engine",
            ))
            agreement.version_fingerprint = generate_fingerprint(
                agreement.title, agreement.text, agreement.version, agreement.status
            )

        await db.commit()
        await db.refresh(agreement)

        logger.info(
            "Agreement %s status: %s -> %s",
            agreement_id, old_status, new_status,
        )

        # Re-load with ratification records
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

        payload = await _agreement_detail_payload(db, agreement, getattr(member, "user_id", None))
        payload["auto_transitions"] = advance["transitions"]
        if advance["decision_record_id"]:
            payload["decision_record_id"] = advance["decision_record_id"]
        return json(payload)


@agreements_api_bp.post("/<agreement_id:uuid>/ceremonies")
async def record_ceremony_evidence(request: Request, agreement_id: uuid.UUID):
    """POST /api/v1/agreements/:id/ceremonies -- record an advice round or test evidence.

    Advice rounds (stage "advice", outcome "round") and test-case evidence
    (stage "test", outcome "evidence") are the measurable units of the ACT
    gates declared at the agreement level. When a recording completes the
    declared conditions the status advances automatically.
    Accepts JSON: {"stage": "advice"|"test", "note": "..."}
    Returns JSON: AgreementDetail with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err
    try:
        evidence_request = AgreementCeremonyEvidenceRequest(**(request.json or {}))
    except Exception as exc:
        return json({"error": f"Invalid request: {exc}"}, status=400)

    eco_ids = get_authorized_ecosystem_ids(request)
    if not eco_ids:
        return json({"error": "Access denied"}, status=403)

    async with request.app.ctx.db() as db:
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))
        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()
        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        actor = await db.scalar(select(Member).where(
            Member.user_id == member.user_id,
            Member.ecosystem_id == agreement.ecosystem_id,
            Member.current_status == "active",
        ))
        if actor is None:
            return json({"error": "Only an active ecosystem member may record ceremony evidence"}, status=403)

        stage = evidence_request.stage
        if agreement.status != stage:
            return json(
                {"error": f"Evidence for the {stage} stage can only be recorded while the agreement is in {stage} (current: {agreement.status})"},
                status=409,
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

        # ACT gate engine: advance automatically when the declared
        # conditions are now met.
        advance = await maybe_auto_advance_agreement(db, agreement, actor_member_id=actor.id)
        if advance["transitions"]:
            db.add(_snapshot_agreement(
                agreement,
                change_reason="Auto-advanced by ACT gate engine: " + ", ".join(advance["transitions"]),
                changed_by="ACT gate engine",
            ))
            agreement.version_fingerprint = generate_fingerprint(
                agreement.title, agreement.text, agreement.version, agreement.status
            )
        await db.commit()

        # Re-load with ceremonies
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

        payload = await _agreement_detail_payload(db, agreement, getattr(member, "user_id", None))
        payload["auto_transitions"] = advance["transitions"]
        if advance["decision_record_id"]:
            payload["decision_record_id"] = advance["decision_record_id"]
        return json(payload, status=201)


@agreements_api_bp.post("/<agreement_id:uuid>/consent")
async def attest_agreement_consent(request: Request, agreement_id: uuid.UUID):
    """Record the caller's explicit acceptance of the current agreement version."""
    member, err = require_auth(request)
    if err:
        return err
    try:
        consent_request = AgreementConsentRequest(**(request.json or {}))
    except Exception as exc:
        return json({"error": f"Invalid request: {exc}"}, status=400)

    async with request.app.ctx.db() as db:
        agreement = await db.scalar(
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement_id)
        )
        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)
        if agreement.status not in {"consent", "test", "active", "under_review"}:
            return json({"error": "Agreement consent opens during the consent ceremony"}, status=409)

        actor = await db.scalar(select(Member).where(
            Member.user_id == member.user_id,
            Member.ecosystem_id == agreement.ecosystem_id,
        ).with_for_update())
        if actor is None:
            return json({"error": "Only an ecosystem member may attest agreement consent"}, status=403)

        consent = await db.scalar(select(AgreementMemberConsent).where(
            AgreementMemberConsent.agreement_id == agreement.id,
            AgreementMemberConsent.member_id == actor.id,
            AgreementMemberConsent.agreement_version == agreement.version,
        ).with_for_update())
        now = _utcnow()
        if consent is None:
            consent = AgreementMemberConsent(
                id=uuid.uuid4(), agreement_id=agreement.id, member_id=actor.id,
                agreement_version=agreement.version, attestation=consent_request.attestation,
                attested_at=now,
            )
            db.add(consent)
            await db.flush()
        else:
            consent.attestation = consent_request.attestation
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
            if not pending:
                actor.current_status = "active"
                actor.onboarding_status = "complete"

        # ACT gate engine: a completed consent ceremony advances the
        # agreement automatically (and mints the commitment artifact if the
        # test gate is already satisfied).
        advance = await maybe_auto_advance_agreement(db, agreement, actor_member_id=actor.id)
        if advance["transitions"]:
            db.add(_snapshot_agreement(
                agreement,
                change_reason="Auto-advanced by ACT gate engine: " + ", ".join(advance["transitions"]),
                changed_by="ACT gate engine",
            ))
            agreement.version_fingerprint = generate_fingerprint(
                agreement.title, agreement.text, agreement.version, agreement.status
            )
        await db.commit()
        await db.refresh(agreement)

        payload = await _agreement_detail_payload(db, agreement, member.user_id)
        payload["auto_transitions"] = advance["transitions"]
        if advance["decision_record_id"]:
            payload["decision_record_id"] = advance["decision_record_id"]
        return json(payload, status=201)


@agreements_api_bp.delete("/<agreement_id:uuid>/consent")
async def withdraw_agreement_consent(request: Request, agreement_id: uuid.UUID):
    """Withdraw the caller's personal consent and reverse its alignment credit."""
    member, err = require_auth(request)
    if err:
        return err
    try:
        withdrawal = AgreementConsentWithdrawalRequest(**(request.json or {}))
    except Exception as exc:
        return json({"error": f"Invalid request: {exc}"}, status=400)

    async with request.app.ctx.db() as db:
        agreement = await db.scalar(
            select(Agreement)
            .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ceremonies))
            .where(Agreement.id == agreement_id)
        )
        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)
        actor = await db.scalar(select(Member).where(
            Member.user_id == member.user_id,
            Member.ecosystem_id == agreement.ecosystem_id,
        ).with_for_update())
        if actor is None:
            return json({"error": "Only an ecosystem member may withdraw agreement consent"}, status=403)
        consent = await db.scalar(select(AgreementMemberConsent).where(
            AgreementMemberConsent.agreement_id == agreement.id,
            AgreementMemberConsent.member_id == actor.id,
            AgreementMemberConsent.agreement_version == agreement.version,
            AgreementMemberConsent.withdrawn_at.is_(None),
        ).with_for_update())
        if consent is None:
            return json({"error": "No current agreement consent to withdraw"}, status=404)

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
        if pending:
            actor.current_status = "pending_consent"
            actor.onboarding_status = "agreement_consent_required"
        await db.commit()
        await db.refresh(agreement)
        return json(await _agreement_detail_payload(db, agreement, member.user_id))


@agreements_api_bp.get("/<agreement_id:uuid>/history")
async def get_history(request: Request, agreement_id: uuid.UUID):
    """GET /api/v1/agreements/:id/history -- amendment and review history.

    Returns JSON: AgreementHistoryResponse
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_authorized_ecosystem_ids(request)
    if not eco_ids:
        return json({"error": "Access denied"}, status=403)

    async with request.app.ctx.db() as db:
        # Verify agreement exists and is in scope
        agr_stmt = select(Agreement.id).where(Agreement.id == agreement_id)
        if eco_ids:
            agr_stmt = agr_stmt.where(Agreement.ecosystem_id.in_(eco_ids))
        exists = await db.scalar(agr_stmt)
        if exists is None:
            return json({"error": "Agreement not found"}, status=404)

        # Load amendments
        amend_result = await db.execute(
            select(AmendmentRecord)
            .where(AmendmentRecord.parent_agreement_id == agreement_id)
            .order_by(AmendmentRecord.date.desc())
        )
        amendments = amend_result.scalars().all()

        # Load reviews
        review_result = await db.execute(
            select(ReviewRecord)
            .where(ReviewRecord.agreement_id == agreement_id)
            .order_by(ReviewRecord.date.desc())
        )
        reviews = review_result.scalars().all()

        # Load versions (capped at 50 most recent)
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

    return json(response.model_dump(mode="json"))


@agreements_api_bp.post("/<agreement_id:uuid>/rollback/<version_id:uuid>")
async def rollback_agreement(request: Request, agreement_id: uuid.UUID, version_id: uuid.UUID):
    """POST /api/v1/agreements/:id/rollback/:version_id -- restore agreement to a previous version.

    Requires the member to be the agreement proposer or have 'active'/'steward' status.
    Status rollback is restricted: cannot rollback to a status that isn't reachable
    from the current status (or the same status). Content fields are always restored.

    Creates a snapshot of the current state, then restores from the specified version.
    Returns JSON: AgreementDetail
    """
    member, err = require_auth(request)
    if err:
        return err

    # Permission check: only proposers or steward/active members can rollback
    member_status = getattr(member, "current_status", None)
    if member_status not in ("active", "steward", "co_creator"):
        return json({"error": "Insufficient permissions: rollback requires active/steward/co_creator status"}, status=403)

    eco_ids = get_authorized_ecosystem_ids(request)
    if not eco_ids:
        return json({"error": "Access denied"}, status=403)

    async with request.app.ctx.db() as db:
        # Load current agreement
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement_id)
        )
        if eco_ids:
            stmt = stmt.where(Agreement.ecosystem_id.in_(eco_ids))

        result = await db.execute(stmt)
        agreement = result.scalar_one_or_none()

        if agreement is None:
            return json({"error": "Agreement not found"}, status=404)

        # Load the target version
        ver_result = await db.execute(
            select(AgreementVersion).where(
                AgreementVersion.id == version_id,
                AgreementVersion.agreement_id == agreement_id,
            )
        )
        target_version = ver_result.scalar_one_or_none()

        if target_version is None:
            return json({"error": "Version not found"}, status=404)

        # Validate status rollback: only allow if same status or a valid transition
        if target_version.status != agreement.status:
            allowed = _VALID_TRANSITIONS.get(agreement.status, set())
            if target_version.status not in allowed:
                return json(
                    {"error": f"Cannot rollback to status '{target_version.status}' from current '{agreement.status}'. Invalid transition."},
                    status=400,
                )

        # Snapshot current state before rollback
        snapshot = _snapshot_agreement(
            agreement,
            change_reason=f"Rollback to version {target_version.version}",
            changed_by=member.display_name,
        )
        db.add(snapshot)

        # Restore fields from target version
        agreement.status = target_version.status
        agreement.title = target_version.title
        agreement.text = target_version.text
        agreement.type = target_version.type
        agreement.proposer = target_version.proposer
        agreement.domain = target_version.domain
        agreement.hierarchy_level = target_version.hierarchy_level
        agreement.affected_parties = target_version.affected_parties
        agreement.review_date = target_version.review_date
        agreement.sunset_date = target_version.sunset_date
        agreement.ratification_date = target_version.ratification_date
        agreement.requires_explicit_consent = target_version.requires_explicit_consent
        agreement.prerequisite_scopes = target_version.prerequisite_scopes
        agreement.prerequisite_domain_ids = target_version.prerequisite_domain_ids
        agreement.alignment_points = target_version.alignment_points

        # Bump version (don't restore old version number — always move forward)
        _bump_version(agreement)

        # Regenerate fingerprint for the restored state
        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )
        await synchronize_agreement_requirements(db, agreement)

        await db.commit()
        await db.refresh(agreement)

        logger.info("Agreement %s rolled back to version %s by %s", agreement_id, target_version.version, member.display_name)

        # Re-load with ratification records
        stmt = (
            select(Agreement)
            .options(selectinload(Agreement.ratification_records))
            .where(Agreement.id == agreement.id)
        )
        result = await db.execute(stmt)
        agreement = result.scalar_one()

    return json(_agreement_to_detail(agreement))
