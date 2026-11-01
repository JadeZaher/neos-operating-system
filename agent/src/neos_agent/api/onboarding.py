"""JSON API blueprint for onboarding ceremony management.

Blueprint: onboarding_api_bp, url_prefix="/api/v1/onboarding"

Manages the UAF onboarding ceremony including section-by-section
consent tracking and completion percentage calculation.
Returns JSON responses only.
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
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    Member,
    MemberOnboarding,
)
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.policy import can_record_onboarding_consent
from neos_agent.api.helpers import get_ecosystem_ids, parse_pagination
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.api.schemas.onboarding import CeremonyState, OnboardingListItem, SectionConsentRequest

logger = logging.getLogger(__name__)


ONBOARDING_CONSENT_DENIED = "Only the member themselves or a steward of their ecosystem can record this consent"

# The 6 UAF consent sections used to calculate completion_percentage
_CONSENT_SECTIONS = [
    "governance",
    "economics",
    "membership",
    "conflict_resolution",
    "data_sovereignty",
    "exit_rights",
]


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

onboarding_api_bp = Blueprint("onboarding_api", url_prefix="/api/v1/onboarding")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _calc_completion(section_consents: dict | None) -> int:
    """Calculate completion percentage from section consents."""
    if not section_consents:
        return 0
    total = len(_CONSENT_SECTIONS)
    if total == 0:
        return 0
    completed = 0
    for section in _CONSENT_SECTIONS:
        val = section_consents.get(section)
        if val is True:
            completed += 1
        elif isinstance(val, dict) and val.get("consented"):
            completed += 1
    return round((completed / total) * 100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@onboarding_api_bp.get("/")
@authenticated
async def list_pending_onboardings(request: Request):
    """GET /api/v1/onboarding -- List pending onboardings.

    Returns onboarding records where completion_percentage < 100.
    Ecosystem scoped via the member join.
    Query params: page (default 1), per_page (default 25, max 100).
    """
    eco_ids = get_ecosystem_ids(request)
    page = parse_pagination(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(MemberOnboarding, Member.display_name)
            .join(Member, MemberOnboarding.member_id == Member.id)
            .where(
                (MemberOnboarding.completion_percentage < 100)
                | (MemberOnboarding.completion_percentage.is_(None))
            )
            .order_by(MemberOnboarding.created_at.desc())
        )

        stmt = restrict_to_ecosystems(stmt, Member, eco_ids, include_shared=False)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        stmt = stmt.offset(page.offset).limit(page.per_page)
        result = await session.execute(stmt)
        rows = result.all()

    items = []
    for ob, display_name in rows:
        items.append(
            OnboardingListItem(
                id=ob.id,
                member_id=ob.member_id,
                member_display_name=display_name,
                facilitator=ob.facilitator,
                completion_percentage=ob.completion_percentage,
                consent_date=ob.consent_date,
                cooling_off_start=ob.cooling_off_start,
                cooling_off_end=ob.cooling_off_end,
                created_at=ob.created_at,
            ).model_dump(mode="json")
        )

    return json({
        "items": items,
        "total": total,
        "page": page.page,
        "per_page": page.per_page,
    })


@onboarding_api_bp.get("/<member_id:uuid>/ceremony")
@authenticated
async def get_ceremony_state(request: Request, member_id: uuid.UUID):
    """GET /api/v1/onboarding/:member_id/ceremony -- Ceremony state.

    Returns section_consents map, completion_percentage, cooling_off dates.
    """
    async with request.app.ctx.db() as session:
        # A member opens from any authorized ecosystem, matching the list's owner-only rule.
        target = await get_scoped_or_404(session, request, Member, member_id, label="Member", include_shared=False)
        can_record = can_record_onboarding_consent(await caller_in(session, request, target.ecosystem_id), target)

        stmt = select(MemberOnboarding).where(
            MemberOnboarding.member_id == member_id
        )
        result = await session.execute(stmt)
        ob = result.scalar_one_or_none()

    if ob is None:
        raise ApiError(404, "No onboarding record found for this member")

    # Ensure section_consents has all sections represented
    consents = dict(ob.section_consents) if ob.section_consents else {}
    for section in _CONSENT_SECTIONS:
        consents.setdefault(section, False)

    state = CeremonyState(
        member_id=ob.member_id,
        section_consents=consents,
        completion_percentage=ob.completion_percentage or 0,
        cooling_off_start=ob.cooling_off_start,
        cooling_off_end=ob.cooling_off_end,
        consent_date=ob.consent_date,
        facilitator=ob.facilitator,
        uaf_version_consented=ob.uaf_version_consented,
        caller_can_record=can_record,
    )
    return json(state.model_dump(mode="json"))


@onboarding_api_bp.post("/<member_id:uuid>/ceremony")
@authenticated
async def submit_section_consent(request: Request, member_id: uuid.UUID):
    """POST /api/v1/onboarding/:member_id/ceremony -- Submit section consent.

    Accepts JSON: {"section": "governance", "consented": true}
    Updates section_consents JSON and recalculates completion_percentage
    (6 sections total).
    """
    body = request.json or {}
    try:
        req = SectionConsentRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    if req.section not in _CONSENT_SECTIONS:
        raise ApiError(400, f"Invalid section: '{req.section}'", {"valid_sections": _CONSENT_SECTIONS})

    async with request.app.ctx.db() as session:
        target = await get_scoped_or_404(session, request, Member, member_id, label="Member", include_shared=False)
        # Only the member themselves, or a steward of their ecosystem facilitating, records their consent.
        if not can_record_onboarding_consent(await caller_in(session, request, target.ecosystem_id), target):
            raise ApiError(403, ONBOARDING_CONSENT_DENIED)

        stmt = select(MemberOnboarding).where(
            MemberOnboarding.member_id == member_id
        )
        result = await session.execute(stmt)
        ob = result.scalar_one_or_none()

        if ob is None:
            raise ApiError(404, "No onboarding record found for this member")

        # Update section consent
        consents = dict(ob.section_consents) if ob.section_consents else {}
        # Store section consent with optional position data
        if req.position and req.position != "consent":
            consents[req.section] = {
                "consented": req.consented,
                "position": req.position,
                "objection_text": req.objection_text,
            }
        else:
            consents[req.section] = req.consented
        ob.section_consents = consents

        # Recalculate completion percentage
        ob.completion_percentage = _calc_completion(consents)

        # If fully complete and no consent_date yet, set it
        if ob.completion_percentage == 100 and ob.consent_date is None:
            ob.consent_date = _dt.date.today()

        await session.commit()
        await session.refresh(ob)

        logger.info(
            "Onboarding %s: section '%s' consented=%s, completion=%d%%",
            member_id, req.section, req.consented, ob.completion_percentage,
        )

    # Return updated ceremony state
    full_consents = dict(ob.section_consents) if ob.section_consents else {}
    for section in _CONSENT_SECTIONS:
        full_consents.setdefault(section, False)

    state = CeremonyState(
        member_id=ob.member_id,
        section_consents=full_consents,
        completion_percentage=ob.completion_percentage or 0,
        cooling_off_start=ob.cooling_off_start,
        cooling_off_end=ob.cooling_off_end,
        consent_date=ob.consent_date,
        facilitator=ob.facilitator,
        uaf_version_consented=ob.uaf_version_consented,
        caller_can_record=True,
    )
    return json(state.model_dump(mode="json"))
