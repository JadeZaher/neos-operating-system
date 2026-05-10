"""Auth & ecosystem schemas."""

import datetime as _dt
from uuid import UUID

from pydantic import BaseModel


class MemberSummary(BaseModel):
    id: UUID
    display_name: str
    did: str | None = None
    profile: str | None = None
    ecosystem_id: UUID
    current_status: str
    has_password: bool = False
    has_did: bool = False
    oauth_provider: str | None = None


class UserSummary(BaseModel):
    id: UUID
    display_name: str
    did: str | None = None
    username: str | None = None
    has_password: bool = False
    has_did: bool = False
    oauth_provider: str | None = None
    profile_picture: str | None = None


class AuthChallengeResponse(BaseModel):
    challenge: str


class AuthVerifyResponse(BaseModel):
    success: bool
    display_name: str
    member: MemberSummary


class LoginRequest(BaseModel):
    username: str
    password: str


class SetCredentialsRequest(BaseModel):
    username: str
    password: str


class SetCredentialsResponse(BaseModel):
    success: bool
    username: str


class EcosystemSummary(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    status: str
    logo_url: str | None = None
    location: str | None = None
    member_count: int = 0


class AuthMeResponse(BaseModel):
    user: UserSummary
    member: MemberSummary | None = None
    ecosystems: list[EcosystemSummary]
