"""JSON API blueprint for badge definition management.

Blueprint: badges_api_bp, url_prefix="/api/v1/badges"

Manages the admin-curated catalog of badge definitions (distinct from
earned UserBadge awards in db/course_models.py). A badge of one ecosystem is
changed by an administrator of that ecosystem (policy.can_administer_ecosystem);
a global badge (no ecosystem) by a platform admin (helpers.require_admin); see
api/AGENTS.md "Platform admin (G-Authority)".
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
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import get_authorized_ecosystem_ids, get_ecosystem_ids, require_admin
from neos_agent.api.policy import can_administer_ecosystem
from neos_agent.api.schemas.badges import (
    BadgeDefinitionCreateRequest,
    BadgeDefinitionSchema,
    BadgeDefinitionUpdateRequest,
)

logger = logging.getLogger(__name__)

BADGE_MANAGE_DENIED = "Only a steward or administrator of this ecosystem can change its badges"


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


async def _badge_administrator(session, request: Request, ecosystem_id: uuid.UUID | None):
    """(acting row, None) when the caller may change badges of `ecosystem_id` (None = global), else (None, 403)."""
    if ecosystem_id is None:
        return require_admin(request)
    caller = await caller_in(session, request, ecosystem_id)
    if not can_administer_ecosystem(caller, ecosystem_id):
        return None, json({"error": BADGE_MANAGE_DENIED}, status=403)
    return caller, None


async def _visible_badge(session, request: Request, badge_id: uuid.UUID) -> BadgeDefinition | None:
    """A global badge, or one of an ecosystem the caller belongs to; anything else reads as missing."""
    badge = await session.get(BadgeDefinition, badge_id)
    if badge is None:
        return None
    if badge.ecosystem_id is not None and badge.ecosystem_id not in get_authorized_ecosystem_ids(request):
        return None
    return badge


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@badges_api_bp.get("/")
@authenticated
async def list_badges(request: Request):
    """GET /api/v1/badges -- List badge definitions in scope, plus global badges."""
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
@authenticated
async def create_badge(request: Request):
    """POST /api/v1/badges -- Create a badge definition in `ecosystem_id` (default: the first selected ecosystem).

    Accepts JSON: BadgeDefinitionCreateRequest
    Returns JSON: BadgeDefinitionSchema with 201 status.
    """
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
        admin, refused = await _badge_administrator(session, request, ecosystem_id)
        if refused is not None:
            return refused
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
@authenticated
async def update_badge(request: Request, badge_id: uuid.UUID):
    """PUT /api/v1/badges/:id -- Update non-None fields of a badge definition."""
    body = request.json or {}
    try:
        update_req = BadgeDefinitionUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        badge = await _visible_badge(session, request, badge_id)
        if badge is None:
            return json({"error": "Badge not found"}, status=404)
        _, refused = await _badge_administrator(session, request, badge.ecosystem_id)
        if refused is not None:
            return refused

        for field, value in update_req.model_dump(exclude_none=True).items():
            setattr(badge, field, value)

        await session.commit()
        await session.refresh(badge)

    return json(_badge_to_schema(badge))


@badges_api_bp.delete("/<badge_id:uuid>")
@authenticated
async def delete_badge(request: Request, badge_id: uuid.UUID):
    """DELETE /api/v1/badges/:id -- Delete a badge definition."""
    async with request.app.ctx.db() as session:
        badge = await _visible_badge(session, request, badge_id)
        if badge is None:
            return json({"error": "Badge not found"}, status=404)
        _, refused = await _badge_administrator(session, request, badge.ecosystem_id)
        if refused is not None:
            return refused

        await session.delete(badge)
        await session.commit()

    return json({"success": True})
