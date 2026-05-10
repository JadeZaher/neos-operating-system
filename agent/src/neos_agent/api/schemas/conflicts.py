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


class ConflictListItem(BaseModel):
    id: uuid.UUID
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


class ConflictDetail(ConflictListItem):
    ecosystem_id: uuid.UUID
    description: str | None = None
    reporter_id: uuid.UUID | None = None
    root_cause_category: str | None = None
    parties: dict | None = None
    facilitator_id: uuid.UUID | None = None
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
    reporter_id: uuid.UUID | None = None
    severity: str | None = None
    scope: str | None = None
    tier: int | None = None
    root_cause_category: str | None = None
    urgency: str | None = None
    safety_flag: bool = False
    parties: dict | None = None
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
    parties: dict | None = None
    facilitator_id: uuid.UUID | None = None
    domain: str | None = None
    triage_notes: str | None = None
    resolution_summary: str | None = None
    resolved_date: _dt.date | None = None


class RepairCreateRequest(BaseModel):
    title: str
    commitments: dict | None = None
    responsible_party: str | None = None
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
    completed_date: _dt.date | None = None
