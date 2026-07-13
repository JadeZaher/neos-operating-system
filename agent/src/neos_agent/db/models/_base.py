"""SQLAlchemy 2.0 async ORM models for the NEOS governance database.

46 tables organized by section:
- Core (8): ecosystems, users, members, member_onboarding, member_status_transitions,
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
- Auth (2): auth_sessions (references users), auth_challenges
- Messaging (4): conversations, conversation_participants, messages,
  conversation_links
- Collaboration (4): circle_memberships, shares_needs, collaborations,
  compliance_summaries
- Push Notifications (1): push_subscriptions
- Orientation & Journey Map (3): journey_maps, ethos_user_access, user_journey_progress
"""

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
# CORE (8 models)
# ========================
