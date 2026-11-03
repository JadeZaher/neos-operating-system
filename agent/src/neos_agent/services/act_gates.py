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
import re
import uuid
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Mapping

from sqlalchemy import func, select

from neos_agent.api.errors import ApiError
from neos_agent.api.policy import (
    ROLE_RANK,
    can_close_advice,
    can_confirm_ratification,
    can_manage_proposal,
    can_participate,
    is_consent_pending_in,
    is_proposal_author,
    is_steward_in,
)
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
    Ecosystem,
    Member,
    Proposal,
    TestReport,
    TestSuccessCriterion,
)
from neos_agent.services import dates
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

    `steward_only` narrows who may make it by hand to a steward who is not the author
    (`policy.can_confirm_ratification`);
    `proposer_until_deadline` keeps it the author's until the advice deadline has passed (`policy.can_close_advice`);
    `note_required` refuses it without a written reason (sending a proposal back).
    """

    source: str
    target: str
    gate: str | None = None
    automatic: bool = False
    steward_only: bool = False
    proposer_until_deadline: bool = False
    note_required: bool = False


# State machine as data: every allowed move, its gate and whether it is automatic.
@dataclass(frozen=True)
class Lifecycle:
    """A record type's status graph; `withdrawn` is reachable by hand from any status not in `terminal`."""

    moves: tuple[Move, ...]
    aliases: Mapping[str, str] = field(default_factory=dict)
    withdrawn: str | None = None
    terminal: frozenset[str] = frozenset()

    def canonical(self, status: str) -> str:
        """The table's name for a stored status (legacy aliases resolved)."""
        return self.aliases.get(status, status)

    def manual_move(self, current: str, target: str) -> Move | None:
        """The move a caller may request from `current` to `target`, or None."""
        source = self.canonical(current)
        if self.withdrawn is not None and target == self.withdrawn:
            return None if source in self.terminal else Move(source, target)
        return next((move for move in self.moves if (move.source, move.target) == (source, target)), None)

    def manual_targets(self, current: str) -> list[str]:
        """Every status a caller may request from `current`, sorted."""
        source = self.canonical(current)
        targets = {move.target for move in self.moves if move.source == source}
        if self.withdrawn is not None and source not in self.terminal:
            targets.add(self.withdrawn)
        return sorted(targets)

    def automatic_move(self, current: str) -> Move | None:
        """The move the engine takes from `current` once its gate is met, or None."""
        source = self.canonical(current)
        return next((move for move in self.moves if move.source == source and move.automatic), None)


PROPOSAL_LIFECYCLE = Lifecycle(
    moves=(
        Move("draft", "advice"),  # opening the process is always deliberate
        # Owner decisions 2026-10-31 and 2026-11-01: the proposer closes advice; another steward only after its deadline.
        Move("advice", "consent", gate="advice", proposer_until_deadline=True),
        Move("consent", "test", gate="consent", automatic=True),
        Move("consent", "advice", note_required=True),  # send back for revision
        Move("test", "advice", note_required=True),  # send back for revision
        Move("test", "ratified", gate="test", steward_only=True),  # owner decision 2026-10-31: a steward confirms
    ),
    aliases={"created": "draft"},  # legacy chat-assistant drafts
    withdrawn="withdrawn",
    terminal=frozenset({"ratified", "withdrawn"}),
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
        Move("under_review", "active"),  # FX-Maint: a review ends on its findings, never a re-test
        Move("sunset", "archived", gate="sunset_ended"),  # FX-Maint: only once the 60-day notice has run
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
NEEDS_ANOTHER_STEWARD = (
    "Another steward needs to confirm this: you wrote the proposal, and ratification is never self-certified. "
    "If you are the only steward, give another member the moderator role first."
)
NOTE_REQUIRED = "Say what will change: sending a proposal back for revision needs a note"
# Machine code for a steward closing someone else's advice before its deadline (owner decision 2026-11-01).
ADVICE_CLOSE_PROPOSER_ONLY = "ADVICE_CLOSE_PROPOSER_ONLY"
PROPOSER_CLOSES_ADVICE = "The proposer closes advice."


def advice_close_refusal(proposal: Proposal) -> str:
    """Plain words for a steward refused the advice close: when they may close it, or that only the proposer can."""
    if proposal.advice_deadline is None:
        return f"{PROPOSER_CLOSES_ADVICE} This proposal has no advice deadline, so only they can close it."
    return (f"{PROPOSER_CLOSES_ADVICE} You can close it after the advice deadline "
            f"({proposal.advice_deadline.isoformat()}) if they haven't.")


def move_authority_refusal(proposal: Proposal, move: Move, caller: Member | None, *,
                           today: _dt.date) -> TransitionRefused | None:
    """Who may make `move` by hand, past the manage rule: steward-only moves and the proposer's advice close."""
    if move.steward_only and not can_confirm_ratification(caller, proposal):
        if is_steward_in(caller, proposal.ecosystem_id):  # a steward who wrote it
            return TransitionRefused(403, NEEDS_ANOTHER_STEWARD, {"code": "NEEDS_ANOTHER_STEWARD"})
        return TransitionRefused(403, STEWARD_MOVE_DENIED)
    if move.proposer_until_deadline and not can_close_advice(caller, proposal, today):
        deadline = proposal.advice_deadline.isoformat() if proposal.advice_deadline else None
        return TransitionRefused(403, advice_close_refusal(proposal),
                                 {"code": ADVICE_CLOSE_PROPOSER_ONLY, "advice_deadline": deadline})
    return None

# Machine code for a membership still waiting on the consent gate (owner rule: a pending newcomer reads, never acts).
CONSENT_PENDING = "CONSENT_PENDING"
INACTIVE_PARTICIPANT = "Only an active member of this proposal's ecosystem can take part in it"


def consent_pending_message(ecosystem_name: str | None) -> str:
    """Plain words for a pending_consent caller who tried to act (REST, MCP and the assistant say the same)."""
    where = ecosystem_name or "this ecosystem"
    return (f"Your membership in {where} is still waiting for your consent to its agreements. Until you give it, "
            f"you can read {where}'s proposals but not give advice, record a position, file a test report or "
            f"write a proposal. Consent to its agreements to finish joining.")


async def refuse_pending_member(session, member: Member | None, ecosystem_id: uuid.UUID | None) -> None:
    """403 CONSENT_PENDING when `member` is a pending_consent row in `ecosystem_id`, naming the ecosystem."""
    if not is_consent_pending_in(member, ecosystem_id):
        return
    name = await session.scalar(select(Ecosystem.name).where(Ecosystem.id == ecosystem_id))
    raise TransitionRefused(403, consent_pending_message(name), {"code": CONSENT_PENDING})


async def require_participant(session, proposal: Proposal, member: Member | None, *, row_optional: bool = False) -> None:
    """The participation rule for advice, positions and test reports: an ACTIVE row in the proposal's ecosystem.

    `row_optional` keeps the shared-ecosystem path (a caller with no row there advises or reports as their
    session member, as before); a row that exists must be active either way.
    """
    if member is None and row_optional:
        return
    await refuse_pending_member(session, member, proposal.ecosystem_id)
    if not can_participate(member, proposal):
        raise TransitionRefused(403, INACTIVE_PARTICIPANT if row_optional else PARTICIPATE_DENIED)


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


def _bump_minor(version: str | None) -> str:
    """'1.0' -> '1.1'; anything unparseable gains a '.1'."""
    major, _, minor = (version or "1.0").partition(".")
    return f"{major}.{int(minor) + 1}" if minor.isdigit() else f"{version or '1'}.1"


async def created_after_newest(session, model, proposal_id) -> dict:
    """`created_at` strictly after the proposal's newest `model` row, else {} (server default).

    "Latest round/record" is ordered by created_at, which SQLite stores to the second; this keeps
    it unambiguous without mixing the Python clock into server timestamps.
    """
    newest = await session.scalar(select(func.max(model.created_at)).where(model.proposal_id == proposal_id))
    return {} if newest is None else {"created_at": newest + _dt.timedelta(microseconds=1)}


# One wording for a revision round's summary, written by _open_revision and read back by revision_round.
_REVISION_SUMMARY = re.compile(r"^Sent back from (?P<source>\w+) for revision by (?P<by>.+) \(v(?P<version>[^)]+)\)$")


def revision_round(log: AdviceLog | None) -> dict | None:
    """A send-back round as {by, source, version, note}; None for an ordinary advice round."""
    note = (getattr(log, "proposer_modifications", None) or "").strip()
    if log is None or not note:
        return None
    parsed = _REVISION_SUMMARY.match((log.summary or "").strip())
    return {
        "by": parsed["by"] if parsed else None,
        "source": parsed["source"] if parsed else None,
        "version": parsed["version"] if parsed else None,
        "note": note,
    }


async def latest_revision_log(session, proposal: Proposal) -> AdviceLog | None:
    """The newest advice round opened by a send-back (it carries the note), or None."""
    return (await session.execute(
        select(AdviceLog)
        .where(AdviceLog.proposal_id == proposal.id, AdviceLog.proposer_modifications.is_not(None),
               AdviceLog.proposer_modifications != "")
        .order_by(AdviceLog.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()


async def reports_since_revision(session, proposal: Proposal) -> list:
    """Test reports on the current version (filed at or after the latest send-back) as rows of
    (id, outcome, reporter_member_id, created_at); see services/AGENTS.md "Send back for revision"."""
    rows = (await session.execute(
        select(TestReport.id, TestReport.outcome, TestReport.reporter_member_id, TestReport.created_at)
        .where(TestReport.proposal_id == proposal.id)
    )).all()
    revision = await latest_revision_log(session, proposal)
    since = revision.updated_at if revision is not None else None
    # Compared in Python: SQLite stores server and client timestamps in different text forms.
    return [row for row in rows if since is None or (row.created_at is not None and row.created_at >= since)]


async def _open_revision(session, proposal: Proposal, source: str, *, actor: Member | None, note: str | None) -> None:
    """Send-back side effects: a minor version, a fresh advice round carrying the note, a fresh consent record."""
    proposal.version = _bump_minor(proposal.version)
    who = actor.display_name if actor is not None else "the proposer"
    proposal.advice_deadline = None  # a revision round starts open-ended; the proposer sets its own deadline
    # proposer_modifications marks a revision round: the advice gate counts rounds from the latest one.
    session.add(AdviceLog(
        id=uuid.uuid4(), proposal_id=proposal.id, advice_window_start=_dt.date.today(),
        advice_window_end=None, urgency=proposal.urgency,
        summary=f"Sent back from {source} for revision by {who} (v{proposal.version})",
        proposer_modifications=note, **await created_after_newest(session, AdviceLog, proposal.id),
    ))
    # A new record keeps earlier positions as history; the gate reads only the latest record.
    session.add(ConsentRecord(
        id=uuid.uuid4(), proposal_id=proposal.id, consent_mode=consent_mode(proposal),
        date=_dt.date.today(), quorum_met=False, outcome="pending",
        **await created_after_newest(session, ConsentRecord, proposal.id),
    ))
    await session.flush()


async def _enter_proposal_stage(session, proposal: Proposal, target: str, *, actor: Member | None = None,
                                evidence: str | None = None, **_context) -> str | None:
    """Set the status; a send-back opens a revision; entering ratified captures the text and mints the decision artifact."""
    source = PROPOSAL_LIFECYCLE.canonical(proposal.status)
    proposal.status = target
    from neos_agent.services.engagement_events import source_event
    await source_event(session, proposal, kind="proposal", family="governance", action=target,
                       actor_user_id=actor.user_id if actor is not None else None)
    if target == "advice" and source in {"consent", "test"}:
        await _open_revision(session, proposal, source, actor=actor, note=evidence)
        return None
    if target != "ratified":
        return None
    # The text the steward confirmed; registering copies this, never the live proposed_change.
    proposal.ratified_text = (proposal.proposed_change or "").strip() or None
    record = await record_proposal_decision(session, proposal, confirmed_by=actor)
    return str(record.id) if record else None


async def transition_proposal(session, proposal: Proposal, *, to: str | None = None,
                              caller: Member | None, note: str | None = None) -> ActOutcome:
    """Make the requested move (manage rule, table, steward, note, gate), then every automatic move whose gate is met.

    `caller` is the acting member's row in the proposal's ecosystem, always resolved
    from the authenticated identity and never from a request field. `note` is the
    reason a send-back requires. The caller commits.
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
        refusal = move_authority_refusal(proposal, move, caller, today=dates.aoe_today())
        if refusal is not None:
            raise refusal
        note = (note or "").strip() or None
        if move.note_required and note is None:
            raise TransitionRefused(400, NOTE_REQUIRED)
        if move.gate is not None:
            gates = await proposal_gate_status(session, proposal)
            if not gates[move.gate]["met"]:
                raise TransitionRefused(
                    409,
                    f"The {move.gate} gate is not satisfied — the conditions declared in the ACT policy must be met first",
                    {"gates": gates},
                )
        moved = f"{proposal.status}->{to}"
        minted = await _apply(session, proposal, move, enter=_enter_proposal_stage, actor=caller,
                              automatic=False, evidence=note)
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
        if raw.get("matching_profile") is not None:
            from copy import deepcopy
            from neos_agent.services.matching import validate_configuration
            from neos_agent.api.errors import ApiError
            try:
                policy["matching_profile"] = deepcopy(validate_configuration(raw["matching_profile"]))
            except ApiError:
                pass
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

# Owner default: a proposal with no declared or inherited quorum needs one position.
DEFAULT_PROPOSAL_QUORUM = 1


def consent_mode(proposal: Proposal) -> str:
    """'consensus' when the proposal declares it, else 'consent' (legacy types fall back to consent)."""
    return "consensus" if (proposal.decision_type or "").strip().lower() == "consensus" else "consent"


def consent_quorum_required(policy: dict) -> int:
    """Positions a proposal's consent gate needs: the declared (or inherited) quorum, else the engine default."""
    return policy["consent_quorum"] or DEFAULT_PROPOSAL_QUORUM


async def _advice_rounds_since_revision(session, proposal: Proposal) -> int:
    """Rounds with at least one entry, counted from the latest revision round (a send-back restarts the count)."""
    rows = (await session.execute(
        select(AdviceLog.id, AdviceLog.proposer_modifications, func.count(AdviceEntry.id))
        .outerjoin(AdviceEntry, AdviceEntry.advice_log_id == AdviceLog.id)
        .where(AdviceLog.proposal_id == proposal.id)
        .group_by(AdviceLog.id, AdviceLog.proposer_modifications, AdviceLog.created_at)
        .order_by(AdviceLog.created_at)
    )).all()
    start = max((index for index, row in enumerate(rows) if row[1]), default=0)
    return sum(1 for row in rows[start:] if row[2] > 0)


async def proposal_gate_status(session, proposal: Proposal) -> dict:
    """Evaluate the declared ACT gates for a proposal against live records."""
    policy, policy_source = await resolve_proposal_policy(session, proposal)

    # --- Advice gate: rounds that carry advice, since the latest revision ---
    effective_rounds = await _advice_rounds_since_revision(session, proposal)
    min_rounds = policy["min_advice_rounds"]
    advice_met = min_rounds == 0 or effective_rounds >= min_rounds
    deadline = proposal.advice_deadline

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
    mode = consent_mode(proposal)
    # Consensus: everyone who takes part consents; a stand-aside (only on legacy rows) holds it open.
    stand_asides = [p for p in active_positions if consent_position(p.position) == "stand_aside"]
    quorum = consent_quorum_required(policy)
    consent_met = (not policy["consent_required"]) or (
        latest_consent is not None
        and len(active_positions) >= quorum
        and not objections
        and not (mode == "consensus" and stand_asides)
    )

    # --- Test gate: declared cases must each show met evidence on this version ---
    declared_cases: list[str] = policy["test_cases"]
    reports = await reports_since_revision(session, proposal)
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
            # Backstop, never a move: the proposer is prompted to close advice once it passes.
            "deadline": deadline.isoformat() if deadline else None,
            "deadline_passed": dates.date_passed(deadline),
        },
        "consent": {
            "met": consent_met,
            "required": policy["consent_required"],
            "mode": mode,
            "positions": len(active_positions),
            "quorum": quorum if policy["consent_required"] else None,
            # "proposal" / "agreement" when declared there (the policy's source), else "default".
            "quorum_source": policy_source if policy["consent_quorum"] else "default",
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


# ---------------------------------------------------------------------------
# Consent positions and the caller's next moves
# ---------------------------------------------------------------------------

CONSENT_POSITIONS = ("consent", "stand_aside", "object")
CONSENT_CLOSED = "Consent positions can only be recorded while the proposal is in consent"
POSITION_UNKNOWN = "Choose consent, stand aside or object"
OBJECTION_REASON_REQUIRED = "Say what your objection is, so the proposer can work with it"
STAND_ASIDE_IN_CONSENSUS = "This proposal decides by consensus: consent or object (standing aside is not available)"
NO_POSITION_TO_WITHDRAW = "You have no position in this consent round to withdraw"
PARTICIPATE_DENIED = "Only a member of this proposal's ecosystem can record or withdraw a consent position"


async def _latest_consent_record(session, proposal: Proposal) -> ConsentRecord | None:
    return (await session.execute(
        select(ConsentRecord)
        .where(ConsentRecord.proposal_id == proposal.id)
        .order_by(ConsentRecord.created_at.desc())
        .limit(1)
    )).scalar_one_or_none()


async def _members_rows(session, record: ConsentRecord, member: Member) -> list[ConsentParticipant]:
    """The member's rows in `record`, oldest first: matched ONLY by member_id, never by display name.

    Display names are self-editable, so a NULL-member legacy row (one migration p8d4f1b6e3a9 could
    not attribute) is read-only history: it counts in the gate as stored and nobody can change it.
    """
    return list((await session.execute(
        select(ConsentParticipant)
        .where(ConsentParticipant.consent_record_id == record.id, ConsentParticipant.member_id == member.id)
        .order_by(ConsentParticipant.created_at)
    )).scalars().all())


async def current_position(session, proposal: Proposal, member: Member | None) -> ConsentParticipant | None:
    """`member`'s row in the latest consent record (the one the gate reads), or None."""
    if member is None:
        return None
    record = await _latest_consent_record(session, proposal)
    rows = await _members_rows(session, record, member) if record is not None else []
    active = [row for row in rows if consent_position(row.position) not in _WITHDRAWN_POSITIONS]
    return (active or rows or [None])[-1]


async def open_objections(session, proposal: Proposal) -> list[ConsentParticipant]:
    """The objections the consent gate waits on (latest consent record, classified as the gate does), oldest first."""
    record = await _latest_consent_record(session, proposal)
    if record is None:
        return []
    rows = (await session.execute(
        select(ConsentParticipant)
        .where(ConsentParticipant.consent_record_id == record.id)
        .order_by(ConsentParticipant.created_at, ConsentParticipant.id)
    )).scalars().all()
    return [row for row in rows if consent_position(row.position) in _BLOCKING_POSITIONS]


async def _require_open_consent(session, proposal: Proposal, member: Member | None) -> None:
    await require_participant(session, proposal, member)
    if PROPOSAL_LIFECYCLE.canonical(proposal.status) != "consent":
        raise TransitionRefused(409, CONSENT_CLOSED)


async def record_consent_position(session, proposal: Proposal, *, member: Member | None, position: str,
                                  reason: str | None = None) -> tuple[ConsentRecord, ActOutcome]:
    """Set `member`'s one position in the latest consent record (a change replaces it), then cascade.

    `member` is the authenticated caller's row in the proposal's ecosystem (`can_participate`,
    403 otherwise). Legacy duplicates the member owns are withdrawn, so one position counts. The caller commits.
    """
    await _require_open_consent(session, proposal, member)
    position = consent_position(position)
    reason = (reason or "").strip() or None
    if position not in CONSENT_POSITIONS:
        raise TransitionRefused(400, POSITION_UNKNOWN)
    if position == "object" and reason is None:
        raise TransitionRefused(400, OBJECTION_REASON_REQUIRED)
    if position == "stand_aside" and consent_mode(proposal) == "consensus":
        raise TransitionRefused(400, STAND_ASIDE_IN_CONSENSUS)

    record = await _latest_consent_record(session, proposal)
    if record is None:
        record = ConsentRecord(
            id=uuid.uuid4(), proposal_id=proposal.id, consent_mode=consent_mode(proposal),
            date=_dt.date.today(), quorum_met=False, outcome="pending",
        )
        session.add(record)
        await session.flush()
    rows = await _members_rows(session, record, member)
    if not rows:
        session.add(ConsentParticipant(
            id=uuid.uuid4(), consent_record_id=record.id, member_id=member.id,
            name=member.display_name, position=position, reason=reason, round=1,
        ))
    else:
        *older, kept = rows
        kept.name, kept.position, kept.reason = member.display_name, position, reason
        for row in older:  # pre-dedupe duplicates (backfilled to this member) stay as withdrawn history
            row.position = "withdrawn"
    await session.flush()
    return record, await _settle_consent(session, proposal, record, member)


async def withdraw_consent_position(session, proposal: Proposal, *, member: Member | None) -> tuple[ConsentRecord, ActOutcome]:
    """Withdraw `member`'s own position (an objection's author lifts it); the row stays as history."""
    await _require_open_consent(session, proposal, member)
    record = await _latest_consent_record(session, proposal)
    rows = await _members_rows(session, record, member) if record is not None else []
    active = [row for row in rows if consent_position(row.position) not in _WITHDRAWN_POSITIONS]
    if not active:
        raise TransitionRefused(404, NO_POSITION_TO_WITHDRAW)
    for row in active:
        row.position = "withdrawn"
    await session.flush()
    return record, await _settle_consent(session, proposal, record, member)


async def _settle_consent(session, proposal: Proposal, record: ConsentRecord, member: Member) -> ActOutcome:
    """Run the cascade, then keep the record's stored quorum flag in step with the gate."""
    outcome = await transition_proposal(session, proposal, caller=member)
    if outcome.status == "consent":
        record.quorum_met = outcome.gates["consent"]["positions"] >= (outcome.gates["consent"]["quorum"] or 0)
    else:
        record.quorum_met, record.outcome = True, "consented"
    return outcome


def proposal_next_moves(proposal: Proposal, gates: dict, caller: Member | None, *,
                        today: _dt.date | None = None) -> list[dict]:
    """The manual moves `caller` may request now, each with whether its gate is met (the UI's buttons).

    `blocked` lists a move the caller may not make yet, so the page says who decides instead of a button.
    """
    if not can_manage_proposal(caller, proposal):
        return []
    today = today or dates.aoe_today()
    moves = []
    for target in PROPOSAL_LIFECYCLE.manual_targets(proposal.status):
        move = PROPOSAL_LIFECYCLE.manual_move(proposal.status, target)
        blocked = None
        if move.steward_only and not can_confirm_ratification(caller, proposal):
            if not is_proposal_author(caller, proposal):
                continue
            blocked = "needs_another_steward"  # the author sees who decides instead of a button
        elif move.proposer_until_deadline and not can_close_advice(caller, proposal, today):
            blocked = "proposer_closes_advice"  # a steward before the deadline (or with none set)
        moves.append({
            "to": target,
            "ready": move.gate is None or bool(gates[move.gate]["met"]),
            "gate": move.gate,
            "note_required": move.note_required,
            "steward_only": move.steward_only,
            "blocked": blocked,
        })
    return moves


_STEWARD_ROLES = tuple(role for role, rank in ROLE_RANK.items() if rank >= ROLE_RANK["mod"])


async def ratification_confirmers(session, proposal: Proposal) -> list[Member]:
    """Active stewards who may confirm this proposal's ratification (`can_confirm_ratification`: never its author), by name."""
    rows = (await session.execute(select(Member).where(
        Member.ecosystem_id == proposal.ecosystem_id,
        Member.current_status == "active",
        Member.role.in_(_STEWARD_ROLES),
    ).order_by(Member.display_name, Member.id))).scalars().all()
    return [member for member in rows if can_confirm_ratification(member, proposal)]


def counted(number: int, singular: str, plural: str | None = None) -> str:
    """'1 advice round', '2 advice rounds': a count with its noun in the right number."""
    return f"{number} {singular if number == 1 else plural or singular + 's'}"


async def record_proposal_decision(session, proposal: Proposal, *, confirmed_by: Member | None = None) -> DecisionRecord | None:
    """Mint the browsable decision artifact for a ratified proposal; `confirmed_by` is the steward who confirmed it.

    Idempotent: one artifact per proposal. Consent participants become
    decision participants — the recorded commitments by members to the
    proposal. Counts match the gates (advice rounds and test reports since the latest revision).
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

    advice_rounds = await _advice_rounds_since_revision(session, proposal)  # what the advice gate counted
    positions = [p for p in participants if consent_position(p.position) not in _WITHDRAWN_POSITIONS]
    report_count = len(await reports_since_revision(session, proposal))  # what the test gate counted
    policy, policy_source = await resolve_proposal_policy(session, proposal)
    source_phrase = {
        "proposal": "set on the proposal",
        "agreement": "taken from the agreement that governs it",
        "default": "the usual ones (none were set)",
    }[policy_source]
    advice_rule = (f"{counted(policy['min_advice_rounds'], 'advice round')} with advice"
                   if policy["min_advice_rounds"] else "no advice round needed")
    consent_rule = (f"at least {counted(consent_quorum_required(policy), 'position')} and no open objection"
                    if policy["consent_required"] else "no consent round needed")
    cases = policy["test_cases"]
    test_rule = f"evidence for {counted(len(cases), 'named test case')}" if cases else "one passed test report"
    steward = confirmed_by.display_name if confirmed_by is not None else "a steward"

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
            f"It went through advice, consent and test. The gates were {source_phrase}: {advice_rule}, "
            f"{consent_rule}, and {test_rule}. On the version that was decided (v{proposal.version}), "
            f"{counted(advice_rounds, 'advice round')} had advice, {counted(len(positions), 'member')} "
            f"recorded a position, and {counted(report_count, 'test report')} "
            f"{'was' if report_count == 1 else 'were'} filed. Advice was closed by hand, consent moved on by "
            f"itself once its gate was met, and {steward}, a steward who did not write it, confirmed ratification."
        ),
        source_skill="act-process",
        artifact_type="proposal",
        artifact_reference=proposal.proposal_id,
        source_proposal_id=proposal.id,
        domain=proposal.affected_domain,
        precedent_level="binding",
        status="active",
        # The record is the confirming steward's act (owner decision: a steward confirms), not the proposer's.
        recorder=confirmed_by.display_name if confirmed_by is not None else proposal.proposer,
        recorder_role="steward who confirmed ratification" if confirmed_by is not None else "proposer",
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
    # One quorum meaning: N members must take part. Undeclared, an agreement needs every participating member.
    consent_met = (not consent_required) or (
        summary["complete"] if quorum is None else summary["consented"] >= quorum
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
            "quorum_source": "agreement" if quorum else "all_members",
        },
        "test": {
            "met": test_met,
            "declared_cases": declared_cases,
            "evidence": test_evidence,
            "required_evidence": required_evidence,
        },
        # FX-Maint: archiving waits for the sunset's end (services/dates); a legacy sunset with no date never blocks.
        "sunset_ended": {
            "met": agreement.sunset_date is None or dates.date_passed(agreement.sunset_date),
            "sunset_date": agreement.sunset_date.isoformat() if agreement.sunset_date else None,
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
    ceremony_id = uuid.uuid4()
    session.add(AgreementCeremony(
        id=ceremony_id,
        agreement_id=agreement.id,
        stage=target,
        completed_by_member_id=actor.id if actor is not None else None,
        outcome=_CEREMONY_OUTCOME.get(target, "completed"),
        evidence=_AUTOMATIC_EVIDENCE.get(target) if automatic else (evidence or None),
        completed_at=_utcnow(),
    ))
    from neos_agent.services.engagement_events import source_event
    await source_event(session, agreement, kind="agreement", family="governance", action=target,
                       actor_user_id=actor.user_id if actor is not None else None, occurrence_id=ceremony_id)
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
