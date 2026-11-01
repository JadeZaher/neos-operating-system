"""Platform admin (owner decision 2026-11-01) through the real app and its request middleware.

Rule: src/neos_agent/api/AGENTS.md "Platform admin (G-Authority)". A co_creator/builder profile counts
platform-wide only on an ACTIVE row in the home ecosystem, pinned by id (PLATFORM_HOME_ECOSYSTEM_ID, else
the app_settings pin; never a name); founding an ecosystem makes you its administrator there, nothing more. Every case asserts the status AND
whether the act took effect (the row was written, or the read disclosed it), so a refusal that still
wrote goes red.
"""

from __future__ import annotations

import contextlib
import functools
import json as jsonlib
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from urllib.parse import quote

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

import neos_agent.db.course_models  # noqa: F401 — registers quiz tables the app's blueprints reference
from neos_agent.api.helpers import PLATFORM_HOME_SETTING_KEY
from neos_agent.api.settings import PLATFORM_HOME_NOT_SETTABLE
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import (
    AppSetting,
    AuthSession,
    BadgeDefinition,
    Base,
    CtcHandoff,
    Ecosystem,
    Member,
    Team,
    TeamMembership,
    User,
)

SECRET = "platform-admin-secret-0123456789abcdef"

OMNIONE = uuid.UUID(int=0xA1)
RIVERBANK = uuid.UUID(int=0xA2)
FRESH = uuid.UUID(int=0xA3)  # founded by finn: the exploit path
SQUAT = uuid.UUID(int=0xA4)  # founded later and named "omnione", so its name slugs like the home's

ECOSYSTEMS = (
    (OMNIONE, "OmniOne", datetime(2026, 1, 1)),
    (RIVERBANK, "Riverbank", datetime(2026, 2, 1)),
    (FRESH, "Fresh Start", datetime(2026, 10, 1)),
    (SQUAT, "omnione", datetime(2026, 10, 15)),
)

# name -> member rows (ecosystem, status, profile, role, created_at).
PEOPLE = {
    "lani": [(OMNIONE, "active", "co_creator", "owner", datetime(2026, 1, 1))],  # platform admin, OmniOne's owner
    "bram": [(OMNIONE, "active", "builder", "user", datetime(2026, 1, 5))],  # platform admin, no role
    "pia": [(OMNIONE, "pending_consent", "co_creator", "user", datetime(2026, 1, 6))],
    "sami": [(OMNIONE, "suspended", "co_creator", "user", datetime(2026, 1, 7))],
    "finn": [
        (OMNIONE, "active", None, "user", datetime(2026, 3, 1)),  # placed in OmniOne at sign-up,
        (FRESH, "active", "co_creator", "user", datetime(2026, 10, 1)),  # then POST /ecosystems
    ],
    "mona": [(OMNIONE, "active", None, "user", datetime(2026, 3, 2))],
    "rhea": [(RIVERBANK, "active", "co_creator", "user", datetime(2026, 2, 1))],
    "quin": [(SQUAT, "active", "co_creator", "user", datetime(2026, 10, 15))],
}
SELECTED = {"finn": [FRESH]}  # the exploit: only the founded ecosystem selected, so ctx.member is its co_creator row
ACTORS = ("anon", "lani", "bram", "pia", "sami", "finn", "mona")
TARGET_JOINED = datetime(2026, 10, 20)  # after every founder row, so a target never counts as a founder


@pytest.fixture(scope="module")
def platform(tmp_path_factory):
    """One create_app (real auth middleware) over a SQLite file seeded with the people above."""
    from neos_agent.config import Settings
    from neos_agent.main import create_app

    database_file = (tmp_path_factory.mktemp("platform-admin") / "platform.db").as_posix()
    engine = create_engine(f"sqlite:///{database_file}")
    Base.metadata.create_all(engine)
    cookies: dict[str, str] = {}
    with Session(engine) as session:  # seeded first, so startup never adds its default ecosystem
        for ecosystem_id, name, created in ECOSYSTEMS:
            session.add(Ecosystem(id=ecosystem_id, name=name, status="active", created_at=created, updated_at=created))
        session.add(AppSetting(key=PLATFORM_HOME_SETTING_KEY, value={"ecosystem_id": str(OMNIONE)}))  # what v1b4e7c9d2f5 writes
        session.flush()
        for name, rows in PEOPLE.items():
            user = User(id=uuid.uuid4(), display_name=name.title())
            session.add(user)
            session.flush()
            for ecosystem_id, status, profile, role, created in rows:
                session.add(Member(
                    id=uuid.uuid4(), ecosystem_id=ecosystem_id, user_id=user.id,
                    member_id=f"MEM-{name}-{ecosystem_id.int}", display_name=name.title(),
                    current_status=status, profile=profile, role=role, created_at=created, updated_at=created,
                ))
            session_id = uuid.uuid4()
            session.add(AuthSession(
                id=session_id, user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            ))
            cookies[name] = make_session_cookie(str(session_id), SECRET)
        session.commit()
    engine.dispose()

    database_url = f"sqlite+aiosqlite:///{database_file}"
    app = create_app(settings=Settings(
        _env_file=None, DATABASE_URL=database_url, SESSION_SECRET=SECRET, SIGNUP_DEFAULT_ECOSYSTEM_SLUG="",
        PLATFORM_HOME_ECOSYSTEM_ID="",
        NEOS_CORE_PATH=str(tmp_path_factory.mktemp("no-skills")), CORS_ORIGINS="*", LOG_LEVEL="info",
    ))
    # sanic-ext's automatic HEAD/OPTIONS routes cost ~20 s per fresh app and play no part here.
    app.config.HTTP_AUTO_HEAD = False
    app.config.HTTP_AUTO_OPTIONS = False
    app.config.CORS = False
    return SimpleNamespace(app=app, database_url=database_url, cookies=cookies)


@pytest_asyncio.fixture
async def db(platform):
    """A session factory on the app's database, bound to this test's event loop."""
    engine = create_async_engine(platform.database_url)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _call(platform, actor: str, method: str, path: str, body: dict | None = None):
    """One request as `actor` (their session cookie and, for finn, the founded ecosystem selected)."""
    headers = {}
    if actor != "anon":
        cookie = f"neos_session={platform.cookies[actor]}"
        if actor in SELECTED:
            cookie += f"; neos_selected_ecosystems={quote(jsonlib.dumps([str(i) for i in SELECTED[actor]]))}"
        headers["cookie"] = cookie
    kwargs = {"headers": headers} if body is None else {"headers": headers, "json": body}
    _, response = await getattr(platform.app.asgi_client, method)(path, **kwargs)
    return response


# --- Seeding: each case acts on its own fresh rows ---------------------------------------------

async def _add(db, *rows) -> None:
    async with db() as session:
        for row in rows:
            session.add(row)
            await session.flush()
        await session.commit()


async def _member_in(db, ecosystem_id: uuid.UUID) -> uuid.UUID:
    """A fresh plain member of `ecosystem_id` (their own user) to act on."""
    user = User(id=uuid.uuid4(), display_name="Target")
    member = Member(
        id=uuid.uuid4(), ecosystem_id=ecosystem_id, user_id=user.id, member_id=f"MEM-T-{user.id.hex[:10]}",
        display_name="Target", current_status="active", role="user",
        created_at=TARGET_JOINED, updated_at=TARGET_JOINED,
    )
    await _add(db, user, member)
    return member.id


async def _team_in(db, ecosystem_id: uuid.UUID) -> uuid.UUID:
    team = Team(id=uuid.uuid4(), ecosystem_id=ecosystem_id, name="Kitchen crew")
    await _add(db, team)
    return team.id


async def _badge_in(db, ecosystem_id: uuid.UUID | None) -> uuid.UUID:
    badge = BadgeDefinition(
        id=uuid.uuid4(), ecosystem_id=ecosystem_id, badge_key=f"key-{uuid.uuid4().hex[:8]}", badge_name="Helper",
    )
    await _add(db, badge)
    return badge.id


async def _read(db, statement):
    async with db() as session:
        return await session.scalar(statement)


# --- Acts: (status, took effect) --------------------------------------------------------------

async def put_setting(db, call):
    key = f"flag-{uuid.uuid4().hex[:8]}"
    response = await call("put", "/api/v1/settings", {"key": key, "value": {"on": True}})
    return response.status, await _read(db, select(AppSetting.id).where(AppSetting.key == key)) is not None


async def list_ctc_handoff(db, call):
    member_id = await _member_in(db, OMNIONE)
    await _add(db, CtcHandoff(member_id=member_id, ready_for_neos_den=True))
    response = await call("get", "/api/v1/admin/ctc-handoff")
    listed = {item["member_id"] for item in (response.json or {}).get("items", [])}
    return response.status, str(member_id) in listed


async def set_ctc_handoff(db, call):
    member_id = await _member_in(db, OMNIONE)
    response = await call("post", f"/api/v1/admin/ctc-handoff/{member_id}", {"ready_for_neos_den": True})
    stored = await _read(db, select(CtcHandoff.ready_for_neos_den).where(CtcHandoff.member_id == member_id))
    return response.status, stored is True


def create_badge(ecosystem_id):
    async def act(db, call):
        key = f"key-{uuid.uuid4().hex[:8]}"
        response = await call("post", "/api/v1/badges",
                              {"badge_key": key, "badge_name": "Steady hand", "ecosystem_id": str(ecosystem_id)})
        return response.status, await _read(db, select(BadgeDefinition.id).where(BadgeDefinition.badge_key == key)) is not None
    return act


def rename_badge(ecosystem_id):
    async def act(db, call):
        badge_id = await _badge_in(db, ecosystem_id)
        response = await call("put", f"/api/v1/badges/{badge_id}", {"badge_name": "Renamed"})
        return response.status, await _read(db, select(BadgeDefinition.badge_name).where(BadgeDefinition.id == badge_id)) == "Renamed"
    return act


def delete_badge(ecosystem_id):
    async def act(db, call):
        badge_id = await _badge_in(db, ecosystem_id)
        response = await call("delete", f"/api/v1/badges/{badge_id}")
        return response.status, await _read(db, select(BadgeDefinition.id).where(BadgeDefinition.id == badge_id)) is None
    return act


def create_team(ecosystem_id):
    async def act(db, call):
        name = f"Team {uuid.uuid4().hex[:8]}"
        response = await call("post", "/api/v1/teams", {"name": name, "ecosystem_id": str(ecosystem_id)})
        return response.status, await _read(db, select(Team.id).where(Team.name == name)) is not None
    return act


def rename_team(ecosystem_id):
    async def act(db, call):
        team_id = await _team_in(db, ecosystem_id)
        response = await call("put", f"/api/v1/teams/{team_id}", {"name": "Renamed"})
        return response.status, await _read(db, select(Team.name).where(Team.id == team_id)) == "Renamed"
    return act


def delete_team(ecosystem_id):
    async def act(db, call):
        team_id = await _team_in(db, ecosystem_id)
        response = await call("delete", f"/api/v1/teams/{team_id}")
        return response.status, await _read(db, select(Team.id).where(Team.id == team_id)) is None
    return act


def add_to_team(ecosystem_id):
    async def act(db, call):
        team_id, member_id = await _team_in(db, ecosystem_id), await _member_in(db, ecosystem_id)
        response = await call("post", f"/api/v1/teams/{team_id}/members", {"member_id": str(member_id)})
        joined = await _read(db, select(TeamMembership.id).where(
            TeamMembership.team_id == team_id, TeamMembership.member_id == member_id))
        return response.status, joined is not None
    return act


def remove_from_team(ecosystem_id):
    async def act(db, call):
        team_id, member_id = await _team_in(db, ecosystem_id), await _member_in(db, ecosystem_id)
        await _add(db, TeamMembership(id=uuid.uuid4(), team_id=team_id, member_id=member_id))
        response = await call("delete", f"/api/v1/teams/{team_id}/members/{member_id}")
        left = await _read(db, select(TeamMembership.id).where(
            TeamMembership.team_id == team_id, TeamMembership.member_id == member_id))
        return response.status, left is None
    return act


def list_team_members(ecosystem_id):
    async def act(db, call):
        team_id, member_id = await _team_in(db, ecosystem_id), await _member_in(db, ecosystem_id)
        await _add(db, TeamMembership(id=uuid.uuid4(), team_id=team_id, member_id=member_id))
        response = await call("get", f"/api/v1/teams/{team_id}/members")
        listed = {item["member_id"] for item in (response.json or {}).get("items", [])}
        return response.status, str(member_id) in listed
    return act


def grant_profile(ecosystem_id):
    async def act(db, call):
        member_id = await _member_in(db, ecosystem_id)
        response = await call("put", f"/api/v1/members/{member_id}/profile-grant", {"profile": "builder"})
        return response.status, await _read(db, select(Member.profile).where(Member.id == member_id)) == "builder"
    return act


# Columns follow ACTORS: anon, lani (OmniOne co_creator, owner), bram (OmniOne builder), pia (pending
# co_creator), sami (suspended co_creator), finn (founder of Fresh, plain OmniOne member, Fresh selected),
# mona (plain OmniOne member). 404 = the resource is outside the caller's active ecosystems.
TABLE = [
    # Kept on require_admin: nothing here belongs to one ecosystem.
    ("PUT /settings", put_setting, (401, 200, 200, 403, 403, 403, 403)),
    ("GET /admin/ctc-handoff", list_ctc_handoff, (401, 200, 200, 403, 403, 403, 403)),
    ("POST /admin/ctc-handoff/:member", set_ctc_handoff, (401, 200, 200, 403, 403, 403, 403)),
    ("PUT /badges/:global", rename_badge(None), (401, 200, 200, 403, 403, 403, 403)),
    ("DELETE /badges/:global", delete_badge(None), (401, 200, 200, 403, 403, 403, 403)),
    # Moved to caller_in + can_administer_ecosystem: OmniOne's own resources.
    ("POST /teams in OmniOne", create_team(OMNIONE), (401, 201, 201, 403, 403, 403, 403)),
    ("PUT /teams/:omnione", rename_team(OMNIONE), (401, 200, 200, 404, 404, 403, 403)),
    ("DELETE /teams/:omnione", delete_team(OMNIONE), (401, 200, 200, 404, 404, 403, 403)),
    ("POST /teams/:omnione/members", add_to_team(OMNIONE), (401, 201, 201, 404, 404, 403, 403)),
    ("DELETE /teams/:omnione/members/:member", remove_from_team(OMNIONE), (401, 200, 200, 404, 404, 403, 403)),
    ("GET /teams/:omnione/members", list_team_members(OMNIONE), (401, 200, 200, 404, 404, 200, 200)),
    ("POST /badges in OmniOne", create_badge(OMNIONE), (401, 201, 201, 403, 403, 403, 403)),
    ("PUT /badges/:omnione", rename_badge(OMNIONE), (401, 200, 200, 404, 404, 403, 403)),
    ("DELETE /badges/:omnione", delete_badge(OMNIONE), (401, 200, 200, 404, 404, 403, 403)),
    # can_grant_profile needs the power to make an admin there: OmniOne's owner, not a builder without a role.
    ("PUT /members/:omnione/profile-grant", grant_profile(OMNIONE), (401, 200, 403, 404, 404, 403, 403)),
    # The founder administers Fresh; OmniOne's platform admins are not stewards there.
    ("POST /teams in Fresh", create_team(FRESH), (401, 403, 403, 403, 403, 201, 403)),
    ("PUT /teams/:fresh", rename_team(FRESH), (401, 404, 404, 404, 404, 200, 404)),
    ("DELETE /teams/:fresh", delete_team(FRESH), (401, 404, 404, 404, 404, 200, 404)),
    ("POST /teams/:fresh/members", add_to_team(FRESH), (401, 404, 404, 404, 404, 201, 404)),
    ("DELETE /teams/:fresh/members/:member", remove_from_team(FRESH), (401, 404, 404, 404, 404, 200, 404)),
    ("GET /teams/:fresh/members", list_team_members(FRESH), (401, 404, 404, 404, 404, 200, 404)),
    ("POST /badges in Fresh", create_badge(FRESH), (401, 403, 403, 403, 403, 201, 403)),
    ("PUT /badges/:fresh", rename_badge(FRESH), (401, 404, 404, 404, 404, 200, 404)),
    ("DELETE /badges/:fresh", delete_badge(FRESH), (401, 404, 404, 404, 404, 200, 404)),
    ("PUT /members/:fresh/profile-grant", grant_profile(FRESH), (401, 404, 404, 404, 404, 200, 404)),
]

CASES = [
    pytest.param(actor, act, statuses[column], id=f"{route} as {actor}")
    for route, act, statuses in TABLE
    for column, actor in enumerate(ACTORS)
]


@pytest.mark.parametrize("actor, act, expected", CASES)
async def test_platform_and_ecosystem_administration_by_actor(platform, db, actor, act, expected):
    status, took_effect = await act(db, functools.partial(_call, platform, actor))
    assert status == expected
    assert took_effect is (expected in (200, 201))


@contextlib.asynccontextmanager
async def _home_altered(db, *, renamed: bool, pinned: bool):
    """Rename OmniOne and/or drop the pin for one test, then put both back (the database is module-wide)."""
    async with db() as session:
        if renamed:
            await session.execute(update(Ecosystem).where(Ecosystem.id == OMNIONE).values(name="OmniOne Network"))
        if not pinned:
            await session.execute(delete(AppSetting).where(AppSetting.key == PLATFORM_HOME_SETTING_KEY))
        await session.commit()
    try:
        yield
    finally:
        async with db() as session:
            await session.execute(update(Ecosystem).where(Ecosystem.id == OMNIONE).values(name="OmniOne"))
            if await session.scalar(select(AppSetting.id).where(AppSetting.key == PLATFORM_HOME_SETTING_KEY)) is None:
                session.add(AppSetting(key=PLATFORM_HOME_SETTING_KEY, value={"ecosystem_id": str(OMNIONE)}))
            await session.commit()


# (env PLATFORM_HOME_ECOSYSTEM_ID, env SIGNUP_DEFAULT_ECOSYSTEM_SLUG, OmniOne renamed, pin row present, actor -> status)
HOME_CASES = [
    pytest.param("", "", False, True, {"lani": 200, "rhea": 403, "quin": 403}, id="the pinned row names the home"),
    pytest.param("", "", True, True, {"lani": 200, "quin": 403},
                 id="renaming OmniOne moves nothing; the later 'omnione' founder gains nothing"),
    pytest.param("", "", False, False, {"lani": 403, "quin": 403},
                 id="no pin and no env: nobody, though ecosystems named OmniOne and 'omnione' exist"),
    pytest.param("", "", True, False, {"lani": 403, "quin": 403},
                 id="no pin and the only 'omnione' left is a squatter's: still nobody"),
    pytest.param("", "riverbank", False, True, {"lani": 200, "rhea": 403}, id="the sign-up slug no longer picks the home"),
    pytest.param(str(RIVERBANK), "", False, True, {"lani": 403, "rhea": 200}, id="the env id overrides the pinned row"),
    pytest.param("not-a-uuid", "", False, True, {"lani": 200, "rhea": 403}, id="an env value that is not a UUID falls back to the pin"),
    pytest.param(str(uuid.UUID(int=0xDEAD)), "", False, True, {"lani": 403, "rhea": 403},
                 id="an env id naming no ecosystem: nobody"),
]


@pytest.mark.parametrize("env_home, signup_slug, renamed, pinned, expected", HOME_CASES)
async def test_the_pinned_home_decides_who_is_a_platform_admin(
    platform, db, monkeypatch, env_home, signup_slug, renamed, pinned, expected,
):
    monkeypatch.setattr(platform.app.ctx.settings, "PLATFORM_HOME_ECOSYSTEM_ID", env_home)
    monkeypatch.setattr(platform.app.ctx.settings, "SIGNUP_DEFAULT_ECOSYSTEM_SLUG", signup_slug)
    async with _home_altered(db, renamed=renamed, pinned=pinned):
        outcomes = {actor: await put_setting(db, functools.partial(_call, platform, actor)) for actor in expected}
    assert outcomes == {actor: (status, status == 200) for actor, status in expected.items()}


async def test_a_platform_admin_cannot_move_the_home_through_the_settings_api(platform, db):
    response = await _call(platform, "lani", "put", "/api/v1/settings",
                           {"key": PLATFORM_HOME_SETTING_KEY, "value": {"ecosystem_id": str(FRESH)}})
    assert (response.status, response.json) == (400, {"error": PLATFORM_HOME_NOT_SETTABLE})
    pinned = await _read(db, select(AppSetting.value).where(AppSetting.key == PLATFORM_HOME_SETTING_KEY))
    assert pinned == {"ecosystem_id": str(OMNIONE)}
    assert (await put_setting(db, functools.partial(_call, platform, "finn")))[0] == 403  # Fresh's founder gained nothing


async def test_a_fresh_server_pins_the_omnione_it_founds(tmp_path):
    from neos_agent.config import Settings
    from neos_agent.main import create_app

    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'fresh.db').as_posix()}"
    app = create_app(settings=Settings(
        _env_file=None, DATABASE_URL=database_url, SESSION_SECRET=SECRET, PLATFORM_HOME_ECOSYSTEM_ID="",
        NEOS_CORE_PATH=str(tmp_path), CORS_ORIGINS="*", LOG_LEVEL="info",
    ))
    app.config.HTTP_AUTO_HEAD = False
    app.config.HTTP_AUTO_OPTIONS = False
    app.config.CORS = False
    await app.asgi_client.get("/api/v1/health")  # any request runs startup: create_all and the default ecosystem

    engine = create_async_engine(database_url)
    async with engine.connect() as conn:
        ecosystems = (await conn.execute(select(Ecosystem.id, Ecosystem.name))).all()
        pinned = await conn.scalar(select(AppSetting.value).where(AppSetting.key == PLATFORM_HOME_SETTING_KEY))
    await engine.dispose()
    [(omnione_id, name)] = ecosystems
    assert (name, pinned) == ("OmniOne", {"ecosystem_id": str(omnione_id)})
