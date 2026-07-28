"""Tests for OAuth authentication flow.

Verifies the full OAuth callback → cookie → /auth/me chain,
isolating the exact point where cookie-based auth breaks
on redirect responses vs. JSON responses.
"""

from __future__ import annotations

import uuid
from datetime import date
from urllib.parse import parse_qs, urlencode, urlsplit
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sanic import Sanic
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import Base, Ecosystem, Member, User, AuthSession
from neos_agent.auth.middleware import make_session_cookie, verify_session_cookie

# ---------------------------------------------------------------------------
# Stable UUIDs
# ---------------------------------------------------------------------------
ECOSYSTEM_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
SESSION_SECRET = "test-secret-for-oauth-flow-1234567890abcdef"
ALTERNATE_FRONTEND_ORIGIN = "https://neos.primusneo.com"
OAUTH_TRANSACTION_COOKIE = "neos_oauth_transaction"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _setup_db():
    """Create in-memory SQLite with schema + ecosystem."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with sf() as session:
        session.add(Ecosystem(
            id=ECOSYSTEM_ID, name="TestEco",
            description="Test", status="active",
        ))
        await session.commit()
    return engine, sf


def _create_app(db_session_factory):
    """Create a Sanic app with OAuth + auth blueprints for testing."""
    app = Sanic(f"test-oauth-{uuid.uuid4().hex[:8]}")

    settings = MagicMock()
    settings.SESSION_SECRET = SESSION_SECRET
    settings.SESSION_MAX_AGE_HOURS = 24
    settings.OAUTH_REDIRECT_BASE = "https://backend.example.com"
    settings.FRONTEND_URL = "https://frontend.example.com"
    settings.GOOGLE_CLIENT_ID = "google-client-id"
    settings.GOOGLE_CLIENT_SECRET = "google-secret"
    settings.LINKEDIN_CLIENT_ID = "linkedin-client-id"
    settings.LINKEDIN_CLIENT_SECRET = "linkedin-secret"
    settings.CORS_ORIGINS = (
        "https://frontend.example.com,"
        f"{ALTERNATE_FRONTEND_ORIGIN}"
    )
    app.ctx.settings = settings
    app.ctx.db = db_session_factory

    from neos_agent.api.oauth import oauth_bp
    from neos_agent.api.auth import auth_api_bp
    app.blueprint(oauth_bp)
    app.blueprint(auth_api_bp)

    return app


def _bound_callback(
    provider: str,
    *,
    frontend_origin: str = "https://frontend.example.com",
    **params: str,
) -> tuple[str, dict[str, str]]:
    """Build a callback URL and its matching browser transaction cookie."""
    from neos_agent.api.oauth import _create_oauth_state

    state = _create_oauth_state(
        provider,
        frontend_origin,
        SESSION_SECRET,
    )
    query = urlencode({**params, "state": state})
    path = f"/api/v1/auth/oauth/{provider}/callback?{query}"
    return path, {OAUTH_TRANSACTION_COOKIE: state}


def _cookie_header(response, name: str) -> str:
    """Return one Set-Cookie header by cookie name."""
    return next(
        (
            header
            for header in response.headers.get_list("set-cookie")
            if header.startswith(f"{name}=")
        ),
        "",
    )


def _assert_transaction_cookie_cleared(response) -> None:
    """Verify the browser-bound transaction was consumed."""
    header = _cookie_header(response, OAUTH_TRANSACTION_COOKIE).lower()
    assert "max-age=0" in header
    assert "path=/api/v1/auth/oauth" in header


# ---------------------------------------------------------------------------
# Unit tests: cookie signing round-trip
# ---------------------------------------------------------------------------
class TestCookieSigning:
    """Verify make/verify cookie helpers work correctly."""

    def test_round_trip(self):
        sid = str(uuid.uuid4())
        cookie = make_session_cookie(sid, SESSION_SECRET)
        assert verify_session_cookie(cookie, SESSION_SECRET) == sid

    def test_wrong_secret_fails(self):
        sid = str(uuid.uuid4())
        cookie = make_session_cookie(sid, SESSION_SECRET)
        assert verify_session_cookie(cookie, "wrong-secret") is None

    def test_tampered_cookie_fails(self):
        sid = str(uuid.uuid4())
        cookie = make_session_cookie(sid, SESSION_SECRET)
        tampered = cookie[:-4] + "XXXX"
        assert verify_session_cookie(tampered, SESSION_SECRET) is None

    def test_malformed_cookie_fails(self):
        assert verify_session_cookie("no-colon-here", SESSION_SECRET) is None
        assert verify_session_cookie("", SESSION_SECRET) is None


# ---------------------------------------------------------------------------
# OAuth destination state
# ---------------------------------------------------------------------------
def test_oauth_state_validates_provider_expiry_and_signature():
    """State is provider-bound, short-lived, and tamper resistant."""
    from neos_agent.api.oauth import _create_oauth_state, _verify_oauth_state

    settings = MagicMock()
    settings.SESSION_SECRET = SESSION_SECRET
    settings.FRONTEND_URL = "https://frontend.example.com"
    settings.CORS_ORIGINS = (
        "https://frontend.example.com,"
        f"{ALTERNATE_FRONTEND_ORIGIN}"
    )
    state = _create_oauth_state(
        "google",
        ALTERNATE_FRONTEND_ORIGIN,
        SESSION_SECRET,
        now=1_000,
    )

    assert (
        _verify_oauth_state(state, "google", settings, now=1_001)
        == ALTERNATE_FRONTEND_ORIGIN
    )
    assert _verify_oauth_state(state, "linkedin", settings, now=1_001) is None
    assert _verify_oauth_state(state, "google", settings, now=1_600) is None

    payload, signature = state.split(".", 1)
    tampered_state = f"A{payload[1:]}.{signature}"
    assert (
        _verify_oauth_state(tampered_state, "google", settings, now=1_001)
        is None
    )


@pytest.mark.asyncio
async def test_oauth_initiate_accepts_allowed_origin_and_embeds_signed_state():
    """The second configured frontend receives a state-bound provider URL."""
    from neos_agent.api.oauth import _verify_oauth_state

    engine, sf = await _setup_db()
    app = _create_app(sf)
    query = urlencode({"origin": ALTERNATE_FRONTEND_ORIGIN})

    _, response = await app.asgi_client.get(
        f"/api/v1/auth/oauth/google?{query}",
    )

    assert response.status_code == 200
    provider_query = parse_qs(urlsplit(response.json["url"]).query)
    assert provider_query["redirect_uri"] == [
        "https://backend.example.com/api/v1/auth/oauth/google/callback"
    ]
    assert (
        _verify_oauth_state(
            provider_query["state"][0],
            "google",
            app.ctx.settings,
        )
        == ALTERNATE_FRONTEND_ORIGIN
    )
    transaction_cookie = _cookie_header(response, OAUTH_TRANSACTION_COOKIE)
    assert transaction_cookie.startswith(
        f"{OAUTH_TRANSACTION_COOKIE}={provider_query['state'][0]}"
    )
    transaction_cookie_lower = transaction_cookie.lower()
    assert "httponly" in transaction_cookie_lower
    assert "secure" in transaction_cookie_lower
    assert "samesite=none" in transaction_cookie_lower
    assert "max-age=600" in transaction_cookie_lower
    assert "path=/api/v1/auth/oauth" in transaction_cookie_lower

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_initiate_rejects_disallowed_origin():
    """An arbitrary origin cannot become an OAuth callback destination."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    query = urlencode({"origin": "https://attacker.example.com"})

    _, response = await app.asgi_client.get(
        f"/api/v1/auth/oauth/google?{query}",
    )

    assert response.status_code == 400
    assert response.json["error"] == "Frontend origin is not allowed"

    await engine.dispose()


# ---------------------------------------------------------------------------
# Integration tests: OAuth callback response
# ---------------------------------------------------------------------------
FAKE_GOOGLE_USER = {
    "id": "google-12345",
    "name": "Test User",
    "email": "test@example.com",
    "picture": "https://example.com/photo.jpg",
}

FAKE_LINKEDIN_USER = {
    "id": "linkedin-67890",
    "name": "LinkedIn User",
    "email": "linkedin@example.com",
    "picture": "https://example.com/li-photo.jpg",
}


@pytest.mark.asyncio
async def test_oauth_callback_redirects_to_state_frontend():
    """A valid state selects the initiating frontend after authentication."""
    from neos_agent.api.oauth import _create_oauth_state

    engine, sf = await _setup_db()
    app = _create_app(sf)
    state = _create_oauth_state(
        "google",
        ALTERNATE_FRONTEND_ORIGIN,
        SESSION_SECRET,
    )
    query = urlencode({"code": "test-auth-code", "state": state})

    with patch(
        "neos_agent.api.oauth._exchange_google_code",
        new_callable=AsyncMock,
    ) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, response = await app.asgi_client.get(
            f"/api/v1/auth/oauth/google/callback?{query}",
            cookies={OAUTH_TRANSACTION_COOKIE: state},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert (
        response.headers.get("location")
        == f"{ALTERNATE_FRONTEND_ORIGIN}/dashboard"
    )
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_rejects_invalid_state_before_exchange():
    """Invalid state fails closed to the configured fallback frontend."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    query = urlencode({"code": "test-auth-code", "state": "invalid.state"})

    with patch(
        "neos_agent.api.oauth._exchange_google_code",
        new_callable=AsyncMock,
    ) as mock_exchange:
        _, response = await app.asgi_client.get(
            f"/api/v1/auth/oauth/google/callback?{query}",
            cookies={OAUTH_TRANSACTION_COOKIE: "invalid.state"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers.get("location") == (
        "https://frontend.example.com/login?error=oauth_state_invalid"
    )
    mock_exchange.assert_not_awaited()
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_rejects_missing_state():
    """A callback cannot use the browser cookie without the state query."""
    from neos_agent.api.oauth import _create_oauth_state

    engine, sf = await _setup_db()
    app = _create_app(sf)
    cookie_state = _create_oauth_state(
        "google",
        "https://frontend.example.com",
        SESSION_SECRET,
    )

    with patch(
        "neos_agent.api.oauth._exchange_google_code",
        new_callable=AsyncMock,
    ) as mock_exchange:
        _, response = await app.asgi_client.get(
            "/api/v1/auth/oauth/google/callback?code=test-auth-code",
            cookies={OAUTH_TRANSACTION_COOKIE: cookie_state},
            follow_redirects=False,
        )

    assert response.headers.get("location") == (
        "https://frontend.example.com/login?error=oauth_state_invalid"
    )
    mock_exchange.assert_not_awaited()
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_rejects_state_from_another_browser():
    """A valid state is insufficient without its initiating browser cookie."""
    callback_path, _ = _bound_callback(
        "google",
        code="test-auth-code",
    )
    engine, sf = await _setup_db()
    app = _create_app(sf)

    with patch(
        "neos_agent.api.oauth._exchange_google_code",
        new_callable=AsyncMock,
    ) as mock_exchange:
        _, response = await app.asgi_client.get(
            callback_path,
            follow_redirects=False,
        )

    assert response.headers.get("location") == (
        "https://frontend.example.com/login?error=oauth_state_invalid"
    )
    mock_exchange.assert_not_awaited()
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_returns_302_with_cookie():
    """The OAuth callback should return 302 + Set-Cookie header."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "google",
        code="test-auth-code",
    )

    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, response = await app.asgi_client.get(
            callback_path,
            cookies=callback_cookies,
            follow_redirects=False,
        )

    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert "/dashboard" in response.headers.get("location", "")

    # Check that Set-Cookie header exists
    set_cookie = _cookie_header(response, "neos_session")
    assert "neos_session" in set_cookie, f"No neos_session in Set-Cookie: {set_cookie!r}"

    # Verify cookie attributes
    set_cookie_lower = set_cookie.lower()
    assert "httponly" in set_cookie_lower, "Cookie missing HttpOnly"
    assert "secure" in set_cookie_lower, "Cookie missing Secure"
    assert "samesite=none" in set_cookie_lower, f"Cookie missing SameSite=None: {set_cookie}"
    assert "path=/" in set_cookie_lower, "Cookie missing Path=/"
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_cookie_is_valid():
    """The cookie from the OAuth callback should pass signature verification."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "google",
        code="test-auth-code",
    )

    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, response = await app.asgi_client.get(
            callback_path,
            cookies=callback_cookies,
            follow_redirects=False,
        )

    # Extract cookie value from Set-Cookie header
    set_cookie = _cookie_header(response, "neos_session")
    # Parse "neos_session=VALUE; ..." from the header
    cookie_value = None
    for part in set_cookie.split(";"):
        part = part.strip()
        if part.startswith("neos_session="):
            cookie_value = part[len("neos_session="):]
            break

    assert cookie_value is not None, f"Could not extract cookie value from: {set_cookie}"

    # Verify the cookie signature
    session_id = verify_session_cookie(cookie_value, SESSION_SECRET)
    assert session_id is not None, "Cookie failed signature verification"

    # Verify session exists in DB
    async with sf() as db:
        auth_session = await db.get(AuthSession, uuid.UUID(session_id))
        assert auth_session is not None, "AuthSession not found in DB"

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_cookie_works_with_auth_me():
    """Full flow: OAuth callback cookie → /auth/me should return 200."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "google",
        code="test-auth-code",
    )

    # Step 1: OAuth callback — get the cookie
    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, callback_response = await app.asgi_client.get(
            callback_path,
            cookies=callback_cookies,
            follow_redirects=False,
        )

    assert callback_response.status_code == 302

    # Extract cookie value
    set_cookie = _cookie_header(callback_response, "neos_session")
    cookie_value = None
    for part in set_cookie.split(";"):
        part = part.strip()
        if part.startswith("neos_session="):
            cookie_value = part[len("neos_session="):]
            break

    assert cookie_value is not None, f"No cookie in response: {set_cookie}"

    # Step 2: Use that cookie to call /auth/me
    _, me_response = await app.asgi_client.get(
        "/api/v1/auth/me",
        cookies={"neos_session": cookie_value},
    )

    assert me_response.status_code == 200, (
        f"/auth/me returned {me_response.status_code}: {me_response.text}"
    )
    data = me_response.json
    assert data.get("member") is not None
    assert data["member"]["display_name"] == "Test User"

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_linkedin_callback_works():
    """LinkedIn OAuth callback also sets a valid cookie."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "linkedin",
        code="test-li-code",
    )

    with patch("neos_agent.api.oauth._exchange_linkedin_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_LINKEDIN_USER
        _, response = await app.asgi_client.get(
            callback_path,
            cookies=callback_cookies,
            follow_redirects=False,
        )

    assert response.status_code == 302
    set_cookie = _cookie_header(response, "neos_session")
    assert "neos_session" in set_cookie
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_error_param_redirects_to_login():
    """Callback with error param redirects to login with error."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "google",
        error="access_denied",
    )

    _, response = await app.asgi_client.get(
        callback_path,
        cookies=callback_cookies,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "/login" in location
    assert "error=oauth_denied" in location

    # No cookie should be set on error
    set_cookie = _cookie_header(response, "neos_session")
    assert "neos_session" not in set_cookie
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_no_code_redirects_to_login():
    """Callback without code param redirects to login with error."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback("google")

    _, response = await app.asgi_client.get(
        callback_path,
        cookies=callback_cookies,
        follow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_denied" in location
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_exchange_failure_redirects():
    """If token exchange fails, redirect to login with error."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "google",
        code="bad-code",
    )

    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = None  # exchange failed
        _, response = await app.asgi_client.get(
            callback_path,
            cookies=callback_cookies,
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location
    _assert_transaction_cookie_cleared(response)

    await engine.dispose()


@pytest.mark.asyncio
async def test_auth_me_without_cookie_returns_401():
    """/auth/me without a cookie returns 401."""
    engine, sf = await _setup_db()
    app = _create_app(sf)

    _, response = await app.asgi_client.get("/api/v1/auth/me")
    assert response.status_code == 401

    await engine.dispose()


@pytest.mark.asyncio
async def test_auth_me_with_bad_cookie_returns_401():
    """/auth/me with an invalid cookie returns 401."""
    engine, sf = await _setup_db()
    app = _create_app(sf)

    _, response = await app.asgi_client.get(
        "/api/v1/auth/me",
        cookies={"neos_session": "garbage:value"},
    )
    assert response.status_code == 401

    await engine.dispose()


# ---------------------------------------------------------------------------
# Compare: password login cookie vs OAuth cookie
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_password_login_cookie_works_with_auth_me():
    """Baseline: password login sets a cookie that works with /auth/me."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "google",
        code="setup-code",
    )

    # Create a user with password first via OAuth (to get them in the DB)
    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        await app.asgi_client.get(
            callback_path,
            cookies=callback_cookies,
            follow_redirects=False,
        )

    # Set credentials on the user
    # First get the user from DB and set username/password
    from neos_agent.api.auth import _hash_password
    async with sf() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.oauth_id == "google-12345")
        )
        user = result.scalar_one()
        user.username = "testuser"
        user.password_hash = _hash_password("testpass123")
        await db.commit()

    # Now login with password
    _, login_response = await app.asgi_client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"},
    )

    assert login_response.status_code == 200, (
        f"Login failed: {login_response.text}"
    )

    # Extract cookie from login response
    set_cookie = login_response.headers.get("set-cookie", "")
    cookie_value = None
    for part in set_cookie.split(";"):
        part = part.strip()
        if part.startswith("neos_session="):
            cookie_value = part[len("neos_session="):]
            break

    assert cookie_value is not None

    # Use it with /auth/me
    _, me_response = await app.asgi_client.get(
        "/api/v1/auth/me",
        cookies={"neos_session": cookie_value},
    )

    assert me_response.status_code == 200, (
        f"Password login cookie failed /auth/me: {me_response.text}"
    )

    await engine.dispose()


# ---------------------------------------------------------------------------
# Test: cookie from 302 vs cookie from 200 — are they the same format?
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_redirect_vs_json_cookie_format():
    """Compare Set-Cookie header format between 302 (OAuth) and 200 (login)."""
    engine, sf = await _setup_db()
    app = _create_app(sf)
    callback_path, callback_cookies = _bound_callback(
        "google",
        code="test-code",
    )

    # OAuth callback → 302 + Set-Cookie
    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, oauth_response = await app.asgi_client.get(
            callback_path,
            cookies=callback_cookies,
            follow_redirects=False,
        )

    oauth_set_cookie = _cookie_header(oauth_response, "neos_session")

    # Set up password login
    from neos_agent.api.auth import _hash_password
    async with sf() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.oauth_id == "google-12345")
        )
        user = result.scalar_one()
        user.username = "compareuser"
        user.password_hash = _hash_password("testpass123")
        await db.commit()

    # Password login → 200 + Set-Cookie
    _, login_response = await app.asgi_client.post(
        "/api/v1/auth/login",
        json={"username": "compareuser", "password": "testpass123"},
    )

    login_set_cookie = _cookie_header(login_response, "neos_session")

    # Both should have the same cookie attributes (minus the value)
    def extract_attrs(sc: str) -> set[str]:
        parts = sc.split(";")
        # Skip the first part (name=value), normalize the rest
        return {p.strip().lower() for p in parts[1:] if p.strip()}

    oauth_attrs = extract_attrs(oauth_set_cookie)
    login_attrs = extract_attrs(login_set_cookie)

    print(f"\nOAuth Set-Cookie:  {oauth_set_cookie}")
    print(f"Login Set-Cookie:  {login_set_cookie}")
    print(f"OAuth attrs:  {oauth_attrs}")
    print(f"Login attrs:  {login_attrs}")

    # The attributes (httponly, secure, samesite, path, max-age) should match
    assert oauth_attrs == login_attrs, (
        f"Cookie attributes differ!\n  OAuth: {oauth_attrs}\n  Login: {login_attrs}"
    )

    await engine.dispose()
