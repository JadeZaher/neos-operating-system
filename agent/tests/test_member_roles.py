"""Tests for per-ecosystem role tiers (user/mod/admin/owner).

Covers ROLE_RANK ordering, PUT /api/v1/members/<id>/role grant rules
(owner any, admin user/mod only, self-demotion, founder bootstrap),
authority profiles (never self-chosen; granted and recorded), per-ecosystem
isolation, and the mod-gate enforcement swaps on update_member and
member_status_transition. Eco B has no owner; Boot founded it.
"""

from __future__ import annotations

import datetime as dt
import uuid
from unittest.mock import MagicMock

import pytest
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.errors import register_api_errors
from neos_agent.api.helpers import ROLE_RANK
from neos_agent.api.members import PROFILE_GRANT_DENIED, PROFILE_GRANT_ONLY, members_api_bp
from neos_agent.db.models import Base, Ecosystem, Member, User

# ---------------------------------------------------------------------------
# Stable UUIDs
# ---------------------------------------------------------------------------
ECO_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ECO_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

U_OWNER = uuid.uuid5(uuid.NAMESPACE_DNS, "roles.owner")
U_ADMIN = uuid.uuid5(uuid.NAMESPACE_DNS, "roles.admin")
U_MOD = uuid.uuid5(uuid.NAMESPACE_DNS, "roles.mod")
U_PLAIN = uuid.uuid5(uuid.NAMESPACE_DNS, "roles.plain")
U_TARGET = uuid.uuid5(uuid.NAMESPACE_DNS, "roles.target")
U_BOOT = uuid.uuid5(uuid.NAMESPACE_DNS, "roles.bootstrap")
U_ROGUE = uuid.uuid5(uuid.NAMESPACE_DNS, "roles.rogue")

M_OWNER = uuid.uuid4()
M_ADMIN = uuid.uuid4()
M_MOD = uuid.uuid4()
M_PLAIN = uuid.uuid4()
M_TARGET = uuid.uuid4()
M_BOOT_B = uuid.uuid4()  # the bootstrap profile's row in eco B, which has no owner
M_TARGET_B = uuid.uuid4()
M_BOOT = uuid.uuid4()
M_PLAIN_B = uuid.uuid4()  # plain user's eco-B membership (mod there)
M_ROGUE_B = uuid.uuid4()  # a later co_creator in eco B: not its founder
FOUNDED, JOINED = dt.datetime(2026, 1, 1), dt.datetime(2026, 2, 1)


async def _seed(session: AsyncSession) -> None:
    session.add(Ecosystem(id=ECO_A, name="Eco A", status="active"))
    session.add(Ecosystem(id=ECO_B, name="Eco B", status="active"))
    for uid, name in [(U_OWNER, "Owner"), (U_ADMIN, "Admin"), (U_MOD, "Mod"),
                      (U_PLAIN, "Plain"), (U_TARGET, "Target"), (U_BOOT, "Boot"), (U_ROGUE, "Rogue")]:
        session.add(User(id=uid, display_name=name))
    await session.flush()

    def m(mid, eco, uid, role, profile=None, created_at=JOINED):
        return Member(
            id=mid, ecosystem_id=eco, user_id=uid,
            member_id=f"MEM-{mid.hex[:6].upper()}", display_name=f"M{mid.hex[:4]}",
            current_status="active", profile=profile, role=role, created_at=created_at,
        )

    session.add_all([
        m(M_OWNER, ECO_A, U_OWNER, "owner"),
        m(M_ADMIN, ECO_A, U_ADMIN, "admin"),
        m(M_MOD, ECO_A, U_MOD, "mod"),
        m(M_PLAIN, ECO_A, U_PLAIN, "user"),
        m(M_TARGET, ECO_A, U_TARGET, "user"),
        m(M_BOOT, ECO_A, U_BOOT, "user", profile="co_creator"),  # bootstrap: profile-admin, role user
        m(M_PLAIN_B, ECO_B, U_PLAIN, "mod"),  # plain is mod in eco B only
        m(M_BOOT_B, ECO_B, U_BOOT, "user", profile="co_creator", created_at=FOUNDED),  # eco B's founder
        m(M_TARGET_B, ECO_B, U_TARGET, "user"),
        m(M_ROGUE_B, ECO_B, U_ROGUE, "user", profile="co_creator"),
    ])
    await session.commit()


def _create_app(auth_member_id: uuid.UUID | None, auth_user_id: uuid.UUID | None,
                profile: str | None = None, role: str = "user"):
    """API-blueprint app with ctx.member + ctx.user injection."""
    app = Sanic(f"test-roles-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()

    @app.on_request
    async def inject_auth(request):
        if auth_member_id is None:
            return
        request.ctx.member = Member(
            id=auth_member_id, ecosystem_id=ECO_A, user_id=auth_user_id,
            member_id="MEM-AUTH", display_name="Auth User",
            current_status="active", profile=profile, role=role,
        )
        request.ctx.user = User(id=auth_user_id, display_name="Auth User")
        request.ctx.selected_ecosystem_ids = [ECO_A, ECO_B]
        request.ctx.authorized_ecosystem_ids = [ECO_A, ECO_B]

    register_api_errors(app)
    app.blueprint(members_api_bp)
    return app


async def _db(app):
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.ctx.db = sf
    async with sf() as session:
        await _seed(session)
    return engine


# ---------------------------------------------------------------------------
# Rank ordering (unit)
# ---------------------------------------------------------------------------
def test_role_rank_ordering():
    assert ROLE_RANK["user"] < ROLE_RANK["mod"] < ROLE_RANK["admin"] < ROLE_RANK["owner"]


# ---------------------------------------------------------------------------
# PUT /members/<id>/role grant rules
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_owner_grants_admin():
    app = _create_app(M_OWNER, U_OWNER, role="owner")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "admin"})
    assert resp.status == 200, resp.text
    assert resp.json["role"] == "admin"
    await engine.dispose()


@pytest.mark.asyncio
async def test_admin_cannot_grant_owner():
    app = _create_app(M_ADMIN, U_ADMIN, role="admin")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "owner"})
    assert resp.status == 403
    await engine.dispose()


@pytest.mark.asyncio
async def test_admin_cannot_touch_other_admin():
    app = _create_app(M_ADMIN, U_ADMIN, role="admin")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_OWNER}/role", json={"role": "user"})
    assert resp.status == 403
    await engine.dispose()


@pytest.mark.asyncio
async def test_admin_grants_mod_to_user():
    app = _create_app(M_ADMIN, U_ADMIN, role="admin")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "mod"})
    assert resp.status == 200, resp.text
    assert resp.json["role"] == "mod"
    await engine.dispose()


@pytest.mark.asyncio
async def test_plain_user_forbidden():
    app = _create_app(M_PLAIN, U_PLAIN, role="user")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "mod"})
    assert resp.status == 403
    await engine.dispose()


@pytest.mark.asyncio
async def test_bootstrap_profile_admin_grants_only_while_there_is_no_owner():
    app = _create_app(M_BOOT, U_BOOT, profile="co_creator", role="user")
    engine = await _db(app)
    # Eco A already has an owner: the co_creator profile is an ordinary member there.
    _, refused = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "owner"})
    assert refused.status == 403
    # Eco B has none: the profile designates the first owner, and then the bootstrap ends.
    _, first = await app.asgi_client.put(f"/api/v1/members/{M_TARGET_B}/role", json={"role": "owner"})
    assert (first.status, first.json["role"]) == (200, "owner"), first.text
    _, after = await app.asgi_client.put(f"/api/v1/members/{M_PLAIN_B}/role", json={"role": "admin"})
    assert after.status == 403
    await engine.dispose()


@pytest.mark.parametrize("caller_member, caller_user, target, expected", [
    (M_BOOT_B, U_BOOT, M_TARGET_B, 200),  # the founder designates the first owner
    (M_ROGUE_B, U_ROGUE, M_ROGUE_B, 403),  # a later co_creator cannot make themselves owner...
    (M_ROGUE_B, U_ROGUE, M_TARGET_B, 403),  # ...nor anyone else
])
@pytest.mark.asyncio
async def test_only_the_founder_bootstraps_an_ownerless_ecosystem(caller_member, caller_user, target, expected):
    app = _create_app(caller_member, caller_user, profile="co_creator")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{target}/role", json={"role": "owner"})
    assert resp.status == expected, resp.text
    _, after = await app.asgi_client.get(f"/api/v1/members/{target}")
    assert after.json["role"] == ("owner" if expected == 200 else "user")
    await engine.dispose()


@pytest.mark.parametrize("profile, allowed", [("builder", False), ("co_creator", False), ("collaborator", True)])
@pytest.mark.asyncio
async def test_members_never_give_themselves_an_authority_profile(profile, allowed):
    """Ownerless eco B: a self-chosen builder profile used to unlock the bootstrap, then owner."""
    app = _create_app(M_TARGET_B, U_TARGET)
    engine = await _db(app)
    _, edited = await app.asgi_client.put(f"/api/v1/members/{M_TARGET_B}", json={"profile": profile})
    _, escalated = await app.asgi_client.put(f"/api/v1/members/{M_TARGET_B}/role", json={"role": "owner"})
    _, after = await app.asgi_client.get(f"/api/v1/members/{M_TARGET_B}/profile")
    assert escalated.status == 403
    assert (after.json["profile"], after.json["role"], after.json["role_history"]) == (
        profile if allowed else None, "user", [])
    if not allowed:
        assert (edited.status, edited.json["error"]) == (403, PROFILE_GRANT_ONLY)
    await engine.dispose()


@pytest.mark.parametrize("profile, expected", [("builder", 403), ("co_creator", 403), ("collaborator", 201)])
@pytest.mark.asyncio
async def test_joining_with_an_authority_profile_is_refused(profile, expected):
    app = _create_app(M_ADMIN, U_ADMIN, role="admin")  # no row in eco B yet: POST /members creates the caller's own
    engine = await _db(app)
    _, created = await app.asgi_client.post("/api/v1/members", json={
        "ecosystem_id": str(ECO_B), "display_name": "Admin in B", "profile": profile,
    })
    assert created.status == expected, created.text
    _, listed = await app.asgi_client.get("/api/v1/members", params={"q": "Admin in B"})
    assert listed.json["total"] == (1 if expected == 201 else 0)
    await engine.dispose()


@pytest.mark.parametrize("caller_member, caller_user, role, target, expected", [
    (M_OWNER, U_OWNER, "owner", M_TARGET, 200),  # whoever could make them an admin
    (M_ADMIN, U_ADMIN, "admin", M_TARGET, 403),  # admins cannot mint admins, nor admin profiles
    (M_OWNER, U_OWNER, "owner", M_OWNER, 403),  # never your own
    (M_BOOT_B, U_BOOT, "user", M_TARGET_B, 200),  # the founder, before eco B has an owner
])
@pytest.mark.asyncio
async def test_authority_profiles_are_granted_and_recorded(caller_member, caller_user, role, target, expected):
    app = _create_app(caller_member, caller_user, role=role)
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{target}/profile-grant", json={"profile": "builder"})
    assert resp.status == expected, resp.text
    _, after = await app.asgi_client.get(f"/api/v1/members/{target}/profile")
    if expected == 403:
        assert resp.json["error"] == PROFILE_GRANT_DENIED
        assert (after.json["profile"], after.json["role_history"]) == (None, [])
    else:
        [grant] = after.json["role_history"]
        assert (after.json["profile"], grant["kind"], grant["to_role"], grant["granted_by"]) == (
            "builder", "profile", "builder", f"M{caller_member.hex[:4]}")
    await engine.dispose()


@pytest.mark.asyncio
async def test_every_grant_is_recorded_and_the_picker_follows_the_rule():
    app = _create_app(M_ADMIN, U_ADMIN, role="admin")
    engine = await _db(app)
    _, granted = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "mod"})
    assert granted.status == 200, granted.text
    # The granter is stored by member id: a later rename shows, an edited name cannot rewrite history.
    _, renamed = await app.asgi_client.put(f"/api/v1/members/{M_ADMIN}", json={"display_name": "Ada Admin"})
    assert renamed.status == 200, renamed.text
    _, profile = await app.asgi_client.get(f"/api/v1/members/{M_TARGET}/profile")
    assert profile.status == 200, profile.text
    [grant] = profile.json["role_history"]
    assert (grant["kind"], grant["from_role"], grant["to_role"], grant["granted_by"]) == ("role", "user", "mod", "Ada Admin")
    assert profile.json["caller_grantable_profiles"] == []  # an admin cannot grant admin-conferring profiles
    assert profile.json["caller_assignable_roles"] == ["user"]  # an admin may only move a mod below admin
    _, owner_view = await app.asgi_client.get(f"/api/v1/members/{M_OWNER}/profile")
    assert owner_view.json["caller_assignable_roles"] == []  # never a member at or above your rank
    _, own = await app.asgi_client.get(f"/api/v1/members/{M_ADMIN}/profile")
    assert (own.json["caller_is_self"], own.json["caller_assignable_roles"]) == (True, ["user", "mod"])  # step down only
    await engine.dispose()


@pytest.mark.asyncio
async def test_per_ecosystem_isolation():
    """Mod in eco B is a plain user in eco A: role grants in A must fail."""
    app = _create_app(M_PLAIN, U_PLAIN, role="user")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "mod"})
    assert resp.status == 403
    await engine.dispose()


@pytest.mark.asyncio
async def test_self_demotion_allowed():
    app = _create_app(M_ADMIN, U_ADMIN, role="admin")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_ADMIN}/role", json={"role": "user"})
    assert resp.status == 200, resp.text
    assert resp.json["role"] == "user"
    await engine.dispose()


@pytest.mark.asyncio
async def test_unknown_member_404():
    app = _create_app(M_OWNER, U_OWNER, role="owner")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{uuid.uuid4()}/role", json={"role": "mod"})
    assert resp.status == 404
    await engine.dispose()


# ---------------------------------------------------------------------------
# Enforcement swaps
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_member_other_requires_mod():
    app = _create_app(M_PLAIN, U_PLAIN, role="user")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(
        f"/api/v1/members/{M_TARGET}", json={"display_name": "Hijack"})
    assert resp.status == 403
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_member_self_ok():
    app = _create_app(M_PLAIN, U_PLAIN, role="user")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(
        f"/api/v1/members/{M_PLAIN}", json={"display_name": "Myself"})
    assert resp.status == 200, resp.text
    assert resp.json["display_name"] == "Myself"
    await engine.dispose()


@pytest.mark.asyncio
async def test_status_transition_requires_mod():
    app = _create_app(M_PLAIN, U_PLAIN, role="user")
    engine = await _db(app)
    _, resp = await app.asgi_client.post(
        f"/api/v1/members/{M_TARGET}/status", json={"status": "inactive"})
    assert resp.status == 403
    await engine.dispose()


@pytest.mark.asyncio
async def test_status_transition_as_mod_ok():
    # G-Onboard: moves come from policy.MEMBER_MOVES; active -> inactive is not one (active -> suspended is).
    app = _create_app(M_MOD, U_MOD, role="mod")
    engine = await _db(app)
    _, resp = await app.asgi_client.post(
        f"/api/v1/members/{M_TARGET}/status", json={"status": "suspended"})
    assert resp.status == 200, resp.text
    assert resp.json["current_status"] == "suspended"
    await engine.dispose()
