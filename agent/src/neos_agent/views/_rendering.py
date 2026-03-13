"""Shared rendering utilities for dashboard views.

Provides Jinja2 template rendering, htmx HTML fragment responses,
and ecosystem-scoping helpers.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")

import jinja2
from sanic import html as html_response

# Template directory is a sibling of the views package
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=True,
    enable_async=True,
)


async def render(template_name: str, *, request=None, **context) -> str:
    """Render a Jinja2 template to an HTML string.

    Args:
        template_name: Path relative to the templates directory.
        request: Optional Sanic request. If provided, injects the
            authenticated member into the template context.
        **context: Template context variables.

    Returns:
        Rendered HTML string.
    """
    if request is not None and hasattr(request, "ctx"):
        member = getattr(request.ctx, "member", None)
        # current_user is a detached Member ORM instance from the auth middleware session.
        # Only column attributes (id, display_name, profile, etc.) are safe for template access.
        # Relationship attributes (ecosystem, onboarding) will raise MissingGreenlet.
        context["current_user"] = member          # always the logged-in user
        context.setdefault("member", member)      # backward compat for views that don't pass member
        ecosystems = getattr(request.ctx, "ecosystems", [])
        context.setdefault("ecosystems", ecosystems)
    template = _env.get_template(template_name)
    return await template.render_async(**context)


def html_fragment(fragment: str):
    """Return an HTML fragment response for htmx partial swaps.

    Args:
        fragment: Rendered HTML string.

    Returns:
        Sanic HTML response.
    """
    return html_response(fragment)


# Pagination defaults
DEFAULT_PAGE_SIZE = 25


def parse_pagination(request) -> tuple[int, int]:
    """Extract offset and limit from query parameters.

    Args:
        request: Sanic request object.

    Returns:
        Tuple of (offset, limit).
    """
    try:
        offset = max(0, int(request.args.get("offset", 0)))
    except (ValueError, TypeError):
        offset = 0
    try:
        limit = min(100, max(1, int(request.args.get("limit", DEFAULT_PAGE_SIZE))))
    except (ValueError, TypeError):
        limit = DEFAULT_PAGE_SIZE
    return offset, limit


def get_ecosystem_id(request) -> uuid.UUID | None:
    """Extract the active ecosystem UUID from the authenticated member.

    Returns the member's ecosystem_id, or None if unauthenticated.
    """
    member = getattr(getattr(request, "ctx", None), "member", None)
    if member is not None:
        return member.ecosystem_id
    return None


def get_selected_ecosystem_ids(request) -> list[uuid.UUID]:
    """Return the list of ecosystem UUIDs the user has selected.

    Reads from ``request.ctx.selected_ecosystem_ids`` (set by auth middleware
    from the ``neos_selected_ecosystems`` cookie).  Falls back to the
    member's own ecosystem if nothing is selected.
    """
    ids = getattr(getattr(request, "ctx", None), "selected_ecosystem_ids", None)
    if ids:
        return list(ids)
    # Fallback: member's own ecosystem
    eco_id = get_ecosystem_id(request)
    if eco_id is not None:
        return [eco_id]
    return []


async def get_scoped_entity(
    session: AsyncSession,
    model_class: type[T],
    entity_id: uuid.UUID,
    request,
    *,
    ecosystem_attr: str = "ecosystem_id",
) -> T | None:
    """Fetch an entity by primary key and verify ecosystem ownership.

    Returns the entity if it exists AND belongs to one of the user's
    selected ecosystems.  Returns ``None`` otherwise (prevents IDOR).

    Args:
        session: SQLAlchemy async session.
        model_class: The ORM model class.
        entity_id: Primary key UUID.
        request: Sanic request (used to resolve selected ecosystems).
        ecosystem_attr: Name of the ecosystem FK attribute on the model.

    Returns:
        The entity if found and authorised, else ``None``.
    """
    entity = await session.get(model_class, entity_id)
    if entity is None:
        return None
    eco_ids = get_selected_ecosystem_ids(request)
    if eco_ids and hasattr(entity, ecosystem_attr):
        if getattr(entity, ecosystem_attr) not in eco_ids:
            return None
    return entity


def validate_ecosystem_id(
    form_ecosystem_id: str | None, request
) -> uuid.UUID | None:
    """Validate that a form-submitted ecosystem_id is in the user's selection.

    Returns the validated UUID or ``None`` if invalid / not permitted.
    """
    if not form_ecosystem_id:
        return None
    try:
        eco_uuid = uuid.UUID(form_ecosystem_id)
    except (ValueError, TypeError):
        return None
    eco_ids = get_selected_ecosystem_ids(request)
    if eco_ids and eco_uuid not in eco_ids:
        return None
    return eco_uuid
