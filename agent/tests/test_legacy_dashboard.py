"""The legacy server-rendered /dashboard shares the session cookie, so it must not bypass the app's rules.

Every legacy write route answers 410 and changes nothing; conflict cases read through it follow
`policy.can_view_conflict`; the legacy chat never trusts the model's `confirmed: true`. Rules:
src/neos_agent/api/AGENTS.md "Legacy dashboard (views/)".
"""

from __future__ import annotations

import copy
import json
import re
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes for create_all
from neos_agent.db.models import (
    Agreement, Base, ConflictCase, Domain, Ecosystem, EmergencyState, ExitRecord, GovernanceHealthAudit, Member,
    MemberOnboarding, Proposal, User,
)
from neos_agent.views import register_views
from neos_agent.views.chat import chat_bp
from neos_agent.views.ecosystems import ecosystems_bp

ECO = uuid.UUID(int=0xEC0)
PROPOSAL = uuid.UUID(int=0x9A)
AGREEMENT = uuid.UUID(int=0xA6)
DOMAIN = uuid.UUID(int=0xD0)
CASE = uuid.UUID(int=0xCA)
EXIT = uuid.UUID(int=0xE1)
ONBOARDING = uuid.UUID(int=0x0B)
EMERGENCY = uuid.UUID(int=0xE3)
FRONTEND = "https://app.example"

# name -> (role, status); ada is a steward, ben reported the case, cy is a named party, dee is uninvolved.
PEOPLE = {"ada": ("admin", "active"), "ben": ("user", "active"), "cy": ("user", "active"), "dee": ("user", "active")}


def _user(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"legacy.{name}")


def _row(name: str) -> uuid.UUID:
    return uuid.uuid5(_user(name), str(ECO))


async def _seed(factory) -> None:
    async with factory() as session:
        session.add(Ecosystem(id=ECO, name="Oasis", status="active"))
        session.add_all([User(id=_user(name), display_name=name.title()) for name in [*PEOPLE, "eve"]])  # eve: no memberships
        await session.flush()
        session.add_all([
            Member(id=_row(name), ecosystem_id=ECO, user_id=_user(name), member_id=f"MEM-{name}",
                   display_name=name.title(), current_status=status, role=role)
            for name, (role, status) in PEOPLE.items()
        ])
        await session.flush()
        session.add_all([
            Proposal(id=PROPOSAL, ecosystem_id=ECO, proposal_id="PROP-1", type="policy", title="Share the tools",
                     status="consent", proposer="Ben", proposer_member_id=_row("ben")),
            Agreement(id=AGREEMENT, ecosystem_id=ECO, agreement_id="AGR-1", type="policy", title="Garden rota",
                      status="draft"),
            Domain(id=DOMAIN, ecosystem_id=ECO, domain_id="DOM-1", version="1.0", status="active", purpose="Kitchen"),
            ConflictCase(id=CASE, ecosystem_id=ECO, case_id="CONF-PRIVATE", title="Harm report about the shed",
                         status="reported", reporter_id=_row("ben"),
                         parties={"member_ids": [str(_row("cy"))], "labels": ["Cy"]}),
            ExitRecord(id=EXIT, ecosystem_id=ECO, member_id=_row("ben"), exit_type="standard", status="declared"),
            MemberOnboarding(id=ONBOARDING, member_id=_row("dee"), facilitator="Ada"),
            GovernanceHealthAudit(id=uuid.uuid4(), ecosystem_id=ECO, audit_id="AUD-1", status="draft"),
            EmergencyState(id=EMERGENCY, ecosystem_id=ECO, state="open", declared_by="Ben",
                           declared_at=datetime(2026, 10, 30), actions_log=[]),
        ])
        await session.commit()


def _app(factory) -> Sanic:
    app = Sanic(f"test-legacy-{uuid.uuid4().hex[:8]}")
    settings = MagicMock()
    settings.ANTHROPIC_API_KEY = "test-key"
    settings.ANTHROPIC_BASE_URL = ""
    settings.CLAUDE_MODEL = "claude-test"
    settings.FRONTEND_URL = FRONTEND + "/"
    app.ctx.settings = settings
    app.ctx.db = factory
    app.ctx.skills = None

    @app.on_request
    async def inject_session(request):
        who = request.headers.get("x-test-as")
        if not who:
            return
        async with factory() as session:
            rows = (await session.execute(select(Member).where(Member.user_id == _user(who)))).scalars().all()
        request.ctx.user = User(id=_user(who), display_name=who.title())
        request.ctx.member = rows[0] if rows else None
        request.ctx.authorized_ecosystem_ids = [ECO] if rows else []
        request.ctx.selected_ecosystem_ids = [ECO] if rows else []
        request.ctx.ecosystems = [Ecosystem(id=ECO, name="Oasis", status="active")] if rows else []

    register_views(app)
    app.blueprint(ecosystems_bp)
    app.blueprint(chat_bp)
    return app


@pytest_asyncio.fixture
async def env():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await _seed(factory)
    yield SimpleNamespace(app=_app(factory), db=factory)
    await engine.dispose()


async def _snapshot(factory) -> dict:
    """Every row of every table, so 'changed nothing' means exactly that."""
    async with factory() as session:
        return {
            table.name: sorted(repr(tuple(row)) for row in (await session.execute(select(table))).all())
            for table in Base.metadata.sorted_tables
        }


# --- Writes: each retired route answers 410, links the app, and changes nothing --------------

PARAMS = {
    "proposal_id": PROPOSAL, "agreement_id": AGREEMENT, "conflict_uuid": CASE, "exit_uuid": EXIT,
    "member_id": _row("ada"), "onboarding_id": ONBOARDING, "domain_id": DOMAIN, "ecosystem_id": ECO,
    "emergency_id": EMERGENCY,
}
ECO_FIELD = {"ecosystem_id": str(ECO)}

# (method, route pattern, form a steward could have sent; each changed state before it was retired)
RETIRED = [
    ("POST", "/dashboard/proposals", {**ECO_FIELD, "title": "Shadow proposal", "type": "policy"}),
    ("POST", "/dashboard/proposals/<proposal_id:uuid>/advice", {"advisor": "Somebody", "advice_text": "Go"}),
    ("POST", "/dashboard/proposals/<proposal_id:uuid>/consent", {"name": "Somebody", "position": "consent"}),
    ("POST", "/dashboard/proposals/<proposal_id:uuid>/phase", {"new_phase": "ratified"}),
    ("POST", "/dashboard/agreements", {**ECO_FIELD, "title": "Shadow", "type": "policy", "agreement_id": "AGR-X"}),
    ("POST", "/dashboard/agreements/<agreement_id:uuid>", {"title": "Rewritten"}),
    ("POST", "/dashboard/agreements/<agreement_id:uuid>/status", {"new_status": "active"}),
    ("POST", "/dashboard/conflicts", {**ECO_FIELD, "triage_notes": "Opened outside triage"}),
    ("POST", "/dashboard/conflicts/<conflict_uuid:uuid>/status", {"new_status": "resolved", "resolution_summary": "x"}),
    ("POST", "/dashboard/exit", {**ECO_FIELD, "member_id": str(_row("dee")), "exit_type": "urgent"}),
    ("POST", "/dashboard/exit/<exit_uuid:uuid>/status", {"new_status": "completed"}),
    ("POST", "/dashboard/members", {**ECO_FIELD, "display_name": "Ghost", "member_id": "MEM-ghost"}),
    ("PUT", "/dashboard/members/<member_id:uuid>", {"kyc_status": "verified", "display_name": "Ada Prime"}),
    ("POST", "/dashboard/members/<member_id:uuid>", {"kyc_status": "verified", "display_name": "Ada Prime"}),
    ("POST", "/dashboard/members/<member_id:uuid>/status", {"new_status": "exited"}),
    ("POST", "/dashboard/members/<member_id:uuid>/onboarding/consent", {"section_key": "exit_rights"}),
    ("POST", "/dashboard/members/<member_id:uuid>/onboarding/finalize", {}),
    ("POST", "/dashboard/onboarding/start", {"member_id": str(_row("ben")), "facilitator": "Ada"}),
    ("POST", "/dashboard/onboarding/ceremony/<onboarding_id:uuid>/consent", {"section_key": "exit_rights"}),
    ("POST", "/dashboard/onboarding/ceremony/<onboarding_id:uuid>/finalize", {}),
    ("POST", "/dashboard/domains", {**ECO_FIELD, "domain_id": "DOM-X", "purpose": "Shadow"}),
    ("PUT", "/dashboard/domains/<domain_id:uuid>", {"purpose": "Rewritten"}),
    ("POST", "/dashboard/domains/<domain_id:uuid>", {"purpose": "Rewritten"}),
    ("POST", "/ecosystems", {"name": "Shadow ecosystem"}),
    ("PUT", "/ecosystems/<ecosystem_id:uuid>", {"name": "Renamed"}),
    ("POST", "/ecosystems/<ecosystem_id:uuid>", {"name": "Renamed"}),
    ("POST", "/dashboard/safeguards/audits", {**ECO_FIELD, "auditor": "Ada"}),
    ("POST", "/dashboard/emergency/declare", {**ECO_FIELD, "notes": "Flood"}),
    ("POST", "/dashboard/emergency/<emergency_id:uuid>/resolve", {}),
]
LEGACY_BLUEPRINTS = {
    "agreements", "conflicts", "dashboard", "decisions", "domains", "ecosystems", "emergency", "exit", "members",
    "onboarding", "proposals", "safeguards",
}


def _concrete(pattern: str) -> str:
    return re.sub(r"<(\w+):uuid>", lambda match: str(PARAMS[match.group(1)]), pattern)


@pytest.mark.parametrize("method, pattern, form", RETIRED, ids=[f"{m} {p}" for m, p, _ in RETIRED])
async def test_every_legacy_write_route_is_gone_and_changes_nothing(env, method, pattern, form):
    before = await _snapshot(env.db)
    path = _concrete(pattern)
    _, response = await getattr(env.app.asgi_client, method.lower())(
        path, headers={"x-test-as": "ada"}, data=form, follow_redirects=False,
    )
    assert response.status == 410, response.text
    assert "Nothing was changed" in response.text
    app_link = re.search(r'href="([^"]+)"', response.text).group(1)
    assert app_link.startswith(FRONTEND + "/") and "dashboard" not in app_link
    assert await _snapshot(env.db) == before


async def test_the_retired_table_covers_every_legacy_write_route(env):
    await env.app.asgi_client.get("/dashboard", headers={"x-test-as": "ada"})  # finalizes the router
    registered = {
        (method, "/" + route.path.strip("/"))
        for route in env.app.router.routes
        if route.name.split(".")[1] in LEGACY_BLUEPRINTS
        for method in route.methods & {"POST", "PUT", "PATCH", "DELETE"}
    }
    assert registered == {(method, pattern) for method, pattern, _ in RETIRED}


# --- Reads: a conflict case shows only to the people the app shows it to ---------------------


@pytest.mark.parametrize("who, can_read", [
    ("ada", True),   # a steward of the ecosystem triages it
    ("ben", True),   # the reporter
    ("cy", True),    # a named party
    ("dee", False),  # an active member with no part in it
])
async def test_a_conflict_case_reads_through_the_legacy_dashboard_only_for_its_readers(env, who, can_read):
    headers = {"x-test-as": who}
    _, detail = await env.app.asgi_client.get(f"/dashboard/conflicts/{CASE}", headers=headers)
    _, listing = await env.app.asgi_client.get("/dashboard/conflicts", headers=headers)
    _, fragment = await env.app.asgi_client.get("/dashboard/conflicts/filter", headers=headers)
    assert detail.status == (200 if can_read else 404)
    for page in (detail, listing, fragment):
        assert ("CONF-PRIVATE" in page.text) is can_read


# --- Chat: irreversible acts cannot be confirmed here -----------------------------------------


class _FakeStream:
    """One scripted Claude turn: no streamed deltas, then the final message."""

    def __init__(self, final):
        self.final = final

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration

    async def get_final_message(self):
        return self.final


async def test_the_legacy_chat_never_trusts_the_models_confirmation(env):
    async with env.db() as session:  # Recovery closed: nothing blocks a new declaration but the confirmation
        (await session.get(EmergencyState, EMERGENCY)).state = "closed"
        await session.commit()
    declare = SimpleNamespace(type="tool_use", id="call-1", name="declare_emergency", input={
        "reason": "The river is flooding the garden.", "confirmed": True,
    })
    turns = [
        SimpleNamespace(stop_reason="tool_use", content=[declare]),
        SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Use the app.")]),
    ]
    sent: list[list] = []

    def stream(**kwargs):
        sent.append(copy.deepcopy(kwargs["messages"]))
        return _FakeStream(turns[len(sent) - 1])

    anthropic = MagicMock()
    anthropic.AsyncAnthropic.return_value.messages.stream.side_effect = stream
    with patch.dict("sys.modules", {"anthropic": anthropic}):
        _, response = await env.app.asgi_client.post(
            "/chat/message", headers={"x-test-as": "ben"}, json={"message": "Yes, declare it now."},
        )
    assert response.status == 200
    async with env.db() as session:
        states = (await session.execute(select(EmergencyState.state))).scalars().all()
    assert states == ["closed"]  # no declaration was recorded
    [tool_result] = sent[1][-1]["content"]
    result = json.loads(tool_result["content"])
    assert result["success"] is False and result["needs_confirmation"]
    assert "assistant in the NEOS app" in result["error"]


async def test_a_signed_in_user_without_memberships_reads_nothing_through_the_legacy_chat(env):
    reads = [
        SimpleNamespace(type="tool_use", id="call-1", name="get_proposal", input={"proposal": str(PROPOSAL)}),
        SimpleNamespace(type="tool_use", id="call-2", name="get_emergency_state", input={}),
    ]
    turns = [
        SimpleNamespace(stop_reason="tool_use", content=reads),
        SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Nothing found.")]),
    ]
    sent: list[list] = []

    def stream(**kwargs):
        sent.append(copy.deepcopy(kwargs["messages"]))
        return _FakeStream(turns[len(sent) - 1])

    anthropic = MagicMock()
    anthropic.AsyncAnthropic.return_value.messages.stream.side_effect = stream
    with patch.dict("sys.modules", {"anthropic": anthropic}):
        _, response = await env.app.asgi_client.post(
            "/chat/message", headers={"x-test-as": "eve"}, json={"message": "What is going on in Oasis?"},
        )
    assert response.status == 200
    blocks = sent[1][-1]["content"]
    assert len(blocks) == 2
    for block in blocks:
        assert "Share the tools" not in block["content"] and "flood" not in block["content"].lower()
        assert json.loads(block["content"])["success"] is False
