"""G-ACT: ACT integrity flows through the real proposals, agreements, members and onboarding blueprints.

Rules: src/neos_agent/api/AGENTS.md "ACT integrity (G-ACT)" and services/AGENTS.md "ACT lifecycle".
People come from the pass-01 governance fixture: Ada authors, Ben and Sol take part, Mo is
a steward (mod), Ari an admin, Olu belongs to another ecosystem.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import importlib.util
import os
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.agreements import agreements_api_bp, register_ratified_proposal
from neos_agent.api.errors import ApiError, register_api_errors
from neos_agent.api.onboarding import ONBOARDING_CONSENT_DENIED, onboarding_api_bp
from neos_agent.api.proposals import MANAGE_DENIED, PROPOSAL_LOCKED, proposals_api_bp
from neos_agent.db.models import (
    Agreement,
    Base,
    ConsentParticipant,
    ConsentRecord,
    Ecosystem,
    Member,
    MemberOnboarding,
    Proposal,
    User,
)
from neos_agent.services.act_gates import (
    CONSENT_CLOSED,
    NEEDS_ANOTHER_STEWARD,
    NO_POSITION_TO_WITHDRAW,
    NOTE_REQUIRED,
    OBJECTION_REASON_REQUIRED,
    PARTICIPATE_DENIED,
    STAND_ASIDE_IN_CONSENSUS,
)

from .test_uxqa_p1_governance import ECO, GARDEN_AGREEMENT, LEGACY_PROPOSAL, OLU, PEOPLE, RIVER, _seed

RULES_AGREEMENT = uuid.UUID("0000000a-0000-0000-0000-0000000000a2")  # active, consent quorum 2


def _app(factory) -> Sanic:
    app = Sanic(f"test-g-act-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        p, home = (OLU, RIVER) if who == "olu" else (PEOPLE[who], ECO)
        request.ctx.member = Member(
            id=p.member_id, ecosystem_id=home, user_id=p.user_id, member_id="MEM-AUTH",
            display_name=p.name, current_status="active", role=p.role,
        )
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = [home]
        request.ctx.authorized_ecosystem_ids = [home]

    for blueprint in (proposals_api_bp, agreements_api_bp, onboarding_api_bp):
        app.blueprint(blueprint)
    return app


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
        session.add(Agreement(
            id=RULES_AGREEMENT, ecosystem_id=ECO, agreement_id="AGR-RULES", type="protocol",
            title="How we decide", version="1.0", status="active", proposer="Ari", text="Two voices decide.",
            act_policy={"min_advice_rounds": 1, "consent_required": True, "consent_quorum": 2, "test_cases": []},
        ))
        await session.commit()
    yield SimpleNamespace(app=_app(factory), db=factory)
    await engine.dispose()


async def _call(env, method: str, who: str, url: str, **kwargs):
    _, resp = await getattr(env.app.asgi_client, method)(url, headers={"x-test-as": who}, **kwargs)
    return resp


async def _proposal(env, **fields) -> str:
    body = {"ecosystem_id": str(ECO), "type": "policy", "title": "Evening garden hours",
            "proposed_change": "The garden opens until nine.", **fields}
    resp = await _call(env, "post", "ada", "/api/v1/proposals", json=body)
    assert resp.status == 201, resp.text
    return f"/api/v1/proposals/{resp.json['id']}"


async def _to_consent(env, url: str) -> None:
    """Open advice, take Ben's advice, and let Ada (the proposer) close advice."""
    for who, path, body in (
        ("ada", "/status", {"status": "advice"}),
        ("ben", "/advice", {"content": "Add a rota"}),
        ("ada", "/status", {"status": "consent"}),
    ):
        resp = await _call(env, "post", who, f"{url}{path}", json=body)
        assert resp.status in (200, 201), resp.text


async def _ratified(env, url: str) -> None:
    await _to_consent(env, url)
    consented = await _call(env, "post", "ben", f"{url}/consent", json={"position": "consent"})
    assert consented.json["auto_transitions"] == ["consent->test"], consented.text
    report = await _call(env, "post", "sol", f"{url}/test", json={"outcome": "passed", "observations": "Ran a week"})
    assert report.status == 201, report.text
    ratified = await _call(env, "post", "mo", f"{url}/status", json={"status": "ratified"})
    assert ratified.json["status"] == "ratified", ratified.text


async def _detail(env, url: str, who: str = "ada") -> dict:
    return (await _call(env, "get", who, url)).json


async def _rows(env) -> list[tuple]:
    async with env.db() as session:
        rows = (await session.execute(
            select(ConsentParticipant.name, ConsentParticipant.position).order_by(ConsentParticipant.created_at)
        )).all()
    return [tuple(row) for row in rows]


# ---------------------------------------------------------------------------
# Consent: the caller's one position, objections and their authors
# ---------------------------------------------------------------------------


async def test_one_position_per_member_and_changing_it_replaces_it(env):
    url = await _proposal(env)
    await _to_consent(env, url)

    # The body names someone else; the position is the caller's.
    objected = await _call(env, "post", "ben", f"{url}/consent",
                           json={"member_name": "Oren", "position": "object", "objection_text": "Too late at night"})
    assert objected.status == 201, objected.text
    assert objected.json["gates"]["consent"]["open_objections"] == 1
    assert (await _detail(env, url, "ben"))["caller_position"] == {"position": "object", "reason": "Too late at night"}

    # Ben changes his mind: the objection is gone, the gate is met, nothing is counted twice.
    consented = await _call(env, "post", "ben", f"{url}/consent", json={"position": "consent"})
    assert (consented.json["gates"]["consent"]["open_objections"], consented.json["auto_transitions"]) == (0, ["consent->test"])
    assert await _rows(env) == [("Ben", "consent")]


@pytest.mark.parametrize("body, status, error", [
    ({"position": "object"}, 400, OBJECTION_REASON_REQUIRED),
    ({"position": "object", "objection_text": "   "}, 400, OBJECTION_REASON_REQUIRED),
    ({"position": "maybe"}, 400, "Choose consent, stand aside or object"),
])
async def test_positions_use_one_vocabulary(env, body, status, error):
    url = await _proposal(env)
    await _to_consent(env, url)
    resp = await _call(env, "post", "ben", f"{url}/consent", json=body)
    assert (resp.status, resp.json["error"]) == (status, error)
    assert await _rows(env) == []


async def test_an_objection_is_lifted_only_by_its_author(env):
    url = await _proposal(env)
    await _to_consent(env, url)
    await _call(env, "post", "ben", f"{url}/consent", json={"position": "object", "objection_text": "Noise"})
    await _call(env, "post", "sol", f"{url}/consent", json={"position": "consent"})

    # Sol withdrawing withdraws Sol's own position; Ben's objection still blocks.
    sol = await _call(env, "delete", "sol", f"{url}/consent")
    assert (sol.status, sol.json["gates"]["consent"]["open_objections"]) == (200, 1)
    again = await _call(env, "delete", "sol", f"{url}/consent")
    assert (again.status, again.json["error"]) == (404, NO_POSITION_TO_WITHDRAW)
    assert (await _detail(env, url))["status"] == "consent"

    # Ben withdraws his objection: it stays in the record as withdrawn, and the gate is no longer blocked.
    ben = await _call(env, "delete", "ben", f"{url}/consent")
    assert ben.json["gates"]["consent"]["open_objections"] == 0
    assert await _rows(env) == [("Ben", "withdrawn"), ("Sol", "withdrawn")]


async def _legacy_position(env, url: str, name: str, position: str, reason: str | None = None) -> None:
    """A pre-G-ACT row in the latest consent record: a display name, no member_id."""
    proposal_id = uuid.UUID(url.rsplit("/", 1)[1])
    async with env.db() as session:
        record = await session.scalar(select(ConsentRecord).where(ConsentRecord.proposal_id == proposal_id))
        if record is None:
            record = ConsentRecord(id=uuid.uuid4(), proposal_id=proposal_id, consent_mode="consent")
            session.add(record)
            await session.flush()
        session.add(ConsentParticipant(id=uuid.uuid4(), consent_record_id=record.id, name=name,
                                       position=position, reason=reason))
        await session.commit()


async def _rename(env, who: str, name: str) -> None:
    async with env.db() as session:
        (await session.get(Member, PEOPLE[who].member_id)).display_name = name
        await session.commit()


def _migration_module():
    path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "p8d4f1b6e3a9_act_integrity.py"
    spec = importlib.util.spec_from_file_location("migration_p8d4f1b6e3a9_flows", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_a_renamed_member_cannot_take_over_an_unowned_legacy_position(env):
    url = await _proposal(env)
    await _to_consent(env, url)
    await _legacy_position(env, url, "Ben", "object", "Too late at night")
    await _rename(env, "sol", "Ben")  # display names are self-editable

    # Withdrawing finds nothing of Sol's; changing a position adds Sol's own row. Ben's objection stands.
    withdrawn = await _call(env, "delete", "sol", f"{url}/consent")
    assert (withdrawn.status, withdrawn.json["error"]) == (404, NO_POSITION_TO_WITHDRAW)
    consented = await _call(env, "post", "sol", f"{url}/consent", json={"position": "consent"})
    assert (consented.json["gates"]["consent"]["open_objections"], consented.json["auto_transitions"]) == (1, [])
    assert sorted(await _rows(env)) == [("Ben", "consent"), ("Ben", "object")]


async def test_a_backfilled_legacy_position_belongs_to_its_member(env):
    url = await _proposal(env)
    await _to_consent(env, url)
    await _legacy_position(env, url, "ben ", "object", "Noise")  # unique in Oasis: backfilled to Ben
    await _legacy_position(env, url, "Nobody", "consent")  # no such member: stays unowned
    async with env.db() as session:
        await session.execute(text(_migration_module().BACKFILL_CONSENT_MEMBERS_SQL))
        await session.commit()

    lifted = await _call(env, "delete", "ben", f"{url}/consent")
    assert lifted.status == 200, lifted.text
    assert lifted.json["gates"]["consent"]["open_objections"] == 0
    assert sorted(await _rows(env)) == [("Nobody", "consent"), ("ben ", "withdrawn")]


async def test_only_members_of_the_proposals_ecosystem_take_positions(env):
    url = await _proposal(env)
    await _to_consent(env, url)
    async with env.db() as session:  # Ben has no row in Oasis any more
        await session.delete(await session.get(Member, PEOPLE["ben"].member_id))
        await session.commit()
    for method, kwargs in (("post", {"json": {"position": "consent"}}), ("delete", {})):
        resp = await _call(env, method, "ben", f"{url}/consent", **kwargs)
        assert (resp.status, resp.json["error"]) == (403, PARTICIPATE_DENIED)


async def test_positions_are_only_taken_during_consent(env):
    url = await _proposal(env)
    await _call(env, "post", "ada", f"{url}/status", json={"status": "advice"})
    resp = await _call(env, "post", "ben", f"{url}/consent", json={"position": "consent"})
    assert (resp.status, resp.json["error"]) == (409, CONSENT_CLOSED)


async def test_consensus_refuses_a_stand_aside(env):
    url = await _proposal(env, decision_type="consensus")
    await _to_consent(env, url)
    resp = await _call(env, "post", "ben", f"{url}/consent", json={"position": "stand_aside"})
    assert (resp.status, resp.json["error"]) == (400, STAND_ASIDE_IN_CONSENSUS)


@pytest.mark.parametrize("decision_type", ["advice", "autocratic"])
async def test_decision_types_the_engine_does_not_apply_are_refused(env, decision_type):
    resp = await _call(env, "post", "ada", "/api/v1/proposals",
                       json={"ecosystem_id": str(ECO), "type": "policy", "title": "T", "decision_type": decision_type})
    assert resp.status == 400


# ---------------------------------------------------------------------------
# Advice: stage check, the proposer's call, the deadline backstop
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("stage", ["draft", "consent"])
async def test_advice_is_only_given_during_advice(env, stage):
    url = await _proposal(env)
    if stage == "consent":
        await _to_consent(env, url)
    resp = await _call(env, "post", "sol", f"{url}/advice", json={"content": "Late advice"})
    assert resp.status == 409
    assert resp.json["status"] == stage


async def test_a_passed_advice_deadline_prompts_the_proposer_and_moves_nothing(env):
    url = await _proposal(env, advice_deadline=(dt.date.today() - dt.timedelta(days=1)).isoformat())
    await _call(env, "post", "ada", f"{url}/status", json={"status": "advice"})
    await _call(env, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})
    detail = await _detail(env, url)
    assert detail["status"] == "advice"
    assert detail["gates"]["advice"]["deadline_passed"] is True
    close = next(move for move in detail["allowed_next"] if move["to"] == "consent")
    assert close["ready"] is True  # the proposer is offered "Move to consent"; nothing moved by itself


# ---------------------------------------------------------------------------
# Send back for revision; withdrawal only before a decision
# ---------------------------------------------------------------------------


async def test_send_back_for_revision_keeps_history_and_needs_fresh_advice(env):
    url = await _proposal(env)
    await _to_consent(env, url)
    await _call(env, "post", "ben", f"{url}/consent", json={"position": "object", "objection_text": "Too late at night"})

    by_member = await _call(env, "post", "ben", f"{url}/status", json={"status": "advice", "note": "Mine now"})
    assert (by_member.status, by_member.json["error"]) == (403, MANAGE_DENIED)
    no_note = await _call(env, "post", "ada", f"{url}/status", json={"status": "advice"})
    assert (no_note.status, no_note.json["error"]) == (400, NOTE_REQUIRED)

    sent_back = await _call(env, "post", "ada", f"{url}/status",
                            json={"status": "advice", "note": "Closing at eight instead of nine"})
    assert sent_back.status == 200, sent_back.text
    body = sent_back.json
    assert (body["status"], body["version"]) == ("advice", "1.1")
    assert body["gates"]["advice"]["met"] is False  # the revision needs advice of its own
    assert body["gates"]["consent"]["open_objections"] == 0  # the old objection is history
    assert len(body["consent_records"]) == 2  # a fresh record; the objection stays in the first
    assert [p["position"] for r in body["consent_records"] for p in r["participants"]] == ["object"]
    assert "Closing at eight instead of nine" in [log["proposer_modifications"] for log in body["advice_logs"]]

    revised = await _call(env, "put", "ada", url, json={"proposed_change": "The garden opens until eight."})
    assert (revised.status, revised.json["proposed_change"]) == (200, "The garden opens until eight."), revised.text
    await _call(env, "post", "sol", f"{url}/advice", json={"content": "Eight works"})
    closed = await _call(env, "post", "ada", f"{url}/status", json={"status": "consent"})
    assert closed.json["status"] == "consent"
    assert (await _detail(env, url, "ben"))["caller_position"] is None  # a fresh round for v1.1


@pytest.mark.parametrize("terminal", ["ratified", "withdrawn"])
async def test_a_decided_or_withdrawn_proposal_cannot_be_withdrawn(env, terminal):
    url = await _proposal(env)
    if terminal == "ratified":
        await _ratified(env, url)
    else:
        await _call(env, "post", "ada", f"{url}/status", json={"status": "withdrawn"})
    resp = await _call(env, "post", "mo", f"{url}/status", json={"status": "withdrawn"})
    assert (resp.status, resp.json["allowed"]) == (400, [])
    assert (await _detail(env, url))["status"] == terminal


@pytest.mark.parametrize("stage", ["consent", "test", "ratified"])
async def test_the_text_is_frozen_once_members_decide_on_it(env, stage):
    url = await _proposal(env)
    if stage == "ratified":
        await _ratified(env, url)
    else:
        await _to_consent(env, url)
        if stage == "test":
            await _call(env, "post", "ben", f"{url}/consent", json={"position": "consent"})
    before = await _detail(env, url)
    assert before["status"] == stage
    for who in ("ada", "mo"):  # the author and a steward alike
        edit = await _call(env, "put", who, url, json={"proposed_change": "The garden never closes."})
        assert (edit.status, edit.json["error"]) == (409, PROPOSAL_LOCKED)
    resent = await _call(env, "put", "ada", url, json={"title": before["title"], "proposed_change": before["proposed_change"]})
    assert resent.status == 200, resent.text  # an unchanged resend is not an edit
    assert (await _detail(env, url))["proposed_change"] == "The garden opens until nine."


@pytest.mark.parametrize("proposer_text, steward, expected", [
    ("Mo", "mo", 403),  # the steward named as the legacy proposer cannot confirm it
    ("  mo ", "mo", 403),
    ("Mo", "ari", 200),  # another steward can
])
async def test_a_steward_named_as_a_legacy_proposer_cannot_ratify_it(env, proposer_text, steward, expected):
    async with env.db() as session:
        legacy = await session.get(Proposal, LEGACY_PROPOSAL)  # no author link
        legacy.status, legacy.proposer = "test", proposer_text
        await session.commit()
    url = f"/api/v1/proposals/{LEGACY_PROPOSAL}"
    report = await _call(env, "post", "sol", f"{url}/test", json={"outcome": "passed", "observations": "Ran a week"})
    assert report.status == 201, report.text
    resp = await _call(env, "post", steward, f"{url}/status", json={"status": "ratified"})
    assert resp.status == expected, resp.text
    if expected == 403:
        assert (resp.json["code"], resp.json["error"]) == ("NEEDS_ANOTHER_STEWARD", NEEDS_ANOTHER_STEWARD)
    assert (await _detail(env, url))["status"] == ("ratified" if expected == 200 else "test")


# ---------------------------------------------------------------------------
# One quorum vocabulary: from the governing agreement, which must be in force
# ---------------------------------------------------------------------------


async def test_quorum_comes_from_the_governing_agreement(env):
    url = await _proposal(env, governing_agreement_id=str(RULES_AGREEMENT))
    await _to_consent(env, url)
    first = await _call(env, "post", "ben", f"{url}/consent", json={"position": "consent"})
    consent_gate = first.json["gates"]["consent"]
    assert (consent_gate["quorum"], consent_gate["quorum_source"], consent_gate["positions"]) == (2, "agreement", 1)
    assert first.json["auto_transitions"] == []
    second = await _call(env, "post", "sol", f"{url}/consent", json={"position": "consent"})
    assert second.json["auto_transitions"] == ["consent->test"]


async def test_default_quorum_is_one_and_says_so(env):
    url = await _proposal(env)
    gate = (await _detail(env, url))["gates"]["consent"]
    assert (gate["quorum"], gate["quorum_source"]) == (1, "default")


async def test_a_draft_agreement_cannot_govern_a_proposal(env):
    resp = await _call(env, "post", "ada", "/api/v1/proposals", json={
        "ecosystem_id": str(ECO), "type": "policy", "title": "T", "governing_agreement_id": str(GARDEN_AGREEMENT),
    })
    assert resp.status == 400
    assert "in force" in resp.json["error"]


# ---------------------------------------------------------------------------
# Ratified is not registered until a steward registers it
# ---------------------------------------------------------------------------


async def test_a_steward_registers_a_ratified_proposal_as_a_new_agreement(env):
    url = await _proposal(env)
    await _ratified(env, url)
    as_author = await _detail(env, url)
    assert (as_author["caller_can_register"], as_author.get("registered_agreement")) == (False, None)

    refused = await _call(env, "post", "ada", f"{url}/register-agreement")
    assert refused.status == 403
    registered = await _call(env, "post", "mo", f"{url}/register-agreement")
    assert registered.status == 201, registered.text
    agreement = registered.json["registered_agreement"]
    assert (agreement["status"], agreement["title"]) == ("active", "Evening garden hours")
    assert registered.json["caller_can_register"] is False
    listed = (await _call(env, "get", "ben", "/api/v1/agreements?status=active")).json
    assert agreement["id"] in {item["id"] for item in listed["items"]}
    again = await _call(env, "post", "mo", f"{url}/register-agreement")
    assert again.status == 409
    async with env.db() as session:
        titled = select(func.count(Agreement.id)).where(Agreement.title == "Evening garden hours")
        assert await session.scalar(titled) == 1  # the second request created nothing


async def test_registering_an_amendment_versions_the_agreement_and_asks_members_to_re_attest(env):
    rules = f"/api/v1/agreements/{RULES_AGREEMENT}"
    attested = await _call(env, "post", "ben", f"{rules}/consent", json={"attestation": "I agree to version one."})
    assert attested.json["current_member_consent"]["agreement_version"] == "1.0"

    url = await _proposal(env, amends_agreement_id=str(RULES_AGREEMENT), proposed_change="Three voices decide.")
    await _ratified(env, url)
    not_ratified_yet = await _call(env, "post", "mo", f"{await _proposal(env)}/register-agreement")
    assert not_ratified_yet.status == 409
    registered = await _call(env, "post", "mo", f"{url}/register-agreement")
    assert registered.status == 201, registered.text
    assert registered.json["registered_agreement"]["id"] == str(RULES_AGREEMENT)

    agreement = (await _call(env, "get", "ben", rules)).json
    assert (agreement["version"], agreement["text"]) == ("1.1", "Three voices decide.")
    assert agreement.get("current_member_consent") is None  # Ben's consent was to v1.0
    history = (await _call(env, "get", "ben", f"{rules}/history")).json
    [amendment] = history["amendments"]
    assert (amendment["new_agreement_version"], amendment["status"]) == ("1.1", "ratified")


async def test_registering_copies_the_text_ratified_not_the_live_text(env):
    url = await _proposal(env)
    await _ratified(env, url)
    async with env.db() as session:  # a write that bypasses PUT's lock (direct SQL, a legacy route)
        proposal = await session.get(Proposal, uuid.UUID(url.rsplit("/", 1)[1]))
        proposal.proposed_change = "The garden never closes."
        await session.commit()
    registered = await _call(env, "post", "mo", f"{url}/register-agreement")
    assert registered.status == 201, registered.text
    agreement_url = f"/api/v1/agreements/{registered.json['registered_agreement']['id']}"
    assert (await _call(env, "get", "ben", agreement_url)).json["text"] == "The garden opens until nine."


@pytest.mark.skipif(not os.environ.get("NEOS_TEST_POSTGRES_URL"), reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
async def test_concurrent_registrations_create_one_agreement_on_postgres():
    """Two stewards press "Register" together: the second waits on the proposal's row lock, then gets 409."""
    schema = f"gact_{uuid.uuid4().hex[:12]}"
    engine = create_async_engine(os.environ["NEOS_TEST_POSTGRES_URL"],
                                 connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        proposal_id = uuid.uuid4()
        async with factory() as session:  # just the people involved (the shared fixture's insert order is SQLite-only)
            session.add(Ecosystem(id=ECO, name="Oasis", status="active"))
            session.add_all([User(id=PEOPLE[key].user_id, display_name=PEOPLE[key].name) for key in ("ada", "mo", "ari")])
            await session.flush()
            session.add_all([
                Member(id=PEOPLE[key].member_id, ecosystem_id=ECO, user_id=PEOPLE[key].user_id, member_id=f"MEM-{key}",
                       display_name=PEOPLE[key].name, current_status="active", role=PEOPLE[key].role)
                for key in ("ada", "mo", "ari")
            ])
            await session.flush()
            session.add(Proposal(id=proposal_id, ecosystem_id=ECO, proposal_id="PROP-RACE", type="policy",
                                 title="Race", version="1.0", status="ratified", proposer="Ada",
                                 proposer_member_id=PEOPLE["ada"].member_id, ratified_text="One text."))
            await session.commit()
        first_holds_lock, release_first = asyncio.Event(), asyncio.Event()

        async def register(steward: str, hold: bool) -> int:
            async with factory() as session:
                caller = await session.get(Member, PEOPLE[steward].member_id)
                proposal = await session.get(Proposal, proposal_id)
                try:
                    await register_ratified_proposal(session, proposal, caller=caller)
                except ApiError as refused:
                    return refused.status
                if hold:
                    first_holds_lock.set()
                    await release_first.wait()
                await session.commit()
                return 201

        first = asyncio.create_task(register("mo", hold=True))
        await first_holds_lock.wait()
        second = asyncio.create_task(register("ari", hold=False))
        await asyncio.sleep(0.5)  # without the lock the second request finishes here and registers again
        release_first.set()
        assert sorted(await asyncio.gather(first, second)) == [201, 409]
        async with factory() as session:
            assert await session.scalar(select(func.count(Agreement.id)).where(Agreement.title == "Race")) == 1
    finally:
        async with engine.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await engine.dispose()


async def test_an_in_force_agreement_offers_a_change_proposal(env):
    detail = (await _call(env, "get", "ben", f"/api/v1/agreements/{RULES_AGREEMENT}")).json
    assert detail["caller_can_propose_change"] is True
    draft = (await _call(env, "get", "ben", f"/api/v1/agreements/{GARDEN_AGREEMENT}")).json
    assert draft["caller_can_propose_change"] is False


# ---------------------------------------------------------------------------
# Agreements: the version bumps only when the attested text changes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("change, version", [
    ({"review_date": "2027-01-01"}, "1.0"),
    ({"domain": "Garden"}, "1.0"),
    ({"text": "Open at sunrise."}, "1.1"),
    ({"title": "Garden opening hours"}, "1.1"),
])
async def test_editing_an_agreement_versions_only_text_changes(env, change, version):
    resp = await _call(env, "put", "ben", f"/api/v1/agreements/{GARDEN_AGREEMENT}", json=change)
    assert resp.status == 200, resp.text
    assert resp.json["version"] == version


async def test_a_declared_agreement_quorum_relaxes_every_member(env):
    async with env.db() as session:
        garden = await session.get(Agreement, GARDEN_AGREEMENT)
        garden.status = "consent"
        garden.act_policy = {"min_advice_rounds": 0, "consent_required": True, "consent_quorum": 1, "test_cases": []}
        await session.commit()
    resp = await _call(env, "post", "ben", f"/api/v1/agreements/{GARDEN_AGREEMENT}/consent",
                       json={"attestation": "I agree to the garden hours."})
    assert resp.status == 201, resp.text
    assert (resp.json["auto_transitions"], resp.json["gates"]["consent"]["quorum_source"]) == (["consent->test"], "agreement")


# ---------------------------------------------------------------------------
# Onboarding ceremony consent: the member or a steward, never another member
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("actor, expected", [
    ("ben", 200),  # the member themselves
    ("mo", 200),  # a steward facilitating
    ("sol", 403),  # another member
    ("olu", 404),  # another ecosystem: the member is not visible
])
async def test_onboarding_section_consent_by_actor(env, actor, expected):
    async with env.db() as session:
        session.add(MemberOnboarding(id=uuid.uuid4(), member_id=PEOPLE["ben"].member_id, section_consents={}))
        await session.commit()
    url = f"/api/v1/onboarding/{PEOPLE['ben'].member_id}/ceremony"
    resp = await _call(env, "post", actor, url, json={"section": "governance", "consented": True})
    assert resp.status == expected, resp.text
    if expected == 403:
        assert resp.json["error"] == ONBOARDING_CONSENT_DENIED
    state = (await _call(env, "get", "ben", url)).json
    assert state["section_consents"]["governance"] is (expected == 200)
    assert state["caller_can_record"] is True
    if actor == "sol":
        assert (await _call(env, "get", "sol", url)).json["caller_can_record"] is False

