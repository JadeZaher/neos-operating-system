"""NEOS model: QuizAssignment (quiz assigned to an individual member).

Distinct from the quiz↔domain / quiz↔ecosystem assignment on the Quiz model
itself; this targets a specific member. See db/models/AGENTS.md.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ._base import Base, GUID, TimestampMixin


class QuizAssignment(TimestampMixin, Base):
    __tablename__ = "quiz_assignments"
    __table_args__ = (
        UniqueConstraint("quiz_id", "member_id", name="uq_quiz_assignment"),
        Index("ix_quiz_assignments_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("quizzes.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    ecosystem_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("ecosystems.id"), nullable=True
    )
    assigned_by: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="assigned")
