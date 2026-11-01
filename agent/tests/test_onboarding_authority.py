"""G-Onboard authority table: the seven actors of review-onboarding.md section 2 against every onboarding write route.

Only an active steward of OmniOne changes OmniOne's onboarding content (policy.can_manage_onboarding) or a member's
status (policy.can_move_member). Every refused call leaves OmniOne's journey steps, its entry quiz's ecosystem,
the ethos access grants, the quiz assignment and the member's status exactly as seeded. Founder-B's co_creator
profile in Oasis opens nothing in OmniOne (review H3). Rules: src/neos_agent/api/AGENTS.md "Onboarding (G-Onboard)".
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from neos_agent.db.course_models import Quiz
from neos_agent.db.models import EthosUserAccess, JourneyMap, Member, MemberOnboarding, QuizAssignment

from .test_onboarding_flows import (  # noqa: F401 — world is the shared fixture
    ACTORS, FREE_QUIZ, OASIS, OASIS_QUIZ, OMNI_ASSIGNMENT, OMNI_MAP, OMNI_QUIZ, OMNIONE, PEOPLE, call, world,
)

MIA = PEOPLE["mia"].member_id(OMNIONE)
STEPS = [{"type": "text", "title": "Only step"}]

# route -> (method, url, body, the steward's status). Everyone else is refused (see REFUSED).
ROUTES = {
    "create journey": ("post", f"/api/v1/orientation/ethos/{OMNIONE}/journey-maps", {"title": "Rewritten", "content_sequence": STEPS}, 201),
    "edit journey": ("put", f"/api/v1/orientation/journey-maps/{OMNI_MAP}", {"content_sequence": []}, 200),
    "deactivate journey": ("post", f"/api/v1/orientation/journey-maps/{OMNI_MAP}/deactivate", None, 200),
    "delete journey": ("delete", f"/api/v1/orientation/journey-maps/{OMNI_MAP}", None, 409),  # walked: deactivate instead
    "assign quiz": ("post", f"/api/v1/ecosystems/{OMNIONE}/quizzes/assign", {"quiz_id": str(FREE_QUIZ), "is_entry_quiz": True}, 200),
    "unassign quiz": ("post", f"/api/v1/ecosystems/{OMNIONE}/quizzes/unassign", {"quiz_id": str(OMNI_QUIZ)}, 200),
    "quiz results": ("get", f"/api/v1/ecosystems/{OMNIONE}/quiz-results", None, 200),
    "list ethos access": ("get", f"/api/v1/ethos/{OMNIONE}/access", None, 200),
    "grant ethos access": ("post", f"/api/v1/ethos/{OMNIONE}/access", {"member_id": str(MIA), "role_in_ethos": "steward"}, 201),
    "revoke ethos access": ("delete", f"/api/v1/ethos/{OMNIONE}/access/{MIA}", None, 200),
    "assign quiz to member": ("post", "/api/v1/quiz-assignments", {"quiz_id": str(FREE_QUIZ), "member_id": str(MIA)}, 201),
    "remove quiz assignment": ("delete", f"/api/v1/quiz-assignments/{OMNI_ASSIGNMENT}", None, 200),
    "move member": ("post", f"/api/v1/members/{MIA}/status", {"status": "suspended"}, 200),
}
REFUSED = {"anon": 401, "pending": 403, "member": 403, "steward_b": 403, "founder_b": 403, "exited": 403}
# A member row outside the caller's active ecosystems is "not found" (get_scoped_or_404), not forbidden.
REFUSED_MOVE = {**REFUSED, "pending": 404, "steward_b": 404, "founder_b": 404, "exited": 404}


async def _omnione_onboarding(world) -> tuple:
    """Everything a refused call must leave as seeded."""
    async with world.db() as session:
        journey = await session.get(JourneyMap, OMNI_MAP)
        quiz = await session.get(Quiz, OMNI_QUIZ)
        access = (await session.execute(select(EthosUserAccess.member_id, EthosUserAccess.role_in_ethos).where(
            EthosUserAccess.ecosystem_id == OMNIONE))).all()
        assignments = await session.scalar(select(func.count()).select_from(QuizAssignment))
        mia = await session.get(Member, MIA)
    return (journey is not None and (journey.step_count, len(journey.content_sequence), journey.is_active),
            (quiz.ecosystem_id, quiz.is_entry_quiz), sorted(map(tuple, access)), assignments, mia.current_status)


@pytest.mark.parametrize("actor", sorted(ACTORS))
@pytest.mark.parametrize("route", sorted(ROUTES))
async def test_only_omniones_steward_changes_its_onboarding(world, route, actor):
    method, url, body, steward_status = ROUTES[route]
    expected = steward_status if actor == "steward" else (REFUSED_MOVE if route == "move member" else REFUSED)[actor]
    before = await _omnione_onboarding(world)
    kwargs = {"json": body} if body is not None else {}
    response = await call(world, method, ACTORS[actor], url, **kwargs)
    assert response.status == expected, (route, actor, response.text)
    if expected >= 400:
        assert await _omnione_onboarding(world) == before


async def test_a_steward_never_takes_another_ecosystems_quiz(world):
    # Oasis's steward cannot pull OmniOne's entry quiz into Oasis, nor can OmniOne's take Oasis's.
    stolen = await call(world, "post", "bea", f"/api/v1/ecosystems/{OASIS}/quizzes/assign", json={"quiz_id": str(OMNI_QUIZ)})
    taken = await call(world, "post", "sam", f"/api/v1/ecosystems/{OMNIONE}/quizzes/assign", json={"quiz_id": str(OASIS_QUIZ)})
    assert (stolen.status, taken.status) == (403, 403)
    async with world.db() as session:
        assert ((await session.get(Quiz, OMNI_QUIZ)).ecosystem_id, (await session.get(Quiz, OASIS_QUIZ)).ecosystem_id) == (
            OMNIONE, OASIS)


async def test_a_steward_grants_ethos_access_only_to_their_own_members_and_is_recorded_as_granter(world):
    outsider = await call(world, "post", "sam", f"/api/v1/ethos/{OMNIONE}/access",
                          json={"member_id": str(PEOPLE["bea"].member_id(OASIS))})
    assert (outsider.status, outsider.json["error"]) == (404, "Member not found in this ethos")
    kit = PEOPLE["kit"].member_id(OMNIONE)
    granted = await call(world, "post", "sam", f"/api/v1/ethos/{OMNIONE}/access", json={"member_id": str(kit)})
    assert granted.status == 201, granted.text
    assert granted.json["granted_by"] == str(PEOPLE["sam"].member_id(OMNIONE))  # the steward's row there


async def test_a_global_journey_is_no_ecosystems_to_change(world):
    from .test_onboarding_flows import GLOBAL_MAP

    response = await call(world, "put", "sam", f"/api/v1/orientation/journey-maps/{GLOBAL_MAP}", json={"title": "Mine"})
    assert response.status == 403
    async with world.db() as session:
        assert (await session.get(JourneyMap, GLOBAL_MAP)).title == "Global"


@pytest.mark.parametrize("url", ["/api/v1/onboarding/{member}/ceremony", "/api/v1/members/{member}/onboarding"])
@pytest.mark.parametrize("reader, expected", [
    ("mia", 200),  # her own record
    ("sam", 200),  # a steward of her ecosystem
    ("kit", 404),  # another OmniOne member: positions and objections are not theirs to read (review A8)
    ("bea", 404),  # another ecosystem's steward does not see her at all
])
async def test_a_members_ceremony_positions_are_read_by_them_and_their_stewards_only(world, url, reader, expected):
    async with world.db() as session:
        record = await session.scalar(select(MemberOnboarding).where(MemberOnboarding.member_id == MIA))
        record.section_consents = {"exit_rights": {"consented": True, "position": "stand_aside",
                                                   "objection_text": "Not sure about the notice period"}}
        await session.commit()
    response = await call(world, "get", reader, url.format(member=MIA))
    assert response.status == expected, response.text
    assert ("Not sure about the notice period" in response.text) is (expected == 200)


async def test_members_see_only_their_own_quiz_assignments(world):
    for who, expected in (("kit", [str(OMNI_ASSIGNMENT)]), ("mia", []), ("sam", [str(OMNI_ASSIGNMENT)]), ("nia", [])):
        listed = await call(world, "get", who, "/api/v1/quiz-assignments")
        assert listed.status == 200, listed.text
        assert [item["id"] for item in listed.json["items"]] == expected, who
