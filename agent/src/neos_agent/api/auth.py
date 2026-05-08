"""JSON API blueprint for DID-based authentication.

Blueprint: auth_api_bp, url_prefix="/api/v1/auth"

Mirrors the HTML auth routes in neos_agent/auth/routes.py but returns
JSON responses only (no HTML rendering or redirects).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import uuid
import datetime as _dt
from datetime import timedelta, timezone

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.auth.did import verify_did_signature
from neos_agent.auth.middleware import make_session_cookie, verify_session_cookie
from neos_agent.db.models import AuthChallenge, AuthSession, Ecosystem, Member, User

from .schemas import (
    AuthMeResponse,
    AuthVerifyResponse,
    EcosystemSummary,
    LoginRequest,
    MemberSummary,
    SetCredentialsRequest,
    SetCredentialsResponse,
    UserSummary,
)

logger = logging.getLogger(__name__)

auth_api_bp = Blueprint("auth_api", url_prefix="/api/v1/auth")

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,50}$")


def _hash_password(password: str) -> str:
    """Hash a password with PBKDF2-SHA256 and a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + key.hex()


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored PBKDF2-SHA256 hash."""
    salt_hex, key_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(key.hex(), key_hex)


def _member_to_summary(member: Member, user: User) -> MemberSummary:
    """Convert a Member + User ORM pair to a MemberSummary schema."""
    return MemberSummary(
        id=member.id,
        display_name=member.display_name,
        did=user.did,
        profile=member.profile,
        ecosystem_id=member.ecosystem_id,
        current_status=member.current_status,
        has_password=bool(user.password_hash),
        has_did=bool(user.did),
        oauth_provider=user.oauth_provider,
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
    expires_at = _dt.datetime.now(timezone.utc) + timedelta(minutes=5)

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
                AuthChallenge.expires_at > _dt.datetime.now(timezone.utc),
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

        if not display_name:
            display_name = f"Member-{did[-8:]}"

        if user is None:
            user = User(
                did=did,
                display_name=display_name,
            )
            session.add(user)
            await session.flush()

        # Find default ecosystem
        eco_result = await session.execute(select(Ecosystem).limit(1))
        ecosystem = eco_result.scalar_one_or_none()
        if ecosystem is None:
            return json({"error": "No ecosystem configured"}, status=500)

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
                member_id=f"did-{did[-12:]}",
                display_name=display_name,
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

        member_summary = _member_to_summary(member, user)

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
        secure=True,
        samesite="None",
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
        all_cookies = list(request.cookies.keys())
        logger.info("/auth/me: no neos_session cookie. All cookies: %s, Origin: %s, Referer: %s",
                     all_cookies, request.headers.get("origin"), request.headers.get("referer"))
        return json({"error": "Not authenticated"}, status=401)

    session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
    if not session_id:
        logger.warning("/auth/me: cookie present but verification failed (len=%d, secret_prefix=%s)",
                       len(cookie), settings.SESSION_SECRET[:8])
        return json({"error": "Invalid session"}, status=401)

    async with request.app.ctx.db() as db:
        # Verify session is still valid
        result = await db.execute(
            select(AuthSession).where(
                AuthSession.id == uuid.UUID(session_id),
                AuthSession.expires_at > _dt.datetime.now(timezone.utc),
            )
        )
        auth_session = result.scalar_one_or_none()
        if not auth_session:
            return json({"error": "Session expired"}, status=401)

        # Load the user
        user = await db.get(User, auth_session.user_id)
        if not user:
            return json({"error": "User not found"}, status=401)

        # Find ecosystems via Member.user_id
        member_records = await db.execute(
            select(Member.ecosystem_id).where(Member.user_id == user.id)
        )
        eco_ids = list(member_records.scalars().all())

        # Load a primary member for the summary
        primary_member_result = await db.execute(
            select(Member).where(Member.user_id == user.id).limit(1)
        )
        member = primary_member_result.scalar_one_or_none()
        if not member:
            return json({"error": "Member not found"}, status=401)

        member_summary = _member_to_summary(member, user)

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

    user_summary = UserSummary(
        id=user.id,
        display_name=user.display_name,
        did=user.did,
        username=user.username,
        has_password=bool(user.password_hash),
        has_did=bool(user.did),
        oauth_provider=user.oauth_provider,
        profile_picture=user.profile_picture,
    )
    response_data = AuthMeResponse(
        user=user_summary,
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


@auth_api_bp.post("/login")
async def api_login(request: Request):
    """Authenticate with username and password.

    Accepts JSON: {"username": "...", "password": "..."}
    Returns JSON: AuthVerifyResponse with member info + sets neos_session cookie.
    """
    body = request.json or {}
    try:
        payload = LoginRequest(**body)
    except Exception:
        return json({"error": "Invalid request body"}, status=400)

    username = payload.username.strip()
    password = payload.password

    if not username or not password:
        return json({"error": "Username and password are required"}, status=400)

    settings = request.app.ctx.settings

    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if user is None or not user.password_hash:
            return json({"error": "Invalid username or password"}, status=401)

        if not _verify_password(password, user.password_hash):
            return json({"error": "Invalid username or password"}, status=401)

        # Load a member for the response
        member_result = await session.execute(
            select(Member).where(Member.user_id == user.id).limit(1)
        )
        member = member_result.scalar_one_or_none()
        if member is None:
            return json({"error": "No membership found"}, status=401)

        # Create auth session (same flow as DID verify)
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

        member_summary = _member_to_summary(member, user)

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
        secure=True,
        samesite="None",
        max_age=settings.SESSION_MAX_AGE_HOURS * 3600,
        path="/",
    )
    return response


@auth_api_bp.post("/register")
async def api_register(request: Request):
    """Register a new member with username and password (no DID required).

    Accepts JSON: {"username": "...", "password": "...", "display_name": "..."}
    Returns JSON: AuthVerifyResponse with member info + sets neos_session cookie.
    """
    body = request.json or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    display_name = (body.get("display_name") or "").strip()

    if not username or not password:
        return json({"error": "Username and password are required"}, status=400)

    if not _USERNAME_RE.match(username):
        return json(
            {"error": "Username must be 3-50 characters, alphanumeric or underscore only"},
            status=400,
        )

    if len(password) < 8:
        return json({"error": "Password must be at least 8 characters"}, status=400)

    if not display_name:
        display_name = username

    settings = request.app.ctx.settings

    async with request.app.ctx.db() as session:
        # Check username uniqueness on User
        existing = await session.execute(
            select(User.id).where(User.username == username)
        )
        if existing.scalar_one_or_none() is not None:
            return json({"error": "Username already taken"}, status=409)

        # Find default ecosystem
        eco_result = await session.execute(select(Ecosystem).limit(1))
        ecosystem = eco_result.scalar_one_or_none()
        if ecosystem is None:
            return json({"error": "No ecosystem configured"}, status=500)

        # Create User first
        user = User(
            username=username,
            password_hash=_hash_password(password),
            display_name=display_name,
        )
        session.add(user)
        await session.flush()

        # Create Member with user_id
        member = Member(
            user_id=user.id,
            ecosystem_id=ecosystem.id,
            member_id=f"usr-{username[:12]}",
            display_name=display_name,
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

        member_summary = _member_to_summary(member, user)

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
        secure=True,
        samesite="None",
        max_age=settings.SESSION_MAX_AGE_HOURS * 3600,
        path="/",
    )
    return response


@auth_api_bp.post("/did/reset")
async def api_did_reset(request: Request):
    """Reset / regenerate a member's DID.

    Requires an active session. Clears the existing DID so the frontend
    can generate a new keypair and re-link it via /did/link.
    Returns JSON: {"success": true, "message": "..."}
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json({"error": "Authentication required"}, status=401)

    async with request.app.ctx.db() as db:
        m = await db.get(Member, member.id)
        if not m:
            return json({"error": "Member not found"}, status=401)

        # Load user via member.user_id and clear user.did
        user = await db.get(User, m.user_id)
        if not user:
            return json({"error": "User not found"}, status=401)
        user.did = None
        m.member_id = f"usr-{user.username or str(m.id)[:12]}"
        await db.commit()

    return json({"success": True, "message": "DID cleared. Generate a new identity to re-link."})


@auth_api_bp.post("/did/link")
async def api_did_link(request: Request):
    """Link a new DID to the current authenticated member.

    Requires an active session + a valid DID challenge-response.
    Accepts JSON: {"did": "...", "challenge": "...", "signature": "..."}
    Returns JSON: {"success": true, "did": "..."}
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json({"error": "Authentication required"}, status=401)

    body = request.json or {}
    did = (body.get("did") or "").strip()
    challenge_hex = (body.get("challenge") or "").strip()
    signature_hex = (body.get("signature") or "").strip()

    if not all([did, challenge_hex, signature_hex]):
        return json({"error": "Missing required fields"}, status=400)

    if not did.startswith("did:key:z"):
        return json({"error": "Invalid DID format"}, status=400)

    # Verify signature
    if not verify_did_signature(did, challenge_hex, signature_hex):
        return json({"error": "Invalid signature"}, status=401)

    async with request.app.ctx.db() as db:
        # Load the member to get user_id
        m = await db.get(Member, member.id)
        if not m:
            return json({"error": "Member not found"}, status=401)

        user = await db.get(User, m.user_id)
        if not user:
            return json({"error": "User not found"}, status=401)

        # Check DID not already used by another User
        existing = await db.execute(
            select(User.id).where(User.did == did, User.id != user.id)
        )
        if existing.scalar_one_or_none() is not None:
            return json({"error": "DID already linked to another account"}, status=409)

        # Verify the challenge was valid
        result = await db.execute(
            select(AuthChallenge).where(
                AuthChallenge.did == did,
                AuthChallenge.challenge == challenge_hex,
                AuthChallenge.used == False,
                AuthChallenge.expires_at > _dt.datetime.now(timezone.utc),
            )
        )
        auth_challenge = result.scalar_one_or_none()
        if auth_challenge is None:
            return json({"error": "Invalid or expired challenge"}, status=401)

        auth_challenge.used = True

        user.did = did
        m.member_id = f"did-{did[-12:]}"
        await db.commit()

    return json({"success": True, "did": did})


@auth_api_bp.post("/set-credentials")
async def api_set_credentials(request: Request):
    """Set username and password on the current authenticated member.

    Requires an active session (neos_session cookie).
    Accepts JSON: {"username": "...", "password": "..."}
    Returns JSON: {"success": true, "username": "..."}
    """
    settings = request.app.ctx.settings
    cookie = request.cookies.get("neos_session")

    if not cookie:
        return json({"error": "Not authenticated"}, status=401)

    session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
    if not session_id:
        return json({"error": "Invalid session"}, status=401)

    body = request.json or {}
    try:
        payload = SetCredentialsRequest(**body)
    except Exception:
        return json({"error": "Invalid request body"}, status=400)

    username = payload.username.strip()
    password = payload.password

    # Validate username: 3-50 chars, alphanumeric + underscore
    if not _USERNAME_RE.match(username):
        return json(
            {"error": "Username must be 3-50 characters, alphanumeric or underscore only"},
            status=400,
        )

    # Validate password: min 8 chars
    if len(password) < 8:
        return json({"error": "Password must be at least 8 characters"}, status=400)

    async with request.app.ctx.db() as db:
        # Verify session is still valid
        result = await db.execute(
            select(AuthSession).where(
                AuthSession.id == uuid.UUID(session_id),
                AuthSession.expires_at > _dt.datetime.now(timezone.utc),
            )
        )
        auth_session = result.scalar_one_or_none()
        if not auth_session:
            return json({"error": "Session expired"}, status=401)

        # Load the user
        user = await db.get(User, auth_session.user_id)
        if not user:
            return json({"error": "User not found"}, status=401)

        # Check username uniqueness
        existing = await db.execute(
            select(User.id).where(User.username == username, User.id != user.id)
        )
        if existing.scalar_one_or_none() is not None:
            return json({"error": "Username already taken"}, status=409)

        # Update credentials
        user.username = username
        user.password_hash = _hash_password(password)
        await db.commit()

    response_data = SetCredentialsResponse(success=True, username=username)
    return json(response_data.model_dump(mode="json"))
