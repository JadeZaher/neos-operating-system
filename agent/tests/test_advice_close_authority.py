"""Advice-close authority holes (review 2026-11-01): a steward cannot backdate the proposer's deadline, and a
send-back starts a revision round with no deadline. See api/AGENTS.md "Proposal authorship and manage rule"."""
import datetime as dt
import uuid
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.api.next_steps import next_steps_api_bp
from neos_agent.auth.ecosystem_scope import EcosystemScope
from neos_agent.db.models import AdviceLog, Base, Proposal
from neos_agent.services.dates import aoe_today
from tests.test_uxqa_p1_governance import (
    ECO, PEOPLE, _call, _create_app, _create_proposal, _open_for_advice, _seed,
)

TODAY = aoe_today()  # due dates pass on the server's Anywhere-on-Earth day, not the UTC calendar day
STEWARD_PROMPT = "close advice for the proposer"


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
    app = _create_app()
    app.ctx.db = factory

    @app.on_request
    async def scope(request):
        if getattr(request.ctx, "member", None) is not None:
            request.ctx.ecosystem_scope = EcosystemScope.from_ecosystems([SimpleNamespace(id=ECO, name="Oasis")], [ECO])

    app.blueprint(next_steps_api_bp)
    yield SimpleNamespace(app=app, db=factory)
    await engine.dispose()


async def _steward_close_prompts(app) -> list:
    queue = (await _call(app, "get", "mo", "/api/v1/me/next-steps")).json
    return [i for i in queue["items"] if STEWARD_PROMPT in i["what"]]


@pytest.mark.asyncio
async def test_steward_cannot_backdate_deadline_to_close_advice(env):
    proposal = await _create_proposal(env.app)  # no deadline: proposer only
    url = f"/api/v1/proposals/{proposal['id']}"
    await _open_for_advice(env.app, proposal["id"])
    assert (await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})).status == 201

    yesterday = (TODAY - dt.timedelta(days=1)).isoformat()
    moved = await _call(env.app, "put", "mo", url, json={"advice_deadline": yesterday})
    assert (moved.status, moved.json["code"]) == (403, "ADVICE_DEADLINE_AUTHOR_ONLY")
    async with env.db() as session:
        assert (await session.get(Proposal, uuid.UUID(proposal["id"]))).advice_deadline is None
    assert (await _call(env.app, "post", "mo", f"{url}/status", json={"status": "consent"})).status == 403
    assert await _steward_close_prompts(env.app) == []

    # The author may move it.
    assert (await _call(env.app, "put", "ada", url, json={"advice_deadline": yesterday})).status == 200
    assert (await _call(env.app, "post", "mo", f"{url}/status", json={"status": "consent"})).status == 200


@pytest.mark.asyncio
async def test_legacy_proposal_without_author_link_keeps_steward_deadline_edit(env):
    from tests.test_uxqa_p1_governance import LEGACY_PROPOSAL
    tomorrow = (TODAY + dt.timedelta(days=1)).isoformat()
    edited = await _call(env.app, "put", "mo", f"/api/v1/proposals/{LEGACY_PROPOSAL}", json={"advice_deadline": tomorrow})
    assert (edited.status, edited.json["advice_deadline"]) == (200, tomorrow)


@pytest.mark.asyncio
async def test_send_back_starts_revision_round_without_a_deadline(env):
    passed = (TODAY - dt.timedelta(days=3)).isoformat()
    proposal = await _create_proposal(env.app, advice_deadline=passed)
    url = f"/api/v1/proposals/{proposal['id']}"
    await _open_for_advice(env.app, proposal["id"])
    assert (await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Add a rota"})).status == 201
    assert (await _call(env.app, "post", "ada", f"{url}/status", json={"status": "consent"})).status == 200
    back = await _call(env.app, "post", "mo", f"{url}/status", json={"status": "advice", "note": "Shorter hours"})
    assert (back.status, back.json["status"], back.json["advice_deadline"]) == (200, "advice", None)
    async with env.db() as session:
        latest = (await session.scalars(select(AdviceLog).order_by(AdviceLog.created_at.desc()))).first()
        assert latest.advice_window_end is None
    assert (await _call(env.app, "post", "ben", f"{url}/advice", json={"content": "Better"})).status == 201

    # No deadline on the revised version: a steward can neither close advice nor is asked to.
    assert (await _call(env.app, "post", "mo", f"{url}/status", json={"status": "consent"})).status == 403
    assert await _steward_close_prompts(env.app) == []

    # The proposer sets a new deadline; the steward is held until it has passed.
    future = (TODAY + dt.timedelta(days=5)).isoformat()
    assert (await _call(env.app, "put", "ada", url, json={"advice_deadline": future})).status == 200
    assert (await _call(env.app, "post", "mo", f"{url}/status", json={"status": "consent"})).status == 403
    assert (await _call(env.app, "put", "ada", url, json={"advice_deadline": passed})).status == 200
    assert len(await _steward_close_prompts(env.app)) == 1
    assert (await _call(env.app, "post", "mo", f"{url}/status", json={"status": "consent"})).status == 200
