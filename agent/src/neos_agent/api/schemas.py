"""Pydantic v2 response schemas for the NEOS agent API."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    skills_loaded: int
    skills_available: bool
    database: str
    version: str


class SkillItem(BaseModel):
    name: str
    description: str
    layer: int
    version: str
    depends_on: list[str]


class SkillsResponse(BaseModel):
    count: int
    skills: list[SkillItem]


class ApiError(BaseModel):
    error: str
