"""UX-QA pass 03 (cross-ecosystem exchange), lane A: a newcomer's first steps come in the order they build on.

Drives the real onboarding, orientation and next-steps blueprints over the shared G-Onboard world
(`tests/test_onboarding_flows.py`). Rules: services/AGENTS.md "Member lifecycle (G-Onboard)" > "Queue items" and
"Next steps" > "Rules of the queue" (`_STEP_ORDER`).
"""

from __future__ import annotations

from tests.test_onboarding_flows import (  # noqa: F401 — world is the shared fixture
    ESCHER, OMNI_MAP, OMNIONE, call, queue_actions, world,
)


async def _newcomer_items(world, who: str) -> list[dict]:
    response = await call(world, "get", who, "/api/v1/me/next-steps")
    assert response.status == 200, response.text
    return [item for item in response.json["items"] if item["kind"] == "newcomer"]


async def test_a_new_member_is_asked_to_walk_the_orientation_before_its_entry_quiz(world):
    items = await _newcomer_items(world, "kit")
    # Before: both undated newcomer items, ordered by title, so "Take Community Onboarding" came first.
    assert [(item["action"], item["title"]) for item in items] == [
        ("start_orientation", "Walk through OmniOne's orientation"), ("take_entry_quiz", "Take Community Onboarding")]
    assert items[1]["why"].startswith("Take it after you finish the orientation journey")

    saved = await call(world, "post", "kit", f"/api/v1/orientation/ethos/{OMNIONE}/progress",
                       json={"journey_map_id": str(OMNI_MAP), "current_step": 3, "status": "complete"})
    assert saved.status == 200, saved.text
    [quiz] = await _newcomer_items(world, "kit")
    assert quiz["action"] == "take_entry_quiz" and "orientation journey" not in quiz["why"]  # nothing left to walk first


async def test_a_stuck_newcomer_item_offers_both_ways_and_clears_when_they_finish_alone(world):
    [item] = await _newcomer_items(world, "eve")
    assert item["action"] == "confirm_membership"
    # Before: "so a steward confirms them", while the newcomer's page says nobody needs to approve them.
    assert "Ask Tess to press Check my membership on their consent page" in item["why"]
    assert "confirm them on their member page" in item["why"]

    healed = await call(world, "post", "tess", f"/api/v1/ecosystems/{ESCHER}/join")  # her "Check my membership"
    assert (healed.status, healed.json["membership_status"]) == (200, "active")
    assert await queue_actions(world, "eve") == []
