import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from neos_agent.api.agreements import _agreement_to_detail
from neos_agent.api.domains import _domain_to_detail
from neos_agent.api.members import _member_to_detail
from neos_agent.api.proposals import _proposal_to_detail


PRIMARY_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
SHARED_IDS = [
    uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
]
NOW = datetime(2026, 7, 13, tzinfo=UTC)


def _serialized_shared_ids(payload) -> list[str]:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    return payload["shared_ecosystem_ids"]


def test_agreement_detail_exposes_shared_ecosystem_ids():
    agreement = SimpleNamespace(
        id=uuid.uuid4(), agreement_id="AGR-TEST", ecosystem_id=PRIMARY_ID,
        shared_ecosystem_ids=[str(value) for value in SHARED_IDS], type="policy",
        title="Shared agreement", version="1.0", status="draft", proposer=None,
        domain=None, hierarchy_level="domain", review_date=None, sunset_date=None,
        created_at=NOW, text=None, affected_parties=None, parent_agreement_id=None,
        ratification_date=None, created_date=None, updated_at=NOW,
        ratification_records=[], version_fingerprint=None,
    )

    assert _serialized_shared_ids(_agreement_to_detail(agreement)) == [
        str(value) for value in SHARED_IDS
    ]


def test_member_detail_exposes_shared_ecosystem_ids():
    member = SimpleNamespace(
        id=uuid.uuid4(), member_id="MEM-TEST", ecosystem_id=PRIMARY_ID,
        shared_ecosystem_ids=[str(value) for value in SHARED_IDS],
        display_name="Shared member", current_status="active", profile=None,
        onboarding_status=None, created_at=NOW, skills_offered=None,
        skills_needed=None, interests=None, kyc_status=None,
        last_governance_activity_date=None, notes=None, privacy=None, updated_at=NOW,
    )

    assert _serialized_shared_ids(_member_to_detail(member)) == [
        str(value) for value in SHARED_IDS
    ]


def test_proposal_detail_exposes_shared_ecosystem_ids():
    proposal = SimpleNamespace(
        id=uuid.uuid4(), proposal_id="PROP-TEST", ecosystem_id=PRIMARY_ID,
        shared_ecosystem_ids=[str(value) for value in SHARED_IDS], type="policy",
        decision_type=None, title="Shared proposal", version="1.0", status="draft",
        proposer=None, affected_domain=None, urgency=None, created_at=NOW,
        co_sponsors=None, impacted_parties=None, proposed_change=None, rationale=None,
        created_date=None, advice_deadline=None, consent_deadline=None,
        test_duration=None, updated_at=NOW, advice_logs=[], consent_records=[],
        test_reports=[],
    )

    assert _serialized_shared_ids(_proposal_to_detail(proposal)) == [
        str(value) for value in SHARED_IDS
    ]


def test_domain_detail_exposes_shared_ecosystem_ids():
    domain = SimpleNamespace(
        id=uuid.uuid4(), domain_id="DOM-TEST", ecosystem_id=PRIMARY_ID,
        shared_ecosystem_ids=[str(value) for value in SHARED_IDS], version="1.0",
        status="active", purpose=None, current_steward=None, parent_domain_id=None,
        created_at=NOW, version_fingerprint=None, steward_id=None, created_by=None,
        metric_definitions=None, elements=None, updated_at=NOW,
        domain_elements=[], domain_metrics=[],
    )

    assert _serialized_shared_ids(_domain_to_detail(domain)) == [
        str(value) for value in SHARED_IDS
    ]
