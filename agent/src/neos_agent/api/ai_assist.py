"""AI text assistance endpoint for governance form fields.

Blueprint: ai_assist_bp, url_prefix="/api/v1/ai"
"""
from __future__ import annotations

import logging

from neos_agent.ai.provider import acompletion, is_ai_enabled
from sanic import Blueprint
from sanic.request import Request
from sanic.response import json as json_response

logger = logging.getLogger(__name__)

ai_assist_bp = Blueprint("ai_assist", url_prefix="/api/v1/ai")

_SYSTEM_PROMPT = (
    "You are a writing assistant helping users fill out governance forms. "
    "Write concise, professional text suitable for governance and organizational contexts. "
    "Return only the requested text with no preamble, explanation, or extra commentary."
)


@ai_assist_bp.post("/assist")
async def assist(request: Request):
    """POST /api/v1/ai/assist — Generate or improve text for a governance form field."""
    member = getattr(request.ctx, "member", None)
    if not member:
        return json_response({"error": "Authentication required"}, status=401)

    body = request.json or {}
    field_label: str = body.get("field_label", "").strip()
    field_context: str = body.get("field_context", "").strip()
    current_text: str = body.get("current_text", "").strip()
    action: str = body.get("action", "").strip()

    if action not in ("generate", "improve"):
        return json_response(
            {"error": "action must be 'generate' or 'improve'"},
            status=400,
        )

    if not field_label:
        return json_response({"error": "field_label is required"}, status=400)

    if action == "improve" and not current_text:
        return json_response(
            {"error": "current_text is required for action 'improve'"},
            status=400,
        )

    # Build the user message based on action
    if action == "generate":
        parts = [f"Write text for the field: {field_label}"]
        if field_context:
            parts.append(f"Context: {field_context}")
        user_message = "\n".join(parts)
    else:  # improve
        parts = [f"Improve the following text for the field: {field_label}"]
        if field_context:
            parts.append(f"Context: {field_context}")
        parts.append(f"Current text:\n{current_text}")
        user_message = "\n".join(parts)

    if not is_ai_enabled():
        return json_response({"error": "AI service not configured"}, status=503)

    try:
        result = await acompletion(
            messages=[{"role": "user", "content": user_message}],
            system=_SYSTEM_PROMPT,
            max_tokens=500,
        )
        if result is None:
            return json_response({"error": "AI service not configured"}, status=503)
        return json_response({"text": result["content"]})
    except Exception:
        logger.exception("AI assist error")
        return json_response({"error": "AI service unavailable"}, status=503)
