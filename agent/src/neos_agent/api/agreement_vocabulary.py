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
