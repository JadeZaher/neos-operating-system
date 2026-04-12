"""Chat SSE handler for the NEOS governance agent.

Blueprint: chat_bp, url_prefix="/chat"

Accepts user messages via POST, streams Claude responses as standard SSE
events (append / morph / skill / done). Manages agent sessions (create,
load, save, prune, cleanup) backed by the agent_sessions table.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from html import escape
from typing import Optional

import httpx

from sanic import Blueprint, Request
from sanic.response import ResponseStream, json as json_response, html as html_response
from sqlalchemy import select, delete, func, or_, Text

from neos_agent.db.models import AgentSession

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", url_prefix="/chat")

# Maximum messages kept in session context (user + assistant pairs)
_MAX_MESSAGES = 30

# Maximum tool-use loop iterations to prevent runaway
_MAX_TOOL_TURNS = 5


# ---------------------------------------------------------------------------
# HTML fragment renderers (inline templates kept as Python strings)
# ---------------------------------------------------------------------------

def render_agent_message(text: str, message_id: Optional[str] = None) -> str:
    """Render an agent message as an HTML fragment.

    Args:
        text: The message text (escaped for safety).
        message_id: Optional DOM id for morphing.

    Returns:
        HTML string for the agent message bubble.
    """
    mid = f' id="{message_id}"' if message_id else ""
    safe = escape(text)
    data_mid = f' data-msg-id="{message_id}"' if message_id else ""
    # No <br> replacement — client-side marked.js handles newlines via markdown
    return (
        f'<div class="group flex gap-3 mb-4"{mid}>'
        f'<div class="w-8 h-8 rounded-full bg-neos-primary text-white flex items-center justify-center text-sm font-bold flex-shrink-0">A</div>'
        f'<div class="flex-1 flex flex-col">'
        f'<div class="bg-neos-surface border border-neos-border rounded-lg p-3 text-sm agent-msg-content">{safe}</div>'
        f'<div class="flex gap-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150">'
        f'<button type="button" class="chat-copy-btn inline-flex items-center gap-1 px-2 py-1 text-xs text-neos-muted hover:text-neos-primary rounded hover:bg-neos-accent/10 transition-colors"{data_mid} title="Copy message">'
        f'<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
        f'<span>Copy</span></button>'
        f'<button type="button" class="chat-share-btn inline-flex items-center gap-1 px-2 py-1 text-xs text-neos-muted hover:text-neos-primary rounded hover:bg-neos-accent/10 transition-colors"{data_mid} title="Copy share link">'
        f'<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'
        f'<span>Share</span></button>'
        f'</div></div>'
        f"</div>"
    )


def render_user_message(text: str) -> str:
    """Render a user message as an HTML fragment."""
    safe = escape(text).replace("\n", "<br>")
    return (
        f'<div class="flex justify-end mb-4">'
        f'<div class="max-w-[80%] bg-neos-primary text-white rounded-lg p-3 text-sm">{safe}</div>'
        f"</div>"
    )


def render_system_message(msg_type: str, text: str) -> str:
    """Render a system message (typing, error, info) as an HTML fragment.

    Args:
        msg_type: One of ``typing``, ``error``, ``info``.
        text: Display text.

    Returns:
        HTML fragment string.
    """
    safe = escape(text)
    color_map = {"typing": "text-neos-muted", "error": "text-red-600", "info": "text-blue-600"}
    color_class = color_map.get(msg_type, "text-neos-muted")
    extra_id = ' id="typing-indicator"' if msg_type == "typing" else ""
    return (
        f'<div class="flex justify-center mb-3"{extra_id}>'
        f'<div class="text-xs {color_class} italic px-3 py-1">{safe}</div>'
        f"</div>"
    )


def render_tool_indicator(
    tool_name: str,
    status: str,
    args: Optional[dict] = None,
    result: Optional[str] = None,
    link_url: Optional[str] = None,
    link_label: Optional[str] = None,
) -> str:
    """Render a tool call indicator HTML fragment.

    Args:
        tool_name: Name of the governance tool.
        status: ``running``, ``success``, or ``error``.
        args: Optional dict of tool arguments.
        result: Optional result summary string.
        link_url: Optional dashboard URL to link to.
        link_label: Optional link display text.

    Returns:
        HTML fragment string.
    """
    safe_name = escape(tool_name)
    status_colors = {"running": "border-yellow-400 bg-neos-surface-alt", "success": "border-green-400 bg-neos-surface-alt", "error": "border-red-400 bg-neos-surface-alt"}
    border_class = status_colors.get(status, "border-neos-border bg-neos-surface-alt")
    args_html = ""
    if args:
        args_html = f'<span class="text-xs text-neos-muted ml-2">{escape(json.dumps(args))}</span>'
    result_html = ""
    if result:
        result_html = f'<div class="mt-1 text-xs text-neos-muted">{escape(result)}</div>'
    link_html = ""
    if link_url and link_label:
        safe_url = escape(link_url)
        safe_label = escape(link_label)
        link_html = (
            f'<a href="{safe_url}" '
            f'class="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-neos-primary hover:underline">'
            f'{safe_label} &rarr;</a>'
        )
    return (
        f'<div class="flex flex-col gap-0.5 mb-3 px-3 py-2 border-l-4 rounded-r {border_class} text-sm">'
        f'<div class="flex items-start gap-2">'
        f'<span class="font-mono font-medium">{safe_name}</span>'
        f'<span class="text-xs px-1.5 py-0.5 rounded bg-neos-surface">{escape(status)}</span>'
        f"{args_html}</div>"
        f"{result_html}{link_html}"
        f"</div>"
    )


def render_transition_indicator(skill_name: str) -> str:
    """Render a skill transition banner HTML fragment."""
    safe = escape(skill_name)
    return (
        f'<div class="flex items-center justify-center gap-2 my-4 py-2 bg-neos-accent/10 rounded-lg text-sm">'
        f'<span class="text-neos-muted">Skill transition:</span> '
        f'<span class="font-semibold text-neos-primary">{safe}</span>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Tool result → dashboard link mapping
# ---------------------------------------------------------------------------

def _extract_result_link(
    tool_name: str, result: dict
) -> tuple[Optional[str], Optional[str]]:
    """Extract a dashboard link from a tool result.

    Returns:
        (url, label) tuple, or (None, None) if no link applies.
    """
    data = result.get("data", {})
    obj_id = data.get("id")
    if not obj_id:
        return None, None

    if tool_name == "create_proposal":
        label = data.get("proposal_id", "View proposal")
        return f"/dashboard/proposals/{obj_id}", label
    if tool_name == "create_agreement_draft":
        label = data.get("agreement_id", "View agreement")
        return f"/dashboard/agreements/{obj_id}", label
    if tool_name == "create_decision_record":
        label = data.get("record_id", "View decision")
        return f"/dashboard/decisions/{obj_id}", label
    if tool_name == "create_domain_draft":
        label = data.get("domain_id", "View domain")
        return f"/dashboard/domains/{obj_id}", label
    if tool_name == "create_ecosystem":
        label = data.get("name", "View ecosystem")
        return f"/dashboard/ecosystems/{obj_id}", label
    if tool_name == "create_safeguard_audit":
        label = data.get("audit_id", "View audit")
        return f"/dashboard/safeguards/{obj_id}", label
    if tool_name == "create_conflict_case":
        label = data.get("case_id", "View conflict")
        return f"/dashboard/conflicts/{obj_id}", label
    if tool_name == "create_repair_agreement":
        case_id = data.get("case_id", "")
        label = data.get("title", "View repair agreement")
        return f"/dashboard/conflicts?case={case_id}", label

    return None, None


def _summarise_result(tool_name: str, result: dict) -> str:
    """Return a short human-readable summary of a tool result."""
    if not result.get("success"):
        return result.get("error", "Tool call failed.")
    data = result.get("data", {})
    if msg := data.get("message"):
        return msg
    if "count" in data:
        return f"{data['count']} result(s) found."
    return "Done."


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

async def emit_chat_event(response, event_type: str, html: str) -> None:
    """Emit a standard SSE event for the chat stream.

    Args:
        response: Sanic streaming response writer.
        event_type: ``append``, ``morph``, ``skill``, or ``done``.
        html: HTML fragment string (or JSON string for ``skill``/``done``).
    """
    # Escape newlines so each continuation line starts with "data: "
    data_lines = html.replace("\n", "\ndata: ")
    await response.write(f"event: {event_type}\ndata: {data_lines}\n\n")


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------

async def get_or_create_session(
    session_id: str,
    app,
    ecosystem_ids: list | None = None,
    member_id: uuid.UUID | None = None,
) -> AgentSession:
    """Load an existing agent session or create a new one.

    Args:
        session_id: UUID string identifying the session.
        app: Sanic application (provides ``app.ctx.db``).
        ecosystem_ids: Optional list of selected ecosystem UUIDs.
        member_id: Optional member UUID to associate with the session.

    Returns:
        An ``AgentSession`` instance (detached from the DB session).
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        sid = uuid.uuid4()

    async with app.ctx.db() as db:
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == sid)
        )
        agent_session = result.scalar_one_or_none()

        if agent_session is None:
            # Use first selected ecosystem, or fall back to first in DB
            eco_id = None
            if ecosystem_ids:
                eco_id = ecosystem_ids[0]
            if eco_id is None:
                from neos_agent.db.models import Ecosystem
                eco_result = await db.execute(select(Ecosystem.id).limit(1))
                eco_id = eco_result.scalar_one_or_none() or uuid.uuid4()

            agent_session = AgentSession(
                id=sid,
                ecosystem_id=eco_id,
                ecosystem_ids=[str(eid) for eid in ecosystem_ids] if ecosystem_ids else None,
                member_id=member_id,
                status="active",
                context={"messages": []},
            )
            db.add(agent_session)
            await db.commit()
            await db.refresh(agent_session)

        # Ensure context is a dict
        if agent_session.context is None:
            agent_session.context = {"messages": []}

    return agent_session


async def save_session(
    session: AgentSession,
    messages: list[dict],
    app,
) -> None:
    """Persist session with updated message history (pruned to last N).

    Args:
        session: The agent session to update.
        messages: Full message list.
        app: Sanic application.
    """
    pruned = messages[-_MAX_MESSAGES:]
    async with app.ctx.db() as db:
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == session.id)
        )
        db_session = result.scalar_one_or_none()
        if db_session is not None:
            db_session.context = {"messages": pruned}
            db_session.skill_name = session.skill_name
            await db.commit()


async def load_session(
    session_id: str,
    app,
) -> Optional[AgentSession]:
    """Load a session by ID. Returns ``None`` if not found."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return None
    async with app.ctx.db() as db:
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == sid)
        )
        return result.scalar_one_or_none()


async def cleanup_expired_sessions(app, max_age_hours: int = 24) -> int:
    """Delete sessions older than *max_age_hours* of inactivity.

    Args:
        app: Sanic application.
        max_age_hours: Maximum inactivity age in hours.

    Returns:
        Number of sessions deleted.
    """
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    async with app.ctx.db() as db:
        result = await db.execute(
            delete(AgentSession).where(AgentSession.updated_at < cutoff)
        )
        await db.commit()
        return result.rowcount  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@chat_bp.route("/message", methods=["POST"])
async def send_message(request: Request):
    """POST /chat/message -- accept user message, stream agent response as SSE.

    Expects JSON body with ``message`` (required) and ``session_id``
    (optional -- generated if absent).  Returns a ``text/event-stream``
    response with standard SSE events (append / morph / skill / done).

    Supports multi-turn tool use: when Claude requests tool calls, the
    handler executes them against the DB, feeds results back, and loops
    until Claude produces a final text response (up to ``_MAX_TOOL_TURNS``
    iterations).
    """
    data = request.json or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id")
    context_page = data.get("context", "dashboard")

    if not message:
        return json_response({"error": "Message required"}, status=400)

    if not session_id:
        session_id = str(uuid.uuid4())

    async def stream(response):
        # 1. Emit user message echo + typing indicator
        await emit_chat_event(response, "append", render_user_message(message))
        await emit_chat_event(response, "append", render_system_message("typing", "Thinking..."))

        # 2. Resolve selected ecosystem IDs and names
        selected_eco_ids = getattr(request.ctx, "selected_ecosystem_ids", [])
        selected_ecosystems = getattr(request.ctx, "ecosystems", [])
        eco_names = [e.name for e in selected_ecosystems] if selected_ecosystems else ["NEOS"]

        # 3. Load or create session (with member association)
        member = getattr(request.ctx, "member", None)
        member_id = member.id if member else None
        session = await get_or_create_session(
            session_id, request.app,
            ecosystem_ids=selected_eco_ids or None,
            member_id=member_id,
        )

        # 4. Build system prompt
        try:
            from neos_agent.agent.system_prompt import assemble_system_prompt
            system_prompt = assemble_system_prompt(
                ecosystem_names=eco_names,
                active_skill=session.skill_name,
                skill_registry=getattr(request.app.ctx, "skills", None),
                page_context=context_page,
            )
            # Prepend explicit multi-ecosystem scope context
            if len(eco_names) == 1:
                eco_scope_note = f"You are assisting within the {eco_names[0]} ecosystem."
            else:
                names_str = ", ".join(eco_names)
                eco_scope_note = (
                    f"The user has {len(eco_names)} ecosystems selected: {names_str}. "
                    f"Scope your responses to these ecosystems."
                )
            system_prompt = eco_scope_note + "\n\n" + system_prompt
        except ImportError:
            system_prompt = "You are the NEOS Governance Agent."

        # 5. Multi-turn tool execution loop
        try:
            import anthropic
            from neos_agent.agent.governance_tools import (
                get_tool_definitions,
                execute_tool,
            )

            settings = request.app.ctx.settings
            client_kwargs = {
                "api_key": settings.ANTHROPIC_API_KEY,
                "timeout": httpx.Timeout(120.0, connect=10.0),
            }
            if settings.ANTHROPIC_BASE_URL:
                client_kwargs["base_url"] = settings.ANTHROPIC_BASE_URL
            
            client = anthropic.AsyncAnthropic(**client_kwargs)

            # Build messages from session context
            messages = (
                session.context.get("messages", [])
                if session.context
                else []
            )
            messages.append({"role": "user", "content": message})

            tools = get_tool_definitions()

            # Working message list for the API (may include tool_use /
            # tool_result blocks within a single user turn)
            api_messages = list(messages[-10:])

            response_text = ""
            tool_calls_made: list[dict] = []
            msg_id = f"agent-msg-{uuid.uuid4().hex[:8]}"

            for _turn in range(_MAX_TOOL_TURNS):
                # --- Stream one Claude turn ---
                turn_text = ""
                final_message = None
                text_started = False

                async with asyncio.timeout(90):
                    async with client.messages.stream(
                        model=settings.CLAUDE_MODEL,
                        max_tokens=4096,
                        system=system_prompt,
                        messages=api_messages,
                        tools=tools if tools else anthropic.NOT_GIVEN,
                    ) as msg_stream:
                        async for event in msg_stream:
                            if event.type == "content_block_delta":
                                if hasattr(event.delta, "text"):
                                    if not text_started:
                                        # Emit an initial agent message placeholder
                                        await emit_chat_event(
                                            response, "append",
                                            render_agent_message("", msg_id),
                                        )
                                        text_started = True
                                    turn_text += event.delta.text
                                    # Morph the specific agent message by ID
                                    await emit_chat_event(
                                        response, "morph",
                                        render_agent_message(turn_text, msg_id),
                                    )
                            elif event.type == "content_block_start":
                                if event.content_block.type == "tool_use":
                                    await emit_chat_event(
                                        response, "append",
                                        render_tool_indicator(
                                            event.content_block.name, "running",
                                        ),
                                    )

                        final_message = await msg_stream.get_final_message()

                response_text = turn_text

                # --- If no tool calls, we're done ---
                if final_message.stop_reason != "tool_use":
                    break

                # --- Execute tool calls ---
                # Serialise assistant content blocks for the API
                assistant_content = []
                for block in final_message.content:
                    if block.type == "text":
                        assistant_content.append(
                            {"type": "text", "text": block.text}
                        )
                    elif block.type == "tool_use":
                        assistant_content.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })
                api_messages.append({
                    "role": "assistant",
                    "content": assistant_content,
                })

                # Execute each tool and collect results
                tool_result_blocks: list[dict] = []
                async with request.app.ctx.db() as db:
                    for block in final_message.content:
                        if block.type != "tool_use":
                            continue

                        # SSE keepalive to prevent proxy/browser timeout
                        await response.write(": keepalive\n\n")

                        tool_calls_made.append({"name": block.name})
                        result = await execute_tool(
                            block.name, block.input, db,
                            ecosystem_ids=selected_eco_ids or None,
                        )

                        # Emit rich indicator with link
                        summary = _summarise_result(block.name, result)
                        status = "success" if result.get("success") else "error"
                        link_url, link_label = _extract_result_link(
                            block.name, result,
                        )
                        await emit_chat_event(
                            response, "append",
                            render_tool_indicator(
                                block.name, status,
                                result=summary,
                                link_url=link_url,
                                link_label=link_label,
                            ),
                        )

                        tool_result_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        })

                    await db.commit()

                # Feed results back to Claude
                api_messages.append({
                    "role": "user",
                    "content": tool_result_blocks,
                })

                # Update typing indicator for next turn
                await emit_chat_event(
                    response, "append",
                    render_system_message("typing", "Processing..."),
                )
                # New msg_id for the next text response
                msg_id = f"agent-msg-{uuid.uuid4().hex[:8]}"

            # Remove typing indicator (morph to empty string removes it)
            await emit_chat_event(response, "morph", '<div id="typing-indicator"></div>')

            # Check skill transitions
            try:
                from neos_agent.agent.router import SkillRouter
                router = SkillRouter()
                new_skill = router.detect_transition(
                    session.skill_name or "",
                    tool_calls_made,
                    response_text,
                )
                if new_skill:
                    session.skill_name = new_skill
                    await emit_chat_event(
                        response, "append",
                        render_transition_indicator(new_skill),
                    )
                    await emit_chat_event(
                        response, "skill",
                        json.dumps({"name": new_skill}),
                    )
            except ImportError:
                pass

            # Save session -- include tool context so Claude has
            # memory of what was created/queried in previous turns.
            if tool_calls_made:
                tool_summary = "Tools called: " + ", ".join(
                    t["name"] for t in tool_calls_made
                )
                full_response = f"{response_text}\n\n[{tool_summary}]"
            else:
                full_response = response_text
            messages.append({"role": "assistant", "content": full_response})
            await save_session(session, messages, request.app)

            # Generate title from first user message if not set yet
            if not session.title:
                title = message[:100].strip()
                if len(title) > 80:
                    title = title[:80].rsplit(" ", 1)[0] + "..."
                if title:
                    async with request.app.ctx.db() as db:
                        result = await db.execute(
                            select(AgentSession).where(AgentSession.id == session.id)
                        )
                        db_session = result.scalar_one_or_none()
                        if db_session and not db_session.title:
                            db_session.title = title
                            await db.commit()

        except (asyncio.TimeoutError, TimeoutError) as exc:
            logger.warning("Chat stream timed out: %s", exc)
            # Remove stale typing/processing indicator
            await emit_chat_event(
                response, "morph",
                '<div id="typing-indicator"></div>',
            )
            await emit_chat_event(
                response, "append",
                render_system_message(
                    "error",
                    "The response took too long. Please try a simpler question or try again.",
                ),
            )
        except Exception as exc:
            logger.exception("Chat error: %s", exc)
            # Remove stale typing/processing indicator
            await emit_chat_event(
                response, "morph",
                '<div id="typing-indicator"></div>',
            )
            await emit_chat_event(
                response, "append",
                render_system_message("error", "An error occurred. Please try again."),
            )

        # Signal stream complete
        await emit_chat_event(response, "done", "")

    return ResponseStream(stream, content_type="text/event-stream")


@chat_bp.route("/history", methods=["GET"])
async def get_history(request: Request):
    """GET /chat/history -- return message history for a session.

    Query params:
        session_id: UUID of the agent session.

    Returns JSON with ``messages`` list and optional ``active_skill``.
    If no session or no session_id, returns ``{"messages": [], "welcome": true}``.
    """
    session_id = request.args.get("session_id")
    if not session_id:
        return json_response({"messages": [], "welcome": True})

    session = await load_session(session_id, request.app)
    if not session or not session.context:
        return json_response({"messages": [], "welcome": True})

    # Ownership check: only return history for own sessions
    member = getattr(request.ctx, "member", None)
    if member and session.member_id and session.member_id != member.id:
        return json_response({"messages": [], "welcome": True})

    messages = session.context.get("messages", [])
    return json_response({
        "messages": messages,
        "active_skill": session.skill_name,
        "title": session.title,
        "session_id": str(session.id),
    })


# ---------------------------------------------------------------------------
# Conversation history routes
# ---------------------------------------------------------------------------

@chat_bp.route("/conversations", methods=["GET"])
async def list_conversations(request: Request):
    """GET /chat/conversations -- list conversations for the authenticated user.

    Query params:
        q: Optional search string (searches title and message content).
        offset: Pagination offset (default 0).
        limit: Pagination limit (default 20, max 50).

    Returns HTML fragment with clickable conversation items.
    """
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    search = (request.args.get("q") or "").strip()
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except (ValueError, TypeError):
        offset = 0
    try:
        limit = min(50, max(1, int(request.args.get("limit", 20))))
    except (ValueError, TypeError):
        limit = 20

    async with request.app.ctx.db() as db:
        stmt = (
            select(AgentSession)
            .where(
                AgentSession.member_id == member.id,
                AgentSession.archived == False,  # noqa: E712
                AgentSession.status == "active",
            )
            .order_by(AgentSession.updated_at.desc())
        )

        if search:
            from neos_agent.views._rendering import escape_like
            pattern = f"%{escape_like(search)}%"
            stmt = stmt.where(
                or_(
                    AgentSession.title.ilike(pattern),
                    AgentSession.context.cast(Text).ilike(pattern),
                )
            )

        # Get total count for pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        # Get paginated results
        result = await db.execute(stmt.offset(offset).limit(limit))
        sessions = result.scalars().all()

    # Build conversation list as HTML fragment
    items: list[str] = []
    for s in sessions:
        msg_count = len(s.context.get("messages", [])) if s.context else 0
        title = escape(s.title or "New conversation")
        updated = s.updated_at.strftime("%b %d, %H:%M") if s.updated_at else ""
        skill = escape(s.skill_name or "General")
        items.append(
            f'<div class="chat-conv-item group flex items-center gap-2 px-4 py-3 '
            f'hover:bg-neos-accent/10 border-b border-neos-border transition-colors cursor-pointer" '
            f'data-session-id="{s.id}" onclick="loadConversation(\'{s.id}\')">'
            f'<div class="flex-1 min-w-0">'
            f'<div class="text-sm font-medium text-neos-text truncate">{title}</div>'
            f'<div class="flex items-center gap-2 mt-1">'
            f'<span class="text-xs text-neos-muted">{msg_count} messages</span>'
            f'<span class="text-xs text-neos-muted">&middot;</span>'
            f'<span class="text-xs text-neos-muted">{updated}</span>'
            f'</div>'
            f'<div class="text-xs text-neos-accent mt-0.5">{skill}</div>'
            f'</div>'
            f'<button type="button" class="chat-conv-delete opacity-0 group-hover:opacity-100 p-1 rounded '
            f'hover:bg-red-100 text-neos-muted hover:text-red-600 transition-all" '
            f'onclick="event.stopPropagation(); deleteConversation(\'{s.id}\', this)" title="Delete">'
            f'<svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">'
            f'<path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 '
            f'21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>'
            f'</svg></button>'
            f'</div>'
        )

    html_content = "".join(items)
    if not items:
        if search:
            html_content = (
                '<div class="px-4 py-8 text-center text-sm text-neos-muted">'
                f'No conversations matching &ldquo;{escape(search)}&rdquo;</div>'
            )
        else:
            html_content = (
                '<div class="px-4 py-8 text-center text-sm text-neos-muted">'
                'No conversations yet. Start a new chat!</div>'
            )

    # Pagination: load more button
    if offset + limit < total:
        next_offset = offset + limit
        q_param = f"&q={escape(search)}" if search else ""
        html_content += (
            f'<button type="button" class="w-full px-4 py-2 text-xs text-neos-primary '
            f'font-medium hover:bg-neos-accent/10 transition-colors border-b border-neos-border" '
            f'onclick="loadMoreConversations({next_offset}, {limit})">'
            f'Load more ({total - next_offset} remaining)</button>'
        )

    return html_response(html_content)


@chat_bp.route("/conversations/<session_id:str>", methods=["DELETE"])
async def archive_conversation(request: Request, session_id: str):
    """DELETE /chat/conversations/<id> -- soft-delete (archive) a conversation."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return json_response({"error": "Invalid session ID"}, status=400)

    async with request.app.ctx.db() as db:
        result = await db.execute(
            select(AgentSession).where(
                AgentSession.id == sid,
                AgentSession.member_id == member.id,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.archived = True
            await db.commit()

    return json_response({"success": True})


@chat_bp.route("/conversations/<session_id:str>", methods=["PATCH"])
async def rename_conversation(request: Request, session_id: str):
    """PATCH /chat/conversations/<id> -- update conversation title."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    data = request.json or {}
    new_title = (data.get("title") or "").strip()[:200]
    if not new_title:
        return json_response({"error": "Title required"}, status=400)

    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return json_response({"error": "Invalid session ID"}, status=400)

    async with request.app.ctx.db() as db:
        result = await db.execute(
            select(AgentSession).where(
                AgentSession.id == sid,
                AgentSession.member_id == member.id,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.title = new_title
            await db.commit()

    return json_response({"success": True, "title": new_title})


@chat_bp.route("/shared/<session_id:str>", methods=["GET"])
async def get_shared_conversation(request: Request, session_id: str):
    """GET /chat/shared/<id> -- return a read-only view of a shared conversation.

    This endpoint is accessible without ownership checks, enabling share links.
    Returns only messages and metadata (no write access).
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return json_response({"error": "Invalid session ID"}, status=400)

    async with request.app.ctx.db() as db:
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == sid)
        )
        session = result.scalar_one_or_none()

    if not session or not session.context:
        return json_response({"messages": [], "title": None})

    messages = session.context.get("messages", [])
    return json_response({
        "messages": messages,
        "title": session.title,
        "active_skill": session.skill_name,
        "session_id": str(session.id),
        "read_only": True,
    })
