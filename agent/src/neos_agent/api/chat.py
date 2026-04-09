"""JSON-based chat API for the React frontend.

Blueprint: chat_api_bp, url_prefix="/api/v1/chat"

Wraps the existing chat SSE handler to emit JSON events instead of HTML.
"""
from __future__ import annotations

import json
import logging
import uuid
import datetime as _dt

from pydantic import BaseModel
from sanic import Blueprint, json as json_response
from sanic.request import Request
from sqlalchemy import select

from neos_agent.db.models import AgentSession

logger = logging.getLogger(__name__)

chat_api_bp = Blueprint("chat_api", url_prefix="/api/v1/chat")


class ChatSendRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatSessionSchema(BaseModel):
    id: str
    title: str | None = None
    created_at: str


@chat_api_bp.get("/sessions")
async def list_sessions(request: Request):
    """GET /api/v1/chat/sessions — List chat sessions for current member."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    try:
        async with request.app.ctx.db() as session:
            result = await session.execute(
                select(AgentSession)
                .where(AgentSession.member_id == member.id)
                .order_by(AgentSession.updated_at.desc())
                .limit(20)
            )
            sessions = result.scalars().all()
            items = []
            for s in sessions:
                messages = (s.context or {}).get("messages", [])
                title = s.title
                if not title and messages:
                    for m in messages:
                        if m.get("role") == "user":
                            content = m.get("content", "")
                            if isinstance(content, str):
                                title = content[:80]
                            break
                items.append({
                    "id": str(s.id),
                    "title": title,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                })
            return json_response({"sessions": items})
    except Exception:
        logger.exception("Failed to list chat sessions")
        return json_response({"sessions": []})


@chat_api_bp.post("/send")
async def send_message(request: Request):
    """POST /api/v1/chat/send — JSON redirect for simpler integrations.

    The primary SSE chat endpoint is POST /chat/send which streams HTML
    fragments. The React ChatPanel uses that endpoint directly via fetch().

    This endpoint handles session management and redirects clients to the
    correct SSE endpoint for streaming.
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    body = request.json or {}
    message = body.get("message", "").strip()
    if not message:
        return json_response({"error": "Message is required"}, status=400)

    # For now, redirect to the existing /chat/send endpoint.
    # The React ChatPanel already uses fetch() with SSE parsing.
    return json_response({
        "redirect": "/chat/send",
        "note": "Use POST /chat/send directly for SSE streaming. This endpoint is for session management.",
    })
