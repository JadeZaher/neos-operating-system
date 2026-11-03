"""Provider transport contract tests; no external requests."""
import base64
import json
from types import SimpleNamespace

import httpx
import pytest

from neos_agent.services.engagement_providers import (
    NoRedirectSession, ProviderTransport, configured_channels, validate_push_destination, validate_push_shape,
)


def provider_settings(**changes):
    fields = dict(ENGAGEMENT_EXTERNAL_ENABLED=True, ENGAGEMENT_EMAIL_ENABLED=True,
        ENGAGEMENT_PUSH_ENABLED=True, ENGAGEMENT_SMS_ENABLED=True,
        ENGAGEMENT_PUBLIC_URL="https://neos.example", ENGAGEMENT_API_PUBLIC_URL="https://api.neos.example",
        ENGAGEMENT_SIGNING_SECRET="s" * 40, RESEND_API_KEY="test-only", RESEND_FROM="NEOS <updates@example.test>",
        RESEND_REPLY_TO="", RESEND_WEBHOOK_SECRET="test-only", VAPID_PUBLIC_KEY="test-only",
        VAPID_PRIVATE_KEY="test-only", VAPID_SUBJECT="mailto:operator@example.test",
        TWILIO_ACCOUNT_SID="AC" + "a" * 32, TWILIO_API_KEY_SID="SK" + "a" * 32,
        TWILIO_API_KEY_SECRET="test-only", TWILIO_AUTH_TOKEN="test-only",
        TWILIO_MESSAGING_SERVICE_SID="MG" + "a" * 32, TWILIO_VERIFY_SERVICE_SID="VA" + "a" * 32,
        ENGAGEMENT_SEND_TIMEOUT_SECONDS=2)
    fields.update(changes)
    return SimpleNamespace(**fields)


def push_keys():
    return (base64.urlsafe_b64encode(b"\x04" + b"a" * 64).decode().rstrip("="),
            base64.urlsafe_b64encode(b"b" * 16).decode().rstrip("="))


@pytest.mark.parametrize("channel", ["email", "sms", "push"])
async def test_disabled_provider_never_calls_transport(channel):
    called = []
    async def handle(request):
        called.append(request)
        return httpx.Response(200, json={"id": "id"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await ProviderTransport(provider_settings(ENGAGEMENT_EXTERNAL_ENABLED=False), client).send(channel, {}, "stable")
    assert result.state == "blocked_configuration"
    assert called == []


async def test_resend_retries_keep_exact_body_and_key():
    requests = []
    async def handle(request):
        requests.append(request)
        return httpx.Response(429, headers={"Retry-After": "75"}) if len(requests) == 1 else httpx.Response(200, json={"id": "email-1"})
    body = {"from": "updates@example.test", "to": ["member@example.test"], "subject": "Updates", "text": "Open updates"}
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        transport = ProviderTransport(provider_settings(), client)
        first = await transport.send("email", body, "stable-key")
        second = await transport.send("email", body, "stable-key")
    assert first.state == "retryable" and first.retry_after == 75
    assert second.state == "accepted" and second.provider_id == "email-1"
    assert requests[0].content == requests[1].content
    assert requests[0].headers["Idempotency-Key"] == requests[1].headers["Idempotency-Key"] == "stable-key"


@pytest.mark.parametrize("channel", ["email", "sms"])
async def test_timeout_is_ambiguous(channel):
    async def handle(request):
        raise httpx.ReadTimeout("synthetic", request=request)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await ProviderTransport(provider_settings(), client).send(channel, {}, "key")
    assert result.state == "ambiguous"
    assert "synthetic" not in result.error_code


@pytest.mark.parametrize("status,expected", [(400, "rejected"), (429, "retryable"), (500, "ambiguous"), (200, "ambiguous")])
async def test_email_response_classification(status, expected):
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(status, json={}))) as client:
        result = await ProviderTransport(provider_settings(), client).send("email", {}, "key")
    assert result.state == expected


async def test_twilio_verify_requires_actual_approved_result():
    replies = [{"sid": "VE123", "status": "pending"}, {"status": "pending"}, {"status": "approved"}]
    requests = []
    async def handle(request):
        requests.append(request)
        return httpx.Response(200, json=replies.pop(0))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        transport = ProviderTransport(provider_settings(), client)
        started = await transport.start_sms_verification("+15555550123")
        assert started.state == "accepted" and started.provider_id == "VE123"
        assert not await transport.check_sms_verification("VE123", "123456")
        assert await transport.check_sms_verification("VE123", "123456")
    assert all(request.url.host == "verify.twilio.com" for request in requests)


@pytest.mark.parametrize("endpoint", [
    "http://fcm.googleapis.com/send/x", "https://fcm.googleapis.com.evil.test/send/x",
    "https://evilpush.services.mozilla.com/send/x", "https://fcm.googleapis.com@127.0.0.1/x",
    "https://fcm.googleapis.com:444/send/x", "https://127.0.0.1/x",
    "https://localhost/x", "https://web.push.apple.com./x", "https://fcm.googleapis.com/x#frag",
])
def test_push_rejects_untrusted_endpoints(endpoint):
    public, auth = push_keys()
    with pytest.raises(ValueError):
        validate_push_shape(endpoint, public, auth)


@pytest.mark.parametrize("address", ["127.0.0.1", "10.0.0.1", "169.254.169.254", "::1"])
async def test_push_rechecks_dns(address):
    public, auth = push_keys()
    async def resolve(*args, **kwargs):
        return [(2, 1, 6, "", (address, 443))]
    with pytest.raises(ValueError):
        await validate_push_destination("https://fcm.googleapis.com/send/x", public, auth, resolver=resolve)


async def test_supported_push_dns_and_keys():
    public, auth = push_keys()
    async def resolve(*args, **kwargs):
        return [(2, 1, 6, "", ("8.8.8.8", 443))]
    await validate_push_destination("https://updates.push.services.mozilla.com/wpush/v2/test", public, auth, resolver=resolve)
    with pytest.raises(ValueError):
        validate_push_shape("https://fcm.googleapis.com/send/x", "invalid", auth)


def test_push_transport_never_follows_redirect(monkeypatch):
    calls = []
    class FakeSession:
        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return SimpleNamespace(status_code=302)
        def close(self):
            pass
    import requests
    monkeypatch.setattr(requests, "Session", FakeSession)
    transport = NoRedirectSession()
    with pytest.raises(ValueError):
        transport.post("https://fcm.googleapis.com/send/x", data="payload")
    assert len(calls) == 1 and calls[0][1]["allow_redirects"] is False


def test_readiness_requires_complete_configuration_and_separate_activation():
    assert configured_channels(provider_settings(RESEND_API_KEY=""))["email"] == (False, "pending_setup")
    assert configured_channels(provider_settings(ENGAGEMENT_EMAIL_ENABLED=False))["email"] == (False, "configured_disabled")
    assert configured_channels(provider_settings(ENGAGEMENT_SIGNING_SECRET="short"))["email"][0] is False
    assert configured_channels(provider_settings())["email"] == (True, "ready")
