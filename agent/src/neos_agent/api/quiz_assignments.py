"""JSON API blueprint for quiz assignment management.

Blueprint: quiz_assignments_api_bp, url_prefix="/api/v1/quiz-assignments"

Manages quizzes assigned to individual members (distinct from
quiz↔domain/quiz↔ecosystem assignment on the Quiz model itself).
Stewards of the member's ecosystem assign (policy.can_manage_onboarding); members see their
own; see api/AGENTS.md "Onboarding (G-Onboard)".
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

from neos_agent.db.models import Member, QuizAssignment
from neos_agent.db.course_models import Quiz
from neos_agent.api.errors import ApiError
from neos_agent.api.guards import authenticated, caller_in, caller_user_id
from neos_agent.api.helpers import get_ecosystem_ids
from neos_agent.api.policy import can_manage_onboarding
from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems
from neos_agent.api.schemas.quiz_assignments import (
    QuizAssignmentCreateRequest,
    QuizAssignmentSchema,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

quiz_assignments_api_bp = Blueprint("quiz_assignments_api", url_prefix="/api/v1/quiz-assignments")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _row_to_schema(qa: QuizAssignment, quiz_title: str | None, member_name: str | None) -> dict:
    return QuizAssignmentSchema(
        id=qa.id,
        quiz_id=qa.quiz_id,
        quiz_title=quiz_title,
        member_id=qa.member_id,
        member_name=member_name,
        ecosystem_id=qa.ecosystem_id,
        assigned_by=qa.assigned_by,
        due_date=qa.due_date,
        status=qa.status,
        created_at=qa.created_at,
    ).model_dump(mode="json")


QUIZ_STEWARDS_ONLY = "Only an active steward of this member's ecosystem can assign or remove their quizzes"
QUIZ_OTHER_ECOSYSTEM = "That quiz belongs to another ecosystem"


async def _steward_of(session, request: Request, ecosystem_id) -> Member:
    """The caller's row when they may manage this ecosystem's onboarding (policy.can_manage_onboarding), else 403."""
    caller = await caller_in(session, request, ecosystem_id)
    if not can_manage_onboarding(caller, ecosystem_id):
        raise ApiError(403, QUIZ_STEWARDS_ONLY)
    return caller


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@quiz_assignments_api_bp.get("/")
@authenticated
async def list_quiz_assignments(request: Request):
    """GET /api/v1/quiz-assignments -- Assignments in the selected ecosystems: all of them where the caller is a
    steward, only their own elsewhere. Query params: member_id (narrow to one member)."""
    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        own_rows = list((await session.scalars(
            select(Member.id).where(Member.user_id == caller_user_id(request))
        )).all())
        stewarded = []
        for ecosystem_id in eco_ids:
            if can_manage_onboarding(await caller_in(session, request, ecosystem_id), ecosystem_id):
                stewarded.append(ecosystem_id)
        stmt = (
            select(QuizAssignment, Quiz.title, Member.display_name)
            .outerjoin(Quiz, QuizAssignment.quiz_id == Quiz.id)
            .outerjoin(Member, QuizAssignment.member_id == Member.id)
            .order_by(QuizAssignment.created_at.desc())
        )
        stmt = restrict_to_ecosystems(stmt, QuizAssignment, eco_ids)  # an empty selection matches nothing
        stmt = stmt.where(or_(QuizAssignment.ecosystem_id.in_(stewarded), QuizAssignment.member_id.in_(own_rows)))

        member_id = request.args.get("member_id")
        if member_id:
            try:
                stmt = stmt.where(QuizAssignment.member_id == uuid.UUID(member_id))
            except ValueError:
                raise ApiError(400, "Invalid member_id") from None

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        rows = (await session.execute(stmt)).all()

    items = [_row_to_schema(qa, quiz_title, member_name) for qa, quiz_title, member_name in rows]

    return json({"items": items, "total": total})


@quiz_assignments_api_bp.post("/")
@authenticated
async def create_quiz_assignment(request: Request):
    """POST /api/v1/quiz-assignments -- A steward of the member's ecosystem assigns them one of its quizzes (or a
    quiz of no ecosystem); `assigned_by` is the steward's row there."""
    body = request.json or {}
    try:
        create_req = QuizAssignmentCreateRequest(**body)
    except Exception as e:
        raise ApiError(400, f"Invalid request: {e}") from None

    async with request.app.ctx.db() as session:
        target_member = await session.get(Member, create_req.member_id)
        if target_member is None:
            raise ApiError(404, "Member not found")
        steward = await _steward_of(session, request, target_member.ecosystem_id)

        quiz = await session.get(Quiz, create_req.quiz_id)
        if quiz is None:
            raise ApiError(404, "Quiz not found")
        if quiz.ecosystem_id not in (None, target_member.ecosystem_id):
            raise ApiError(403, QUIZ_OTHER_ECOSYSTEM)

        assignment = QuizAssignment(
            id=uuid.uuid4(),
            quiz_id=create_req.quiz_id,
            member_id=create_req.member_id,
            ecosystem_id=target_member.ecosystem_id,
            assigned_by=steward.id,
            due_date=create_req.due_date,
        )
        session.add(assignment)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            raise ApiError(409, "That quiz is already assigned to this member") from None

        await session.refresh(assignment)

    return json(
        _row_to_schema(assignment, quiz.title, target_member.display_name),
        status=201,
    )


@quiz_assignments_api_bp.delete("/<assignment_id:uuid>")
@authenticated
async def delete_quiz_assignment(request: Request, assignment_id: uuid.UUID):
    """DELETE /api/v1/quiz-assignments/:id -- A steward of the assignment's ecosystem removes it."""
    async with request.app.ctx.db() as session:
        assignment = await session.get(QuizAssignment, assignment_id)
        if assignment is None:
            raise ApiError(404, "Quiz assignment not found")
        await _steward_of(session, request, assignment.ecosystem_id)

        await session.delete(assignment)
        await session.commit()

    return json({"success": True})
