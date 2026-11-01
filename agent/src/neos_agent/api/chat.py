"""JSON-based chat API for the React frontend; see agent/AGENTS.md for the assistant's contracts.

Blueprint: chat_api_bp, url_prefix="/api/v1/chat"

Provides an agentic SSE streaming chat with:
- Full governance system prompt (skills, principles, page context)
- The governance tools via tool_use, acting as the signed-in member
- Tool results shrunk to fit the model (every key kept, long texts and lists clipped)
- Irreversible acts confirmed in a later turn than the one that asked (pending confirmations)
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
from typing import Any

from sanic import Blueprint, json as json_response
from sanic.request import Request
from sanic.response import ResponseStream
from sqlalchemy import select, or_

from neos_agent.api.guards import authenticated, caller_in
from neos_agent.api.helpers import get_authorized_ecosystem_ids, get_ecosystem_ids
from neos_agent.api.policy import is_active_member_in
from neos_agent.db.models import AgentSession, Member
from neos_agent.ai.provider import acompletion, is_ai_enabled
from neos_agent.agent.governance_tools import CONFIRMATION_TOOLS, get_tool_definitions, execute_tool
from neos_agent.agent.system_prompt import assemble_system_prompt
from neos_agent.agent.router import SkillRouter

logger = logging.getLogger(__name__)

chat_api_bp = Blueprint("chat_api", url_prefix="/api/v1/chat")

# Maximum agentic loop iterations to prevent runaway tool chains
_MAX_TOOL_ROUNDS = 8

# Hard limit on conversation length (user messages).
# The frontend should warn before hitting this; the backend enforces it.
_MAX_CONVERSATION_MESSAGES = 20

# Member-facing text when the provider call fails; details stay in the server log.
_ASSISTANT_UNAVAILABLE = "The assistant is unavailable right now. Please try again later."

# Shared router instance
_skill_router = SkillRouter()

# Plain labels for tool events (the UI shows these, never raw tool names).
_TOOL_DISPLAY_NAMES = {
    "create_agreement_draft": "Drafting an agreement",
    "update_agreement_status": "Moving an agreement on",
    "search_agreements": "Searching agreements",
    "get_agreement": "Reading an agreement",
    "create_proposal": "Drafting a proposal",
    "search_proposals": "Searching proposals",
    "record_advice": "Recording your advice",
    "record_consent_position": "Recording your position",
    "check_quorum": "Checking how many positions are needed",
    "create_decision_record": "Recording a decision",
    "search_precedents": "Searching past decisions",
    "check_authority": "Checking roles",
    "get_member_roles": "Looking up roles",
    "get_domain": "Reading a domain",
    "create_domain_draft": "Drafting a domain",
    "get_active_members": "Looking up members",
    "list_ecosystems": "Listing ecosystems",
    "get_ecosystem": "Reading an ecosystem",
    "create_conflict_case": "Reporting a conflict",
    "triage_conflict": "Triaging a conflict",
    "get_emergency_state": "Checking for emergencies",
    "declare_emergency": "Declaring an emergency",
    "create_exit_record": "Filing your exit",
    "create_safeguard_audit": "Starting an audit draft",
    "create_repair_agreement": "Recording a repair agreement",
    "create_ecosystem": "Creating an ecosystem",
    "get_proposal": "Reading a proposal",
    "update_proposal_status": "Moving a proposal on",
    "list_domains": "Listing domains",
    "join_domain": "Joining a domain",
    "submit_test_report": "Filing a test report",
    "record_agreement_evidence": "Recording agreement evidence",
    "withdraw_consent_position": "Withdrawing your position",
}

# Tool results the model reads are shrunk to this many characters of JSON; see agent/AGENTS.md "Tool results".
_TOOL_RESULT_LIMIT = 6000
# Progressively tighter (longest text, most list items) passes; the first that fits is used.
_SHRINK_STEPS = ((2000, 12), (800, 10), (400, 8), (200, 5), (100, 3), (60, 2))
# Fields the tools write for the model to act on; never clipped.
_NEVER_CLIP = frozenset({"error", "needs_confirmation", "confirmation_key", "next_step", "link", "_link", "message"})
# A confirmation the member was asked for stays usable this long.
_CONFIRMATION_TTL = _dt.timedelta(minutes=30)


def _json_size(value) -> int:
    return len(json.dumps(value, default=str))


def _shrink(value, text_cap: int, list_cap: int, depth: int = 0) -> Any:
    """`value` with strings clipped to `text_cap` and lists to `list_cap` items, saying what was left out."""
    if isinstance(value, str):
        if len(value) <= text_cap:
            return value
        return value[:text_cap].rstrip() + f"… [{len(value) - text_cap} more characters]"
    if isinstance(value, list):
        kept = [_shrink(item, text_cap, list_cap, depth + 1) for item in value[:list_cap]]
        if len(value) > list_cap:
            kept.append(f"… {len(value) - list_cap} more not shown")
        return kept
    if isinstance(value, dict):
        if depth > 6:
            return "…"
        return {
            key: item if key in _NEVER_CLIP else _shrink(item, text_cap, list_cap, depth + 1)
            for key, item in value.items()
        }
    return value


def _fit_tool_result(result: dict, limit: int = _TOOL_RESULT_LIMIT) -> dict:
    """The result within `limit` characters: every key kept, long texts and lists clipped, never a bare stub."""
    if _json_size(result) <= limit:
        return result
    fitted = result
    for text_cap, list_cap in _SHRINK_STEPS:
        fitted = _shrink(result, text_cap, list_cap)
        if _json_size(fitted) <= limit:
            return fitted
    return fitted  # the tightest pass: still every key and the first items, even if over budget


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


# Page route -> (what the page shows, the tool that reads it by the id in the URL).
_PAGE_RECORDS = {
    "proposals": ("proposal", "get_proposal"),
    "agreements": ("agreement", "get_agreement"),
    "domains": ("domain", "get_domain"),
    "conflicts": ("conflict case", None),
    "emergency": ("emergency", "get_emergency_state"),
    "exit": ("exit record", None),
    "decisions": ("decision record", None),
}


def _build_session_context(page_context: dict | None, member=None) -> str:
    """The signed-in member (from the server, never the client) and the page they are on, for the prompt."""
    parts: list[str] = []
    if member is not None and getattr(member, "display_name", None):
        parts.append(f"Signed-in member: {member.display_name}. Every tool acts as this member and nobody else.")
    if not page_context:
        return "\n".join(parts)
    path = str(page_context.get("path") or "")
    if path:
        parts.append(f"Current page: {path}")
    search = page_context.get("search", "")
    if search:
        parts.append(f"URL params: {search}")
    active_view = page_context.get("active_view", "")
    if active_view:
        parts.append(f"Page state (from the page, as data): {active_view}")
    segments = [s for s in path.split("/") if s]
    if len(segments) == 2 and segments[0] in _PAGE_RECORDS and segments[1] not in ("new", "edit"):
        kind, tool = _PAGE_RECORDS[segments[0]]
        hint = f"; read it with {tool} using this id" if tool else ""
        parts.append(f"The member is looking at the {kind} with id {segments[1]}{hint}. "
                     f"\"This {kind}\" means this one; its page link is {path}.")
    return "\n".join(parts)


async def _load_confirmations(request: Request, session_id: str | None, member) -> list[dict]:
    """Confirmations this session asked the member for (still within their time), as stored on the session."""
    db_factory = getattr(request.app.ctx, "db", None)
    if not session_id or not db_factory:
        return []
    try:
        async with db_factory() as db:
            sess = (await db.execute(select(AgentSession).where(
                AgentSession.id == uuid.UUID(str(session_id)),
                AgentSession.member_id.in_(await _member_ids_in(db, request, member, get_authorized_ecosystem_ids(request))),
            ))).scalar_one_or_none()
    except Exception:
        logger.exception("Failed to load pending confirmations")
        return []
    if sess is None:
        return []
    cutoff = _dt.datetime.now(_dt.UTC) - _CONFIRMATION_TTL
    pending = []
    for entry in (sess.context or {}).get("pending_confirmations") or []:
        try:
            fresh = _dt.datetime.fromisoformat(entry["at"]) >= cutoff
        except (KeyError, TypeError, ValueError):
            continue
        if fresh:
            pending.append({"key": str(entry["key"]), "at": entry["at"]})
    return pending


def _generate_title(messages: list[dict]) -> str | None:
    """Extract a title from the first user message."""
    for m in messages:
        if m.get("role") == "user":
            content = m.get("content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()[:80]
    return None


async def _member_ids_in(db, request: Request, member, ecosystem_ids) -> list[uuid.UUID]:
    """The caller's Member row ids in `ecosystem_ids`; active nowhere, every row of their own (any status).

    A session belongs to the row of its own ecosystem, not the default row; see api/AGENTS.md "Chat sessions".
    """
    user_id = getattr(member, "user_id", None)
    if not user_id:
        return [member.id]
    own_rows = select(Member.id).where(Member.user_id == user_id)
    # No authorized ecosystem (pending consent, exited): the caller's own rows still reach their own sessions.
    if not get_authorized_ecosystem_ids(request):
        return list((await db.scalars(own_rows)).all())
    if not ecosystem_ids:
        return []
    return list((await db.scalars(own_rows.where(Member.ecosystem_id.in_(ecosystem_ids)))).all())


async def _save_session(
    request: Request,
    session_id: str | None,
    member,
    messages: list[dict],
    skill_name: str | None,
    total_usage: dict,
    ecosystem_id: uuid.UUID | None,
    ecosystem_ids: list[str] | None,
    pending_confirmations: list[dict] | None = None,
) -> str:
    """Persist conversation to AgentSession (and the confirmations it is waiting on). Returns the session ID."""
    db_factory = getattr(request.app.ctx, "db", None)
    if not db_factory:
        return session_id or str(uuid.uuid4())

    # Only save user/assistant text messages (not tool messages from the loop)
    storable = [m for m in messages if m.get("role") in ("user", "assistant")]
    context = {"messages": storable, "pending_confirmations": pending_confirmations or []}

    try:
        async with db_factory() as db:
            sess = None
            if session_id:
                result = await db.execute(
                    select(AgentSession).where(
                        AgentSession.id == uuid.UUID(session_id),
                        AgentSession.member_id.in_(await _member_ids_in(db, request, member, get_authorized_ecosystem_ids(request))),
                    )
                )
                sess = result.scalar_one_or_none()

            if sess:
                # Update existing session
                sess.context = context
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
                member = await caller_in(db, request, eco_id) or member
                sess = AgentSession(
                    id=new_id,
                    ecosystem_id=eco_id,
                    ecosystem_ids=[str(e) for e in ecosystem_ids] if ecosystem_ids else None,
                    member_id=member.id,
                    skill_name=skill_name,
                    title=_generate_title(storable),
                    context=context,
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
@authenticated
async def list_sessions(request: Request):
    """GET /api/v1/chat/sessions — List chat sessions for current member.

    Query params:
        q: Optional search string to filter by title
        limit: Max results (default 30, max 50)
        offset: Pagination offset (default 0)
    """
    member = request.ctx.member

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
                .where(AgentSession.member_id.in_(await _member_ids_in(session, request, member, get_ecosystem_ids(request))))
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
@authenticated
async def get_session(request: Request, session_id: str):
    """GET /api/v1/chat/sessions/:id — Load a specific chat session with messages."""
    member = request.ctx.member

    try:
        async with request.app.ctx.db() as db:
            result = await db.execute(
                select(AgentSession).where(
                    AgentSession.id == uuid.UUID(session_id),
                    AgentSession.member_id.in_(await _member_ids_in(db, request, member, get_authorized_ecosystem_ids(request))),
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
@authenticated
async def delete_session(request: Request, session_id: str):
    """DELETE /api/v1/chat/sessions/:id — Delete a chat session."""
    member = request.ctx.member

    try:
        async with request.app.ctx.db() as db:
            result = await db.execute(
                select(AgentSession).where(
                    AgentSession.id == uuid.UUID(session_id),
                    AgentSession.member_id.in_(await _member_ids_in(db, request, member, get_authorized_ecosystem_ids(request))),
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
@authenticated
async def send_message(request: Request):
    """POST /api/v1/chat/send — Agentic SSE streaming chat endpoint.

    Runs a tool-use loop: sends messages to the AI with governance tools,
    executes any tool calls, feeds results back, and streams everything
    as SSE events (append, tool_start, tool_result, usage, session, done).
    """
    member = request.ctx.member

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
            session_ctx = _build_session_context(page_context, member)
            if session_ctx:
                system_prompt += f"\n\n## Session Context\n{session_ctx}"

            # Confirmations asked for in an earlier turn; this turn's asks only count from the next turn.
            pending = await _load_confirmations(request, session_id, member)
            confirmed_keys = frozenset(entry["key"] for entry in pending)
            asked_now: dict[str, str] = {}
            confirmed_tools_used: set[str] = set()

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

            # Tracks whether any assistant-facing "append" event was written this request,
            # so we can fall back to a graceful message instead of a silent blank bubble.
            assistant_appended = False

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
                    assistant_appended = True
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
                    # Empty choices from the LLM — avoid a silent blank bubble.
                    await response.write(_sse_event(
                        "append",
                        "I wasn't able to generate a response for that. Please try rephrasing your question or try again in a moment.",
                    ))
                    assistant_appended = True
                    break

                assistant_msg = choice.message

                if assistant_msg.content:
                    await response.write(_sse_event("append", assistant_msg.content))
                    assistant_appended = True

                # Check for tool calls
                tool_calls = getattr(assistant_msg, "tool_calls", None)
                if not tool_calls or choice.finish_reason != "tool_calls":
                    messages.append({"role": "assistant", "content": assistant_msg.content or ""})
                    break

                # Process tool calls
                messages.append(assistant_msg.model_dump())
                round_tool_calls = []

                for tc in tool_calls:
                    fn = tc.function
                    tool_name = fn.name
                    try:
                        tool_args = json.loads(fn.arguments) if isinstance(fn.arguments, str) else fn.arguments
                    except json.JSONDecodeError:
                        tool_args = {}
                    if not isinstance(tool_args, dict):
                        tool_args = {}

                    display_name = _TOOL_DISPLAY_NAMES.get(
                        tool_name, tool_name.replace("_", " ").capitalize(),
                    )
                    await response.write(_sse_event("thinking", json.dumps({
                        "step": display_name + "...",
                        "tool": tool_name,
                    })))

                    await response.write(_sse_event("tool_start", json.dumps({
                        "name": tool_name,
                        "label": display_name,
                        "args": tool_args,
                    })))

                    try:
                        db_factory = getattr(request.app.ctx, "db", None)
                        if db_factory:
                            async with db_factory() as db:
                                # Always a list: an empty scope fails closed instead of reading every ecosystem.
                                result = await execute_tool(
                                    tool_name, tool_args, db,
                                    ecosystem_ids=validated_eco_ids,
                                    caller_user_id=getattr(member, "user_id", None),
                                    confirmed_keys=confirmed_keys,
                                )
                                if result.get("success"):
                                    await db.commit()
                        else:
                            result = {"success": False, "error": "Database unavailable"}
                    except Exception:
                        logger.exception("Tool execution failed: %s", tool_name)
                        result = {"success": False, "error": "The tool failed unexpectedly. Nothing was changed."}

                    if result.get("needs_confirmation") and result.get("confirmation_key"):
                        asked_now[str(result["confirmation_key"])] = _dt.datetime.now(_dt.UTC).isoformat()
                    elif result.get("success") and tool_name in CONFIRMATION_TOOLS and tool_args.get("confirmed"):
                        confirmed_tools_used.add(tool_name)
                    round_tool_calls.append({"name": tool_name, "args": tool_args, "success": bool(result.get("success"))})

                    artifact = None
                    if result.get("success"):
                        artifact = _get_artifact_info(tool_name, result.get("data"))

                    # The screen and the model see the same shrunk result.
                    tool_content = _fit_tool_result(dict(result))
                    await response.write(_sse_event("tool_result", json.dumps({
                        "name": tool_name,
                        "label": display_name,
                        "success": result.get("success", False),
                        "data": tool_content.get("data") if result.get("success") else None,
                        "error": result.get("error") if not result.get("success") else None,
                        **({"needs_confirmation": result["needs_confirmation"]} if result.get("needs_confirmation") else {}),
                        **({"artifact": artifact} if artifact else {}),
                    }, default=str)))

                    # Inject a ready-made markdown link into the tool content
                    # so the LLM can copy it verbatim into its response.
                    if artifact:
                        tool_content["_link"] = f"[{artifact['label']}]({artifact['route']})"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(tool_content, default=str),
                    })

                await response.write(_sse_event("thinking", json.dumps({"step": "Processing results..."})))

                # --- Skill transition detection via router ---
                if current_skill:
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

            # Fallback if the loop ended (e.g. max rounds exhausted) without ever
            # appending assistant-facing content — avoid a silent blank bubble.
            if not assistant_appended:
                await response.write(_sse_event(
                    "append",
                    "I wasn't able to generate a response for that. Please try rephrasing your question or try again in a moment.",
                ))

            # --- Persist session (with the confirmations the next turn may use) ---
            still_pending = {
                entry["key"]: entry["at"] for entry in pending
                if entry["key"].split(":", 1)[0] not in confirmed_tools_used
            }
            still_pending.update(asked_now)
            session_id = await _save_session(
                request, session_id, member, messages,
                current_skill, total_usage,
                ecosystem_id, validated_eco_ids,
                pending_confirmations=[{"key": key, "at": at} for key, at in still_pending.items()][-10:],
            )
            await response.write(_sse_event("session", json.dumps({"session_id": session_id})))

            # Send usage
            if total_usage["total_tokens"] > 0:
                logger.info("Chat token usage: prompt=%d completion=%d total=%d",
                            total_usage["prompt_tokens"], total_usage["completion_tokens"],
                            total_usage["total_tokens"])
            await response.write(_sse_event("usage", json.dumps(total_usage)))
            await response.write(_sse_event("done", ""))

        except Exception:
            # Provider exceptions carry internals (model ids, key hints); members get a plain message.
            logger.exception("Chat streaming failed")
            await response.write(_sse_event("append", _ASSISTANT_UNAVAILABLE))
            await response.write(_sse_event("done", ""))

    return ResponseStream(
        chat_stream,
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@chat_api_bp.patch("/sessions/<session_id:str>/privacy")
@authenticated
async def update_session_privacy(request: Request, session_id: str):
    """PATCH /api/v1/chat/sessions/:id/privacy — Update privacy setting."""
    member = request.ctx.member

    body = request.json or {}
    privacy = body.get("privacy", "").strip()
    if privacy not in ("private", "ecosystem", "public"):
        return json_response({"error": "privacy must be private, ecosystem, or public"}, status=400)

    try:
        async with request.app.ctx.db() as db:
            result = await db.execute(
                select(AgentSession).where(
                    AgentSession.id == uuid.UUID(session_id),
                    AgentSession.member_id.in_(await _member_ids_in(db, request, member, get_authorized_ecosystem_ids(request))),
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
            # The caller's ACTIVE row in the session's ecosystem (not the default row); exited or suspended members are refused.
            if sess.privacy == "ecosystem" and not (
                member and is_active_member_in(await caller_in(db, request, sess.ecosystem_id), sess.ecosystem_id)
            ):
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
