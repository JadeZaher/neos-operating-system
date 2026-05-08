"""JSON-based chat API for the React frontend.

Blueprint: chat_api_bp, url_prefix="/api/v1/chat"

Provides SSE streaming chat using the AI provider, with graceful
fallback when AI is disabled.
"""
from __future__ import annotations

import json
import logging
import secrets
import uuid
import datetime as _dt

from pydantic import BaseModel
from sanic import Blueprint, json as json_response
from sanic.request import Request
from sanic.response import ResponseStream
from sqlalchemy import select, or_

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


def _sse_event(event: str, data: str) -> str:
    """Format an SSE event with proper multi-line data handling."""
    lines = data.split("\n")
    data_lines = "\n".join(f"data: {line}" for line in lines)
    return f"event: {event}\n{data_lines}\n\n"


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
            await response.write(_sse_event("append", msg))
            await response.write(_sse_event("done", ""))

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
                await response.write(_sse_event("append", "AI is currently unavailable. Please try again later."))
                await response.write(_sse_event("done", ""))
                return

            usage = None
            async for chunk in result:
                if hasattr(chunk, "usage") and chunk.usage:
                    usage = chunk.usage
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        await response.write(_sse_event("append", delta.content))

            usage_data = {}
            if usage:
                usage_data = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                    "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) or 0,
                }
                logger.info("Chat token usage: prompt=%d completion=%d total=%d",
                            usage_data["prompt_tokens"], usage_data["completion_tokens"], usage_data["total_tokens"])
            await response.write(_sse_event("usage", json.dumps(usage_data)))
            await response.write(_sse_event("done", ""))
        except Exception as exc:
            logger.exception("Chat streaming failed")
            err_msg = str(exc).replace("\n", " ")
            await response.write(_sse_event("append", f"Chat error: {err_msg}"))
            await response.write(_sse_event("done", ""))

    return ResponseStream(
        chat_stream,
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@chat_api_bp.patch("/sessions/<session_id:str>/privacy")
async def update_session_privacy(request: Request, session_id: str):
    """PATCH /api/v1/chat/sessions/:id/privacy — Update privacy setting."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    body = request.json or {}
    privacy = body.get("privacy", "").strip()
    if privacy not in ("private", "ecosystem", "public"):
        return json_response({"error": "privacy must be private, ecosystem, or public"}, status=400)

    try:
        async with request.app.ctx.db() as db:
            result = await db.execute(
                select(AgentSession).where(
                    AgentSession.id == uuid.UUID(session_id),
                    AgentSession.member_id == member.id,
                )
            )
            sess = result.scalar_one_or_none()
            if not sess:
                return json_response({"error": "Session not found"}, status=404)

            sess.privacy = privacy
            # Generate a share token when making non-private, clear when private
            if privacy != "private" and not sess.share_token:
                sess.share_token = secrets.token_urlsafe(32)
            elif privacy == "private":
                sess.share_token = None

            await db.commit()
            return json_response({
                "privacy": sess.privacy,
                "share_token": sess.share_token,
            })
    except Exception:
        logger.exception("Failed to update session privacy")
        return json_response({"error": "Internal error"}, status=500)


@chat_api_bp.get("/shared/<share_token:str>")
async def get_shared_session(request: Request, share_token: str):
    """GET /api/v1/chat/shared/:token — View a shared chat session (no auth required for public)."""
    member = getattr(request.ctx, "member", None)

    try:
        async with request.app.ctx.db() as db:
            result = await db.execute(
                select(AgentSession).where(AgentSession.share_token == share_token)
            )
            sess = result.scalar_one_or_none()
            if not sess:
                return json_response({"error": "Shared session not found"}, status=404)

            # Access control
            if sess.privacy == "private":
                return json_response({"error": "This session is private"}, status=403)
            if sess.privacy == "ecosystem" and (not member or member.ecosystem_id != sess.ecosystem_id):
                return json_response({"error": "Only ecosystem members can view this session"}, status=403)

            messages = (sess.context or {}).get("messages", [])
            return json_response({
                "id": str(sess.id),
                "title": sess.title,
                "privacy": sess.privacy,
                "messages": messages,
                "created_at": sess.created_at.isoformat() if sess.created_at else None,
            })
    except Exception:
        logger.exception("Failed to fetch shared session")
        return json_response({"error": "Internal error"}, status=500)
