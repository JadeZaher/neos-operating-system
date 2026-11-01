"""UX-QA pass 03 (cross-ecosystem exchange), lane A: the health and audit pages say why, name, date and filter.

Drives the real safeguards and agreements blueprints over the shared G-Maint world (`tests/test_g_health.py`,
its one clock included). Rules: api/AGENTS.md "Maintenance and health (G-Maint)" > "Governance health" ("Say why,
name the ecosystem, one publish date") and "Agreement review" (`?review=overdue`).
"""

from __future__ import annotations

import datetime as dt
import uuid

from neos_agent.api.safeguards import AUDITOR_NOT_INDEPENDENT
from neos_agent.db.models import Agreement, GovernanceHealthAudit

from tests.test_g_health import (  # noqa: F401 — env and _one_clock are the shared fixtures
    HOUSE, NOW, OASIS, RIVER, TODAY, _add, _agreement, _call, _one_clock, _publish, env,
)


# ---------------------------------------------------------------------------
# p3-health-audit-and-review-1: the page says why there is no "Record an audit"
# ---------------------------------------------------------------------------


async def test_the_safeguards_entry_says_why_the_caller_cannot_record_an_audit_in_the_routes_words(env):
    member = (await _call(env, "get", "ben", "/api/v1/safeguards", expect=200)).json["ecosystems"][0]
    steward = (await _call(env, "get", "mo", "/api/v1/safeguards", expect=200)).json["ecosystems"][0]
    assert (member["caller_can_record_audit"], member["caller_record_audit_refusal"]) == (True, None)
    assert (steward["caller_can_record_audit"], steward["caller_record_audit_refusal"]) == (False, AUDITOR_NOT_INDEPENDENT)

    started = await _call(env, "post", "mo", "/api/v1/safeguards/audits", json={"ecosystem_id": str(OASIS)}, expect=403)
    assert started.json["error"] == steward["caller_record_audit_refusal"]  # the page and the route say the same


# ---------------------------------------------------------------------------
# p3-health-audit-and-review-5 and -6: the audit names its ecosystem; "Completed" is the publish date
# ---------------------------------------------------------------------------


async def test_a_published_audit_names_its_ecosystem_and_keeps_its_publish_date_after_a_later_write(env):
    published = await _publish(env, "ben")
    assert (published["ecosystem_name"], published["completed_at"]) == ("Oasis", published["audit_date"])
    async with env.db() as session:  # a later write to the row (the seeded audits had one): updated_at moves
        (await session.get(GovernanceHealthAudit, uuid.UUID(published["id"]))).updated_at = NOW + dt.timedelta(days=40)
        await session.commit()

    detail = (await _call(env, "get", "ada", f"/api/v1/safeguards/audits/{published['id']}", expect=200)).json
    listed = (await _call(env, "get", "ada", "/api/v1/safeguards/audits", expect=200)).json["items"]
    latest = (await _call(env, "get", "ada", "/api/v1/safeguards", expect=200)).json["ecosystems"][0]["latest_audit"]
    # Before: completed_at was updated_at, so "Completed" moved 40 days past "Published on".
    assert (detail["ecosystem_name"], detail["completed_at"]) == ("Oasis", published["audit_date"])
    assert [(item["id"], item["completed_at"]) for item in listed] == [(published["id"], published["audit_date"])]
    assert (latest["ecosystem_name"], latest["completed_at"]) == ("Oasis", published["audit_date"])


# ---------------------------------------------------------------------------
# p3-health-audit-and-review-9: "N Agreement reviews overdue" opens exactly those N
# ---------------------------------------------------------------------------


async def test_reviews_overdue_links_to_the_list_filtered_by_the_same_rule(env):
    overdue = await _agreement(env, status="active", review_date=TODAY - dt.timedelta(days=3), title="Late rules")
    reviewing = await _agreement(env, status="under_review", review_date=TODAY - dt.timedelta(days=1), title="In review")
    await _agreement(env, status="active", review_date=TODAY, title="Due today")  # not passed everywhere yet
    await _agreement(env, status="sunset", review_date=TODAY - dt.timedelta(days=30), title="Winding down")  # not in force

    snapshot = (await _call(env, "get", "ada", f"/api/v1/safeguards/snapshot?ecosystem_id={OASIS}", expect=200)).json
    attention = {item["key"]: item for item in snapshot["attention"]}["reviews_overdue"]
    assert (attention["count"], attention["link"]) == (2, f"/agreements?review=overdue&ecosystem_id={OASIS}")

    filtered = (await _call(env, "get", "ada", "/api/v1/agreements/?review=overdue", expect=200)).json
    flagged = {item["id"] for item in (await _call(env, "get", "ada", "/api/v1/agreements/", expect=200)).json["items"]
               if item["review_overdue"]}
    assert {item["id"] for item in filtered["items"]} == flagged == {str(overdue), str(reviewing)}
    assert filtered["total"] == attention["count"] and str(HOUSE) not in flagged

    refused = await _call(env, "get", "ada", "/api/v1/agreements/?review=soon", expect=400)
    assert "review" in refused.json["error"]


async def test_the_link_opens_exactly_the_counted_reviews_with_two_ecosystems_selected_or_one_shared_in(env):
    late = TODAY - dt.timedelta(days=3)
    oasis_own = {await _agreement(env, status="active", review_date=late, title="Late rules"),
                 await _agreement(env, status="under_review", review_date=late, title="In review")}
    river_own, shared_in = uuid.uuid4(), uuid.uuid4()  # both River's; the second is shared with Oasis
    await _add(env, *(Agreement(id=agreement_id, ecosystem_id=RIVER, agreement_id=f"AGR-{agreement_id.hex[:6].upper()}",
                                type="organizational", title=title, version="1.0", status="active", text="River terms.",
                                review_date=late, shared_ecosystem_ids=shared)
                      for agreement_id, title, shared in ((river_own, "River rota", None),
                                                          (shared_in, "Shared tools", [str(OASIS)]))))

    # Dee is active in Oasis and River, both selected: each ecosystem's count opens exactly its own overdue reviews.
    for ecosystem, counted in ((OASIS, oasis_own), (RIVER, {river_own, shared_in})):
        snapshot = (await _call(env, "get", "dee", f"/api/v1/safeguards/snapshot?ecosystem_id={ecosystem}", expect=200)).json
        attention = {item["key"]: item for item in snapshot["attention"]}["reviews_overdue"]
        opened = (await _call(env, "get", "dee", "/api/v1" + attention["link"], expect=200)).json  # the page's request
        assert opened["total"] == attention["count"] == len(counted)
        assert {item["id"] for item in opened["items"]} == {str(agreement_id) for agreement_id in counted}
    # Before: the link named no ecosystem, so Oasis's "2 reviews overdue" opened all four selected ones.
    assert (await _call(env, "get", "dee", "/api/v1/agreements?review=overdue", expect=200)).json["total"] == 4

    # Ada selects Oasis only: River's agreement shared into Oasis is in her registry, but Oasis's count never had it.
    assert (await _call(env, "get", "ada", "/api/v1/agreements?review=overdue", expect=200)).json["total"] == 3
    oasis_link = f"/api/v1/agreements?review=overdue&ecosystem_id={OASIS}"
    assert (await _call(env, "get", "ada", oasis_link, expect=200)).json["total"] == 2

    # An ecosystem outside the caller's scope lists nothing; an id that is not a UUID is refused.
    assert (await _call(env, "get", "olu", oasis_link, expect=200)).json["total"] == 0
    malformed = await _call(env, "get", "dee", "/api/v1/agreements?ecosystem_id=oasis", expect=400)
    assert "ecosystem_id" in malformed.json["error"]
