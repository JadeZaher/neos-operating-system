"""Pinned OpenRouter generation with bounded retries; see ai/AGENTS.md."""
from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

_DISABLED_MSG = "AI features are disabled (no AI_API_KEY configured)"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


_clock = time.monotonic
_sleep = asyncio.sleep
_MAX_ATTEMPTS = 3
_RETRY_STATUSES = frozenset({429, 503})


class AICompletionUnavailable(RuntimeError):
    """A safe availability receipt without provider bodies or credential hints."""
    def __init__(self, *, status_code=None, retry_after_seconds=None, attempts=1):
        super().__init__("AI request could not complete within its availability policy")
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds
        self.attempts = attempts

    def as_event(self):
        return {"status": "unavailable", "provider_status": self.status_code,
                "retryable": self.status_code in _RETRY_STATUSES,
                "retry_after_seconds": self.retry_after_seconds, "attempts": self.attempts}


def _retry_after(error) -> float | None:
    """Read the upstream Retry-After minimum, including HTTP-date form."""
    for headers in (getattr(getattr(error, "response", None), "headers", None), getattr(error, "headers", None)):
        if not headers:
            continue
        value = next((value for key, value in headers.items() if str(key).lower() == "retry-after"), None)
        if value is None:
            continue
        try:
            delay = float(value)
        except (ValueError, TypeError):
            try:
                when = parsedate_to_datetime(str(value))
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                delay = (when - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                continue
        if math.isfinite(delay) and delay >= 0:
            return delay
    return None


async def _request(completion, kwargs, timeout):
    """Retry only rejected generation requests within one monotonic caller deadline."""
    deadline = _clock() + timeout
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        remaining = deadline - _clock()
        try:
            async with asyncio.timeout(max(0, remaining)):
                return await completion(**{**kwargs, "timeout": max(0, remaining)})
        except asyncio.CancelledError:
            raise
        except Exception as error:
            status = getattr(error, "status_code", None)
            if type(status) is not int:
                status = getattr(getattr(error, "response", None), "status_code", None)
            status = status if type(status) is int and 100 <= status <= 599 else None
            retry_after = _retry_after(error)
            delay = retry_after if retry_after is not None else min(2 ** (attempt - 1), 10)
            if status not in _RETRY_STATUSES or attempt == _MAX_ATTEMPTS or delay >= deadline - _clock():
                logger.warning("AI request unavailable status=%s attempts=%s", status, attempt)
                raise AICompletionUnavailable(status_code=status, retry_after_seconds=retry_after, attempts=attempt) from None
            logger.info("AI request rejected status=%s attempt=%s retry_delay_seconds=%s", status, attempt, delay)
            try:
                async with asyncio.timeout(max(0, deadline - _clock())):
                    await _sleep(delay)
            except TimeoutError:
                raise AICompletionUnavailable(status_code=status, retry_after_seconds=retry_after, attempts=attempt) from None
            if _clock() >= deadline:
                raise AICompletionUnavailable(status_code=status, retry_after_seconds=retry_after, attempts=attempt) from None
    raise AssertionError("retry attempts exhausted")


def _resolve_openrouter_model(model: str | None, configured_model: str) -> str:
    """Return a LiteLLM model name explicitly routed through OpenRouter."""
    resolved = (model or configured_model).strip()
    if not resolved:
        raise ValueError("AI_MODEL must be configured for OpenRouter")
    return resolved if resolved.startswith("openrouter/") else f"openrouter/{resolved}"


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
        model: OpenRouter model ID, with or without the ``openrouter/`` prefix.
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

    if settings.AI_PROVIDER.lower() != "openrouter":
        raise ValueError("NEOS AI provider must be configured as 'openrouter'")

    resolved_model = _resolve_openrouter_model(model, settings.AI_MODEL)

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
        "num_retries": 0,
        "max_retries": 0,
    }

    if tools:
        kwargs["tools"] = tools

    kwargs["api_base"] = (settings.AI_BASE_URL or _OPENROUTER_BASE_URL).rstrip("/")

    # Identify this application to OpenRouter.
    kwargs["extra_headers"] = {
        "HTTP-Referer": "https://neos-governance.org",
        "X-Title": "NEOS Governance Agent",
    }

    response = await _request(litellm.acompletion, kwargs, timeout)
    if stream or tools:
        return response
    content = response.choices[0].message.content if response.choices else ""
    return {"content": content, "model": resolved_model, "usage": dict(response.usage) if response.usage else None}


def is_ai_enabled() -> bool:
    """Check if AI features are available."""
    try:
        from neos_agent.config import get_settings
        settings = get_settings()
        return bool(settings.AI_API_KEY)
    except Exception:
        return False
