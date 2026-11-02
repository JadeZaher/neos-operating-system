"""Server evidence for required orientation completion; see api/ORIENTATION_MATCHING.md."""
from __future__ import annotations

import json
import uuid
from sqlalchemy import select
from neos_agent.api.errors import ApiError
from neos_agent.db.models import OrientationChatSession
from neos_agent.services.orientation_content import journey_fingerprint, validate_journey_routes


def _index(key, count):
    try:
        prefix, number = key.split("_", 1)
        index = int(number)
        if prefix == "step" and key == f"step_{index}" and 0 <= index < count:
            return index
    except (AttributeError, TypeError, ValueError):
        pass
    raise ApiError(400, "Choose a step from the current journey")


async def _proof(db, member, journey, index, response, node_admin_actor=None):
    step = journey.content_sequence[index]
    if step.get("type") == "survey" and isinstance(response, dict) and response.get("node_admin_bypass") is True:
        from neos_agent.services.node_admin import audit_event
        if node_admin_actor is not None:
            db.add(audit_event(node_admin_actor, "orientation_quiz_bypass", "journey_maps", journey.id, organization_id=member.ecosystem_id,
                               reason="Access management", fields=(), summary={"basis": "entrant_node_admin", "step_index": index}))
            return
        raise ApiError(403, "Only a currently enabled node administrator can use the audited quiz exemption")
    if not isinstance(response, dict):
        raise ApiError(409, "Complete this required step before continuing", {"step_key": f"step_{index}"})
    if step.get("type") == "ai_conversation":
        try:
            identifier = uuid.UUID(str(response.get("session_id", "")))
        except ValueError:
            raise ApiError(409, "A real reply from this AI conversation step is required") from None
        row = await db.scalar(select(OrientationChatSession).where(OrientationChatSession.id == identifier,
            OrientationChatSession.owner_user_id == member.user_id, OrientationChatSession.journey_map_id == journey.id,
            OrientationChatSession.step_key == f"step_{index}", OrientationChatSession.source_fingerprint == journey_fingerprint(journey)))
        if row is None or row.turn_count < 1 or not any(message.get("role") == "assistant" and isinstance(message.get("content"), str) and message["content"].strip() for message in row.messages or []):
            raise ApiError(409, "A successful reply for your own current journey step is required; errors and older steps do not count", {"step_key": f"step_{index}"})
    elif step.get("type") == "survey":
        from neos_agent.db.course_models import Course, Quiz, QuizResult
        from neos_agent.db.models import Domain
        from neos_agent.services.join_gates import quiz_fingerprint, quiz_questions
        try:
            quiz_id = uuid.UUID(str(step.get("quiz_id", "")))
            result_id = uuid.UUID(str(response.get("result_id", "")))
        except ValueError:
            raise ApiError(409, "This required survey needs a configured quiz and your real submitted result") from None
        quiz = await db.get(Quiz, quiz_id)
        result = await db.get(QuizResult, result_id)
        course = await db.get(Course, quiz.course_id) if quiz and quiz.course_id else None
        domain_id = quiz.domain_id or (course.domain_id if course else None) if quiz else None
        domain = await db.get(Domain, domain_id) if domain_id else None
        scope = quiz.ecosystem_id or (domain.ecosystem_id if domain else None) or (course.ecosystem_id if course else None) if quiz else None
        if quiz is None or not quiz.is_published or scope not in (None, member.ecosystem_id) or (scope is None and quiz.visibility != "public"):
            raise ApiError(409, "The configured survey is unavailable for this ecosystem")
        if result is None or result.quiz_id != quiz.id or result.member_id != member.id or result.graded_fingerprint != quiz_fingerprint(quiz, course):
            raise ApiError(409, "Submit your own current version of this step's configured quiz before continuing")
        if getattr(result, "completion_verified", False) is not True:
            raise ApiError(409, "Complete this required survey using the server-validated submission flow before continuing")
        if quiz_questions(quiz) and result.is_passed is not True:
            raise ApiError(409, "This required graded quiz has not met its passing requirement")


def _next_step(steps, index, response):
    step = steps[index]
    routes = step.get("choice_routes") if isinstance(step, dict) else None
    choice = response.get("choice") if isinstance(response, dict) else None
    if step.get("type") == "choice":
        names = {item.get("value") for item in step.get("choices", []) if isinstance(item, dict)}
        if (step.get("required") or choice is not None) and (not isinstance(choice, str) or choice not in names):
            raise ApiError(409, "Select a configured choice before continuing", {"step_key": f"step_{index}"})
    destination = routes.get(choice) if isinstance(routes, dict) and isinstance(choice, str) else None
    if destination is not None:
        if type(destination) is not int or not index < destination <= len(steps):
            raise ApiError(409, "This journey has an invalid or cyclic choice route; ask a steward to repair it")
        return destination
    return index + 1


async def validate_progress(db, member, journey, progress, body, node_admin_actor=None):
    steps = journey.content_sequence if isinstance(journey.content_sequence, list) else []
    if len(steps) > 500 or any(not isinstance(step, dict) for step in steps):
        raise ApiError(409, "This journey's steps need repair before progress can be saved")
    same_journey = progress is not None and progress.journey_map_id == journey.id
    body["status"] = body.get("status", progress.status if same_journey else "in_progress")
    responses = dict(progress.step_responses or {}) if same_journey else {}
    completed = list(progress.completed_steps or []) if same_journey else []
    incoming = body.get("current_step", progress.current_step if same_journey else 0)
    if body.get("status") == "opted_out":
        body["current_step"] = min(progress.current_step or 0, len(steps)) if same_journey else 0
        return responses, completed
    validate_journey_routes(steps, status=409)
    if type(incoming) is not int or not 0 <= incoming <= len(steps):
        raise ApiError(400, "The current step must be inside this journey")
    verified = set()

    async def proof(index, response):
        if index not in verified:
            await _proof(db, member, journey, index, response, node_admin_actor)
            verified.add(index)
    key = body.get("step_key")
    if key is not None:
        index = _index(key, len(steps))
        response = body.get("step_response")
        if len(json.dumps(response, default=str)) > 12000:
            raise ApiError(400, "This step response is too large")
        if steps[index].get("required") and steps[index].get("type") in {"ai_conversation", "survey"}:
            await proof(index, response)
        if "current_step" in body and incoming != _next_step(steps, index, response):
            raise ApiError(409, "Continue to the next step declared by this journey")
        responses[key] = response
        if index not in completed:
            completed.append(index)
    elif incoming > 0 and incoming - 1 not in completed:
        completed.append(incoming - 1)
    index = 0
    while index < incoming and index < len(steps):
        step = steps[index]
        if step.get("required") and step.get("type") in {"ai_conversation", "survey"}:
            await proof(index, responses.get(f"step_{index}"))
        index = _next_step(steps, index, responses.get(f"step_{index}"))
    if body.get("status") == "complete":
        index = 0
        while index < len(steps):
            step = steps[index]
            response = responses.get(f"step_{index}")
            if step.get("required"):
                if index not in completed:
                    raise ApiError(409, "Complete every required step on this journey path before finishing", {"step_key": f"step_{index}"})
                if step.get("type") in {"ai_conversation", "survey"}:
                    await proof(index, response)
            index = _next_step(steps, index, response)
    return canonical_genplan_inputs(journey, responses), sorted(set(completed))


def canonical_genplan_inputs(journey, responses):
    """Derive plan output atomically from saved choices and current source."""
    responses = dict(responses)
    genplan = {}
    for index, step in enumerate(journey.content_sequence or []):
        saved = responses.get(f"step_{index}")
        if step.get("type") != "choice" or not isinstance(saved, dict) or saved.get("choice") is None:
            continue
        selected = next((choice for choice in step.get("choices", []) if isinstance(choice, dict) and choice.get("value") == saved["choice"]), None)
        if selected is None:
            raise ApiError(409, "This saved choice is no longer configured in the current journey")
        genplan[str(index)] = {"section_key": step.get("section_key"), "choice_key": selected["value"], "choice_label": selected.get("label"), "choice_index": selected.get("choice_index"), "output_text": selected.get("description") or selected.get("label")}
    responses["genplan_inputs"] = genplan
    return responses
