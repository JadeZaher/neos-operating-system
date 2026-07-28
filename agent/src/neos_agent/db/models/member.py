"""NEOS model: Member."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import JSON, TypeDecorator, CHAR
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)

from ._base import Base, GUID, TimestampMixin


class Member(TimestampMixin, Base):
    __tablename__ = "members"
    __table_args__ = (
        Index("ix_members_ecosystem_id", "ecosystem_id"),
        UniqueConstraint("ecosystem_id", "user_id", name="uq_member_ecosystem_user"),
        CheckConstraint(
            "role IN ('user', 'mod', 'admin', 'owner')",
            name="ck_members_role_tier",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)
    shared_ecosystem_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # additional ecosystems for cross-ecosystem work
    member_id: Mapped[str] = mapped_column(String(100), nullable=False)  # business key
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_status: Mapped[str] = mapped_column(String(50), nullable=False, default="prospective")
    role: Mapped[str] = mapped_column(Text, nullable=False, default="user", server_default="user")  # per-ecosystem tier: user, mod, admin, owner
    profile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # co_creator, builder, collaborator, townhall
    skills_offered: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skills_needed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    interests: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    onboarding_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    kyc_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_governance_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    privacy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    agreement_alignment_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    ecosystem: Mapped[Ecosystem] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="members")
    onboarding: Mapped[Optional[MemberOnboarding]] = relationship(back_populates="member", foreign_keys="MemberOnboarding.member_id")
    status_transitions: Mapped[list[MemberStatusTransition]] = relationship(back_populates="member")
