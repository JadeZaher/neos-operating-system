"""G-Agent: the in-app assistant is easy and safe to use (uxqa/governance/plan.md, lane G-Agent).

Drives the chat tool dispatch (`execute_tool`, as api/chat.py calls it) and the real
POST /api/v1/chat/send with a scripted model over in-memory SQLite. Contracts:
src/neos_agent/agent/AGENTS.md.
"""

from __future__ import annotations

import datetime as _dt
import json
import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.agent.governance_tools import execute_tool
from neos_agent.agent.governance_tools import _needs_confirmation
from neos_agent.api.chat import chat_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.auth.ecosystem_scope import EcosystemScope
from neos_agent.services.act_gates import NEEDS_ANOTHER_STEWARD
from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    AgentSession,
    Agreement,
    AgreementCeremony,
    AgreementRequirement,
    Base,
    CircleMembership,
    ConflictCase,
    ConsentParticipant,
    Domain,
    Ecosystem,
    EmergencyState,
    ExitRecord,
    GovernanceHealthAudit,
    Member,
    Proposal,
    User,
)
from neos_agent.db.models import TestReport as ProposalTestReport  # aliased: pytest collects Test* names

OASIS = uuid.UUID("0000000b-0000-0000-0000-000000000001")
RIVER = uuid.UUID("0000000b-0000-0000-0000-000000000002")
SEED_LIBRARY = uuid.UUID("0000000b-0000-0000-0000-0000000000d1")
GATED_GARDEN = uuid.UUID("0000000b-0000-0000-0000-0000000000d2")
GARDEN_RULES = uuid.UUID("0000000b-0000-0000-0000-0000000000a1")
TOOL_HOURS = uuid.UUID("0000000b-0000-0000-0000-0000000000a2")


@dataclass(frozen=True)
class Person:
    key: str
    name: str
    role: str
    ecosystems: tuple[uuid.UUID, ...] = (OASIS,)

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"g-agent.{self.key}.user")

    def member_id(self, ecosystem: uuid.UUID = OASIS) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"g-agent.{self.key}.{ecosystem}")


PEOPLE = {p.key: p for p in (
    Person("ada", "Ada", "user"),  # writes the proposals
    Person("ben", "Ben", "user"),  # an ordinary member
    Person("mo", "Mo", "mod"),  # an ecosystem steward
    Person("ari", "Ari", "admin"),
    Person("fay", "Fay", "user", (OASIS, RIVER)),  # two ecosystems selected
    Person("sam1", "Sam Lee", "user"),
    Person("sam2", "Sam Ray", "user"),
    Person("olu", "Olu", "user", (RIVER,)),  # an outsider to Oasis
)}
BY_NAME = {p.name: p for p in PEOPLE.values()}


async def _seed(session: AsyncSession) -> None:
    session.add_all([Ecosystem(id=OASIS, name="Oasis", status="active"),
                     Ecosystem(id=RIVER, name="River House", status="active")])
    for p in PEOPLE.values():
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for p in PEOPLE.values():
        for eco in p.ecosystems:
            session.add(Member(
                id=p.member_id(eco), ecosystem_id=eco, user_id=p.user_id, member_id=f"MEM-{p.key}-{eco.hex[-1]}",
                display_name=p.name, current_status="active", role=p.role,
            ))
    await session.flush()
    session.add_all([
        Domain(id=SEED_LIBRARY, ecosystem_id=OASIS, domain_id="DOM-5EED0001", name="Seed Library", version="1.0",
               status="active", purpose="Saving, swapping and lending seeds.", steward_id=PEOPLE["mo"].member_id()),
        Domain(id=GATED_GARDEN, ecosystem_id=OASIS, domain_id="DOM-6A7E0002", version="1.0", status="active",
               purpose="Gated Garden — plots for members who agreed to the garden rules"),
        Agreement(id=GARDEN_RULES, ecosystem_id=OASIS, agreement_id="AGR-RULES", type="space", title="Garden rules",
                  version="1.0", status="active", proposer="Mo", requires_explicit_consent=True),
        Agreement(id=TOOL_HOURS, ecosystem_id=OASIS, agreement_id="AGR-TOOLS", type="space", title="Tool shed hours",
                  version="1.0", status="advice", proposer="Mo", text="Open on weekends.",
                  act_policy={"min_advice_rounds": 1, "consent_required": True, "test_cases": []}),
    ])
    await session.flush()
    session.add(AgreementRequirement(
        id=uuid.uuid4(), agreement_id=GARDEN_RULES, target_kind="domain_participation", target_id=GATED_GARDEN,
        enforcement="block_participation", is_active=True,
    ))
    await session.commit()


def _scope_for(person: Person) -> list[uuid.UUID]:
    return list(person.ecosystems)


def _create_app(session_factory) -> Sanic:
    """The chat blueprint; the x-test-as header signs a seeded person in with their ecosystems selected."""
    app = Sanic(f"test-g-agent-{uuid.uuid4().hex[:8]}")
    register_api_errors(app)
    app.ctx.db = session_factory

    @app.on_request
    async def sign_in(request):
        p = PEOPLE[request.headers["x-test-as"]]
        home = p.ecosystems[0]
        request.ctx.member = Member(
            id=p.member_id(home), ecosystem_id=home, user_id=p.user_id, member_id="MEM-AUTH",
            display_name=p.name, current_status="active", role=p.role,
        )
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = _scope_for(p)
        request.ctx.authorized_ecosystem_ids = _scope_for(p)
        names = {OASIS: "Oasis", RIVER: "River House"}
        request.ctx.ecosystem_scope = EcosystemScope.from_ecosystems(
            [SimpleNamespace(id=e, name=names[e]) for e in p.ecosystems], _scope_for(p),
        )

    app.blueprint(chat_api_bp)
    return app


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
    yield SimpleNamespace(db=factory, app=_create_app(factory))
    await engine.dispose()


async def _tool(env, who: str, name: str, /, scope: list | None = None, confirmed_keys=None, **args) -> dict:
    """Run a chat tool as api/chat.py does: the person's selected ecosystems as strings, commit on success."""
    person = PEOPLE[who]
    ids = [str(e) for e in (scope if scope is not None else _scope_for(person))]
    async with env.db() as session:
        result = await execute_tool(name, args, session, ecosystem_ids=ids, caller_user_id=person.user_id,
                                    confirmed_keys=confirmed_keys)
        if result.get("success"):
            await session.commit()
    return result


async def _proposal(env, *, title="Bike shed", status="advice", author="ada", policy=None, advice=()) -> Proposal:
    """A proposal written by `author`; `advice` is (advisor name, text[, member id]) entries in its first round.

    The member id defaults to the named person's (as the tools record it); pass None for a legacy name-only row.
    """
    prop = Proposal(
        id=uuid.uuid4(), ecosystem_id=OASIS, proposal_id=f"PROP-{uuid.uuid4().hex[:6].upper()}", type="policy",
        title=title, version="1.0", status=status, proposer=PEOPLE[author].name,
        proposer_member_id=PEOPLE[author].member_id(), decision_type="consent", act_policy=policy,
        proposed_change="Build a covered bike shed by the hall.", rationale="Bikes rust in the rain.",
    )
    async with env.db() as session:
        session.add(prop)
        if advice:
            log = AdviceLog(id=uuid.uuid4(), proposal_id=prop.id, advice_window_start=_dt.date.today())
            session.add(log)
            await session.flush()
            for advisor, text, *member in advice:
                member_id = member[0] if member else BY_NAME[advisor].member_id()
                session.add(AdviceEntry(id=uuid.uuid4(), advice_log_id=log.id, advisor=advisor, advice_text=text,
                                        member_id=member_id))
        await session.commit()
    return prop


async def _status(env, model, record_id) -> str:
    async with env.db() as session:
        return (await session.get(model, record_id)).status


# ---------------------------------------------------------------------------
# The real chat endpoint with a scripted model
# ---------------------------------------------------------------------------


def _model_turn(text: str | None = None, calls: tuple[tuple[str, dict], ...] = ()):
    """One completion: optional text and tool calls, shaped like litellm's response."""
    tool_calls = [
        SimpleNamespace(id=f"call-{uuid.uuid4().hex[:6]}", function=SimpleNamespace(name=name, arguments=json.dumps(args)))
        for name, args in calls
    ]
    dumped = {"role": "assistant", "content": text or "", "tool_calls": [
        {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
        for c in tool_calls
    ]}
    message = SimpleNamespace(content=text, tool_calls=tool_calls or None, model_dump=lambda: dumped)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="tool_calls" if calls else "stop")],
                           usage=None)


def _events(body: str) -> list[tuple[str, str]]:
    """The SSE stream as (event, data) pairs."""
    events = []
    for block in body.split("\n\n"):
        lines = block.split("\n")
        kind = next((line[7:] for line in lines if line.startswith("event: ")), None)
        if kind:
            events.append((kind, "\n".join(line[6:] for line in lines if line.startswith("data: "))))
    return events


async def _chat(env, who: str, message: str, script: list, session_id: str | None = None):
    """POST one member turn; returns the SSE events, the session id and the scripted model mock."""
    model = AsyncMock(side_effect=script)
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), \
         patch("neos_agent.api.chat.acompletion", new=model):
        _, response = await env.app.asgi_client.post(
            "/api/v1/chat/send", headers={"x-test-as": who},
            json={"message": message, "history": [], "session_id": session_id},
        )
    assert response.status == 200, response.text
    events = _events(response.text)
    session = next(json.loads(data)["session_id"] for kind, data in events if kind == "session")
    return events, session, model


def _tool_messages(model, completion: int) -> list[dict]:
    """The tool results the model was given on its `completion`-th call (0-based)."""
    return [json.loads(m["content"]) for m in model.call_args_list[completion].kwargs["messages"] if m.get("role") == "tool"]


async def test_long_results_reach_the_model_shrunk_with_every_key_never_as_a_stub(env):
    advisors = ("Ben", "Mo", "Ari")
    prop = await _proposal(env, policy={"min_advice_rounds": 2}, advice=[(n, f"{n} says: " + "x" * 800) for n in advisors])
    events, _, model = await _chat(env, "fay", "What's happening with this proposal?", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(prop.id)}),)),
        _model_turn("It is in advice."),
    ])

    [seen] = _tool_messages(model, 1)
    raw = json.dumps(seen)
    assert len(raw) <= 6000
    assert (seen["data"]["title"], seen["data"]["status"], seen["data"]["link"]) == ("Bike shed", "advice", f"/proposals/{prop.id}")
    assert [e["advisor"] for e in seen["data"]["advice_logs"][0]["entries"]] == list(advisors)
    assert "1 of 2" in seen["data"]["next_step"]
    # The member's screen gets the same shrunk result the model saw.
    shown = next(json.loads(data) for kind, data in events if kind == "tool_result")
    assert shown["data"] == seen["data"]


async def test_an_irreversible_act_waits_for_a_yes_given_in_a_later_turn(env):
    prop = await _proposal(env)
    withdraw = {"proposal_id": str(prop.id), "new_status": "withdrawn"}

    # The model cannot confirm on the member's behalf: not straight away, nor in the turn that asked.
    await _chat(env, "ada", "Withdraw my bike shed proposal.", [
        _model_turn(calls=(("update_proposal_status", {**withdraw, "confirmed": True}),)),
        _model_turn("Shall I?"),
    ])
    assert await _status(env, Proposal, prop.id) == "advice"
    events, session, _ = await _chat(env, "ada", "Withdraw my bike shed proposal.", [
        _model_turn(calls=(("update_proposal_status", withdraw),)),
        _model_turn(calls=(("update_proposal_status", {**withdraw, "confirmed": True}),)),
        _model_turn("Withdrawing ends it for good. Shall I go ahead?"),
    ])
    asked = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert all(r["success"] is False and "ends it for good" in r["needs_confirmation"] for r in asked)
    assert await _status(env, Proposal, prop.id) == "advice"

    # The member says yes in the next turn of the same conversation.
    await _chat(env, "ada", "Yes, withdraw it.", [
        _model_turn(calls=(("update_proposal_status", {**withdraw, "confirmed": True}),)),
        _model_turn("Done."),
    ], session_id=session)
    assert await _status(env, Proposal, prop.id) == "withdrawn"


@pytest.mark.parametrize("reply, preserved", [
    ("No, cancel", False),
    ("What does withdrawal mean?", True),
    ("Yes, but do not withdraw it.", True),
    ("Yes, send it.", True),
])
async def test_a_model_cannot_use_an_old_confirmation_after_a_decline_or_unrelated_reply(env, reply, preserved):
    prop = await _proposal(env)
    withdraw = {"proposal_id": str(prop.id), "new_status": "withdrawn"}
    _, session_id, _ = await _chat(env, "ada", "Withdraw my bike shed proposal.", [
        _model_turn(calls=(("update_proposal_status", withdraw),)),
        _model_turn("Withdrawing ends it for good. Shall I go ahead?"),
    ])
    events, _, _ = await _chat(env, "ada", reply, [
        _model_turn(calls=(("update_proposal_status", {**withdraw, "confirmed": True}),)),
        _model_turn("I will wait."),
    ], session_id=session_id)
    [result] = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert result["success"] is False
    assert await _status(env, Proposal, prop.id) == "advice"
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session_id))
        assert bool(saved.context["pending_confirmations"]) is preserved

    events, _, _ = await _chat(env, "ada", "Yes, go ahead", [
        _model_turn(calls=(("update_proposal_status", {**withdraw, "confirmed": True}),)),
        _model_turn("The tool has answered."),
    ], session_id=session_id)
    results = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert [result["success"] for result in results] == ([True] if preserved else [])
    assert await _status(env, Proposal, prop.id) == ("withdrawn" if preserved else "advice")


@pytest.mark.parametrize("link_style", ["omitted", "linked", "raw", "external", "code"])
async def test_successful_record_reads_always_leave_a_trusted_link_in_the_stream_and_saved_reply(env, link_style):
    prop = await _proposal(env, title="Bike [shed]")
    route = f"/proposals/{prop.id}"
    text = {
        "omitted": "Your proposal is in advice.", "linked": f"Read [the proposal]({route}).",
        "raw": f"Its path is {route}.", "external": f"Read [the proposal](https://example.com{route}).",
        "code": f"```\n[the proposal]({route})\n```",
    }[link_style]
    events, session_id, _ = await _chat(env, "ben", "Where does this proposal stand?", [
        _model_turn(calls=(("get_proposal", {"proposal_id": str(prop.id)}),)),
        _model_turn("It needs advice.", calls=(("get_proposal", {"proposal_id": str(prop.id)}),)),
        _model_turn(text),
    ])
    displayed = "".join(data for kind, data in events if kind == "append")
    if link_style == "linked":
        assert displayed.count(route) == 1
        assert "Related records:" not in displayed
    else:
        assert displayed.endswith(f"Related records: [Bike \\[shed\\]]({route})")
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session_id))
        replies = [m["content"] for m in saved.context["messages"] if m["role"] == "assistant"]
        assert "".join(replies).endswith(text if link_style == "linked" else f"Related records: [Bike \\[shed\\]]({route})")


async def test_failed_tools_cannot_add_a_record_reference_even_if_their_payload_has_a_link(env):
    route = f"/proposals/{uuid.uuid4()}"
    with patch("neos_agent.api.chat.execute_tool", new=AsyncMock(return_value={
        "success": False, "error": "Not found", "data": {"title": "Hidden record", "link": route},
    })):
        events, _, _ = await _chat(env, "ben", "Read the proposal.", [
            _model_turn(calls=(("get_proposal", {"proposal_id": str(uuid.uuid4())}),)),
            _model_turn("The proposal was not found."),
        ])
    assert route not in "".join(data for kind, data in events if kind == "append")


async def test_confirmation_binds_the_message_and_is_consumed_before_a_same_turn_replay(env):
    post_id = str(uuid.uuid4())
    key = f"respond:{post_id}"
    sent = []

    async def send(tool_name, args, db, **context):
        asked = _needs_confirmation(args, key, f"Send this exact message: {args['message']}?", context["confirmed_keys"])
        if asked:
            return asked
        sent.append(args["message"])
        return {"success": True, "data": {"message": "Sent"}}

    original = {"post": post_id, "message": "I can help on Saturday."}
    changed = {**original, "message": "I will pay the entire bill.", "confirmed": True}
    with patch("neos_agent.api.chat.execute_tool", new=AsyncMock(side_effect=send)):
        _, session_id, _ = await _chat(env, "ben", "Send my offer to help.", [
            _model_turn(calls=(("respond_to_share_need", original),)), _model_turn("Shall I send that exact message?"),
        ])
        events, _, _ = await _chat(env, "ben", "Yes, go ahead", [
            _model_turn(calls=(("respond_to_share_need", changed),)), _model_turn("The changed message needs your confirmation."),
        ], session_id=session_id)
        assert sent == [original["message"]]
        [result] = [json.loads(data) for kind, data in events if kind == "tool_result"]
        assert result["success"] is True

        events, _, _ = await _chat(env, "ben", "Yes, go ahead", [
            _model_turn(calls=(("respond_to_share_need", changed), ("respond_to_share_need", changed))),
            _model_turn("Sent once."),
        ], session_id=session_id)
        assert sent == [original["message"]]
        results = [json.loads(data) for kind, data in events if kind == "tool_result"]
        assert results == []
        async with env.db() as db:
            saved = await db.get(AgentSession, uuid.UUID(session_id))
            assert saved.context["pending_confirmations"] == []

        await _chat(env, "ben", "Yes, go ahead", [
            _model_turn(calls=(("respond_to_share_need", changed),)), _model_turn("That needs a new request."),
        ], session_id=session_id)
        assert sent == [original["message"]]


async def test_a_generic_yes_cannot_confirm_multiple_actions_and_reasking_one_narrows_the_choice(env):
    first = await _proposal(env, title="Bike shed")
    second = await _proposal(env, title="Tool library")
    actions = [{"proposal_id": str(prop.id), "new_status": "withdrawn"} for prop in (first, second)]
    _, session_id, _ = await _chat(env, "ada", "Withdraw both proposals.", [
        _model_turn(calls=tuple(("update_proposal_status", args) for args in actions)),
        _model_turn("Which withdrawal should I do first?"),
    ])
    events, _, _ = await _chat(env, "ada", "Yes", [
        _model_turn(calls=(("update_proposal_status", {**actions[0], "confirmed": True}),)),
        _model_turn("Confirm just the bike shed withdrawal?"),
    ], session_id=session_id)
    assert await _status(env, Proposal, first.id) == "advice"
    assert await _status(env, Proposal, second.id) == "advice"
    assert all(not json.loads(data)["success"] for kind, data in events if kind == "tool_result")
    await _chat(env, "ada", "Yes, withdraw it.", [
        _model_turn(calls=(("update_proposal_status", {**actions[0], "confirmed": True}),)), _model_turn("Withdrawn."),
    ], session_id=session_id)
    assert await _status(env, Proposal, first.id) == "withdrawn"
    assert await _status(env, Proposal, second.id) == "advice"


async def test_a_legacy_unbound_confirmation_requires_a_new_question(env):
    prop = await _proposal(env)
    withdraw = {"proposal_id": str(prop.id), "new_status": "withdrawn"}
    _, session_id, _ = await _chat(env, "ada", "Withdraw my proposal.", [
        _model_turn(calls=(("update_proposal_status", withdraw),)), _model_turn("Shall I withdraw it?"),
    ])
    async with env.db() as db:
        saved = await db.get(AgentSession, uuid.UUID(session_id))
        context = dict(saved.context)
        context["pending_confirmations"] = [{key: entry[key] for key in ("key", "at")} for entry in context["pending_confirmations"]]
        saved.context = context
        await db.commit()
    events, _, _ = await _chat(env, "ada", "Yes", [
        _model_turn(calls=(("update_proposal_status", {**withdraw, "confirmed": True}),)), _model_turn("Please confirm again."),
    ], session_id=session_id)
    assert await _status(env, Proposal, prop.id) == "advice"
    assert all(not json.loads(data)["success"] for kind, data in events if kind == "tool_result")


@pytest.mark.parametrize("route", [
    "https://example.com/proposals/00000000-0000-0000-0000-000000000001",
    "//example.com/proposals/00000000-0000-0000-0000-000000000001",
    "/proposals/not-a-record",
    "/proposals/00000000-0000-0000-0000-000000000001#member-text",
    "/discover?tab=shares-needs&post=not-a-record",
])
def test_record_reference_rejects_external_or_noncanonical_routes(route):
    from neos_agent.api.chat import _record_reference

    assert _record_reference({"link": route, "title": "A member's text"}) is None


# ---------------------------------------------------------------------------
# Confirmation contract, every irreversible tool
# ---------------------------------------------------------------------------


async def _counts(env) -> tuple:
    async with env.db() as session:
        return tuple([await session.scalar(select(func.count()).select_from(m)) for m in (EmergencyState, ExitRecord)])


@pytest.mark.parametrize("who, name, args, key", [
    ("ben", "declare_emergency", {"reason": "The hall is flooding"}, f"declare_emergency:{OASIS}"),
    ("ben", "create_exit_record", {}, f"create_exit_record:{OASIS}"),
])
async def test_irreversible_tools_write_only_after_an_earlier_confirmation(env, who, name, args, key):
    before = await _counts(env)
    for confirmed_keys, extra in ((frozenset(), {}), (frozenset(), {"confirmed": True})):
        asked = await _tool(env, who, name, confirmed_keys=confirmed_keys, **args, **extra)
        assert (asked["success"], asked["confirmation_key"]) == (False, key), asked
        assert await _counts(env) == before
    done = await _tool(env, who, name, confirmed_keys=frozenset({key}), **args, confirmed=True)
    assert done["success"] is True, done
    assert await _counts(env) != before


# ---------------------------------------------------------------------------
# Lookups, names and links
# ---------------------------------------------------------------------------


async def test_lookups_take_the_page_id_a_key_or_a_title_and_answer_with_the_page_link(env):
    prop = await _proposal(env, title="Kitchen rota")
    for key in (str(prop.id), prop.proposal_id.lower(), "kitchen rota"):
        read = await _tool(env, "ben", "get_proposal", proposal_id=key)
        assert (read["data"]["id"], read["data"]["link"]) == (str(prop.id), f"/proposals/{prop.id}"), key


async def test_domains_are_found_and_shown_by_name_never_by_code(env):
    seed = await _tool(env, "ben", "get_domain", domain="seed library")
    assert (seed["data"]["name"], seed["data"]["steward"], seed["data"]["link"]) == (
        "Seed Library", "Mo", f"/domains/{SEED_LIBRARY}")
    garden = await _tool(env, "ben", "get_domain", domain="Gated Garden")  # named only in its purpose label
    assert garden["data"]["name"] == "Gated Garden"
    listed = await _tool(env, "ben", "list_domains")
    assert {d["name"] for d in listed["data"]["domains"]} == {"Seed Library", "Gated Garden"}
    assert "DOM-" not in json.dumps([seed, garden, listed])


@pytest.mark.parametrize("who, listed, contact", [
    # Ben belongs to Oasis only: the private River House is hidden from him entirely.
    ("ben", ["Oasis"], {"Oasis": "hello@oasis.example", "River House": None}),
    # Olu belongs to River House only: public Oasis is visible, but its contact email is for members.
    ("olu", ["Oasis", "River House"], {"Oasis": None, "River House": "door@river.example"}),
])
async def test_ecosystems_follow_rest_visibility_and_contact_email_is_for_members(env, who, listed, contact):
    async with env.db() as session:
        (await session.get(Ecosystem, OASIS)).contact_email = "hello@oasis.example"
        river = await session.get(Ecosystem, RIVER)
        river.visibility, river.contact_email = "private", "door@river.example"
        await session.commit()

    found = await _tool(env, who, "list_ecosystems")
    assert [e["name"] for e in found["data"]["ecosystems"]] == listed
    for name, email in contact.items():
        read = await _tool(env, who, "get_ecosystem", name=name.split()[0].lower())  # partial name, any case
        if name not in listed:
            assert read == {"success": False, "error": f"Ecosystem '{name.split()[0].lower()}' not found."}
            continue
        assert (read["data"]["name"], read["data"]["contact_email"]) == (name, email)


@pytest.mark.parametrize("who, expected", [
    ("ben", ["Advice stage: 1 of 2 advice rounds have advice.", "You can give advice."]),
    ("mo", ["You already gave advice in this round."]),
    ("ada", ["you cannot advise on it yourself", "You can also withdraw it."]),
])
async def test_a_proposal_says_where_it_stands_and_what_the_caller_can_do(env, who, expected):
    prop = await _proposal(env, policy={"min_advice_rounds": 2}, advice=[("Mo", "Add a roof.")])
    read = await _tool(env, who, "get_proposal", proposal_id=str(prop.id))
    gates = read["data"]["gates"]["advice"]
    assert (gates["rounds"], gates["required_rounds"]) == (1, 2)
    for sentence in expected:
        assert sentence in read["data"]["next_step"], (who, read["data"]["next_step"])


async def _rename(env, who: str, name: str) -> None:
    """A member edits their own display name (self-service, so never an identity)."""
    async with env.db() as session:
        (await session.get(Member, PEOPLE[who].member_id())).display_name = name
        await session.commit()


async def test_standing_follows_member_ids_never_display_names(env):
    # A legacy name-only advice row "Ben" and Mo's own advice; then a legacy name-only objection "Ben".
    prop = await _proposal(env, status="consent", policy={"consent_quorum": 3},
                           advice=[("Ben", "Legacy advice.", None), ("Mo", "Add a roof.")])
    assert (await _tool(env, "mo", "record_consent_position", proposal_id=str(prop.id), position="consent"))["success"]
    async with env.db() as session:
        record_id = await session.scalar(select(ConsentParticipant.consent_record_id))
        session.add(ConsentParticipant(id=uuid.uuid4(), consent_record_id=record_id, name="Ben", position="object",
                                       reason="Legacy objection."))
        await session.commit()
    await _rename(env, "ari", "Ben")  # Ari now shows as "Ben" and must inherit nothing

    async def standing(who):
        you = (await _tool(env, who, "get_proposal", proposal_id=str(prop.id)))["data"]["you"]
        return you["has_advised_this_round"], you["my_position"]

    assert [await standing(who) for who in ("ben", "ari", "mo")] == [(False, None), (False, None), (True, "consent")]
    await _tool(env, "ben", "record_consent_position", proposal_id=str(prop.id), position="stand_aside",
                reason="Not my area.")
    assert await standing("ben") == (False, "stand_aside")
    assert await standing("ari") == (False, None)


# ---------------------------------------------------------------------------
# Scope: a member with nothing selected reads nothing; several selected means asking which
# ---------------------------------------------------------------------------


async def test_an_empty_scope_reads_nothing(env):
    await _proposal(env)
    assert (await _tool(env, "ben", "search_proposals"))["data"]["count"] == 1
    for scope in ([], None):
        async with env.db() as session:
            result = await execute_tool("search_proposals", {}, session, ecosystem_ids=scope,
                                        caller_user_id=PEOPLE["ben"].user_id)
        assert result["data"]["count"] == 0, scope


async def test_creating_with_two_ecosystems_selected_asks_which(env):
    draft = {"title": "Seed swap", "type": "policy", "proposed_change": "Hold a seed swap.", "rationale": "Share seeds."}
    asked = await _tool(env, "fay", "create_proposal", **draft)
    assert asked["success"] is False
    assert "Oasis" in asked["error"] and "River House" in asked["error"]
    created = await _tool(env, "fay", "create_proposal", **draft, ecosystem="River House")
    async with env.db() as session:
        rows = (await session.execute(select(Proposal.ecosystem_id).where(Proposal.title == "Seed swap"))).scalars().all()
    assert (created["success"], rows) == (True, [RIVER])


# ---------------------------------------------------------------------------
# Member actions the assistant was missing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("who, domain, joined", [
    ("ben", "Seed Library", True),
    ("ben", "Gated Garden", False),  # needs consent to "Garden rules" first
    ("olu", "Seed Library", False),  # another ecosystem's domain is not found
])
async def test_joining_a_domain_follows_its_agreement_gate(env, who, domain, joined):
    result = await _tool(env, who, "join_domain", domain=domain)
    assert result["success"] is joined, result
    if domain == "Gated Garden":
        assert result["required_agreements"] == [{"id": str(GARDEN_RULES), "title": "Garden rules", "version": "1.0", "href": f"/agreements/{GARDEN_RULES}"}]
    async with env.db() as session:
        rows = (await session.execute(select(CircleMembership.member_id, CircleMembership.status))).all()
    assert rows == ([(PEOPLE[who].member_id(), "active")] if joined else [])


async def test_a_test_report_is_evidence_and_a_steward_confirms_ratification(env):
    prop = await _proposal(env, status="test")
    unknown = await _tool(env, "ben", "submit_test_report", proposal_id=str(prop.id), outcome="passed",
                          observations="Bikes stayed dry.", met_cases=["Dry bikes"])
    assert unknown["success"] is False and "declares none" in unknown["error"]

    filed = await _tool(env, "ben", "submit_test_report", proposal_id=str(prop.id), outcome="passed",
                        observations="Bikes stayed dry all week.")
    assert filed["success"] is True, filed
    assert (filed["data"]["status"], filed["data"]["gates"]["test"]["met"]) == ("test", True)
    assert "a steward who did not write it confirms" in filed["data"]["next_step"]
    async with env.db() as session:
        assert await session.scalar(select(func.count()).select_from(ProposalTestReport)) == 1

    ratify = {"proposal_id": str(prop.id), "new_status": "ratified"}
    assert (await _tool(env, "ada", "update_proposal_status", **ratify, confirmed=True))["success"] is False
    asked = await _tool(env, "mo", "update_proposal_status", **ratify)
    assert "cannot be undone" in asked["needs_confirmation"]
    assert await _status(env, Proposal, prop.id) == "test"
    done = await _tool(env, "mo", "update_proposal_status", **ratify, confirmed=True)
    assert done["data"]["new_status"] == "ratified", done


async def test_a_steward_who_wrote_the_proposal_is_told_another_steward_confirms(env):
    prop = await _proposal(env, status="test", author="mo")
    await _tool(env, "ben", "submit_test_report", proposal_id=str(prop.id), outcome="passed", observations="Worked.")

    refused = await _tool(env, "mo", "update_proposal_status", proposal_id=str(prop.id), new_status="ratified",
                          confirmed=True)
    assert refused == {"success": False, "error": NEEDS_ANOTHER_STEWARD}  # plain words, not a generic failure
    read = await _tool(env, "mo", "get_proposal", proposal_id=str(prop.id))
    [ratify] = [move for move in read["data"]["your_moves"] if move["to"] == "ratified"]
    assert ratify["blocked"] == "needs_another_steward"
    assert await _status(env, Proposal, prop.id) == "test"


async def test_agreement_evidence_moves_the_agreement_through_its_gate(env):
    outsider = await _tool(env, "olu", "record_agreement_evidence", agreement_id="AGR-TOOLS", stage="advice", note="Held")
    assert outsider["success"] is False
    recorded = await _tool(env, "ben", "record_agreement_evidence", agreement_id="tool shed hours", stage="advice",
                           note="Advice round held at the Sunday circle")
    assert recorded["success"] is True, recorded
    assert recorded["data"]["auto_transitions"] == ["advice->consent"]
    assert await _status(env, Agreement, TOOL_HOURS) == "consent"


async def test_evidence_that_would_put_an_agreement_in_force_waits_for_a_yes_in_a_later_turn(env):
    quiet = uuid.uuid4()
    async with env.db() as session:
        session.add(Agreement(id=quiet, ecosystem_id=OASIS, agreement_id="AGR-QUIET", type="space", title="Quiet hours",
                              version="1.0", status="test", proposer="Mo",
                              act_policy={"min_advice_rounds": 1, "consent_required": True, "test_cases": []}))
        await session.commit()

    async def evidence_rows():
        async with env.db() as session:
            return await session.scalar(select(func.count()).select_from(AgreementCeremony).where(
                AgreementCeremony.agreement_id == quiet, AgreementCeremony.outcome == "evidence"))

    evidence = {"agreement_id": "Quiet hours", "stage": "test", "note": "A quiet week, no complaints."}
    events, session_id, _ = await _chat(env, "ben", "Record our test evidence for quiet hours.", [
        _model_turn(calls=(("record_agreement_evidence", evidence),)),
        _model_turn(calls=(("record_agreement_evidence", {**evidence, "confirmed": True}),)),  # same turn: no
        _model_turn("That puts it in force. Shall I go ahead?"),
    ])
    asked = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert len(asked) == 2 and all("binding for every member of Oasis" in r["needs_confirmation"] for r in asked), asked
    assert (await _status(env, Agreement, quiet), await evidence_rows()) == ("test", 0)

    events, _, _ = await _chat(env, "ben", "Yes.", [
        _model_turn(calls=(("record_agreement_evidence", {**evidence, "confirmed": True}),)),
        _model_turn("Done: it is in force."),
    ], session_id=session_id)
    [done] = [json.loads(data) for kind, data in events if kind == "tool_result"]
    assert done["data"]["auto_transitions"] == ["test->active"], done
    assert (await _status(env, Agreement, quiet), await evidence_rows()) == ("active", 1)


async def test_consent_through_the_assistant_is_one_position_per_member_and_only_its_owner_lifts_it(env):
    prop = await _proposal(env, status="consent", policy={"consent_quorum": 3})  # stays in consent
    await _tool(env, "ben", "record_consent_position", proposal_id=str(prop.id), position="consent", participant="Ada")
    changed = await _tool(env, "ben", "record_consent_position", proposal_id=str(prop.id), position="objection",
                          reason="All weekend shifts land on newcomers.")
    assert changed["data"]["gates"]["consent"]["open_objections"] == 1
    async with env.db() as session:
        rows = (await session.execute(select(ConsentParticipant.name, ConsentParticipant.position))).all()
    assert [tuple(r) for r in rows] == [("Ben", "object")]

    # Only Ben can lift Ben's objection; withdrawing his position does.
    assert (await _tool(env, "mo", "withdraw_consent_position", proposal_id=str(prop.id)))["success"] is False
    lifted = await _tool(env, "ben", "withdraw_consent_position", proposal_id=str(prop.id))
    assert lifted["data"]["gates"]["consent"]["open_objections"] == 0, lifted


# ---------------------------------------------------------------------------
# G-Care hand-offs: conflicts and audits through the assistant
# ---------------------------------------------------------------------------


NOISE = {"title": "Noise at night", "description": "Music after midnight."}


async def _cases(env) -> list[ConflictCase]:
    async with env.db() as session:
        return list((await session.execute(select(ConflictCase))).scalars().all())


@pytest.mark.parametrize("parties, outcome", [
    (["Ada"], ["ada"]),
    ([str(PEOPLE["sam1"].member_id())], ["sam1"]),
    (["  sam   LEE "], ["sam1"]),  # the full name, case and spacing ignored
    (["Sam"], "No member is called exactly 'Sam'. Members with similar names: Sam Lee, Sam Ray."),  # no first-name shortcut
    (["Zed"], "No member is called exactly 'Zed'. Ask the member"),
])
async def test_conflict_parties_resolve_by_full_name_and_the_member_confirms_who(env, parties, outcome):
    asked = await _tool(env, "ben", "create_conflict_case", **NOISE, parties=parties)
    assert await _cases(env) == []
    if isinstance(outcome, str):
        assert asked["success"] is False and outcome in asked["error"], asked
        return
    expected = [{"name": PEOPLE[k].name, "id": str(PEOPLE[k].member_id())} for k in outcome]
    assert asked["parties"] == expected
    assert f"names {expected[0]['name']} as the people involved" in asked["needs_confirmation"]

    done = await _tool(env, "ben", "create_conflict_case", **NOISE, parties=parties,
                       confirmed_keys=frozenset({asked["confirmation_key"]}), confirmed=True)
    assert done["success"] is True, done
    [case] = await _cases(env)
    assert (case.parties["member_ids"], case.reporter_id) == ([p["id"] for p in expected], PEOPLE["ben"].member_id())


@pytest.mark.parametrize("ari_renamed_to, named, shown", [
    ("Sam", "Sam", "names Sam (not Sam Lee or Sam Ray) as the people involved"),  # a short name says who it is not
    ("sam  LEE", "Sam Lee", "2 members are called 'Sam Lee'"),  # a look-alike makes the full name ambiguous
])
async def test_a_member_renamed_to_look_like_another_never_slips_into_a_case(env, ari_renamed_to, named, shown):
    await _rename(env, "ari", ari_renamed_to)
    result = await _tool(env, "ben", "create_conflict_case", **NOISE, parties=[named])
    assert shown in json.dumps(result), result
    assert await _cases(env) == []


async def test_a_confirmation_covers_only_the_people_the_member_saw(env):
    asked = await _tool(env, "ben", "create_conflict_case", **NOISE, parties=["Sam Lee"])
    # Between the turns the name moves to someone else: the yes no longer applies.
    await _rename(env, "sam1", "Sam Leeds")
    await _rename(env, "ari", "Sam Lee")
    again = await _tool(env, "ben", "create_conflict_case", **NOISE, parties=["Sam Lee"],
                        confirmed_keys=frozenset({asked["confirmation_key"]}), confirmed=True)
    assert again["parties"] == [{"name": "Sam Lee", "id": str(PEOPLE["ari"].member_id())}]
    assert await _cases(env) == []


async def test_triage_keeps_fields_it_was_not_given_and_follows_the_case_table(env):
    reported = await _tool(env, "ben", "create_conflict_case", title="Noise", description="Music late.")
    case_key = reported["data"]["case_id"]
    async with env.db() as session:
        case = await session.scalar(select(ConflictCase).where(ConflictCase.case_id == case_key))
        case.root_cause_category = "shared walls"
        await session.commit()

    assert (await _tool(env, "olu", "triage_conflict", case_id=case_key, tier=1))["error"].endswith("not found.")
    triaged = await _tool(env, "mo", "triage_conflict", case_id=case_key, tier=2)
    assert triaged["data"]["status"] == "triaged", triaged
    async with env.db() as session:
        case = await session.scalar(select(ConflictCase).where(ConflictCase.case_id == case_key))
        assert (case.tier, case.root_cause_category) == (2, "shared walls")
        case.status = "resolved"
        await session.commit()
    again = await _tool(env, "mo", "triage_conflict", case_id=case_key, tier=1)
    assert again["success"] is False and "Allowed: in_progress, closed" in again["error"]


async def test_an_assistant_audit_is_a_draft_owned_by_its_human_auditor(env):
    started = await _tool(env, "ben", "create_safeguard_audit", findings="Participation is healthy.", auditor="Mo")
    async with env.db() as session:
        audit = await session.scalar(select(GovernanceHealthAudit))
    assert (audit.status, audit.auditor_ids, audit.trigger_type) == ("draft", [str(PEOPLE["ben"].member_id())], "human")
    assert started["data"]["link"] == f"/safeguards/audits/{audit.id}"
