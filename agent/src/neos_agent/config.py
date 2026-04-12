"""Centralized configuration using pydantic-settings.

Loads from environment variables and .env files. Required variables
(DATABASE_URL, ANTHROPIC_API_KEY) cause a startup error if missing.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so it works regardless of CWD
_AGENT_DIR = Path(__file__).resolve().parent.parent.parent  # agent/
_ENV_FILE = _AGENT_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_BASE_URL: str | None = None
    NEOS_CORE_PATH: str = "../neos-core"
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8000"
    SESSION_SECRET: str = "change-me-in-production"
    SESSION_MAX_AGE_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
