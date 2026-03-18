"""Shared rendering utilities for dashboard views.

Provides Jinja2 template rendering, htmx HTML fragment responses,
and ecosystem-scoping helpers.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@dataclass
class EcosystemScope:
    """Typed ecosystem selection context attached to every request.

    Provides a single source of truth for which ecosystems the current
    user has selected, replacing loose request.ctx attributes.
    """
    selected: list = field(default_factory=list)      # ORM Ecosystem objects
    selected_ids: list = field(default_factory=list)   # list[uuid.UUID]
    active: object = None                              # First ecosystem if single-select
    active_id: uuid.UUID | None = None                 # Convenience: active.id

    @property
    def is_multi(self) -> bool:
        """True when more than one ecosystem is selected."""
        return len(self.selected) > 1

    def require_ids(self) -> list:
        """Return selected_ids or raise if empty (fail-safe)."""
        if not self.selected_ids:
            raise ValueError("No ecosystem scope active")
        return self.selected_ids

    @classmethod
    def empty(cls) -> "EcosystemScope":
        """Create an empty scope (no ecosystems selected)."""
        return cls()

    @classmethod
    def from_ecosystems(cls, ecosystems: list, eco_ids: list) -> "EcosystemScope":
        """Build scope from loaded ecosystem objects and their IDs."""
        active = ecosystems[0] if len(ecosystems) == 1 else None
        active_id = eco_ids[0] if len(eco_ids) == 1 else None
        return cls(
            selected=ecosystems,
            selected_ids=eco_ids,
            active=active,
            active_id=active_id,
        )


import mistune
import nh3
import jinja2
from markupsafe import Markup
from sanic import html as html_response

# Template directory is a sibling of the views package
TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=True,
    enable_async=True,
)


# ---------------------------------------------------------------------------
# Markdown rendering (mistune → nh3 sanitisation)
# ---------------------------------------------------------------------------

_MARKDOWN_ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
    "strong", "em", "del", "code", "pre",
    "ul", "ol", "li", "blockquote",
    "a", "img", "table", "thead", "tbody", "tr", "th", "td",
    "sup", "sub", "input",
}

_MARKDOWN_ALLOWED_ATTRS = {
    "a": {"href", "title"},  # rel is set via link_rel parameter
    "img": {"src", "alt", "title"},
    "code": {"class"},
    "pre": {"class"},
    "th": {"align"},
    "td": {"align"},
    "input": {"type", "checked", "disabled"},
}

_md = mistune.create_markdown(
    plugins=["strikethrough", "table", "task_lists", "footnotes"],
)


def render_markdown(text: str | dict | None) -> Markup:
    """Convert markdown text to sanitised HTML safe for Jinja2 autoescape."""
    if not text:
        return Markup("")
    if not isinstance(text, str):
        import json
        text = json.dumps(text, indent=2, default=str)
    raw_html = _md(text)
    clean = nh3.clean(
        raw_html,
        tags=_MARKDOWN_ALLOWED_TAGS,
        attributes=_MARKDOWN_ALLOWED_ATTRS,
        link_rel="noopener noreferrer nofollow",
    )
    return Markup(clean)


_env.filters["markdown"] = render_markdown


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
        scope = getattr(request.ctx, "ecosystem_scope", None)
        if scope is None:
            ecosystems = getattr(request.ctx, "ecosystems", [])
            eco_ids = getattr(request.ctx, "selected_ecosystem_ids", [])
            scope = EcosystemScope.from_ecosystems(ecosystems, eco_ids) if ecosystems else EcosystemScope.empty()
        context["ecosystem_scope"] = scope
        context["selected_ecosystems"] = scope.selected  # never overridable
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


def escape_like(value: str) -> str:
    """Escape SQL LIKE/ILIKE wildcard characters (%, _, \\)."""
    return re.sub(r"([%_\\])", r"\\\1", value)


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

    Reads from ``request.ctx.ecosystem_scope`` first, then falls back to
    ``request.ctx.selected_ecosystem_ids`` (set by auth middleware from the
    ``neos_selected_ecosystems`` cookie). Falls back to the member's own
    ecosystem if nothing is selected.
    """
    scope = getattr(getattr(request, "ctx", None), "ecosystem_scope", None)
    if scope is not None and scope.selected_ids:
        return list(scope.selected_ids)
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
    Also denies access when no ecosystems are selected (fail-safe).

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
    if hasattr(entity, ecosystem_attr):
        # Fail-safe: deny access when no ecosystems are selected
        if not eco_ids:
            return None
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
    if not eco_ids or eco_uuid not in eco_ids:
        return None
    return eco_uuid
