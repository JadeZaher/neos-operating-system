"""NEOS model: AgentToken.

Bearer tokens that let a logged-in user's own agents connect over MCP.
A token is bound to the auth session it was minted from: logout (session
expiry) or explicit revocation kills the agent's access. Authority is
always session-scoped — every request re-resolves the user's live
memberships and roles.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class AgentToken(TimestampMixin, Base):
    __tablename__ = "agent_tokens"
    __table_args__ = (
        Index("ix_agent_tokens_user_id", "user_id"),
        Index("ix_agent_tokens_auth_session_id", "auth_session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    # The auth session this token was minted from — when it dies, the token dies.
    auth_session_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("auth_sessions.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    # sha256 hex of the bearer token; the plaintext is shown once at mint.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
