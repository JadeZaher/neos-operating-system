"""Ecosystem scope dataclass for request-level ecosystem selection context.

Relocated from views/_rendering.py for use in API-only mode.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy import false

from neos_agent.api.helpers import apply_ecosystem_filter


# Fail-closed filter (default deny): see api/AGENTS.md "Handler contracts".
def restrict_to_ecosystems(stmt, model, ecosystem_ids, *, include_shared: bool = True):
    """Rows owned by (or, with `include_shared`, shared with) `ecosystem_ids`; an empty list matches no rows."""
    if not ecosystem_ids:
        return stmt.where(false())
    return apply_ecosystem_filter(stmt, model, list(ecosystem_ids), include_shared=include_shared)


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

    def filter(self, stmt, model):
        """Restrict `stmt` to the selected ecosystems; an empty selection matches no rows."""
        return restrict_to_ecosystems(stmt, model, self.selected_ids)

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
