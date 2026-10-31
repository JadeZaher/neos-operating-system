"""Domain schemas."""

import datetime as _dt
import uuid
from typing import Any

from pydantic import BaseModel, Field


class DomainElementSchema(BaseModel):
    id: uuid.UUID
    element_name: str
    element_value: Any = None  # JSON: object, list, or scalar


class DomainMetricSchema(BaseModel):
    id: uuid.UUID
    metric: str
    target: str | None = None
    measurement_method: str | None = None


class DomainParticipantSchema(BaseModel):
    member_id: uuid.UUID
    display_name: str
    role: str


class DomainListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    domain_id: str
    name: str | None = None
    display_name: str  # name -> purpose "Name — ..." prefix -> domain_id
    version: str
    status: str
    purpose: str | None = None
    current_steward: str | None = None
    parent_domain_id: uuid.UUID | None = None
    created_at: _dt.datetime
    version_fingerprint: str | None = None
    caller_is_participant: bool = False
    caller_is_steward: bool = False


class DomainDetail(DomainListItem):
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    steward_id: uuid.UUID | None = None
    created_by: str | None = None
    metric_definitions: str | dict | None = None
    elements: dict | None = None
    updated_at: _dt.datetime
    domain_elements: list[DomainElementSchema] = []
    domain_metrics: list[DomainMetricSchema] = []
    caller_can_edit: bool = False
    participants: list[DomainParticipantSchema] = []
    participant_count: int = 0


class DomainCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    name: str | None = Field(default=None, max_length=200)
    purpose: str | None = None
    current_steward: str | None = None
    steward_id: uuid.UUID | None = None
    parent_domain_id: uuid.UUID | None = None
    created_by: str | None = None
    metric_definitions: str | dict | None = None
    elements: dict | None = None


class DomainUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    status: str | None = None
    purpose: str | None = None
    current_steward: str | None = None
    steward_id: uuid.UUID | None = None
    parent_domain_id: uuid.UUID | None = None
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    metric_definitions: str | dict | None = None
    elements: dict | None = None
