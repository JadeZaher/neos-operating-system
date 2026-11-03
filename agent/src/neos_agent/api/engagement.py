"""Owner-scoped engagement APIs; provider callbacks use a separate blueprint."""
from __future__ import annotations

import uuid
from urllib.parse import urlsplit

from sanic import Blueprint, json
from sqlalchemy import delete, select

from neos_agent.api.errors import ApiError
from neos_agent.api.helpers import require_auth_user
from neos_agent.db.models.engagement import EngagementSubscription
from neos_agent.db.models import User
from neos_agent.services import engagement as service

engagement_api_bp = Blueprint("engagement_api", url_prefix="/api/v1/engagement")


def require_engagement_write(request):
    user, error = require_auth_user(request)
    if error:
        return user, error
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        return None, json({"error": "Use application/json for this request"}, status=415)
    settings = request.app.ctx.settings
    origins = set()
    for configured in [getattr(settings, "FRONTEND_URL", ""), *getattr(settings, "CORS_ORIGINS", "").split(",")]:
        parsed = urlsplit(configured.strip())
        if parsed.scheme in ("https", "http") and parsed.netloc:
            origins.add(parsed.scheme + "://" + parsed.netloc)
    origin = request.headers.get("origin")
    if origin:
        if origin == "null" or origin not in origins:
            return None, json({"error": "This request origin is not allowed"}, status=403)
    elif any(str(key).lower().startswith("sec-fetch-") for key in request.headers):
        return None, json({"error": "A browser request origin is required"}, status=403)
    return user, None


def object_body(request):
    body = request.json
    if not isinstance(body, dict):
        raise ApiError(400, "Expected a JSON object")
    return body


def page_limit(request):
    try:
        value = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        raise ApiError(400, "Invalid page size") from None
    if value < 1 or value > 50:
        raise ApiError(400, "Page size must be between 1 and 50")
    return value


@engagement_api_bp.get("/preferences")
async def preferences(request):
    user, error = require_auth_user(request)
    if error:
        return error
    async with request.app.ctx.db() as session:
        return json(service.preference_payload(await service.get_preference(session, user.id)))


@engagement_api_bp.put("/preferences")
async def put_preferences(request):
    user, error = require_engagement_write(request)
    if error:
        return error
    from neos_agent.services.engagement_delivery import get_capabilities
    data = object_body(request)
    async with request.app.ctx.db() as session:
        await session.execute(select(User.id).where(User.id == user.id).with_for_update())
        capabilities = await get_capabilities(session, user.id, request.app.ctx.settings)
        payload = await service.update_preference(session, user.id, data, capabilities)
        await session.commit()
        return json(payload)


@engagement_api_bp.get("/capabilities")
async def capabilities(request):
    user, error = require_auth_user(request)
    if error:
        return error
    from neos_agent.services.engagement_delivery import get_capabilities
    async with request.app.ctx.db() as session:
        return json(await get_capabilities(session, user.id, request.app.ctx.settings))


@engagement_api_bp.get("/subscriptions")
async def subscriptions(request):
    user, error = require_auth_user(request)
    if error:
        return error
    async with request.app.ctx.db() as session:
        rows = (await session.scalars(select(EngagementSubscription).where(
            EngagementSubscription.user_id == user.id).order_by(
            EngagementSubscription.created_at, EngagementSubscription.id))).all()
        items = []
        for row in rows:
            item = await service.subscription_payload(session, user.id, row)
            if item:
                items.append(item)
        return json({"items": items})


@engagement_api_bp.post("/subscriptions")
async def save_subscription(request):
    user, error = require_engagement_write(request)
    if error:
        return error
    async with request.app.ctx.db() as session:
        payload = await service.save_subscription(session, user.id, object_body(request))
        await session.commit()
        return json(payload)


@engagement_api_bp.delete("/subscriptions/<subscription_id:uuid>")
async def remove_subscription(request, subscription_id: uuid.UUID):
    user, error = require_engagement_write(request)
    if error:
        return error
    async with request.app.ctx.db() as session:
        row = await session.scalar(select(EngagementSubscription).where(
            EngagementSubscription.id == subscription_id, EngagementSubscription.user_id == user.id))
        if row is None:
            raise ApiError(404, "Subscription not found")
        await session.delete(row)
        await session.commit()
        return json({}, status=204)


@engagement_api_bp.get("/scope-options")
async def scopes(request):
    user, error = require_auth_user(request)
    if error:
        return error
    async with request.app.ctx.db() as session:
        return json({"items": await service.scope_options(session, user.id,
            request.args.get("kind", "ecosystem"), request.args.get("q", ""), request.args.get("id"))})


@engagement_api_bp.get("/activity")
async def activity(request):
    user, error = require_auth_user(request)
    if error:
        return error
    limit = page_limit(request)
    ecosystem_id = service.as_uuid(request.args["ecosystem_id"]) if request.args.get("ecosystem_id") else None
    async with request.app.ctx.db() as session:
        return json(await service.activity_page(session, user.id, ecosystem_id=ecosystem_id,
            cursor=request.args.get("cursor"), limit=limit))


@engagement_api_bp.get("/inbox")
async def inbox(request):
    user, error = require_auth_user(request)
    if error:
        return error
    unread = request.args.get("unread", "false")
    if unread not in ("true", "false"):
        raise ApiError(400, "Unread filter must be true or false")
    limit = page_limit(request)
    async with request.app.ctx.db() as session:
        await service.fanout_pending(session, limit=3)
        payload = await service.inbox_page(session, user.id, unread=unread == "true",
            cursor=request.args.get("cursor"), limit=limit)
        await session.commit()
        return json(payload)


@engagement_api_bp.patch("/inbox/<item_id:uuid>")
async def read_item(request, item_id: uuid.UUID):
    user, error = require_engagement_write(request)
    if error:
        return error
    body = object_body(request)
    if set(body) != {"read"} or type(body["read"]) is not bool:
        raise ApiError(400, "Specify read as true or false")
    async with request.app.ctx.db() as session:
        payload = await service.mark_inbox(session, user.id, [item_id], read=body["read"])
        await session.commit()
        return json(payload[0])


@engagement_api_bp.post("/inbox/read")
async def read_items(request):
    user, error = require_engagement_write(request)
    if error:
        return error
    body = object_body(request)
    ids = body.get("ids")
    if set(body) != {"ids"} or not isinstance(ids, list) or not 1 <= len(ids) <= 50:
        raise ApiError(400, "Choose between 1 and 50 updates")
    identifiers = [service.as_uuid(value) for value in ids]
    async with request.app.ctx.db() as session:
        payload = await service.mark_inbox(session, user.id, identifiers)
        await session.commit()
        return json({"items": payload})
