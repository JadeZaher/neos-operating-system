"""Purpose-limited discovery consent and versioned fit evidence; see api/ORIENTATION_MATCHING.md."""
from __future__ import annotations

import uuid
from sqlalchemy import Boolean, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ._base import Base, GUID, TimestampMixin


class MatchingConsent(TimestampMixin, Base):
    __tablename__ = "matching_consents"
    __table_args__ = (UniqueConstraint("user_id", "ecosystem_id", name="uq_matching_consent_owner_ecosystem"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    directory_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contact_discovery: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    matching_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class EcosystemMatchingProfile(TimestampMixin, Base):
    __tablename__ = "ecosystem_matching_profiles"
    __table_args__ = (UniqueConstraint("ecosystem_id", "version", name="uq_matching_profile_ecosystem_version"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    governing_agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_versions: Mapped[list] = mapped_column(JSON, nullable=False)
    published_by_user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False)


class MatchingAnswers(TimestampMixin, Base):
    __tablename__ = "matching_answers"
    __table_args__ = (UniqueConstraint("user_id", "ecosystem_id", name="uq_matching_answers_owner_ecosystem"),)
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(80), nullable=False)
    answers: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    paused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class MatchingAssessment(TimestampMixin, Base):
    __tablename__ = "matching_assessments"
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    profile_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystem_matching_profiles.id"), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    corrections: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
