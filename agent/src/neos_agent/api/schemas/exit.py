"""Exit schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class ExitListItem(BaseModel):
    id: uuid.UUID
    exit_type: str
    status: str
    member_id: uuid.UUID
    declared_date: _dt.date | None = None
    target_completion_date: _dt.date | None = None
    completed_date: _dt.date | None = None
    created_at: _dt.datetime


class ExitDetail(ExitListItem):
    ecosystem_id: uuid.UUID
    coordinator_id: uuid.UUID | None = None
    commitment_inventory: list | dict | None = None
    unwinding_status: dict | None = None
    data_export_requested: bool = False
    data_export_completed: _dt.date | None = None
    departure_notice: str | None = None
    re_entry_eligible: bool = True
    notes: str | None = None
    updated_at: _dt.datetime


class ExitCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    member_id: uuid.UUID
    exit_type: str = "standard"
    reason: str | None = None


class ExitStatusRequest(BaseModel):
    new_status: str
