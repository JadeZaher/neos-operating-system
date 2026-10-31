"""Detail serializers expose shared_ecosystem_ids; fixtures are transient ORM rows so new model fields never break them."""
import uuid
from datetime import UTC, datetime

import pytest

import neos_agent.db.course_models  # noqa: F401  registers tables the models' relationships reference
from neos_agent.api.agreements import _agreement_to_detail
from neos_agent.api.domains import _domain_to_detail
from neos_agent.api.members import _member_to_detail
from neos_agent.api.proposals import _proposal_to_detail
from neos_agent.db.models import Agreement, Domain, Member, Proposal


PRIMARY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SHARED_IDS = [
    uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
]
NOW = datetime(2026, 7, 13, tzinfo=UTC)


def _shared_row(model, **fields):
    """A transient row shared with SHARED_IDS; only fields the database would default on flush are spelled out."""
    return model(
        id=uuid.uuid4(), ecosystem_id=PRIMARY_ID, shared_ecosystem_ids=[str(value) for value in SHARED_IDS],
        created_at=NOW, updated_at=NOW, **fields,
    )


def _serialized_shared_ids(payload) -> list[str]:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    return payload["shared_ecosystem_ids"]


@pytest.mark.parametrize(
    "serialize, row",
    [
        (_agreement_to_detail, lambda: _shared_row(
            Agreement, agreement_id="AGR-TEST", type="policy", title="Shared agreement", version="1.0",
            status="draft", hierarchy_level="domain", requires_explicit_consent=False, alignment_points=0)),
        (_domain_to_detail, lambda: _shared_row(Domain, domain_id="DOM-TEST", version="1.0", status="active")),
        (_member_to_detail, lambda: _shared_row(
            Member, member_id="MEM-TEST", display_name="Shared member", role="user", current_status="active")),
        (_proposal_to_detail, lambda: _shared_row(
            Proposal, proposal_id="PROP-TEST", type="policy", title="Shared proposal", version="1.0", status="draft")),
    ],
    ids=["agreement", "domain", "member", "proposal"],
)
def test_detail_exposes_shared_ecosystem_ids(serialize, row):
    assert _serialized_shared_ids(serialize(row())) == [str(value) for value in SHARED_IDS]
