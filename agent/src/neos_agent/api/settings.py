"""JSON API blueprint for generic application settings (key/value store).

Blueprint: settings_api_bp, url_prefix="/api/v1/settings"

Backs feature flags / configuration values used by the frontend. A missing
key is not an error -- the frontend treats a null value as "not configured".
Returns JSON responses only.
"""

from __future__ import annotations

import logging

from sanic import Blueprint, json
from sanic.request import Request
from sqlalchemy import select

from neos_agent.db.models import AppSetting
from neos_agent.api.helpers import require_auth, require_admin
from neos_agent.api.schemas.settings import AppSettingPutRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

settings_api_bp = Blueprint("settings_api", url_prefix="/api/v1/settings")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@settings_api_bp.get("/")
async def get_setting(request: Request):
    """GET /api/v1/settings?key=... -- Read a single setting by key.

    Always returns 200; value is null when the key is unset.
    """
    member, err = require_auth(request)
    if err:
        return err

    key = request.args.get("key")
    if not key:
        return json({"error": "key is required"}, status=400)

    async with request.app.ctx.db() as session:
        stmt = select(AppSetting).where(AppSetting.key == key)
        row = (await session.execute(stmt)).scalar_one_or_none()

    return json({"key": key, "value": row.value if row else None})


@settings_api_bp.put("/")
async def put_setting(request: Request):
    """PUT /api/v1/settings -- Upsert a setting by key.

    Accepts JSON: AppSettingPutRequest
    """
    admin, err = require_admin(request)
    if err:
        return err

    body = request.json or {}
    try:
        put_req = AppSettingPutRequest(**body)
    except Exception as e:
        return json({"error": f"Invalid request: {e}"}, status=400)

    async with request.app.ctx.db() as session:
        stmt = select(AppSetting).where(AppSetting.key == put_req.key)
        row = (await session.execute(stmt)).scalar_one_or_none()

        if row is None:
            row = AppSetting(key=put_req.key, value=put_req.value, updated_by=admin.id)
            session.add(row)
        else:
            row.value = put_req.value
            row.updated_by = admin.id

        await session.commit()

    return json({"key": put_req.key, "value": put_req.value})
