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

import logging
import uuid
import datetime as _dt
from datetime import timedelta, timezone

from sanic import Blueprint, json
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select

from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import AuthSession, Ecosystem, Member, User

logger = logging.getLogger(__name__)

oauth_bp = Blueprint("oauth", url_prefix="/api/v1/auth/oauth")

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
        redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/api/v1/auth/oauth/google/callback"
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            "&response_type=code"
            "&scope=openid%20email%20profile"
            "&access_type=offline"
            "&prompt=consent"
        )
        return json({"url": url})

    elif provider == "linkedin":
        if not settings.LINKEDIN_CLIENT_ID:
            return json({"error": "LinkedIn OAuth not configured"}, status=503)
        redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/api/v1/auth/oauth/linkedin/callback"
        url = (
            "https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code"
            f"&client_id={settings.LINKEDIN_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            "&scope=openid%20profile%20email"
        )
        return json({"url": url})

    return json({"error": f"Unknown provider: {provider}"}, status=400)


@oauth_bp.get("/<provider:str>/callback")
async def oauth_callback(request: Request, provider: str):
    """GET /api/v1/auth/oauth/<provider>/callback — Handle OAuth redirect."""
    settings = request.app.ctx.settings
    code = request.args.get("code")
    error = request.args.get("error")
    frontend_base = settings.OAUTH_REDIRECT_BASE or "http://localhost:5173"

    if error or not code:
        return redirect(f"{frontend_base}/login?error=oauth_denied")

    # Exchange code for user info
    if provider == "google":
        user_info = await _exchange_google_code(code, settings)
        if not user_info:
            return redirect(f"{frontend_base}/login?error=oauth_failed")
        oauth_id = user_info.get("id")
        display_name = user_info.get("name", "")
        email = user_info.get("email", "")
        picture = user_info.get("picture")

    elif provider == "linkedin":
        user_info = await _exchange_linkedin_code(code, settings)
        if not user_info:
            return redirect(f"{frontend_base}/login?error=oauth_failed")
        oauth_id = user_info.get("id")
        display_name = user_info.get("name", "")
        email = user_info.get("email", "")
        picture = user_info.get("picture")

    else:
        return redirect(f"{frontend_base}/login?error=unknown_provider")

    if not oauth_id:
        return redirect(f"{frontend_base}/login?error=oauth_failed")

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
            return redirect(f"{frontend_base}/login?error=no_ecosystem")

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
    redirect_url = f"{frontend_base}/dashboard"
    logger.info(
        "OAuth %s callback success: user_id=%s, session_id=%s, redirect_to=%s, cookie_len=%d",
        provider, user.id, session_id, redirect_url, len(cookie_value),
    )
    response = redirect(redirect_url)
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
