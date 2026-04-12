"""Messaging blueprint with WebSocket endpoint for real-time messaging.

HTML view routes have been removed; conversation management is handled
by the JSON API layer in neos_agent.api.messaging.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sanic import Blueprint
from sanic.request import Request
from sqlalchemy import select

from neos_agent.auth.middleware import verify_session_cookie
from neos_agent.db.models import (
    AuthSession,
    Conversation,
    ConversationParticipant,
    Member,
)
from neos_agent.messaging.connections import connection_manager
from neos_agent.messaging.handlers import (
    handle_message,
    handle_read_receipt,
    handle_typing,
)

logger = logging.getLogger(__name__)

messaging_bp = Blueprint("messaging", url_prefix="/messaging")

# Map of WebSocket message types to handlers
WS_HANDLERS = {
    "message": handle_message,
    "typing": handle_typing,
    "read_receipt": handle_read_receipt,
}


# ===================================================================
# WebSocket endpoint
# ===================================================================


@messaging_bp.websocket("/ws")
async def messaging_ws(request: Request, ws):
    """Authenticated WebSocket endpoint for real-time messaging."""
    app = request.app
    settings = app.ctx.settings

    cookie = request.cookies.get("neos_session")
    if not cookie:
        await ws.close(code=4001, reason="Authentication required")
        return

    session_id = verify_session_cookie(cookie, settings.SESSION_SECRET)
    if not session_id:
        await ws.close(code=4001, reason="Invalid session")
        return

    member = None
    try:
        async with app.ctx.db() as db:
            result = await db.execute(
                select(AuthSession).where(
                    AuthSession.id == uuid.UUID(session_id),
                    AuthSession.expires_at > datetime.utcnow(),
                )
            )
            auth_session = result.scalar_one_or_none()
            if not auth_session:
                await ws.close(code=4001, reason="Session expired")
                return
            member = await db.get(Member, auth_session.member_id)
            if not member:
                await ws.close(code=4001, reason="Member not found")
                return
    except Exception:
        logger.exception("WebSocket auth error")
        await ws.close(code=4001, reason="Authentication error")
        return

    connection_manager.register(member.id, ws)
    logger.info("WebSocket connected: %s (%s)", member.display_name, member.id)

    async def _keepalive():
        try:
            while True:
                await asyncio.sleep(30)
                await ws.ping()
        except Exception:
            pass

    keepalive_task = asyncio.create_task(_keepalive())

    try:
        async for raw in ws:
            try:
                frame = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                await ws.send('{"type":"error","data":{"message":"Invalid JSON"}}')
                continue

            msg_type = frame.get("type")
            msg_data = frame.get("data", {})

            handler = WS_HANDLERS.get(msg_type)
            if handler:
                try:
                    await handler(ws, member, msg_data, app)
                except Exception:
                    logger.exception("Handler error for type=%s", msg_type)
                    await ws.send('{"type":"error","data":{"message":"Internal error"}}')
            else:
                await ws.send('{"type":"error","data":{"message":"Unknown message type"}}')
    except Exception:
        logger.debug("WebSocket disconnected: %s", member.id)
    finally:
        keepalive_task.cancel()
        connection_manager.unregister(member.id, ws)
        logger.info("WebSocket disconnected: %s (%s)", member.display_name, member.id)
