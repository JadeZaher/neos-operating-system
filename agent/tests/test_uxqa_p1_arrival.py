"""UXQA pass 01 (first week) arrival flows driven through the public HTTP seam.

Covers: deterministic sign-up placement (register, DID, OAuth), placement when a
seed gives every ecosystem one created_at, the agreement-consent gate at
sign-up and on /auth/me, JSON 404s for unknown API paths, and plain chat
failure copy. Rules: src/neos_agent/api/AGENTS.md "Sign-up placement and the
consent gate".
"""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import urlencode, urlsplit

import pytest
import pytest_asyncio
from sanic import Sanic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import neos_agent.db.course_models  # noqa: F401 — registers quizzes, which quiz_assignments references
from neos_agent.db.models import Agreement, AuthChallenge, Base, Ecosystem, Member, User
from neos_agent.services.agreement_consent import synchronize_agreement_requirements

# Insertion order differs from age on purpose: an unordered `LIMIT 1` returns Oasis.
OASIS_ID = uuid.UUID(int=1)
OMNIONE_ID = uuid.UUID(int=2)
THIRD_SPACE_ID = uuid.UUID(int=3)
SEEDED_ECOSYSTEMS = (
    (OASIS_ID, "Oasis", datetime(2026, 3, 1)),
    (OMNIONE_ID, "OmniOne", datetime(2026, 1, 1)),
    (THIRD_SPACE_ID, "Third Space", datetime(2026, 2, 1)),
)
SESSION_SECRET = "uxqa-arrival-secret-0123456789abcdef"
FRONTEND = "https://frontend.example.com"

# Like scripts/seed_omnione.py: one add_all + flush, so every created_at is equal.
# Oasis has the lowest id (the old tie-break winner); OmniOne was founded first.
SEED_CREATED_AT = datetime(2026, 10, 31, 12, 35, 13)
ESCHERBRIDGE_ID = uuid.UUID(int=4)
TIED_SEED = (
    (OASIS_ID, "Oasis", date(2026, 9, 1)),
    (OMNIONE_ID, "OmniOne", date(2026, 5, 4)),
    (ESCHERBRIDGE_ID, "Escherbridge", date(2026, 7, 3)),
    (THIRD_SPACE_ID, "Plan Systems", None),
)


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        for ecosystem_id, name, created_at in SEEDED_ECOSYSTEMS:
            session.add(Ecosystem(
                id=ecosystem_id, name=name, status="active",
                created_at=created_at, updated_at=created_at,
            ))
            await session.flush()
        await session.commit()
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def tied_session_factory():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        session.add_all([
            Ecosystem(
                id=ecosystem_id, name=name, status="active", founded_date=founded,
                created_at=SEED_CREATED_AT, updated_at=SEED_CREATED_AT,
            )
            for ecosystem_id, name, founded in TIED_SEED
        ])
        await session.commit()
    yield factory
    await engine.dispose()


def _auth_app(factory, default_slug: str = "") -> Sanic:
    app = Sanic(f"uxqa-arrival-{uuid.uuid4().hex[:8]}")
    app.ctx.settings = SimpleNamespace(
        SESSION_SECRET=SESSION_SECRET,
        SESSION_MAX_AGE_HOURS=24,
        SIGNUP_DEFAULT_ECOSYSTEM_SLUG=default_slug,
        OAUTH_REDIRECT_BASE="https://backend.example.com",
        FRONTEND_URL=FRONTEND,
        CORS_ORIGINS=FRONTEND,
        GOOGLE_CLIENT_ID="google-client-id",
        GOOGLE_CLIENT_SECRET="google-secret",
        LINKEDIN_CLIENT_ID="",
        LINKEDIN_CLIENT_SECRET="",
    )
    app.ctx.db = factory
    from neos_agent.api.auth import auth_api_bp
    from neos_agent.api.oauth import oauth_bp
    app.blueprint(auth_api_bp)
    app.blueprint(oauth_bp)
    return app


async def _gate_ecosystem(factory, ecosystem_id: uuid.UUID) -> str:
    """Give an ecosystem one active membership agreement that needs explicit consent."""
    async with factory() as session:
        agreement = Agreement(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            agreement_id=f"AGR-UAF-{ecosystem_id.int:03d}",
            type="uaf",
            title="Universal Agreement Field",
            version="1.0",
            status="active",
            proposer="Lani",
            affected_parties=["All members"],
            text="Every member consents before participating.",
            created_date=date(2026, 1, 2),
            requires_explicit_consent=True,
            prerequisite_scopes=["ecosystem"],
        )
        session.add(agreement)
        await session.flush()
        await synchronize_agreement_requirements(session, agreement)
        await session.commit()
        return str(agreement.id)


def _session_cookie(response) -> dict[str, str]:
    """The neos_session cookie a sign-in response set, ready to send back."""
    for header in response.headers.get_list("set-cookie"):
        if header.startswith("neos_session="):
            return {"neos_session": header.split(";", 1)[0].split("=", 1)[1]}
    raise AssertionError("no neos_session cookie set")


async def _register(app: Sanic, username: str, **extra):
    _, response = await app.asgi_client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "correct-horse-1", **extra},
    )
    return response


async def _memberships(factory, *, username: str | None = None, did: str | None = None) -> list[Member]:
    criterion = User.username == username if username is not None else User.did == did
    async with factory() as session:
        return list((await session.execute(
            select(Member).join(User, User.id == Member.user_id).where(criterion)
        )).scalars().all())


@pytest.mark.asyncio
@pytest.mark.parametrize(("default_slug", "expected_id"), [
    ("", OMNIONE_ID),               # unset -> oldest ecosystem, not the first row
    ("third-space", THIRD_SPACE_ID),  # configured slug of the ecosystem name
    ("Third Space", THIRD_SPACE_ID),  # the name itself slugs to the same value
    (str(THIRD_SPACE_ID), THIRD_SPACE_ID),  # an ecosystem id
    ("nowhere", OMNIONE_ID),        # unknown default falls back to the oldest
])
async def test_register_places_every_newcomer_in_the_same_deterministic_ecosystem(
    session_factory, default_slug, expected_id,
):
    app = _auth_app(session_factory, default_slug)

    for username in ("priya_first", "oren_second"):
        response = await _register(app, username)
        assert response.status == 200, response.text
        assert response.json["member"]["ecosystem_id"] == str(expected_id)
        assert [m.ecosystem_id for m in await _memberships(session_factory, username=username)] == [expected_id]


@pytest.mark.asyncio
async def test_register_honours_a_requested_ecosystem_and_refuses_unknown_ones(session_factory):
    app = _auth_app(session_factory, "third-space")

    response = await _register(app, "kofi_requested", ecosystem_id=str(OASIS_ID))
    assert response.status == 200, response.text
    assert [m.ecosystem_id for m in await _memberships(session_factory, username="kofi_requested")] == [OASIS_ID]

    for username, requested in (("sol_unknown", str(uuid.uuid4())), ("sol_malformed", "not-a-uuid")):
        response = await _register(app, username, ecosystem_id=requested)
        assert response.status == 404
        assert response.json == {"error": "Ecosystem not found"}
        async with session_factory() as session:
            assert await session.scalar(select(User.id).where(User.username == username)) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(("default_slug", "expected_id"), [
    ("omnione", OMNIONE_ID),          # the configured deployment value
    ("", OMNIONE_ID),                 # unset: founded_date breaks the created_at tie, not the id
    ("escherbridge", ESCHERBRIDGE_ID),  # configuration beats the tie-break
])
async def test_placement_is_intended_when_the_seed_shares_one_created_at(
    tied_session_factory, default_slug, expected_id,
):
    app = _auth_app(tied_session_factory, default_slug)

    response = await _register(app, "tied_newcomer")
    assert response.status == 200, response.text
    assert response.json["member"]["ecosystem_id"] == str(expected_id)


@pytest.mark.asyncio
async def test_register_applies_the_ecosystem_agreement_consent_gate(session_factory):
    agreement_id = await _gate_ecosystem(session_factory, OMNIONE_ID)
    app = _auth_app(session_factory)  # unset default -> OmniOne, which is gated

    gated = await _register(app, "newcomer_gated")
    assert gated.status == 200, gated.text
    assert gated.json["status"] == "consent_required"
    assert [a["id"] for a in gated.json["required_agreements"]] == [agreement_id]
    [member] = await _memberships(session_factory, username="newcomer_gated")
    assert (member.current_status, member.onboarding_status) == ("pending_consent", "agreement_consent_required")

    # The gate survives the sign-up response: /auth/me reports it on every load.
    _, me = await app.asgi_client.get("/api/v1/auth/me", cookies=_session_cookie(gated))
    assert me.status == 200, me.text
    assert me.json["member"]["current_status"] == "pending_consent"
    assert me.json["pending_consents"] == [{
        "ecosystem_id": str(OMNIONE_ID),
        "ecosystem_name": "OmniOne",
        "required_agreements": [{"id": agreement_id, "title": "Universal Agreement Field", "version": "1.0"}],
    }]

    open_join = await _register(app, "newcomer_open", ecosystem_id=str(THIRD_SPACE_ID))
    assert open_join.status == 200, open_join.text
    assert open_join.json["status"] == "joined"
    [member] = await _memberships(session_factory, username="newcomer_open")
    assert member.current_status == "active"
    _, me = await app.asgi_client.get("/api/v1/auth/me", cookies=_session_cookie(open_join))
    assert me.json["pending_consents"] == []


@pytest.mark.asyncio
async def test_oauth_newcomer_is_placed_gated_and_sent_to_the_consent_gate(tied_session_factory):
    from neos_agent.api.oauth import _create_oauth_state

    await _gate_ecosystem(tied_session_factory, OMNIONE_ID)

    async def oauth_sign_in(default_slug: str, oauth_id: str):
        state = _create_oauth_state("google", FRONTEND, SESSION_SECRET)
        app = _auth_app(tied_session_factory, default_slug)
        google_user = {"id": oauth_id, "name": "Priya", "email": f"{oauth_id}@example.com", "picture": None}
        with patch("neos_agent.api.oauth._exchange_google_code", new=AsyncMock(return_value=google_user)):
            _, response = await app.asgi_client.get(
                f"/api/v1/auth/oauth/google/callback?{urlencode({'code': 'auth-code', 'state': state})}",
                cookies={"neos_oauth_transaction": state},
                follow_redirects=False,
            )
        return response

    async def memberships(oauth_id: str) -> list[Member]:
        async with tied_session_factory() as session:
            return list((await session.execute(
                select(Member).join(User, User.id == Member.user_id).where(User.oauth_id == oauth_id)
            )).scalars().all())

    gated = await oauth_sign_in("", "google-gated-1")  # unset -> OmniOne by founded_date, which is gated
    assert gated.status == 302
    assert urlsplit(gated.headers["location"]).path == "/welcome/consent"
    [member] = await memberships("google-gated-1")
    assert (member.ecosystem_id, member.current_status) == (OMNIONE_ID, "pending_consent")

    # A returning OAuth user keeps that membership whatever the default says now.
    returning = await oauth_sign_in("escherbridge", "google-gated-1")
    assert returning.status == 302
    assert [m.ecosystem_id for m in await memberships("google-gated-1")] == [OMNIONE_ID]

    open_join = await oauth_sign_in("escherbridge", "google-open-2")
    assert urlsplit(open_join.headers["location"]).path == "/dashboard"
    [member] = await memberships("google-open-2")
    assert (member.ecosystem_id, member.current_status) == (ESCHERBRIDGE_ID, "active")


@pytest.mark.asyncio
async def test_did_sign_in_places_a_new_identity_once_and_never_re_enrolls_it(session_factory):
    did = "did:key:z6MkUxqaArrivalNewcomer000000000000000000"

    async def sign_in(default_slug: str):
        challenge = uuid.uuid4().hex
        async with session_factory() as session:
            session.add(AuthChallenge(
                did=did, challenge=challenge, used=False,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            ))
            await session.commit()
        app = _auth_app(session_factory, default_slug)
        with patch("neos_agent.api.auth.verify_did_signature", return_value=True):
            _, response = await app.asgi_client.post(
                "/api/v1/auth/verify",
                json={"did": did, "challenge": challenge, "signature": "signed"},
            )
        return response

    first = await sign_in("third-space")
    assert first.status == 200, first.text
    assert [m.ecosystem_id for m in await _memberships(session_factory, did=did)] == [THIRD_SPACE_ID]

    returning = await sign_in("oasis")
    assert returning.status == 200, returning.text
    assert returning.json["member"]["ecosystem_id"] == str(THIRD_SPACE_ID)
    assert [m.ecosystem_id for m in await _memberships(session_factory, did=did)] == [THIRD_SPACE_ID]


@pytest.mark.asyncio
async def test_unknown_api_path_is_a_json_404_while_browser_paths_still_redirect():
    from neos_agent.config import Settings
    from neos_agent.main import create_app

    values = {"DATABASE_URL": "sqlite+aiosqlite://", "CORS_ORIGINS": "*", "LOG_LEVEL": "info"}
    with patch.dict(os.environ, values, clear=False):
        app = create_app(settings=Settings(**values))

    _, api_response = await app.asgi_client.get("/api/v1/auth/no-such-endpoint", follow_redirects=False)
    assert api_response.status == 404
    assert api_response.json == {"error": "Not found"}

    _, page_response = await app.asgi_client.get("/auth/no-such-page", follow_redirects=False)
    assert page_response.status == 302
    assert page_response.headers["location"] == "/dashboard"


@pytest.mark.asyncio
async def test_chat_provider_failure_reaches_the_member_as_plain_copy():
    app = Sanic(f"uxqa-chat-{uuid.uuid4().hex[:8]}")
    from neos_agent.api.chat import chat_api_bp
    app.blueprint(chat_api_bp)

    @app.on_request
    async def signed_in(request):
        request.ctx.member = SimpleNamespace(
            id=uuid.uuid4(), display_name="Kofi", ecosystem=None, ecosystem_id=None,
        )

    provider_error = RuntimeError(
        "litellm.AuthenticationError: OpenrouterException - key sk-or-v1-abc123 rejected",
    )
    with patch("neos_agent.api.chat.is_ai_enabled", return_value=True), \
         patch("neos_agent.api.chat.acompletion", new=AsyncMock(side_effect=provider_error)):
        _, response = await app.asgi_client.post("/api/v1/chat/send", json={"message": "What is ACT?"})

    assert response.status == 200
    assert "The assistant is unavailable right now. Please try again later." in response.text
    assert "OpenrouterException" not in response.text
    assert "sk-or-v1" not in response.text
