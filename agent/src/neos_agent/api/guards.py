"""Who is calling: the authentication guard and per-ecosystem caller lookup; see api/AGENTS.md "Handler contracts"."""
from __future__ import annotations

import uuid
from functools import wraps
from typing import Awaitable, Callable, Concatenate, ParamSpec

from sanic.request import Request
from sanic.response import HTTPResponse
from sqlalchemy import select

from neos_agent.api.helpers import get_authorized_ecosystem_ids, require_auth
from neos_agent.db.models import Member

HandlerArguments = ParamSpec("HandlerArguments")
Handler = Callable[Concatenate[Request, HandlerArguments], Awaitable[HTTPResponse]]


# Decorator: authentication guard.
def authenticated(handler: Handler[HandlerArguments]) -> Handler[HandlerArguments]:
    """401 {"error": "Authentication required"} without a signed-in member; the handler reads request.ctx.member."""

    @wraps(handler)  # keeps __name__, which Sanic uses as the route name
    async def guarded(request: Request, *args: HandlerArguments.args, **kwargs: HandlerArguments.kwargs) -> HTTPResponse:
        _, unauthenticated = require_auth(request)
        if unauthenticated is not None:
            return unauthenticated
        return await handler(request, *args, **kwargs)

    return guarded


def _caller_user_id(request: Request) -> uuid.UUID | None:
    user = getattr(request.ctx, "user", None)
    if user is not None:
        return user.id
    member = getattr(request.ctx, "member", None)
    return member.user_id if member is not None else None


# Per-ecosystem identity lookup: the only correct input to policy.py predicates.
async def caller_in(session, request: Request, ecosystem_id: uuid.UUID | None) -> Member | None:
    """The signed-in user's Member row in `ecosystem_id`, or None when they hold none there."""
    user_id = _caller_user_id(request)
    if user_id is None or ecosystem_id is None:
        return None
    return await session.scalar(select(Member).where(
        Member.user_id == user_id,
        Member.ecosystem_id == ecosystem_id,
    ))


# Scope widening for the consent gate: a pending newcomer reads and consents to agreements before they are active.
async def reachable_ecosystem_ids(session, request: Request, *, include_pending: bool = False) -> list[uuid.UUID]:
    """The caller's authorized (active) ecosystems, plus the ones whose membership awaits consent when `include_pending`."""
    authorized = list(get_authorized_ecosystem_ids(request))
    user_id = _caller_user_id(request)
    if not include_pending or user_id is None:
        return authorized
    pending = (await session.scalars(select(Member.ecosystem_id).where(
        Member.user_id == user_id,
        Member.current_status == "pending_consent",
    ))).all()
    return authorized + [ecosystem_id for ecosystem_id in pending if ecosystem_id not in authorized]


# Deterministic default: the row the auth middleware stores as request.ctx.member.
async def default_member(
    session,
    user_id: uuid.UUID,
    *,
    selected_ids: list[uuid.UUID],
    authorized_ids: list[uuid.UUID],
) -> Member | None:
    """The oldest active row in the selected ecosystems, else the oldest active membership, else the oldest at all."""
    oldest_first = (Member.current_status != "active", Member.created_at.asc(), Member.id.asc())
    in_scope = [ecosystem_id for ecosystem_id in selected_ids if ecosystem_id in authorized_ids]
    if in_scope:
        selected = await session.scalar(
            select(Member)
            .where(Member.user_id == user_id, Member.ecosystem_id.in_(in_scope))
            .order_by(*oldest_first)
            .limit(1)
        )
        if selected is not None:
            return selected
    return await session.scalar(
        select(Member).where(Member.user_id == user_id).order_by(*oldest_first).limit(1)
    )
