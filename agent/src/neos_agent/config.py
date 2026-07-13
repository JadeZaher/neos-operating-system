"""Centralized configuration using pydantic-settings.

Loads from environment variables and .env files. Required variables
(DATABASE_URL) cause a startup error if missing.
"""

from __future__ import annotations

import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of CWD
_AGENT_DIR = Path(__file__).resolve().parent.parent.parent  # agent/
_ENV_FILE = _AGENT_DIR / ".env"

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    # AI Provider settings (LiteLLM/OpenRouter)
    # Legacy Anthropic fields remain for compatibility with older integrations.
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str | None = None
    # OpenRouter free tier: sign up at https://openrouter.ai/keys
    # Free models: openrouter/quasar-alpha, openrouter/google/gemini-flash-1.5,
    # openrouter/meta-llama/llama-3.1-8b-instruct:free
    AI_API_KEY: str = Field(
        default="",  # Empty = AI disabled (governance still works)
        validation_alias=AliasChoices("AI_API_KEY", "OPENROUTER_KEY"),
    )
    AI_BASE_URL: str = "https://openrouter.ai/api/v1"
    AI_MODEL: str = "openrouter/qwen/qwen3-30b-a3b-instruct-2507"  # Default OpenRouter model
    AI_PROVIDER: str = "openrouter"  # openrouter, anthropic, openai, local

    NEOS_CORE_PATH: str = "../neos-core"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8000"
    SESSION_SECRET: str = ""
    SESSION_MAX_AGE_HOURS: int = 24

    # Private Railway bucket (empty = media redirects disabled)
    AWS_ENDPOINT_URL: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_DEFAULT_REGION: str = ""
    AWS_S3_URL_STYLE: Literal["virtual", "path"] = "virtual"

    # OAuth settings (empty = disabled)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_BASE: str = ""  # Base URL for OAuth callback (backend URL)
    FRONTEND_URL: str = ""  # Frontend URL for post-OAuth redirect (if different from OAUTH_REDIRECT_BASE)

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _resolve_ai_key(self) -> Settings:
        """Sync AI_* and legacy ANTHROPIC_* settings."""
        if not self.AI_API_KEY and self.ANTHROPIC_API_KEY:
            self.AI_API_KEY = self.ANTHROPIC_API_KEY
        if not self.ANTHROPIC_API_KEY and self.AI_API_KEY:
            self.ANTHROPIC_API_KEY = self.AI_API_KEY
        if not self.ANTHROPIC_BASE_URL and self.AI_BASE_URL:
            self.ANTHROPIC_BASE_URL = self.AI_BASE_URL
        return self

    @model_validator(mode="after")
    def _validate_session_secret(self) -> Settings:
        if not self.SESSION_SECRET or self.SESSION_SECRET == "change-me-in-production":
            if os.environ.get("NEOS_ENV", "development") == "production":
                raise ValueError("SESSION_SECRET must be set in production")
            self.SESSION_SECRET = secrets.token_hex(32)
            _logger.warning(
                "SESSION_SECRET not set — using random value "
                "(sessions won't persist across restarts)"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
