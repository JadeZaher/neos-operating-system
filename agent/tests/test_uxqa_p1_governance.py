"""UX-QA pass 01 (first week), lane 1: governance integrity flows.

Drives the real proposals/domains blueprints (and the MCP tool functions) over
an in-memory SQLite DB, acting as different members through an injected
session. Rules under test live in src/neos_agent/api/AGENTS.md:
"Proposal authorship and manage rule" and "Domain naming and participation flags".
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent import mcp_server
from neos_agent.api.domains import domain_display_name, domains_api_bp
from neos_agent.api.proposals import MANAGE_DENIED, SELF_ADVICE_DENIED, proposals_api_bp
from neos_agent.db.models import Base, Domain, Ecosystem, Member, Proposal, User

ECO = uuid.UUID("0000000a-0000-0000-0000-000000000001")
STEWARDED_DOMAIN = uuid.UUID("0000000a-0000-0000-0000-0000000000d1")
LEGACY_PROPOSAL = uuid.UUID("0000000a-0000-0000-0000-0000000000f1")


@dataclass(frozen=True)
class Person:
    user_id: uuid.UUID
    member_id: uuid.UUID
    name: str
    role: str


def _person(key: str, name: str, role: str) -> Person:
    return Person(
        user_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"uxqa-p1.{key}.user"),
        member_id=uuid.uuid5(uuid.NAMESPACE_DNS, f"uxqa-p1.{key}.member"),
        name=name,
        role=role,
    )


PEOPLE = {
    "ada": _person("ada", "Ada", "user"),  # proposal author
    "ben": _person("ben", "Ben", "user"),  # another member
    "mo": _person("mo", "Mo", "mod"),  # ecosystem steward
    "sol": _person("sol", "Sol", "user"),  # domain steward without an ecosystem role
}


async def _seed(session: AsyncSession) -> None:
    session.add(Ecosystem(id=ECO, name="Oasis", status="active"))
    for key, p in PEOPLE.items():
        session.add(User(id=p.user_id, display_name=p.name))
    await session.flush()
    for key, p in PEOPLE.items():
        session.add(Member(
            id=p.member_id, ecosystem_id=ECO, user_id=p.user_id,
            member_id=f"MEM-{key.upper()}", display_name=p.name,
            current_status="active", role=p.role,
        ))
    session.add(Domain(
        id=STEWARDED_DOMAIN, ecosystem_id=ECO, domain_id="DOM-1A2B3C4D", version="1.0",
        status="active", purpose="Newcomer Garden — a shared garden for first-month members",
        current_steward="Sol", steward_id=PEOPLE["sol"].member_id,
    ))
    # Legacy row: free-text proposer that happens to match Ben, but no author link.
    session.add(Proposal(
        id=LEGACY_PROPOSAL, ecosystem_id=ECO, proposal_id="PROP-LEGACY", type="policy",
        title="Legacy proposal", version="1.0", status="advice", proposer="Ben",
    ))
    await session.commit()


def _create_app() -> Sanic:
    """Blueprint app; the x-test-as header picks who is signed in."""
    app = Sanic(f"test-uxqa-p1-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        p = PEOPLE[who]
        request.ctx.member = Member(
            id=p.member_id, ecosystem_id=ECO, user_id=p.user_id, member_id="MEM-AUTH",
            display_name=p.name, current_status="active", role=p.role,
        )
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = [ECO]
        request.ctx.authorized_ecosystem_ids = [ECO]

    app.blueprint(proposals_api_bp)
    app.blueprint(domains_api_bp)
    return app


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await _seed(session)
    app = _create_app()
    app.ctx.db = session_factory
    yield SimpleNamespace(app=app, db=session_factory)
    await engine.dispose()


async def _call(app: Sanic, method: str, who: str, url: str, **kwargs):
    _, resp = await getattr(app.asgi_client, method)(url, headers={"x-test-as": who}, **kwargs)
    return resp


async def _create_proposal(app: Sanic, who: str = "ada", **fields) -> dict:
    body = {"ecosystem_id": str(ECO), "type": "policy", "title": "Evening garden hours", **fields}
    resp = await _call(app, "post", who, "/api/v1/proposals", json=body)
    assert resp.status == 201, resp.text
    return resp.json


async def _open_for_advice(app: Sanic, proposal_id: str) -> None:
    resp = await _call(app, "post", "ada", f"/api/v1/proposals/{proposal_id}/status", json={"status": "advice"})
    assert resp.status == 200, resp.text


# ---------------------------------------------------------------------------
# Proposals: authorship and the manage rule
# ---------------------------------------------------------------------------


async def test_created_proposal_records_the_caller_as_author(env):
    created = await _create_proposal(env.app)
    assert created["proposer"] == "Ada"  # defaults to the caller's name
    assert created["proposer_member_id"] == str(PEOPLE["ada"].member_id)
    assert created["caller_is_proposer"] is True and created["caller_can_manage"] is True

    # Proposing on someone's behalf keeps the text but the caller stays the author.
    on_behalf = await _create_proposal(env.app, proposer="Garden Circle")
    assert on_behalf["proposer"] == "Garden Circle"
    assert on_behalf["proposer_member_id"] == str(PEOPLE["ada"].member_id)

    other_view = (await _call(env.app, "get", "ben", f"/api/v1/proposals/{created['id']}")).json
    assert other_view["caller_can_conduct"] is True
    assert other_view["caller_can_manage"] is False
    assert other_view["caller_is_proposer"] is False


@pytest.mark.parametrize("actor, expected_status", [
    ("ben", 403),  # another member: participation only
    ("ada", 200),  # the author
    ("mo", 200),  # an ecosystem steward
])
async def test_withdraw_requires_author_or_steward(env, actor, expected_status):
    proposal = await _create_proposal(env.app)
    resp = await _call(env.app, "post", actor, f"/api/v1/proposals/{proposal['id']}/status", json={"status": "withdrawn"})
    assert resp.status == expected_status, resp.text
    current = (await _call(env.app, "get", "ada", f"/api/v1/proposals/{proposal['id']}")).json
    assert current["status"] == ("withdrawn" if expected_status == 200 else "draft")
    if expected_status == 403:
        assert resp.json["error"] == MANAGE_DENIED


async def test_only_the_author_or_steward_can_edit(env):
    proposal = await _create_proposal(env.app)
    url = f"/api/v1/proposals/{proposal['id']}"
    denied = await _call(env.app, "put", "ben", url, json={"title": "Hijacked"})
    assert denied.status == 403
    allowed = await _call(env.app, "put", "ada", url, json={"title": "Evening and weekend hours"})
    assert allowed.status == 200, allowed.text
    assert allowed.json["title"] == "Evening and weekend hours"


async def test_legacy_proposal_without_author_link_is_steward_only(env):
    url = f"/api/v1/proposals/{LEGACY_PROPOSAL}/status"
    # Matching proposer text does not grant management; only the link does.
    assert (await _call(env.app, "post", "ben", url, json={"status": "withdrawn"})).status == 403
    assert (await _call(env.app, "post", "mo", url, json={"status": "withdrawn"})).status == 200


# ---------------------------------------------------------------------------
# Advice integrity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("body", [{"content": ""}, {"content": "   \n "}, {}])
async def test_blank_advice_is_rejected_and_does_not_advance(env, body):
    proposal = await _create_proposal(env.app)
    await _open_for_advice(env.app, proposal["id"])
    resp = await _call(env.app, "post", "ben", f"/api/v1/proposals/{proposal['id']}/advice", json=body)
    assert resp.status == 400
    assert resp.json["error"] == "Advice text is required"
    current = (await _call(env.app, "get", "ben", f"/api/v1/proposals/{proposal['id']}")).json
    assert current["status"] == "advice"
    assert current["advice_logs"] == []


async def test_proposer_cannot_self_advise_and_others_advance_the_round(env):
    proposal = await _create_proposal(env.app)
    await _open_for_advice(env.app, proposal["id"])
    url = f"/api/v1/proposals/{proposal['id']}/advice"

    self_advice = await _call(env.app, "post", "ada", url, json={"content": "I agree with myself"})
    assert self_advice.status == 409
    assert self_advice.json["error"] == SELF_ADVICE_DENIED

    # The advisor is the caller, whatever the body claims; the default
    # one-round gate then advances the proposal and says so.
    advice = await _call(env.app, "post", "ben", url, json={"advisor": "Spoofed", "content": "Add a winter schedule"})
    assert advice.status == 201, advice.text
    assert [e["advisor"] for e in advice.json["entries"]] == ["Ben"]
    assert advice.json["auto_transitions"] == ["advice->consent"]
    current = (await _call(env.app, "get", "ada", f"/api/v1/proposals/{proposal['id']}")).json
    assert current["status"] == "consent"


# ---------------------------------------------------------------------------
# Domains: naming, role checks, participation flags
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name, purpose, expected", [
    ("Community Kitchen", "Kitchen — meals", "Community Kitchen"),  # stored name wins
    ("  ", "Newcomer Garden — a shared garden", "Newcomer Garden"),  # blank name -> purpose prefix
    (None, "Just a purpose with no name segment", "DOM-CODE"),  # no separator -> code
    (None, ("x" * 121) + " — too long to be a name", "DOM-CODE"),  # over 120 chars -> code
    (None, None, "DOM-CODE"),
])
def test_domain_display_name_fallbacks(name, purpose, expected):
    domain = SimpleNamespace(name=name, purpose=purpose, domain_id="DOM-CODE")
    assert domain_display_name(domain) == expected


@pytest.mark.parametrize("actor, expected_status", [("ben", 403), ("mo", 201)])
async def test_creating_a_domain_requires_an_ecosystem_steward(env, actor, expected_status):
    body = {"ecosystem_id": str(ECO), "name": "Tool Library", "purpose": "Lend tools to members"}
    resp = await _call(env.app, "post", actor, "/api/v1/domains", json=body)
    assert resp.status == expected_status, resp.text
    if expected_status == 201:
        assert resp.json["name"] == "Tool Library"
        assert resp.json["display_name"] == "Tool Library"
        assert resp.json["domain_id"].startswith("DOM-")


@pytest.mark.parametrize("actor, expected_status", [
    ("ben", 403),  # plain member
    ("sol", 200),  # this domain's steward
    ("mo", 200),  # ecosystem steward
])
async def test_editing_a_domain_requires_its_steward_or_an_ecosystem_steward(env, actor, expected_status):
    resp = await _call(env.app, "put", actor, f"/api/v1/domains/{STEWARDED_DOMAIN}", json={"name": "Garden Commons"})
    assert resp.status == expected_status, resp.text
    if expected_status == 200:
        assert resp.json["display_name"] == "Garden Commons"


async def test_joining_a_domain_is_reflected_in_detail_and_list(env):
    detail_url = f"/api/v1/domains/{STEWARDED_DOMAIN}"
    before = (await _call(env.app, "get", "ben", detail_url)).json
    assert before["display_name"] == "Newcomer Garden"
    assert before["caller_is_participant"] is False
    assert before["caller_can_edit"] is False

    joined = await _call(env.app, "post", "ben", f"{detail_url}/participation", json={})
    assert joined.status == 201, joined.text

    after = (await _call(env.app, "get", "ben", detail_url)).json
    assert after["caller_is_participant"] is True
    assert after["participant_count"] == 1
    assert [p["display_name"] for p in after["participants"]] == ["Ben"]

    listed = (await _call(env.app, "get", "ben", "/api/v1/domains")).json
    item = next(i for i in listed["items"] if i["id"] == str(STEWARDED_DOMAIN))
    assert item["caller_is_participant"] is True
    assert listed["caller_can_create"] is False

    # The steward is a steward, not (yet) a participant.
    steward_view = (await _call(env.app, "get", "sol", detail_url)).json
    assert steward_view["caller_is_steward"] is True
    assert steward_view["caller_can_edit"] is True
    assert steward_view["caller_is_participant"] is False


# ---------------------------------------------------------------------------
# MCP parity: the agent tools apply the same authorship rules
# ---------------------------------------------------------------------------


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
