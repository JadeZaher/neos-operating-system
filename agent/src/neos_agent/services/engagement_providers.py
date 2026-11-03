"""Notification provider adapters with explicit delivery outcomes."""
from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import ipaddress
import json
import re
import socket
from urllib.parse import urlsplit

import httpx


@dataclass(frozen=True)
class SendResult:
    state: str
    provider_id: str | None = None
    error_code: str | None = None
    retry_after: int = 60


def setting(settings, name, default=""):
    return getattr(settings, name, default)


def valid_https_base(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment
    except ValueError:
        return False


def configured_channels(settings) -> dict[str, tuple[bool, str]]:
    common = (
        len(setting(settings, "ENGAGEMENT_SIGNING_SECRET")) >= 32
        and valid_https_base(setting(settings, "ENGAGEMENT_PUBLIC_URL"))
        and valid_https_base(setting(settings, "ENGAGEMENT_API_PUBLIC_URL"))
    )
    required = {
        "email": ("RESEND_API_KEY", "RESEND_FROM", "RESEND_WEBHOOK_SECRET"),
        "push": ("VAPID_PUBLIC_KEY", "VAPID_PRIVATE_KEY", "VAPID_SUBJECT"),
        "sms": ("TWILIO_ACCOUNT_SID", "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET", "TWILIO_AUTH_TOKEN", "TWILIO_MESSAGING_SERVICE_SID", "TWILIO_VERIFY_SERVICE_SID"),
    }
    result = {}
    for channel, names in required.items():
        missing = [name for name in names if not setting(settings, name)]
        if not common or missing:
            result[channel] = (False, "pending_setup")
        elif not setting(settings, "ENGAGEMENT_EXTERNAL_ENABLED", False) or not setting(settings, f"ENGAGEMENT_{channel.upper()}_ENABLED", False):
            result[channel] = (False, "configured_disabled")
        else:
            result[channel] = (True, "ready")
    return result


def _decode_key(value: str, size: int) -> bytes:
    if not isinstance(value, str) or len(value) > 255 or not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", value):
        raise ValueError("Invalid browser push key")
    try:
        decoded = base64.urlsafe_b64decode(value.rstrip("=") + "=" * (-len(value.rstrip("=")) % 4))
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid browser push key") from error
    if len(decoded) != size:
        raise ValueError("Invalid browser push key")
    return decoded


def validate_push_shape(endpoint: str, p256dh: str, auth: str) -> str:
    if not isinstance(endpoint, str) or len(endpoint) > 2048:
        raise ValueError("Unsupported browser push endpoint")
    try:
        parsed = urlsplit(endpoint)
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as error:
        raise ValueError("Unsupported browser push endpoint") from error
    exact = {"fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com"}
    suffixes = (".push.services.mozilla.com", ".push.apple.com", ".notify.windows.com")
    if (parsed.scheme != "https" or parsed.username or parsed.password or port not in (None, 443)
            or parsed.fragment or not parsed.path or host.endswith(".")
            or not (host in exact or any(host.endswith(suffix) and host != suffix[1:] for suffix in suffixes))):
        raise ValueError("Unsupported browser push endpoint")
    if _decode_key(p256dh, 65)[0] != 4:
        raise ValueError("Invalid browser push key")
    _decode_key(auth, 16)
    return host


async def validate_push_destination(endpoint: str, p256dh: str, auth: str, *, resolver=None) -> None:
    host = validate_push_shape(endpoint, p256dh, auth)
    lookup = resolver or asyncio.get_running_loop().getaddrinfo
    answers = await lookup(host, 443, type=socket.SOCK_STREAM)
    if not answers or any(not ipaddress.ip_address(row[4][0]).is_global for row in answers):
        raise ValueError("Unsupported browser push destination")


class NoRedirectSession:
    """Reject redirects in the HTTP transport used by pywebpush."""

    def __init__(self):
        import requests
        self.session = requests.Session()

    def post(self, url, **kwargs):
        kwargs["allow_redirects"] = False
        response = self.session.post(url, **kwargs)
        if 300 <= response.status_code < 400:
            raise ValueError("Push redirects are not supported")
        return response

    def close(self):
        self.session.close()


def _retry_after(response) -> int:
    try:
        return min(3600, max(1, int(response.headers.get("retry-after", "60"))))
    except (TypeError, ValueError):
        return 60


class ProviderTransport:
    """Ports/adapters boundary; callers inject a fake transport for tests."""

    def __init__(self, settings, client: httpx.AsyncClient):
        self.settings = settings
        self.client = client

    def _ready(self, channel):
        return configured_channels(self.settings)[channel][0]

    async def send(self, channel: str, payload: dict, key: str) -> SendResult:
        if not self._ready(channel):
            return SendResult("blocked_configuration", error_code="channel_not_ready")
        if channel == "email":
            return await self._email(payload, key)
        if channel == "sms":
            return await self._sms(payload)
        if channel == "push":
            return await self._push(payload)
        return SendResult("rejected", error_code="unsupported_channel")

    async def _email(self, payload: dict, key: str) -> SendResult:
        try:
            response = await self.client.post(
                "https://api.resend.com/emails", json=payload,
                headers={"Authorization": f"Bearer {self.settings.RESEND_API_KEY}", "Idempotency-Key": key},
            )
        except httpx.HTTPError:
            return SendResult("ambiguous", error_code="email_transport_uncertain")
        if response.status_code == 429:
            return SendResult("retryable", error_code="email_rate_limit", retry_after=_retry_after(response))
        if response.status_code >= 500:
            return SendResult("ambiguous", error_code="email_provider_uncertain")
        if not 200 <= response.status_code < 300:
            return SendResult("rejected", error_code=f"email_http_{response.status_code}")
        try:
            provider_id = response.json().get("id")
        except ValueError:
            provider_id = None
        if not isinstance(provider_id, str) or not provider_id:
            return SendResult("ambiguous", error_code="email_missing_receipt")
        return SendResult("accepted", provider_id=provider_id)

    def _twilio_auth(self):
        return httpx.BasicAuth(self.settings.TWILIO_API_KEY_SID, self.settings.TWILIO_API_KEY_SECRET)

    async def _sms(self, payload: dict) -> SendResult:
        try:
            response = await self.client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{self.settings.TWILIO_ACCOUNT_SID}/Messages.json",
                data=payload, auth=self._twilio_auth(),
            )
        except httpx.HTTPError:
            return SendResult("ambiguous", error_code="sms_transport_uncertain")
        if response.status_code == 429:
            return SendResult("retryable", error_code="sms_rate_limit", retry_after=_retry_after(response))
        if response.status_code >= 500:
            return SendResult("ambiguous", error_code="sms_provider_uncertain")
        if not 200 <= response.status_code < 300:
            return SendResult("rejected", error_code=f"sms_http_{response.status_code}")
        try:
            provider_id = response.json().get("sid")
        except ValueError:
            provider_id = None
        return SendResult("accepted", provider_id) if provider_id else SendResult("ambiguous", error_code="sms_missing_receipt")

    async def start_sms_verification(self, destination: str) -> SendResult:
        if not self._ready("sms"):
            return SendResult("blocked_configuration", error_code="channel_not_ready")
        try:
            response = await self.client.post(
                f"https://verify.twilio.com/v2/Services/{self.settings.TWILIO_VERIFY_SERVICE_SID}/Verifications",
                data={"To": destination, "Channel": "sms"}, auth=self._twilio_auth(),
            )
            body = response.json() if response.status_code < 500 else {}
        except (httpx.HTTPError, ValueError):
            return SendResult("ambiguous", error_code="verification_transport_uncertain")
        if response.status_code == 429:
            return SendResult("retryable", error_code="verification_rate_limit", retry_after=_retry_after(response))
        if 200 <= response.status_code < 300 and body.get("sid") and body.get("status") == "pending":
            return SendResult("accepted", provider_id=body["sid"])
        return SendResult("rejected", error_code="verification_not_started")

    async def check_sms_verification(self, provider_id: str, code: str) -> bool:
        if not self._ready("sms"):
            return False
        try:
            response = await self.client.post(
                f"https://verify.twilio.com/v2/Services/{self.settings.TWILIO_VERIFY_SERVICE_SID}/VerificationCheck",
                data={"VerificationSid": provider_id, "Code": code}, auth=self._twilio_auth(),
            )
            return response.status_code == 200 and response.json().get("status") == "approved"
        except (httpx.HTTPError, ValueError):
            return False

    async def _push(self, payload: dict) -> SendResult:
        try:
            subscription = payload["subscription"]
            await validate_push_destination(subscription["endpoint"], subscription["keys"]["p256dh"], subscription["keys"]["auth"])
        except (ValueError, KeyError, OSError):
            return SendResult("rejected", error_code="push_destination_invalid")
        timeout = min(20, max(1, float(setting(self.settings, "ENGAGEMENT_SEND_TIMEOUT_SECONDS", 15))))

        def send_sync():
            from pywebpush import webpush
            transport = NoRedirectSession()
            try:
                response = webpush(
                    subscription_info=subscription, data=json.dumps(payload["data"], separators=(",", ":")),
                    vapid_private_key=self.settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": self.settings.VAPID_SUBJECT},
                    timeout=timeout, requests_session=transport,
                )
                return response.status_code
            except Exception as error:
                response = getattr(error, "response", None)
                if response is not None:
                    return response.status_code
                raise
            finally:
                transport.close()
        try:
            code = await asyncio.wait_for(asyncio.to_thread(send_sync), timeout=timeout + 2)
        except (ValueError, ImportError):
            return SendResult("rejected", error_code="push_transport_invalid")
        except Exception:
            return SendResult("ambiguous", error_code="push_transport_uncertain")
        if 200 <= code < 300:
            return SendResult("accepted")
        if code in (404, 410):
            return SendResult("rejected", error_code="push_endpoint_expired")
        if code == 429:
            return SendResult("retryable", error_code="push_rate_limit")
        if code >= 500:
            return SendResult("ambiguous", error_code="push_provider_uncertain")
        return SendResult("rejected", error_code=f"push_http_{code}")
