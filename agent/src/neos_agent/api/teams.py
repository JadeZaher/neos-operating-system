"""JSON API blueprint for team management.

Blueprint: teams_api_bp, url_prefix="/api/v1/teams"

Manages ecosystem-scoped teams and their memberships.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import Member, Team, TeamMembership
from neos_agent.api.helpers import require_auth, require_admin, get_ecosystem_ids
from neos_agent.api.schemas.teams import (
    TeamCreateRequest,
    TeamMemberAddRequest,
    TeamMemberSchema,
    TeamSchema,
    TeamUpdateRequest,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

teams_api_bp = Blueprint("teams_api", url_prefix="/api/v1/teams")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _team_to_schema(t: Team, member_count: int = 0) -> dict:
    return TeamSchema(
        id=t.id,
        ecosystem_id=t.ecosystem_id,
        name=t.name,
        description=t.description,
        is_active=t.is_active,
        created_by=t.created_by,
        created_at=t.created_at,
        updated_at=t.updated_at,
        member_count=member_count,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@teams_api_bp.get("/")
async def list_teams(request: Request):
    """GET /api/v1/teams -- List teams in scope with member counts."""
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = select(Team).order_by(Team.name)
        if eco_ids:
            stmt = stmt.where(Team.ecosystem_id.in_(eco_ids))

        result = await session.execute(stmt)
        teams = result.scalars().all()

        counts: dict[uuid.UUID, int] = {}
        if teams:
            count_stmt = (
                select(TeamMembership.team_id, func.count(TeamMembership.id))
                .where(TeamMembership.team_id.in_([t.id for t in teams]))
                .group_by(TeamMembership.team_id)
            )
            count_rows = await session.execute(count_stmt)
            counts = dict(count_rows.all())

    return json({
        "items": [_team_to_schema(t, counts.get(t.id, 0)) for t in teams],
        "total": len(teams),
    })


@teams_api_bp.post("/")
async def create_team(request: Request):
    """POST /api/v1/teams -- Create a new team.

    Accepts JSON: TeamCreateRequest
    Returns JSON: TeamSchema with 201 status.
    """
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = TeamCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    ecosystem_id = create_req.ecosystem_id
    if ecosystem_id is None:
        eco_ids = get_ecosystem_ids(request)
        if not eco_ids:
            return json({"error": "No ecosystem in scope"}, status=400)
        ecosystem_id = eco_ids[0]

    async with request.app.ctx.db() as session:
        team = Team(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            name=create_req.name,
            description=create_req.description,
            created_by=admin.id,
        )
        session.add(team)
        await session.commit()
        await session.refresh(team)

    return json(_team_to_schema(team), status=201)


@teams_api_bp.put("/<team_id:uuid>")
async def update_team(request: Request, team_id: uuid.UUID):
    """PUT /api/v1/teams/:id -- Update non-None fields of a team."""
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        update_req = TeamUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        team = await session.get(Team, team_id)
        if team is None:
            return json({"error": "Team not found"}, status=404)

        for field, value in update_req.model_dump(exclude_none=True).items():
            setattr(team, field, value)

        await session.commit()
        await session.refresh(team)

        count_stmt = select(func.count(TeamMembership.id)).where(
            TeamMembership.team_id == team.id
        )
        member_count = await session.scalar(count_stmt) or 0

    return json(_team_to_schema(team, member_count))


@teams_api_bp.delete("/<team_id:uuid>")
async def delete_team(request: Request, team_id: uuid.UUID):
    """DELETE /api/v1/teams/:id -- Delete a team and its memberships."""
    admin, err = require_admin(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        team = await session.get(Team, team_id)
        if team is None:
            return json({"error": "Team not found"}, status=404)

        memberships = (
            await session.execute(
                select(TeamMembership).where(TeamMembership.team_id == team_id)
            )
        ).scalars().all()
        for tm in memberships:
            await session.delete(tm)

        await session.delete(team)
        await session.commit()

    return json({"success": True})


@teams_api_bp.get("/<team_id:uuid>/members")
async def list_team_members(request: Request, team_id: uuid.UUID):
    """GET /api/v1/teams/:id/members -- List a team's memberships."""
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        stmt = (
            select(TeamMembership, Member.display_name)
            .join(Member, Member.id == TeamMembership.member_id)
            .where(TeamMembership.team_id == team_id)
            .order_by(TeamMembership.created_at)
        )
        rows = (await session.execute(stmt)).all()

    items = [
        TeamMemberSchema(
            id=tm.id,
            team_id=tm.team_id,
            member_id=tm.member_id,
            member_name=display_name,
            role=tm.role,
            created_at=tm.created_at,
        ).model_dump(mode="json")
        for tm, display_name in rows
    ]

    return json({"items": items, "total": len(items)})


@teams_api_bp.post("/<team_id:uuid>/members")
async def add_team_member(request: Request, team_id: uuid.UUID):
    """POST /api/v1/teams/:id/members -- Add a member to a team.

    Accepts JSON: TeamMemberAddRequest
    Returns JSON: TeamMemberSchema with 201 status. Idempotent if already a member.
    """
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        add_req = TeamMemberAddRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        team = await session.get(Team, team_id)
        if team is None:
            return json({"error": "Team not found"}, status=404)

        member = await session.get(Member, add_req.member_id)
        if member is None:
            return json({"error": "Member not found"}, status=404)

        existing = (
            await session.execute(
                select(TeamMembership).where(
                    TeamMembership.team_id == team_id,
                    TeamMembership.member_id == add_req.member_id,
                )
            )
        ).scalar_one_or_none()

        if existing is not None:
            return json(
                TeamMemberSchema(
                    id=existing.id,
                    team_id=existing.team_id,
                    member_id=existing.member_id,
                    member_name=member.display_name,
                    role=existing.role,
                    created_at=existing.created_at,
                ).model_dump(mode="json"),
                status=201,
            )

        tm = TeamMembership(
            id=uuid.uuid4(),
            team_id=team_id,
            member_id=add_req.member_id,
            role=add_req.role or "member",
        )
        session.add(tm)
        await session.commit()
        await session.refresh(tm)

    return json(
        TeamMemberSchema(
            id=tm.id,
            team_id=tm.team_id,
            member_id=tm.member_id,
            member_name=member.display_name,
            role=tm.role,
            created_at=tm.created_at,
        ).model_dump(mode="json"),
        status=201,
    )


@teams_api_bp.delete("/<team_id:uuid>/members/<member_id:uuid>")
async def remove_team_member(request: Request, team_id: uuid.UUID, member_id: uuid.UUID):
    """DELETE /api/v1/teams/:id/members/:member_id -- Remove a member from a team."""
    admin, err = require_admin(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        tm = (
            await session.execute(
                select(TeamMembership).where(
                    TeamMembership.team_id == team_id,
                    TeamMembership.member_id == member_id,
                )
            )
        ).scalar_one_or_none()
        if tm is None:
            return json({"error": "Team membership not found"}, status=404)

        await session.delete(tm)
        await session.commit()

    return json({"success": True})
