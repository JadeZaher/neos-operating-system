"""G-Next: one source for "what is waiting for me" and "what happens next here" (uxqa/governance/plan.md, wave B).

Drives the real proposals, agreements, conflicts, emergency, exit, safeguards, next-steps and chat
blueprints over in-memory SQLite, acting as different members; the assistant runs through
`execute_tool` and the real POST /api/v1/chat/send with a scripted model. Contracts:
src/neos_agent/services/AGENTS.md "Next steps", api/AGENTS.md "Next steps (G-Next)".
"""

from __future__ import annotations

import datetime as dt
import json
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.agent.governance_tools import execute_tool
from neos_agent.api.agreements import agreements_api_bp
from neos_agent.api.chat import chat_api_bp
from neos_agent.api.conflicts import conflicts_api_bp
from neos_agent.api.emergency import emergency_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.exit import exit_api_bp
from neos_agent.api.next_steps import next_steps_api_bp
from neos_agent.api.proposals import proposals_api_bp
from neos_agent.api.safeguards import safeguards_api_bp
from neos_agent.auth.ecosystem_scope import EcosystemScope
from neos_agent.db.models import Agreement, Base, EmergencyState, Ecosystem, Member, Proposal, User
from neos_agent.services.next_steps import ADVICE_DEADLINE_PROMPT, ADVICE_READY_PROMPT

OASIS = uuid.UUID("0000000e-0000-0000-0000-000000000001")
RIVER = uuid.UUID("0000000e-0000-0000-0000-000000000002")
HOUSE_RULES = uuid.UUID("0000000e-0000-0000-0000-0000000000a1")


@dataclass(frozen=True)
class Person:
    key: str
    name: str
    role: str
    home: uuid.UUID = OASIS

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"g-next.{self.key}.user")

    @property
    def member_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"g-next.{self.key}.member")


PEOPLE = {p.key: p for p in (
    Person("ada", "Ada", "user"),  # writes the proposal, reports the conflict
    Person("ben", "Ben", "user"),  # declares the emergency, drafts an audit
    Person("cy", "Cy", "user"),  # named in the conflict, files an exit
    Person("mo", "Mo", "mod"),  # steward
    Person("sol", "Sol", "mod"),  # steward
    Person("ari", "Ari", "admin"),  # steward who conducts agreement ceremonies
    Person("olu", "Olu", "user", RIVER),  # another ecosystem only
)}
OASIS_MEMBERS = [key for key, p in PEOPLE.items() if p.home == OASIS]


async def _seed(session: AsyncSession) -> None:
    session.add_all([Ecosystem(id=OASIS, name="Oasis", status="active"),
                     Ecosystem(id=RIVER, name="River House", status="active")])
    for p in PEOPLE.values():
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for p in PEOPLE.values():
        session.add(Member(id=p.member_id, ecosystem_id=p.home, user_id=p.user_id, member_id=f"MEM-{p.key.upper()}",
                           display_name=p.name, current_status="active", role=p.role))
    session.add(Agreement(id=HOUSE_RULES, ecosystem_id=OASIS, agreement_id="AGR-HOUSE", type="organizational",
                          title="House rules", version="1.0", status="consent", proposer="Ari", text="Quiet after ten.",
                          requires_explicit_consent=True))
    await session.commit()


def _create_app(factory) -> Sanic:
    app = Sanic(f"test-g-next-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def sign_in(request):
        p = PEOPLE[request.headers["x-test-as"]]
        request.ctx.member = Member(id=p.member_id, ecosystem_id=p.home, user_id=p.user_id, member_id="MEM-AUTH",
                                    display_name=p.name, current_status="active", role=p.role)
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = [p.home]
        request.ctx.authorized_ecosystem_ids = [p.home]
        names = {OASIS: "Oasis", RIVER: "River House"}
        request.ctx.ecosystem_scope = EcosystemScope.from_ecosystems([SimpleNamespace(id=p.home, name=names[p.home])], [p.home])

    for blueprint in (proposals_api_bp, agreements_api_bp, conflicts_api_bp, emergency_api_bp, exit_api_bp,
                      safeguards_api_bp, next_steps_api_bp, chat_api_bp):
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


async def _queue(env, who: str) -> dict:
    return (await _call(env, "get", who, "/api/v1/me/next-steps", expect=200)).json


async def _items(env, who: str, kind: str | None = None) -> set[tuple[str, str]]:
    return {(i["action"], i["title"]) for i in (await _queue(env, who))["items"] if kind in (None, i["kind"])}


async def _explain(env, who: str, kind: str, record_id, expect: int = 200):
    return await _call(env, "get", who, f"/api/v1/explain/{kind}/{record_id}", expect=expect)


async def _tool(env, who: str, name: str, confirmed_keys=None, **args) -> dict:
    """A chat tool as api/chat.py runs it: the person's selected ecosystem, commit on success."""
    p = PEOPLE[who]
    async with env.db() as session:
        result = await execute_tool(name, args, session, ecosystem_ids=[str(p.home)], caller_user_id=p.user_id,
                                    confirmed_keys=confirmed_keys)
        if result.get("success"):
            await session.commit()
    return result


async def _proposal(env, title: str = "Bike shed") -> str:
    created = await _call(env, "post", "ada", "/api/v1/proposals", expect=201,
                          json={"ecosystem_id": str(OASIS), "type": "policy", "title": title})
    proposal_id = created.json["id"]
    await _call(env, "post", "ada", f"/api/v1/proposals/{proposal_id}/status", expect=200, json={"status": "advice"})
    return proposal_id


async def _advise(env, who: str, proposal_id: str) -> None:
    await _call(env, "post", who, f"/api/v1/proposals/{proposal_id}/advice", expect=201, json={"content": f"{who} thinks it helps"})


async def _world(env) -> SimpleNamespace:
    """One of everything: a proposal in advice, a pending emergency, a conflict naming Cy, Cy's exit, Ben's audit draft."""
    proposal_id = await _proposal(env)
    emergency = (await _call(env, "post", "ben", "/api/v1/emergency/declare", expect=201,
                             json={"ecosystem_id": str(OASIS), "reason": "The hall is flooding"})).json
    case = (await _call(env, "post", "ada", "/api/v1/conflicts", expect=201, json={
        "ecosystem_id": str(OASIS), "title": "Noise at night", "description": "Music after midnight.",
        "party_member_ids": [str(PEOPLE["cy"].member_id)],
    })).json
    exit_record = (await _call(env, "post", "cy", "/api/v1/exit", expect=201,
                               json={"ecosystem_id": str(OASIS), "reason": "Moving away"})).json
    await _call(env, "post", "ben", "/api/v1/safeguards/audits", expect=201,
                json={"ecosystem_id": str(OASIS), "audit_scope": "Q4 health"})
    await _call(env, "post", "ari", f"/api/v1/agreements/{HOUSE_RULES}/consent", expect=201,
                json={"attestation": "I agree to the house rules."})
    return SimpleNamespace(proposal=proposal_id, emergency=emergency["id"], case=case["id"], exit=exit_record["id"])


# ---------------------------------------------------------------------------
# The queue (GET /me/next-steps): the dashboard and the bell
# ---------------------------------------------------------------------------

ADVISE = ("give_advice", "Bike shed")
COSIGN = ("cosign_emergency", "The hall is flooding")
ATTEST = ("attest_agreement", "House rules")
TRIAGE = ("triage_conflict", "Noise at night")
HANDOFF = ("exit_unwinding", "Cy is leaving Oasis")
AUDIT = ("finish_audit", "Q4 health")

# Who should see what once _world() has run; every rule is a policy predicate or a lifecycle row.
EXPECTED = {
    "ada": {COSIGN, ATTEST},  # wrote the proposal; reported the case (reads it, never triages it)
    "ben": {ADVISE, ATTEST, AUDIT},  # declared the emergency, so someone else co-signs
    "cy": {ADVISE, COSIGN, ATTEST},  # a named party never triages; a leaver does not hand over their own exit
    "mo": {ADVISE, COSIGN, ATTEST, TRIAGE, HANDOFF},
    "sol": {ADVISE, COSIGN, ATTEST, TRIAGE, HANDOFF},
    "ari": {ADVISE, COSIGN, TRIAGE, HANDOFF},  # already consented to the house rules
    "olu": set(),  # another ecosystem: nothing here is theirs
}


async def test_each_member_sees_exactly_the_items_waiting_for_them_and_the_bell_counts_them(env):
    await _world(env)
    for who, expected in EXPECTED.items():
        queue = await _queue(env, who)
        assert {(i["action"], i["title"]) for i in queue["items"]} == expected, who
        assert queue["count"] == len(expected), who  # the bell's number
    [cosign] = [i for i in (await _queue(env, "ada"))["items"] if i["kind"] == "emergency"]
    assert cosign["ecosystem"] == "Oasis" and cosign["link"].startswith("/emergency/") and cosign["due"].endswith("Z")
    assert "Ben declared it" in cosign["why"]


async def test_items_leave_the_queue_once_done_and_the_owner_decisions_shape_the_proposal_items(env):
    proposal_id = await _proposal(env)
    await _advise(env, "ben", proposal_id)
    assert ADVISE not in await _items(env, "ben") and ADVISE in await _items(env, "cy")

    # Advice closes on the proposer's call: no prompt before the deadline, and none for a steward.
    async with env.db() as session:
        await session.execute(update(Proposal).where(Proposal.id == uuid.UUID(proposal_id))
                              .values(advice_deadline=dt.date.today() + dt.timedelta(days=3)))
        await session.commit()
    assert await _items(env, "ada", "proposal") == set()
    async with env.db() as session:
        await session.execute(update(Proposal).where(Proposal.id == uuid.UUID(proposal_id))
                              .values(advice_deadline=dt.date.today() - dt.timedelta(days=1)))
        await session.commit()
    [prompt] = [i for i in (await _queue(env, "ada"))["items"] if i["kind"] == "proposal"]
    assert (prompt["action"], prompt["what"], prompt["overdue"]) == ("close_advice", ADVICE_DEADLINE_PROMPT, True)
    assert ("close_advice", "Bike shed") not in await _items(env, "mo")
    async with env.db() as session:
        assert (await session.get(Proposal, uuid.UUID(proposal_id))).status == "advice"  # the deadline moved nothing

    await _call(env, "post", "ada", f"/api/v1/proposals/{proposal_id}/status", expect=200, json={"status": "consent"})
    position = ("record_position", "Bike shed")
    assert all([position in await _items(env, who) for who in OASIS_MEMBERS])
    await _call(env, "post", "ben", f"/api/v1/proposals/{proposal_id}/consent", expect=201, json={"position": "consent"})
    # One position meets the default quorum, so consent moved on to test: nobody has a position left to record.
    assert all([position not in await _items(env, who) for who in OASIS_MEMBERS])

    await _call(env, "post", "ben", f"/api/v1/proposals/{proposal_id}/test", expect=201,
                json={"observations": "Bikes stayed dry all week.", "outcome": "passed"})
    ratify = ("confirm_ratification", "Bike shed")
    # A steward who did not write it confirms ratification; test reports never self-certify.
    assert {who for who in OASIS_MEMBERS if ratify in await _items(env, who)} == {"mo", "sol", "ari"}
    await _call(env, "post", "mo", f"/api/v1/proposals/{proposal_id}/status", expect=200, json={"status": "ratified"})
    assert all([await _items(env, who, "proposal") == set() for who in OASIS_MEMBERS])


async def test_a_proposal_without_an_advice_deadline_still_asks_its_author_to_close_advice_once_the_gate_is_met(env):
    proposal_id = await _proposal(env)  # no deadline set
    assert await _items(env, "ada", "proposal") == set()  # advice gate not met yet
    await _advise(env, "ben", proposal_id)
    [prompt] = [i for i in (await _queue(env, "ada"))["items"] if i["kind"] == "proposal"]
    assert (prompt["action"], prompt["what"], prompt["due"]) == ("close_advice", ADVICE_READY_PROMPT, None)
    assert ("close_advice", "Bike shed") not in await _items(env, "mo")


async def test_a_proposal_sent_back_asks_its_author_to_revise_until_advice_arrives_on_the_new_version(env):
    proposal_id = await _proposal(env)
    await _advise(env, "ben", proposal_id)
    await _call(env, "post", "ada", f"/api/v1/proposals/{proposal_id}/status", expect=200, json={"status": "consent"})
    await _call(env, "post", "mo", f"/api/v1/proposals/{proposal_id}/status", expect=200,
                json={"status": "advice", "note": "Add a rota for the key"})

    [revise] = [i for i in (await _queue(env, "ada"))["items"] if i["kind"] == "proposal"]
    assert revise["action"] == "revise" and "Add a rota for the key" in revise["why"]
    assert ADVISE in await _items(env, "ben")  # a fresh round: earlier advice was on the old version
    await _advise(env, "ben", proposal_id)
    assert await _items(env, "ada", "proposal") == {("close_advice", "Bike shed")}  # revise is done; no deadline, gate met


async def test_a_repair_check_in_that_has_come_due_is_on_the_triage_stewards_list(env):
    world = await _world(env)
    await _call(env, "put", "mo", f"/api/v1/conflicts/{world.case}", expect=200, json={"status": "triaged"})
    await _call(env, "post", "mo", f"/api/v1/conflicts/{world.case}/repair", expect=201, json={
        "title": "Quiet hours", "commitments": ["Music off by eleven"],
        "checkin_30_date": (dt.date.today() - dt.timedelta(days=2)).isoformat(),
    })
    for who in ("mo", "sol"):
        [checkin] = [i for i in (await _queue(env, who))["items"] if i["action"] == "repair_checkin"]
        assert checkin["overdue"] is True and "30-day check-in" in checkin["what"]
    assert all(i["kind"] != "conflict" for i in (await _queue(env, "cy"))["items"])  # a party, not the triage


# ---------------------------------------------------------------------------
# explain(): the status banner
# ---------------------------------------------------------------------------


async def test_explain_offers_exactly_the_moves_the_engine_accepts(env):
    world = await _world(env)
    await _advise(env, "ben", world.proposal)

    # Proposal: the banner's moves are the detail page's buttons (lifecycle table + manage rule).
    for who in ("ada", "ben", "mo"):
        detail = (await _call(env, "get", who, f"/api/v1/proposals/{world.proposal}", expect=200)).json
        explained = (await _explain(env, who, "proposal", world.proposal)).json
        assert [m["move"] for m in explained["your_moves"]] == [m["to"] for m in detail.get("allowed_next") or []], who
    explained = (await _explain(env, "ada", "proposal", world.proposal)).json
    assert (explained["state"], explained["decided_by"]) == ("Advice", "Ada or a steward")

    # Emergency: what each member may do with a pending declaration, then the move itself.
    moves = {who: [m["move"] for m in (await _explain(env, who, "emergency", world.emergency)).json["your_moves"]]
             for who in ("ada", "ben", "mo")}
    assert moves == {"ada": ["cosign"], "ben": ["withdraw"], "mo": ["cosign", "withdraw"]}
    await _call(env, "post", "ben", f"/api/v1/emergency/{world.emergency}/cosign", expect=403)
    await _call(env, "post", "ada", f"/api/v1/emergency/{world.emergency}/cosign", expect=200)
    page = (await _call(env, "get", "ada", f"/api/v1/emergency/{world.emergency}", expect=200)).json
    banner = (await _explain(env, "ada", "emergency", world.emergency)).json
    assert (banner["state"], banner["next_step"], banner["due_label"]) == ("Emergency in effect", page["next_step"], "Authority ends")

    # Exit: the steward's handoff, the leaver's withdrawal, nobody else's.
    moves = {who: [m["move"] for m in (await _explain(env, who, "exit", world.exit)).json["your_moves"]]
             for who in ("mo", "cy", "ben")}
    assert moves == {"mo": ["unwinding", "completed"], "cy": ["cancelled"], "ben": []}
    await _call(env, "post", "ben", f"/api/v1/exit/{world.exit}/status", expect=403, json={"new_status": "unwinding"})
    await _call(env, "post", "mo", f"/api/v1/exit/{world.exit}/status", expect=200, json={"new_status": "unwinding"})
    page = (await _call(env, "get", "cy", f"/api/v1/exit/{world.exit}", expect=200)).json
    assert (await _explain(env, "cy", "exit", world.exit)).json["next_step"] == page["next_step"]

    # Conflict: triage for a steward, withdrawal for the reporter, nothing for a named party.
    moves = {who: [m["move"] for m in (await _explain(env, who, "conflict", world.case)).json["your_moves"]]
             for who in ("mo", "ada", "cy")}
    assert moves == {"mo": ["triaged", "closed"], "ada": ["closed"], "cy": []}
    await _call(env, "put", "cy", f"/api/v1/conflicts/{world.case}", expect=403, json={"status": "triaged"})
    page = (await _call(env, "put", "mo", f"/api/v1/conflicts/{world.case}", expect=200, json={"status": "triaged"})).json
    banner = (await _explain(env, "cy", "conflict", world.case)).json
    assert (banner["state"], banner["next_step"], banner["decided_by"]) == (page["stage"], page["next_step"], page["decided_by"])

    # Agreement: the ceremony steward's next ceremony waits on its gate (409 until then); members attest.
    ceremony = (await _explain(env, "ari", "agreement", HOUSE_RULES)).json["your_moves"]
    assert ceremony == [{"move": "test", "label": "Start the test", "ready": False, "blocked": None}]
    await _call(env, "post", "ari", f"/api/v1/agreements/{HOUSE_RULES}/status", expect=409,
                json={"status": "test", "evidence": "Everyone has had a say"})
    assert [m["move"] for m in (await _explain(env, "ben", "agreement", HOUSE_RULES)).json["your_moves"]] == ["attest"]


async def test_a_hidden_conflict_is_not_listed_and_its_status_is_not_found(env):
    world = await _world(env)
    hidden = await _explain(env, "ben", "conflict", world.case, expect=404)
    page = await _call(env, "get", "ben", f"/api/v1/conflicts/{world.case}", expect=404)
    assert hidden.json == page.json == {"error": "Conflict case not found"}  # the same answer as a missing case
    await _explain(env, "olu", "conflict", world.case, expect=404)
    await _explain(env, "olu", "proposal", world.proposal, expect=404)
    assert (await _explain(env, "cy", "conflict", world.case)).json["waiting_on_you"] == []  # a party reads, never triages
    assert (await _explain(env, "ben", "decision", world.proposal, expect=400)).json["allowed"]


# ---------------------------------------------------------------------------
# The assistant reads and acts through the same source
# ---------------------------------------------------------------------------


async def test_the_assistant_reads_the_same_queue_and_the_same_status_words(env):
    world = await _world(env)
    for who in PEOPLE:
        asked = await _tool(env, who, "what_needs_me")
        assert asked["data"]["items"] == (await _queue(env, who))["items"], who
    for kind, record in (("proposal", world.proposal), ("emergency", world.emergency), ("exit", world.exit),
                         ("conflict", world.case), ("agreement", str(HOUSE_RULES))):
        said = await _tool(env, "mo", "explain_status", kind=kind, record=record)
        assert said["data"] == (await _explain(env, "mo", kind, record)).json, kind

    assert (await _tool(env, "ben", "get_conflict_case", case_id=world.case))["success"] is False  # hidden == not found
    case = (await _tool(env, "mo", "get_conflict_case", case_id=world.case))["data"]
    page = (await _call(env, "get", "mo", f"/api/v1/conflicts/{world.case}", expect=200)).json
    assert (case["stage"], case["next_step"], case["party_names"]) == (page["stage"], page["next_step"], ["Cy"])
    [own] = (await _tool(env, "cy", "get_exit_status"))["data"]["exits"]
    assert (own["state"], own["title"], [m["move"] for m in own["your_moves"]]) == ("Filed", "Your exit", ["cancelled"])


def _model_turn(text: str | None = None, calls: tuple[tuple[str, dict], ...] = ()):
    """One scripted completion shaped like litellm's response (the real model is never called)."""
    tool_calls = [SimpleNamespace(id=f"call-{uuid.uuid4().hex[:6]}",
                                  function=SimpleNamespace(name=name, arguments=json.dumps(args))) for name, args in calls]
    dumped = {"role": "assistant", "content": text or "", "tool_calls": [
        {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
        for c in tool_calls]}
    message = SimpleNamespace(content=text, tool_calls=tool_calls or None, model_dump=lambda: dumped)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="tool_calls" if calls else "stop")],
                           usage=None)


async def _chat(env, who: str, message: str, script: list, session_id: str | None = None):
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), \
         patch("neos_agent.api.chat.acompletion", new=AsyncMock(side_effect=script)):
        resp = await _call(env, "post", who, "/api/v1/chat/send", expect=200,
                           json={"message": message, "history": [], "session_id": session_id})
    events = []
    for block in resp.text.split("\n\n"):
        lines = block.split("\n")
        kind = next((line[7:] for line in lines if line.startswith("event: ")), None)
        if kind:
            events.append((kind, "\n".join(line[6:] for line in lines if line.startswith("data: "))))
    session = next(json.loads(data)["session_id"] for kind, data in events if kind == "session")
    return [json.loads(data) for kind, data in events if kind == "tool_result"], session


async def _emergency_state(env, emergency_id: str) -> str:
    async with env.db() as session:
        return (await session.get(EmergencyState, uuid.UUID(emergency_id))).state


async def test_cosigning_through_the_assistant_needs_the_members_yes_in_a_later_turn(env):
    world = await _world(env)
    cosign = {"emergency_id": world.emergency, "confirmed": True}

    # The declarer is refused outright: there is nothing to confirm.
    [refused], _ = await _chat(env, "ben", "Co-sign it.", [_model_turn(calls=(("cosign_emergency", cosign),)),
                                                           _model_turn("You declared it.")])
    assert "needs_confirmation" not in refused and "second member" in refused["error"]

    # The model cannot confirm for the member, not even in the turn that asked.
    results, session = await _chat(env, "ada", "Co-sign the flooding emergency.", [
        _model_turn(calls=(("cosign_emergency", {"emergency_id": world.emergency}),)),
        _model_turn(calls=(("cosign_emergency", cosign),)),
        _model_turn("Co-signing cannot be undone. Shall I?"),
    ])
    assert all("cannot be undone" in r["needs_confirmation"] for r in results)
    assert await _emergency_state(env, world.emergency) == "pending"

    await _chat(env, "ada", "Yes, co-sign it.", [_model_turn(calls=(("cosign_emergency", cosign),)), _model_turn("Done.")],
                session_id=session)
    assert await _emergency_state(env, world.emergency) == "open"
    assert COSIGN not in await _items(env, "cy")  # nothing left to co-sign


async def test_ending_authority_and_a_complete_review_wait_for_a_yes_and_recovery_is_a_stewards_item(env):
    world = await _world(env)
    await _call(env, "post", "ada", f"/api/v1/emergency/{world.emergency}/cosign", expect=200)

    key = f"end_emergency_authority:{world.emergency}"
    asked = await _tool(env, "ben", "end_emergency_authority", confirmed_keys=frozenset(), confirmed=True)
    assert (asked["success"], asked["confirmation_key"]) == (False, key)
    assert await _emergency_state(env, world.emergency) == "open"
    assert (await _tool(env, "ben", "end_emergency_authority", confirmed_keys=frozenset({key}), confirmed=True))["success"]
    assert await _emergency_state(env, world.emergency) == "half_open"

    # Owner default: the review is a steward's alarm; the declarer, co-signer and ender are excluded from it.
    review = ("record_review", "The hall is flooding")
    assert {who for who in OASIS_MEMBERS if review in await _items(env, who)} == {"mo", "sol", "ari"}

    args = {"outcome": "complete", "summary": "We met on Monday and kept the pumps."}
    asked = await _tool(env, "mo", "record_emergency_review", confirmed_keys=frozenset(), confirmed=True, **args)
    key = asked["confirmation_key"]
    assert key.startswith(f"record_emergency_review:{world.emergency}:complete:")
    # A yes to one summary is not a yes to another: the model cannot swap the text after the member agreed.
    changed = {**args, "summary": "Nothing happened; closing it."}
    again = await _tool(env, "mo", "record_emergency_review", confirmed_keys=frozenset({key}), confirmed=True, **changed)
    assert (again["success"], again["confirmation_key"]) == (False, again["confirmation_key"]) and again["confirmation_key"] != key
    assert await _emergency_state(env, world.emergency) != "closed"
    done = await _tool(env, "mo", "record_emergency_review", confirmed_keys=frozenset({key}), confirmed=True, **args)
    assert done["success"] and "close Recovery" in done["data"]["next_step"]
    assert {who for who in OASIS_MEMBERS if ("complete_recovery", "The hall is flooding") in await _items(env, who)} == {
        "mo", "sol", "ari"}
