"""Regression coverage for enforceable, version-bound agreement consent."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from neos_agent.api.agreement_vocabulary import canonical_agreement_status, canonical_agreement_type
from neos_agent.api.agreements import _VALID_TRANSITIONS
from neos_agent.api.schemas.agreements import AgreementUpdateRequest
from neos_agent.db.models import Agreement, AgreementMemberConsent, AgreementRequirement, Member
from neos_agent.services.agreement_consent import (
    agreement_consent_summary,
    missing_agreement_consents,
    synchronize_agreement_requirements,
)


@pytest.mark.asyncio
async def test_member_consents_are_version_bound_and_gate_ecosystem_participation(seeded_db):
    agreement = await seeded_db.scalar(select(Agreement).where(Agreement.status == "active"))
    members = list((await seeded_db.execute(select(Member).where(
        Member.ecosystem_id == agreement.ecosystem_id
    ))).scalars().all())
    agreement.requires_explicit_consent = True
    agreement.prerequisite_scopes = ["ecosystem"]
    await synchronize_agreement_requirements(seeded_db, agreement)
    await seeded_db.commit()

    requirements = list((await seeded_db.execute(select(AgreementRequirement).where(
        AgreementRequirement.agreement_id == agreement.id
    ))).scalars().all())
    assert [requirement.target_kind for requirement in requirements] == ["ecosystem_membership"]
    assert await missing_agreement_consents(
        seeded_db, members[0].id, agreement.ecosystem_id, "ecosystem"
    ) == [agreement]

    now = datetime.now(UTC)
    for member in members:
        seeded_db.add(AgreementMemberConsent(
            agreement_id=agreement.id,
            member_id=member.id,
            agreement_version=agreement.version,
            attestation="I have read and explicitly consent.",
            attested_at=now,
        ))
    await seeded_db.commit()

    assert await missing_agreement_consents(
        seeded_db, members[0].id, agreement.ecosystem_id, "ecosystem"
    ) == []
    assert await agreement_consent_summary(seeded_db, agreement) == {
        "required": len(members), "consented": len(members), "outstanding": 0, "complete": True,
    }

    agreement.version = "1.1"
    assert await missing_agreement_consents(
        seeded_db, members[0].id, agreement.ecosystem_id, "ecosystem"
    ) == [agreement]


def test_agreement_vocabulary_and_lifecycle_cannot_bypass_ceremonies():
    assert canonical_agreement_type("constitutional") == "constitutional"
    assert canonical_agreement_type("universal_field") == "uaf"
    assert canonical_agreement_status("ratified") == "active"
    assert _VALID_TRANSITIONS["consent"] == {"test"}
    assert "status" not in AgreementUpdateRequest(status="active").model_dump(exclude_none=True)
