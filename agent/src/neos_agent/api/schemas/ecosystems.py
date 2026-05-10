"""Ecosystem schemas."""

import datetime as _dt
from uuid import UUID

from pydantic import BaseModel

from .auth import EcosystemSummary


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
