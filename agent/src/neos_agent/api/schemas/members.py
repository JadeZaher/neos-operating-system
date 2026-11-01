"""Pydantic schemas for the members API."""

from __future__ import annotations

import uuid
import datetime as _dt
from typing import Literal

from pydantic import BaseModel

MemberRole = Literal["user", "mod", "admin", "owner"]
# policy.MEMBER_PROFILES; co_creator and builder confer administration and are granted, never self-chosen.
MemberProfile = Literal["co_creator", "builder", "collaborator", "townhall"]


class MemberListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    member_id: str
    display_name: str
    current_status: str
    role: MemberRole = "user"
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
    shared_ecosystem_ids: list[uuid.UUID] | None = None
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


class RoleGrantSchema(BaseModel):
    """One recorded role or profile change (a MemberStatusTransition, trigger "role_grant" / "profile_grant")."""
    kind: Literal["role", "profile"] = "role"
    from_role: str
    to_role: str
    date: _dt.date
    granted_by: str | None = None  # the granter's current display name (stored by member id)


class MemberProfileResponse(MemberDetail):
    user_id: uuid.UUID
    username: str | None = None
    user_display_name: str | None = None
    profile_picture: str | None = None
    quiz_summary: dict
    badges: list
    tags: list
    # Roles the signed-in caller may give this member now (policy.assignable_roles); empty = no picker.
    caller_assignable_roles: list[MemberRole] = []
    # Profiles the caller may give this member (policy.can_grant_profile); empty = no picker.
    caller_grantable_profiles: list[MemberProfile] = []
    caller_is_self: bool = False
    role_history: list[RoleGrantSchema] = []


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


class RoleUpdateRequest(BaseModel):
    role: MemberRole


class ProfileGrantRequest(BaseModel):
    profile: MemberProfile


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
