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

from .helpers import require_auth

logger = logging.getLogger(__name__)

orientation_api_bp = Blueprint("orientation_api", url_prefix="/api/v1/orientation")


# --- Endpoints ---


@orientation_api_bp.get("/ethos/<ecosystem_id:uuid>")
async def get_ethos_detail(request: Request, ecosystem_id: uuid.UUID):
    """Get ecosystem detail for orientation (acts as ethos detail).

    Returns JSON with ecosystem info, member count, tags, and governance summary.
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        member_count = await db.scalar(
            select(func.count(Member.id)).where(Member.ecosystem_id == ecosystem_id)
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
        })


@orientation_api_bp.get("/ethos/<ecosystem_id:uuid>/journey-maps")
async def list_journey_maps(request: Request, ecosystem_id: uuid.UUID):
    """List available journey maps for an ecosystem.

    Returns JSON: list of journey map summaries.
    """
    member, err = require_auth(request)
    if err:
        return err

    include_inactive = request.args.get("include_inactive", "").lower() in ("true", "1")

    async with request.app.ctx.db() as db:
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

        return json([
            {
                "id": str(m.id),
                "slug": m.slug,
                "title": m.title,
                "description": m.description,
                "ecosystem_id": str(m.ecosystem_id) if m.ecosystem_id else None,
                "step_count": m.step_count or len(m.content_sequence or []),
                "content_sequence": m.content_sequence or [],
                "exit_package": m.exit_package or {},
                "is_default": m.is_default,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in maps
        ])


@orientation_api_bp.get("/journey-maps")
async def list_all_journey_maps(request: Request):
    """List all journey maps across ecosystems (admin / management view).

    Query params:
      - ethos_id: optional ecosystem UUID to filter by
      - is_active: optional "true"/"false" filter
    Returns JSON: { maps: [...] }
    """
    member, err = require_auth(request)
    if err:
        return err

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

        return json({
            "maps": [
                {
                    "id": str(m.id),
                    "slug": m.slug,
                    "title": m.title,
                    "description": m.description,
                    "ecosystem_id": str(m.ecosystem_id) if m.ecosystem_id else None,
                    "step_count": m.step_count or len(m.content_sequence or []),
                    "content_sequence": m.content_sequence or [],
                    "exit_package": m.exit_package or {},
                    "is_default": m.is_default,
                    "is_active": m.is_active,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in maps
            ]
        })


@orientation_api_bp.get("/journey-maps/<journey_map_id:uuid>")
async def get_journey_map(request: Request, journey_map_id: uuid.UUID):
    """Get a specific journey map with full content.

    Returns JSON: journey map detail including content_sequence and exit_package.
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        jm = await db.get(JourneyMap, journey_map_id)
        if jm is None:
            return json({"error": "Journey map not found"}, status=404)

        return json({
            "id": str(jm.id),
            "slug": jm.slug,
            "title": jm.title,
            "description": jm.description,
            "ecosystem_id": str(jm.ecosystem_id) if jm.ecosystem_id else None,
            "step_count": jm.step_count or len(jm.content_sequence or []),
            "content_sequence": jm.content_sequence or [],
            "exit_package": jm.exit_package or {},
            "is_default": jm.is_default,
            "is_active": jm.is_active,
            "created_at": jm.created_at.isoformat() if jm.created_at else None,
        })


@orientation_api_bp.post("/ethos/<ecosystem_id:uuid>/journey-maps")
async def create_journey_map(request: Request, ecosystem_id: uuid.UUID):
    """POST -- Create a new journey map for an ecosystem."""
    member, err = require_auth(request)
    if err:
        return err

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
async def update_journey_map(request: Request, journey_map_id: uuid.UUID):
    """PUT -- Update an existing journey map."""
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}

    async with request.app.ctx.db() as db:
        jm = await db.get(JourneyMap, journey_map_id)
        if jm is None:
            return json({"error": "Journey map not found"}, status=404)

        if "title" in body:
            jm.title = body["title"]
        if "description" in body:
            jm.description = body["description"]
        if "slug" in body:
            jm.slug = body["slug"]
        if "content_sequence" in body:
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
async def delete_journey_map(request: Request, journey_map_id: uuid.UUID):
    """DELETE -- Delete a journey map."""
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        jm = await db.get(JourneyMap, journey_map_id)
        if jm is None:
            return json({"error": "Journey map not found"}, status=404)

        # Delete associated progress records first
        await db.execute(
            sa_delete(UserJourneyProgress).where(
                UserJourneyProgress.journey_map_id == journey_map_id
            )
        )
        await db.delete(jm)
        await db.commit()

    return json({"ok": True, "message": "Journey map deleted"})


@orientation_api_bp.post("/journey-maps/<journey_map_id:uuid>/deactivate")
async def deactivate_journey_map(request: Request, journey_map_id: uuid.UUID):
    """POST -- Soft-delete a journey map by setting is_active=False."""
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        jm = await db.get(JourneyMap, journey_map_id)
        if jm is None:
            return json({"error": "Journey map not found"}, status=404)

        jm.is_active = False
        await db.commit()

    return json({"ok": True, "message": "Journey map deactivated"})


@orientation_api_bp.get("/ethos/<ecosystem_id:uuid>/progress")
async def get_progress(request: Request, ecosystem_id: uuid.UUID):
    """Get current user's orientation progress for an ecosystem.

    Returns JSON: progress object or empty dict if none exists.
    """
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
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
async def save_progress(request: Request, ecosystem_id: uuid.UUID):
    """Save or update orientation progress.

    Accepts JSON with fields: journey_map_id, current_step, orientation_path,
    was_recommended, step_key, step_response, status.
    Returns JSON: saved progress summary.
    """
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}

    async with request.app.ctx.db() as db:
        # Find existing progress
        stmt = select(UserJourneyProgress).where(
            and_(
                UserJourneyProgress.member_id == member.id,
                UserJourneyProgress.ecosystem_id == ecosystem_id,
            )
        )
        result = await db.execute(stmt)
        progress = result.scalars().first()

        now = datetime.utcnow()

        if progress:
            # Update existing
            if "journey_map_id" in body:
                progress.journey_map_id = body["journey_map_id"]
            if "current_step" in body:
                progress.current_step = body["current_step"]
            if "orientation_path" in body:
                progress.orientation_path = body["orientation_path"]
            if "was_recommended" in body:
                progress.was_recommended = body["was_recommended"]
            progress.updated_at = now

            # Merge step responses
            if "step_key" in body and "step_response" in body:
                responses = dict(progress.step_responses or {})
                responses[body["step_key"]] = body["step_response"]
                progress.step_responses = responses

            # Track completed steps
            if "current_step" in body:
                completed = list(progress.completed_steps or [])
                step_idx = body["current_step"] - 1  # previous step was completed
                if step_idx >= 0 and step_idx not in completed:
                    completed.append(step_idx)
                progress.completed_steps = completed

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
                completed_steps=[],
                step_responses={},
                status=body.get("status", "in_progress"),
                started_at=now,
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
async def save_genplan_input(request: Request):
    """Save generative plan input from orientation choices.

    Accepts JSON payload with orientation choice data.
    Returns JSON: {"status": "ok", "received": true}
    """
    member, err = require_auth(request)
    if err:
        return err

    # Store genplan inputs as part of journey progress step_responses.
    # For now, acknowledge receipt.
    return json({"status": "ok", "received": True})
