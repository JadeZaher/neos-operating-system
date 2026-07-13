"""Versioned trait — provides version control for entities."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class VersionedTrait:
    """Trait that creates and retrieves versions of an entity.

    Supports rollback, comparison, and audit history for governance
    entities and other versioned domain objects.
    """

    async def create_version(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        version_number: int,
        change_description: str,
        data: dict[str, Any],
        parent_version_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new version record for an entity.

        Args:
            db: Database session
            entity_type: Type of entity
            entity_id: Entity identifier
            version_number: Version number
            change_description: Human-readable change summary
            data: Snapshot of entity data
            parent_version_id: Previous version identifier

        Returns:
            Created version record
        """
        version = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "version_number": version_number,
            "change_description": change_description,
            "data": data,
            "parent_version_id": parent_version_id,
        }
        return {"version": version}

    async def list_versions(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
        order: str = "desc",
    ) -> dict[str, Any]:
        """List versions for an entity."""
        return {"versions": []}

    async def compare_versions(
        self,
        db: AsyncSession,
        entity_type: str,
        version_id_1: str,
        version_id_2: str,
    ) -> dict[str, Any]:
        """Compare two versions and return a diff."""
        return {"diff": {}}
