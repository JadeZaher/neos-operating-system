"""UX-QA pass 01 (first week), lane 1: governance integrity flows.

Drives the real proposals/domains/agreements blueprints and the chat
assistant's tool dispatch over an in-memory SQLite DB, acting as different
members through an injected session. Rules under test live in
src/neos_agent/api/AGENTS.md: "Proposal authorship and manage rule", "Domain
naming and participation flags" and "Chat assistant tools (caller-scoped)". The
REST / MCP / chat parity table lives in test_uxqa_p1_mcp_parity.py so these
collect without the `mcp` package.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.agent.governance_tools import (
    CALLER_REQUIRED,
    CALLER_SCOPED_TOOLS,
    DECISION_DENIED,
    EXIT_SELF_ONLY,
    MEMBER_REQUIRED,
    execute_tool,
)
from neos_agent.api.agreements import CEREMONY_DENIED, agreements_api_bp
from neos_agent.api.conflicts import TRIAGE_DENIED
from neos_agent.api.domains import CREATE_DENIED, domain_display_name, domains_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.proposals import MANAGE_DENIED, SELF_ADVICE_DENIED, proposals_api_bp
from neos_agent.db.models import (
    Agreement,
    Base,
    ConflictCase,
    ConsentParticipant,
    DecisionRecord,
    Domain,
    DomainElement,
    Ecosystem,
    EmergencyState,
    ExitRecord,
    GovernanceHealthAudit,
    Member,
    Proposal,
    RepairAgreementRecord,
    User,
)

ECO = uuid.UUID("0000000a-0000-0000-0000-000000000001")
RIVER = uuid.UUID("0000000a-0000-0000-0000-000000000002")  # another ecosystem
RIVER_PROPOSAL = uuid.UUID("0000000a-0000-0000-0000-0000000000f2")
GARDEN_AGREEMENT = uuid.UUID("0000000a-0000-0000-0000-0000000000a1")
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
    "ari": _person("ari", "Ari", "admin"),  # conducts agreement ceremonies
}
OLU = _person("olu", "Olu", "user")  # a member of River only: an outsider to Oasis


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
    # A list-valued S3 element (element_value is any JSON, not only an object).
    session.add(DomainElement(
        id=uuid.uuid4(), domain_id=STEWARDED_DOMAIN, element_name="drivers",
        element_value=["Newcomers need a first task"],
    ))
    # Legacy row: free-text proposer that happens to match Ben, but no author link.
    session.add(Proposal(
        id=LEGACY_PROPOSAL, ecosystem_id=ECO, proposal_id="PROP-LEGACY", type="policy",
        title="Legacy proposal", version="1.0", status="advice", proposer="Ben",
    ))
    session.add(Agreement(
        id=GARDEN_AGREEMENT, ecosystem_id=ECO, agreement_id="AGR-GARDEN", type="space",
        title="Garden hours", version="1.0", status="draft", proposer="Ada", text="Open at dawn.",
    ))
    session.add(Ecosystem(id=RIVER, name="River House", status="active"))
    session.add(User(id=OLU.user_id, display_name=OLU.name))
    await session.flush()
    session.add(Member(
        id=OLU.member_id, ecosystem_id=RIVER, user_id=OLU.user_id, member_id="MEM-OLU",
        display_name=OLU.name, current_status="active", role=OLU.role,
    ))
    session.add(Proposal(
        id=RIVER_PROPOSAL, ecosystem_id=RIVER, proposal_id="PROP-RIVER", type="policy",
        title="River proposal", version="1.0", status="draft", proposer="Olu",
        proposer_member_id=OLU.member_id,
    ))
    await session.commit()


def _create_app() -> Sanic:
    """Blueprint app; the x-test-as header picks who is signed in."""
    app = Sanic(f"test-uxqa-p1-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        p, home = (OLU, RIVER) if who == "olu" else (PEOPLE[who], ECO)
        request.ctx.member = Member(
            id=p.member_id, ecosystem_id=home, user_id=p.user_id, member_id="MEM-AUTH",
            display_name=p.name, current_status="active", role=p.role,
        )
        request.ctx.user = User(id=p.user_id, display_name=p.name)
        request.ctx.selected_ecosystem_ids = [home]
        request.ctx.authorized_ecosystem_ids = [home]

    app.blueprint(proposals_api_bp)
    app.blueprint(domains_api_bp)
    app.blueprint(agreements_api_bp)
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


async def test_proposer_cannot_self_advise_and_others_complete_the_round(env):
    proposal = await _create_proposal(env.app)
    await _open_for_advice(env.app, proposal["id"])
    url = f"/api/v1/proposals/{proposal['id']}/advice"

    self_advice = await _call(env.app, "post", "ada", url, json={"content": "I agree with myself"})
    assert self_advice.status == 409
    assert self_advice.json["error"] == SELF_ADVICE_DENIED

    # The advisor is the caller, whatever the body claims; the default one-round
    # gate is then met, and advice stays open until the proposer closes it (owner decision).
    advice = await _call(env.app, "post", "ben", url, json={"advisor": "Spoofed", "content": "Add a winter schedule"})
    assert advice.status == 201, advice.text
    assert [e["advisor"] for e in advice.json["entries"]] == ["Ben"]
    assert (advice.json["auto_transitions"], advice.json["gates"]["advice"]["met"]) == ([], True)
    current = (await _call(env.app, "get", "ada", f"/api/v1/proposals/{proposal['id']}")).json
    assert current["status"] == "advice"


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
    assert steward_view["domain_elements"][0]["element_value"] == ["Newcomers need a first task"]


@pytest.mark.parametrize("actor, is_steward, can_create", [
    ("sol", True, False),  # this domain's steward, plain ecosystem role
    ("mo", False, True),  # ecosystem steward (mod)
    ("ben", False, False),
])
async def test_domain_list_flags_reflect_the_caller(env, actor, is_steward, can_create):
    listed = (await _call(env.app, "get", actor, "/api/v1/domains")).json
    item = next(i for i in listed["items"] if i["id"] == str(STEWARDED_DOMAIN))
    assert item["caller_is_steward"] is is_steward
    assert listed["caller_can_create"] is can_create


async def test_clearing_a_domain_name_falls_back_to_the_purpose_label(env):
    url = f"/api/v1/domains/{STEWARDED_DOMAIN}"
    named = await _call(env.app, "put", "mo", url, json={"name": "Garden Commons"})
    assert named.json["display_name"] == "Garden Commons"

    # An update that omits "name" keeps it.
    kept = await _call(env.app, "put", "mo", url, json={"purpose": "Newcomer Garden — beds for first-month members"})
    assert kept.status == 200, kept.text
    assert kept.json["name"] == "Garden Commons"

    # Present-and-empty clears it back to the derived label.
    cleared = await _call(env.app, "put", "mo", url, json={"name": "  "})
    assert cleared.status == 200, cleared.text
    assert cleared.json["name"] is None
    assert cleared.json["display_name"] == "Newcomer Garden"


# ---------------------------------------------------------------------------
# Chat assistant parity: the in-app tools act as the signed-in member
# ---------------------------------------------------------------------------


async def _tool(env, who: str | None, tool_name: str, /, **args) -> dict:
    """Run a chat tool the way api/chat.py does: scoped ids as strings, commit on success."""
    caller = (OLU if who == "olu" else PEOPLE[who]).user_id if who else None
    async with env.db() as session:
        result = await execute_tool(tool_name, args, session, ecosystem_ids=[str(ECO)], caller_user_id=caller)
        if result.get("success"):
            await session.commit()
    return result


# Arguments each state-changing tool would succeed with for an entitled member.
_TOOL_ARGS = {
    "create_agreement_draft": {"title": "Tool shed rota", "type": "space", "domain": "Garden", "text": "Lend tools."},
    "update_agreement_status": {"agreement_id": "AGR-GARDEN", "new_status": "advice", "evidence": "Opening the advice round"},
    "create_proposal": {"title": "T", "type": "policy", "proposed_change": "C", "rationale": "R"},
    "record_advice": {"proposal_id": "PROP-LEGACY", "advice_text": "Advice"},
    "record_consent_position": {"proposal_id": "PROP-LEGACY", "position": "consent"},
    "create_decision_record": {"holding": "Quiet hours start at ten.", "rationale": "Neighbours asked."},
    "create_conflict_case": {"title": "Noise at night", "description": "Music after midnight."},
    "triage_conflict": {"case_id": "set by the test", "tier": 1},
    # Irreversible acts carry the member's confirmation (no chat turns here, so the flag suffices).
    "declare_emergency": {"notes": "The river is flooding the garden.", "confirmed": True},
    "create_exit_record": {"departure_notice": "Moving to another valley.", "confirmed": True},
    "create_domain_draft": {"domain_id": "tools", "purpose": "Lend tools"},
    "create_ecosystem": {"name": "New Commons"},
    "create_safeguard_audit": {"findings": "Participation is healthy."},
    "create_repair_agreement": {
        "case_id": "set by the test", "title": "Quiet repair",
        "commitments": [{"commitment": "Lower the volume", "owner": "Ben"}],
    },
    "update_proposal_status": {"proposal_id": "PROP-LEGACY", "new_status": "withdrawn", "confirmed": True},
    "join_domain": {"domain": "Newcomer Garden"},
    "submit_test_report": {"proposal_id": "PROP-LEGACY", "outcome": "passed", "observations": "It worked."},
    "record_agreement_evidence": {"agreement_id": "AGR-GARDEN", "stage": "advice", "note": "Advice round held"},
    "withdraw_consent_position": {"proposal_id": "PROP-LEGACY"},
    "cosign_emergency": {"confirmed": True},
    "end_emergency_authority": {"confirmed": True},
    "record_emergency_review": {"outcome": "complete", "summary": "Held on Monday", "confirmed": True},
    # G-Onboard
    "join_ecosystem": {"ecosystem": "Garden", "confirmed": True},
    "attest_agreement_consent": {"agreement_id": "AGR-GARDEN", "attestation": "I consent to it", "confirmed": True},
    "move_member": {"member": "Ben", "status": "suspended", "confirmed": True},
    # G-Exchange
    "publish_share_need": {"domain": "Newcomer Garden", "type": "need", "title": "Spades"},
    "respond_to_share_need": {"post": "Spades", "message": "I have one", "confirmed": True},
    "update_share_need_status": {"post": "Spades", "status": "withdrawn"},
    "approve_collaboration": {"collaboration": "Garden crews"},
    "end_collaboration": {"collaboration": "Garden crews", "outcome": "dissolved", "reason": "No", "confirmed": True},
    # FX-Exchange
    "review_collaboration": {"collaboration": "Garden crews", "note": "Going well"},
    # FX-Maint
    "respond_to_health_audit": {"note": "We will rotate authorship.", "confirmed": True},
}


@pytest.mark.parametrize("name", sorted(CALLER_SCOPED_TOOLS))
async def test_chat_tools_refuse_to_act_without_a_signed_in_member(env, name):
    result = await _tool(env, None, name, **_TOOL_ARGS[name])
    assert result == {"success": False, "error": CALLER_REQUIRED}


async def test_chat_tools_apply_authorship_advice_and_manage_rules(env):
    created = await _tool(
        env, "ada", "create_proposal",
        title="Seed library", type="policy", proposed_change="Open a seed library", rationale="Share seeds",
        proposer="Spoofed Steward",
    )
    assert created["success"] is True, created
    proposal_key = created["data"]["proposal_id"]
    async with env.db() as session:
        stored = await session.scalar(select(Proposal).where(Proposal.proposal_id == proposal_key))
    assert (stored.status, stored.proposer_member_id) == ("draft", PEOPLE["ada"].member_id)
    assert stored.proposer == "Spoofed Steward"  # display text only; Ada stays the author

    # Another member cannot open, advance or withdraw it.
    denied = await _tool(env, "ben", "update_proposal_status", proposal_id=proposal_key, new_status="advice")
    assert denied == {"success": False, "error": MANAGE_DENIED}
    opened = await _tool(env, "ada", "update_proposal_status", proposal_id=proposal_key, new_status="advice")
    assert opened["data"]["new_status"] == "advice"
    gated = await _tool(env, "ada", "update_proposal_status", proposal_id=proposal_key, new_status="consent")
    assert gated["success"] is False and "advice gate is not satisfied" in gated["error"]

    # Advice integrity: no self-advice, no blank advice, advisor is the caller.
    self_advice = await _tool(env, "ada", "record_advice", proposal_id=proposal_key, advice_text="Agree with myself")
    assert self_advice == {"success": False, "error": SELF_ADVICE_DENIED}
    blank = await _tool(env, "ben", "record_advice", proposal_id=proposal_key, advice_text="   ")
    assert blank == {"success": False, "error": "Advice text is required."}
    advised = await _tool(
        env, "ben", "record_advice", proposal_id=proposal_key, advice_text="Add a swap shelf", advisor="Mo",
    )
    assert advised["data"]["advisor"] == "Ben"
    assert advised["data"]["auto_transitions"] == []  # the proposer closes advice (owner decision)

    withdrawn = await _tool(
        env, "mo", "update_proposal_status", proposal_id=proposal_key, new_status="withdrawn", confirmed=True,
    )
    assert withdrawn["data"]["new_status"] == "withdrawn"


@pytest.mark.parametrize("actor, expected", [("ben", False), ("mo", True)])
async def test_chat_domain_creation_requires_an_ecosystem_steward(env, actor, expected):
    result = await _tool(
        env, actor, "create_domain_draft", domain_id="tool-library", purpose="Lend tools", name="Tool Library",
    )
    assert result["success"] is expected, result
    if not expected:
        assert result["error"] == CREATE_DENIED
    async with env.db() as session:
        created = await session.scalar(select(Domain).where(Domain.domain_id == "tool-library"))
    assert (created is not None) is expected
    if expected:
        assert domain_display_name(created) == "Tool Library"


# ---------------------------------------------------------------------------
# Chat assistant authorization: every state-changing tool (ledger p1-coord-chat-tool-authz)
# ---------------------------------------------------------------------------


async def _open_case(env) -> str:
    created = await _tool(env, "ben", "create_conflict_case", **_TOOL_ARGS["create_conflict_case"])
    assert created["success"] is True, created
    return created["data"]["case_id"]


async def _governance_state(env) -> tuple:
    """Row counts of everything these tools write, plus the seeded agreement's status and version."""
    async with env.db() as session:
        counts = [
            await session.scalar(select(func.count()).select_from(model))
            for model in (Agreement, DecisionRecord, ConflictCase, EmergencyState, ExitRecord,
                          GovernanceHealthAudit, RepairAgreementRecord)
        ]
        garden = await session.get(Agreement, GARDEN_AGREEMENT)
        case_statuses = sorted((await session.execute(select(ConflictCase.status))).scalars().all())
        return (*counts, garden.status, garden.version, *case_statuses)


@pytest.mark.parametrize("name, denied, refusal, allowed", [
    ("create_agreement_draft", "olu", MEMBER_REQUIRED, "ben"),  # an active member here, as REST POST /agreements
    ("update_agreement_status", "ben", CEREMONY_DENIED, "ari"),  # active admin or owner, as REST ceremonies
    ("create_decision_record", "ben", DECISION_DENIED, "mo"),  # no REST route: stewards only
    ("create_conflict_case", "olu", MEMBER_REQUIRED, "ben"),
    ("triage_conflict", "ben", TRIAGE_DENIED, "mo"),  # G-Care: a steward there (ben reported it), never a party
    ("declare_emergency", "olu", MEMBER_REQUIRED, "ben"),  # owner decision: any active member
    ("create_exit_record", "olu", MEMBER_REQUIRED, "ben"),
    ("create_safeguard_audit", "olu", MEMBER_REQUIRED, "ben"),
    ("create_repair_agreement", "ben", TRIAGE_DENIED, "mo"),
])
async def test_chat_tools_apply_the_rule_for_the_callers_ecosystem(env, name, denied, refusal, allowed):
    args = dict(_TOOL_ARGS[name])
    if "case_id" in args:
        args["case_id"] = await _open_case(env)
    before = await _governance_state(env)

    assert await _tool(env, denied, name, **args) == {"success": False, "error": refusal}
    assert await _governance_state(env) == before

    granted = await _tool(env, allowed, name, **args)
    assert granted["success"] is True, granted
    assert await _governance_state(env) != before


@pytest.mark.parametrize("name, actor, spoofed, model, column, expected", [
    ("declare_emergency", "ben", {"declared_by": "Mo"}, EmergencyState, "declared_by", "Ben"),
    ("create_decision_record", "mo", {"recorder": "Ada"}, DecisionRecord, "recorder", "Mo"),
    ("create_safeguard_audit", "ben", {"auditor": "Ada"}, GovernanceHealthAudit, "auditor", "Ben"),
    ("create_conflict_case", "ben", {"reporter_id": str(PEOPLE["ada"].member_id)}, ConflictCase,
     "reporter_id", PEOPLE["ben"].member_id),
    ("create_agreement_draft", "ben", {}, Agreement, "proposer", "Ben"),  # proposer text defaults to the caller
])
async def test_chat_tools_record_the_caller_not_a_model_supplied_identity(env, name, actor, spoofed, model, column, expected):
    async with env.db() as session:
        existing = set((await session.execute(select(model.id))).scalars().all())
    result = await _tool(env, actor, name, **_TOOL_ARGS[name], **spoofed)
    assert result["success"] is True, result
    async with env.db() as session:
        [stored] = (await session.execute(select(model).where(model.id.not_in(existing)))).scalars().all()
    assert getattr(stored, column) == expected


async def test_chat_exit_is_only_the_callers_own(env):
    refused = await _tool(env, "ben", "create_exit_record", **_TOOL_ARGS["create_exit_record"], member_name="Ada")
    assert refused == {"success": False, "error": EXIT_SELF_ONLY}
    started = await _tool(env, "ben", "create_exit_record", **_TOOL_ARGS["create_exit_record"], member_name="ben")
    assert started["data"]["member"] == "Ben"
    async with env.db() as session:
        exits = (await session.execute(select(ExitRecord.member_id))).scalars().all()
    assert exits == [PEOPLE["ben"].member_id]


async def test_chat_ecosystem_founder_joins_and_stewards_its_core_domain(env):
    created = await _tool(env, "ben", "create_ecosystem", **_TOOL_ARGS["create_ecosystem"])
    assert created["success"] is True, created
    new_ecosystem = uuid.UUID(created["data"]["id"])
    async with env.db() as session:
        founder = await session.scalar(select(Member).where(Member.ecosystem_id == new_ecosystem))
        core = await session.scalar(select(Domain).where(Domain.ecosystem_id == new_ecosystem))
    assert (founder.user_id, founder.current_status) == (PEOPLE["ben"].user_id, "active")
    assert core.steward_id == founder.id


async def _proposal_in_consent(env) -> dict:
    """Ada's proposal after Ben's advice, with advice closed by Ada (the proposer closes advice)."""
    proposal = await _create_proposal(env.app)
    await _open_for_advice(env.app, proposal["id"])
    advice = await _call(env.app, "post", "ben", f"/api/v1/proposals/{proposal['id']}/advice", json={"content": "Add a rota"})
    assert advice.status == 201, advice.text
    closed = await _call(env.app, "post", "ada", f"/api/v1/proposals/{proposal['id']}/status", json={"status": "consent"})
    assert closed.json["status"] == "consent", closed.text
    return proposal


async def _positions(env) -> list[tuple[str, str]]:
    async with env.db() as session:
        rows = (await session.execute(
            select(ConsentParticipant.name, ConsentParticipant.position).order_by(ConsentParticipant.created_at)
        )).all()
    return [tuple(row) for row in rows]


async def test_chat_consent_is_the_callers_own_and_an_objection_blocks(env):
    proposal = await _proposal_in_consent(env)

    outsider = await _tool(env, "olu", "record_consent_position", proposal_id=proposal["id"], position="consent")
    assert outsider["success"] is False

    # Accepts the page's UUID, ignores the name argument, stores the engine's "object".
    objected = await _tool(
        env, "mo", "record_consent_position",
        proposal_id=proposal["id"], participant="Ada", position="objection", reason="Too noisy at night",
    )
    assert objected["success"] is True, objected
    assert (objected["data"]["participant"], objected["data"]["position"]) == ("Mo", "object")
    assert objected["data"]["gates"]["consent"]["open_objections"] == 1

    # With the objection open, another member's consent (quorum 1) does not advance it.
    consent = await _call(env.app, "post", "sol", f"/api/v1/proposals/{proposal['id']}/consent",
                          json={"member_name": "Sol", "position": "consent"})
    assert consent.status == 201, consent.text
    assert consent.json["auto_transitions"] == []
    current = (await _call(env.app, "get", "ada", f"/api/v1/proposals/{proposal['id']}")).json
    assert current["status"] == "consent"
    assert await _positions(env) == [("Mo", "object"), ("Sol", "consent")]


async def test_rest_consent_position_is_always_the_callers(env):
    proposal = await _proposal_in_consent(env)
    resp = await _call(env.app, "post", "ben", f"/api/v1/proposals/{proposal['id']}/consent",
                       json={"member_name": "Ada", "position": "consent"})
    assert resp.status == 201, resp.text
    assert [p["member_name"] for p in resp.json["participants"]] == ["Ben"]
    assert resp.json["auto_transitions"] == ["consent->test"]


async def test_chat_reads_a_proposal_in_consent_by_its_page_id(env):
    proposal = await _proposal_in_consent(env)
    await _tool(env, "mo", "record_consent_position", proposal_id=proposal["proposal_id"], position="consent")
    read = await _tool(env, "ben", "get_proposal", proposal_id=proposal["id"])
    assert read["success"] is True, read
    assert read["data"]["status"] == "test"
    assert [e["advisor"] for e in read["data"]["advice_logs"][0]["entries"]] == ["Ben"]
    assert read["data"]["consent_records"][0]["round"] == 1


# ---------------------------------------------------------------------------
# REST contracts on the proposals blueprint
# ---------------------------------------------------------------------------


async def test_proposal_list_pages_by_25_and_rejects_a_non_numeric_page(env):
    for index in range(26):
        await _create_proposal(env.app, title=f"Proposal {index}")
    first = (await _call(env.app, "get", "ben", "/api/v1/proposals")).json
    assert (first["per_page"], len(first["items"]), first["total"]) == (25, 25, 27)  # 26 + the legacy row
    bad = await _call(env.app, "get", "ben", "/api/v1/proposals?page=abc")
    assert bad.status == 400
    assert bad.json == {"error": "Query parameter 'page' must be a whole number"}


@pytest.mark.parametrize("who, proposal, method, path, body", [
    ("olu", LEGACY_PROPOSAL, "get", "", None),
    ("olu", LEGACY_PROPOSAL, "post", "/status", {"status": "withdrawn"}),
    ("ada", RIVER_PROPOSAL, "get", "", None),
    ("ada", RIVER_PROPOSAL, "post", "/advice", {"content": "Advice from outside"}),
])
async def test_another_ecosystems_proposal_is_not_found(env, who, proposal, method, path, body):
    kwargs = {"json": body} if body is not None else {}
    resp = await _call(env.app, method, who, f"/api/v1/proposals/{proposal}{path}", **kwargs)
    assert resp.status == 404
    assert resp.json == {"error": "Proposal not found"}
