"""Pydantic v2 response schemas for the NEOS agent API."""

import datetime as _dt
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    skills_loaded: int
    skills_available: bool
    database: str
    version: str


class SkillItem(BaseModel):
    name: str
    description: str
    layer: int
    version: str
    depends_on: list[str]


class SkillsResponse(BaseModel):
    count: int
    skills: list[SkillItem]


class ApiError(BaseModel):
    error: str


# --- Auth schemas ---


class MemberSummary(BaseModel):
    id: UUID
    display_name: str
    did: str
    profile: str | None = None
    ecosystem_id: UUID
    current_status: str


class AuthChallengeResponse(BaseModel):
    challenge: str


class AuthVerifyResponse(BaseModel):
    success: bool
    display_name: str
    member: MemberSummary


# --- Ecosystem schemas ---


class EcosystemSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    status: str
    logo_url: str | None = None
    location: str | None = None
    member_count: int = 0


class AuthMeResponse(BaseModel):
    member: MemberSummary
    ecosystems: list[EcosystemSummary]


class EcosystemDetail(EcosystemSummary):
    website: str | None = None
    founded_date: _dt.date | None = None
    tags: list[str] | None = None
    contact_email: str | None = None
    governance_summary: str | None = None
    visibility: str = "public"


class EcosystemCreateRequest(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    website: str | None = None
    logo_url: str | None = None
    founded_date: _dt.date | None = None
    tags: list[str] | None = None
    contact_email: str | None = None
    governance_summary: str | None = None
    visibility: str = "public"


class EcosystemUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    website: str | None = None
    logo_url: str | None = None
    founded_date: _dt.date | None = None
    tags: list[str] | None = None
    contact_email: str | None = None
    governance_summary: str | None = None
    visibility: str | None = None
    status: str | None = None


# --- Dashboard schemas ---


class SummaryCard(BaseModel):
    label: str
    value: int
    trend: str | None = None
    href: str
    breakdown: dict[str, int] | None = None


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    status: str
    timestamp: _dt.datetime
    label: str
    href: str


class DashboardSummary(BaseModel):
    cards: list[SummaryCard]
    activity: list[ActivityItem]


# --- Agreement schemas ---


class AgreementListItem(BaseModel):
    id: UUID
    agreement_id: str
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


class AgreementDetail(AgreementListItem):
    ecosystem_id: UUID
    text: str | None = None
    affected_parties: list[str] | None = None
    parent_agreement_id: UUID | None = None
    ratification_date: _dt.date | None = None
    created_date: _dt.date | None = None
    updated_at: _dt.datetime
    ratification_records: list[RatificationRecordSchema] = []


class AgreementCreateRequest(BaseModel):
    ecosystem_id: UUID
    type: str
    title: str
    text: str | None = None
    proposer: str | None = None
    domain: str | None = None
    hierarchy_level: str = "domain"
    affected_parties: list[str] | None = None
    review_date: _dt.date | None = None
    sunset_date: _dt.date | None = None


class AgreementUpdateRequest(BaseModel):
    title: str | None = None
    text: str | None = None
    proposer: str | None = None
    domain: str | None = None
    hierarchy_level: str | None = None
    affected_parties: list[str] | None = None
    review_date: _dt.date | None = None
    sunset_date: _dt.date | None = None
    status: str | None = None


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


class AgreementHistoryResponse(BaseModel):
    amendments: list[AmendmentRecordSchema]
    reviews: list[ReviewRecordSchema]
