"""Server-side evaluation of agreement consent and participation gates."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from neos_agent.db.models import Agreement, AgreementMemberConsent, AgreementRequirement, Member


_SCOPE_TO_TARGET = {
    "ecosystem": "ecosystem_membership",
    "domain": "domain_participation",
    "collaboration": "collaboration",
}
_PARTICIPATING_MEMBER_STATUSES = {"active", "steward", "co_creator", "builder", "townhall", "pending_consent"}


def _scope_values(value: object) -> set[str]:
    """Return valid prerequisite scopes from potentially legacy JSON data."""
    return {item for item in value if item in _SCOPE_TO_TARGET} if isinstance(value, list) else set()


async def agreement_consent_summary(session, agreement: Agreement) -> dict[str, int | bool]:
    """Count current participating members who attested to this agreement version."""
    participant_ids = list((await session.execute(
        select(Member.id).where(
            Member.ecosystem_id == agreement.ecosystem_id,
            Member.current_status.in_(_PARTICIPATING_MEMBER_STATUSES),
        )
    )).scalars().all())
    if not participant_ids:
        return {"required": 0, "consented": 0, "outstanding": 0, "complete": True}

    consented = await session.scalar(
        select(func.count(AgreementMemberConsent.id))
        .where(
            AgreementMemberConsent.agreement_id == agreement.id,
            AgreementMemberConsent.agreement_version == agreement.version,
            AgreementMemberConsent.member_id.in_(participant_ids),
            AgreementMemberConsent.withdrawn_at.is_(None),
        )
    )
    count = int(consented or 0)
    required = len(participant_ids)
    return {
        "required": required,
        "consented": count,
        "outstanding": required - count,
        "complete": count == required,
    }


async def required_agreements_for_scope(session, ecosystem_id: uuid.UUID, scope: str, domain_id: uuid.UUID | None = None) -> list[Agreement]:
    """Return active agreements configured as gates for a participation scope."""
    target_kind = _SCOPE_TO_TARGET[scope]
    requirements = (await session.execute(
        select(AgreementRequirement, Agreement)
        .join(Agreement, Agreement.id == AgreementRequirement.agreement_id)
        .where(
            Agreement.ecosystem_id == ecosystem_id,
            Agreement.status == "active",
            Agreement.requires_explicit_consent.is_(True),
            AgreementRequirement.target_kind == target_kind,
            AgreementRequirement.is_active.is_(True),
        )
    )).all()
    return [
        agreement for requirement, agreement in requirements
        if requirement.target_id is None or requirement.target_id == domain_id
    ]


async def missing_agreement_consents(session, member_id: uuid.UUID, ecosystem_id: uuid.UUID, scope: str, domain_id: uuid.UUID | None = None) -> list[Agreement]:
    """Return prerequisite agreements the named member has not currently accepted."""
    agreements = await required_agreements_for_scope(session, ecosystem_id, scope, domain_id)
    if not agreements:
        return []
    consents = (await session.execute(
        select(AgreementMemberConsent.agreement_id, AgreementMemberConsent.agreement_version)
        .where(
            AgreementMemberConsent.member_id == member_id,
            AgreementMemberConsent.withdrawn_at.is_(None),
            AgreementMemberConsent.agreement_id.in_([agreement.id for agreement in agreements]),
        )
    )).all()
    accepted = {(agreement_id, version) for agreement_id, version in consents}
    return [agreement for agreement in agreements if (agreement.id, agreement.version) not in accepted]


async def synchronize_agreement_requirements(session, agreement: Agreement) -> None:
    """Keep normalized participation gates in lock-step with agreement policy."""
    scopes = _scope_values(agreement.prerequisite_scopes)
    target_ids = []
    for raw_id in getattr(agreement, "prerequisite_domain_ids", None) or []:
        try:
            target_ids.append(uuid.UUID(str(raw_id)))
        except (TypeError, ValueError):
            continue
    existing = (await session.execute(
        select(AgreementRequirement).where(AgreementRequirement.agreement_id == agreement.id)
    )).scalars().all()
    by_target = {(requirement.target_kind, requirement.target_id): requirement for requirement in existing}
    for scope, target_kind in _SCOPE_TO_TARGET.items():
        desired_ids = [None] if scope == "ecosystem" or not target_ids else target_ids
        desired = {(target_kind, target_id) for target_id in desired_ids} if scope in scopes else set()
        for key, requirement in by_target.items():
            if key[0] == target_kind:
                requirement.is_active = key in desired
        for _, target_id in desired:
            requirement = by_target.get((target_kind, target_id))
            if requirement is None:
                session.add(AgreementRequirement(
                    id=uuid.uuid4(), agreement_id=agreement.id, target_kind=target_kind,
                    target_id=target_id,
                    enforcement={
                        "ecosystem": "block_join",
                        "domain": "block_participation",
                        "collaboration": "block_proposal",
                    }[scope],
                    is_active=True,
                ))
            else:
                requirement.is_active = True
