"""Dashboard home view — summary data and activity feed.

Blueprint: dashboard_bp, url_prefix="/dashboard"

Provides the main dashboard page with governance summary cards
(counts of agreements, proposals by phase, members, domains) and
a recent activity feed of the last 10 governance actions.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sanic import Blueprint, html
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import (
    Agreement,
    DecisionRecord,
    Domain,
    Member,
    Proposal,
)
from neos_agent.views._rendering import render, html_fragment, get_selected_ecosystem_ids

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint("dashboard", url_prefix="/dashboard")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _summary_counts(session, ecosystem_ids=None) -> dict:
    """Gather aggregate counts for the dashboard summary cards.

    When ecosystem_ids is provided, all counts are scoped to those ecosystems.
    """
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
    """Return the most recent governance actions across entity types.

    When ecosystem_ids is provided, only shows activity from those ecosystems.
    """
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

@dashboard_bp.get("/")
async def dashboard_home(request: Request):
    """GET /dashboard -- render home page with summary data."""
    eco_ids = get_selected_ecosystem_ids(request)
    try:
        async with request.app.ctx.db() as session:
            counts = await _summary_counts(session, ecosystem_ids=eco_ids)
            activity = await _recent_activity(session, ecosystem_ids=eco_ids)
    except Exception:
        logger.exception("Failed to load dashboard data")
        counts = {
            "agreements": 0, "members": 0, "domains": 0,
            "proposals": 0, "decisions": 0,
            "proposals_by_status": {}, "agreements_by_status": {},
        }
        activity = []

    content = await render(
        "dashboard/home.html",
        request=request,
        counts=counts,
        activity=activity,
        now=datetime.utcnow(),
        active_page="dashboard",
    )
    return html(content)


@dashboard_bp.get("/data")
async def dashboard_data(request: Request):
    """GET /dashboard/data -- htmx fragment returning summary cards."""
    eco_ids = get_selected_ecosystem_ids(request)
    try:
        async with request.app.ctx.db() as session:
            counts = await _summary_counts(session, ecosystem_ids=eco_ids)
    except Exception:
        logger.exception("Failed to load dashboard summary data")
        counts = {
            "agreements": 0, "members": 0, "domains": 0,
            "proposals": 0, "decisions": 0,
            "proposals_by_status": {}, "agreements_by_status": {},
        }

    fragment = await render("dashboard/_summary_cards.html", request=request, counts=counts)
    return html_fragment(fragment)


@dashboard_bp.get("/activity")
async def dashboard_activity(request: Request):
    """GET /dashboard/activity -- htmx fragment returning recent activity feed."""
    eco_ids = get_selected_ecosystem_ids(request)
    try:
        async with request.app.ctx.db() as session:
            activity = await _recent_activity(session, ecosystem_ids=eco_ids, limit=10)
    except Exception:
        logger.exception("Failed to load activity feed")
        activity = []

    fragment = await render("dashboard/_activity_feed.html", request=request, activity=activity)
    return html_fragment(fragment)
