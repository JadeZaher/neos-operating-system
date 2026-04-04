"""Dashboard JSON API blueprint.

Blueprint: dashboard_api_bp, url_prefix="/api/v1/dashboard"

Returns structured JSON for the dashboard summary cards and recent
activity feed. Mirrors the query logic from views/dashboard.py but
returns DashboardSummary JSON instead of rendered HTML.
"""

from __future__ import annotations

import json
import logging
import uuid

from sanic import Blueprint
from sanic.request import Request
from sanic.response import JSONResponse, json as json_response
from sqlalchemy import func, select

from neos_agent.db.models import (
    Agreement,
    DecisionRecord,
    Domain,
    Member,
    Proposal,
)
from neos_agent.api.schemas import ActivityItem, DashboardSummary, SummaryCard

logger = logging.getLogger(__name__)

dashboard_api_bp = Blueprint("dashboard_api", url_prefix="/api/v1/dashboard")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_ecosystem_ids_from_request(request) -> list[uuid.UUID]:
    """Extract ecosystem IDs from cookie or member context."""
    cookie = request.cookies.get("neos_selected_ecosystems")
    if cookie:
        try:
            ids = json.loads(cookie)
            return [uuid.UUID(i) for i in ids if i]
        except (json.JSONDecodeError, ValueError):
            pass
    # Fallback to member's ecosystem
    member = getattr(request.ctx, "member", None)
    if member:
        return [member.ecosystem_id]
    return []


async def _summary_counts(session, ecosystem_ids=None) -> dict:
    """Gather aggregate counts for the dashboard summary cards."""

    def _eco_filter(stmt, model):
        if ecosystem_ids:
            stmt = stmt.where(model.ecosystem_id.in_(ecosystem_ids))
        return stmt

    agreement_count = await session.scalar(
        _eco_filter(select(func.count()).select_from(Agreement), Agreement)
    )
    member_count = await session.scalar(
        _eco_filter(select(func.count()).select_from(Member), Member)
    )
    domain_count = await session.scalar(
        _eco_filter(select(func.count()).select_from(Domain), Domain)
    )
    proposal_count = await session.scalar(
        _eco_filter(select(func.count()).select_from(Proposal), Proposal)
    )
    decision_count = await session.scalar(
        _eco_filter(select(func.count()).select_from(DecisionRecord), DecisionRecord)
    )

    # Proposals grouped by status
    prop_stmt = select(Proposal.status, func.count()).group_by(Proposal.status)
    if ecosystem_ids:
        prop_stmt = prop_stmt.where(Proposal.ecosystem_id.in_(ecosystem_ids))
    proposal_by_status_rows = (await session.execute(prop_stmt)).all()
    proposals_by_status = {row[0]: row[1] for row in proposal_by_status_rows}

    # Agreements grouped by status
    agr_stmt = select(Agreement.status, func.count()).group_by(Agreement.status)
    if ecosystem_ids:
        agr_stmt = agr_stmt.where(Agreement.ecosystem_id.in_(ecosystem_ids))
    agreement_by_status_rows = (await session.execute(agr_stmt)).all()
    agreements_by_status = {row[0]: row[1] for row in agreement_by_status_rows}

    return {
        "agreements": agreement_count or 0,
        "members": member_count or 0,
        "domains": domain_count or 0,
        "proposals": proposal_count or 0,
        "decisions": decision_count or 0,
        "proposals_by_status": proposals_by_status,
        "agreements_by_status": agreements_by_status,
    }


async def _recent_activity(session, ecosystem_ids=None, limit: int = 10) -> list[dict]:
    """Return the most recent governance actions across entity types."""
    activities: list[dict] = []

    # Recent proposals
    prop_stmt = select(Proposal).order_by(Proposal.created_at.desc()).limit(limit)
    if ecosystem_ids:
        prop_stmt = prop_stmt.where(Proposal.ecosystem_id.in_(ecosystem_ids))
    proposals = (await session.execute(prop_stmt)).scalars().all()
    for p in proposals:
        activities.append({
            "type": "proposal",
            "title": p.title,
            "status": p.status,
            "timestamp": p.created_at,
            "id": str(p.id),
            "label": f"Proposal: {p.title}",
        })

    # Recent agreements
    agr_stmt = select(Agreement).order_by(Agreement.created_at.desc()).limit(limit)
    if ecosystem_ids:
        agr_stmt = agr_stmt.where(Agreement.ecosystem_id.in_(ecosystem_ids))
    agreements = (await session.execute(agr_stmt)).scalars().all()
    for a in agreements:
        activities.append({
            "type": "agreement",
            "title": a.title,
            "status": a.status,
            "timestamp": a.created_at,
            "id": str(a.id),
            "label": f"Agreement: {a.title}",
        })

    # Recent decisions
    dec_stmt = select(DecisionRecord).order_by(DecisionRecord.created_at.desc()).limit(limit)
    if ecosystem_ids:
        dec_stmt = dec_stmt.where(DecisionRecord.ecosystem_id.in_(ecosystem_ids))
    decisions = (await session.execute(dec_stmt)).scalars().all()
    for d in decisions:
        activities.append({
            "type": "decision",
            "title": d.holding or d.record_id,
            "status": d.status,
            "timestamp": d.created_at,
            "id": str(d.id),
            "label": f"Decision: {d.record_id}",
        })

    # Sort by timestamp descending, take first `limit`
    activities.sort(key=lambda a: a["timestamp"], reverse=True)
    return activities[:limit]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@dashboard_api_bp.get("/summary")
async def dashboard_summary(request: Request) -> JSONResponse:
    """GET /api/v1/dashboard/summary -- return DashboardSummary JSON."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Unauthorized"}, status=401)

    ecosystem_ids = _get_ecosystem_ids_from_request(request)

    try:
        async with request.app.ctx.db() as session:
            counts = await _summary_counts(session, ecosystem_ids=ecosystem_ids)
            raw_activity = await _recent_activity(session, ecosystem_ids=ecosystem_ids, limit=10)
    except Exception:
        logger.exception("Failed to load dashboard summary data")
        counts = {
            "agreements": 0,
            "members": 0,
            "domains": 0,
            "proposals": 0,
            "decisions": 0,
            "proposals_by_status": {},
            "agreements_by_status": {},
        }
        raw_activity = []

    cards = [
        SummaryCard(
            label="Agreements",
            value=counts["agreements"],
            href="/agreements",
            breakdown=counts.get("agreements_by_status"),
        ),
        SummaryCard(
            label="Proposals",
            value=counts["proposals"],
            href="/proposals",
            breakdown=counts.get("proposals_by_status"),
        ),
        SummaryCard(label="Members", value=counts["members"], href="/members"),
        SummaryCard(label="Domains", value=counts["domains"], href="/domains"),
        SummaryCard(label="Decisions", value=counts["decisions"], href="/decisions"),
    ]

    activity_items = [
        ActivityItem(
            id=a["id"],
            type=a["type"],
            title=a["title"],
            status=a["status"],
            timestamp=a["timestamp"],
            label=a["label"],
            href=f"/{a['type']}s/{a['id']}",
        )
        for a in raw_activity
    ]

    summary = DashboardSummary(cards=cards, activity=activity_items)
    return json_response(summary.model_dump(mode="json"))
