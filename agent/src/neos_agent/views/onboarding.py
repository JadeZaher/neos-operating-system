"""Onboarding & UAF consent ceremony views for the NEOS dashboard.

Blueprint: onboarding_bp, url_prefix="/dashboard/onboarding"

Handles the Universal Agreement Field consent ceremony — step-by-step
walkthrough of all 6 UAF sections with AI explanation and facilitation.
Tracks per-section consent with a 48-hour cooling-off period.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sanic import Blueprint, html
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from neos_agent.db.models import MemberOnboarding, Member
from neos_agent.views._rendering import render, parse_pagination, get_selected_ecosystem_ids

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


def apply_section_consent(onboarding: MemberOnboarding, section_key: str, now: datetime) -> bool:
    """Record consent for a single UAF section on an onboarding record.

    Mutates the onboarding object in-place (section_consents, completion_percentage,
    cooling-off dates). Caller must commit the session.

    Returns True if all 6 sections are now consented.
    """
    consents = onboarding.section_consents or {}
    if isinstance(consents, str):
        consents = json.loads(consents)
    consents[section_key] = {
        "consented_at": now.isoformat(),
        "consented": True,
    }
    onboarding.section_consents = consents

    all_consented = all(
        s["key"] in consents and consents[s["key"]].get("consented")
        for s in UAF_SECTIONS
    )
    if all_consented and not onboarding.cooling_off_start:
        onboarding.cooling_off_start = now.date()
        onboarding.cooling_off_end = (now + timedelta(hours=48)).date()
        onboarding.consent_date = now.date()

    consented_count = sum(
        1 for s in UAF_SECTIONS
        if s["key"] in consents and consents[s["key"]].get("consented")
    )
    onboarding.completion_percentage = int((consented_count / len(UAF_SECTIONS)) * 100)
    return all_consented


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
            if eco_ids and (member is None or member.ecosystem_id not in eco_ids):
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
    """POST /dashboard/onboarding/ceremony/{id}/consent -- record consent for a UAF section.

    After all 6 sections are consented, a 48-hour cooling-off period starts.
    """
    form = request.form
    section_key = form.get("section_key")

    if not section_key:
        return redirect(f"/dashboard/onboarding/ceremony/{onboarding_id}")

    try:
        now = datetime.now(timezone.utc)
        async with request.app.ctx.db() as session:
            onboarding = await session.get(MemberOnboarding, onboarding_id)
            if onboarding is None:
                return redirect("/dashboard/onboarding")

            # Verify ecosystem scope through parent member
            member = await session.get(Member, onboarding.member_id)
            eco_ids = get_selected_ecosystem_ids(request)
            if eco_ids and (member is None or member.ecosystem_id not in eco_ids):
                return redirect("/dashboard/onboarding")

            apply_section_consent(onboarding, section_key, now)

            await session.commit()
    except Exception:
        logger.exception("Failed to record consent")
        return redirect(f"/dashboard/onboarding/ceremony/{onboarding_id}")

    return redirect(f"/dashboard/onboarding/ceremony/{onboarding_id}")


@onboarding_bp.post("/start")
async def start_onboarding(request: Request):
    """POST /dashboard/onboarding/start -- start a new onboarding process."""
    form = request.form
    try:
        member_id = uuid.UUID(form.get("member_id"))
    except (ValueError, TypeError):
        content = await render(
            "dashboard/onboarding/list.html",
            request=request,
            onboardings=[],
            error="Invalid member ID.",
            active_page="onboarding",
        )
        return html(content, status=400)
    try:
        async with request.app.ctx.db() as session:
            # Verify the member belongs to one of the user's selected ecosystems
            member = await session.get(Member, member_id)
            eco_ids = get_selected_ecosystem_ids(request)
            if member is None or (eco_ids and member.ecosystem_id not in eco_ids):
                content = await render(
                    "dashboard/onboarding/list.html",
                    request=request,
                    onboardings=[],
                    error="Member not found or not in your selected ecosystems.",
                    active_page="onboarding",
                )
                return html(content, status=400)
            onboarding = MemberOnboarding(
                id=uuid.uuid4(),
                member_id=member_id,
                facilitator=form.get("facilitator"),
                section_consents={},
                completion_percentage=0,
            )
            session.add(onboarding)
            await session.commit()
            new_id = onboarding.id
    except Exception:
        logger.exception("Failed to start onboarding")
        content = await render(
            "dashboard/onboarding/list.html",
            request=request,
            onboardings=[],
            error="Failed to start onboarding.",
            active_page="onboarding",
        )
        return html(content, status=400)

    return redirect(f"/dashboard/onboarding/ceremony/{new_id}")


@onboarding_bp.post("/ceremony/<onboarding_id:uuid>/finalize")
async def finalize_onboarding(request: Request, onboarding_id: uuid.UUID):
    """POST /dashboard/onboarding/ceremony/{id}/finalize -- complete onboarding.

    Only succeeds if all sections are consented and cooling-off period has passed.
    """
    try:
        now = datetime.now(timezone.utc)
        async with request.app.ctx.db() as session:
            onboarding = await session.get(MemberOnboarding, onboarding_id)
            if onboarding is None:
                return redirect("/dashboard/onboarding")

            # Verify ecosystem scope through parent member
            member = await session.get(Member, onboarding.member_id)
            eco_ids = get_selected_ecosystem_ids(request)
            if eco_ids and (member is None or member.ecosystem_id not in eco_ids):
                return redirect("/dashboard/onboarding")

            # Verify all 6 UAF sections are consented
            consents = onboarding.section_consents or {}
            if isinstance(consents, str):
                consents = json.loads(consents)
            all_consented = all(
                s["key"] in consents and consents[s["key"]].get("consented")
                for s in UAF_SECTIONS
            )
            if not all_consented:
                content = await render(
                    "dashboard/onboarding/ceremony.html",
                    request=request,
                    onboarding=onboarding,
                    uaf_sections=UAF_SECTIONS,
                    error="All 6 UAF sections must be consented before finalizing.",
                    active_page="onboarding",
                )
                return html(content, status=400)

            # Verify cooling-off period has passed
            if not onboarding.cooling_off_end or now.date() < onboarding.cooling_off_end:
                content = await render(
                    "dashboard/onboarding/ceremony.html",
                    request=request,
                    onboarding=onboarding,
                    uaf_sections=UAF_SECTIONS,
                    error="Cooling-off period has not yet passed.",
                    active_page="onboarding",
                )
                return html(content, status=400)

            onboarding.completion_percentage = 100

            # Update the member's status to active
            member = await session.get(Member, onboarding.member_id)
            if member:
                member.current_status = "active"

            await session.commit()
    except Exception:
        logger.exception("Failed to finalize onboarding")
        return redirect(f"/dashboard/onboarding/ceremony/{onboarding_id}")

    return redirect("/dashboard/onboarding")
