"""Pydantic schemas for the app settings API."""

from __future__ import annotations

from pydantic import BaseModel


class AppSettingResponse(BaseModel):
    key: str
    value: dict | None = None


class AppSettingPutRequest(BaseModel):
    key: str
    value: dict
