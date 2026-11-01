"""Exit schemas: requests, and the list/detail shapes api/exit.py serializes (see api/AGENTS.md "Emergency and exit")."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class ExitListItem(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    member_id: uuid.UUID
    member_name: str | None = None
    exit_type: str
    status: str
    reason: str | None = None
    declared_date: _dt.date | None = None
    target_completion_date: _dt.date | None = None  # the handoff ends by this date
    completed_date: _dt.date | None = None
    created_at: _dt.datetime | None = None


class ExitDetail(ExitListItem):
    coordinator_id: uuid.UUID | None = None
    commitment_inventory: list | dict | None = None
    unwinding_status: dict | None = None
    data_export_requested: bool = False
    data_export_completed: _dt.date | None = None
    departure_notice: str | None = None
    re_entry_eligible: bool = True
    notes: str | None = None
    updated_at: _dt.datetime | None = None
    handoff_max_days: int
    next_step: str
    caller_is_leaver: bool
    allowed_next: list[str]


class ExitCreateRequest(BaseModel):
    ecosystem_id: uuid.UUID
    shared_ecosystem_ids: list[uuid.UUID] | None = None
    member_id: uuid.UUID | None = None  # ignored when it is the caller; anyone else is refused (self-only)
    exit_type: str = "standard"
    reason: str | None = None


class ExitStatusRequest(BaseModel):
    new_status: str
