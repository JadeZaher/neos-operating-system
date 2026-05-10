"""Safeguards schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class AuditListItem(BaseModel):
    id: uuid.UUID
    audit_id: str
    audit_date: _dt.date | None = None
    auditor: str | None = None
    overall_health_score: int | None = None
    status: str
    created_at: _dt.datetime


class AuditDetail(AuditListItem):
    ecosystem_id: uuid.UUID
    capture_risk_indicators: list | dict | None = None
    findings: str | None = None
    recommendations: list | dict | None = None
    next_audit_date: _dt.date | None = None
    updated_at: _dt.datetime


class AuditCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    auditor: str = "AI Governance Agent"


class HealthSummary(BaseModel):
    latest_audit: AuditDetail | None = None
    total_audits: int = 0
    latest_health_score: int | None = None
