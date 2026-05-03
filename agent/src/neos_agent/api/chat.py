"""JSON-based chat API for the React frontend.

Blueprint: chat_api_bp, url_prefix="/api/v1/chat"

Provides SSE streaming chat using the AI provider, with graceful
fallback when AI is disabled.
"""
from __future__ import annotations

import json
import logging
import uuid
import datetime as _dt

from pydantic import BaseModel
from sanic import Blueprint, json as json_response
from sanic.request import Request
from sanic.response import ResponseStream
from sqlalchemy import select

from neos_agent.db.models import AgentSession
from neos_agent.ai.provider import acompletion, is_ai_enabled

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
    """POST /api/v1/chat/send — SSE streaming chat endpoint.

    Streams AI responses as SSE events. Falls back to a static message
    when AI is not configured.
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    body = request.json or {}
    message = body.get("message", "").strip()
    if not message:
        return json_response({"error": "Message is required"}, status=400)

    if not is_ai_enabled():
        async def disabled_stream(response):
            msg = "AI chat is not configured. Set AI_API_KEY in the server environment to enable chat features."
            await response.write(f"event: append\ndata: {msg}\n\n")
            await response.write("event: done\ndata: \n\n")

        return ResponseStream(
            disabled_stream,
            content_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async def chat_stream(response):
        try:
            result = await acompletion(
                messages=[{"role": "user", "content": message}],
                system="You are a helpful governance assistant for the NEOS platform. Help users understand governance processes, agreements, proposals, and other platform features.",
                max_tokens=1024,
                temperature=0.7,
                stream=True,
            )

            if result is None:
                await response.write("event: append\ndata: AI is currently unavailable. Please try again later.\n\n")
                await response.write("event: done\ndata: \n\n")
                return

            async for chunk in result:
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        await response.write(f"event: append\ndata: {delta.content}\n\n")

            await response.write("event: done\ndata: \n\n")
        except Exception as exc:
            logger.error("Chat streaming failed: %s", exc)
            await response.write(f"event: append\ndata: Chat error: {exc}\n\n")
            await response.write("event: done\ndata: \n\n")

    return ResponseStream(
        chat_stream,
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
