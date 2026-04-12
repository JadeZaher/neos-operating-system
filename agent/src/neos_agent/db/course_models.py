"""SQLAlchemy 2.0 async ORM models for courses, quizzes, results, and user profiles.

Tables:
- courses: Learning courses scoped to an ecosystem/domain
- quizzes: Surveys/quizzes attached to courses or standalone
- quiz_results: Completed quiz submissions
- quiz_progress: In-progress quiz state
- user_tags: Key/value tags derived from quiz results
- user_badges: Earned badges derived from tags
- profile_tiles: Member profile display tiles
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from neos_agent.db.models import Base, GUID, TimestampMixin


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        Index("ix_courses_ecosystem_id", "ecosystem_id"),
        Index("ix_courses_domain_id", "domain_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("ecosystems.id"), nullable=False
    )
    domain_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("domains.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=True
    )
    is_onboarding_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    quizzes: Mapped[list[Quiz]] = relationship(back_populates="course")


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------


class Quiz(TimestampMixin, Base):
    __tablename__ = "quizzes"
    __table_args__ = (
        Index("ix_quizzes_course_id", "course_id"),
        Index("ix_quizzes_created_by", "created_by"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    survey_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    time_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passing_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    allow_retakes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    visibility: Mapped[str] = mapped_column(String(50), nullable=False, default="public")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=True
    )

    # Relationships
    course: Mapped[Optional[Course]] = relationship(back_populates="quizzes")
    results: Mapped[list[QuizResult]] = relationship(back_populates="quiz")


# ---------------------------------------------------------------------------
# QuizResult
# ---------------------------------------------------------------------------


class QuizResult(Base):
    __tablename__ = "quiz_results"
    __table_args__ = (
        Index("ix_quiz_results_quiz_id", "quiz_id"),
        Index("ix_quiz_results_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quizzes.id"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=False
    )
    survey_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )

    # Relationships
    quiz: Mapped[Quiz] = relationship(back_populates="results")


# ---------------------------------------------------------------------------
# QuizProgress
# ---------------------------------------------------------------------------


class QuizProgress(Base):
    __tablename__ = "quiz_progress"
    __table_args__ = (
        Index("ix_quiz_progress_quiz_id", "quiz_id"),
        Index("ix_quiz_progress_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("quizzes.id"), nullable=False
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=False
    )
    current_question_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )


# ---------------------------------------------------------------------------
# UserTag
# ---------------------------------------------------------------------------


class UserTag(Base):
    __tablename__ = "user_tags"
    __table_args__ = (
        Index("ix_user_tags_member_id", "member_id"),
        Index("ix_user_tags_quiz_result_id", "quiz_result_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=False
    )
    quiz_result_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("quiz_results.id"), nullable=True
    )
    tag_key: Mapped[str] = mapped_column(String(255), nullable=False)
    tag_value: Mapped[str] = mapped_column(String(500), nullable=False)
    tag_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    data_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    numeric_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


# ---------------------------------------------------------------------------
# UserBadge
# ---------------------------------------------------------------------------


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        Index("ix_user_badges_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=False
    )
    badge_key: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_name: Mapped[str] = mapped_column(String(255), nullable=False)
    badge_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    badge_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    badge_icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    strength: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_tag_keys: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    earned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )


# ---------------------------------------------------------------------------
# ProfileTile
# ---------------------------------------------------------------------------


class ProfileTile(Base):
    __tablename__ = "profile_tiles"
    __table_args__ = (
        Index("ix_profile_tiles_member_id", "member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("members.id"), nullable=False
    )
    submission_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    layout_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
