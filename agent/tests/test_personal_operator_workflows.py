"""Ordinary operator workflows: real tools/SSE, shared services and persisted effects."""
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from neos_agent.agent.governance_tools import CONFIRMATION_TOOLS, get_tool_definitions
from neos_agent.api.chat import _confirmation_matches_action, _confirmation_reply, _record_reference
from neos_agent.api.exit import exit_api_bp
from neos_agent.api.messaging import messaging_api_bp
from neos_agent.db.models import (
    AgentSession, Collaboration, CollaborationApproval, ConflictCase, Conversation, Ecosystem, ExitRecord,
    GovernanceHealthAudit, Member, Message, RepairAgreementRecord,
)
from tests.test_g_agent_assistant import OASIS, RIVER, SEED_LIBRARY, PEOPLE, _chat, _model_turn, _tool, env


def _results(events):
    return [json.loads(data) for kind, data in events if kind == "tool_result"]


async def _conversation(env, who="ben", target="ada", message=None):
    result = await _tool(env, who, "create_conversation", participant_ids=[str(PEOPLE[target].member_id())],
        type="dm", message=message, confirmed=True)
    assert result["success"], result
    return result["data"]["id"]


async def test_conversation_and_first_message_wait_for_frozen_confirmation_and_cannot_replay(env):
    action = {"participant_ids": [str(PEOPLE["ada"].member_id())], "type": "dm", "message": "I can help with seeds."}
    events, session, _ = await _chat(env, "ben", "Send Ada my offer to help with seeds.", [
        _model_turn(calls=(("create_conversation", action),)), _model_turn("Send this message to Ada?"),
    ])
    assert _results(events)[0]["success"] is False
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Conversation)) == 0
        assert await db.scalar(select(func.count()).select_from(Message)) == 0
    events, _, model = await _chat(env, "ben", "Yes, send it.", [
        _model_turn(calls=(("create_conversation", {**action, "message": "I will pay every bill."}),)),
    ], session_id=session)
    model.assert_not_awaited()
    assert _results(events)[0]["success"] is True
    async with env.db() as db:
        conversation = (await db.scalars(select(Conversation))).one()
        message = (await db.scalars(select(Message))).one()
        assert conversation.created_by == PEOPLE["ben"].member_id()
        assert (message.content, message.sender_id) == (action["message"], PEOPLE["ben"].member_id())
    events, _, replay = await _chat(env, "ben", "Yes", [], session_id=session)
    replay.assert_not_awaited()
    assert not _results(events)


@pytest.mark.parametrize("missing", [{}, {"message": None}])
async def test_incomplete_message_intent_creates_no_pending_then_same_loop_correction_sends_exactly_once(env, missing):
    action = {"participant_ids": [str(PEOPLE["ada"].member_id())], "type": "dm"}
    text = "I can help with the seed swap."
    step = 0

    async def completion(**kwargs):
        nonlocal step
        step += 1
        if step == 1:
            return _model_turn(calls=(("create_conversation", {**action, **missing}),))
        async with env.db() as db:
            assert await db.scalar(select(func.count()).select_from(Conversation)) == 0
            assert await db.scalar(select(func.count()).select_from(Message)) == 0
            for session in await db.scalars(select(AgentSession)):
                assert not session.context.get("pending_confirmations")
        if step == 2:
            results = [json.loads(item["content"]) for item in kwargs["messages"] if item.get("role") == "tool"]
            assert results[-1]["code"] == "MESSAGE_INTENT_REQUIRED"
            assert not results[-1].get("needs_confirmation")
            return _model_turn(calls=(("create_conversation", {**action, "message": text}),))
        return _model_turn("Send this exact message to Ada?")

    events, session, _ = await _chat(env, "ben", f"Start a direct conversation with Ada and send exactly: {text}", completion)
    results = _results(events)
    assert len(results) == 2 and not results[0].get("needs_confirmation") and results[1]["needs_confirmation"]
    async with env.db() as db:
        pending = (await db.get(AgentSession, uuid.UUID(session))).context["pending_confirmations"]
        assert len(pending) == 1 and pending[0]["args"] == {**action, "message": text}
    events, _, executed = await _chat(env, "ben", "Yes, send it.", [], session_id=session)
    executed.assert_not_awaited()
    assert _results(events)[0]["success"]
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Conversation)) == 1
        message = (await db.scalars(select(Message))).one()
        assert message.content == text and message.sender_id == PEOPLE["ben"].member_id()
    replayed, _, replay = await _chat(env, "ben", "Yes, send it.", [], session_id=session)
    replay.assert_not_awaited()
    assert not _results(replayed)
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 1


async def test_explicit_conversation_only_intent_creates_no_initial_message(env):
    action = {"participant_ids": [str(PEOPLE["ada"].member_id())], "type": "dm", "message": ""}
    events, session, _ = await _chat(env, "ben", "Start a direct conversation with Ada without a message.", [
        _model_turn(calls=(("create_conversation", action),)), _model_turn("Create this conversation with no message?")])
    assert _results(events)[0]["needs_confirmation"]
    rejected, _, wrong = await _chat(env, "ben", "Yes, send it.", [], session_id=session)
    wrong.assert_not_awaited()
    assert not _results(rejected)[0]["success"]
    events, _, model = await _chat(env, "ben", "Yes, create it.", [], session_id=session)
    model.assert_not_awaited()
    assert _results(events)[0]["success"]
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Conversation)) == 1
        assert await db.scalar(select(func.count()).select_from(Message)) == 0


async def test_cancelled_send_writes_nothing_and_member_name_duplicates_are_not_auto_chosen(env):
    conversation = await _conversation(env)
    events, session, _ = await _chat(env, "ben", "Tell Ada I can help.", [
        _model_turn(calls=(("send_message", {"conversation_id": conversation, "content": "I can help."}),)),
        _model_turn("Send that exact text?"),
    ])
    assert not _results(events)[0]["success"]
    await _chat(env, "ben", "No, cancel", [_model_turn("Cancelled.")], session_id=session)
    await _chat(env, "ben", "Yes", [], session_id=session)
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 0
    choices = await _tool(env, "ben", "find_message_members", query="Sam")
    assert {row["display_name"] for row in choices["data"]["members"]} == {"Sam Lee", "Sam Ray"}


async def test_messaging_privacy_current_participation_and_shared_rest_actor(env):
    env.app.blueprint(messaging_api_bp)
    conversation = await _conversation(env, message="Private seed note.")
    hidden = await _tool(env, "olu", "get_conversation", conversation_id=conversation)
    assert hidden["success"] is False and hidden["error"] == "Conversation not found"
    search = await _tool(env, "olu", "search_messages", query="Private seed")
    assert search["data"]["messages"] == []
    forged = await _tool(env, "ben", "send_message", conversation_id=conversation, content="Wrong actor", sender_id=str(PEOPLE["ada"].member_id()), confirmed=True)
    assert forged["success"] is False
    _, response = await env.app.asgi_client.post(f"/api/v1/messaging/conversations/{conversation}/messages",
        headers={"x-test-as": "ben"}, json={"content": "REST shares the same sender rule", "sender_id": str(PEOPLE["ada"].member_id())})
    assert response.status == 201, response.text
    assert response.json["sender_id"] == str(PEOPLE["ben"].member_id())
    async with env.db() as db:
        (await db.get(Member, PEOPLE["ben"].member_id())).current_status = "suspended"
        await db.commit()
    denied = await _tool(env, "ben", "send_message", conversation_id=conversation, content="No longer active", confirmed=True)
    assert denied["success"] is False
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 2


async def test_starting_conversation_rejects_private_outside_recipients_and_empty_scope(env):
    denied = await _tool(env, "ben", "create_conversation", participant_ids=[str(PEOPLE["olu"].member_id(RIVER))], confirmed=True)
    assert denied["success"] is False
    no_scope = await _tool(env, "ben", "create_conversation", scope=[], participant_ids=[str(PEOPLE["ada"].member_id())], confirmed=True)
    assert no_scope["success"] is False
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Conversation)) == 0


async def test_changed_message_recipient_identity_requires_a_fresh_confirmation(env):
    conversation = await _conversation(env)
    _, session, _ = await _chat(env, "ben", "Send Ada exactly: I can help.", [
        _model_turn(calls=(("send_message", {"conversation_id": conversation, "content": "I can help."}),)),
        _model_turn("Send this message to Ada?"),
    ])
    async with env.db() as db:
        (await db.get(Member, PEOPLE["ada"].member_id())).display_name = "A newly changed identity"
        await db.commit()
    events, _, model = await _chat(env, "ben", "Yes, send it", [], session_id=session)
    model.assert_not_awaited()
    assert _results(events)[0]["success"] is False
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 0


async def test_failed_tool_rollback_cannot_restore_the_consumed_send_approval(env):
    conversation = await _conversation(env)
    _, session, _ = await _chat(env, "ben", "Send exactly: I can help.", [
        _model_turn(calls=(("send_message", {"conversation_id": conversation, "content": "I can help."}),)),
        _model_turn("Send it?"),
    ])
    async def rollback_failure(name, args, db, **kwargs):
        await db.rollback()
        return {"success": False, "error": "The write failed; no message was sent."}
    with patch("neos_agent.api.chat.execute_tool", new=AsyncMock(side_effect=rollback_failure)):
        events, _, _ = await _chat(env, "ben", "Yes, send it", [], session_id=session)
    assert _results(events)[0]["success"] is False
    events, _, replay = await _chat(env, "ben", "Yes, send it", [], session_id=session)
    replay.assert_not_awaited()
    assert not _results(events)
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Message)) == 0


async def test_collaboration_discovery_proposal_and_actual_source_actor(env):
    from neos_agent.db.models import Domain
    target_id, hidden_id, hidden_domain = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with env.db() as db:
        db.add(Ecosystem(id=hidden_id, name="Private outside", visibility="private", status="active"))
        await db.flush()
        db.add_all([Domain(id=target_id, ecosystem_id=RIVER, domain_id="DOM-RIVER-OP", name="River seeds", purpose="Share seeds", status="active"),
                    Domain(id=hidden_domain, ecosystem_id=hidden_id, domain_id="DOM-HIDDEN-OP", name="Hidden seeds", status="active")])
        await db.commit()
    discover = await _tool(env, "ben", "find_collaboration_domains", query="seeds")
    assert str(hidden_domain) not in json.dumps(discover)
    args = {"source_domain": str(SEED_LIBRARY), "target_domain": str(target_id), "title": "Local seed exchange", "description": "Trade spare seeds"}
    asked = await _tool(env, "ben", "propose_collaboration", **args)
    assert asked["needs_confirmation"]
    async with env.db() as db:
        assert await db.scalar(select(func.count()).select_from(Collaboration)) == 0
    made = await _tool(env, "ben", "propose_collaboration", **args, confirmed=True)
    assert made["success"], made
    async with env.db() as db:
        collaboration = await db.get(Collaboration, uuid.UUID(made["data"]["id"]))
        assert collaboration.proposed_by_member_id == PEOPLE["ben"].member_id()
        assert collaboration.status == "proposed"
        assert await db.scalar(select(func.count()).select_from(CollaborationApproval)) == 0
    visible = await _tool(env, "olu", "find_collaborations", status="proposed", query="Local seed")
    assert visible["data"]["total"] == 1
    hidden = await _tool(env, "ben", "propose_collaboration", **{**args, "target_domain": str(hidden_domain)}, confirmed=True)
    assert hidden["success"] is False


async def _rated_audit(env):
    started = await _tool(env, "ben", "create_safeguard_audit", findings="We heard from a broad set of members.")
    assert started["success"], started
    audit_id = started["data"]["id"]
    snapshot = await _tool(env, "ben", "get_governance_health")
    ratings = [{"indicator_id": row["indicator_id"], "indicator_name": row["name"], "status": "healthy", "notes": "Auditor reviewed this value."}
               for row in snapshot["data"]["indicators"]]
    edited = await _tool(env, "ben", "update_health_audit", audit_id=audit_id, changes={"indicator_scores": ratings})
    assert edited["success"], edited
    return audit_id


async def test_audit_edit_publish_freeze_and_independent_actor_checks(env):
    audit_id = await _rated_audit(env)
    other = await _tool(env, "ada", "update_health_audit", audit_id=audit_id, changes={"findings": "Overwrite another auditor"})
    assert other["success"] is False
    events, session, _ = await _chat(env, "ben", "Publish my rated audit.", [
        _model_turn(calls=(("publish_health_audit", {"audit_id": audit_id}),)), _model_turn("Publish these ratings?"),
    ])
    assert _results(events)[0]["success"] is False
    async with env.db() as db:
        assert (await db.get(GovernanceHealthAudit, uuid.UUID(audit_id))).status == "draft"
    done, _, model = await _chat(env, "ben", "Yes, publish it.", [], session_id=session)
    model.assert_not_awaited()
    assert _results(done)[0]["success"] is True
    async with env.db() as db:
        published = await db.get(GovernanceHealthAudit, uuid.UUID(audit_id))
        assert published.status == "completed" and published.overall_health_score is not None
        assert any("basis" in row for row in published.indicator_scores)
    cannot_edit = await _tool(env, "ben", "update_health_audit", audit_id=audit_id, changes={"findings": "Edit after publication"})
    assert cannot_edit["success"] is False


async def test_changed_audit_and_lost_independence_cannot_publish_old_plan(env):
    audit_id = await _rated_audit(env)
    _, session, _ = await _chat(env, "ben", "Publish the audit.", [
        _model_turn(calls=(("publish_health_audit", {"audit_id": audit_id}),)), _model_turn("Publish?"),
    ])
    await _tool(env, "ben", "update_health_audit", audit_id=audit_id, changes={"findings": "Material new finding before publication"})
    done, _, _ = await _chat(env, "ben", "Yes", [], session_id=session)
    assert _results(done)[0]["success"] is False
    async with env.db() as db:
        assert (await db.get(GovernanceHealthAudit, uuid.UUID(audit_id))).status == "draft"
        (await db.get(Member, PEOPLE["ben"].member_id())).role = "mod"
        await db.commit()
    denied = await _tool(env, "ben", "publish_health_audit", audit_id=audit_id, confirmed=True)
    assert denied["success"] is False and denied.get("code") == "AUDITOR_NOT_INDEPENDENT"


async def test_audit_abandonment_records_reason_and_never_publishes(env):
    created = await _tool(env, "ben", "create_safeguard_audit", findings="A draft needing more evidence")
    audit_id = created["data"]["id"]
    assert not (await _tool(env, "mo", "abandon_health_audit", audit_id=audit_id, reason="short", confirmed=True))["success"]
    done = await _tool(env, "mo", "abandon_health_audit", audit_id=audit_id, reason="Duplicate of the current audit", confirmed=True)
    assert done["success"], done
    async with env.db() as db:
        assert (await db.get(GovernanceHealthAudit, uuid.UUID(audit_id))).status == "abandoned"


async def test_exit_cancel_completion_and_private_export_link_without_approval_wait(env):
    env.app.blueprint(exit_api_bp)
    first = await _tool(env, "ben", "create_exit_record", confirmed=True)
    first_id = first["data"]["id"]
    assert not (await _tool(env, "mo", "update_exit_status", exit_id=first_id, new_status="cancelled", confirmed=True))["success"]
    cancelled = await _tool(env, "ben", "update_exit_status", exit_id=first_id, new_status="cancelled", confirmed=True)
    assert cancelled["success"] and cancelled["data"]["status"] == "cancelled"
    second = await _tool(env, "ben", "create_exit_record", confirmed=True)
    second_id = second["data"]["id"]
    assert not (await _tool(env, "ben", "update_exit_status", exit_id=second_id, new_status="completed", confirmed=True))["success"]
    completed = await _tool(env, "mo", "update_exit_status", exit_id=second_id, new_status="completed", confirmed=True)
    assert completed["success"], completed
    async with env.db() as db:
        assert (await db.get(Member, PEOPLE["ben"].member_id())).current_status == "exited"
    link = await _tool(env, "ben", "export_portable_record", scope=[], exit_id=second_id)
    assert link["success"] and link["data"]["downloaded"] is False
    assert "proposals_authored" not in json.dumps(link)
    assert _record_reference(link["data"])[0] == f"/api/v1/exit/{second_id}/portable-record"
    async with env.db() as db:
        assert (await db.get(ExitRecord, uuid.UUID(second_id))).data_export_completed is None
    _, download = await env.app.asgi_client.get(link["data"]["link"], headers={"x-test-as": "ben"})
    assert download.status == 200 and download.json["format"] == "neos-portable-record/1"
    denied = await _tool(env, "mo", "export_portable_record", exit_id=second_id)
    assert denied["success"] is False


async def test_specific_exit_cancel_request_saves_frozen_confirmation_executes_once_and_cannot_replay(env):
    from neos_agent.db.models import AgentSession
    created = await _tool(env, "ben", "create_exit_record", confirmed=True)
    exit_id = created["data"]["id"]
    action = {"exit_id": exit_id, "new_status": "cancelled"}
    events, session, _ = await _chat(env, "ben", f"Cancel my own exit {exit_id}.", [
        _model_turn(calls=(("update_exit_status", action),)), _model_turn("Cancel this exit?")])
    assert _results(events)[0]["needs_confirmation"]
    async with env.db() as db:
        assert (await db.get(ExitRecord, uuid.UUID(exit_id))).status == "declared"
        pending = (await db.get(AgentSession, uuid.UUID(session))).context["pending_confirmations"]
        assert len(pending) == 1 and pending[0]["args"] == action
    events, _, model = await _chat(env, "ben", "Yes, cancel it.", [], session_id=session)
    model.assert_not_awaited()
    assert _results(events)[0]["success"]
    async with env.db() as db:
        assert (await db.get(ExitRecord, uuid.UUID(exit_id))).status == "cancelled"
    events, _, replay = await _chat(env, "ben", "Yes, cancel it.", [], session_id=session)
    replay.assert_not_awaited()
    assert not _results(events)


@pytest.mark.parametrize("message, expected", [
    ("Cancel", "cancel"), ("No, cancel.", "cancel"),
    ("No, cancel. Where does my proposal stand?", "cancel"),
    ("Cancel the pending action.", "cancel"), ("Do not go ahead.", "cancel"),
    ("Cancel my own exit 00000000-0000-4000-8000-000000000001.", None),
    ("Cancel exit 00000000-0000-4000-8000-000000000001.", None),
    ("Stop the emergency authority.", None), ("Yes, cancel it.", "confirm:cancel"),
])
def test_pending_controls_do_not_consume_specific_domain_action_requests(message, expected):
    assert _confirmation_reply(message) == expected


async def test_conflict_resolution_close_and_repair_follow_shared_policy(env):
    reported = await _tool(env, "ben", "create_conflict_case", title="Noise at night", description="Loud work after dark")
    case_id = reported["data"]["id"]
    denied = await _tool(env, "ada", "update_conflict_case", case_id=case_id, changes={"status": "closed"}, confirmed=True)
    assert denied["success"] is False and denied["error"] == "Conflict case not found"
    skipped = await _tool(env, "mo", "update_conflict_case", case_id=case_id, changes={"status": "resolved", "resolution_summary": "Agreed on quiet hours"}, confirmed=True)
    assert skipped["success"] is False
    assert (await _tool(env, "mo", "update_conflict_case", case_id=case_id, changes={"status": "triaged"}, confirmed=True))["success"]
    no_summary = await _tool(env, "mo", "update_conflict_case", case_id=case_id, changes={"status": "resolved"}, confirmed=True)
    assert no_summary["success"] is False
    resolved = await _tool(env, "mo", "update_conflict_case", case_id=case_id, changes={"status": "resolved", "resolution_summary": "Both agreed on quiet hours"}, confirmed=True)
    assert resolved["success"], resolved
    repair_id = uuid.uuid4()
    async with env.db() as db:
        db.add(RepairAgreementRecord(id=repair_id, conflict_case_id=uuid.UUID(case_id), title="Quiet hours check-in", commitments={"items": ["Stop loud work after dark"]}, status="active"))
        await db.commit()
    no_attestation = await _tool(env, "mo", "update_repair_agreement", case_id=case_id, repair_id=str(repair_id), changes={"status": "fulfilled"}, confirmed=True)
    assert no_attestation["success"] is False
    bypass = await _tool(env, "mo", "update_repair_agreement", case_id=case_id, repair_id=str(repair_id), changes={"status": "completed"}, confirmed=True)
    assert bypass["success"] is False
    done = await _tool(env, "mo", "update_repair_agreement", case_id=case_id, repair_id=str(repair_id),
        changes={"status": "fulfilled", "confirmed_by_parties": True, "checkin_30_notes": "Both parties reported it worked."}, confirmed=True)
    assert done["success"], done
    async with env.db() as db:
        repair = await db.get(RepairAgreementRecord, repair_id)
        assert repair.status == "fulfilled" and repair.completed_date is not None
        assert repair.commitments["confirmed_by_parties_on"]
    closed = await _tool(env, "mo", "update_conflict_case", case_id=case_id, changes={"status": "closed"}, confirmed=True)
    assert closed["success"]
    async with env.db() as db:
        assert (await db.get(ConflictCase, uuid.UUID(case_id))).status == "closed"


@pytest.mark.parametrize("prepared_status", [False, True])
async def test_qualified_resolution_executes_only_the_exact_prepared_status_and_never_narrates_a_refused_change(env, prepared_status):
    created = await _tool(env, "ben", "create_conflict_case", title="Quiet work", description="Loud work after dark")
    case_id = created["data"]["id"]
    assert (await _tool(env, "mo", "update_conflict_case", case_id=case_id, changes={"status": "triaged"}, confirmed=True))["success"]
    summary = "Both parties agreed to stop loud work after dark."
    changes = {"resolution_summary": summary, **({"status": "resolved"} if prepared_status else {})}
    action = {"case_id": case_id, "changes": changes}
    events, session, _ = await _chat(env, "mo", f"Resolve case {case_id} with this exact summary: {summary}", [
        _model_turn(calls=(("update_conflict_case", action),)), _model_turn("Record these exact changes?")])
    assert _results(events)[0]["needs_confirmation"]
    events, _, model = await _chat(env, "mo", "Yes, resolve it.", [
        _model_turn("The case is now resolved.", calls=(("update_conflict_case", {"case_id": case_id, "changes": {"status": "resolved", "resolution_summary": summary}, "confirmed": True}),)),
    ], session_id=session)
    model.assert_not_awaited()
    assert _results(events)[0]["success"] is prepared_status
    text = "".join(data for kind, data in events if kind == "append")
    if not prepared_status:
        assert "Nothing was changed." in text
        assert "now resolved" not in text
    async with env.db() as db:
        record = await db.get(ConflictCase, uuid.UUID(case_id))
        assert record.status == ("resolved" if prepared_status else "triaged")
        assert record.resolution_summary == (summary if prepared_status else None)
    if not prepared_status:
        async with env.db() as db:
            stored = (await db.get(AgentSession, uuid.UUID(session))).context
            assert len(stored["pending_confirmations"]) == 1
            assert stored["pending_confirmations"][0]["args"] == action
        summary_only, _, original = await _chat(env, "mo", "Yes", [], session_id=session)
        original.assert_not_awaited()
        assert _results(summary_only)[0]["success"]
        dispatched = [json.loads(data) for kind, data in summary_only if kind == "tool_start"]
        assert dispatched[0]["args"] == {**action, "confirmed": True}
        async with env.db() as db:
            record = await db.get(ConflictCase, uuid.UUID(case_id))
            assert record.status == "triaged" and record.resolution_summary == summary
        replayed, _, repeat = await _chat(env, "mo", "Yes", [], session_id=session)
        repeat.assert_not_awaited()
        assert not _results(replayed)
        await _chat(env, "mo", f"Resolve this case with the summary {summary}", [
            _model_turn(calls=(("update_conflict_case", {"case_id": case_id, "changes": {"status": "resolved", "resolution_summary": summary}}),)),
            _model_turn("Resolve the case with this summary?")], session_id=session)
        done, _, executed = await _chat(env, "mo", "Yes, resolve it.", [], session_id=session)
        executed.assert_not_awaited()
        assert _results(done)[0]["success"]
    events, _, replay = await _chat(env, "mo", "Yes, resolve it.", [], session_id=session)
    replay.assert_not_awaited()
    assert not _results(events)
    async with env.db() as db:
        record = await db.get(ConflictCase, uuid.UUID(case_id))
        assert record.status == "resolved" and record.resolution_summary == summary


def test_conflict_changes_expose_the_actual_shared_form_fields():
    from neos_agent.api.schemas.conflicts import ConflictUpdateRequest
    definition = next(row for row in get_tool_definitions() if row["name"] == "update_conflict_case")
    changes = definition["input_schema"]["properties"]["changes"]
    assert set(changes["properties"]) == set(ConflictUpdateRequest.model_fields)
    assert "status" in changes["properties"] and "resolution_summary" in changes["properties"]
    assert "summary" not in changes["properties"]


@pytest.mark.parametrize("reply, tool, args, expected", [
    ("Yes, send it", "send_message", {}, True), ("Yes, publish it", "send_message", {}, False),
    ("Yes, cancel it", "update_exit_status", {"new_status": "cancelled"}, True),
    ("Yes, close it", "update_conflict_case", {"changes": {"status": "resolved"}}, False),
    ("Yes, resolve it", "update_conflict_case", {"changes": {"status": "resolved"}}, True),
    ("Yes, abandon it", "abandon_health_audit", {}, True),
])
def test_qualified_confirmation_names_the_actual_operator_action(reply, tool, args, expected):
    assert tool in CONFIRMATION_TOOLS
    assert _confirmation_matches_action(_confirmation_reply(reply), tool, args) is expected


def test_new_operator_tools_have_human_labels_and_explicit_actor_dispatch():
    from neos_agent.api.chat import _TOOL_DISPLAY_NAMES
    from neos_agent.agent.operator_tools import READ_TOOLS, SPECS
    from neos_agent.agent.governance_tools import CALLER_AWARE_TOOLS, CALLER_SCOPED_TOOLS
    definitions = {row["name"] for row in get_tool_definitions()}
    assert set(SPECS) <= definitions & set(_TOOL_DISPLAY_NAMES)
    assert READ_TOOLS <= CALLER_AWARE_TOOLS
    assert set(SPECS) - READ_TOOLS <= CALLER_SCOPED_TOOLS


async def test_plain_record_help_matches_actual_standing_and_consensus_without_writing(env):
    from tests.test_g_agent_assistant import _proposal
    proposal = await _proposal(env)
    reader = await _tool(env, "ben", "get_proposal", proposal_id=str(proposal.id))
    author = await _tool(env, "ada", "get_proposal", proposal_id=str(proposal.id))
    assert "share what may help" in reader["data"]["plain_help"]
    assert "You wrote it" in author["data"]["plain_help"]
    assert len(reader["data"]["plain_help"].split()) < 70
    async with env.db() as db:
        record = await db.get(type(proposal), proposal.id)
        record.status, record.decision_type = "consent", "consensus"
        await db.commit()
    consensus = await _tool(env, "ben", "get_proposal", proposal_id=str(proposal.id))
    assert "Standing aside is not a choice" in consensus["data"]["plain_help"]


def test_legal_unicode_message_can_be_frozen_without_truncation():
    from neos_agent.api.chat import _frozen_args
    content = "🌱" * 10000
    frozen = _frozen_args({"conversation_id": str(uuid.uuid4()), "content": content, "confirmed": True})
    assert frozen["content"] == content and "confirmed" not in frozen


@pytest.mark.parametrize("legacy", [False, True])
async def test_registered_repair_creation_or_legacy_list_reads_checks_in_and_fulfills_once(env, legacy):
    from neos_agent.api.conflicts import conflicts_api_bp
    env.app.blueprint(conflicts_api_bp)
    report = await _tool(env, "ben", "create_conflict_case", title="Repair flow", description="Restore the shared shed")
    case_id = report["data"]["id"]
    items = [{"commitment": "Repair the hinge", "owner": "Ben"}]
    if legacy:
        repair_id = str(uuid.uuid4())
        async with env.db() as db:
            db.add(RepairAgreementRecord(id=uuid.UUID(repair_id), conflict_case_id=uuid.UUID(case_id), title="Hinge repair", commitments=items, status="active"))
            await db.commit()
    else:
        created = await _tool(env, "mo", "create_repair_agreement", case_id=case_id, title="Hinge repair", commitments=items)
        assert created["success"], created
        repair_id = created["data"]["id"]
    _, response = await env.app.asgi_client.get(f"/api/v1/conflicts/{case_id}", headers={"x-test-as": "mo"})
    assert response.status == 200, response.text
    assert response.json["repair_agreements"][0]["commitments"]["items"] == items
    detail = await _tool(env, "mo", "get_conflict_case", case_id=case_id)
    assert detail["success"] and detail["data"]["repair_agreements"][0]["title"] == "Hinge repair"
    _, checkin = await env.app.asgi_client.put(f"/api/v1/conflicts/{case_id}/repair/{repair_id}", headers={"x-test-as": "mo"}, json={"checkin_30_notes": "Hinge repaired; both parties checked it."})
    assert checkin.status == 200 and checkin.json["commitments"]["items"] == items
    action = {"case_id": case_id, "repair_id": repair_id, "changes": {"status": "fulfilled", "confirmed_by_parties": True}}
    events, session, _ = await _chat(env, "mo", "Both parties confirmed this repair is done. Mark it fulfilled.", [
        _model_turn(calls=(("update_repair_agreement", action),)), _model_turn("Mark this repair fulfilled?")])
    assert not _results(events)[0]["success"]
    events, _, model = await _chat(env, "mo", "Yes, complete it", [], session_id=session)
    model.assert_not_awaited()
    assert _results(events)[0]["success"]
    events, _, replay = await _chat(env, "mo", "Yes", [], session_id=session)
    replay.assert_not_awaited()
    assert not _results(events)
    async with env.db() as db:
        saved = await db.get(RepairAgreementRecord, uuid.UUID(repair_id))
        assert saved.status == "fulfilled" and saved.completed_date is not None
        assert saved.commitments["items"] == items and saved.commitments["confirmed_by_parties_on"]
        assert saved.checkin_30_notes == "Hinge repaired; both parties checked it."
