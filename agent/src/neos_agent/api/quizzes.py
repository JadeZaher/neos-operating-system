"""JSON API blueprint for quiz management and member profile data.

Blueprint: quizzes_api_bp, url_prefix="/api/v1"

Manages quizzes, quiz submissions, results, member badges, and tags.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from neos_agent.db.course_models import (
    Quiz,
    QuizResult,
    UserBadge,
    UserTag,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class QuizListItem(BaseModel):
    id: uuid.UUID
    course_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    mode: str
    visibility: str
    is_published: bool
    time_limit: Optional[int] = None
    passing_score: Optional[int] = None
    allow_retakes: bool
    created_at: datetime
    updated_at: datetime


class QuizDetail(QuizListItem):
    survey_json: Optional[dict] = None
    created_by: Optional[uuid.UUID] = None


class QuizCreateRequest(BaseModel):
    course_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    mode: str = "standard"
    survey_json: Optional[dict] = None
    time_limit: Optional[int] = None
    passing_score: Optional[int] = None
    allow_retakes: bool = True
    visibility: str = "public"
    is_published: bool = False
    created_by: Optional[uuid.UUID] = None


class QuizUpdateRequest(BaseModel):
    course_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    mode: Optional[str] = None
    survey_json: Optional[dict] = None
    time_limit: Optional[int] = None
    passing_score: Optional[int] = None
    allow_retakes: Optional[bool] = None
    visibility: Optional[str] = None
    is_published: Optional[bool] = None


class QuizSubmitRequest(BaseModel):
    survey_results: Optional[dict] = None
    score: Optional[float] = None
    time_spent: Optional[int] = None
    is_passed: Optional[bool] = None
    result_metadata: Optional[dict] = None


class QuizResultItem(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    member_id: uuid.UUID
    score: Optional[float] = None
    is_passed: Optional[bool] = None
    time_spent: Optional[int] = None
    completed_at: Optional[datetime] = None


class UserTagItem(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    quiz_result_id: Optional[uuid.UUID] = None
    tag_key: str
    tag_value: str
    tag_category: Optional[str] = None
    data_type: Optional[str] = None
    numeric_value: Optional[float] = None


class UserBadgeItem(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    badge_key: str
    badge_name: str
    badge_description: Optional[str] = None
    badge_category: Optional[str] = None
    badge_icon: Optional[str] = None
    strength: Optional[float] = None
    source_tag_keys: Optional[dict] = None
    earned_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

quizzes_api_bp = Blueprint("quizzes_api", url_prefix="/api/v1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_auth(request: Request):
    member = getattr(request.ctx, "member", None)
    if member is None:
        return None, json({"error": "Authentication required"}, status=401)
    return member, None


def _get_ecosystem_ids(request: Request) -> list[uuid.UUID]:
    cookie = request.cookies.get("neos_selected_ecosystems")
    if cookie:
        try:
            ids = json_module.loads(cookie)
            return [uuid.UUID(i) for i in ids if i]
        except (json_module.JSONDecodeError, ValueError):
            pass
    member = getattr(request.ctx, "member", None)
    if member:
        return [member.ecosystem_id]
    return []


def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


def _quiz_to_list_item(q: Quiz) -> dict:
    return QuizListItem(
        id=q.id,
        course_id=q.course_id,
        title=q.title,
        description=q.description,
        mode=q.mode,
        visibility=q.visibility,
        is_published=q.is_published,
        time_limit=q.time_limit,
        passing_score=q.passing_score,
        allow_retakes=q.allow_retakes,
        created_at=q.created_at,
        updated_at=q.updated_at,
    ).model_dump(mode="json")


def _quiz_to_detail(q: Quiz) -> dict:
    return QuizDetail(
        id=q.id,
        course_id=q.course_id,
        title=q.title,
        description=q.description,
        mode=q.mode,
        visibility=q.visibility,
        is_published=q.is_published,
        time_limit=q.time_limit,
        passing_score=q.passing_score,
        allow_retakes=q.allow_retakes,
        created_at=q.created_at,
        updated_at=q.updated_at,
        survey_json=q.survey_json,
        created_by=q.created_by,
    ).model_dump(mode="json")


def _result_to_item(r: QuizResult) -> dict:
    return QuizResultItem(
        id=r.id,
        quiz_id=r.quiz_id,
        member_id=r.member_id,
        score=r.score,
        is_passed=r.is_passed,
        time_spent=r.time_spent,
        completed_at=r.completed_at,
    ).model_dump(mode="json")


def _tag_to_item(t: UserTag) -> dict:
    return UserTagItem(
        id=t.id,
        member_id=t.member_id,
        quiz_result_id=t.quiz_result_id,
        tag_key=t.tag_key,
        tag_value=t.tag_value,
        tag_category=t.tag_category,
        data_type=t.data_type,
        numeric_value=t.numeric_value,
    ).model_dump(mode="json")


def _badge_to_item(b: UserBadge) -> dict:
    return UserBadgeItem(
        id=b.id,
        member_id=b.member_id,
        badge_key=b.badge_key,
        badge_name=b.badge_name,
        badge_description=b.badge_description,
        badge_category=b.badge_category,
        badge_icon=b.badge_icon,
        strength=b.strength,
        source_tag_keys=b.source_tag_keys,
        earned_at=b.earned_at,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Quiz Endpoints
# ---------------------------------------------------------------------------


@quizzes_api_bp.get("/quizzes")
async def list_quizzes(request: Request):
    """GET /api/v1/quizzes -- Paginated quiz list.

    Query params: course_id, visibility, is_published, q (search title),
    page (default 1), per_page (default 25, max 100).
    """
    member, err = _require_auth(request)
    if err:
        return err

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        filters = []

        course_id_str = request.args.get("course_id")
        if course_id_str:
            try:
                filters.append(Quiz.course_id == uuid.UUID(course_id_str))
            except ValueError:
                return json({"error": "Invalid course_id"}, status=400)

        visibility = request.args.get("visibility")
        if visibility:
            filters.append(Quiz.visibility == visibility)

        is_published_str = request.args.get("is_published")
        if is_published_str is not None:
            filters.append(Quiz.is_published == (is_published_str.lower() == "true"))

        search = request.args.get("q")
        if search:
            filters.append(Quiz.title.ilike(f"%{_escape_like(search)}%"))

        count_stmt = select(Quiz.id).where(*filters)
        total_result = await session.execute(count_stmt)
        total = len(total_result.scalars().all())

        stmt = (
            select(Quiz)
            .where(*filters)
            .order_by(Quiz.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        quizzes = result.scalars().all()

    return json({
        "items": [_quiz_to_list_item(q) for q in quizzes],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@quizzes_api_bp.get("/quizzes/<quiz_id:str>")
async def get_quiz(request: Request, quiz_id: str):
    """GET /api/v1/quizzes/:id -- Quiz detail with survey_json."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        qid = uuid.UUID(quiz_id)
    except ValueError:
        return json({"error": "Invalid quiz ID"}, status=400)

    async with request.app.ctx.db() as session:
        result = await session.execute(select(Quiz).where(Quiz.id == qid))
        quiz = result.scalar_one_or_none()

    if quiz is None:
        return json({"error": "Quiz not found"}, status=404)

    return json(_quiz_to_detail(quiz))


@quizzes_api_bp.post("/quizzes")
async def create_quiz(request: Request):
    """POST /api/v1/quizzes -- Create a new quiz."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        body = QuizCreateRequest.model_validate(request.json or {})
    except Exception as e:
        return json({"error": str(e)}, status=400)

    quiz = Quiz(
        id=uuid.uuid4(),
        course_id=body.course_id,
        title=body.title,
        description=body.description,
        mode=body.mode,
        survey_json=body.survey_json,
        time_limit=body.time_limit,
        passing_score=body.passing_score,
        allow_retakes=body.allow_retakes,
        visibility=body.visibility,
        is_published=body.is_published,
        created_by=body.created_by,
    )

    async with request.app.ctx.db() as session:
        session.add(quiz)
        await session.commit()
        await session.refresh(quiz)

    return json(_quiz_to_list_item(quiz), status=201)


@quizzes_api_bp.put("/quizzes/<quiz_id:str>")
async def update_quiz(request: Request, quiz_id: str):
    """PUT /api/v1/quizzes/:id -- Update an existing quiz."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        qid = uuid.UUID(quiz_id)
    except ValueError:
        return json({"error": "Invalid quiz ID"}, status=400)

    try:
        body = QuizUpdateRequest.model_validate(request.json or {})
    except Exception as e:
        return json({"error": str(e)}, status=400)

    async with request.app.ctx.db() as session:
        result = await session.execute(select(Quiz).where(Quiz.id == qid))
        quiz = result.scalar_one_or_none()

        if quiz is None:
            return json({"error": "Quiz not found"}, status=404)

        if body.course_id is not None:
            quiz.course_id = body.course_id
        if body.title is not None:
            quiz.title = body.title
        if body.description is not None:
            quiz.description = body.description
        if body.mode is not None:
            quiz.mode = body.mode
        if body.survey_json is not None:
            quiz.survey_json = body.survey_json
        if body.time_limit is not None:
            quiz.time_limit = body.time_limit
        if body.passing_score is not None:
            quiz.passing_score = body.passing_score
        if body.allow_retakes is not None:
            quiz.allow_retakes = body.allow_retakes
        if body.visibility is not None:
            quiz.visibility = body.visibility
        if body.is_published is not None:
            quiz.is_published = body.is_published

        await session.commit()
        await session.refresh(quiz)

    return json(_quiz_to_list_item(quiz))


@quizzes_api_bp.post("/quizzes/<quiz_id:str>/submit")
async def submit_quiz(request: Request, quiz_id: str):
    """POST /api/v1/quizzes/:id/submit -- Submit a quiz result."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        qid = uuid.UUID(quiz_id)
    except ValueError:
        return json({"error": "Invalid quiz ID"}, status=400)

    try:
        body = QuizSubmitRequest.model_validate(request.json or {})
    except Exception as e:
        return json({"error": str(e)}, status=400)

    async with request.app.ctx.db() as session:
        quiz_result_check = await session.execute(
            select(Quiz.id).where(Quiz.id == qid)
        )
        if quiz_result_check.scalar_one_or_none() is None:
            return json({"error": "Quiz not found"}, status=404)

        quiz_result = QuizResult(
            id=uuid.uuid4(),
            quiz_id=qid,
            member_id=member.id,
            survey_results=body.survey_results,
            score=body.score,
            is_passed=body.is_passed,
            time_spent=body.time_spent,
            result_metadata=body.result_metadata,
        )
        session.add(quiz_result)
        await session.commit()
        await session.refresh(quiz_result)

    return json(_result_to_item(quiz_result), status=201)


@quizzes_api_bp.get("/quizzes/<quiz_id:str>/results")
async def get_quiz_results(request: Request, quiz_id: str):
    """GET /api/v1/quizzes/:id/results -- All results for a quiz."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        qid = uuid.UUID(quiz_id)
    except ValueError:
        return json({"error": "Invalid quiz ID"}, status=400)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        total_result = await session.execute(
            select(QuizResult.id).where(QuizResult.quiz_id == qid)
        )
        total = len(total_result.scalars().all())

        result = await session.execute(
            select(QuizResult)
            .where(QuizResult.quiz_id == qid)
            .order_by(QuizResult.completed_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        results = result.scalars().all()

    return json({
        "items": [_result_to_item(r) for r in results],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ---------------------------------------------------------------------------
# Member Profile Endpoints
# ---------------------------------------------------------------------------


@quizzes_api_bp.get("/members/<member_id:str>/quiz-history")
async def get_member_quiz_history(request: Request, member_id: str):
    """GET /api/v1/members/:member_id/quiz-history -- Member's quiz results."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        mid = uuid.UUID(member_id)
    except ValueError:
        return json({"error": "Invalid member ID"}, status=400)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        total_result = await session.execute(
            select(QuizResult.id).where(QuizResult.member_id == mid)
        )
        total = len(total_result.scalars().all())

        result = await session.execute(
            select(QuizResult)
            .where(QuizResult.member_id == mid)
            .order_by(QuizResult.completed_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        results = result.scalars().all()

    return json({
        "items": [_result_to_item(r) for r in results],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@quizzes_api_bp.get("/members/<member_id:str>/badges")
async def get_member_badges(request: Request, member_id: str):
    """GET /api/v1/members/:member_id/badges -- Member's earned badges."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        mid = uuid.UUID(member_id)
    except ValueError:
        return json({"error": "Invalid member ID"}, status=400)

    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(UserBadge)
            .where(UserBadge.member_id == mid)
            .order_by(UserBadge.earned_at.desc())
        )
        badges = result.scalars().all()

    return json({"items": [_badge_to_item(b) for b in badges]})


@quizzes_api_bp.get("/members/<member_id:str>/tags")
async def get_member_tags(request: Request, member_id: str):
    """GET /api/v1/members/:member_id/tags -- Member's profile tags."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        mid = uuid.UUID(member_id)
    except ValueError:
        return json({"error": "Invalid member ID"}, status=400)

    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(UserTag)
            .where(UserTag.member_id == mid)
            .order_by(UserTag.tag_category.asc(), UserTag.tag_key.asc())
        )
        tags = result.scalars().all()

    return json({"items": [_tag_to_item(t) for t in tags]})
