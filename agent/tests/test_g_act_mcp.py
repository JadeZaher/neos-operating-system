"""G-ACT: the MCP agent tools write ACT records exactly as REST does (agreement consent ledger, one position).

Separate module so an environment without the `mcp` package skips only this file.
Rules: src/neos_agent/api/AGENTS.md "ACT integrity (G-ACT)".
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp.server.fastmcp")

from sqlalchemy import func, select  # noqa: E402

from neos_agent import mcp_server  # noqa: E402
from neos_agent.db.models import Agreement, ConsentParticipant, Member, MemberAlignmentEvent, User  # noqa: E402

from .test_uxqa_p1_governance import GARDEN_AGREEMENT, PEOPLE, _call, _create_proposal, env  # noqa: E402,F401


@pytest.fixture
def acting(env, monkeypatch):
    who: dict = {}

    async def fake_caller(ctx):
        p = who["person"]
        return mcp_server.Caller(user=User(id=p.user_id, display_name=p.name), token=None)

    monkeypatch.setattr(mcp_server, "_caller", fake_caller)
    monkeypatch.setattr(mcp_server, "_db", lambda: env.db)
    return who


async def test_mcp_agreement_consent_writes_the_alignment_ledger_like_rest(env, acting):
    async with env.db() as session:
        garden = await session.get(Agreement, GARDEN_AGREEMENT)
        garden.alignment_points = 5
        await session.commit()

    acting["person"] = PEOPLE["ben"]
    with pytest.raises(ValueError, match="consent ceremony"):  # the draft is not open for consent
        await mcp_server.attest_agreement_consent(str(GARDEN_AGREEMENT), "I agree to the garden hours.", ctx=None)

    async with env.db() as session:
        (await session.get(Agreement, GARDEN_AGREEMENT)).status = "consent"
        await session.commit()
    await mcp_server.attest_agreement_consent(str(GARDEN_AGREEMENT), "I agree to the garden hours.", ctx=None)
    # Attesting again never credits twice.
    await mcp_server.attest_agreement_consent(str(GARDEN_AGREEMENT), "Still agree to the garden hours.", ctx=None)

    async with env.db() as session:
        ledger = (await session.execute(
            select(MemberAlignmentEvent.member_id, MemberAlignmentEvent.delta)
        )).all()
        ben = await session.get(Member, PEOPLE["ben"].member_id)
    assert [tuple(row) for row in ledger] == [(PEOPLE["ben"].member_id, 5)]
    assert ben.agreement_alignment_score == 5


async def test_mcp_consent_keeps_one_position_per_member(env, acting):
    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    await _call(env.app, "post", "ada", f"{url}/status", json={"status": "advice"})
    await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})
    await _call(env.app, "post", "ada", f"{url}/status", json={"status": "consent"})

    acting["person"] = PEOPLE["ben"]
    objected = await mcp_server.submit_proposal_consent(proposal["id"], "objection", ctx=None, objection_text="Noise")
    assert objected["auto_transitions"] == []
    consented = await mcp_server.submit_proposal_consent(proposal["id"], "consent", ctx=None)
    assert consented["auto_transitions"] == ["consent->test"]
    async with env.db() as session:
        rows = int(await session.scalar(select(func.count(ConsentParticipant.id))) or 0)
    assert rows == 1
