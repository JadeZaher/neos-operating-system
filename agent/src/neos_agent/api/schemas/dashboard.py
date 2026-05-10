"""Dashboard response schemas."""

import datetime as _dt

from pydantic import BaseModel


class SummaryCard(BaseModel):
    label: str
    value: int
    trend: str | None = None
    href: str
    breakdown: dict[str, int] | None = None


class ActivityItem(BaseModel):
    id: str
    type: str
    title: str
    status: str
    timestamp: _dt.datetime
    label: str
    href: str


class DashboardSummary(BaseModel):
    cards: list[SummaryCard]
    activity: list[ActivityItem]
