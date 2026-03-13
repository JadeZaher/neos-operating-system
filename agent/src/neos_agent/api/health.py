"""Health check endpoint.

Reports service status, skill loading status, and database connectivity.
Always returns 200, even in degraded mode.
"""

from __future__ import annotations

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import text

health_bp = Blueprint("health", url_prefix="/api/v1")


@health_bp.get("/health")
async def health_check(request: Request):
    """GET /api/v1/health — Service health status."""
    from neos_agent import __version__

    # Skill registry status
    skills_registry = getattr(request.app.ctx, "skills", None)
    skills_loaded = skills_registry.count if skills_registry else 0
    skills_available = skills_registry.is_loaded if skills_registry else False

    # Database connectivity
    db_status = "disconnected"
    session_factory = getattr(request.app.ctx, "db", None)
    if session_factory is not None:
        try:
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "disconnected"

    return json({
        "status": "healthy",
        "skills_loaded": skills_loaded,
        "skills_available": skills_available,
        "database": db_status,
        "version": __version__,
    })
