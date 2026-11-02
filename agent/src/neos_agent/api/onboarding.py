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
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from neos_agent.db.models import (
    Ecosystem,
    Member,
    MemberOnboarding,
    UserJourneyProgress,
)
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.policy import can_manage_onboarding, can_read_onboarding_record, can_record_onboarding_consent
from neos_agent.services import dates
from neos_agent.services.agreement_consent import missing_agreement_consents
from neos_agent.services.member_lifecycle import agreement_brief
from neos_agent.api.helpers import get_authorized_ecosystem_ids, get_ecosystem_ids, parse_pagination
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
    """Completion from section consents: a stand-aside or objection is recorded but is not consent (review M3)."""
    if not section_consents:
        return 0
    completed = 0
    for section in _CONSENT_SECTIONS:
        val = section_consents.get(section)
        if val is True:
            completed += 1
        elif isinstance(val, dict) and val.get("consented") and val.get("position") in (None, "consent"):
            completed += 1
    return round((completed / len(_CONSENT_SECTIONS)) * 100)


NEWCOMER_WINDOW_DAYS = 30  # a member counts as new for this long after joining
STEWARDS_ONLY = "Only stewards see newcomers"


async def _stewarded_ecosystem_ids(session, request: Request, ecosystem_ids) -> list[uuid.UUID]:
    """The ecosystems among `ecosystem_ids` whose onboarding the caller manages (policy.can_manage_onboarding)."""
    stewarded = []
    for ecosystem_id in ecosystem_ids:
        if can_manage_onboarding(await caller_in(session, request, ecosystem_id), ecosystem_id):
            stewarded.append(ecosystem_id)
    return stewarded


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@onboarding_api_bp.get("/")
@authenticated
async def list_pending_onboardings(request: Request):
    """GET /api/v1/onboarding -- Ceremony records below 100% (read-only history), for stewards of the selection.

    Members no longer see everyone's ceremony progress (review L-row "List onboardings").
    Query params: page (default 1), per_page (default 25, max 100).
    """
    page = parse_pagination(request)

    async with request.app.ctx.db() as session:
        eco_ids = await _stewarded_ecosystem_ids(session, request, get_ecosystem_ids(request))
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


@onboarding_api_bp.get("/newcomers")
@authenticated
async def list_newcomers(request: Request):
    """GET /api/v1/onboarding/newcomers -- Stewards' Newcomers list: pending members and members joined in the last
    30 days in EVERY ecosystem they steward (the queue's reach, not the selection: FX-Onboard F12); stuck ones
    (pending, nothing left to consent to) first. 403 otherwise."""
    cutoff = dates.utc_now() - _dt.timedelta(days=NEWCOMER_WINDOW_DAYS)
    async with request.app.ctx.db() as session:
        eco_ids = await _stewarded_ecosystem_ids(session, request, get_authorized_ecosystem_ids(request))
        if not eco_ids:
            raise ApiError(403, STEWARDS_ONLY)
        rows = (await session.execute(
            select(Member, Ecosystem.name)
            .join(Ecosystem, Ecosystem.id == Member.ecosystem_id)
            .where(
                Member.ecosystem_id.in_(eco_ids),
                or_(Member.current_status == "pending_consent",
                    and_(Member.current_status == "active", Member.created_at >= cutoff)),
            )
            .order_by(Member.created_at.desc(), Member.id)
        )).all()
        progress: dict[uuid.UUID, str] = {}
        for record in (await session.execute(
            select(UserJourneyProgress).where(UserJourneyProgress.member_id.in_([member.id for member, _ in rows]))
            .order_by(UserJourneyProgress.created_at)
        )).scalars():
            progress[record.member_id] = record.status or "in_progress"  # the latest row wins
        items = []
        for member, ecosystem_name in rows:
            from neos_agent.services.join_gates import join_gate_summary
            gates = await join_gate_summary(session, ecosystem_id=member.ecosystem_id, member=member)
            missing = (await missing_agreement_consents(session, member.id, member.ecosystem_id, "ecosystem")
                       if member.current_status == "pending_consent" else [])
            items.append({
                "id": str(member.id),
                "display_name": member.display_name,
                "ecosystem_id": str(member.ecosystem_id),
                "ecosystem_name": ecosystem_name,
                "current_status": member.current_status,
                "joined_at": member.created_at.isoformat() if member.created_at else None,
                "required_agreements": [agreement_brief(agreement) for agreement in missing],
                "orientation_status": progress.get(member.id, "not_started"),
                "join_gates": gates,
                "stuck": member.current_status == "pending_consent" and gates["eligible"],
            })
    items.sort(key=lambda item: (not item["stuck"], item["current_status"] != "pending_consent"))  # stable: newest first within
    return json({"items": items, "total": len(items)})


@onboarding_api_bp.get("/<member_id:uuid>/ceremony")
@authenticated
async def get_ceremony_state(request: Request, member_id: uuid.UUID):
    """GET /api/v1/onboarding/:member_id/ceremony -- Ceremony state.

    Returns section_consents map, completion_percentage, cooling_off dates.
    """
    async with request.app.ctx.db() as session:
        # A member opens from any authorized ecosystem, matching the list's owner-only rule.
        target = await get_scoped_or_404(session, request, Member, member_id, label="Member", include_shared=False)
        caller = await caller_in(session, request, target.ecosystem_id)
        if not can_read_onboarding_record(caller, target):  # FX-Onboard A8: positions and objections are not public
            raise ApiError(404, "Member not found")
        can_record = can_record_onboarding_consent(caller, target)

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

        stmt = (  # locked: a section write is a JSON read-modify-write, so two at once must not lose one (L4)
            select(MemberOnboarding).where(MemberOnboarding.member_id == member_id)
            .order_by(MemberOnboarding.created_at, MemberOnboarding.id).limit(1).with_for_update()
        )
        ob = (await session.execute(stmt)).scalars().first()

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
            ob.consent_date = dates.utc_today()

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
