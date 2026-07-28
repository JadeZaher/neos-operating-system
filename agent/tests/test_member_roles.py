"""Tests for per-ecosystem role tiers (user/mod/admin/owner).

Covers ROLE_RANK ordering, PUT /api/v1/members/<id>/role grant rules
(owner any, admin user/mod only, self-demotion, profile-admin bootstrap),
per-ecosystem isolation, and the mod-gate enforcement swaps on
update_member and member_status_transition.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.helpers import ROLE_RANK
from neos_agent.api.members import members_api_bp
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

M_OWNER = uuid.uuid4()
M_ADMIN = uuid.uuid4()
M_MOD = uuid.uuid4()
M_PLAIN = uuid.uuid4()
M_TARGET = uuid.uuid4()
M_BOOT = uuid.uuid4()
M_PLAIN_B = uuid.uuid4()  # plain user's eco-B membership (mod there)


async def _seed(session: AsyncSession) -> None:
    session.add(Ecosystem(id=ECO_A, name="Eco A", status="active"))
    session.add(Ecosystem(id=ECO_B, name="Eco B", status="active"))
    for uid, name in [(U_OWNER, "Owner"), (U_ADMIN, "Admin"), (U_MOD, "Mod"),
                      (U_PLAIN, "Plain"), (U_TARGET, "Target"), (U_BOOT, "Boot")]:
        session.add(User(id=uid, display_name=name))
    await session.flush()

    def m(mid, eco, uid, role, profile=None):
        return Member(
            id=mid, ecosystem_id=eco, user_id=uid,
            member_id=f"MEM-{mid.hex[:6].upper()}", display_name=f"M{mid.hex[:4]}",
            current_status="active", profile=profile, role=role,
        )

    session.add_all([
        m(M_OWNER, ECO_A, U_OWNER, "owner"),
        m(M_ADMIN, ECO_A, U_ADMIN, "admin"),
        m(M_MOD, ECO_A, U_MOD, "mod"),
        m(M_PLAIN, ECO_A, U_PLAIN, "user"),
        m(M_TARGET, ECO_A, U_TARGET, "user"),
        m(M_BOOT, ECO_A, U_BOOT, "user", profile="co_creator"),  # bootstrap: profile-admin, role user
        m(M_PLAIN_B, ECO_B, U_PLAIN, "mod"),  # plain is mod in eco B only
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
async def test_bootstrap_profile_admin_grants():
    app = _create_app(M_BOOT, U_BOOT, profile="co_creator", role="user")
    engine = await _db(app)
    _, resp = await app.asgi_client.put(f"/api/v1/members/{M_TARGET}/role", json={"role": "owner"})
    assert resp.status == 200, resp.text
    assert resp.json["role"] == "owner"
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
    app = _create_app(M_MOD, U_MOD, role="mod")
    engine = await _db(app)
    _, resp = await app.asgi_client.post(
        f"/api/v1/members/{M_TARGET}/status", json={"status": "inactive"})
    assert resp.status == 200, resp.text
    assert resp.json["current_status"] == "inactive"
    await engine.dispose()
