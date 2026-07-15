"""JSON API blueprint for badge definition management.

Blueprint: badges_api_bp, url_prefix="/api/v1/badges"

Manages the admin-curated catalog of badge definitions (distinct from
earned UserBadge awards in db/course_models.py).
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from neos_agent.db.models import BadgeDefinition
from neos_agent.api.helpers import require_auth, require_admin, get_ecosystem_ids
from neos_agent.api.schemas.badges import (
    BadgeDefinitionCreateRequest,
    BadgeDefinitionSchema,
    BadgeDefinitionUpdateRequest,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

badges_api_bp = Blueprint("badges_api", url_prefix="/api/v1/badges")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _badge_to_schema(b: BadgeDefinition) -> dict:
    return BadgeDefinitionSchema(
        id=b.id,
        ecosystem_id=b.ecosystem_id,
        badge_key=b.badge_key,
        badge_name=b.badge_name,
        badge_description=b.badge_description,
        badge_category=b.badge_category,
        badge_icon=b.badge_icon,
        strength=b.strength,
        is_active=b.is_active,
        created_by=b.created_by,
        created_at=b.created_at,
        updated_at=b.updated_at,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@badges_api_bp.get("/")
async def list_badges(request: Request):
    """GET /api/v1/badges -- List badge definitions in scope, plus global badges."""
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(BadgeDefinition)
            .where(or_(
                BadgeDefinition.ecosystem_id.in_(eco_ids),
                BadgeDefinition.ecosystem_id.is_(None),
            ))
            .order_by(BadgeDefinition.badge_name)
        )
        result = await session.execute(stmt)
        badges = result.scalars().all()

    return json({
        "items": [_badge_to_schema(b) for b in badges],
        "total": len(badges),
    })


@badges_api_bp.post("/")
async def create_badge(request: Request):
    """POST /api/v1/badges -- Create a badge definition.

    Accepts JSON: BadgeDefinitionCreateRequest
    Returns JSON: BadgeDefinitionSchema with 201 status.
    """
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = BadgeDefinitionCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    ecosystem_id = create_req.ecosystem_id
    if ecosystem_id is None:
        eco_ids = get_ecosystem_ids(request)
        if eco_ids:
            ecosystem_id = eco_ids[0]

    async with request.app.ctx.db() as session:
        badge = BadgeDefinition(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            badge_key=create_req.badge_key,
            badge_name=create_req.badge_name,
            badge_description=create_req.badge_description,
            badge_category=create_req.badge_category,
            badge_icon=create_req.badge_icon,
            strength=create_req.strength,
            created_by=admin.id,
        )
        session.add(badge)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return json({"error": "A badge with that key already exists"}, status=409)

        await session.refresh(badge)

    return json(_badge_to_schema(badge), status=201)


@badges_api_bp.put("/<badge_id:uuid>")
async def update_badge(request: Request, badge_id: uuid.UUID):
    """PUT /api/v1/badges/:id -- Update non-None fields of a badge definition."""
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = BadgeDefinitionUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        badge = await session.get(BadgeDefinition, badge_id)
        if badge is None:
            return json({"error": "Badge not found"}, status=404)

        for field, value in update_req.model_dump(exclude_none=True).items():
            setattr(badge, field, value)

        await session.commit()
        await session.refresh(badge)

    return json(_badge_to_schema(badge))


@badges_api_bp.delete("/<badge_id:uuid>")
async def delete_badge(request: Request, badge_id: uuid.UUID):
    """DELETE /api/v1/badges/:id -- Delete a badge definition."""
    admin, err = require_admin(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        badge = await session.get(BadgeDefinition, badge_id)
        if badge is None:
            return json({"error": "Badge not found"}, status=404)

        await session.delete(badge)
        await session.commit()

    return json({"success": True})
