"""Typed Decisions API contracts without network or credentials."""

from __future__ import annotations

import asyncio
import json
import urllib.error
from io import BytesIO

import pytest

from neos_agent.ai import decisions


def _request():
    return {
        "model": "typesafe/jev-1.14-20261014",
        "state": {"message": "Explain consent"},
        "questions": {
            "needed": {"type": "noul", "instructions": "Is a workflow useful?"},
            "route": {"type": "choice", "instructions": "Which context?", "criteria": {"platform": "App help", "framework": "Governance concepts"}},
        },
    }


def _response():
    return {
        "model": "typesafe/jev-1.14-20261014",
        "answers": {
            "needed": {"type": "noul", "noul": 0.1},
            "route": {"type": "choice", "choice": "framework", "probabilities": {"platform": 0.1, "framework": 0.9}, "confidence": 0.8},
        },
        "usage": {"input_tokens": 150, "output_tokens": 12, "cost": 0.00001},
    }


def test_valid_typed_response_retains_raw_probability_and_usage():
    response = decisions.parse_response(_response(), _request())
    assert response.answers["needed"]["noul"] == 0.1
    assert response.answers["route"]["probabilities"] == {"platform": 0.1, "framework": 0.9}
    assert response.usage == decisions.DecisionUsage(150, 12, 0.00001)


def test_optional_api_fields_need_not_be_present():
    raw = _response()
    del raw["answers"]["route"]["probabilities"]
    del raw["answers"]["route"]["confidence"]
    del raw["usage"]
    assert decisions.parse_response(raw, _request()).answers["route"] == {"type": "choice", "choice": "framework"}


@pytest.mark.parametrize("model", [
    "typesafe/jev-1.14-20261015",
    "perplexity/pplx-decider-flash-v1.2-20261016",
])
def test_different_pinned_build_cannot_replace_the_calibrated_model(model):
    raw = _response()
    raw["model"] = model
    with pytest.raises(decisions.DecisionError, match="does not match the requested build"):
        decisions.parse_response(raw, _request())


@pytest.mark.parametrize("model", [None, True, "", "typesafe/jev-latest", "~typesafe/jev-latest", "anthropic/fake-decider-20261014"])
def test_malformed_or_disallowed_response_model_is_rejected(model):
    raw = _response()
    raw["model"] = model
    with pytest.raises(decisions.DecisionError):
        decisions.parse_response(raw, _request())


@pytest.mark.parametrize("value", [True, -0.1, 1.1, 10 ** 500, float("nan"), float("inf"), "0.9", None])
def test_non_probabilities_cannot_control_a_route(value):
    raw = _response()
    raw["answers"]["needed"]["noul"] = value
    with pytest.raises(decisions.DecisionError):
        decisions.parse_response(raw, _request())


@pytest.mark.parametrize("change", [
    lambda raw: raw["answers"].pop("needed"),
    lambda raw: raw["answers"].update(extra={"type": "noul", "noul": 0.5}),
    lambda raw: raw["answers"]["needed"].update(type="choice"),
    lambda raw: raw["answers"]["route"].update(choice="invented-skill"),
    lambda raw: raw["answers"]["route"].update(probabilities={"platform": 1}),
    lambda raw: raw["answers"]["route"].update(probabilities={"platform": 0, "framework": 0.5, "injected": 0.5}),
    lambda raw: raw["answers"]["route"].update(confidence=float("nan")),
    lambda raw: raw.update(usage={"input_tokens": 1.5}),
    lambda raw: raw.update(usage={"cost": -1}),
])
def test_malformed_typed_answers_are_rejected(change):
    raw = _response()
    change(raw)
    with pytest.raises(decisions.DecisionError):
        decisions.parse_response(raw, _request())


@pytest.mark.parametrize("change", [
    lambda request: request.update(model="typesafe/jev-latest"),
    lambda request: request.update(model="anthropic/fake-decider-20261014"),
    lambda request: request.update(model="~typesafe/jev-latest"),
    lambda request: request.update(provider={"order": ["untrusted"]}),
    lambda request: request["questions"]["route"].update(criteria={"only": "One option"}),
    lambda request: request["questions"]["needed"].update(type="chat"),
    lambda request: request["questions"]["needed"].update(criteria={"yes": "wrong", "no": "wrong"}),
    lambda request: request.update(state={"bad": float("nan")}),
    lambda request: request.update(state={"long": "x" * 256_001}),
])
def test_invalid_requests_are_rejected_before_network(change):
    request = _request()
    change(request)
    with pytest.raises(decisions.DecisionError):
        decisions.validate_request(request)


async def test_transport_uses_the_decisions_endpoint_and_bearer_header(monkeypatch):
    captured = {}

    class Reply(BytesIO):
        pass

    class Opener:
        def open(self, request, timeout):
            captured.update(url=request.full_url, header=request.get_header("Authorization"), body=json.loads(request.data), timeout=timeout)
            return Reply(json.dumps(_response()).encode())

    monkeypatch.setattr(decisions.urllib.request, "build_opener", lambda handler: Opener())
    result = await decisions.decide(_request(), api_key="unit-test-only", timeout=1)
    assert result.answers["route"]["choice"] == "framework"
    assert captured == {"url": decisions.DECISIONS_URL, "header": "Bearer unit-test-only", "body": _request(), "timeout": 1}
    assert decisions._NoRedirect().redirect_request(None, None, 302, None, None, "https://elsewhere.invalid") is None


async def test_provider_error_does_not_expose_authentication_or_body(monkeypatch):
    class Opener:
        def open(self, request, timeout):
            raise urllib.error.HTTPError(request.full_url, 429, "key=unit-secret", {}, BytesIO(b"private provider body"))

    monkeypatch.setattr(decisions.urllib.request, "build_opener", lambda handler: Opener())
    with pytest.raises(decisions.DecisionError, match="service is unavailable") as error:
        await decisions.decide(_request(), api_key="unit-secret", timeout=1)
    assert "unit-secret" not in str(error.value)
    assert "private" not in str(error.value)


async def test_slow_transport_is_bounded(monkeypatch):
    async def stalled(*args, **kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(decisions.asyncio, "to_thread", stalled)
    with pytest.raises(decisions.DecisionError, match="timed out"):
        await decisions.decide(_request(), api_key="unit-test-only", timeout=0.25)


async def test_invalid_key_never_reaches_transport(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("Network must not run")

    monkeypatch.setattr(decisions, "_post", unexpected)
    with pytest.raises(decisions.DecisionError):
        await decisions.decide(_request(), api_key="")
