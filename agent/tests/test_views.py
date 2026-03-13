"""Tests for the NEOS dashboard view blueprints.

Uses Sanic ASGI test client with an in-memory SQLite database.
Validates routing, DB queries, status codes, and rendered HTML
against real Jinja2 templates with Tailwind CSS.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import (
    Agreement,
    Base,
    DecisionRecord,
    Domain,
    Ecosystem,
    Member,
    Proposal,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ECOSYSTEM_ID = uuid.uuid4()
AGREEMENT_ID = uuid.uuid4()
DOMAIN_ID = uuid.uuid4()
MEMBER_ID = uuid.uuid4()
PROPOSAL_ID = uuid.uuid4()
DECISION_ID = uuid.uuid4()


async def _seed_data(session: AsyncSession) -> None:
    """Insert minimal governance test data."""
    ecosystem = Ecosystem(
        id=ECOSYSTEM_ID,
        name="OmniOne Test",
        description="Test ecosystem",
        status="active",
    )
    session.add(ecosystem)
    await session.flush()

    agreement = Agreement(
        id=AGREEMENT_ID,
        ecosystem_id=ECOSYSTEM_ID,
        agreement_id="AGR-TEST-001",
        type="operational",
        title="Kitchen Scheduling Agreement",
        version="1.0",
        status="draft",
        proposer="Kai",
        domain="SHUR Kitchen",
        hierarchy_level="domain",
        created_date=date.today(),
    )
    session.add(agreement)

    domain = Domain(
        id=DOMAIN_ID,
        ecosystem_id=ECOSYSTEM_ID,
        domain_id="DOM-SHUR-KITCHEN",
        version="1.0",
        status="active",
        purpose="Community kitchen operations",
        current_steward="Lani",
        created_by="OSC",
    )
    session.add(domain)

    member = Member(
        id=MEMBER_ID,
        ecosystem_id=ECOSYSTEM_ID,
        member_id="MEM-KAI-001",
        display_name="Kai",
        current_status="active",
        profile="co_creator",
    )
    session.add(member)

    proposal = Proposal(
        id=PROPOSAL_ID,
        ecosystem_id=ECOSYSTEM_ID,
        proposal_id="PROP-TEST-001",
        type="operational",
        title="New composting rotation schedule",
        version="1.0",
        status="advice",
        proposer="Kai",
        affected_domain="SHUR Kitchen",
        urgency="standard",
        proposed_change="Rotate composting duties weekly",
        rationale="Fairer distribution of work",
        created_date=date.today(),
    )
    session.add(proposal)

    decision = DecisionRecord(
        id=DECISION_ID,
        ecosystem_id=ECOSYSTEM_ID,
        record_id="DEC-SHUR-KITCHEN-2026-001",
        date=date.today(),
        holding="Kitchen schedule approved as proposed",
        ratio_decidendi="Unanimous consent after advice integration",
        source_skill="act-process",
        source_layer=3,
        artifact_type="agreement",
        domain="SHUR Kitchen",
        precedent_level="domain",
        status="active",
    )
    session.add(decision)

    await session.commit()


def _create_dashboard_app() -> Sanic:
    """Create a Sanic app with dashboard blueprints and in-memory SQLite."""
    from unittest.mock import MagicMock

    app = Sanic(f"test-dashboard-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()
    return app


@pytest.fixture
def app():
    """Create a test app with all dashboard views registered."""
    test_app = _create_dashboard_app()

    from neos_agent.views import register_views
    register_views(test_app)

    return test_app


async def _setup_db(app):
    """Create in-memory SQLite, seed data, and attach to app."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.ctx.db = session_factory

    async with session_factory() as session:
        await _seed_data(session)

    return engine


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_home_returns_200(app):
    """GET /dashboard returns 200 with rendered Tailwind HTML."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "tailwindcss" in response.text
    assert "neos-primary" in response.text

    await engine.dispose()


@pytest.mark.asyncio
async def test_agreements_list_returns_200(app):
    """GET /dashboard/agreements returns 200 with agreements table."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard/agreements")
    assert response.status_code == 200
    assert "Agreements" in response.text
    assert "tailwindcss" in response.text

    await engine.dispose()


@pytest.mark.asyncio
async def test_agreements_filter_by_type(app):
    """GET /dashboard/agreements?type=operational returns 200."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard/agreements?type=operational")
    assert response.status_code == 200
    assert "Agreements" in response.text

    await engine.dispose()


@pytest.mark.asyncio
async def test_agreements_create_form_200(app):
    """GET /dashboard/agreements/new returns 200 with create form."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard/agreements/new")
    assert response.status_code == 200
    assert "Agreement" in response.text
    assert "form" in response.text.lower()

    await engine.dispose()


@pytest.mark.asyncio
async def test_domains_list_returns_200(app):
    """GET /dashboard/domains returns 200 with domain list."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard/domains")
    assert response.status_code == 200
    assert "Domains" in response.text
    assert "DOM-SHUR-KITCHEN" in response.text

    await engine.dispose()


@pytest.mark.asyncio
async def test_members_directory_200(app):
    """GET /dashboard/members returns 200 with member directory."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard/members")
    assert response.status_code == 200
    assert "Members" in response.text
    assert "Kai" in response.text

    await engine.dispose()


@pytest.mark.asyncio
async def test_proposals_list_200(app):
    """GET /dashboard/proposals returns 200 with proposal list."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard/proposals")
    assert response.status_code == 200
    assert "Proposals" in response.text
    assert "composting" in response.text.lower()

    await engine.dispose()


@pytest.mark.asyncio
async def test_decisions_browse_200(app):
    """GET /dashboard/decisions returns 200 with decisions list."""
    engine = await _setup_db(app)

    _, response = await app.asgi_client.get("/dashboard/decisions")
    assert response.status_code == 200
    assert "Decision Records" in response.text
    assert "DEC-SHUR-KITCHEN-2026-001" in response.text

    await engine.dispose()
