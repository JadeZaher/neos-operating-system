"""JSON API blueprint for DID-based authentication.

Blueprint: auth_api_bp, url_prefix="/api/v1/auth"

Mirrors the HTML auth routes in neos_agent/auth/routes.py but returns
JSON responses only (no HTML rendering or redirects).
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.auth.did import verify_did_signature
from neos_agent.auth.middleware import make_session_cookie, verify_session_cookie
from neos_agent.db.models import AuthChallenge, AuthSession, Ecosystem, Member

from .schemas import AuthMeResponse, AuthVerifyResponse, EcosystemSummary, MemberSummary

logger = logging.getLogger(__name__)

auth_api_bp = Blueprint("auth_api", url_prefix="/api/v1/auth")


def _member_to_summary(member: Member) -> MemberSummary:
    """Convert a Member ORM instance to a MemberSummary schema."""
    return MemberSummary(
        id=member.id,
        display_name=member.display_name,
        did=member.did,
        profile=member.profile,
        ecosystem_id=member.ecosystem_id,
        current_status=member.current_status,
    )


@auth_api_bp.post("/challenge")
async def api_challenge(request: Request):
    """Issue a random challenge for the given DID.

    Accepts JSON: {"did": "did:key:z..."}
    Returns JSON: {"challenge": "<hex>"}
    """
    body = request.json or {}
    did = body.get("did", "").strip()

    if not did or not did.startswith("did:key:z"):
        return json({"error": "Invalid DID format"}, status=400)

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


@auth_api_bp.post("/verify")
async def api_verify(request: Request):
    """Verify a signed challenge and establish a session.

    Accepts JSON: {"did": "...", "challenge": "...", "signature": "...", "display_name": "..."}
    Returns JSON: AuthVerifyResponse with member info + sets neos_session cookie.
    """
    body = request.json or {}
    did = body.get("did", "").strip()
    challenge_hex = body.get("challenge", "").strip()
    signature_hex = body.get("signature", "").strip()
    display_name = body.get("display_name", "").strip()

    if not all([did, challenge_hex, signature_hex]):
        return json({"error": "Missing required fields"}, status=400)

    settings = request.app.ctx.settings

    async with request.app.ctx.db() as session:
        # Look up and validate the challenge
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
            if not display_name:
                display_name = f"Member-{did[-8:]}"

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

        member_summary = _member_to_summary(member)

    # Set signed session cookie
    cookie_value = make_session_cookie(str(session_id), settings.SESSION_SECRET)
    response_data = AuthVerifyResponse(
        success=True,
        display_name=member.display_name,
        member=member_summary,
    )
    response = json(response_data.model_dump(mode="json"), status=200)
    response.add_cookie(
        "neos_session",
        cookie_value,
        httponly=True,
        samesite="Lax",
        max_age=settings.SESSION_MAX_AGE_HOURS * 3600,
        path="/",
    )
    return response


@auth_api_bp.get("/me")
async def api_me(request: Request):
    """Return the current authenticated member and their ecosystems.

    Reads the neos_session cookie.
    Returns JSON: AuthMeResponse with member info + list of ecosystems.
    """
    settings = request.app.ctx.settings
    cookie = request.cookies.get("neos_session")

    if not cookie:
        return json({"error": "Not authenticated"}, status=401)

    session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
    if not session_id:
        return json({"error": "Invalid session"}, status=401)

    async with request.app.ctx.db() as db:
        # Verify session is still valid
        result = await db.execute(
            select(AuthSession).where(
                AuthSession.id == uuid.UUID(session_id),
                AuthSession.expires_at > datetime.utcnow(),
            )
        )
        auth_session = result.scalar_one_or_none()
        if not auth_session:
            return json({"error": "Session expired"}, status=401)

        # Load the member
        member = await db.get(Member, auth_session.member_id)
        if not member:
            return json({"error": "Member not found"}, status=401)

        member_summary = _member_to_summary(member)

        # Find all ecosystems this DID belongs to
        member_records = await db.execute(
            select(Member.ecosystem_id).where(Member.did == member.did)
        )
        eco_ids = list(member_records.scalars().all())

        ecosystems = []
        if eco_ids:
            eco_result = await db.execute(
                select(Ecosystem).where(Ecosystem.id.in_(eco_ids))
            )
            for eco in eco_result.scalars().all():
                # Count members in this ecosystem
                count_result = await db.execute(
                    select(Member.id).where(Member.ecosystem_id == eco.id)
                )
                member_count = len(count_result.all())
                ecosystems.append(
                    EcosystemSummary(
                        id=eco.id,
                        name=eco.name,
                        description=eco.description,
                        status=eco.status,
                        logo_url=eco.logo_url,
                        location=eco.location,
                        member_count=member_count,
                    )
                )

    response_data = AuthMeResponse(
        member=member_summary,
        ecosystems=ecosystems,
    )
    return json(response_data.model_dump(mode="json"))


@auth_api_bp.post("/logout")
async def api_logout(request: Request):
    """Destroy the current session and return JSON confirmation.

    Reads neos_session cookie, deletes the AuthSession from DB, clears cookie.
    Returns JSON: {"success": true}
    """
    settings = request.app.ctx.settings
    cookie = request.cookies.get("neos_session")

    if cookie:
        session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
        if session_id:
            try:
                async with request.app.ctx.db() as db:
                    result = await db.execute(
                        select(AuthSession).where(
                            AuthSession.id == uuid.UUID(session_id)
                        )
                    )
                    auth_session = result.scalar_one_or_none()
                    if auth_session:
                        await db.delete(auth_session)
                        await db.commit()
            except Exception:
                logger.exception("Error during API logout session cleanup")

    response = json({"success": True})
    response.delete_cookie("neos_session", path="/")
    return response
