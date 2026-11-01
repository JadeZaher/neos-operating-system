"""Operator domain choices stay unambiguous; see agent/AGENTS.md 'Domain lookup'."""

from datetime import datetime, timedelta
import uuid

import pytest
from sqlalchemy import func, select

from neos_agent.db.models import CircleMembership, Domain, SharesNeeds
from tests.test_g_agent_assistant import OASIS, RIVER, SEED_LIBRARY, _tool, env  # noqa: F401


async def _domain(env, *, name, purpose, ecosystem=OASIS, older=False):
    domain = Domain(
        id=uuid.uuid4(), ecosystem_id=ecosystem, domain_id=f"DOM-{uuid.uuid4().hex[:8]}",
        name=name, purpose=purpose, status="active", version="1.0",
        created_at=datetime.now() - timedelta(days=1 if older else 0),
    )
    async with env.db() as db:
        db.add(domain)
        await db.commit()
    return domain


async def _write_counts(env):
    async with env.db() as db:
        return tuple([await db.scalar(select(func.count()).select_from(model)) for model in (CircleMembership, SharesNeeds)])


@pytest.mark.parametrize("name", ["Seed Bank", "Seed Bank (uxqa eval)"])
async def test_a_named_group_precedes_an_older_groups_purpose_match(env, name):
    await _domain(env, name="Regenerative Circle", purpose="Maintaining a seed bank and food forest.", older=True)
    requested = await _domain(env, name=name, purpose="Save and exchange seeds.")
    read = await _tool(env, "ben", "get_domain", domain="Seed Bank")
    assert read["success"] is True
    assert read["data"]["id"] == str(requested.id)
    joined = await _tool(env, "ben", "join_domain", domain="Seed Bank")
    assert joined["success"] is True
    async with env.db() as db:
        assert list((await db.scalars(select(CircleMembership.domain_id))).all()) == [requested.id]


async def test_duplicate_exact_names_across_selected_ecosystems_require_a_choice_but_identifiers_work(env):
    duplicate = await _domain(env, name="Seed Library", purpose="River seeds.", ecosystem=RIVER)
    before = await _write_counts(env)
    for tool, extra in (
        ("get_domain", {}), ("join_domain", {}),
        ("publish_share_need", {"type": "need", "title": "Seed trays", "description": "We need trays.", "visibility": "public"}),
    ):
        result = await _tool(env, "fay", tool, domain="Seed Library", **extra)
        assert result["success"] is False
        assert result["code"] == "AMBIGUOUS_DOMAIN"
        assert {candidate["id"] for candidate in result["candidates"]} == {str(SEED_LIBRARY), str(duplicate.id)}
        assert {candidate["ecosystem"] for candidate in result["candidates"]} == {"Oasis", "River House"}
    assert await _write_counts(env) == before
    for identifier in (str(duplicate.id), duplicate.domain_id):
        result = await _tool(env, "fay", "get_domain", domain=identifier)
        assert result["success"] is True
        assert result["data"]["id"] == str(duplicate.id)
    scoped = await _tool(env, "ben", "get_domain", domain="Seed Library")
    assert scoped["success"] is True
    assert scoped["data"]["id"] == str(SEED_LIBRARY)


@pytest.mark.parametrize("match_kind", ["partial_name", "legacy_label", "purpose"])
async def test_ambiguous_partial_names_or_labels_never_join_or_publish(env, match_kind):
    for side in ("North", "South"):
        name = f"Seed Bank {side}" if match_kind == "partial_name" else None if match_kind == "legacy_label" else side
        purpose = f"Seed Bank — {side} seed exchange" if match_kind == "legacy_label" else "Maintaining the seed bank."
        await _domain(env, name=name, purpose=purpose)
    before = await _write_counts(env)
    for tool, extra in (
        ("join_domain", {}),
        ("publish_share_need", {"type": "share", "title": "Spare seeds", "description": "Seeds to share.", "visibility": "public"}),
    ):
        result = await _tool(env, "ben", tool, domain="Seed Bank", **extra)
        assert result["success"] is False
        assert result["code"] == "AMBIGUOUS_DOMAIN"
        assert len(result["candidates"]) == 2
        assert "Ask which one" in result["error"]
    assert await _write_counts(env) == before
