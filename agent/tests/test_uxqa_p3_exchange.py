"""UX-QA pass 03 (cross-ecosystem exchange), lane A: acts someone waits on rank high; archived domains take nothing new.

Drives the real discover, messaging and next-steps blueprints over the shared G-Exchange world
(`tests/test_exchange_support.py`). Rules: services/AGENTS.md "Next steps" > "Rules of the queue" (FIRST_TIER)
and "Exchange (G-Exchange)" > "Archived domains"; api/AGENTS.md "Exchange (G-Exchange)" (DOMAIN_NOT_ACTIVE).
"""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import func, select, update

from neos_agent.db.models import AdviceLog, Collaboration, Domain, GovernanceHealthAudit, Proposal, SharesNeeds
from neos_agent.services import dates

from tests.test_exchange_support import COLLABS, DOCK, GARDEN, KITCHEN, OASIS, POSTS, build_world, call, member_id, post_as


@pytest_asyncio.fixture
async def exchange():
    engine, world = await build_world()
    yield world
    await engine.dispose()


# ---------------------------------------------------------------------------
# p3-needs-across-ecosystems-1: an answer, an approval or an audit response ranks right after overdue items
# ---------------------------------------------------------------------------


async def _advice_proposal(env, title: str, deadline: dt.date) -> str:
    """An Oasis proposal by Ana in its advice stage: every other active member there is asked for advice (dated)."""
    proposal_id = uuid.uuid4()
    async with env.db() as session:
        session.add(Proposal(id=proposal_id, ecosystem_id=OASIS, proposal_id=f"PROP-{proposal_id.hex[:6]}", type="policy",
                             title=title, status="advice", proposer="Ana", proposer_member_id=member_id("ana"),
                             proposed_change="Change how we share.", advice_deadline=deadline))
        await session.flush()
        session.add(AdviceLog(id=uuid.uuid4(), proposal_id=proposal_id))
        await session.commit()
    return str(proposal_id)


async def _someone_answered_sams_post(env) -> None:
    post = await post_as(env, "sam", title="Ladders for the barn", domain=GARDEN)
    await call(env, "post", "olu", f"{POSTS}/{post['id']}/respond", expect=201, json={"message": "I have two."})


async def _a_collaboration_waits_for_oasis(env) -> None:
    await call(env, "post", "mel", COLLABS, expect=201, json={
        "source_domain_id": str(GARDEN), "target_domain_id": str(DOCK), "title": "Garden crews the dock"})


async def _an_audit_rated_something_critical(env) -> None:
    today = dates.utc_today()
    async with env.db() as session:
        session.add(GovernanceHealthAudit(
            id=uuid.uuid4(), ecosystem_id=OASIS, audit_id="AUDIT-P3", audit_date=today, auditor="Mel",
            status="completed", overall_health_score=0, next_audit_due=today + dt.timedelta(days=90),
            indicator_scores=[{"indicator_id": "GHI-01", "indicator_name": "Proposal authorship diversity",
                               "status": "critical"}]))
        await session.commit()


WAITED_ON = {  # action -> how a real flow puts it in Sam's (an Oasis steward's) queue
    "read_response": _someone_answered_sams_post,
    "approve_collaboration": _a_collaboration_waits_for_oasis,
    "respond_to_audit": _an_audit_rated_something_critical,
}


@pytest.mark.parametrize("action", list(WAITED_ON))
async def test_an_act_someone_waits_on_comes_right_after_overdue_items(exchange, action):
    overdue = await _advice_proposal(exchange, "Tool library", dates.aoe_today() - dt.timedelta(days=2))
    dated = await _advice_proposal(exchange, "Garden rota", dates.aoe_today() + dt.timedelta(days=5))
    await WAITED_ON[action](exchange)

    items = (await call(exchange, "get", "sam", "/api/v1/me/next-steps", expect=200)).json["items"]
    order = [(item["action"], item["id"]) for item in items if item["action"] in ("give_advice", action)]
    # Before: undated, it sank under every dated advice item (pass 03: an answer was item 25 of 26 in the bell).
    assert [name for name, _ in order] == ["give_advice", action, "give_advice"]
    assert (order[0][1], order[2][1]) == (overdue, dated)


# ---------------------------------------------------------------------------
# p3-collaboration-and-moderation-2: an archived domain takes no new post, reopen or collaboration
# ---------------------------------------------------------------------------


async def test_an_archived_domain_takes_nothing_new_and_its_open_posts_stay_editable(exchange):
    kept = await post_as(exchange, "ana", title="Bread oven")
    closed = await post_as(exchange, "ana", title="Old oven")
    await call(exchange, "post", "ana", f"{POSTS}/{closed['id']}/status", expect=200, json={"status": "withdrawn"})
    async with exchange.db() as session:
        await session.execute(update(Domain).where(Domain.id == KITCHEN).values(status="archived"))
        await session.commit()

    refused = [
        await call(exchange, "post", "ana", POSTS, expect=409, json={
            "ecosystem_id": str(OASIS), "domain_id": str(KITCHEN), "type": "share", "title": "Spare flour"}),
        await call(exchange, "post", "ana", f"{POSTS}/{closed['id']}/status", expect=409, json={"status": "active"}),
        await call(exchange, "post", "mel", COLLABS, expect=409, json={
            "source_domain_id": str(KITCHEN), "target_domain_id": str(DOCK), "title": "Kitchen crews"}),
        await call(exchange, "post", "olu", COLLABS, expect=409, json={
            "source_domain_id": str(DOCK), "target_domain_id": str(KITCHEN), "title": "Dock feeds"}),
    ]
    assert [(r.json["code"], r.json["field"]) for r in refused] == [
        ("DOMAIN_NOT_ACTIVE", "domain_id"), ("DOMAIN_NOT_ACTIVE", "domain_id"),
        ("DOMAIN_NOT_ACTIVE", "source_domain_id"), ("DOMAIN_NOT_ACTIVE", "target_domain_id")]
    assert all(r.json["error"].startswith("Community Kitchen is archived") for r in refused)
    async with exchange.db() as session:
        assert await session.scalar(select(func.count(SharesNeeds.id))) == 2
        assert await session.scalar(select(func.count(Collaboration.id))) == 0
        assert (await session.get(SharesNeeds, uuid.UUID(closed["id"]))).status == "withdrawn"

    # A post already there can still be corrected (and withdrawn or fulfilled): only new publishing is refused.
    edited = await call(exchange, "put", "ana", f"{POSTS}/{kept['id']}", expect=200, json={"title": "Bread oven (fixed)"})
    assert edited.json["title"] == "Bread oven (fixed)"
