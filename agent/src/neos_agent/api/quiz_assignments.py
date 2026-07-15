"""JSON API blueprint for quiz assignment management.

Blueprint: quiz_assignments_api_bp, url_prefix="/api/v1/quiz-assignments"

Manages quizzes assigned to individual members (distinct from
quiz↔domain/quiz↔ecosystem assignment on the Quiz model itself).
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from neos_agent.db.models import Member, QuizAssignment
from neos_agent.db.course_models import Quiz
from neos_agent.api.helpers import require_auth, require_admin, get_ecosystem_ids, apply_ecosystem_filter
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@quiz_assignments_api_bp.get("/")
async def list_quiz_assignments(request: Request):
    """GET /api/v1/quiz-assignments -- List quiz assignments.

    Query params: member_id (filter to a single member's assignments).
    """
    member, err = require_auth(request)
    if err:
        return err

    eco_ids = get_ecosystem_ids(request)

    async with request.app.ctx.db() as session:
        stmt = (
            select(QuizAssignment, Quiz.title, Member.display_name)
            .outerjoin(Quiz, QuizAssignment.quiz_id == Quiz.id)
            .outerjoin(Member, QuizAssignment.member_id == Member.id)
            .order_by(QuizAssignment.created_at.desc())
        )

        if eco_ids:
            stmt = apply_ecosystem_filter(stmt, QuizAssignment, eco_ids)

        member_id = request.args.get("member_id")
        if member_id:
            try:
                stmt = stmt.where(QuizAssignment.member_id == uuid.UUID(member_id))
            except ValueError:
                return json({"error": "Invalid member_id"}, status=400)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        rows = (await session.execute(stmt)).all()

    items = [_row_to_schema(qa, quiz_title, member_name) for qa, quiz_title, member_name in rows]

    return json({"items": items, "total": total})


@quiz_assignments_api_bp.post("/")
async def create_quiz_assignment(request: Request):
    """POST /api/v1/quiz-assignments -- Assign a quiz to a member.

    Accepts JSON: QuizAssignmentCreateRequest
    Returns JSON: QuizAssignmentSchema with 201 status.
    """
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        create_req = QuizAssignmentCreateRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        quiz = await session.get(Quiz, create_req.quiz_id)
        if quiz is None:
            return json({"error": "Quiz not found"}, status=404)

        target_member = await session.get(Member, create_req.member_id)
        if target_member is None:
            return json({"error": "Member not found"}, status=404)

        assignment = QuizAssignment(
            id=uuid.uuid4(),
            quiz_id=create_req.quiz_id,
            member_id=create_req.member_id,
            ecosystem_id=target_member.ecosystem_id,
            assigned_by=admin.id,
            due_date=create_req.due_date,
        )
        session.add(assignment)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return json({"error": "That quiz is already assigned to this member"}, status=409)

        await session.refresh(assignment)

    return json(
        _row_to_schema(assignment, quiz.title, target_member.display_name),
        status=201,
    )


@quiz_assignments_api_bp.delete("/<assignment_id:uuid>")
async def delete_quiz_assignment(request: Request, assignment_id: uuid.UUID):
    """DELETE /api/v1/quiz-assignments/:id -- Remove a quiz assignment."""
    admin, err = require_admin(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        assignment = await session.get(QuizAssignment, assignment_id)
        if assignment is None:
            return json({"error": "Quiz assignment not found"}, status=404)

        await session.delete(assignment)
        await session.commit()

    return json({"success": True})
