"""Pydantic v2 response schemas for the NEOS agent API."""

from __future__ import annotations

from datetime import date, datetime
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
    founded_date: date | None = None
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
    founded_date: date | None = None
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
    founded_date: date | None = None
    tags: list[str] | None = None
    contact_email: str | None = None
    governance_summary: str | None = None
    visibility: str | None = None
    status: str | None = None
