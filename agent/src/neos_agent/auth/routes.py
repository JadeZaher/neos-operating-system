"""Authentication routes for DID-based self-sovereign identity.

Blueprint: auth_bp, url_prefix="/auth"

Provides challenge-response authentication using W3C did:key (Ed25519).
No blockchain, no external resolvers, no tokens.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from sanic import Blueprint, json
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select

from neos_agent.api.auth import (  # FX-Onboard: one placement path for every sign-in
    consent_gate_payload, create_signup_member, existing_membership, signup_ecosystem,
)
from neos_agent.auth.did import verify_did_signature
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import AuthChallenge, AuthSession, User

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", url_prefix="/auth")


@auth_bp.get("/login")
async def login_page(request: Request):
    """Render the login page. Redirect to dashboard if already authenticated."""
    member = getattr(request.ctx, "member", None)
    if member:
        return redirect("/dashboard")

    from sanic import html
    from neos_agent.views._rendering import render

    content = await render("auth/login.html", request=request)
    return html(content)


@auth_bp.post("/challenge")
async def request_challenge(request: Request):
    """Issue a random challenge for the given DID.

    Expects JSON: {"did": "did:key:z..."}
    Returns JSON: {"challenge": "<hex>"}
    """
    body = request.json or {}
    did = body.get("did", "").strip()

    if not did or not did.startswith("did:key:z"):
        return json({"error": "Invalid DID format"}, status=400)

    settings = request.app.ctx.settings
    challenge_hex = os.urandom(32).hex()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    async with request.app.ctx.db() as session:
        challenge = AuthChallenge(
            did=did,
            challenge=challenge_hex,
            expires_at=expires_at,
        )
        session.add(challenge)
        await session.commit()

    return json({"challenge": challenge_hex})


@auth_bp.post("/verify")
async def verify_challenge(request: Request):
    """Verify a signed challenge and establish a session.

    Expects JSON: {"did": "did:key:z...", "challenge": "<hex>", "signature": "<hex>", "display_name": "..."}
    Returns JSON: {"success": true} + sets session cookie.
    """
    body = request.json or {}
    did = body.get("did", "").strip()
    challenge_hex = body.get("challenge", "").strip()
    signature_hex = body.get("signature", "").strip()
    display_name = body.get("display_name", "").strip()

    if not all([did, challenge_hex, signature_hex]):
        return json({"error": "Missing required fields"}, status=400)

    settings = request.app.ctx.settings

    # Look up and validate the challenge
    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(AuthChallenge).where(
                AuthChallenge.did == did,
                AuthChallenge.challenge == challenge_hex,
                AuthChallenge.used == False,
                AuthChallenge.expires_at > datetime.now(timezone.utc),
            )
        )
        auth_challenge = result.scalar_one_or_none()

        if auth_challenge is None:
            return json({"error": "Invalid or expired challenge"}, status=401)

        # Mark challenge as used
        auth_challenge.used = True

        # Verify the cryptographic signature
        if not verify_did_signature(did, challenge_hex, signature_hex):
            await session.commit()
            return json({"error": "Invalid signature"}, status=401)

        # Find or create User by DID
        user_result = await session.execute(
            select(User).where(User.did == did)
        )
        user = user_result.scalar_one_or_none()

        if user is not None and user.disabled_at is not None:
            return json({"error": "Account unavailable"}, status=403)

        if not display_name:
            display_name = f"Member-{did[-8:]}"

        if user is None:
            user = User(
                did=did,
                display_name=display_name,
            )
            session.add(user)
            await session.flush()

        # FX-Onboard (A3): the same placement as /api/v1/auth/verify, never an ACTIVE row in an arbitrary ecosystem.
        consent_gate = {}
        member = await existing_membership(session, user.id)
        if member is None:
            ecosystem = await signup_ecosystem(session, settings)
            if ecosystem is None:
                return json({"error": "No ecosystem configured"}, status=500)
            member, missing = await create_signup_member(
                session, user=user, ecosystem=ecosystem, member_id=f"did-{did[-12:]}", display_name=display_name,
            )
            consent_gate = consent_gate_payload(missing)

        # Create auth session
        session_id = uuid.uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.SESSION_MAX_AGE_HOURS)
        auth_session = AuthSession(
            id=session_id,
            user_id=user.id,
            expires_at=expires_at,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.remote_addr,
        )
        session.add(auth_session)
        await session.commit()

    # Set signed session cookie
    cookie_value = make_session_cookie(str(session_id), settings.SESSION_SECRET)
    response = json({"success": True, "display_name": member.display_name, **consent_gate})
    response.add_cookie(
        "neos_session",
        cookie_value,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=settings.SESSION_MAX_AGE_HOURS * 3600,
        path="/",
    )
    return response


@auth_bp.post("/logout")
async def logout(request: Request):
    """Destroy the current session and redirect to login."""
    from neos_agent.auth.middleware import verify_session_cookie

    settings = request.app.ctx.settings
    cookie = request.cookies.get("neos_session")

    if cookie:
        session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
        if session_id:
            try:
                async with request.app.ctx.db() as session:
                    result = await session.execute(
                        select(AuthSession).where(AuthSession.id == uuid.UUID(session_id))
                    )
                    auth_session = result.scalar_one_or_none()
                    if auth_session:
                        # Expire, never delete: an agent token may reference the row (FK).
                        auth_session.expires_at = datetime.now(timezone.utc)
                        await session.commit()
            except Exception:
                logger.exception("Error during logout session cleanup")

    response = json({"success": True})
    response.delete_cookie("neos_session", path="/")
    return response
