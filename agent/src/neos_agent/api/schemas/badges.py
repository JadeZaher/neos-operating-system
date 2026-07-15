"""Pydantic schemas for the badges API."""

from __future__ import annotations

import uuid
import datetime as _dt

from pydantic import BaseModel


class BadgeDefinitionSchema(BaseModel):
    id: uuid.UUID
    ecosystem_id: uuid.UUID | None = None
    badge_key: str
    badge_name: str
    badge_description: str | None = None
    badge_category: str | None = None
    badge_icon: str | None = None
    strength: float | None = None
    is_active: bool = True
    created_by: uuid.UUID | None = None
    created_at: _dt.datetime
    updated_at: _dt.datetime


class BadgeDefinitionCreateRequest(BaseModel):
    badge_key: str
    badge_name: str
    badge_description: str | None = None
    badge_category: str | None = None
    badge_icon: str | None = None
    strength: float | None = None
    ecosystem_id: uuid.UUID | None = None


class BadgeDefinitionUpdateRequest(BaseModel):
    badge_name: str | None = None
    badge_description: str | None = None
    badge_category: str | None = None
    badge_icon: str | None = None
    strength: float | None = None
    is_active: bool | None = None
