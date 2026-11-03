"""Authentication middleware for Sanic.

Provides HMAC-signed session cookies and route protection.
Unauthenticated requests to protected routes receive a JSON 401 response.
"""

from __future__ import annotations

import hashlib
import hmac
import re

# Routes that do NOT require authentication
PUBLIC_PREFIXES = (
    "/auth/",
    "/api/v1/health",
    "/api/v1/auth/",
    "/api/v1/skills",
    "/api/v1/auth/oauth/",
    "/api/v1/media/",
    "/api/v1/profiles/",
)

PUBLIC_EXACT = frozenset({
    "/auth/challenge",
    "/auth/verify",
    "/auth/logout",
    "/",
})


def is_public_route(path: str, method: str = "GET") -> bool:
    """Check if a request path is publicly accessible."""
    if method == "GET" and (path == "/api/v1/communities" or re.fullmatch(r"/api/v1/communities/[0-9a-fA-F-]{36}", path)):
        return True
    if method in {"GET", "POST"} and path == "/api/v1/engagement/unsubscribe":
        return True
    if method == "POST" and path in {"/api/v1/engagement/webhooks/resend", "/api/v1/engagement/webhooks/twilio"}:
        return True
    if method == "GET" and (path in {"/api/v1/node-admin/audit", "/api/v1/node-admin/roster"} or re.fullmatch(r"/api/v1/node-admin/audit/[0-9a-fA-F-]{36}", path)):
        return True
    if path in PUBLIC_EXACT:
        return True
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def sign_session_id(session_id: str, secret: str) -> str:
    """Create HMAC-SHA256 signature for a session ID."""
    return hmac.new(
        secret.encode("utf-8"),
        session_id.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def make_session_cookie(session_id: str, secret: str) -> str:
    """Create a signed session cookie value: {session_id}:{hmac}."""
    sig = sign_session_id(session_id, secret)
    return f"{session_id}:{sig}"


def verify_session_cookie(cookie_value: str, secret: str) -> str | None:
    """Verify and extract session ID from a signed cookie.

    Returns:
        The session_id if valid, None if tampered or malformed.
    """
    if ":" not in cookie_value:
        return None
    session_id, sig = cookie_value.rsplit(":", 1)
    expected = sign_session_id(session_id, secret)
    if hmac.compare_digest(sig, expected):
        return session_id
    return None
