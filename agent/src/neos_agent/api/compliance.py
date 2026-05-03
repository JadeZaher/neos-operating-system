"""JSON API blueprint for compliance summary management.

Blueprint: compliance_api_bp, url_prefix="/api/v1/compliance"

Endpoints for generating and retrieving AI-powered governance compliance
summaries for ecosystems. All endpoints require authentication.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.db.models import (
    Agreement,
    ComplianceSummary,
    ConflictCase,
    Domain,
    Proposal,
)
from neos_agent.ai.provider import acompletion, is_ai_enabled

from .helpers import require_auth, get_ecosystem_ids

logger = logging.getLogger(__name__)

compliance_api_bp = Blueprint("compliance_api", url_prefix="/api/v1/compliance")


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
        "version_fingerprint": s.version_fingerprint,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@compliance_api_bp.post("/generate")
async def generate_compliance(request: Request):
    """POST /api/v1/compliance/generate -- Generate a compliance summary.

    Loads all agreements, domains, proposals, and open conflicts for the
    selected ecosystem(s), then uses AI (or a structural fallback) to
    produce a scored compliance summary stored in ComplianceSummary.

    Returns JSON: ComplianceSummary dict with 201 status.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)
    if not eco_ids:
        return json({"error": "No ecosystem in scope"}, status=400)

    async with request.app.ctx.db() as session:
        # Load agreements
        agr_result = await session.execute(
            select(Agreement).where(Agreement.ecosystem_id.in_(eco_ids))
        )
        agreements = agr_result.scalars().all()

        # Load domains
        dom_result = await session.execute(
            select(Domain).where(Domain.ecosystem_id.in_(eco_ids))
        )
        domains = dom_result.scalars().all()

        # Load proposals
        prop_result = await session.execute(
            select(Proposal).where(Proposal.ecosystem_id.in_(eco_ids))
        )
        proposals = prop_result.scalars().all()

        # Load open conflicts
        conflict_result = await session.execute(
            select(ConflictCase).where(
                ConflictCase.ecosystem_id.in_(eco_ids),
                ConflictCase.status.notin_(["resolved", "closed"]),
            )
        )
        open_conflicts = conflict_result.scalars().all()

        # Build summary statistics
        agr_total = len(agreements)
        agr_status_counts: dict[str, int] = {}
        for a in agreements:
            agr_status_counts[a.status] = agr_status_counts.get(a.status, 0) + 1

        dom_total = len(domains)
        prop_total = len(proposals)
        conflict_total = len(open_conflicts)

        status_summary = ", ".join(
            f"{count} {status}" for status, count in agr_status_counts.items()
        ) or "none"

        summary_text: str | None = None
        score_data: dict | None = None
        flagged_issues: dict | None = None

        if is_ai_enabled():
            prompt = (
                f"Analyze the governance compliance of this ecosystem. "
                f"Agreements: {agr_total} ({status_summary}). "
                f"Domains: {dom_total}. "
                f"Proposals: {prop_total}. "
                f"Open conflicts: {conflict_total}. "
                f"Generate a compliance summary with scores (0-100) for: "
                f"agreement_coverage, domain_health, process_adherence, conflict_resolution. "
                f"Flag any issues. Respond in JSON with keys: summary (string), scores (object), flagged_issues (array)."
            )
            try:
                ai_result = await acompletion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                    temperature=0.3,
                )
                if ai_result and ai_result.get("content"):
                    import json as _json
                    raw = ai_result["content"].strip()
                    # Strip markdown code fences if present
                    if raw.startswith("```"):
                        lines = raw.split("\n")
                        raw = "\n".join(
                            l for l in lines
                            if not l.startswith("```")
                        ).strip()
                    try:
                        parsed = _json.loads(raw)
                        summary_text = parsed.get("summary")
                        scores = parsed.get("scores", {})
                        score_data = {
                            "agreement_coverage": scores.get("agreement_coverage"),
                            "domain_health": scores.get("domain_health"),
                            "process_adherence": scores.get("process_adherence"),
                            "conflict_resolution": scores.get("conflict_resolution"),
                        }
                        issues = parsed.get("flagged_issues", [])
                        flagged_issues = {"issues": issues}
                    except Exception:
                        summary_text = ai_result["content"]
            except Exception as exc:
                logger.error("AI compliance generation failed: %s", exc)
                # Fall through to structural summary

        if summary_text is None:
            # Structural fallback — no AI needed
            active_count = agr_status_counts.get("active", 0)
            agr_coverage_score = int((active_count / agr_total * 100)) if agr_total else 0
            conflict_score = max(0, 100 - conflict_total * 10)
            summary_text = (
                f"Structural compliance summary: {agr_total} agreements "
                f"({status_summary}), {dom_total} domains, {prop_total} proposals, "
                f"{conflict_total} open conflicts."
            )
            score_data = {
                "agreement_coverage": agr_coverage_score,
                "domain_health": 100 if dom_total > 0 else 0,
                "process_adherence": 100 if prop_total > 0 else 50,
                "conflict_resolution": conflict_score,
            }
            flagged_issues = {
                "issues": [
                    f"Open conflict: {c.case_id} — {c.title}" for c in open_conflicts
                ]
            }

        # Use first ecosystem_id for storage (one summary per generate call)
        ecosystem_id = eco_ids[0]

        compliance = ComplianceSummary(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            summary=summary_text,
            score_data=score_data,
            flagged_issues=flagged_issues,
        )
        session.add(compliance)
        await session.commit()
        await session.refresh(compliance)

    return json(_summary_to_dict(compliance), status=201)


@compliance_api_bp.get("/latest")
async def get_latest_compliance(request: Request):
    """GET /api/v1/compliance/latest -- Most recent compliance summary.

    Returns the latest ComplianceSummary for the selected ecosystem(s).
    Returns 404 if none exists.
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(ComplianceSummary)
            .order_by(ComplianceSummary.generated_at.desc())
        )
        if eco_ids:
            stmt = stmt.where(ComplianceSummary.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt.limit(1))
        summary = result.scalar_one_or_none()

    if summary is None:
        return json({"error": "No compliance summary found"}, status=404)

    return json(_summary_to_dict(summary))


@compliance_api_bp.get("/history")
async def get_compliance_history(request: Request):
    """GET /api/v1/compliance/history -- Paginated compliance history.

    Query params: page (default 1), per_page (default 25, max 100).
    Returns JSON: {"items": [...], "total": N, "page": P, "per_page": PP}
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    from sqlalchemy import func

    async with request.app.ctx.db() as session:
        stmt = select(ComplianceSummary).order_by(
            ComplianceSummary.generated_at.desc()
        )
        if eco_ids:
            stmt = stmt.where(ComplianceSummary.ecosystem_id.in_(eco_ids))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        summaries = result.scalars().all()

    return json({
        "items": [_summary_to_dict(s) for s in summaries],
        "total": total,
        "page": page,
        "per_page": per_page,
    })
