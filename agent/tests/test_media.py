"""Focused coverage for private-bucket media delivery."""

from __future__ import annotations

import json
from types import SimpleNamespace
from urllib.parse import urlsplit

from botocore.exceptions import ClientError
import pytest

from neos_agent.api import media
from neos_agent.auth.middleware import is_public_route


def _settings(**overrides):
    values = {
        "AWS_ENDPOINT_URL": "https://storage.example.test",
        "AWS_ACCESS_KEY_ID": "server-access-key",
        "AWS_SECRET_ACCESS_KEY": "server-secret-key",
        "AWS_S3_BUCKET_NAME": "neos-rich-media",
        "AWS_DEFAULT_REGION": "auto",
        "AWS_S3_URL_STYLE": "virtual",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def _request(settings):
    return SimpleNamespace(app=SimpleNamespace(ctx=SimpleNamespace(settings=settings)))


class _FakeS3:
    def __init__(self, presign_error: ClientError | None = None):
        self.presign_error = presign_error
        self.presign_call = None

    def generate_presigned_url(self, operation, **kwargs):
        self.presign_call = (operation, kwargs)
        if self.presign_error is not None:
            raise self.presign_error
        return "https://storage.example.test/signed-object"


@pytest.mark.parametrize(
    "object_key",
    [
        "ecosystems/omnione.webp",
        "covers/2026-07/plan_systems-01.avif",
        "image.JPG",
    ],
)
def test_safe_media_object_keys(object_key):
    assert media._is_safe_object_key(object_key)


@pytest.mark.parametrize(
    "object_key",
    [
        "",
        "../secret.webp",
        "ecosystems/../secret.webp",
        "/ecosystems/omnione.webp",
        "ecosystems\\omnione.webp",
        "ecosystems//omnione.webp",
        "ecosystems/omnione.svg",
        "ecosystems/\u2603.webp",
    ],
)
def test_unsafe_media_object_keys(object_key):
    assert not media._is_safe_object_key(object_key)


def test_media_route_is_public_for_image_elements():
    assert is_public_route("/api/v1/media/ecosystems/omnione.webp")


@pytest.mark.parametrize(
    ("url_style", "expected_host", "expected_path"),
    [
        (
            "virtual",
            "neos-rich-media-abc123.storage.railway.app",
            "/ecosystems/omnione.webp",
        ),
        (
            "path",
            "storage.railway.app",
            "/neos-rich-media-abc123/ecosystems/omnione.webp",
        ),
    ],
)
def test_s3_client_presigns_requested_url_style(
    url_style,
    expected_host,
    expected_path,
):
    media._build_s3_client.cache_clear()
    try:
        client = media._build_s3_client(
            "https://storage.railway.app",
            "server-access-key",
            "server-secret-key",
            "auto",
            url_style,
        )
        presigned_url = client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": "neos-rich-media-abc123",
                "Key": "ecosystems/omnione.webp",
            },
            ExpiresIn=3600,
            HttpMethod="GET",
        )
    finally:
        media._build_s3_client.cache_clear()

    parsed = urlsplit(presigned_url)
    assert parsed.hostname == expected_host
    assert parsed.path == expected_path
    assert "X-Amz-Signature=" in parsed.query


@pytest.mark.asyncio
async def test_media_redirect_presigns_get_for_one_hour(monkeypatch):
    client = _FakeS3()
    build_args = None

    def build_client(*args):
        nonlocal build_args
        build_args = args
        return client

    monkeypatch.setattr(media, "_build_s3_client", build_client)

    response = await media.get_media_object(
        _request(_settings()), "ecosystems/omnione.webp"
    )

    assert response.status == 302
    assert response.headers["location"] == "https://storage.example.test/signed-object"
    assert build_args == (
        "https://storage.example.test",
        "server-access-key",
        "server-secret-key",
        "auto",
        "virtual",
    )
    operation, options = client.presign_call
    assert operation == "get_object"
    assert options["Params"] == {
        "Bucket": "neos-rich-media",
        "Key": "ecosystems/omnione.webp",
    }
    assert options["ExpiresIn"] == 3600
    assert options["HttpMethod"] == "GET"


@pytest.mark.asyncio
async def test_unlisted_media_returns_clean_not_found(monkeypatch):
    monkeypatch.setattr(
        media,
        "_build_s3_client",
        lambda *args: pytest.fail("client should not be created"),
    )

    response = await media.get_media_object(
        _request(_settings()), "ecosystems/missing.webp"
    )

    assert response.status == 404
    assert json.loads(response.body) == {"error": "Media object not found"}


@pytest.mark.asyncio
async def test_unavailable_media_never_leaks_credentials(monkeypatch):
    settings = _settings()
    error = ClientError(
        {
            "Error": {"Code": "AccessDenied", "Message": settings.AWS_SECRET_ACCESS_KEY},
            "ResponseMetadata": {"HTTPStatusCode": 403},
        },
        "GetObject",
    )
    monkeypatch.setattr(media, "_build_s3_client", lambda *args: _FakeS3(error))

    response = await media.get_media_object(
        _request(settings), "ecosystems/omnione.webp"
    )

    assert response.status == 503
    assert json.loads(response.body) == {"error": "Media storage is unavailable"}
    assert settings.AWS_SECRET_ACCESS_KEY.encode() not in response.body


@pytest.mark.asyncio
async def test_incomplete_media_configuration_returns_unavailable(monkeypatch):
    monkeypatch.setattr(
        media,
        "_build_s3_client",
        lambda *args: pytest.fail("client should not be created"),
    )

    response = await media.get_media_object(
        _request(_settings(AWS_SECRET_ACCESS_KEY="")), "ecosystems/omnione.webp"
    )

    assert response.status == 503
    assert json.loads(response.body) == {"error": "Media storage is unavailable"}
