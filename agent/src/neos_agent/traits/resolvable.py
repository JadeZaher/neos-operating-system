"""Resolvable trait — provides entity resolution by identifier."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ResolvableTrait:
    """Trait that resolves entities by business key, UUID, or name.

    Works with any SQLAlchemy model that exposes a resolvable identifier.
    """

    def __init__(self, model_class: type | None = None) -> None:
        self.model_class = model_class

    async def resolve(
        self,
        db: AsyncSession,
        identifier: str,
        by_field: str | None = None,
        scope: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve an entity by identifier within a scope.

        Args:
            db: Database session
            identifier: Business key, UUID, or display name
            by_field: Specific field to match on
            scope: Scope dict (e.g., ecosystem_ids, tenant_id)

        Returns:
            Resolved entity context
        """
        if self.model_class is None:
            return {"resolved": None}

        # Domain-specific implementations should build the proper query
        # using the model and scope.
        return {"resolved": None, "model": self.model_class.__name__}

    async def resolve_by_field(
        self,
        db: AsyncSession,
        field: str,
        value: Any,
        scope: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve an entity by a specific field value."""
        return {"resolved": None, "field": field, "value": value}
