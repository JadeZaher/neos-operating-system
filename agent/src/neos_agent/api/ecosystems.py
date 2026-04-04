"""JSON API blueprint for ecosystem management.

Blueprint: ecosystems_api_bp, url_prefix="/api/v1/ecosystems"

All endpoints require authentication via the neos_session cookie.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import Ecosystem, Member

from .schemas import (
    EcosystemCreateRequest,
    EcosystemDetail,
    EcosystemSummary,
    EcosystemUpdateRequest,
)

logger = logging.getLogger(__name__)

ecosystems_api_bp = Blueprint("ecosystems_api", url_prefix="/api/v1/ecosystems")


# --- Helpers ---


async def _get_member_ecosystem_ids(db, did: str) -> list[uuid.UUID]:
    """Return all ecosystem_ids for a given DID."""
    result = await db.execute(
        select(Member.ecosystem_id).where(Member.did == did)
    )
    return list(result.scalars().all())


async def _get_member_count(db, ecosystem_id: uuid.UUID) -> int:
    """Return the number of members in an ecosystem."""
    result = await db.execute(
        select(func.count(Member.id)).where(Member.ecosystem_id == ecosystem_id)
    )
    return result.scalar() or 0


def _ecosystem_to_summary(eco: Ecosystem, count: int) -> EcosystemSummary:
    """Convert an Ecosystem ORM instance to an EcosystemSummary schema."""
    return EcosystemSummary(
        id=eco.id,
        name=eco.name,
        description=eco.description,
        status=eco.status,
        logo_url=eco.logo_url,
        location=eco.location,
        member_count=count,
    )


def _ecosystem_to_detail(eco: Ecosystem, count: int) -> EcosystemDetail:
    """Convert an Ecosystem ORM instance to an EcosystemDetail schema."""
    tags = eco.tags if isinstance(eco.tags, list) else None
    return EcosystemDetail(
        id=eco.id,
        name=eco.name,
        description=eco.description,
        status=eco.status,
        logo_url=eco.logo_url,
        location=eco.location,
        member_count=count,
        website=eco.website,
        founded_date=eco.founded_date,
        tags=tags,
        contact_email=eco.contact_email,
        governance_summary=eco.governance_summary,
        visibility=eco.visibility,
    )


def _require_auth(request: Request):
    """Return the authenticated member or None with a 401 response."""
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


# --- Endpoints ---


@ecosystems_api_bp.get("/")
async def list_ecosystems(request: Request):
    """List ecosystems the authenticated member belongs to.

    Optional query params: ?status=, ?q= (search name/description)
    Returns JSON: {"ecosystems": [...], "total": N}
    """
    member, err = _require_auth(request)
    if err:
        return err

    status_filter = request.args.get("status")
    search_query = request.args.get("q")

    async with request.app.ctx.db() as db:
        eco_ids = await _get_member_ecosystem_ids(db, member.did)
        if not eco_ids:
            return json({"ecosystems": [], "total": 0})

        query = select(Ecosystem).where(Ecosystem.id.in_(eco_ids))

        if status_filter:
            query = query.where(Ecosystem.status == status_filter)

        if search_query:
            pattern = f"%{search_query}%"
            query = query.where(
                Ecosystem.name.ilike(pattern) | Ecosystem.description.ilike(pattern)
            )

        result = await db.execute(query)
        ecosystems = list(result.scalars().all())

        summaries = []
        for eco in ecosystems:
            count = await _get_member_count(db, eco.id)
            summaries.append(_ecosystem_to_summary(eco, count))

    return json({
        "ecosystems": [s.model_dump(mode="json") for s in summaries],
        "total": len(summaries),
    })


@ecosystems_api_bp.get("/<ecosystem_id:uuid>")
async def get_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Return detail for a specific ecosystem.

    Verifies the member belongs to this ecosystem or it is public.
    Returns JSON: EcosystemDetail
    """
    member, err = _require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        # Check access: member belongs to ecosystem or it's public
        eco_ids = await _get_member_ecosystem_ids(db, member.did)
        if ecosystem_id not in eco_ids and eco.visibility != "public":
            return json({"error": "Access denied"}, status=403)

        count = await _get_member_count(db, eco.id)
        detail = _ecosystem_to_detail(eco, count)

    return json(detail.model_dump(mode="json"))


@ecosystems_api_bp.post("/")
async def create_ecosystem(request: Request):
    """Create a new ecosystem and add the current member to it.

    Accepts JSON: EcosystemCreateRequest
    Returns JSON: EcosystemDetail with 201 status.
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = EcosystemCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    # Sanitize website URL
    website = create_req.website
    if website and not website.startswith("https://"):
        if website.startswith("http://"):
            website = "https://" + website[7:]
        elif not website.startswith("https://"):
            website = "https://" + website

    async with request.app.ctx.db() as db:
        eco = Ecosystem(
            id=uuid.uuid4(),
            name=create_req.name,
            description=create_req.description,
            status="active",
            location=create_req.location,
            website=website,
            logo_url=create_req.logo_url,
            founded_date=create_req.founded_date,
            tags=create_req.tags,
            contact_email=create_req.contact_email,
            governance_summary=create_req.governance_summary,
            visibility=create_req.visibility,
        )
        db.add(eco)
        await db.flush()

        # Add the creating member to this ecosystem
        new_member = Member(
            ecosystem_id=eco.id,
            member_id=f"did-{member.did[-12:]}",
            did=member.did,
            display_name=member.display_name,
            current_status="active",
        )
        db.add(new_member)
        await db.commit()

        detail = _ecosystem_to_detail(eco, 1)

    return json(detail.model_dump(mode="json"), status=201)


@ecosystems_api_bp.put("/<ecosystem_id:uuid>")
async def update_ecosystem(request: Request, ecosystem_id: uuid.UUID):
    """Update an existing ecosystem.

    Verifies the member belongs to this ecosystem.
    Accepts JSON: EcosystemUpdateRequest
    Returns JSON: EcosystemDetail
    """
    member, err = _require_auth(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = EcosystemUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as db:
        eco = await db.get(Ecosystem, ecosystem_id)
        if eco is None:
            return json({"error": "Ecosystem not found"}, status=404)

        # Verify membership
        eco_ids = await _get_member_ecosystem_ids(db, member.did)
        if ecosystem_id not in eco_ids:
            return json({"error": "Access denied"}, status=403)

        # Update fields that are not None
        update_data = update_req.model_dump(exclude_none=True)
        for field, value in update_data.items():
            # Sanitize website URL
            if field == "website" and value and not value.startswith("https://"):
                if value.startswith("http://"):
                    value = "https://" + value[7:]
                else:
                    value = "https://" + value
            setattr(eco, field, value)

        await db.commit()
        await db.refresh(eco)

        count = await _get_member_count(db, eco.id)
        detail = _ecosystem_to_detail(eco, count)

    return json(detail.model_dump(mode="json"))
