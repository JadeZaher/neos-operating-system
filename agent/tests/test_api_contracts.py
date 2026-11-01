"""Wave-0 handler contracts driven through HTTP: guards, errors, pagination, scoping, policy.

Rules: src/neos_agent/api/AGENTS.md "Handler contracts". The probe blueprint is
written exactly as a migrated handler should read, so it doubles as the example.
The request.ctx.member rule and ApiError registration run through the real
create_app over a file-backed SQLite database.
"""

from __future__ import annotations

import json as jsonlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.parse import quote

import pytest
import pytest_asyncio
from sanic import Blueprint, Sanic, json
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.api.errors import ApiError, get_scoped_or_404, register_api_errors
from neos_agent.api.guards import authenticated, caller_in, reachable_ecosystem_ids
from neos_agent.api.helpers import get_ecosystem_ids, parse_pagination
from neos_agent.api.policy import (
    assignable_roles,
    can_assign_role,
    can_conduct_agreement_ceremony,
    can_edit_domain,
    can_manage_proposal,
    is_steward,
    is_steward_in,
)
from neos_agent.auth.ecosystem_scope import EcosystemScope, restrict_to_ecosystems
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import Agreement, AuthSession, Base, Domain, Ecosystem, Member, Proposal, User

OASIS = uuid.UUID(int=1)
OMNIONE = uuid.UUID(int=2)
THIRD_SPACE = uuid.UUID(int=3)
RIVER_HOUSE = uuid.UUID(int=4)


@dataclass(frozen=True)
class Person:
    user_id: uuid.UUID
    rows: dict[uuid.UUID, tuple[str, str]]  # ecosystem -> (role, status)
    session_ecosystem: uuid.UUID  # where the injected request.ctx.member row lives


def _member_id(user_id: uuid.UUID, ecosystem_id: uuid.UUID) -> uuid.UUID:
    return uuid.uuid5(user_id, str(ecosystem_id))


PEOPLE = {
    "ada": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "contracts.ada"), {OASIS: ("user", "active")}, OASIS),
    "bo": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "contracts.bo"), {OMNIONE: ("user", "active")}, OMNIONE),
    # Steward in Oasis, plain member in OmniOne; the session's default row is the OmniOne one.
    "sam": Person(
        uuid.uuid5(uuid.NAMESPACE_DNS, "contracts.sam"),
        {OASIS: ("mod", "active"), OMNIONE: ("user", "active")},
        OMNIONE,
    ),
    # Only membership still waits on the consent gate, so no ecosystem is authorized.
    "nia": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "contracts.nia"), {OASIS: ("user", "pending_consent")}, OASIS),
    # Active in OmniOne, still behind Oasis's consent gate.
    "kai": Person(
        uuid.uuid5(uuid.NAMESPACE_DNS, "contracts.kai"),
        {OMNIONE: ("user", "active"), OASIS: ("user", "pending_consent")},
        OMNIONE,
    ),
}

PROPOSAL_IDS = {key: uuid.uuid5(uuid.NAMESPACE_DNS, f"contracts.{key}") for key in ("A1", "A2", "A3", "B1", "B2")}


async def _seed_people_and_proposals(session: AsyncSession) -> None:
    session.add_all([
        Ecosystem(id=OASIS, name="Oasis", status="active"),
        Ecosystem(id=OMNIONE, name="OmniOne", status="active"),
    ])
    for key, person in PEOPLE.items():
        session.add(User(id=person.user_id, display_name=key.title()))
    await session.flush()
    for key, person in PEOPLE.items():
        for ecosystem_id, (role, status) in person.rows.items():
            session.add(Member(
                id=_member_id(person.user_id, ecosystem_id), ecosystem_id=ecosystem_id,
                user_id=person.user_id, member_id=f"MEM-{key}-{ecosystem_id.int}",
                display_name=key.title(), role=role, current_status=status,
            ))
    ada_in_oasis = _member_id(PEOPLE["ada"].user_id, OASIS)
    for key, ecosystem_id, shared_with in (
        ("A1", OASIS, None), ("A2", OASIS, None), ("A3", OASIS, None),
        ("B1", OMNIONE, None), ("B2", OMNIONE, [str(OASIS)]),
    ):
        session.add(Proposal(
            id=PROPOSAL_IDS[key], ecosystem_id=ecosystem_id, proposal_id=f"PROP-{key}",
            type="policy", title=f"Proposal {key}", version="1.0", status="draft",
            proposer="Ada", proposer_member_id=ada_in_oasis if ecosystem_id == OASIS else None,
            shared_ecosystem_ids=shared_with,
        ))
    await session.commit()


# --- Probe blueprint: how a migrated handler reads -------------------------

probe_bp = Blueprint("contract_probe", url_prefix="/api/v1/probe")


@probe_bp.get("/proposals")
@authenticated
async def list_probe_proposals(request):
    page = parse_pagination(request)
    async with request.app.ctx.db() as session:
        statement = select(Proposal).order_by(Proposal.proposal_id)
        statement = restrict_to_ecosystems(statement, Proposal, get_ecosystem_ids(request))
        rows = (await session.execute(statement.offset(page.offset).limit(page.per_page))).scalars().all()
    return json({"page": page.page, "per_page": page.per_page, "items": [p.proposal_id for p in rows]})


@probe_bp.get("/proposals/<proposal_id:uuid>")
@authenticated
async def get_probe_proposal(request, proposal_id: uuid.UUID):
    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal")
        caller = await caller_in(session, request, proposal.ecosystem_id)
    return json({"proposal_id": proposal.proposal_id, "caller_can_manage": can_manage_proposal(caller, proposal)})


@probe_bp.get("/consent-gate/proposals/<proposal_id:uuid>")
@authenticated
async def get_probe_proposal_behind_the_gate(request, proposal_id: uuid.UUID):
    """Scoped like agreement detail, history and consent: pending memberships count."""
    async with request.app.ctx.db() as session:
        scope = await reachable_ecosystem_ids(session, request, include_pending=True)
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal", ecosystem_ids=scope)
    return json({"proposal_id": proposal.proposal_id})


@probe_bp.get("/owner-only/proposals/<proposal_id:uuid>")
@authenticated
async def get_probe_proposal_owner_only(request, proposal_id: uuid.UUID):
    """Scoped like an entity whose list matches owning ecosystems only."""
    async with request.app.ctx.db() as session:
        proposal = await get_scoped_or_404(session, request, Proposal, proposal_id, label="Proposal", include_shared=False)
    return json({"proposal_id": proposal.proposal_id})


def _probe_app(session_factory) -> Sanic:
    """Blueprint app; the x-test-as header picks who is signed in."""
    app = Sanic(f"test-contracts-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = session_factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        person = PEOPLE[who]
        role, status = person.rows[person.session_ecosystem]
        request.ctx.user = User(id=person.user_id, display_name=who.title())
        request.ctx.member = Member(
            id=_member_id(person.user_id, person.session_ecosystem), ecosystem_id=person.session_ecosystem,
            user_id=person.user_id, member_id="MEM-SESSION", display_name=who.title(),
            role=role, current_status=status,
        )
        authorized = [eco for eco, (_, row_status) in person.rows.items() if row_status == "active"]
        request.ctx.authorized_ecosystem_ids = authorized
        request.ctx.selected_ecosystem_ids = [eco for eco in authorized if eco == person.session_ecosystem]

    app.blueprint(probe_bp)
    return app


@pytest_asyncio.fixture
async def probe():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed_people_and_proposals(session)
    yield SimpleNamespace(app=_probe_app(factory), db=factory)
    await engine.dispose()


async def _get(app: Sanic, url: str, who: str | None = None):
    headers = {"x-test-as": who} if who else {}
    _, response = await app.asgi_client.get(url, headers=headers)
    return response


# --- @authenticated ---------------------------------------------------------


async def test_guarded_routes_refuse_anonymous_callers_with_the_require_auth_shape(probe):
    for url in ("/api/v1/probe/proposals", f"/api/v1/probe/proposals/{PROPOSAL_IDS['A1']}"):
        response = await _get(probe.app, url)
        assert response.status == 401
        assert response.json == {"error": "Authentication required"}
    assert (await _get(probe.app, "/api/v1/probe/proposals", "ada")).status == 200


# --- get_scoped_or_404 + caller_in -------------------------------------------


@pytest.mark.parametrize("who, proposal, status", [
    ("ada", "A1", 200),     # own ecosystem
    ("ada", "B2", 200),     # owned by OmniOne, shared with Oasis
    ("ada", "B1", 404),     # another ecosystem's row
    ("ada", "missing", 404),  # same body as a foreign row: existence never leaks
    ("bo", "A1", 404),
    ("nia", "A1", 404),     # membership pending consent: nothing authorized, fail closed
])
async def test_rows_outside_the_callers_ecosystems_are_not_found(probe, who, proposal, status):
    proposal_id = PROPOSAL_IDS.get(proposal, uuid.uuid4())
    response = await _get(probe.app, f"/api/v1/probe/proposals/{proposal_id}", who)
    assert response.status == status, response.text
    if status == 404:
        assert response.json == {"error": "Proposal not found"}


async def test_stewardship_is_read_from_the_callers_row_in_the_resource_ecosystem(probe):
    # Sam's session row is his plain OmniOne membership; he stewards Oasis.
    sam = await _get(probe.app, f"/api/v1/probe/proposals/{PROPOSAL_IDS['A1']}", "sam")
    assert sam.json["caller_can_manage"] is True
    shared = await _get(probe.app, f"/api/v1/probe/proposals/{PROPOSAL_IDS['B2']}", "ada")
    assert shared.json["caller_can_manage"] is False  # visible through sharing, but ada holds no OmniOne row


@pytest.mark.parametrize("who, route, proposal, status", [
    ("nia", "consent-gate/proposals", "A1", 200),  # a pending newcomer reads what the gate asks them to accept
    ("kai", "consent-gate/proposals", "A1", 200),  # pending here, active elsewhere: still readable
    ("kai", "proposals", "A1", 404),               # ...while the default scope stays active-only
    ("bo", "consent-gate/proposals", "A1", 404),   # widening adds only the caller's own pending memberships
    ("ada", "owner-only/proposals", "A1", 200),
    ("ada", "owner-only/proposals", "B2", 404),    # shared with Oasis, hidden where the list matches owners only
])
async def test_scope_overrides_widen_to_pending_memberships_or_narrow_to_owned_rows(probe, who, route, proposal, status):
    response = await _get(probe.app, f"/api/v1/probe/{route}/{PROPOSAL_IDS[proposal]}", who)
    assert response.status == status, response.text
    if status == 404:
        assert response.json == {"error": "Proposal not found"}


# --- parse_pagination + restrict_to_ecosystems ------------------------------

ADA_SCOPE = ["PROP-A1", "PROP-A2", "PROP-A3", "PROP-B2"]


@pytest.mark.parametrize("who, query, page, per_page, items", [
    ("ada", "", 1, 25, ADA_SCOPE),
    ("ada", "?page=2&per_page=2", 2, 2, ["PROP-A3", "PROP-B2"]),
    ("ada", "?page=0&per_page=1000", 1, 100, ADA_SCOPE),  # numbers clamp into range
    ("ada", f"?ecosystem_ids={OMNIONE}", 1, 25, []),        # unauthorized explicit scope: nothing, not everything
    ("nia", "", 1, 25, []),                                 # no authorized ecosystem: nothing, not everything
])
async def test_listing_pages_within_the_callers_scope(probe, who, query, page, per_page, items):
    response = await _get(probe.app, f"/api/v1/probe/proposals{query}", who)
    assert response.status == 200, response.text
    assert response.json == {"page": page, "per_page": per_page, "items": items}


@pytest.mark.parametrize("query, message", [
    ("?page=abc", "Query parameter 'page' must be a whole number"),
    ("?per_page=ten", "Query parameter 'per_page' must be a whole number"),
    ("?page=2.5", "Query parameter 'page' must be a whole number"),
    (f"?page={10**30}", "Query parameter 'page' is out of range"),
])
async def test_junk_pagination_is_a_400_not_a_500(probe, query, message):
    response = await _get(probe.app, f"/api/v1/probe/proposals{query}", "ada")
    assert response.status == 400
    assert response.json == {"error": message}


async def test_an_empty_ecosystem_scope_selects_no_rows(probe):
    async with probe.db() as session:
        nothing = (await session.execute(EcosystemScope.empty().filter(select(Proposal), Proposal))).scalars().all()
        oasis = (await session.execute(
            EcosystemScope(selected_ids=[OASIS]).filter(select(Proposal), Proposal)
        )).scalars().all()
    assert nothing == []
    assert sorted(p.proposal_id for p in oasis) == ADA_SCOPE


# --- Real app: ApiError registration and the request.ctx.member rule ---------

SESSION_SECRET = "contracts-secret-0123456789abcdef"


@pytest.fixture(scope="module")
def real_app(tmp_path_factory):
    """One create_app over a SQLite file: every request's startup reconnects to the same seed."""
    from neos_agent.config import Settings
    from neos_agent.main import create_app

    database_file = (tmp_path_factory.mktemp("contracts") / "contracts.db").as_posix()
    engine = create_engine(f"sqlite:///{database_file}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:  # seeded first, so startup never adds its default ecosystem
        session.add_all([
            Ecosystem(id=OASIS, name="Oasis", status="active"),
            Ecosystem(id=OMNIONE, name="OmniOne", status="active"),
            Ecosystem(id=THIRD_SPACE, name="Third Space", status="active"),
            Ecosystem(id=RIVER_HOUSE, name="River House", status="active"),
        ])
        session.commit()
    engine.dispose()

    database_url = f"sqlite+aiosqlite:///{database_file}"
    app = create_app(settings=Settings(
        _env_file=None, DATABASE_URL=database_url, SESSION_SECRET=SESSION_SECRET,
        NEOS_CORE_PATH=str(tmp_path_factory.mktemp("no-skills")), CORS_ORIGINS="*", LOG_LEVEL="info",
    ))
    # sanic-ext's automatic HEAD/OPTIONS routes cost ~20 s per fresh app and play no part here.
    app.config.HTTP_AUTO_HEAD = False
    app.config.HTTP_AUTO_OPTIONS = False
    app.config.CORS = False

    @app.get("/api/v1/auth/probe/conflict")
    async def probe_conflict(request):
        raise ApiError(409, "Consent gate not met", {"gates": {"consent": False}})

    @app.get("/auth/probe/missing")
    async def probe_missing_page(request):
        raise ApiError(404, "Agreement not found")

    @app.get("/api/v1/probe/default-member")
    async def probe_protected_member(request):
        return json({"ecosystem_id": str(request.ctx.member.ecosystem_id)})

    @app.get("/api/v1/auth/probe/default-member")
    async def probe_public_member(request):
        member = request.ctx.member
        return json({"ecosystem_id": str(member.ecosystem_id) if member else None})

    @app.get("/api/v1/probe/default-scope")
    async def probe_default_scope(request):
        return json({
            "member": str(request.ctx.member.ecosystem_id),
            "scope": [str(i) for i in request.ctx.selected_ecosystem_ids],
        })

    return SimpleNamespace(app=app, database_url=database_url)


@pytest_asyncio.fixture
async def real_db(real_app):
    """A session factory on the real app's database, bound to this test's event loop."""
    engine = create_async_engine(real_app.database_url)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def test_api_errors_render_as_json_with_their_status_on_the_real_app(real_app):
    _, conflict = await real_app.app.asgi_client.get("/api/v1/auth/probe/conflict")
    assert conflict.status == 409
    assert conflict.json == {"error": "Consent gate not met", "gates": {"consent": False}}

    # Unlike Sanic's NotFound, an ApiError 404 keeps its message and never redirects a page path.
    _, missing = await real_app.app.asgi_client.get("/auth/probe/missing", follow_redirects=False)
    assert missing.status == 404
    assert missing.json == {"error": "Agreement not found"}


async def _sign_in_with_memberships(factory, name: str, rows) -> str:
    """Seed a user with Member rows inserted in the given order; return a session cookie."""
    user_id, session_id = uuid.uuid4(), uuid.uuid4()
    async with factory() as session:
        session.add(User(id=user_id, display_name=name))
        await session.flush()
        for member_id, ecosystem_id, status, created_at in rows:
            session.add(Member(
                id=member_id, ecosystem_id=ecosystem_id, user_id=user_id,
                member_id=f"MEM-{member_id.hex}", display_name=name,
                current_status=status, created_at=created_at, updated_at=created_at,
            ))
            await session.flush()  # insertion order: an unordered LIMIT 1 returns the first row
        session.add(AuthSession(
            id=session_id, user_id=user_id, expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
        await session.commit()
    return make_session_cookie(str(session_id), SESSION_SECRET)


def _cookie_header(session_cookie: str, selected: list[uuid.UUID] | None) -> dict[str, str]:
    cookie = f"neos_session={session_cookie}"
    if selected is not None:
        cookie += f"; neos_selected_ecosystems={quote(jsonlib.dumps([str(i) for i in selected]))}"
    return {"cookie": cookie}


@pytest.mark.parametrize("path, selected, expected", [
    ("/api/v1/probe/default-member", None, OMNIONE),                 # no selection: oldest membership
    ("/api/v1/probe/default-member", [OASIS], OASIS),                # one selected ecosystem: its row
    ("/api/v1/probe/default-member", [OASIS, OMNIONE], OMNIONE),     # several selected: the oldest of them
    ("/api/v1/probe/default-member", [THIRD_SPACE], OMNIONE),        # selected but pending consent: the default
    ("/api/v1/auth/probe/default-member", None, OMNIONE),            # public routes follow the same rule
    ("/api/v1/auth/probe/default-member", [OASIS], OASIS),
])
async def test_a_member_of_several_ecosystems_gets_a_deterministic_default_row(real_app, real_db, path, selected, expected):
    cookie = await _sign_in_with_memberships(real_db, "Wren", [
        (uuid.uuid4(), OASIS, "active", datetime(2026, 3, 1)),
        (uuid.uuid4(), THIRD_SPACE, "pending_consent", datetime(2026, 2, 1)),
        (uuid.uuid4(), OMNIONE, "active", datetime(2026, 1, 1)),
    ])
    _, response = await real_app.app.asgi_client.get(path, headers=_cookie_header(cookie, selected))
    assert response.status == 200, response.text
    assert response.json == {"ecosystem_id": str(expected)}


@pytest.mark.parametrize("selected, member, scope", [
    (None, OMNIONE, {OMNIONE}),                              # no cookie: the oldest ACTIVE membership
    ([THIRD_SPACE], OMNIONE, {OMNIONE}),                     # only a pending ecosystem selected: the default, not empty
    ([uuid.UUID(int=99), OASIS], OASIS, {OASIS}),            # a stale id is dropped before the row is chosen
    ([RIVER_HOUSE, OASIS], OASIS, {OASIS, RIVER_HOUSE}),     # several selected: the oldest row inside the scope
])
async def test_the_default_row_always_lies_inside_the_default_scope(real_app, real_db, selected, member, scope):
    # Only created_at order finds OmniOne: the newest active row goes in first and Oasis has the lowest id, so
    # insertion order, an unordered query and next(iter(set)) all pick Oasis; the oldest row of all is pending.
    cookie = await _sign_in_with_memberships(real_db, "Ola", [
        (uuid.uuid4(), OASIS, "active", datetime(2026, 3, 1)),
        (uuid.uuid4(), THIRD_SPACE, "pending_consent", datetime(2026, 1, 1)),
        (uuid.uuid4(), OMNIONE, "active", datetime(2026, 2, 1)),
        (uuid.uuid4(), RIVER_HOUSE, "active", datetime(2026, 4, 1)),
    ])
    _, response = await real_app.app.asgi_client.get(
        "/api/v1/probe/default-scope", headers=_cookie_header(cookie, selected),
    )
    assert response.status == 200, response.text
    assert response.json["member"] == str(member)
    assert set(response.json["scope"]) == {str(ecosystem_id) for ecosystem_id in scope}


async def test_memberships_created_together_break_the_tie_by_id(real_app, real_db):
    seeded_at = datetime(2026, 10, 31, 12, 35, 13)  # seeds add_all + flush: one created_at
    cookie = await _sign_in_with_memberships(real_db, "Tia", [
        (uuid.UUID(int=0xB), OASIS, "active", seeded_at),
        (uuid.UUID(int=0xA), OMNIONE, "active", seeded_at),
    ])
    _, response = await real_app.app.asgi_client.get(
        "/api/v1/probe/default-member", headers=_cookie_header(cookie, None),
    )
    assert response.json == {"ecosystem_id": str(OMNIONE)}


# --- policy.py: actor x action ---------------------------------------------


def _row(role: str = "user", *, ecosystem: uuid.UUID = OASIS, status: str = "active", profile: str | None = None) -> Member:
    return Member(
        id=uuid.uuid4(), ecosystem_id=ecosystem, user_id=uuid.uuid4(), member_id="MEM", display_name="M",
        role=role, current_status=status, profile=profile,
    )


ACTORS = {
    "nobody": None,
    "member": _row(),
    "author": _row(),
    "domain_steward": _row(),
    "mod": _row("mod"),
    "admin": _row("admin"),
    "owner": _row("owner"),
    "suspended_admin": _row("admin", status="suspended"),
    "foreign_owner": _row("owner", ecosystem=OMNIONE),
}
AUTHORED = Proposal(ecosystem_id=OASIS, proposer_member_id=ACTORS["author"].id)
LEGACY = Proposal(ecosystem_id=OASIS, proposer_member_id=None)
DOMAIN = Domain(ecosystem_id=OASIS, steward_id=ACTORS["domain_steward"].id)
AGREEMENT = Agreement(ecosystem_id=OASIS)


@pytest.mark.parametrize("actor, steward, steward_here, manage_authored, manage_legacy, edit_domain, conduct_ceremony", [
    ("nobody",          False, False, False, False, False, False),
    ("member",          False, False, False, False, False, False),
    ("author",          False, False, True,  False, False, False),
    ("domain_steward",  False, False, False, False, True,  False),
    ("mod",             True,  True,  True,  True,  True,  False),
    ("admin",           True,  True,  True,  True,  True,  True),
    ("owner",           True,  True,  True,  True,  True,  True),
    ("suspended_admin", True,  True,  True,  True,  True,  False),  # only ceremonies require an active row
    ("foreign_owner",   True,  False, False, False, False, False),  # a steward elsewhere has no say here
])
def test_governance_permissions_by_actor(actor, steward, steward_here, manage_authored, manage_legacy, edit_domain, conduct_ceremony):
    member = ACTORS[actor]
    assert is_steward(member) is steward  # the row's own ecosystem: only meaningful for a caller_in row
    assert is_steward_in(member, OASIS) is steward_here
    assert can_manage_proposal(member, AUTHORED) is manage_authored
    assert can_manage_proposal(member, LEGACY) is manage_legacy
    assert can_edit_domain(member, DOMAIN) is edit_domain
    assert can_conduct_agreement_ceremony(member, AGREEMENT) is conduct_ceremony


PROFILE_ADMIN = _row(profile="co_creator")  # the ecosystem's founder
OTHER_PROFILE_ADMIN = _row(profile="builder")
OTHER_ADMIN = _row("admin")
OTHER_OWNER = _row("owner")


# Owner decision (2026-10-31): only roles below your own rank, to members below it; only an owner makes an owner.
@pytest.mark.parametrize("caller, target, new_role, has_owner, allowed", [
    ("owner", "admin", "user", True, True),               # below the owner's rank
    ("owner", "member", "owner", True, True),             # only an owner makes an owner
    ("admin", "member", "owner", True, False),
    ("owner", "other_owner", "user", True, False),        # never a peer at your own rank
    ("profile_admin", "member", "owner", False, True),    # the founder bootstraps while there is no owner
    ("profile_admin", "member", "mod", True, False),      # ...and only then
    ("other_profile_admin", "other_profile_admin", "owner", False, False),  # a later co_creator never does
    ("admin", "member", "mod", True, True),
    ("admin", "member", "admin", True, False),            # admins cannot mint admins
    ("admin", "other_admin", "user", True, False),        # nor demote a peer
    ("admin", "admin", "user", True, True),               # anyone may step down
    ("admin", "admin", "owner", True, False),             # but not up
    ("member", "member", "mod", True, False),
    ("mod", "member", "mod", True, False),
    ("foreign_owner", "member", "mod", True, False),      # an owner elsewhere has no say here
    ("nobody", "member", "mod", True, False),
    ("owner", "member", "superuser", True, False),        # unknown tiers are never granted
])
def test_role_changes_by_actor(caller, target, new_role, has_owner, allowed):
    people = {**ACTORS, "profile_admin": PROFILE_ADMIN, "other_admin": OTHER_ADMIN, "other_owner": OTHER_OWNER,
              "other_profile_admin": OTHER_PROFILE_ADMIN}
    assert can_assign_role(people[caller], people[target], new_role, ecosystem_has_owner=has_owner,
                           founder_id=PROFILE_ADMIN.id) is allowed


@pytest.mark.parametrize("caller, expected", [
    ("owner", ["mod", "admin", "owner"]),  # the member's current tier is never offered
    ("admin", ["mod"]),
    ("mod", []),
])
def test_role_picker_offers_only_grantable_tiers(caller, expected):
    assert assignable_roles(ACTORS[caller], ACTORS["member"]) == expected
