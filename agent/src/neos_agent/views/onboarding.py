"""Onboarding & UAF consent ceremony views for the NEOS dashboard.

Blueprint: onboarding_bp, url_prefix="/dashboard/onboarding"

Handles the Universal Agreement Field consent ceremony — step-by-step
walkthrough of all 6 UAF sections with AI explanation and facilitation.
Tracks per-section consent with a 48-hour cooling-off period.
"""

from __future__ import annotations

import logging
import uuid
from sanic import Blueprint, html
from sanic.request import Request
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from neos_agent.db.models import MemberOnboarding, Member
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids, retired_write

logger = logging.getLogger(__name__)

onboarding_bp = Blueprint("onboarding", url_prefix="/dashboard/onboarding")

# The 6 UAF sections for the consent ceremony
UAF_SECTIONS = [
    {
        "key": "purpose_values",
        "title": "Section 1: Purpose & Values",
        "description": "Shared purpose statement and core value commitments of the ecosystem.",
        "step": 1,
    },
    {
        "key": "governance_structure",
        "title": "Section 2: Governance Structure",
        "description": "How authority is distributed — domains, circles, stewardship roles.",
        "step": 2,
    },
    {
        "key": "decision_making",
        "title": "Section 3: Decision-Making",
        "description": "The ACT process (Advice, Consent, Test) and escalation pathways.",
        "step": 3,
    },
    {
        "key": "resource_agreements",
        "title": "Section 4: Resource Agreements",
        "description": "How economic resources and Current-See influence are managed.",
        "step": 4,
    },
    {
        "key": "conflict_resolution",
        "title": "Section 5: Conflict Resolution",
        "description": "Escalation tiers, NVC dialogue, harm circles, and repair processes.",
        "step": 5,
    },
    {
        "key": "exit_rights",
        "title": "Section 6: Exit Rights & Portability",
        "description": "Right to voluntary exit, commitment unwinding, and data portability.",
        "step": 6,
    },
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@onboarding_bp.get("/")
async def list_onboardings(request: Request):
    """GET /dashboard/onboarding -- list onboarding processes."""
    eco_ids = get_selected_ecosystem_ids(request)
    offset, limit = parse_pagination(request)
    try:
        async with request.app.ctx.db() as session:
            stmt = (
                select(MemberOnboarding)
                .options(selectinload(MemberOnboarding.member))
                .order_by(MemberOnboarding.created_at.desc())
            )
            if eco_ids:
                stmt = stmt.join(MemberOnboarding.member).where(
                    Member.ecosystem_id.in_(eco_ids)
                )
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = await session.scalar(count_stmt) or 0

            stmt = stmt.offset(offset).limit(limit)
            result = await session.execute(stmt)
            onboardings = result.scalars().all()
    except Exception:
        logger.exception("Failed to load onboarding list")
        onboardings = []
        total = 0

    content = await render(
        "dashboard/onboarding/list.html",
        request=request,
        onboardings=onboardings,
        total=total,
        offset=offset,
        limit=limit,
        active_page="onboarding",
    )
    return html(content)


@onboarding_bp.get("/ceremony/<onboarding_id:uuid>")
async def ceremony(request: Request, onboarding_id: uuid.UUID):
    """GET /dashboard/onboarding/ceremony/{id} -- UAF consent ceremony view.

    Renders a step-by-step walkthrough of all 6 UAF sections.
    """
    try:
        async with request.app.ctx.db() as session:
            onboarding = await session.get(MemberOnboarding, onboarding_id)
            if onboarding is None:
                content = await render(
                    "dashboard/onboarding/list.html",
                    request=request,
                    onboardings=[],
                    error="Onboarding record not found.",
                    active_page="onboarding",
                )
                return html(content, status=404)

            # Get member info and verify ecosystem scope
            member = await session.get(Member, onboarding.member_id)
            eco_ids = get_selected_ecosystem_ids(request)
            if not eco_ids or member is None or member.ecosystem_id not in eco_ids:
                content = await render(
                    "dashboard/onboarding/list.html",
                    request=request,
                    onboardings=[],
                    error="Onboarding record not found.",
                    active_page="onboarding",
                )
                return html(content, status=404)
    except Exception:
        logger.exception("Failed to load ceremony")
        content = await render(
            "dashboard/onboarding/list.html",
            request=request,
            onboardings=[],
            error="Failed to load ceremony.",
            active_page="onboarding",
        )
        return html(content, status=500)

    content = await render(
        "dashboard/onboarding/ceremony.html",
        request=request,
        onboarding=onboarding,
        member=member,
        uaf_sections=UAF_SECTIONS,
        active_page="onboarding",
    )
    return html(content)


@onboarding_bp.post("/ceremony/<onboarding_id:uuid>/consent")
async def record_consent(request: Request, onboarding_id: uuid.UUID):
    """POST /dashboard/onboarding/ceremony/{id}/consent -- retired (410): writes happen in the app."""
    return retired_write(request, "/onboarding")


@onboarding_bp.post("/start")
async def start_onboarding(request: Request):
    """POST /dashboard/onboarding/start -- retired (410): writes happen in the app."""
    return retired_write(request, "/onboarding")


@onboarding_bp.post("/ceremony/<onboarding_id:uuid>/finalize")
async def finalize_onboarding(request: Request, onboarding_id: uuid.UUID):
    """POST /dashboard/onboarding/ceremony/{id}/finalize -- retired (410): writes happen in the app."""
    return retired_write(request, "/onboarding")
