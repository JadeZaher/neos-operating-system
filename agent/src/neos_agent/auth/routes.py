"""Authentication routes for DID-based self-sovereign identity.

Blueprint: auth_bp, url_prefix="/auth"

Provides challenge-response authentication using W3C did:key (Ed25519).
No blockchain, no external resolvers, no tokens.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta

from sanic import Blueprint, html, json
from sanic.request import Request
from sanic.response import redirect
from sqlalchemy import select

from neos_agent.auth.did import verify_did_signature
from neos_agent.auth.middleware import make_session_cookie
from neos_agent.db.models import AuthChallenge, AuthSession, Member
from neos_agent.views._rendering import render

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", url_prefix="/auth")


@auth_bp.get("/login")
async def login_page(request: Request):
    """Render the self-sovereign sign-in page."""
    content = await render("auth/login.html")
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
    expires_at = datetime.utcnow() + timedelta(minutes=5)

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
                AuthChallenge.expires_at > datetime.utcnow(),
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

        # Find or create member
        member_result = await session.execute(
            select(Member).where(Member.did == did)
        )
        member = member_result.scalar_one_or_none()

        if member is None:
            # New identity — need a display name
            if not display_name:
                display_name = f"Member-{did[-8:]}"

            # Find the first ecosystem for association
            from neos_agent.db.models import Ecosystem
            eco_result = await session.execute(select(Ecosystem).limit(1))
            ecosystem = eco_result.scalar_one_or_none()
            if ecosystem is None:
                return json({"error": "No ecosystem configured"}, status=500)

            member = Member(
                ecosystem_id=ecosystem.id,
                member_id=f"did-{did[-12:]}",
                did=did,
                display_name=display_name,
                current_status="active",
            )
            session.add(member)
            await session.flush()

        # Create auth session
        session_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_MAX_AGE_HOURS)
        auth_session = AuthSession(
            id=session_id,
            member_id=member.id,
            did=did,
            expires_at=expires_at,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.remote_addr,
        )
        session.add(auth_session)
        await session.commit()

    # Set signed session cookie
    cookie_value = make_session_cookie(str(session_id), settings.SESSION_SECRET)
    response = json({"success": True, "display_name": member.display_name})
    response.add_cookie(
        "neos_session",
        cookie_value,
        httponly=True,
        samesite="Lax",
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
                        await session.delete(auth_session)
                        await session.commit()
            except Exception:
                logger.exception("Error during logout session cleanup")

    response = redirect("/auth/login")
    response.delete_cookie("neos_session", path="/")
    return response
