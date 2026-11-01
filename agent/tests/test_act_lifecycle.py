"""BE-ACT: the declarative ACT lifecycle, its transition hook, and agreement scoping over REST.

Rules: src/neos_agent/services/AGENTS.md "ACT lifecycle" and
src/neos_agent/api/AGENTS.md "Handler contracts" rule 5 (agreement exemption).
Proposal flows reuse the governance fixture; agreement flows seed a consent-gated
newcomer and a shared agreement of their own.
"""

from __future__ import annotations

import datetime as dt
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.agreements import CEREMONY_DENIED, agreements_api_bp
from neos_agent.api.policy import can_confirm_ratification
from neos_agent.api.errors import register_api_errors
from neos_agent.db.models import Agreement, Base, ConsentParticipant, ConsentRecord, Ecosystem, Member, Proposal, User
from neos_agent.services import act_gates
from neos_agent.services.act_gates import (
    ADVICE_CLOSE_PROPOSER_ONLY,
    AGREEMENT_LIFECYCLE,
    MANAGE_DENIED,
    NEEDS_ANOTHER_STEWARD,
    PROPOSAL_LIFECYCLE,
    STEWARD_MOVE_DENIED,
)
from neos_agent.services.agreement_consent import synchronize_agreement_requirements

from .test_uxqa_p1_governance import LEGACY_PROPOSAL, _call, _create_proposal, env  # noqa: F401 — env is the shared fixture


# ---------------------------------------------------------------------------
# The tables
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lifecycle, current, target, allowed", [
    (PROPOSAL_LIFECYCLE, "created", "advice", True),  # legacy chat drafts open like drafts
    (PROPOSAL_LIFECYCLE, "advice", "test", False),  # no stage is skipped by hand
    (PROPOSAL_LIFECYCLE, "consent", "withdrawn", True),
    (PROPOSAL_LIFECYCLE, "ratified", "withdrawn", False),  # terminal: a decided proposal stays decided
    (PROPOSAL_LIFECYCLE, "withdrawn", "withdrawn", False),
    (PROPOSAL_LIFECYCLE, "consent", "advice", True),  # send back for revision
    (PROPOSAL_LIFECYCLE, "test", "advice", True),
    (AGREEMENT_LIFECYCLE, "consent", "active", False),  # activation needs the test ceremony
    (AGREEMENT_LIFECYCLE, "under_review", "active", True),
    (AGREEMENT_LIFECYCLE, "advice", "withdrawn", False),  # agreements sunset instead
])
def test_manual_moves_follow_the_table(lifecycle, current, target, allowed):
    assert (lifecycle.manual_move(current, target) is not None) is allowed


# ---------------------------------------------------------------------------
# The transition hook and the owner's decisions (live since 2026-10-31)
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
    assert (await _call(env.app, "post", "ada", f"{url}/status", json={"status": "consent"})).status == 200

    assert seen == [("draft", "advice", False, "Ada"), ("advice", "consent", False, "Ada")]


def test_owner_decisions_are_live_in_the_table():
    """Flipping an owner decision back (automatic advice close, a steward closing advice any time,
    self-certifying ratification) goes red here."""
    advice_close = PROPOSAL_LIFECYCLE.manual_move("advice", "consent")
    ratification = PROPOSAL_LIFECYCLE.manual_move("test", "ratified")
    assert (advice_close.automatic, advice_close.gate, advice_close.proposer_until_deadline) == (False, "advice", True)
    assert (ratification.automatic, ratification.steward_only, ratification.gate) == (False, True, "test")
    assert PROPOSAL_LIFECYCLE.automatic_move("advice") is None
    assert PROPOSAL_LIFECYCLE.automatic_move("test") is None

    # ...and the confirming steward is never the author (no self-certified ratification).
    home = uuid.UUID(int=0xE1)
    author_steward, other_steward = (Member(id=uuid.uuid4(), ecosystem_id=home, role=role, current_status="active")
                                     for role in ("mod", "admin"))
    own = Proposal(ecosystem_id=home, proposer_member_id=author_steward.id)
    legacy = Proposal(ecosystem_id=home, proposer_member_id=None)  # no author link: steward-managed
    assert can_confirm_ratification(author_steward, own) is False
    assert can_confirm_ratification(other_steward, own) is True
    assert can_confirm_ratification(author_steward, legacy) is True


async def test_owner_decisions_proposer_closes_advice_and_a_steward_confirms_ratification(env):
    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    await _call(env.app, "post", "ada", f"{url}/status", json={"status": "advice"})

    # Advice stays open until the proposer closes it; the detail offers her the move once the gate is met.
    advice = await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})
    assert advice.json["auto_transitions"] == []
    as_proposer = (await _call(env.app, "get", "ada", url)).json
    assert (as_proposer["status"], _next(as_proposer, "consent")) == ("advice", {"ready": True, "gate": "advice", "blocked": None})
    assert _next((await _call(env.app, "get", "ben", url)).json, "consent") is None  # not his to close
    closed = await _call(env.app, "post", "ada", f"{url}/status", json={"status": "consent"})
    assert (closed.json["status"], closed.json["auto_transitions"]) == ("consent", [])

    consent = await _call(env.app, "post", "ben", f"{url}/consent", json={"position": "consent"})
    assert consent.json["auto_transitions"] == ["consent->test"]
    report = await _call(env.app, "post", "ben", f"{url}/test", json={"outcome": "passed", "observations": "Ran a week"})
    assert report.json["auto_transitions"] == []  # a report is evidence, never self-certifying

    # The author is offered no ratify button and is refused; a steward sees the reports and confirms.
    as_author = (await _call(env.app, "get", "ada", url)).json
    assert _next(as_author, "ratified") == {"ready": True, "gate": "test", "blocked": "needs_another_steward"}
    by_author = await _call(env.app, "post", "ada", f"{url}/status", json={"status": "ratified"})
    assert (by_author.status, by_author.json["error"]) == (403, STEWARD_MOVE_DENIED)
    as_steward = (await _call(env.app, "get", "mo", url)).json
    assert _next(as_steward, "ratified") == {"ready": True, "gate": "test", "blocked": None}
    assert [r["reporter_name"] for r in as_steward["test_reports"]] == ["Ben"]
    by_steward = await _call(env.app, "post", "mo", f"{url}/status", json={"status": "ratified"})
    assert by_steward.json["status"] == "ratified"
    assert by_steward.json["decision_record_id"]


def _next(detail: dict, target: str) -> dict | None:
    """The caller's offered manual move into `target` (ready, gate, blocked), or None when not offered."""
    move = next((m for m in detail["allowed_next"] if m["to"] == target), None)
    return None if move is None else {key: move[key] for key in ("ready", "gate", "blocked")}


async def test_a_steward_who_wrote_the_proposal_cannot_confirm_its_ratification(env):
    proposal = await _create_proposal(env.app, who="mo")  # Mo is a steward and the author
    url = f"/api/v1/proposals/{proposal['id']}"
    for who, path, body in (
        ("mo", "/status", {"status": "advice"}),
        ("ben", "/advice", {"content": "Add a rota"}),
        ("mo", "/status", {"status": "consent"}),
        ("ben", "/consent", {"position": "consent"}),
        ("sol", "/test", {"outcome": "passed", "observations": "Ran a week"}),
    ):
        assert (await _call(env.app, "post", who, f"{url}{path}", json=body)).status in (200, 201)

    as_author = (await _call(env.app, "get", "mo", url)).json
    assert _next(as_author, "ratified")["blocked"] == "needs_another_steward"  # the page names who decides
    refused = await _call(env.app, "post", "mo", f"{url}/status", json={"status": "ratified"})
    assert (refused.status, refused.json["code"], refused.json["error"]) == (403, "NEEDS_ANOTHER_STEWARD", NEEDS_ANOTHER_STEWARD)
    confirmed = await _call(env.app, "post", "ari", f"{url}/status", json={"status": "ratified"})
    assert confirmed.json["status"] == "ratified", confirmed.text


# ---------------------------------------------------------------------------
# Who closes advice (owner decision 2026-11-01): the proposer; another steward only after the deadline
# ---------------------------------------------------------------------------

TODAY = dt.date.today()
NO_DEADLINE, TOMORROW, DEADLINE_TODAY, YESTERDAY = None, TODAY + dt.timedelta(days=1), TODAY, TODAY - dt.timedelta(days=1)


@pytest.mark.parametrize("who, deadline, status, refusal", [
    ("ada", NO_DEADLINE, 200, None),  # the proposer closes whenever she chooses
    ("ada", TOMORROW, 200, None),
    ("ada", YESTERDAY, 200, None),
    ("mo", NO_DEADLINE, 403, "This proposal has no advice deadline, so only they can close it."),
    ("mo", TOMORROW, 403, f"You can close it after the advice deadline ({TOMORROW.isoformat()}) if they haven't."),
    ("mo", DEADLINE_TODAY, 403, f"after the advice deadline ({TODAY.isoformat()})"),  # a deadline passes the next day
    ("mo", YESTERDAY, 200, None),  # the absent proposer: a steward closes it for her
    ("ben", YESTERDAY, 403, MANAGE_DENIED),  # never a member who neither wrote it nor stewards
])
async def test_a_steward_closes_someone_elses_advice_only_after_its_deadline(env, who, deadline, status, refusal):
    fields = {"advice_deadline": deadline.isoformat()} if deadline else {}
    proposal = await _create_proposal(env.app, **fields)
    url = f"/api/v1/proposals/{proposal['id']}"
    assert (await _call(env.app, "post", "ada", f"{url}/status", json={"status": "advice"})).status == 200
    assert (await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})).status == 201

    closed = await _call(env.app, "post", who, f"{url}/status", json={"status": "consent"})
    assert closed.status == status, closed.text
    if status == 200:
        assert closed.json["status"] == "consent"
    elif refusal == MANAGE_DENIED:
        assert closed.json["error"] == MANAGE_DENIED
    else:
        assert closed.json["code"] == ADVICE_CLOSE_PROPOSER_ONLY
        assert closed.json["error"].startswith("The proposer closes advice.") and refusal in closed.json["error"]
        assert closed.json["advice_deadline"] == (deadline.isoformat() if deadline else None)
        # The page still lists the move for the steward, blocked, so it can say who decides.
        detail = (await _call(env.app, "get", who, url)).json
        assert (detail["status"], _next(detail, "consent")) == (
            "advice", {"ready": True, "gate": "advice", "blocked": "proposer_closes_advice"})


async def test_stewards_still_close_advice_on_a_legacy_proposal_with_no_author_to_act(env):
    url = f"/api/v1/proposals/{LEGACY_PROPOSAL}"  # seeded in advice; its proposer text is Ben, no author link
    assert (await _call(env.app, "post", "sol", f"{url}/advice", json={"content": "Keep it short"})).status == 201
    assert (await _call(env.app, "post", "ben", f"{url}/status", json={"status": "consent"})).status == 403
    assert _next((await _call(env.app, "get", "mo", url)).json, "consent")["blocked"] is None
    closed = await _call(env.app, "post", "mo", f"{url}/status", json={"status": "consent"})
    assert (closed.status, closed.json["status"]) == (200, "consent"), closed.text


# Owner decision 2026-11-01 (no behaviour change): the author's own consent position counts toward the quorum.
async def test_the_authors_own_consent_counts_toward_the_quorum(env):
    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    for who, path, body in (
        ("ada", "/status", {"status": "advice"}),
        ("ben", "/advice", {"content": "Add a rota"}),
        ("ada", "/status", {"status": "consent"}),
    ):
        assert (await _call(env.app, "post", who, f"{url}{path}", json=body)).status in (200, 201)

    own = await _call(env.app, "post", "ada", f"{url}/consent", json={"position": "consent"})
    assert own.status == 201, own.text
    assert (own.json["auto_transitions"], own.json["gates"]["consent"]["positions"]) == (["consent->test"], 1)


async def test_a_legacy_objection_spelling_blocks_the_consent_gate(env):
    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    await _call(env.app, "post", "ada", f"{url}/status", json={"status": "advice"})
    await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})
    await _call(env.app, "post", "ada", f"{url}/status", json={"status": "consent"})
    # A chat row stored before positions were normalized (migration o7c3e9a5d2f8 rewrites the lowercase ones).
    async with env.db() as session:
        record = ConsentRecord(id=uuid.uuid4(), proposal_id=uuid.UUID(proposal["id"]), consent_mode="consent")
        session.add(record)
        await session.flush()
        session.add(ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name="Mo",
                                       position=" Objection", reason="Too noisy at night"))
        await session.commit()

    consent = await _call(env.app, "post", "sol", f"{url}/consent", json={"position": "consent"})
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
