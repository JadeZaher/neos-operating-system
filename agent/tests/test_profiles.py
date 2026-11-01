"""Focused tests for public profile validation and serialization."""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
import uuid

import pytest
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from neos_agent.api.errors import register_api_errors
from neos_agent.api.members import members_api_bp
from neos_agent.api.profiles import _build_profile_response, profiles_api_bp
from neos_agent.api.schemas.profiles import ProfileUpdateRequest
from neos_agent.api.discover import _shares_needs_stats
from neos_agent.api.errors import ApiError
from neos_agent.services import exchange
from neos_agent.db.course_models import Course, Quiz, QuizResult
from neos_agent.db.models import (
    CircleMembership,
    Domain,
    Ecosystem,
    Member,
    SharesNeeds,
    User,
)


def test_profile_update_normalizes_lists_and_projects():
    payload = ProfileUpdateRequest.model_validate(
        {
            "skills": [" Facilitation ", "facilitation", "Systems Design"],
            "interests": ["Regeneration"],
            "social_links": {
                "linkedin": "",
                "github": "https://github.com/example",
            },
            "projects": [
                {
                    "name": " NEOS ",
                    "description": "A public collaboration",
                    "url": "https://example.com/neos",
                    "role": "Builder",
                    "started_at": "2026-01-01",
                    "ended_at": None,
                }
            ],
        }
    ).model_dump(mode="json")

    assert payload["skills"] == ["Facilitation", "Systems Design"]
    assert payload["interests"] == ["Regeneration"]
    assert payload["social_links"] == {"github": "https://github.com/example"}
    assert payload["projects"][0].keys() == {
        "id",
        "name",
        "description",
        "url",
        "role",
        "started_at",
        "ended_at",
    }


def test_admin_publication_stats_include_solutions():
    stats = _shares_needs_stats(
        SimpleNamespace(
            total=3,
            shares=1,
            needs=1,
            solutions=1,
            active=3,
            fulfilled=0,
            withdrawn=0,
        )
    )

    assert stats["solutions"] == 1
    assert set(stats) == {
        "total",
        "shares",
        "needs",
        "solutions",
        "active",
        "fulfilled",
        "withdrawn",
    }


@pytest.mark.asyncio
async def test_public_profile_aggregates_memberships_without_private_fields(db_session):
    user = User(
        id=uuid.uuid4(),
        did="did:key:not-public",
        username="kai",
        display_name="Kai",
        phone="+15555550100",
        headline="Community builder",
        skills=["Facilitation"],
        interests=["Regeneration"],
        projects=[],
    )
    ecosystem = Ecosystem(
        id=uuid.uuid4(),
        name="OmniOne",
        status="active",
        visibility="public",
    )
    member = Member(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        user_id=user.id,
        member_id="kai-omni",
        display_name="Kai",
        current_status="active",
        profile="townhall",
        notes="not public",
        privacy={"phone": "private"},
    )
    domain = Domain(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        domain_id="SHUR-KITCHEN",
        name="Community Kitchen",
        status="active",
        purpose="Coordinate the community kitchen",
    )
    circle = CircleMembership(
        id=uuid.uuid4(),
        domain_id=domain.id,
        member_id=member.id,
        role="member",
        joined_date=date(2026, 1, 1),
        status="active",
    )
    course = Course(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        domain_id=domain.id,
        title="Kitchen Course",
    )
    quiz = Quiz(
        id=uuid.uuid4(),
        course_id=course.id,
        title="Kitchen Orientation",
        mode="standard",
        visibility="public",
        is_published=True,
    )
    result = QuizResult(
        id=uuid.uuid4(),
        quiz_id=quiz.id,
        member_id=member.id,
        survey_results={"private_answer": "never serialize"},
        score=100,
        is_passed=True,
        result_metadata={
            "correctCount": 1,
            "perQuestion": [{"userAnswer": "never serialize"}],
        },
        completed_at=datetime(2026, 1, 2),
    )
    private_quiz = Quiz(
        id=uuid.uuid4(),
        course_id=course.id,
        title="Private Kitchen Assessment",
        mode="assessment",
        visibility="private",
        is_published=True,
    )
    private_result = QuizResult(
        id=uuid.uuid4(),
        quiz_id=private_quiz.id,
        member_id=member.id,
        score=100,
        is_passed=True,
        completed_at=datetime(2026, 1, 3),
    )
    public_post = SharesNeeds(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        domain_id=domain.id,
        author_member_id=member.id,
        type="solution",
        title="Kitchen scheduling",
        visibility="public",
        status="active",
    )
    private_post = SharesNeeds(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        domain_id=domain.id,
        author_member_id=member.id,
        type="need",
        title="Private need",
        visibility="private",
        status="active",
    )
    db_session.add_all(
        [
            user,
            ecosystem,
            member,
            domain,
            circle,
            course,
            quiz,
            result,
            private_quiz,
            private_result,
            public_post,
            private_post,
        ]
    )
    await db_session.commit()

    response = await _build_profile_response(db_session, user, user.id)

    assert response["is_owner"] is True
    assert response["profile"]["skills"] == ["Facilitation"]
    assert "did" not in response["profile"]
    assert "phone" not in response["profile"]
    assert "notes" not in response["ecosystems"][0]["membership"]
    assert response["domains"][0]["domain_id"] == "SHUR-KITCHEN"
    # Members see the domain's name; the generated code stays secondary.
    assert response["domains"][0]["display_name"] == "Community Kitchen"
    assert response["quiz_results"][0]["domain"]["display_name"] == "Community Kitchen"
    assert response["quiz_results"][0]["quiz"]["title"] == "Kitchen Orientation"
    assert "survey_results" not in response["quiz_results"][0]["results"][0]
    assert response["quiz_results"][0]["results"][0]["result_metadata"] == {}
    assert len(response["quiz_results"]) == 1
    assert [post["title"] for post in response["publications"]] == [
        "Kitchen scheduling"
    ]
    assert response["publications"][0]["ecosystem_name"] == "OmniOne"
    assert response["publications"][0]["domain_name"] == "Community Kitchen"


@pytest.mark.asyncio
async def test_publication_edits_are_author_only_and_a_profile_admin_moderates_only_its_own_ecosystem(db_session):
    """Flipped by G-Exchange (D1): this used to assert that any co_creator/builder manages any publication."""
    ecosystem = Ecosystem(id=uuid.uuid4(), name="Author Test", status="active")
    elsewhere = Ecosystem(id=uuid.uuid4(), name="Founded Elsewhere", status="active")
    domain = Domain(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        domain_id="AUTHOR-TEST",
        status="active",
    )
    author_user = User(id=uuid.uuid4(), display_name="Author")
    other_user = User(id=uuid.uuid4(), display_name="Other")
    author = Member(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        user_id=author_user.id,
        member_id="author",
        display_name="Author",
        current_status="active",
        profile="townhall",
    )
    other = Member(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        user_id=other_user.id,
        member_id="other",
        display_name="Other",
        current_status="active",
        profile="townhall",
    )
    publication = SharesNeeds(
        id=uuid.uuid4(),
        ecosystem_id=ecosystem.id,
        domain_id=domain.id,
        author_member_id=author.id,
        type="share",
        title="Author-owned share",
        visibility="public",
        status="active",
    )
    founder_user = User(id=uuid.uuid4(), display_name="Founder")
    founder = Member(  # founded another ecosystem: co_creator there, a plain member here (the D1 exploit)
        id=uuid.uuid4(), ecosystem_id=elsewhere.id, user_id=founder_user.id, member_id="founder",
        display_name="Founder", current_status="active", profile="co_creator",
    )
    founder_here = Member(
        id=uuid.uuid4(), ecosystem_id=ecosystem.id, user_id=founder_user.id, member_id="founder-here",
        display_name="Founder", current_status="active", profile="townhall",
    )
    db_session.add_all(
        [ecosystem, elsewhere, domain, author_user, other_user, founder_user, author, other, founder,
         founder_here, publication]
    )
    await db_session.commit()

    async def attempt(user, write):
        viewer = await exchange.load_viewer(db_session, user.id)
        try:
            await write(db_session, viewer, publication)
        except ApiError as refusal:
            return refusal.status, refusal.extra.get("code")
        return 200, None

    def edit(session, viewer, record):
        return exchange.update_publication(session, viewer, record, {"title": "Edited"})

    def hide(session, viewer, record):
        return exchange.hide_publication(session, viewer, record, "Off-topic")

    assert await attempt(other_user, edit) == (403, "AUTHOR_ONLY")
    assert await attempt(author_user, edit) == (200, None)
    # A co_creator profile on a row in ANOTHER ecosystem moderates nothing here.
    assert await attempt(founder_user, hide) == (403, "MODERATOR_ONLY")
    assert await attempt(founder_user, edit) == (403, "AUTHOR_ONLY")
    # A builder profile on a row in the post's own ecosystem moderates it (hide), but still never edits it.
    other.profile = "builder"
    await db_session.commit()
    assert await attempt(other_user, edit) == (403, "AUTHOR_ONLY")
    assert await attempt(other_user, hide) == (200, None)
    assert (publication.title, publication.hidden_reason) == ("Edited", "Off-topic")


# ---------------------------------------------------------------------------
# Owner decision 2026-11-01: the profile name is the member name in every ecosystem
# ---------------------------------------------------------------------------


async def test_saving_the_profile_name_renames_every_membership_and_governance_reads_show_it(db_engine):
    oasis, river = (Ecosystem(id=uuid.uuid4(), name=name, status="active") for name in ("Oasis", "River House"))
    kai, ines = User(id=uuid.uuid4(), display_name="Kai"), User(id=uuid.uuid4(), display_name="Ines")
    rows = {
        "kai-oasis": Member(id=uuid.uuid4(), ecosystem_id=oasis.id, user_id=kai.id, member_id="kai-oasis",
                            display_name="Kai", current_status="active", role="mod"),
        "kai-river": Member(id=uuid.uuid4(), ecosystem_id=river.id, user_id=kai.id, member_id="kai-river",
                            display_name="Kai R.", current_status="pending_consent"),
        "ines-oasis": Member(id=uuid.uuid4(), ecosystem_id=oasis.id, user_id=ines.id, member_id="ines-oasis",
                             display_name="Ines", current_status="active"),
    }
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add_all([oasis, river, kai, ines])
        await session.flush()
        session.add_all(rows.values())
        await session.commit()

    app = Sanic(f"test-profile-name-{uuid.uuid4().hex[:8]}")
    app.ctx.settings, app.ctx.db = MagicMock(), factory
    register_api_errors(app)

    @app.on_request
    async def sign_in_as_kai(request):
        request.ctx.user = User(id=kai.id, display_name="Kai")
        request.ctx.member = Member(id=rows["kai-oasis"].id, ecosystem_id=oasis.id, user_id=kai.id,
                                    member_id="kai-oasis", display_name="Kai", current_status="active", role="mod")
        request.ctx.selected_ecosystem_ids = request.ctx.authorized_ecosystem_ids = [oasis.id, river.id]

    app.blueprint(profiles_api_bp)
    app.blueprint(members_api_bp)

    _, saved = await app.asgi_client.put("/api/v1/profiles/me", json={"display_name": "  Kai Rivers "})
    assert saved.status == 200, saved.text
    assert saved.json["profile"]["display_name"] == "Kai Rivers"

    async with factory() as session:
        stored = {row.member_id: row.display_name for row in (await session.execute(select(Member))).scalars()}
    assert stored == {"kai-oasis": "Kai Rivers", "kai-river": "Kai Rivers", "ines-oasis": "Ines"}  # only Kai's rows
    for key in ("kai-oasis", "kai-river"):  # the governance read every page and the sidebar's session use
        _, detail = await app.asgi_client.get(f"/api/v1/members/{rows[key].id}")
        assert (detail.status, detail.json["display_name"]) == (200, "Kai Rivers"), key
