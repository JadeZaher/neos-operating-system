"""Onboarding schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class OnboardingListItem(BaseModel):
    id: uuid.UUID
    member_id: uuid.UUID
    member_display_name: str | None = None
    facilitator: str | None = None
    completion_percentage: int | None = 0
    consent_date: _dt.date | None = None
    cooling_off_start: _dt.date | None = None
    cooling_off_end: _dt.date | None = None
    created_at: _dt.datetime


class CeremonyState(BaseModel):
    member_id: uuid.UUID
    section_consents: dict
    completion_percentage: int
    cooling_off_start: _dt.date | None = None
    cooling_off_end: _dt.date | None = None
    consent_date: _dt.date | None = None
    facilitator: str | None = None
    uaf_version_consented: str | None = None


class SectionConsentRequest(BaseModel):
    section: str
    consented: bool
    position: str | None = None  # consent, stand_aside, object
    objection_text: str | None = None
