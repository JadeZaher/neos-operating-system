"""JSON API blueprint for orientation / journey-map management.

Blueprint: orientation_api_bp, url_prefix="/api/v1/orientation"

All endpoints require authentication via the neos_session cookie.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import and_, delete as sa_delete, func, select

from neos_agent.db.models import (
    Ecosystem,
    EthosUserAccess,
    JourneyMap,
    Member,
    UserJourneyProgress,
)
from neos_agent.services.member_lifecycle import counts_as_member

from neos_agent.services.member_messaging import owner_contact

from .errors import ApiError
from .guards import JOIN_REQUIRED, authenticated, caller_in, caller_in_or_join_required
from .policy import can_manage_onboarding

logger = logging.getLogger(__name__)

orientation_api_bp = Blueprint("orientation_api", url_prefix="/api/v1/orientation")

ORIENTATION_STEWARDS_ONLY = "Only an active steward of this ecosystem can change its orientation"
GLOBAL_JOURNEY_LOCKED = "This journey belongs to no ecosystem, so no ecosystem's steward can change it"
PROGRESS_STATUSES = ("in_progress", "complete", "opted_out")


async def _journey_view(db, request, journey):
    from neos_agent.api.guards import caller_user_id
    from neos_agent.services.matching import visible_ecosystem
    from neos_agent.services.orientation_content import entrant_content
    may_edit = False
    if journey.ecosystem_id is not None:
        _, member = await visible_ecosystem(db, journey.ecosystem_id, caller_user_id(request))
        may_edit = can_manage_onboarding(member, journey.ecosystem_id)
    if not journey.is_active and not may_edit:
        raise ApiError(404, "Journey map not found")
    return {"id": str(journey.id), "slug": journey.slug, "title": journey.title, "description": journey.description,
            "ecosystem_id": str(journey.ecosystem_id) if journey.ecosystem_id else None,
            "step_count": journey.step_count or len(journey.content_sequence or []),
            "content_sequence": journey.content_sequence or [] if may_edit else entrant_content(journey.content_sequence or []),
            "exit_package": journey.exit_package or {} if may_edit else entrant_content(journey.exit_package or {}),
            "is_default": journey.is_default, "is_active": journey.is_active,
            "created_at": journey.created_at.isoformat() if journey.created_at else None}


async def _visible_journeys(db, request, maps):
    visible = []
    for journey in maps:
        try:
            visible.append(await _journey_view(db, request, journey))
        except ApiError as error:
            if error.status != 404:
                raise
    return visible


async def _require_onboarding_steward(db, request: Request, ecosystem_id: uuid.UUID) -> Member:
    """The caller's row when they may change this ecosystem's orientation (policy.can_manage_onboarding), else 403."""
    caller = await caller_in(db, request, ecosystem_id)
    if not can_manage_onboarding(caller, ecosystem_id):
        raise ApiError(403, ORIENTATION_STEWARDS_ONLY)
    return caller


async def _steward_map_or_error(db, request: Request, journey_map_id: uuid.UUID) -> JourneyMap:
    """A journey map the caller may change: 404 missing, 403 global (no ecosystem) or not a steward of its ecosystem."""
    jm = await db.get(JourneyMap, journey_map_id)
    if jm is None:
        raise ApiError(404, "Journey map not found")
    if jm.ecosystem_id is None:
        raise ApiError(403, GLOBAL_JOURNEY_LOCKED)
    await _require_onboarding_steward(db, request, jm.ecosystem_id)
    return jm


def _require_orienting_member(member: Member) -> None:
    """Orientation is for active members and newcomers; a leaver joins again first, a paused membership waits."""
    if member.current_status == "exited":
        raise ApiError(409, "Join this ecosystem again to begin its orientation", {"code": JOIN_REQUIRED})
    if member.current_status not in ("active", "pending_consent"):
        raise ApiError(403, "Your membership here is paused, so your orientation cannot be saved right now")


async def _validate_progress_body(db, ecosystem_id: uuid.UUID, body: dict) -> None:
    """The journey is this ecosystem's and active; status and step are from the known vocabulary (review L3)."""
    if "status" in body and body["status"] not in PROGRESS_STATUSES:
        raise ApiError(400, "Unknown orientation status", {"allowed": list(PROGRESS_STATUSES)})
    if "current_step" in body and (isinstance(body["current_step"], bool) or not isinstance(body["current_step"], int)
                                   or body["current_step"] < 0):
        raise ApiError(400, "current_step must be a whole number from 0")
    if body.get("journey_map_id"):
        try:
            map_id = uuid.UUID(str(body["journey_map_id"]))
        except ValueError:
            raise ApiError(400, "journey_map_id is not a valid id") from None
        jm = await db.get(JourneyMap, map_id)
        if jm is None or jm.ecosystem_id != ecosystem_id or not jm.is_active:
            raise ApiError(400, "That journey is not part of this ecosystem's orientation", {"field": "journey_map_id"})
        body["journey_map_id"] = map_id


# --- Endpoints ---


@orientation_api_bp.get("/ethos/<ecosystem_id:uuid>")
@authenticated
async def get_ethos_detail(request: Request, ecosystem_id: uuid.UUID):
    """Get ecosystem detail for orientation (acts as ethos detail).

    Returns JSON with ecosystem info, member count, tags, and governance summary.
    """
    async with request.app.ctx.db() as db:
        from neos_agent.api.guards import caller_user_id
        from neos_agent.services.matching import visible_ecosystem
        eco, _ = await visible_ecosystem(db, ecosystem_id, caller_user_id(request))

        member_count = await db.scalar(
            select(func.count(Member.id)).where(Member.ecosystem_id == ecosystem_id, counts_as_member())
        )

        return json({
            "id": str(eco.id),
            "name": eco.name,
            "slug": eco.slug if hasattr(eco, "slug") and eco.slug else str(eco.id),
            "description": eco.description,
            "sector": getattr(eco, "sector", None),
            "member_count": member_count or 0,
            "tags": eco.tags if isinstance(eco.tags, list) else [],
            "governance_summary": eco.governance_summary,
            "owner": await owner_contact(db, eco.id),
        })


@orientation_api_bp.get("/ethos/<ecosystem_id:uuid>/journey-maps")
@authenticated
async def list_journey_maps(request: Request, ecosystem_id: uuid.UUID):
    """List available journey maps for an ecosystem.

    Returns JSON: list of journey map summaries.
    """
    include_inactive = request.args.get("include_inactive", "").lower() in ("true", "1")

    async with request.app.ctx.db() as db:
        from neos_agent.api.guards import caller_user_id
        from neos_agent.services.matching import visible_ecosystem
        await visible_ecosystem(db, ecosystem_id, caller_user_id(request))
        filters = [JourneyMap.ecosystem_id == ecosystem_id]
        if not include_inactive:
            filters.append(JourneyMap.is_active == True)  # noqa: E712

        stmt = (
            select(JourneyMap)
            .where(and_(*filters))
            .order_by(JourneyMap.is_default.desc(), JourneyMap.created_at)
        )

        result = await db.execute(stmt)
        maps = result.scalars().all()

        return json(await _visible_journeys(db, request, maps))


@orientation_api_bp.get("/journey-maps")
@authenticated
async def list_all_journey_maps(request: Request):
    """List all journey maps across ecosystems (admin / management view).

    Query params:
      - ethos_id: optional ecosystem UUID to filter by
      - is_active: optional "true"/"false" filter
    Returns JSON: { maps: [...] }
    """
    async with request.app.ctx.db() as db:
        filters = []
        ethos_id = request.args.get("ethos_id")
        if ethos_id:
            filters.append(JourneyMap.ecosystem_id == ethos_id)
        is_active_param = request.args.get("is_active")
        if is_active_param is not None:
            filters.append(JourneyMap.is_active == (is_active_param.lower() in ("true", "1")))

        stmt = (
            select(JourneyMap)
            .where(and_(*filters) if filters else True)
            .order_by(JourneyMap.created_at.desc())
        )
        result = await db.execute(stmt)
        maps = result.scalars().all()

        return json({"maps": await _visible_journeys(db, request, maps)})


@orientation_api_bp.get("/journey-maps/<journey_map_id:uuid>")
@authenticated
async def get_journey_map(request: Request, journey_map_id: uuid.UUID):
    """Get a specific journey map with full content.

    Returns JSON: journey map detail including content_sequence and exit_package.
    """
    async with request.app.ctx.db() as db:
        jm = await db.get(JourneyMap, journey_map_id)
        if jm is None:
            return json({"error": "Journey map not found"}, status=404)

        return json(await _journey_view(db, request, jm))


@orientation_api_bp.post("/ethos/<ecosystem_id:uuid>/journey-maps")
@authenticated
async def create_journey_map(request: Request, ecosystem_id: uuid.UUID):
    """POST -- Create a new journey map for an ecosystem."""
    body = request.json or {}
    title = (body.get("title") or "").strip()
    if not title:
        return json({"error": "title is required"}, status=400)

    raw_slug = body.get("slug") or title
    slug = re.sub(r"[^a-z0-9]+", "-", raw_slug.lower()).strip("-")[:200]
    content_sequence = body.get("content_sequence", [])
    if not isinstance(content_sequence, list):
        return json({"error": "content_sequence must be a list"}, status=400)

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)
        await _require_onboarding_steward(db, request, ecosystem_id)
        from neos_agent.services.orientation_content import validate_journey_routes
        validate_journey_routes(content_sequence)

        jm = JourneyMap(
            id=uuid.uuid4(),
            slug=slug,
            title=title,
            description=body.get("description"),
            ecosystem_id=ecosystem_id,
            content_sequence=content_sequence,
            exit_package=body.get("exit_package", {}),
            step_count=len(content_sequence),
            is_default=body.get("is_default", False),
            is_active=body.get("is_active", True),
        )
        db.add(jm)
        await db.commit()

        return json({
            "id": str(jm.id),
            "slug": jm.slug,
            "title": jm.title,
            "description": jm.description,
            "ecosystem_id": str(jm.ecosystem_id),
            "step_count": jm.step_count,
            "content_sequence": jm.content_sequence,
            "exit_package": jm.exit_package or {},
            "is_default": jm.is_default,
            "is_active": jm.is_active,
            "created_at": jm.created_at.isoformat() if jm.created_at else None,
        }, status=201)


@orientation_api_bp.put("/journey-maps/<journey_map_id:uuid>")
@authenticated
async def update_journey_map(request: Request, journey_map_id: uuid.UUID):
    """PUT -- Update an existing journey map (an active steward of its ecosystem)."""
    body = request.json or {}
    if "content_sequence" in body and not isinstance(body["content_sequence"], list):
        return json({"error": "content_sequence must be a list"}, status=400)

    async with request.app.ctx.db() as db:
        jm = await _steward_map_or_error(db, request, journey_map_id)

        if "title" in body:
            jm.title = body["title"]
        if "description" in body:
            jm.description = body["description"]
        if "slug" in body:
            jm.slug = body["slug"]
        if "content_sequence" in body:
            from neos_agent.services.orientation_content import validate_journey_routes
            validate_journey_routes(body["content_sequence"])
            jm.content_sequence = body["content_sequence"]
            jm.step_count = len(body["content_sequence"])
        if "exit_package" in body:
            jm.exit_package = body["exit_package"]
        if "is_default" in body:
            jm.is_default = body["is_default"]
        if "is_active" in body:
            jm.is_active = body["is_active"]

        await db.commit()

        return json({
            "id": str(jm.id),
            "slug": jm.slug,
            "title": jm.title,
            "description": jm.description,
            "ecosystem_id": str(jm.ecosystem_id) if jm.ecosystem_id else None,
            "step_count": jm.step_count,
            "content_sequence": jm.content_sequence or [],
            "exit_package": jm.exit_package or {},
            "is_default": jm.is_default,
            "is_active": jm.is_active,
            "created_at": jm.created_at.isoformat() if jm.created_at else None,
        })


@orientation_api_bp.delete("/journey-maps/<journey_map_id:uuid>")
@authenticated
async def delete_journey_map(request: Request, journey_map_id: uuid.UUID):
    """DELETE -- Delete a journey map nobody has walked; one with members' progress is deactivated instead (409)."""
    async with request.app.ctx.db() as db:
        jm = await _steward_map_or_error(db, request, journey_map_id)
        from neos_agent.db.models import OrientationChatSession
        walked = await db.scalar(
            select(func.count(UserJourneyProgress.id)).where(UserJourneyProgress.journey_map_id == journey_map_id)
        )
        conversations = await db.scalar(select(func.count(OrientationChatSession.id)).where(OrientationChatSession.journey_map_id == journey_map_id))
        if walked or conversations:
            raise ApiError(409, "Members have progress on this journey. Deactivate it instead.",
                           {"code": "JOURNEY_IN_USE", "progress_count": walked, "conversation_count": conversations})
        await db.delete(jm)
        await db.commit()

    return json({"ok": True, "message": "Journey map deleted"})


@orientation_api_bp.post("/journey-maps/<journey_map_id:uuid>/deactivate")
@authenticated
async def deactivate_journey_map(request: Request, journey_map_id: uuid.UUID):
    """POST -- Soft-delete a journey map by setting is_active=False (an active steward of its ecosystem)."""
    async with request.app.ctx.db() as db:
        jm = await _steward_map_or_error(db, request, journey_map_id)

        jm.is_active = False
        await db.commit()

    return json({"ok": True, "message": "Journey map deactivated"})


@orientation_api_bp.get("/ethos/<ecosystem_id:uuid>/progress")
@authenticated
async def get_progress(request: Request, ecosystem_id: uuid.UUID):
    """Get current user's orientation progress for an ecosystem.

    Returns JSON: progress object or empty dict if none exists.
    """
    async with request.app.ctx.db() as db:
        # Progress belongs to the caller's Member row in THIS ecosystem, not the default row.
        member = await caller_in(db, request, ecosystem_id)
        if member is None:
            return json({})

        stmt = (
            select(UserJourneyProgress)
            .where(
                and_(
                    UserJourneyProgress.member_id == member.id,
                    UserJourneyProgress.ecosystem_id == ecosystem_id,
                )
            )
            .order_by(UserJourneyProgress.created_at.desc())
        )

        result = await db.execute(stmt)
        progress = result.scalars().first()

        if not progress:
            return json({})

        return json({
            "id": str(progress.id),
            "user_id": str(progress.member_id),
            "ethos_id": str(progress.ecosystem_id),
            "journey_map_id": str(progress.journey_map_id),
            "orientation_path": progress.orientation_path or "explorer",
            "current_step": progress.current_step or 0,
            "completed_steps": progress.completed_steps or [],
            "step_responses": progress.step_responses or {},
            "status": progress.status or "not_started",
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "was_recommended": progress.was_recommended if progress.was_recommended is not None else True,
            "misalignment_flags": progress.misalignment_flags or [],
            "created_at": progress.created_at.isoformat() if progress.created_at else None,
            "updated_at": progress.updated_at.isoformat() if progress.updated_at else None,
        })


@orientation_api_bp.post("/ethos/<ecosystem_id:uuid>/progress")
@authenticated
async def save_progress(request: Request, ecosystem_id: uuid.UUID):
    """Save or update orientation progress.

    Accepts JSON with fields: journey_map_id, current_step, orientation_path,
    was_recommended, step_key, step_response, status.
    Returns JSON: saved progress summary.
    """
    body = request.json or {}

    async with request.app.ctx.db() as db:
        # Beginning an orientation is joining's first step: no row here is a 409 the client answers by joining.
        member = await caller_in_or_join_required(
            db, request, ecosystem_id,
            not_found="Ecosystem not found", join_message="Join this ecosystem to begin its orientation",
        )
        _require_orienting_member(member)
        await _validate_progress_body(db, ecosystem_id, body)
        from neos_agent.services.node_admin import authorize, is_node_admin
        node_admin_actor = await authorize(db, member.user_id) if await is_node_admin(db, member.user_id) else None

        # Find existing progress (locked: a step save is a read-modify-write of completed_steps)
        stmt = select(UserJourneyProgress).where(
            and_(
                UserJourneyProgress.member_id == member.id,
                UserJourneyProgress.ecosystem_id == ecosystem_id,
            )
        ).order_by(UserJourneyProgress.created_at.desc()).with_for_update()
        result = await db.execute(stmt)
        progress = result.scalars().first()
        if progress is None and not body.get("journey_map_id"):
            raise ApiError(400, "Choose a journey to begin", {"field": "journey_map_id"})

        journey_id = body.get("journey_map_id") or progress.journey_map_id
        journey = await db.get(JourneyMap, journey_id)
        if journey is None or journey.ecosystem_id != ecosystem_id or not journey.is_active:
            raise ApiError(409, "Choose a current journey from this ecosystem")
        from neos_agent.services.orientation_completion import validate_progress
        step_responses, completed_steps = await validate_progress(db, member, journey, progress, body, node_admin_actor)

        now = datetime.utcnow()

        if progress:
            # Update existing
            if progress.journey_map_id != journey.id:
                progress.current_step, progress.completed_at = 0, None
            if body.get("journey_map_id"):  # FX-Onboard A11: a null keeps the journey (NOT NULL column, was a 500)
                progress.journey_map_id = body["journey_map_id"]
            if "current_step" in body:
                progress.current_step = body["current_step"]
            if "orientation_path" in body:
                progress.orientation_path = body["orientation_path"]
            if "was_recommended" in body:
                progress.was_recommended = body["was_recommended"]
            progress.updated_at = now
            progress.step_responses = step_responses
            progress.completed_steps = completed_steps

            # Merge step responses
            status = body.get("status", progress.status)
            progress.status = status
            if status == "complete" and not progress.completed_at:
                progress.completed_at = now
            if status == "in_progress" and not progress.started_at:
                progress.started_at = now
        else:
            # Create new
            progress = UserJourneyProgress(
                id=uuid.uuid4(),
                member_id=member.id,
                ecosystem_id=ecosystem_id,
                journey_map_id=body.get("journey_map_id"),
                orientation_path=body.get("orientation_path", "explorer"),
                current_step=body.get("current_step", 0),
                completed_steps=completed_steps,
                step_responses=step_responses,
                status=body.get("status", "in_progress"),
                started_at=now,
                completed_at=now if body.get("status") == "complete" else None,
                was_recommended=body.get("was_recommended", True),
                misalignment_flags=[],
            )
            db.add(progress)

        await db.commit()

        return json({
            "id": str(progress.id),
            "user_id": str(progress.member_id),
            "ethos_id": str(progress.ecosystem_id),
            "journey_map_id": str(progress.journey_map_id),
            "current_step": progress.current_step,
            "status": progress.status,
        })


@orientation_api_bp.post("/genplan-input")
@authenticated
async def save_genplan_input(request: Request):
    """Save generative plan input from orientation choices.

    Accepts JSON payload with orientation choice data.
    Returns JSON: {"status": "ok", "received": true}
    """
    body = request.json or {}
    if not isinstance(body, dict) or set(body) - {"ethos_id", "journey_step_id", "section_key", "choice_key", "choice_label", "choice_index", "output_text"}:
        raise ApiError(400, "Use only the documented saved-choice fields")
    try:
        ecosystem_id = uuid.UUID(str(body.get("ethos_id", "")))
        step_index = int(body.get("journey_step_id", ""))
    except (TypeError, ValueError):
        raise ApiError(400, "Choose the ecosystem and saved journey choice") from None
    async with request.app.ctx.db() as db:
        member = await caller_in_or_join_required(db, request, ecosystem_id, not_found="Ecosystem not found", join_message="Begin this ecosystem's orientation first")
        _require_orienting_member(member)
        progress = await db.scalar(select(UserJourneyProgress).where(UserJourneyProgress.member_id == member.id, UserJourneyProgress.ecosystem_id == ecosystem_id).order_by(UserJourneyProgress.created_at.desc()).with_for_update().limit(1))
        journey = await db.get(JourneyMap, progress.journey_map_id) if progress else None
        steps = journey.content_sequence if journey and isinstance(journey.content_sequence, list) else []
        if not 0 <= step_index < len(steps) or not isinstance(steps[step_index], dict) or steps[step_index].get("type") != "choice":
            raise ApiError(409, "Save a real choice from your current journey first")
        step = steps[step_index]
        selected = next((choice for choice in step.get("choices", []) if isinstance(choice, dict) and choice.get("value") == body.get("choice_key")), None)
        saved = (progress.step_responses or {}).get(f"step_{step_index}")
        if selected is None or not isinstance(saved, dict) or saved.get("choice") != selected["value"]:
            raise ApiError(409, "This choice has not been saved in your own orientation")
        from neos_agent.services.orientation_completion import canonical_genplan_inputs
        responses = canonical_genplan_inputs(journey, progress.step_responses or {})
        canonical = responses["genplan_inputs"][str(step_index)]
        if any(key in body and body[key] != canonical[key] for key in canonical):
            raise ApiError(409, "Plan labels and output must match the saved journey source")
        progress.step_responses = responses
        await db.commit()
        return json({"status": "ok", "received": True, "saved": True, "journey_id": str(journey.id), "step_id": f"step_{step_index}"})
