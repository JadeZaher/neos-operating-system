"""JSON API blueprint for agent tokens (MCP access).

Blueprint: agent_tokens_api_bp, url_prefix="/api/v1/agent-tokens"

Logged-in users mint bearer tokens for their own agents (MCP clients).
The plaintext token is returned ONCE at mint; only its sha256 hash is
stored. Every token is bound to the auth session it was minted from:
when that session expires or the token is revoked, the agent's access
ends — authority is always session-scoped.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.auth.middleware import verify_session_cookie
from neos_agent.config import get_settings
from neos_agent.db.models import AgentToken, AuthSession

from .helpers import require_auth

logger = logging.getLogger(__name__)

agent_tokens_api_bp = Blueprint("agent_tokens_api", url_prefix="/api/v1/agent-tokens")

MAX_TOKEN_DAYS = 30
DEFAULT_TOKEN_DAYS = 7


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _to_dict(t: AgentToken) -> dict:
    return {
        "id": str(t.id),
        "label": t.label,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "expires_at": t.expires_at.isoformat() if t.expires_at else None,
        "revoked": t.revoked_at is not None,
        "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
    }


@agent_tokens_api_bp.post("/")
async def mint_agent_token(request: Request):
    """POST /api/v1/agent-tokens -- mint an agent token.

    Accepts JSON: {"label": str (optional), "expires_in_days": int (<=30, optional)}
    Returns JSON: token metadata + the plaintext token (shown once), 201.
    """
    member, err = require_auth(request)
    if err:
        return err

    user = getattr(request.ctx, "user", None)
    if user is None:
        return json({"error": "Authentication required"}, status=401)

    body = request.json or {}
    label = str(body.get("label") or "My agent").strip()[:120] or "My agent"
    try:
        days = int(body.get("expires_in_days") or DEFAULT_TOKEN_DAYS)
    except (TypeError, ValueError):
        return json({"error": "expires_in_days must be an integer"}, status=400)
    if not 1 <= days <= MAX_TOKEN_DAYS:
        return json({"error": f"expires_in_days must be 1-{MAX_TOKEN_DAYS}"}, status=400)

    # Bind the token to the very auth session the user is logged in with.
    cookie = request.cookies.get("neos_session")
    sid = verify_session_cookie(cookie, get_settings().SESSION_SECRET) if cookie else None
    if not sid:
        return json({"error": "Session unavailable"}, status=401)

    now = datetime.now(timezone.utc)
    async with request.app.ctx.db() as session:
        auth_session = await session.scalar(
            select(AuthSession).where(
                AuthSession.id == uuid.UUID(sid),
                AuthSession.expires_at > now,
            )
        )
        if auth_session is None:
            return json({"error": "Session expired"}, status=401)

        # The token never outlives its parent session, nor MAX_TOKEN_DAYS.
        expires_at = min(now + timedelta(days=days), auth_session.expires_at)
        plaintext = f"neos_agt_{secrets.token_urlsafe(32)}"
        token = AgentToken(
            id=uuid.uuid4(),
            user_id=user.id,
            auth_session_id=auth_session.id,
            label=label,
            token_hash=_hash(plaintext),
            expires_at=expires_at,
        )
        session.add(token)
        await session.commit()

        payload = _to_dict(token)
        payload["token"] = plaintext
        return json(payload, status=201)


@agent_tokens_api_bp.get("/")
async def list_agent_tokens(request: Request):
    """GET /api/v1/agent-tokens -- list the caller's tokens (no secrets)."""
    member, err = require_auth(request)
    if err:
        return err

    user = getattr(request.ctx, "user", None)
    if user is None:
        return json({"error": "Authentication required"}, status=401)

    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(AgentToken)
            .where(AgentToken.user_id == user.id)
            .order_by(AgentToken.created_at.desc())
        )
        tokens = result.scalars().all()

    return json({"items": [_to_dict(t) for t in tokens]})


@agent_tokens_api_bp.delete("/<token_id:uuid>")
async def revoke_agent_token(request: Request, token_id: uuid.UUID):
    """DELETE /api/v1/agent-tokens/:id -- revoke a token the caller owns."""
    member, err = require_auth(request)
    if err:
        return err

    user = getattr(request.ctx, "user", None)
    if user is None:
        return json({"error": "Authentication required"}, status=401)

    async with request.app.ctx.db() as session:
        token = await session.scalar(
            select(AgentToken).where(
                AgentToken.id == token_id,
                AgentToken.user_id == user.id,
            )
        )
        if token is None:
            return json({"error": "Token not found"}, status=404)
        if token.revoked_at is None:
            token.revoked_at = datetime.now(timezone.utc)
            await session.commit()

    return json(_to_dict(token))
