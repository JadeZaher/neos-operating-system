"""Pydantic schemas for the members API."""

from __future__ import annotations

import uuid
import datetime as _dt

from pydantic import BaseModel


class MemberListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    member_id: str
    display_name: str
    current_status: str
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    onboarding_status: str | None = None
    created_at: _dt.datetime


class OnboardingSnapshot(BaseModel):
    id: uuid.UUID
    facilitator: str | None = None
    completion_percentage: int | None = 0
    consent_date: _dt.date | None = None
    cooling_off_start: _dt.date | None = None
    cooling_off_end: _dt.date | None = None


class MemberDetail(MemberListItem):
    did: str | None = None
    skills_offered: list | dict | None = None
    skills_needed: list | dict | None = None
    interests: list | dict | None = None
    kyc_status: str | None = None
    last_governance_activity_date: _dt.date | None = None
    notes: str | None = None
    privacy: dict | None = None
    updated_at: _dt.datetime
    onboarding: OnboardingSnapshot | None = None


class MemberProfileResponse(MemberDetail):
    user_id: uuid.UUID
    username: str | None = None
    user_display_name: str | None = None
    profile_picture: str | None = None
    quiz_summary: dict
    badges: list
    tags: list


class MemberCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    display_name: str
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    skills_offered: list | dict | None = None
    skills_needed: list | dict | None = None
    interests: list | dict | None = None
    notes: str | None = None


class MemberUpdateRequest(BaseModel):
    display_name: str | None = None
    profile: str | None = None
    phone: str | None = None
    profile_picture: str | None = None
    skills_offered: list | dict | None = None
    skills_needed: list | dict | None = None
    interests: list | dict | None = None
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    notes: str | None = None
    privacy: dict | None = None


class StatusTransitionRequest(BaseModel):
    status: str
    trigger: str | None = None
    notes: str | None = None


class OnboardingChecklistItem(BaseModel):
    id: uuid.UUID
    facilitator: str | None = None
    mentor_id: uuid.UUID | None = None
    uaf_version_consented: str | None = None
    consent_date: _dt.date | None = None
    cooling_off_start: _dt.date | None = None
    cooling_off_end: _dt.date | None = None
    section_consents: dict | None = None
    checklist_items: dict | None = None
    completion_percentage: int | None = 0
