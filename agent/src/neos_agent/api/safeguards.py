"""JSON API blueprint for governance safeguards & health monitoring.

Blueprint: safeguards_api_bp, url_prefix="/api/v1/safeguards"

Governance health audits: a member starts a draft, fills in the indicators, and
publishes it; the score comes from published audits only. AI analysis is optional
and never blocks. See api/AGENTS.md "Audits".
"""

from __future__ import annotations

import logging
import re
import uuid
import datetime as _dt
from typing import Optional

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import DecisionRecord, Ecosystem, GovernanceHealthAudit, Member, Proposal
from neos_agent.api import policy
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import require_auth, get_ecosystem_ids, get_authorized_ecosystem_ids, apply_ecosystem_filter, apply_ecosystem_name_filter, build_search_filter, parse_pagination
from neos_agent.api.schemas.safeguards import AuditCreateRequest, AuditDetail, AuditListItem, AuditUpdateRequest, HealthSummary
from neos_agent.api.schemas.safeguards import AuditAbandonRequest, AuditRespondRequest  # FX-Maint
from neos_agent.services import dates, health

logger = logging.getLogger(__name__)

# Published-audit rules: an indicator's status is worth these points; the score is their mean.
INDICATOR_STATUS_POINTS = {"healthy": 100, "warning": 50, "critical": 0}
AUDIT_PUBLISHED = "completed"
AUDIT_DRAFT = "draft"
NEXT_AUDIT_AFTER_DAYS = 90
AUDIT_FINISH_DENIED = "Only the member who is recording this audit can edit or publish it"
# G-Maint: owner decision 2026-11-01 (policy.AUDIT_EXCLUDES_STEWARDS); api/AGENTS.md "Maintenance and health (G-Maint)".
AUDITOR_NOT_INDEPENDENT = ("A steward of this ecosystem cannot audit it while a member who is not a steward can: "
                           "ask one of them to record it.")
AUDIT_MEMBERS_ONLY = "Only active members of this ecosystem can record an audit"


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

safeguards_api_bp = Blueprint("safeguards_api", url_prefix="/api/v1/safeguards")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _health_score_to_label(score: int | None) -> str | None:
    """Map numeric health score to string enum."""
    if score is None:
        return None
    if score >= 80:
        return "healthy"
    if score >= 50:
        return "mixed"
    if score >= 25:
        return "degrading"
    return "critical"


def _published_score(a: GovernanceHealthAudit) -> int | None:
    """A score exists only once its auditor publishes; a draft never shows one (D14)."""
    return a.overall_health_score if a.status == AUDIT_PUBLISHED else None


def _published_label(a: GovernanceHealthAudit) -> str | None:
    if a.status != AUDIT_PUBLISHED:
        return None
    return getattr(a, 'overall_health', None) or _health_score_to_label(a.overall_health_score)


def _published_on(a: GovernanceHealthAudit) -> _dt.date | None:
    """The publish date (publish sets `audit_date`); never `updated_at`, which a later write moves."""
    return a.audit_date if a.status == AUDIT_PUBLISHED else None


async def _ecosystem_name(session, ecosystem_id) -> str | None:
    return await session.scalar(select(Ecosystem.name).where(Ecosystem.id == ecosystem_id))


def _audit_to_list_item(a: GovernanceHealthAudit) -> dict:
    return AuditListItem(
        id=a.id,
        audit_id=a.audit_id,
        ecosystem_id=a.ecosystem_id,
        audit_date=a.audit_date,
        auditor=a.auditor,
        overall_health_score=_published_score(a),
        status=a.status,
        created_at=a.created_at,
        completed_at=_published_on(a),
        overall_health=_published_label(a),
        audit_scope=getattr(a, 'audit_scope', None),
        trigger_type=getattr(a, 'trigger_type', None),
        self_assessment=bool(getattr(a, 'self_assessment', False)),
    ).model_dump(mode="json")


def _scores_to_list(value) -> list | None:
    """Legacy JSON may store dict keyed by id; coerce to a list of dicts."""
    if value is None:
        return None
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)] or None
    if isinstance(value, dict):
        if isinstance(value.get("items"), list):
            return [v for v in value["items"] if isinstance(v, dict)] or None
        out = []
        for k, v in value.items():
            if isinstance(v, dict):
                v = dict(v)
                v.setdefault("indicator_id", k)
                out.append(v)
        return out or None
    return None


def _str_list(value) -> list | None:
    """Coerce stored JSON to a list of strings; drop anything else."""
    if value is None:
        return None
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)] or None
    if isinstance(value, dict):
        if isinstance(value.get("items"), list):
            return [v for v in value["items"] if isinstance(v, str)] or None
        return [v for v in value.values() if isinstance(v, str)] or None
    return None


def audit_score(indicator_scores: list[dict] | None) -> int | None:
    """Mean of the indicators' status points; None when no indicator has a known status."""
    points = [INDICATOR_STATUS_POINTS[s["status"]] for s in indicator_scores or [] if s.get("status") in INDICATOR_STATUS_POINTS]
    return round(sum(points) / len(points)) if points else None


def _audit_to_detail(a: GovernanceHealthAudit, caller: Member | None = None, ecosystem_name: str | None = None) -> dict:
    return AuditDetail(
        caller_can_edit=a.status == AUDIT_DRAFT and policy.can_finish_audit(caller, a),
        id=a.id,
        audit_id=a.audit_id,
        ecosystem_id=a.ecosystem_id,
        ecosystem_name=ecosystem_name,
        audit_date=a.audit_date,
        auditor=a.auditor,
        overall_health_score=_published_score(a),
        status=a.status,
        created_at=a.created_at,
        completed_at=_published_on(a),
        overall_health=_published_label(a),
        audit_scope=getattr(a, 'audit_scope', None),
        trigger_type=getattr(a, 'trigger_type', None),
        self_assessment=bool(getattr(a, 'self_assessment', False)),
        capture_risk_indicators=a.capture_risk_indicators,
        # Requested-but-pending audits store {} placeholders in text columns —
        # coerce to None so detail consumers never render a raw object.
        findings=a.findings if isinstance(a.findings, str) else None,
        recommendations=a.recommendations if isinstance(a.recommendations, str) else None,
        next_audit_due=getattr(a, 'next_audit_due', None) or a.next_audit_date,
        updated_at=a.updated_at,
        audit_period_start=getattr(a, 'audit_period_start', None),
        audit_period_end=getattr(a, 'audit_period_end', None),
        auditor_ids=getattr(a, 'auditor_ids', None),
        indicator_scores=_scores_to_list(getattr(a, 'indicator_scores', None)),
        triggered_safeguards=_scores_to_list(getattr(a, 'triggered_safeguards', None)),
        structured_recommendations=_str_list(getattr(a, 'structured_recommendations', None)),
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@safeguards_api_bp.get("/")
async def health_summary(request: Request):
    """GET /api/v1/safeguards -- per selected ecosystem: its latest published audit, when the next is due, who may record it.

    `ecosystems` is one labelled entry per ecosystem (D12: one score used to mix them). The single
    `latest_audit` / `health_score` fields are kept for one selected ecosystem only.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        base_stmt = select(GovernanceHealthAudit).order_by(
            GovernanceHealthAudit.audit_date.desc()
        )
        base_stmt = restrict_to_ecosystems(base_stmt, GovernanceHealthAudit, eco_ids)

        # Recent audits include drafts so an auditor can find and finish theirs; the score reads published ones only.
        recent_audits = (await session.execute(base_stmt.limit(10))).scalars().all()
        entries = await _ecosystem_health(session, request, eco_ids)

    single = entries[0] if len(entries) == 1 else None
    latest = single["latest_audit"] if single else None
    summary = HealthSummary(
        latest_audit=latest,
        recent_audits=[_audit_to_list_item(a) for a in recent_audits],
        health_score=latest["overall_health_score"] if latest else None,
        indicator_scores=latest["indicator_scores"] if latest else None,
        triggered_safeguards=latest["triggered_safeguards"] if latest else None,
        ecosystems=entries,
    )

    return json(summary.model_dump(mode="json"))


async def _ecosystem_health(session, request: Request, eco_ids: list) -> list[dict]:
    """One labelled entry per ecosystem: latest published audit, next audit due (and overdue), the audit rule for the caller."""
    names = dict((await session.execute(select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_(eco_ids or [])))).all())
    entries = []
    for eco_id in sorted(names, key=lambda key: names[key] or ""):
        latest = await health.latest_published_audit(session, eco_id)
        due = await health.audit_due_date(session, eco_id, latest)
        caller = await caller_in(session, request, eco_id)
        refusal = await auditor_refusal(session, caller, eco_id)
        can_record = refusal is None
        scores = _scores_to_list(latest.indicator_scores) if latest else None
        entries.append({
            "ecosystem_id": str(eco_id),
            "ecosystem": names[eco_id],
            "latest_audit": _audit_to_detail(latest, caller, names[eco_id]) if latest else None,
            "published_on": latest.audit_date.isoformat() if latest and latest.audit_date else None,
            "audit_due": due.isoformat() if due else None,
            "audit_overdue": dates.date_passed(due),
            "critical_count": sum(row.get("status") == "critical" for row in scores or []),
            "caller_can_record_audit": can_record,
            "caller_record_audit_refusal": refusal.message if refusal is not None else None,  # why there is no button
            "caller_records_self_assessment": can_record and policy.is_self_assessment(caller),
        })
    return entries


def _period_arg(request: Request, name: str):
    """An optional YYYY-MM-DD query argument; anything else is 400."""
    value = request.args.get(name)
    if not value:
        return None
    try:
        return _dt.date.fromisoformat(value)
    except ValueError:
        raise ApiError(400, f"'{name}' must be a date (YYYY-MM-DD)") from None


@safeguards_api_bp.get("/snapshot")
@authenticated
async def health_snapshot(request: Request):
    """GET /api/v1/safeguards/snapshot?ecosystem_id=&from=&to= -- computed indicator values and needs-attention counts.

    Read-only (services/health.py). Active members of that ecosystem only; anyone else gets 404.
    """
    selected = get_ecosystem_ids(request)
    raw_id = request.args.get("ecosystem_id") or (str(selected[0]) if len(selected) == 1 else None)
    try:
        ecosystem_id = uuid.UUID(str(raw_id))
    except (TypeError, ValueError):
        raise ApiError(400, "Choose an ecosystem (ecosystem_id)") from None
    start, end = _period_arg(request, "from"), _period_arg(request, "to")
    if start and end and start > end:
        raise ApiError(400, "'from' must be on or before 'to'")
    start, end = health.period_bounds(start, end)  # FX-Maint (F11): the rule publish freezes with
    async with request.app.ctx.db() as session:
        caller = await caller_in(session, request, ecosystem_id)
        if not policy.is_active_member_in(caller, ecosystem_id):
            raise ApiError(404, "Ecosystem not found")
        return json(await health.health_snapshot(session, ecosystem_id, start=start, end=end))


@safeguards_api_bp.get("/audits")
async def list_audits(request: Request):
    """GET /api/v1/safeguards/audits -- paginated audit list.

    Query params: status, overall_health, q, page (default 1), per_page (default 25, max 100).
    Lists audits across all selected ecosystems.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    page_args = parse_pagination(request)
    page, per_page, offset = page_args.page, page_args.per_page, page_args.offset

    async with request.app.ctx.db() as session:
        stmt = select(GovernanceHealthAudit).order_by(
            GovernanceHealthAudit.audit_date.desc()
        )
        stmt = restrict_to_ecosystems(stmt, GovernanceHealthAudit, eco_ids)
        stmt = apply_ecosystem_name_filter(stmt, GovernanceHealthAudit, request)

        status = request.args.get("status")
        if status:
            stmt = stmt.where(GovernanceHealthAudit.status == status)

        overall_health_param = request.args.get("overall_health")
        if overall_health_param:
            # Filter by computed overall_health from score
            health_ranges = {
                "healthy": (80, 999),
                "mixed": (50, 79),
                "degrading": (25, 49),
                "critical": (0, 24),
            }
            if overall_health_param in health_ranges:
                low, high = health_ranges[overall_health_param]
                stmt = stmt.where(
                    GovernanceHealthAudit.overall_health_score >= low,
                    GovernanceHealthAudit.overall_health_score <= high,
                )

        search = request.args.get("q")
        if search:
            stmt = stmt.where(build_search_filter(
                GovernanceHealthAudit, search,
                GovernanceHealthAudit.auditor, GovernanceHealthAudit.audit_id,
            ))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        audits = result.scalars().all()

    return json({
        "items": [_audit_to_list_item(a) for a in audits],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@safeguards_api_bp.get("/audits/<audit_id:uuid>")
async def get_audit(request: Request, audit_id: uuid.UUID):
    """GET /api/v1/safeguards/audits/:id -- audit detail.

    Audits are readable by any member of the ecosystem the audit is tied to,
    regardless of the current cookie selection — so this authorizes against
    the caller's full membership scope, not the UI focus selection.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_authorized_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(GovernanceHealthAudit).where(
            GovernanceHealthAudit.id == audit_id
        )
        stmt = restrict_to_ecosystems(stmt, GovernanceHealthAudit, eco_ids)

        result = await session.execute(stmt)
        audit = result.scalar_one_or_none()
        if audit is None:
            return json({"error": "Audit not found"}, status=404)
        caller = await caller_in(session, request, audit.ecosystem_id)
        return json(await audit_detail_payload(session, audit, caller))


async def _audit_to_edit(session, request: Request, audit_id: uuid.UUID) -> tuple[GovernanceHealthAudit, Member]:
    """A draft audit the caller is recording; 404 outside their ecosystems, 403 for anyone else, 409 once published."""
    audit = await get_scoped_or_404(session, request, GovernanceHealthAudit, audit_id, label="Audit")
    caller = await caller_in(session, request, audit.ecosystem_id)
    if not policy.can_finish_audit(caller, audit):
        raise ApiError(403, AUDIT_FINISH_DENIED)
    if audit.status != AUDIT_DRAFT:
        raise ApiError(409, "This audit is already published")
    return audit, caller


def _apply_audit_fields(audit: GovernanceHealthAudit, fields: dict) -> None:
    """Copy the sent fields onto a draft; indicator rows are stored as plain dicts."""
    for name, value in fields.items():
        if name == "indicator_scores":
            value = [row if isinstance(row, dict) else row.model_dump() for row in value]
        setattr(audit, name, value)


@safeguards_api_bp.post("/audits")
@authenticated
async def request_audit(request: Request):
    """POST /api/v1/safeguards/audits -- start a draft audit; the caller is the auditor.

    Accepts AuditCreateRequest (scope, period and any indicators already known).
    The draft stays out of the health score until its auditor publishes it.
    """
    try:
        create_req = AuditCreateRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        auditor = await caller_in(session, request, create_req.ecosystem_id)
        await require_auditor(session, auditor, create_req.ecosystem_id)

        audit = GovernanceHealthAudit(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
            audit_date=dates.utc_today(),
            auditor=auditor.display_name,
            auditor_ids=[str(auditor.id)],
            trigger_type="human",
            capture_risk_indicators={},
            status=AUDIT_DRAFT,
            self_assessment=policy.is_self_assessment(auditor),
        )
        _apply_audit_fields(audit, create_req.model_dump(exclude_none=True, exclude={"ecosystem_id"}))
        session.add(audit)
        await session.commit()
        await session.refresh(audit)
        return json(_audit_to_detail(audit, auditor, await _ecosystem_name(session, audit.ecosystem_id)), status=201)


@safeguards_api_bp.put("/audits/<audit_id:uuid>")
@authenticated
async def update_audit(request: Request, audit_id: uuid.UUID):
    """PUT /api/v1/safeguards/audits/:id -- edit a draft (its auditor only)."""
    try:
        update_req = AuditUpdateRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e

    async with request.app.ctx.db() as session:
        audit, caller = await _audit_to_edit(session, request, audit_id)
        _apply_audit_fields(audit, update_req.model_dump(exclude_none=True))
        await session.commit()
        await session.refresh(audit)
        return json(_audit_to_detail(audit, caller, await _ecosystem_name(session, audit.ecosystem_id)))


async def auditor_refusal(session, member: Member | None, ecosystem_id) -> ApiError | None:
    """Why `member` may not record an audit of `ecosystem_id` (policy.can_record_audit), else None."""
    independent = await health.has_independent_member(session, ecosystem_id)
    if policy.can_record_audit(member, ecosystem_id, has_independent_member=independent):
        return None
    if not policy.is_active_member_in(member, ecosystem_id):
        return ApiError(403, AUDIT_MEMBERS_ONLY)
    return ApiError(403, AUDITOR_NOT_INDEPENDENT, {"code": "AUDITOR_NOT_INDEPENDENT"})


async def require_auditor(session, member: Member | None, ecosystem_id) -> None:
    """Raise the auditor refusal, if any (REST start and publish; the assistant reads auditor_refusal)."""
    refusal = await auditor_refusal(session, member, ecosystem_id)
    if refusal is not None:
        raise refusal


@safeguards_api_bp.post("/audits/<audit_id:uuid>/publish")
@authenticated
async def publish_audit(request: Request, audit_id: uuid.UUID):
    """POST /api/v1/safeguards/audits/:id/publish -- freeze the computed values beside the ratings of the auditor.

    Every computable indicator with data in the audit period needs a rating (400 RATINGS_MISSING); the
    auditor rule is checked again. Values, prior values and trends are stored, so later data never changes
    a published report. The score is the mean of the ratings.
    """
    async with request.app.ctx.db() as session:
        audit, caller = await _audit_to_edit(session, request, audit_id)
        await require_auditor(session, caller, audit.ecosystem_id)
        now = dates.utc_now()
        start, end = health.period_bounds(audit.audit_period_start, audit.audit_period_end, now)  # FX-Maint (F11)
        if start > end:
            raise ApiError(400, "The audit period must start on or before its end")
        snapshot = await health.health_snapshot(session, audit.ecosystem_id, start=start, end=end, now=now)
        prior = await health.latest_published_audit(session, audit.ecosystem_id)
        rows, missing = health.frozen_indicators(
            snapshot, _scores_to_list(audit.indicator_scores), _scores_to_list(prior.indicator_scores) if prior else None,
        )
        if missing:
            names = ", ".join(f"{i} {health.INDICATOR_BY_ID[i].name}" for i in missing)
            raise ApiError(400, f"Rate every indicator that has data in the period before publishing. Still to rate: {names}.",
                           {"code": "RATINGS_MISSING", "missing": missing})
        score = audit_score(rows)
        if score is None:
            raise ApiError(400, "Rate at least one indicator (healthy, warning or critical) before publishing")
        audit.indicator_scores = rows
        audit.audit_period_start, audit.audit_period_end = start, end
        audit.overall_health_score = score
        audit.overall_health = _health_score_to_label(score)
        audit.self_assessment = policy.is_self_assessment(caller)
        audit.status = AUDIT_PUBLISHED
        audit.audit_date = dates.utc_today(now)
        audit.next_audit_due = audit.audit_date + _dt.timedelta(days=NEXT_AUDIT_AFTER_DAYS)
        await session.commit()
        await session.refresh(audit)
        return json(_audit_to_detail(audit, caller, await _ecosystem_name(session, audit.ecosystem_id)))


# ---------------------------------------------------------------------------
# FX-Maint: closing an audit's loop (wave-c F6, F7); api/AGENTS.md "Maintenance and health (G-Maint)" > "FX-Maint"
# ---------------------------------------------------------------------------

AUDIT_ABANDONED = health.AUDIT_ABANDONED
STEWARD_NOTE_MIN = 8
ABANDON_DENIED = "Only the audit's auditor or a steward of this ecosystem can abandon its draft"
ABANDON_REASON_REQUIRED = "Say why the draft is abandoned (at least 8 characters); it is recorded."
NOT_A_DRAFT = "Only a draft can be abandoned; this audit is {status}."
RESPOND_DENIED = "Only a steward of this ecosystem can record the response to its audit"
RESPONSE_REQUIRED = ("Write the stewards' response (at least 8 characters): what you will do about the indicators "
                     "the audit rated, or why no change is needed.")
NOT_PUBLISHED = "Only a published audit can be responded to."
ALREADY_RESPONDED = "The stewards' response to this audit is already recorded."
RESPONSE_PROPOSAL_INVALID = "The proposal must belong to this ecosystem."


def _steward_record(record) -> dict | None:
    """A response or abandonment DecisionRecord as the detail shows it."""
    if record is None:
        return None
    related = record.related_records if isinstance(record.related_records, dict) else {}
    return {"note": record.ratio_decidendi or "", "recorded_by": record.recorder,
            "date": record.date.isoformat() if record.date else None, "proposal": related.get("proposal")}


async def audit_detail_payload(session, audit: GovernanceHealthAudit, caller: Member | None) -> dict:
    """Detail plus what stewards recorded on it, and whether the caller may abandon it or respond to it."""
    payload = _audit_to_detail(audit, caller, await _ecosystem_name(session, audit.ecosystem_id))
    response = (await health.audit_record(session, audit.id, health.AUDIT_RESPONSE_SKILL)
                if audit.status == AUDIT_PUBLISHED else None)
    abandoned = (await health.audit_record(session, audit.id, health.AUDIT_ABANDON_SKILL)
                 if audit.status == AUDIT_ABANDONED else None)
    payload["response"] = _steward_record(response)
    payload["abandonment"] = _steward_record(abandoned)
    payload["caller_can_abandon"] = audit.status == AUDIT_DRAFT and policy.can_abandon_audit(caller, audit)
    payload["caller_can_respond"] = (audit.status == AUDIT_PUBLISHED and response is None
                                     and policy.can_respond_to_audit(caller, audit))
    return payload


async def _locked_status(session, audit: GovernanceHealthAudit) -> str:
    """Take the audit row FOR UPDATE (two stewards at once write one record) and read its committed status."""
    return await session.scalar(select(GovernanceHealthAudit.status)
                                .where(GovernanceHealthAudit.id == audit.id).with_for_update())


def _audit_decision(audit: GovernanceHealthAudit, caller: Member, *, skill: str, holding: str, note: str,
                    related: dict | None = None) -> DecisionRecord:
    """The smallest existing record of a steward's act on an audit (as domain authority changes: api/domains.py)."""
    return DecisionRecord(
        id=uuid.uuid4(), ecosystem_id=audit.ecosystem_id, record_id=f"DEC-AUD-{uuid.uuid4().hex[:8].upper()}",
        date=dates.utc_today(), holding=holding, ratio_decidendi=note,
        deliberation_summary=f"Recorded by {caller.display_name} on the governance health audit {audit.audit_id}.",
        source_skill=skill, source_layer=7, artifact_type="audit", artifact_reference=str(audit.id),
        related_records=related, precedent_level="ecosystem", status="active", recorder=caller.display_name,
        recorder_role="auditor" if policy.can_finish_audit(caller, audit) else "ecosystem steward",
    )


async def abandon_audit_draft(session, audit: GovernanceHealthAudit, caller: Member | None, reason: str | None) -> None:
    """Mark a draft abandoned with a recorded reason (its auditor or a steward); the caller commits."""
    if not policy.can_abandon_audit(caller, audit):
        raise ApiError(403, ABANDON_DENIED)
    reason = (reason or "").strip()
    if len(reason) < STEWARD_NOTE_MIN:
        raise ApiError(400, ABANDON_REASON_REQUIRED, {"code": "REASON_REQUIRED", "field": "reason"})
    status = await _locked_status(session, audit)
    if status != AUDIT_DRAFT:
        raise ApiError(409, NOT_A_DRAFT.format(status=status), {"code": "NOT_A_DRAFT", "status": status})
    audit.status = AUDIT_ABANDONED
    session.add(_audit_decision(audit, caller, skill=health.AUDIT_ABANDON_SKILL, note=reason,
                                holding=f"The draft governance health audit {audit.audit_id} by "
                                        f"{audit.auditor or 'its auditor'} was abandoned."))


async def record_audit_response(session, audit: GovernanceHealthAudit, caller: Member | None, note: str | None,
                                proposal_id: uuid.UUID | None = None) -> DecisionRecord:
    """Record the stewards' response to a published audit, optionally naming a proposal; it clears respond_to_audit.
    Shared by REST and the assistant; the caller commits."""
    if not policy.can_respond_to_audit(caller, audit):
        raise ApiError(403, RESPOND_DENIED)
    note = (note or "").strip()
    if len(note) < STEWARD_NOTE_MIN:
        raise ApiError(400, RESPONSE_REQUIRED, {"code": "RESPONSE_REQUIRED", "field": "note"})
    proposal = None
    if proposal_id is not None:
        proposal = await session.scalar(select(Proposal).where(
            Proposal.id == proposal_id, Proposal.ecosystem_id == audit.ecosystem_id))
        if proposal is None:
            raise ApiError(400, RESPONSE_PROPOSAL_INVALID, {"code": "PROPOSAL_INVALID", "field": "proposal_id"})
    if await _locked_status(session, audit) != AUDIT_PUBLISHED:
        raise ApiError(409, NOT_PUBLISHED, {"code": "NOT_PUBLISHED"})
    if await health.audit_record(session, audit.id, health.AUDIT_RESPONSE_SKILL) is not None:
        raise ApiError(409, ALREADY_RESPONDED, {"code": "ALREADY_RESPONDED"})
    named = ({"proposal": {"id": str(proposal.id), "proposal_id": proposal.proposal_id, "title": proposal.title}}
             if proposal is not None else None)  # never source_proposal_id: that marks a proposal's own decision
    record = _audit_decision(
        audit, caller, skill=health.AUDIT_RESPONSE_SKILL, note=note, related=named,
        holding=(f"The stewards responded to the governance health audit {audit.audit_id}"
                 + (f" with the proposal {proposal.proposal_id} “{proposal.title}”." if proposal else ".")))
    session.add(record)
    return record


@safeguards_api_bp.post("/audits/<audit_id:uuid>/abandon")
@authenticated
async def abandon_audit(request: Request, audit_id: uuid.UUID):
    """POST /api/v1/safeguards/audits/:id/abandon {reason} -- a draft its auditor or a steward abandons, recorded."""
    try:
        body = AuditAbandonRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e
    async with request.app.ctx.db() as session:
        audit = await get_scoped_or_404(session, request, GovernanceHealthAudit, audit_id, label="Audit")
        caller = await caller_in(session, request, audit.ecosystem_id)
        await abandon_audit_draft(session, audit, caller, body.reason)
        await session.commit()
        await session.refresh(audit)
        return json(await audit_detail_payload(session, audit, caller))


@safeguards_api_bp.post("/audits/<audit_id:uuid>/respond")
@authenticated
async def respond_to_audit(request: Request, audit_id: uuid.UUID):
    """POST /api/v1/safeguards/audits/:id/respond {note, proposal_id?} -- the stewards' recorded response."""
    try:
        body = AuditRespondRequest(**(request.json or {}))
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from e
    async with request.app.ctx.db() as session:
        audit = await get_scoped_or_404(session, request, GovernanceHealthAudit, audit_id, label="Audit")
        caller = await caller_in(session, request, audit.ecosystem_id)
        await record_audit_response(session, audit, caller, body.note, body.proposal_id)
        await session.commit()
        return json(await audit_detail_payload(session, audit, caller), status=201)
