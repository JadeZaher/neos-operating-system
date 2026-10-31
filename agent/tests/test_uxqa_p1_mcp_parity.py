"""UX-QA pass 01: the MCP agent tools apply the same authorship rules as REST.

Separate from test_uxqa_p1_governance.py so an environment without the `mcp`
package (or with an incompatible 2.x) skips only this module instead of
failing collection for the whole run. `mcp>=1,<2` is a declared dependency.
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp.server.fastmcp")

from sqlalchemy import select  # noqa: E402

from neos_agent import mcp_server  # noqa: E402
from neos_agent.api.proposals import MANAGE_DENIED, SELF_ADVICE_DENIED  # noqa: E402
from neos_agent.db.models import Proposal, User  # noqa: E402

from .test_uxqa_p1_governance import ECO, PEOPLE, Person, env  # noqa: E402,F401 — env is the shared fixture


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
    assert advised["auto_transitions"] == ["advice->consent"]
    with pytest.raises(ValueError, match=MANAGE_DENIED):
        await mcp_server.transition_proposal(created["id"], "withdrawn", ctx=None)

    acting["who"] = PEOPLE["mo"]
    assert (await mcp_server.transition_proposal(created["id"], "withdrawn", ctx=None))["status"] == "withdrawn"
