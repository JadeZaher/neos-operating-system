"""Private orientation conversations; see api/ORIENTATION_MATCHING.md."""
from __future__ import annotations

import uuid
from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from ._base import Base, GUID, TimestampMixin


class OrientationChatSession(TimestampMixin, Base):
    __tablename__ = "orientation_chat_sessions"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    journey_map_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("journey_maps.id"), nullable=False)
    step_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    messages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
