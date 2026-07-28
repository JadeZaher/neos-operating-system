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
    User,
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
    member_ids: list[uuid.UUID] = []
    try:
        async with app.ctx.db() as db:
            result = await db.execute(
                select(AuthSession).where(
                    AuthSession.id == uuid.UUID(session_id),
                    AuthSession.expires_at > datetime.now(timezone.utc),
                )
            )
            auth_session = result.scalar_one_or_none()
            if not auth_session:
                await ws.close(code=4001, reason="Session expired")
                return
            user = await db.get(User, auth_session.user_id)
            if not user:
                await ws.close(code=4001, reason="User not found")
                return
            # A user holds one Member row per ecosystem — register ALL of them so
            # realtime delivery works for conversations in every ecosystem.
            member_result = await db.execute(
                select(Member).where(Member.user_id == user.id)
            )
            members = list(member_result.scalars().all())
            if not members:
                await ws.close(code=4001, reason="Member not found")
                return
            member = members[0]
            member_ids = [m.id for m in members]
    except Exception:
        logger.exception("WebSocket auth error")
        await ws.close(code=4001, reason="Authentication error")
        return

    for mid in member_ids:
        connection_manager.register(mid, ws)
    logger.info("WebSocket connected: %s (%d member rows)", member.display_name, len(member_ids))

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
                    await handler(ws, member, msg_data, app, member_ids=member_ids)
                except Exception:
                    logger.exception("Handler error for type=%s", msg_type)
                    await ws.send('{"type":"error","data":{"message":"Internal error"}}')
            else:
                await ws.send('{"type":"error","data":{"message":"Unknown message type"}}')
    except Exception:
        logger.debug("WebSocket disconnected: %s", member.id)
    finally:
        keepalive_task.cancel()
        for mid in member_ids:
            connection_manager.unregister(mid, ws)
        logger.info("WebSocket disconnected: %s (%d member rows)", member.display_name, len(member_ids))
