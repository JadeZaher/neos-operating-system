"""Node support schema never promotes legacy profiles on SQLite or disposable PostgreSQL."""
from __future__ import annotations

import importlib.util
import uuid
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

from neos_agent.db.models import AdviceLog, AppSetting, Ecosystem, Member, NodeAdmin, NodeAdminAction, Proposal, User
from .test_platform_admin_migration import BACKENDS, _engine


def migration():
    path = Path(__file__).resolve().parents[1] / "alembic/versions/w3c7f1a9d5e2_node_admin_support.py"
    spec = importlib.util.spec_from_file_location("node_support_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def run(engine, step="upgrade"):
    def invoke(connection):
        with Operations.context(MigrationContext.configure(connection)):
            getattr(migration(), step)()
    async with engine.begin() as connection:
        await connection.run_sync(invoke)


@pytest.mark.parametrize("backend", BACKENDS)
async def test_migration_never_grants_node_authority_from_legacy_profiles(backend, monkeypatch):
    monkeypatch.delenv("PLATFORM_HOME_ECOSYSTEM_ID", raising=False)
    async with _engine(backend) as engine:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        home, other = uuid.uuid4(), uuid.uuid4()
        identifiers = {name: uuid.uuid4() for name in ("creator", "builder", "pending", "foreign", "plain")}
        async with factory() as session:
            session.add_all([Ecosystem(id=home, name="Pinned home"), Ecosystem(id=other, name="Other")])
            session.add(AppSetting(key="platform_home_ecosystem_id", value={"ecosystem_id": str(home)}))
            for name, identifier in identifiers.items():
                session.add(User(id=identifier, display_name=name))
            await session.flush()
            for name, identifier in identifiers.items():
                session.add(Member(user_id=identifier, ecosystem_id=other if name == "foreign" else home, member_id=name,
                    display_name=name, current_status="pending_consent" if name == "pending" else "active",
                    profile="builder" if name == "builder" else "townhall" if name == "plain" else "co_creator"))
            await session.commit()
        await run(engine)
        async with factory() as session:
            assert not (await session.scalars(select(NodeAdmin.user_id))).all()
            assert not (await session.scalars(select(NodeAdminAction))).all()
            assert await session.scalar(select(AppSetting.id).where(AppSetting.key == "node_admin_bootstrap_complete")) is None
            plain = await session.scalar(select(Member).where(Member.user_id == identifiers["plain"]))
            plain.profile = "co_creator"
            await session.commit()
        await run(engine)
        async with factory() as session:
            assert not (await session.scalars(select(NodeAdmin.user_id))).all()
            assert not (await session.scalars(select(NodeAdminAction))).all()


@pytest.mark.parametrize("backend", BACKENDS)
async def test_preexisting_schema_gets_columns_and_private_archive_triggers(backend, monkeypatch):
    monkeypatch.delenv("PLATFORM_HOME_ECOSYSTEM_ID", raising=False)
    async with _engine(backend) as engine:
        async with engine.begin() as connection:
            await connection.execute(text("DROP TABLE node_admin_snapshots"))
            await connection.execute(text("DROP TABLE node_admin_actions"))
            await connection.execute(text("DROP TABLE node_admins"))
            await connection.execute(text("ALTER TABLE proposals DROP COLUMN support_created_by_user_id"))
            await connection.execute(text("ALTER TABLE proposals DROP COLUMN support_action_id"))
            await connection.execute(text("ALTER TABLE users DROP COLUMN disabled_at"))
        await run(engine)
        async with engine.begin() as connection:
            await connection.execute(text("INSERT INTO node_admin_snapshots (id,action_id,resource_type,resource_id,operation,snapshot) VALUES (:id,:action,'advice_entries',:resource,'archive_evidence',:snapshot)"),
                {"id": str(uuid.uuid4()) if backend == "postgresql" else uuid.uuid4().hex, "action": str(uuid.uuid4()) if backend == "postgresql" else uuid.uuid4().hex,
                 "resource": str(uuid.uuid4()), "snapshot": '{}'})
        async with engine.connect() as connection:
            with pytest.raises(DBAPIError, match="append-only"):
                await connection.execute(text("DELETE FROM node_admin_snapshots"))
            await connection.rollback()


@pytest.mark.parametrize("backend", BACKENDS)
async def test_support_parent_record_search_handles_native_uuid_columns(backend):
    from neos_agent.api.schemas.node_admin import SupportCommandRequest
    from neos_agent.services.node_admin import inspect_resource, list_resources, execute_command
    async with _engine(backend) as engine:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        operator_id, organization_id, proposal_id, log_id = [uuid.uuid4() for _ in range(4)]
        async with factory() as session:
            session.add(User(id=operator_id, display_name="Support operator", did="did:key:lookup-fixture"))
            session.add(Ecosystem(id=organization_id, name="Lookup organization"))
            await session.flush()
            session.add(NodeAdmin(user_id=operator_id, active=True))
            session.add(Proposal(id=proposal_id, ecosystem_id=organization_id, proposal_id="PROP-lookup", type="policy", title="Lookup proposal"))
            await session.flush()
            session.add(AdviceLog(id=log_id, proposal_id=proposal_id))
            await session.commit()
        # AdviceLog.proposal_id is a native UUID on PostgreSQL, not a text business key.
        result = await list_resources(factory, operator_id, "advice_logs", organization_id=organization_id, search=str(proposal_id))
        assert [row["id"] for row in result["items"]] == [str(log_id)]
        missing = await list_resources(factory, operator_id, "advice_logs", organization_id=organization_id, search="not-a-matching-proposal")
        assert missing["items"] == []
        inspected = await inspect_resource(factory, operator_id, "proposals", proposal_id, "Data correction")
        corrected = await execute_command(factory, operator_id, SupportCommandRequest(resource_type="proposals", resource_id=proposal_id, action="update",
            organization_id=organization_id, reason="Data correction", expected_version=inspected["resource"]["version"], values={"status": "advice", "proposed_change": "Private correction marker"}))
        assert corrected["resource"]["status"] == "advice" and corrected["resource"]["updated_at"]
