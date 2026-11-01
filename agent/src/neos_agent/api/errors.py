"""Expected API failures as exceptions, and the scoped loader; see api/AGENTS.md "Handler contracts"."""
from __future__ import annotations

import uuid
from typing import Any, Iterable, TypeVar

from sanic import Sanic, json
from sanic.request import Request
from sqlalchemy import select

Model = TypeVar("Model")


# Exception-as-response: raise anywhere in a handler, rendered once by register_api_errors.
class ApiError(Exception):
    """An expected failure answered as {"error": message, **extra} with `status`."""

    def __init__(self, status: int, message: str, extra: dict[str, Any] | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.extra = extra or {}


# Centralized exception handler: one JSON shape for every ApiError.
def register_api_errors(app: Sanic) -> None:
    """Render ApiError as its JSON body and status on every route of `app`."""

    @app.exception(ApiError)
    async def render_api_error(request: Request, error: ApiError):
        return json({"error": error.message, **error.extra}, status=error.status)


# Scoped loader: a row outside the caller's ecosystems is "not found", never a 403 existence leak.
async def get_scoped_or_404(
    session,
    request: Request,
    model: type[Model],
    entity_id: uuid.UUID,
    *,
    options: Iterable = (),
    label: str,
    ecosystem_ids: Iterable[uuid.UUID] | None = None,
    include_shared: bool = True,
) -> Model:
    """Load `model` by id within `ecosystem_ids` (default: the caller's authorized ones), else ApiError(404, "<label> not found").

    `include_shared` must match the entity's list endpoint; see api/AGENTS.md "Handler contracts" rule 5.
    """
    # Deferred: helpers imports ApiError from this module.
    from neos_agent.api.helpers import get_authorized_ecosystem_ids
    from neos_agent.auth.ecosystem_scope import restrict_to_ecosystems

    scope = get_authorized_ecosystem_ids(request) if ecosystem_ids is None else list(ecosystem_ids)
    statement = select(model).where(model.id == entity_id).options(*options)
    statement = restrict_to_ecosystems(statement, model, scope, include_shared=include_shared)
    row = (await session.execute(statement)).scalar_one_or_none()
    if row is None:
        raise ApiError(404, f"{label} not found")
    return row
