"""JSON API blueprint for compliance summary management.

Blueprint: compliance_api_bp, url_prefix="/api/v1/compliance"

Endpoints for generating and retrieving AI-powered governance compliance
summaries for ecosystems. All endpoints require authentication. Scores are measured or null
("not measured"); see api/AGENTS.md "Maintenance and health (G-Maint)".
"""

from __future__ import annotations

import asyncio
import json as _json
import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import (
    Agreement,
    ComplianceSummary,
    ConflictCase,
    Domain,
    Proposal,
)
from neos_agent.ai.provider import acompletion, is_ai_enabled
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.services import health

from .errors import ApiError
from .guards import authenticated, caller_in
from .helpers import get_ecosystem_ids, parse_pagination
from .policy import is_active_member_in

logger = logging.getLogger(__name__)

compliance_api_bp = Blueprint("compliance_api", url_prefix="/api/v1/compliance")

# G-Maint (C9): only measured numbers are stored; the rest is "not measured" (null), never an invented 100.
SCORE_KEYS = ("agreement_coverage", "domain_health", "process_adherence", "conflict_resolution")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summary_to_dict(s: ComplianceSummary) -> dict:
    return {
        "id": str(s.id),
        "ecosystem_id": str(s.ecosystem_id),
        "generated_at": s.generated_at.isoformat() if s.generated_at else None,
        "summary": s.summary,
        "score_data": s.score_data,
        "agreement_coverage": s.agreement_coverage,
        "domain_health": s.domain_health,
        "flagged_issues": s.flagged_issues,
        # Optional: present only if the column exists (not yet migrated).
        "version_fingerprint": getattr(s, "version_fingerprint", None),
    }


async def _target_ecosystem(db, request: Request) -> uuid.UUID:
    """The ecosystem a summary is generated for: the body's `ecosystem_id`, else the one selected; active members only."""
    selected = get_ecosystem_ids(request)
    raw = (request.json or {}).get("ecosystem_id") or (str(selected[0]) if len(selected) == 1 else None)
    if not raw:
        raise ApiError(400, "Choose an ecosystem (ecosystem_id)")
    try:
        ecosystem_id = uuid.UUID(str(raw))
    except ValueError:
        raise ApiError(400, "Choose an ecosystem (ecosystem_id)") from None
    if not is_active_member_in(await caller_in(db, request, ecosystem_id), ecosystem_id):
        raise ApiError(404, "Ecosystem not found")
    return ecosystem_id


async def _ai_summary(facts: str) -> tuple[str | None, list | None]:
    """An optional narrative and issue list from the model; never scores (statuses and numbers are not the model's)."""
    prompt = (
        "Summarise the governance upkeep of this ecosystem for its members in plain words, from these facts only: "
        f"{facts} Respond in JSON with keys: summary (string) and flagged_issues (array of strings). Do not give scores."
    )
    try:
        # Bound the AI call so a slow provider falls back to the structural summary instead of stalling the request.
        result = await asyncio.wait_for(
            acompletion(messages=[{"role": "user", "content": prompt}], max_tokens=1024, temperature=0.3),
            timeout=45,
        )
    except Exception as exc:
        logger.error("AI compliance generation failed: %s", exc)
        return None, None
    raw = ((result or {}).get("content") or "").strip()
    if not raw:
        return None, None
    if raw.startswith("```"):
        raw = "\n".join(line for line in raw.split("\n") if not line.startswith("```")).strip()
    try:
        parsed = _json.loads(raw)
    except Exception:
        return raw, None
    issues = parsed.get("flagged_issues")
    return parsed.get("summary"), [str(issue) for issue in issues] if isinstance(issues, list) else None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@compliance_api_bp.post("/generate")
@authenticated
async def generate_compliance(request: Request):
    """POST /api/v1/compliance/generate -- store a summary for ONE ecosystem (`ecosystem_id`).

    Counts agreements, domains, proposals and open conflicts of that ecosystem only, plus the health
    snapshot's needs-attention counts. Only measured numbers are scored (agreement coverage); the
    others are null ("not measured"). The model, when enabled, writes the narrative only.
    Returns JSON: ComplianceSummary dict with 201 status.
    """
    async with request.app.ctx.db() as session:
        ecosystem_id = await _target_ecosystem(session, request)
        status_counts = dict((await session.execute(select(Agreement.status, func.count(Agreement.id)).where(
            Agreement.ecosystem_id == ecosystem_id).group_by(Agreement.status))).all())
        agr_total = sum(status_counts.values())
        dom_total = await session.scalar(select(func.count(Domain.id)).where(Domain.ecosystem_id == ecosystem_id)) or 0
        prop_total = await session.scalar(select(func.count(Proposal.id)).where(Proposal.ecosystem_id == ecosystem_id)) or 0
        open_conflicts = (await session.execute(select(ConflictCase.case_id).where(
            ConflictCase.ecosystem_id == ecosystem_id, ConflictCase.status.notin_(["resolved", "closed"]),
        ))).scalars().all()
        snapshot = await health.health_snapshot(session, ecosystem_id)

        status_summary = ", ".join(f"{count} {status}" for status, count in status_counts.items()) or "none"
        attention = [f"{item['label']}: {item['count']}" + (f" ({item['detail']})" if item["detail"] else "")
                     for item in snapshot["attention"] if item["count"]]
        in_force = status_counts.get("active", 0) + status_counts.get("under_review", 0)
        score_data = dict.fromkeys(SCORE_KEYS)
        score_data["agreement_coverage"] = round(in_force * 100 / agr_total) if agr_total else None
        facts = (f"Agreements: {agr_total} ({status_summary}). Domains: {dom_total}. Proposals: {prop_total}. "
                 f"Open conflicts: {len(open_conflicts)}. Needs attention: {'; '.join(attention) or 'nothing'}.")
        # Case id only: a harm report's title is visible to its parties and triage stewards only.
        issues = attention + [f"Open conflict case: {case_id}" for case_id in open_conflicts]

        summary_text, ai_issues = await _ai_summary(facts) if is_ai_enabled() else (None, None)
        if summary_text is None:
            summary_text = f"Structural compliance summary: {facts}"
        compliance = ComplianceSummary(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            summary=summary_text,
            score_data=score_data,
            flagged_issues={"issues": issues + [issue for issue in ai_issues or [] if issue not in issues]},
        )
        session.add(compliance)
        await session.commit()
        await session.refresh(compliance)

    return json(_summary_to_dict(compliance), status=201)


@compliance_api_bp.get("/latest")
@authenticated
async def get_latest_compliance(request: Request):
    """GET /api/v1/compliance/latest -- the newest summary of the selected ecosystem(s); 404 if none (fails closed)."""
    async with request.app.ctx.db() as session:
        stmt = restrict_to_ecosystems(
            select(ComplianceSummary).order_by(ComplianceSummary.generated_at.desc()),
            ComplianceSummary, get_ecosystem_ids(request),
        )
        summary = (await session.execute(stmt.limit(1))).scalar_one_or_none()

    if summary is None:
        raise ApiError(404, "No compliance summary found")

    return json(_summary_to_dict(summary))


@compliance_api_bp.get("/history")
@authenticated
async def get_compliance_history(request: Request):
    """GET /api/v1/compliance/history -- paginated summaries of the selected ecosystem(s) (fails closed).

    Query params: page (default 1), per_page (default 25, max 100).
    Returns JSON: {"items": [...], "total": N, "page": P, "per_page": PP}
    """
    page = parse_pagination(request)

    async with request.app.ctx.db() as session:
        stmt = restrict_to_ecosystems(
            select(ComplianceSummary).order_by(ComplianceSummary.generated_at.desc()),
            ComplianceSummary, get_ecosystem_ids(request),
        )
        total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        summaries = (await session.execute(stmt.offset(page.offset).limit(page.per_page))).scalars().all()

    return json({
        "items": [_summary_to_dict(s) for s in summaries],
        "total": total,
        "page": page.page,
        "per_page": page.per_page,
    })
