"""Safeguards schemas."""

import datetime as _dt
import uuid
from typing import Any

from pydantic import BaseModel


class IndicatorScoreSchema(BaseModel):
    indicator_id: str
    indicator_name: str
    measured_value: str | int | float | None = None
    status: str | None = None  # healthy, warning, critical
    prior_value: str | int | float | None = None
    trend: str | None = None  # improving, stable, degrading, baseline
    notes: str | None = None
    # G-Maint: frozen at publish from services/health (the computed value's unit, how it was computed, its band).
    unit: str | None = None
    basis: str | None = None
    band: str | None = None
    computable: bool | None = None


class TriggeredSafeguardSchema(BaseModel):
    trigger_id: str
    indicator_id: str
    threshold_crossed: str
    recommended_action: str


class AuditListItem(BaseModel):
    id: uuid.UUID
    audit_id: str
    ecosystem_id: uuid.UUID | None = None
    audit_date: _dt.date | None = None
    auditor: str | None = None
    overall_health_score: int | None = None
    status: str
    created_at: _dt.datetime
    completed_at: _dt.datetime | None = None
    # New fields (optional for backward compat)
    overall_health: str | None = None
    audit_scope: str | None = None
    trigger_type: str | None = None
    self_assessment: bool = False  # G-Maint: a steward audited their own ecosystem because nobody else could


class AuditDetail(AuditListItem):
    capture_risk_indicators: list | dict | None = None
    findings: str | None = None
    recommendations: list | dict | None = None
    next_audit_due: _dt.date | None = None
    updated_at: _dt.datetime | None = None
    # New structured fields
    audit_period_start: _dt.date | None = None
    audit_period_end: _dt.date | None = None
    auditor_ids: list[str] | None = None
    indicator_scores: list[IndicatorScoreSchema] | None = None
    triggered_safeguards: list[TriggeredSafeguardSchema] | None = None
    structured_recommendations: list[str] | None = None
    caller_can_edit: bool = False


class AuditAbandonRequest(BaseModel):
    """FX-Maint: why a draft is abandoned (recorded)."""
    reason: str = ""


class AuditRespondRequest(BaseModel):
    """FX-Maint: the stewards' response to a published audit, optionally naming a proposal of that ecosystem."""
    note: str = ""
    proposal_id: uuid.UUID | None = None


class AuditCreateRequest(BaseModel):
    """Start an audit as the signed-in member (the auditor is always the caller)."""
    ecosystem_id: uuid.UUID
    audit_scope: str | None = None
    audit_period_start: _dt.date | None = None
    audit_period_end: _dt.date | None = None
    indicator_scores: list[IndicatorScoreSchema] | None = None
    findings: str | None = None
    structured_recommendations: list[str] | None = None


class AuditUpdateRequest(BaseModel):
    """Edit a draft audit; only fields that are sent change."""
    audit_scope: str | None = None
    audit_period_start: _dt.date | None = None
    audit_period_end: _dt.date | None = None
    indicator_scores: list[IndicatorScoreSchema] | None = None
    findings: str | None = None
    structured_recommendations: list[str] | None = None


class HealthSummary(BaseModel):
    latest_audit: AuditDetail | dict | None = None
    recent_audits: list[dict] = []
    health_score: int | None = None
    indicator_scores: list[IndicatorScoreSchema] | None = None
    triggered_safeguards: list[TriggeredSafeguardSchema] | None = None
    ecosystems: list[dict] = []  # G-Maint: the latest published audit per selected ecosystem, labelled
