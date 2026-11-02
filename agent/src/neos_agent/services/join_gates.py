"""Configured entry quizzes and agreement prerequisites; see services/AGENTS.md."""
from __future__ import annotations

import hashlib
import json
import uuid

from sqlalchemy import and_, or_, select

from neos_agent.api.errors import ApiError
from neos_agent.db.course_models import Course, Quiz, QuizResult
from neos_agent.db.models import Domain, Member, Team
from neos_agent.services.agreement_consent import missing_agreement_consents


def quiz_fingerprint(quiz: Quiz, course: Course | None = None) -> str:
    value = {name: getattr(quiz, name) for name in (
        "id", "ecosystem_id", "domain_id", "team_id", "course_id", "mode", "survey_json", "passing_score",
    )}
    value["verification_version"] = "survey-completion-v2-typed-grading"
    value["course_scope"] = {"ecosystem_id": course.ecosystem_id, "domain_id": course.domain_id} if course else None
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def quiz_questions(quiz: Quiz) -> list[dict]:
    def walk(elements):
        for element in elements if isinstance(elements, list) else []:
            if not isinstance(element, dict):
                continue
            if isinstance(element.get("name"), str) and element.get("correctAnswer") is not None:
                yield element
            yield from walk(element.get("elements"))
    survey = quiz.survey_json if isinstance(quiz.survey_json, dict) else {}
    pages = survey.get("pages") if isinstance(survey.get("pages"), list) else []
    return list(walk(survey.get("elements"))) + [question for page in pages
        if isinstance(page, dict) for question in walk(page.get("elements"))]


def same_answer_value(left, right) -> bool:
    """Compare JSON answer types without case or string/number coercion."""
    if type(left) in {int, float} and type(right) in {int, float}:
        return left == right
    return type(left) is type(right) and left == right


def quiz_available(quiz: Quiz) -> bool:
    _, errors = completion_questions(quiz)
    return bool(quiz.is_published and not errors and (not quiz_questions(quiz)
                or 0 <= (quiz.passing_score if quiz.passing_score is not None else 70) <= 100))


def completion_questions(quiz: Quiz) -> tuple[list[dict], list[str]]:
    survey = quiz.survey_json
    if not isinstance(survey, dict):
        return [], ["The questionnaire content is unavailable"]
    pages = survey.get("pages", [])
    if not isinstance(pages, list):
        return [], ["The questionnaire pages need repair"]
    if "elements" in survey and not isinstance(survey["elements"], list):
        return [], ["The questionnaire fields need repair"]
    elements = list(survey.get("elements", [])) if isinstance(survey.get("elements", []), list) else []
    for page in pages:
        if not isinstance(page, dict) or not isinstance(page.get("elements", []), list):
            return [], ["The questionnaire pages need repair"]
        elements.extend(page.get("elements", []))
    supported = {"boolean", "comment", "text", "radiogroup", "dropdown", "checkbox", "rating"}
    questions, errors, names = [], [], set()
    for question in elements:
        if not isinstance(question, dict):
            errors.append("A questionnaire field needs repair")
            continue
        if question.get("type") in {"html", "image"}:
            continue
        name = question.get("name")
        if question.get("type") not in supported or not isinstance(name, str) or not name.strip() or name in names:
            errors.append("The questionnaire has an unsupported format or invalid question key")
            continue
        names.add(name)
        if "isRequired" in question and type(question["isRequired"]) is not bool:
            errors.append("A question's required-answer setting needs repair")
        if question["type"] in {"radiogroup", "dropdown", "checkbox"}:
            choices = question.get("choices")
            values = [choice.get("value") if isinstance(choice, dict) else choice for choice in choices] if isinstance(choices, list) else []
            if not values or any(type(value) not in {str, int, float, bool} or isinstance(value, str) and not value.strip() for value in values):
                errors.append("A question's answer choices need repair")
            correct = question.get("correctAnswer")
            if correct is not None:
                expected = correct if question["type"] == "checkbox" and isinstance(correct, list) else [correct]
                if question["type"] == "checkbox" and not isinstance(correct, list) or not all(any(same_answer_value(item, value) for value in values) for item in expected):
                    errors.append("A question's grading key does not match its choices")
        if question["type"] == "rating":
            low, high = question.get("rateMin", 1), question.get("rateMax", 5)
            if type(low) not in {int, float} or type(high) not in {int, float} or low > high:
                errors.append("A question's rating range needs repair")
        if question.get("correctAnswer") is not None and question["type"] == "boolean" and type(question["correctAnswer"]) is not bool:
            errors.append("A boolean question's grading key needs repair")
        questions.append(question)
    if not questions:
        errors.append("The questionnaire needs at least one supported answerable question")
    return questions, errors


def verify_quiz_completion(quiz: Quiz, answers: dict | None) -> bool:
    questions, configuration_errors = completion_questions(quiz)
    if quiz_questions(quiz) and not 0 <= (quiz.passing_score if quiz.passing_score is not None else 70) <= 100:
        configuration_errors.append("The knowledge quiz passing threshold needs repair")
    if configuration_errors:
        raise ApiError(409, "This questionnaire needs steward repair before it can be completed", {
            "code": "QUIZ_CONFIGURATION_INVALID", "configuration_errors": sorted(set(configuration_errors)),
        })
    answers = answers if isinstance(answers, dict) else {}
    if set(answers) - {q["name"] for q in questions}:
        raise ApiError(400, "Submit answers only for the configured questionnaire fields", {"code": "QUIZ_ANSWERS_INVALID"})
    errors, meaningful = [], False
    for question in questions:
        name, kind = question["name"], question["type"]
        value = answers.get(name)
        missing = value is None or isinstance(value, str) and not value.strip() or isinstance(value, list) and not value
        if missing:
            if question.get("isRequired", True):
                errors.append(name)
            continue
        valid = False
        if kind == "boolean":
            valid = type(value) is bool
        elif kind in {"text", "comment"}:
            valid = isinstance(value, str) and bool(value.strip()) and len(value) <= 50000
        elif kind in {"radiogroup", "dropdown", "checkbox"}:
            allowed = [choice.get("value") if isinstance(choice, dict) else choice for choice in question["choices"]]
            def allowed_value(item):
                return any(same_answer_value(item, option) for option in allowed)
            valid = (isinstance(value, list) and bool(value) and all(allowed_value(item) for item in value)
                     and len({json.dumps(item, sort_keys=True) for item in value}) == len(value)) if kind == "checkbox" else allowed_value(value)
        elif kind == "rating":
            valid = type(value) in {int, float} and question.get("rateMin", 1) <= value <= question.get("rateMax", 5)
        meaningful = meaningful or valid
        if not valid:
            errors.append(name)
    if errors or not meaningful:
        raise ApiError(400, "Answer every required question with a valid response before completing this questionnaire", {
            "code": "QUIZ_ANSWERS_INCOMPLETE", "invalid_fields": errors,
        })
    return True


async def _domain_path(session, domain: Domain) -> list[Domain]:
    path, seen = [], set()
    while domain is not None:
        if domain.id in seen or len(path) >= 100:
            raise ApiError(409, "The subgroup hierarchy needs steward repair", {"code": "JOIN_CONFIGURATION_INVALID"})
        if path and domain.ecosystem_id != path[0].ecosystem_id:
            raise ApiError(409, "The subgroup hierarchy belongs to another ecosystem", {"code": "JOIN_CONFIGURATION_INVALID"})
        seen.add(domain.id)
        path.append(domain)
        if domain.parent_domain_id is None:
            break
        domain = await session.get(Domain, domain.parent_domain_id)
        if domain is None:
            raise ApiError(409, "The subgroup hierarchy is unavailable", {"code": "JOIN_CONFIGURATION_INVALID"})
    return path


async def join_gate_summary(session, *, ecosystem_id: uuid.UUID, member: Member | None,
                            domain: Domain | None = None, team: Team | None = None,
                            user_id: uuid.UUID | None = None) -> dict:
    target = domain or team
    target_type = "domain" if domain else "team" if team else "ecosystem"
    target_id = target.id if target else ecosystem_id
    if target is not None and target.ecosystem_id != ecosystem_id:
        raise ApiError(400, "The subgroup belongs to another ecosystem")
    if member is not None and member.ecosystem_id != ecosystem_id:
        raise ApiError(400, "The membership belongs to another ecosystem")
    path = await _domain_path(session, domain) if domain else []
    domain_ids = {row.id for row in path}
    from neos_agent.services.node_admin import is_node_admin
    entrant_id = member.user_id if member is not None else user_id
    quiz_exempt = entrant_id is not None and await is_node_admin(session, entrant_id)
    rows = (await session.execute(select(Quiz, Course).outerjoin(Course, Course.id == Quiz.course_id).where(
        or_(Quiz.ecosystem_id == ecosystem_id, and_(Quiz.ecosystem_id.is_(None), Course.ecosystem_id == ecosystem_id)),
        or_(Quiz.is_entry_quiz.is_(True), Course.is_onboarding_required.is_(True)),
    ).order_by(Quiz.created_at, Quiz.id))).all()
    requirements = []
    for quiz, course in rows:
        quiz_domain = quiz.domain_id or (course.domain_id if course is not None else None)
        if quiz.team_id is not None:
            if team is None or quiz.team_id != team.id:
                continue
            scope_type, scope_id = "team", team.id
        elif quiz_domain is not None:
            if quiz_domain not in domain_ids:
                continue
            scope_type, scope_id = "domain", quiz_domain
        else:
            scope_type, scope_id = "ecosystem", ecosystem_id
        graded = bool(quiz_questions(quiz))
        passed = False
        if member is not None:
            passed = await session.scalar(select(QuizResult.id).where(
                QuizResult.quiz_id == quiz.id, QuizResult.member_id == member.id,
                QuizResult.completion_verified.is_(True),
                QuizResult.is_passed.is_(True) if graded else QuizResult.is_passed.is_(None),
                QuizResult.graded_fingerprint == quiz_fingerprint(quiz, course),
            ).limit(1)) is not None
        valid_scope = course is None or (course.ecosystem_id == ecosystem_id and
            (quiz.domain_id is None or course.domain_id in (None, quiz.domain_id)))
        status = "bypassed" if quiz_exempt else "unavailable" if not valid_scope or not quiz_available(quiz) else ("passed" if graded else "completed") if passed else "required"
        requirements.append({"id": str(quiz.id), "title": quiz.title, "scope_type": scope_type,
            "scope_id": str(scope_id), "status": status, "completion_mode": "graded" if graded else "completion", "href": f"/quiz/take/{quiz.id}"})
    agreements = {}
    if member is not None:
        for agreement in await missing_agreement_consents(session, member.id, ecosystem_id, "ecosystem"):
            agreements[agreement.id] = agreement
        for ancestor in path:
            for agreement in await missing_agreement_consents(session, member.id, ecosystem_id, "domain", ancestor.id):
                agreements[agreement.id] = agreement
    else:
        from neos_agent.services.agreement_consent import required_agreements_for_scope
        for agreement in await required_agreements_for_scope(session, ecosystem_id, "ecosystem"):
            agreements[agreement.id] = agreement
        for ancestor in path:
            for agreement in await required_agreements_for_scope(session, ecosystem_id, "domain", ancestor.id):
                agreements[agreement.id] = agreement
    status = ("quiz_unavailable" if any(q["status"] == "unavailable" for q in requirements)
              else "quiz_required" if any(q["status"] == "required" for q in requirements)
              else "agreement_consent_required" if agreements else "ready")
    return {"target_type": target_type, "target_id": str(target_id), "status": status, "eligible": status == "ready",
        "quiz_bypass": {"applied": bool(quiz_exempt and requirements), "reason": "node_admin" if quiz_exempt and requirements else None},
        "required_quizzes": requirements, "required_agreements": [{"id": str(a.id), "title": a.title,
        "version": a.version, "href": f"/agreements/{a.id}"} for a in agreements.values()]}


def require_join_gates(summary: dict) -> None:
    if summary["eligible"]:
        return
    code = {"quiz_required": "JOIN_QUIZ_REQUIRED", "quiz_unavailable": "JOIN_QUIZ_UNAVAILABLE",
            "agreement_consent_required": "CONSENT_REQUIRED"}[summary["status"]]
    raise ApiError(409, "Complete the configured entry requirements before joining", {
        "code": code, "join_gates": summary, "required_agreements": summary["required_agreements"],
        "required_quizzes": summary["required_quizzes"],
    })


async def activate_if_ready(session, member: Member, *, trigger: str, notes: str | None = None) -> dict:
    summary = await join_gate_summary(session, ecosystem_id=member.ecosystem_id, member=member)
    if member.current_status == "pending_consent" and summary["eligible"]:
        from neos_agent.services.member_lifecycle import record_transition
        record_transition(session, member, "active", trigger=trigger, notes=notes)
        await record_quiz_bypass(session, member, summary)
    return summary


async def record_quiz_bypass(session, member: Member, summary: dict, *, actor_user_id=None) -> None:
    if not summary.get("quiz_bypass", {}).get("applied"):
        return
    from neos_agent.db.models import User
    from neos_agent.services.node_admin import audit_event
    actor = await session.get(User, actor_user_id or member.user_id)
    session.add(audit_event(actor, "join_quiz_bypass", summary["target_type"], summary["target_id"],
        organization_id=member.ecosystem_id, reason="Access management", fields=(),
        summary={"basis": "entrant_node_admin", "entrant_user_id": str(member.user_id),
                 "quiz_ids": [q["id"] for q in summary["required_quizzes"]]}))
