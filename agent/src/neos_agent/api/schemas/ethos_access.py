"""Ethos access & participation-consent schemas."""

import datetime as _dt
import uuid

from pydantic import BaseModel


class EthosAccessStatus(BaseModel):
    """Current member's access/consent status for an ethos (ecosystem)."""
    has_access: bool
    role_in_ethos: str | None = None
    access_level: str | None = None


class EthosAccessGrant(BaseModel):
    """An access grant row, for the admin management surface."""
    id: uuid.UUID
    member_id: uuid.UUID
    member_name: str | None = None
    ecosystem_id: uuid.UUID
    role_in_ethos: str | None = None
    access_level: str | None = None
    granted_at: _dt.datetime
    granted_by: uuid.UUID | None = None


class EthosAccessGrantRequest(BaseModel):
    """Admin grant request."""
    member_id: uuid.UUID
    role_in_ethos: str | None = None
    access_level: str | None = None
