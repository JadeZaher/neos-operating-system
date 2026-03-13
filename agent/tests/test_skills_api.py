"""Tests for the skill index endpoint."""

from __future__ import annotations

import pytest
from tests.test_health import create_test_app


@pytest.mark.asyncio
async def test_skills_returns_all():
    """GET /api/v1/skills returns all skills with count."""
    app = create_test_app(skills_loaded=10, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/skills")
    assert response.status_code == 200
    data = response.json
    assert data["count"] == 10
    assert len(data["skills"]) == 10


@pytest.mark.asyncio
async def test_skills_filter_by_layer():
    """GET /api/v1/skills?layer=1 returns only layer 1 skills."""
    app = create_test_app(skills_loaded=10, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/skills?layer=1")
    assert response.status_code == 200
    data = response.json
    assert all(s["layer"] == 1 for s in data["skills"])
    assert data["count"] == len(data["skills"])


@pytest.mark.asyncio
async def test_skills_invalid_layer():
    """GET /api/v1/skills?layer=abc returns 400."""
    app = create_test_app(skills_loaded=10, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/skills?layer=abc")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_skills_layer_out_of_range():
    """GET /api/v1/skills?layer=99 returns 400."""
    app = create_test_app(skills_loaded=10, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/skills?layer=99")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_skills_response_format():
    """Each skill has required fields."""
    app = create_test_app(skills_loaded=5, skills_available=True)
    _, response = await app.asgi_client.get("/api/v1/skills")
    data = response.json
    for skill in data["skills"]:
        assert "name" in skill
        assert "description" in skill
        assert "layer" in skill
        assert "version" in skill
        assert "depends_on" in skill


@pytest.mark.asyncio
async def test_skills_not_loaded():
    """Returns 503 when skills are not loaded."""
    app = create_test_app(skills_loaded=0, skills_available=False)
    _, response = await app.asgi_client.get("/api/v1/skills")
    assert response.status_code == 503
