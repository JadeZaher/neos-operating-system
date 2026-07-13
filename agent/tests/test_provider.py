"""Contract tests for the OpenRouter provider boundary."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from neos_agent.ai import provider
from neos_agent.config import Settings


def _settings(**overrides):
    values = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "OPENROUTER_KEY": "sk-or-test",
        "AI_PROVIDER": "openrouter",
        "AI_MODEL": "qwen/qwen3-30b-a3b-instruct-2507",
        "AI_BASE_URL": "https://openrouter.ai/api/v1/",
        "SESSION_SECRET": "test-secret",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.mark.asyncio
async def test_openrouter_request_contract(monkeypatch):
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))],
        usage=None,
    )
    completion = AsyncMock(return_value=response)
    monkeypatch.setattr("neos_agent.config.get_settings", lambda: _settings())
    monkeypatch.setitem(
        sys.modules,
        "litellm",
        SimpleNamespace(drop_params=False, acompletion=completion),
    )

    result = await provider.acompletion(
        messages=[{"role": "user", "content": "hello"}],
        model="qwen/qwen3-30b-a3b-instruct-2507",
    )

    assert result["content"] == "hello"
    kwargs = completion.await_args.kwargs
    assert kwargs["model"] == "openrouter/qwen/qwen3-30b-a3b-instruct-2507"
    assert kwargs["api_base"] == "https://openrouter.ai/api/v1"
    assert kwargs["api_key"] == "sk-or-test"
    assert kwargs["extra_headers"]["X-Title"] == "NEOS Governance Agent"


@pytest.mark.asyncio
async def test_provider_rejects_non_openrouter_configuration(monkeypatch):
    monkeypatch.setattr("neos_agent.config.get_settings", lambda: _settings(AI_PROVIDER="anthropic"))
    with pytest.raises(ValueError, match="openrouter"):
        await provider.acompletion(messages=[{"role": "user", "content": "hello"}])

