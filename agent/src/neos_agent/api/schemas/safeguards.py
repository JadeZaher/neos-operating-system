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
    trend: str | None = None  # improving, stable, degrading
    notes: str | None = None


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


class AuditCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    auditor: str = "AI Governance Agent"


class HealthSummary(BaseModel):
    latest_audit: AuditDetail | dict | None = None
    recent_audits: list[dict] = []
    health_score: int | None = None
    indicator_scores: list[IndicatorScoreSchema] | None = None
    triggered_safeguards: list[TriggeredSafeguardSchema] | None = None
