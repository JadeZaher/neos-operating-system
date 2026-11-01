"""JSON API blueprint for Ethos access & participation consent.

Blueprint: ethos_access_api_bp, url_prefix="/api/v1/ethos"

Backs the ConsentGate: a member records participation consent for an ethos
(ecosystem) before viewing its member directory and taking part. Admins may
grant or revoke access directly. Consent/access is modeled as the presence of
an EthosUserAccess row for (member, ecosystem). See api/AGENTS.md.
"""

from __future__ import annotations

import logging
import uuid

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.api.schemas.ethos_access import (
    EthosAccessGrant,
    EthosAccessGrantRequest,
    EthosAccessStatus,
)
from neos_agent.db.models import EthosUserAccess, Member
from neos_agent.api.errors import ApiError
from neos_agent.api.guards import authenticated, caller_in, caller_in_or_join_required
from neos_agent.api.helpers import require_admin

logger = logging.getLogger(__name__)


ethos_access_api_bp = Blueprint("ethos_access_api", url_prefix="/api/v1/ethos")


def _access_to_status(a: EthosUserAccess | None) -> dict:
    return EthosAccessStatus(
        has_access=a is not None,
        role_in_ethos=a.role_in_ethos if a else None,
        access_level=a.access_level if a else None,
    ).model_dump(mode="json")


def _access_to_grant(a: EthosUserAccess, member_name: str | None) -> dict:
    return EthosAccessGrant(
        id=a.id,
        member_id=a.member_id,
        member_name=member_name,
        ecosystem_id=a.ecosystem_id,
        role_in_ethos=a.role_in_ethos,
        access_level=a.access_level,
        granted_at=a.granted_at,
        granted_by=a.granted_by,
    ).model_dump(mode="json")


@ethos_access_api_bp.get("/<ecosystem_id:uuid>/access/me")
@authenticated
async def get_my_ethos_access(request: Request, ecosystem_id: uuid.UUID):
    """GET /api/v1/ethos/:ecosystem_id/access/me -- Current member's access/consent status."""
    async with request.app.ctx.db() as session:
        # Access is per (member, ecosystem): the caller's row in THIS ethos, not the default row.
        member = await caller_in(session, request, ecosystem_id)
        access = None
        if member is not None:
            stmt = select(EthosUserAccess).where(
                EthosUserAccess.member_id == member.id,
                EthosUserAccess.ecosystem_id == ecosystem_id,
            )
            access = (await session.execute(stmt)).scalar_one_or_none()

    return json(_access_to_status(access))


@ethos_access_api_bp.post("/<ecosystem_id:uuid>/access/consent")
@authenticated
async def consent_ethos_access(request: Request, ecosystem_id: uuid.UUID):
    """POST /api/v1/ethos/:ecosystem_id/access/consent -- Record self-service participation consent (idempotent)."""
    async with request.app.ctx.db() as session:
        member = await caller_in_or_join_required(
            session, request, ecosystem_id,
            not_found="Ethos not found", join_message="Join this ecosystem to consent to participate in it",
        )

        stmt = select(EthosUserAccess).where(
            EthosUserAccess.member_id == member.id,
            EthosUserAccess.ecosystem_id == ecosystem_id,
        )
        access = (await session.execute(stmt)).scalar_one_or_none()
        if access is None:
            access = EthosUserAccess(
                id=uuid.uuid4(),
                member_id=member.id,
                ecosystem_id=ecosystem_id,
                role_in_ethos="member",
                access_level="member",
                granted_by=member.id,
            )
            session.add(access)
            await session.commit()
            await session.refresh(access)

    return json(_access_to_status(access), status=201)


@ethos_access_api_bp.get("/<ecosystem_id:uuid>/access")
async def list_ethos_access(request: Request, ecosystem_id: uuid.UUID):
    """GET /api/v1/ethos/:ecosystem_id/access -- Admin: list all access grants for an ethos."""
    _admin, err = require_admin(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        stmt = (
            select(EthosUserAccess, Member.display_name)
            .join(Member, Member.id == EthosUserAccess.member_id)
            .where(EthosUserAccess.ecosystem_id == ecosystem_id)
            .order_by(EthosUserAccess.granted_at.desc())
        )
        rows = (await session.execute(stmt)).all()

    items = [_access_to_grant(a, name) for a, name in rows]
    return json({"items": items, "total": len(items)})


@ethos_access_api_bp.post("/<ecosystem_id:uuid>/access")
async def grant_ethos_access(request: Request, ecosystem_id: uuid.UUID):
    """POST /api/v1/ethos/:ecosystem_id/access -- Admin: grant a member access to an ethos."""
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        grant_req = EthosAccessGrantRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        target = await session.get(Member, grant_req.member_id)
        if target is None:
            raise ApiError(404, "Member not found")
        granter = await caller_in(session, request, ecosystem_id) or admin

        stmt = select(EthosUserAccess).where(
            EthosUserAccess.member_id == grant_req.member_id,
            EthosUserAccess.ecosystem_id == ecosystem_id,
        )
        access = (await session.execute(stmt)).scalar_one_or_none()
        if access is None:
            access = EthosUserAccess(
                id=uuid.uuid4(),
                member_id=grant_req.member_id,
                ecosystem_id=ecosystem_id,
                role_in_ethos=grant_req.role_in_ethos or "member",
                access_level=grant_req.access_level or "member",
                granted_by=granter.id,
            )
            session.add(access)
        else:
            if grant_req.role_in_ethos is not None:
                access.role_in_ethos = grant_req.role_in_ethos
            if grant_req.access_level is not None:
                access.access_level = grant_req.access_level
        await session.commit()
        await session.refresh(access)

    return json(_access_to_grant(access, target.display_name), status=201)


@ethos_access_api_bp.delete("/<ecosystem_id:uuid>/access/<member_id:uuid>")
async def revoke_ethos_access(request: Request, ecosystem_id: uuid.UUID, member_id: uuid.UUID):
    """DELETE /api/v1/ethos/:ecosystem_id/access/:member_id -- Admin: revoke a member's access."""
    _admin, err = require_admin(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        stmt = select(EthosUserAccess).where(
            EthosUserAccess.member_id == member_id,
            EthosUserAccess.ecosystem_id == ecosystem_id,
        )
        access = (await session.execute(stmt)).scalar_one_or_none()
        if access is None:
            raise ApiError(404, "Access grant not found")
        await session.delete(access)
        await session.commit()

    return json({"success": True})
