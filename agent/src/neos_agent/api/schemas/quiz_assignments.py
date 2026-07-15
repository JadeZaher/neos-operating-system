"""Pydantic schemas for the quiz assignments API."""

from __future__ import annotations

import uuid
import datetime as _dt

from pydantic import BaseModel


class QuizAssignmentSchema(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    quiz_title: str | None = None
    member_id: uuid.UUID
    member_name: str | None = None
    ecosystem_id: uuid.UUID | None = None
    assigned_by: uuid.UUID | None = None
    due_date: _dt.date | None = None
    status: str
    created_at: _dt.datetime


class QuizAssignmentCreateRequest(BaseModel):
    quiz_id: uuid.UUID
    member_id: uuid.UUID
    due_date: _dt.date | None = None
