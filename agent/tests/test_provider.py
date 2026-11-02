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



class Rejected(RuntimeError):
    def __init__(self, status=429, retry_after="10"):
        super().__init__("private provider body with a credential hint")
        self.status_code = status
        self.response = SimpleNamespace(status_code=status, headers={"Retry-After": retry_after} if retry_after is not None else {})
        self.headers = {"Retry-After": "1"}


def retry_clock(monkeypatch):
    clock = [0.0]
    waits = []
    async def wait(seconds):
        waits.append(seconds)
        clock[0] += seconds
    monkeypatch.setattr(provider, "_clock", lambda: clock[0])
    monkeypatch.setattr(provider, "_sleep", wait)
    return clock, waits


@pytest.mark.parametrize("status", [429, 503])
async def test_retry_after_uses_upstream_minimum_and_remaining_deadline_without_sdk_multiplication(monkeypatch, status):
    _, waits = retry_clock(monkeypatch)
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Ready"))], usage=None)
    completion = AsyncMock(side_effect=[Rejected(status), response])
    monkeypatch.setattr("neos_agent.config.get_settings", lambda: _settings())
    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(drop_params=False, acompletion=completion))
    result = await provider.acompletion(messages=[{"role": "user", "content": "Hello"}], timeout=30)
    assert result["content"] == "Ready" and waits == [10]
    first, second = [call.kwargs for call in completion.await_args_list]
    assert first["timeout"] == 30 and second["timeout"] == 20
    assert all(call["num_retries"] == call["max_retries"] == 0 for call in (first, second))
    assert first["model"] == second["model"] and first["api_key"] == second["api_key"]


async def test_retry_after_cannot_be_shortened_to_fit_a_deadline(monkeypatch):
    _, waits = retry_clock(monkeypatch)
    completion = AsyncMock(side_effect=Rejected())
    with pytest.raises(provider.AICompletionUnavailable) as error:
        await provider._request(completion, {}, 9)
    assert completion.await_count == 1 and waits == []
    assert error.value.as_event() == {"status": "unavailable", "provider_status": 429, "retryable": True, "retry_after_seconds": 10, "attempts": 1}
    assert "credential" not in str(error.value)


async def test_repeated_rejection_stops_at_three_attempts_and_debits_request_time(monkeypatch):
    clock, waits = retry_clock(monkeypatch)
    async def rejected(**kwargs):
        clock[0] += 2
        raise Rejected()
    completion = AsyncMock(side_effect=rejected)
    with pytest.raises(provider.AICompletionUnavailable) as error:
        await provider._request(completion, {}, 60)
    assert completion.await_count == 3 and waits == [10, 10]
    assert [call.kwargs["timeout"] for call in completion.await_args_list] == [60, 48, 36]
    assert error.value.attempts == 3


@pytest.mark.parametrize("status", [400, 401, 402, 403])
async def test_non_retryable_response_is_not_misclassified_or_retried(monkeypatch, status):
    _, waits = retry_clock(monkeypatch)
    completion = AsyncMock(side_effect=Rejected(status))
    with pytest.raises(provider.AICompletionUnavailable) as error:
        await provider._request(completion, {}, 60)
    assert completion.await_count == 1 and waits == []
    assert error.value.status_code == status and error.value.as_event()["retryable"] is False


async def test_retry_after_http_date_and_header_precedence():
    from datetime import datetime, timedelta, timezone
    from email.utils import format_datetime
    error = Rejected(retry_after=format_datetime(datetime.now(timezone.utc) + timedelta(seconds=20), usegmt=True))
    assert 18 <= provider._retry_after(error) <= 20
    error.response.headers = {"retry-after": "10"}
    assert provider._retry_after(error) == 10


async def test_cancellation_and_partial_stream_never_restart_generation(monkeypatch):
    import asyncio
    _, waits = retry_clock(monkeypatch)
    cancelled = AsyncMock(side_effect=asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        await provider._request(cancelled, {}, 60)
    assert cancelled.await_count == 1 and not waits
    async def stream():
        yield "first chunk"
        raise Rejected()
    completion = AsyncMock(return_value=stream())
    iterator = await provider._request(completion, {}, 60)
    assert await anext(iterator) == "first chunk"
    with pytest.raises(Rejected):
        await anext(iterator)
    assert completion.await_count == 1 and not waits


async def test_late_wakeup_does_not_start_a_request_after_the_monotonic_deadline(monkeypatch):
    clock, _ = retry_clock(monkeypatch)
    async def late_wait(delay):
        clock[0] += delay + 2
    monkeypatch.setattr(provider, "_sleep", late_wait)
    completion = AsyncMock(side_effect=Rejected())
    with pytest.raises(provider.AICompletionUnavailable) as error:
        await provider._request(completion, {}, 11)
    assert completion.await_count == 1 and error.value.attempts == 1
