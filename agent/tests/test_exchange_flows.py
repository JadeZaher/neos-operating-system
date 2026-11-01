"""G-Exchange flows through the real blueprints (uxqa/governance/review-exchange.md §5 C2-C8).

A post is found across ecosystems, answered, the poster sees an unread conversation and a queue item, marks it
fulfilled naming the responder, and further answers are refused; a collaboration is proposed from a post, approved
by a steward of each side, gets its review date, shows up for review and ends with a reason; a post still open after
90 days asks its author; an exited author's open posts are withdrawn. The concurrency rows run on a disposable
PostgreSQL schema when NEOS_TEST_POSTGRES_URL is set (alembic/AGENTS.md "Data revisions").
"""

from __future__ import annotations

import asyncio
import datetime as dt
import os
import uuid

import pytest
import pytest_asyncio
import sqlalchemy as sa
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine

from neos_agent.db.models import Collaboration, CollaborationApproval, SharesNeeds
from neos_agent.services import dates
from neos_agent.services.next_steps import waiting_for

from tests.test_exchange_support import (
    COLLABS, DOCK, GARDEN, KITCHEN, OASIS, PEOPLE, POSTS, RIVER, build_world, call, member_id, post_as,
)

CONVERSATIONS = "/api/v1/messaging/conversations"


@pytest_asyncio.fixture
async def env():
    engine, world = await build_world()
    yield world
    await engine.dispose()


async def _queue(env, who: str, kind: str | None = None) -> list[dict]:
    items = (await call(env, "get", who, "/api/v1/me/next-steps", expect=200)).json["items"]
    return [item for item in items if kind is None or item["kind"] == kind]


async def test_post_found_across_ecosystems_answered_unread_then_fulfilled(env):
    post = await post_as(env, "ana", title="Soup pots for Saturday")
    # An Oasis need is found by a River House member, with who, where and how old.
    found = {i["id"]: i for i in (await call(env, "get", "olu", POSTS, expect=200)).json["items"]}[post["id"]]
    assert (found["author_name"], found["domain_name"], found["ecosystem_name"], found["age_days"]) == (
        "Ana", "Community Kitchen", "Oasis", 0)
    assert found["caller_can_respond"] is True and found["respond_blocked"] is None

    first = (await call(env, "post", "olu", f"{POSTS}/{post['id']}/respond", expect=201,
                        json={"message": "I have four big pots."})).json
    assert first["created"] is True and first["post"]["caller_has_responded"] is True
    # The poster has an unread conversation with the responder, tagged to the post, and a queue item.
    conversations = (await call(env, "get", "ana", "/api/v1/messaging/conversations", expect=200)).json["conversations"]
    assert [(c["id"], c["unread_count"], sorted(p["display_name"] for p in c["participants"]))
            for c in conversations] == [(first["conversation_id"], 1, ["Ana", "Olu"])]
    [item] = await _queue(env, "ana", "share_need")
    assert (item["action"], item["link"]) == ("read_response", f"/messaging?conversation={first['conversation_id']}")
    assert item["what"].startswith("Olu answered your need")
    # Answering again reuses the conversation.
    again = (await call(env, "post", "olu", f"{POSTS}/{post['id']}/respond", expect=200,
                        json={"message": "And a ladle."})).json
    assert (again["created"], again["conversation_id"]) == (False, first["conversation_id"])
    # Reading it clears the queue item.
    await call(env, "get", "ana", f"/api/v1/messaging/conversations/{first['conversation_id']}", expect=200)
    assert await _queue(env, "ana", "share_need") == []

    mine = (await call(env, "get", "ana", f"{POSTS}/{post['id']}", expect=200)).json
    assert mine["responders"] == [{"member_id": str(member_id("olu")), "name": "Olu"}]
    assert {m["label"] for m in mine["allowed_next"]} == {"Mark fulfilled", "Withdraw", "Keep it open"}
    await call(env, "post", "ana", f"{POSTS}/{post['id']}/status", expect=400,
               json={"status": "fulfilled", "fulfilled_by_member_id": str(member_id("mel"))})  # not a responder
    done = (await call(env, "post", "ana", f"{POSTS}/{post['id']}/status", expect=200, json={
        "status": "fulfilled", "fulfilled_by_member_id": str(member_id("olu")), "note": "Olu lent the pots"})).json
    assert (done["status"], done["fulfilled_by_name"], done["status_reason"]) == ("fulfilled", "Olu", "Olu lent the pots")
    assert [m["status"] for m in done["allowed_next"]] == ["active"]  # reopen only

    refused = await call(env, "post", "mel", f"{POSTS}/{post['id']}/respond", expect=409, json={"message": "Me too"})
    assert (refused.json["code"], refused.json["status"]) == ("POST_CLOSED", "fulfilled")
    assert post["id"] not in {i["id"] for i in (await call(env, "get", "olu", POSTS, expect=200)).json["items"]}
    assert post["id"] in {i["id"] for i in (await call(env, "get", "olu", f"{POSTS}?status=all", expect=200)).json["items"]}
    resp = await call(env, "post", "ana", f"{POSTS}/{post['id']}/status", expect=409, json={"status": "withdrawn"})
    assert (resp.json["code"], resp.json["allowed"]) == ("MOVE_NOT_ALLOWED", ["active"])

    # The author's own profile lists it in every state; the public profile only open, public, visible posts.
    me = (await call(env, "get", "ana", "/api/v1/profiles/me", expect=200)).json
    assert [(p["id"], p["status"]) for p in me["own_publications"]] == [(post["id"], "fulfilled")]
    assert me["publications"] == []
    reopened = (await call(env, "post", "ana", f"{POSTS}/{post['id']}/status", expect=200, json={"status": "active"})).json
    assert (reopened["status"], reopened["fulfilled_by_name"]) == ("active", None)


async def test_collaboration_from_a_post_approved_by_both_sides_reviewed_and_ended(env):
    need = await post_as(env, "olu", title="Boat crew", domain=DOCK, ecosystem=RIVER)
    collab = (await call(env, "post", "mel", COLLABS, expect=201, json={
        "source_domain_id": str(KITCHEN), "target_domain_id": str(DOCK), "title": "Kitchen crews the boats",
        "linked_share_need_id": need["id"]})).json
    assert collab["proposed_by_name"] == "Mel" and collab["approvals"] == []
    assert [a["ecosystem_name"] for a in collab["awaiting"]] == ["Oasis", "River House"]
    assert collab["linked_publications"] == [{"id": need["id"], "title": "Boat crew", "type": "need", "status": "active"}]
    # Each side's stewards are asked; a plain member is not.
    assert [i["action"] for i in await _queue(env, "sam", "collaboration")] == ["approve_collaboration"]
    assert await _queue(env, "mel", "collaboration") == []
    sam_view = (await call(env, "get", "sam", f"{COLLABS}/{collab['id']}", expect=200)).json
    assert [s["ecosystem_name"] for s in sam_view["caller_can_approve_for"]] == ["Oasis"]

    half = (await call(env, "post", "sam", f"{COLLABS}/{collab['id']}/approve", expect=200, json={})).json
    assert (half["status"], [a["approved_by"] for a in half["approvals"]]) == ("proposed", ["Sam"])
    assert [a["ecosystem_name"] for a in half["awaiting"]] == ["River House"]
    assert await _queue(env, "sam", "collaboration") == [] and await _queue(env, "tia", "collaboration") == []
    assert [i["action"] for i in await _queue(env, "rex", "collaboration")] == ["approve_collaboration"]
    resp = await call(env, "post", "tia", f"{COLLABS}/{collab['id']}/approve", expect=409, json={})  # double approval
    assert resp.json["code"] == "ALREADY_APPROVED"

    active = (await call(env, "post", "rex", f"{COLLABS}/{collab['id']}/approve", expect=200, json={})).json
    today = dates.utc_today()  # started_date is a creation stamp (F9: services/dates, not the server's local day)
    assert (active["status"], active["started_date"], active["review_date"]) == (
        "active", today.isoformat(), (today + dt.timedelta(days=365)).isoformat())
    assert collab["id"] in {i["id"] for i in (await call(env, "get", "pip", COLLABS, expect=200)).json["items"]}
    async with env.db() as session:
        assert await session.scalar(sa.select(sa.func.count(CollaborationApproval.id))) == 2
        # The review date passes: stewards of both sides are asked to review it (one item each).
        later = dt.datetime.now(dt.UTC).replace(tzinfo=None) + dt.timedelta(days=367)
        for who in ("sam", "rex", "mel"):
            items = [i for i in await waiting_for(session, PEOPLE[who].user_id, now=later) if i["kind"] == "collaboration"]
            assert [i["action"] for i in items] == ([] if who == "mel" else ["review_collaboration"]), who

    ended = (await call(env, "post", "rex", f"{COLLABS}/{collab['id']}/end", expect=200,
                        json={"outcome": "completed", "reason": "The season is over"})).json
    assert (ended["status"], ended["ended_by_name"], ended["end_reason"]) == ("completed", "Rex", "The season is over")
    assert ended["caller_can_end"] is False
    await call(env, "post", "sam", f"{COLLABS}/{collab['id']}/end", expect=409,
               json={"outcome": "dissolved", "reason": "Again"})


async def test_proposing_from_a_closed_or_invisible_post_is_refused(env):
    hidden_from_river = await post_as(env, "ana", title="Members only", visibility="ecosystem")
    await call(env, "post", "olu", COLLABS, expect=404, json={
        "source_domain_id": str(DOCK), "target_domain_id": str(KITCHEN), "title": "x",
        "linked_share_need_id": hidden_from_river["id"]})
    withdrawn = await post_as(env, "ana", title="Gone")
    await call(env, "post", "ana", f"{POSTS}/{withdrawn['id']}/status", expect=200, json={"status": "withdrawn"})
    resp = await call(env, "post", "olu", COLLABS, expect=409, json={
        "source_domain_id": str(DOCK), "target_domain_id": str(KITCHEN), "title": "x",
        "linked_share_need_id": withdrawn["id"]})
    assert resp.json["code"] == "POST_CLOSED"
    resp = await call(env, "post", "mel", COLLABS, expect=400, json={
        "source_domain_id": str(KITCHEN), "target_domain_id": str(KITCHEN), "title": "Self"})
    assert resp.json["code"] == "SAME_DOMAIN"


async def test_a_post_still_open_after_90_days_asks_its_author(env):
    post = await post_as(env, "ana", title="Long open")
    now = dt.datetime.now(dt.UTC).replace(tzinfo=None)

    async def still_open(age_days: int) -> list[dict]:
        async with env.db() as session:
            await session.execute(update(SharesNeeds).where(SharesNeeds.id == uuid.UUID(post["id"])).values(
                created_at=now - dt.timedelta(days=age_days)))
            await session.commit()
            return [i for i in await waiting_for(session, PEOPLE["ana"].user_id, now=now) if i["action"] == "still_open"]

    assert await still_open(89) == []
    [item] = await still_open(91)
    assert (item["what"], item["link"], item["overdue"]) == (
        "Still open? Long open", f"/discover?tab=shares-needs&post={post['id']}", False)
    assert (await call(env, "get", "ana", f"{POSTS}/{post['id']}", expect=200)).json["age_days"] == 91
    # "Keep it open" restarts the count (the move active -> active is the check-in).
    kept = (await call(env, "post", "ana", f"{POSTS}/{post['id']}/status", expect=200, json={"status": "active"})).json
    assert kept["age_days"] == 0
    async with env.db() as session:
        assert [i for i in await waiting_for(session, PEOPLE["ana"].user_id, now=now) if i["action"] == "still_open"] == []


async def test_an_exited_authors_open_posts_are_withdrawn(env):
    open_post = await post_as(env, "mel", title="Mel's tools", domain=GARDEN)
    closed = await post_as(env, "mel", title="Mel's chairs", domain=GARDEN)
    await call(env, "post", "mel", f"{POSTS}/{closed['id']}/status", expect=200, json={"status": "fulfilled"})
    exit_record = (await call(env, "post", "mel", "/api/v1/exit", expect=201, json={"ecosystem_id": str(OASIS)})).json
    await call(env, "post", "sam", f"/api/v1/exit/{exit_record['id']}/status", expect=200, json={"new_status": "completed"})
    async with env.db() as session:
        rows = {str(r.id): (r.status, r.status_reason) for r in (await session.execute(select(SharesNeeds))).scalars()}
    assert rows == {open_post["id"]: ("withdrawn", "author left"), closed["id"]: ("fulfilled", None)}
    blocked = (await call(env, "get", "olu", f"{POSTS}/{open_post['id']}", expect=200)).json
    assert blocked["respond_blocked"] == "POST_CLOSED"


@pytest.mark.parametrize("body, field", [
    ({"title": ""}, "title"),
    ({"title": "x" * 256}, "title"),
    ({"type": "offer"}, "type"),
    ({"category": "skill-share"}, "category"),
    ({"visibility": "friends"}, "visibility"),
    ({"tags": ["ok", ""]}, "tags"),
    ({"description": 5}, "description"),
    ({"domain_id": "not-a-uuid"}, "domain_id"),
    ({"domain_id": str(DOCK)}, "domain_id"),  # a domain of another ecosystem
])
async def test_post_validation_names_the_field(env, body, field):
    base = {"ecosystem_id": str(OASIS), "domain_id": str(GARDEN), "type": "need", "title": "Valid"}
    resp = await call(env, "post", "mel", POSTS, expect=400, json={**base, **body})
    assert resp.json["field"] == field, resp.json


async def test_vocabulary_and_duplicates(env):
    post = await post_as(env, "mel", title="Rakes", domain=GARDEN, category=" Skills ", visibility="private")
    assert (post["category"], post["visibility"]) == ("skills", "domain")  # the retired spelling is "domain"
    resp = await call(env, "post", "mel", POSTS, expect=409, json={
        "ecosystem_id": str(OASIS), "domain_id": str(GARDEN), "type": "need", "title": "rakes"})
    assert (resp.json["code"], resp.json["existing_id"]) == ("DUPLICATE_POST", post["id"])
    await post_as(env, "mel", title="Rakes", domain=GARDEN, type_="share")  # a share of the same name is different


# --- Fix wave (wave-c.md "Fix wave", FX-Exchange) -------------------------------------------------------------------


async def test_a_poster_in_two_ecosystems_reads_an_answer_whatever_the_selection(env):
    """F1: Fay is active in Oasis and Fresh Start with Fresh Start selected; her Oasis need is answered by Olu."""
    post = await post_as(env, "fay", title="Ladders", ecosystem=OASIS)
    answer = (await call(env, "post", "olu", f"{POSTS}/{post['id']}/respond", expect=201,
                         json={"message": "I have a ladder."})).json["conversation_id"]
    # A plain Oasis DM to Fay's Oasis row: the header selection (Fresh Start) still keeps it off her list.
    plain = (await call(env, "post", "mel", CONVERSATIONS, expect=201, json={
        "type": "dm", "participant_ids": [str(member_id("fay", OASIS))]})).json["id"]
    await call(env, "post", "mel", f"{CONVERSATIONS}/{plain}/messages", expect=201, json={"content": "Hi Fay"})

    # The bell, the list (and so the unread badge) and the detail agree on the answer.
    [item] = await _queue(env, "fay", "share_need")
    assert (item["action"], item["link"]) == ("read_response", f"/messaging?conversation={answer}")
    listed = (await call(env, "get", "fay", CONVERSATIONS, expect=200)).json["conversations"]
    assert [(c["id"], c["unread_count"]) for c in listed] == [(answer, 1)]
    # Participants only: someone outside the conversation gets the same 404 as a missing one.
    for outsider in ("dee", "rex"):
        await call(env, "get", outsider, f"{CONVERSATIONS}/{answer}", expect=404)
    opened = (await call(env, "get", "fay", f"{CONVERSATIONS}/{answer}", expect=200)).json
    assert [m["content"] for m in opened["messages"]] == ["I have a ladder."]
    assert await _queue(env, "fay", "share_need") == []  # reading it cleared "Olu answered your need"
    assert [(c["id"], c["unread_count"]) for c in (await call(env, "get", "fay", CONVERSATIONS)).json["conversations"]] == [
        (answer, 0)]
    # She can reply, and the reply reaches the responder.
    await call(env, "post", "fay", f"{CONVERSATIONS}/{answer}/messages", expect=201, json={"content": "Thanks!"})
    olu = {c["id"]: c["unread_count"] for c in (await call(env, "get", "olu", CONVERSATIONS)).json["conversations"]}
    assert olu == {answer: 1}
    # A conversation outside the selection still opens by its link (she takes part through an active row).
    await call(env, "get", "fay", f"{CONVERSATIONS}/{plain}", expect=200)


async def _active_collaboration(env, title: str) -> dict:
    collab = (await call(env, "post", "mel", COLLABS, expect=201, json={
        "source_domain_id": str(KITCHEN), "target_domain_id": str(DOCK), "title": title})).json
    for steward in ("sam", "rex"):
        await call(env, "post", steward, f"{COLLABS}/{collab['id']}/approve", expect=200, json={})
    return collab


async def _set_review_date(env, collab_id: str, review_date: dt.date) -> None:
    async with env.db() as session:
        await session.execute(update(Collaboration).where(Collaboration.id == uuid.UUID(collab_id)).values(
            review_date=review_date))
        await session.commit()


async def test_a_steward_records_a_review_and_the_item_clears_for_both_sides(env):
    """F3: "Review or end" can be answered by a review: who, what it found, the next date; or by ending it."""
    collab = await _active_collaboration(env, "Kitchen crews the boats")
    url = f"{COLLABS}/{collab['id']}"
    overdue = dates.utc_today() - dt.timedelta(days=10)
    await _set_review_date(env, collab["id"], overdue)
    for steward in ("sam", "rex"):
        [item] = await _queue(env, steward, "collaboration")
        assert (item["action"], item["overdue"]) == ("review_collaboration", True)
        assert item["what"] == "Review or end the collaboration “Kitchen crews the boats”"
    seen = (await call(env, "get", "sam", url, expect=200)).json
    assert (seen["review_due"], seen["caller_can_review"], seen["reviewed_by_name"]) == (True, True, None)
    assert (await call(env, "get", "olu", url, expect=200)).json["caller_can_review"] is False

    # Refusals leave the date where it was.
    assert (await call(env, "post", "olu", f"{url}/review", expect=403, json={"note": "Fine"})).json["code"] == "REVIEW_DENIED"
    assert (await call(env, "post", "rex", f"{url}/review", expect=400, json={"note": " "})).json["field"] == "note"
    resp = await call(env, "post", "rex", f"{url}/review", expect=400,
                      json={"note": "Going well", "next_review_date": dates.aoe_today().isoformat()})
    assert resp.json["field"] == "next_review_date"
    assert (await call(env, "get", "sam", url)).json["review_date"] == overdue.isoformat()

    next_date = dates.utc_today() + dt.timedelta(days=180)
    reviewed = (await call(env, "post", "rex", f"{url}/review", expect=200, json={
        "note": "Crews turned up every week", "next_review_date": next_date.isoformat()})).json
    assert (reviewed["review_date"], reviewed["review_due"], reviewed["reviewed_by_name"], reviewed["review_note"]) == (
        next_date.isoformat(), False, "Rex", "Crews turned up every week")
    for steward in ("sam", "rex"):
        assert await _queue(env, steward, "collaboration") == [], steward

    # No date given: a year out. Once it has ended, nothing is reviewed.
    again = (await call(env, "post", "sam", f"{url}/review", expect=200, json={"note": "Still good"})).json
    assert (again["review_date"], again["reviewed_by_name"]) == (
        (dates.utc_today() + dt.timedelta(days=365)).isoformat(), "Sam")
    await call(env, "post", "rex", f"{url}/end", expect=200, json={"outcome": "completed", "reason": "Season over"})
    ended = await call(env, "post", "sam", f"{url}/review", expect=409, json={"note": "Late"})
    assert ended.json["code"] == "NOT_ACTIVE"


@pytest.mark.parametrize("instant, due", [
    (dt.datetime(2026, 6, 2, 11, 59), False),  # 1 June has not ended everywhere on Earth yet
    (dt.datetime(2026, 6, 2, 12, 0), True),  # now it has (UTC-12): the page and the queue both say so
])
async def test_review_due_follows_the_one_date_rule_on_the_page_and_in_the_queue(env, monkeypatch, instant, due):
    """F9: the detail's review_due and the queue item read services/dates, so they turn on at the same instant."""
    collab = await _active_collaboration(env, "Dates agree")
    await _set_review_date(env, collab["id"], dt.date(2026, 6, 1))
    monkeypatch.setattr(dates, "utc_now", lambda: instant)
    assert (await call(env, "get", "sam", f"{COLLABS}/{collab['id']}", expect=200)).json["review_due"] is due
    assert [i["action"] for i in await _queue(env, "sam", "collaboration")] == (["review_collaboration"] if due else [])
    # A proposed review date is "not in the past" by the same rule: 1 June is still today somewhere at 11:59 UTC.
    proposed = await call(env, "post", "mel", COLLABS, json={
        "source_domain_id": str(KITCHEN), "target_domain_id": str(DOCK), "title": f"Later {due}",
        "review_date": "2026-06-01"})
    assert proposed.status == (400 if due else 201), proposed.text


# --- PostgreSQL: the row locks (D15) -------------------------------------------------------------------------------

POSTGRES_URL = os.environ.get("NEOS_TEST_POSTGRES_URL")


@pytest.mark.skipif(not POSTGRES_URL, reason="needs NEOS_TEST_POSTGRES_URL (disposable PG)")
async def test_concurrent_approvals_and_answers_on_postgres():
    schema = f"exch_{uuid.uuid4().hex[:12]}"
    admin = create_async_engine(POSTGRES_URL)
    async with admin.begin() as conn:
        await conn.execute(sa.text(f'CREATE SCHEMA "{schema}"'))
    engine, env = await build_world(POSTGRES_URL, connect_args={"server_settings": {"search_path": schema}})
    try:
        # Two stewards of one side approve at once: exactly one approval, the other is told it is done.
        collab = (await call(env, "post", "mel", COLLABS, expect=201, json={
            "source_domain_id": str(KITCHEN), "target_domain_id": str(DOCK), "title": "Race"})).json
        url = f"{COLLABS}/{collab['id']}/approve"
        results = await asyncio.gather(*(call(env, "post", who, url, json={}) for who in ("sam", "tia")))
        assert sorted(r.status for r in results) == [200, 409]
        # Both sides at once: it ends active (neither sees "one approval, still proposed" and leaves it).
        other = (await call(env, "post", "mel", COLLABS, expect=201, json={
            "source_domain_id": str(KITCHEN), "target_domain_id": str(DOCK), "title": "Race two"})).json
        url = f"{COLLABS}/{other['id']}/approve"
        await asyncio.gather(*(call(env, "post", who, url, expect=200, json={}) for who in ("sam", "rex")))
        assert (await call(env, "get", "sam", f"{COLLABS}/{other['id']}", expect=200)).json["status"] == "active"
        # One responder answering twice at once opens one conversation.
        post = await post_as(env, "ana", title="Race pots")
        answers = await asyncio.gather(*(call(env, "post", "olu", f"{POSTS}/{post['id']}/respond",
                                              json={"message": f"Hi {n}"}) for n in range(2)))
        assert sorted(r.status for r in answers) == [200, 201]
        assert len({r.json["conversation_id"] for r in answers}) == 1
    finally:
        await engine.dispose()
        async with admin.begin() as conn:
            await conn.execute(sa.text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        await admin.dispose()
