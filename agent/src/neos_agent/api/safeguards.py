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

from neos_agent.db.models import GovernanceHealthAudit, Member
from neos_agent.api import policy
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import require_auth, get_ecosystem_ids, get_authorized_ecosystem_ids, apply_ecosystem_filter, apply_ecosystem_name_filter, build_search_filter
from neos_agent.api.schemas.safeguards import AuditCreateRequest, AuditDetail, AuditListItem, AuditUpdateRequest, HealthSummary

logger = logging.getLogger(__name__)

# Published-audit rules: an indicator's status is worth these points; the score is their mean.
INDICATOR_STATUS_POINTS = {"healthy": 100, "warning": 50, "critical": 0}
AUDIT_PUBLISHED = "completed"
AUDIT_DRAFT = "draft"
NEXT_AUDIT_AFTER_DAYS = 90
AUDIT_FINISH_DENIED = "Only the member who is recording this audit can edit or publish it"


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


def _audit_to_list_item(a: GovernanceHealthAudit) -> dict:
    return AuditListItem(
        id=a.id,
        audit_id=a.audit_id,
        ecosystem_id=a.ecosystem_id,
        audit_date=a.audit_date,
        auditor=a.auditor,
        overall_health_score=a.overall_health_score,
        status=a.status,
        created_at=a.created_at,
        completed_at=getattr(a, 'updated_at', None) if a.status == 'completed' else None,
        overall_health=getattr(a, 'overall_health', None) or _health_score_to_label(a.overall_health_score),
        audit_scope=getattr(a, 'audit_scope', None),
        trigger_type=getattr(a, 'trigger_type', None),
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


def _audit_to_detail(a: GovernanceHealthAudit, caller: Member | None = None) -> dict:
    return AuditDetail(
        caller_can_edit=a.status == AUDIT_DRAFT and policy.can_finish_audit(caller, a),
        id=a.id,
        audit_id=a.audit_id,
        ecosystem_id=a.ecosystem_id,
        audit_date=a.audit_date,
        auditor=a.auditor,
        overall_health_score=a.overall_health_score,
        status=a.status,
        created_at=a.created_at,
        completed_at=getattr(a, 'updated_at', None) if a.status == 'completed' else None,
        overall_health=getattr(a, 'overall_health', None) or _health_score_to_label(a.overall_health_score),
        audit_scope=getattr(a, 'audit_scope', None),
        trigger_type=getattr(a, 'trigger_type', None),
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
    """GET /api/v1/safeguards -- latest audit + health metrics summary."""
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
        published_stmt = base_stmt.where(GovernanceHealthAudit.status == AUDIT_PUBLISHED).limit(1)
        latest_audit = (await session.execute(published_stmt)).scalar_one_or_none()

    # Extract indicator scores from latest audit if available
    latest_indicators = getattr(latest_audit, 'indicator_scores', None) if latest_audit else None
    latest_safeguards = getattr(latest_audit, 'triggered_safeguards', None) if latest_audit else None

    summary = HealthSummary(
        latest_audit=_audit_to_detail(latest_audit) if latest_audit else None,
        recent_audits=[_audit_to_list_item(a) for a in recent_audits],
        health_score=latest_audit.overall_health_score if latest_audit else None,
        indicator_scores=latest_indicators,
        triggered_safeguards=latest_safeguards,
    )

    return json(summary.model_dump(mode="json"))


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

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

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

    return json(_audit_to_detail(audit, caller))


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
        if not policy.is_active_member_in(auditor, create_req.ecosystem_id):
            raise ApiError(403, "Only active members of this ecosystem can record an audit")

        audit = GovernanceHealthAudit(
            id=uuid.uuid4(),
            ecosystem_id=create_req.ecosystem_id,
            audit_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
            audit_date=_dt.date.today(),
            auditor=auditor.display_name,
            auditor_ids=[str(auditor.id)],
            trigger_type="human",
            capture_risk_indicators={},
            status=AUDIT_DRAFT,
        )
        _apply_audit_fields(audit, create_req.model_dump(exclude_none=True, exclude={"ecosystem_id"}))
        session.add(audit)
        await session.commit()
        await session.refresh(audit)
        return json(_audit_to_detail(audit, auditor), status=201)


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
        return json(_audit_to_detail(audit, caller))


@safeguards_api_bp.post("/audits/<audit_id:uuid>/publish")
@authenticated
async def publish_audit(request: Request, audit_id: uuid.UUID):
    """POST /api/v1/safeguards/audits/:id/publish -- finish a draft: it needs indicator statuses, then sets the score."""
    async with request.app.ctx.db() as session:
        audit, caller = await _audit_to_edit(session, request, audit_id)
        score = audit_score(_scores_to_list(audit.indicator_scores))
        if score is None:
            raise ApiError(400, "Rate at least one indicator (healthy, warning or critical) before publishing")
        audit.overall_health_score = score
        audit.overall_health = _health_score_to_label(score)
        audit.status = AUDIT_PUBLISHED
        audit.audit_date = _dt.date.today()
        audit.next_audit_due = _dt.date.today() + _dt.timedelta(days=NEXT_AUDIT_AFTER_DAYS)
        await session.commit()
        await session.refresh(audit)
        return json(_audit_to_detail(audit, caller))
