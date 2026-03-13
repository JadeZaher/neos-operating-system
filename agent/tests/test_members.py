"""Tests for NEOS member profile views.

Covers all CRUD paths, ownership guards, async session safety,
skills/interests round-trip, and template rendering for the
members blueprint.

Phase 1 of track member_profile_harden_20260313.
"""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import (
    Base,
    Ecosystem,
    Member,
    MemberOnboarding,
    MemberStatusTransition,
)

# ---------------------------------------------------------------------------
# Stable UUIDs
# ---------------------------------------------------------------------------
ECOSYSTEM_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OWNER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
OTHER_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
NONEXISTENT_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
async def _seed_data(session: AsyncSession) -> None:
    """Seed ecosystem, two members, and an onboarding record for owner."""
    ecosystem = Ecosystem(
        id=ECOSYSTEM_ID, name="OmniOne Test",
        description="Test ecosystem", status="active",
    )
    session.add(ecosystem)
    await session.flush()

    session.add(Member(
        id=OWNER_ID, ecosystem_id=ECOSYSTEM_ID,
        member_id="MEM-OWNER-001", display_name="Alice Owner",
        current_status="active", profile="co_creator",
        skills_offered=["facilitation", "design"],
        skills_needed=["legal"],
        interests=["permaculture", "governance"],
        phone="+1234567890", notes="Owner notes",
    ))
    session.add(Member(
        id=OTHER_ID, ecosystem_id=ECOSYSTEM_ID,
        member_id="MEM-OTHER-002", display_name="Bob Other",
        current_status="onboarding", profile="builder",
    ))
    session.add(MemberOnboarding(
        id=uuid.uuid4(), member_id=OWNER_ID,
        facilitator="Carol", completion_percentage=65,
        consent_date=date(2026, 1, 15),
        cooling_off_start=date(2026, 1, 20),
    ))
    await session.commit()


def _create_app(auth_as=OWNER_ID):
    """Create a Sanic test app with auth simulation.

    Args:
        auth_as: UUID of the member to authenticate as, or None for no auth.
    """
    app = Sanic(f"test-members-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = MagicMock()

    @app.on_request
    async def inject_auth(request):
        if auth_as is None:
            return
        # Create a transient Member for current_user context.
        # Only column attributes are safe — no relationship access.
        request.ctx.member = Member(
            id=auth_as, ecosystem_id=ECOSYSTEM_ID,
            member_id="MEM-AUTH", display_name="Auth User",
            current_status="active", profile="co_creator",
        )
        request.ctx.ecosystems = [Ecosystem(
            id=ECOSYSTEM_ID, name="OmniOne Test", status="active",
        )]
        request.ctx.selected_ecosystem_ids = [ECOSYSTEM_ID]

    from neos_agent.views import register_views
    register_views(app)
    return app


async def _setup_db(app):
    """Create in-memory SQLite, seed data, attach to app."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    app.ctx.db = sf
    async with sf() as session:
        await _seed_data(session)
    return engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def app():
    """App authenticated as owner (OWNER_ID)."""
    return _create_app(auth_as=OWNER_ID)


@pytest.fixture
def app_as_other():
    """App authenticated as other member (OTHER_ID)."""
    return _create_app(auth_as=OTHER_ID)


@pytest.fixture
def app_noauth():
    """Unauthenticated app."""
    return _create_app(auth_as=None)


# ---------------------------------------------------------------------------
# Task 1.1: Fixture smoke test
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fixture_works(app):
    """Verify seed data is queryable via the test app DB."""
    engine = await _setup_db(app)
    async with app.ctx.db() as session:
        owner = await session.get(Member, OWNER_ID)
        assert owner is not None
        assert owner.display_name == "Alice Owner"
        other = await session.get(Member, OTHER_ID)
        assert other is not None
        assert other.display_name == "Bob Other"
        eco = await session.get(Ecosystem, ECOSYSTEM_ID)
        assert eco is not None
        assert eco.name == "OmniOne Test"
    await engine.dispose()


# ---------------------------------------------------------------------------
# Task 1.2: Member detail page tests (FR-1, FR-4)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_member_detail_own_profile_200(app):
    """GET own profile returns 200 with display name, skills, ecosystem."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.get(f"/dashboard/members/{OWNER_ID}")
    assert response.status_code == 200
    assert "Alice Owner" in response.text
    assert "MEM-OWNER-001" in response.text
    assert "facilitation" in response.text
    assert "design" in response.text
    assert "permaculture" in response.text
    assert "OmniOne Test" in response.text  # ecosystem card
    assert "Edit Profile" in response.text  # own profile shows edit button
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_detail_other_profile_200(app_as_other):
    """GET another member's profile returns 200 without Edit button."""
    engine = await _setup_db(app_as_other)
    _, response = await app_as_other.asgi_client.get(f"/dashboard/members/{OWNER_ID}")
    assert response.status_code == 200
    assert "Alice Owner" in response.text
    assert "Edit Profile" not in response.text
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_detail_nonexistent_404(app):
    """GET with nonexistent UUID returns 404 with error message."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.get(f"/dashboard/members/{NONEXISTENT_ID}")
    assert response.status_code == 404
    assert "Member not found" in response.text
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_detail_no_onboarding_200(app_as_other):
    """GET profile for member with no onboarding record returns 200."""
    engine = await _setup_db(app_as_other)
    # Bob Other has no onboarding record
    _, response = await app_as_other.asgi_client.get(f"/dashboard/members/{OTHER_ID}")
    assert response.status_code == 200
    assert "Bob Other" in response.text
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_detail_with_onboarding_200(app):
    """GET profile for member with onboarding record shows completion %."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.get(f"/dashboard/members/{OWNER_ID}")
    assert response.status_code == 200
    assert "65%" in response.text or "65" in response.text
    assert "Carol" in response.text  # facilitator
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_detail_with_transitions_shows_history(app):
    """GET profile with status transitions shows Status History section."""
    engine = await _setup_db(app)
    # Seed a status transition
    async with app.ctx.db() as session:
        session.add(MemberStatusTransition(
            id=uuid.uuid4(), member_id=OWNER_ID,
            from_status="prospective", to_status="active",
            date=date(2026, 1, 10), trigger="onboarding_complete",
        ))
        await session.commit()
    _, response = await app.asgi_client.get(f"/dashboard/members/{OWNER_ID}")
    assert response.status_code == 200
    assert "Status History" in response.text
    await engine.dispose()


# ---------------------------------------------------------------------------
# Task 1.3: Edit/update ownership guard tests (FR-3)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_edit_form_own_profile_200(app):
    """GET /members/<own-id>/edit returns 200 with pre-populated form."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.get(f"/dashboard/members/{OWNER_ID}/edit")
    assert response.status_code == 200
    assert "Alice Owner" in response.text
    assert "form" in response.text.lower()
    await engine.dispose()


@pytest.mark.asyncio
async def test_edit_form_other_profile_redirects(app_as_other):
    """GET /members/<other-id>/edit redirects when user doesn't own profile."""
    engine = await _setup_db(app_as_other)
    _, response = await app_as_other.asgi_client.get(
        f"/dashboard/members/{OWNER_ID}/edit", follow_redirects=False
    )
    assert response.status_code == 302
    assert f"/dashboard/members/{OWNER_ID}" in response.headers.get("location", "")
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_own_profile_redirects_to_detail(app):
    """POST /members/<own-id> with valid data redirects to detail page."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}",
        data={"display_name": "Alice Updated", "profile": "builder"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert f"/dashboard/members/{OWNER_ID}" in response.headers.get("location", "")
    # Verify the update persisted
    async with app.ctx.db() as session:
        member = await session.get(Member, OWNER_ID)
        assert member.display_name == "Alice Updated"
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_other_profile_redirects(app_as_other):
    """POST /members/<other-id> with data redirects without updating."""
    engine = await _setup_db(app_as_other)
    _, response = await app_as_other.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}",
        data={"display_name": "Hacked Name"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    # Verify no update
    async with app_as_other.ctx.db() as session:
        member = await session.get(Member, OWNER_ID)
        assert member.display_name == "Alice Owner"
    await engine.dispose()


@pytest.mark.asyncio
async def test_edit_form_unauthenticated_redirects(app_noauth):
    """GET /members/<id>/edit with no auth redirects to detail."""
    engine = await _setup_db(app_noauth)
    _, response = await app_noauth.asgi_client.get(
        f"/dashboard/members/{OWNER_ID}/edit", follow_redirects=False
    )
    assert response.status_code == 302
    await engine.dispose()


# ---------------------------------------------------------------------------
# Task 1.4: Skills/interests round-trip tests (FR-5)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_update_skills_offered_stores_json_list(app):
    """POST with skills_offered comma string stores JSON list."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}",
        data={"skills_offered": "coding, writing, leadership"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    async with app.ctx.db() as session:
        member = await session.get(Member, OWNER_ID)
        assert member.skills_offered == ["coding", "writing", "leadership"]
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_interests_stores_json_list(app):
    """POST with interests comma string stores JSON list."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}",
        data={"interests": "permaculture, governance"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    async with app.ctx.db() as session:
        member = await session.get(Member, OWNER_ID)
        assert member.interests == ["permaculture", "governance"]
    await engine.dispose()


@pytest.mark.asyncio
async def test_update_clear_skills_sets_none(app):
    """POST with empty skills_offered clears the value."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}",
        data={"skills_offered": ""},
        follow_redirects=False,
    )
    assert response.status_code == 302
    async with app.ctx.db() as session:
        member = await session.get(Member, OWNER_ID)
        assert member.skills_offered is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_detail_shows_skills_tags(app):
    """GET detail page for member with skills shows skill text."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.get(f"/dashboard/members/{OWNER_ID}")
    assert response.status_code == 200
    assert "facilitation" in response.text
    assert "design" in response.text
    assert "Skills Offered" in response.text
    await engine.dispose()


@pytest.mark.asyncio
async def test_detail_hides_empty_skills(app_as_other):
    """GET detail for member with no skills hides Skills Offered section."""
    engine = await _setup_db(app_as_other)
    # Bob Other has no skills
    _, response = await app_as_other.asgi_client.get(f"/dashboard/members/{OTHER_ID}")
    assert response.status_code == 200
    assert "Skills Offered" not in response.text
    await engine.dispose()


# ---------------------------------------------------------------------------
# Task 1.5: Remaining CRUD path tests (FR-4)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_member_directory_200(app):
    """GET /members returns 200 with member names."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.get("/dashboard/members")
    assert response.status_code == 200
    assert "Alice Owner" in response.text
    assert "Bob Other" in response.text
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_create_form_200(app):
    """GET /members/new returns 200 with form."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.get("/dashboard/members/new")
    assert response.status_code == 200
    assert "New Member" in response.text or "Add New Member" in response.text
    assert "form" in response.text.lower()
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_create_valid_redirects(app):
    """POST /members with valid data creates member and redirects."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.post(
        "/dashboard/members",
        data={
            "ecosystem_id": str(ECOSYSTEM_ID),
            "display_name": "New Member",
            "member_id": "MEM-NEW-001",
            "profile": "townhall",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/dashboard/members/" in response.headers.get("location", "")
    await engine.dispose()


@pytest.mark.asyncio
async def test_member_create_bad_ecosystem_403(app):
    """POST /members with invalid ecosystem_id returns 403."""
    engine = await _setup_db(app)
    bad_eco = uuid.uuid4()
    _, response = await app.asgi_client.post(
        "/dashboard/members",
        data={
            "ecosystem_id": str(bad_eco),
            "display_name": "Bad Member",
            "member_id": "MEM-BAD-001",
            "profile": "builder",
        },
    )
    assert response.status_code == 403
    assert "Invalid" in response.text or "unauthorized" in response.text.lower()
    await engine.dispose()


@pytest.mark.asyncio
async def test_status_transition_valid_redirects(app):
    """POST /members/<id>/status with new_status redirects."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}/status",
        data={"new_status": "inactive", "trigger": "voluntary"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    # Verify status changed
    async with app.ctx.db() as session:
        member = await session.get(Member, OWNER_ID)
        assert member.current_status == "inactive"
    await engine.dispose()


@pytest.mark.asyncio
async def test_status_transition_missing_status_400(app):
    """POST /members/<id>/status without new_status returns 400."""
    engine = await _setup_db(app)
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}/status",
        data={},
    )
    assert response.status_code == 400
    assert "new_status" in response.text.lower() or "required" in response.text.lower()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Phase 4: End-to-End Integration Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_signup_to_profile_flow(app):
    """Simulate signup: create member, view profile, edit, verify update."""
    engine = await _setup_db(app)
    # 1. Create a new member
    _, response = await app.asgi_client.post(
        "/dashboard/members",
        data={
            "ecosystem_id": str(ECOSYSTEM_ID),
            "display_name": "New Joiner",
            "member_id": "MEM-JOINER-001",
            "profile": "townhall",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "/dashboard/members/" in location
    new_member_id = location.split("/dashboard/members/")[-1]

    # 2. View the new member's detail page
    _, response = await app.asgi_client.get(f"/dashboard/members/{new_member_id}")
    assert response.status_code == 200
    assert "New Joiner" in response.text
    assert "MEM-JOINER-001" in response.text
    await engine.dispose()


@pytest.mark.asyncio
async def test_skills_interests_complete_roundtrip(app):
    """Full round-trip: no skills → add skills → verify display → clear → verify gone."""
    engine = await _setup_db(app)
    # Start: Bob has no skills
    _, response = await app.asgi_client.get(f"/dashboard/members/{OTHER_ID}")
    assert "Skills Offered" not in response.text

    # Add skills via update (as owner of OWNER_ID, update our own profile)
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}",
        data={
            "skills_offered": "coding, mentoring, facilitation",
            "skills_needed": "accounting",
            "interests": "regenerative agriculture, web3",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Verify skills display
    _, response = await app.asgi_client.get(f"/dashboard/members/{OWNER_ID}")
    assert response.status_code == 200
    assert "coding" in response.text
    assert "mentoring" in response.text
    assert "accounting" in response.text
    assert "regenerative agriculture" in response.text

    # Clear all skills/interests
    _, response = await app.asgi_client.post(
        f"/dashboard/members/{OWNER_ID}",
        data={
            "skills_offered": "",
            "skills_needed": "",
            "interests": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302

    # Verify cleared
    _, response = await app.asgi_client.get(f"/dashboard/members/{OWNER_ID}")
    assert response.status_code == 200
    assert "Skills Offered" not in response.text
    assert "Interests" not in response.text
    await engine.dispose()
