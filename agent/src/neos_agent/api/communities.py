"""Explicit public-active community previews with minimal public opportunity fields."""
from __future__ import annotations

import uuid
from urllib.parse import urlsplit

from sanic import Blueprint, json
from sqlalchemy import func, or_, select

from neos_agent.api.engagement import page_limit
from neos_agent.api.errors import ApiError
from neos_agent.db.models import Ecosystem, Member, SharesNeeds
from neos_agent.services.engagement import after_cursor, cursor_for
from neos_agent.services.exchange import OPEN, load_viewer, visible_clause
from neos_agent.services.member_lifecycle import counts_as_member
from neos_agent.services.member_messaging import owner_contact

communities_api_bp = Blueprint("communities_api", url_prefix="/api/v1/communities")


def community_payload(row, member_count):
    logo = row.logo_url or ""
    try:
        parsed = urlsplit(logo)
    except ValueError:
        logo, parsed = "", urlsplit("")
    safe_logo = logo if "\\" not in logo and ((logo.startswith("/") and not logo.startswith("//")) or
        (parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password)) else None
    return {"id": str(row.id), "name": row.name, "description": (row.description or "")[:2000],
            "tags": [value for value in (row.tags or []) if isinstance(value, str)][:20] if isinstance(row.tags, list) else [],
            "location": row.location, "logo_url": safe_logo,
            "preview_url": "/communities/" + str(row.id), "join_url": "/ethos/" + str(row.id),
            "member_count": member_count}


async def _active_member_counts(session, ecosystem_ids):
    """Active members per ecosystem. The public preview returns this count and no member identities."""
    if not ecosystem_ids:
        return {}
    rows = await session.execute(select(Member.ecosystem_id, func.count(Member.id)).where(
        Member.ecosystem_id.in_(ecosystem_ids), counts_as_member()).group_by(Member.ecosystem_id))
    return {ecosystem_id: count for ecosystem_id, count in rows.all()}


@communities_api_bp.get("")
async def list_communities(request):
    limit = page_limit(request)
    query = request.args.get("q", "").strip()[:100]
    statement = select(Ecosystem).where(Ecosystem.visibility == "public", Ecosystem.status == "active")
    if query:
        safe = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(or_(Ecosystem.name.ilike("%" + safe + "%", escape="\\"),
                                        Ecosystem.description.ilike("%" + safe + "%", escape="\\")))
    statement = after_cursor(statement, Ecosystem, request.args.get("cursor"))
    async with request.app.ctx.db() as session:
        rows = list((await session.scalars(statement.order_by(Ecosystem.created_at.desc(), Ecosystem.id.desc())
                                           .limit(limit + 1))).all())
        shown = rows[:limit]
        counts = await _active_member_counts(session, [row.id for row in shown])
        return json({"items": [community_payload(row, counts.get(row.id, 0)) for row in shown],
                     "next_cursor": cursor_for(rows[limit - 1]) if len(rows) > limit else None})


@communities_api_bp.get("/<community_id:uuid>")
async def community_detail(request, community_id: uuid.UUID):
    async with request.app.ctx.db() as session:
        row = await session.scalar(select(Ecosystem).where(Ecosystem.id == community_id,
            Ecosystem.visibility == "public", Ecosystem.status == "active"))
        if row is None:
            raise ApiError(404, "Community not found")
        user = getattr(request.ctx, "user", None)
        viewer = await load_viewer(session, user.id if user and user.disabled_at is None else None)
        opportunities = (await session.scalars(select(SharesNeeds).where(
            SharesNeeds.ecosystem_id == row.id, SharesNeeds.visibility == "public",
            SharesNeeds.hidden_at.is_(None), SharesNeeds.status == OPEN, visible_clause(viewer))
            .order_by(SharesNeeds.created_at.desc(), SharesNeeds.id.desc()).limit(5))).all()
        member_count = (await _active_member_counts(session, [row.id])).get(row.id, 0)
        return json({**community_payload(row, member_count), "owner": await owner_contact(session, row.id),
                     "opportunities_require_sign_in": viewer.user_id is None, "opportunities": [
            {"id": str(item.id), "title": item.title, "url": "/discover?post=" + str(item.id)}
            for item in opportunities]})
