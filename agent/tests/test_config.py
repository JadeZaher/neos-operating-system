"""Tests for neos_agent.config."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


def test_settings_loads_from_env():
    """Settings reads required values from environment."""
    env = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "OPENROUTER_KEY": "sk-or-test-123",
    }
    with patch.dict(os.environ, env, clear=True):
        from neos_agent.config import Settings
        s = Settings(_env_file=None)
        assert s.DATABASE_URL == env["DATABASE_URL"]
        assert s.AI_API_KEY == env["OPENROUTER_KEY"]
        assert s.AI_PROVIDER == "openrouter"


def test_settings_defaults():
    """Settings has correct defaults for optional fields."""
    env = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "OPENROUTER_KEY": "sk-or-test-123",
    }
    with patch.dict(os.environ, env, clear=True):
        from neos_agent.config import Settings
        s = Settings(_env_file=None)
        assert s.NEOS_CORE_PATH == "../neos-core"
        assert s.LOG_LEVEL == "info"
        assert s.CORS_ORIGINS == "http://localhost:5173,http://localhost:8000"
        assert s.AI_MODEL.startswith("openrouter/")
        assert s.AWS_S3_URL_STYLE == "virtual"


def test_settings_missing_required_raises():
    """Missing required env vars raise a validation error."""
    # Clear both required vars to force failure
    env = {k: v for k, v in os.environ.items()
           if k not in ("DATABASE_URL", "ANTHROPIC_API_KEY", "OPENROUTER_KEY", "AI_API_KEY")}
    with patch.dict(os.environ, env, clear=True):
        from neos_agent.config import Settings
        with pytest.raises(Exception):
            Settings(_env_file=None)


def test_settings_custom_overrides():
    """All settings can be overridden via environment."""
    env = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "OPENROUTER_KEY": "sk-or-custom",
        "NEOS_CORE_PATH": "/custom/path",
        "AI_MODEL": "openrouter/qwen/qwen3-30b-a3b-instruct-2507",
        "LOG_LEVEL": "debug",
        "CORS_ORIGINS": "https://example.com",
        "AWS_S3_URL_STYLE": "path",
    }
    with patch.dict(os.environ, env, clear=True):
        from neos_agent.config import Settings
        s = Settings(_env_file=None)
        assert s.NEOS_CORE_PATH == "/custom/path"
        assert s.AI_MODEL == "openrouter/qwen/qwen3-30b-a3b-instruct-2507"
        assert s.LOG_LEVEL == "debug"
        assert s.CORS_ORIGINS == "https://example.com"
        assert s.AWS_S3_URL_STYLE == "path"


def test_settings_rejects_invalid_s3_url_style():
    """Railway bucket URL style is restricted to boto3's supported modes."""
    env = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "AWS_S3_URL_STYLE": "automatic",
    }
    with patch.dict(os.environ, env, clear=True):
        from neos_agent.config import Settings
        with pytest.raises(Exception, match="AWS_S3_URL_STYLE"):
            Settings(_env_file=None)


def test_get_settings_cached():
    """get_settings returns the same instance on repeated calls."""
    env = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "OPENROUTER_KEY": "sk-or-test",
    }
    with patch.dict(os.environ, env, clear=True):
        from neos_agent.config import get_settings
        # Clear LRU cache to isolate this test
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
        get_settings.cache_clear()
