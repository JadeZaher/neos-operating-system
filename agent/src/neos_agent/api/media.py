"""Private bucket media delivery through short-lived signed redirects."""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from sanic import Blueprint, json
from sanic.request import Request
from sanic.response import redirect


logger = logging.getLogger(__name__)

media_api_bp = Blueprint("media_api", url_prefix="/api/v1/media")

_ALLOWED_MEDIA_SUFFIXES = (".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp")
_KEY_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")
_NOT_FOUND_CODES = frozenset({"404", "NoSuchKey", "NoSuchObject", "NotFound"})
_PRESIGN_TTL_SECONDS = 60 * 60
_ALLOWED_URL_STYLES = frozenset({"path", "virtual"})
_PUBLIC_MEDIA_KEYS = frozenset(
    {
        "ecosystems/escherbridge.webp",
        "ecosystems/oasis.webp",
        "ecosystems/omnione.webp",
        "ecosystems/plan-systems.webp",
    }
)


def _is_safe_object_key(object_key: str) -> bool:
    """Accept conservative, traversal-free keys for raster media objects."""
    if not object_key or len(object_key) > 1024:
        return False
    if not object_key.lower().endswith(_ALLOWED_MEDIA_SUFFIXES):
        return False

    segments = object_key.split("/")
    return all(
        segment not in {"", ".", ".."} and _KEY_SEGMENT.fullmatch(segment)
        for segment in segments
    )


def _storage_config(settings: object) -> tuple[str, str, str, str, str, str] | None:
    endpoint_url = str(getattr(settings, "AWS_ENDPOINT_URL", "") or "").strip()
    access_key = str(getattr(settings, "AWS_ACCESS_KEY_ID", "") or "").strip()
    secret_key = str(getattr(settings, "AWS_SECRET_ACCESS_KEY", "") or "").strip()
    bucket = str(getattr(settings, "AWS_S3_BUCKET_NAME", "") or "").strip()
    region = str(getattr(settings, "AWS_DEFAULT_REGION", "") or "").strip()
    url_style = str(getattr(settings, "AWS_S3_URL_STYLE", "virtual") or "").strip()

    if not all((endpoint_url, access_key, secret_key, bucket, region)):
        return None
    if url_style not in _ALLOWED_URL_STYLES:
        return None
    return endpoint_url, access_key, secret_key, bucket, region, url_style


@lru_cache(maxsize=4)
def _build_s3_client(
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    region: str,
    url_style: str,
) -> Any:
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": url_style},
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )


def _is_missing_object(error: ClientError) -> bool:
    error_code = str(error.response.get("Error", {}).get("Code", ""))
    status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return error_code in _NOT_FOUND_CODES or status_code == 404


@media_api_bp.get("/<object_key:path>")
async def get_media_object(request: Request, object_key: str):
    """Redirect a safe media key to a one-hour S3-compatible presigned URL."""
    if not _is_safe_object_key(object_key):
        return json({"error": "Invalid media object key"}, status=400)
    if object_key not in _PUBLIC_MEDIA_KEYS:
        return json({"error": "Media object not found"}, status=404)

    storage = _storage_config(request.app.ctx.settings)
    if storage is None:
        return json({"error": "Media storage is unavailable"}, status=503)

    endpoint_url, access_key, secret_key, bucket, region, url_style = storage
    try:
        client = _build_s3_client(
            endpoint_url,
            access_key,
            secret_key,
            region,
            url_style,
        )
        presigned_url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": object_key},
            ExpiresIn=_PRESIGN_TTL_SECONDS,
            HttpMethod="GET",
        )
    except ClientError as error:
        if _is_missing_object(error):
            return json({"error": "Media object not found"}, status=404)
        logger.warning("Media storage rejected a request")
        return json({"error": "Media storage is unavailable"}, status=503)
    except (BotoCoreError, OSError, ValueError):
        logger.warning("Media storage request failed")
        return json({"error": "Media storage is unavailable"}, status=503)
    except Exception:
        logger.warning("Unexpected media storage failure")
        return json({"error": "Media storage is unavailable"}, status=503)

    response = redirect(presigned_url, status=302)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
