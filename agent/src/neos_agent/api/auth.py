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
from sqlalchemy import func, select

from neos_agent.auth.did import verify_did_signature
from neos_agent.auth.middleware import make_session_cookie, verify_session_cookie
from neos_agent.db.models import AuthChallenge, AuthSession, Ecosystem, Member, User
from neos_agent.services.agreement_consent import missing_agreement_consents
from neos_agent.services.member_lifecycle import SIGNUP, counts_as_member, place_member
from neos_agent.api.guards import default_member
from neos_agent.api.helpers import home_ecosystem_id  # FX-Onboard: sign-up prefers the pinned home
from neos_agent.api.policy import can_administer_ecosystem  # FX-Onboard: /auth/me `is_steward` per ecosystem

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


def _slug(value: str) -> str:
    """Lowercase, hyphen-joined form of a name, used to match the configured default."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class SignupEcosystemNotFound(Exception):
    """The caller named an ecosystem for the new account that does not exist."""


def requested_ecosystem_id(body: dict) -> uuid.UUID | None:
    """Parse the optional ``ecosystem_id`` a sign-up request names; raise if it is malformed."""
    raw = body.get("ecosystem_id")
    if raw in (None, ""):
        return None
    try:
        return uuid.UUID(str(raw))
    except ValueError as exc:
        raise SignupEcosystemNotFound(str(raw)) from exc


async def signup_ecosystem(session, settings, requested_id: uuid.UUID | None = None) -> Ecosystem | None:
    """Ecosystem a new account joins: requested id, then the pinned platform home, then
    SIGNUP_DEFAULT_ECOSYSTEM_SLUG, then the oldest PUBLIC one (FX-Onboard: never a private ecosystem nobody chose).

    "Oldest" breaks created_at ties (a seed inserts every ecosystem in one
    transaction) by founded_date before id; see api/AGENTS.md "Sign-up placement".
    """
    if requested_id is not None:
        ecosystem = await session.get(Ecosystem, requested_id)
        if ecosystem is None or ecosystem.visibility != "public":  # private ecosystems are not self-service (owner Q3)
            raise SignupEcosystemNotFound(str(requested_id))
        return ecosystem

    home_id = await home_ecosystem_id(session, settings)  # the operator's pin, by id (G-Authority)
    if home_id is not None:
        return await session.get(Ecosystem, home_id)

    ecosystems = list((await session.execute(
        select(Ecosystem).order_by(
            Ecosystem.created_at.asc(),
            Ecosystem.founded_date.asc().nulls_last(),
            Ecosystem.id.asc(),
        )
    )).scalars().all())
    configured = getattr(settings, "SIGNUP_DEFAULT_ECOSYSTEM_SLUG", "")
    if isinstance(configured, str) and configured.strip():
        wanted = _slug(configured.strip())
        for ecosystem in ecosystems:
            if str(ecosystem.id) == configured.strip().lower() or _slug(ecosystem.name) == wanted:
                return ecosystem
        logger.warning(
            "SIGNUP_DEFAULT_ECOSYSTEM_SLUG=%r matches no ecosystem; using the oldest", configured,
        )
    return next((ecosystem for ecosystem in ecosystems if ecosystem.visibility == "public"), None)


async def create_signup_member(
    session, *, user: User, ecosystem: Ecosystem, member_id: str, display_name: str,
) -> tuple[Member, list]:
    """Place a newcomer behind the ecosystem's agreement-consent gate through member_lifecycle.place_member.

    Same path as ``POST /ecosystems/:id/join`` (trigger ``signup``, one transition): ``pending_consent``
    until every ecosystem-membership agreement is attested, otherwise ``active``. The configured default
    may be private (the operator chose it); a requested private ecosystem was refused by signup_ecosystem.
    """
    placement = await place_member(
        session, user_id=user.id, ecosystem=ecosystem, display_name=display_name, member_key=member_id,
        trigger=SIGNUP, public_only=False,
    )
    await session.flush()
    return placement.member, placement.missing


async def existing_membership(session, user_id: uuid.UUID) -> Member | None:
    """Oldest membership a returning user already holds (login never re-enrolls them)."""
    return (await session.execute(
        select(Member)
        .where(Member.user_id == user_id)
        .order_by(Member.created_at.asc(), Member.id.asc())
        .limit(1)
    )).scalar_one_or_none()


def _agreement_brief(agreement) -> dict:
    """The {id, title, version} shape every consent-gate payload uses."""
    return {"id": str(agreement.id), "title": agreement.title, "version": agreement.version}


def consent_gate_payload(missing: list, join_gates: dict | None = None) -> dict:
    """Extra sign-up response keys mirroring the join endpoint's consent contract."""
    return {
        "status": (join_gates["status"] if join_gates and join_gates["status"] in {"quiz_required", "quiz_unavailable"}
                   else "consent_required" if missing else "joined"),
        "required_agreements": [_agreement_brief(agreement) for agreement in missing],
        "join_gates": join_gates,
    }


async def pending_consent_gates(session, user_id: uuid.UUID) -> list[dict]:
    """Every membership of the user still behind its ecosystem's agreement-consent gate."""
    rows = (await session.execute(
        select(Member, Ecosystem)
        .join(Ecosystem, Ecosystem.id == Member.ecosystem_id)
        .where(Member.user_id == user_id, Member.current_status == "pending_consent")
        .order_by(Member.created_at.asc(), Member.id.asc())
    )).all()
    gates = []
    for member, ecosystem in rows:
        from neos_agent.services.join_gates import join_gate_summary
        missing = await missing_agreement_consents(session, member.id, ecosystem.id, "ecosystem")
        gates.append({
            "ecosystem_id": str(ecosystem.id),
            "ecosystem_name": ecosystem.name,
            "required_agreements": [_agreement_brief(agreement) for agreement in missing],
            "join_gates": await join_gate_summary(session, ecosystem_id=ecosystem.id, member=member),
        })
    return gates


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

    try:
        requested_id = requested_ecosystem_id(body)
    except SignupEcosystemNotFound:
        return json({"error": "Ecosystem not found"}, status=404)

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

        # Returning users keep their memberships; only a user with none is placed.
        consent_gate = None
        member = await existing_membership(session, user.id)
        if member is None:
            try:
                ecosystem = await signup_ecosystem(session, settings, requested_id)
            except SignupEcosystemNotFound:
                return json({"error": "Ecosystem not found"}, status=404)
            if ecosystem is None:
                return json({"error": "No ecosystem configured"}, status=500)
            member, missing = await create_signup_member(
                session,
                user=user,
                ecosystem=ecosystem,
                member_id=f"did-{did[-12:]}",
                display_name=display_name,
            )
            from neos_agent.services.join_gates import join_gate_summary
            consent_gate = consent_gate_payload(missing, await join_gate_summary(session, ecosystem_id=ecosystem.id, member=member))

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
    payload = response_data.model_dump(mode="json")
    if consent_gate is not None:
        payload.update(consent_gate)
    response = json(payload, status=200)
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
        logger.warning("/auth/me: cookie verification failed")
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
        if not user or user.disabled_at is not None:
            return json({"error": "User not found"}, status=401)

        # Every membership row, any status: the client applies the active-only rule per ecosystem from these.
        member_rows = (await db.execute(select(Member).where(Member.user_id == user.id))).scalars().all()
        eco_ids = [row.ecosystem_id for row in member_rows]
        standing = {row.ecosystem_id: (row.current_status, row.role, can_administer_ecosystem(row, row.ecosystem_id))
                    for row in member_rows}

        # The server's default row (oldest ACTIVE membership, else the oldest), as request.ctx.member without a selection.
        member = await default_member(db, user.id, selected_ids=[], authorized_ids=[])
        if not member and not getattr(request.ctx, "node_admin", False):
            return json({"error": "Member not found"}, status=401)

        member_summary = _member_to_summary(member, user) if member else None
        pending_consents = await pending_consent_gates(db, user.id)

        ecosystems = []
        if eco_ids:
            eco_result = await db.execute(
                select(Ecosystem).where(Ecosystem.id.in_(eco_ids))
            )
            for eco in eco_result.scalars().all():
                # Active members only. Pending sign-ups, and suspended or departed rows, are not counted.
                member_count = await db.scalar(
                    select(func.count(Member.id)).where(Member.ecosystem_id == eco.id, counts_as_member())
                ) or 0
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
        pending_consents=pending_consents,
    )
    payload = response_data.model_dump(mode="json")
    for item in payload["ecosystems"]:  # the caller's own standing there (api/AGENTS.md "Onboarding (G-Onboard)")
        status, role, steward = standing.get(uuid.UUID(item["id"]), (None, None, False))
        item["membership_status"], item["role"] = status, role
        item["is_steward"] = steward  # FX-Onboard: policy.can_administer_ecosystem there, so the client never re-derives it
    payload["is_platform_admin"] = bool(getattr(request.ctx, "platform_admin", False))  # set by G-Authority's middleware
    payload["is_node_admin"] = bool(getattr(request.ctx, "node_admin", False))
    payload["node_admin_badge"] = {"key": "node_admin", "label": "Node admin"} if payload["is_node_admin"] else None
    return json(payload)


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
                        # Expire, never delete: an agent token may reference the row (FK).
                        auth_session.expires_at = _dt.datetime.now(timezone.utc)
                        from neos_agent.services.engagement_delivery import disable_user_devices
                        await disable_user_devices(db, auth_session.user_id, auth_session_id=auth_session.id)
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

        if user is None or user.disabled_at is not None or not user.password_hash:
            return json({"error": "Invalid username or password"}, status=401)

        if not _verify_password(password, user.password_hash):
            return json({"error": "Invalid username or password"}, status=401)

        # Load a member for the response
        member_result = await session.execute(
            select(Member).where(Member.user_id == user.id).limit(1)
        )
        member = member_result.scalar_one_or_none()
        if member is None and not user.node_admin_active:
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

        member_summary = _member_to_summary(member, user) if member else None

    cookie_value = make_session_cookie(str(session_id), settings.SESSION_SECRET)
    response_data = AuthVerifyResponse(
        success=True,
        display_name=member.display_name if member else user.display_name,
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

    Accepts JSON: {"username": "...", "password": "...", "display_name": "...", "ecosystem_id": optional}
    Returns JSON: AuthVerifyResponse with member info plus the consent-gate keys of
    POST /ecosystems/:id/join (status, required_agreements); sets neos_session cookie.
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

    try:
        requested_id = requested_ecosystem_id(body)
    except SignupEcosystemNotFound:
        return json({"error": "Ecosystem not found"}, status=404)

    settings = request.app.ctx.settings

    async with request.app.ctx.db() as session:
        # Check username uniqueness on User
        existing = await session.execute(
            select(User.id).where(User.username == username)
        )
        if existing.scalar_one_or_none() is not None:
            return json({"error": "Username already taken"}, status=409)

        try:
            ecosystem = await signup_ecosystem(session, settings, requested_id)
        except SignupEcosystemNotFound:
            return json({"error": "Ecosystem not found"}, status=404)
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

        member, missing = await create_signup_member(
            session,
            user=user,
            ecosystem=ecosystem,
            member_id=f"usr-{username[:12]}",
            display_name=display_name,
        )
        from neos_agent.services.join_gates import join_gate_summary
        signup_gates = await join_gate_summary(session, ecosystem_id=ecosystem.id, member=member)

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
    payload = response_data.model_dump(mode="json")
    payload.update(consent_gate_payload(missing, signup_gates))
    response = json(payload, status=200)
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
