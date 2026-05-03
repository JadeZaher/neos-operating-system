"""JSON API blueprint for push notification subscriptions and preferences.

Blueprint: notifications_api_bp, url_prefix="/api/v1/notifications"

All endpoints require authentication via the neos_session cookie.
Returns JSON responses only.
"""

from __future__ import annotations

import logging

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select, delete

from neos_agent.db.models import PushSubscription

from .helpers import require_auth

logger = logging.getLogger(__name__)

notifications_api_bp = Blueprint("notifications_api", url_prefix="/api/v1/notifications")


# ---------------------------------------------------------------------------
# Subscribe / Unsubscribe
# ---------------------------------------------------------------------------


@notifications_api_bp.post("/subscribe")
async def subscribe(request: Request):
    """Store or update a Web Push subscription for the authenticated member."""
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    endpoint = body.get("endpoint")
    keys = body.get("keys") or {}
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")
    notification_types = body.get("notification_types")

    if not endpoint or not p256dh or not auth:
        return json({"error": "endpoint, keys.p256dh, and keys.auth are required"}, status=400)

    async with request.app.ctx.db() as session:
        # Check for existing subscription with same member + endpoint
        result = await session.execute(
            select(PushSubscription).where(
                PushSubscription.member_id == member.id,
                PushSubscription.endpoint == endpoint,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.p256dh_key = p256dh
            existing.auth_key = auth
            existing.enabled = True
            if notification_types is not None:
                existing.notification_types = notification_types
        else:
            sub = PushSubscription(
                member_id=member.id,
                endpoint=endpoint,
                p256dh_key=p256dh,
                auth_key=auth,
                notification_types=notification_types,
            )
            session.add(sub)

        await session.commit()

    return json({"status": "subscribed"}, status=201)


@notifications_api_bp.delete("/subscribe")
async def unsubscribe(request: Request):
    """Remove a Web Push subscription for the authenticated member."""
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    endpoint = body.get("endpoint")

    if not endpoint:
        return json({"error": "endpoint is required"}, status=400)

    async with request.app.ctx.db() as session:
        await session.execute(
            delete(PushSubscription).where(
                PushSubscription.member_id == member.id,
                PushSubscription.endpoint == endpoint,
            )
        )
        await session.commit()

    return json({}, status=204)


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------


@notifications_api_bp.get("/preferences")
async def get_preferences(request: Request):
    """Return the notification_types for all of the member's active subscriptions."""
    member, err = require_auth(request)
    if err:
        return err

    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(PushSubscription).where(
                PushSubscription.member_id == member.id,
                PushSubscription.enabled.is_(True),
            )
        )
        subs = result.scalars().all()

    # Merge preferences across all subscriptions (all should be in sync)
    merged: dict = {}
    for sub in subs:
        if sub.notification_types:
            merged.update(sub.notification_types)

    return json({"notification_types": merged})


@notifications_api_bp.put("/preferences")
async def update_preferences(request: Request):
    """Update notification_types for all of the member's subscriptions."""
    member, err = require_auth(request)
    if err:
        return err

    body = request.json or {}
    notification_types = body.get("notification_types")

    if notification_types is None:
        return json({"error": "notification_types is required"}, status=400)

    # Validate expected keys
    allowed_keys = {"agreement_reviews", "consent_rounds", "proposal_deadlines", "conflict_updates"}
    invalid = set(notification_types.keys()) - allowed_keys
    if invalid:
        return json({"error": f"Unknown notification type(s): {sorted(invalid)}"}, status=400)

    async with request.app.ctx.db() as session:
        result = await session.execute(
            select(PushSubscription).where(
                PushSubscription.member_id == member.id,
            )
        )
        subs = result.scalars().all()

        for sub in subs:
            sub.notification_types = notification_types

        await session.commit()

    return json({"status": "updated", "notification_types": notification_types})
