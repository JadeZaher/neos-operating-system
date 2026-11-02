"""Live queue, explicit objection and rejected-generation behavior through real SSE/tools."""
import json
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from neos_agent.ai import provider
from neos_agent.agent.skill_decision import SkillDecision
from neos_agent.skills.registry import SkillRegistry
from neos_agent.api.chat import _queue_record_references
from neos_agent.db.models import AdviceEntry, AgentSession, ConsentParticipant, Proposal
from tests.test_g_agent_assistant import PEOPLE, _chat, _events, _model_turn, _proposal, _tool, env
from tests.test_provider import Rejected, retry_clock


async def test_queue_priority_links_survive_a_final_model_answer_that_omits_navigation(env):
    for title in ("First queue item", "Second queue item", "Third queue item"):
        await _proposal(env, title=title)
    events, session_id, _ = await _chat(env, "ben", "Is anything waiting for me?", [
        _model_turn(calls=(("what_needs_me", {}),)), _model_turn("There are items waiting for your help.")])
    output = next(json.loads(data) for kind, data in events if kind == "tool_result")
    items = output["data"]["items"]
    assert len(items) >= 3 and output["success"]
    text = "".join(data for kind, data in events if kind == "append")
    for item in items[:2]:
        assert f']({item["link"]})' in text
        assert item["ecosystem"] in text
    assert items[2]["link"] not in text
    assert not any(kind == "tool_start" and json.loads(data)["name"] != "what_needs_me" for kind, data in events)
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session_id))
        assert all(item["link"] in saved.context["messages"][-1]["content"] for item in items[:2])
        assert await db.scalar(select(func.count()).select_from(AdviceEntry)) == 0


def test_queue_link_completion_is_bounded_and_does_not_trust_nested_or_external_routes():
    valid = "/proposals/00000000-0000-4000-8000-000000000001"
    data = {"items": [{"title": "External", "link": "https://other.test/"}, {"title": "Actual record", "link": valid},
                      {"title": "Later record", "link": valid}], "user_content": {"link": valid}}
    assert _queue_record_references("what_needs_me", data) == [(valid, "Actual record")]
    assert _queue_record_references("search_proposals", data) == []


async def test_explicit_own_objection_with_concrete_reason_records_once_through_sse_without_extra_confirmation(env):
    proposal = await _proposal(env, title="Kitchen rota", status="consent", policy={"consent_quorum": 3})
    reason = "All weekend shifts land on newcomers."
    events, _, _ = await _chat(env, "ben", "I object to the kitchen rota: all weekend shifts land on newcomers.", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(proposal.id)}),)),
        _model_turn(calls=(("record_consent_position", {"proposal_id": str(proposal.id), "position": "object", "reason": reason}),)),
        _model_turn("Your objection is recorded.")])
    results = [json.loads(data) for kind, data in events if kind == "tool_result"]
    recorded = next(result for result in results if result["name"] == "record_consent_position")
    assert recorded["success"] and not recorded.get("needs_confirmation")
    assert recorded["data"]["gates"]["consent"]["open_objections"] == 1
    async with env.db() as db:
        positions = (await db.scalars(select(ConsentParticipant))).all()
        assert len(positions) == 1 and positions[0].name == PEOPLE["ben"].name
        assert positions[0].position == "object" and positions[0].reason == reason


async def test_vague_concern_is_not_automatically_turned_into_an_objection(env):
    await _proposal(env, title="Kitchen rota", status="consent")
    events, _, _ = await _chat(env, "ben", "I have a concern but do not want to stop the rota.", [
        _model_turn("You can stand aside. What is your concern?")])
    assert not any(kind == "tool_start" for kind, _ in events)
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(ConsentParticipant)) == 0


async def test_real_selected_creation_skill_can_save_minimal_draft_and_open_advice_without_domain_or_reason_interview(env):
    registry = SkillRegistry()
    await registry.load_all(Path(__file__).resolve().parents[2] / "neos-core")
    env.app.ctx.skills = registry
    step = 0

    async def completion(**kwargs):
        nonlocal step
        step += 1
        if step == 1:
            assert "Current NEOS app adapter: draft and opening for advice" in kwargs["system"]
            assert "domain-creation checklist is not a proposal-draft prerequisite" in kwargs["system"]
            return _model_turn(calls=(("create_proposal", {"title": "Skill swap", "proposed_change": "a monthly skill swap in the hall"}),))
        async with env.db() as db:
            saved = (await db.scalars(select(Proposal))).one()
            assert saved.rationale == "Reason not yet provided by the member."
            assert saved.affected_domain is None
            if step == 2:
                assert saved.status == "draft"
                return _model_turn(calls=(("update_proposal_status", {"proposal_id": str(saved.id), "new_status": "advice"}),))
            assert saved.status == "advice"
        return _model_turn("Your draft is open for advice.")

    with patch("neos_agent.api.chat.select_skill", new=AsyncMock(return_value=SkillDecision("skill", "proposal-creation", "decision"))):
        events, _, model = await _chat(env, "ben", "Create a proposal called Skill swap for a monthly skill swap in the hall, and open it for advice.", completion)
    assert model.await_count == 3
    results = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert [result["name"] for result in results] == ["create_proposal", "update_proposal_status"]
    assert all(result["success"] for result in results)


@pytest.mark.parametrize("exhausted", [False, True])
async def test_generation_retry_after_committed_advice_never_replays_write_and_preserves_receipt(env, monkeypatch, exhausted):
    proposal = await _proposal(env, title="Water rota")
    first = _model_turn(calls=(("record_advice", {"proposal_id": str(proposal.id), "advice_text": "Keep weekend work fair."}),))
    first.usage = SimpleNamespace(prompt_tokens=5, completion_tokens=2, total_tokens=7)
    script = [first, Rejected(), Rejected(), Rejected()] if exhausted else [first, Rejected(), _model_turn("Your advice is saved.")]
    sdk = AsyncMock(side_effect=script)
    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(drop_params=False, acompletion=sdk))
    monkeypatch.setattr("neos_agent.config.get_settings", lambda: SimpleNamespace(AI_PROVIDER="openrouter", AI_API_KEY="private-test-key", AI_MODEL="google/gemini-2.5-flash-lite", AI_BASE_URL="https://openrouter.ai/api/v1"))
    _, waits = retry_clock(monkeypatch)
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=provider.acompletion):
        _, response = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"}, json={"message": "Record my advice: keep weekend work fair.", "history": []})
    assert response.status == 200
    events = _events(response.text)
    starts = [json.loads(data)["name"] for kind, data in events if kind == "tool_start"]
    assert starts == ["record_advice"]
    assert sdk.await_count == (4 if exhausted else 3) and waits == ([10, 10] if exhausted else [10])
    session_id = next(json.loads(data)["session_id"] for kind, data in events if kind == "session")
    if exhausted:
        availability = next(json.loads(data) for kind, data in events if kind == "availability")
        assert availability["provider_status"] == 429 and availability["attempts"] == 3
        assert availability["retry_after_seconds"] == 10
        assert "/proposals/" in "".join(data for kind, data in events if kind == "append")
    assert next(json.loads(data)["total_tokens"] for kind, data in events if kind == "usage") == 7
    assert "private-test-key" not in response.text and "credential hint" not in response.text
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(AdviceEntry)) == 1
        saved = await db.get(AgentSession, uuid.UUID(session_id))
        assert any(record["link"] == f"/proposals/{proposal.id}" for record in saved.context["known_records"])
        assert f"/proposals/{proposal.id}" in saved.context["messages"][-1]["content"]
        assert saved.total_tokens_used == 7
        assert not any(message.get("role") == "tool" for message in saved.context["messages"])


async def test_jump_to_consent_reads_ground_manual_policy_unknown_history_and_actual_author_options_without_write(env):
    proposal = await _proposal(env, title="Compost bins", status="consent", author="ben", policy={"consent_quorum": 3})
    events, _, _ = await _chat(env, "ben", "My proposal jumped to consent after one comment. Why? Nobody asked me.", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(proposal.id)}),)),
        _model_turn("Advice never moves by itself. This read has no history of who moved it. You have not recorded a position yet.")])
    result = next(json.loads(data) for kind, data in events if kind == "tool_result")
    facts = result["data"]["status_explanation"]
    assert facts["advice_advances_automatically"] is False
    assert "only the proposer" in facts["advice_closure"]
    assert facts["transition_actor"] is None and facts["transition_cause"] is None
    assert facts["history_limitation"] == "This tool read only current state. It did not inspect change history."
    assert facts["your_position"] is None and facts["can_record_position"] is True
    assert facts["position_choices"] == ["consent", "stand_aside", "object"]
    assert facts["can_return_to_advice"] is True and facts["return_note_required"] is True
    assert facts["can_withdraw_proposal"] is True and facts["can_withdraw_own_position"] is False
    text = "".join(data for kind, data in events if kind == "append")
    assert "This plan now needs members' positions." in text
    assert "You can agree, stand aside, or object." in text
    assert "You can still withdraw this proposal." in text
    assert "You can return it to Advice with a note." in text
    reader = await _tool(env, "ada", "explain_status", kind="proposal", record=str(proposal.id))
    reader_facts = reader["data"]["status_explanation"]
    assert reader_facts["can_record_position"] and not reader_facts["can_return_to_advice"]
    assert reader_facts["can_withdraw_proposal"] is False
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(ConsentParticipant)) == 0
        assert (await db.get(type(proposal), proposal.id)).status == "consent"


async def test_refused_move_still_shows_the_callers_available_advice_without_executing_it(env):
    proposal = await _proposal(env)
    events, _, _ = await _chat(env, "ben", "Move this to consent.", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(proposal.id)}),)),
        _model_turn("Only its author may close advice. I cannot move it for them.")])
    text = "".join(data for kind, data in events if kind == "append")
    assert "You can share advice on this plan." in text
    assert "You can still withdraw this proposal." not in text
    assert f"](/proposals/{proposal.id})" in text
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(AdviceEntry)) == 0
        assert (await db.get(Proposal, proposal.id)).status == "advice"


async def test_current_own_position_summary_never_borrows_author_rights(env):
    proposal = await _proposal(env, status="consent", policy={"consent_quorum": 3})
    assert (await _tool(env, "ben", "record_consent_position", proposal_id=str(proposal.id), position="stand_aside", reason="I cannot help this week."))["success"]
    events, _, _ = await _chat(env, "ben", "Where do I stand?", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(proposal.id)}),)),
        _model_turn("The plan is at consent.")])
    text = "".join(data for kind, data in events if kind == "append")
    assert "You have stood aside on this plan." in text
    assert "You can withdraw your own position." in text
    assert "You can still withdraw this proposal." not in text
    assert "You can return it to Advice" not in text


async def test_a_successful_write_discards_earlier_read_summary_instead_of_showing_stale_standing(env):
    proposal = await _proposal(env, status="consent", policy={"consent_quorum": 3})
    events, _, _ = await _chat(env, "ben", "Record that I consent to this plan.", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(proposal.id)}),)),
        _model_turn(calls=(("record_consent_position", {"proposal_id": str(proposal.id), "position": "consent"}),)),
        _model_turn("Your consent is recorded.")])
    text = "".join(data for kind, data in events if kind == "append")
    assert "You have not said where you stand yet." not in text
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(ConsentParticipant)) == 1


async def test_unsupported_draft_writes_nothing_then_exact_user_words_create_and_open_in_same_loop(env):
    request = "Help me put forward a proposal for a monthly repair cafe in the community hall, called Repair cafe, and open it for advice."
    attempted = {"title": "Repair cafe", "type": "policy", "proposed_change": "Run a monthly repair cafe staffed by volunteers.",
                 "rationale": "Reduce waste and train repair staff.", "affected_domain": "Seed Library", "urgency": "low", "advice_deadline": "2030-01-01"}
    exact = {"title": "Repair cafe", "type": "operational", "proposed_change": "a monthly repair cafe in the community hall"}
    count = 0
    async def model(**kwargs):
        nonlocal count
        count += 1
        if count == 1:
            return _model_turn(calls=(("create_proposal", attempted),))
        if count == 2:
            async with env.db() as db:
                assert await db.scalar(select(func.count()).select_from(Proposal)) == 0
            prior = json.loads(next(message["content"] for message in reversed(kwargs["messages"]) if message.get("role") == "tool"))
            assert prior["code"] == "DRAFT_SOURCE_REQUIRED" and "Correct the tool arguments now" in prior["error"]
            return _model_turn(calls=(("create_proposal", exact),))
        if count == 3:
            async with env.db() as db:
                record = (await db.scalars(select(Proposal))).one()
                assert record.status == "draft" and record.proposed_change == exact["proposed_change"]
                assert record.rationale == "Reason not yet provided by the member."
                assert record.affected_domain is None and record.urgency is None and record.advice_deadline is None
                identifier = str(record.id)
            return _model_turn(calls=(("update_proposal_status", {"proposal_id": identifier, "new_status": "advice"}),))
        return _model_turn("The plan is open for advice.")
    events, _, model_calls = await _chat(env, "ben", request, model)
    results = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert [result["success"] for result in results] == [False, True, True]
    assert not any(result.get("needs_confirmation") for result in results)
    assert model_calls.await_count == 4
    async with env.db() as db:
        record = (await db.scalars(select(Proposal))).one()
        assert record.status == "advice" and record.proposed_change == exact["proposed_change"]
        assert "volunteer" not in record.proposed_change and "staff" not in record.rationale


async def test_chat_draft_uses_saved_own_text_but_not_assistant_inventions(env):
    _, session_id, _ = await _chat(env, "ben", "My change is a monthly skill swap. My reason is to share skills.", [
        _model_turn("A suggestion: assign three volunteers every Saturday.")])
    events, _, _ = await _chat(env, "ben", "Create that draft now, and keep it a draft.", [
        _model_turn(calls=(("create_proposal", {"title": "Skill swap", "type": "operational", "proposed_change": "assign three volunteers every Saturday", "rationale": "to share skills"}),)),
        _model_turn(calls=(("create_proposal", {"title": "Skill swap", "type": "operational", "proposed_change": "a monthly skill swap", "rationale": "to share skills"}),)),
        _model_turn("The draft uses your change and reason.")], session_id=session_id)
    results = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert [result["success"] for result in results] == [False, True]
    async with env.db() as db:
        record = (await db.scalars(select(Proposal))).one()
        assert record.status == "draft" and record.proposed_change == "a monthly skill swap"


async def test_explicit_request_for_ideas_keeps_ordinary_drafting_useful(env):
    change = "Try a skill-share event, with helpers invited rather than assigned."
    events, _, _ = await _chat(env, "ben", "Create a draft proposal for a skill swap. Use your ideas for its text. Keep it a draft.", [
        _model_turn(calls=(("create_proposal", {"title": "Skill swap", "type": "operational", "proposed_change": change, "rationale": "Explore ways to share skills."}),)),
        _model_turn("Your draft has ideas for you to review.")])
    assert next(json.loads(data)["success"] for kind, data in events if kind == "tool_result")
    async with env.db() as db:
        record = (await db.scalars(select(Proposal))).one()
        assert record.status == "draft" and record.proposed_change == change


async def test_negated_invitation_does_not_allow_generated_commitments(env):
    events, _, _ = await _chat(env, "ben", "Create a draft for a monthly skill swap. Do not use your ideas.", [
        _model_turn(calls=(("create_proposal", {"title": "Skill swap", "type": "operational", "proposed_change": "Assign three volunteers each Saturday."}),)),
        _model_turn("I will use only the change you gave.")])
    result = next(json.loads(data) for kind, data in events if kind == "tool_result")
    assert result["success"] is False and "No proposal was created" in result["error"]
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Proposal)) == 0
