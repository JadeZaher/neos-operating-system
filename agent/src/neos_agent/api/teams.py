"""JSON API blueprint for team management.

Blueprint: teams_api_bp, url_prefix="/api/v1/teams"

Manages ecosystem-scoped teams and their memberships. A team belongs to one
ecosystem, so every change is authorized by the caller's row there
(policy.can_administer_ecosystem), never by a platform-wide profile; see
api/AGENTS.md "Platform admin (G-Authority)".
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select

from neos_agent.db.models import Member, Team, TeamMembership
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import get_ecosystem_ids
from neos_agent.api.policy import can_administer_ecosystem
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.api.schemas.teams import (
    TeamCreateRequest,
    TeamMemberAddRequest,
    TeamMemberSchema,
    TeamSchema,
    TeamUpdateRequest,
)

logger = logging.getLogger(__name__)

TEAM_MANAGE_DENIED = "Only a steward or administrator of this ecosystem can change its teams"


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


async def _team_administrator(session, request: Request, ecosystem_id: uuid.UUID) -> Member:
    """The caller's row in `ecosystem_id` when it may change that ecosystem's teams, else ApiError 403."""
    caller = await caller_in(session, request, ecosystem_id)
    if not can_administer_ecosystem(caller, ecosystem_id):
        raise ApiError(403, TEAM_MANAGE_DENIED)
    return caller


async def _managed_team(session, request: Request, team_id: uuid.UUID) -> tuple[Team, Member]:
    """A team in the caller's ecosystems (404 otherwise) and the caller's administering row there (403 otherwise)."""
    team = await get_scoped_or_404(session, request, Team, team_id, label="Team")
    return team, await _team_administrator(session, request, team.ecosystem_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@teams_api_bp.get("/")
@authenticated
async def list_teams(request: Request):
    """GET /api/v1/teams -- List teams in scope with member counts."""
    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = restrict_to_ecosystems(select(Team).order_by(Team.name), Team, eco_ids)

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

        items = []
        for team in teams:
            caller = await caller_in(session, request, team.ecosystem_id)
            joined = caller is not None and await session.scalar(select(TeamMembership.id).where(
                TeamMembership.team_id == team.id, TeamMembership.member_id == caller.id).limit(1)) is not None
            items.append({**_team_to_schema(team, counts.get(team.id, 0)), "caller_is_member": joined,
                          "caller_can_manage": can_administer_ecosystem(caller, team.ecosystem_id)})
    return json({
        "items": items,
        "total": len(teams),
    })


@teams_api_bp.get("/<team_id:uuid>")
@authenticated
async def get_team(request: Request, team_id: uuid.UUID):
    async with request.app.ctx.db() as session:
        team = await get_scoped_or_404(session, request, Team, team_id, label="Team")
        caller = await caller_in(session, request, team.ecosystem_id)
        joined = caller is not None and await session.scalar(select(TeamMembership.id).where(
            TeamMembership.team_id == team.id, TeamMembership.member_id == caller.id).limit(1)) is not None
        count = await session.scalar(select(func.count(TeamMembership.id)).where(TeamMembership.team_id == team.id)) or 0
        return json({**_team_to_schema(team, count), "caller_is_member": joined,
                     "caller_can_manage": can_administer_ecosystem(caller, team.ecosystem_id)})


@teams_api_bp.post("/<team_id:uuid>/join")
@authenticated
async def join_team(request: Request, team_id: uuid.UUID):
    from neos_agent.services.join_gates import join_gate_summary, require_join_gates
    if request.json and set(request.json):
        raise ApiError(400, "Team self-join takes no member or role fields")
    async with request.app.ctx.db() as session:
        team = await get_scoped_or_404(session, request, Team, team_id, label="Team")
        if not team.is_active:
            raise ApiError(409, "This team is not accepting participation")
        caller = await caller_in(session, request, team.ecosystem_id)
        if caller is None or caller.current_status != "active":
            raise ApiError(403, "Active ecosystem membership is required for team participation")
        existing = await session.scalar(select(TeamMembership).where(
            TeamMembership.team_id == team.id, TeamMembership.member_id == caller.id))
        gates = await join_gate_summary(session, ecosystem_id=team.ecosystem_id, member=caller, team=team)
        if existing is None:
            require_join_gates(gates)
            from neos_agent.services.join_gates import record_quiz_bypass
            await record_quiz_bypass(session, caller, gates)
            session.add(TeamMembership(team_id=team.id, member_id=caller.id, role="member"))
            from neos_agent.services.engagement_events import source_event
            await source_event(session, team, kind="team", family="community", action="participation_changed", actor_user_id=caller.user_id)
            await session.commit()
        else:
            gates.update(eligible=True, status="ready", grandfathered=True)
        return json({"status": "joined", "team_id": str(team.id), "member_id": str(caller.id), "join_gates": gates}, status=201)


@teams_api_bp.post("/")
@authenticated
async def create_team(request: Request):
    """POST /api/v1/teams -- Create a team in `ecosystem_id` (default: the first selected ecosystem).

    Accepts JSON: TeamCreateRequest
    Returns JSON: TeamSchema with 201 status.
    """
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
        caller = await _team_administrator(session, request, ecosystem_id)
        team = Team(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            name=create_req.name,
            description=create_req.description,
            created_by=caller.id,
        )
        session.add(team)
        await session.commit()
        await session.refresh(team)

    return json(_team_to_schema(team), status=201)


@teams_api_bp.put("/<team_id:uuid>")
@authenticated
async def update_team(request: Request, team_id: uuid.UUID):
    """PUT /api/v1/teams/:id -- Update non-None fields of a team."""
    body = request.json or {}
    try:
        update_req = TeamUpdateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        team, _ = await _managed_team(session, request, team_id)

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
@authenticated
async def delete_team(request: Request, team_id: uuid.UUID):
    """DELETE /api/v1/teams/:id -- Delete a team and its memberships."""
    async with request.app.ctx.db() as session:
        team, _ = await _managed_team(session, request, team_id)

        memberships = (
            await session.execute(
                select(TeamMembership).where(TeamMembership.team_id == team_id)
            )
        ).scalars().all()
        for tm in memberships:
            await session.delete(tm)
        from neos_agent.db.course_models import Quiz
        for quiz in (await session.scalars(select(Quiz).where(Quiz.team_id == team_id))).all():
            quiz.team_id = None
            quiz.is_entry_quiz = False

        await session.delete(team)
        await session.commit()

    return json({"success": True})


@teams_api_bp.get("/<team_id:uuid>/members")
@authenticated
async def list_team_members(request: Request, team_id: uuid.UUID):
    """GET /api/v1/teams/:id/members -- List a team's memberships (a team outside your ecosystems is 404)."""
    async with request.app.ctx.db() as session:
        await get_scoped_or_404(session, request, Team, team_id, label="Team")
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
@authenticated
async def add_team_member(request: Request, team_id: uuid.UUID):
    """POST /api/v1/teams/:id/members -- Add a member of the team's ecosystem to the team.

    Accepts JSON: TeamMemberAddRequest
    Returns JSON: TeamMemberSchema with 201 status. Idempotent if already a member.
    """
    body = request.json or {}
    try:
        add_req = TeamMemberAddRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        team, administrator = await _managed_team(session, request, team_id)

        member = await session.get(Member, add_req.member_id)
        if member is None or member.ecosystem_id != team.ecosystem_id:
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

        if member.current_status != "active":
            raise ApiError(403, "Active ecosystem membership is required for team participation")
        from neos_agent.services.join_gates import join_gate_summary, require_join_gates
        gates = await join_gate_summary(session, ecosystem_id=team.ecosystem_id, member=member, team=team)
        require_join_gates(gates)
        from neos_agent.services.join_gates import record_quiz_bypass
        await record_quiz_bypass(session, member, gates, actor_user_id=administrator.user_id)

        tm = TeamMembership(
            id=uuid.uuid4(),
            team_id=team_id,
            member_id=add_req.member_id,
            role=add_req.role or "member",
        )
        session.add(tm)
        from neos_agent.services.engagement_events import source_event
        await source_event(session, team, kind="team", family="community", action="participation_changed", actor_user_id=administrator.user_id)
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
@authenticated
async def remove_team_member(request: Request, team_id: uuid.UUID, member_id: uuid.UUID):
    """DELETE /api/v1/teams/:id/members/:member_id -- Remove a member from a team."""
    async with request.app.ctx.db() as session:
        team, administrator = await _managed_team(session, request, team_id)
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
        from neos_agent.services.engagement_events import source_event
        await source_event(session, team, kind="team", family="community", action="participation_changed", actor_user_id=administrator.user_id)
        await session.commit()

    return json({"success": True})


@teams_api_bp.get("/<team_id:uuid>/join-gates")
@authenticated
async def team_join_gates(request: Request, team_id: uuid.UUID):
    from neos_agent.services.join_gates import join_gate_summary
    async with request.app.ctx.db() as session:
        team = await get_scoped_or_404(session, request, Team, team_id, label="Team")
        member = await caller_in(session, request, team.ecosystem_id)
        return json({"join_gates": await join_gate_summary(session, ecosystem_id=team.ecosystem_id, member=member, team=team)})


@teams_api_bp.get("/<team_id:uuid>/quizzes")
@authenticated
async def list_team_quizzes(request: Request, team_id: uuid.UUID):
    from neos_agent.db.course_models import Quiz
    from neos_agent.api.quizzes import _quiz_to_list_item
    async with request.app.ctx.db() as session:
        team = await get_scoped_or_404(session, request, Team, team_id, label="Team")
        member = await caller_in(session, request, team.ecosystem_id)
        from neos_agent.api.policy import can_manage_onboarding
        stmt = select(Quiz).where(Quiz.team_id == team.id)
        if not can_manage_onboarding(member, team.ecosystem_id):
            stmt = stmt.where(Quiz.is_published.is_(True))
        quizzes = (await session.scalars(stmt.order_by(Quiz.created_at))).all()
        return json({"quizzes": [_quiz_to_list_item(quiz) for quiz in quizzes]})


@teams_api_bp.post("/<team_id:uuid>/quizzes/assign")
@authenticated
async def assign_team_quiz(request: Request, team_id: uuid.UUID):
    from neos_agent.db.course_models import Quiz
    from neos_agent.api.quizzes import copy_quiz, quiz_steward_or_error
    body = request.json or {}
    try:
        quiz_id = uuid.UUID(str(body.get("quiz_id")))
    except (TypeError, ValueError):
        raise ApiError(400, "Invalid quiz_id") from None
    if not isinstance(body.get("is_entry_quiz", False), bool):
        raise ApiError(400, "is_entry_quiz must be true or false")
    async with request.app.ctx.db() as session:
        team = await get_scoped_or_404(session, request, Team, team_id, label="Team")
        steward = await quiz_steward_or_error(session, request, team.ecosystem_id)
        quiz = await session.get(Quiz, quiz_id, with_for_update=True)
        if quiz is None:
            raise ApiError(404, "Quiz not found")
        if quiz.ecosystem_id not in (None, team.ecosystem_id):
            raise ApiError(403, "That quiz belongs to another ecosystem")
        if quiz.ecosystem_id is None:
            quiz = copy_quiz(quiz, ecosystem_id=team.ecosystem_id, domain_id=None, created_by=steward.id)
            session.add(quiz)
        quiz.domain_id = None
        quiz.team_id = team.id
        quiz.is_entry_quiz = body.get("is_entry_quiz", False)
        await session.commit()
        return json({"success": True, "quiz_id": str(quiz.id), "team_id": str(team.id)})


@teams_api_bp.post("/<team_id:uuid>/quizzes/unassign")
@authenticated
async def unassign_team_quiz(request: Request, team_id: uuid.UUID):
    from neos_agent.db.course_models import Quiz
    from neos_agent.api.quizzes import quiz_steward_or_error
    try:
        quiz_id = uuid.UUID(str((request.json or {}).get("quiz_id")))
    except (TypeError, ValueError):
        raise ApiError(400, "Invalid quiz_id") from None
    async with request.app.ctx.db() as session:
        team = await get_scoped_or_404(session, request, Team, team_id, label="Team")
        await quiz_steward_or_error(session, request, team.ecosystem_id)
        quiz = await session.get(Quiz, quiz_id, with_for_update=True)
        if quiz is None or quiz.team_id != team.id:
            raise ApiError(404, "Quiz not found in this team")
        quiz.team_id = None
        quiz.is_entry_quiz = False
        await session.commit()
        return json({"success": True, "quiz_id": str(quiz.id)})
