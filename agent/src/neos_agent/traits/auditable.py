"""Auditable trait — provides audit logging for entities."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class AuditableTrait:
    """Trait that logs all state changes to an audit trail.

    Can be applied to models or pipeline handlers to ensure
    every operation is recorded.
    """

    async def log_audit(
        self,
        db: AsyncSession,
        action: str,
        entity_type: str,
        entity_id: str | None,
        actor: str | None = None,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log an audit event.

        Args:
            db: Database session
            action: Action name (e.g., create, update, transition)
            entity_type: Type of entity being audited
            entity_id: Entity identifier
            actor: Actor performing the action
            changes: Changed fields with before/after values
            metadata: Additional metadata

        Returns:
            Audit log record representation
        """
        # Domain-specific implementations should override this
        # to write to the actual AuditLog table.
        record = {
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": actor,
            "changes": changes or {},
            "metadata": metadata or {},
        }
        return {"audit_record": record}

    async def get_audit_trail(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: str | None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get audit trail for an entity.

        Args:
            db: Database session
            entity_type: Type of entity
            entity_id: Entity identifier
            limit: Maximum records
            offset: Pagination offset

        Returns:
            Audit trail records
        """
        return {"audit_trail": []}
