"""Pydantic schemas for the proposals API (ACT process).

Extracted from proposals.py to keep schema definitions co-located with
other API schemas.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pydantic import BaseModel, field_validator


class ProposalListItem(BaseModel):
    support_provenance: dict | None = None
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    proposal_id: str
    type: str
    decision_type: str | None = None
    title: str
    version: str
    status: str
    proposer: str | None = None
    proposer_member_id: uuid.UUID | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    created_at: _dt.datetime


class AdviceEntrySchema(BaseModel):
    id: uuid.UUID
    advisor: str
    member_id: uuid.UUID | None = None
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
    member_name: str  # display name of the member holding the position (server-set)
    member_id: uuid.UUID | None = None
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
    reporter_member_id: uuid.UUID | None = None
    reporter_name: str | None = None


class ActPolicySchema(BaseModel):
    """ACT gate declaration made at the proposal/agreement level."""
    min_advice_rounds: int = 1
    consent_required: bool = True
    consent_quorum: int | None = None
    test_cases: list[str] = []
    matching_profile: dict | None = None

    @field_validator("matching_profile")
    @classmethod
    def matching_configuration(cls, value):
        if value is not None:
            from neos_agent.services.matching import validate_configuration
            from neos_agent.api.errors import ApiError
            try:
                validate_configuration(value)
            except ApiError as error:
                raise ValueError(error.message) from None
        return value


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
    act_policy: dict | None = None
    own_act_policy: dict | None = None
    gates: dict | None = None
    governing_agreement_id: uuid.UUID | None = None
    governing_agreement: dict | None = None
    amends_agreement_id: uuid.UUID | None = None
    amends_agreement: dict | None = None
    registered_agreement_id: uuid.UUID | None = None
    registered_agreement: dict | None = None
    advice_logs: list[AdviceLogSchema] = []
    consent_records: list[ConsentRecordSchema] = []
    test_reports: list[TestReportSchema] = []
    caller_role: str | None = None
    caller_can_conduct: bool = False  # may participate (advice/consent/test)
    caller_can_manage: bool = False  # may edit and make manual status moves
    caller_is_proposer: bool = False
    caller_can_register: bool = False  # a steward may register this ratified proposal as an agreement
    caller_position: dict | None = None  # the caller's current position in the latest consent record
    allowed_next: list[dict] = []  # manual moves the caller may request now (act_gates.proposal_next_moves)


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
    act_policy: ActPolicySchema | None = None
    governing_agreement_id: uuid.UUID | None = None
    amends_agreement_id: uuid.UUID | None = None


class ProposalUpdateRequest(BaseModel):
    title: str | None = None
    proposed_change: str | None = None
    rationale: str | None = None
    affected_domain: str | None = None
    urgency: str | None = None
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    advice_deadline: _dt.date | None = None
    consent_deadline: _dt.date | None = None
    act_policy: ActPolicySchema | None = None
    governing_agreement_id: uuid.UUID | None = None
    amends_agreement_id: uuid.UUID | None = None
    decision_type: str | None = None


class AdviceEntryCreateRequest(BaseModel):
    advisor: str | None = None  # ignored: the server records the caller's member name
    role: str | None = None
    ethos: str | None = None
    advice_type: str | None = None
    content: str | None = None
    concerns: str | None = None
    new_round: bool = False  # open a fresh advice round (counts toward min_advice_rounds)


class ConsentPositionRequest(BaseModel):
    """The caller's position; the participant is always the caller (a sent member_name is ignored)."""
    position: str
    objection_text: str | None = None


class StatusTransitionRequest(BaseModel):
    status: str
    note: str | None = None  # required when sending a proposal back for revision


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
