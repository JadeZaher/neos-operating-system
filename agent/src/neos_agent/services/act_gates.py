"""ACT gate engine: declared gates, evaluation, and automatic advancement.

Both proposals and agreements move through the ACT sequence
(draft -> advice -> consent -> test -> ratified/active). Each record declares
its own gate policy in ``act_policy``:

    {
        "min_advice_rounds": int,   # advice rounds required before consent
        "consent_required": bool,   # consent round required before test
        "consent_quorum": int|None, # minimum non-withdrawn positions (>=1 default)
        "test_cases": [str],        # named test cases that must show met evidence
    }

Gate status is computed from the live sub-records (advice logs, consent
records, test reports for proposals; ceremonies + member consents for
agreements). ``maybe_auto_advance_*`` moves the status forward while the
declared conditions are met, recording ceremonies for agreements and minting
the browsable decision artifact when the process completes:

- proposal ratified  -> DecisionRecord(artifact_type="proposal")
- agreement active   -> DecisionRecord(artifact_type="commitment")

The engine never commits; callers own the transaction boundary.
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid

from sqlalchemy import func, select

from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    Agreement,
    AgreementCeremony,
    AgreementMemberConsent,
    ConsentParticipant,
    ConsentRecord,
    DecisionParticipant,
    DecisionRecord,
    DecisionSemanticTag,
    Member,
    Proposal,
    TestReport,
    TestSuccessCriterion,
)
from neos_agent.services.agreement_consent import agreement_consent_summary

logger = logging.getLogger(__name__)

# Positions that do not block consent and do not count toward quorum.
_WITHDRAWN_POSITIONS = {"withdrawn"}
# Positions that block consent until integrated.
_BLOCKING_POSITIONS = {"object"}

DEFAULT_ACT_POLICY: dict = {
    "min_advice_rounds": 1,
    "consent_required": True,
    "consent_quorum": None,
    "test_cases": [],
}


def _utcnow() -> _dt.datetime:
    """Naive UTC — governance tables use TIMESTAMP WITHOUT TIME ZONE."""
    return _dt.datetime.now(_dt.UTC).replace(tzinfo=None)


def normalize_act_policy(raw: object) -> dict:
    """Merge a stored act_policy payload with defaults, tolerating junk."""
    policy = dict(DEFAULT_ACT_POLICY)
    if isinstance(raw, dict):
        rounds = raw.get("min_advice_rounds")
        if isinstance(rounds, int) and rounds >= 0:
            policy["min_advice_rounds"] = rounds
        if isinstance(raw.get("consent_required"), bool):
            policy["consent_required"] = raw["consent_required"]
        quorum = raw.get("consent_quorum")
        if isinstance(quorum, int) and quorum >= 1:
            policy["consent_quorum"] = quorum
        cases = raw.get("test_cases")
        if isinstance(cases, list):
            policy["test_cases"] = [str(c).strip() for c in cases if str(c).strip()]
    return policy


async def resolve_proposal_policy(session, proposal: Proposal) -> tuple[dict, str]:
    """Return the effective ACT policy and where it came from.

    The proposal's own act_policy wins; when undeclared (NULL), the gates
    are inherited from the governing agreement's act_policy; otherwise the
    engine defaults apply.
    """
    if proposal.act_policy is not None:
        return normalize_act_policy(proposal.act_policy), "proposal"
    governing_id = getattr(proposal, "governing_agreement_id", None)
    if governing_id:
        agreement = await session.scalar(select(Agreement).where(Agreement.id == governing_id))
        if agreement is not None:
            return normalize_act_policy(agreement.act_policy), "agreement"
    return normalize_act_policy(None), "default"


# ---------------------------------------------------------------------------
# Proposal gates
# ---------------------------------------------------------------------------

async def proposal_gate_status(session, proposal: Proposal) -> dict:
    """Evaluate the declared ACT gates for a proposal against live records."""
    policy, policy_source = await resolve_proposal_policy(session, proposal)

    # --- Advice gate: one AdviceLog = one completed advice round -----------
    rounds = int(await session.scalar(
        select(func.count(AdviceLog.id)).where(AdviceLog.proposal_id == proposal.id)
    ) or 0)
    latest_log = (await session.execute(
        select(AdviceLog)
        .where(AdviceLog.proposal_id == proposal.id)
        .order_by(AdviceLog.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    latest_entries = 0
    if latest_log is not None:
        latest_entries = int(await session.scalar(
            select(func.count(AdviceEntry.id)).where(AdviceEntry.advice_log_id == latest_log.id)
        ) or 0)
    min_rounds = policy["min_advice_rounds"]
    # A freshly opened empty round does not count until it carries an entry.
    effective_rounds = rounds if latest_entries > 0 or latest_log is None else rounds - 1
    advice_met = min_rounds == 0 or effective_rounds >= min_rounds

    # --- Consent gate: latest consent record positions ----------------------
    latest_consent = (await session.execute(
        select(ConsentRecord)
        .where(ConsentRecord.proposal_id == proposal.id)
        .order_by(ConsentRecord.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    participants: list[ConsentParticipant] = []
    if latest_consent is not None:
        participants = list((await session.execute(
            select(ConsentParticipant).where(ConsentParticipant.consent_record_id == latest_consent.id)
        )).scalars().all())
    active_positions = [p for p in participants if (p.position or "").lower() not in _WITHDRAWN_POSITIONS]
    objections = [p for p in active_positions if (p.position or "").lower() in _BLOCKING_POSITIONS]
    quorum = policy["consent_quorum"] or 1
    consent_met = (not policy["consent_required"]) or (
        latest_consent is not None
        and len(active_positions) >= quorum
        and not objections
    )

    # --- Test gate: declared cases must each show met evidence --------------
    declared_cases: list[str] = policy["test_cases"]
    reports = list((await session.execute(
        select(TestReport).where(TestReport.proposal_id == proposal.id)
    )).scalars().all())
    criteria = []
    if reports:
        criteria = list((await session.execute(
            select(TestSuccessCriterion).where(
                TestSuccessCriterion.test_report_id.in_([r.id for r in reports])
            )
        )).scalars().all())
    met_criteria = {(c.criterion or "").strip().lower() for c in criteria if c.met}
    if declared_cases:
        cases_met = [c for c in declared_cases if c.strip().lower() in met_criteria]
        cases_missing = [c for c in declared_cases if c.strip().lower() not in met_criteria]
        test_met = not cases_missing
    else:
        cases_met, cases_missing = [], []
        # No declared cases: one passed report is sufficient test evidence.
        test_met = any((r.outcome or "").lower() == "passed" for r in reports)

    gates = {
        "policy": policy,
        "policy_source": policy_source,
        "advice": {
            "met": advice_met,
            "rounds": effective_rounds,
            "required_rounds": min_rounds,
        },
        "consent": {
            "met": consent_met,
            "required": policy["consent_required"],
            "positions": len(active_positions),
            "quorum": quorum if policy["consent_required"] else None,
            "open_objections": len(objections),
        },
        "test": {
            "met": test_met,
            "declared_cases": declared_cases,
            "cases_met": cases_met,
            "cases_missing": cases_missing,
            "reports": len(reports),
        },
    }
    gates["complete"] = advice_met and consent_met and test_met
    return gates


async def maybe_auto_advance_proposal(session, proposal: Proposal) -> dict:
    """Advance a proposal through ACT while its declared gates are satisfied.

    Mints the decision artifact on ratification. Returns the gate status plus
    the transitions applied (empty when nothing moved).
    """
    gates = await proposal_gate_status(session, proposal)
    transitions: list[str] = []
    decision_id: uuid.UUID | None = None

    while True:
        if proposal.status == "advice" and gates["advice"]["met"]:
            proposal.status = "consent"
            transitions.append("advice->consent")
        elif proposal.status == "consent" and gates["consent"]["met"]:
            proposal.status = "test"
            transitions.append("consent->test")
        elif proposal.status == "test" and gates["test"]["met"]:
            proposal.status = "ratified"
            transitions.append("test->ratified")
            record = await record_proposal_decision(session, proposal)
            decision_id = record.id if record else None
        else:
            break

    if transitions:
        logger.info("Proposal %s auto-advanced: %s", proposal.id, ", ".join(transitions))
    return {
        "status": proposal.status,
        "transitions": transitions,
        "decision_record_id": str(decision_id) if decision_id else None,
        "gates": gates,
    }


async def record_proposal_decision(session, proposal: Proposal) -> DecisionRecord | None:
    """Mint the browsable decision artifact for a ratified proposal.

    Idempotent: one artifact per proposal. Consent participants become
    decision participants — the recorded commitments by members to the
    proposal.
    """
    existing = await session.scalar(
        select(DecisionRecord.id).where(DecisionRecord.source_proposal_id == proposal.id)
    )
    if existing:
        return await session.scalar(select(DecisionRecord).where(DecisionRecord.id == existing))

    latest_consent = (await session.execute(
        select(ConsentRecord)
        .where(ConsentRecord.proposal_id == proposal.id)
        .order_by(ConsentRecord.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()
    participants: list[ConsentParticipant] = []
    if latest_consent is not None:
        participants = list((await session.execute(
            select(ConsentParticipant).where(ConsentParticipant.consent_record_id == latest_consent.id)
        )).scalars().all())

    advice_rounds = int(await session.scalar(
        select(func.count(AdviceLog.id)).where(AdviceLog.proposal_id == proposal.id)
    ) or 0)
    report_count = int(await session.scalar(
        select(func.count(TestReport.id)).where(TestReport.proposal_id == proposal.id)
    ) or 0)
    policy, policy_source = await resolve_proposal_policy(session, proposal)
    source_phrase = {
        "proposal": "declared at the proposal level",
        "agreement": "inherited from the governing agreement",
        "default": "the ecosystem default",
    }[policy_source]

    record = DecisionRecord(
        id=uuid.uuid4(),
        ecosystem_id=proposal.ecosystem_id,
        shared_ecosystem_ids=proposal.shared_ecosystem_ids,
        record_id=f"DEC-{proposal.proposal_id}",
        date=_dt.date.today(),
        holding=(
            f"{proposal.title} — ratified after completing the ACT process. "
            f"{(proposal.proposed_change or '').strip()}".strip()
        ),
        ratio_decidendi=proposal.rationale,
        deliberation_summary=(
            f"ACT process completed under the gate policy {source_phrase} "
            f"(min advice rounds: {policy['min_advice_rounds']}, consent required: "
            f"{policy['consent_required']}, test cases: {len(policy['test_cases'])}). "
            f"{advice_rounds} advice round(s), {len(participants)} consent position(s), "
            f"{report_count} test report(s). Status advanced automatically as each "
            f"gate's conditions were met."
        ),
        source_skill="act-process",
        artifact_type="proposal",
        artifact_reference=proposal.proposal_id,
        source_proposal_id=proposal.id,
        domain=proposal.affected_domain,
        precedent_level="binding",
        status="active",
        recorder=proposal.proposer,
        recorder_role="proposer",
    )
    session.add(record)
    await session.flush()

    for participant in participants:
        if (participant.position or "").lower() in _WITHDRAWN_POSITIONS:
            continue
        session.add(DecisionParticipant(
            id=uuid.uuid4(),
            decision_record_id=record.id,
            name=participant.name,
            role=None,
            position=participant.position,
        ))
    session.add(DecisionSemanticTag(
        id=uuid.uuid4(),
        decision_record_id=record.id,
        topic={"category": proposal.affected_domain} if proposal.affected_domain else None,
        affected_parties=proposal.impacted_parties,
        ecosystem_scope="internal",
        urgency_at_time=proposal.urgency,
    ))
    await session.flush()
    logger.info("Minted decision artifact %s for proposal %s", record.record_id, proposal.id)
    return record


# ---------------------------------------------------------------------------
# Agreement gates
# ---------------------------------------------------------------------------

async def agreement_gate_status(session, agreement: Agreement) -> dict:
    """Evaluate the declared ACT gates for an agreement against live records."""
    policy = normalize_act_policy(agreement.act_policy)
    if agreement.requires_explicit_consent is False:
        policy["consent_required"] = False

    advice_rounds = int(await session.scalar(
        select(func.count(AgreementCeremony.id)).where(
            AgreementCeremony.agreement_id == agreement.id,
            AgreementCeremony.stage == "advice",
            AgreementCeremony.outcome == "round",
        )
    ) or 0)
    min_rounds = policy["min_advice_rounds"]
    advice_met = min_rounds == 0 or advice_rounds >= min_rounds

    summary = await agreement_consent_summary(session, agreement)
    consent_required = policy["consent_required"]
    quorum = policy["consent_quorum"]
    consent_met = (not consent_required) or (
        summary["complete"] and (quorum is None or summary["consented"] >= quorum)
    )

    declared_cases: list[str] = policy["test_cases"]
    test_evidence = int(await session.scalar(
        select(func.count(AgreementCeremony.id)).where(
            AgreementCeremony.agreement_id == agreement.id,
            AgreementCeremony.stage == "test",
            AgreementCeremony.outcome == "evidence",
        )
    ) or 0)
    required_evidence = max(1, len(declared_cases))
    test_met = test_evidence >= required_evidence

    gates = {
        "policy": policy,
        "advice": {"met": advice_met, "rounds": advice_rounds, "required_rounds": min_rounds},
        "consent": {
            "met": consent_met,
            "required": consent_required,
            "consented": summary["consented"],
            "outstanding": summary["outstanding"],
            "quorum": quorum,
        },
        "test": {
            "met": test_met,
            "declared_cases": declared_cases,
            "evidence": test_evidence,
            "required_evidence": required_evidence,
        },
    }
    gates["complete"] = advice_met and consent_met and test_met
    return gates


async def maybe_auto_advance_agreement(
    session,
    agreement: Agreement,
    *,
    actor_member_id: uuid.UUID | None = None,
) -> dict:
    """Advance an agreement through ACT while its declared gates are satisfied.

    Each automatic transition is recorded as a governance ceremony with no
    conducting member (system-recorded). Activation mints the commitment
    decision artifact. The caller owns commit, version snapshots, and
    fingerprint regeneration.
    """
    gates = await agreement_gate_status(session, agreement)
    transitions: list[str] = []
    decision_id: uuid.UUID | None = None
    outcome_by_stage = {"consent": "opened", "test": "started", "active": "passed"}
    evidence_by_stage = {
        "consent": "Auto-advanced: minimum advice rounds completed.",
        "test": "Auto-advanced: consent ceremony complete.",
        "active": "Auto-advanced: declared test cases evidenced.",
    }

    while True:
        if agreement.status == "advice" and gates["advice"]["met"]:
            new_status = "consent"
        elif agreement.status == "consent" and gates["consent"]["met"]:
            new_status = "test"
        elif agreement.status == "test" and gates["test"]["met"]:
            new_status = "active"
        else:
            break

        transitions.append(f"{agreement.status}->{new_status}")
        agreement.status = new_status
        session.add(AgreementCeremony(
            id=uuid.uuid4(),
            agreement_id=agreement.id,
            stage=new_status,
            completed_by_member_id=actor_member_id,
            outcome=outcome_by_stage.get(new_status, "completed"),
            evidence=evidence_by_stage.get(new_status),
            completed_at=_utcnow(),
        ))
        if new_status == "active":
            if agreement.ratification_date is None:
                agreement.ratification_date = _dt.date.today()
            record = await record_agreement_commitment(session, agreement)
            decision_id = record.id if record else None
        # Re-evaluate against the new stage before any further advance.
        gates = await agreement_gate_status(session, agreement)

    if transitions:
        logger.info("Agreement %s auto-advanced: %s", agreement.id, ", ".join(transitions))
    return {
        "status": agreement.status,
        "transitions": transitions,
        "decision_record_id": str(decision_id) if decision_id else None,
        "gates": gates,
    }


async def record_agreement_commitment(session, agreement: Agreement) -> DecisionRecord | None:
    """Mint the commitment decision artifact produced by an activated agreement.

    Idempotent: one commitment artifact per agreement. Members who attested
    to the ratified version become decision participants — the artifact is
    the browsable record of their commitment to the agreement.
    """
    existing = await session.scalar(
        select(DecisionRecord.id).where(DecisionRecord.source_agreement_id == agreement.id)
    )
    if existing:
        return await session.scalar(select(DecisionRecord).where(DecisionRecord.id == existing))

    consents = (await session.execute(
        select(AgreementMemberConsent, Member)
        .join(Member, Member.id == AgreementMemberConsent.member_id)
        .where(
            AgreementMemberConsent.agreement_id == agreement.id,
            AgreementMemberConsent.agreement_version == agreement.version,
            AgreementMemberConsent.withdrawn_at.is_(None),
        )
    )).all()
    policy = normalize_act_policy(agreement.act_policy)

    record = DecisionRecord(
        id=uuid.uuid4(),
        ecosystem_id=agreement.ecosystem_id,
        shared_ecosystem_ids=agreement.shared_ecosystem_ids,
        record_id=f"DEC-{agreement.agreement_id}",
        date=agreement.ratification_date or _dt.date.today(),
        holding=(
            f"The members of this ecosystem commit to \"{agreement.title}\" "
            f"(v{agreement.version}). {(agreement.text or '').strip()}".strip()
        ),
        ratio_decidendi=(
            "The agreement completed the ACT process: advice rounds, member "
            "consent to the ratified text, and declared test evidence were all "
            "satisfied under the gate policy declared at the agreement level."
        ),
        deliberation_summary=(
            f"ACT gates declared by the agreement (min advice rounds: "
            f"{policy['min_advice_rounds']}, consent required: "
            f"{policy['consent_required']}, test cases: {len(policy['test_cases'])}). "
            f"{len(consents)} member(s) attested to version {agreement.version}. "
            f"This record is the standing commitment artifact for the agreement."
        ),
        source_skill="act-process",
        artifact_type="commitment",
        artifact_reference=agreement.agreement_id,
        source_agreement_id=agreement.id,
        domain=agreement.domain,
        precedent_level="binding",
        status="active",
        recorder=agreement.proposer,
        recorder_role="proposer",
        review_date=agreement.review_date,
    )
    session.add(record)
    await session.flush()

    for consent, member_row in consents:
        session.add(DecisionParticipant(
            id=uuid.uuid4(),
            decision_record_id=record.id,
            name=member_row.display_name,
            role=member_row.role,
            position="consent",
        ))
    session.add(DecisionSemanticTag(
        id=uuid.uuid4(),
        decision_record_id=record.id,
        topic={"category": agreement.domain, "agreement_type": agreement.type},
        affected_parties=agreement.affected_parties,
        ecosystem_scope="internal",
        urgency_at_time="standard",
    ))
    await session.flush()
    logger.info("Minted commitment artifact %s for agreement %s", record.record_id, agreement.id)
    return record
