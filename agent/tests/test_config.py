"""Tests for neos_agent.config."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


def test_settings_loads_from_env():
    """Settings reads required values from environment."""
    env = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "ANTHROPIC_API_KEY": "sk-test-123",
    }
    with patch.dict(os.environ, env, clear=False):
        from neos_agent.config import Settings
        s = Settings()
        assert s.DATABASE_URL == env["DATABASE_URL"]
        assert s.ANTHROPIC_API_KEY == env["ANTHROPIC_API_KEY"]


def test_settings_defaults():
    """Settings has correct defaults for optional fields."""
    env = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "ANTHROPIC_API_KEY": "sk-test-123",
    }
    with patch.dict(os.environ, env, clear=False):
        from neos_agent.config import Settings
        s = Settings()
        assert s.NEOS_CORE_PATH == "../neos-core"
        assert s.LOG_LEVEL == "info"
        assert s.CORS_ORIGINS == "*"
        assert "claude" in s.CLAUDE_MODEL.lower() or "sonnet" in s.CLAUDE_MODEL.lower()


def test_settings_missing_required_raises():
    """Missing required env vars raise a validation error."""
    # Clear both required vars to force failure
    env = {k: v for k, v in os.environ.items()
           if k not in ("DATABASE_URL", "ANTHROPIC_API_KEY")}
    with patch.dict(os.environ, env, clear=True):
        from neos_agent.config import Settings
        with pytest.raises(Exception):
            Settings()


def test_settings_custom_overrides():
    """All settings can be overridden via environment."""
    env = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "ANTHROPIC_API_KEY": "sk-custom",
        "NEOS_CORE_PATH": "/custom/path",
        "CLAUDE_MODEL": "claude-opus-4-20250514",
        "LOG_LEVEL": "debug",
        "CORS_ORIGINS": "https://example.com",
    }
    with patch.dict(os.environ, env, clear=False):
        from neos_agent.config import Settings
        s = Settings()
        assert s.NEOS_CORE_PATH == "/custom/path"
        assert s.CLAUDE_MODEL == "claude-opus-4-20250514"
        assert s.LOG_LEVEL == "debug"
        assert s.CORS_ORIGINS == "https://example.com"


def test_get_settings_cached():
    """get_settings returns the same instance on repeated calls."""
    env = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "ANTHROPIC_API_KEY": "sk-test",
    }
    with patch.dict(os.environ, env, clear=False):
        from neos_agent.config import get_settings
        # Clear LRU cache to isolate this test
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()
