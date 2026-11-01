"""ACT lifecycle tables, gate engine and transitions; see services/AGENTS.md "ACT lifecycle".

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
agreements). ``PROPOSAL_LIFECYCLE`` / ``AGREEMENT_LIFECYCLE`` say which moves
exist, which gate each needs and which the engine takes by itself;
``transition_proposal`` and ``advance_agreement`` apply them, minting the
browsable decision artifact when the process completes:

- proposal ratified  -> DecisionRecord(artifact_type="proposal")
- agreement active   -> DecisionRecord(artifact_type="commitment")

The engine never commits; callers own the transaction boundary.
"""

from __future__ import annotations

import datetime as _dt
import logging
import uuid
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Mapping

from sqlalchemy import func, select

from neos_agent.api.errors import ApiError
from neos_agent.api.policy import can_manage_proposal, is_steward_in
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


# ---------------------------------------------------------------------------
# Lifecycle tables
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Move:
    """One status change: `gate` must be met first; the engine takes `automatic` moves by itself.

    `steward_only` narrows who may make it by hand from the manage rule to stewards.
    """

    source: str
    target: str
    gate: str | None = None
    automatic: bool = False
    steward_only: bool = False


# State machine as data: every allowed move, its gate and whether it is automatic.
@dataclass(frozen=True)
class Lifecycle:
    """A record type's status graph; `withdrawn` is reachable from any status by a manual move."""

    moves: tuple[Move, ...]
    aliases: Mapping[str, str] = field(default_factory=dict)
    withdrawn: str | None = None

    def canonical(self, status: str) -> str:
        """The table's name for a stored status (legacy aliases resolved)."""
        return self.aliases.get(status, status)

    def manual_move(self, current: str, target: str) -> Move | None:
        """The move a caller may request from `current` to `target`, or None."""
        source = self.canonical(current)
        if self.withdrawn is not None and target == self.withdrawn:
            return Move(source, target)
        return next((move for move in self.moves if (move.source, move.target) == (source, target)), None)

    def manual_targets(self, current: str) -> list[str]:
        """Every status a caller may request from `current`, sorted."""
        source = self.canonical(current)
        targets = {move.target for move in self.moves if move.source == source}
        if self.withdrawn is not None:
            targets.add(self.withdrawn)
        return sorted(targets)

    def automatic_move(self, current: str) -> Move | None:
        """The move the engine takes from `current` once its gate is met, or None."""
        source = self.canonical(current)
        return next((move for move in self.moves if move.source == source and move.automatic), None)


PROPOSAL_LIFECYCLE = Lifecycle(
    moves=(
        Move("draft", "advice"),  # opening the process is always deliberate
        # Owner decision, not yet live: drop automatic=True (the proposer closes advice; deadline backstop later).
        Move("advice", "consent", gate="advice", automatic=True),
        Move("consent", "test", gate="consent", automatic=True),
        # Owner decision, not yet live: automatic=True -> steward_only=True (a steward confirms ratification).
        Move("test", "ratified", gate="test", automatic=True),
    ),
    aliases={"created": "draft"},  # legacy chat-assistant drafts
    withdrawn="withdrawn",
)

# Kept separate from proposals: agreements add review and sunset after activation.
AGREEMENT_LIFECYCLE = Lifecycle(
    moves=(
        Move("draft", "advice"),
        Move("advice", "consent", gate="advice", automatic=True),
        Move("consent", "test", gate="consent", automatic=True),
        Move("test", "active", gate="test", automatic=True),
        Move("active", "under_review"),
        Move("under_review", "sunset"),
        Move("under_review", "active", gate="test"),
        Move("sunset", "archived"),
    ),
)


# ---------------------------------------------------------------------------
# Outcomes, refusals and the transition hook
# ---------------------------------------------------------------------------


@dataclass
class ActOutcome:
    """What one ACT action did: the requested move, the automatic cascade, the artifact, the gates after."""

    status: str
    gates: dict
    moved: str | None = None
    auto_transitions: list[str] = field(default_factory=list)
    decision_record_id: str | None = None

    @property
    def transitions(self) -> list[str]:
        """Every applied move in order, the requested one first."""
        return ([self.moved] if self.moved else []) + self.auto_transitions

    def attach(self, payload: dict, *, gates: bool = False) -> dict:
        """Add `auto_transitions`, `decision_record_id` when one was minted, and `gates` when asked."""
        if gates:
            payload["gates"] = self.gates
        payload["auto_transitions"] = list(self.auto_transitions)
        if self.decision_record_id:
            payload["decision_record_id"] = self.decision_record_id
        return payload


class TransitionRefused(ApiError):
    """A requested ACT move the caller may not make, shaped as its REST refusal (403, 400 or 409)."""


MANAGE_DENIED = "Only the proposer or an ecosystem steward can change this proposal"
STEWARD_MOVE_DENIED = "Only an ecosystem steward can confirm this move"


@dataclass(frozen=True)
class Transition:
    """One applied move, as handed to on_transition listeners."""

    record: Proposal | Agreement
    source: str
    target: str
    automatic: bool
    actor: Member | None


TransitionListener = Callable[[object, Transition], Awaitable[None]]
_TRANSITION_LISTENERS: list[TransitionListener] = []


# Observer pattern: the one hook point for side effects of a move (nothing registers yet).
def on_transition(listener: TransitionListener) -> TransitionListener:
    """Run `listener(session, transition)` after every applied move, inside the caller's transaction."""
    _TRANSITION_LISTENERS.append(listener)
    return listener


# Assistant vocabulary -> engine vocabulary; the gate blocks only on "object".
_POSITION_ALIASES = {"objection": "object"}


def consent_position(raw: str | None) -> str:
    """A consent position in the engine's vocabulary (lower case, 'objection' -> 'object')."""
    position = (raw or "").strip().lower()
    return _POSITION_ALIASES.get(position, position)


# ---------------------------------------------------------------------------
# Transition engine
# ---------------------------------------------------------------------------

StageEntry = Callable[..., Awaitable[str | None]]
GateEvaluation = Callable[..., Awaitable[dict]]


async def _apply(session, record, move: Move, *, enter: StageEntry, actor: Member | None,
                 automatic: bool, evidence: str | None = None) -> str | None:
    """Enter `move.target`, then notify listeners; returns a minted decision record id."""
    source = record.status
    minted = await enter(session, record, move.target, actor=actor, automatic=automatic, evidence=evidence)
    for listener in list(_TRANSITION_LISTENERS):
        await listener(session, Transition(record, source, move.target, automatic, actor))
    return minted


async def _advance(session, record, lifecycle: Lifecycle, *, evaluate: GateEvaluation,
                   enter: StageEntry, actor: Member | None) -> ActOutcome:
    """Take every automatic move whose gate is met, re-evaluating the gates after each one."""
    gates = await evaluate(session, record)
    outcome = ActOutcome(status=record.status, gates=gates)
    while (move := lifecycle.automatic_move(record.status)) is not None:
        if move.gate is not None and not gates[move.gate]["met"]:
            break
        outcome.auto_transitions.append(f"{record.status}->{move.target}")
        minted = await _apply(session, record, move, enter=enter, actor=actor, automatic=True)
        outcome.decision_record_id = minted or outcome.decision_record_id
        gates = await evaluate(session, record)
    outcome.status, outcome.gates = record.status, gates
    if outcome.auto_transitions:
        logger.info("%s %s auto-advanced: %s", type(record).__name__, record.id, ", ".join(outcome.auto_transitions))
    return outcome


async def _enter_proposal_stage(session, proposal: Proposal, target: str, **_context) -> str | None:
    """Set the status; entering ratified mints the decision artifact (idempotent)."""
    proposal.status = target
    if target != "ratified":
        return None
    record = await record_proposal_decision(session, proposal)
    return str(record.id) if record else None


async def transition_proposal(session, proposal: Proposal, *, to: str | None = None,
                              caller: Member | None) -> ActOutcome:
    """Make the requested move (manage rule, table, gate), then every automatic move whose gate is met.

    `caller` is the acting member's row in the proposal's ecosystem, always resolved
    from the authenticated identity and never from a request field. The caller commits.
    """
    moved, minted = None, None
    if to is not None:
        if not can_manage_proposal(caller, proposal):
            raise TransitionRefused(403, MANAGE_DENIED)
        move = PROPOSAL_LIFECYCLE.manual_move(proposal.status, to)
        if move is None:
            raise TransitionRefused(
                400,
                f"Invalid transition from '{proposal.status}' to '{to}'",
                {"allowed": PROPOSAL_LIFECYCLE.manual_targets(proposal.status)},
            )
        if move.steward_only and not is_steward_in(caller, proposal.ecosystem_id):
            raise TransitionRefused(403, STEWARD_MOVE_DENIED)
        if move.gate is not None:
            gates = await proposal_gate_status(session, proposal)
            if not gates[move.gate]["met"]:
                raise TransitionRefused(
                    409,
                    f"The {move.gate} gate is not satisfied — the conditions declared in the ACT policy must be met first",
                    {"gates": gates},
                )
        moved = f"{proposal.status}->{to}"
        minted = await _apply(session, proposal, move, enter=_enter_proposal_stage, actor=caller, automatic=False)
    outcome = await _advance(
        session, proposal, PROPOSAL_LIFECYCLE,
        evaluate=proposal_gate_status, enter=_enter_proposal_stage, actor=caller,
    )
    outcome.moved = moved
    outcome.decision_record_id = outcome.decision_record_id or minted
    return outcome


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
    # Classified through consent_position, so a legacy spelling ("Objection") blocks like "object".
    active_positions = [p for p in participants if consent_position(p.position) not in _WITHDRAWN_POSITIONS]
    objections = [p for p in active_positions if consent_position(p.position) in _BLOCKING_POSITIONS]
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
        if consent_position(participant.position) in _WITHDRAWN_POSITIONS:
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


# Ceremony vocabulary per entered stage; these stages also need documented evidence when conducted by hand.
_CEREMONY_OUTCOME = {"advice": "opened", "consent": "opened", "test": "started", "active": "passed"}
EVIDENCED_CEREMONIES = frozenset(_CEREMONY_OUTCOME)
_AUTOMATIC_EVIDENCE = {
    "consent": "Auto-advanced: minimum advice rounds completed.",
    "test": "Auto-advanced: consent ceremony complete.",
    "active": "Auto-advanced: declared test cases evidenced.",
}


async def _enter_agreement_stage(session, agreement: Agreement, target: str, *, actor: Member | None,
                                 automatic: bool, evidence: str | None) -> str | None:
    """Set the status and record its ceremony; entering active mints the commitment artifact."""
    agreement.status = target
    session.add(AgreementCeremony(
        id=uuid.uuid4(),
        agreement_id=agreement.id,
        stage=target,
        completed_by_member_id=actor.id if actor is not None else None,
        outcome=_CEREMONY_OUTCOME.get(target, "completed"),
        evidence=_AUTOMATIC_EVIDENCE.get(target) if automatic else (evidence or None),
        completed_at=_utcnow(),
    ))
    if target != "active":
        return None
    if agreement.ratification_date is None:
        agreement.ratification_date = _dt.date.today()
    record = await record_agreement_commitment(session, agreement)
    return str(record.id) if record else None


async def apply_agreement_move(session, agreement: Agreement, move: Move, *, caller: Member,
                               evidence: str | None) -> str | None:
    """Enter one already-validated manual agreement move; returns a minted decision record id."""
    return await _apply(session, agreement, move, enter=_enter_agreement_stage, actor=caller,
                        automatic=False, evidence=evidence)


async def advance_agreement(session, agreement: Agreement, *, caller: Member | None) -> ActOutcome:
    """Every automatic agreement move whose gate is met; the caller snapshots, fingerprints and commits."""
    return await _advance(
        session, agreement, AGREEMENT_LIFECYCLE,
        evaluate=agreement_gate_status, enter=_enter_agreement_stage, actor=caller,
    )


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
