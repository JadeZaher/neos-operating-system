"""Ecosystem schemas."""

import datetime as _dt
from uuid import UUID

from pydantic import BaseModel

from .auth import EcosystemSummary


class EcosystemStewardItem(BaseModel):
    """Minimal, public-safe steward reference for an ecosystem detail response."""
    id: UUID  # member id
    display_name: str
    role: str  # per-ecosystem tier: admin | owner


class EcosystemDetail(EcosystemSummary):
    website: str | None = None
    founded_date: _dt.date | None = None
    tags: list[str] | None = None
    contact_email: str | None = None
    governance_summary: str | None = None
    visibility: str = "public"
    stewards: list[EcosystemStewardItem] = []
    caller_role: str | None = None  # caller's per-ecosystem role tier, None if not a member


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
