"""Canonical agreement vocabulary shared by validation and API filtering."""

from __future__ import annotations

AGREEMENT_TYPES = frozenset({
    "uaf", "ecosystem", "access", "stewardship", "ethos", "culture_code",
    "space", "organizational", "policy", "protocol", "role_definition",
    "domain_contract", "guideline", "constitutional", "operational", "resource",
})
AGREEMENT_STATUSES = frozenset({
    "draft", "advice", "consent", "test", "active", "under_review", "sunset", "archived",
})
AGREEMENT_TYPE_ALIASES = {"universal_field": "uaf"}
AGREEMENT_STATUS_ALIASES = {"ratified": "active"}
PREREQUISITE_SCOPES = frozenset({"ecosystem", "domain", "collaboration"})


def canonical_agreement_type(value: str) -> str:
    """Return a canonical agreement type or raise for unsupported values."""
    normalized = AGREEMENT_TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())
    if normalized not in AGREEMENT_TYPES:
        raise ValueError(f"Unsupported agreement type: {value}")
    return normalized


def canonical_agreement_status(value: str) -> str:
    """Return a canonical lifecycle status or raise for unsupported values."""
    normalized = AGREEMENT_STATUS_ALIASES.get(value.strip().lower(), value.strip().lower())
    if normalized not in AGREEMENT_STATUSES:
        raise ValueError(f"Unsupported agreement status: {value}")
    return normalized


# G-Maint: review cycle (services/AGENTS.md "Maintenance and health (G-Maint)").

# Months from a renewal (or from creation) to the next review, by agreement type; others use the default.
REVIEW_INTERVAL_MONTHS = {"space": 12, "access": 6, "organizational": 24, "uaf": 12, "culture_code": 12}
DEFAULT_REVIEW_INTERVAL_MONTHS = 12
# Framework agreement-review E.3: a sunset gives this many days' notice before the agreement ends.
SUNSET_NOTICE_DAYS = 60


def default_review_date(agreement_type: str | None, today):
    """The next review date for an agreement of `agreement_type`, counted from `today` (a date)."""
    from neos_agent.services.dates import add_months

    return add_months(today, REVIEW_INTERVAL_MONTHS.get(agreement_type or "", DEFAULT_REVIEW_INTERVAL_MONTHS))
