"""UX-QA pass 01: REST, the MCP agent tools and the chat assistant apply one ACT rule set.

Separate from test_uxqa_p1_governance.py so an environment without the `mcp`
package (or with an incompatible 2.x) skips only this module instead of
failing collection for the whole run. `mcp>=1,<2` is a declared dependency.
The parity table is documented in src/neos_agent/api/AGENTS.md "ACT parity".
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest

pytest.importorskip("mcp.server.fastmcp")

from sqlalchemy import select  # noqa: E402

from neos_agent import mcp_server  # noqa: E402
from neos_agent.agent.governance_tools import execute_tool  # noqa: E402
from neos_agent.api.agreements import CEREMONY_DENIED  # noqa: E402
from neos_agent.api.proposals import MANAGE_DENIED, SELF_ADVICE_DENIED  # noqa: E402
from neos_agent.db.models import AdviceEntry, Agreement, Proposal, User  # noqa: E402
from neos_agent.services.act_gates import ADVICE_CLOSE_PROPOSER_ONLY, PROPOSER_CLOSES_ADVICE  # noqa: E402
from neos_agent.services.dates import aoe_today  # noqa: E402

from .test_uxqa_p1_governance import (  # noqa: E402,F401 — env is the shared fixture
    ECO,
    GARDEN_AGREEMENT,
    PEOPLE,
    Person,
    _call,
    _create_proposal,
    _open_for_advice,
    env,
)

GATE_UNMET = "The advice gate is not satisfied"


async def test_mcp_tools_apply_authorship_rules(env, monkeypatch):
    acting: dict[str, Person] = {}

    async def fake_caller(ctx):
        p = acting["who"]
        return mcp_server.Caller(user=User(id=p.user_id, display_name=p.name), token=None)

    monkeypatch.setattr(mcp_server, "_caller", fake_caller)
    monkeypatch.setattr(mcp_server, "_db", lambda: env.db)

    acting["who"] = PEOPLE["ada"]
    created = await mcp_server.create_proposal(str(ECO), "Shared tool shed", ctx=None)
    async with env.db() as session:
        stored = await session.scalar(select(Proposal).where(Proposal.proposal_id == created["proposal_id"]))
    assert stored.proposer_member_id == PEOPLE["ada"].member_id

    acting["who"] = PEOPLE["ben"]
    with pytest.raises(ValueError, match=MANAGE_DENIED):
        await mcp_server.transition_proposal(created["id"], "advice", ctx=None)

    acting["who"] = PEOPLE["ada"]
    assert (await mcp_server.transition_proposal(created["id"], "advice", ctx=None))["status"] == "advice"
    with pytest.raises(ValueError, match=SELF_ADVICE_DENIED):
        await mcp_server.record_proposal_advice(created["id"], "Looks right to me", ctx=None)

    acting["who"] = PEOPLE["ben"]
    advised = await mcp_server.record_proposal_advice(created["id"], "Add a sign-out sheet", ctx=None)
    assert advised["auto_transitions"] == []  # the proposer closes advice (owner decision)
    async with env.db() as session:
        [entry] = (await session.execute(select(AdviceEntry))).scalars().all()
    assert entry.member_id == PEOPLE["ben"].member_id  # standing is matched by id, never by name
    with pytest.raises(ValueError, match=MANAGE_DENIED):  # a refusal comes before any question
        await mcp_server.transition_proposal(created["id"], "withdrawn", ctx=None)

    # Withdrawing cannot be undone: without confirm=true nothing changes and the agent is told what would.
    acting["who"] = PEOPLE["mo"]
    asked = await mcp_server.transition_proposal(created["id"], "withdrawn", ctx=None)
    assert (asked["status"], "ends it for good" in asked["needs_confirmation"]) == ("advice", True)
    async with env.db() as session:
        assert (await session.get(Proposal, uuid.UUID(created["id"]))).status == "advice"
    done = await mcp_server.transition_proposal(created["id"], "withdrawn", ctx=None, confirm=True)
    assert (done["status"], "needs_confirmation" in done) == ("withdrawn", False)


# ---------------------------------------------------------------------------
# Parity table: the same ACT script through each surface yields the same outcomes
# ---------------------------------------------------------------------------


class Surfaces:
    """One adapter per surface: each action returns ("ok", auto_transitions) or ("refused", error text)."""

    def __init__(self, env, monkeypatch):
        self.env = env
        self.acting: dict[str, Person] = {}

        async def fake_caller(ctx):
            p = self.acting["who"]
            return mcp_server.Caller(user=User(id=p.user_id, display_name=p.name), token=None)

        monkeypatch.setattr(mcp_server, "_caller", fake_caller)
        monkeypatch.setattr(mcp_server, "_db", lambda: env.db)

    async def rest(self, who, action, proposal, **args):
        paths = {
            "move": ("/status", {"status": args.get("status")}),
            "advise": ("/advice", {"content": args.get("text")}),
            "position": ("/consent", {"member_name": "Anyone", "position": args.get("position"),
                                      "objection_text": args.get("reason")}),
        }
        if action == "ceremony":
            url = f"/api/v1/agreements/{GARDEN_AGREEMENT}/status"
            body = {"status": args["status"], "evidence": args["evidence"]}
        else:
            path, body = paths[action]
            url = f"/api/v1/proposals/{proposal['id']}{path}"
        resp = await _call(self.env.app, "post", who, url, json=body)
        if resp.status >= 400:  # a coded refusal reads "CODE: message", as MCP renders it
            return ("refused", ": ".join(filter(None, (resp.json.get("code"), resp.json["error"]))))
        return ("ok", resp.json.get("auto_transitions", []))

    async def mcp(self, who, action, proposal, **args):
        self.acting["who"] = PEOPLE[who]
        calls = {
            # A confirmed owner, as the chat adapter below; the confirm step is covered in the test above.
            "move": lambda: mcp_server.transition_proposal(proposal["id"], args.get("status", ""), ctx=None, confirm=True),
            "advise": lambda: mcp_server.record_proposal_advice(proposal["id"], args.get("text", ""), ctx=None),
            "position": lambda: mcp_server.submit_proposal_consent(
                proposal["id"], args.get("position", ""), ctx=None, objection_text=args.get("reason")),
            "ceremony": lambda: mcp_server.transition_agreement(
                str(GARDEN_AGREEMENT), args.get("status", ""), args.get("evidence", ""), ctx=None),
        }
        try:
            result = await calls[action]()
        except ValueError as refusal:
            return ("refused", str(refusal))
        return ("ok", result["auto_transitions"])

    async def chat(self, who, action, proposal, **args):
        tool, tool_args = {
            # A confirmed member: the chat's two-turn confirmation is covered in test_g_agent_assistant.py.
            "move": ("update_proposal_status", {"proposal_id": proposal["id"], "new_status": args.get("status"),
                                                "confirmed": True}),
            "advise": ("record_advice", {"proposal_id": proposal["id"], "advice_text": args.get("text")}),
            "position": ("record_consent_position", {"proposal_id": proposal["id"],
                                                     "position": args.get("position"), "reason": args.get("reason")}),
            "ceremony": ("update_agreement_status", {"agreement_id": "AGR-GARDEN", "new_status": args.get("status"),
                                                     "evidence": args.get("evidence")}),
        }[action]
        async with self.env.db() as session:
            result = await execute_tool(tool, tool_args, session, ecosystem_ids=[str(ECO)],
                                        caller_user_id=PEOPLE[who].user_id)
            if result.get("success"):
                await session.commit()
        if not result["success"]:
            return ("refused", ": ".join(filter(None, (result.get("code"), result["error"]))))
        return ("ok", result["data"].get("auto_transitions", []))


# (actor, action, arguments, expected outcome, proposal status afterwards); see api/AGENTS.md "ACT parity".
ACT_SCRIPT = [
    ("ben", "move", {"status": "advice"}, ("refused", MANAGE_DENIED), "draft"),
    ("ada", "move", {"status": "advice"}, ("ok", []), "advice"),
    ("ada", "move", {"status": "consent"}, ("refused", GATE_UNMET), "advice"),
    ("ada", "advise", {"text": "I agree with myself"}, ("refused", SELF_ADVICE_DENIED), "advice"),
    ("ben", "advise", {"text": "Add a sign-out sheet"}, ("ok", []), "advice"),  # the proposer closes advice
    ("ben", "move", {"status": "consent"}, ("refused", MANAGE_DENIED), "advice"),
    # No advice deadline: a steward never closes someone else's advice (owner decision 2026-11-01).
    ("mo", "move", {"status": "consent"}, ("refused", f"{ADVICE_CLOSE_PROPOSER_ONLY}: {PROPOSER_CLOSES_ADVICE}"), "advice"),
    ("ada", "move", {"status": "consent"}, ("ok", []), "consent"),
    ("mo", "position", {"position": "objection", "reason": "Too noisy at night"}, ("ok", []), "consent"),
    ("sol", "position", {"position": "consent"}, ("ok", []), "consent"),  # the open objection blocks
    ("ben", "move", {"status": "withdrawn"}, ("refused", MANAGE_DENIED), "consent"),
    ("mo", "move", {"status": "withdrawn"}, ("ok", []), "withdrawn"),
]
AGREEMENT_SCRIPT = [
    ("ben", "ceremony", {"status": "advice", "evidence": "Opening the advice round"}, ("refused", CEREMONY_DENIED), "draft"),
    ("ari", "ceremony", {"status": "advice", "evidence": "Open"}, ("refused", "Documented evidence is required"), "draft"),
    ("ari", "ceremony", {"status": "advice", "evidence": "Opening the advice round"}, ("ok", []), "advice"),
    ("ari", "ceremony", {"status": "consent", "evidence": "Closing advice early"}, ("refused", GATE_UNMET), "advice"),
    ("ari", "ceremony", {"status": "active", "evidence": "Adopting it straight away"}, ("refused", "Invalid transition"), "advice"),
]
SEEDED_AGREEMENT_VERSION = "1.0"  # a ceremony never bumps it: member consent is bound to the version
_TODAY = aoe_today()  # due dates pass on the server's Anywhere-on-Earth day, not the UTC calendar day
TOMORROW, YESTERDAY = _TODAY + dt.timedelta(days=1), _TODAY - dt.timedelta(days=1)
# Mo (a steward who did not write it) closes Ada's advice: (advice deadline, expected outcome, status afterwards).
ADVICE_DEADLINE_SCRIPT = [
    (TOMORROW, ("refused", f"{ADVICE_CLOSE_PROPOSER_ONLY}: {PROPOSER_CLOSES_ADVICE} You can close it after the "
                           f"advice deadline ({TOMORROW.isoformat()})"), "advice"),
    (YESTERDAY, ("ok", []), "consent"),  # the proposer did not close it by the deadline
]


def _matches(observed: tuple, expected: tuple) -> bool:
    """Same outcome kind; a refusal names the expected rule (surfaces may append gates or context)."""
    if observed[0] != expected[0]:
        return False
    return expected[1] in observed[1] if expected[0] == "refused" else observed[1] == expected[1]


@pytest.mark.parametrize("surface", ["rest", "mcp", "chat"])
async def test_every_surface_applies_the_same_act_rules(env, monkeypatch, surface):
    surfaces = Surfaces(env, monkeypatch)
    run = getattr(surfaces, surface)
    proposal = await _create_proposal(env.app)

    for actor, action, args, expected, status_after in ACT_SCRIPT + AGREEMENT_SCRIPT:
        observed = await run(actor, action, proposal, **args)
        assert _matches(observed, expected), (surface, actor, action, observed)
        async with env.db() as session:
            if action == "ceremony":
                current = (await session.get(Agreement, GARDEN_AGREEMENT)).status
            else:
                current = (await session.scalar(select(Proposal).where(Proposal.id == proposal["id"]))).status
        assert current == status_after, (surface, actor, action, current)

    async with env.db() as session:
        assert (await session.get(Agreement, GARDEN_AGREEMENT)).version == SEEDED_AGREEMENT_VERSION, surface


@pytest.mark.parametrize("surface", ["rest", "mcp", "chat"])
async def test_every_surface_lets_a_steward_close_advice_only_after_its_deadline(env, monkeypatch, surface):
    run = getattr(Surfaces(env, monkeypatch), surface)
    for deadline, expected, status_after in ADVICE_DEADLINE_SCRIPT:
        proposal = await _create_proposal(env.app, advice_deadline=deadline.isoformat())
        await _open_for_advice(env.app, proposal["id"])
        advice = await _call(env.app, "post", "ben", f"/api/v1/proposals/{proposal['id']}/advice", json={"content": "Add a rota"})
        assert advice.status == 201, advice.text

        observed = await run("mo", "move", proposal, status="consent")
        assert _matches(observed, expected), (surface, deadline, observed)
        async with env.db() as session:
            current = (await session.scalar(select(Proposal).where(Proposal.id == proposal["id"]))).status
        assert current == status_after, (surface, deadline, current)
