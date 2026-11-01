"""Shared world for the G-Exchange tests (no tests here): three ecosystems, their people and domains, and a Sanic app
mounting the real exchange-related blueprints over in-memory SQLite (or a disposable PostgreSQL schema).

People sign in with the `x-test-as` header; no header is a signed-out visitor. Contracts: services/AGENTS.md and
api/AGENTS.md "Exchange (G-Exchange)", uxqa/governance/wave-c.md (owner decisions 2026-11-01).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.api.discover import discover_api_bp
from neos_agent.api.domains import domains_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.exit import exit_api_bp
from neos_agent.api.messaging import messaging_api_bp
from neos_agent.api.next_steps import next_steps_api_bp
from neos_agent.api.profiles import profiles_api_bp
from neos_agent.auth.ecosystem_scope import EcosystemScope
from neos_agent.db.models import Base, CircleMembership, Domain, Ecosystem, Member, User

OASIS = uuid.UUID("0000e0c0-0000-0000-0000-000000000001")
RIVER = uuid.UUID("0000e0c0-0000-0000-0000-000000000002")
FRESH = uuid.UUID("0000e0c0-0000-0000-0000-000000000003")
NAMES = {OASIS: "Oasis", RIVER: "River House", FRESH: "Fresh Start"}
KITCHEN = uuid.UUID("0000e0c0-0000-0000-0000-0000000000d1")  # Oasis
GARDEN = uuid.UUID("0000e0c0-0000-0000-0000-0000000000d2")  # Oasis
DOCK = uuid.UUID("0000e0c0-0000-0000-0000-0000000000d3")  # River House


@dataclass(frozen=True)
class Row:
    ecosystem: uuid.UUID
    role: str = "user"
    status: str = "active"
    profile: str | None = "townhall"


@dataclass(frozen=True)
class Person:
    key: str
    name: str
    rows: tuple[Row, ...]
    selected: uuid.UUID | None = None  # the header selection (default: the first row's ecosystem)

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"exchange.{self.key}.user")

    def member_id(self, ecosystem: uuid.UUID | None = None) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"exchange.{self.key}.{ecosystem or self.rows[0].ecosystem}")


PEOPLE = {p.key: p for p in (
    Person("ana", "Ana", (Row(OASIS),)),  # writes posts; takes part in the kitchen
    Person("mel", "Mel", (Row(OASIS),)),  # plain member of the poster's ecosystem
    Person("dee", "Dee", (Row(OASIS),)),  # takes part in the kitchen (domain participant)
    Person("sam", "Sam", (Row(OASIS, role="mod"),)),  # ecosystem steward (moderator)
    Person("tia", "Tia", (Row(OASIS, role="mod"),)),  # a second Oasis steward
    Person("pip", "Pip", (Row(OASIS, status="pending_consent"),)),  # pending newcomer
    Person("xen", "Xen", (Row(OASIS, status="exited"),)),  # exited member
    Person("olu", "Olu", (Row(RIVER),)),  # member of another ecosystem
    Person("rex", "Rex", (Row(RIVER, role="mod"),)),  # steward of ANOTHER ecosystem
    # The D1 exploit: founded Fresh Start (co_creator on that row) and is a plain member of Oasis.
    Person("fay", "Fay", (Row(OASIS), Row(FRESH, profile="co_creator")), selected=FRESH),
    Person("duo", "Duo", (Row(OASIS, role="mod"), Row(RIVER, role="mod"))),  # steward on both sides
)}
ACTORS = ("anon", *PEOPLE)


def member_id(key: str, ecosystem: uuid.UUID | None = None) -> uuid.UUID:
    return PEOPLE[key].member_id(ecosystem)


async def seed(session: AsyncSession) -> None:
    session.add_all([Ecosystem(id=eco, name=name, status="active", visibility="public") for eco, name in NAMES.items()])
    for p in PEOPLE.values():
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for p in PEOPLE.values():
        for row in p.rows:
            session.add(Member(id=p.member_id(row.ecosystem), ecosystem_id=row.ecosystem, user_id=p.user_id,
                               member_id=f"MEM-{p.key.upper()}-{NAMES[row.ecosystem][:3].upper()}",
                               display_name=p.name, current_status=row.status, role=row.role, profile=row.profile))
    session.add_all([
        Domain(id=KITCHEN, ecosystem_id=OASIS, domain_id="DOM-KITCHEN", name="Community Kitchen", status="active"),
        Domain(id=GARDEN, ecosystem_id=OASIS, domain_id="DOM-GARDEN", name="Garden", status="active"),
        Domain(id=DOCK, ecosystem_id=RIVER, domain_id="DOM-DOCK", name="Boat Dock", status="active"),
    ])
    await session.flush()
    session.add_all([CircleMembership(id=uuid.uuid4(), domain_id=KITCHEN, member_id=member_id(key), status="active")
                     for key in ("ana", "dee")])
    await session.commit()


def create_app(factory) -> Sanic:
    app = Sanic(f"test-exchange-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def sign_in(request):
        key = request.headers.get("x-test-as")
        if not key:
            return  # signed out: request.ctx.member stays unset, so every route answers 401
        p = PEOPLE[key]
        active = [row.ecosystem for row in p.rows if row.status == "active"]
        selected = [p.selected or p.rows[0].ecosystem]
        default = next((row for row in p.rows if row.ecosystem in selected), p.rows[0])
        request.ctx.member = Member(id=p.member_id(default.ecosystem), ecosystem_id=default.ecosystem, user_id=p.user_id,
                                    member_id="MEM-AUTH", display_name=p.name, current_status=default.status,
                                    role=default.role, profile=default.profile)
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = [eco for eco in selected if eco in active]
        request.ctx.authorized_ecosystem_ids = active
        request.ctx.platform_admin = False
        request.ctx.ecosystem_scope = EcosystemScope.from_ecosystems(
            [SimpleNamespace(id=eco, name=NAMES[eco]) for eco in active], request.ctx.selected_ecosystem_ids)

    for blueprint in (discover_api_bp, domains_api_bp, ecosystems_api_bp, profiles_api_bp, messaging_api_bp,
                      next_steps_api_bp, exit_api_bp):
        app.blueprint(blueprint)
    return app


async def build_world(url: str = "sqlite+aiosqlite://", **engine_args):
    """A fresh schema, seeded; returns (engine, env) with env.app and env.db."""
    engine = create_async_engine(url, echo=False, **engine_args)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await seed(session)
    return engine, SimpleNamespace(app=create_app(factory), db=factory)


async def call(env, method: str, who: str, url: str, expect: int | None = None, **kwargs):
    """One request as `who` ("anon" = signed out); `expect` asserts the status with the body in the message."""
    headers = {} if who == "anon" else {"x-test-as": who}
    _, resp = await getattr(env.app.asgi_client, method)(url, headers=headers, **kwargs)
    if expect is not None:
        assert resp.status == expect, (method, url, who, resp.status, resp.text)
    return resp


POSTS = "/api/v1/discover/shares-needs"
COLLABS = "/api/v1/discover/collaborations"


async def post_as(env, who: str, *, title: str = "Soup pots", type_: str = "need", domain=KITCHEN,
                  ecosystem=OASIS, visibility: str = "public", **extra) -> dict:
    body = {"ecosystem_id": str(ecosystem), "domain_id": str(domain), "type": type_, "title": title,
            "visibility": visibility, **extra}
    return (await call(env, "post", who, POSTS, expect=201, json=body)).json
