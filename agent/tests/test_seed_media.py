"""Seed image URL backfill coverage."""

from __future__ import annotations

from neos_agent.db.models import Ecosystem
from scripts.seed_omnione import (
    ECOSYSTEM_MEDIA_URLS,
    _backfill_ecosystem_media_urls,
    _uid,
)


async def test_ecosystem_media_backfill_is_idempotent_for_deterministic_rows(
    db_session,
):
    omnione = Ecosystem(
        id=_uid("eco.omnione"),
        name="OmniOne",
        status="active",
    )
    escherbridge = Ecosystem(
        id=_uid("eco.escherbridge"),
        name="Escherbridge",
        status="active",
        logo_url="https://cdn.example.test/custom.webp",
    )
    db_session.add_all([omnione, escherbridge])
    await db_session.commit()

    assert await _backfill_ecosystem_media_urls(db_session) == 1
    assert omnione.logo_url == ECOSYSTEM_MEDIA_URLS[omnione.id]
    assert escherbridge.logo_url == "https://cdn.example.test/custom.webp"

    assert await _backfill_ecosystem_media_urls(db_session) == 0
