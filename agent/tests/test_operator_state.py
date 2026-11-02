"""Server-owned action payloads, record context and explicit support through SSE."""
import datetime as dt
import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from neos_agent.api.chat import _known_records
from neos_agent.api.chat import _save_session
from neos_agent.db.models import AgentSession, Domain, Member, NodeAdmin, NodeAdminAction, Proposal, User
from sqlalchemy import select
from tests.test_g_agent_assistant import (
    OASIS, PEOPLE, SEED_LIBRARY, _chat, _events, _model_turn, _proposal, _status, _tool, env,
)


def _session(events):
    return next(json.loads(value)["session_id"] for name, value in events if name == "session")


async def test_yes_executes_original_payload_without_a_model_choosing_target(env):
    first = await _proposal(env, title="Original bike shed")
    other = await _proposal(env, title="Other bike shed")
    original = {"proposal_id": first.proposal_id, "new_status": "withdrawn", "note": "My original reason"}
    _, session, _ = await _chat(env, "ada", "Withdraw the original proposal", [
        _model_turn(calls=(("update_proposal_status", original),)), _model_turn("This ends it for good. Confirm?"),
    ])
    events, _, model = await _chat(env, "ada", "Yes, withdraw it.", [
        _model_turn(calls=(("update_proposal_status", {"proposal_id": str(other.id), "new_status": "withdrawn"}),)),
    ], session_id=session)
    model.assert_not_awaited()
    assert await _status(env, Proposal, first.id) == "withdrawn"
    assert await _status(env, Proposal, other.id) == "advice"
    [start] = [json.loads(value) for name, value in events if name == "tool_start"]
    assert start["args"] == {**original, "confirmed": True}
    assert f"/proposals/{first.id}" in "".join(value for name, value in events if name == "append")
    async with env.db() as db:
        assert (await db.get(AgentSession, uuid.UUID(session))).context["pending_confirmations"] == []


async def test_unrelated_request_saving_an_old_snapshot_cannot_restore_consumed_approval(env):
    proposal = await _proposal(env)
    action = {"proposal_id": str(proposal.id), "new_status": "withdrawn"}
    _, session, _ = await _chat(env, "ada", "Withdraw it", [
        _model_turn(calls=(("update_proposal_status", action),)), _model_turn("Confirm withdrawal?"),
    ])
    async with env.db() as db:
        stale = dict((await db.get(AgentSession, uuid.UUID(session))).context)
    await _chat(env, "ada", "Yes, withdraw it.", [], session_id=session)
    # Interleave the unrelated turn's delayed persistence after the confirmed write.
    person = PEOPLE["ada"]
    request = SimpleNamespace(app=env.app, ctx=SimpleNamespace(
        user=User(id=person.user_id, display_name=person.name),
        member=Member(id=person.member_id(), user_id=person.user_id, ecosystem_id=OASIS),
        authorized_ecosystem_ids=[OASIS], selected_ecosystem_ids=[OASIS],
    ))
    await _save_session(request, session, request.ctx.member, [{"role": "assistant", "content": "Unrelated answer"}],
        None, {}, OASIS, [str(OASIS)], pending_confirmations=stale["pending_confirmations"],
        confirmation_epoch=stale.get("confirmation_epoch", 0))
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session))
        assert saved.context["confirmation_epoch"] == 1
        assert saved.context["pending_confirmations"] == []
    events, _, model = await _chat(env, "ada", "Yes, withdraw it.", [], session_id=session)
    model.assert_not_awaited()
    assert not any(name == "tool_start" for name, _ in events)


@pytest.mark.parametrize("change", ["expire", "revoke", "retarget"])
async def test_frozen_action_rechecks_expiry_authority_and_resolved_target(env, change):
    proposal = await _proposal(env, title="Original bike shed")
    action = {"proposal_id": proposal.proposal_id, "new_status": "withdrawn"}
    who = "mo" if change == "revoke" else "ada"
    _, session, _ = await _chat(env, who, "Withdraw it", [
        _model_turn(calls=(("update_proposal_status", action),)), _model_turn("Confirm withdrawal?"),
    ])
    async with env.db() as db:
        if change == "expire":
            saved = await db.get(AgentSession, uuid.UUID(session))
            context = dict(saved.context)
            entry = dict(context["pending_confirmations"][0])
            entry["at"] = (dt.datetime.now(dt.UTC) - dt.timedelta(hours=1)).isoformat()
            context["pending_confirmations"] = [entry]
            saved.context = context
        elif change == "revoke":
            from neos_agent.api.policy import can_manage_proposal

            steward = await db.get(Member, PEOPLE[who].member_id())
            steward.role = "user"
            assert not can_manage_proposal(steward, await db.get(Proposal, proposal.id))
        else:
            (await db.get(Proposal, proposal.id)).proposal_id = "PROP-RENAMED"
        await db.commit()
    events, _, model = await _chat(env, who, "Yes, withdraw it.", [
        _model_turn(calls=(("update_proposal_status", {**action, "confirmed": True}),)), _model_turn("Not changed."),
    ], session_id=session)
    assert await _status(env, Proposal, proposal.id) == "advice"
    assert not any(json.loads(value)["success"] for name, value in events if name == "tool_result")
    if change == "revoke":
        model.assert_not_awaited()
        async with env.db() as db:
            assert (await db.get(AgentSession, uuid.UUID(session))).context["pending_confirmations"] == []


async def test_pending_payload_is_private_in_owner_and_shared_serializers(env):
    proposal = await _proposal(env)
    _, session, _ = await _chat(env, "ada", "Withdraw it", [
        _model_turn(calls=(("update_proposal_status", {"proposal_id": str(proposal.id), "new_status": "withdrawn", "note": "private action payload"}),)),
        _model_turn("Confirm withdrawal?"),
    ])
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session))
        assert saved.context["pending_confirmations"][0]["args"]["note"] == "private action payload"
        saved.privacy, saved.share_token = "public", "operator-state-public-test"
        await db.commit()
    for url, headers in ((f"/api/v1/chat/sessions/{session}", {"x-test-as": "ada"}),
                         ("/api/v1/chat/shared/operator-state-public-test", {"x-test-as": "ben"})):
        _, response = await env.app.asgi_client.get(url, headers=headers)
        assert response.status == 200
        assert "pending_confirmations" not in response.text and "private action payload" not in response.text


async def test_cancel_with_a_new_request_still_answers_the_new_request(env):
    proposal = await _proposal(env)
    _, session, _ = await _chat(env, "ada", "Withdraw it", [
        _model_turn(calls=(("update_proposal_status", {"proposal_id": str(proposal.id), "new_status": "withdrawn"}),)),
        _model_turn("Confirm withdrawal?"),
    ])
    _, _, model = await _chat(env, "ada", "No, cancel. Where does my proposal stand?", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(proposal.id)}),)),
        _model_turn("It remains in Advice."),
    ], session_id=session)
    assert model.await_count == 2
    assert await _status(env, Proposal, proposal.id) == "advice"
    async with env.db() as db:
        assert (await db.get(AgentSession, uuid.UUID(session))).context["pending_confirmations"] == []


async def test_domain_candidates_survive_own_session_and_recheck_scope(env):
    other_id = uuid.uuid4()
    async with env.db() as db:
        first = await db.get(Domain, SEED_LIBRARY)
        first.name = "Operator Garden East"
        db.add(Domain(id=other_id, ecosystem_id=OASIS, domain_id="DOM-OP-WEST", name="Operator Garden West",
                      version="1.0", status="active", purpose="Growing together"))
        await db.commit()
    _, session, _ = await _chat(env, "ben", "Join Operator Garden", [
        _model_turn(calls=(("get_domain", {"domain_id": "Operator Garden"}),)),
        _model_turn("East or West?"),
    ])
    _, _, model = await _chat(env, "ben", "The east one", [
        _model_turn(calls=(("join_domain", {"domain_id": str(SEED_LIBRARY)}),)), _model_turn("Joined East."),
    ], session_id=session)
    prompt = model.call_args_list[0].kwargs["system"]
    assert str(SEED_LIBRARY) in prompt and '"kind": "domain"' in prompt
    assert "Operator Garden East" in prompt and "Operator Garden West" in prompt
    # Another person's session cannot supply these references.
    _, outsider = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "olu"},
        json={"message": "The east one", "session_id": session})
    assert outsider.status == 404 and "Operator Garden East" not in outsider.text


async def test_multiorg_draft_waits_for_real_user_choice_and_replays_only_safe_fields(env):
    args = {"title": "Choice-bound seeds", "type": "operational", "proposed_change": "Share spare seeds", "rationale": "Reduce waste",
            "ecosystem": "Oasis", "affected_domain": "Guessed foreign circle", "advice_deadline": "2030-01-01"}
    original_request = "Create a proposal called Choice-bound seeds to share spare seeds"
    _, session, first_model = await _chat(env, "fay", original_request, [
        _model_turn(calls=(("create_proposal", args),)), _model_turn("Which organization: Oasis or River House?"),
    ])
    first_model.assert_not_awaited()
    async with env.db() as db:
        assert not (await db.scalars(select(Proposal).where(Proposal.title == args["title"]))).all()
        saved = await db.get(AgentSession, uuid.UUID(session))
        staged = saved.context["pending_proposal_choice"]
        assert {item["name"] for item in staged["choices"]} == {"Oasis", "River House"}
        assert set(staged["args"]) == {"title", "type", "proposed_change", "rationale"}
    events, _, model = await _chat(env, "fay", "River House", [], session_id=session)
    model.assert_not_awaited()
    assert any(json.loads(value).get("success") for name, value in events if name == "tool_result")
    async with env.db() as db:
        from tests.test_g_agent_assistant import RIVER
        proposal = (await db.scalars(select(Proposal).where(Proposal.title == args["title"]))).one()
        assert proposal.ecosystem_id == RIVER and proposal.status == "draft"
        assert proposal.proposed_change == original_request
        assert proposal.rationale == "Draft requested by the member; details to confirm."
        assert proposal.affected_domain is None and proposal.advice_deadline is None
        assert (await db.get(AgentSession, uuid.UUID(session))).context["pending_proposal_choice"] is None
    from neos_agent.api.chat import _execute_proposal_choice
    person = PEOPLE["fay"]
    request = SimpleNamespace(app=env.app, ctx=SimpleNamespace(user=User(id=person.user_id, display_name=person.name),
        member=Member(id=person.member_id(), user_id=person.user_id, ecosystem_id=OASIS), authorized_ecosystem_ids=[OASIS, RIVER],
        selected_ecosystem_ids=[OASIS, RIVER], proposal_user_message="Oasis", pending_proposal_choice=staged))
    duplicate = await _execute_proposal_choice(request, session, request.ctx.member, sorted([str(OASIS), str(RIVER)]), staged)
    assert not duplicate["success"]
    # An earlier draft-choice turn saving late must not resurrect a consumed payload.
    await _save_session(request, session, request.ctx.member, [{"role": "assistant", "content": "Stale draft choice"}], None, {}, OASIS,
        [str(OASIS), str(RIVER)], confirmation_epoch=0)
    async with env.db() as db:
        assert (await db.get(AgentSession, uuid.UUID(session))).context["pending_proposal_choice"] is None
        assert len((await db.scalars(select(Proposal).where(Proposal.title == args["title"]))).all()) == 1


def test_pending_proposal_choice_rejects_changed_scope_expiry_or_assistant_arguments():
    from neos_agent.api.chat import _pending_proposal_args, _user_proposal_target
    from tests.test_g_agent_assistant import RIVER
    choices = [{"id": str(OASIS), "name": "Oasis"}, {"id": str(RIVER), "name": "River House"}]
    pending = {"args": {"title": "Draft", "type": "policy", "proposed_change": "Seeds", "rationale": "Less waste"}, "choices": choices,
               "selected_ids": sorted([str(OASIS), str(RIVER)]), "at": dt.datetime.now(dt.UTC).isoformat()}
    assert _pending_proposal_args({"pending_proposal_choice": pending}, "Oasis", [str(OASIS)]) is None
    expired = {**pending, "at": (dt.datetime.now(dt.UTC) - dt.timedelta(hours=1)).isoformat()}
    assert _pending_proposal_args({"pending_proposal_choice": expired}, "Oasis", pending["selected_ids"]) is None
    assert _user_proposal_target("Create a seed draft", choices) is None
    assert _user_proposal_target("Create it in River House", choices) == str(RIVER)
    assert _user_proposal_target("not for Oasis", choices) is None


def test_staged_draft_uses_authenticated_request_words_without_invented_commitments():
    from neos_agent.api.chat import _user_draft_args
    request = "Draft a proposal for a seed swap, call it 'Seed swap', so members can exchange locally adapted seeds. Keep it a draft."
    args = _user_draft_args(request)
    assert args["title"] == "Seed swap" and args["proposed_change"] == request
    assert "recurring" not in args["proposed_change"] and "deadline" not in args
    assert _user_draft_args("Explain how to draft a proposal for a seed swap") is None


async def test_support_prose_approval_is_corrected_to_nonwriting_server_preparation(env):
    async with env.db() as db:
        db.add(NodeAdmin(user_id=PEOPLE["ben"].user_id, active=True))
        await db.commit()
    context = {"enabled": True, "organization_id": str(OASIS), "reason": "Agent testing"}
    args = {"resource_type": "proposals", "action": "create", "values": {"type": "operational", "title": "Prepared before approval", "proposed_change": "Share seeds", "rationale": "Reduce waste"}, "confirmed": True}
    model = AsyncMock(side_effect=[_model_turn("Shall I go ahead and create the draft?"),
        _model_turn(calls=(("node_support_command", args),)), _model_turn("Review the prepared draft before confirming.")])
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=model):
        _, response = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"}, json={"message": "Prepare the seed draft for my review before creating it", "support_context": context})
    session = _session(_events(response.text))
    assert model.await_count == 3 and "Server review correction" in model.call_args_list[1].kwargs["system"]
    definitions = model.call_args_list[0].kwargs["tools"]
    command = next(item["function"] for item in definitions if item["function"]["name"] == "node_support_command")
    assert "confirmed" not in command["parameters"]["properties"] and "PREPARE FOR REVIEW" in command["description"]
    assert "Shall I go ahead" not in response.text
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session))
        pending = saved.context["pending_confirmations"]
        assert len(pending) == 1 and pending[0]["key"]
        assert "confirmed" not in pending[0]["args"]
        assert not (await db.scalars(select(Proposal).where(Proposal.title == args["values"]["title"]))).all()
        assert "Shall I go ahead" not in json.dumps(saved.context["messages"])
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=AsyncMock(side_effect=AssertionError("Server confirmation must not use the model"))):
        _, done = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"}, json={"message": "Yes", "session_id": session, "support_context": context})
    assert any(json.loads(value).get("success") for name, value in _events(done.text) if name == "tool_result")


@pytest.mark.parametrize("answer", ["Support actions are public and keep the actual operator's identity.", "Which proposal title should I use?"])
async def test_support_read_only_answer_and_information_question_need_no_preparation_retry(env, answer):
    async with env.db() as db:
        db.add(NodeAdmin(user_id=PEOPLE["ben"].user_id, active=True))
        await db.commit()
    model = AsyncMock(return_value=_model_turn(answer))
    context = {"enabled": True, "organization_id": str(OASIS), "reason": "Agent testing"}
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=model):
        _, response = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"}, json={"message": "Explain the support process", "support_context": context})
    assert model.await_count == 1 and answer in response.text


async def test_unprepared_support_review_retry_is_bounded_and_never_authorizes_yes(env):
    async with env.db() as db:
        db.add(NodeAdmin(user_id=PEOPLE["ben"].user_id, active=True))
        await db.commit()
    model = AsyncMock(side_effect=[_model_turn("Shall I go ahead?"), _model_turn("Should I proceed?")])
    context = {"enabled": True, "organization_id": str(OASIS), "reason": "Agent testing"}
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=model):
        _, response = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"}, json={"message": "Prepare a seed draft for review", "support_context": context})
    session = _session(_events(response.text))
    assert model.await_count == 2 and "No change was made" in response.text
    assert "Shall I go ahead" not in response.text and "Should I proceed" not in response.text
    async with env.db() as db:
        assert (await db.get(AgentSession, uuid.UUID(session))).context["pending_confirmations"] == []
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=AsyncMock(side_effect=AssertionError("No pending action means no model confirmation"))):
        _, declined = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"}, json={"message": "Yes", "session_id": session, "support_context": context})
    assert "There is no pending action to confirm" in declined.text


async def test_new_draft_choice_invalidates_old_unrelated_approval_and_yes_cannot_apply_it(env):
    original = await _proposal(env, title="Original kept proposal", author="fay")
    _, session, _ = await _chat(env, "fay", "Withdraw my original kept proposal", [
        _model_turn(calls=(("update_proposal_status", {"proposal_id": str(original.id), "new_status": "withdrawn"}),)), _model_turn("Confirm withdrawal?"),
    ])
    async with env.db() as db:
        old = dict((await db.get(AgentSession, uuid.UUID(session))).context)
        assert old["pending_confirmations"]
    _, _, model = await _chat(env, "fay", "Draft a proposal called 'New seed draft' so members can exchange seeds", [], session_id=session)
    model.assert_not_awaited()
    async with env.db() as db:
        state = (await db.get(AgentSession, uuid.UUID(session))).context
        assert state["pending_confirmations"] == [] and state["pending_proposal_choice"]
        assert state["confirmation_epoch"] > old.get("confirmation_epoch", 0)
    _, _, yes_model = await _chat(env, "fay", "Yes", [], session_id=session)
    yes_model.assert_not_awaited()
    assert await _status(env, Proposal, original.id) == "advice"


def test_reference_cache_is_bounded_typed_and_rejects_nested_or_external_data():
    records = [{"name": f"Group {i}", "link": f"/domains/{uuid.uuid4()}", "private_text": "do not retain"} for i in range(30)]
    cached = _known_records({"success": True, "data": {"domains": records}})
    assert len(cached) <= 20
    assert all(set(record) == {"kind", "id", "label", "link"} for record in cached)
    assert not _known_records({"success": False, "data": records})
    assert not _known_records({"success": True, "data": {"private_nested": records}})
    assert not _known_records({"success": True, "data": {"link": "https://example.com/domains/x"}})


async def test_proposal_tools_ground_automatic_policy_and_unknown_history(env):
    proposal = await _proposal(env)
    for name, args in (("get_proposal", {"proposal_id": str(proposal.id)}),
                       ("explain_status", {"kind": "proposal", "record": str(proposal.id)})):
        result = await _tool(env, "ada", name, **args)
        facts = result["data"]["lifecycle_facts"]
        assert facts["advice_advances_automatically"] is False
        assert facts["meeting_advice_gate_advances_stage"] is False
        assert facts["transition_history_available"] is False
        assert "Unknown" in facts["actor_and_cause"]


async def test_support_tools_require_actual_role_and_explicit_context(env):
    context = {"enabled": True, "organization_id": str(OASIS), "reason": "Agent testing"}
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True):
        _, denied = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Inspect support resources", "support_context": context, "is_node_admin": True})
    assert denied.status == 403
    async with env.db() as db:
        db.add(NodeAdmin(user_id=PEOPLE["ben"].user_id, active=True))
        await db.commit()
    _, _, member_model = await _chat(env, "ben", "Help me", [_model_turn("How can I help?")])
    assert not any(tool["function"]["name"].startswith("node_support_") for tool in member_model.call_args.kwargs["tools"])
    model = AsyncMock(return_value=_model_turn("Use support tools."))
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=model):
        _, response = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Inspect support resources", "support_context": context})
    assert response.status == 200
    assert {tool["function"]["name"] for tool in model.call_args.kwargs["tools"]} == {
        "node_support_catalog", "node_support_list", "node_support_inspect", "node_support_command",
        "node_support_prepare_proposal",
    }
    session = _session(_events(response.text))
    _, mismatch = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"},
        json={"message": "Continue", "session_id": session})
    assert mismatch.status == 409
    _, sharing = await env.app.asgi_client.patch(f"/api/v1/chat/sessions/{session}/privacy", headers={"x-test-as": "ben"},
        json={"privacy": "public"})
    assert sharing.status == 403
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session))
        saved.share_token = "legacy-support-token"
        await db.commit()
    _, shared = await env.app.asgi_client.get("/api/v1/chat/shared/legacy-support-token", headers={"x-test-as": "ben"})
    assert shared.status == 403
    async with env.db() as db:
        (await db.get(NodeAdmin, PEOPLE["ben"].user_id)).active = False
        await db.commit()
    denied_model = AsyncMock()
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=denied_model):
        _, revoked = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Continue support", "session_id": session, "support_context": context})
    assert revoked.status == 403
    denied_model.assert_not_awaited()
    _, hidden = await env.app.asgi_client.get(f"/api/v1/chat/sessions/{session}", headers={"x-test-as": "ben"})
    assert hidden.status == 404 and "support_context" not in hidden.json and "messages" not in hidden.json
    _, listing = await env.app.asgi_client.get("/api/v1/chat/sessions", headers={"x-test-as": "ben"})
    assert session not in {item["id"] for item in listing.json["sessions"]}
    for method, suffix, body in (("patch", "/privacy", {"privacy": "private"}), ("delete", "", None)):
        _, inaccessible = await getattr(env.app.asgi_client, method)(f"/api/v1/chat/sessions/{session}{suffix}", headers={"x-test-as": "ben"}, **({"json": body} if body else {}))
        assert inaccessible.status == 404
    _, continuation = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"}, json={"message": "Yes", "session_id": session})
    assert continuation.status == 404


async def test_support_write_freezes_payload_and_records_actor_session_without_member_consent(env):
    context = {"enabled": True, "organization_id": str(OASIS), "reason": "Agent testing"}
    async with env.db() as db:
        db.add(NodeAdmin(user_id=PEOPLE["ben"].user_id, active=True))
        await db.commit()
    args = {"resource_type": "proposals", "action": "create", "values": {
        "type": "proposal", "title": "Support seed swap", "proposed_change": "Share spare seeds", "rationale": "Reduce waste", "status": "draft",
    }}
    model = AsyncMock(side_effect=[_model_turn(calls=(("node_support_command", args),)), _model_turn("Confirm this draft?")])
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=model):
        _, asked = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Create the seed sharing draft as support", "support_context": context})
    session = _session(_events(asked.text))
    async with env.db() as db:
        assert not (await db.scalars(select(Proposal).where(Proposal.title == "Support seed swap"))).first()
    model = AsyncMock(side_effect=AssertionError("Confirmation must not invoke the model"))
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=model):
        _, done = await env.app.asgi_client.post("/api/v1/chat/send", headers={"x-test-as": "ben"},
            json={"message": "Yes, go ahead", "session_id": session, "support_context": context})
    assert done.status == 200
    model.assert_not_awaited()
    [receipt] = [json.loads(value) for name, value in _events(done.text) if name == "tool_result"]
    assert receipt["success"] is True
    async with env.db() as db:
        proposal = (await db.scalars(select(Proposal).where(Proposal.title == "Support seed swap"))).one()
        assert proposal.proposer_member_id is None and proposal.support_created_by_user_id == PEOPLE["ben"].user_id
        audit = (await db.scalars(select(NodeAdminAction).where(NodeAdminAction.resource_id == str(proposal.id)))).one()
        assert audit.actor_user_id == PEOPLE["ben"].user_id and audit.source == "agent"
        assert audit.correlation_id == session
        assert (await db.get(AgentSession, uuid.UUID(session))).context["pending_confirmations"] == []


async def test_memberless_node_admin_owns_support_chat_and_confirms_as_actual_user(env):
    operator_id, other_id = uuid.uuid4(), uuid.uuid4()
    async with env.db() as db:
        db.add_all([User(id=operator_id, display_name="Independent operator"), User(id=other_id, display_name="Other operator")])
        await db.flush()
        db.add_all([NodeAdmin(user_id=operator_id, active=True), NodeAdmin(user_id=other_id, active=True)])
        await db.commit()

    @env.app.on_request
    async def memberless_identity(request):
        identity = other_id if request.headers.get("x-other-operator") else operator_id
        request.ctx.member = None
        request.ctx.user = User(id=identity, display_name="Independent operator")
        request.ctx.authorized_ecosystem_ids = []
        request.ctx.selected_ecosystem_ids = []
        request.ctx.ecosystem_scope = None

    headers = {"x-test-as": "ben"}
    context = {"enabled": True, "organization_id": str(OASIS), "reason": "Agent testing"}
    args = {"title": "Memberless support draft", "proposed_change": "Exchange seeds", "rationale": "Reduce waste"}
    model = AsyncMock(side_effect=[_model_turn(calls=(("node_support_prepare_proposal", args),)), _model_turn("Confirm this draft?")])
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=model):
        _, asked = await env.app.asgi_client.post("/api/v1/chat/send", headers=headers,
            json={"message": "Create the support draft", "support_context": context})
    assert asked.status == 200, asked.text
    session = _session(_events(asked.text))
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), patch("neos_agent.api.chat.acompletion", new=AsyncMock(side_effect=AssertionError("No model on confirmation"))):
        _, done = await env.app.asgi_client.post("/api/v1/chat/send", headers=headers,
            json={"message": "Yes", "session_id": session, "support_context": context})
    assert any(json.loads(value)["success"] for name, value in _events(done.text) if name == "tool_result"), done.text
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session))
        assert saved.owner_user_id == operator_id and saved.member_id is None
        proposal = (await db.scalars(select(Proposal).where(Proposal.title == "Memberless support draft"))).one()
        assert proposal.support_created_by_user_id == operator_id and proposal.proposer_member_id is None
        assert not (await db.scalars(select(Member).where(Member.user_id == operator_id))).all()
    _, history = await env.app.asgi_client.get(f"/api/v1/chat/sessions/{session}", headers=headers)
    assert history.status == 200 and history.json["support_context"] == context
    _, listing = await env.app.asgi_client.get("/api/v1/chat/sessions", headers=headers)
    assert session in {item["id"] for item in listing.json["sessions"]}
    _, foreign = await env.app.asgi_client.get(f"/api/v1/chat/sessions/{session}", headers={**headers, "x-other-operator": "true"})
    assert foreign.status == 404
    _, member_chat = await env.app.asgi_client.post("/api/v1/chat/send", headers=headers, json={"message": "Act as a member"})
    assert member_chat.status == 403
