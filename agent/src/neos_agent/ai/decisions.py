"""Validated access to OpenRouter's typed Decisions API; see ai/AGENTS.md."""

from __future__ import annotations

import asyncio
import json
import math
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
_MAX_RESPONSE_BYTES = 1_000_000
_MAX_REQUEST_BYTES = 256_000
_PINNED_MODEL = re.compile(r"^[a-z0-9_.-]+/[a-zA-Z0-9_.-]+-\d{8}$")


class DecisionError(ValueError):
    """A decision request or response is invalid or unavailable."""


@dataclass(frozen=True)
class DecisionUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None


@dataclass(frozen=True)
class DecisionResponse:
    model: str
    answers: dict[str, dict[str, Any]]
    usage: DecisionUsage = DecisionUsage()


def _number(value: Any, *, probability: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DecisionError("Decision number must be finite")
    try:
        number = float(value)
    except OverflowError:
        raise DecisionError("Decision number must be finite") from None
    if not math.isfinite(number):
        raise DecisionError("Decision number must be finite")
    if number < 0 or (probability and number > 1):
        raise DecisionError("Decision number is outside its range")
    return number


def validate_request(request: dict) -> bytes:
    """Validate the text-only noul/choice contract before any network access."""
    if not isinstance(request, dict) or set(request) != {"model", "state", "questions"}:
        raise DecisionError("Decision request needs model, state and questions")
    model = request["model"]
    if not isinstance(model, str) or not _PINNED_MODEL.fullmatch(model) or model.startswith("anthropic/"):
        raise DecisionError("Decision model must be a pinned non-Anthropic build")
    if not isinstance(request["state"], (dict, list, str)):
        raise DecisionError("Decision state must be JSON state")
    questions = request["questions"]
    if not isinstance(questions, dict) or not questions:
        raise DecisionError("Decision questions must be a non-empty map")
    for key, question in questions.items():
        if not isinstance(key, str) or not key or not isinstance(question, dict):
            raise DecisionError("Decision question is invalid")
        if set(question) - {"type", "instructions", "criteria"}:
            raise DecisionError("Decision question has unsupported fields")
        if not isinstance(question.get("instructions"), str) or not question["instructions"].strip():
            raise DecisionError("Decision question needs instructions")
        criteria = question.get("criteria")
        if question.get("type") == "noul":
            if criteria is not None and (not isinstance(criteria, dict) or set(criteria) != {"true", "false"}):
                raise DecisionError("Noul criteria must describe true and false")
        elif question.get("type") == "choice":
            if not isinstance(criteria, dict) or len(criteria) < 2 or not all(isinstance(k, str) and k for k in criteria):
                raise DecisionError("Choice needs at least two named options")
        else:
            raise DecisionError("Only noul and choice questions are supported")
        if criteria is not None and not all(isinstance(v, str) and v.strip() for v in criteria.values()):
            raise DecisionError("Decision criteria need non-empty descriptions")
    try:
        encoded = json.dumps(request, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DecisionError("Decision request is not finite JSON") from error
    if len(encoded) > _MAX_REQUEST_BYTES:
        raise DecisionError("Decision request exceeds its size budget")
    return encoded


def parse_response(raw: Any, request: dict) -> DecisionResponse:
    """Validate types, probabilities and candidate identities against the request."""
    if not isinstance(raw, dict) or not isinstance(raw.get("model"), str) or not raw["model"]:
        raise DecisionError("Decision response needs a model")
    if not _PINNED_MODEL.fullmatch(raw["model"]) or raw["model"].startswith("anthropic/"):
        raise DecisionError("Decision response model must be a pinned non-Anthropic build")
    if raw["model"] != request["model"]:
        raise DecisionError("Decision response model does not match the requested build")
    answers = raw.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(request["questions"]):
        raise DecisionError("Decision answers do not match the questions")
    parsed = {}
    for key, question in request["questions"].items():
        answer = answers[key]
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            raise DecisionError("Decision answer has the wrong type")
        if question["type"] == "noul":
            parsed[key] = {"type": "noul", "noul": _number(answer.get("noul"), probability=True)}
            continue
        choice = answer.get("choice")
        if not isinstance(choice, str) or choice not in question["criteria"]:
            raise DecisionError("Decision chose an unknown candidate")
        clean = {"type": "choice", "choice": choice}
        if "probabilities" in answer:
            probabilities = answer["probabilities"]
            if not isinstance(probabilities, dict) or set(probabilities) != set(question["criteria"]):
                raise DecisionError("Decision probability candidates do not match")
            clean["probabilities"] = {name: _number(value, probability=True) for name, value in probabilities.items()}
        if "confidence" in answer:
            clean["confidence"] = _number(answer["confidence"], probability=True)
        parsed[key] = clean
    usage = raw.get("usage")
    if usage is not None and not isinstance(usage, dict):
        raise DecisionError("Decision usage is invalid")
    usage = usage or {}
    tokens = []
    for name in ("input_tokens", "output_tokens"):
        value = _number(usage.get(name, 0))
        if not value.is_integer():
            raise DecisionError("Decision token count must be an integer")
        tokens.append(int(value))
    cost = _number(usage["cost"]) if "cost" in usage else None
    return DecisionResponse(raw["model"], parsed, DecisionUsage(*tokens, cost))


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _post(encoded: bytes, *, api_key: str, timeout: float) -> Any:
    request = urllib.request.Request(
        DECISIONS_URL,
        data=encoded,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout) as response:
            body = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(body) > _MAX_RESPONSE_BYTES:
            raise DecisionError("Decision response exceeds its size budget")
        return json.loads(body)
    except (urllib.error.URLError, OSError, UnicodeError, json.JSONDecodeError):
        raise DecisionError("Decision service is unavailable") from None


async def decide(request: dict, *, api_key: str, timeout: float = 6.0) -> DecisionResponse:
    """Submit one bounded request; authentication and provider errors stay private."""
    encoded = validate_request(request)
    if not isinstance(api_key, str) or not api_key.strip():
        raise DecisionError("Decision service needs a configured key")
    timeout = _number(timeout)
    if not 0.25 <= timeout <= 15:
        raise DecisionError("Decision timeout is outside its bounds")
    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_post, encoded, api_key=api_key, timeout=timeout), timeout=timeout + 0.25)
    except TimeoutError:
        raise DecisionError("Decision service timed out") from None
    return parse_response(raw, request)
