"""G-Exchange authority: actor x action tables through the real blueprints (uxqa/governance/review-exchange.md §2).

Actors (test_exchange_support.PEOPLE): anon (signed out), pip (pending newcomer), mel (member of the poster's
ecosystem), ana (the author), dee (domain participant), sam/tia (ecosystem stewards), rex (steward of ANOTHER
ecosystem), olu (member of another ecosystem), fay (founder of a fresh ecosystem: the D1 exploit), xen (exited).
Every refused call is checked to leave the post or collaboration unchanged. Each owner decision of 2026-11-01
(wave-c.md "Exchange governance") has a row here that goes red if the rule is flipped.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from neos_agent.db.models import Collaboration, CollaborationApproval, ConversationLink, Message, SharesNeeds

from tests.test_exchange_support import (
    COLLABS, DOCK, GARDEN, KITCHEN, OASIS, POSTS, RIVER, build_world, call, post_as,
)


@pytest_asyncio.fixture
async def env():
    engine, world = await build_world()
    yield world
    await engine.dispose()


async def _post_row(env, post_id: str) -> dict | None:
    """Every stored column of the post plus its answers: what a refused call must not change."""
    async with env.db() as session:
        record = await session.get(SharesNeeds, uuid.UUID(post_id))
        if record is None:
            return None
        row = {attr.key: getattr(record, attr.key) for attr in SharesNeeds.__mapper__.column_attrs}
        row["links"] = await session.scalar(select(func.count(ConversationLink.id)).where(
            ConversationLink.entity_id == record.id))
        row["messages"] = await session.scalar(select(func.count(Message.id)))
        return row


def _expect(expected) -> tuple[int, str | None]:
    return expected if isinstance(expected, tuple) else (expected, None)


async def _check_table(env, table: dict, method: str, suffix: str, body: dict | None, *, effect=None):
    """One fresh post by Ana per actor; refused calls leave it unchanged, allowed ones show `effect`."""
    for index, (who, expected) in enumerate(table.items()):
        status, code = _expect(expected)
        post = await post_as(env, "ana", title=f"Spare ladders {suffix} {index}")
        before = await _post_row(env, post["id"])
        kwargs = {"json": body} if body is not None else {}
        resp = await call(env, method, who, f"{POSTS}/{post['id']}{suffix}", **kwargs)
        assert resp.status == status, (who, suffix, resp.status, resp.text)
        if code:
            assert resp.json.get("code") == code, (who, suffix, resp.json)
        after = await _post_row(env, post["id"])
        if status >= 400:
            assert after == before, (who, suffix, "a refused call changed the post")
        elif effect is not None:
            effect(who, before, after)


async def test_who_may_post_where():
    engine, env = await build_world()
    try:
        table = {"anon": 401, "pip": (403, "CONSENT_PENDING"), "mel": 201, "ana": 201, "dee": 201, "sam": 201,
                 "olu": (403, "MEMBERSHIP_REQUIRED"), "rex": (403, "MEMBERSHIP_REQUIRED"), "fay": 201,
                 "xen": (403, "MEMBERSHIP_REQUIRED")}
        for who, expected in table.items():
            status, code = _expect(expected)
            resp = await call(env, "post", who, POSTS, json={
                "ecosystem_id": str(OASIS), "domain_id": str(GARDEN), "type": "share", "title": f"Seeds from {who}"})
            assert resp.status == status, (who, resp.text)
            if code:
                assert resp.json["code"] == code
            if status == 201:
                assert resp.json["author_name"] and resp.json["caller_is_author"] is True
        async with env.db() as session:
            authors = (await session.execute(select(SharesNeeds.title))).scalars().all()
        assert sorted(authors) == sorted(f"Seeds from {who}" for who, e in table.items() if _expect(e)[0] == 201)
    finally:
        await engine.dispose()


async def test_one_visibility_rule_for_detail_and_lists(env):
    public = await post_as(env, "ana", title="Public pots")
    members_only = await post_as(env, "ana", title="Members pots", visibility="ecosystem")
    domain_only = await post_as(env, "ana", title="Kitchen pots", visibility="domain")
    hidden = await post_as(env, "ana", title="Hidden pots")
    await call(env, "post", "sam", f"{POSTS}/{hidden['id']}/hide", expect=200, json={"reason": "Duplicate listing"})
    everyone = {"pip": 200, "mel": 200, "ana": 200, "dee": 200, "sam": 200, "tia": 200, "olu": 200, "rex": 200,
                "fay": 200, "xen": 200}
    expected = {
        public["id"]: {"anon": 401, **everyone},
        # ecosystem: active members of Oasis only (pip is pending, xen exited, olu/rex elsewhere)
        members_only["id"]: {"anon": 401, **everyone, "pip": 404, "xen": 404, "olu": 404, "rex": 404},
        # domain: the domain's participants plus Oasis stewards (owner default; "Domain Only" works)
        domain_only["id"]: {"anon": 401, **{k: 404 for k in everyone}, "ana": 200, "dee": 200, "sam": 200, "tia": 200},
        # hidden: the author and Oasis stewards only (moderation is per ecosystem: rex and fay see nothing)
        hidden["id"]: {"anon": 401, **{k: 404 for k in everyone}, "ana": 200, "sam": 200, "tia": 200},
    }
    for post_id, table in expected.items():
        for who, status in table.items():
            await call(env, "get", who, f"{POSTS}/{post_id}", expect=status)
    # Discover lists exactly what the detail opens, minus hidden posts (never in Discover, even for stewards).
    for who in ("mel", "dee", "olu", "sam", "ana"):
        listed = {item["id"] for item in (await call(env, "get", who, POSTS, expect=200)).json["items"]}
        opens = {pid for pid, table in expected.items() if table[who] == 200 and pid != hidden["id"]}
        assert listed == opens, who
    # The domain page uses the same rule; there the steward and author also see the hidden post, flagged.
    domain_items = {i["id"]: i for i in (await call(env, "get", "sam", f"/api/v1/domains/{KITCHEN}/shares-needs",
                                                     expect=200)).json["items"]}
    assert domain_items[hidden["id"]]["hidden"] is True and domain_items[hidden["id"]]["hidden_reason"] == "Duplicate listing"
    mel_domain = {i["id"] for i in (await call(env, "get", "mel", f"/api/v1/domains/{KITCHEN}/shares-needs",
                                                expect=200)).json["items"]}
    assert mel_domain == {public["id"], members_only["id"]}
    # The ecosystem list needs an ACTIVE row there (a pending newcomer used to read every post).
    await call(env, "get", "pip", f"/api/v1/ecosystems/{OASIS}/shares-needs", expect=403)
    await call(env, "get", "mel", f"/api/v1/ecosystems/{OASIS}/shares-needs", expect=200)


async def test_only_the_author_edits_and_moves_a_post(env):
    refused_by_all_but_ana = {"anon": 401, "pip": (403, "AUTHOR_ONLY"), "mel": (403, "AUTHOR_ONLY"),
                              "dee": (403, "AUTHOR_ONLY"), "sam": (403, "AUTHOR_ONLY"), "olu": (403, "AUTHOR_ONLY"),
                              "rex": (403, "AUTHOR_ONLY"), "fay": (403, "AUTHOR_ONLY"), "xen": (403, "AUTHOR_ONLY")}
    await _check_table(env, {**refused_by_all_but_ana, "ana": 200}, "put", "", {"title": "Changed title"},
                       effect=lambda who, b, a: a["title"] == "Changed title" or pytest.fail(who))
    await _check_table(env, {**refused_by_all_but_ana, "ana": 200}, "post", "/status", {"status": "withdrawn"},
                       effect=lambda who, b, a: (a["status"], a["status_changed_by_member_id"]) == (
                           "withdrawn", b["author_member_id"]) or pytest.fail(who))


async def test_stewards_of_the_posts_own_ecosystem_hide_with_a_reason(env):
    """Owner decision: moderators are stewards of the post's ecosystem; never a founder elsewhere (D1), never
    a steward of another ecosystem; they hide with a recorded reason instead of deleting."""
    table = {"anon": 401, "pip": (403, "MODERATOR_ONLY"), "mel": (403, "MODERATOR_ONLY"),
             "ana": (403, "MODERATOR_ONLY"), "dee": (403, "MODERATOR_ONLY"), "sam": 200, "tia": 200,
             "olu": (403, "MODERATOR_ONLY"), "rex": (403, "MODERATOR_ONLY"), "fay": (403, "MODERATOR_ONLY"),
             "xen": (403, "MODERATOR_ONLY")}

    def hidden_with_reason(who, before, after):
        assert after["hidden_at"] is not None and after["hidden_reason"] == "Off-topic advert"
        assert after["status"] == before["status"]  # a hide is not a status move; the author's state stays

    await _check_table(env, table, "post", "/hide", {"reason": "Off-topic advert"}, effect=hidden_with_reason)
    post = await post_as(env, "ana", title="Needs a reason")
    resp = await call(env, "post", "sam", f"{POSTS}/{post['id']}/hide", expect=400, json={"reason": "  "})
    assert resp.json["code"] == "REASON_REQUIRED"


async def test_a_hidden_post_is_restorable_and_keeps_its_trail(env):
    post = await post_as(env, "ana", title="Restorable")
    await call(env, "post", "sam", f"{POSTS}/{post['id']}/hide", expect=200, json={"reason": "Checking a report"})
    await call(env, "get", "mel", f"{POSTS}/{post['id']}", expect=404)
    # The author sees her hidden post but cannot restore it; others (incl. the D1 founder) cannot even see it.
    for who, status in {"ana": 403, "fay": 404, "rex": 404, "mel": 404}.items():
        await call(env, "post", who, f"{POSTS}/{post['id']}/restore", expect=status, json={})
    shown = (await call(env, "post", "tia", f"{POSTS}/{post['id']}/restore", expect=200, json={})).json
    assert shown["hidden"] is False
    await call(env, "get", "mel", f"{POSTS}/{post['id']}", expect=200)
    row = await _post_row(env, post["id"])
    assert row["hidden_at"] is None and row["hidden_reason"] == "Checking a report"  # the trail stays
    await call(env, "post", "tia", f"{POSTS}/{post['id']}/restore", expect=409, json={})


async def test_only_the_author_hard_deletes_and_only_an_unanswered_post(env):
    """Owner decision: hard delete belongs to the author, and only while nobody has answered."""
    table = {"anon": 401, "mel": (403, "AUTHOR_ONLY"), "dee": (403, "AUTHOR_ONLY"), "sam": (403, "AUTHOR_ONLY"),
             "tia": (403, "AUTHOR_ONLY"), "rex": (403, "AUTHOR_ONLY"), "fay": (403, "AUTHOR_ONLY"), "ana": 200}
    for who, expected in table.items():
        status, code = _expect(expected)
        post = await post_as(env, "ana", title=f"Deletable {who}")
        resp = await call(env, "delete", who, f"{POSTS}/{post['id']}")
        assert resp.status == status, (who, resp.text)
        assert (await _post_row(env, post["id"]) is None) == (status == 200), who
    answered = await post_as(env, "ana", title="Answered one")
    await call(env, "post", "olu", f"{POSTS}/{answered['id']}/respond", expect=201, json={"message": "I have one"})
    resp = await call(env, "delete", "ana", f"{POSTS}/{answered['id']}", expect=409)
    assert resp.json["code"] == "HAS_RESPONSES"
    assert (await call(env, "get", "ana", f"{POSTS}/{answered['id']}", expect=200)).json["caller_can_delete"] is False


async def test_nobody_moves_a_post_to_another_ecosystem_or_domain(env):
    """Owner decision: a post stays where it was posted (the old admin PUT could rewrite ecosystem_id)."""
    post = await post_as(env, "ana", title="Stays put")
    before = await _post_row(env, post["id"])
    for field, value in (("ecosystem_id", RIVER), ("domain_id", GARDEN), ("domain_id", DOCK)):
        resp = await call(env, "put", "ana", f"{POSTS}/{post['id']}", expect=400, json={field: str(value), "title": "X"})
        assert resp.json["code"] == "CANNOT_MOVE"
    assert await _post_row(env, post["id"]) == before
    # Resending the unchanged place with an edit is fine (edit forms resend every field).
    await call(env, "put", "ana", f"{POSTS}/{post['id']}", expect=200,
               json={"ecosystem_id": str(OASIS), "domain_id": str(KITCHEN), "title": "Stays put, renamed"})


async def test_who_may_respond(env):
    table = {"anon": 401, "pip": (403, "CONSENT_PENDING"), "mel": 201, "dee": 201, "sam": 201, "olu": 201,
             "rex": 201, "fay": 201, "xen": (403, "MEMBERSHIP_REQUIRED"), "ana": (409, "OWN_POST")}
    await _check_table(env, table, "post", "/respond", {"message": "Happy to help"},
                       effect=lambda who, b, a: a["links"] == 1 or pytest.fail(who))


async def test_the_moderation_list_covers_only_ecosystems_the_caller_stewards(env):
    oasis_post = await post_as(env, "ana", title="Oasis post")
    river_post = await post_as(env, "olu", title="River post", domain=DOCK, ecosystem=RIVER)
    await call(env, "post", "sam", f"{POSTS}/{oasis_post['id']}/hide", expect=200, json={"reason": "Spam"})
    views = {}
    for who in ("sam", "rex", "fay", "mel", "duo"):
        body = (await call(env, "get", who, f"{POSTS}/admin", expect=200)).json
        views[who] = ({i["id"] for i in body["items"]}, {e["name"] for e in body["moderated_ecosystems"]})
    assert views["sam"] == ({oasis_post["id"]}, {"Oasis"})
    assert views["rex"] == ({river_post["id"]}, {"River House"})
    assert views["fay"] == (set(), {"Fresh Start"})  # the D1 founder moderates only her own ecosystem
    assert views["mel"] == (set(), set())
    assert views["duo"] == ({oasis_post["id"], river_post["id"]}, {"Oasis", "River House"})
    await call(env, "get", "anon", f"{POSTS}/admin", expect=401)


async def _collab_row(env, collab_id) -> tuple:
    async with env.db() as session:
        record = await session.get(Collaboration, uuid.UUID(collab_id))
        approvals = await session.scalar(select(func.count(CollaborationApproval.id)).where(
            CollaborationApproval.collaboration_id == record.id))
        return record.status, approvals, record.ended_by_member_id, record.end_reason


async def _propose(env, who: str, source=KITCHEN, target=DOCK, title: str = "Shared boats") -> dict:
    return (await call(env, "post", who, COLLABS, expect=201, json={
        "source_domain_id": str(source), "target_domain_id": str(target), "title": title})).json


async def test_a_steward_of_each_side_approves_for_that_side(env):
    """Owner decision: per-side approval by a steward there; members, other ecosystems and the D1 founder cannot."""
    table = {"anon": 401, "pip": 404, "xen": 404, "mel": (403, "APPROVE_DENIED"), "ana": (403, "APPROVE_DENIED"),
             "dee": (403, "APPROVE_DENIED"), "olu": (403, "APPROVE_DENIED"), "fay": (403, "APPROVE_DENIED"),
             "sam": 200, "tia": 200, "rex": 200}
    for who, expected in table.items():
        status, code = _expect(expected)
        collab = await _propose(env, "mel", title=f"Boats {who}")
        before = await _collab_row(env, collab["id"])
        resp = await call(env, "post", who, f"{COLLABS}/{collab['id']}/approve", json={})
        assert resp.status == status, (who, resp.text)
        if code:
            assert resp.json["code"] == code
        after = await _collab_row(env, collab["id"])
        assert (after == before) == (status != 200), who
        if status == 200:
            assert after[:2] == ("proposed", 1) and len(resp.json["awaiting"]) == 1


async def test_same_ecosystem_collaboration_needs_a_steward_who_did_not_propose_it(env):
    collab = await _propose(env, "sam", source=KITCHEN, target=GARDEN, title="Kitchen garden")
    assert collab["approvals"] == []  # no auto-approval when both sides are one ecosystem
    resp = await call(env, "post", "sam", f"{COLLABS}/{collab['id']}/approve", expect=403, json={})
    assert resp.json["code"] == "APPROVE_DENIED"
    done = (await call(env, "post", "tia", f"{COLLABS}/{collab['id']}/approve", expect=200, json={})).json
    assert done["status"] == "active" and done["review_date"]


async def test_a_proposing_steward_counts_for_the_source_side_only(env):
    """Owner default: the source side is auto-approved when its steward proposes; nobody activates alone."""
    collab = await _propose(env, "duo", title="Duo's boats")  # a steward of BOTH sides
    assert [a["ecosystem_name"] for a in collab["approvals"]] == ["Oasis"]
    assert [a["ecosystem_name"] for a in collab["awaiting"]] == ["River House"]
    assert collab["caller_can_approve_for"] == []
    resp = await call(env, "post", "duo", f"{COLLABS}/{collab['id']}/approve", expect=409, json={})
    assert resp.json["code"] == "ALREADY_APPROVED"
    await call(env, "post", "duo", f"{COLLABS}/{collab['id']}/approve", expect=403, json={"ecosystem_id": str(RIVER)})
    assert await _collab_row(env, collab["id"]) == ("proposed", 1, None, None)
    # A member proposing records no approval at all.
    assert (await _propose(env, "mel", title="Mel's boats"))["approvals"] == []


async def test_who_may_end_a_collaboration(env):
    table = {"anon": 401, "pip": 404, "xen": 404, "ana": (403, "END_DENIED"), "dee": (403, "END_DENIED"),
             "olu": (403, "END_DENIED"), "fay": (403, "END_DENIED"), "mel": 200, "sam": 200, "rex": 200}
    for who, expected in table.items():
        status, code = _expect(expected)
        collab = await _propose(env, "mel", title=f"Ending {who}")
        before = await _collab_row(env, collab["id"])
        resp = await call(env, "post", who, f"{COLLABS}/{collab['id']}/end",
                          json={"outcome": "dissolved", "reason": "Not this season"})
        assert resp.status == status, (who, resp.text)
        if code:
            assert resp.json["code"] == code
        after = await _collab_row(env, collab["id"])
        assert (after == before) == (status != 200), who
    collab = await _propose(env, "mel", title="Needs a reason")
    resp = await call(env, "post", "sam", f"{COLLABS}/{collab['id']}/end", expect=400, json={"outcome": "dissolved"})
    assert resp.json["code"] == "REASON_REQUIRED"
    resp = await call(env, "post", "sam", f"{COLLABS}/{collab['id']}/end", expect=409,
                      json={"outcome": "completed", "reason": "Never started"})
    assert resp.json["allowed"] == ["dissolved"]


async def test_proposed_collaborations_are_read_by_either_side_only(env):
    collab = await _propose(env, "mel", title="Quiet plan")
    for who, status in {"anon": 401, "olu": 200, "sam": 200, "fay": 200, "pip": 404, "xen": 404}.items():
        await call(env, "get", who, f"{COLLABS}/{collab['id']}", expect=status)
    listed = {i["id"] for i in (await call(env, "get", "pip", f"{COLLABS}?status=all", expect=200)).json["items"]}
    assert collab["id"] not in listed


# --- FX-Exchange (wave-c F3): recording a collaboration's review -------------------------------------------------


async def test_who_may_record_a_collaboration_review(env):
    """A steward of either side records a review; the proposer, members, other ecosystems and the D1 founder cannot."""
    collab = await _propose(env, "mel", title="Reviewed boats")
    for steward in ("sam", "rex"):
        await call(env, "post", steward, f"{COLLABS}/{collab['id']}/approve", expect=200, json={})

    async def review_state():
        async with env.db() as session:
            record = await session.get(Collaboration, uuid.UUID(collab["id"]))
            await session.refresh(record)
            return record.review_date, record.reviewed_by_member_id, record.review_note

    table = {"anon": 401, "pip": (403, "REVIEW_DENIED"), "xen": (403, "REVIEW_DENIED"), "mel": (403, "REVIEW_DENIED"),
             "ana": (403, "REVIEW_DENIED"), "dee": (403, "REVIEW_DENIED"), "olu": (403, "REVIEW_DENIED"),
             "fay": (403, "REVIEW_DENIED"), "sam": 200, "tia": 200, "rex": 200, "duo": 200}
    for who, expected in table.items():
        status, code = _expect(expected)
        before = await review_state()
        resp = await call(env, "post", who, f"{COLLABS}/{collab['id']}/review", json={"note": f"Checked by {who}"})
        assert resp.status == status, (who, resp.text)
        if code:
            assert resp.json["code"] == code
        after = await review_state()
        if status == 200:
            assert after[2] == f"Checked by {who}" and after[1] is not None, who
        else:
            assert after == before, (who, "a refused review changed the collaboration")
