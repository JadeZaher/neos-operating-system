"""OAuth authentication endpoints for Google and LinkedIn.

Blueprint: oauth_bp, url_prefix="/api/v1/auth/oauth"

Flow:
  1. Frontend calls GET /api/v1/auth/oauth/<provider> to get the redirect URL
  2. User authenticates with the provider in a popup/redirect
  3. Provider redirects to GET /api/v1/auth/oauth/<provider>/callback with a code
  4. Backend exchanges code for user info, creates/finds member, sets session cookie
  5. Callback redirects to frontend with success/error status
"""

from __future__ import annotations

import base64
import binascii
import datetime as _dt
import hashlib
import hmac
import json as _json
import logging
import secrets
import time
import uuid
from datetime import timedelta, timezone
from urllib.parse import urlencode, urlsplit

from sanic import Blueprint, json
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select

from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import AuthSession, Ecosystem, Member, User

logger = logging.getLogger(__name__)

oauth_bp = Blueprint("oauth", url_prefix="/api/v1/auth/oauth")

_OAUTH_STATE_TTL_SECONDS = 10 * 60
_OAUTH_STATE_CLOCK_SKEW_SECONDS = 60
_OAUTH_TRANSACTION_COOKIE = "neos_oauth_transaction"
_OAUTH_COOKIE_PATH = "/api/v1/auth/oauth"


def _normalize_frontend_origin(value: str) -> str | None:
    """Return a canonical HTTP(S) origin, or None for a non-origin URL."""
    try:
        parsed = urlsplit(value.strip())
        port = parsed.port
    except (AttributeError, ValueError):
        return None

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        return None

    host = parsed.hostname
    if ":" in host:
        host = f"[{host}]"
    default_port = (
        (parsed.scheme == "http" and port == 80)
        or (parsed.scheme == "https" and port == 443)
    )
    authority = host if port is None or default_port else f"{host}:{port}"
    return f"{parsed.scheme}://{authority}"


def _allowed_frontend_origins(settings) -> set[str]:
    """Build the redirect allowlist from explicit frontend/CORS settings."""
    configured = [
        getattr(settings, "FRONTEND_URL", ""),
        *str(getattr(settings, "CORS_ORIGINS", "")).split(","),
    ]
    return {
        normalized
        for value in configured
        if value.strip() != "*"
        if (normalized := _normalize_frontend_origin(value)) is not None
    }


def _fallback_frontend_origin(settings) -> str:
    """Choose a safe configured destination for rejected callbacks."""
    frontend = _normalize_frontend_origin(getattr(settings, "FRONTEND_URL", ""))
    if frontend:
        return frontend

    for value in str(getattr(settings, "CORS_ORIGINS", "")).split(","):
        origin = _normalize_frontend_origin(value)
        if origin:
            return origin

    redirect_base = _normalize_frontend_origin(
        getattr(settings, "OAUTH_REDIRECT_BASE", "")
    )
    return redirect_base or "http://localhost:5173"


def _create_oauth_state(
    provider: str,
    frontend_origin: str,
    secret: str,
    *,
    now: int | None = None,
) -> str:
    """Sign the frontend destination and OAuth request metadata."""
    issued_at = int(time.time() if now is None else now)
    payload = {
        "v": 1,
        "provider": provider,
        "origin": frontend_origin,
        "nonce": secrets.token_urlsafe(24),
        "iat": issued_at,
        "exp": issued_at + _OAUTH_STATE_TTL_SECONDS,
    }
    encoded_payload = base64.urlsafe_b64encode(
        _json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).rstrip(b"=").decode()
    signature = hmac.new(
        secret.encode(), encoded_payload.encode(), hashlib.sha256
    ).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{encoded_payload}.{encoded_signature}"


def _verify_oauth_state(
    state: str,
    provider: str,
    settings,
    *,
    now: int | None = None,
) -> str | None:
    """Validate a signed state and return its allowed frontend origin."""
    try:
        encoded_payload, encoded_signature = state.split(".", 1)
        expected_signature = hmac.new(
            settings.SESSION_SECRET.encode(),
            encoded_payload.encode(),
            hashlib.sha256,
        ).digest()
        supplied_signature = base64.urlsafe_b64decode(
            encoded_signature + "=" * (-len(encoded_signature) % 4)
        )
        if not hmac.compare_digest(expected_signature, supplied_signature):
            return None

        payload = _json.loads(
            base64.urlsafe_b64decode(
                encoded_payload + "=" * (-len(encoded_payload) % 4)
            )
        )
    except (
        AttributeError,
        binascii.Error,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        _json.JSONDecodeError,
    ):
        return None

    current_time = int(time.time() if now is None else now)
    issued_at = payload.get("iat") if isinstance(payload, dict) else None
    expires_at = payload.get("exp") if isinstance(payload, dict) else None
    nonce = payload.get("nonce") if isinstance(payload, dict) else None
    origin = payload.get("origin") if isinstance(payload, dict) else None
    if (
        not isinstance(payload, dict)
        or payload.get("v") != 1
        or payload.get("provider") != provider
        or type(issued_at) is not int
        or type(expires_at) is not int
        or expires_at <= current_time
        or issued_at > current_time + _OAUTH_STATE_CLOCK_SKEW_SECONDS
        or expires_at - issued_at != _OAUTH_STATE_TTL_SECONDS
        or not isinstance(nonce, str)
        or len(nonce) < 16
        or not isinstance(origin, str)
    ):
        return None

    normalized_origin = _normalize_frontend_origin(origin)
    if (
        normalized_origin != origin
        or normalized_origin not in _allowed_frontend_origins(settings)
    ):
        return None
    return normalized_origin


def _frontend_redirect(frontend_origin: str, path: str, **query: str) -> str:
    """Build an encoded redirect URL beneath a validated frontend origin."""
    suffix = f"?{urlencode(query)}" if query else ""
    return f"{frontend_origin}{path}{suffix}"


def _clear_oauth_transaction_cookie(response):
    """Expire the browser-bound OAuth transaction cookie."""
    response.delete_cookie(
        _OAUTH_TRANSACTION_COOKIE,
        path=_OAUTH_COOKIE_PATH,
    )
    return response


def _oauth_callback_redirect(frontend_origin: str, path: str, **query: str):
    """Create a callback redirect that consumes the OAuth transaction."""
    response = redirect(_frontend_redirect(frontend_origin, path, **query))
    return _clear_oauth_transaction_cookie(response)


# ---------------------------------------------------------------------------
# Provider helpers
# ---------------------------------------------------------------------------

async def _exchange_google_code(code: str, settings) -> dict | None:
    """Exchange Google auth code for user info."""
    import httpx

    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/api/v1/auth/oauth/google/callback"

    async with httpx.AsyncClient() as http:
        # Exchange code for tokens
        token_resp = await http.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.error("Google token exchange failed: %s", token_resp.text)
            return None
        tokens = token_resp.json()

        # Get user info
        userinfo_resp = await http.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            return None
        return userinfo_resp.json()


async def _exchange_linkedin_code(code: str, settings) -> dict | None:
    """Exchange LinkedIn auth code for user info."""
    import httpx

    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/api/v1/auth/oauth/linkedin/callback"

    async with httpx.AsyncClient() as http:
        # Exchange code for tokens
        token_resp = await http.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "code": code,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status_code != 200:
            logger.error("LinkedIn token exchange failed: %s", token_resp.text)
            return None
        tokens = token_resp.json()

        # Get user info via OpenID Connect userinfo endpoint
        userinfo_resp = await http.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            return None
        info = userinfo_resp.json()
        return {
            "id": info.get("sub"),
            "name": info.get("name"),
            "email": info.get("email"),
            "picture": info.get("picture"),
        }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@oauth_bp.get("/<provider:str>")
async def oauth_initiate(request: Request, provider: str):
    """GET /api/v1/auth/oauth/<provider> — Return the OAuth redirect URL."""
    settings = request.app.ctx.settings

    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID:
            return json({"error": "Google OAuth not configured"}, status=503)
    elif provider == "linkedin":
        if not settings.LINKEDIN_CLIENT_ID:
            return json({"error": "LinkedIn OAuth not configured"}, status=503)
    else:
        return json({"error": f"Unknown provider: {provider}"}, status=400)

    requested_origin = request.args.get("origin")
    if requested_origin is None:
        frontend_origin = _fallback_frontend_origin(settings)
    else:
        frontend_origin = _normalize_frontend_origin(requested_origin)
        if frontend_origin not in _allowed_frontend_origins(settings):
            return json({"error": "Frontend origin is not allowed"}, status=400)

    state = _create_oauth_state(
        provider,
        frontend_origin,
        settings.SESSION_SECRET,
    )
    redirect_uri = (
        f"{settings.OAUTH_REDIRECT_BASE}/api/v1/auth/oauth/{provider}/callback"
    )
    if provider == "google":
        authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    else:
        authorization_url = "https://www.linkedin.com/oauth/v2/authorization"
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "state": state,
        }
    response = json({"url": f"{authorization_url}?{urlencode(params)}"})
    response.add_cookie(
        _OAUTH_TRANSACTION_COOKIE,
        state,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=_OAUTH_STATE_TTL_SECONDS,
        path=_OAUTH_COOKIE_PATH,
    )
    return response


@oauth_bp.get("/<provider:str>/callback")
async def oauth_callback(request: Request, provider: str):
    """GET /api/v1/auth/oauth/<provider>/callback — Handle OAuth redirect."""
    settings = request.app.ctx.settings
    code = request.args.get("code")
    error = request.args.get("error")
    state = request.args.get("state")
    cookie_state = request.cookies.get(_OAUTH_TRANSACTION_COOKIE)
    fallback_origin = _fallback_frontend_origin(settings)
    if (
        not state
        or not cookie_state
        or not hmac.compare_digest(state, cookie_state)
    ):
        return _oauth_callback_redirect(
            fallback_origin,
            "/login",
            error="oauth_state_invalid",
        )

    frontend_origin = _verify_oauth_state(state, provider, settings)
    if frontend_origin is None:
        return _oauth_callback_redirect(
            fallback_origin,
            "/login",
            error="oauth_state_invalid",
        )

    if error or not code:
        return _oauth_callback_redirect(
            frontend_origin,
            "/login",
            error="oauth_denied",
        )

    # Exchange code for user info
    if provider == "google":
        user_info = await _exchange_google_code(code, settings)
        if not user_info:
            return _oauth_callback_redirect(
                frontend_origin,
                "/login",
                error="oauth_failed",
            )
        oauth_id = user_info.get("id")
        display_name = user_info.get("name", "")
        email = user_info.get("email", "")
        picture = user_info.get("picture")

    elif provider == "linkedin":
        user_info = await _exchange_linkedin_code(code, settings)
        if not user_info:
            return _oauth_callback_redirect(
                frontend_origin,
                "/login",
                error="oauth_failed",
            )
        oauth_id = user_info.get("id")
        display_name = user_info.get("name", "")
        email = user_info.get("email", "")
        picture = user_info.get("picture")

    else:
        return _oauth_callback_redirect(
            frontend_origin,
            "/login",
            error="unknown_provider",
        )

    if not oauth_id:
        return _oauth_callback_redirect(
            frontend_origin,
            "/login",
            error="oauth_failed",
        )

    # Find or create User, then ensure Member exists
    async with request.app.ctx.db() as session:
        # Try to find User by oauth_provider + oauth_id
        result = await session.execute(
            select(User).where(
                User.oauth_provider == provider,
                User.oauth_id == oauth_id,
            )
        )
        user = result.scalar_one_or_none()

        if user is None and email:
            # Check if there's a user with the same email as username
            email_result = await session.execute(
                select(User).where(User.username == email)
            )
            user = email_result.scalar_one_or_none()
            if user:
                # Link OAuth to existing account
                user.oauth_provider = provider
                user.oauth_id = oauth_id
                if picture and not user.profile_picture:
                    user.profile_picture = picture

        if user is None:
            # New user — create User
            user = User(
                oauth_provider=provider,
                oauth_id=oauth_id,
                display_name=display_name or f"User-{oauth_id[:8]}",
                profile_picture=picture,
            )
            session.add(user)
            await session.flush()

        # Find default ecosystem
        eco_result = await session.execute(select(Ecosystem).limit(1))
        ecosystem = eco_result.scalar_one_or_none()
        if ecosystem is None:
            return _oauth_callback_redirect(
                frontend_origin,
                "/login",
                error="no_ecosystem",
            )

        # Find or create Member for this user + ecosystem
        member_result = await session.execute(
            select(Member).where(
                Member.user_id == user.id,
                Member.ecosystem_id == ecosystem.id,
            )
        )
        member = member_result.scalar_one_or_none()

        if member is None:
            member = Member(
                user_id=user.id,
                ecosystem_id=ecosystem.id,
                member_id=f"oauth-{provider}-{oauth_id[:12]}",
                display_name=display_name or f"User-{oauth_id[:8]}",
                current_status="active",
            )
            session.add(member)
            await session.flush()

        # Create auth session
        session_id = uuid.uuid4()
        expires_at = _dt.datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_MAX_AGE_HOURS)
        auth_session = AuthSession(
            id=session_id,
            user_id=user.id,
            expires_at=expires_at,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.remote_addr,
        )
        session.add(auth_session)
        await session.commit()

    # Set session cookie and redirect to frontend
    cookie_value = make_session_cookie(str(session_id), settings.SESSION_SECRET)
    redirect_url = _frontend_redirect(frontend_origin, "/dashboard")
    logger.info(
        "OAuth %s callback success: user_id=%s, session_id=%s, redirect_to=%s, cookie_len=%d",
        provider, user.id, session_id, redirect_url, len(cookie_value),
    )
    response = _clear_oauth_transaction_cookie(redirect(redirect_url))
    response.add_cookie(
        "neos_session",
        cookie_value,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=settings.SESSION_MAX_AGE_HOURS * 3600,
        path="/",
    )
    # Log cookie info
    logger.info("OAuth response: status=%s, Location=%s, has_cookie=%s",
                response.status, response.headers.get("location"),
                "neos_session" in str(response.cookies))
    return response


@oauth_bp.get("/providers")
async def oauth_providers(request: Request):
    """GET /api/v1/auth/oauth/providers — List available OAuth providers."""
    settings = request.app.ctx.settings
    providers = []
    if settings.GOOGLE_CLIENT_ID:
        providers.append({"id": "google", "name": "Google"})
    if settings.LINKEDIN_CLIENT_ID:
        providers.append({"id": "linkedin", "name": "LinkedIn"})
    return json({"providers": providers})
