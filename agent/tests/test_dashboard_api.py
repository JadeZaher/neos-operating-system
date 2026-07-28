"""Dashboard aggregate and ecosystem-scope regressions."""

from __future__ import annotations

from types import SimpleNamespace
import uuid

import pytest

from neos_agent.api.dashboard import _summary_counts
from neos_agent.api.helpers import get_ecosystem_ids
from neos_agent.db import course_models as _course_models  # noqa: F401
from neos_agent.db.models import Domain, Ecosystem


ECO_ID = uuid.UUID("00000000000000000000000000000001")


@pytest.mark.asyncio
async def test_summary_counts_include_records_shared_into_scope(seeded_db):
    other_ecosystem_id = uuid.uuid4()
    seeded_db.add(
        Ecosystem(id=other_ecosystem_id, name="Shared source", status="active")
    )
    seeded_db.add(
        Domain(
            ecosystem_id=other_ecosystem_id,
            shared_ecosystem_ids=[str(ECO_ID)],
            domain_id="SHARED-DOMAIN",
            version="1.0",
            status="active",
        )
    )
    await seeded_db.commit()

    counts = await _summary_counts(seeded_db, [ECO_ID])

    assert counts == {
        "agreements": 2,
        "members": 3,
        "domains": 2,
        "proposals": 1,
        "decisions": 0,
        "proposals_by_status": {"advice": 1},
        "agreements_by_status": {"active": 1, "draft": 1},
    }


def test_explicit_ecosystem_scope_is_limited_to_authorized_ids():
    authorized_id = uuid.uuid4()
    unauthorized_id = uuid.uuid4()
    request = SimpleNamespace(
        ctx=SimpleNamespace(
            selected_ecosystem_ids=[authorized_id],
            authorized_ecosystem_ids=[authorized_id],
        ),
        args={"ecosystem_ids": str(unauthorized_id)},
    )

    assert get_ecosystem_ids(request) == []
