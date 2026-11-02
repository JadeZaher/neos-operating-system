"""JSON API blueprint for quiz management and member profile data.

Blueprint: quizzes_api_bp, url_prefix="/api/v1"

Manages quizzes, quiz submissions, results, member badges, and tags.
Returns JSON responses only.
"""

from __future__ import annotations

import logging
import re
import uuid
import datetime as _dt
from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import delete as sa_delete, select, or_, and_, func
from sqlalchemy.orm import selectinload

from neos_agent.api.schemas.quizzes import (
    QuizCreateRequest, QuizDetail, QuizListItem, QuizResultItem,
    QuizSubmitRequest, QuizUpdateRequest, UserBadgeItem, UserTagItem,
)
from neos_agent.db.course_models import (
    Course,
    Quiz,
    QuizResult,
    UserBadge,
    UserTag,
)
from neos_agent.db.models import Domain, Member, QuizAssignment, Team
from neos_agent.api.errors import ApiError
from neos_agent.api.guards import caller_in, caller_user_id
from neos_agent.services.join_gates import activate_if_ready, completion_questions, quiz_fingerprint, quiz_questions, same_answer_value, verify_quiz_completion
from neos_agent.api.helpers import require_auth, require_auth_user, require_admin, get_ecosystem_ids
from neos_agent.api.policy import can_manage_onboarding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

quizzes_api_bp = Blueprint("quizzes_api", url_prefix="/api/v1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------



def _escape_like(value: str) -> str:
    return re.sub(r"([%_\\])", r"\\\1", value)


# FX-Onboard (A2): onboarding content is the ecosystem's stewards'; see api/AGENTS.md "Onboarding" § FX-Onboard.
QUIZ_STEWARDS_ONLY = "Only an active steward of this quiz's ecosystem can change it or read its results"
GLOBAL_QUIZ_ADMINS_ONLY = "A quiz shared by every ecosystem is changed only by a platform admin"


async def quiz_steward_or_error(session, request: Request, ecosystem_id: uuid.UUID | None) -> Member:
    """The row that may write a quiz of `ecosystem_id` or read its results: a steward there (can_manage_onboarding),
    or for a global quiz (no ecosystem) a platform admin; else 403."""
    if ecosystem_id is None:
        administrator, error = await require_admin(request)
        if error is not None:
            raise ApiError(403, GLOBAL_QUIZ_ADMINS_ONLY)
        return administrator
    caller = await caller_in(session, request, ecosystem_id)
    if not can_manage_onboarding(caller, ecosystem_id):
        raise ApiError(403, QUIZ_STEWARDS_ONLY)
    return caller


async def _stewarded_quiz(session, request: Request, quiz_id: str, *, for_update: bool = False) -> Quiz:
    """A quiz by id that the caller stewards (quiz_steward_or_error): 400 bad id, 404 missing, 403 not theirs."""
    try:
        qid = uuid.UUID(quiz_id)
    except ValueError:
        raise ApiError(400, "Invalid quiz ID") from None
    stmt = select(Quiz).where(Quiz.id == qid)
    quiz = (await session.execute(stmt.with_for_update() if for_update else stmt)).scalar_one_or_none()
    if quiz is None:
        raise ApiError(404, "Quiz not found")
    ecosystem_id, _ = await _quiz_ecosystem(session, quiz)
    await quiz_steward_or_error(session, request, ecosystem_id)
    return quiz


async def _quiz_ecosystem(session, quiz):
    from neos_agent.db.course_models import Course
    course = await session.get(Course, quiz.course_id) if quiz.course_id else None
    if quiz.course_id and course is None:
        raise ApiError(409, "This quiz's configured course is unavailable")
    if course and quiz.ecosystem_id not in (None, course.ecosystem_id):
        raise ApiError(409, "This quiz's configured course belongs to another ecosystem")
    return quiz.ecosystem_id or (course.ecosystem_id if course else None), course


def copy_quiz(quiz: Quiz, *, ecosystem_id: uuid.UUID, domain_id: uuid.UUID | None, created_by: uuid.UUID | None) -> Quiz:
    """A copy of a shared (global) quiz owned by one ecosystem; the original stays shared (FX-Onboard A9)."""
    return Quiz(
        id=uuid.uuid4(), course_id=quiz.course_id, ecosystem_id=ecosystem_id, domain_id=domain_id,
        title=quiz.title, description=quiz.description, mode=quiz.mode, survey_json=quiz.survey_json,
        time_limit=quiz.time_limit, passing_score=quiz.passing_score, allow_retakes=quiz.allow_retakes,
        visibility=quiz.visibility, is_published=quiz.is_published, is_entry_quiz=False, created_by=created_by,
    )


def _quiz_to_list_item(q: Quiz) -> dict:
    return QuizListItem(
        id=q.id,
        course_id=q.course_id,
        ecosystem_id=q.ecosystem_id,
        domain_id=q.domain_id,
        team_id=q.team_id,
        title=q.title,
        description=q.description,
        mode=q.mode,
        visibility=q.visibility,
        is_published=q.is_published,
        is_entry_quiz=q.is_entry_quiz,
        time_limit=q.time_limit,
        passing_score=q.passing_score,
        allow_retakes=q.allow_retakes,
        created_at=q.created_at,
        updated_at=q.updated_at,
    ).model_dump(mode="json")


def _without_answer_keys(value):
    if isinstance(value, list):
        return [_without_answer_keys(item) for item in value]
    if isinstance(value, dict):
        return {key: _without_answer_keys(item) for key, item in value.items()
                if "correctanswer" not in key.lower() and key.lower() not in {"iscorrect", "calculatedvalues", "completedhtmloncondition"}}
    return value


def _quiz_to_detail(q: Quiz, *, editable: bool = False) -> dict:
    return QuizDetail(
        id=q.id,
        course_id=q.course_id,
        ecosystem_id=q.ecosystem_id,
        domain_id=q.domain_id,
        team_id=q.team_id,
        title=q.title,
        description=q.description,
        mode=q.mode,
        visibility=q.visibility,
        is_published=q.is_published,
        is_entry_quiz=q.is_entry_quiz,
        time_limit=q.time_limit,
        passing_score=q.passing_score,
        allow_retakes=q.allow_retakes,
        created_at=q.created_at,
        updated_at=q.updated_at,
        survey_json=q.survey_json if editable else _without_answer_keys(q.survey_json),
        created_by=q.created_by,
    ).model_dump(mode="json")


def _result_to_item(r: QuizResult) -> dict:
    return QuizResultItem(
        id=r.id,
        quiz_id=r.quiz_id,
        member_id=r.member_id,
        score=r.score,
        is_passed=r.is_passed,
        completion_verified=r.completion_verified,
        time_spent=r.time_spent,
        survey_results=r.survey_results,
        result_metadata=_without_answer_keys(r.result_metadata),
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
    member, err = require_auth(request)
    if err:
        return err

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        filters = []
        memberships = (await session.scalars(select(Member).where(Member.user_id == caller_user_id(request)))).all()
        readable_ids = [m.ecosystem_id for m in memberships if m.current_status in {"active", "pending_consent"}]
        steward_ids = [m.ecosystem_id for m in memberships if can_manage_onboarding(m, m.ecosystem_id)]
        quiz_ecosystem = func.coalesce(Quiz.ecosystem_id, Course.ecosystem_id)
        filters.append(or_(quiz_ecosystem.in_(steward_ids), and_(Quiz.is_published.is_(True),
            or_(quiz_ecosystem.is_(None), quiz_ecosystem.in_(readable_ids)))))

        course_id_str = request.args.get("course_id")
        if course_id_str:
            try:
                filters.append(Quiz.course_id == uuid.UUID(course_id_str))
            except ValueError:
                return json({"error": "Invalid course_id"}, status=400)

        # Ecosystem/domain scoping
        eco_id_str = request.args.get("ecosystem_id")
        if eco_id_str:
            try:
                filters.append(quiz_ecosystem == uuid.UUID(eco_id_str))
            except ValueError:
                return json({"error": "Invalid ecosystem_id"}, status=400)

        domain_id_str = request.args.get("domain_id")
        if domain_id_str:
            try:
                filters.append(Quiz.domain_id == uuid.UUID(domain_id_str))
            except ValueError:
                return json({"error": "Invalid domain_id"}, status=400)
        team_id_str = request.args.get("team_id")
        if team_id_str:
            try:
                filters.append(Quiz.team_id == uuid.UUID(team_id_str))
            except ValueError:
                return json({"error": "Invalid team_id"}, status=400)

        visibility = request.args.get("visibility")
        if visibility:
            filters.append(Quiz.visibility == visibility)

        is_published_str = request.args.get("is_published")
        if is_published_str is not None:
            filters.append(Quiz.is_published == (is_published_str.lower() == "true"))

        search = request.args.get("q")
        if search:
            filters.append(Quiz.title.ilike(f"%{_escape_like(search)}%"))

        count_stmt = select(Quiz.id).outerjoin(Course, Course.id == Quiz.course_id).where(*filters)
        total_result = await session.execute(count_stmt)
        total = len(total_result.scalars().all())

        stmt = (
            select(Quiz)
            .outerjoin(Course, Course.id == Quiz.course_id)
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
    member, err = require_auth(request)
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
        candidate = request.args.get("candidate") == "1"
        ecosystem_id, course = await _quiz_ecosystem(session, quiz)
        row = await caller_in(session, request, ecosystem_id) if ecosystem_id else None
        editable = can_manage_onboarding(row, ecosystem_id) if ecosystem_id else False
        if ecosystem_id is None and not candidate and getattr(request.ctx, "is_node_admin", False):
            await quiz_steward_or_error(session, request, None)
            editable = True
        if candidate:
            editable = False
        if not editable and (not quiz.is_published or (ecosystem_id is not None
                and (row is None or row.current_status not in {"active", "pending_consent"}))):
            raise ApiError(404, "Quiz not found")
        if not editable and ecosystem_id is None and course is None and quiz.visibility != "public":
            raise ApiError(404, "Quiz not found")
        return json(_quiz_to_detail(quiz, editable=editable))


@quizzes_api_bp.post("/quizzes")
async def create_quiz(request: Request):
    """POST /api/v1/quizzes -- Create a new quiz."""
    member, err = require_auth(request)
    if err:
        return err

    try:
        body = QuizCreateRequest.model_validate(request.json or {})
    except Exception as e:
        return json({"error": str(e)}, status=400)

    async with request.app.ctx.db() as session:
        author = await quiz_steward_or_error(session, request, body.ecosystem_id)
        if body.domain_id is not None:  # a domain quiz belongs to that domain's ecosystem
            domain_ecosystem = await session.scalar(select(Domain.ecosystem_id).where(Domain.id == body.domain_id))
            if domain_ecosystem is None or domain_ecosystem != body.ecosystem_id:
                raise ApiError(400, "Choose a domain of the quiz's ecosystem", {"field": "domain_id"})
        if body.team_id is not None:
            team = await session.get(Team, body.team_id)
            if team is None or team.ecosystem_id != body.ecosystem_id or body.domain_id is not None:
                raise ApiError(400, "Choose a team of the quiz's ecosystem without a domain", {"field": "team_id"})
        if body.course_id is not None:
            from neos_agent.db.course_models import Course
            course = await session.get(Course, body.course_id)
            if course is None or course.ecosystem_id != body.ecosystem_id:
                raise ApiError(400, "Choose a course of the quiz's ecosystem", {"field": "course_id"})
        quiz = Quiz(
            id=uuid.uuid4(),
            course_id=body.course_id,
            ecosystem_id=body.ecosystem_id,
            domain_id=body.domain_id,
            team_id=body.team_id,
            title=body.title,
            description=body.description,
            mode=body.mode,
            survey_json=body.survey_json,
            time_limit=body.time_limit,
            passing_score=body.passing_score,
            allow_retakes=body.allow_retakes,
            visibility=body.visibility,
            is_published=body.is_published,
            is_entry_quiz=body.is_entry_quiz,
            created_by=author.id if isinstance(author, Member) else None,
        )
        session.add(quiz)
        await session.commit()
        await session.refresh(quiz)

    return json(_quiz_to_list_item(quiz), status=201)


@quizzes_api_bp.put("/quizzes/<quiz_id:str>")
async def update_quiz(request: Request, quiz_id: str):
    """PUT /api/v1/quizzes/:id -- Update an existing quiz."""
    member, err = require_auth(request)
    if err:
        return err

    try:
        body = QuizUpdateRequest.model_validate(request.json or {})
    except Exception as e:
        return json({"error": str(e)}, status=400)

    async with request.app.ctx.db() as session:
        quiz = await _stewarded_quiz(session, request, quiz_id, for_update=True)  # FX-Onboard A2
        if "team_id" in body.model_fields_set:
            team = await session.get(Team, body.team_id) if body.team_id else None
            if body.team_id and (team is None or team.ecosystem_id != quiz.ecosystem_id or quiz.domain_id is not None):
                raise ApiError(400, "Choose a team of the quiz's ecosystem without a domain", {"field": "team_id"})
            quiz.team_id = body.team_id

        if body.course_id is not None:
            from neos_agent.db.course_models import Course
            course = await session.get(Course, body.course_id)
            if course is None or course.ecosystem_id != quiz.ecosystem_id:
                raise ApiError(400, "Choose a course of the quiz's ecosystem", {"field": "course_id"})
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
        if body.is_entry_quiz is not None:
            quiz.is_entry_quiz = body.is_entry_quiz

        await session.commit()
        await session.refresh(quiz)

    return json(_quiz_to_list_item(quiz))


def _grade_quiz(quiz: Quiz, survey_results: dict | None) -> dict:
    """Grade a quiz submission against correctAnswer fields in survey_json.

    Returns dict with keys: score, is_passed, result_metadata.
    """
    answers = survey_results or {}
    all_questions, _ = completion_questions(quiz)
    gradable = quiz_questions(quiz)
    all_questions = {q.get("name"): q for q in [*all_questions, *gradable] if q.get("name")}
    total_questions = len(all_questions)
    answered = sum(1 for name in all_questions if name in answers and answers[name] is not None)
    skipped = total_questions - answered

    if not gradable:
        # Non-graded assessment -- just track completion
        completion_pct = round((answered / total_questions) * 100) if total_questions else 100
        return {
            "score": completion_pct,
            "is_passed": None,
            "result_metadata": {
                "totalQuestions": total_questions,
                "answeredQuestions": answered,
                "skippedQuestions": skipped,
                "gradableQuestions": 0,
                "completionPercentage": completion_pct,
                "isAssessment": True,
            },
        }

    correct_count = 0
    per_question: list[dict] = []
    for q in gradable:
        user_answer = answers.get(q["name"])
        correct_answer = q["correctAnswer"]
        if q.get("type") in {"text", "comment"}:
            is_correct = isinstance(user_answer, str) and isinstance(correct_answer, str) and user_answer.strip().lower() == correct_answer.strip().lower()
        elif q.get("type") == "checkbox":
            remaining = list(correct_answer) if isinstance(correct_answer, list) else []
            is_correct = isinstance(user_answer, list) and isinstance(correct_answer, list) and len(user_answer) == len(remaining)
            for value in user_answer if isinstance(user_answer, list) else []:
                match = next((index for index, expected in enumerate(remaining) if same_answer_value(value, expected)), None)
                if match is None:
                    is_correct = False
                    break
                remaining.pop(match)
        else:
            is_correct = user_answer is not None and same_answer_value(user_answer, correct_answer)
        if is_correct:
            correct_count += 1
        per_question.append({
            "name": q["name"],
            "title": q.get("title", q["name"]),
            "userAnswer": user_answer,
            "isCorrect": is_correct,
        })

    gradable_count = len(gradable)
    score_pct = round((correct_count / gradable_count) * 100) if gradable_count else 0
    passing_score = quiz.passing_score if quiz.passing_score is not None else 70
    is_passed = score_pct >= passing_score
    completion_pct = round((answered / total_questions) * 100) if total_questions else 100

    return {
        "score": score_pct,
        "is_passed": is_passed,
        "result_metadata": {
            "totalQuestions": total_questions,
            "answeredQuestions": answered,
            "skippedQuestions": skipped,
            "correctCount": correct_count,
            "incorrectCount": gradable_count - correct_count,
            "gradableQuestions": gradable_count,
            "completionPercentage": completion_pct,
            "correctnessPercentage": score_pct,
            "isAssessment": False,
            "passingScore": passing_score,
            "perQuestion": per_question,
        },
    }


@quizzes_api_bp.post("/quizzes/<quiz_id:str>/submit")
async def submit_quiz(request: Request, quiz_id: str):
    """POST /api/v1/quizzes/:id/submit -- Submit a quiz result.

    Server-side grading: compares answers against correctAnswer fields
    in the quiz survey_json to compute score, is_passed, and result_metadata.
    """
    member, err = require_auth(request)
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
        quiz_row = await session.execute(select(Quiz).where(Quiz.id == qid).with_for_update())
        quiz = quiz_row.scalar_one_or_none()
        if quiz is None:
            return json({"error": "Quiz not found"}, status=404)
        # G-Onboard (review M7): an ecosystem's quiz lands on the caller's row there, not the default row.
        ecosystem_id, course = await _quiz_ecosystem(session, quiz)
        if body.target_ecosystem_id is not None:
            if ecosystem_id is not None and body.target_ecosystem_id != ecosystem_id:
                raise ApiError(400, "The submission target must be this quiz's ecosystem", {"field": "target_ecosystem_id"})
            ecosystem_id = body.target_ecosystem_id
        row = await caller_in(session, request, ecosystem_id) if ecosystem_id else None
        if not quiz.is_published or (ecosystem_id is not None and
                (row is None or row.current_status not in {"active", "pending_consent"})):
            raise ApiError(404, "Quiz not found")
        if quiz.ecosystem_id is None and course is None and quiz.visibility != "public":
            raise ApiError(404, "Quiz not found")
        member_row_id = row.id if row is not None else member.id
        fingerprint = quiz_fingerprint(quiz, course)
        if not quiz.allow_retakes and await session.scalar(select(QuizResult.id).where(
                QuizResult.quiz_id == qid, QuizResult.member_id == member_row_id,
                QuizResult.completion_verified.is_(True), QuizResult.graded_fingerprint == fingerprint).limit(1)):
            raise ApiError(409, "This quiz allows one verified attempt per current version. Ask a steward for help with this version.")
        completion_verified = verify_quiz_completion(quiz, body.survey_results)
        grading = _grade_quiz(quiz, body.survey_results)
        grading["completion_verified"] = completion_verified
        grading["completion_mode"] = "graded" if quiz_questions(quiz) else "completion"

        quiz_result = QuizResult(
            id=uuid.uuid4(),
            quiz_id=qid,
            member_id=member_row_id,
            survey_results=body.survey_results,
            score=grading["score"],
            is_passed=grading["is_passed"],
            time_spent=body.time_spent,
            result_metadata=grading["result_metadata"],
            graded_fingerprint=fingerprint,
            completion_verified=completion_verified,
        )
        session.add(quiz_result)
        await session.flush()
        if grading["is_passed"] or grading["is_passed"] is None and completion_verified:
            for assignment in (await session.execute(select(QuizAssignment).where(
                QuizAssignment.quiz_id == qid, QuizAssignment.member_id == member_row_id,
                QuizAssignment.status != "completed",
            ))).scalars():
                assignment.status = "completed"
        graded = grading["completion_mode"] == "graded"
        join_gates = await activate_if_ready(session, row, trigger="quiz_passed" if graded else "quiz_completed",
            notes="Configured entry quiz passed" if graded else "Configured entry questionnaire completed") if row else None
        await session.commit()
        await session.refresh(quiz_result)

    return json({
        "result": _result_to_item(quiz_result),
        "grading": grading,
        "join_gates": join_gates,
    }, status=201)


@quizzes_api_bp.get("/quizzes/<quiz_id:str>/results")
async def get_quiz_results(request: Request, quiz_id: str):
    """GET /api/v1/quizzes/:id/results -- All results for a quiz: its stewards only (FX-Onboard A2)."""
    member, err = require_auth(request)
    if err:
        return err

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        qid = (await _stewarded_quiz(session, request, quiz_id)).id
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


@quizzes_api_bp.delete("/quizzes/<quiz_id:str>")
async def delete_quiz(request: Request, quiz_id: str):
    """DELETE /api/v1/quizzes/:id -- Delete a quiz and its results: its stewards only (FX-Onboard A2)."""
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        quiz = await _stewarded_quiz(session, request, quiz_id, for_update=True)

        # Delete associated results first
        await session.execute(sa_delete(QuizResult).where(QuizResult.quiz_id == quiz.id))
        await session.delete(quiz)
        await session.commit()

    return json({"ok": True, "message": "Quiz deleted"})


@quizzes_api_bp.get("/quizzes/<quiz_id:str>/results/all")
async def get_quiz_results_admin(request: Request, quiz_id: str):
    """GET /api/v1/quizzes/:id/results/all -- All results with member info (admin view).

    Returns all quiz results enriched with member display_name: the quiz's stewards only (FX-Onboard A2).
    """
    member, err = require_auth(request)
    if err:
        return err

    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))
    offset = (page - 1) * per_page

    async with request.app.ctx.db() as session:
        quiz = await _stewarded_quiz(session, request, quiz_id)
        qid = quiz.id

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

        # Fetch member display names
        member_ids = list({r.member_id for r in results})
        member_names: dict[uuid.UUID, str] = {}
        if member_ids:
            member_rows = await session.execute(
                select(Member.id, Member.display_name).where(
                    Member.id.in_(member_ids)
                )
            )
            for mid, dname in member_rows.all():
                member_names[mid] = dname or "Unknown"

    return json({
        "items": [
            {
                **_result_to_item(r),
                "member_name": member_names.get(r.member_id, "Unknown"),
            }
            for r in results
        ],
        "quiz_title": quiz.title,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


# ---------------------------------------------------------------------------
# Member Profile Endpoints
# ---------------------------------------------------------------------------


@quizzes_api_bp.get("/quiz-results/<result_id:uuid>")
async def get_own_quiz_result(request: Request, result_id: uuid.UUID):
    """Read one attempt by its owner's User identity, independent of selected membership."""
    user, err = require_auth_user(request)
    if err:
        return err
    async with request.app.ctx.db() as session:
        result = await session.scalar(select(QuizResult).join(Member, QuizResult.member_id == Member.id)
            .where(QuizResult.id == result_id, Member.user_id == user.id)
            .options(selectinload(QuizResult.quiz)))
        if result is None:
            raise ApiError(404, "Quiz result not found")
        item = _result_to_item(result)
        item["quiz"] = _quiz_to_detail(result.quiz, editable=False) if result.quiz else None
        if result.quiz:
            _, course = await _quiz_ecosystem(session, result.quiz)
            fingerprint = quiz_fingerprint(result.quiz, course)
            current_attempt = await session.scalar(select(QuizResult.id).where(QuizResult.quiz_id == result.quiz_id,
                QuizResult.member_id == result.member_id, QuizResult.completion_verified.is_(True), QuizResult.graded_fingerprint == fingerprint).limit(1))
            item["attempt_policy"] = {"can_submit": result.quiz.allow_retakes or current_attempt is None,
                                      "result_is_current": result.completion_verified and result.graded_fingerprint == fingerprint,
                                      "scope": "current_verified_version"}
        return json(item)


@quizzes_api_bp.get("/members/<member_id:str>/quiz-history")
async def get_member_quiz_history(request: Request, member_id: str):
    """GET /api/v1/members/:member_id/quiz-history -- Member's quiz results with quiz info: the member themselves (any
    of their rows) or a steward of that member's ecosystem; anyone else 404 (FX-Onboard A2: results never leak)."""
    member, err = require_auth(request)
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
        target = await session.get(Member, mid)
        own = target is not None and target.user_id == member.user_id
        if target is None or not (own or can_manage_onboarding(
                await caller_in(session, request, target.ecosystem_id), target.ecosystem_id)):
            raise ApiError(404, "Member not found")
        total_result = await session.execute(
            select(QuizResult.id).where(QuizResult.member_id == mid)
        )
        total = len(total_result.scalars().all())

        result = await session.execute(
            select(QuizResult)
            .where(QuizResult.member_id == mid)
            .options(selectinload(QuizResult.quiz))
            .order_by(QuizResult.completed_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        results = result.scalars().all()

    items = []
    for r in results:
        item = _result_to_item(r)
        if r.quiz:
            item["quiz"] = {"title": r.quiz.title, "description": r.quiz.description}
        else:
            item["quiz"] = None
        items.append(item)

    return json({
        "results": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@quizzes_api_bp.get("/members/<member_id:str>/badges")
async def get_member_badges(request: Request, member_id: str):
    """GET /api/v1/members/:member_id/badges -- Member's earned badges."""
    member, err = require_auth(request)
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
    member, err = require_auth(request)
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
