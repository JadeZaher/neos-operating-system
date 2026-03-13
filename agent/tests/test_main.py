"""Tests for neos_agent.main app factory."""

from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import pytest

from neos_agent.config import Settings


def _make_settings(**overrides) -> Settings:
    """Create a Settings instance with test defaults."""
    defaults = {
        "DATABASE_URL": "sqlite+aiosqlite://",
        "ANTHROPIC_API_KEY": "sk-test-key",
        "NEOS_CORE_PATH": "../neos-core",
        "LOG_LEVEL": "info",
        "CORS_ORIGINS": "*",
    }
    defaults.update(overrides)
    env = {k: v for k, v in defaults.items()}
    with patch.dict(os.environ, env, clear=False):
        return Settings(**defaults)


def test_create_app_returns_sanic_app():
    """create_app returns a Sanic application instance."""
    from neos_agent.main import create_app
    from sanic import Sanic

    settings = _make_settings()
    app = create_app(settings=settings)
    assert isinstance(app, Sanic)


def test_create_app_registers_blueprints():
    """App has health and skills blueprints registered."""
    from neos_agent.main import create_app

    settings = _make_settings()
    app = create_app(settings=settings)

    blueprint_names = [bp.name for bp in app.blueprints.values()]
    assert "health" in blueprint_names
    assert "skills" in blueprint_names


def test_create_app_stores_settings():
    """App stores settings on app.ctx."""
    from neos_agent.main import create_app

    settings = _make_settings()
    app = create_app(settings=settings)
    assert app.ctx.settings is settings


def test_create_app_configures_cors():
    """App sets CORS_ORIGINS in config."""
    from neos_agent.main import create_app

    settings = _make_settings(CORS_ORIGINS="https://example.com")
    app = create_app(settings=settings)
    assert app.config.CORS_ORIGINS == "https://example.com"


def test_create_app_default_cors():
    """Default CORS_ORIGINS is wildcard."""
    from neos_agent.main import create_app

    settings = _make_settings()
    app = create_app(settings=settings)
    assert app.config.CORS_ORIGINS == "*"


def test_create_app_has_lifecycle_listeners():
    """App has before_server_start and after_server_stop listeners."""
    from neos_agent.main import create_app

    settings = _make_settings()
    app = create_app(settings=settings)

    # Sanic 25.x stores listeners in _future_listeners before server starts
    future = getattr(app, "_future_listeners", [])
    before_start = [fl for fl in future if fl.event == "before_server_start"]
    after_stop = [fl for fl in future if fl.event == "after_server_stop"]
    assert len(before_start) >= 2  # skills + db
    assert len(after_stop) >= 1  # db cleanup
