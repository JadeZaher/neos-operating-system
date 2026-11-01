"""Craft wave 1 BE-Groups: domains, members, ecosystems and discover flows.

Drives the real blueprints over in-memory SQLite as different signed-in users.
Rules under test: src/neos_agent/api/AGENTS.md "Handler contracts" (rule 5:
a detail load matches its list's visibility; fail-closed scoping; bad
pagination is a 400, never a 500).
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.discover import discover_api_bp
from neos_agent.api.domains import domains_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.members import members_api_bp
from neos_agent.db.models import Base, Domain, Ecosystem, Member, User

HOME = uuid.UUID("0000000b-0000-0000-0000-00000000000a")  # the caller's ecosystem
OTHER = uuid.UUID("0000000b-0000-0000-0000-00000000000b")  # public, caller is outside
SECRET = uuid.UUID("0000000b-0000-0000-0000-00000000000c")  # private, caller is outside
SOLO = uuid.UUID("0000000b-0000-0000-0000-00000000000d")  # one member only

HOME_DOMAIN = uuid.UUID("0000000b-0000-0000-0000-0000000000a1")
OTHER_DOMAIN = uuid.UUID("0000000b-0000-0000-0000-0000000000b1")
SHARED_DOMAIN = uuid.UUID("0000000b-0000-0000-0000-0000000000b2")  # owned by OTHER, shared with HOME

PEOPLE = {
    # key: (role, ecosystems the person is an active member of)
    "user": ("user", [HOME]),
    "mod": ("mod", [HOME]),
    "steward": ("user", [HOME]),  # stewards HOME_DOMAIN, plain tier
    "founder": ("user", [SOLO]),
    "outsider": ("user", [OTHER]),
    "newcomer": ("user", []),  # holds only a pending-consent row in HOME: no active scope
}
USER_IDS = {key: uuid.uuid5(uuid.NAMESPACE_DNS, f"groups.{key}") for key in PEOPLE}
MEMBER_IDS: dict[tuple[str, uuid.UUID], uuid.UUID] = {}


async def _seed(session: AsyncSession) -> None:
    session.add_all([
        Ecosystem(id=HOME, name="Home", status="active", visibility="public"),
        Ecosystem(id=OTHER, name="Other", status="active", visibility="public"),
        Ecosystem(id=SECRET, name="Secret", status="active", visibility="private"),
        Ecosystem(id=SOLO, name="Solo", status="active", visibility="private"),
    ])
    for key, user_id in USER_IDS.items():
        session.add(User(id=user_id, display_name=key.title()))
    await session.flush()
    for key, (role, ecosystems) in PEOPLE.items():
        for ecosystem_id in ecosystems:
            member_id = uuid.uuid4()
            MEMBER_IDS[(key, ecosystem_id)] = member_id
            session.add(Member(
                id=member_id, ecosystem_id=ecosystem_id, user_id=USER_IDS[key],
                member_id=f"MEM-{key.upper()}", display_name=key.title(),
                current_status="active", role=role,
            ))
    pending_id = uuid.uuid4()
    MEMBER_IDS[("newcomer", HOME)] = pending_id
    session.add(Member(
        id=pending_id, ecosystem_id=HOME, user_id=USER_IDS["newcomer"], member_id="MEM-NEWCOMER",
        display_name="Newcomer", current_status="pending_consent", role="user",
    ))
    await session.flush()
    session.add_all([
        Domain(id=HOME_DOMAIN, ecosystem_id=HOME, domain_id="DOM-HOME", version="1.0", status="active",
               purpose="Home work", steward_id=MEMBER_IDS[("steward", HOME)]),
        Domain(id=OTHER_DOMAIN, ecosystem_id=OTHER, domain_id="DOM-OTHER", version="1.0", status="active",
               purpose="Other work"),
        Domain(id=SHARED_DOMAIN, ecosystem_id=OTHER, domain_id="DOM-SHARED", version="1.0", status="active",
               purpose="Shared work", shared_ecosystem_ids=[str(HOME)]),
    ])
    await session.commit()


def _create_app() -> Sanic:
    """Real blueprints; the x-test-as header picks who is signed in, scoped to their active ecosystems."""
    app = Sanic(f"test-groups-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        key = request.headers.get("x-test-as")
        if not key:
            return
        role, ecosystems = PEOPLE[key]
        user_id = USER_IDS[key]
        home = ecosystems[0] if ecosystems else HOME
        request.ctx.user = User(id=user_id, display_name=key.title())
        request.ctx.member = Member(
            id=MEMBER_IDS[(key, home)], ecosystem_id=home, user_id=user_id,
            member_id="MEM-AUTH", display_name=key.title(), current_status="active", role=role,
        )
        request.ctx.selected_ecosystem_ids = list(ecosystems)
        request.ctx.authorized_ecosystem_ids = list(ecosystems)

    for blueprint in (domains_api_bp, members_api_bp, ecosystems_api_bp, discover_api_bp):
        app.blueprint(blueprint)
    return app


@pytest_asyncio.fixture
async def app():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await _seed(session)
    application = _create_app()
    application.ctx.db = session_factory
    yield application
    await engine.dispose()


async def _call(app: Sanic, method: str, who: str | None, url: str, **kwargs):
    headers = {"x-test-as": who} if who else {}
    _, response = await getattr(app.asgi_client, method)(url, headers=headers, **kwargs)
    return response


# --- visibility: a list and its detail agree, and empty scope fails closed ---


async def test_domain_detail_opens_exactly_what_the_list_shows(app):
    listed = (await _call(app, "get", "user", "/api/v1/domains")).json["items"]
    listed_ids = {item["id"] for item in listed}
    assert listed_ids == {str(HOME_DOMAIN), str(SHARED_DOMAIN)}  # owned + shared-with, not the foreign one

    for domain_id in (HOME_DOMAIN, SHARED_DOMAIN):
        assert (await _call(app, "get", "user", f"/api/v1/domains/{domain_id}")).status == 200
    foreign = await _call(app, "get", "user", f"/api/v1/domains/{OTHER_DOMAIN}")
    assert foreign.status == 404
    assert foreign.json == {"error": "Domain not found"}


async def test_member_without_active_membership_sees_nothing(app):
    for url in ("/api/v1/domains", "/api/v1/members"):
        assert (await _call(app, "get", "newcomer", url)).json["items"] == []
    # Before the fix an empty scope dropped the filter and opened every ecosystem's rows.
    assert (await _call(app, "get", "newcomer", f"/api/v1/domains/{HOME_DOMAIN}")).status == 404
    member_id = MEMBER_IDS[("user", HOME)]
    assert (await _call(app, "get", "newcomer", f"/api/v1/members/{member_id}")).status == 404


async def test_explicit_foreign_ecosystem_filter_lists_nothing(app):
    response = await _call(app, "get", "user", f"/api/v1/domains?ecosystem_ids={OTHER}")
    assert response.json["items"] == []


async def test_member_detail_is_scoped_like_the_member_list(app):
    own = MEMBER_IDS[("mod", HOME)]
    foreign = MEMBER_IDS[("outsider", OTHER)]
    assert (await _call(app, "get", "user", f"/api/v1/members/{own}")).status == 200
    assert (await _call(app, "get", "user", f"/api/v1/members/{foreign}")).status == 404
    # A foreign member cannot be promoted by guessing the id: 404, not a 403 that confirms the row.
    promote = await _call(app, "put", "user", f"/api/v1/members/{foreign}/role", json={"role": "mod"})
    assert promote.status == 404


async def test_private_ecosystem_is_a_404_public_one_a_403_for_outsiders(app):
    assert (await _call(app, "get", "user", f"/api/v1/ecosystems/{OTHER}")).status == 200  # public detail opens
    assert (await _call(app, "get", "user", f"/api/v1/ecosystems/{SECRET}")).status == 404
    assert (await _call(app, "get", "founder", f"/api/v1/ecosystems/{SOLO}")).json["caller_role"] == "user"
    # Members-only reads on a public ecosystem still say "Access denied", never leaking a private one.
    assert (await _call(app, "get", "user", f"/api/v1/ecosystems/{OTHER}/shares-needs")).status == 403
    assert (await _call(app, "get", "user", f"/api/v1/ecosystems/{SECRET}/shares-needs")).status == 404


# --- authorization decisions made in the resource's ecosystem ---


async def test_create_member_outside_scope_is_denied_even_with_empty_scope(app):
    body = {"ecosystem_id": str(OTHER), "display_name": "Sneaky"}
    assert (await _call(app, "post", "user", "/api/v1/members", json=body)).status == 403
    # An empty scope used to skip the check entirely, letting a newcomer self-enroll anywhere.
    assert (await _call(app, "post", "newcomer", "/api/v1/members", json=body)).status == 403


async def test_domain_create_and_edit_follow_the_resource_ecosystem(app):
    body = {"ecosystem_id": str(HOME), "purpose": "New work"}
    assert (await _call(app, "post", "user", "/api/v1/domains", json=body)).status == 403
    created = await _call(app, "post", "mod", "/api/v1/domains", json=body)
    assert created.status == 201 and created.json["caller_can_edit"] is True

    edit = {"purpose": "Edited"}
    assert (await _call(app, "put", "user", f"/api/v1/domains/{HOME_DOMAIN}", json=edit)).status == 403
    assert (await _call(app, "put", "steward", f"/api/v1/domains/{HOME_DOMAIN}", json=edit)).status == 200
    # Shared domain opens for the caller, but editing still needs standing in its OWN ecosystem.
    assert (await _call(app, "put", "mod", f"/api/v1/domains/{SHARED_DOMAIN}", json=edit)).status == 403


async def test_ecosystem_update_needs_a_domain_steward_unless_sole_member(app):
    edit = {"description": "Updated"}
    assert (await _call(app, "put", "user", f"/api/v1/ecosystems/{HOME}", json=edit)).status == 403  # several members, not a domain steward
    assert (await _call(app, "put", "steward", f"/api/v1/ecosystems/{HOME}", json=edit)).status == 200
    assert (await _call(app, "put", "founder", f"/api/v1/ecosystems/{SOLO}", json=edit)).status == 200  # sole member
    assert (await _call(app, "put", "user", f"/api/v1/ecosystems/{SOLO}", json=edit)).status == 404  # private, outside


# --- bad input is a 400 ---


@pytest.mark.parametrize("url", [
    "/api/v1/domains?page=abc",
    "/api/v1/members?per_page=x",
    "/api/v1/ecosystems?page=abc",
    "/api/v1/discover?page=abc",
    "/api/v1/discover/shares-needs?page=abc",
    "/api/v1/discover/collaborations?per_page=abc",
])
async def test_junk_pagination_is_a_400_not_a_500(app, url):
    response = await _call(app, "get", "user", url)
    assert response.status == 400
    assert "must be a whole number" in response.json["error"]


async def test_unauthenticated_requests_get_the_standard_401(app):
    for url in ("/api/v1/domains", "/api/v1/ecosystems", "/api/v1/discover"):
        response = await _call(app, "get", None, url)
        assert response.status == 401 and response.json == {"error": "Authentication required"}
