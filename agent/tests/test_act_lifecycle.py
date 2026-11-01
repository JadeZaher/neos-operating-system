"""BE-ACT: the declarative ACT lifecycle, its transition hook, and agreement scoping over REST.

Rules: src/neos_agent/services/AGENTS.md "ACT lifecycle" and
src/neos_agent/api/AGENTS.md "Handler contracts" rule 5 (agreement exemption).
Proposal flows reuse the governance fixture; agreement flows seed a consent-gated
newcomer and a shared agreement of their own.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.agreements import CEREMONY_DENIED, agreements_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.db.models import Agreement, Base, ConsentParticipant, ConsentRecord, Ecosystem, Member, Proposal, User
from neos_agent.services import act_gates
from neos_agent.services.act_gates import AGREEMENT_LIFECYCLE, PROPOSAL_LIFECYCLE, STEWARD_MOVE_DENIED
from neos_agent.services.agreement_consent import synchronize_agreement_requirements

from .test_uxqa_p1_governance import _call, _create_proposal, env  # noqa: F401 — env is the shared fixture


# ---------------------------------------------------------------------------
# The tables
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lifecycle, current, target, allowed", [
    (PROPOSAL_LIFECYCLE, "created", "advice", True),  # legacy chat drafts open like drafts
    (PROPOSAL_LIFECYCLE, "advice", "test", False),  # no stage is skipped by hand
    (PROPOSAL_LIFECYCLE, "consent", "withdrawn", True),
    (AGREEMENT_LIFECYCLE, "consent", "active", False),  # activation needs the test ceremony
    (AGREEMENT_LIFECYCLE, "under_review", "active", True),
    (AGREEMENT_LIFECYCLE, "advice", "withdrawn", False),  # agreements sunset instead
])
def test_manual_moves_follow_the_table(lifecycle, current, target, allowed):
    assert (lifecycle.manual_move(current, target) is not None) is allowed


# ---------------------------------------------------------------------------
# The transition hook and the owner's pending decisions
# ---------------------------------------------------------------------------


async def test_on_transition_sees_each_applied_move_once(env, monkeypatch):
    seen = []
    monkeypatch.setattr(act_gates, "_TRANSITION_LISTENERS", [])

    @act_gates.on_transition
    async def record(session, transition):
        seen.append((transition.source, transition.target, transition.automatic, transition.actor.display_name))

    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    assert (await _call(env.app, "post", "ben", f"{url}/status", json={"status": "advice"})).status == 403
    assert (await _call(env.app, "post", "ada", f"{url}/status", json={"status": "advice"})).status == 200
    assert (await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})).status == 201

    assert seen == [("draft", "advice", False, "Ada"), ("advice", "consent", True, "Ben")]


def _owner_decided_lifecycle():
    """The owner's decisions as the one-line table edits the comments in act_gates.py describe."""
    edits = {
        ("advice", "consent"): {"automatic": False},
        ("test", "ratified"): {"automatic": False, "steward_only": True},
    }
    moves = tuple(replace(move, **edits.get((move.source, move.target), {})) for move in PROPOSAL_LIFECYCLE.moves)
    return replace(PROPOSAL_LIFECYCLE, moves=moves)


async def test_owner_decisions_are_table_edits(env, monkeypatch):
    monkeypatch.setattr(act_gates, "PROPOSAL_LIFECYCLE", _owner_decided_lifecycle())
    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    await _call(env.app, "post", "ada", f"{url}/status", json={"status": "advice"})

    # Advice stays open until the proposer closes it.
    advice = await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})
    assert advice.json["auto_transitions"] == []
    closed = await _call(env.app, "post", "ada", f"{url}/status", json={"status": "consent"})
    assert closed.json["status"] == "consent"

    consent = await _call(env.app, "post", "ben", f"{url}/consent", json={"member_name": "Ben", "position": "consent"})
    assert consent.json["auto_transitions"] == ["consent->test"]
    report = await _call(env.app, "post", "ben", f"{url}/test", json={"outcome": "passed", "observations": "Ran a week"})
    assert report.json["auto_transitions"] == []

    # Ratification waits for a steward, and a manual ratification mints the decision artifact.
    by_author = await _call(env.app, "post", "ada", f"{url}/status", json={"status": "ratified"})
    assert (by_author.status, by_author.json["error"]) == (403, STEWARD_MOVE_DENIED)
    by_steward = await _call(env.app, "post", "mo", f"{url}/status", json={"status": "ratified"})
    assert by_steward.json["status"] == "ratified"
    assert by_steward.json["decision_record_id"]


async def test_a_legacy_objection_spelling_blocks_the_consent_gate(env):
    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    await _call(env.app, "post", "ada", f"{url}/status", json={"status": "advice"})
    await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})
    # A chat row stored before positions were normalized (migration o7c3e9a5d2f8 rewrites the lowercase ones).
    async with env.db() as session:
        record = ConsentRecord(id=uuid.uuid4(), proposal_id=uuid.UUID(proposal["id"]), consent_mode="consent")
        session.add(record)
        await session.flush()
        session.add(ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name="Mo",
                                       position=" Objection", reason="Too noisy at night"))
        await session.commit()

    consent = await _call(env.app, "post", "sol", f"{url}/consent", json={"member_name": "Sol", "position": "consent"})
    assert consent.status == 201, consent.text
    assert (consent.json["gates"]["consent"]["open_objections"], consent.json["auto_transitions"]) == (1, [])
    async with env.db() as session:
        assert (await session.get(Proposal, uuid.UUID(proposal["id"]))).status == "consent"


# ---------------------------------------------------------------------------
# Agreements over REST: consent-gate scope, shared rows, ceremonies
# ---------------------------------------------------------------------------

OASIS = uuid.UUID(int=0xA1)
RIVER = uuid.UUID(int=0xA2)
AGREEMENTS = {key: uuid.uuid5(uuid.NAMESPACE_DNS, f"be-act.{key}") for key in ("uaf", "shared", "river", "draft")}
MEMBERS = {
    # who: (ecosystem, role, status)
    "ada": (OASIS, "user", "active"),
    "ari": (OASIS, "admin", "active"),
    "nia": (OASIS, "user", "pending_consent"),  # only membership waits on the consent gate
    "olu": (RIVER, "user", "active"),
}


def _user_id(who: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"be-act.{who}")


async def _seed_agreements(session: AsyncSession) -> None:
    session.add_all([Ecosystem(id=OASIS, name="Oasis", status="active"), Ecosystem(id=RIVER, name="River", status="active")])
    for who, (ecosystem, role, status) in MEMBERS.items():
        session.add(User(id=_user_id(who), display_name=who.title()))
    await session.flush()
    for who, (ecosystem, role, status) in MEMBERS.items():
        session.add(Member(
            id=uuid.uuid5(_user_id(who), "member"), ecosystem_id=ecosystem, user_id=_user_id(who),
            member_id=f"MEM-{who}", display_name=who.title(), role=role, current_status=status,
        ))
    rows = {
        "uaf": dict(ecosystem_id=OASIS, status="active", prerequisite_scopes=["ecosystem"]),
        "shared": dict(ecosystem_id=RIVER, status="active", shared_ecosystem_ids=[str(OASIS)]),
        "river": dict(ecosystem_id=RIVER, status="active"),
        "draft": dict(ecosystem_id=OASIS, status="draft"),
    }
    for key, fields in rows.items():
        agreement = Agreement(
            id=AGREEMENTS[key], agreement_id=f"AGR-{key.upper()}", type="uaf", title=f"{key} agreement",
            version="1.0", proposer="Ari", text="Terms.", requires_explicit_consent=True, alignment_points=5,
            **fields,
        )
        session.add(agreement)
        await session.flush()
        await synchronize_agreement_requirements(session, agreement)
    await session.commit()


def _agreements_app(factory) -> Sanic:
    app = Sanic(f"test-be-act-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        ecosystem, role, status = MEMBERS[who]
        request.ctx.user = User(id=_user_id(who), display_name=who.title())
        request.ctx.member = Member(
            id=uuid.uuid5(_user_id(who), "member"), ecosystem_id=ecosystem, user_id=_user_id(who),
            member_id=f"MEM-{who}", display_name=who.title(), role=role, current_status=status,
        )
        authorized = [ecosystem] if status == "active" else []
        request.ctx.authorized_ecosystem_ids = authorized
        request.ctx.selected_ecosystem_ids = authorized

    app.blueprint(agreements_api_bp)
    return app


@pytest_asyncio.fixture
async def agreements():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed_agreements(session)
    yield SimpleNamespace(app=_agreements_app(factory), db=factory)
    await engine.dispose()


def _agreement_url(key: str, path: str = "") -> str:
    return f"/api/v1/agreements/{AGREEMENTS[key]}{path}"


async def test_pending_newcomer_reads_and_consents_from_the_gate(agreements):
    assert (await _call(agreements.app, "get", "nia", _agreement_url("uaf"))).status == 200
    assert (await _call(agreements.app, "get", "nia", _agreement_url("uaf", "/history"))).status == 200
    consent = await _call(agreements.app, "post", "nia", _agreement_url("uaf", "/consent"),
                          json={"attestation": "I have read this and consent."})
    assert consent.status == 201, consent.text
    async with agreements.db() as session:
        nia = await session.scalar(select(Member).where(Member.user_id == _user_id("nia")))
    assert nia.current_status == "active"
    assert (await _call(agreements.app, "get", "nia", _agreement_url("river"))).status == 404


async def test_a_listed_shared_agreement_opens_but_only_its_owners_edit_it(agreements):
    listed = (await _call(agreements.app, "get", "ada", "/api/v1/agreements")).json
    assert str(AGREEMENTS["shared"]) in {item["id"] for item in listed["items"]}
    detail = await _call(agreements.app, "get", "ada", _agreement_url("shared"))
    assert detail.status == 200
    assert detail.json["caller_can_conduct"] is False
    edit = await _call(agreements.app, "put", "ada", _agreement_url("shared"), json={"title": "Taken over"})
    assert edit.status == 403


async def test_consent_on_another_ecosystems_agreement_is_not_found(agreements):
    resp = await _call(agreements.app, "post", "ada", _agreement_url("river", "/consent"),
                       json={"attestation": "I have read this and consent."})
    assert (resp.status, resp.json) == (404, {"error": "Agreement not found"})


async def test_agreement_ceremonies_run_through_the_engine(agreements):
    status_url = _agreement_url("draft", "/status")
    by_member = await _call(agreements.app, "post", "ada", status_url, json={"status": "advice", "evidence": "Opening advice"})
    assert (by_member.status, by_member.json["error"]) == (403, CEREMONY_DENIED)
    thin = await _call(agreements.app, "post", "ari", status_url, json={"status": "advice", "evidence": "go"})
    assert thin.status == 400
    opened = await _call(agreements.app, "post", "ari", status_url, json={"status": "advice", "evidence": "Opening advice"})
    assert (opened.status, opened.json["status"], opened.json["auto_transitions"]) == (200, "advice", [])

    early = await _call(agreements.app, "post", "ari", status_url, json={"status": "consent", "evidence": "Closing advice"})
    assert early.status == 409
    assert early.json["gates"]["advice"]["met"] is False

    round_recorded = await _call(agreements.app, "post", "ada", _agreement_url("draft", "/ceremonies"),
                                 json={"stage": "advice", "note": "Round one with the garden circle"})
    assert round_recorded.status == 201, round_recorded.text
    assert (round_recorded.json["status"], round_recorded.json["auto_transitions"]) == ("consent", ["advice->consent"])
    history = (await _call(agreements.app, "get", "ada", _agreement_url("draft", "/history"))).json
    reasons = [version["change_reason"] for version in history["versions"]]
    assert "Auto-advanced by ACT gate engine: advice->consent" in reasons
    assert "Status transition: draft -> advice" in reasons


async def test_agreement_list_rejects_a_non_numeric_page(agreements):
    resp = await _call(agreements.app, "get", "ada", "/api/v1/agreements?page=abc")
    assert resp.status == 400
