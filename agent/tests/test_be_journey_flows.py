"""BE-Journey flows: per-ecosystem journey/ethos/chat state keyed on the caller's row, and exit-record scoping.

Rules: src/neos_agent/api/AGENTS.md "Handler contracts". Real blueprints on a bare Sanic app;
x-test-as picks the caller, whose request.ctx.member is the DEFAULT row (not necessarily the
ecosystem a route names).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.api.chat import chat_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.ethos_access import ethos_access_api_bp
from neos_agent.api.exit import exit_api_bp
from neos_agent.api.orientation import orientation_api_bp
from neos_agent.db.models import (
    AgentSession, Base, Ecosystem, EthosUserAccess, ExitRecord, JourneyMap, Member, User, UserJourneyProgress,
)

OASIS = uuid.UUID(int=1)
OMNIONE = uuid.UUID(int=2)
ELSEWHERE = uuid.UUID(int=3)


@dataclass(frozen=True)
class Person:
    user_id: uuid.UUID
    rows: dict[uuid.UUID, str]  # ecosystem -> membership status
    default_ecosystem: uuid.UUID  # where request.ctx.member lives
    selected: tuple[uuid.UUID, ...]


def _member_id(user_id: uuid.UUID, ecosystem_id: uuid.UUID) -> uuid.UUID:
    return uuid.uuid5(user_id, str(ecosystem_id))


PEOPLE = {
    # Member in both; the session default row is OmniOne and the picker selects only it.
    "sam": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "journey.sam"), {OASIS: "active", OMNIONE: "active"}, OMNIONE, (OMNIONE,)),
    # Same two rows, both selected, default row Oasis.
    "kit": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "journey.kit"), {OASIS: "active", OMNIONE: "active"}, OASIS, (OASIS, OMNIONE)),
    # Only row awaits the consent gate: nothing authorized, nothing selected.
    "nia": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "journey.nia"), {OASIS: "pending_consent"}, OASIS, ()),
    "bo": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "journey.bo"), {ELSEWHERE: "active"}, ELSEWHERE, (ELSEWHERE,)),
    # Left Oasis (the row stays, exited); active elsewhere.
    "eli": Person(uuid.uuid5(uuid.NAMESPACE_DNS, "journey.eli"), {OASIS: "exited", ELSEWHERE: "active"}, ELSEWHERE, (ELSEWHERE,)),
}
MISSING_ECOSYSTEM = uuid.UUID(int=99)
JOURNEY_MAP_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "journey.map")
OMNIONE_MAP_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "journey.map.omnione")  # G-Onboard: progress takes only its ecosystem's journeys
OASIS_EXIT = uuid.uuid5(uuid.NAMESPACE_DNS, "journey.exit.oasis")
OMNIONE_EXIT = uuid.uuid5(uuid.NAMESPACE_DNS, "journey.exit.omnione")
SAM_OASIS = _member_id(PEOPLE["sam"].user_id, OASIS)
SAM_OMNIONE = _member_id(PEOPLE["sam"].user_id, OMNIONE)


async def _seed(session: AsyncSession) -> None:
    session.add_all([Ecosystem(id=eco, name=name, status="active") for eco, name in
                     ((OASIS, "Oasis"), (OMNIONE, "OmniOne"), (ELSEWHERE, "Elsewhere"))])
    for key, person in PEOPLE.items():
        session.add(User(id=person.user_id, display_name=key.title()))
    await session.flush()
    for key, person in PEOPLE.items():
        for ecosystem_id, status in person.rows.items():
            session.add(Member(
                id=_member_id(person.user_id, ecosystem_id), ecosystem_id=ecosystem_id, user_id=person.user_id,
                member_id=f"MEM-{key}-{ecosystem_id.int}", display_name=key.title(), role="user", current_status=status,
            ))
    session.add(JourneyMap(id=JOURNEY_MAP_ID, slug="welcome", title="Welcome", ecosystem_id=OASIS, content_sequence=[], step_count=0))
    session.add(JourneyMap(id=OMNIONE_MAP_ID, slug="welcome", title="Welcome", ecosystem_id=OMNIONE, content_sequence=[], step_count=0))
    session.add_all([
        ExitRecord(id=OASIS_EXIT, ecosystem_id=OASIS, member_id=SAM_OASIS, exit_type="standard", status="declared"),
        ExitRecord(id=OMNIONE_EXIT, ecosystem_id=OMNIONE, member_id=SAM_OMNIONE, exit_type="standard", status="declared"),
    ])
    await session.commit()


def _app(session_factory) -> Sanic:
    app = Sanic(f"test-be-journey-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = session_factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        person = PEOPLE[who]
        request.ctx.user = User(id=person.user_id, display_name=who.title())
        request.ctx.member = Member(
            id=_member_id(person.user_id, person.default_ecosystem), ecosystem_id=person.default_ecosystem,
            user_id=person.user_id, member_id="MEM-SESSION", display_name=who.title(),
            role="user", current_status=person.rows[person.default_ecosystem],
        )
        request.ctx.authorized_ecosystem_ids = [eco for eco, status in person.rows.items() if status == "active"]
        request.ctx.selected_ecosystem_ids = list(person.selected)

    for blueprint in (orientation_api_bp, ethos_access_api_bp, exit_api_bp, chat_api_bp):
        app.blueprint(blueprint)
    return app


@pytest_asyncio.fixture
async def journey():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
    yield SimpleNamespace(app=_app(factory), db=factory)
    await engine.dispose()


def _as(who: str) -> dict:
    return {"x-test-as": who}


# --- Orientation progress: one record per (caller row, ecosystem) -------------


async def test_journey_progress_lands_on_the_member_row_of_the_ecosystem_it_names(journey):
    # Sam's session default is his OmniOne row; the orientation he is walking belongs to Oasis.
    _, saved = await journey.app.asgi_client.post(
        f"/api/v1/orientation/ethos/{OASIS}/progress", headers=_as("sam"),
        json={"journey_map_id": str(JOURNEY_MAP_ID), "current_step": 2, "status": "in_progress"},
    )
    assert saved.status == 200, saved.text
    assert saved.json["user_id"] == str(SAM_OASIS)

    _, oasis_progress = await journey.app.asgi_client.get(f"/api/v1/orientation/ethos/{OASIS}/progress", headers=_as("sam"))
    assert oasis_progress.json["current_step"] == 2
    assert oasis_progress.json["user_id"] == str(SAM_OASIS)

    # The other ecosystem starts empty and keeps its own record on its own row.
    _, omnione_progress = await journey.app.asgi_client.get(f"/api/v1/orientation/ethos/{OMNIONE}/progress", headers=_as("sam"))
    assert omnione_progress.json == {}
    _, omnione_saved = await journey.app.asgi_client.post(
        f"/api/v1/orientation/ethos/{OMNIONE}/progress", headers=_as("sam"),
        json={"journey_map_id": str(OMNIONE_MAP_ID), "current_step": 1, "status": "in_progress"},
    )
    assert omnione_saved.json["user_id"] == str(SAM_OMNIONE)
    async with journey.db() as session:
        rows = (await session.execute(select(UserJourneyProgress))).scalars().all()
    assert {(row.ecosystem_id, row.member_id, row.current_step) for row in rows} == {
        (OASIS, SAM_OASIS, 2), (OMNIONE, SAM_OMNIONE, 1),
    }


async def test_beginning_another_ecosystems_orientation_asks_the_caller_to_join_first(journey):
    # Bo is a member of Elsewhere only; Oasis is public and exists.
    _, response = await journey.app.asgi_client.post(
        f"/api/v1/orientation/ethos/{OASIS}/progress", headers=_as("bo"),
        json={"journey_map_id": str(JOURNEY_MAP_ID), "current_step": 1},
    )
    assert (response.status, response.json) == (
        409, {"error": "Join this ecosystem to begin its orientation", "code": "JOIN_REQUIRED"},
    )
    _, read = await journey.app.asgi_client.get(f"/api/v1/orientation/ethos/{OASIS}/progress", headers=_as("bo"))
    assert read.json == {}
    async with journey.db() as session:
        assert (await session.execute(select(UserJourneyProgress))).scalars().all() == []

    _, unknown = await journey.app.asgi_client.post(
        f"/api/v1/orientation/ethos/{MISSING_ECOSYSTEM}/progress", headers=_as("bo"),
        json={"journey_map_id": str(JOURNEY_MAP_ID), "current_step": 1},
    )
    assert (unknown.status, unknown.json) == (404, {"error": "Ecosystem not found"})


async def test_once_joined_the_same_begin_records_progress_on_the_new_row(journey):
    # The client's join-first step: POST /ecosystems/:id/join creates the row (pending consent here).
    bo_oasis = _member_id(PEOPLE["bo"].user_id, OASIS)
    async with journey.db() as session:
        session.add(Member(
            id=bo_oasis, ecosystem_id=OASIS, user_id=PEOPLE["bo"].user_id, member_id="MEM-bo-oasis",
            display_name="Bo", role="user", current_status="pending_consent",
        ))
        await session.commit()
    _, response = await journey.app.asgi_client.post(
        f"/api/v1/orientation/ethos/{OASIS}/progress", headers=_as("bo"),
        json={"journey_map_id": str(JOURNEY_MAP_ID), "current_step": 0, "status": "in_progress"},
    )
    assert response.status == 200, response.text
    assert response.json["user_id"] == str(bo_oasis)


# --- Ethos access: consent is recorded for the caller's row in that ethos ---


async def test_ethos_consent_is_recorded_per_ecosystem_and_asks_a_non_member_to_join(journey):
    _, consented = await journey.app.asgi_client.post(f"/api/v1/ethos/{OASIS}/access/consent", headers=_as("sam"))
    assert consented.status == 201, consented.text
    _, oasis_status = await journey.app.asgi_client.get(f"/api/v1/ethos/{OASIS}/access/me", headers=_as("sam"))
    _, omnione_status = await journey.app.asgi_client.get(f"/api/v1/ethos/{OMNIONE}/access/me", headers=_as("sam"))
    assert oasis_status.json["has_access"] is True
    assert omnione_status.json["has_access"] is False  # sam's default row is OmniOne and holds no grant
    async with journey.db() as session:
        grant = (await session.execute(select(EthosUserAccess))).scalar_one()
    assert grant.member_id == SAM_OASIS

    _, refused = await journey.app.asgi_client.post(f"/api/v1/ethos/{OASIS}/access/consent", headers=_as("bo"))
    assert (refused.status, refused.json["code"]) == (409, "JOIN_REQUIRED")
    _, unknown = await journey.app.asgi_client.post(f"/api/v1/ethos/{MISSING_ECOSYSTEM}/access/consent", headers=_as("bo"))
    assert (unknown.status, unknown.json) == (404, {"error": "Ethos not found"})
    async with journey.db() as session:
        assert len((await session.execute(select(EthosUserAccess))).scalars().all()) == 1  # still only Sam's


# --- Exit records: detail and status match the list's visibility, fail closed -


@pytest.mark.parametrize("who, exit_id, status", [
    ("sam", OASIS_EXIT, 200),      # authorized in Oasis though the picker selects only OmniOne: deep links open
    ("sam", OMNIONE_EXIT, 200),
    ("bo", OASIS_EXIT, 404),       # another ecosystem's record
    ("nia", OASIS_EXIT, 404),      # memberless scope used to open every record (fail-open `if eco_ids:`)
    ("nia", OMNIONE_EXIT, 404),
])
async def test_exit_detail_and_status_are_scoped_to_the_callers_authorized_ecosystems(journey, who, exit_id, status):
    _, detail = await journey.app.asgi_client.get(f"/api/v1/exit/{exit_id}", headers=_as(who))
    assert detail.status == status, detail.text
    _, transition = await journey.app.asgi_client.post(
        f"/api/v1/exit/{exit_id}/status", headers=_as(who), json={"new_status": "cancelled"},  # the leaver's own move
    )
    assert transition.status == status, transition.text
    if status == 404:
        assert detail.json == {"error": "Exit record not found"}
        async with journey.db() as session:
            assert (await session.get(ExitRecord, exit_id)).status == "declared"  # the write never happened


async def test_exit_list_with_an_empty_selection_is_empty_and_junk_paging_is_a_400(journey):
    _, nobody = await journey.app.asgi_client.get("/api/v1/exit/", headers=_as("nia"))
    assert nobody.status == 200 and nobody.json["items"] == [] and nobody.json["total"] == 0
    _, selected = await journey.app.asgi_client.get("/api/v1/exit/", headers=_as("sam"))
    assert [item["id"] for item in selected.json["items"]] == [str(OMNIONE_EXIT)]
    _, junk = await journey.app.asgi_client.get("/api/v1/exit/?page=abc", headers=_as("sam"))
    assert junk.status == 400


# --- Shared chat privacy: membership is looked up in the session's ecosystem --


async def test_ecosystem_shared_chat_opens_for_a_member_whose_default_row_is_elsewhere(journey):
    async with journey.db() as session:
        session.add(AgentSession(
            id=uuid.uuid4(), ecosystem_id=OASIS, member_id=_member_id(PEOPLE["kit"].user_id, OASIS), title="Plan",
            privacy="ecosystem", share_token="tok-eco", context={"messages": [{"role": "user", "content": "hi"}]},
        ))
        await session.commit()
    # Sam's default row is OmniOne, but he also belongs to Oasis.
    _, member = await journey.app.asgi_client.get("/api/v1/chat/shared/tok-eco", headers=_as("sam"))
    assert member.status == 200, member.text
    _, outsider = await journey.app.asgi_client.get("/api/v1/chat/shared/tok-eco", headers=_as("bo"))
    assert outsider.status == 403
    _, anonymous = await journey.app.asgi_client.get("/api/v1/chat/shared/tok-eco")
    assert anonymous.status == 403
    # Eli still has an Oasis row, but exited: only active members read an ecosystem-shared chat.
    _, former = await journey.app.asgi_client.get("/api/v1/chat/shared/tok-eco", headers=_as("eli"))
    assert former.status == 403


async def test_chat_sessions_belong_to_the_callers_rows_across_their_ecosystems(journey):
    kit_oasis = _member_id(PEOPLE["kit"].user_id, OASIS)
    kit_omnione = _member_id(PEOPLE["kit"].user_id, OMNIONE)
    omnione_session = uuid.uuid4()
    async with journey.db() as session:
        session.add_all([
            AgentSession(id=uuid.uuid4(), ecosystem_id=OASIS, member_id=kit_oasis, title="Oasis chat", context={"messages": []}),
            AgentSession(id=omnione_session, ecosystem_id=OMNIONE, member_id=kit_omnione, title="OmniOne chat", context={"messages": []}),
        ])
        await session.commit()
    # Kit's default row is Oasis; both ecosystems are selected, so both histories list and open.
    _, listed = await journey.app.asgi_client.get("/api/v1/chat/sessions", headers=_as("kit"))
    assert {item["title"] for item in listed.json["sessions"]} == {"Oasis chat", "OmniOne chat"}
    _, opened = await journey.app.asgi_client.get(f"/api/v1/chat/sessions/{omnione_session}", headers=_as("kit"))
    assert opened.status == 200
    # Another user, even in the same ecosystem, never opens it.
    _, others = await journey.app.asgi_client.get(f"/api/v1/chat/sessions/{omnione_session}", headers=_as("sam"))
    assert others.status == 404


async def test_a_member_active_nowhere_still_reaches_only_their_own_chat_sessions(journey):
    # Nia's only row awaits consent, so nothing is authorized or selected.
    nia_session = uuid.uuid4()
    kit_session = uuid.uuid4()
    async with journey.db() as session:
        session.add_all([
            AgentSession(id=nia_session, ecosystem_id=OASIS, member_id=_member_id(PEOPLE["nia"].user_id, OASIS),
                         title="Nia's questions", context={"messages": []}),
            AgentSession(id=kit_session, ecosystem_id=OASIS, member_id=_member_id(PEOPLE["kit"].user_id, OASIS),
                         title="Kit's plan", context={"messages": []}),
        ])
        await session.commit()
    _, listed = await journey.app.asgi_client.get("/api/v1/chat/sessions", headers=_as("nia"))
    assert [item["title"] for item in listed.json["sessions"]] == ["Nia's questions"]
    _, own = await journey.app.asgi_client.get(f"/api/v1/chat/sessions/{nia_session}", headers=_as("nia"))
    assert own.status == 200
    _, other = await journey.app.asgi_client.get(f"/api/v1/chat/sessions/{kit_session}", headers=_as("nia"))
    assert other.status == 404
