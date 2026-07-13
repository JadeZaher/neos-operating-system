"""Indexable trait — provides semantic search indexing for entities."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class IndexableTrait:
    """Trait that indexes entity content for semantic search and similarity.

    Enables precedent systems, memory, and decision record search.
    """

    async def index(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        content: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Index an entity for semantic search.

        Args:
            db: Database session
            entity_type: Type of entity
            entity_id: Entity identifier
            content: Content to index
            tags: Optional tags for filtering
            metadata: Optional metadata

        Returns:
            Indexing result
        """
        return {
            "indexed": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "tags": tags or [],
            "metadata": metadata or {},
        }

    async def search(
        self,
        db: AsyncSession,
        query: str,
        entity_types: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Perform semantic search."""
        return {"results": []}

    async def similar(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        limit: int = 10,
        threshold: float = 0.8,
    ) -> dict[str, Any]:
        """Find similar entities."""
        return {"results": []}
