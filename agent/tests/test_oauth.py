"""Tests for OAuth authentication flow.

Verifies the full OAuth callback → cookie → /auth/me chain,
isolating the exact point where cookie-based auth breaks
on redirect responses vs. JSON responses.
"""

from __future__ import annotations

import uuid
from datetime import date
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
    settings.OAUTH_REDIRECT_BASE = "https://frontend.example.com"
    settings.GOOGLE_CLIENT_ID = "google-client-id"
    settings.GOOGLE_CLIENT_SECRET = "google-secret"
    settings.LINKEDIN_CLIENT_ID = "linkedin-client-id"
    settings.LINKEDIN_CLIENT_SECRET = "linkedin-secret"
    settings.CORS_ORIGINS = "https://frontend.example.com"
    app.ctx.settings = settings
    app.ctx.db = db_session_factory

    from neos_agent.api.oauth import oauth_bp
    from neos_agent.api.auth import auth_api_bp
    app.blueprint(oauth_bp)
    app.blueprint(auth_api_bp)

    return app


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
async def test_oauth_callback_returns_302_with_cookie():
    """The OAuth callback should return 302 + Set-Cookie header."""
    engine, sf = await _setup_db()
    app = _create_app(sf)

    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, response = await app.asgi_client.get(
            "/api/v1/auth/oauth/google/callback?code=test-auth-code",
            allow_redirects=False,
        )

    assert response.status_code == 302, f"Expected 302, got {response.status_code}"
    assert "/dashboard" in response.headers.get("location", "")

    # Check that Set-Cookie header exists
    set_cookie = response.headers.get("set-cookie", "")
    assert "neos_session" in set_cookie, f"No neos_session in Set-Cookie: {set_cookie!r}"

    # Verify cookie attributes
    set_cookie_lower = set_cookie.lower()
    assert "httponly" in set_cookie_lower, "Cookie missing HttpOnly"
    assert "secure" in set_cookie_lower, "Cookie missing Secure"
    assert "samesite=none" in set_cookie_lower, f"Cookie missing SameSite=None: {set_cookie}"
    assert "path=/" in set_cookie_lower, "Cookie missing Path=/"

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_cookie_is_valid():
    """The cookie from the OAuth callback should pass signature verification."""
    engine, sf = await _setup_db()
    app = _create_app(sf)

    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, response = await app.asgi_client.get(
            "/api/v1/auth/oauth/google/callback?code=test-auth-code",
            allow_redirects=False,
        )

    # Extract cookie value from Set-Cookie header
    set_cookie = response.headers.get("set-cookie", "")
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

    # Step 1: OAuth callback — get the cookie
    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, callback_response = await app.asgi_client.get(
            "/api/v1/auth/oauth/google/callback?code=test-auth-code",
            allow_redirects=False,
        )

    assert callback_response.status_code == 302

    # Extract cookie value
    set_cookie = callback_response.headers.get("set-cookie", "")
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

    with patch("neos_agent.api.oauth._exchange_linkedin_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_LINKEDIN_USER
        _, response = await app.asgi_client.get(
            "/api/v1/auth/oauth/linkedin/callback?code=test-li-code",
            allow_redirects=False,
        )

    assert response.status_code == 302
    set_cookie = response.headers.get("set-cookie", "")
    assert "neos_session" in set_cookie

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_error_param_redirects_to_login():
    """Callback with error param redirects to login with error."""
    engine, sf = await _setup_db()
    app = _create_app(sf)

    _, response = await app.asgi_client.get(
        "/api/v1/auth/oauth/google/callback?error=access_denied",
        allow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "/login" in location
    assert "error=oauth_denied" in location

    # No cookie should be set on error
    set_cookie = response.headers.get("set-cookie", "")
    assert "neos_session" not in set_cookie

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_no_code_redirects_to_login():
    """Callback without code param redirects to login with error."""
    engine, sf = await _setup_db()
    app = _create_app(sf)

    _, response = await app.asgi_client.get(
        "/api/v1/auth/oauth/google/callback",
        allow_redirects=False,
    )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_denied" in location

    await engine.dispose()


@pytest.mark.asyncio
async def test_oauth_callback_exchange_failure_redirects():
    """If token exchange fails, redirect to login with error."""
    engine, sf = await _setup_db()
    app = _create_app(sf)

    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = None  # exchange failed
        _, response = await app.asgi_client.get(
            "/api/v1/auth/oauth/google/callback?code=bad-code",
            allow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "error=oauth_failed" in location

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

    # Create a user with password first via OAuth (to get them in the DB)
    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        await app.asgi_client.get(
            "/api/v1/auth/oauth/google/callback?code=setup-code",
            allow_redirects=False,
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

    # OAuth callback → 302 + Set-Cookie
    with patch("neos_agent.api.oauth._exchange_google_code", new_callable=AsyncMock) as mock_exchange:
        mock_exchange.return_value = FAKE_GOOGLE_USER
        _, oauth_response = await app.asgi_client.get(
            "/api/v1/auth/oauth/google/callback?code=test-code",
            allow_redirects=False,
        )

    oauth_set_cookie = oauth_response.headers.get("set-cookie", "")

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

    login_set_cookie = login_response.headers.get("set-cookie", "")

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
