"""Authorization, public accountability and reversible node support corrections."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from neos_agent.api.errors import ApiError
from neos_agent.api.schemas.node_admin import SupportCommandRequest
from neos_agent.auth.middleware import is_public_route
from neos_agent.db.models import AdviceEntry, AdviceLog, AppSetting, Base, Ecosystem, Member, NodeAdmin, NodeAdminAction, NodeAdminSnapshot, Proposal, User
from neos_agent.services.node_admin import change_admin, execute_command, initialize_node_support, inspect_resource, is_node_admin, serialize_audit
from neos_agent.services.node_admin_catalog import INTERNAL, registry


@pytest_asyncio.fixture
async def support(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'support.db').as_posix()}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    owner, second, plain = [uuid.uuid4() for _ in range(3)]
    org, other = uuid.uuid4(), uuid.uuid4()
    async with factory() as session:
        session.add_all([User(id=owner, display_name="Support One", did="did:key:support-one"), User(id=second, display_name="Support Two", did="did:key:support-two"), User(id=plain, display_name="Founder", did="did:key:founder")])
        session.add_all([Ecosystem(id=org, name="Organization", status="active"), Ecosystem(id=other, name="Private org", status="active", visibility="private")])
        await session.flush()
        session.add(NodeAdmin(user_id=owner, active=True))
        session.add(Member(ecosystem_id=org, user_id=plain, member_id="MEM-founder", display_name="Founder", profile="co_creator", role="owner", current_status="active"))
        await session.commit()
    yield SimpleNamespace(engine=engine, factory=factory, owner=owner, second=second, plain=plain, org=org, other=other)
    await engine.dispose()


def command(kind, action, reason="Technical support", **kwargs):
    return SupportCommandRequest(resource_type=kind, action=action, reason=reason, **kwargs)


async def create_proposal(support):
    return await execute_command(support.factory, support.owner, command("proposals", "create", organization_id=support.other,
        values={"type": "operational", "title": "Support proposal", "proposed_change": "Private body sentinel", "rationale": "Private rationale sentinel"}))


async def test_explicit_role_is_independent_of_profile_and_target_membership(support):
    async with support.factory() as session:
        assert await is_node_admin(session, support.owner)
        assert not await is_node_admin(session, support.plain)
        assert not await session.scalar(select(Member.id).where(Member.user_id == support.owner))
    with pytest.raises(ApiError, match="Node administrator"):
        await execute_command(support.factory, support.plain, command("proposals", "create", organization_id=support.other, values={"type": "operational", "title": "Unauthorized"}))
    receipt = await create_proposal(support)
    async with support.factory() as session:
        proposal = await session.get(Proposal, uuid.UUID(receipt["resource"]["id"]))
        assert proposal.ecosystem_id == support.other
        assert proposal.proposer_member_id is None
        assert proposal.support_created_by_user_id == support.owner
        assert str(proposal.support_action_id) == receipt["audit_id"]
        event = await session.get(NodeAdminAction, uuid.UUID(receipt["audit_id"]))
        assert event.actor_user_id == support.owner and event.organization_id == support.other
        assert event.safe_summary == {"administrative_correction": True}
        assert "Private body sentinel" not in json.dumps(serialize_audit(event))
        snapshot = await session.scalar(select(NodeAdminSnapshot).where(NodeAdminSnapshot.action_id == event.id))
        assert snapshot.snapshot["after"]["proposed_change"] == "Private body sentinel"


async def test_correction_requires_version_and_private_values_never_enter_public_audit(support):
    receipt = await create_proposal(support)
    resource_id = receipt["resource"]["id"]
    with pytest.raises(ApiError, match="Inspect"):
        await execute_command(support.factory, support.owner, command("proposals", "update", resource_id=resource_id, values={"title": "Changed"}))
    inspected = await inspect_resource(support.factory, support.owner, "proposals", resource_id, "password=private-contact@example.invalid")
    updated = await execute_command(support.factory, support.owner, command("proposals", "update", resource_id=resource_id,
        expected_version=inspected["resource"]["version"], values={"proposed_change": "New confidential body"}, reason="private-contact@example.invalid"))
    with pytest.raises(ApiError, match="changed"):
        await execute_command(support.factory, support.owner, command("proposals", "update", resource_id=resource_id,
            expected_version=inspected["resource"]["version"], values={"title": "Stale"}))
    async with support.factory() as session:
        events = (await session.scalars(select(NodeAdminAction))).all()
        public = json.dumps([serialize_audit(event) for event in events])
        assert "confidential" not in public and "private-contact" not in public and "Private body" not in public
        assert "Technical support" in public
        assert updated["audit_id"] in public


async def test_failed_cross_org_reference_does_not_mutate_or_commit_success_audit(support):
    receipt = await create_proposal(support)
    async with support.factory() as session:
        from neos_agent.db.models import Agreement
        agreement = Agreement(ecosystem_id=support.org, agreement_id="AGR-wrong", type="policy", title="Wrong organization")
        session.add(agreement)
        await session.commit()
        agreement_id = agreement.id
        before = await session.scalar(select(func.count()).select_from(NodeAdminAction))
    with pytest.raises(ApiError, match="another organization"):
        await execute_command(support.factory, support.owner, command("proposals", "update", resource_id=receipt["resource"]["id"],
            expected_version=receipt["resource"]["version"], values={"governing_agreement_id": str(agreement_id)}))
    async with support.factory() as session:
        assert await session.scalar(select(func.count()).select_from(NodeAdminAction)) == before
        assert (await session.get(Proposal, uuid.UUID(receipt["resource"]["id"]))).governing_agreement_id is None


async def test_audit_insert_failure_rolls_back_the_state_change(support, monkeypatch):
    from sqlalchemy import event
    def reject_audit(*_):
        raise RuntimeError("audit unavailable")
    event.listen(NodeAdminAction, "before_insert", reject_audit)
    try:
        with pytest.raises(RuntimeError, match="audit unavailable"):
            await create_proposal(support)
    finally:
        event.remove(NodeAdminAction, "before_insert", reject_audit)
    async with support.factory() as session:
        assert await session.scalar(select(func.count()).select_from(Proposal)) == 0
        assert await session.scalar(select(func.count()).select_from(NodeAdminSnapshot)) == 0


@pytest.mark.parametrize("table", ["node_admin_actions", "node_admin_snapshots"])
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
async def test_storage_rejects_audit_and_archive_mutation(support, table, operation):
    await create_proposal(support)
    async with support.engine.begin() as connection:
        sql = f"UPDATE {table} SET resource_type = 'tampered'" if operation == "UPDATE" else f"DELETE FROM {table}"
        with pytest.raises(DBAPIError, match="append-only"):
            await connection.execute(text(sql))


async def test_two_admins_can_manage_across_orgs_but_cannot_remove_last_usable_admin(support):
    await change_admin(support.factory, support.owner, support.second, "Access management")
    receipt = await execute_command(support.factory, support.second, command("proposals", "create", organization_id=support.org, values={"type": "policy", "title": "Second operator"}))
    assert receipt["resource"]["support_created_by_user_id"] == str(support.second)
    await change_admin(support.factory, support.second, support.owner, "Access management", revoke=True)
    with pytest.raises(ApiError, match="last node administrator"):
        await change_admin(support.factory, support.second, support.second, "Access management", revoke=True)
    with pytest.raises(ApiError, match="Node administrator"):
        await execute_command(support.factory, support.owner, command("proposals", "create", organization_id=support.other, values={"type": "policy", "title": "Revoked"}))


async def test_concurrent_self_revocations_leave_a_usable_administrator(support):
    await change_admin(support.factory, support.owner, support.second, "Access management")
    results = await asyncio.gather(change_admin(support.factory, support.owner, support.owner, "Access management", revoke=True),
                                   change_admin(support.factory, support.second, support.second, "Access management", revoke=True), return_exceptions=True)
    assert sum(isinstance(result, dict) for result in results) == 1
    assert any(isinstance(result, ApiError) for result in results)
    async with support.factory() as session:
        assert await session.scalar(select(func.count()).select_from(NodeAdmin).where(NodeAdmin.active.is_(True))) == 1


async def test_evidence_subtree_archival_and_restore_preserve_original_human_statements(support):
    receipt = await create_proposal(support)
    async with support.factory() as session:
        log = AdviceLog(proposal_id=uuid.UUID(receipt["resource"]["id"]))
        session.add(log)
        await session.flush()
        entry = AdviceEntry(advice_log_id=log.id, advisor="Actual human", advice_text="Original private advice")
        session.add(entry)
        await session.commit()
        log_id, entry_id = log.id, entry.id
    inspected = await inspect_resource(support.factory, support.owner, "advice_logs", log_id, "Data correction")
    archived = await execute_command(support.factory, support.owner, command("advice_logs", "archive_evidence", resource_id=log_id, expected_version=inspected["resource"]["version"]))
    async with support.factory() as session:
        assert await session.get(AdviceLog, log_id) is None and await session.get(AdviceEntry, entry_id) is None
    restored = await execute_command(support.factory, support.owner, command("advice_logs", "restore_evidence", resource_id=log_id, values={"archive_id": archived["resource"]["archive_id"]}))
    assert not restored["resource"]["archived"]
    async with support.factory() as session:
        entry = await session.get(AdviceEntry, entry_id)
        assert entry.advisor == "Actual human" and entry.advice_text == "Original private advice"
        public = json.dumps([serialize_audit(row) for row in (await session.scalars(select(NodeAdminAction))).all()])
        assert "Original private advice" not in public and "Actual human" not in public
    with pytest.raises(ApiError, match="still exists"):
        await execute_command(support.factory, support.owner, command("advice_logs", "restore_evidence", resource_id=log_id, values={"archive_id": archived["resource"]["archive_id"]}))


def test_catalog_inventory_and_feature_families_have_real_repairs():
    resources = registry()
    actual = {mapper.class_.__tablename__ for mapper in Base.registry.mappers}
    assert set(resources) | INTERNAL == actual
    assert all(any(action != "inspect" for action in spec.actions) for spec in resources.values())
    for family in ("users", "members", "ecosystems", "domains", "proposals", "agreements", "conflict_cases", "repair_agreement_records", "emergency_states", "exit_records", "governance_health_audits", "shares_needs", "collaborations", "courses", "quizzes", "user_journey_progress", "user_badges", "teams", "messages", "agent_sessions", "consent_participants", "agreement_member_consents"):
        assert set(resources[family].actions) - {"inspect"}, family
    assert "password_hash" not in resources["users"].editable
    assert resources["agent_tokens"].actions == ["revoke"]


def test_public_support_paths_are_get_only_and_exact():
    assert is_public_route("/api/v1/node-admin/roster", "GET")
    assert is_public_route("/api/v1/node-admin/audit", "GET")
    assert is_public_route(f"/api/v1/node-admin/audit/{uuid.uuid4()}", "GET")
    for path in ("/api/v1/node-admin/catalog", "/api/v1/node-admin/auditors", "/api/v1/node-admin/audit/secret/more"):
        assert not is_public_route(path, "GET")
    assert not is_public_route("/api/v1/node-admin/audit", "POST")


async def test_controlled_fresh_bootstrap_never_uses_profiles_or_founders(support):
    await initialize_node_support(support.factory, "")
    async with support.factory() as session:
        assert not await is_node_admin(session, support.plain)
        assert await session.scalar(select(func.count()).select_from(NodeAdmin)) == 1


async def test_disabling_last_usable_admin_is_refused(support):
    inspected = await inspect_resource(support.factory, support.owner, "users", support.owner, "Account recovery")
    with pytest.raises(ApiError, match="last usable"):
        await execute_command(support.factory, support.owner, command("users", "update", resource_id=support.owner, expected_version=inspected["resource"]["version"], values={"disabled_at": datetime.now().isoformat()}))


async def test_only_explicit_bootstrap_ids_are_granted_once(support):
    async with support.factory() as session:
        await session.execute(delete(NodeAdmin))
        await session.commit()
    await initialize_node_support(support.factory, "")
    async with support.factory() as session:
        assert not await session.scalar(select(NodeAdmin.user_id))
        assert await session.scalar(select(AppSetting.id).where(AppSetting.key == "node_admin_bootstrap_complete")) is None
    await initialize_node_support(support.factory, str(support.owner))
    await initialize_node_support(support.factory, str(support.plain))
    async with support.factory() as session:
        assert (await session.scalars(select(NodeAdmin.user_id))).all() == [support.owner]
        event = await session.scalar(select(NodeAdminAction))
        assert event.source == "bootstrap" and event.actor_name == "Server bootstrap"


async def test_agent_persistence_failure_is_redacted_and_audited(support, monkeypatch, caplog):
    from sqlalchemy.exc import IntegrityError
    from neos_agent.agent import node_admin_tools
    context = {"enabled": True, "organization_id": str(support.other), "reason": "Agent testing"}
    arguments = {"resource_type": "proposals", "action": "create", "values": {"type": "policy", "title": "private-SQL-marker"}}
    pending = await node_admin_tools.execute_node_admin_tool("node_support_command", arguments, factory=support.factory, caller_user_id=support.owner, support_context=context)
    assert "private-SQL-marker" in pending["needs_confirmation"] and str(support.other) in pending["needs_confirmation"]
    assert "new record" in pending["needs_confirmation"]
    async def fail(*_args, **_kwargs):
        raise IntegrityError("private-SQL-marker", {"body": "private-SQL-marker"}, Exception("private-SQL-marker"))
    monkeypatch.setattr(node_admin_tools, "execute_command", fail)
    result = await node_admin_tools.execute_node_admin_tool("node_support_command", {**arguments, "confirmed": True}, factory=support.factory,
        caller_user_id=support.owner, support_context=context, confirmed_keys=frozenset({pending["confirmation_key"]}))
    assert not result["success"] and "private-SQL-marker" not in json.dumps(result) + caplog.text
    async with support.factory() as session:
        event = await session.scalar(select(NodeAdminAction).where(NodeAdminAction.action == "agent_support_request"))
        assert event.outcome == "failed" and event.source == "agent"


async def test_session_revocation_preserves_token_fk_and_expires_parent_liveness(support):
    import hashlib
    from neos_agent.db.models import AgentToken, AuthSession
    async with support.factory() as session:
        parent = AuthSession(user_id=support.plain, expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1))
        session.add(parent)
        await session.flush()
        token = AgentToken(user_id=support.plain, auth_session_id=parent.id, label="Existing agent", token_hash=hashlib.sha256(b"test-token").hexdigest(), expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1))
        session.add(token)
        await session.commit()
        parent_id, token_id = parent.id, token.id
    inspected = await inspect_resource(support.factory, support.owner, "auth_sessions", parent_id, "Account recovery")
    assert "token_hash" not in inspected["resource"] and "user_agent" not in inspected["resource"]
    await execute_command(support.factory, support.owner, command("auth_sessions", "revoke", resource_id=parent_id, expected_version=inspected["resource"]["version"]))
    async with support.factory() as session:
        assert (await session.get(AuthSession, parent_id)).expires_at <= datetime.now(timezone.utc).replace(tzinfo=None)
        assert await session.get(AgentToken, token_id) is not None


async def test_last_session_only_admin_cannot_revoke_its_only_usable_sign_in(support):
    from neos_agent.db.models import AuthSession
    async with support.factory() as session:
        (await session.get(User, support.owner)).did = None
        parent = AuthSession(user_id=support.owner, expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1))
        session.add(parent)
        await session.commit()
        parent_id = parent.id
    inspected = await inspect_resource(support.factory, support.owner, "auth_sessions", parent_id, "Account recovery")
    with pytest.raises(ApiError, match="last usable"):
        await execute_command(support.factory, support.owner, command("auth_sessions", "revoke", resource_id=parent_id, expected_version=inspected["resource"]["version"]))
    async with support.factory() as session:
        assert (await session.get(AuthSession, parent_id)).expires_at > datetime.now(timezone.utc).replace(tzinfo=None)


async def test_agent_lookup_discovers_exact_ids_and_scopes_parent_records(support):
    from neos_agent.agent.node_admin_tools import execute_node_admin_tool
    context = {"enabled": True, "organization_id": str(support.other), "reason": "Agent testing"}
    receipt = await create_proposal(support)
    foreign = await execute_command(support.factory, support.owner, command("proposals", "create", organization_id=support.org, values={"type": "policy", "title": "Other support proposal"}))
    async with support.factory() as session:
        local_log = AdviceLog(proposal_id=uuid.UUID(receipt["resource"]["id"]))
        foreign_log = AdviceLog(proposal_id=uuid.UUID(foreign["resource"]["id"]))
        session.add_all([local_log, foreign_log])
        await session.commit()
        local_id, foreign_id = str(local_log.id), str(foreign_log.id)
    listed = await execute_node_admin_tool("node_support_list", {"resource_type": "proposals", "search": "Support proposal"}, factory=support.factory, caller_user_id=support.owner, support_context=context)
    assert listed["success"] and [row["id"] for row in listed["data"]["items"]] == [receipt["resource"]["id"]]
    parent = await execute_node_admin_tool("node_support_list", {"resource_type": "advice_logs"}, factory=support.factory, caller_user_id=support.owner, support_context=context)
    assert parent["success"] and [row["id"] for row in parent["data"]["items"]] == [local_id]
    assert foreign_id not in json.dumps(parent)


async def test_complete_catalog_and_targeted_fields_survive_actual_model_result_budget(support):
    from neos_agent.agent.node_admin_tools import definitions_for_node_admin, execute_node_admin_tool
    from neos_agent.api.chat import _fit_tool_result
    context = {"enabled": True, "organization_id": str(support.other), "reason": "Agent testing"}
    definitions = await definitions_for_node_admin(support.factory, support.owner, context)
    for definition in definitions:
        if "resource_type" in definition["input_schema"]["properties"]:
            assert definition["input_schema"]["properties"]["resource_type"]["enum"] == sorted(registry())
    index = _fit_tool_result(await execute_node_admin_tool("node_support_catalog", {}, factory=support.factory, caller_user_id=support.owner, support_context=context))
    assert set(index["data"]["resource_actions"]) == set(registry())
    schema = _fit_tool_result(await execute_node_admin_tool("node_support_catalog", {"resource_type": "proposals"}, factory=support.factory, caller_user_id=support.owner, support_context=context))
    assert set(schema["data"]["fields"]) >= {"title", "type", "proposed_change", "rationale", "status"}
    assert not {"id", "ecosystem_id", "proposer_member_id", "support_created_by_user_id", "support_action_id", "created_at", "updated_at"} & set(schema["data"]["fields"])
    assert schema["data"]["fields"]["proposed_change"]["editable"] and schema["data"]["fields"]["rationale"]["editable"]
    assert len(json.dumps(schema)) <= 24000
    oversized = _fit_tool_result({"complete_support_schema": True, "data": "private" * 5000})
    assert not oversized["success"] and "data" not in oversized
    await execute_node_admin_tool("node_support_list", {"resource_type": "not_a_resource"}, factory=support.factory, caller_user_id=support.owner, support_context=context)
    async with support.factory() as session:
        failure = await session.scalar(select(NodeAdminAction).where(NodeAdminAction.action == "agent_support_request"))
        assert failure.organization_id == support.other and failure.reason == "Agent testing"


async def test_typed_proposal_preparation_defaults_and_server_key_bind_actual_actor_and_organization(support):
    from neos_agent.agent.node_admin_tools import execute_node_admin_tool
    context = {"enabled": True, "organization_id": str(support.other), "reason": "Agent testing"}
    args = {"title": "Typed organization draft", "proposed_change": "Share locally adapted seeds"}
    pending = await execute_node_admin_tool("node_support_prepare_proposal", args, factory=support.factory, caller_user_id=support.owner, support_context=context)
    assert pending["needs_confirmation"] and '"status": "draft"' in pending["needs_confirmation"]
    assert '"type": "operational"' in pending["needs_confirmation"]
    no_key = await execute_node_admin_tool("node_support_prepare_proposal", {**args, "confirmed": True}, factory=support.factory, caller_user_id=support.owner, support_context=context)
    assert no_key["confirmation_key"] == pending["confirmation_key"] and not no_key["success"]
    retargeted = await execute_node_admin_tool("node_support_prepare_proposal", {**args, "title": "Altered draft", "confirmed": True}, factory=support.factory,
        caller_user_id=support.owner, support_context=context, confirmed_keys=frozenset({pending["confirmation_key"]}))
    assert not retargeted["success"] and retargeted["confirmation_key"] != pending["confirmation_key"]
    async with support.factory() as session:
        assert not (await session.scalars(select(Proposal).where(Proposal.title.in_([args["title"], "Altered draft"])))).all()
    created = await execute_node_admin_tool("node_support_prepare_proposal", {**args, "confirmed": True}, factory=support.factory,
        caller_user_id=support.owner, support_context=context, confirmed_keys=frozenset({pending["confirmation_key"]}))
    assert created["success"] and created["data"]["resource"]["status"] == "draft"
    async with support.factory() as session:
        proposal = await session.get(Proposal, uuid.UUID(created["data"]["resource"]["id"]))
        assert proposal.ecosystem_id == support.other and proposal.proposer_member_id is None
        assert proposal.support_created_by_user_id == support.owner
        audit = await session.get(NodeAdminAction, uuid.UUID(created["data"]["audit_id"]))
        assert audit.actor_user_id == support.owner and audit.organization_id == support.other and audit.source == "agent"


async def test_typed_proposal_rejects_authority_fields_and_generic_failure_names_safe_writable_fields(support):
    from neos_agent.agent.node_admin_tools import definitions_for_node_admin, execute_node_admin_tool
    context = {"enabled": True, "organization_id": str(support.other), "reason": "Agent testing"}
    definitions = await definitions_for_node_admin(support.factory, support.owner, context)
    typed = next(item for item in definitions if item["name"] == "node_support_prepare_proposal")
    assert set(typed["input_schema"]["properties"]) == {"title", "proposed_change", "rationale", "type"}
    assert typed["input_schema"]["additionalProperties"] is False
    forged = await execute_node_admin_tool("node_support_prepare_proposal", {"title": "Draft", "proposed_change": "Seeds", "organization_id": str(support.org)},
        factory=support.factory, caller_user_id=support.owner, support_context=context)
    assert not forged["success"] and "confirmation_key" not in forged
    unknown = await execute_node_admin_tool("node_support_command", {"resource_type": "proposals", "action": "create", "values": {"title": "Draft", "proposer_member_id": "private-authority-marker"}},
        factory=support.factory, caller_user_id=support.owner, support_context=context)
    assert not unknown["success"] and "title" in unknown["writable_fields"] and "proposer_member_id" not in unknown["writable_fields"]
    assert "private-authority-marker" not in json.dumps(unknown)
