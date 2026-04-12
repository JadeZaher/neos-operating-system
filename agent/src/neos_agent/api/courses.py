"""JSON API blueprint for course management.

Blueprint: courses_api_bp, url_prefix="/api/v1/courses"

Manages learning courses scoped to ecosystems.
Returns JSON responses only.
"""

from __future__ import annotations

import json as json_module
import logging
import re
import uuid
import datetime as _dt
from typing import Optional

from pydantic import BaseModel
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from neos_agent.db.course_models import Course, Quiz

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Local Pydantic schemas
# ---------------------------------------------------------------------------


class CourseListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    domain_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    is_onboarding_required: bool
    sort_order: int
    created_at: _dt.datetime
    updated_at: _dt.datetime


class QuizSummary(BaseModel):
    id: uuid.UUID
    title: str
    mode: str
    is_published: bool
    visibility: str


class CourseDetail(CourseListItem):
    created_by: Optional[uuid.UUID] = None
    quizzes: list[QuizSummary] = []


class CourseCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    domain_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    is_onboarding_required: bool = False
    sort_order: int = 0


class CourseUpdateRequest(BaseModel):
    domain_id: Optional[uuid.UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_onboarding_required: Optional[bool] = None
    sort_order: Optional[int] = None


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

courses_api_bp = Blueprint("courses_api", url_prefix="/api/v1/courses")


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


def _course_to_list_item(c: Course) -> dict:
    return CourseListItem(
        id=c.id,
        ecosystem_id=c.ecosystem_id,
        domain_id=c.domain_id,
        title=c.title,
        description=c.description,
        is_onboarding_required=c.is_onboarding_required,
        sort_order=c.sort_order,
        created_at=c.created_at,
        updated_at=c.updated_at,
    ).model_dump(mode="json")


def _quiz_summary(q: Quiz) -> dict:
    return QuizSummary(
        id=q.id,
        title=q.title,
        mode=q.mode,
        is_published=q.is_published,
        visibility=q.visibility,
    ).model_dump(mode="json")


def _course_to_detail(c: Course) -> dict:
    return CourseDetail(
        id=c.id,
        ecosystem_id=c.ecosystem_id,
        domain_id=c.domain_id,
        title=c.title,
        description=c.description,
        is_onboarding_required=c.is_onboarding_required,
        sort_order=c.sort_order,
        created_at=c.created_at,
        updated_at=c.updated_at,
        created_by=c.created_by,
        quizzes=[_quiz_summary(q) for q in (c.quizzes or [])],
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@courses_api_bp.get("/")
async def list_courses(request: Request):
    """GET /api/v1/courses -- Paginated list of courses scoped to ecosystem.

    Query params: q (search title), page (default 1), per_page (default 25, max 100).
    """
    member, err = _require_auth(request)
    if err:
        return err

    eco_ids = _get_ecosystem_ids(request)

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        stmt = select(Course).order_by(Course.sort_order.asc(), Course.created_at.desc())

        if eco_ids:
            stmt = stmt.where(Course.ecosystem_id.in_(eco_ids))

        search = request.args.get("q")
        if search:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(Course.title.ilike(pattern))

        count_stmt = stmt.with_only_columns(
            *[c for c in Course.__table__.c if c.key == "id"]
        )

        total_result = await session.execute(
            select(Course.id).where(
                *([Course.ecosystem_id.in_(eco_ids)] if eco_ids else []),
                *([Course.title.ilike(f"%{_escape_like(search)}%")] if search else []),
            )
        )
        total = len(total_result.scalars().all())

        stmt = stmt.offset(offset).limit(per_page)
        result = await session.execute(stmt)
        courses = result.scalars().all()

    return json({
        "items": [_course_to_list_item(c) for c in courses],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@courses_api_bp.get("/<course_id:str>")
async def get_course(request: Request, course_id: str):
    """GET /api/v1/courses/:id -- Course detail with quizzes."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        cid = uuid.UUID(course_id)
    except ValueError:
        return json({"error": "Invalid course ID"}, status=400)

    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(Course)
            .where(Course.id == cid)
            .options(selectinload(Course.quizzes))
        )
        course = result.scalar_one_or_none()

    if course is None:
        return json({"error": "Course not found"}, status=404)

    return json(_course_to_detail(course))


@courses_api_bp.post("/")
async def create_course(request: Request):
    """POST /api/v1/courses -- Create a new course."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        body = CourseCreateRequest.model_validate(request.json or {})
    except Exception as e:
        return json({"error": str(e)}, status=400)

    course = Course(
        id=uuid.uuid4(),
        ecosystem_id=body.ecosystem_id,
        domain_id=body.domain_id,
        title=body.title,
        description=body.description,
        created_by=body.created_by,
        is_onboarding_required=body.is_onboarding_required,
        sort_order=body.sort_order,
    )

    async with request.app.ctx.db() as session:
        session.add(course)
        await session.commit()
        await session.refresh(course)

    return json(_course_to_list_item(course), status=201)


@courses_api_bp.put("/<course_id:str>")
async def update_course(request: Request, course_id: str):
    """PUT /api/v1/courses/:id -- Update an existing course."""
    member, err = _require_auth(request)
    if err:
        return err

    try:
        cid = uuid.UUID(course_id)
    except ValueError:
        return json({"error": "Invalid course ID"}, status=400)

    try:
        body = CourseUpdateRequest.model_validate(request.json or {})
    except Exception as e:
        return json({"error": str(e)}, status=400)

    async with request.app.ctx.db() as session:
        result = await session.execute(select(Course).where(Course.id == cid))
        course = result.scalar_one_or_none()

        if course is None:
            return json({"error": "Course not found"}, status=404)

        if body.domain_id is not None:
            course.domain_id = body.domain_id
        if body.title is not None:
            course.title = body.title
        if body.description is not None:
            course.description = body.description
        if body.is_onboarding_required is not None:
            course.is_onboarding_required = body.is_onboarding_required
        if body.sort_order is not None:
            course.sort_order = body.sort_order

        await session.commit()
        await session.refresh(course)

    return json(_course_to_list_item(course))
