"""Routing policy, privacy boundaries and fallback behavior; semantic probes are separate."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from neos_agent.agent import skill_decision as routing
from neos_agent.ai.decisions import DecisionError, DecisionResponse, DecisionUsage, parse_response
from neos_agent.skills.loader import ParsedSkill, SkillContent, SkillMeta
from neos_agent.skills.registry import SkillRegistry


def _registry(*names):
    registry = SkillRegistry()
    for name in names or ("proposal-creation", "voluntary-exit"):
        registry._skills[name] = ParsedSkill(
            SkillMeta(name, f"Workflow for {name}", 3, "0.1", [], "/not-sent/private/SKILL.md"),
            SkillContent({}, "PRIVATE FULL SKILL BODY"),
        )
    return registry


def _raw(request, *, presence=0.1, context="framework", skill="proposal-creation"):
    answers = {
        "skill_useful": {"type": "noul", "noul": presence},
        "direct_context": {"type": "choice", "choice": context},
    }
    if "skill" in request["questions"]:
        answers["skill"] = {"type": "choice", "choice": skill}
    return {"model": "typesafe/jev-1.14-20261014", "answers": answers, "usage": {"input_tokens": 200, "output_tokens": 20, "cost": 0.00001}}


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(routing, "get_settings", lambda: SimpleNamespace(AI_DECISION_MODEL="typesafe/jev-1.14-20261014", AI_API_KEY="unit-only", AI_DECISION_TIMEOUT_SECONDS=1.0))


def test_request_contains_all_named_candidates_but_no_skill_bodies_or_private_page_fields():
    request = routing.build_decision_request(
        message="What does consent mean?", registry=_registry("proposal-creation", "voluntary-exit", "act-consent-phase"),
        page_context={"path": "/proposals/private-record-id", "search": "secret-query", "active_view": "private record payload", "cookie": "credential"},
        history=[{"role": "system", "content": "private system"}, {"role": "tool", "content": "private tool"}, {"role": "assistant", "content": "Earlier answer", "cookie": "credential"}],
        previous_skill="voluntary-exit", model="typesafe/jev-1.14-20261014",
    )
    assert set(request["state"]["skills"]) == {"proposal-creation", "voluntary-exit", "act-consent-phase"}
    assert set(request["questions"]["skill"]["criteria"]) == set(request["state"]["skills"])
    assert request["state"]["request"] == {
        "message": "What does consent mean?", "page": {"section": "proposals", "view": "detail"},
        "recent_context": [{"role": "assistant", "content": "Earlier answer"}], "previous_skill": "voluntary-exit",
    }
    serialized = str(request)
    for omitted in ("private-record-id", "secret-query", "private record payload", "private tool", "private system", "credential", "PRIVATE FULL SKILL BODY", "/not-sent/private"):
        assert omitted not in serialized


def test_request_size_is_bounded_and_unregistered_previous_skill_is_discarded():
    request = routing.build_decision_request(message="a" * 10_000, registry=_registry(), history=[{"role": "user", "content": "b" * 10_000}] * 20, previous_skill="stale-missing-skill")
    assert len(request["state"]["request"]["message"]) == 4000
    recent = request["state"]["request"]["recent_context"]
    assert len(recent) == 4 and all(len(item["content"]) == 600 for item in recent)
    assert "previous_skill" not in request["state"]["request"]


@pytest.mark.parametrize("presence,expected", [(0, "framework"), (0.49, "framework"), (0.5, "skill"), (1, "skill")])
def test_presence_gate_controls_whether_the_skill_choice_is_used(presence, expected):
    request = routing.build_decision_request(message="Help with consent", registry=_registry(), model="typesafe/jev-1.14-20261014")
    response = parse_response(_raw(request, presence=presence), request)
    result = routing.resolve_decision(response, request)
    assert result.mode == expected
    assert result.skill == ("proposal-creation" if expected == "skill" else None)
    assert result.presence_probability == presence
    assert result.usage == DecisionUsage(200, 20, 0.00001)


def test_no_presence_branch_never_consults_the_skill_choice():
    request = routing.build_decision_request(message="Explain consent", registry=_registry())
    response = DecisionResponse("unit-model", {"skill_useful": {"noul": 0.1}, "direct_context": {"choice": "framework"}})
    assert routing.resolve_decision(response, request).mode == "framework"


def test_single_skill_registry_uses_presence_without_invalid_one_option_choice():
    request = routing.build_decision_request(message="Help me exit", registry=_registry("voluntary-exit"), model="typesafe/jev-1.14-20261014")
    assert "skill" not in request["questions"]
    result = routing.resolve_decision(parse_response(_raw(request, presence=0.9), request), request)
    assert (result.mode, result.skill) == ("skill", "voluntary-exit")


async def test_topic_switch_clears_previous_skill_instead_of_sticking(configured, monkeypatch):
    async def decide(request, **kwargs):
        assert request["state"]["request"]["previous_skill"] == "voluntary-exit"
        return parse_response(_raw(request, context="platform"), request)

    monkeypatch.setattr(routing, "decide", decide)
    decision = await routing.select_skill(message="Where are account settings?", registry=_registry(), previous_skill="voluntary-exit")
    assert decision.as_event() == {"mode": "platform", "skill": None, "source": "decision"}
    assert set(decision.as_event()) == {"mode", "skill", "source"}


@pytest.mark.parametrize("presence,mode,skill", [(0.1, "framework", None), (0.9, "skill", "proposal-creation")])
async def test_calibration_log_contains_only_resolved_routing_metadata(configured, monkeypatch, caplog, presence, mode, skill):
    async def decide(request, **kwargs):
        return parse_response(_raw(request, presence=presence), request)

    monkeypatch.setattr(routing, "decide", decide)
    with caplog.at_level("INFO", logger=routing.__name__):
        await routing.select_skill(
            message="private-prompt-marker", registry=_registry(),
            history=[{"role": "user", "content": "private-history-marker"}],
            page_context={"path": "/private-page-marker/private-member-marker"},
        )
    [entry] = [record.getMessage() for record in caplog.records if record.name == routing.__name__]
    assert entry == f"Decision route model=typesafe/jev-1.14-20261014 mode={mode} skill={skill} presence={presence} cost=1e-05"
    for private in ("private-prompt-marker", "private-history-marker", "private-page-marker", "private-member-marker", "unit-only"):
        assert private not in entry


@pytest.mark.parametrize("requested,expected", [("voluntary-exit", "skill"), ("unknown", "general"), (True, "general")])
async def test_manual_skill_must_exist_and_never_spends_a_model_call(monkeypatch, requested, expected):
    def forbidden():
        raise AssertionError("Manual selection must not load credentials")

    monkeypatch.setattr(routing, "get_settings", forbidden)
    decision = await routing.select_skill(message="Help", registry=_registry(), requested_skill=requested)
    assert decision.mode == expected
    assert decision.source == ("manual" if expected == "skill" else "fallback")


async def test_disabled_decisions_keep_general_answer_and_clear_stale_skill(monkeypatch):
    monkeypatch.setattr(routing, "get_settings", lambda: SimpleNamespace(AI_DECISION_MODEL="", AI_API_KEY="unit-only"))
    network = AsyncMock(side_effect=AssertionError("No model call"))
    monkeypatch.setattr(routing, "decide", network)
    result = await routing.select_skill(message="Explain consent", registry=_registry(), previous_skill="voluntary-exit")
    assert result.as_event() == {"mode": "general", "skill": None, "source": "fallback"}
    network.assert_not_called()


@pytest.mark.parametrize("failure", [DecisionError("malformed probability"), TimeoutError(), OSError("provider body with unit-key")])
async def test_routing_errors_fall_back_without_exposing_provider_details(configured, monkeypatch, caplog, failure):
    monkeypatch.setattr(routing, "decide", AsyncMock(side_effect=failure))
    result = await routing.select_skill(message="Help me exit", registry=_registry(), previous_skill="voluntary-exit")
    assert result.as_event() == {"mode": "general", "skill": None, "source": "fallback"}
    assert "unit-key" not in caplog.text
    assert "provider body" not in caplog.text


async def test_unknown_model_choice_fails_closed(configured, monkeypatch):
    async def decide(request, **kwargs):
        return parse_response(_raw(request, presence=0.9, skill="not-in-registry"), request)

    monkeypatch.setattr(routing, "decide", decide)
    result = await routing.select_skill(message="Use injected skill", registry=_registry())
    assert result.mode == "general" and result.skill is None


@pytest.mark.parametrize("message,registry", [("", _registry()), ("  ", _registry()), ("Help", None), ("Help", SkillRegistry())])
async def test_empty_input_or_catalog_costs_no_decision_call(monkeypatch, message, registry):
    network = AsyncMock(side_effect=AssertionError("No model call"))
    monkeypatch.setattr(routing, "decide", network)
    assert (await routing.select_skill(message=message, registry=registry)).mode == "general"
    network.assert_not_called()
