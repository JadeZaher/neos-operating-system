"""Tests for the health check endpoint."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sanic import Sanic


def create_test_app(skills_loaded=0, skills_available=False, db_connected=True):
    """Create a minimal Sanic app for endpoint testing."""
    app = Sanic(f"test-{uuid.uuid4().hex[:8]}")

    # Register blueprints
    from neos_agent.api.health import health_bp
    from neos_agent.api.skills import skills_bp

    app.blueprint(health_bp)
    app.blueprint(skills_bp)

    # Mock the skill registry
    mock_registry = MagicMock()
    mock_registry.count = skills_loaded
    mock_registry.is_loaded = skills_available

    # Mock skill listing
    if skills_available:
        from neos_agent.skills.loader import SkillMeta

        mock_skills = [
            SkillMeta(
                name=f"skill-{i}",
                description=f"Test skill {i}",
                layer=(i % 10) + 1,
                version="0.1.0",
                depends_on=[],
                file_path=f"/fake/skill-{i}/SKILL.md",
            )
            for i in range(skills_loaded)
        ]
        mock_registry.all_skills.return_value = mock_skills
        mock_registry.list_by_layer.side_effect = lambda layer: [
            s for s in mock_skills if s.layer == layer
        ]

    app.ctx.skills = mock_registry

    # Mock database
    if db_connected:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock()

        mock_db = MagicMock()
        mock_db.return_value = mock_session
        app.ctx.db = mock_db
    else:
        app.ctx.db = None

    app.ctx.db_engine = None

    return app


@pytest.mark.asyncio
async def test_health_returns_200():
    """GET /api/v1/health returns 200."""
    app = create_test_app(skills_loaded=54, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_fields():
    """Response contains all required fields."""
    app = create_test_app(skills_loaded=54, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/health")
    data = response.json
    assert "status" in data
    assert "skills_loaded" in data
    assert "skills_available" in data
    assert "database" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_skills_loaded_count():
    """skills_loaded matches registry count."""
    app = create_test_app(skills_loaded=54, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/health")
    data = response.json
    assert data["skills_loaded"] == 54


@pytest.mark.asyncio
async def test_health_skills_available_true():
    """skills_available is True when registry is loaded."""
    app = create_test_app(skills_loaded=54, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/health")
    data = response.json
    assert data["skills_available"] is True


@pytest.mark.asyncio
async def test_health_degraded_without_db():
    """Returns 200 with database='disconnected' when DB is not available."""
    app = create_test_app(skills_loaded=54, skills_available=True, db_connected=False)
    _, response = await app.asgi_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json
    assert data["database"] == "disconnected"
