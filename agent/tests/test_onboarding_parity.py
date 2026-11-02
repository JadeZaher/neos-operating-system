"""G-Onboard parity: REST, the MCP server and the chat assistant join, consent and move members by the same rules.

Each surface calls member_lifecycle (place_member, move_member) or agreements.record_member_consent, so a refusal
on one is a refusal on all and an act writes the same transition row. Rules: src/neos_agent/api/AGENTS.md
"Onboarding (G-Onboard)".
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp.server.fastmcp")

import uuid  # noqa: E402

from sqlalchemy import func, select  # noqa: E402

from neos_agent import mcp_server  # noqa: E402
from neos_agent.agent.governance_tools import execute_tool  # noqa: E402
from neos_agent.db.models import Ecosystem, Member, User  # noqa: E402

from .test_onboarding_flows import (  # noqa: E402,F401 — world is the shared fixture
    ESCHER, GATE_AGREEMENT, HIDDEN, OASIS, OMNIONE, PEOPLE, agreement_only, call, row_id, status_of, transitions, world,
)


class Surfaces:
    """One adapter per surface; each returns ("ok", payload) or ("refused", code or words)."""

    def __init__(self, world, monkeypatch):
        self.world = world
        self.acting: dict[str, str] = {}

        async def fake_caller(ctx):
            person = PEOPLE[self.acting["who"]]
            return mcp_server.Caller(user=User(id=person.user_id, display_name=person.key.title()), token=None)

        monkeypatch.setattr(mcp_server, "_caller", fake_caller)
        monkeypatch.setattr(mcp_server, "_db", lambda: world.db)

    async def chat(self, who: str, tool: str, **args):
        person = PEOPLE[who]
        scope = [eco for eco, (status, *_rest) in person.rows.items() if status == "active"]
        async with self.world.db() as session:
            result = await execute_tool(tool, {**args, "confirmed": True}, session, ecosystem_ids=scope,
                                        caller_user_id=person.user_id)
        return ("ok", result["data"]) if result["success"] else ("refused", result.get("code") or result["error"])

    async def mcp_join(self, who: str, ecosystem_id):
        self.acting["who"] = who
        try:
            return "ok", await mcp_server.join_ecosystem(str(ecosystem_id), ctx=None, confirm=True)
        except ValueError as refusal:
            return "refused", str(refusal)


async def _rows_in(world, ecosystem_id) -> int:
    async with world.db() as session:
        return await session.scalar(select(func.count()).select_from(Member).where(Member.ecosystem_id == ecosystem_id))


async def test_a_private_ecosystem_cannot_be_joined_on_any_surface(world, monkeypatch):
    surfaces = Surfaces(world, monkeypatch)
    rest = await call(world, "post", "mia", f"/api/v1/ecosystems/{HIDDEN}/join")
    assert (rest.status, rest.json["error"]) == (404, "Ecosystem not found")
    assert await surfaces.mcp_join("mia", HIDDEN) == ("refused", "Ecosystem not found")
    assert await surfaces.chat("mia", "join_ecosystem", ecosystem="Hidden Grove") == ("refused", "Ecosystem not found")
    assert await _rows_in(world, HIDDEN) == 0


@pytest.mark.parametrize("surface", ["rest", "mcp", "chat"])
async def test_joining_writes_the_same_row_and_transition_on_every_surface(world, monkeypatch, surface):
    surfaces = Surfaces(world, monkeypatch)
    if surface == "rest":
        response = await call(world, "post", "mia", f"/api/v1/ecosystems/{OASIS}/join")
        outcome = ("ok", response.json) if response.status == 201 else ("refused", response.json)
    elif surface == "mcp":
        outcome = await surfaces.mcp_join("mia", OASIS)
    else:
        outcome = await surfaces.chat("mia", "join_ecosystem", ecosystem="Oasis")
    assert outcome[0] == "ok", outcome
    assert (outcome[1]["status"], outcome[1]["membership_status"]) == ("joined", "active")
    assert [t[1:3] for t in await transitions(world, await row_id(world, "mia", OASIS))] == [("active", "joined")]
    # A second join is refused the same way everywhere: already a member.
    again = await call(world, "post", "mia", f"/api/v1/ecosystems/{OASIS}/join")
    assert (again.status, again.json["code"]) == (409, "ALREADY_MEMBER")
    assert await surfaces.mcp_join("mia", OASIS) == ("refused", "ALREADY_MEMBER: You are already a member of Oasis.")
    assert await surfaces.chat("mia", "join_ecosystem", ecosystem="Oasis") == ("refused", "ALREADY_MEMBER")


async def test_the_chat_refuses_a_name_two_ecosystems_share_instead_of_guessing(world, monkeypatch):
    # A lookalike "oasis" founded later (review A12): "join Oasis" must not place Mia in whichever row comes back first.
    lookalike = uuid.UUID(int=15)
    async with world.db() as session:
        session.add(Ecosystem(id=lookalike, name="oasis", status="active", visibility="public"))
        await session.commit()
    surfaces = Surfaces(world, monkeypatch)
    before = (await _rows_in(world, OASIS), await _rows_in(world, lookalike))
    assert await surfaces.chat("mia", "join_ecosystem", ecosystem="Oasis") == ("refused", "AMBIGUOUS_ECOSYSTEM")
    assert (await _rows_in(world, OASIS), await _rows_in(world, lookalike)) == before
    # Named by id, the join goes ahead.
    assert (await surfaces.chat("mia", "join_ecosystem", ecosystem_id=str(lookalike)))[0] == "ok"


async def test_the_chat_asks_before_joining_and_writes_nothing_until_the_member_says_yes(world):
    person = PEOPLE["mia"]
    async with world.db() as session:
        asked = await execute_tool("join_ecosystem", {"ecosystem": "Oasis"}, session, ecosystem_ids=[OMNIONE],
                                   caller_user_id=person.user_id, confirmed_keys=frozenset())
    assert (asked["success"], "member of Oasis" in asked["needs_confirmation"]) == (False, True)
    assert await _rows_in(world, OASIS) == len([p for p in PEOPLE.values() if OASIS in p.rows])


@pytest.mark.usefixtures("agreement_only")
async def test_a_pending_newcomer_consents_through_the_assistant_and_is_active_with_one_transition(world, monkeypatch):
    surfaces = Surfaces(world, monkeypatch)
    nia = PEOPLE["nia"].member_id(OMNIONE)
    # Nia is active nowhere, so the chat's scope is empty; the consent gate's agreements are still hers to consent to.
    outcome = await surfaces.chat("nia", "attest_agreement_consent", agreement_id=str(GATE_AGREEMENT),
                                  attestation="I consent to the Universal Agreement Field")
    assert outcome[0] == "ok", outcome
    assert outcome[1]["membership_status"] == "active"
    assert [t[:3] for t in await transitions(world, nia)] == [("pending_consent", "active", "consent")]


@pytest.mark.parametrize("surface", ["rest", "chat"])
async def test_a_steward_confirms_a_stuck_newcomer_with_the_same_record_on_each_surface(world, monkeypatch, surface):
    surfaces = Surfaces(world, monkeypatch)
    tess, eve = PEOPLE["tess"].member_id(ESCHER), PEOPLE["eve"].member_id(ESCHER)
    if surface == "rest":
        response = await call(world, "post", "eve", f"/api/v1/members/{tess}/status", json={"status": "active"})
        assert response.status == 200, response.text
    else:
        assert (await surfaces.chat("eve", "move_member", member=str(tess), status="active"))[0] == "ok"
    assert await transitions(world, tess) == [("pending_consent", "active", "steward_move", eve)]


@pytest.mark.parametrize("who, target, ecosystem, status, code", [
    ("sam", "nia", OMNIONE, "active", "CONSENT_REQUIRED"),  # no approval while consent is missing (owner decision)
    ("sam", "ola", OMNIONE, "suspended", None),             # rank: refused with words, no code
    ("sam", "mia", OMNIONE, "exited", "USE_EXIT_FLOW"),
])
@pytest.mark.usefixtures("agreement_only")
async def test_refused_moves_are_refused_alike_by_rest_and_chat(world, monkeypatch, who, target, ecosystem, status, code):
    surfaces = Surfaces(world, monkeypatch)
    target_id = PEOPLE[target].member_id(ecosystem)
    before = await status_of(world, target_id)
    rest = await call(world, "post", who, f"/api/v1/members/{target_id}/status", json={"status": status})
    chat = await surfaces.chat(who, "move_member", member=str(target_id), status=status)
    assert rest.json.get("code") == code
    assert chat == ("refused", code or rest.json["error"])
    assert await status_of(world, target_id) == before and await transitions(world, target_id) == []
