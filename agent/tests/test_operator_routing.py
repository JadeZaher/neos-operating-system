"""Operator routing and bounded lookups through the real SSE endpoint."""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from neos_agent.agent import skill_decision
from neos_agent.db.models import AgentSession, Proposal
from tests.test_g_agent_assistant import _events, _model_turn, _proposal, _tool, env  # noqa: F401
from tests.test_system_prompt import _make_skill, _mock_registry


def _decision(mode, skill=None, source="decision"):
    return SimpleNamespace(mode=mode, skill=skill, source=source,
                           as_event=lambda: {"mode": mode, "skill": skill, "source": source})


async def _send(env, script, decision, **body):
    model = AsyncMock(side_effect=script)
    selector = AsyncMock(return_value=decision)
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), \
         patch("neos_agent.api.chat.acompletion", new=model), \
         patch("neos_agent.api.chat.select_skill", new=selector):
        _, response = await env.app.asgi_client.post(
            "/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Help me", "history": [], **body},
        )
    assert response.status == 200, response.text
    return _events(response.text), model, selector


async def test_direct_answer_clears_previous_skill_in_sse_and_saved_session(env):
    events, model, selector = await _send(
        env, [_model_turn("Consent is not a vote.")], _decision("framework"),
        message="What does consent mean?", active_skill="proposal-creation",
    )
    [route] = [json.loads(data) for kind, data in events if kind == "skill_route"]
    assert route == {"mode": "framework", "skill": None, "source": "decision"}
    assert selector.call_args.kwargs["previous_skill"] == "proposal-creation"
    assert "Answer a governance question directly" in model.call_args.kwargs["system"]
    session_id = next(json.loads(data)["session_id"] for kind, data in events if kind == "session")
    async with env.db() as db:
        assert (await db.get(AgentSession, uuid.UUID(session_id))).skill_name is None


async def test_manual_skill_request_is_separate_from_automatic_prior_hint(env):
    env.app.ctx.skills = _mock_registry(_make_skill("proposal-creation"))
    events, model, selector = await _send(
        env, [_model_turn("What change do you want to propose?")],
        _decision("skill", "proposal-creation", "manual"),
        requested_skill="proposal-creation", active_skill="voluntary-exit",
    )
    assert selector.call_args.kwargs["requested_skill"] == "proposal-creation"
    assert selector.call_args.kwargs["previous_skill"] == "voluntary-exit"
    assert "## Active Skill: proposal-creation" in model.call_args.kwargs["system"]
    assert json.loads(next(data for kind, data in events if kind == "skill_route"))["source"] == "manual"


@pytest.mark.parametrize("invalid_manual", [True, False])
async def test_invalid_explicit_manual_skill_does_not_trigger_automatic_classification(env, invalid_manual):
    env.app.ctx.skills = _mock_registry(_make_skill("proposal-creation"))
    selector = AsyncMock(wraps=skill_decision.select_skill)
    classifier = AsyncMock()
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), \
         patch("neos_agent.api.chat.acompletion", new=AsyncMock(return_value=_model_turn("How can I help?"))), \
         patch("neos_agent.api.chat.select_skill", new=selector), \
         patch("neos_agent.agent.skill_decision.get_settings") as settings, \
         patch("neos_agent.agent.skill_decision.decide", new=classifier):
        _, response = await env.app.asgi_client.post(
            "/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Help me", "requested_skill": invalid_manual, "active_skill": "proposal-creation"},
        )
    assert response.status == 200, response.text
    assert selector.call_args.kwargs["requested_skill"] is invalid_manual
    settings.assert_not_called()
    classifier.assert_not_awaited()
    routes = [json.loads(data) for kind, data in _events(response.text) if kind == "skill_route"]
    assert routes == [{"mode": "general", "skill": None, "source": "fallback"}]


async def test_terminal_tool_transition_clears_skill_in_stream_prompt_and_session(env):
    env.app.ctx.skills = _mock_registry(_make_skill("governance-health-audit"))
    events, model, _ = await _send(env, [
        _model_turn(calls=(("create_safeguard_audit", {"findings": "Participation is healthy."}),)),
        _model_turn("Your audit draft is ready."),
    ], _decision("skill", "governance-health-audit"))
    routes = [json.loads(data) for kind, data in events if kind == "skill_route"]
    assert routes[-1] == {"mode": "general", "skill": None, "source": "transition"}
    assert json.loads(next(data for kind, data in events if kind == "skill_transition")) == {
        "from": "governance-health-audit", "to": None,
    }
    assert "## Active Skill:" not in model.call_args_list[-1].kwargs["system"]
    session_id = next(json.loads(data)["session_id"] for kind, data in events if kind == "session")
    async with env.db() as db:
        assert (await db.get(AgentSession, uuid.UUID(session_id))).skill_name is None


@pytest.mark.parametrize("queries", [["Private workshop", "Private workshop"], ["one", "two", "three", "four"]])
async def test_unresolved_searches_stop_with_useful_scope_help_instead_of_exhausting_loop(env, queries):
    script = [_model_turn(calls=(("search_proposals", {"query": query}),)) for query in queries]
    events, model, _ = await _send(env, script, _decision("general", source="fallback"))
    text = "".join(data for kind, data in events if kind == "append")
    assert "ecosystems you selected" in text and "not a member" in text
    assert "wasn't able to generate" not in text
    assert model.await_count == len(queries)
    results = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert results[0]["success"] is True
    assert results[-1]["success"] is False
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Proposal)) == 0


async def test_prelookup_model_narration_is_not_streamed_as_a_live_record_claim(env):
    proposal = await _proposal(env)
    events, _, _ = await _send(env, [
        _model_turn("It moved to consent automatically.", calls=(("get_proposal", {"proposal_id": str(proposal.id)}),)),
        _model_turn("It is still in advice. Its author chooses when to close advice."),
    ], _decision("general", source="fallback"))
    text = "".join(data for kind, data in events if kind == "append")
    assert "moved to consent automatically" not in text
    assert "still in advice" in text
    session_id = next(json.loads(data)["session_id"] for kind, data in events if kind == "session")
    async with env.db() as db:
        saved = (await db.get(AgentSession, uuid.UUID(session_id))).context["messages"]
    assert "moved to consent automatically" not in json.dumps(saved)
    assert all(not message.get("tool_calls") for message in saved)


async def test_disabled_assistant_explicitly_clears_prior_routing_state(env):
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=False):
        _, response = await env.app.asgi_client.post(
            "/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Help", "active_skill": "proposal-creation"},
        )
    routes = [json.loads(data) for kind, data in _events(response.text) if kind == "skill_route"]
    assert routes == [{"mode": "general", "skill": None, "source": "fallback"}]


async def test_created_draft_returns_the_actual_change_and_reason_for_review(env):
    draft = {"title": "Repair cafe", "type": "operational", "proposed_change": "Hold a monthly repair cafe.",
             "rationale": "Members want to repair things together."}
    result = await _tool(env, "ben", "create_proposal", **draft)
    assert result["success"] is True
    async with env.db() as db:
        stored = await db.get(Proposal, uuid.UUID(result["data"]["id"]))
    assert stored.status == "draft"
    assert result["data"]["proposed_change"] == stored.proposed_change == draft["proposed_change"]
    assert result["data"]["rationale"] == stored.rationale == draft["rationale"]
    assert "Review" in result["data"]["next_step"]
