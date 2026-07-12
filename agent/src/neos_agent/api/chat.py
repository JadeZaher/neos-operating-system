"""JSON-based chat API for the React frontend.

Blueprint: chat_api_bp, url_prefix="/api/v1/chat"

Provides an agentic SSE streaming chat with:
- Full governance system prompt (skills, principles, page context)
- 29 governance tools via tool_use
- Persistent sessions saved to AgentSession DB
- Conversation history (up to 20 user messages per session)
- Skill transitions via SkillRouter transition patterns
- Session listing, search, and detail retrieval
- Privacy / sharing for sessions
"""
from __future__ import annotations

import json
import logging
import secrets
import uuid
import datetime as _dt

from sanic import Blueprint, json as json_response
from sanic.request import Request
from sanic.response import ResponseStream
from sqlalchemy import select, or_

from neos_agent.db.models import AgentSession
from neos_agent.ai.provider import acompletion, is_ai_enabled
from neos_agent.agent.governance_tools import get_tool_definitions, execute_tool
from neos_agent.agent.system_prompt import assemble_system_prompt
from neos_agent.agent.router import SkillRouter
from neos_agent.agent.hitl import parse_approval_request

logger = logging.getLogger(__name__)

chat_api_bp = Blueprint("chat_api", url_prefix="/api/v1/chat")

# Maximum agentic loop iterations to prevent runaway tool chains
_MAX_TOOL_ROUNDS = 8

# Hard limit on conversation length (user messages).
# The frontend should warn before hitting this; the backend enforces it.
_MAX_CONVERSATION_MESSAGES = 20

# Shared router instance
_skill_router = SkillRouter()

# Human-friendly labels for tool execution thinking events
_TOOL_DISPLAY_NAMES = {
    "create_agreement_draft": "Creating agreement draft",
    "update_agreement_status": "Updating agreement status",
    "search_agreements": "Searching agreements",
    "get_agreement": "Looking up agreement",
    "create_proposal": "Creating proposal",
    "search_proposals": "Searching proposals",
    "record_advice": "Recording advice",
    "record_consent_position": "Recording consent position",
    "check_quorum": "Checking quorum",
    "create_decision_record": "Creating decision record",
    "search_precedents": "Searching precedents",
    "check_authority": "Checking authority boundaries",
    "get_member_roles": "Looking up member roles",
    "get_domain": "Looking up domain",
    "create_domain_draft": "Creating domain draft",
    "get_active_members": "Looking up active members",
    "list_ecosystems": "Listing ecosystems",
    "get_ecosystem": "Looking up ecosystem",
    "create_conflict_case": "Creating conflict case",
    "triage_conflict": "Triaging conflict",
    "get_emergency_state": "Checking emergency state",
    "declare_emergency": "Declaring emergency",
    "create_exit_record": "Creating exit record",
    "create_safeguard_audit": "Creating safeguard audit",
    "create_repair_agreement": "Creating repair agreement",
    "create_ecosystem": "Creating ecosystem",
    "get_proposal": "Looking up proposal",
    "update_proposal_status": "Updating proposal status",
    "list_domains": "Listing domains",
}


def _get_artifact_info(tool_name: str, result_data: dict | None) -> dict | None:
    """Extract artifact routing info from a successful tool result."""
    if not result_data:
        return None

    ROUTE_MAP = {
        "create_agreement_draft": ("agreement", lambda d: (d.get("id"), d.get("agreement_id"), f"/agreements/{d.get('id')}")),
        "create_proposal": ("proposal", lambda d: (d.get("id"), d.get("proposal_id"), f"/proposals/{d.get('id')}")),
        "create_domain_draft": ("domain", lambda d: (d.get("id"), d.get("domain_id"), f"/domains/{d.get('id')}")),
        "create_conflict_case": ("conflict", lambda d: (d.get("id"), d.get("case_id"), f"/conflicts/{d.get('id')}")),
        "create_exit_record": ("exit", lambda d: (d.get("id"), None, f"/exit/{d.get('id')}")),
        "create_safeguard_audit": ("audit", lambda d: (d.get("id"), d.get("audit_id"), f"/safeguards/audits/{d.get('id')}")),
        "create_repair_agreement": ("repair", lambda d: (d.get("id"), d.get("case_id"), f"/conflicts")),
        "create_decision_record": ("decision", lambda d: (d.get("id"), None, f"/decisions/{d.get('id')}")),
    }

    if tool_name not in ROUTE_MAP:
        return None

    artifact_type, extractor = ROUTE_MAP[tool_name]
    try:
        uid, biz_key, route = extractor(result_data)
        if not uid:
            return None
        return {
            "type": artifact_type,
            "id": uid,
            "business_key": biz_key,
            "route": route,
            "label": biz_key or f"{artifact_type.title()} {uid[:8]}",
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sse_event(event: str, data: str) -> str:
    """Format an SSE event with proper multi-line data handling."""
    lines = data.split("\n")
    data_lines = "\n".join(f"data: {line}" for line in lines)
    return f"event: {event}\n{data_lines}\n\n"


def _sanitize_history(raw_history: list[dict]) -> list[dict]:
    """Validate and sanitize conversation history from the client.

    Only keeps user/assistant text messages (no tool messages — those are
    replayed within a single request's agentic loop, not across requests).
    Enforces the hard message limit.
    """
    clean: list[dict] = []
    user_count = 0
    for entry in raw_history:
        role = entry.get("role")
        content = entry.get("content", "")
        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str):
            continue
        if role == "user":
            user_count += 1
            if user_count > _MAX_CONVERSATION_MESSAGES:
                break
        clean.append({"role": role, "content": content})
    return clean


def _page_to_context(page_context: dict | None) -> str | None:
    """Extract a page context hint keyword from the frontend path."""
    if not page_context:
        return None
    path = page_context.get("path", "")
    for segment in ["agreements", "proposals", "domains", "members", "conflicts",
                     "safeguards", "emergency", "decisions", "exit", "onboarding", "discover"]:
        if segment in path:
            return segment
    return None


def _build_session_context(page_context: dict | None) -> str:
    """Build a rich session context string from frontend page_context."""
    if not page_context:
        return ""
    parts: list[str] = []
    path = page_context.get("path", "")
    if path:
        parts.append(f"Current page: {path}")
    search = page_context.get("search", "")
    if search:
        parts.append(f"URL params: {search}")
    active_view = page_context.get("active_view", "")
    if active_view:
        parts.append(f"Page state: {active_view}")
    member_name = page_context.get("member_name")
    member_id = page_context.get("member_id")
    if member_name:
        parts.append(f"Current user: {member_name} (ID: {member_id})")
    eco_name = page_context.get("ecosystem_name")
    if eco_name:
        parts.append(f"Active ecosystem: {eco_name}")
    # Extract item ID from path (e.g. /agreements/abc-123)
    segments = [s for s in path.split("/") if s]
    if len(segments) >= 2:
        # If second segment looks like an ID (UUID or business key), note it
        candidate = segments[-1]
        if len(candidate) > 8 and candidate not in ("new", "edit"):
            parts.append(f"Viewing item: {candidate}")
    return "\n".join(parts)


def _generate_title(messages: list[dict]) -> str | None:
    """Extract a title from the first user message."""
    for m in messages:
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()[:80]
    return None


async def _save_session(
    request: Request,
    session_id: str | None,
    member,
    messages: list[dict],
    skill_name: str | None,
    total_usage: dict,
    ecosystem_id: uuid.UUID | None,
    ecosystem_ids: list[str] | None,
) -> str:
    """Persist conversation to AgentSession. Returns the session ID."""
    db_factory = getattr(request.app.ctx, "db", None)
    if not db_factory:
        return session_id or str(uuid.uuid4())

    # Only save user/assistant text messages (not tool messages from the loop)
    storable = [m for m in messages if m.get("role") in ("user", "assistant")]

    try:
        async with db_factory() as db:
            sess = None
            if session_id:
                result = await db.execute(
                    select(AgentSession).where(
                        AgentSession.id == uuid.UUID(session_id),
                        AgentSession.member_id == member.id,
                    )
                )
                sess = result.scalar_one_or_none()

            if sess:
                # Update existing session
                sess.context = {"messages": storable}
                sess.skill_name = skill_name
                sess.total_tokens_used = (sess.total_tokens_used or 0) + total_usage.get("total_tokens", 0)
                if not sess.title:
                    sess.title = _generate_title(storable)
            else:
                # Create new session
                eco_id = ecosystem_id or (member.ecosystem_id if hasattr(member, "ecosystem_id") else None)
                if not eco_id:
                    logger.warning("Cannot save session: no ecosystem_id available")
                    return session_id or str(uuid.uuid4())
                new_id = uuid.uuid4()
                sess = AgentSession(
                    id=new_id,
                    ecosystem_id=eco_id,
                    ecosystem_ids=[str(e) for e in ecosystem_ids] if ecosystem_ids else None,
                    member_id=member.id,
                    skill_name=skill_name,
                    title=_generate_title(storable),
                    context={"messages": storable},
                    total_tokens_used=total_usage.get("total_tokens", 0),
                )
                db.add(sess)
                session_id = str(new_id)

            await db.commit()
            return str(sess.id)
    except Exception:
        logger.exception("Failed to save chat session")
        return session_id or str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@chat_api_bp.get("/sessions")
async def list_sessions(request: Request):
    """GET /api/v1/chat/sessions — List chat sessions for current member.

    Query params:
        q: Optional search string to filter by title
        limit: Max results (default 30, max 50)
        offset: Pagination offset (default 0)
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    q = request.args.get("q", "").strip()
    try:
        limit = min(int(request.args.get("limit", "30")), 50)
    except ValueError:
        limit = 30
    try:
        offset = max(int(request.args.get("offset", "0")), 0)
    except ValueError:
        offset = 0

    try:
        async with request.app.ctx.db() as session:
            query = (
                select(AgentSession)
                .where(AgentSession.member_id == member.id)
                .order_by(AgentSession.updated_at.desc())
            )

            if q:
                query = query.where(AgentSession.title.ilike(f"%{q}%"))

            query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            sessions = result.scalars().all()

            items = []
            for s in sessions:
                msgs = (s.context or {}).get("messages", [])
                title = s.title
                if not title:
                    title = _generate_title(msgs)
                msg_count = len([m for m in msgs if m.get("role") == "user"])
                items.append({
                    "id": str(s.id),
                    "title": title,
                    "skill": s.skill_name,
                    "message_count": msg_count,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                })

            return json_response({"sessions": items})
    except Exception:
        logger.exception("Failed to list chat sessions")
        return json_response({"sessions": []})


@chat_api_bp.get("/sessions/<session_id:str>")
async def get_session(request: Request, session_id: str):
    """GET /api/v1/chat/sessions/:id — Load a specific chat session with messages."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

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

            msgs = (sess.context or {}).get("messages", [])
            return json_response({
                "id": str(sess.id),
                "title": sess.title,
                "skill": sess.skill_name,
                "privacy": sess.privacy,
                "share_token": sess.share_token,
                "messages": msgs,
                "created_at": sess.created_at.isoformat() if sess.created_at else None,
                "updated_at": sess.updated_at.isoformat() if sess.updated_at else None,
            })
    except Exception:
        logger.exception("Failed to load chat session")
        return json_response({"error": "Internal error"}, status=500)


@chat_api_bp.delete("/sessions/<session_id:str>")
async def delete_session(request: Request, session_id: str):
    """DELETE /api/v1/chat/sessions/:id — Delete a chat session."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

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

            await db.delete(sess)
            await db.commit()
            return json_response({"ok": True})
    except Exception:
        logger.exception("Failed to delete chat session")
        return json_response({"error": "Internal error"}, status=500)


@chat_api_bp.post("/send")
async def send_message(request: Request):
    """POST /api/v1/chat/send — Agentic SSE streaming chat endpoint.

    Runs a tool-use loop: sends messages to the AI with governance tools,
    executes any tool calls, feeds results back, and streams everything
    as SSE events (append, tool_start, tool_result, usage, session, done).
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    body = request.json or {}
    message = body.get("message", "").strip()
    if not message:
        return json_response({"error": "Message is required"}, status=400)

    page_context = body.get("page_context")
    raw_history = body.get("history", [])
    active_skill = body.get("active_skill")
    session_id = body.get("session_id")

    # Enforce conversation limit server-side
    history = _sanitize_history(raw_history) if isinstance(raw_history, list) else []
    user_msg_count = sum(1 for m in history if m["role"] == "user") + 1
    if user_msg_count > _MAX_CONVERSATION_MESSAGES:
        return json_response({
            "error": f"Conversation limit reached ({_MAX_CONVERSATION_MESSAGES} messages). Please start a new conversation.",
        }, status=400)

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
        nonlocal session_id
        try:
            registry = getattr(request.app.ctx, "skills", None)

            # --- Build system prompt with skill awareness ---
            page_hint = _page_to_context(page_context)
            current_skill = active_skill

            # Use validated ecosystem scope from auth middleware
            eco_scope = getattr(request.ctx, "ecosystem_scope", None)
            ecosystem_names = []
            validated_eco_ids = []
            ecosystem_id = None
            if eco_scope and eco_scope.selected:
                ecosystem_names = [e.name for e in eco_scope.selected]
                validated_eco_ids = [str(eid) for eid in eco_scope.selected_ids]
                ecosystem_id = eco_scope.selected_ids[0] if eco_scope.selected_ids else None
            elif hasattr(member, "ecosystem") and member.ecosystem:
                ecosystem_names = [member.ecosystem.name]
                if member.ecosystem_id:
                    validated_eco_ids = [str(member.ecosystem_id)]
                    ecosystem_id = member.ecosystem_id

            system_prompt = assemble_system_prompt(
                active_skill=current_skill,
                skill_registry=registry,
                page_context=page_hint,
                ecosystem_names=ecosystem_names or None,
                selected_ecosystem_ids=validated_eco_ids or None,
            )

            # Append rich session context (user, page, URL params)
            session_ctx = _build_session_context(page_context)
            if session_ctx:
                system_prompt += f"\n\n## Session Context\n{session_ctx}"

            if current_skill:
                await response.write(_sse_event("skill", current_skill))

            # --- Prepare tool definitions ---
            tool_defs = get_tool_definitions()
            tools_for_api = [
                {"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
                for t in tool_defs
            ] if tool_defs else None

            # --- Agentic loop ---
            messages = history + [{"role": "user", "content": message}]
            total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            # Index marking the boundary between session history and loop-appended messages.
            # Used for safe old-turn pruning in A6(b).
            history_end_idx = len(messages)

            await response.write(_sse_event("thinking", json.dumps({"step": "Analyzing your request..."})))

            for _round in range(_MAX_TOOL_ROUNDS):
                # (A6-b) From round 3 onward, drop the oldest tool-turn pair
                # (assistant-with-tool_calls + its tool results) appended during
                # this request to keep the context window bounded.
                if _round >= 3:
                    # Walk forward from history_end_idx and find the first assistant
                    # message that has tool_calls, plus all immediately following
                    # tool-role messages — then drop that group.
                    loop_messages = messages[history_end_idx:]
                    new_loop: list[dict] = []
                    i = 0
                    dropped = False
                    while i < len(loop_messages):
                        msg = loop_messages[i]
                        if (
                            not dropped
                            and msg.get("role") == "assistant"
                            and isinstance(msg.get("tool_calls"), list)
                        ):
                            # Skip this assistant message and all following tool messages
                            i += 1
                            while i < len(loop_messages) and loop_messages[i].get("role") == "tool":
                                i += 1
                            dropped = True
                            continue
                        new_loop.append(msg)
                        i += 1
                    messages = messages[:history_end_idx] + new_loop
                resp = await acompletion(
                    messages=messages,
                    system=system_prompt,
                    tools=tools_for_api,
                    max_tokens=2048,
                    timeout=60,
                )

                if resp is None:
                    await response.write(_sse_event("append", "AI service is not available."))
                    break

                # Accumulate usage
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

                approval_request = None
                if assistant_msg.content:
                    cleaned_text, approval_request = parse_approval_request(
                        assistant_msg.content,
                    )
                    if approval_request:
                        await response.write(_sse_event("append", cleaned_text))
                        await response.write(_sse_event(
                            "approval_request", json.dumps(approval_request),
                        ))
                    else:
                        await response.write(_sse_event("append", assistant_msg.content))

                # Check for tool calls
                tool_calls = getattr(assistant_msg, "tool_calls", None)
                if not tool_calls or choice.finish_reason != "tool_calls":
                    assistant_record = {"role": "assistant", "content": assistant_msg.content or ""}
                    if approval_request:
                        assistant_record["approval_request"] = approval_request
                    messages.append(assistant_record)
                    break

                # Process tool calls
                messages.append(assistant_msg.model_dump())

                for tc in tool_calls:
                    fn = tc.function
                    tool_name = fn.name
                    try:
                        tool_args = json.loads(fn.arguments) if isinstance(fn.arguments, str) else fn.arguments
                    except json.JSONDecodeError:
                        tool_args = {}

                    display_name = _TOOL_DISPLAY_NAMES.get(
                        tool_name, tool_name.replace("_", " ").title(),
                    )
                    await response.write(_sse_event("thinking", json.dumps({
                        "step": display_name + "...",
                        "tool": tool_name,
                    })))

                    await response.write(_sse_event("tool_start", json.dumps({
                        "name": tool_name,
                        "args": tool_args,
                    })))

                    try:
                        db_factory = getattr(request.app.ctx, "db", None)
                        if db_factory:
                            async with db_factory() as db:
                                result = await execute_tool(tool_name, tool_args, db, ecosystem_ids=validated_eco_ids or None)
                                if result.get("success"):
                                    await db.commit()
                        else:
                            result = {"success": False, "error": "Database unavailable"}
                    except Exception as e:
                        logger.exception("Tool execution failed: %s", tool_name)
                        result = {"success": False, "error": str(e)}

                    artifact = None
                    if result.get("success"):
                        artifact = _get_artifact_info(tool_name, result.get("data"))

                    await response.write(_sse_event("tool_result", json.dumps({
                        "name": tool_name,
                        "success": result.get("success", False),
                        "data": result.get("data") if result.get("success") else None,
                        "error": result.get("error") if not result.get("success") else None,
                        **({"artifact": artifact} if artifact else {}),
                    })))

                    # Inject a ready-made markdown link into the tool content
                    # so the LLM can copy it verbatim into its response.
                    tool_content = dict(result)
                    if artifact:
                        link = f"[{artifact['label']}]({artifact['route']})"
                        tool_content["_link"] = link

                    # (A6-a) Cap oversized tool results to prevent context bloat.
                    serialized = json.dumps(tool_content)
                    if len(serialized) > 2000:
                        tool_content = {
                            "success": tool_content.get("success"),
                            "summary": (
                                f"Result truncated ({len(serialized)} chars). "
                                f"Key fields: {', '.join(list(tool_content.keys())[:8])}"
                            ),
                            "_link": tool_content.get("_link"),
                        }

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_content),
                    })

                await response.write(_sse_event("thinking", json.dumps({"step": "Processing results..."})))

                # --- Skill transition detection via router ---
                if current_skill:
                    round_tool_calls = []
                    for tc in tool_calls:
                        fn = tc.function
                        try:
                            tc_args = json.loads(fn.arguments) if isinstance(fn.arguments, str) else fn.arguments
                        except (json.JSONDecodeError, TypeError):
                            tc_args = {}
                        round_tool_calls.append({
                            "name": fn.name,
                            "args": tc_args,
                            "success": True,
                        })

                    new_skill = _skill_router.detect_transition(
                        current_skill, round_tool_calls, "",
                    )
                    if new_skill is not None and new_skill != current_skill:
                        await response.write(_sse_event("thinking", json.dumps({
                            "step": f"Transitioning to {new_skill}...",
                        })))
                        current_skill = new_skill
                        await response.write(_sse_event("skill_transition", json.dumps({
                            "from": active_skill,
                            "to": new_skill,
                        })))
                        # Rebuild system prompt for the new skill so the next
                        # acompletion call uses the updated persona/context.
                        system_prompt = assemble_system_prompt(
                            active_skill=current_skill,
                            skill_registry=registry,
                            page_context=page_hint,
                            ecosystem_names=ecosystem_names or None,
                            selected_ecosystem_ids=validated_eco_ids or None,
                        )
                        if session_ctx:
                            system_prompt += f"\n\n## Session Context\n{session_ctx}"

            # --- Persist session ---
            session_id = await _save_session(
                request, session_id, member, messages,
                current_skill, total_usage,
                ecosystem_id, validated_eco_ids,
            )
            await response.write(_sse_event("session", json.dumps({"session_id": session_id})))

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
