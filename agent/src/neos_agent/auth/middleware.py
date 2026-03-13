"""Authentication middleware for Sanic.

Provides HMAC-signed session cookies and route protection.
Unauthenticated requests to protected routes redirect to /auth/login.
"""

from __future__ import annotations

import hashlib
import hmac

# Routes that do NOT require authentication
PUBLIC_PREFIXES = (
    "/auth/",
    "/api/v1/health",
    "/static/",
    "/ecosystems",
)

PUBLIC_EXACT = frozenset({
    "/auth/login",
    "/auth/challenge",
    "/auth/verify",
    "/auth/logout",
})


def is_public_route(path: str) -> bool:
    """Check if a request path is publicly accessible."""
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
