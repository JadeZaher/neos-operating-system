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
    AI_MODEL: str = "openrouter/anthropic/claude-sonnet-4-20250514"
    AI_PROVIDER: str = "openrouter"  # openrouter, anthropic, openai, local

    # Legacy aliases (backward compat with existing .env files)
    ANTHROPIC_API_KEY: str = ""

    NEOS_CORE_PATH: str = "../neos-core"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8000"
    SESSION_SECRET: str = ""
    SESSION_MAX_AGE_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @model_validator(mode="after")
    def _resolve_ai_key(self) -> Settings:
        """Fall back to ANTHROPIC_API_KEY if AI_API_KEY is not set."""
        if not self.AI_API_KEY and self.ANTHROPIC_API_KEY:
            self.AI_API_KEY = self.ANTHROPIC_API_KEY
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
