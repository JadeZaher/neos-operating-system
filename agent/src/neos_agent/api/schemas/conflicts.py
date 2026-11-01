"""Conflict schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class RepairAgreementSchema(BaseModel):
    id: uuid.UUID
    title: str
    commitments: dict | None = None
    responsible_party: str | None = None
    status: str
    checkin_30_date: _dt.date | None = None
    checkin_30_notes: str | None = None
    checkin_60_date: _dt.date | None = None
    checkin_60_notes: str | None = None
    checkin_90_date: _dt.date | None = None
    checkin_90_notes: str | None = None
    completed_date: _dt.date | None = None
    created_at: _dt.datetime
    next_checkin_date: _dt.date | None = None
    next_checkin_overdue: bool = False


class ConflictListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    case_id: str
    title: str
    status: str
    severity: str | None = None
    scope: str | None = None
    tier: int | None = None
    urgency: str | None = None
    safety_flag: bool = False
    domain: str | None = None
    created_at: _dt.datetime
    stage: str = ""
    next_step: str = ""
    decided_by: str = ""
    caller_is_reporter: bool = False


class ConflictDetail(ConflictListItem):
    description: str | None = None
    reporter_id: uuid.UUID | None = None
    reporter_name: str | None = None
    root_cause_category: str | None = None
    parties: dict | list | None = None
    facilitator_id: uuid.UUID | None = None
    facilitator_name: str | None = None
    party_names: list[str] = []
    caller_can_triage: bool = False
    allowed_next: list[str] = []
    triage_notes: str | None = None
    resolution_summary: str | None = None
    resolved_date: _dt.date | None = None
    updated_at: _dt.datetime
    repair_agreements: list[RepairAgreementSchema] = []


class ConflictCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    title: str
    description: str | None = None
    severity: str | None = None
    scope: str | None = None
    tier: int | None = None
    root_cause_category: str | None = None
    urgency: str | None = None
    safety_flag: bool = False
    # Members involved; only these ids grant access to the case.
    party_member_ids: list[uuid.UUID] | None = None
    domain: str | None = None


class ConflictUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    severity: str | None = None
    scope: str | None = None
    tier: int | None = None
    root_cause_category: str | None = None
    urgency: str | None = None
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    safety_flag: bool | None = None
    party_member_ids: list[uuid.UUID] | None = None
    facilitator_id: uuid.UUID | None = None
    domain: str | None = None
    triage_notes: str | None = None
    resolution_summary: str | None = None


class RepairCreateRequest(BaseModel):
    title: str
    commitments: list | dict | None = None  # Accept both formats
    responsible_party: str | None = None
    parties: list[str] | None = None  # NEW: list of party names
    review_date: _dt.date | None = None  # NEW
    facilitator_notes: str | None = None  # NEW
    checkin_30_date: _dt.date | None = None
    checkin_60_date: _dt.date | None = None
    checkin_90_date: _dt.date | None = None


class RepairUpdateRequest(BaseModel):
    title: str | None = None
    commitments: dict | None = None
    responsible_party: str | None = None
    status: str | None = None
    checkin_30_date: _dt.date | None = None
    checkin_30_notes: str | None = None
    checkin_60_date: _dt.date | None = None
    checkin_60_notes: str | None = None
    checkin_90_date: _dt.date | None = None
    checkin_90_notes: str | None = None
    # Required with status "fulfilled": both parties agree the repair is done. The server sets completed_date.
    confirmed_by_parties: bool = False
