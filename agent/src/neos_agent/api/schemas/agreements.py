"""Pydantic v2 schemas for Agreement-related API responses and requests."""

import datetime as _dt
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from neos_agent.api.agreement_vocabulary import (
    PREREQUISITE_SCOPES,
    canonical_agreement_type,
)
from neos_agent.api.schemas.proposals import ActPolicySchema


class AgreementListItem(BaseModel):
    id: UUID
    agreement_id: str
    ecosystem_id: UUID
    type: str
    title: str
    version: str
    status: str
    proposer: str | None = None
    domain: str | None = None
    hierarchy_level: str
    review_date: _dt.date | None = None
    sunset_date: _dt.date | None = None
    created_at: _dt.datetime


class RatificationRecordSchema(BaseModel):
    id: UUID
    participant: str
    role: str | None = None
    position: str | None = None
    date: _dt.date | None = None


class AgreementCeremonySchema(BaseModel):
    id: UUID
    stage: str
    outcome: str
    evidence: str | None = None
    completed_at: _dt.datetime


class AgreementConsentSummary(BaseModel):
    required: int
    consented: int
    outstanding: int
    complete: bool


class AgreementMemberConsentSchema(BaseModel):
    id: UUID
    member_id: UUID
    agreement_version: str
    attested_at: _dt.datetime
    withdrawn_at: _dt.datetime | None = None
    alignment_awarded: int = 0


class AgreementDetail(AgreementListItem):
    shared_ecosystem_ids: list[UUID] | None = None
    text: str | None = None
    affected_parties: list | dict | None = None
    parent_agreement_id: UUID | None = None
    ratification_date: _dt.date | None = None
    created_date: _dt.date | None = None
    updated_at: _dt.datetime
    ratification_records: list[RatificationRecordSchema] = []
    ceremonies: list[AgreementCeremonySchema] = []
    requires_explicit_consent: bool = True
    prerequisite_scopes: list[str] = []
    prerequisite_domain_ids: list[UUID] = []
    alignment_points: int = 5
    consent_summary: AgreementConsentSummary | None = None
    current_member_consent: AgreementMemberConsentSchema | None = None
    act_policy: dict | None = None
    gates: dict | None = None
    caller_role: str | None = None
    caller_can_conduct: bool = False


class AgreementCreateRequest(BaseModel):
    ecosystem_id: UUID
    shared_ecosystem_ids: list[UUID] | None = None
    type: str
    title: str
    text: str | None = None
    proposer: str | None = None
    domain: str | None = None
    hierarchy_level: str = "domain"
    affected_parties: list | dict | None = None
    review_date: _dt.date | None = None
    sunset_date: _dt.date | None = None
    requires_explicit_consent: bool = True
    prerequisite_scopes: list[str] = Field(default_factory=list)
    prerequisite_domain_ids: list[UUID] = Field(default_factory=list)
    alignment_points: int = Field(default=5, ge=0, le=25)
    act_policy: ActPolicySchema | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        return canonical_agreement_type(value)

    @field_validator("requires_explicit_consent")
    @classmethod
    def require_explicit_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("All agreements require explicit member consent")
        return True

    @field_validator("prerequisite_scopes")
    @classmethod
    def validate_prerequisite_scopes(cls, values: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(value.strip().lower() for value in values))
        invalid = set(normalized) - PREREQUISITE_SCOPES
        if invalid:
            raise ValueError(f"Unsupported prerequisite scopes: {', '.join(sorted(invalid))}")
        return normalized


class AgreementUpdateRequest(BaseModel):
    type: str | None = None
    title: str | None = None
    text: str | None = None
    proposer: str | None = None
    domain: str | None = None
    hierarchy_level: str | None = None
    affected_parties: list | dict | None = None
    shared_ecosystem_ids: list[UUID] | None = None
    review_date: _dt.date | None = None
    sunset_date: _dt.date | None = None
    prerequisite_scopes: list[str] | None = None
    prerequisite_domain_ids: list[UUID] | None = None
    alignment_points: int | None = Field(default=None, ge=0, le=25)
    act_policy: ActPolicySchema | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        return canonical_agreement_type(value) if value is not None else None

    @field_validator("prerequisite_scopes")
    @classmethod
    def validate_prerequisite_scopes(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        normalized = list(dict.fromkeys(value.strip().lower() for value in values))
        invalid = set(normalized) - PREREQUISITE_SCOPES
        if invalid:
            raise ValueError(f"Unsupported prerequisite scopes: {', '.join(sorted(invalid))}")
        return normalized


class AgreementConsentRequest(BaseModel):
    attestation: str = Field(min_length=8, max_length=500)


class AgreementConsentWithdrawalRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


class AgreementCeremonyEvidenceRequest(BaseModel):
    """Record an advice round or test-case evidence against an agreement."""
    stage: str
    note: str = Field(min_length=3, max_length=2000)

    @field_validator("stage")
    @classmethod
    def validate_stage(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"advice", "test"}:
            raise ValueError("Ceremony evidence is recorded at the advice or test stage")
        return normalized


class AmendmentRecordSchema(BaseModel):
    id: UUID
    amendment_id: str
    amendment_type: str
    proposed_by: str | None = None
    date: _dt.date | None = None
    changes: dict | None = None
    rationale: str | None = None
    status: str
    new_agreement_version: str | None = None
    created_at: _dt.datetime


class ReviewRecordSchema(BaseModel):
    id: UUID
    review_id: str
    review_type: str
    trigger: str | None = None
    date: _dt.date | None = None
    outcome: str | None = None
    next_review_date: _dt.date | None = None
    created_at: _dt.datetime


class AgreementVersionSchema(BaseModel):
    id: UUID
    agreement_id: UUID
    version: str
    status: str
    title: str
    text: str | None = None
    type: str
    proposer: str | None = None
    domain: str | None = None
    hierarchy_level: str = "domain"
    affected_parties: list | dict | None = None
    review_date: _dt.date | None = None
    sunset_date: _dt.date | None = None
    ratification_date: _dt.date | None = None
    version_fingerprint: str | None = None
    change_reason: str | None = None
    changed_by: str | None = None
    created_at: _dt.datetime | None = None


class AgreementHistoryResponse(BaseModel):
    amendments: list[AmendmentRecordSchema]
    reviews: list[ReviewRecordSchema]
    versions: list[AgreementVersionSchema] = []
