"""UX-QA pass 02 (ACT lifecycle), lane 1: who may take part, and every hand-off says who acts next.

Drives the real proposals, agreements, decisions and next-steps blueprints over in-memory SQLite as
different members; the assistant runs through `execute_tool` and MCP through its tool functions.
Rules: src/neos_agent/services/AGENTS.md "Next steps" and "ACT lifecycle", api/AGENTS.md "ACT integrity
(G-ACT)" (participation and the CONSENT_PENDING refusal).
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.agent.governance_tools import execute_tool
from neos_agent.api.agreements import agreements_api_bp
from neos_agent.api.decisions import decisions_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.next_steps import next_steps_api_bp
from neos_agent.api.proposals import proposals_api_bp
from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    Base,
    ConsentParticipant,
    Ecosystem,
    Member,
    Proposal,
    TestReport,
    User,
)
from neos_agent.services.act_gates import CONSENT_PENDING, PARTICIPATE_DENIED, consent_pending_message
from neos_agent.services.next_steps import ADVICE_READY_PROMPT

OASIS = uuid.UUID("0000000f-0000-0000-0000-000000000001")
ESCHER = uuid.UUID("0000000f-0000-0000-0000-000000000002")


@dataclass(frozen=True)
class Person:
    key: str
    name: str
    rows: dict = field(default_factory=dict)  # ecosystem -> (role, status)

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"p2-act.{self.key}.user")

    def member_id(self, ecosystem: uuid.UUID) -> uuid.UUID:
        return uuid.uuid5(self.user_id, str(ecosystem))

    @property
    def active_in(self) -> list[uuid.UUID]:
        return [eco for eco, (_, status) in self.rows.items() if status == "active"]


PEOPLE = {p.key: p for p in (
    Person("ada", "Ada", {OASIS: ("user", "active")}),  # writes the Oasis proposals
    Person("ben", "Ben", {OASIS: ("user", "active")}),
    Person("cy", "Cy", {OASIS: ("user", "active")}),
    Person("mo", "Mo", {OASIS: ("mod", "active")}),
    Person("sol", "Sol", {OASIS: ("mod", "active")}),
    Person("ari", "Ari", {OASIS: ("admin", "active")}),
    # Active in Oasis, still waiting on Escherbridge's consent gate: reads its shared proposals, never acts on them.
    Person("tess", "Tess", {OASIS: ("user", "active"), ESCHER: ("user", "pending_consent")}),
    Person("uma", "Uma", {OASIS: ("user", "active")}),  # no Escherbridge row: the shared-ecosystem path
    Person("eli", "Eli", {ESCHER: ("user", "active")}),
    Person("esme", "Esme", {ESCHER: ("user", "active")}),  # writes the Escherbridge proposals
)}
OASIS_MEMBERS = [key for key, p in PEOPLE.items() if OASIS in p.active_in]
NAMES = {OASIS: "Oasis", ESCHER: "Escherbridge"}


async def _seed(session: AsyncSession) -> None:
    session.add_all([Ecosystem(id=eco, name=name, status="active") for eco, name in NAMES.items()])
    for p in PEOPLE.values():
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for p in PEOPLE.values():
        for eco, (role, status) in p.rows.items():
            session.add(Member(id=p.member_id(eco), ecosystem_id=eco, user_id=p.user_id,
                               member_id=f"MEM-{p.key.upper()}-{NAMES[eco][:3].upper()}",
                               display_name=p.name, current_status=status, role=role))
    await session.commit()


def _create_app(factory) -> Sanic:
    app = Sanic(f"test-p2-act-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def sign_in(request):
        p = PEOPLE[request.headers["x-test-as"]]
        home = p.active_in[0]
        role, status = p.rows[home]
        request.ctx.member = Member(id=p.member_id(home), ecosystem_id=home, user_id=p.user_id, member_id="MEM-AUTH",
                                    display_name=p.name, current_status=status, role=role)
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = list(p.active_in)  # the auth middleware admits active rows only
        request.ctx.authorized_ecosystem_ids = list(p.active_in)

    for blueprint in (proposals_api_bp, agreements_api_bp, decisions_api_bp, next_steps_api_bp):
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
    yield SimpleNamespace(app=_create_app(factory), db=factory)
    await engine.dispose()


async def _call(env, method: str, who: str, url: str, expect: int | None = None, **kwargs):
    _, resp = await getattr(env.app.asgi_client, method)(url, headers={"x-test-as": who}, **kwargs)
    if expect is not None:
        assert resp.status == expect, (method, url, who, resp.status, resp.text)
    return resp


async def _queue(env, who: str, kind: str = "proposal") -> list[dict]:
    items = (await _call(env, "get", who, "/api/v1/me/next-steps", expect=200)).json["items"]
    return [item for item in items if item["kind"] == kind]


async def _explain(env, who: str, proposal_id: str) -> dict:
    return (await _call(env, "get", who, f"/api/v1/explain/proposal/{proposal_id}", expect=200)).json


async def _detail(env, who: str, proposal_id: str) -> dict:
    return (await _call(env, "get", who, f"/api/v1/proposals/{proposal_id}", expect=200)).json


async def _tool(env, who: str, name: str, scope: list[uuid.UUID] | None = None, **args) -> dict:
    """A chat tool as api/chat.py runs it: the member's selected ecosystems, commit on success."""
    p = PEOPLE[who]
    async with env.db() as session:
        result = await execute_tool(name, args, session, ecosystem_ids=[str(e) for e in scope or p.active_in],
                                    caller_user_id=p.user_id)
        if result.get("success"):
            await session.commit()
    return result


async def _post(env, who: str, proposal_id: str, path: str, expect: int = 201, **body):
    return await _call(env, "post", who, f"/api/v1/proposals/{proposal_id}{path}", expect=expect, json=body)


async def _proposal(env, who: str = "ada", title: str = "Bike shed", **fields) -> str:
    """An Oasis proposal opened for advice by its author."""
    created = await _call(env, "post", who, "/api/v1/proposals", expect=201, json={
        "ecosystem_id": str(OASIS), "type": "policy", "title": title, **fields,
    })
    await _post(env, who, created.json["id"], "/status", expect=200, status="advice")
    return created.json["id"]


async def _to_consent(env, proposal_id: str) -> None:
    await _post(env, "ben", proposal_id, "/advice", content="A shed keeps them dry.")
    await _post(env, "ada", proposal_id, "/status", expect=200, status="consent")


async def _shared_proposal(env, status: str) -> str:
    """An Escherbridge proposal by Esme in `status`, shared into Oasis (so Tess and Uma can open it)."""
    proposal_id = uuid.uuid4()
    async with env.db() as session:
        session.add(Proposal(
            id=proposal_id, ecosystem_id=ESCHER, shared_ecosystem_ids=[str(OASIS)], proposal_id=f"PROP-{status.upper()}",
            type="policy", title=f"Repair bench ({status})", version="1.0", status=status, proposer="Esme",
            proposer_member_id=PEOPLE["esme"].member_id(ESCHER), proposed_change="A shared repair bench.",
        ))
        await session.commit()
    return str(proposal_id)


# ---------------------------------------------------------------------------
# Participation: an ACTIVE row acts; a pending newcomer reads and is told why (p2-act-authority-probe-1/-2)
# ---------------------------------------------------------------------------

ACTS = {
    "advice": ("/advice", {"content": "Keep the bench indoors."}),
    "consent": ("/consent", {"position": "consent"}),
    "test": ("/test", {"observations": "Used it all week.", "outcome": "passed"}),
}


@pytest.mark.parametrize("who, act, status, refusal", [
    ("tess", "advice", 403, CONSENT_PENDING),
    ("tess", "consent", 403, CONSENT_PENDING),  # her consent would have counted toward the quorum
    ("tess", "test", 403, CONSENT_PENDING),
    ("uma", "advice", 201, None),  # no row in Escherbridge: the shared-ecosystem advice path is kept
    ("uma", "test", 201, None),
    ("uma", "consent", 403, PARTICIPATE_DENIED),  # a position always needs a row there (unchanged)
    ("eli", "advice", 201, None),
    ("eli", "consent", 201, None),
    ("eli", "test", 201, None),
])
async def test_only_an_active_row_takes_part_and_a_pending_newcomer_is_told_why(env, who, act, status, refusal):
    path, body = ACTS[act]
    proposal_id = await _shared_proposal(env, act)
    resp = await _post(env, who, proposal_id, path, expect=status, **body)
    if refusal == CONSENT_PENDING:
        assert resp.json == {"error": consent_pending_message("Escherbridge"), "code": CONSENT_PENDING}
    elif refusal:
        assert resp.json["error"] == refusal
    async with env.db() as session:  # a refusal writes nothing
        written = sum([
            await session.scalar(select(func.count(AdviceEntry.id))) or 0,
            await session.scalar(select(func.count(ConsentParticipant.id))) or 0,
            await session.scalar(select(func.count(TestReport.id))) or 0,
        ])
    assert written == (1 if status == 201 else 0)


async def test_a_pending_newcomer_reads_the_page_and_cannot_write_a_proposal_there(env):
    shared = await _shared_proposal(env, "advice")
    page = await _detail(env, "tess", shared)
    assert (page["caller_can_conduct"], page["caller_consent_pending"]) == (False, True)
    assert (await _detail(env, "eli", shared))["caller_consent_pending"] is False

    body = {"ecosystem_id": str(ESCHER), "type": "policy", "title": "Tess's idea"}
    refused = await _call(env, "post", "tess", "/api/v1/proposals", expect=403, json=body)
    assert refused.json == {"error": consent_pending_message("Escherbridge"), "code": CONSENT_PENDING}
    # Someone with no row at all keeps the plain refusal; an active member writes it.
    assert (await _call(env, "post", "uma", "/api/v1/proposals", expect=403, json=body)).json == {
        "error": "Access denied to this ecosystem"}
    await _call(env, "post", "eli", "/api/v1/proposals", expect=201, json=body)


async def test_the_assistant_refuses_a_pending_newcomer_in_the_same_words(env):
    pending = {"success": False, "error": consent_pending_message("Escherbridge"), "code": CONSENT_PENDING}
    calls = [
        ("record_advice", {"proposal_id": await _shared_proposal(env, "advice"), "advice_text": "Keep it indoors."}),
        ("record_consent_position", {"proposal_id": await _shared_proposal(env, "consent"), "position": "consent"}),
        ("submit_test_report", {"proposal_id": await _shared_proposal(env, "test"), "outcome": "passed",
                                "observations": "Used it all week."}),
    ]
    for name, args in calls:
        assert await _tool(env, "tess", name, **args) == pending, name
    # A stale scope that still lists Escherbridge cannot make her its author either.
    created = await _tool(env, "tess", "create_proposal", scope=[ESCHER], title="Tess's idea", type="policy",
                          proposed_change="A tool shelf.", rationale="We lose tools.")
    assert created == pending
    name, args = calls[0]
    assert (await _tool(env, "uma", name, **args))["success"] is True  # shared path, no row: unchanged


async def test_mcp_refuses_a_pending_newcomer_in_the_same_words(env, monkeypatch):
    pytest.importorskip("mcp.server.fastmcp")
    from neos_agent import mcp_server

    async def as_tess(ctx):
        return mcp_server.Caller(user=User(id=PEOPLE["tess"].user_id, display_name="Tess"), token=None)

    monkeypatch.setattr(mcp_server, "_caller", as_tess)
    monkeypatch.setattr(mcp_server, "_db", lambda: env.db)
    advice, consent, test = [await _shared_proposal(env, stage) for stage in ("advice", "consent", "test")]
    calls = (
        lambda: mcp_server.record_proposal_advice(advice, "Keep it indoors.", ctx=None),
        lambda: mcp_server.submit_proposal_consent(consent, "consent", ctx=None),
        lambda: mcp_server.submit_test_report(test, "passed", ctx=None),
        lambda: mcp_server.create_proposal(str(ESCHER), "Tess's idea", ctx=None),
    )
    for call in calls:
        with pytest.raises(ValueError, match=f"^{CONSENT_PENDING}: Your membership in Escherbridge"):
            await call()


# ---------------------------------------------------------------------------
# The queue: owner acts first; the author answers objections; a steward registers (keyboard-3/-1, stewards-7/-8)
# ---------------------------------------------------------------------------


async def test_the_acts_only_you_can_take_come_right_after_overdue_items(env):
    soon = (dt.date.today() + dt.timedelta(days=2)).isoformat()
    late = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    dated = await _proposal(env, "ben", "Garden rota", advice_deadline=soon)
    overdue = await _proposal(env, "ben", "Tool library", advice_deadline=late)
    own = await _proposal(env, "ada", "Bike shed")  # no deadline
    await _post(env, "cy", own, "/advice", content="Yes, by the gate.")

    order = [(item["action"], item["id"]) for item in await _queue(env, "ada")]
    # Before: dated items first and close_advice (undated) sank to the bottom, sorted by title.
    assert order == [("give_advice", overdue), ("close_advice", own), ("give_advice", dated)]
    [close] = [item for item in await _queue(env, "ada") if item["action"] == "close_advice"]
    assert close["what"] == ADVICE_READY_PROMPT and close["what"].startswith("Close advice")


async def test_the_author_is_asked_to_answer_each_objection_by_name(env):
    proposal_id = await _proposal(env, proposed_change="Bikes go in the shed.")
    await _to_consent(env, proposal_id)
    await _post(env, "ben", proposal_id, "/consent", position="object", objection_text="Too noisy at night")
    await _post(env, "cy", proposal_id, "/consent", position="consent")

    queue = await _queue(env, "ada")
    assert [(item["action"], item["what"]) for item in queue] == [
        ("answer_objection", "Ben objected: “Too noisy at night”"),
        ("record_position", "Record your position: consent, stand aside or object"),
    ]
    assert "send it back for revision" in queue[0]["why"] and "wait for Ben to withdraw it" in queue[0]["why"]

    said = {who: (await _explain(env, who, proposal_id))["next_step"] for who in ("ada", "ben", "cy")}
    assert all("Ben objected: “Too noisy at night”." in text for text in said.values()), said
    assert "Answer it: send it back for revision" in said["ada"]
    assert "You objected: once your concern is answered, you can withdraw your objection." in said["ben"]
    assert "Ada answers it." in said["cy"]
    # Only objecting needs a reason (the old copy asked one for standing aside too).
    assert "(objecting needs a reason)" in said["ada"] and "standing aside" not in said["ada"]

    await _call(env, "delete", "ben", f"/api/v1/proposals/{proposal_id}/consent", expect=200)
    assert all(item["action"] != "answer_objection" for item in await _queue(env, "ada"))


async def test_revise_leaves_the_authors_list_once_she_edits_and_the_banner_says_who_sent_it_back(env):
    proposal_id = await _proposal(env, proposed_change="Bikes go in the shed.")
    await _to_consent(env, proposal_id)
    await _post(env, "ada", proposal_id, "/status", expect=200, status="advice", note="Adding a rota for the key")

    banner = (await _explain(env, "ben", proposal_id))["next_step"]
    assert ("Ada sent it back for revision with this note: “Adding a rota for the key”. This is version 1.1; "
            "advice, positions and test reports on earlier versions are kept as history.") in banner
    # The send-back happened an hour ago (the clock is the process edge); she has not edited yet.
    an_hour_ago = dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(hours=1)
    async with env.db() as session:
        await session.execute(update(Proposal).where(Proposal.id == uuid.UUID(proposal_id)).values(updated_at=an_hour_ago))
        await session.execute(update(AdviceLog).where(AdviceLog.proposal_id == uuid.UUID(proposal_id))
                              .values(updated_at=an_hour_ago))
        await session.commit()
    assert [item["action"] for item in await _queue(env, "ada")] == ["revise"]

    await _call(env, "put", "ada", f"/api/v1/proposals/{proposal_id}", expect=200,
                json={"proposed_change": "Bikes go in the shed; a rota keeps the key."})
    assert await _queue(env, "ada") == []  # revised; the new round has no advice yet, so nothing else is hers


async def test_the_advice_banner_says_the_author_closes_advice_to_each_viewer(env):
    proposal_id = await _proposal(env)
    await _post(env, "ben", proposal_id, "/advice", content="A shed keeps them dry.")

    said = {who: await _explain(env, who, proposal_id) for who in ("ada", "mo", "cy")}
    assert "You decide when to close advice and move it to consent: nothing moves by itself." in said["ada"]["next_step"]
    # A steward is never told "you decide" (owner decision 2026-11-01): with no deadline only the proposer can.
    assert ("Ada wrote it and closes advice. There is no advice deadline, so only Ada can close it."
            in said["mo"]["next_step"])
    assert "Ada wrote it and decides when to close advice and move it to consent." in said["cy"]["next_step"]
    assert all("or a steward moves it" not in s["next_step"] for s in said.values())
    assert {s["decided_by"] for s in said.values()} == {"Ada, who wrote it"}
    assert said["ada"]["next_step"].startswith("Advice stage: 1 of 1 advice round has advice.")
    # The page's done state: the advisor sees they advised in this round, nobody else does.
    assert [(await _detail(env, who, proposal_id))["caller_has_advised"] for who in ("ben", "cy")] == [True, False]

    # With a deadline the steward is told when they may act, and once it has passed that they may.
    for deadline, steward_words, decided_by in (
        (dt.date.today() + dt.timedelta(days=2), "You can close it after the advice deadline ({date}) if they haven't.",
         "Ada, who wrote it (a steward can close it for them after the advice deadline, {date})"),
        (dt.date.today() - dt.timedelta(days=1),
         "The advice deadline ({date}) has passed, so as a steward you can close it for them if they haven't.",
         "Ada, who wrote it; the advice deadline has passed, so a steward can close it for them"),
    ):
        async with env.db() as session:
            await session.execute(update(Proposal).where(Proposal.id == uuid.UUID(proposal_id))
                                  .values(advice_deadline=deadline))
            await session.commit()
        steward = await _explain(env, "mo", proposal_id)
        assert steward_words.format(date=deadline.isoformat()) in steward["next_step"], steward["next_step"]
        assert steward["decided_by"] == decided_by.format(date=deadline.isoformat())
        assert "You decide" not in steward["next_step"]


async def test_a_passed_report_hands_off_to_named_stewards_then_registration_waits_in_their_lists(env):
    proposal_id = await _proposal(env, proposed_change="Bikes go in the shed.")
    await _to_consent(env, proposal_id)
    # One send-back first, so the record's round count must follow the gate (rounds since the revision).
    await _post(env, "mo", proposal_id, "/status", expect=200, status="advice", note="Say where the key lives")
    await _to_consent(env, proposal_id)
    await _post(env, "ben", proposal_id, "/consent", position="consent")  # meets the quorum: on to test
    await _post(env, "ben", proposal_id, "/test", observations="Bikes stayed dry all week.", outcome="passed")

    as_author = await _explain(env, "ada", proposal_id)
    assert "Test stage: the test evidence is in." in as_author["next_step"]
    assert "Now a steward who did not write it confirms ratification: Ari, Mo or Sol can" in as_author["next_step"]
    assert "You can file a test report." not in (await _explain(env, "cy", proposal_id))["next_step"]
    assert as_author["decided_by"] == "A steward who did not write it: Ari, Mo or Sol"
    page = await _detail(env, "ada", proposal_id)
    assert [c["display_name"] for c in page["ratification_confirmers"]] == ["Ari", "Mo", "Sol"]
    assert [(await _detail(env, who, proposal_id))["caller_has_reported"] for who in ("ben", "cy")] == [True, False]

    ratified = await _post(env, "mo", proposal_id, "/status", expect=200, status="ratified")
    decision_id = ratified.json["decision_record_id"]
    stewards = {who for who in OASIS_MEMBERS
                if ("register_agreement", proposal_id) in {(i["action"], i["id"]) for i in await _queue(env, who)}}
    assert stewards == {"mo", "sol", "ari"}
    waiting = await _explain(env, "ada", proposal_id)
    assert "not in the agreement registry yet" in waiting["next_step"] and "Nothing more is needed" not in waiting["next_step"]
    assert waiting["decided_by"] == "Any steward of this ecosystem, by registering it as an agreement"

    decision = (await _call(env, "get", "ada", f"/api/v1/decisions/{decision_id}", expect=200)).json
    assert (decision["recorder"], decision["recorder_role"]) == ("Mo", "steward who confirmed ratification")
    summary = decision["deliberation_summary"]
    assert "1 advice round had advice" in summary and "1 member recorded a position" in summary, summary
    assert "Mo, a steward who did not write it, confirmed ratification" in summary and "True" not in summary
    assert decision["registered_agreement"] is None

    registered = await _post(env, "sol", proposal_id, "/register-agreement")
    agreement = registered.json["registered_agreement"]
    queues = [await _queue(env, who) for who in OASIS_MEMBERS]
    assert all(item["action"] != "register_agreement" for queue in queues for item in queue)
    done = (await _explain(env, "ada", proposal_id))["next_step"]
    assert done == "It is ratified and registered as the agreement “Bike shed”, which is in force. Nothing more is needed."
    decision = (await _call(env, "get", "ada", f"/api/v1/decisions/{decision_id}", expect=200)).json
    assert decision["registered_agreement"] == {"id": agreement["id"], "agreement_id": agreement["agreement_id"],
                                                "title": "Bike shed"}
    page = (await _call(env, "get", "ada", f"/api/v1/agreements/{agreement['id']}", expect=200)).json
    assert page["registered_from_proposal"] == {"id": proposal_id, "proposal_id": ratified.json["proposal_id"],
                                                "title": "Bike shed"}


async def test_a_report_on_an_earlier_version_is_history_for_the_gate_the_page_and_the_record(env):
    """The revision banner says earlier test reports are history: the gate, the page and the record count none."""
    proposal_id = await _proposal(env, proposed_change="Bikes go in the shed.")
    await _to_consent(env, proposal_id)
    await _post(env, "ben", proposal_id, "/consent", position="consent")  # meets the quorum: on to test
    await _post(env, "ben", proposal_id, "/test", observations="Bikes stayed dry all week.", outcome="passed")
    # Filed an hour before the send-back (the clock is the process edge; SQLite keeps server time to the second).
    an_hour_ago = dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(hours=1)
    async with env.db() as session:
        await session.execute(update(TestReport).where(TestReport.proposal_id == uuid.UUID(proposal_id))
                              .values(created_at=an_hour_ago))
        await session.commit()
    await _post(env, "ada", proposal_id, "/status", expect=200, status="advice", note="Say where the key lives")
    await _to_consent(env, proposal_id)
    await _post(env, "ben", proposal_id, "/consent", position="consent")  # v1.1 enters test

    page = await _detail(env, "ben", proposal_id)
    assert (page["status"], page["version"]) == ("test", "1.1")
    assert (page["gates"]["test"]["met"], page["gates"]["test"]["reports"]) == (False, 0)
    assert page["caller_has_reported"] is False
    assert "Test stage: 0 test reports so far" in (await _explain(env, "ben", proposal_id))["next_step"]
    assert all(item["action"] != "confirm_ratification" for item in await _queue(env, "mo"))
    await _post(env, "mo", proposal_id, "/status", expect=409, status="ratified")

    await _post(env, "cy", proposal_id, "/test", observations="Dry again with the rota.", outcome="passed")
    ratified = await _post(env, "mo", proposal_id, "/status", expect=200, status="ratified")
    decision = (await _call(env, "get", "ada", f"/api/v1/decisions/{ratified.json['decision_record_id']}",
                            expect=200)).json
    summary = decision["deliberation_summary"]
    assert "On the version that was decided (v1.1)" in summary and "1 test report was filed" in summary, summary
