"""Pydantic v2 schemas for Agreement-related API responses and requests."""

import datetime as _dt
from uuid import UUID

from pydantic import BaseModel


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


class AgreementDetail(AgreementListItem):
    text: str | None = None
    affected_parties: list | dict | None = None
    parent_agreement_id: UUID | None = None
    ratification_date: _dt.date | None = None
    created_date: _dt.date | None = None
    updated_at: _dt.datetime
    ratification_records: list[RatificationRecordSchema] = []


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


class AgreementUpdateRequest(BaseModel):
    title: str | None = None
    text: str | None = None
    proposer: str | None = None
    domain: str | None = None
    hierarchy_level: str | None = None
    affected_parties: list | dict | None = None
    shared_ecosystem_ids: list[UUID] | None = None
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
