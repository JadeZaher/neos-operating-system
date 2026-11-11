"""Onboarding boundaries through the real app and its middleware (wave C fix lane FX-Onboard).

Who comes back as what after leaving (A1, F4), who changes an ecosystem's quizzes or reads their results (A2, A9),
where every sign-in lands (A3), and what a signed-out visitor sees on a profile (A6). Rules:
src/neos_agent/api/AGENTS.md "Onboarding (G-Onboard)" and services/AGENTS.md "Member lifecycle (G-Onboard)", both
§ FX-Onboard. Each case asserts the status AND whether the act took effect, so a refusal that still wrote goes red.
"""

from __future__ import annotations

import contextlib
import functools
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session

import neos_agent.db.course_models  # noqa: F401 — registers quiz tables the app's blueprints reference
from neos_agent.api.helpers import PLATFORM_HOME_SETTING_KEY
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.course_models import Quiz, QuizResult
from neos_agent.db.models import (
    Agreement, AgreementMemberConsent, AgreementRequirement, AppSetting, AuthSession, Base, Domain, Ecosystem,
    EcosystemAdmin, Member, MemberStatusTransition, NodeAdmin, SharesNeeds, User,
)

SECRET = "fx-onboard-boundaries-secret-0123456789"
HIDDEN = uuid.UUID(int=0xF0)  # private, and the oldest row: what select(Ecosystem).limit(1) used to return
OMNIONE = uuid.UUID(int=0xF1)  # the pinned home, with a membership agreement
RIVERBANK = uuid.UUID(int=0xF2)
RIVER_DOMAIN = uuid.UUID(int=0xD2)
UAF = uuid.UUID(int=0xA1)

ECOSYSTEMS = (  # inserted in this order, so the private one is the first heap row too
    (HIDDEN, "Hidden Grove", "private", datetime(2025, 12, 1)),
    (OMNIONE, "OmniOne", "public", datetime(2026, 1, 1)),
    (RIVERBANK, "Riverbank", "public", datetime(2026, 2, 1)),
)
# name -> rows (ecosystem, status, role, profile)
PEOPLE = {
    "olga": [(OMNIONE, "active", "owner", "co_creator")],  # the home's owner; the exit test separately grants node authority
    "sami": [(OMNIONE, "active", "admin", None)],  # a home steward (confirms Olga's exit); no row in Riverbank
    "lani": [(OMNIONE, "active", "owner", "co_creator")],  # explicit NodeAdmin assignment below; no row in Riverbank
    "rudy": [(RIVERBANK, "active", "user", None)],  # a plain Riverbank member
    "rhea": [(RIVERBANK, "active", "mod", None), (HIDDEN, "active", "user", None)],  # Riverbank's steward
    "fern": [(RIVERBANK, "active", "user", "co_creator")],  # Riverbank's founder (role user, co_creator there)
    "hal": [(HIDDEN, "active", "user", None)],
}
ACTORS = ("anon", "rudy", "sami", "rhea", "fern", "lani")


def _user_id(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"fx-onboard.{name}")


def _row_id(name: str, ecosystem_id: uuid.UUID) -> uuid.UUID:
    return uuid.uuid5(_user_id(name), str(ecosystem_id))


@pytest.fixture(scope="module")
def boundaries(tmp_path_factory):
    """One create_app (real auth and platform-admin middleware) over a SQLite file seeded with the people above."""
    from neos_agent.config import Settings
    from neos_agent.main import create_app

    database_file = (tmp_path_factory.mktemp("fx-onboard") / "boundaries.db").as_posix()
    engine = create_engine(f"sqlite:///{database_file}")
    Base.metadata.create_all(engine)
    cookies: dict[str, str] = {}
    with Session(engine) as session:
        for ecosystem_id, name, visibility, created in ECOSYSTEMS:
            session.add(Ecosystem(id=ecosystem_id, name=name, status="active", visibility=visibility,
                                  created_at=created, updated_at=created))
            session.flush()
        session.add(AppSetting(key=PLATFORM_HOME_SETTING_KEY, value={"ecosystem_id": str(OMNIONE)}))
        session.add(Domain(id=RIVER_DOMAIN, ecosystem_id=RIVERBANK, domain_id="DOM-RIVER", status="active"))
        session.add(Agreement(
            id=UAF, ecosystem_id=OMNIONE, agreement_id="AGR-UAF", type="uaf", title="Universal Agreement Field",
            version="1.0", status="active", proposer="Lani", text="Every member consents before taking part.",
            requires_explicit_consent=True, prerequisite_scopes=["ecosystem"],
        ))
        session.flush()
        session.add(AgreementRequirement(id=uuid.uuid4(), agreement_id=UAF, target_kind="ecosystem_membership",
                                         target_id=None, enforcement="block_join", is_active=True))
        for name, rows in PEOPLE.items():
            session.add(User(id=_user_id(name), display_name=name.title(), username=name))
            session.flush()
            if name == "lani":
                session.add(NodeAdmin(user_id=_user_id(name), active=True))
            for ecosystem_id, status, role, profile in rows:
                session.add(Member(
                    id=_row_id(name, ecosystem_id), ecosystem_id=ecosystem_id, user_id=_user_id(name),
                    member_id=f"MEM-{name}-{ecosystem_id.int}", display_name=name.title(), current_status=status,
                    role=role, profile=profile, created_at=datetime(2026, 3, 1), updated_at=datetime(2026, 3, 1),
                ))
            session_id = uuid.uuid4()
            session.add(AuthSession(id=session_id, user_id=_user_id(name),
                                    expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
            cookies[name] = make_session_cookie(str(session_id), SECRET)
        session.flush()
        # The founder holds both cross-links, as the backfill would. Quiz creation stays steward-gated while an admin is active.
        fern = _row_id("fern", RIVERBANK)
        for designation in ("internal", "external"):
            session.add(EcosystemAdmin(
                id=uuid.uuid5(fern, designation), ecosystem_id=RIVERBANK, member_id=fern,
                designation=designation, appointed_by_member_id=fern,
            ))
        session.add(AgreementMemberConsent(  # Olga consented to the home's membership agreement before leaving
            id=uuid.uuid4(), agreement_id=UAF, member_id=_row_id("olga", OMNIONE), agreement_version="1.0",
            attestation="I consent to the Universal Agreement Field", attested_at=datetime(2026, 3, 2),
        ))
        session.add(SharesNeeds(
            id=uuid.uuid4(), ecosystem_id=RIVERBANK, domain_id=RIVER_DOMAIN, author_member_id=_row_id("rhea", RIVERBANK),
            type="need", title="Seeking a grant writer", visibility="public", status="active",
        ))
        session.commit()
    engine.dispose()

    database_url = f"sqlite+aiosqlite:///{database_file}"
    app = create_app(settings=Settings(
        _env_file=None, DATABASE_URL=database_url, SESSION_SECRET=SECRET, SIGNUP_DEFAULT_ECOSYSTEM_SLUG="",
        PLATFORM_HOME_ECOSYSTEM_ID="", NEOS_CORE_PATH=str(tmp_path_factory.mktemp("no-skills")), CORS_ORIGINS="*",
        LOG_LEVEL="info",
    ))
    app.config.HTTP_AUTO_HEAD = False  # sanic-ext's automatic routes cost ~20 s per fresh app and play no part here
    app.config.HTTP_AUTO_OPTIONS = False
    app.config.CORS = False
    return SimpleNamespace(app=app, database_url=database_url, cookies=cookies)


@pytest_asyncio.fixture
async def db(boundaries):
    engine = create_async_engine(boundaries.database_url)
    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await engine.dispose()


async def _call(boundaries, actor: str, method: str, path: str, body: dict | None = None, *, cookies: dict | None = None):
    headers = {"cookie": f"neos_session={boundaries.cookies[actor]}"} if actor != "anon" else {}
    kwargs = {"headers": headers} if body is None else {"headers": headers, "json": body}
    if cookies:
        kwargs["cookies"] = cookies
    _, response = await getattr(boundaries.app.asgi_client, method)(path, **kwargs)
    return response


async def _read(db, statement):
    async with db() as session:
        return await session.scalar(statement)


async def _put_setting(boundaries, db, actor: str) -> tuple[int, bool]:
    key, value = "ctc_map", {"test_marker": uuid.uuid4().hex}
    response = await _call(boundaries, actor, "put", "/api/v1/settings", {"key": key, "value": value})
    return response.status, await _read(db, select(AppSetting.value).where(AppSetting.key == key)) == value


# --- A1 + F4: a member who leaves comes back as a fresh member --------------------------------------------------


async def test_a_home_owner_who_leaves_comes_back_as_a_member_who_consents_again(boundaries, db):
    olga = _row_id("olga", OMNIONE)
    assert (await _call(boundaries, "olga", "get", "/api/v1/auth/me")).json["is_platform_admin"] is False
    async with db() as session:
        session.add(NodeAdmin(user_id=_user_id("olga"), active=True))
        await session.commit()
    assert (await _call(boundaries, "olga", "get", "/api/v1/auth/me")).json["is_platform_admin"] is True

    filed = await _call(boundaries, "olga", "post", "/api/v1/exit/",
                        {"ecosystem_id": str(OMNIONE), "exit_type": "standard", "reason": "Moving on"})
    assert filed.status == 201, filed.text
    done = await _call(boundaries, "sami", "post", f"/api/v1/exit/{filed.json['id']}/status", {"new_status": "completed"})
    assert done.status == 200, done.text
    async with db() as session:
        row = await session.get(Member, olga)
        consent = await session.scalar(select(AgreementMemberConsent).where(AgreementMemberConsent.member_id == olga))
    assert (row.current_status, row.role, row.profile) == ("exited", "user", None)
    assert consent.withdrawn_at is not None and consent.withdrawal_reason.startswith("Membership ended")
    assert (await _call(boundaries, "olga", "get", "/api/v1/auth/me")).json["is_node_admin"] is True

    # Membership re-entry loses local standing; the separately assigned global role remains.
    back = await _call(boundaries, "olga", "post", f"/api/v1/ecosystems/{OMNIONE}/join")
    assert back.status == 200, back.text
    assert (back.json["outcome"], back.json["membership_status"], [a["title"] for a in back.json["required_agreements"]]) == (
        "re_entry", "pending_consent", ["Universal Agreement Field"])
    assert (await _call(boundaries, "olga", "get", "/api/v1/auth/me")).json["is_platform_admin"] is True
    assert await _put_setting(boundaries, db, "olga") == (200, True)

    consented = await _call(boundaries, "olga", "post", f"/api/v1/agreements/{UAF}/consent",
                            {"attestation": "I consent to the Universal Agreement Field again"})
    assert consented.status == 201, consented.text
    async with db() as session:
        row = await session.get(Member, olga)
    assert (row.current_status, row.role, row.profile) == ("active", "user", None)
    assert (await _call(boundaries, "olga", "get", "/api/v1/auth/me")).json["is_platform_admin"] is True
    assert await _put_setting(boundaries, db, "olga") == (200, True)
    async with db() as session:
        assert (await session.get(NodeAdmin, _user_id("olga"))).active is True

    # The member page shows what leaving changed, and which steward's confirmation did it.
    profile = await _call(boundaries, "sami", "get", f"/api/v1/members/{olga}/profile")
    assert profile.status == 200, profile.text
    assert sorted((g["kind"], g["from_role"], g["to_role"], g["granted_by"]) for g in profile.json["role_history"]) == [
        ("profile", "co_creator", "", "Sami"), ("role", "owner", "user", "Sami")]
    async with db() as session:
        statuses = (await session.execute(select(MemberStatusTransition.from_status, MemberStatusTransition.to_status,
                                                 MemberStatusTransition.trigger).where(
            MemberStatusTransition.member_id == olga, MemberStatusTransition.trigger.in_(
                ("exit_completed", "re_entry", "consent"))))).all()
    assert sorted(statuses) == sorted([("active", "exited", "exit_completed"), ("exited", "pending_consent", "re_entry"),
                                       ("pending_consent", "active", "consent")])


# --- A2: quizzes and their results belong to the quiz's ecosystem's stewards ------------------------------------


async def _quiz(db, *, ecosystem_id=RIVERBANK, domain_id=None) -> uuid.UUID:
    """A fresh quiz with one result (Rudy's), so a read discloses and a delete removes something."""
    quiz_id = uuid.uuid4()
    async with db() as session:
        session.add(Quiz(id=quiz_id, title=f"Quiz {quiz_id.hex[:6]}", ecosystem_id=ecosystem_id, domain_id=domain_id,
                         passing_score=60, is_published=True, is_entry_quiz=False))
        await session.flush()
        session.add(QuizResult(id=uuid.uuid4(), quiz_id=quiz_id, member_id=_row_id("rudy", RIVERBANK), score=91,
                               is_passed=True, completed_at=datetime.now(timezone.utc).replace(tzinfo=None)))  # newest first
        await session.commit()
    return quiz_id


async def _snapshot(db, quiz_id: uuid.UUID) -> tuple:
    async with db() as session:
        quiz = await session.get(Quiz, quiz_id)
        results = await session.scalar(select(func.count()).select_from(QuizResult).where(QuizResult.quiz_id == quiz_id))
    return (quiz and (quiz.title, quiz.passing_score, quiz.ecosystem_id, quiz.domain_id), results)


def create_quiz(ecosystem_id):
    async def act(db, call):
        title = f"New quiz {uuid.uuid4().hex[:6]}"
        body = {"title": title, **({"ecosystem_id": str(ecosystem_id)} if ecosystem_id else {})}
        response = await call("post", "/api/v1/quizzes", body)
        return response.status, await _read(db, select(Quiz.id).where(Quiz.title == title)) is not None, None
    return act


def update_quiz(ecosystem_id):
    async def act(db, call):
        quiz_id = await _quiz(db, ecosystem_id=ecosystem_id)
        before = await _snapshot(db, quiz_id)
        response = await call("put", f"/api/v1/quizzes/{quiz_id}", {"passing_score": 100})
        return response.status, (await _snapshot(db, quiz_id)) != before, ((await _snapshot(db, quiz_id)), before)
    return act


async def delete_quiz(db, call):
    quiz_id = await _quiz(db)
    before = await _snapshot(db, quiz_id)
    response = await call("delete", f"/api/v1/quizzes/{quiz_id}")
    return response.status, (await _snapshot(db, quiz_id)) == (None, 0), ((await _snapshot(db, quiz_id)), before)


def read_results(path: str):
    async def act(db, call):
        quiz_id = await _quiz(db)
        response = await call("get", f"/api/v1/quizzes/{quiz_id}/{path}")
        return response.status, str(_row_id("rudy", RIVERBANK)) in response.text, None
    return act


async def assign_to_domain(db, call):
    quiz_id = await _quiz(db)
    before = await _snapshot(db, quiz_id)
    response = await call("post", f"/api/v1/domains/{RIVER_DOMAIN}/quizzes/assign", {"quiz_id": str(quiz_id)})
    return response.status, (await _snapshot(db, quiz_id)) != before, ((await _snapshot(db, quiz_id)), before)


async def unassign_from_domain(db, call):
    quiz_id = await _quiz(db, domain_id=RIVER_DOMAIN)
    before = await _snapshot(db, quiz_id)
    response = await call("post", f"/api/v1/domains/{RIVER_DOMAIN}/quizzes/unassign", {"quiz_id": str(quiz_id)})
    return response.status, (await _snapshot(db, quiz_id)) != before, ((await _snapshot(db, quiz_id)), before)


async def member_quiz_history(db, call):
    quiz_id = await _quiz(db)
    response = await call("get", f"/api/v1/members/{_row_id('rudy', RIVERBANK)}/quiz-history?per_page=100")
    return response.status, str(quiz_id) in response.text, None


# Columns follow ACTORS: anon, rudy (Riverbank member), sami (steward of OmniOne only), rhea (Riverbank mod),
# fern (Riverbank's founder: role user, co_creator there), lani (platform admin, no Riverbank row).
# 404 = the domain or member is outside the caller's active ecosystems.
QUIZ_TABLE = [
    ("POST /quizzes in Riverbank", create_quiz(RIVERBANK), (401, 403, 403, 201, 201, 403)),
    ("PUT /quizzes/:riverbank", update_quiz(RIVERBANK), (401, 403, 403, 200, 200, 403)),
    ("DELETE /quizzes/:riverbank", delete_quiz, (401, 403, 403, 200, 200, 403)),
    ("GET /quizzes/:riverbank/results/all", read_results("results/all"), (401, 403, 403, 200, 200, 403)),
    ("GET /quizzes/:riverbank/results", read_results("results"), (401, 403, 403, 200, 200, 403)),
    ("POST /domains/:river/quizzes/assign", assign_to_domain, (401, 403, 404, 200, 200, 404)),
    ("POST /domains/:river/quizzes/unassign", unassign_from_domain, (401, 403, 404, 200, 200, 404)),
    ("GET /members/:rudy/quiz-history", member_quiz_history, (401, 200, 404, 200, 200, 404)),
    # A quiz shared by every ecosystem: explicit global NodeAdmins only.
    ("POST /quizzes (shared)", create_quiz(None), (401, 403, 403, 403, 403, 201)),
    ("PUT /quizzes/:shared", update_quiz(None), (401, 403, 403, 403, 403, 200)),
]


@pytest.mark.parametrize("actor, act, expected", [
    pytest.param(actor, act, statuses[column], id=f"{route} as {actor}")
    for route, act, statuses in QUIZ_TABLE for column, actor in enumerate(ACTORS)
])
async def test_only_the_quizs_stewards_change_it_or_read_its_results(boundaries, db, actor, act, expected):
    status, took_effect, rows = await act(db, functools.partial(_call, boundaries, actor))
    assert status == expected
    assert took_effect is (expected in (200, 201)), rows  # a refusal leaves the quiz and its results as they were


async def test_a_shared_quiz_stays_shared_when_an_ecosystem_or_domain_takes_it_up(boundaries, db):
    shared = await _quiz(db, ecosystem_id=None)
    assigned = await _call(boundaries, "rhea", "post", f"/api/v1/ecosystems/{RIVERBANK}/quizzes/assign",
                           {"quiz_id": str(shared), "is_entry_quiz": True})
    into_domain = await _call(boundaries, "fern", "post", f"/api/v1/domains/{RIVER_DOMAIN}/quizzes/assign",
                              {"quiz_id": str(shared)})
    assert (assigned.status, into_domain.status) == (200, 200), (assigned.text, into_domain.text)
    async with db() as session:
        original = await session.get(Quiz, shared)
        entry_copy = await session.get(Quiz, uuid.UUID(assigned.json["quiz_id"]))
        domain_copy = await session.get(Quiz, uuid.UUID(into_domain.json["quiz_id"]))
    assert (original.ecosystem_id, original.domain_id, original.is_entry_quiz) == (None, None, False)
    assert (entry_copy.ecosystem_id, entry_copy.is_entry_quiz, entry_copy.title) == (RIVERBANK, True, original.title)
    assert (domain_copy.ecosystem_id, domain_copy.domain_id) == (RIVERBANK, RIVER_DOMAIN)
    assert len({shared, entry_copy.id, domain_copy.id}) == 3


# --- A3: every sign-in places through place_member, preferring the pinned home ----------------------------------


@contextlib.asynccontextmanager
async def _unpinned(db):
    """Drop the home pin for one test, then put it back (the database is module-wide)."""
    async with db() as session:
        await session.execute(delete(AppSetting).where(AppSetting.key == PLATFORM_HOME_SETTING_KEY))
        await session.commit()
    try:
        yield
    finally:
        async with db() as session:
            session.add(AppSetting(key=PLATFORM_HOME_SETTING_KEY, value={"ecosystem_id": str(OMNIONE)}))
            await session.commit()


async def _did_login(boundaries) -> str:
    from nacl.signing import SigningKey

    from neos_agent.auth.did import public_bytes_to_did_key

    key = SigningKey.generate()
    did = public_bytes_to_did_key(bytes(key.verify_key))
    _, challenge = await boundaries.app.asgi_client.post("/auth/challenge", json={"did": did})
    assert challenge.status == 200, challenge.text
    signature = key.sign(challenge.json["challenge"].encode("utf-8")).signature.hex()
    _, verified = await boundaries.app.asgi_client.post("/auth/verify", json={
        "did": did, "challenge": challenge.json["challenge"], "signature": signature, "display_name": "Stranger"})
    assert verified.status == 200, verified.text
    assert verified.json["status"] == "consent_required"
    return did


async def _placements(db, criterion) -> list[tuple]:
    async with db() as session:
        rows = (await session.execute(select(Member).join(User, User.id == Member.user_id).where(criterion))).scalars().all()
        moves = {row.id: (await session.execute(select(MemberStatusTransition.trigger).where(
            MemberStatusTransition.member_id == row.id))).scalars().all() for row in rows}
    return [(row.ecosystem_id, row.current_status, moves[row.id]) for row in rows]


async def test_the_legacy_did_login_waits_on_consent_in_the_pinned_home_never_a_private_ecosystem(boundaries, db):
    did = await _did_login(boundaries)
    assert await _placements(db, User.did == did) == [(OMNIONE, "pending_consent", ["signup"])]
    async with _unpinned(db):  # no pin, no slug: the oldest PUBLIC ecosystem, never the older private one
        did = await _did_login(boundaries)
    assert await _placements(db, User.did == did) == [(OMNIONE, "pending_consent", ["signup"])]


async def test_sign_up_prefers_the_pinned_home_over_the_configured_slug(boundaries, db, monkeypatch):
    monkeypatch.setattr(boundaries.app.ctx.settings, "SIGNUP_DEFAULT_ECOSYSTEM_SLUG", "riverbank")
    _, pinned = await boundaries.app.asgi_client.post("/api/v1/auth/register", json={
        "username": "pinned_newcomer", "password": "correct-horse-1"})
    assert pinned.status == 200, pinned.text
    assert await _placements(db, User.username == "pinned_newcomer") == [(OMNIONE, "pending_consent", ["signup"])]
    monkeypatch.setattr(boundaries.app.ctx.settings, "SIGNUP_DEFAULT_ECOSYSTEM_SLUG", "")
    async with _unpinned(db):
        _, oldest = await boundaries.app.asgi_client.post("/api/v1/auth/register", json={
            "username": "unpinned_newcomer", "password": "correct-horse-1"})
    assert oldest.status == 200, oldest.text
    assert await _placements(db, User.username == "unpinned_newcomer") == [(OMNIONE, "pending_consent", ["signup"])]


# --- A6: a signed-out visitor sees no posts and no private memberships on a profile -----------------------------


@pytest.mark.parametrize("viewer, sees_post, sees_hidden", [
    ("anon", False, False),  # owner default: signed-out visitors see no posts
    ("rudy", True, False),  # a member elsewhere: the public post, not the private ecosystem
    ("hal", True, True),  # a member of Hidden Grove knows it exists
    ("rhea", True, True),  # her own profile
])
async def test_a_profile_shows_posts_only_to_the_signed_in_and_private_memberships_only_to_members(
    boundaries, viewer, sees_post, sees_hidden,
):
    response = await _call(boundaries, viewer, "get", f"/api/v1/profiles/{_user_id('rhea')}")
    assert response.status == 200, response.text
    assert ([p["title"] for p in response.json["publications"]] == ["Seeking a grant writer"]) is sees_post
    names = [ecosystem["name"] for ecosystem in response.json["ecosystems"]]
    assert ("Riverbank" in names, "Hidden Grove" in names) == (True, sees_hidden)
    assert ("Hidden Grove" in response.text) is sees_hidden


# Domain quiz results (coordinator fix)


async def test_domain_quiz_results_show_a_steward_everyones_and_a_member_only_their_own(boundaries, db):
    quiz_id = await _quiz(db, domain_id=RIVER_DOMAIN)  # carries Rudy's result
    async with db() as session:
        session.add(QuizResult(id=uuid.uuid4(), quiz_id=quiz_id, member_id=_row_id("fern", RIVERBANK), score=40,
                               is_passed=False, completed_at=datetime(2026, 4, 1)))
        await session.commit()
    rudy, fern = str(_row_id("rudy", RIVERBANK)), str(_row_id("fern", RIVERBANK))
    path = f"/api/v1/domains/{RIVER_DOMAIN}/quiz-results"

    steward = await _call(boundaries, "rhea", "get", path)
    assert steward.status == 200, steward.text
    assert {i["member_id"]: i["member_name"] for i in steward.json["items"] if i["quiz_id"] == str(quiz_id)} == {
        rudy: "Rudy", fern: "Fern"}
    by_member = {i["member_id"]: i for i in steward.json["items"] if i["quiz_id"] == str(quiz_id)}
    assert (by_member[rudy]["passed"], by_member[fern]["passed"]) == (True, False)
    assert by_member[fern]["created_at"].startswith("2026-04-01")

    member = await _call(boundaries, "rudy", "get", path)
    assert member.status == 200, member.text
    assert {i["member_id"] for i in member.json["items"]} == {rudy}

    # A caller with no row in Riverbank (sami: OmniOne only) gets 404 here: the domain is not visible to them.
    outsider = await _call(boundaries, "sami", "get", path)
    assert outsider.status == 404, outsider.text
