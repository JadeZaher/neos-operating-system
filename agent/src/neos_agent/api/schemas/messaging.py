"""Messaging schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class ParticipantSummary(BaseModel):
    id: uuid.UUID
    display_name: str
    role: str = "member"


class ConversationSummary(BaseModel):
    id: uuid.UUID
    type: str
    title: str | None = None
    last_message: str | None = None
    last_message_at: _dt.datetime | None = None
    unread_count: int = 0
    participants: list[ParticipantSummary] = []


class MessageSchema(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    content: str
    message_type: str
    created_at: _dt.datetime
    edited_at: _dt.datetime | None = None


class ConversationDetailSchema(BaseModel):
    id: uuid.UUID
    type: str
    title: str | None = None
    participants: list[ParticipantSummary] = []
    messages: list[MessageSchema] = []
    total_messages: int = 0


class CreateConversationRequest(BaseModel):
    type: str  # "dm" or "group"
    title: str | None = None
    participant_ids: list[uuid.UUID]


class MemberPickerItem(BaseModel):
    id: uuid.UUID
    display_name: str
    profile: str | None = None
    ecosystem_id: uuid.UUID | None = None
    ecosystem_name: str | None = None
    role: str | None = None  # per-ecosystem tier: user, mod, admin, owner
