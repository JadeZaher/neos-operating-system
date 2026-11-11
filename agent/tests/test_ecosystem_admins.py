"""Cross-link admins: default founder, backfill, grant/revoke, and the public contact.

The stored founder is not Member.role == 'owner'. Seed data and POST /ecosystems
leave role at 'user' and set profile to 'co_creator'. The root domain's steward_id
is that same person. A later role='owner' grant outranks the co_creator.
"""

from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401
from neos_agent.agent.governance_tools import create_ecosystem
from neos_agent.api.communities import communities_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.messaging import messaging_api_bp
from neos_agent.db.models import (
    Base, Domain, Ecosystem, EcosystemAdmin, Member, MemberStatusTransition, User,
)
from neos_agent.services.ecosystem_admins import AdminCandidate, StewardDomain, choose_default_admin
from .test_platform_admin_migration import BACKENDS, _engine

MIGRATION_PATH = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "b8d3f1a6c4e2_ecosystem_cross_link_admins.py"
FOUNDED = datetime(2020, 1, 1)
LATER = datetime(2024, 6, 1)


def _migration():
    spec = importlib.util.spec_from_file_location("ecosystem_admin_migration", MIGRATION_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate(key, *, role="user", profile=None, status="active", disabled=False, created_at=FOUNDED):
    return AdminCandidate(uuid.uuid5(uuid.NAMESPACE_DNS, key), created_at, role, profile, status, disabled)


def test_default_admin_follows_owner_then_creator_then_lead_steward():
    founder = _candidate("josh", profile="co_creator")
    circle = _candidate("nathan", profile="builder", created_at=LATER)
    owner = _candidate("ada", role="owner", created_at=LATER)
    root = StewardDomain(uuid.uuid4(), circle.id, None, "active", FOUNDED)
    child = StewardDomain(uuid.uuid4(), founder.id, root.id, "active", datetime(2019, 1, 1))
    assert choose_default_admin([founder, circle, owner], [root, child]) == owner.id
    assert choose_default_admin([founder, circle], [root, child]) == founder.id
    assert choose_default_admin([circle], [child, root]) == circle.id
    departed = _candidate("gone", profile="co_creator", status="exited")
    disabled = _candidate("closed", profile="co_creator", disabled=True, created_at=datetime(2018, 1, 1))
    assert choose_default_admin([departed, disabled, circle], [root]) == circle.id
    assert choose_default_admin([_candidate("plain", profile="collaborator")], []) is None


async def _run(engine, step="upgrade"):
    def invoke(connection):
        with Operations.context(MigrationContext.configure(connection)):
            getattr(_migration(), step)()
    async with engine.begin() as connection:
        await connection.run_sync(invoke)


async def _links(factory, ecosystem_id):
    async with factory() as session:
        rows = (await session.scalars(select(EcosystemAdmin).where(EcosystemAdmin.ecosystem_id == ecosystem_id))).all()
        return {(row.member_id, row.designation) for row in rows}


@pytest.mark.parametrize("backend", BACKENDS)
async def test_backfill_assigns_the_stored_founder_and_is_idempotent(backend):
    async with _engine(backend) as engine:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        seeded, granted, stewarded, plain, empty = (uuid.uuid4() for _ in range(5))
        josh, later, nathan = (uuid.uuid4() for _ in range(3))
        ada, founder_b = uuid.uuid4(), uuid.uuid4()
        lead, nested = uuid.uuid4(), uuid.uuid4()
        someone = uuid.uuid4()
        async with factory() as session:
            for eco_id, name in (
                (seeded, "Seeded OmniOne"), (granted, "Granted"), (stewarded, "Stewarded"),
                (plain, "Plain"), (empty, "Empty"),
            ):
                session.add(Ecosystem(id=eco_id, name=name, status="active", visibility="public"))
            for user_id, name, disabled in (
                (josh, "Josh Pasmore", None), (later, "Later Creator", None), (nathan, "Nathan", None),
                (ada, "Ada", None), (founder_b, "Old Founder", None), (lead, "Lead", None),
                (nested, "Nested", None), (someone, "Someone", None),
            ):
                session.add(User(id=user_id, display_name=name, disabled_at=disabled))
            await session.flush()
            session.add_all([
                Member(id=josh, ecosystem_id=seeded, user_id=josh, member_id="MBR-OMNI-001", display_name="Josh Pasmore",
                       current_status="active", role="user", profile="co_creator", created_at=FOUNDED),
                Member(id=later, ecosystem_id=seeded, user_id=later, member_id="MBR-LATER", display_name="Later Creator",
                       current_status="active", role="user", profile="co_creator", created_at=LATER),
                Member(id=nathan, ecosystem_id=seeded, user_id=nathan, member_id="MBR-OMNI-002", display_name="Nathan",
                       current_status="active", role="user", profile="builder", created_at=datetime(2021, 1, 1)),
                Member(id=ada, ecosystem_id=granted, user_id=ada, member_id="MBR-ADA", display_name="Ada",
                       current_status="active", role="owner", profile=None, created_at=LATER),
                Member(id=founder_b, ecosystem_id=granted, user_id=founder_b, member_id="MBR-OLD", display_name="Old Founder",
                       current_status="active", role="user", profile="co_creator", created_at=FOUNDED),
                Member(id=lead, ecosystem_id=stewarded, user_id=lead, member_id="MBR-LEAD", display_name="Lead",
                       current_status="active", role="user", profile="collaborator", created_at=LATER),
                Member(id=nested, ecosystem_id=stewarded, user_id=nested, member_id="MBR-NEST", display_name="Nested",
                       current_status="active", role="user", profile="builder", created_at=FOUNDED),
                Member(id=someone, ecosystem_id=plain, user_id=someone, member_id="MBR-PLAIN", display_name="Someone",
                       current_status="active", role="user", profile="collaborator", created_at=FOUNDED),
            ])
            await session.flush()
            root = uuid.uuid4()
            session.add(Domain(id=root, ecosystem_id=seeded, domain_id="dom-omni-ops-001", version="1.0", status="active",
                               steward_id=josh, parent_domain_id=None, created_by="Josh Pasmore", created_at=FOUNDED))
            session.add(Domain(id=uuid.uuid4(), ecosystem_id=seeded, domain_id="dom-omni-regen-001", version="1.0",
                               status="active", steward_id=nathan, parent_domain_id=root, created_at=datetime(2019, 1, 1)))
            root_steward = uuid.uuid4()
            session.add(Domain(id=root_steward, ecosystem_id=stewarded, domain_id="DOM-ROOT", version="1.0", status="active",
                               steward_id=lead, parent_domain_id=None, created_at=datetime(2022, 1, 1)))
            session.add(Domain(id=uuid.uuid4(), ecosystem_id=stewarded, domain_id="DOM-CHILD", version="1.0", status="active",
                               steward_id=nested, parent_domain_id=root_steward, created_at=datetime(2019, 1, 1)))
            await session.commit()
        await _run(engine)
        assert await _links(factory, seeded) == {(josh, "internal"), (josh, "external")}
        assert await _links(factory, granted) == {(ada, "internal"), (ada, "external")}
        assert await _links(factory, stewarded) == {(lead, "internal"), (lead, "external")}
        assert await _links(factory, plain) == set()
        assert await _links(factory, empty) == set()
        async with factory() as session:
            audits = (await session.scalars(select(MemberStatusTransition).where(
                MemberStatusTransition.trigger == "ecosystem_admin"))).all()
            assert len(audits) == 6
            assert {row.role for row in (await session.scalars(select(Member))).all()} >= {"user", "owner"}
        await _run(engine)
        assert await _links(factory, seeded) == {(josh, "internal"), (josh, "external")}
        async with factory() as session:
            assert await session.scalar(select(func.count(MemberStatusTransition.id)).where(
                MemberStatusTransition.trigger == "ecosystem_admin")) == 6
        await _run(engine, "downgrade")
        await _run(engine)
        assert await _links(factory, seeded) == {(josh, "internal"), (josh, "external")}


# --- role controls and the public contact ---

ECO = uuid.uuid4()
FOUNDER = uuid.uuid4()
PEER = uuid.uuid4()
OUTSIDER = uuid.uuid4()
OWNER = uuid.uuid4()
PENDING = uuid.uuid4()
PEOPLE = {
    "founder": (FOUNDER, "user", "active", "co_creator"),
    "peer": (PEER, "user", "active", None),
    "outsider": (OUTSIDER, "user", "active", None),
    "owner": (OWNER, "owner", "active", None),
    "pending": (PENDING, "user", "pending_consent", None),
}


async def _seed_api(session: AsyncSession) -> None:
    session.add(Ecosystem(id=ECO, name="Harbor Admins", status="active", visibility="public",
                          contact_email="secret-admin@example.test"))
    for key, (member_id, role, status, profile) in PEOPLE.items():
        session.add(User(id=member_id, display_name=key, did=f"did:neos:secret-{key}"))
    await session.flush()
    for key, (member_id, role, status, profile) in PEOPLE.items():
        session.add(Member(
            id=member_id, ecosystem_id=ECO, user_id=member_id, member_id=f"MEM-{key}",
            display_name=key, current_status=status, role=role, profile=profile,
        ))
    await session.flush()
    for designation in ("internal", "external"):
        session.add(EcosystemAdmin(
            ecosystem_id=ECO, member_id=FOUNDER, designation=designation, appointed_by_member_id=FOUNDER,
        ))
    await session.commit()


def _app() -> Sanic:
    app = Sanic(f"test-ecosystem-admins-{uuid.uuid4().hex[:8]}")
    register_api_errors(app)

    @app.on_request
    async def inject(request):
        key = request.headers.get("x-test-as")
        if not key:
            return
        member_id, role, status, profile = PEOPLE[key]
        request.ctx.user = User(id=member_id, display_name=key)
        request.ctx.member = Member(
            id=member_id, ecosystem_id=ECO, user_id=member_id, member_id="MEM-AUTH",
            display_name=key, current_status=status, role=role, profile=profile,
        )
        request.ctx.selected_ecosystem_ids = [ECO] if status == "active" else []
        request.ctx.authorized_ecosystem_ids = [ECO] if status == "active" else []

    for blueprint in (ecosystems_api_bp, communities_api_bp, messaging_api_bp):
        app.blueprint(blueprint)
    return app


@pytest_asyncio.fixture
async def api():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed_api(session)
    application = _app()
    application.ctx.db = factory
    yield application
    await engine.dispose()


async def _call(app, method, who, url, **kwargs):
    headers = {"x-test-as": who} if who else {}
    _, response = await getattr(app.asgi_client, method)(url, headers=headers, **kwargs)
    return response


async def test_creating_an_ecosystem_assigns_both_links_to_the_founder(api):
    created = await _call(api, "post", "founder", "/api/v1/ecosystems", json={"name": "Fresh Circle"})
    if created.status == 404:
        created = await _call(api, "post", "founder", "/api/v1/ecosystems/", json={"name": "Fresh Circle"})
    assert created.status == 201, created.text
    assert created.json["owner"]["display_name"] == "founder"
    assert created.json["owner"]["role"] == "external"
    assert set(created.json["owner"]) == {"id", "display_name", "role"}
    eco_id = uuid.UUID(created.json["id"])
    async with api.ctx.db() as session:
        links = await _links_of(session, eco_id)
        assert links == {(uuid.UUID(created.json["owner"]["id"]), "internal"), (uuid.UUID(created.json["owner"]["id"]), "external")}
        user = await session.get(User, FOUNDER)
        again = await create_ecosystem({"name": "Chat Circle"}, session, caller_user_id=user.id)
        await session.commit()
        assert again["success"] is True
        chat_links = await _links_of(session, uuid.UUID(again["data"]["id"]))
    assert len(chat_links) == 2 and {item[1] for item in chat_links} == {"internal", "external"}


async def _links_of(session, ecosystem_id):
    rows = (await session.scalars(select(EcosystemAdmin).where(EcosystemAdmin.ecosystem_id == ecosystem_id))).all()
    return {(row.member_id, row.designation) for row in rows}


async def test_non_admins_cannot_grant_and_the_last_admin_cannot_be_removed(api):
    body = {"member_id": str(PEER), "designation": "external"}
    refused = await _call(api, "post", "outsider", f"/api/v1/ecosystems/{ECO}/admins", json=body)
    assert refused.status == 403 and refused.json["code"] == "ADMIN_REQUIRED"
    assert (await _call(api, "post", "pending", f"/api/v1/ecosystems/{ECO}/admins", json=body)).status == 403
    assert (await _call(api, "post", None, f"/api/v1/ecosystems/{ECO}/admins", json=body)).status == 401
    async with api.ctx.db() as session:
        assert len(await _links_of(session, ECO)) == 2

    granted = await _call(api, "post", "founder", f"/api/v1/ecosystems/{ECO}/admins", json=body)
    assert granted.status == 201
    again = await _call(api, "post", "owner", f"/api/v1/ecosystems/{ECO}/admins", json=body)
    assert again.status == 200 and again.json["status"] == "exists"
    moved = await _call(api, "put", "founder", f"/api/v1/ecosystems/{ECO}/admins/{PEER}", json={"designation": "internal"})
    assert moved.status == 200
    # Founder still holds both, so dropping one link is allowed.
    dropped = await _call(api, "delete", "founder", f"/api/v1/ecosystems/{ECO}/admins/{FOUNDER}?designation=internal")
    assert dropped.status == 200
    dropped = await _call(api, "delete", "owner", f"/api/v1/ecosystems/{ECO}/admins/{FOUNDER}?designation=external")
    assert dropped.status == 200
    # Peer is the only remaining admin. Removing that link is refused.
    last = await _call(api, "delete", "peer", f"/api/v1/ecosystems/{ECO}/admins/{PEER}?designation=internal")
    assert last.status == 409 and last.json["code"] == "LAST_ADMIN"
    async with api.ctx.db() as session:
        assert await _links_of(session, ECO) == {(PEER, "internal")}
        assert await session.scalar(select(func.count(MemberStatusTransition.id)).where(
            MemberStatusTransition.trigger == "ecosystem_admin", MemberStatusTransition.actor_member_id.is_not(None),
        )) >= 1


async def test_public_contact_is_the_external_rep_and_is_the_only_person_a_pending_account_can_message(api):
    community = await _call(api, "get", None, f"/api/v1/communities/{ECO}")
    assert community.status == 200
    assert community.json["owner"] == {"id": str(FOUNDER), "display_name": "founder", "role": "external"}
    assert set(community.json["owner"]) == {"id", "display_name", "role"}
    for secret in ("peer", "outsider", "pending", "secret-admin@example.test", "did:neos:"):
        assert secret not in community.text

    opened = await _call(api, "post", "pending", "/api/v1/messaging/conversations",
                         json={"type": "dm", "participant_ids": [str(FOUNDER)]})
    assert opened.status == 201
    refused = await _call(api, "post", "pending", "/api/v1/messaging/conversations",
                          json={"type": "dm", "participant_ids": [str(PEER)]})
    assert refused.status == 403

    await _call(api, "post", "founder", f"/api/v1/ecosystems/{ECO}/admins",
                json={"member_id": str(PEER), "designation": "internal"})
    await _call(api, "put", "founder", f"/api/v1/ecosystems/{ECO}/admins/{PEER}", json={"designation": "external"})
    await _call(api, "delete", "founder", f"/api/v1/ecosystems/{ECO}/admins/{FOUNDER}?designation=external")
    await _call(api, "delete", "founder", f"/api/v1/ecosystems/{ECO}/admins/{FOUNDER}?designation=internal")
    community = await _call(api, "get", None, f"/api/v1/communities/{ECO}")
    assert community.json["owner"] == {"id": str(PEER), "display_name": "peer", "role": "external"}
    assert "founder" not in community.text
    opened = await _call(api, "post", "pending", "/api/v1/messaging/conversations",
                         json={"type": "dm", "participant_ids": [str(PEER)]})
    assert opened.status == 201
    refused = await _call(api, "post", "pending", "/api/v1/messaging/conversations",
                          json={"type": "dm", "participant_ids": [str(FOUNDER)]})
    assert refused.status == 403


async def test_an_external_admin_cannot_grant_or_revoke(api):
    dropped = await _call(api, "delete", "owner", f"/api/v1/ecosystems/{ECO}/admins/{FOUNDER}?designation=internal")
    assert dropped.status == 200
    grant = await _call(api, "post", "founder", f"/api/v1/ecosystems/{ECO}/admins",
                        json={"member_id": str(PEER), "designation": "internal"})
    revoke = await _call(api, "delete", "founder", f"/api/v1/ecosystems/{ECO}/admins/{FOUNDER}?designation=external")
    assert grant.status == 403 and grant.json["code"] == "ADMIN_REQUIRED"
    assert revoke.status == 403 and revoke.json["code"] == "ADMIN_REQUIRED"
    async with api.ctx.db() as session:
        assert await _links_of(session, ECO) == {(FOUNDER, "external")}
