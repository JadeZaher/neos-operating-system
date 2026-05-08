"""JSON-based chat API for the React frontend.

Blueprint: chat_api_bp, url_prefix="/api/v1/chat"

Provides an agentic SSE streaming chat with:
- Full governance system prompt (skills, principles, page context)
- 23 governance tools via tool_use
- Skill matching from trigger conditions
- Token usage logging
- Privacy / sharing for sessions
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
from sqlalchemy import select

from neos_agent.db.models import AgentSession
from neos_agent.ai.provider import is_ai_enabled
from neos_agent.agent.governance_tools import get_tool_definitions, execute_tool
from neos_agent.agent.system_prompt import assemble_system_prompt

logger = logging.getLogger(__name__)

chat_api_bp = Blueprint("chat_api", url_prefix="/api/v1/chat")

# Maximum agentic loop iterations to prevent runaway tool chains
_MAX_TOOL_ROUNDS = 8


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _match_skill(message: str, registry) -> str | None:
    """Match user message to a skill via trigger condition keywords.

    Scans Section C (Trigger Conditions) of each skill for keyword overlap
    with the user's message. Returns the best-matching skill name, or None.
    """
    if not registry or not registry.is_loaded:
        return None

    msg_lower = message.lower()
    best_skill = None
    best_score = 0

    for skill in registry.all_skills():
        try:
            parsed = registry.get(skill.name)
        except KeyError:
            continue

        trigger_text = (parsed.content.sections or {}).get("C", "") or ""
        if not trigger_text:
            continue

        # Simple keyword overlap scoring
        trigger_words = set(trigger_text.lower().split())
        msg_words = set(msg_lower.split())
        # Filter out tiny words
        trigger_words = {w for w in trigger_words if len(w) > 3}
        overlap = trigger_words & msg_words
        score = len(overlap)

        if score > best_score:
            best_score = score
            best_skill = skill.name

    # Require at least 2 keyword matches to activate a skill
    return best_skill if best_score >= 2 else None


def _page_to_context(page_context: dict | None) -> str | None:
    """Extract a page context hint from the frontend's page_context object."""
    if not page_context:
        return None
    path = page_context.get("path", "")
    # Match known governance page segments
    for segment in ["agreements", "proposals", "domains", "members", "conflicts",
                     "safeguards", "emergency", "decisions", "exit", "onboarding", "discover"]:
        if segment in path:
            return segment
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


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
    """POST /api/v1/chat/send — Agentic SSE streaming chat endpoint.

    Runs a tool-use loop: sends messages to the AI with governance tools,
    executes any tool calls, feeds results back, and streams everything
    as SSE events (append, tool_start, tool_result, usage, done).
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    body = request.json or {}
    message = body.get("message", "").strip()
    if not message:
        return json_response({"error": "Message is required"}, status=400)

    page_context = body.get("page_context")

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
            import litellm
            from neos_agent.config import get_settings
            settings = get_settings()

            registry = getattr(request.app.ctx, "skills", None)

            # --- Build system prompt with skill awareness ---
            page_hint = _page_to_context(page_context)
            matched_skill = _match_skill(message, registry)

            # Use validated ecosystem scope from auth middleware (anti-spoof:
            # middleware already filters cookie IDs to only those the user
            # has active membership in).
            eco_scope = getattr(request.ctx, "ecosystem_scope", None)
            ecosystem_names = []
            validated_eco_ids = []
            if eco_scope and eco_scope.selected:
                ecosystem_names = [e.name for e in eco_scope.selected]
                validated_eco_ids = [str(eid) for eid in eco_scope.selected_ids]
            elif hasattr(member, "ecosystem") and member.ecosystem:
                ecosystem_names = [member.ecosystem.name]
                if member.ecosystem_id:
                    validated_eco_ids = [str(member.ecosystem_id)]

            system_prompt = assemble_system_prompt(
                active_skill=matched_skill,
                skill_registry=registry,
                page_context=page_hint,
                ecosystem_names=ecosystem_names or None,
                selected_ecosystem_ids=validated_eco_ids or None,
            )

            # Notify client which skill was matched
            if matched_skill:
                await response.write(_sse_event("skill", matched_skill))

            # --- Prepare tool definitions ---
            tools = get_tool_definitions()

            # --- Agentic loop ---
            messages = [{"role": "user", "content": message}]
            total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            litellm.drop_params = True
            base_kwargs = {
                "model": settings.AI_MODEL,
                "api_key": settings.AI_API_KEY,
                "temperature": 0.7,
                "max_tokens": 2048,
                "timeout": 60,
            }
            if settings.AI_BASE_URL:
                base_kwargs["api_base"] = settings.AI_BASE_URL

            for _ in range(_MAX_TOOL_ROUNDS):
                # Non-streaming call to support tool_use detection
                resp = await litellm.acompletion(
                    **base_kwargs,
                    messages=[{"role": "system", "content": system_prompt}] + messages,
                    tools=[{"type": "function", "function": t} for t in tools] if tools else None,
                    stream=False,
                )

                # Accumulate usage (litellm types are dynamic)
                usage = getattr(resp, "usage", None)
                if usage:
                    total_usage["prompt_tokens"] += getattr(usage, "prompt_tokens", 0) or 0
                    total_usage["completion_tokens"] += getattr(usage, "completion_tokens", 0) or 0
                    total_usage["total_tokens"] += getattr(usage, "total_tokens", 0) or 0

                choices = getattr(resp, "choices", None)
                choice = choices[0] if choices else None
                if not choice:
                    break

                assistant_msg = choice.message

                # Stream any text content
                if assistant_msg.content:
                    await response.write(_sse_event("append", assistant_msg.content))

                # Check for tool calls
                tool_calls = getattr(assistant_msg, "tool_calls", None)
                if not tool_calls or choice.finish_reason != "tool_calls":
                    # No tool calls — we're done
                    messages.append({"role": "assistant", "content": assistant_msg.content or ""})
                    break

                # Process tool calls
                # Add assistant message with tool_calls to conversation
                messages.append(assistant_msg.model_dump())

                for tc in tool_calls:
                    fn = tc.function
                    tool_name = fn.name
                    try:
                        tool_args = json.loads(fn.arguments) if isinstance(fn.arguments, str) else fn.arguments
                    except json.JSONDecodeError:
                        tool_args = {}

                    # Notify client: tool starting
                    await response.write(_sse_event("tool_start", json.dumps({
                        "name": tool_name,
                        "args": tool_args,
                    })))

                    # Execute the tool
                    try:
                        db_factory = getattr(request.app.ctx, "db", None)
                        if db_factory:
                            async with db_factory() as db:
                                result = await execute_tool(tool_name, tool_args, db, ecosystem_ids=validated_eco_ids or None)
                        else:
                            result = {"success": False, "error": "Database unavailable"}
                    except Exception as e:
                        logger.exception("Tool execution failed: %s", tool_name)
                        result = {"success": False, "error": str(e)}

                    # Notify client: tool result
                    await response.write(_sse_event("tool_result", json.dumps({
                        "name": tool_name,
                        "success": result.get("success", False),
                        "data": result.get("data") if result.get("success") else None,
                        "error": result.get("error") if not result.get("success") else None,
                    })))

                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    })

                # Loop continues — model will process tool results

            # Send usage
            if total_usage["total_tokens"] > 0:
                logger.info("Chat token usage: prompt=%d completion=%d total=%d",
                            total_usage["prompt_tokens"], total_usage["completion_tokens"],
                            total_usage["total_tokens"])
            await response.write(_sse_event("usage", json.dumps(total_usage)))
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
    """GET /api/v1/chat/shared/:token — View a shared chat session."""
    member = getattr(request.ctx, "member", None)

    try:
        async with request.app.ctx.db() as db:
            result = await db.execute(
                select(AgentSession).where(AgentSession.share_token == share_token)
            )
            sess = result.scalar_one_or_none()
            if not sess:
                return json_response({"error": "Shared session not found"}, status=404)

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
