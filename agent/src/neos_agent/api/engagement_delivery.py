"""Owner notification contacts/devices and signed provider callbacks."""
from __future__ import annotations

from contextlib import asynccontextmanager
from html import escape
import uuid

import httpx
from sanic import Blueprint, html, json
from sqlalchemy import select

from neos_agent.api.errors import ApiError
from neos_agent.api.engagement import require_engagement_write
from neos_agent.auth.middleware import verify_session_cookie
from neos_agent.db.models.engagement import EngagementPushDevice
from neos_agent.services import engagement_delivery as delivery
from neos_agent.services.engagement_providers import ProviderTransport, setting

engagement_delivery_api_bp = Blueprint("engagement_delivery_api", url_prefix="/api/v1/engagement")


def _uuid(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as error:
        raise ApiError(400, "Invalid identifier") from error


def _body(request, allowed):
    body = request.json
    if not isinstance(body, dict) or set(body) - set(allowed):
        raise ApiError(400, "Invalid notification request")
    return body


@asynccontextmanager
async def _transport(request):
    current = getattr(request.app.ctx, "engagement_transport", None)
    if current is not None:
        yield current
        return
    timeout = min(30, max(1, float(setting(request.app.ctx.settings, "ENGAGEMENT_SEND_TIMEOUT_SECONDS", 15))))
    async with httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5), follow_redirects=False) as client:
        yield ProviderTransport(request.app.ctx.settings, client)


@engagement_delivery_api_bp.post("/contacts")
async def create_contact(request):
    user, error = require_engagement_write(request)
    if error:
        return error
    body = _body(request, {"channel", "destination"})
    channel = body.get("channel")
    if channel not in {"email", "sms"}:
        raise ApiError(400, "Choose email or SMS")
    async with _transport(request) as transport:
        result = await delivery.request_contact(request.app.ctx.db, user.id, channel, body.get("destination"),
            request.app.ctx.settings, transport)
    return json(result, status=201)


@engagement_delivery_api_bp.post("/contacts/<contact_id:uuid>/verify")
async def verify_contact(request, contact_id):
    user, error = require_engagement_write(request)
    if error:
        return error
    body = _body(request, {"challenge_id", "code"})
    async with _transport(request) as transport:
        result = await delivery.verify_contact(request.app.ctx.db, user.id, contact_id,
            _uuid(body.get("challenge_id")), body.get("code"), request.app.ctx.settings, transport)
    return json(result)


@engagement_delivery_api_bp.delete("/contacts/<contact_id:uuid>")
async def delete_contact(request, contact_id):
    user, error = require_engagement_write(request)
    if error:
        return error
    async with request.app.ctx.db() as session:
        await delivery.revoke_contact(session, user.id, contact_id)
        await session.commit()
    return json({}, status=204)


@engagement_delivery_api_bp.post("/push")
async def create_push(request):
    user, error = require_engagement_write(request)
    if error:
        return error
    body = _body(request, {"endpoint", "keys", "expirationTime"})
    cookie = request.cookies.get("neos_session", "")
    sid = verify_session_cookie(cookie, request.app.ctx.settings.SESSION_SECRET)
    if not sid:
        raise ApiError(401, "A current browser session is required")
    async with request.app.ctx.db() as session:
        result = await delivery.register_push(session, user.id, _uuid(sid), body, request.app.ctx.settings)
        await session.commit()
    return json(result, status=201)


@engagement_delivery_api_bp.delete("/push")
async def delete_push(request):
    user, error = require_engagement_write(request)
    if error:
        return error
    body = _body(request, {"endpoint"})
    endpoint = body.get("endpoint")
    if not isinstance(endpoint, str) or len(endpoint) > 2048:
        raise ApiError(400, "A browser endpoint is required")
    async with request.app.ctx.db() as session:
        device = (await session.execute(select(EngagementPushDevice).where(
            EngagementPushDevice.user_id == user.id, EngagementPushDevice.endpoint == endpoint,
        ).with_for_update())).scalar_one_or_none()
        if device:
            device.enabled = False
        await session.commit()
    return json({}, status=204)


@engagement_delivery_api_bp.get("/unsubscribe")
async def unsubscribe_preview(request):
    token = request.args.get("token", "")
    delivery.read_unsubscribe_token(token, request.app.ctx.settings)
    return html('<!doctype html><html lang="en"><meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>NEOS notification preferences</title><body><main><h1>Stop these notifications?</h1>'
        '<p>This affects notifications to the destination associated with this link.</p>'
        f'<form method="post"><input type="hidden" name="token" value="{escape(token, quote=True)}">'
        '<button type="submit">Unsubscribe</button></form></main></body></html>',
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                 "Content-Security-Policy": "default-src 'none'; form-action 'self'; frame-ancestors 'none'"})


@engagement_delivery_api_bp.post("/unsubscribe")
async def unsubscribe_apply(request):
    token = request.args.get("token") or request.form.get("token")
    async with request.app.ctx.db() as session:
        result = await delivery.unsubscribe_contact(session, token, request.app.ctx.settings)
        await session.commit()
    return json(result, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})


@engagement_delivery_api_bp.post("/webhooks/resend")
async def resend_webhook(request):
    secret = setting(request.app.ctx.settings, "RESEND_WEBHOOK_SECRET")
    if not secret:
        raise ApiError(503, "Webhook configuration is pending")
    if len(request.body) > 65536:
        raise ApiError(413, "Webhook body is too large")
    try:
        from svix.webhooks import Webhook
        payload = Webhook(secret).verify(request.body, {
            "svix-id": request.headers.get("svix-id", ""),
            "svix-timestamp": request.headers.get("svix-timestamp", ""),
            "svix-signature": request.headers.get("svix-signature", ""),
        })
    except Exception as error:
        raise ApiError(400, "Invalid webhook signature") from error
    if not isinstance(payload, dict):
        raise ApiError(400, "Invalid webhook body")
    receipt_id = request.headers.get("svix-id", "")
    if not receipt_id or len(receipt_id) > 200:
        raise ApiError(400, "Invalid webhook receipt")
    async with request.app.ctx.db() as session:
        result = await delivery.apply_resend_webhook(session, payload, receipt_id)
        await session.commit()
    return json(result)


@engagement_delivery_api_bp.post("/webhooks/twilio")
async def twilio_webhook(request):
    settings = request.app.ctx.settings
    secret = setting(settings, "TWILIO_AUTH_TOKEN")
    public_base = setting(settings, "ENGAGEMENT_API_PUBLIC_URL").rstrip("/")
    if not secret or not public_base:
        raise ApiError(503, "Webhook configuration is pending")
    if len(request.body) > 65536:
        raise ApiError(413, "Webhook body is too large")
    try:
        from twilio.request_validator import RequestValidator
        expected_url = public_base + "/api/v1/engagement/webhooks/twilio"
        if request.query_string:
            raise ValueError("Unexpected callback query")
        valid = RequestValidator(secret).validate(expected_url, request.form,
            request.headers.get("X-Twilio-Signature", ""))
    except Exception as error:
        raise ApiError(400, "Invalid webhook signature") from error
    if not valid:
        raise ApiError(400, "Invalid webhook signature")
    async with request.app.ctx.db() as session:
        result = await delivery.apply_twilio_webhook(session, {key: request.form.get(key) for key in request.form})
        await session.commit()
    return json(result)
