"""G-Exchange parity (review-exchange.md C9): one script of exchange moves on REST, the chat assistant and MCP.

Each surface must allow and refuse the same moves with the same codes and leave the same state. The chat tools
and MCP call the same services/exchange.py functions as REST; confirmations are given up front here (the chat
two-phase contract itself is covered in tests/test_g_agent_assistant.py and agent/AGENTS.md).
"""

from __future__ import annotations

import re
import uuid

import pytest
import pytest_asyncio

from neos_agent import mcp_server
from neos_agent.agent.governance_tools import execute_tool
from neos_agent.db.models import Collaboration, SharesNeeds, User

from tests.test_exchange_support import (
    COLLABS, DOCK, KITCHEN, OASIS, PEOPLE, POSTS, build_world, call, member_id,
)

# (actor, move, args, expected outcome): "ok" or the refusal code every surface must give.
SCRIPT = (
    ("ana", "publish", {"title": "Ladder"}, "ok"),
    ("ana", "publish", {"title": "ladder"}, "DUPLICATE_POST"),
    ("pip", "respond", {"message": "Me!"}, "CONSENT_PENDING"),
    ("ana", "respond", {"message": "Bump"}, "OWN_POST"),
    ("olu", "respond", {"message": "I have one"}, "ok"),
    ("sam", "status", {"status": "fulfilled"}, "AUTHOR_ONLY"),
    ("fay", "status", {"status": "hidden", "reason": "Founder elsewhere"}, "MODERATOR_ONLY"),  # D1
    ("rex", "status", {"status": "hidden", "reason": "Other ecosystem"}, "MODERATOR_ONLY"),
    ("sam", "status", {"status": "hidden"}, "REASON_REQUIRED"),
    ("sam", "status", {"status": "hidden", "reason": "Checking a report"}, "ok"),
    ("sam", "status", {"status": "restored"}, "ok"),
    ("ana", "status", {"status": "fulfilled", "fulfilled_by": "Olu"}, "ok"),
    ("ana", "status", {"status": "withdrawn"}, "MOVE_NOT_ALLOWED"),
    ("mel", "respond", {"message": "Too late?"}, "POST_CLOSED"),
    ("mel", "approve", {}, "APPROVE_DENIED"),
    ("sam", "approve", {}, "ok"),
    ("tia", "approve", {}, "ALREADY_APPROVED"),
    ("rex", "approve", {}, "ok"),
    ("olu", "review", {"note": "Looks fine"}, "REVIEW_DENIED"),  # FX-Exchange F3
    ("rex", "review", {"note": "Crews came every week"}, "ok"),
    ("olu", "end", {"outcome": "completed", "reason": "Not mine"}, "END_DENIED"),
    ("rex", "end", {"outcome": "completed", "reason": "Season over"}, "ok"),
    ("sam", "review", {"note": "Too late"}, "NOT_ACTIVE"),
)
TOOLS = {"publish": "publish_share_need", "respond": "respond_to_share_need", "status": "update_share_need_status",
         "approve": "approve_collaboration", "end": "end_collaboration", "review": "review_collaboration"}


@pytest_asyncio.fixture
async def env():
    engine, world = await build_world()
    yield world
    await engine.dispose()


class Surfaces:
    """Run one move as `who` on a surface; return "ok" or the refusal code."""

    def __init__(self, env, monkeypatch):
        self.env, self.acting, self.post_id, self.collab_id = env, {}, None, None

        async def fake_caller(ctx):
            p = PEOPLE[self.acting["who"]]
            return mcp_server.Caller(user=User(id=p.user_id, display_name=p.name), token=None)

        monkeypatch.setattr(mcp_server, "_caller", fake_caller)
        monkeypatch.setattr(mcp_server, "_db", lambda: env.db)

    def _args(self, move: str, args: dict) -> dict:
        if move == "publish":
            return {"domain": str(KITCHEN), "type": "need", **args}
        if move in ("approve", "end", "review"):
            return {"collaboration": self.collab_id, **args}
        return {"post": self.post_id, **args}

    async def rest(self, who, move, args):
        if move == "publish":
            resp = await call(self.env, "post", who, POSTS, json={
                "ecosystem_id": str(OASIS), "domain_id": str(KITCHEN), "type": "need", **args})
        elif move == "respond":
            resp = await call(self.env, "post", who, f"{POSTS}/{self.post_id}/respond", json=args)
        elif move == "status" and args["status"] in ("hidden", "restored"):
            action = "hide" if args["status"] == "hidden" else "restore"
            resp = await call(self.env, "post", who, f"{POSTS}/{self.post_id}/{action}", json={"reason": args.get("reason")})
        elif move == "status":
            body = {"status": args["status"]}
            if args.get("fulfilled_by"):
                body["fulfilled_by_member_id"] = str(member_id(args["fulfilled_by"].lower()))
            resp = await call(self.env, "post", who, f"{POSTS}/{self.post_id}/status", json=body)
        else:
            resp = await call(self.env, "post", who, f"{COLLABS}/{self.collab_id}/{move}", json=args)
        if resp.status < 300 and move == "publish":
            self.post_id = resp.json["id"]
        return "ok" if resp.status < 300 else resp.json.get("code", resp.status)

    async def chat(self, who, move, args):
        p = PEOPLE[who]
        async with self.env.db() as session:
            result = await execute_tool(TOOLS[move], {**self._args(move, args), "confirmed": True}, session,
                                        ecosystem_ids=[str(row.ecosystem) for row in p.rows if row.status == "active"],
                                        caller_user_id=p.user_id, confirmed_keys=None)
            if result.get("success"):
                await session.commit()
        if result.get("success") and move == "publish":
            self.post_id = result["data"]["id"]
        return "ok" if result.get("success") else result.get("code", result.get("error"))

    async def mcp(self, who, move, args):
        self.acting["who"] = who
        call_args = self._args(move, args)
        tool = {"publish": mcp_server.post_share_need, "respond": mcp_server.respond_to_share_need,
                "status": mcp_server.update_share_need_status, "approve": mcp_server.approve_collaboration,
                "end": mcp_server.end_collaboration, "review": mcp_server.review_collaboration}[move]
        if move in ("respond", "status", "end"):
            call_args["confirm"] = True
        try:
            result = await tool(ctx=None, **call_args)
        except ValueError as refusal:
            text = str(refusal)
            return text.split(":", 1)[0] if ":" in text and text.split(":", 1)[0].isupper() else text
        if move == "publish":
            self.post_id = result["data"]["id"]
        return "ok"


@pytest.mark.parametrize("surface", ["rest", "chat", "mcp"])
async def test_every_surface_applies_the_same_exchange_rules(env, monkeypatch, surface):
    surfaces = Surfaces(env, monkeypatch)
    collab = (await call(env, "post", "mel", COLLABS, expect=201, json={
        "source_domain_id": str(KITCHEN), "target_domain_id": str(DOCK), "title": "Ladders to the dock"})).json
    surfaces.collab_id = collab["id"]
    run = getattr(surfaces, surface)
    outcomes = [await run(who, move, dict(args)) for who, move, args, _ in SCRIPT]
    assert outcomes == [expected for *_, expected in SCRIPT]
    async with env.db() as session:
        post = await session.get(SharesNeeds, uuid.UUID(surfaces.post_id))
        collaboration = await session.get(Collaboration, uuid.UUID(collab["id"]))
    assert (post.status, post.fulfilled_by_member_id, post.hidden_at, post.hidden_reason) == (
        "fulfilled", member_id("olu"), None, "Checking a report")
    assert (collaboration.status, collaboration.end_reason) == ("completed", "Season over")
    assert (collaboration.review_note, collaboration.reviewed_by_member_id) == ("Crews came every week", member_id("rex"))


def test_every_assistant_tool_has_a_plain_label_and_the_page_hints_name_real_tools():
    """The chat UI shows a label, never a raw tool name; the page hints name the wave-C tools and only real ones."""
    from neos_agent.agent.governance_tools import get_tool_definitions
    from neos_agent.agent.system_prompt import _PAGE_CONTEXT_HINTS
    from neos_agent.api.chat import _TOOL_DISPLAY_NAMES

    tools = {definition["name"] for definition in get_tool_definitions()}
    assert tools - set(_TOOL_DISPLAY_NAMES) == set()
    named = {word for hint in _PAGE_CONTEXT_HINTS.values() for word in re.findall(r"\b[a-z]+(?:_[a-z]+)+\b", hint)}
    assert named - tools == set()
    assert {"join_ecosystem", "attest_agreement_consent", "move_member", "get_governance_health", "find_shares_needs",
            "respond_to_share_need", "review_collaboration", "end_collaboration"} <= named
