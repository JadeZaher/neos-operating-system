"""Published member counts include only consented, active members.

Pending sign-ups, suspended rows, and departed rows stay out of the ecosystem,
community, discover, orientation, auth, and dashboard counts. The public
community preview used by /ethos/:id returns that count and no member identity.
The sole-member settings gate still counts every membership row.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — quizzes, read while a pending caller loads /auth/me
from neos_agent.agent.governance_tools import get_ecosystem
from neos_agent.api.auth import auth_api_bp
from neos_agent.api.communities import communities_api_bp
from neos_agent.api.dashboard import _summary_counts as api_summary_counts
from neos_agent.api.dashboard import dashboard_api_bp
from neos_agent.api.discover import discover_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.orientation import orientation_api_bp
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import AuthSession, Base, Ecosystem, Member, User
from neos_agent.views import register_views
from neos_agent.views.dashboard import _summary_counts as view_summary_counts
from neos_agent.views.ecosystems import ecosystems_bp

HARBOR = uuid.UUID("0000000c-0000-0000-0000-0000000000a1")
SOLO = uuid.UUID("0000000c-0000-0000-0000-0000000000b1")  # one active member plus a pending sign-up
LONE = uuid.UUID("0000000c-0000-0000-0000-0000000000c1")  # one active member, and nobody else
ELSEWHERE = uuid.UUID("0000000c-0000-0000-0000-0000000000d1")
SECRET = "active-member-count-test-secret"
ACTIVE_COUNT = 2  # Ada and Eve. Everyone else in Harbor is not active.

# name -> (ecosystem, status). Secrets are names, keys, DIDs, and usernames the public payload must not carry.
PEOPLE = {
    "ada": (HARBOR, "active"),
    "eve": (HARBOR, "active"),
    "bea": (HARBOR, "pending_consent"),
    "cy": (HARBOR, "exited"),
    "dee": (HARBOR, "suspended"),
    "gio": (HARBOR, "inactive"),
    "finn": (SOLO, "active"),
    "pia": (SOLO, "pending_consent"),
    "ned": (LONE, "active"),
}
USER_IDS = {name: uuid.uuid5(uuid.NAMESPACE_DNS, f"active-count.{name}") for name in PEOPLE}
MEMBER_IDS = {name: uuid.uuid5(USER_IDS[name], "member") for name in PEOPLE}
IDENTITY = {
    name: (
        f"{name.title()} Secretname",
        f"MEM-{name.upper()}-SECRET",
        f"did:key:z{name.title()}SecretIdentity",
        f"{name}-secret-login",
        f"555-private-{name}",
    )
    for name in PEOPLE
}
PUBLIC_FIELDS = {
    "id", "name", "description", "tags", "location", "logo_url",
    "preview_url", "join_url", "member_count",
}


def _user_id(name: str) -> uuid.UUID:
    return USER_IDS[name]


async def _seed(session: AsyncSession) -> None:
    session.add_all([
        Ecosystem(id=HARBOR, name="Harbor", description="A public harbor", status="active", visibility="public"),
        Ecosystem(id=SOLO, name="Solo Gate", description="A private roster", status="active", visibility="private"),
        Ecosystem(id=LONE, name="Lone Gate", description="One person", status="active", visibility="private"),
        Ecosystem(id=ELSEWHERE, name="Elsewhere", description="Another place", status="active", visibility="private"),
    ])
    for name in PEOPLE:
        display_name, _member_key, did, username, phone = IDENTITY[name]
        session.add(User(
            id=_user_id(name), display_name=display_name, did=did, username=username, phone=phone,
        ))
    await session.flush()
    for name, (ecosystem_id, status) in PEOPLE.items():
        display_name, member_key, _did, _username, _phone = IDENTITY[name]
        session.add(Member(
            id=MEMBER_IDS[name], ecosystem_id=ecosystem_id, user_id=_user_id(name),
            member_id=member_key, display_name=display_name, current_status=status, role="user",
        ))
    await session.commit()


def _app(factory) -> Sanic:
    app = Sanic(f"test-active-count-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = type("Settings", (), {"SESSION_SECRET": SECRET, "FRONTEND_URL": "https://app.example"})()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        name = request.headers.get("x-test-as")
        if not name:
            return
        ecosystem_id, status = PEOPLE[name]
        request.ctx.user = User(id=_user_id(name), display_name=IDENTITY[name][0], disabled_at=None)
        request.ctx.member = Member(
            id=MEMBER_IDS[name], ecosystem_id=ecosystem_id, user_id=_user_id(name),
            member_id=IDENTITY[name][1], display_name=IDENTITY[name][0], current_status=status, role="user",
        )
        request.ctx.selected_ecosystem_ids = [ecosystem_id]
        request.ctx.authorized_ecosystem_ids = [ecosystem_id]
        request.ctx.ecosystems = [Ecosystem(id=ecosystem_id, name="Selected", status="active", visibility="public")]

    for blueprint in (
        ecosystems_api_bp, communities_api_bp, discover_api_bp, dashboard_api_bp,
        orientation_api_bp, auth_api_bp,
    ):
        app.blueprint(blueprint)
    register_views(app)
    app.blueprint(ecosystems_bp)
    return app


@pytest_asyncio.fixture
async def world():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
    application = _app(factory)
    yield type("World", (), {"app": application, "db": factory})()
    await engine.dispose()


async def _call(world, method: str, who: str | None, url: str, **kwargs):
    headers = {"x-test-as": who} if who else {}
    _, response = await getattr(world.app.asgi_client, method)(url, headers=headers, **kwargs)
    return response


def _members_card(summary: dict) -> int:
    return next(card["value"] for card in summary["cards"] if card["label"] == "Members")


def _html_count(html: str, label: str) -> int:
    match = re.search(
        rf">{label}</(?:dt|span)>\s*<(?:dd|span)[^>]*>\s*(\d+)\s*</(?:dd|span)>",
        html,
    )
    assert match, html
    return int(match.group(1))


def _dashboard_members(html: str) -> int:
    match = re.search(
        r'tracking-wide">Members</span>\s*</div>\s*<div class="text-3xl[^"]*">\s*(\d+)\s*</div>',
        html,
    )
    assert match, html
    return int(match.group(1))


def _identity_text() -> list[str]:
    leaked = []
    for name, (display_name, member_key, did, username, phone) in IDENTITY.items():
        leaked.extend([display_name, member_key, did, username, phone, str(USER_IDS[name]), str(MEMBER_IDS[name])])
    return leaked


async def _session_cookie(world, name: str) -> dict[str, str]:
    session_id = uuid.uuid4()
    async with world.db() as session:
        session.add(AuthSession(
            id=session_id, user_id=_user_id(name),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))
        await session.commit()
    return {"neos_session": make_session_cookie(str(session_id), SECRET)}


async def test_every_published_count_includes_only_active_members(world):
    listed = await _call(world, "get", "ada", "/api/v1/ecosystems")
    assert listed.status == 200
    harbor = next(item for item in listed.json["ecosystems"] if item["name"] == "Harbor")
    assert harbor["member_count"] == ACTIVE_COUNT

    detail = await _call(world, "get", "ada", f"/api/v1/ecosystems/{HARBOR}")
    assert detail.json["member_count"] == ACTIVE_COUNT
    solo = await _call(world, "get", "finn", f"/api/v1/ecosystems/{SOLO}")
    assert solo.json["member_count"] == 1
    lone = await _call(world, "get", "ned", f"/api/v1/ecosystems/{LONE}")
    assert lone.json["member_count"] == 1

    discovered = await _call(world, "get", "ada", "/api/v1/discover?tab=ecosystems")
    by_name = {item["name"]: item["member_count"] for item in discovered.json["ecosystems"]["items"]}
    assert by_name["Harbor"] == ACTIVE_COUNT
    assert "Solo Gate" not in by_name and "Lone Gate" not in by_name

    summary = await _call(world, "get", "ada", "/api/v1/dashboard/summary")
    assert summary.status == 200
    assert _members_card(summary.json) == ACTIVE_COUNT

    for who in ("ada", "bea"):
        ethos = await _call(world, "get", who, f"/api/v1/orientation/ethos/{HARBOR}")
        assert ethos.status == 200, ethos.text
        assert ethos.json["member_count"] == ACTIVE_COUNT
        assert "display_name" not in ethos.json and "did" not in ethos.json

    for who in ("ada", "bea"):
        cookie = await _session_cookie(world, who)
        _, me = await world.app.asgi_client.get("/api/v1/auth/me", cookies=cookie)
        assert me.status == 200, me.text
        mine = next(item for item in me.json["ecosystems"] if item["name"] == "Harbor")
        assert mine["member_count"] == ACTIVE_COUNT
        assert mine["membership_status"] == PEOPLE[who][1]

    async with world.db() as session:
        assistant = await get_ecosystem({"name": "Harbor"}, session, None, caller_user_id=_user_id("ada"))
    assert assistant["data"]["active_member_count"] == ACTIVE_COUNT

    page = await _call(world, "get", "ada", "/dashboard/data")
    assert page.status == 200
    assert _dashboard_members(page.text) == ACTIVE_COUNT
    directory = await _call(world, "get", None, f"/ecosystems/{HARBOR}")
    assert directory.status == 200
    assert _html_count(directory.text, "Members") == ACTIVE_COUNT
    listing = await _call(world, "get", None, "/ecosystems/")
    assert _html_count(listing.text, "Members") == ACTIVE_COUNT


async def test_public_ethos_preview_returns_the_active_count_and_no_identities(world):
    listing = await _call(world, "get", None, "/api/v1/communities")
    assert listing.status == 200
    public = {item["name"]: item for item in listing.json["items"]}
    assert set(public) == {"Harbor"}
    assert set(public["Harbor"]) == PUBLIC_FIELDS
    assert public["Harbor"]["member_count"] == ACTIVE_COUNT
    assert public["Harbor"]["join_url"] == f"/ethos/{HARBOR}"

    for who in (None, "bea"):
        detail = await _call(world, "get", who, f"/api/v1/communities/{HARBOR}")
        assert detail.status == 200, detail.text
        assert set(detail.json) == PUBLIC_FIELDS | {"opportunities_require_sign_in", "opportunities"}
        assert detail.json["member_count"] == ACTIVE_COUNT
        assert detail.json["opportunities"] == []
        assert isinstance(detail.json["member_count"], int)
        body = detail.text
        for secret in _identity_text():
            assert secret not in body
        assert "Solo Gate" not in body and "Lone Gate" not in body

    hidden = await _call(world, "get", None, f"/api/v1/communities/{SOLO}")
    assert hidden.status == 404
    assert "Finn Secretname" not in hidden.text and "Pia Secretname" not in hidden.text


async def test_a_pending_sign_up_does_not_change_who_may_edit_settings(world):
    edit = {"description": "Updated from the test"}
    denied = await _call(world, "put", "finn", f"/api/v1/ecosystems/{SOLO}", json=edit)
    assert denied.status == 403
    assert denied.json["error"] == "Only ecosystem stewards can update ecosystem settings"
    allowed = await _call(world, "put", "ned", f"/api/v1/ecosystems/{LONE}", json=edit)
    assert allowed.status == 200
    assert allowed.json["member_count"] == 1
    assert allowed.json["description"] == edit["description"]


async def test_dashboard_counts_a_shared_active_member_and_skips_a_shared_pending_one(world):
    async with world.db() as session:
        for name, status in (("shared-active", "active"), ("shared-pending", "pending_consent")):
            user_id = uuid.uuid5(uuid.NAMESPACE_DNS, name)
            session.add(User(id=user_id, display_name=name))
            await session.flush()
            session.add(Member(
                id=uuid.uuid4(), ecosystem_id=ELSEWHERE, user_id=user_id, member_id=f"MEM-{name}",
                display_name=name, current_status=status, role="user",
                shared_ecosystem_ids=[str(HARBOR)],
            ))
        await session.commit()
        api_counts = await api_summary_counts(session, [HARBOR])
        view_counts = await view_summary_counts(session, [HARBOR])
    # The JSON dashboard already included a member shared into the selection. The legacy page counts the home row only.
    assert api_counts["members"] == ACTIVE_COUNT + 1
    assert view_counts["members"] == ACTIVE_COUNT
