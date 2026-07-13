"""Pydantic schemas for the proposals API (ACT process).

Extracted from proposals.py to keep schema definitions co-located with
other API schemas.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pydantic import BaseModel


class ProposalListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    proposal_id: str
    type: str
    decision_type: str | None = None
    title: str
    version: str
    status: str
    proposer: str | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    created_at: _dt.datetime


class AdviceEntrySchema(BaseModel):
    id: uuid.UUID
    advisor: str
    role: str | None = None
    ethos: str | None = None
    advice_type: str | None = None
    content: str | None = None
    concerns: str | None = None
    date: _dt.date | None = None


class AdviceLogSchema(BaseModel):
    id: uuid.UUID
    advice_window_start: _dt.date | None = None
    advice_window_end: _dt.date | None = None
    urgency: str | None = None
    summary: str | None = None
    proposer_modifications: str | None = None
    entries: list[AdviceEntrySchema] = []


class ConsentParticipantSchema(BaseModel):
    id: uuid.UUID
    member_name: str
    position: str | None = None
    objection_text: str | None = None
    integration_attempted: bool | None = None
    integration_outcome: str | None = None
    date: _dt.date | None = None


class ConsentRecordSchema(BaseModel):
    id: uuid.UUID
    consent_mode: str
    weighting_model: str | None = None
    facilitator: str | None = None
    date: _dt.date | None = None
    quorum_required: str | None = None
    quorum_met: bool = False
    outcome: str | None = None
    escalation_level: str | None = None
    participants: list[ConsentParticipantSchema] = []


class TestSuccessCriterionSchema(BaseModel):
    id: uuid.UUID
    criterion: str | None = None
    metric: str | None = None
    baseline: str | None = None
    target: str | None = None
    actual: str | None = None
    met: bool | None = None


class TestReportSchema(BaseModel):
    id: uuid.UUID
    test_start_date: _dt.date | None = None
    test_end_date: _dt.date | None = None
    outcome: str | None = None
    observations: str | None = None
    midpoint_findings: str | None = None
    modifications: str | None = None
    next_action: str | None = None
    success_criteria_summary: str | None = None
    success_criteria: list[TestSuccessCriterionSchema] = []


class ProposalDetail(ProposalListItem):
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    co_sponsors: list | dict | None = None
    impacted_parties: list | dict | None = None
    proposed_change: str | None = None
    rationale: str | None = None
    created_date: _dt.date | None = None
    advice_deadline: _dt.date | None = None
    consent_deadline: _dt.date | None = None
    test_duration: str | None = None
    updated_at: _dt.datetime
    advice_logs: list[AdviceLogSchema] = []
    consent_records: list[ConsentRecordSchema] = []
    test_reports: list[TestReportSchema] = []


class ProposalCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    type: str
    title: str
    decision_type: str | None = None
    proposer: str | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    proposed_change: str | None = None
    rationale: str | None = None
    advice_deadline: _dt.date | None = None


class ProposalUpdateRequest(BaseModel):
    title: str | None = None
    proposed_change: str | None = None
    rationale: str | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    advice_deadline: _dt.date | None = None
    consent_deadline: _dt.date | None = None


class AdviceEntryCreateRequest(BaseModel):
    advisor: str
    role: str | None = None
    ethos: str | None = None
    advice_type: str | None = None
    content: str | None = None
    concerns: str | None = None


class ConsentPositionRequest(BaseModel):
    member_name: str
    position: str
    objection_text: str | None = None


class TestCriterionInput(BaseModel):
    criterion: str
    metric: str | None = None
    target: str | None = None
    actual: str | None = None
    met: bool = False
    evidence: str | None = None


class TestReportCreateRequest(BaseModel):
    observations: str
    outcome: str  # passed, failed, modified
    success_criteria: list[TestCriterionInput] = []
