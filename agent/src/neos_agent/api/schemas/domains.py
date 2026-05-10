"""Domain schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class DomainElementSchema(BaseModel):
    id: uuid.UUID
    element_name: str
    element_value: dict | None = None


class DomainMetricSchema(BaseModel):
    id: uuid.UUID
    metric: str
    target: str | None = None
    measurement_method: str | None = None


class DomainListItem(BaseModel):
    id: uuid.UUID
    domain_id: str
    version: str
    status: str
    purpose: str | None = None
    current_steward: str | None = None
    parent_domain_id: uuid.UUID | None = None
    created_at: _dt.datetime
    version_fingerprint: str | None = None


class DomainDetail(DomainListItem):
    ecosystem_id: uuid.UUID
    steward_id: uuid.UUID | None = None
    created_by: str | None = None
    metric_definitions: str | dict | None = None
    elements: dict | None = None
    updated_at: _dt.datetime
    domain_elements: list[DomainElementSchema] = []
    domain_metrics: list[DomainMetricSchema] = []


class DomainCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    purpose: str | None = None
    current_steward: str | None = None
    steward_id: uuid.UUID | None = None
    parent_domain_id: uuid.UUID | None = None
    created_by: str | None = None
    metric_definitions: str | dict | None = None
    elements: dict | None = None


class DomainUpdateRequest(BaseModel):
    status: str | None = None
    purpose: str | None = None
    current_steward: str | None = None
    steward_id: uuid.UUID | None = None
    parent_domain_id: uuid.UUID | None = None
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    metric_definitions: str | dict | None = None
    elements: dict | None = None
