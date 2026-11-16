"""The signed-in ethos page fans these reads out together on first paint.

Client: charting-the-course EthosDetail + EcosystemHome for an active member.
Each one must answer 200 on a cold call and again when they all run at once.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401
from neos_agent.api.agreements import agreements_api_bp
from neos_agent.api.decisions import decisions_api_bp
from neos_agent.api.domains import domains_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.matching import matching_api_bp
from neos_agent.api.members import members_api_bp
from neos_agent.api.next_steps import next_steps_api_bp
from neos_agent.api.orientation import orientation_api_bp
from neos_agent.api.proposals import proposals_api_bp
from neos_agent.db.course_models import Quiz
from neos_agent.db.models import (
    Agreement,
    Base,
    DecisionRecord,
    Domain,
    Ecosystem,
    EmergencyState,
    EthosUserAccess,
    GovernanceHealthAudit,
    JourneyMap,
    MatchingConsent,
    Member,
    Proposal,
    User,
)

ECO = uuid.UUID("25af625f-8ee4-5285-ac74-24acaee7b705")
USER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "ethos-home.ada.user")
MEMBER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "ethos-home.ada.member")
PEER_USER = uuid.uuid5(uuid.NAMESPACE_DNS, "ethos-home.ben.user")
PEER_MEMBER = uuid.uuid5(uuid.NAMESPACE_DNS, "ethos-home.ben.member")

# The same query string EcosystemHome sends for members, domains, proposals, decisions and agreements.
LIST = f"?ecosystem_id={ECO}&per_page=20"
READS = (
    f"/api/v1/ecosystems/{ECO}",
    f"/api/v1/orientation/ethos/{ECO}/journey-maps",
    "/api/v1/me/next-steps",
    f"/api/v1/members{LIST}",
    f"/api/v1/domains{LIST}",
    f"/api/v1/matching/ecosystems/{ECO}/consent",
    f"/api/v1/matching/ecosystems/{ECO}/participants?page=1",
    f"/api/v1/proposals{LIST}",
    f"/api/v1/decisions{LIST}",
    f"/api/v1/agreements{LIST}",
)


async def _seed(session: AsyncSession) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(Ecosystem(
        id=ECO, name="PGT", status="active", visibility="public", description="A public ethos",
        tags=["harbor"], governance_summary="Consent.", created_at=now - timedelta(days=400),
    ))
    session.add(User(
        id=USER_ID, display_name="Ada", skills=["maps"], interests=["harbors"],
    ))
    session.add(User(
        id=PEER_USER, display_name="Ben", skills=["maps", {"not": "a string"}], interests=["harbors"],
    ))
    await session.flush()
    session.add(Member(
        id=MEMBER_ID, ecosystem_id=ECO, user_id=USER_ID, member_id="MEM-ADA",
        display_name="Ada", current_status="active", role="owner", profile="co_creator",
        created_at=now - timedelta(days=3),
    ))
    session.add(Member(
        id=PEER_MEMBER, ecosystem_id=ECO, user_id=PEER_USER, member_id="MEM-BEN",
        display_name="Ben", current_status="active", role="user",
    ))
    await session.flush()
    for user_id, member_id in ((USER_ID, MEMBER_ID), (PEER_USER, PEER_MEMBER)):
        session.add(MatchingConsent(
            id=uuid.uuid4(), user_id=user_id, ecosystem_id=ECO,
            directory_visible=True, contact_discovery=True, matching_enabled=False,
        ))
        session.add(EthosUserAccess(
            id=uuid.uuid4(), member_id=member_id, ecosystem_id=ECO, role_in_ethos="member",
        ))
    session.add(Domain(
        id=uuid.uuid4(), ecosystem_id=ECO, domain_id="DOM-HOME", name="Harbor", version="1.0",
        status="active", purpose="Keep the channel open", steward_id=MEMBER_ID, current_steward="Ada",
    ))
    session.add(Proposal(
        id=uuid.uuid4(), ecosystem_id=ECO, proposal_id="PROP-HOME", type="operational", title="Dredge the channel",
        version="1.0", status="advice", proposer="Ada", proposer_member_id=MEMBER_ID,
    ))
    session.add(Agreement(
        id=uuid.uuid4(), ecosystem_id=ECO, agreement_id="AGR-HOME", type="uaf", title="Harbor ways",
        version="1.0", status="active", text="We decide by consent.", hierarchy_level="ecosystem",
        review_date=(now - timedelta(days=10)).date(),
    ))
    session.add(DecisionRecord(
        id=uuid.uuid4(), ecosystem_id=ECO, record_id="DEC-HOME", status="active", holding="The channel stays open",
    ))
    session.add(JourneyMap(
        id=uuid.uuid4(), ecosystem_id=ECO, slug="harbor", title="Welcome", is_active=True, is_default=True,
        content_sequence=[{"type": "content", "title": "Hello"}],
    ))
    session.add(EmergencyState(
        id=uuid.uuid4(), ecosystem_id=ECO, state="closed", declared_at=now - timedelta(days=40),
        closed_at=now - timedelta(days=20),
    ))
    session.add(GovernanceHealthAudit(
        id=uuid.uuid4(), ecosystem_id=ECO, audit_id="AUD-HOME", status="completed",
        audit_date=(now - timedelta(days=30)).date(), next_audit_due=(now + timedelta(days=60)).date(),
        indicator_scores=[{"indicator_id": "GHI-01", "indicator_name": "Authorship", "status": "critical"}],
        auditor_ids=[str(MEMBER_ID)],
    ))
    session.add(Quiz(
        id=uuid.uuid4(), ecosystem_id=ECO, title="Entry", is_entry_quiz=True, is_published=True,
        survey_json={"pages": [{"elements": [{"type": "text", "name": "why", "isRequired": True}]}]},
    ))
    await session.commit()


def _app() -> Sanic:
    app = Sanic(f"ethos-home-{uuid.uuid4().hex[:8]}")
    register_api_errors(app)

    @app.on_request
    async def inject(request):
        request.ctx.user = User(id=USER_ID, display_name="Ada", skills=["maps"], interests=["harbors"])
        request.ctx.member = Member(
            id=MEMBER_ID, ecosystem_id=ECO, user_id=USER_ID, member_id="MEM-ADA",
            display_name="Ada", current_status="active", role="owner",
        )
        request.ctx.selected_ecosystem_ids = [ECO]
        request.ctx.authorized_ecosystem_ids = [ECO]
        request.ctx.platform_admin = False
        request.ctx.node_admin = False

    for blueprint in (
        ecosystems_api_bp, orientation_api_bp, next_steps_api_bp, members_api_bp, domains_api_bp,
        matching_api_bp, proposals_api_bp, decisions_api_bp, agreements_api_bp,
    ):
        app.blueprint(blueprint)
    return app


@pytest_asyncio.fixture
async def app():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
    application = _app()
    application.ctx.db = factory
    application.ctx.settings = type("Settings", (), {"PLATFORM_HOME_ECOSYSTEM_ID": ""})()
    yield application
    await engine.dispose()


async def _get(app, path: str):
    _, response = await app.asgi_client.get(path, headers={"x-test-as": "ada"})
    return response


async def test_ethos_home_reads_answer_200(app):
    for path in READS:
        response = await _get(app, path)
        assert response.status == 200, f"{path} -> {response.status} {response.text}"


async def test_ethos_home_reads_survive_the_first_parallel_burst(app):
    responses = await asyncio.gather(*(_get(app, path) for path in READS))
    failed = [(READS[index], response.status, response.text) for index, response in enumerate(responses) if response.status != 200]
    assert failed == []
