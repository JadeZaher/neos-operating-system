"""Pydantic schemas for the CTC → NEOS Den handoff API."""

from __future__ import annotations

import uuid
import datetime as _dt

from pydantic import BaseModel


class CtcHandoffItem(BaseModel):
    member_id: uuid.UUID
    ready_for_neos_den: bool
    updated_at: _dt.datetime | None = None


class CtcHandoffSetRequest(BaseModel):
    ready_for_neos_den: bool
