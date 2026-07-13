"""Session-aware trait — tracks agent session state and workflow continuity."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class SessionAwareTrait:
    """Trait that tracks agent session state and workflow context.

    Ensures workflow continuity across skill boundaries and interactions.
    """

    async def create_session(
        self,
        db: AsyncSession,
        session_type: str,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create an agent session.

        Args:
            db: Database session
            session_type: Type of session
            context: Initial session context
            metadata: Session metadata

        Returns:
            Created session information
        """
        return {
            "session_id": None,
            "session_type": session_type,
            "context": context or {},
            "metadata": metadata or {},
            "state": "created",
        }

    async def update_session(
        self,
        db: AsyncSession,
        session_id: str,
        state: str | None = None,
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an agent session."""
        return {
            "session_id": session_id,
            "state": state,
            "context": context,
            "metadata": metadata,
            "updated": True,
        }

    async def get_session(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> dict[str, Any]:
        """Get an agent session."""
        return {"session_id": session_id, "session": None}
