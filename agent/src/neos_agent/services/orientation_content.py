"""Entrant-safe journey sources and version binding; see api/ORIENTATION_MATCHING.md."""
import hashlib
import json

GRADING_KEYS = frozenset({"correctanswer", "correctanswers", "answerkey", "answerkeys", "answerexplanation", "correctanswerhtml", "correctanswertext", "solution", "solutions", "solutionhtml", "solutiontext", "scoringrules", "grading"})


def entrant_content(value):
    """Recursively remove grading secrets from entrant/model journey content."""
    if isinstance(value, dict):
        return {key: entrant_content(item) for key, item in value.items() if "".join(char for char in str(key).lower() if char.isalnum()) not in GRADING_KEYS}
    if isinstance(value, list):
        return [entrant_content(item) for item in value]
    return value


def journey_fingerprint(journey):
    value = {"id": str(journey.id), "title": journey.title, "description": journey.description,
             "content_sequence": journey.content_sequence, "exit_package": journey.exit_package}
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def validate_ai_step(journey, step_id):
    from neos_agent.api.errors import ApiError
    if step_id is None:
        return None
    steps = journey.content_sequence if isinstance(journey.content_sequence, list) else []
    try:
        prefix, number = step_id.split("_", 1)
        index = int(number)
        valid = prefix == "step" and step_id == f"step_{index}" and 0 <= index < len(steps) and steps[index].get("type") == "ai_conversation"
    except (AttributeError, TypeError, ValueError):
        valid = False
    if not valid:
        raise ApiError(400, "Choose an AI conversation step from this journey")
    return step_id


def validate_journey_routes(steps, *, status=400):
    """Require named choices and forward, in-range destinations in authored routes."""
    from neos_agent.api.errors import ApiError
    if not isinstance(steps, list) or len(steps) > 500 or any(not isinstance(step, dict) for step in steps):
        raise ApiError(status, "This journey needs a list of at most 500 steps")
    for index, step in enumerate(steps):
        routes = step.get("choice_routes", {})
        if not isinstance(routes, dict) or (routes and step.get("type") != "choice"):
            raise ApiError(status, "Only choice steps can declare choice routes")
        if step.get("type") != "choice":
            continue
        choices = step.get("choices")
        if not isinstance(choices, list) or not choices or any(not isinstance(choice, dict) or not isinstance(choice.get("value"), str) or not choice["value"].strip() for choice in choices):
            raise ApiError(status, "Each choice step needs named choices")
        names = [choice["value"] for choice in choices]
        if len(set(names)) != len(names) or any(name not in names for name in routes):
            raise ApiError(status, "Choice routes must reference unique configured choices")
        if any(type(destination) is not int or not index < destination <= len(steps) for destination in routes.values()):
            raise ApiError(status, "Choice destinations must be later steps or the end of this journey")
