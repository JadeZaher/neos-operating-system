"""Pydantic schemas for the teams API."""

from __future__ import annotations

import uuid
import datetime as _dt

from pydantic import BaseModel


class TeamSchema(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID
    name: str
    description: str | None = None
    is_active: bool = True
    created_by: uuid.UUID | None = None
    created_at: _dt.datetime
    updated_at: _dt.datetime
    member_count: int = 0


class TeamCreateRequest(BaseModel):
    name: str
    description: str | None = None
    ecosystem_id: uuid.UUID | None = None


class TeamUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class TeamMemberSchema(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    member_id: uuid.UUID
    member_name: str | None = None
    role: str
    created_at: _dt.datetime


class TeamMemberAddRequest(BaseModel):
    member_id: uuid.UUID
    role: str | None = None
