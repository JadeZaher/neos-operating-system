"""The one date rule: when is a due date passed? See services/AGENTS.md "Maintenance and health (G-Maint)"."""

from __future__ import annotations

import calendar
import datetime as _dt

# "Anywhere on Earth": a date-only due date passes once that day has ended at UTC-12 (owner default 2026-11-01).
# Set to timedelta(0) to revert to UTC midnight.
DAY_ENDS_EVERYWHERE_AFTER = _dt.timedelta(hours=12)


def utc_now() -> _dt.datetime:
    """Naive UTC now: the timestamp columns are TIMESTAMP WITHOUT TIME ZONE."""
    return _dt.datetime.now(_dt.UTC).replace(tzinfo=None)


def naive_utc(moment: _dt.datetime) -> _dt.datetime:
    """An aware datetime converted to naive UTC; a naive one is taken as UTC already."""
    return moment.astimezone(_dt.UTC).replace(tzinfo=None) if moment.tzinfo else moment


def utc_today(now: _dt.datetime | None = None) -> _dt.date:
    """The UTC calendar day: for creation stamps (`created_date`, a review's or an audit's date)."""
    return naive_utc(now or utc_now()).date()


def aoe_today(now: _dt.datetime | None = None) -> _dt.date:
    """The latest calendar day that has not yet ended everywhere on Earth: 'today' for every due-date decision."""
    return (naive_utc(now or utc_now()) - DAY_ENDS_EVERYWHERE_AFTER).date()


def date_passed(due: _dt.date | _dt.datetime | None, now: _dt.datetime | None = None) -> bool:
    """True once `due` has gone by: a date when its day has ended everywhere, a timestamp at that instant (UTC)."""
    if due is None:
        return False
    if isinstance(due, _dt.datetime):
        return naive_utc(now or utc_now()) > naive_utc(due)
    return due < aoe_today(now)


def add_months(day: _dt.date, months: int) -> _dt.date:
    """`day` plus whole calendar months, clamped to the month's last day (31 Jan + 1 month = 28/29 Feb)."""
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))
