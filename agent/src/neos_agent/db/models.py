"""SQLAlchemy 2.0 async ORM models for the NEOS governance database.

33 tables organized by section:
- Core (7): ecosystems, members, member_onboarding, member_status_transitions,
  domains, domain_elements, domain_metrics
- Agreements (4): agreements, agreement_ratification_records, amendment_records,
  review_records
- ACT Process (10): proposals, advice_logs, advice_entries, advice_non_respondents,
  consent_records, consent_participants, consent_integration_rounds,
  consent_objections_addressed, test_reports, test_success_criteria
- Memory (4): decision_records, decision_dissent_records, decision_participants,
  decision_semantic_tags
- Sessions (1): agent_sessions
- Conflict & Repair (3): conflict_cases, repair_agreement_records,
  governance_health_audits
- Emergency (1): emergency_states
- Exit & Portability (1): exit_records
- Auth (2): auth_sessions, auth_challenges
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
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


# --- Custom UUID type that works with both PostgreSQL and SQLite ---

class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise stores as CHAR(32).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value.hex
            else:
                return uuid.UUID(value).hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value


# --- Base ---

class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin adding created_at and updated_at timestamp columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


# ========================
# CORE (7 models)
# ========================

class Ecosystem(TimestampMixin, Base):
    __tablename__ = "ecosystems"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uaf_agreement_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    # Directory fields
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    founded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    governance_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")

    # Relationships
    members: Mapped[list[Member]] = relationship(back_populates="ecosystem")
    domains: Mapped[list[Domain]] = relationship(back_populates="ecosystem")
    agreements: Mapped[list[Agreement]] = relationship(back_populates="ecosystem")


class Member(TimestampMixin, Base):
    __tablename__ = "members"
    __table_args__ = (Index("ix_members_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    member_id: Mapped[str] = mapped_column(String(100), nullable=False)  # business key
    did: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_status: Mapped[str] = mapped_column(String(50), nullable=False, default="prospective")
    profile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # co_creator, builder, townhall
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    profile_picture: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    skills_offered: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    skills_needed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    interests: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    onboarding_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    kyc_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_governance_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ecosystem: Mapped[Ecosystem] = relationship(back_populates="members")
    onboarding: Mapped[Optional[MemberOnboarding]] = relationship(back_populates="member", foreign_keys="MemberOnboarding.member_id")
    status_transitions: Mapped[list[MemberStatusTransition]] = relationship(back_populates="member")


class MemberOnboarding(TimestampMixin, Base):
    __tablename__ = "member_onboarding"
    __table_args__ = (Index("ix_member_onboarding_member_id", "member_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    facilitator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mentor_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    uaf_version_consented: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    consent_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cooling_off_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cooling_off_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    section_consents: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    checklist_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    completion_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    member: Mapped[Member] = relationship(back_populates="onboarding", foreign_keys=[member_id])


class MemberStatusTransition(TimestampMixin, Base):
    __tablename__ = "member_status_transitions"
    __table_args__ = (Index("ix_member_status_transitions_member_id", "member_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    from_status: Mapped[str] = mapped_column(String(50), nullable=False)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    trigger: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    member: Mapped[Member] = relationship(back_populates="status_transitions")


class Domain(TimestampMixin, Base):
    __tablename__ = "domains"
    __table_args__ = (Index("ix_domains_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    domain_id: Mapped[str] = mapped_column(String(100), nullable=False)  # business key
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_steward: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    steward_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    parent_domain_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metric_definitions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    elements: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSONB for complex elements

    ecosystem: Mapped[Ecosystem] = relationship(back_populates="domains")
    domain_elements: Mapped[list[DomainElement]] = relationship(back_populates="domain")
    domain_metrics: Mapped[list[DomainMetric]] = relationship(back_populates="domain")


class DomainElement(TimestampMixin, Base):
    __tablename__ = "domain_elements"
    __table_args__ = (Index("ix_domain_elements_domain_id", "domain_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    element_name: Mapped[str] = mapped_column(String(100), nullable=False)
    element_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    domain: Mapped[Domain] = relationship(back_populates="domain_elements")


class DomainMetric(TimestampMixin, Base):
    __tablename__ = "domain_metrics"
    __table_args__ = (Index("ix_domain_metrics_domain_id", "domain_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("domains.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(255), nullable=False)
    target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    measurement_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    domain: Mapped[Domain] = relationship(back_populates="domain_metrics")


# ========================
# AGREEMENTS (4 models)
# ========================

class Agreement(TimestampMixin, Base):
    __tablename__ = "agreements"
    __table_args__ = (Index("ix_agreements_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    agreement_id: Mapped[str] = mapped_column(String(100), nullable=False)  # business key
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    proposer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    affected_parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hierarchy_level: Mapped[str] = mapped_column(String(50), nullable=False, default="domain")
    parent_agreement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("agreements.id"), nullable=True
    )
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sunset_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ratification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    ecosystem: Mapped[Ecosystem] = relationship(back_populates="agreements")
    parent_agreement: Mapped[Optional[Agreement]] = relationship(remote_side="Agreement.id")
    ratification_records: Mapped[list[AgreementRatificationRecord]] = relationship(back_populates="agreement")
    amendment_records: Mapped[list[AmendmentRecord]] = relationship(
        back_populates="agreement", foreign_keys="AmendmentRecord.parent_agreement_id"
    )
    review_records: Mapped[list[ReviewRecord]] = relationship(back_populates="agreement")


class AgreementRatificationRecord(TimestampMixin, Base):
    __tablename__ = "agreement_ratification_records"
    __table_args__ = (Index("ix_agreement_ratification_records_agreement_id", "agreement_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    participant: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    agreement: Mapped[Agreement] = relationship(back_populates="ratification_records")


class AmendmentRecord(TimestampMixin, Base):
    __tablename__ = "amendment_records"
    __table_args__ = (Index("ix_amendment_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    amendment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    parent_agreement_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    amendment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    proposed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    changes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    act_level_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    consent_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    new_agreement_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="proposed")

    agreement: Mapped[Agreement] = relationship(back_populates="amendment_records", foreign_keys=[parent_agreement_id])


class ReviewRecord(TimestampMixin, Base):
    __tablename__ = "review_records"
    __table_args__ = (Index("ix_review_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    review_id: Mapped[str] = mapped_column(String(100), nullable=False)
    agreement_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agreements.id"), nullable=False)
    agreement_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_body: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    evaluation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    next_review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    follow_up_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    agreement: Mapped[Agreement] = relationship(back_populates="review_records")


# ========================
# ACT PROCESS (10 models)
# ========================

class Proposal(TimestampMixin, Base):
    __tablename__ = "proposals"
    __table_args__ = (Index("ix_proposals_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    proposal_id: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    decision_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    proposer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    co_sponsors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    affected_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    impacted_parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    proposed_change: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advice_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    consent_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    test_duration: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_proposals: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    synergy_check: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    advice_logs: Mapped[list[AdviceLog]] = relationship(back_populates="proposal")
    consent_records: Mapped[list[ConsentRecord]] = relationship(back_populates="proposal")
    test_reports: Mapped[list[TestReport]] = relationship(back_populates="proposal")


class AdviceLog(TimestampMixin, Base):
    __tablename__ = "advice_logs"
    __table_args__ = (Index("ix_advice_logs_proposal_id", "proposal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("proposals.id"), nullable=False)
    advice_window_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advice_window_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposer_modifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    proposal: Mapped[Proposal] = relationship(back_populates="advice_logs")
    entries: Mapped[list[AdviceEntry]] = relationship(back_populates="advice_log")
    non_respondents: Mapped[list[AdviceNonRespondent]] = relationship(back_populates="advice_log")


class AdviceEntry(TimestampMixin, Base):
    __tablename__ = "advice_entries"
    __table_args__ = (Index("ix_advice_entries_advice_log_id", "advice_log_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    advice_log_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("advice_logs.id"), nullable=False)
    advisor: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    azpo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advice_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    proposer_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    integration_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    advice_log: Mapped[AdviceLog] = relationship(back_populates="entries")


class AdviceNonRespondent(TimestampMixin, Base):
    __tablename__ = "advice_non_respondents"
    __table_args__ = (Index("ix_advice_non_respondents_advice_log_id", "advice_log_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    advice_log_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("advice_logs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    notified_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    follow_up_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    advice_log: Mapped[AdviceLog] = relationship(back_populates="non_respondents")


class ConsentRecord(TimestampMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (Index("ix_consent_records_proposal_id", "proposal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("proposals.id"), nullable=False)
    consent_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    weighting_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    facilitator: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    quorum_required: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quorum_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    escalation_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    final_proposal_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    proposal: Mapped[Proposal] = relationship(back_populates="consent_records")
    participants: Mapped[list[ConsentParticipant]] = relationship(back_populates="consent_record")
    integration_rounds: Mapped[list[ConsentIntegrationRound]] = relationship(back_populates="consent_record")


class ConsentParticipant(TimestampMixin, Base):
    __tablename__ = "consent_participants"
    __table_args__ = (Index("ix_consent_participants_consent_record_id", "consent_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    consent_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("consent_records.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    azpo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    round: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    consent_record: Mapped[ConsentRecord] = relationship(back_populates="participants")


class ConsentIntegrationRound(TimestampMixin, Base):
    __tablename__ = "consent_integration_rounds"
    __table_args__ = (Index("ix_consent_integration_rounds_consent_record_id", "consent_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    consent_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("consent_records.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    modifications_made: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    consent_record: Mapped[ConsentRecord] = relationship(back_populates="integration_rounds")
    objections_addressed: Mapped[list[ConsentObjectionAddressed]] = relationship(back_populates="integration_round")


class ConsentObjectionAddressed(TimestampMixin, Base):
    __tablename__ = "consent_objections_addressed"
    __table_args__ = (Index("ix_consent_objections_addressed_integration_round_id", "integration_round_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    integration_round_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("consent_integration_rounds.id"), nullable=False)
    objector: Mapped[str] = mapped_column(String(255), nullable=False)
    objection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    integration_round: Mapped[ConsentIntegrationRound] = relationship(back_populates="objections_addressed")


class TestReport(TimestampMixin, Base):
    __tablename__ = "test_reports"
    __table_args__ = (Index("ix_test_reports_proposal_id", "proposal_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    proposal_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("proposals.id"), nullable=False)
    test_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    test_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    midpoint_checkin_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    revert_procedure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    midpoint_findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extension_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    modifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    agreement_registry_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    success_criteria_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    proposal: Mapped[Proposal] = relationship(back_populates="test_reports")
    success_criteria: Mapped[list[TestSuccessCriterion]] = relationship(back_populates="test_report")


class TestSuccessCriterion(TimestampMixin, Base):
    __tablename__ = "test_success_criteria"
    __table_args__ = (Index("ix_test_success_criteria_test_report_id", "test_report_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    test_report_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("test_reports.id"), nullable=False)
    criterion: Mapped[str] = mapped_column(String(500), nullable=False)
    met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    test_report: Mapped[TestReport] = relationship(back_populates="success_criteria")


# ========================
# MEMORY (4 models)
# ========================

class DecisionRecord(TimestampMixin, Base):
    __tablename__ = "decision_records"
    __table_args__ = (Index("ix_decision_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    record_id: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    holding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ratio_decidendi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    obiter_dicta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deliberation_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_skill: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_layer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    artifact_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    artifact_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    precedent_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    overruled_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    superseded_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    related_records: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    review_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    recorder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recorder_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verification_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    dissent_records: Mapped[list[DecisionDissentRecord]] = relationship(back_populates="decision_record")
    participants: Mapped[list[DecisionParticipant]] = relationship(back_populates="decision_record")
    semantic_tags: Mapped[list[DecisionSemanticTag]] = relationship(back_populates="decision_record")


class DecisionDissentRecord(TimestampMixin, Base):
    __tablename__ = "decision_dissent_records"
    __table_args__ = (Index("ix_decision_dissent_records_decision_record_id", "decision_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("decision_records.id"), nullable=False)
    objector: Mapped[str] = mapped_column(String(255), nullable=False)
    objection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    decision_record: Mapped[DecisionRecord] = relationship(back_populates="dissent_records")


class DecisionParticipant(TimestampMixin, Base):
    __tablename__ = "decision_participants"
    __table_args__ = (Index("ix_decision_participants_decision_record_id", "decision_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("decision_records.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    decision_record: Mapped[DecisionRecord] = relationship(back_populates="participants")


class DecisionSemanticTag(TimestampMixin, Base):
    __tablename__ = "decision_semantic_tags"
    __table_args__ = (Index("ix_decision_semantic_tags_decision_record_id", "decision_record_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_record_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("decision_records.id"), nullable=False)
    topic: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    affected_parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ecosystem_scope: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    urgency_at_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    related_precedents: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    decision_record: Mapped[DecisionRecord] = relationship(back_populates="semantic_tags")


# ========================
# CONFLICT & REPAIR (3 models)
# ========================

class ConflictCase(TimestampMixin, Base):
    """A reported conflict or harm requiring governance process."""
    __tablename__ = "conflict_cases"
    __table_args__ = (Index("ix_conflict_cases_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reporter_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="reported")
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    scope: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tier: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    root_cause_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    urgency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    safety_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    parties: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    facilitator_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    triage_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    repair_agreements: Mapped[list["RepairAgreementRecord"]] = relationship(back_populates="conflict_case")


class RepairAgreementRecord(TimestampMixin, Base):
    """Binding repair commitment arising from conflict resolution."""
    __tablename__ = "repair_agreement_records"
    __table_args__ = (Index("ix_repair_agreements_conflict_case_id", "conflict_case_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    conflict_case_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("conflict_cases.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    commitments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    responsible_party: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    checkin_30_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    checkin_30_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checkin_60_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    checkin_60_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checkin_90_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    checkin_90_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    conflict_case: Mapped["ConflictCase"] = relationship(back_populates="repair_agreements")


class GovernanceHealthAudit(TimestampMixin, Base):
    """Periodic governance health assessment (Layer VII)."""
    __tablename__ = "governance_health_audits"
    __table_args__ = (Index("ix_governance_health_audits_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    audit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    audit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    auditor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    capture_risk_indicators: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    overall_health_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    next_audit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


# ========================
# EMERGENCY (1 model)
# ========================

class EmergencyState(TimestampMixin, Base):
    """Circuit breaker state tracking for an ecosystem (Layer VIII)."""
    __tablename__ = "emergency_states"
    __table_args__ = (Index("ix_emergency_states_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="closed")
    declared_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    declared_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    criteria_met: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    auto_revert_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    recovery_entered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    pre_authorized_roles: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    actions_log: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    post_review_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ========================
# EXIT & PORTABILITY (1 model)
# ========================

class ExitRecord(TimestampMixin, Base):
    """Voluntary departure tracking (Layer X)."""
    __tablename__ = "exit_records"
    __table_args__ = (Index("ix_exit_records_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    exit_type: Mapped[str] = mapped_column(String(50), nullable=False, default="standard")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="declared")
    declared_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    coordinator_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    commitment_inventory: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    unwinding_status: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    data_export_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_export_completed: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    departure_notice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    re_entry_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    completed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ========================
# SESSIONS (1 model)
# ========================

class AgentSession(TimestampMixin, Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (Index("ix_agent_sessions_ecosystem_id", "ecosystem_id"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    ecosystem_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("ecosystems.id"), nullable=False)
    member_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("members.id"), nullable=True)
    skill_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


# ========================
# AUTH (2 models)
# ========================

class AuthSession(TimestampMixin, Base):
    """Server-side authentication sessions tied to a DID identity."""
    __tablename__ = "auth_sessions"
    __table_args__ = (
        Index("ix_auth_sessions_member_id", "member_id"),
        Index("ix_auth_sessions_expires_at", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("members.id"), nullable=False)
    did: Mapped[str] = mapped_column(String(500), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class AuthChallenge(TimestampMixin, Base):
    """Short-lived challenges for DID authentication."""
    __tablename__ = "auth_challenges"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    did: Mapped[str] = mapped_column(String(500), nullable=False)
    challenge: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
