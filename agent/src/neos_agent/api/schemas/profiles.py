"""Validation schemas for editable public profile fields."""

from __future__ import annotations

from datetime import date
import re
import uuid
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,50}$")


def _optional_http_url(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be an http(s) URL")
    return value


class ProfileProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    url: str | None = Field(default=None, max_length=500)
    role: str | None = Field(default=None, max_length=255)
    started_at: str | None = None
    ended_at: str | None = None

    @field_validator("id", "name", "description", "role", mode="before")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return _optional_http_url(value, "project url")

    @field_validator("started_at", "ended_at")
    @classmethod
    def validate_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        date.fromisoformat(value)
        return value


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    profile_picture: str | None = Field(default=None, max_length=500)
    headline: str | None = Field(default=None, max_length=255)
    bio: str | None = Field(default=None, max_length=10000)
    location: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    social_links: dict[str, str] | None = None
    skills: list[str] | None = Field(default=None, max_length=100)
    interests: list[str] | None = Field(default=None, max_length=100)
    projects: list[ProfileProject] | None = Field(default=None, max_length=50)

    @field_validator(
        "username",
        "display_name",
        "profile_picture",
        "headline",
        "bio",
        "location",
        mode="before",
    )
    @classmethod
    def strip_optional_text(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is not None and not _USERNAME_RE.fullmatch(value):
            raise ValueError("username must be 3-50 letters, numbers, or underscores")
        return value

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        return _optional_http_url(value, "website")

    @field_validator("profile_picture")
    @classmethod
    def validate_profile_picture(cls, value: str | None) -> str | None:
        return _optional_http_url(value, "profile_picture")

    @field_validator("social_links")
    @classmethod
    def validate_social_links(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        if len(value) > 20:
            raise ValueError("social_links may contain at most 20 entries")
        normalized: dict[str, str] = {}
        for key, url in value.items():
            key = key.strip().lower()
            if not key or len(key) > 50:
                raise ValueError("social link names must be 1-50 characters")
            normalized_url = _optional_http_url(url, f"social_links.{key}")
            if not normalized_url:
                continue
            normalized[key] = normalized_url
        return normalized

    @field_validator("skills", "interests")
    @classmethod
    def normalize_string_list(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            item = item.strip()
            if not item or len(item) > 100:
                raise ValueError("list entries must be 1-100 characters")
            key = item.casefold()
            if key not in seen:
                normalized.append(item)
                seen.add(key)
        return normalized
