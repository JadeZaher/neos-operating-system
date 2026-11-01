"""Emergency flows through the real blueprint: co-signed declaration, bounded timer, Recovery you can finish.

Rules: src/neos_agent/api/AGENTS.md "Emergency and exit". The test middleware resolves the caller's
memberships from the database the way main._load_ecosystems does (active rows authorize).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.api import emergency as emergency_api
from neos_agent.api.emergency import MAX_AUTHORITY_DAYS, emergency_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.db.models import Base, Ecosystem, EmergencyState, Member, User
from neos_agent.services.cron import _auto_revert_emergencies
from neos_agent.views.emergency import emergency_bp as legacy_emergency_bp

OASIS = uuid.UUID(int=0x0A)
DELTA = uuid.UUID(int=0x0D)

# name -> {ecosystem: (status, role)}; the first active ecosystem is the selection.
PEOPLE = {
    "ada": {OASIS: ("active", "mod")},  # steward
    "ben": {OASIS: ("active", "user")},
    "cy": {OASIS: ("active", "user")},
    "dee": {OASIS: ("active", "user")},
    "eve": {OASIS: ("pending_consent", "user")},
    "fay": {DELTA: ("active", "user")},
    "gus": {OASIS: ("active", "user"), DELTA: ("active", "user")},
}


def _user(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"emergency.{name}")


def _row(name: str, ecosystem: uuid.UUID) -> uuid.UUID:
    return uuid.uuid5(_user(name), str(ecosystem))


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _seed(factory) -> None:
    async with factory() as session:
        session.add_all([Ecosystem(id=OASIS, name="Oasis", status="active"),
                         Ecosystem(id=DELTA, name="Delta", status="active")])
        session.add_all([User(id=_user(name), display_name=name.title()) for name in PEOPLE])
        await session.flush()
        for name, rows in PEOPLE.items():
            for ecosystem, (status, role) in rows.items():
                session.add(Member(
                    id=_row(name, ecosystem), ecosystem_id=ecosystem, user_id=_user(name),
                    member_id=f"MEM-{name}-{ecosystem.int}", display_name=name.title(),
                    current_status=status, role=role,
                ))
        await session.commit()


def _app(factory) -> Sanic:
    app = Sanic(f"test-emergency-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        async with factory() as session:
            rows = (await session.execute(
                select(Member).where(Member.user_id == _user(who)).order_by(Member.created_at)
            )).scalars().all()
        authorized = [row.ecosystem_id for row in rows if row.current_status == "active"]
        request.ctx.user = User(id=_user(who), display_name=who.title())
        request.ctx.member = next((row for row in rows if row.current_status == "active"), rows[0])
        request.ctx.authorized_ecosystem_ids = authorized
        request.ctx.selected_ecosystem_ids = authorized[:1]

    app.blueprint(emergency_api_bp)
    app.blueprint(legacy_emergency_bp)
    return app


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await _seed(factory)
    yield SimpleNamespace(app=_app(factory), db=factory)
    await engine.dispose()


async def _post(env, who: str, path: str, body: dict | None = None):
    _, response = await env.app.asgi_client.post(f"/api/v1/emergency{path}", headers={"x-test-as": who}, json=body or {})
    return response


async def _get(env, who: str, path: str):
    _, response = await env.app.asgi_client.get(f"/api/v1/emergency{path}", headers={"x-test-as": who})
    return response


async def _declare(env, who: str = "ben", ecosystem: uuid.UUID = OASIS, **body):
    payload = {"ecosystem_id": str(ecosystem), "reason": "The river is flooding the garden.", **body}
    return await _post(env, who, "/declare", payload)


async def _stored(env, emergency_id) -> EmergencyState:
    async with env.db() as session:
        return await session.get(EmergencyState, uuid.UUID(str(emergency_id)))


async def _open(env, declarer: str = "ben", cosigner: str = "cy", **body) -> str:
    declared = await _declare(env, declarer, **body)
    assert declared.status == 201, declared.text
    cosigned = await _post(env, cosigner, f"/{declared.json['id']}/cosign")
    assert cosigned.status == 200, cosigned.text
    return declared.json["id"]


async def _age(env, emergency_id, **changes) -> None:
    async with env.db() as session:
        row = await session.get(EmergencyState, uuid.UUID(str(emergency_id)))
        for field, value in changes.items():
            setattr(row, field, value)
        await session.commit()


# --- Owner decision: any ACTIVE member declares; a second active member co-signs ---


@pytest.mark.parametrize("who, status", [
    ("ben", 201),   # a plain member: goes red if declaring becomes steward-only
    ("ada", 201),   # a steward
    ("eve", 403),   # pending consent is not active
    ("fay", 403),   # active, but in another ecosystem
])
async def test_who_may_declare(env, who, status):
    response = await _declare(env, who)
    assert response.status == status, response.text
    if status == 201:
        assert (response.json["state"], response.json["phase"]) == ("pending", "pending")
        assert response.json["auto_revert_at"] is None  # no authority, no timer, until co-signed


async def test_declaration_opens_only_when_a_second_active_member_cosigns(env):
    declared = await _declare(env, "ben", declared_by="Mallory", auto_revert_days=5)
    emergency_id = declared.json["id"]
    assert declared.json["declared_by"] == "Ben"  # from the caller, never the body
    assert declared.json["caller_can_cosign"] is False and declared.json["caller_can_withdraw"] is True

    own = await _post(env, "ben", f"/{emergency_id}/cosign")
    assert own.status == 403 and "second member" in own.json["error"]
    outsider = await _post(env, "fay", f"/{emergency_id}/cosign")
    assert outsider.status == 404  # another ecosystem's record does not exist for her
    assert (await _stored(env, emergency_id)).state == "pending"

    cosigned = await _post(env, "cy", f"/{emergency_id}/cosign")
    assert cosigned.status == 200
    stored = await _stored(env, emergency_id)
    assert (stored.state, stored.co_signed_by, stored.co_signer_member_id) == ("open", "Cy", _row("cy", OASIS))
    assert stored.auto_revert_at - stored.co_signed_at == timedelta(days=5)  # the timer starts at co-sign
    again = await _post(env, "dee", f"/{emergency_id}/cosign")
    assert again.status == 409


@pytest.mark.parametrize("body, status, stored_days", [
    ({}, 201, 7),                                                # omitted: the default
    ({"auto_revert_days": MAX_AUTHORITY_DAYS}, 201, MAX_AUTHORITY_DAYS),
    ({"auto_revert_days": MAX_AUTHORITY_DAYS + 1}, 400, None),  # the ceiling; 3650 days used to be accepted
    ({"auto_revert_days": 0}, 400, None),
    ({"auto_revert_days": "ten"}, 400, None),
    ({"reason": "   "}, 400, None),                              # a reason is required
])
async def test_the_timer_is_bounded_and_a_reason_required(env, body, status, stored_days):
    response = await _declare(env, "ben", **body)
    assert response.status == status, response.text
    if status == 201:
        assert response.json["authority_days"] == stored_days


async def test_one_live_emergency_per_ecosystem_and_a_lapsed_declaration_does_not_block(env):
    first = await _declare(env, "ben")
    duplicate = await _declare(env, "cy")
    assert duplicate.status == 409 and duplicate.json["emergency_id"] == first.json["id"]
    await _age(env, first.json["id"], declared_at=_now() - timedelta(hours=49))
    lapsed = await _get(env, "dee", f"/{first.json['id']}")
    assert lapsed.json["phase"] == "withdrawn" and lapsed.json["caller_can_cosign"] is False
    assert (await _post(env, "dee", f"/{first.json['id']}/cosign")).status == 409
    fresh = await _declare(env, "cy")
    assert fresh.status == 201
    assert (await _stored(env, first.json["id"])).state == "withdrawn"


def _row_in(ecosystem: uuid.UUID, state: str) -> EmergencyState:
    return EmergencyState(id=uuid.uuid4(), ecosystem_id=ecosystem, state=state, declared_at=_now(), actions_log=[])


async def test_the_database_holds_one_live_emergency_per_ecosystem(env):
    """What two concurrent declarations race into: the partial unique index refuses the second live row."""
    await _open(env)
    async with env.db() as session:
        session.add_all([_row_in(OASIS, "closed"), _row_in(OASIS, "withdrawn"), _row_in(DELTA, "pending")])
        await session.commit()  # finished rows, and a live one elsewhere, are fine
        for state in ("pending", "open", "half_open"):
            session.add(_row_in(OASIS, state))
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()


async def test_cosign_refuses_while_another_emergency_is_live(env):
    """Belt and braces for a database without the index: co-signing never makes a second live emergency."""
    declared = await _declare(env, "ben")
    async with env.db() as session:
        await session.execute(text("DROP INDEX uq_emergency_states_one_live"))
        stray = _row_in(OASIS, "open")
        session.add(stray)
        await session.commit()
    refused = await _post(env, "cy", f"/{declared.json['id']}/cosign")
    assert refused.status == 409 and refused.json["emergency_id"] == str(stray.id)
    assert (await _stored(env, declared.json["id"])).state == "pending"


@pytest.mark.parametrize("who, status", [("ben", 200), ("ada", 200), ("cy", 403), ("dee", 403)])
async def test_who_may_withdraw_a_pending_declaration(env, who, status):
    declared = await _declare(env, "ben")
    response = await _post(env, who, f"/{declared.json['id']}/withdraw")
    assert response.status == status, response.text
    assert (await _stored(env, declared.json["id"])).state == ("withdrawn" if status == 200 else "pending")


# --- Ending authority and Recovery ------------------------------------------


@pytest.mark.parametrize("who, status", [
    ("ben", 200),  # declarer
    ("cy", 200),   # co-signer
    ("ada", 200),  # steward
    ("dee", 403),  # anyone else waits for the timer
])
async def test_who_may_end_emergency_authority_early(env, who, status):
    emergency_id = await _open(env)
    response = await _post(env, who, f"/{emergency_id}/resolve")
    assert response.status == status, response.text
    stored = await _stored(env, emergency_id)
    assert stored.state == ("half_open" if status == 200 else "open")
    assert stored.closed_at is None  # ending authority never skips Recovery


async def test_recovery_is_finished_by_an_independent_review_and_a_steward(env):
    emergency_id = await _open(env, "ben", "cy")
    ended = await _post(env, "ben", f"/{emergency_id}/resolve")
    assert ended.json["phase"] == "recovery" and ended.json["review_due_at"] is not None

    too_early = await _post(env, "ada", f"/{emergency_id}/complete-recovery")
    assert too_early.status == 409 and too_early.json["next_step"].startswith("Schedule")

    for actor in ("ben", "cy"):  # declarer (who also ended it) and co-signer
        refused = await _post(env, actor, f"/{emergency_id}/review", {"outcome": "complete", "summary": "Fine."})
        assert refused.status == 403, actor
    assert (await _post(env, "dee", f"/{emergency_id}/review", {"outcome": "complete", "summary": " "})).status == 400

    scheduled = await _post(env, "dee", f"/{emergency_id}/review", {"outcome": "scheduled", "summary": "Circle on the 12th."})
    assert scheduled.json["post_review_status"] == "scheduled"
    assert (await _post(env, "ada", f"/{emergency_id}/complete-recovery")).status == 409

    reviewed = await _post(env, "dee", f"/{emergency_id}/review",
                           {"outcome": "complete", "summary": "Decisions stayed in scope."})
    assert reviewed.json["post_review_status"] == "complete"
    assert reviewed.json["caller_can_complete_recovery"] is False  # dee is not a steward

    assert (await _post(env, "dee", f"/{emergency_id}/complete-recovery")).status == 403
    closed = await _post(env, "ada", f"/{emergency_id}/complete-recovery")
    assert (closed.status, closed.json["state"], closed.json["phase"]) == (200, "closed", "closed")
    actions = [entry["action"] for entry in closed.json["actions_log"]]
    assert actions == ["declared", "co_signed", "half_open_transition", "review_recorded", "review_recorded",
                       "recovery_completed"]


async def test_recovery_past_its_window_shows_review_overdue_to_stewards_and_never_auto_closes(env):
    emergency_id = await _open(env)
    await _post(env, "ben", f"/{emergency_id}/resolve")
    await _age(env, emergency_id, half_open_entered_at=_now() - timedelta(days=31))
    await _auto_revert_emergencies(env.app)

    steward_view = await _get(env, "ada", f"/{emergency_id}")
    assert (steward_view.json["state"], steward_view.json["review_overdue"]) == ("half_open", True)
    assert steward_view.json["caller_is_steward"] is True
    assert steward_view.json["next_step"].startswith("Review overdue.")
    banner = await _get(env, "ada", "/active")
    assert [item["id"] for item in banner.json["items"]] == [emergency_id]  # still live: no auto-close


# --- Cron: the timer and the co-sign window --------------------------------


async def test_cron_starts_recovery_when_the_timer_runs_out_and_lapses_unsigned_declarations(env):
    open_id = await _open(env, "ben", "cy")
    await _age(env, open_id, auto_revert_at=_now() - timedelta(minutes=1))
    pending = await _declare(env, "fay", DELTA)
    await _age(env, pending.json["id"], declared_at=_now() - timedelta(hours=49))

    await _auto_revert_emergencies(env.app)
    reverted, lapsed = await _stored(env, open_id), await _stored(env, pending.json["id"])
    assert (reverted.state, reverted.closed_at) == ("half_open", None)
    assert reverted.actions_log[-1]["trigger"] == "auto_revert_timer"
    assert lapsed.state == "withdrawn"

    await _auto_revert_emergencies(env.app)  # a second sweep changes nothing
    assert len((await _stored(env, open_id)).actions_log) == len(reverted.actions_log)


# --- Everyone can see it: the banner feed and the dashboard -------------------


async def test_the_banner_lists_live_emergencies_in_every_ecosystem_the_member_is_active_in(env):
    declared = await _declare(env, "fay", DELTA)
    delta_id = declared.json["id"]
    await _post(env, "gus", f"/{delta_id}/cosign")
    oasis_id = await _open(env, "ben", "cy")  # Oasis: open, then fully closed more recently
    await _post(env, "ben", f"/{oasis_id}/resolve")
    await _post(env, "dee", f"/{oasis_id}/review", {"outcome": "complete", "summary": "Done."})
    await _post(env, "ada", f"/{oasis_id}/complete-recovery")

    both = await _get(env, "gus", "/active")  # selection is Oasis only; the banner still shows Delta
    assert [(item["id"], item["ecosystem_name"], item["phase"]) for item in both.json["items"]] == [
        (delta_id, "Delta", "open"),
    ]
    oasis_only = await _get(env, "ben", "/active")
    assert oasis_only.json["items"] == []

    dashboard = await _get(env, "ben", "/")  # a plain member reads the page; Oasis may declare again
    assert dashboard.json["active"] == [] and dashboard.json["caller_can_declare_in"] == [str(OASIS)]
    assert dashboard.json["limits"]["max_authority_days"] == MAX_AUTHORITY_DAYS


async def test_a_pending_declaration_is_on_the_banner_so_a_co_signer_can_find_it(env):
    declared = await _declare(env, "ben")
    banner = await _get(env, "dee", "/active")
    [item] = banner.json["items"]
    assert (item["id"], item["phase"], item["caller_can_cosign"]) == (declared.json["id"], "pending", True)
    dashboard = await _get(env, "dee", "/")
    assert dashboard.json["caller_can_declare_in"] == []  # blocked by the pending one


# --- The legacy dashboard can no longer skip Recovery -------------------------


async def test_legacy_dashboard_routes_change_nothing(env):
    emergency_id = await _open(env)
    _, resolve = await env.app.asgi_client.post(
        f"/dashboard/emergency/{emergency_id}/resolve", headers={"x-test-as": "ada"})
    _, declare = await env.app.asgi_client.post(
        "/dashboard/emergency/declare", headers={"x-test-as": "ada"}, data={"ecosystem_id": str(DELTA)})
    assert (resolve.status, declare.status) == (410, 410)
    assert (await _stored(env, emergency_id)).state == "open"
    async with env.db() as session:
        assert len((await session.execute(select(EmergencyState))).scalars().all()) == 1


async def test_the_state_check_rejects_unknown_states(env):
    async with env.db() as session:
        session.add(EmergencyState(id=uuid.uuid4(), ecosystem_id=OASIS, state="resolved", actions_log=[]))
        with pytest.raises(IntegrityError):
            await session.commit()


def test_describe_uses_the_recovery_start_not_the_authority_deadline():
    now = _now()
    row = SimpleNamespace(
        state="half_open", declared_at=now - timedelta(days=9), auto_revert_at=now + timedelta(days=20),
        half_open_entered_at=now - timedelta(days=2), recovery_entered_at=None, post_review_status=None,
    )
    timeline = emergency_api.describe(row, now)
    assert timeline["review_due_at"] == (now - timedelta(days=2) + timedelta(days=30)).isoformat()
    assert timeline["authority_ends_at"] is None and timeline["review_overdue"] is False
