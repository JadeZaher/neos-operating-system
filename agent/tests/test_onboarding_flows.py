"""G-Onboard flows through the real blueprints: sign-up, join, return, the consent gate, steward moves, the queue.

Rules: src/neos_agent/api/AGENTS.md "Onboarding (G-Onboard)" and services/AGENTS.md "Member lifecycle (G-Onboard)".
Owner decisions (2026-11-01) each have a row that goes red if flipped: consent activates (no steward approval),
private ecosystems are not self-service, a leaver returns when eligible, stewards step in only for the stuck case.
The world below is shared with test_onboarding_authority.py and test_onboarding_parity.py.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.api.agreements import agreements_api_bp
from neos_agent.api.auth import auth_api_bp
from neos_agent.api.ecosystems import ecosystems_api_bp
from neos_agent.api.errors import register_api_errors
from neos_agent.api.ethos_access import ethos_access_api_bp
from neos_agent.api.members import members_api_bp
from neos_agent.api.next_steps import next_steps_api_bp
from neos_agent.api.onboarding import onboarding_api_bp
from neos_agent.api.orientation import orientation_api_bp
from neos_agent.api.quiz_assignments import quiz_assignments_api_bp
from neos_agent.api.quizzes import quizzes_api_bp
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.course_models import Quiz, QuizResult
from neos_agent.db.models import (
    Agreement, AgreementMemberConsent, AuthSession, Base, Ecosystem, EthosUserAccess, ExitRecord, JourneyMap, Member,
    MemberOnboarding, MemberStatusTransition, QuizAssignment, User, UserJourneyProgress,
)
from neos_agent.services import member_lifecycle
from neos_agent.services.agreement_consent import synchronize_agreement_requirements

OMNIONE, OASIS, HIDDEN, ESCHER = (uuid.UUID(int=n) for n in (11, 12, 13, 14))
OLD = datetime(2026, 1, 1)
SECRET = "g-onboard-session-secret-0123456789"
GATE_AGREEMENT = uuid.UUID(int=101)  # OmniOne's membership agreement
OMNI_MAP, GLOBAL_MAP, OASIS_MAP = uuid.UUID(int=201), uuid.UUID(int=202), uuid.UUID(int=203)
OMNI_QUIZ, OASIS_QUIZ, FREE_QUIZ = uuid.UUID(int=301), uuid.UUID(int=302), uuid.UUID(int=303)
OMNI_ASSIGNMENT = uuid.UUID(int=401)
PASSING_ANSWERS = {"q1": "consent"}


@dataclass(frozen=True)
class Person:
    key: str
    rows: dict  # ecosystem -> (status, role[, profile])
    new_in: tuple = field(default=())  # ecosystems where the row was created today (a first-month member)

    @property
    def user_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"g-onboard.{self.key}")

    def member_id(self, ecosystem_id: uuid.UUID) -> uuid.UUID:
        return uuid.uuid5(self.user_id, str(ecosystem_id))


PEOPLE = {person.key: person for person in (
    Person("ola", {OMNIONE: ("active", "owner")}),
    Person("sam", {OMNIONE: ("active", "mod")}),          # Steward
    Person("mia", {OMNIONE: ("active", "user")}),         # Member
    Person("nia", {OMNIONE: ("pending_consent", "user")}),  # Pending: OmniOne's agreement is still missing
    Person("eli", {OMNIONE: ("exited", "user"), OASIS: ("active", "user")}),  # Exited, may return
    Person("rex", {OMNIONE: ("exited", "user"), OASIS: ("active", "user")}),  # Exited, exit recorded as final
    Person("bea", {OASIS: ("active", "mod")}),            # Steward-B
    Person("finn", {OASIS: ("active", "user", "co_creator")}),  # Founder-B
    Person("eve", {ESCHER: ("active", "mod")}),
    Person("tess", {ESCHER: ("pending_consent", "user")}),  # stuck: Escher has no membership agreement
    Person("pia", {OASIS: ("active", "user"), OMNIONE: ("pending_consent", "user")}),
    Person("kit", {OASIS: ("active", "user"), OMNIONE: ("active", "user")}, new_in=(OMNIONE,)),  # first month
)}
# The seven actors of review-onboarding.md section 2 (relative to OmniOne).
ACTORS = {"anon": None, "pending": "nia", "member": "mia", "steward": "sam", "steward_b": "bea",
          "founder_b": "finn", "exited": "eli"}


def _quiz(quiz_id, ecosystem_id, title, *, entry=False):
    return Quiz(id=quiz_id, title=title, ecosystem_id=ecosystem_id, is_entry_quiz=entry, is_published=True,
                passing_score=50, survey_json={"pages": [{"elements": [{"type": "text", "name": "q1", "correctAnswer": "consent"}]}]})


async def _seed(session: AsyncSession) -> None:
    session.add_all([
        Ecosystem(id=OMNIONE, name="OmniOne", status="active", visibility="public"),
        Ecosystem(id=OASIS, name="Oasis", status="active", visibility="public"),
        Ecosystem(id=HIDDEN, name="Hidden Grove", status="active", visibility="private"),
        Ecosystem(id=ESCHER, name="Escherbridge", status="active", visibility="public"),
    ])
    for person in PEOPLE.values():
        session.add(User(id=person.user_id, display_name=person.key.title(), username=person.key))
    await session.flush()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for person in PEOPLE.values():
        for ecosystem_id, (status, role, *profile) in person.rows.items():
            session.add(Member(
                id=person.member_id(ecosystem_id), ecosystem_id=ecosystem_id, user_id=person.user_id,
                member_id=f"MEM-{person.key}-{ecosystem_id.int}", display_name=person.key.title(), role=role,
                current_status=status, profile=profile[0] if profile else None,
                created_at=now if ecosystem_id in person.new_in else OLD,
            ))
    await session.flush()
    gate = Agreement(
        id=GATE_AGREEMENT, ecosystem_id=OMNIONE, agreement_id="AGR-UAF-OMNI", type="uaf",
        title="Universal Agreement Field", version="1.0", status="active", proposer="Ola",
        text="Every member consents before taking part.", created_date=date(2026, 1, 2),
        requires_explicit_consent=True, prerequisite_scopes=["ecosystem"],
    )
    session.add(gate)
    await session.flush()
    await synchronize_agreement_requirements(session, gate)
    steps = [{"type": "text", "title": f"Step {n}"} for n in range(3)]
    session.add_all([
        JourneyMap(id=OMNI_MAP, slug="explorer", title="Explorer", ecosystem_id=OMNIONE, content_sequence=steps,
                   step_count=3),
        JourneyMap(id=GLOBAL_MAP, slug="global", title="Global", ecosystem_id=None, content_sequence=steps, step_count=3),
        JourneyMap(id=OASIS_MAP, slug="oasis", title="Oasis path", ecosystem_id=OASIS, content_sequence=steps,
                   step_count=3),
        _quiz(OMNI_QUIZ, OMNIONE, "Community Onboarding", entry=True),
        _quiz(OASIS_QUIZ, OASIS, "Oasis basics"),
        _quiz(FREE_QUIZ, None, "Governance basics"),
        UserJourneyProgress(id=uuid.uuid4(), member_id=PEOPLE["mia"].member_id(OMNIONE), ecosystem_id=OMNIONE,
                            journey_map_id=OMNI_MAP, status="complete", current_step=3, completed_steps=[0, 1, 2]),
        EthosUserAccess(id=uuid.uuid4(), member_id=PEOPLE["mia"].member_id(OMNIONE), ecosystem_id=OMNIONE,
                        role_in_ethos="member", access_level="member", granted_by=PEOPLE["sam"].member_id(OMNIONE)),
        QuizAssignment(id=OMNI_ASSIGNMENT, quiz_id=OMNI_QUIZ, member_id=PEOPLE["kit"].member_id(OMNIONE),
                       ecosystem_id=OMNIONE, assigned_by=PEOPLE["sam"].member_id(OMNIONE)),
        MemberOnboarding(id=uuid.uuid4(), member_id=PEOPLE["mia"].member_id(OMNIONE), section_consents={}),
        ExitRecord(id=uuid.uuid4(), ecosystem_id=OMNIONE, member_id=PEOPLE["eli"].member_id(OMNIONE),
                   status="completed", re_entry_eligible=True),
        ExitRecord(id=uuid.uuid4(), ecosystem_id=OMNIONE, member_id=PEOPLE["rex"].member_id(OMNIONE),
                   status="completed", re_entry_eligible=False),
    ])
    await session.commit()


def _app(factory) -> Sanic:
    """Real blueprints; x-test-as / x-test-user set the session as main._load_ecosystems would (rows read from the DB)."""
    app = Sanic(f"g-onboard-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = SimpleNamespace(SESSION_SECRET=SECRET, SESSION_MAX_AGE_HOURS=24,
                                       SIGNUP_DEFAULT_ECOSYSTEM_SLUG="omnione")
    app.ctx.db = factory
    register_api_errors(app)

    @app.on_request
    async def inject_session(request):
        request.ctx.platform_admin = request.headers.get("x-platform-admin") == "1"
        who = request.headers.get("x-test-as")
        raw = PEOPLE[who].user_id if who else request.headers.get("x-test-user")
        if not raw:
            return
        user_id = uuid.UUID(str(raw))
        async with factory() as session:
            request.ctx.user = await session.get(User, user_id)
            rows = (await session.execute(select(Member).where(Member.user_id == user_id).order_by(
                Member.current_status != "active", Member.created_at, Member.id))).scalars().all()
        active = [row.ecosystem_id for row in rows if row.current_status == "active"]
        request.ctx.member = rows[0] if rows else None
        request.ctx.authorized_ecosystem_ids = active
        selected = request.headers.get("x-test-selected")  # the ecosystem picker; default: every active one
        request.ctx.selected_ecosystem_ids = [uuid.UUID(e) for e in selected.split(",")] if selected else list(active)

    for blueprint in (auth_api_bp, ecosystems_api_bp, members_api_bp, onboarding_api_bp, orientation_api_bp,
                      ethos_access_api_bp, quiz_assignments_api_bp, quizzes_api_bp, agreements_api_bp,
                      next_steps_api_bp):
        app.blueprint(blueprint)
    return app


@pytest_asyncio.fixture
async def world():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        await _seed(session)
    yield SimpleNamespace(app=_app(factory), db=factory)
    await engine.dispose()


@pytest_asyncio.fixture
async def agreement_only(world):
    """Select a consent-only fixture while keeping the quiz available for ordinary learning."""
    async with world.db() as session:
        quiz = await session.get(Quiz, OMNI_QUIZ)
        quiz.is_entry_quiz = False
        await session.commit()


async def call(world, method: str, who: str | None, url: str, **kwargs):
    headers = {"x-test-as": who} if who else {}
    headers.update(kwargs.pop("headers", {}))
    _, response = await world.app.asgi_client.request(method.upper(), url, headers=headers, **kwargs)  # DELETE takes a body
    return response


async def row_id(world, who: str, ecosystem_id) -> uuid.UUID:
    """A row the test did not seed (placement gives it a fresh id): looked up by user and ecosystem."""
    async with world.db() as session:
        return await session.scalar(select(Member.id).where(
            Member.user_id == PEOPLE[who].user_id, Member.ecosystem_id == ecosystem_id))


async def transitions(world, member_id) -> list[tuple]:
    """(from, to, trigger, actor) for one row, oldest first."""
    async with world.db() as session:
        rows = (await session.execute(select(MemberStatusTransition).where(
            MemberStatusTransition.member_id == member_id).order_by(MemberStatusTransition.created_at))).scalars().all()
    return [(row.from_status, row.to_status, row.trigger, row.actor_member_id) for row in rows]


async def status_of(world, member_id) -> str | None:
    async with world.db() as session:
        row = await session.get(Member, member_id)
    return row.current_status if row else None


async def queue_actions(world, who: str) -> list[tuple]:
    response = await call(world, "get", who, "/api/v1/me/next-steps")
    assert response.status == 200, response.text
    return [(item["action"], item["title"]) for item in response.json["items"] if item["kind"] == "newcomer"]


def _cookie(response) -> dict:
    for header in response.headers.get_list("set-cookie"):
        if header.startswith("neos_session="):
            return {"neos_session": header.split(";", 1)[0].split("=", 1)[1]}
    raise AssertionError("no session cookie")


# --- Sign-up -> pending -> consent -> active, one transition per move --------------------------------------------


@pytest.mark.usefixtures("agreement_only")
async def test_sign_up_waits_on_consent_and_consenting_activates_with_one_transition_each(world):
    _, signed_up = await world.app.asgi_client.post("/api/v1/auth/register", json={
        "username": "newbie", "password": "correct-horse-1"})
    assert signed_up.status == 200, signed_up.text
    assert (signed_up.json["status"], [a["title"] for a in signed_up.json["required_agreements"]]) == (
        "consent_required", ["Universal Agreement Field"])
    async with world.db() as session:
        user = await session.scalar(select(User).where(User.username == "newbie"))
        row = await session.scalar(select(Member).where(Member.user_id == user.id))
    assert await transitions(world, row.id) == [("prospective", "pending_consent", "signup", None)]
    _, me = await world.app.asgi_client.get("/api/v1/auth/me", cookies=_cookie(signed_up))
    assert [(e["name"], e["membership_status"]) for e in me.json["ecosystems"]] == [("OmniOne", "pending_consent")]

    # Owner decision: consent is what activates; no steward approves.
    as_newbie = {"x-test-user": str(user.id)}
    consented = await call(world, "post", None, f"/api/v1/agreements/{GATE_AGREEMENT}/consent", headers=as_newbie,
                           json={"attestation": "I consent to the Universal Agreement Field"})
    assert consented.status == 201, consented.text
    assert await status_of(world, row.id) == "active"
    assert [t[:3] for t in await transitions(world, row.id)] == [
        ("prospective", "pending_consent", "signup"), ("pending_consent", "active", "consent")]

    # Withdrawing that consent still demotes (owner default), recorded the same way.
    withdrawn = await call(world, "delete", None, f"/api/v1/agreements/{GATE_AGREEMENT}/consent", headers=as_newbie,
                           json={"reason": "I need to reread it"})
    assert withdrawn.status == 200, withdrawn.text
    assert await status_of(world, row.id) == "pending_consent"
    assert (await transitions(world, row.id))[-1][:3] == ("active", "pending_consent", "consent_withdrawn")


# --- Private ecosystems are not self-service; public ones are -----------------------------------------------------


async def test_a_private_ecosystem_is_not_found_by_join_or_sign_up(world):
    _, signed_up = await world.app.asgi_client.post("/api/v1/auth/register", json={
        "username": "lurker", "password": "correct-horse-1", "ecosystem_id": str(HIDDEN)})
    assert (signed_up.status, signed_up.json) == (404, {"error": "Ecosystem not found"})
    joined = await call(world, "post", "mia", f"/api/v1/ecosystems/{HIDDEN}/join")
    assert (joined.status, joined.json) == (404, {"error": "Ecosystem not found"})
    async with world.db() as session:
        assert await session.scalar(select(func.count()).select_from(Member).where(Member.ecosystem_id == HIDDEN)) == 0
        assert await session.scalar(select(User).where(User.username == "lurker")) is None

    # A public ecosystem with no membership agreement: active at once, one "joined" transition.
    opened = await call(world, "post", "mia", f"/api/v1/ecosystems/{OASIS}/join")
    assert opened.status == 201, opened.text
    assert (opened.json["status"], opened.json["outcome"], opened.json["membership_status"]) == ("joined", "joined", "active")
    assert await transitions(world, await row_id(world, "mia", OASIS)) == [("prospective", "active", "joined", None)]


async def test_an_invite_link_places_the_sign_up_in_the_public_ecosystem_it_names(world):
    _, signed_up = await world.app.asgi_client.post("/api/v1/auth/register", json={
        "username": "invited", "password": "correct-horse-1", "ecosystem_id": str(OASIS)})
    assert (signed_up.status, signed_up.json["status"], signed_up.json["member"]["ecosystem_id"]) == (
        200, "joined", str(OASIS))


# --- Leaving and returning ----------------------------------------------------------------------------------------


@pytest.mark.usefixtures("agreement_only")
async def test_a_leaver_returns_to_the_same_row_as_a_fresh_member_who_consents_again(world):
    eli = PEOPLE["eli"].member_id(OMNIONE)
    # Eli left before exits cleared anything (a row from before FX-Onboard): he had consented to the UAF and was an
    # admin with the co_creator profile. None of it carries over (review F4, A1).
    async with world.db() as session:
        session.add(AgreementMemberConsent(
            id=uuid.uuid4(), agreement_id=GATE_AGREEMENT, member_id=eli, agreement_version="1.0",
            attestation="I consent to the Universal Agreement Field", attested_at=datetime(2026, 2, 1)))
        row = await session.get(Member, eli)
        row.role, row.profile = "admin", "co_creator"
        await session.commit()
    back = await call(world, "post", "eli", f"/api/v1/ecosystems/{OMNIONE}/join")
    assert back.status == 200, back.text
    assert (back.json["outcome"], back.json["status"], back.json["membership_status"]) == (
        "re_entry", "consent_required", "pending_consent")  # re-consents to the current agreements
    async with world.db() as session:
        rows = (await session.execute(select(Member).where(
            Member.user_id == PEOPLE["eli"].user_id, Member.ecosystem_id == OMNIONE))).scalars().all()
        old_consent = await session.scalar(select(AgreementMemberConsent).where(AgreementMemberConsent.member_id == eli))
    assert [(row.id, row.role, row.profile) for row in rows] == [(eli, "user", None)]  # the same row, history kept
    assert old_consent.withdrawal_reason.startswith("Returned after leaving")
    assert sorted(await transitions(world, eli)) == [
        ("exited", "pending_consent", "re_entry", None),
        ("profile:co_creator", "profile:", "profile_grant", None),
        ("role:admin", "role:user", "role_grant", None),
    ]
    assert ("consent_to_join", "Consent to Universal Agreement Field") in await queue_actions(world, "eli")

    # An exit recorded as final is not reopened by the leaver.
    closed = await call(world, "post", "rex", f"/api/v1/ecosystems/{OMNIONE}/join")
    assert (closed.status, closed.json["code"]) == (403, "RE_ENTRY_CLOSED")
    assert await status_of(world, PEOPLE["rex"].member_id(OMNIONE)) == "exited"


# --- Concurrency and repeats --------------------------------------------------------------------------------------


async def test_two_concurrent_joins_leave_one_row_201_then_409(world, monkeypatch):
    first = await call(world, "post", "mia", f"/api/v1/ecosystems/{OASIS}/join")
    assert first.status == 201, first.text

    async def read_before_the_first_committed(session, user_id, ecosystem_id):
        return None  # the second request looked before the first insert existed

    monkeypatch.setattr(member_lifecycle, "_existing_row", read_before_the_first_committed)
    second = await call(world, "post", "mia", f"/api/v1/ecosystems/{OASIS}/join")
    assert (second.status, second.json["code"]) == (409, "ALREADY_MEMBER")  # was an uncaught IntegrityError (500)
    async with world.db() as session:
        count = await session.scalar(select(func.count()).select_from(Member).where(
            Member.user_id == PEOPLE["mia"].user_id, Member.ecosystem_id == OASIS))
    assert count == 1
    assert len(await transitions(world, await row_id(world, "mia", OASIS))) == 1


async def test_creating_a_second_row_for_yourself_is_a_409_not_a_500(world):
    response = await call(world, "post", "mia", "/api/v1/members", json={
        "ecosystem_id": str(OMNIONE), "display_name": "Mia again"})
    assert (response.status, response.json["code"]) == (409, "ALREADY_MEMBER")


# --- The consent gate: an empty gate heals, a non-empty one waits --------------------------------------------------


@pytest.mark.usefixtures("agreement_only")
async def test_an_empty_gate_heals_on_join_and_a_waiting_one_names_what_is_left(world):
    healed = await call(world, "post", "tess", f"/api/v1/ecosystems/{ESCHER}/join")  # "Check my membership"
    assert healed.status == 200, healed.text
    assert (healed.json["outcome"], healed.json["membership_status"]) == ("gate_cleared", "active")
    assert await transitions(world, PEOPLE["tess"].member_id(ESCHER)) == [
        ("pending_consent", "active", "gate_cleared", None)]

    waiting = await call(world, "post", "nia", f"/api/v1/ecosystems/{OMNIONE}/join")
    assert (waiting.status, waiting.json["code"]) == (409, "CONSENT_REQUIRED")
    assert [a["title"] for a in waiting.json["required_agreements"]] == ["Universal Agreement Field"]
    assert await status_of(world, PEOPLE["nia"].member_id(OMNIONE)) == "pending_consent"


# --- Steward moves: the closed table ------------------------------------------------------------------------------


@pytest.mark.parametrize("who, target, ecosystem, to, expected, after", [
    ("sam", "ola", OMNIONE, "suspended", 403, "active"),          # a mod never moves the owner (rank)
    ("sam", "sam", OMNIONE, "suspended", 403, "active"),          # never yourself
    ("mia", "kit", OMNIONE, "suspended", 403, "active"),          # members make no moves
    ("ola", "mia", OMNIONE, "suspended", 200, "suspended"),
    ("sam", "nia", OMNIONE, "active", 409, "pending_consent"),    # owner decision: no approval while consent is missing
    ("eve", "tess", ESCHER, "active", 200, "active"),             # the stuck case: a steward confirms
    ("sam", "mia", OMNIONE, "exited", 400, "active"),             # leaving is the exit flow
    ("sam", "mia", OMNIONE, "inactive", 400, "active"),           # not in the table
    ("sam", "mia", OMNIONE, "x" * 51, 400, "active"),             # too long: a 400, never a 500
    ("bea", "mia", OMNIONE, "suspended", 404, "active"),          # another ecosystem's steward does not see her
])
async def test_steward_moves_follow_the_closed_table(world, who, target, ecosystem, to, expected, after):
    target_id = PEOPLE[target].member_id(ecosystem)
    response = await call(world, "post", who, f"/api/v1/members/{target_id}/status", json={"status": to})
    assert response.status == expected, response.text
    assert await status_of(world, target_id) == after
    recorded = await transitions(world, target_id)
    if expected == 200:
        assert recorded == [(recorded[0][0], after, "steward_move", PEOPLE[who].member_id(ecosystem))]
    else:
        assert recorded == []
    if expected == 409:
        assert [a["title"] for a in response.json["required_agreements"]] == ["Universal Agreement Field"]
    if to in ("exited", "inactive"):
        assert response.json["allowed"] == ["suspended"]
        assert response.json.get("code") == ("USE_EXIT_FLOW" if to == "exited" else None)


@pytest.mark.parametrize("who, target, ecosystem, labels", [
    ("eve", "tess", ESCHER, ["Confirm membership"]),
    ("sam", "nia", OMNIONE, []),  # consenting will activate her; nothing for a steward to press
    ("ola", "mia", OMNIONE, ["Suspend membership"]),
    ("mia", "kit", OMNIONE, []),
])
async def test_the_member_page_offers_exactly_the_moves_the_route_accepts(world, who, target, ecosystem, labels):
    profile = await call(world, "get", who, f"/api/v1/members/{PEOPLE[target].member_id(ecosystem)}/profile")
    assert profile.status == 200, profile.text
    assert [move["label"] for move in profile.json["caller_member_moves"]] == labels


# --- The queue: newcomers and stewards ----------------------------------------------------------------------------


async def test_a_stuck_newcomer_is_in_their_stewards_queue_until_confirmed(world):
    tess = PEOPLE["tess"].member_id(ESCHER)
    assert await queue_actions(world, "eve") == [("confirm_membership", "Confirm Tess's membership")]
    assert await queue_actions(world, "bea") == []  # a steward elsewhere is not asked
    assert await queue_actions(world, "sam") == []  # Nia is pending but not stuck: her consent activates her
    assert (await call(world, "post", "eve", f"/api/v1/members/{tess}/status", json={"status": "active"})).status == 200
    assert await queue_actions(world, "eve") == []


async def test_a_first_month_member_is_asked_to_orient_and_take_the_entry_quiz_until_done(world):
    kit = PEOPLE["kit"].member_id(OMNIONE)
    assert sorted(await queue_actions(world, "kit")) == [
        ("start_orientation", "Walk through OmniOne's orientation"), ("take_entry_quiz", "Take Community Onboarding")]
    assert await queue_actions(world, "mia") == []  # joined long ago

    saved = await call(world, "post", "kit", f"/api/v1/orientation/ethos/{OMNIONE}/progress",
                       json={"journey_map_id": str(OMNI_MAP), "current_step": 3, "status": "complete"})
    assert saved.status == 200, saved.text
    # Kit's default row is Oasis (older); the entry quiz is OmniOne's, so the result lands on the OmniOne row.
    submitted = await call(world, "post", "kit", f"/api/v1/quizzes/{OMNI_QUIZ}/submit",
                           json={"survey_results": PASSING_ANSWERS})
    assert submitted.status == 201, submitted.text
    async with world.db() as session:
        result = await session.scalar(select(QuizResult).where(QuizResult.quiz_id == OMNI_QUIZ))
        assignment = await session.get(QuizAssignment, OMNI_ASSIGNMENT)
    assert (result.member_id, result.is_passed, assignment.status) == (kit, True, "completed")
    assert await queue_actions(world, "kit") == []


@pytest.mark.parametrize("who, expected", [
    ("nia", [("consent_to_join", "Consent to Universal Agreement Field")]),  # an agreement is still missing
    ("tess", [("finish_joining", "Finish joining Escherbridge")]),  # nothing is left: she checks her membership
])
async def test_a_newcomer_active_nowhere_gets_their_joining_steps_over_rest(world, who, expected):
    # REST scopes the queue to active AND pending memberships (api/next_steps.py); active-only would leave them empty.
    assert await queue_actions(world, who) == expected


async def test_a_founder_sees_and_confirms_a_stuck_newcomer_of_their_ecosystem(world):
    # Ivy is pending in Oasis, which has no membership agreement: stuck. Finn founded Oasis (role user, co_creator).
    ivy_user, ivy = uuid.uuid4(), uuid.uuid4()
    async with world.db() as session:
        session.add(User(id=ivy_user, display_name="Ivy", username="ivy"))
        await session.flush()
        session.add(Member(id=ivy, ecosystem_id=OASIS, user_id=ivy_user, member_id="MEM-ivy", display_name="Ivy",
                           role="user", current_status="pending_consent", created_at=OLD))
        await session.commit()
    assert await queue_actions(world, "finn") == [("confirm_membership", "Confirm Ivy's membership")]
    listed = await call(world, "get", "finn", "/api/v1/onboarding/newcomers")
    assert [(item["display_name"], item["stuck"]) for item in listed.json["items"]] == [("Ivy", True)]
    profile = await call(world, "get", "finn", f"/api/v1/members/{ivy}/profile")
    assert [move["label"] for move in profile.json["caller_member_moves"]] == ["Confirm membership"]
    confirmed = await call(world, "post", "finn", f"/api/v1/members/{ivy}/status", json={"status": "active"})
    assert confirmed.status == 200, confirmed.text
    assert await transitions(world, ivy) == [("pending_consent", "active", "steward_move", PEOPLE["finn"].member_id(OASIS))]
    assert await queue_actions(world, "finn") == []
    # Confirming confers nothing, so it needs no rank; suspending still does (Finn does not outrank a member).
    suspend = await call(world, "post", "finn", f"/api/v1/members/{ivy}/status", json={"status": "suspended"})
    assert suspend.status == 403
    assert await status_of(world, ivy) == "active"


async def test_newcomers_reach_a_steward_whose_selected_ecosystem_is_another(world):
    # Eve stewards Escherbridge and is also a plain member of Oasis, with Oasis selected. The queue already brings her
    # Tess's confirmation; the Newcomers page used to answer "Only stewards see newcomers" (review F12).
    async with world.db() as session:
        session.add(Member(id=uuid.uuid4(), ecosystem_id=OASIS, user_id=PEOPLE["eve"].user_id, member_id="MEM-eve-oasis",
                           display_name="Eve", role="user", current_status="active", created_at=OLD))
        await session.commit()
    listed = await call(world, "get", "eve", "/api/v1/onboarding/newcomers", headers={"x-test-selected": str(OASIS)})
    assert listed.status == 200, listed.text
    assert [(item["display_name"], item["ecosystem_name"]) for item in listed.json["items"]] == [("Tess", "Escherbridge")]


async def test_a_pending_newcomer_is_asked_to_consent_by_the_assistant_queue(world):
    from neos_agent.agent.governance_tools import execute_tool

    async with world.db() as session:
        result = await execute_tool("what_needs_me", {}, session, caller_user_id=PEOPLE["pia"].user_id)
    items = [(item["action"], item["title"], item["link"]) for item in result["data"]["items"] if item["kind"] == "newcomer"]
    assert items == [("consent_to_join", "Consent to Universal Agreement Field", f"/agreements/{GATE_AGREEMENT}")]


# --- Newcomers list, ceremony history, /auth/me ------------------------------------------------------------------


async def test_stewards_see_their_newcomers_and_members_do_not(world):
    listed = await call(world, "get", "sam", "/api/v1/onboarding/newcomers")
    assert listed.status == 200, listed.text
    rows = [(item["display_name"], item["ecosystem_name"], item["current_status"], item["stuck"],
             [a["title"] for a in item["required_agreements"]]) for item in listed.json["items"]]
    assert sorted(rows) == [
        ("Kit", "OmniOne", "active", False, []),
        ("Nia", "OmniOne", "pending_consent", False, ["Universal Agreement Field"]),
        ("Pia", "OmniOne", "pending_consent", False, ["Universal Agreement Field"]),
    ]
    stuck_first = await call(world, "get", "eve", "/api/v1/onboarding/newcomers")
    assert [(item["display_name"], item["stuck"]) for item in stuck_first.json["items"]] == [("Tess", True)]
    refused = await call(world, "get", "mia", "/api/v1/onboarding/newcomers")
    assert (refused.status, refused.json["error"]) == (403, "Only stewards see newcomers")


async def test_a_stand_aside_is_recorded_but_does_not_complete_the_ceremony(world):
    url = f"/api/v1/onboarding/{PEOPLE['mia'].member_id(OMNIONE)}/ceremony"
    for section in ("governance", "economics", "membership", "conflict_resolution", "data_sovereignty"):
        assert (await call(world, "post", "mia", url, json={"section": section, "consented": True})).status == 200
    last = await call(world, "post", "mia", url, json={"section": "exit_rights", "consented": True,
                                                       "position": "stand_aside"})
    assert last.status == 200, last.text
    assert (last.json["completion_percentage"], last.json["consent_date"]) == (83, None)


async def test_auth_me_reports_each_membership_and_the_platform_admin_flag(world):
    session_id = uuid.uuid4()
    async with world.db() as session:
        session.add(AuthSession(id=session_id, user_id=PEOPLE["eli"].user_id,
                                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
        await session.commit()
    cookie = {"neos_session": make_session_cookie(str(session_id), SECRET)}
    _, me = await world.app.asgi_client.get("/api/v1/auth/me", cookies=cookie)
    assert me.status == 200, me.text
    assert sorted((e["name"], e["membership_status"], e["role"]) for e in me.json["ecosystems"]) == [
        ("Oasis", "active", "user"), ("OmniOne", "exited", "user")]
    assert (me.json["member"]["ecosystem_id"], me.json["is_platform_admin"]) == (str(OASIS), False)  # the active row
    _, admin = await world.app.asgi_client.get("/api/v1/auth/me", cookies=cookie, headers={"x-platform-admin": "1"})
    assert admin.json["is_platform_admin"] is True


async def test_orientation_progress_takes_only_this_ecosystems_journeys_and_known_statuses(world):
    url = f"/api/v1/orientation/ethos/{OMNIONE}/progress"
    foreign = await call(world, "post", "kit", url, json={"journey_map_id": str(OASIS_MAP), "current_step": 0})
    assert (foreign.status, foreign.json["field"]) == (400, "journey_map_id")
    unknown = await call(world, "post", "kit", url, json={"journey_map_id": str(OMNI_MAP), "status": "done-ish"})
    assert unknown.status == 400
    leaver = await call(world, "post", "eli", url, json={"journey_map_id": str(OMNI_MAP), "current_step": 1})
    assert (leaver.status, leaver.json["code"]) == (409, "JOIN_REQUIRED")  # rejoin first; never written on the exited row
    newcomer = await call(world, "post", "nia", url, json={"journey_map_id": str(OMNI_MAP), "current_step": 1,
                                                           "status": "in_progress"})
    assert newcomer.status == 200, newcomer.text  # walkthrough before consent (member-lifecycle E.3-6)
    async with world.db() as session:
        written = (await session.execute(select(UserJourneyProgress.member_id).where(
            UserJourneyProgress.ecosystem_id == OMNIONE))).scalars().all()
    assert sorted(map(str, written)) == sorted(map(str, [PEOPLE["mia"].member_id(OMNIONE), PEOPLE["nia"].member_id(OMNIONE)]))


async def test_a_progress_save_that_names_no_journey_keeps_the_one_it_has(world):
    saved = await call(world, "post", "mia", f"/api/v1/orientation/ethos/{OMNIONE}/progress",
                       json={"journey_map_id": None, "current_step": 2})
    assert saved.status == 200, saved.text  # was a NOT NULL IntegrityError (500), review A11
    assert (saved.json["journey_map_id"], saved.json["current_step"]) == (str(OMNI_MAP), 2)
