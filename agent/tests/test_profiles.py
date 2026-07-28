"""Focused tests for public profile validation and serialization."""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
import uuid

import pytest

from neos_agent.api.profiles import _build_profile_response
from neos_agent.api.schemas.profiles import ProfileUpdateRequest
from neos_agent.api.discover import (
    _require_auth_for_shares_needs,
    _shares_needs_stats,
)
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
    assert response["quiz_results"][0]["quiz"]["title"] == "Kitchen Orientation"
    assert "survey_results" not in response["quiz_results"][0]["results"][0]
    assert response["quiz_results"][0]["results"][0]["result_metadata"] == {}
    assert len(response["quiz_results"]) == 1
    assert [post["title"] for post in response["publications"]] == [
        "Kitchen scheduling"
    ]
    assert response["publications"][0]["ecosystem_name"] == "OmniOne"
    assert response["publications"][0]["domain_name"] == "SHUR-KITCHEN"


@pytest.mark.asyncio
async def test_publication_mutation_is_author_only_except_for_admins(db_session):
    ecosystem = Ecosystem(id=uuid.uuid4(), name="Author Test", status="active")
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
    db_session.add_all(
        [ecosystem, domain, author_user, other_user, author, other, publication]
    )
    await db_session.commit()

    request = SimpleNamespace(ctx=SimpleNamespace(member=other))
    _, _, error = await _require_auth_for_shares_needs(
        request,
        db_session,
        publication.id,
    )
    assert error.status == 403

    request.ctx.member = author
    _, owned_record, error = await _require_auth_for_shares_needs(
        request,
        db_session,
        publication.id,
    )
    assert error is None
    assert owned_record.id == publication.id

    other.profile = "builder"
    request.ctx.member = other
    _, admin_record, error = await _require_auth_for_shares_needs(
        request,
        db_session,
        publication.id,
    )
    assert error is None
    assert admin_record.id == publication.id
