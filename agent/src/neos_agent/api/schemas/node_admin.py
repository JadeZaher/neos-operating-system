"""Typed node support requests."""
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SupportInspectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: UUID
    reason: str = Field(min_length=3, max_length=500)


class SupportCommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: UUID | None = None
    action: str = Field(min_length=1, max_length=60)
    organization_id: UUID | None = None
    values: dict[str, Any] = Field(default_factory=dict, max_length=60)
    reason: str = Field(min_length=3, max_length=500)
    expected_version: str | None = Field(default=None, max_length=100)


class SupportProposalPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=500)
    proposed_change: str = Field(min_length=1, max_length=50000)
    rationale: str = Field(default="Draft requested by the member; details to confirm.", min_length=1, max_length=50000)
    type: Literal["operational", "policy", "resource", "structural"] = "operational"


class NodeAdminGrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    reason: str = Field(min_length=3, max_length=500)


class NodeAdminRevokeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=3, max_length=500)
