"""Decision schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class DissentRecordSchema(BaseModel):
    id: uuid.UUID
    objector: str
    objection: str | None = None
    resolution: str | None = None
    notes: str | None = None


class ParticipantSchema(BaseModel):
    id: uuid.UUID
    name: str
    role: str | None = None
    position: str | None = None


class SemanticTagSchema(BaseModel):
    id: uuid.UUID
    topic: dict | None = None
    affected_parties: dict | None = None
    ecosystem_scope: str | None = None
    urgency_at_time: str | None = None
    related_precedents: dict | None = None


class DecisionListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    record_id: str
    date: _dt.date | None = None
    holding: str | None = None
    source_skill: str | None = None
    source_layer: int | None = None
    artifact_type: str | None = None
    domain: str | None = None
    precedent_level: str | None = None
    status: str
    created_at: _dt.datetime


class DecisionDetail(DecisionListItem):
    ratio_decidendi: str | None = None
    obiter_dicta: str | None = None
    deliberation_summary: str | None = None
    artifact_reference: str | None = None
    source_proposal_id: uuid.UUID | None = None
    source_agreement_id: uuid.UUID | None = None
    overruled_by: str | None = None
    superseded_by: str | None = None
    related_records: dict | None = None
    review_date: _dt.date | None = None
    recorder: str | None = None
    recorder_role: str | None = None
    verification_by: str | None = None
    verification_date: _dt.date | None = None
    updated_at: _dt.datetime
    dissent_records: list[DissentRecordSchema] = []
    participants: list[ParticipantSchema] = []
    semantic_tags: list[SemanticTagSchema] = []
