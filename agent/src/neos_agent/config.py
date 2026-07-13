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

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of CWD
_AGENT_DIR = Path(__file__).resolve().parent.parent.parent  # agent/
_ENV_FILE = _AGENT_DIR / ".env"

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    # AI Provider settings (LiteLLM/OpenRouter)
    AI_API_KEY: str = ""  # Empty = AI disabled (governance still works)
    AI_BASE_URL: str | None = None
    AI_MODEL: str = "anthropic/claude-sonnet-4-20250514"
    AI_PROVIDER: str = "anthropic"  # openrouter, anthropic, openai, local

    _DEFAULT_AI_MODEL: str = "anthropic/claude-sonnet-4-20250514"
    _DEFAULT_OPENROUTER_MODEL: str = "openrouter/anthropic/claude-sonnet-4-20250514"

    # Legacy aliases (backward compat with existing .env files and views)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str | None = None

    # OpenRouter aliases (preferred for multi-provider deployments)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str | None = None
    NEOS_CORE_PATH: str = "../neos-core"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8000"
    SESSION_SECRET: str = ""
    SESSION_MAX_AGE_HOURS: int = 24

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
    )

    @model_validator(mode="after")
    def _resolve_ai_key(self) -> Settings:
        """Sync AI_* and legacy ANTHROPIC_* / OPENROUTER_* settings."""
        # Canonical AI_API_KEY, falling back to OpenRouter then Anthropic keys
        if not self.AI_API_KEY:
            if self.OPENROUTER_API_KEY:
                self.AI_API_KEY = self.OPENROUTER_API_KEY
            elif self.ANTHROPIC_API_KEY:
                self.AI_API_KEY = self.ANTHROPIC_API_KEY

        # Mirror the canonical key back to the provider-specific aliases
        if self.AI_API_KEY:
            if not self.OPENROUTER_API_KEY:
                self.OPENROUTER_API_KEY = self.AI_API_KEY
            if not self.ANTHROPIC_API_KEY:
                self.ANTHROPIC_API_KEY = self.AI_API_KEY

        # Canonical AI_BASE_URL, falling back to OpenRouter then Anthropic URLs
        if not self.AI_BASE_URL:
            if self.OPENROUTER_BASE_URL:
                self.AI_BASE_URL = self.OPENROUTER_BASE_URL
            elif self.ANTHROPIC_BASE_URL:
                self.AI_BASE_URL = self.ANTHROPIC_BASE_URL
            elif self.OPENROUTER_API_KEY:
                # If an OpenRouter key is configured and no base URL was given,
                # default to the OpenRouter API endpoint.
                self.AI_BASE_URL = "https://openrouter.ai/api/v1"

        # Mirror the canonical base URL back to the provider-specific aliases
        if self.AI_BASE_URL:
            if not self.OPENROUTER_BASE_URL:
                self.OPENROUTER_BASE_URL = self.AI_BASE_URL
            if not self.ANTHROPIC_BASE_URL:
                self.ANTHROPIC_BASE_URL = self.AI_BASE_URL

        # If OpenRouter is configured and the model is still the Anthropic default,
        # route via the OpenRouter provider so the base URL/key are used correctly.
        if (
            self.OPENROUTER_API_KEY
            and self.AI_MODEL == self._DEFAULT_AI_MODEL
        ):
            self.AI_MODEL = self._DEFAULT_OPENROUTER_MODEL
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
