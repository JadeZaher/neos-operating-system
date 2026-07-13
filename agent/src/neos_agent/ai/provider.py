"""AI provider abstraction using LiteLLM for multi-model support.

Supports OpenRouter, Anthropic, OpenAI, and local models.
All governance processes work without AI — this is an optimization layer.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_DISABLED_MSG = "AI features are disabled (no AI_API_KEY configured)"


async def acompletion(
    messages: list[dict],
    model: str | None = None,
    system: str | None = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    stream: bool = False,
    tools: list[dict] | None = None,
    timeout: int = 30,
):
    """Async completion via LiteLLM. Returns None if AI is disabled.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."} dicts
        model: Model identifier (e.g. "openrouter/anthropic/claude-sonnet-4-20250514")
        system: System prompt (prepended as system message)
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        stream: If True, returns an async generator instead of dict
        tools: Optional list of tool definitions for function calling.
               When provided, returns the raw litellm response object
               so callers can inspect tool_calls on the message.
        timeout: Request timeout in seconds

    Returns:
        Dict with "content" key containing the response text, or None if disabled.
        If stream=True, returns an async generator yielding content chunks.
        If tools are provided, returns the raw litellm response object.
    """
    try:
        import litellm
    except ImportError:
        logger.warning("litellm not installed — AI features disabled")
        return None

    from neos_agent.config import get_settings
    settings = get_settings()

    api_key = settings.AI_API_KEY
    if not api_key:
        logger.debug(_DISABLED_MSG)
        return None

    resolved_model = model or settings.AI_MODEL

    # Build messages with system prompt
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    # Configure litellm
    litellm.drop_params = True  # Drop unsupported params per provider

    kwargs = {
        "model": resolved_model,
        "messages": full_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "api_key": api_key,
        "stream": stream,
        "timeout": timeout,
    }

    if tools:
        kwargs["tools"] = tools

    # Add base URL if configured (for self-hosted or custom endpoints)
    if settings.AI_BASE_URL:
        kwargs["api_base"] = settings.AI_BASE_URL

    # OpenRouter requires extra_headers for optimal routing and free tier usage
    if "openrouter" in resolved_model or settings.AI_PROVIDER == "openrouter":
        kwargs.setdefault("extra_headers", {})
        # Allow OpenRouter to route to the best available free tier model
        kwargs["extra_headers"].setdefault("HTTP-Referer", "https://neos-governance.org")
        kwargs["extra_headers"].setdefault("X-Title", "NEOS Governance Agent")

    try:
        if stream:
            return await litellm.acompletion(**kwargs)

        response = await litellm.acompletion(**kwargs)

        # When tools are provided, return the raw response so callers
        # can inspect tool_calls, finish_reason, etc.
        if tools:
            return response

        content = response.choices[0].message.content if response.choices else ""
        return {"content": content, "model": resolved_model, "usage": dict(response.usage) if response.usage else None}
    except Exception as e:
        logger.error("AI completion failed (%s): %s", resolved_model, e)
        raise


def is_ai_enabled() -> bool:
    """Check if AI features are available."""
    try:
        from neos_agent.config import get_settings
        settings = get_settings()
        return bool(settings.AI_API_KEY)
    except Exception:
        return False
