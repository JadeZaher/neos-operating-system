"""Skill index endpoint.

Returns the full skill catalog with metadata, filterable by layer.
"""

from __future__ import annotations

from sanic import Blueprint, json
from sanic.request import Request

from neos_agent.api.schemas import ApiError, SkillItem, SkillsResponse

skills_bp = Blueprint("skills", url_prefix="/api/v1")


@skills_bp.get("/skills")
async def list_skills(request: Request):
    """GET /api/v1/skills — Skill catalog with optional layer filter."""
    registry = getattr(request.app.ctx, "skills", None)
    if registry is None or not registry.is_loaded:
        return json(ApiError(error="Skills not loaded").model_dump(), status=503)

    # Parse optional layer parameter
    layer_param = request.args.get("layer")
    if layer_param is not None:
        try:
            layer = int(layer_param)
        except ValueError:
            return json(
                ApiError(error=f"Invalid layer parameter: {layer_param!r} — must be an integer").model_dump(),
                status=400,
            )

        if layer < 1 or layer > 10:
            return json(
                ApiError(error=f"Layer must be between 1 and 10, got {layer}").model_dump(),
                status=400,
            )

        skills = registry.list_by_layer(layer)
    else:
        skills = registry.all_skills()

    skill_items = [
        SkillItem(
            name=s.name,
            description=s.description,
            layer=s.layer,
            version=s.version,
            depends_on=s.depends_on,
        )
        for s in skills
    ]

    return json(SkillsResponse(count=len(skill_items), skills=skill_items).model_dump())
