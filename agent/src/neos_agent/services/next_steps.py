"""What is waiting for the caller, and what happens next on a record; see services/AGENTS.md "Next steps".

Derived from state on every call: no table, no notification service. REST
(`api/next_steps.py`: the dashboard queue, the bell, the status banner) and the
assistant (`what_needs_me`, `explain_status`, `get_proposal`, `get_agreement`)
read the same words from here. Rules are never restated: moves come from the
lifecycle tables (`act_gates`, `exit.EXIT_MOVES`, `conflicts.CONFLICT_MOVES`),
who may act from `policy` and the emergency caller flags, and the sentences
from `emergency.describe`, `exit.NEXT_STEP` and `conflicts.conflict_stage`.
"""

from __future__ import annotations

import datetime as _dt
import uuid
from dataclasses import dataclass

from sqlalchemy import and_, func, or_, select

from neos_agent.api import conflicts as conflict_api
from neos_agent.api import emergency as emergency_api
from neos_agent.api import exit as exit_api
from neos_agent.api.agreements import CONSENT_OPEN_STATUSES
from neos_agent.api.errors import ApiError, get_scoped_or_404
from neos_agent.api.guards import caller_in, reachable_ecosystem_ids
from neos_agent.api.policy import (
    can_close_advice,
    can_conduct_agreement_ceremony,
    can_confirm_ratification,
    can_finish_audit,
    can_manage_proposal,
    can_participate,
    can_register_agreement,
    can_triage_conflict,
    can_view_conflict,
    is_proposal_author,
)
from neos_agent.api.safeguards import AUDIT_DRAFT
from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    Agreement,
    AgreementMemberConsent,
    ConflictCase,
    Ecosystem,
    EmergencyState,
    ExitRecord,
    GovernanceHealthAudit,
    Member,
    Proposal,
    RepairAgreementRecord,
)
from neos_agent.services.act_gates import (
    AGREEMENT_LIFECYCLE,
    PROPOSAL_LIFECYCLE,
    Lifecycle,
    Move,
    agreement_gate_status,
    consent_mode,
    consent_position,
    counted,
    current_position,
    latest_revision_log,
    normalize_act_policy,
    open_objections,
    proposal_gate_status,
    proposal_next_moves,
    ratification_confirmers,
    revision_round,
)
from neos_agent.services.agreement_consent import _PARTICIPATING_MEMBER_STATUSES

# Client routes (charting-the-course App.tsx); the assistant links to the same pages.
ROUTES = {
    "proposal": "/proposals", "agreement": "/agreements", "domain": "/domains", "conflict": "/conflicts",
    "exit": "/exit", "emergency": "/emergency", "decision": "/decisions", "audit": "/safeguards/audits",
}
# Records with a status banner (GET /explain/<kind>/<id>, the assistant's explain_status).
EXPLAIN_KINDS = ("proposal", "agreement", "conflict", "emergency", "exit", "audit")
# Queue order among items with the same urgency.
_KIND_ORDER = {"emergency": 0, "conflict": 1, "proposal": 2, "agreement": 3, "exit": 4, "audit": 5}
# Acts only this caller's role can take, which hold a record up until taken: after overdue items, these come first.
OWNER_ACTIONS = frozenset({"close_advice", "revise", "answer_objection", "confirm_ratification", "register_agreement",
                           "finish_review"})
# Acts another person is waiting on (an answer to read, a side to approve, an audit to answer): ranked with OWNER_ACTIONS.
UNBLOCKING_ACTIONS = frozenset({"read_response", "approve_collaboration", "respond_to_audit"})
FIRST_TIER = OWNER_ACTIONS | UNBLOCKING_ACTIONS
# Steps that build on each other, within one kind and date: the entry quiz checks the orientation journey.
_STEP_ORDER = {"start_orientation": 0, "take_entry_quiz": 1}

# The proposer's prompt, word for word as the proposal page (client lib/proposal-vocab.ts adviceClosePrompt).
ADVICE_DEADLINE_PROMPT = "Advice deadline passed: move to consent?"
ADVICE_READY_PROMPT = "Close advice and move to consent: enough advice is in"  # names the act (deadline not passed)
# A steward's prompt once the deadline passed and the proposer has not closed advice (owner decision 2026-11-01).
ADVICE_DEADLINE_STEWARD_PROMPT = "Advice deadline passed: close advice for the proposer?"

# Plain stage names, as the client labels them (proposal-vocab, agreement-status, emergency-phase, exit-status).
PROPOSAL_STATES = {"draft": "Draft", "advice": "Advice", "consent": "Consent", "test": "Test",
                   "ratified": "Ratified", "withdrawn": "Withdrawn"}
AGREEMENT_STATES = {"draft": "Draft", "advice": "Advice", "consent": "Consent", "test": "Test", "active": "Active",
                    "under_review": "Under Review", "sunset": "Sunset", "archived": "Archived"}
EMERGENCY_STATES = {"pending": "Waiting for a co-signer", "open": "Emergency in effect", "recovery": "Recovery",
                    "closed": "Closed", "withdrawn": "Withdrawn"}
EXIT_STATES = {"declared": "Filed", "cooling_off": "Filed", "unwinding": "Handoff in progress",
               "completed": "Departure confirmed", "cancelled": "Withdrawn"}

_PROPOSAL_MOVE_LABELS = {
    "advice": "Open for advice", "consent": "Close advice and move to consent", "test": "Start the test period",
    "ratified": "Confirm ratification", "withdrawn": "Withdraw proposal",
}
_AGREEMENT_MOVE_LABELS = {
    "advice": "Open the advice ceremony", "consent": "Open the consent ceremony", "test": "Start the test",
    "active": "Put it in force", "under_review": "Start a review", "sunset": "Start its sunset", "archived": "Archive it",
}
_CONFLICT_MOVE_LABELS = {
    "triaged": "Triage it", "in_progress": "Start the process", "resolved": "Record how it was resolved",
    "closed": "Close the case",
}
_EXIT_MOVE_LABELS = {"unwinding": "Start the handoff", "completed": "Confirm departure", "cancelled": "Withdraw your exit"}
_EMERGENCY_MOVES = (  # caller flag -> (move, label), in the page's order
    ("caller_can_cosign", "cosign", "Co-sign this emergency"),
    ("caller_can_end", "end", "End emergency authority now"),
    ("caller_can_withdraw", "withdraw", "Withdraw declaration"),
    ("caller_can_review", "review", "Record the post-emergency review"),
    ("caller_can_complete_recovery", "complete_recovery", "Close Recovery"),
)
_POSITION_WORDS = {"consent": "consent", "stand_aside": "stand aside", "object": "object"}


from neos_agent.services import dates as _dates  # noqa: E402  (G-Maint: the one date rule)


@dataclass(frozen=True)
class Clock:
    """One reading of the clock per request: `today` (services/dates.aoe_today) for date columns, naive-UTC `now`."""

    today: _dt.date
    now: _dt.datetime

    @classmethod
    def at(cls, now: _dt.datetime | None = None) -> "Clock":
        now = _dates.naive_utc(now or _dates.utc_now())
        return cls(today=_dates.aoe_today(now), now=now)

    def past(self, due: _dt.date | _dt.datetime | None) -> bool:
        """True once `due` has gone by: services/dates.date_passed at this reading of the clock."""
        return _dates.date_passed(due, self.now)


def link(kind: str, record_id) -> str:
    """The page for a record, as the app routes it."""
    return f"{ROUTES[kind]}/{record_id}"


def _due_text(due: _dt.date | _dt.datetime | None) -> str | None:
    """A date as YYYY-MM-DD; a (naive UTC) timestamp as ISO with Z, so browsers read it as UTC."""
    if due is None:
        return None
    if isinstance(due, _dt.datetime):
        return emergency_api.naive_utc(due).replace(microsecond=0).isoformat() + "Z"
    return due.isoformat()


def _active(caller: Member | None) -> bool:
    return caller is not None and caller.current_status == "active"


def _clip(text: str | None, limit: int = 90) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _item(kind: str, record, *, action: str, what: str, why: str, title: str, ecosystem: str | None,
          clock: Clock, key: str | None = None, due=None, overdue: bool | None = None, part: str | None = None) -> dict:
    """One thing waiting for the caller; `uid` stays unique when one record yields several (repair check-ins)."""
    return {
        "uid": ":".join(filter(None, (action, str(record.id), part))),
        "kind": kind,
        "id": str(record.id),
        "key": key,
        "title": title,
        "ecosystem_id": str(record.ecosystem_id),
        "ecosystem": ecosystem,
        "action": action,
        "what": what,
        "why": why,
        "due": _due_text(due),
        "overdue": clock.past(due) if overdue is None else overdue,
        "link": link(kind, record.id),
    }


# ---------------------------------------------------------------------------
# Standing and next-step sentences (shared by explain() and the assistant's reads)
# ---------------------------------------------------------------------------


async def proposal_standing(session, prop: Proposal, caller: Member | None) -> dict:
    """The caller's relation to a proposal: author, may manage, may take part, advised this round, consent position.

    Matched by member id only, never by display name (self-editable); legacy NULL-member rows are nobody's.
    """
    if caller is None:
        return {"is_member_here": False, "is_author": False, "can_manage": False, "can_take_part": False}
    latest_log = (await session.execute(
        select(AdviceLog.id).where(AdviceLog.proposal_id == prop.id).order_by(AdviceLog.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    advised = latest_log is not None and bool(await session.scalar(
        select(func.count(AdviceEntry.id)).where(
            AdviceEntry.advice_log_id == latest_log, AdviceEntry.member_id == caller.id,
        )
    ))
    row = await current_position(session, prop, caller)  # the engine's own lookup, as the REST consent tab
    return {
        "is_member_here": True,
        "is_author": is_proposal_author(caller, prop),
        "can_manage": can_manage_proposal(caller, prop),
        "can_take_part": can_participate(caller, prop),
        "has_advised_this_round": advised,
        "my_position": consent_position(row.position) if row is not None and row.position else None,
        "can_confirm": can_confirm_ratification(caller, prop),
        "can_register": can_register_agreement(caller, prop),
        "can_close_advice": can_close_advice(caller, prop, _dates.aoe_today()),
    }


async def proposal_facts(session, prop: Proposal) -> dict:
    """Who and what the next-step sentences name at this stage: the revision round, open objections,
    the stewards who may confirm ratification, and the agreement it is (or will be) registered as."""
    stage = PROPOSAL_LIFECYCLE.canonical(prop.status)
    facts: dict = {"revision": None, "objections": [], "confirmers": [], "registered": None, "amends": None}
    if stage == "advice":
        facts["revision"] = revision_round(await latest_revision_log(session, prop))
    elif stage == "consent":
        facts["objections"] = [
            {"id": str(row.id), "name": row.name or "A member", "reason": row.reason,
             "member_id": str(row.member_id) if row.member_id else None}
            for row in await open_objections(session, prop)
        ]
    elif stage == "test":
        facts["confirmers"] = [{"id": str(member.id), "display_name": member.display_name}
                               for member in await ratification_confirmers(session, prop)]
    elif stage == "ratified":
        linked = prop.registered_agreement_id or prop.amends_agreement_id
        title = await session.scalar(select(Agreement.title).where(Agreement.id == linked)) if linked else None
        facts["registered" if prop.registered_agreement_id else "amends"] = title
    return facts


async def agreement_standing(session, agr: Agreement, caller: Member | None) -> dict:
    """The caller's relation to an agreement: member here, consented to this version, may conduct ceremonies."""
    has_consented = caller is not None and bool(await session.scalar(
        select(func.count(AgreementMemberConsent.id)).where(
            AgreementMemberConsent.agreement_id == agr.id,
            AgreementMemberConsent.member_id == caller.id,
            AgreementMemberConsent.agreement_version == agr.version,
            AgreementMemberConsent.withdrawn_at.is_(None),
        )
    ))
    return {
        "is_member_here": caller is not None,
        "has_consented": has_consented,
        "can_conduct_ceremonies": can_conduct_agreement_ceremony(caller, agr),
    }


def _verb(number: int, one: str, many: str) -> str:
    return one if number == 1 else many


def _names(people: list[dict] | None) -> str:
    """'Mo', 'Mo or Sol', 'Mo, Sol or Ari'."""
    names = [person["display_name"] for person in people or []]
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} or {names[-1]}" if names else ""


def _gate_condition(stage: str, gates: dict) -> str:
    """What the gate out of `stage` waits for, in plain words."""
    if stage == "advice":
        rounds = gates["advice"]["required_rounds"]
        return f"{counted(rounds, 'advice round')} {_verb(rounds, 'has', 'have')} advice"
    if stage == "consent":
        consent = gates["consent"]
        quorum = consent.get("quorum")
        if "consented" in consent:  # agreements count member attestations
            return (f"{counted(quorum, 'member')} {_verb(quorum, 'has', 'have')} consented" if quorum
                    else "every member who takes part has consented")
        return (f"{counted(quorum, 'position')} {_verb(quorum, 'is', 'are')} recorded and no objection is open"
                if quorum else "consent is complete")
    return "the test evidence is in"


def _forward_move(lifecycle: Lifecycle, stage: str) -> Move | None:
    """The table's way forward out of `stage`: not a send-back (note required), not a withdrawal."""
    return next((
        move for move in lifecycle.moves
        if move.source == stage and move.target != lifecycle.withdrawn and not move.note_required
    ), None)


def _move_note(lifecycle: Lifecycle, stage: str, gates: dict, who_moves: str) -> str | None:
    """How a record moves forward from `stage`, read from the lifecycle table, so it follows the owner's table edits."""
    move = _forward_move(lifecycle, stage)
    if move is None:
        return None
    if move.automatic and move.gate:
        return f"It moves to {move.target} by itself once {_gate_condition(stage, gates)}."
    if move.steward_only:
        return f"Then a steward who did not write it confirms the move to {move.target}."
    return f"When it is ready, {who_moves} moves it to {move.target}."


def _decider(lifecycle: Lifecycle, stage: str, gates: dict, who_moves: str) -> str | None:
    """Who makes the next forward move, from the same table row as `_move_note`."""
    move = _forward_move(lifecycle, stage)
    if move is None:
        return None
    if move.automatic and move.gate:
        return f"It moves on by itself once {_gate_condition(stage, gates)}"
    if move.steward_only:
        return "A steward who did not write it"
    return who_moves[:1].upper() + who_moves[1:]


def _proposal_managers(prop: Proposal) -> str:
    """Who may move a proposal by hand (policy.can_manage_proposal), in words."""
    if prop.proposer_member_id is None:
        return "a steward of this ecosystem"
    return f"{prop.proposer or 'the author'} or a steward"


def _proposal_decider(prop: Proposal, stage: str, gates: dict, facts: dict) -> str | None:
    """'Who decides' for the banner: the advice close is the author's (a steward only after its deadline), names the confirmers."""
    if stage == "advice":
        if prop.proposer_member_id is None:
            return "A steward of this ecosystem"
        author = f"{prop.proposer or 'The author'}, who wrote it"
        if prop.advice_deadline is None:
            return author
        if gates["advice"].get("deadline_passed"):
            return f"{author}; the advice deadline has passed, so a steward can close it for them"
        return f"{author} (a steward can close it for them after the advice deadline, {prop.advice_deadline.isoformat()})"
    if stage == "test" and facts.get("confirmers"):
        return f"A steward who did not write it: {_names(facts['confirmers'])}"
    if stage == "ratified" and prop.registered_agreement_id is None and (prop.ratified_text or "").strip():
        return "Any steward of this ecosystem, by registering it as an agreement"
    return _decider(PROPOSAL_LIFECYCLE, stage, gates, _proposal_managers(prop))


def _capitalized(text: str) -> str:
    return text[:1].upper() + text[1:]


def _advice_step(prop: Proposal, gates: dict, you: dict, facts: dict) -> list[str]:
    """The advice stage per viewer: the author closes advice; anyone else is told who does and whether they advised."""
    advice = gates["advice"]
    required = advice["required_rounds"]
    parts = [f"Advice stage: {advice['rounds']} of {counted(required, 'advice round')} {_verb(required, 'has', 'have')} advice."
             if required else "Advice stage: no advice round is needed before consent."]
    revision = facts.get("revision")
    if revision:
        parts.append(f"{_capitalized(revision['by'] or 'someone')} sent it back for revision with this note: "
                     f"“{_clip(revision['note'], 200)}”. This is version {prop.version}; advice, positions and "
                     "test reports on earlier versions are kept as history.")
    author = prop.proposer or "the author"
    if you.get("is_author"):
        parts.append("You wrote it, so you gather advice; you cannot advise on it yourself.")
        if revision:
            parts.append("Change the text if the note calls for it, then gather advice on this version.")
        parts.append("You decide when to close advice and move it to consent: nothing moves by itself.")
    else:
        if you.get("can_take_part"):
            parts.append("You already gave advice in this round." if you.get("has_advised_this_round")
                         else "You can give advice.")
        if prop.proposer_member_id is None:  # legacy, no author link: steward-managed
            parts.append("A steward of this ecosystem closes advice and moves it to consent"
                         + (": you can, as a steward." if you.get("can_manage") else "."))
        elif you.get("can_manage"):  # a steward who did not write it (owner decision 2026-11-01)
            parts.append(_steward_advice_close(prop, author, you))
        else:
            parts.append(f"{author} wrote it and decides when to close advice and move it to consent.")
    proposer_role = you.get("is_author") or prop.proposer_member_id is None
    if advice.get("deadline_passed") and proposer_role and you.get("can_manage"):
        parts.append("The advice deadline has passed: it is time to decide whether to move it to consent.")
    return parts


def _steward_advice_close(prop: Proposal, author: str, you: dict) -> str:
    """What a steward who did not write it may do about closing advice: wait for the deadline, or act once it passed."""
    if prop.advice_deadline is None:
        return f"{author} wrote it and closes advice. There is no advice deadline, so only {author} can close it."
    deadline = prop.advice_deadline.isoformat()
    if you.get("can_close_advice"):
        return (f"{author} wrote it and closes advice. The advice deadline ({deadline}) has passed, so as a steward "
                "you can close it for them if they haven't.")
    return f"{author} wrote it and closes advice. You can close it after the advice deadline ({deadline}) if they haven't."


def _consent_step(prop: Proposal, gates: dict, you: dict, facts: dict) -> list[str]:
    """The consent stage: positions against the quorum, each open objection by name, and who answers it."""
    consent = gates["consent"]
    parts = []
    if consent.get("required"):
        parts.append(f"Consent stage: {counted(consent['positions'], 'position')} recorded, {consent['quorum']} needed.")
    open_count = consent.get("open_objections") or 0
    objections = facts.get("objections") or []
    if open_count:
        parts.extend(f"{row['name']} objected: “{_clip(row['reason'], 160)}”." for row in objections)
        if not objections:
            parts.append(f"{counted(open_count, 'objection')} {_verb(open_count, 'is', 'are')} open.")
        held = f"It cannot move on while {_verb(open_count, 'this objection is', 'these objections are')} open."
        answers_it = you.get("is_author") or (prop.proposer_member_id is None and you.get("can_manage"))
        if answers_it:
            parts.append(f"{held} Answer it: send it back for revision with a note on what will change, "
                         "or wait for the objection to be withdrawn.")
        elif you.get("my_position") == "object":
            parts.append(f"{held} You objected: once your concern is answered, you can withdraw your objection.")
        elif you.get("can_manage"):
            parts.append(f"{held} {prop.proposer or 'The author'} answers it, usually by sending it back for revision; "
                         "as a steward you can send it back too.")
        else:
            parts.append(f"{held} {prop.proposer or 'The author'} answers it.")
    if you.get("can_take_part"):
        mine = you.get("my_position")
        choices = "consent or object" if consent.get("mode") == "consensus" else "consent, stand aside or object"
        parts.append(f"Your position: {_POSITION_WORDS.get(mine, mine)}." if mine and mine != "withdrawn"
                     else f"You can record your position: {choices} (objecting needs a reason).")
    note = _move_note(PROPOSAL_LIFECYCLE, "consent", gates, _proposal_managers(prop))
    if note:
        parts.append(note)
    return parts


def _test_step(gates: dict, you: dict, facts: dict) -> list[str]:
    """The test stage: evidence so far; once it is in, which stewards confirm (and stop inviting reports)."""
    test = gates["test"]
    if not test["met"]:
        declared = len(test["declared_cases"])
        parts = [f"Test stage: {len(test['cases_met'])} of {counted(declared, 'test case')} "
                 f"{_verb(declared, 'has', 'have')} evidence." if declared
                 else f"Test stage: {counted(test['reports'], 'test report')} so far; one passed report is the evidence needed."]
        if you.get("can_take_part"):
            parts.append("You can file a test report.")
        parts.append("When the evidence is in, a steward who did not write it confirms ratification.")
        return parts
    parts = ["Test stage: the test evidence is in."]
    confirmers = facts.get("confirmers")
    if you.get("can_confirm"):
        parts.append("Now a steward who did not write it confirms ratification, and you can: it is waiting in your list.")
    elif confirmers:
        parts.append(f"Now a steward who did not write it confirms ratification: {_names(confirmers)} can, "
                     "and it is waiting in their list.")
    elif "confirmers" in facts:
        parts.append("Now a steward who did not write it confirms ratification, but there is no such steward yet: "
                     "an owner or admin first gives another member the moderator role.")
    else:
        parts.append("Now a steward who did not write it confirms ratification.")
    if you.get("is_author"):
        parts.append("You wrote it, so you cannot confirm it yourself.")
    return parts


def _ratified_step(prop: Proposal, you: dict, facts: dict) -> str:
    """Ratified: registration is the next step until it is registered; then the banner names the agreement."""
    if prop.registered_agreement_id is not None:
        title = facts.get("registered")
        return (f"It is ratified and registered as the agreement “{title}”, which is in force. Nothing more is needed."
                if title else "It is ratified and registered as an agreement. Nothing more is needed.")
    if not (prop.ratified_text or "").strip():
        return ("It is ratified: a binding decision. No text was kept when it was ratified, "
                "so it cannot be registered as an agreement.")
    who = "You can do it as a steward." if you.get("can_register") else "Any steward of this ecosystem can do it."
    amends = facts.get("amends")
    change = (f" Registering it changes the agreement “{amends}”; until then that agreement keeps its current text."
              if amends else "")
    return ("It is ratified: a binding decision, but it is not in the agreement registry yet. "
            f"The next step is to register it as an agreement. {who}{change}")


def proposal_next_step(prop: Proposal, gates: dict, you: dict, facts: dict | None = None) -> str:
    """Plain sentences: where the proposal stands, what the caller can do, and what happens next.

    `facts` (proposal_facts) lets the sentences name people: who sent it back and why, each objector,
    the stewards who confirm, the registered agreement. Without it they fall back to counts.
    """
    facts = facts or {}
    stage = PROPOSAL_LIFECYCLE.canonical(prop.status)
    author = prop.proposer or "the author"
    if stage == "draft":
        return "It is a draft. " + (
            "You can open it for advice when it is ready." if you.get("can_manage")
            else f"Only {author} or a steward can open it for advice."
        )
    if stage == "ratified":
        return _ratified_step(prop, you, facts)
    if stage == "withdrawn":
        return "It was withdrawn, so nothing more happens to it."
    if stage == "advice":
        parts = _advice_step(prop, gates, you, facts)
    elif stage == "consent":
        parts = _consent_step(prop, gates, you, facts)
    elif stage == "test":
        parts = _test_step(gates, you, facts)
    else:
        parts = [f"Status: {prop.status}."]
    if you.get("can_manage") and PROPOSAL_LIFECYCLE.manual_move(prop.status, "withdrawn") is not None:
        parts.append("You can also withdraw it.")
    return " ".join(parts)


def agreement_next_step(agr: Agreement, gates: dict, you: dict) -> str:
    """Plain sentences: where the agreement stands, what the caller can do, and what happens next."""
    stage = agr.status
    consent_line = "" if "has_consented" not in you else (
        "You have consented to this version." if you["has_consented"]
        else "You have not consented to this version; you can do it on its page."
    )
    if stage == "draft":
        return "It is a draft. An ecosystem admin or owner opens the advice ceremony when it is ready."
    if stage == "active":
        return f"It is in force. {_review_line(agr)} {consent_line}".strip()
    if stage == "under_review":
        return ("It is under review and stays in force meanwhile. An admin or owner ends the review with written "
                "findings: keep it in force (its next review date is then set) or start its sunset (it ends "
                f"{_SUNSET_NOTICE_DAYS} days later and cannot be put back in force).")
    if stage == "sunset":
        if agr.sunset_date is None:
            return "It is being ended (sunset); an admin or owner archives it when that is done."
        if _dates.date_passed(agr.sunset_date):
            return f"Its sunset ended on {agr.sunset_date.isoformat()}; an admin or owner archives it now."
        return f"It is being ended (sunset) and ends on {agr.sunset_date.isoformat()}; then an admin or owner archives it."
    if stage == "archived":
        return "It is archived and no longer in force."
    parts: list[str] = []
    if stage == "advice":
        advice = gates["advice"]
        parts.append(f"Advice stage: {advice['rounds']} of {advice['required_rounds']} advice rounds recorded. "
                     "Any active member can record an advice round.")
    elif stage == "consent":
        consent = gates["consent"]
        consented = consent["consented"]
        parts.append(f"Consent stage: {counted(consented, 'member')} {_verb(consented, 'has', 'have')} consented, "
                     f"{consent['outstanding']} still need to.")
        if consent_line:
            parts.append(consent_line)
    elif stage == "test":
        test = gates["test"]
        parts.append(f"Test stage: {test['evidence']} of {test['required_evidence']} pieces of test evidence recorded. "
                     "Any active member can record test evidence.")
    note = _move_note(AGREEMENT_LIFECYCLE, stage, gates, "an admin or owner")
    if note:
        parts.append(note)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Items: what one record asks of one caller (the queue and explain() share these)
# ---------------------------------------------------------------------------


async def _open_revision_note(session, prop: Proposal) -> str | None:
    """The send-back note while the author still has to revise: the revision round has no advice yet and the
    proposal was not edited since the send-back (its `updated_at` is later than the round's insert time)."""
    log = (await session.execute(
        select(AdviceLog).where(AdviceLog.proposal_id == prop.id).order_by(AdviceLog.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    revision = revision_round(log)
    if revision is None:
        return None
    if await session.scalar(select(func.count(AdviceEntry.id)).where(AdviceEntry.advice_log_id == log.id)):
        return None
    # created_at is ordered artificially (created_after_newest); updated_at is the server clock at the send-back.
    edited_at = await session.scalar(select(Proposal.updated_at).where(Proposal.id == prop.id))
    if edited_at is not None and log.updated_at is not None and edited_at > log.updated_at:
        return None
    return revision["note"]


async def proposal_items(session, prop: Proposal, caller: Member | None, ecosystem: str | None, clock: Clock) -> list[dict]:
    """Advice to give, a position to record, and the acts only one role can take: closing advice, revising,
    answering an objection (the author), confirming ratification and registering (stewards)."""
    stage = PROPOSAL_LIFECYCLE.canonical(prop.status)
    if not _active(caller) or not can_participate(caller, prop) or stage not in ("advice", "consent", "test", "ratified"):
        return []

    def item(action: str, what: str, why: str, **extra) -> dict:
        return _item("proposal", prop, action=action, what=what, why=why, title=prop.title, key=prop.proposal_id,
                     ecosystem=ecosystem, clock=clock, **extra)

    if stage == "ratified":  # ratified is not registered: a steward's step until the agreement exists
        if (prop.registered_agreement_id is not None or not (prop.ratified_text or "").strip()
                or not can_register_agreement(caller, prop)):
            return []
        return [item("register_agreement", "Register it as an agreement",
                     "It is ratified but not in the agreement registry yet, and any steward of this ecosystem "
                     "registers it.")]

    # The proposer closes advice (owner decision); an unlinked legacy proposal is steward-managed.
    proposer_role = is_proposal_author(caller, prop) or (prop.proposer_member_id is None and can_manage_proposal(caller, prop))
    if stage == "advice" and proposer_role:
        note = await _open_revision_note(session, prop)
        if note is not None:
            return [item("revise", "Revise it: it was sent back for revision",
                         f"You wrote it, and it was sent back with this note: {_clip(note, 200)}. Change the text, "
                         "or keep it, then gather advice on this version.", due=prop.advice_deadline)]
        gates = await proposal_gate_status(session, prop)
        # Once the gate is met, deadline or not: advice never closes by itself, so nothing may stall silently.
        if any(m["to"] == "consent" and m["ready"] for m in proposal_next_moves(prop, gates, caller, today=clock.today)):
            return [item("close_advice", ADVICE_DEADLINE_PROMPT if clock.past(prop.advice_deadline) else ADVICE_READY_PROMPT,
                         "You wrote it, and advice closes on your call: nothing moves by itself.",
                         due=prop.advice_deadline)]
        return []
    if stage == "advice":
        items = []
        # A steward who did not write it, once the deadline passed and the proposer has not closed advice.
        if can_close_advice(caller, prop, clock.today):
            gates = await proposal_gate_status(session, prop)
            moves = proposal_next_moves(prop, gates, caller, today=clock.today)
            if any(m["to"] == "consent" and m["ready"] and not m["blocked"] for m in moves):
                items.append(item("close_advice", ADVICE_DEADLINE_STEWARD_PROMPT,
                                  f"{prop.proposer or 'The proposer'} wrote it and has not closed advice. The advice "
                                  "deadline has passed, so a steward can close it for them.",
                                  due=prop.advice_deadline))
        you = await proposal_standing(session, prop, caller)
        if not you["has_advised_this_round"]:
            items.append(item("give_advice", "Give your advice",
                              f"You are a member of {ecosystem or 'this ecosystem'} and have not advised in this round.",
                              due=prop.advice_deadline))
        return items
    if stage == "consent":
        items = []
        if proposer_role:  # the author answers each open objection (the author's own position counts: owner decision)
            for row in await open_objections(session, prop):
                name = row.name or "A member"
                items.append(item(
                    "answer_objection", f"{name} objected: “{_clip(row.reason, 80)}”",
                    "It cannot move on while the objection is open. Answer it: send it back for revision with a "
                    f"note on what will change, or wait for {name} to withdraw it.",
                    due=prop.consent_deadline, part=str(row.id),
                ))
        you = await proposal_standing(session, prop, caller)
        if you["my_position"] in (None, "withdrawn"):
            choices = "consent or object" if consent_mode(prop) == "consensus" else "consent, stand aside or object"
            items.append(item("record_position", f"Record your position: {choices}",
                              "It is in consent, and you have not recorded a position in this round.",
                              due=prop.consent_deadline))
        return items
    if not can_confirm_ratification(caller, prop):
        return []
    gates = await proposal_gate_status(session, prop)
    ratify = next((m for m in proposal_next_moves(prop, gates, caller, today=clock.today) if m["to"] == "ratified"), None)
    if ratify is None or not ratify["ready"] or ratify["blocked"]:
        return []
    return [item("confirm_ratification", "Confirm ratification",
                 "Its test evidence is in, and a steward who did not write it confirms.")]


def _consent_required(agr: Agreement) -> bool:
    """The agreement asks members for consent (agreement_gate_status's rule)."""
    return agr.requires_explicit_consent is not False and normalize_act_policy(agr.act_policy)["consent_required"]


def agreement_items(agr: Agreement, caller: Member | None, consents: list[AgreementMemberConsent], ecosystem: str | None,
                    clock: Clock) -> list[dict]:
    """Consent to record (the consent stage) or to renew (in force, after the text changed version)."""
    if not _active(caller) or caller.ecosystem_id != agr.ecosystem_id or caller.current_status not in _PARTICIPATING_MEMBER_STATUSES:
        return []
    if agr.status not in CONSENT_OPEN_STATUSES or not _consent_required(agr):
        return []
    held = [c for c in consents if c.withdrawn_at is None]
    if any(c.agreement_version == agr.version for c in held):
        return []

    def item(action: str, what: str, why: str) -> dict:
        return _item("agreement", agr, action=action, what=what, why=why, title=agr.title, key=agr.agreement_id,
                     ecosystem=ecosystem, clock=clock)

    if agr.status == "consent":
        return [item("attest_agreement", "Read it and record your consent",
                     "It is in its consent stage, and your consent to this version is not recorded yet.")]
    if held:
        return [item("reattest_agreement", "Read the new version and record your consent again",
                     f"It changed to version {agr.version}; your consent was to an earlier version.")]
    return []


def emergency_items(emergency: EmergencyState, caller: Member | None, ecosystem: str | None, clock: Clock) -> list[dict]:
    """Co-signing a pending declaration; a steward's post-emergency review and closing Recovery."""
    if not _active(caller):
        return []
    flags = emergency_api.caller_flags(emergency, caller, clock.now)
    title = _clip(emergency.notes) or f"Emergency in {ecosystem or 'this ecosystem'}"

    def item(action: str, what: str, why: str, **extra) -> dict:
        return _item("emergency", emergency, action=action, what=what, why=why, title=title, ecosystem=ecosystem,
                     clock=clock, **extra)

    if flags["caller_can_cosign"]:
        return [item("cosign_emergency", "Read this emergency declaration and co-sign it if you agree",
                     f"{emergency.declared_by or 'A member'} declared it. It needs a second active member, "
                     "and nothing changes until someone co-signs.", due=emergency_api.cosign_deadline(emergency))]
    # Owner default: the review alarm is a steward's (api/AGENTS.md "Emergency and exit").
    if flags["caller_can_review"] and flags["caller_is_steward"]:
        started = emergency_api.recovery_started(emergency)
        scheduled = emergency.post_review_status == emergency_api.REVIEW_SCHEDULED
        days = emergency_api.RECOVERY_WINDOW_DAYS if scheduled else emergency_api.REVIEW_SCHEDULE_DAYS
        return [item(
            "record_review",
            "Record the post-emergency review as complete once it has happened" if scheduled
            else "Schedule the post-emergency review",
            "You are a steward who did not declare, co-sign or end it, and Recovery does not close by itself.",
            due=started + _dt.timedelta(days=days) if started else None,
        )]
    if flags["caller_can_complete_recovery"]:
        return [item("complete_recovery", "Close Recovery: the review is complete",
                     f"You are a steward of {ecosystem or 'this ecosystem'}; closing Recovery restores normal governance.")]
    return []


def _checkin_days(repair: RepairAgreementRecord, date: _dt.date) -> int | None:
    return next((days for days in conflict_api.REPAIR_CHECKIN_DAYS
                 if getattr(repair, f"checkin_{days}_date") == date), None)


def conflict_items(case: ConflictCase, caller: Member | None, repairs: list[RepairAgreementRecord],
                   ecosystem: str | None, clock: Clock) -> list[dict]:
    """Triage for whoever may triage (a hidden case yields nothing); repair check-ins that have come due."""
    if not _active(caller) or not can_view_conflict(caller, case) or not can_triage_conflict(caller, case):
        return []
    items = []
    if case.status == "reported" or case.status not in conflict_api.CONFLICT_MOVES:
        safety = " It is flagged as a safety concern." if case.safety_flag else ""
        items.append(_item(
            "conflict", case, action="triage_conflict",
            what="Triage this case" if case.status == "reported" else "Check this case and move it to the right stage",
            why=f"You can triage conflicts here, and nobody has picked it up yet.{safety}",
            title=case.title, key=case.case_id, ecosystem=ecosystem, clock=clock,
        ))
    for repair in repairs:
        date, overdue = conflict_api.next_checkin(repair, clock.today)
        if date is None or date > clock.today:
            continue
        days = _checkin_days(repair, date)
        items.append(_item(
            "conflict", case, action="repair_checkin",
            what=f"Record the {days}-day check-in on the repair agreement “{_clip(repair.title, 60)}”",
            why="You can triage this case, and a repair check-in has come due.",
            title=case.title, key=case.case_id, ecosystem=ecosystem, clock=clock, due=date, overdue=overdue,
            part=str(repair.id),
        ))
    return items


def exit_items(record: ExitRecord, caller: Member | None, member_name: str | None, ecosystem: str | None,
               clock: Clock) -> list[dict]:
    """A steward's next move on someone else's exit (exit.EXIT_MOVES); withdrawing is the leaver's, never a task."""
    moves = [move for move in exit_api.allowed_next(record, caller) if move != "cancelled"] if _active(caller) else []
    if not moves:
        return []
    who = member_name or "A member"
    if "unwinding" in moves:
        what, why = "Start the handoff", (
            f"{who} filed an exit; a steward who is not leaving starts the handoff of their roles and commitments.")
    else:
        what, why = "Confirm the departure once roles and commitments are handed over", (
            "The handoff is in progress, and a steward who is not leaving confirms the departure.")
    return [_item("exit", record, action="exit_" + moves[0], what=what, why=why,
                  title=f"{who} is leaving {ecosystem or 'this ecosystem'}", ecosystem=ecosystem, clock=clock,
                  due=record.target_completion_date)]


def audit_items(audit: GovernanceHealthAudit, caller: Member | None, ecosystem: str | None, clock: Clock) -> list[dict]:
    """The caller's own audit draft, which counts only once they publish it."""
    if audit.status != AUDIT_DRAFT or not can_finish_audit(caller, audit):
        return []
    return [_item("audit", audit, action="finish_audit", what="Finish and publish your audit",
                  why="You are its auditor; a draft does not count until you publish it.",
                  title=_audit_title(ecosystem), key=audit.audit_id, ecosystem=ecosystem, clock=clock)]


def _audit_title(ecosystem: str | None) -> str:
    """FX-Maint (F14): an audit item is about an ecosystem's health; its scope ("full") is detail, never the title."""
    return f"Governance health of {ecosystem or 'this ecosystem'}"


# ---------------------------------------------------------------------------
# The queue
# ---------------------------------------------------------------------------


async def ecosystem_names(session, ecosystem_ids) -> dict[uuid.UUID, str]:
    ids = list(ecosystem_ids)
    if not ids:
        return {}
    return {row.id: row.name for row in await session.execute(
        select(Ecosystem.id, Ecosystem.name).where(Ecosystem.id.in_(ids)))}


async def _member_names(session, member_ids) -> dict[uuid.UUID, str]:
    ids = [member_id for member_id in member_ids if member_id is not None]
    if not ids:
        return {}
    return dict((await session.execute(select(Member.id, Member.display_name).where(Member.id.in_(ids)))).all())


async def _repairs_by_case(session, case_ids) -> dict[uuid.UUID, list[RepairAgreementRecord]]:
    """Repair agreements per case, loaded explicitly (async sessions cannot lazy-load the relationship)."""
    found: dict[uuid.UUID, list[RepairAgreementRecord]] = {}
    if case_ids:
        rows = (await session.execute(select(RepairAgreementRecord).where(
            RepairAgreementRecord.conflict_case_id.in_(list(case_ids))
        ).order_by(RepairAgreementRecord.created_at))).scalars()
        for repair in rows:
            found.setdefault(repair.conflict_case_id, []).append(repair)
    return found


@dataclass(frozen=True)
class QueueScope:
    """What a queue item source sees: the caller's active rows by ecosystem, their names, the clock and the asked-for ids."""

    user_id: uuid.UUID
    callers: dict[uuid.UUID, Member]
    names: dict[uuid.UUID, str]
    clock: Clock
    wanted: set[uuid.UUID] | None  # None: every membership; sources that read non-active rows must respect it


# Registry pattern: lanes add queue items by registering a source in their own section, never by editing waiting_for.
_ITEM_SOURCES: list = []


def item_source(*kinds: tuple[str, int]):
    """Register `async def source(session, scope: QueueScope) -> list[dict]` and its kinds' queue order."""
    def register(source):
        _KIND_ORDER.update(dict(kinds))
        _ITEM_SOURCES.append(source)
        return source
    return register


def _queue_order(item: dict) -> tuple:
    """Overdue first, then FIRST_TIER (acts only this caller's role can take, and acts someone else waits on), then
    the nearest due date (undated last), the more urgent kind, the earlier step (_STEP_ORDER) and the title."""
    return (not item["overdue"], item["action"] not in FIRST_TIER, item["due"] is None, item["due"] or "",
            _KIND_ORDER.get(item["kind"], 9), _STEP_ORDER.get(item["action"], 0), item["title"])


async def waiting_for(session, user_id: uuid.UUID | None, ecosystem_ids=None, *, now: _dt.datetime | None = None) -> list[dict]:
    """Every item the caller should act on, in the ecosystems where they are an active member.

    `ecosystem_ids` narrows the scope (REST passes the authorized ids); None means every active membership.
    """
    if user_id is None:
        return []
    clock = Clock.at(now)
    wanted = None if ecosystem_ids is None else {uuid.UUID(str(e)) for e in ecosystem_ids}
    rows = (await session.execute(select(Member).where(
        Member.user_id == user_id, Member.current_status == "active",
    ))).scalars().all()
    callers = {row.ecosystem_id: row for row in rows if wanted is None or row.ecosystem_id in wanted}
    if not callers:  # no active row in scope: only the registered sources can still apply (a newcomer's joining steps)
        return await _sourced(session, QueueScope(user_id=user_id, callers={}, names={}, clock=clock, wanted=wanted), [])
    scope = list(callers)
    names = await ecosystem_names(session, scope)
    items: list[dict] = []

    for prop in (await session.execute(select(Proposal).where(
        Proposal.ecosystem_id.in_(scope),
        or_(Proposal.status.in_(("advice", "consent", "test")),
            and_(Proposal.status == "ratified", Proposal.registered_agreement_id.is_(None))),  # to register
    ).order_by(Proposal.created_at))).scalars():
        items += await proposal_items(session, prop, callers[prop.ecosystem_id], names.get(prop.ecosystem_id), clock)

    consents: dict[uuid.UUID, list[AgreementMemberConsent]] = {}
    for consent in (await session.execute(select(AgreementMemberConsent).where(
        AgreementMemberConsent.member_id.in_([row.id for row in callers.values()]),
    ))).scalars():
        consents.setdefault(consent.agreement_id, []).append(consent)
    for agr in (await session.execute(select(Agreement).where(
        Agreement.ecosystem_id.in_(scope), Agreement.status.in_(CONSENT_OPEN_STATUSES),
    ).order_by(Agreement.created_at))).scalars():
        items += agreement_items(agr, callers[agr.ecosystem_id], consents.get(agr.id, []), names.get(agr.ecosystem_id), clock)

    for emergency in (await session.execute(select(EmergencyState).where(
        EmergencyState.ecosystem_id.in_(scope), emergency_api.live_condition(clock.now),
    ))).scalars():
        items += emergency_items(emergency, callers[emergency.ecosystem_id], names.get(emergency.ecosystem_id), clock)

    cases = [case for case in (await session.execute(select(ConflictCase).where(
        ConflictCase.ecosystem_id.in_(scope), ConflictCase.status.is_distinct_from("closed"),
    ).order_by(ConflictCase.created_at))).scalars() if can_triage_conflict(callers[case.ecosystem_id], case)]
    repairs = await _repairs_by_case(session, [case.id for case in cases])
    for case in cases:
        items += conflict_items(case, callers[case.ecosystem_id], repairs.get(case.id, []), names.get(case.ecosystem_id), clock)

    exits = (await session.execute(select(ExitRecord).where(
        ExitRecord.ecosystem_id.in_(scope), ExitRecord.status.in_(exit_api.OPEN_STATUSES),
    ).order_by(ExitRecord.created_at))).scalars().all()
    leavers = await _member_names(session, {record.member_id for record in exits})
    for record in exits:
        items += exit_items(record, callers[record.ecosystem_id], leavers.get(record.member_id),
                            names.get(record.ecosystem_id), clock)

    for audit in (await session.execute(select(GovernanceHealthAudit).where(
        GovernanceHealthAudit.ecosystem_id.in_(scope), GovernanceHealthAudit.status == AUDIT_DRAFT,
    ))).scalars():
        items += audit_items(audit, callers[audit.ecosystem_id], names.get(audit.ecosystem_id), clock)

    return await _sourced(session, QueueScope(user_id=user_id, callers=callers, names=names, clock=clock, wanted=wanted), items)


async def _sourced(session, scope: QueueScope, items: list[dict]) -> list[dict]:
    """`items` plus every registered source's items, in queue order."""
    for source in _ITEM_SOURCES:
        items += await source(session, scope)
    return sorted(items, key=_queue_order)


# ---------------------------------------------------------------------------
# explain(): state, what happens next, who decides, by when, the caller's moves
# ---------------------------------------------------------------------------


def _explanation(kind: str, record, *, key, title, ecosystem, state, next_step, decided_by, due, due_label,
                 open_: bool, your_moves: list[dict], waiting_on_you: list[dict], clock: Clock,
                 overdue: bool | None = None) -> dict:
    return {
        "kind": kind,
        "id": str(record.id),
        "key": key,
        "title": title,
        "ecosystem": ecosystem,
        "status": record.status if kind != "emergency" else record.state,
        "state": state,
        "next_step": next_step,
        "decided_by": decided_by,
        "due": _due_text(due) if open_ else None,
        "due_label": due_label if open_ and due is not None else None,
        "overdue": open_ and (clock.past(due) if overdue is None else overdue),
        "your_moves": your_moves,
        "waiting_on_you": waiting_on_you,
        "link": link(kind, record.id),
    }


def _move(move: str, label: str, *, ready: bool = True, blocked: str | None = None) -> dict:
    return {"move": move, "label": label, "ready": ready, "blocked": blocked}


async def _explain_proposal(session, prop: Proposal, caller, ecosystem, clock) -> dict:
    gates = await proposal_gate_status(session, prop)
    you = await proposal_standing(session, prop, caller)
    facts = await proposal_facts(session, prop)
    stage = PROPOSAL_LIFECYCLE.canonical(prop.status)
    due, due_label = {"advice": (prop.advice_deadline, "Advice deadline"),
                      "consent": (prop.consent_deadline, "Consent deadline")}.get(stage, (None, None))
    moves = [
        _move(m["to"], "Send back for revision" if m["note_required"] else _PROPOSAL_MOVE_LABELS.get(m["to"], m["to"]),
              ready=m["ready"], blocked=m["blocked"])
        for m in proposal_next_moves(prop, gates, caller, today=clock.today)  # the page's buttons (detail `allowed_next`)
    ]
    return _explanation(
        "proposal", prop, key=prop.proposal_id, title=prop.title, ecosystem=ecosystem,
        state=PROPOSAL_STATES.get(stage, prop.status), next_step=proposal_next_step(prop, gates, you, facts),
        decided_by=_proposal_decider(prop, stage, gates, facts),
        due=due, due_label=due_label, open_=stage not in PROPOSAL_LIFECYCLE.terminal, your_moves=moves,
        waiting_on_you=await proposal_items(session, prop, caller, ecosystem, clock), clock=clock,
    )


async def _explain_agreement(session, agr: Agreement, caller, ecosystem, clock) -> dict:
    gates = await agreement_gate_status(session, agr)
    you = await agreement_standing(session, agr, caller)
    moves = []
    if you["can_conduct_ceremonies"]:
        for target in AGREEMENT_LIFECYCLE.manual_targets(agr.status):
            move = AGREEMENT_LIFECYCLE.manual_move(agr.status, target)
            label = "Keep it in force" if (agr.status, target) == ("under_review", "active") else _AGREEMENT_MOVE_LABELS[target]
            ready = move.gate is None or bool(gates[move.gate]["met"])
            blocked = (f"Archiving opens once its sunset ends on {agr.sunset_date.isoformat()}."  # FX-Maint (F5)
                       if move.gate == "sunset_ended" and not ready else None)
            moves.append(_move(target, label, ready=ready, blocked=blocked))
    consents = [] if caller is None else list((await session.execute(select(AgreementMemberConsent).where(
        AgreementMemberConsent.agreement_id == agr.id, AgreementMemberConsent.member_id == caller.id,
    ))).scalars())
    waiting = agreement_items(agr, caller, consents, ecosystem, clock)
    if (caller is not None and caller.current_status in _PARTICIPATING_MEMBER_STATUSES and not you["has_consented"]
            and agr.status in CONSENT_OPEN_STATUSES and _consent_required(agr)):
        # FX-Maint (F2): not a status move; `kind` tells every surface it is the consent act (POST /agreements/:id/consent).
        moves.append({**_move("attest", "Record your consent to this version"), "kind": "consent"})
    in_force = agr.status in ("active", "under_review")
    sunset = agr.status == "sunset"  # G-Maint: the sunset's end is a date, never "overdue" (archiving follows it)
    sunset_over = sunset and _dates.date_passed(agr.sunset_date)
    return _explanation(
        "agreement", agr, key=agr.agreement_id, title=agr.title, ecosystem=ecosystem,
        state=AGREEMENT_STATES.get(agr.status, agr.status), next_step=agreement_next_step(agr, gates, you),
        decided_by=_decider(AGREEMENT_LIFECYCLE, agr.status, gates, "an ecosystem admin or owner")
        or ("An ecosystem admin or owner" if in_force or sunset else None),
        due=agr.review_date if in_force else agr.sunset_date if sunset else None,
        due_label=("Sunset ended" if sunset_over else "Sunset ends") if sunset else "Review date", open_=in_force or sunset,
        overdue=False if sunset else None,
        your_moves=moves, waiting_on_you=waiting + agreement_review_items(agr, caller, ecosystem, clock), clock=clock,
    )


async def _explain_conflict(session, case: ConflictCase, caller, ecosystem, clock) -> dict:
    facilitator = (await _member_names(session, [case.facilitator_id])).get(case.facilitator_id)
    stage = conflict_api.conflict_stage(case, facilitator)
    repairs = (await _repairs_by_case(session, [case.id])).get(case.id, [])
    checkins = [date for date, _ in (conflict_api.next_checkin(r, clock.today) for r in repairs) if date is not None]
    moves = []
    if can_triage_conflict(caller, case):
        moves = [_move(status, _CONFLICT_MOVE_LABELS[status]) for status in conflict_api.allowed_moves(case.status)]
    elif caller is not None and caller.id == case.reporter_id and "closed" in conflict_api.allowed_moves(case.status):
        moves = [_move("closed", "Withdraw your report")]  # the reporter's one move (PUT /conflicts/:id)
    return _explanation(
        "conflict", case, key=case.case_id, title=case.title, ecosystem=ecosystem, state=stage["stage"],
        next_step=stage["next_step"], decided_by=stage["decided_by"], due=min(checkins, default=None),
        due_label="Next repair check-in", open_=case.status != "closed", your_moves=moves,
        waiting_on_you=conflict_items(case, caller, repairs, ecosystem, clock), clock=clock,
    )


_EMERGENCY_DECIDERS = {
    "pending": "A second active member, by co-signing; the declarer or a steward can withdraw it",
    "open": "The timer; the declarer, the co-signer or a steward can end it early",
    "closed": None,
    "withdrawn": None,
}


async def _explain_emergency(session, emergency: EmergencyState, caller, ecosystem, clock) -> dict:
    described = emergency_api.describe(emergency, clock.now)
    phase = described["phase"]
    flags = emergency_api.caller_flags(emergency, caller, clock.now)
    if phase == "recovery":
        decided_by = ("A steward closes Recovery" if emergency.post_review_status == emergency_api.REVIEW_COMPLETE
                      else "A member who did not declare, co-sign or end it records the review; then a steward closes Recovery")
    else:
        decided_by = _EMERGENCY_DECIDERS.get(phase)
    started = emergency_api.recovery_started(emergency)
    due, due_label = {
        "pending": (emergency_api.cosign_deadline(emergency), "Co-sign by"),
        "open": (emergency.auto_revert_at, "Authority ends"),
        "recovery": (started + _dt.timedelta(days=emergency_api.RECOVERY_WINDOW_DAYS) if started else None, "Review due"),
    }.get(phase, (None, None))
    return _explanation(
        "emergency", emergency, key=None, title=_clip(emergency.notes) or f"Emergency in {ecosystem or 'this ecosystem'}",
        ecosystem=ecosystem, state=EMERGENCY_STATES.get(phase, phase), next_step=described["next_step"],
        decided_by=decided_by, due=due, due_label=due_label, open_=phase in ("pending", "open", "recovery"),
        overdue=described["review_overdue"] if phase == "recovery" else None,
        your_moves=[_move(move, label) for flag, move, label in _EMERGENCY_MOVES if flags[flag]],
        waiting_on_you=emergency_items(emergency, caller, ecosystem, clock), clock=clock,
    )


async def _explain_exit(session, record: ExitRecord, caller, ecosystem, clock) -> dict:
    member_name = (await _member_names(session, [record.member_id])).get(record.member_id)
    is_open = record.status in exit_api.OPEN_STATUSES
    title = "Your exit" if caller is not None and caller.id == record.member_id else f"Exit: {member_name or 'a member'}"
    return _explanation(
        "exit", record, key=None, title=title, ecosystem=ecosystem, state=EXIT_STATES.get(record.status, record.status),
        next_step=exit_api.NEXT_STEP.get(record.status, ""),
        decided_by="A steward of this ecosystem who is not leaving; the person leaving can withdraw it" if is_open else None,
        due=record.target_completion_date, due_label="Handoff ends", open_=is_open,
        your_moves=[_move(status, _EXIT_MOVE_LABELS.get(status, status)) for status in exit_api.allowed_next(record, caller)],
        waiting_on_you=exit_items(record, caller, member_name, ecosystem, clock), clock=clock,
    )


_EXPLAINERS = {
    "proposal": _explain_proposal, "agreement": _explain_agreement, "conflict": _explain_conflict,
    "emergency": _explain_emergency, "exit": _explain_exit,
}


async def explain_record(session, kind: str, record, caller: Member | None, *, now: _dt.datetime | None = None) -> dict:
    """State, what happens next, who decides, by when and the caller's own moves for an already-visible record."""
    ecosystem = (await ecosystem_names(session, [record.ecosystem_id])).get(record.ecosystem_id)
    return await _EXPLAINERS[kind](session, record, caller, ecosystem, Clock.at(now))


async def explain(session, request, kind: str, record_id: uuid.UUID) -> dict:
    """explain_record behind each record's own REST visibility rule: a record the caller cannot open is a 404."""
    if kind not in EXPLAIN_KINDS:
        raise ApiError(400, "There is no status to explain for that kind of record.", {"allowed": list(EXPLAIN_KINDS)})
    if kind == "proposal":
        record = await get_scoped_or_404(session, request, Proposal, record_id, label="Proposal")
    elif kind == "agreement":  # the detail page's consent-gate scope (api/AGENTS.md rule 5 exemption)
        record = await get_scoped_or_404(session, request, Agreement, record_id, label="Agreement",
                                         ecosystem_ids=await reachable_ecosystem_ids(session, request, include_pending=True))
    elif kind == "conflict":  # policy.can_view_conflict: a hidden case is "not found"
        record, _ = await conflict_api.load_visible_case(session, request, record_id)
    elif kind == "emergency":
        record = await get_scoped_or_404(session, request, EmergencyState, record_id, label="Emergency record")
    elif kind == "audit":  # G-Maint: as GET /safeguards/audits/:id (every active member of its ecosystem)
        record = await get_scoped_or_404(session, request, GovernanceHealthAudit, record_id, label="Audit")
    else:  # in scope, or the leaver's own exit after they left
        record = await exit_api.load_visible_exit(session, request, record_id)
    return await explain_record(session, kind, record, await caller_in(session, request, record.ecosystem_id))


# ---------------------------------------------------------------------------
# G-Maint: agreement reviews and governance health audits; services/AGENTS.md "Maintenance and health (G-Maint)"
# ---------------------------------------------------------------------------

from types import SimpleNamespace  # noqa: E402

from neos_agent.api.agreement_vocabulary import SUNSET_NOTICE_DAYS as _SUNSET_NOTICE_DAYS  # noqa: E402
from neos_agent.api.policy import (  # noqa: E402
    can_abandon_audit,
    can_administer_ecosystem,
    can_respond_to_audit,
    has_role_at_least,
)
from neos_agent.api.safeguards import AUDIT_PUBLISHED  # noqa: E402
from neos_agent.services import health as _health  # noqa: E402

REVIEW_NOTICE_DAYS = 14  # owner default: admins and owners are told from 14 days before the review date
AUDIT_NOTICE_DAYS = 14  # stewards are told from 14 days before the next audit is due
RESPOND_TO_RATINGS = frozenset({"critical"})  # owner default: only critical indicators raise a steward item


def _review_line(agr: Agreement) -> str:
    """The agreement banner's review sentence (overdue never takes it out of force: framework agreement-review I-J)."""
    if agr.review_date is None:
        return "It has no review date yet."
    if _dates.date_passed(agr.review_date):
        return (f"Its review was due {agr.review_date.isoformat()}; an admin or owner starts it. "
                "It stays in force until the review ends.")
    return f"Its next review is due {agr.review_date.isoformat()}."


def agreement_review_items(agr: Agreement, caller: Member | None, ecosystem: str | None, clock: Clock) -> list[dict]:
    """Start a review (from 14 days before its date), finish one, or archive after the sunset: admins and owners only
    (`can_conduct_agreement_ceremony`, never mods, who could not act on it)."""
    if not _active(caller) or not can_conduct_agreement_ceremony(caller, agr):
        return []

    def item(action: str, what: str, why: str, due, **extra) -> dict:
        return _item("agreement", agr, action=action, what=what, why=why, title=agr.title, key=agr.agreement_id,
                     ecosystem=ecosystem, clock=clock, due=due, **extra)

    if (agr.status == "active" and agr.review_date is not None
            and agr.review_date - _dt.timedelta(days=REVIEW_NOTICE_DAYS) <= clock.today):
        return [item("start_review", "Start its review",
                     f"Its review is due {agr.review_date.isoformat()}, and admins and owners start reviews. Overdue or "
                     "not, it stays in force until the review ends.", agr.review_date)]
    if agr.status == "under_review":
        return [item("finish_review", "Finish its review: keep it in force or start its sunset",
                     "It is under review, and an admin or owner ends the review with written findings.", agr.review_date)]
    if agr.status == "sunset" and agr.sunset_date is not None and clock.past(agr.sunset_date):
        # FX-Maint (F13): nothing is late, so no due date (a past date read as "Due <date>"); `why` names the end.
        return [item("archive_agreement", "Archive it: its sunset has ended",
                     f"Its sunset ended on {agr.sunset_date.isoformat()}, so it can be archived.", None,
                     overdue=False)]
    return []


@item_source(("agreement", 3))
async def review_items(session, scope: QueueScope) -> list[dict]:
    """Review items for the agreements of every ecosystem where the caller is an active admin or owner."""
    ceremony_ecosystems = [eco for eco, row in scope.callers.items() if has_role_at_least(row, "admin")]
    if not ceremony_ecosystems:
        return []
    items: list[dict] = []
    for agr in (await session.execute(select(Agreement).where(
        Agreement.ecosystem_id.in_(ceremony_ecosystems), Agreement.status.in_(("active", "under_review", "sunset")),
    ).order_by(Agreement.created_at))).scalars():
        items += agreement_review_items(agr, scope.callers[agr.ecosystem_id], scope.names.get(agr.ecosystem_id), scope.clock)
    return items


def _audit_rows(audit: GovernanceHealthAudit | None) -> list[dict]:
    rows = audit.indicator_scores if audit is not None else None
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def audit_due_items(ecosystem_id, latest: GovernanceHealthAudit | None, due: _dt.date | None, caller: Member | None,
                    ecosystem: str | None, clock: Clock, *, independent: bool,
                    stale: GovernanceHealthAudit | None = None) -> list[dict]:
    """A steward's reminder, from 14 days before the next audit is due, that someone who is not a steward records it;
    `stale` is a draft that no longer holds it (FX-Maint F6), named so a steward can chase or abandon it."""
    if (not _active(caller) or not can_administer_ecosystem(caller, ecosystem_id) or due is None
            or due - _dt.timedelta(days=AUDIT_NOTICE_DAYS) > clock.today):
        return []
    who = ("Ask a member who is not a steward to record it: stewards do not audit their own ecosystem."
           if independent else "Every active member is a steward, so you can record it yourself as a self-assessment.")
    if stale is not None:
        who += (f" A draft by {stale.auditor or 'a member'} has not moved for {_health.STALE_DRAFT_DAYS} days or its "
                "auditor left: ask them to finish it, or abandon it on its page.")
    record = latest or SimpleNamespace(id=ecosystem_id, ecosystem_id=ecosystem_id)
    item = _item("audit", record, action="audit_due", what="The next governance health audit is due",
                 why=f"Audits run every quarter and after an emergency. {who}",
                 title=_audit_title(ecosystem), ecosystem=ecosystem, clock=clock, due=due)
    item["link"] = ROUTES["audit"].rsplit("/", 1)[0]  # the safeguards page, where an audit is started
    return [item]


def respond_items(audit: GovernanceHealthAudit | None, caller: Member | None, ecosystem: str | None,
                  clock: Clock, *, responded: bool = False) -> list[dict]:
    """Stewards respond to the latest published audit's critical indicators (the recommendations are advice). It clears
    when the stewards record their response on the audit (FX-Maint F7) or a newer audit is published."""
    if (audit is None or audit.status != AUDIT_PUBLISHED or responded or not _active(caller)
            or not can_administer_ecosystem(caller, audit.ecosystem_id)):
        return []
    flagged = [row.get("indicator_name") or row.get("indicator_id") for row in _audit_rows(audit)
               if row.get("status") in RESPOND_TO_RATINGS]
    if not flagged:
        return []
    return [_item("audit", audit, action="respond_to_audit", what="Respond to the critical health indicators",
                  why=(f"The audit published on {audit.audit_date.isoformat() if audit.audit_date else 'its date'} rated "
                       f"{', '.join(flagged)} critical. Record the stewards' response on the audit (it can name a "
                       "proposal); the recommendations are advice."),
                  title=_audit_title(ecosystem), key=audit.audit_id, ecosystem=ecosystem, clock=clock)]


async def _responded(session, audit: GovernanceHealthAudit | None) -> bool:
    return audit is not None and await _health.audit_record(session, audit.id, _health.AUDIT_RESPONSE_SKILL) is not None


@item_source(("audit", 5))
async def health_items(session, scope: QueueScope) -> list[dict]:
    """Audit due and critical indicators, for the stewards of each ecosystem (policy.can_administer_ecosystem: mod+ or
    a co_creator/builder row there, the audit independence rule's steward)."""
    items: list[dict] = []
    for eco_id, caller in scope.callers.items():
        if not can_administer_ecosystem(caller, eco_id):
            continue
        latest = await _health.latest_published_audit(session, eco_id)
        live, stale = await _health.audit_drafts(session, eco_id, scope.clock.now)
        if not live:  # a live draft (recent, its auditor still here) means someone is already recording it
            items += audit_due_items(eco_id, latest, await _health.audit_due_date(session, eco_id, latest), caller,
                                     scope.names.get(eco_id), scope.clock,
                                     independent=await _health.has_independent_member(session, eco_id),
                                     stale=stale[0] if stale else None)
        items += respond_items(latest, caller, scope.names.get(eco_id), scope.clock,
                               responded=await _responded(session, latest))
    return items


async def _explain_audit(session, audit: GovernanceHealthAudit, caller, ecosystem, clock) -> dict:
    """The audit banner: draft, abandoned or published, critical count, next audit due, who responds."""
    published = audit.status == AUDIT_PUBLISHED
    rows = _audit_rows(audit)
    critical = [row.get("indicator_name") or row.get("indicator_id") for row in rows
                if row.get("status") in RESPOND_TO_RATINGS]
    due, waiting = None, audit_items(audit, caller, ecosystem, clock)
    moves = []
    if published:
        latest = await _health.latest_published_audit(session, audit.ecosystem_id)
        is_latest = latest is not None and latest.id == audit.id
        response = await _health.audit_record(session, audit.id, _health.AUDIT_RESPONSE_SKILL)
        if is_latest:
            due = await _health.audit_due_date(session, audit.ecosystem_id, latest)
            waiting += respond_items(audit, caller, ecosystem, clock, responded=response is not None)
        parts = [f"Published on {audit.audit_date.isoformat() if audit.audit_date else 'its date'}: its values are "
                 "frozen as they were then, beside the auditor's ratings."]
        parts.append(f"{counted(len(critical), 'indicator')} rated critical ({', '.join(critical)}): the stewards "
                     "record their response here; the recommendations are advice." if critical
                     else "No indicator was rated critical; the recommendations are advice.")
        if response is not None:
            parts.append(f"The stewards' response was recorded by {response.recorder or 'a steward'}"
                         f"{' on ' + response.date.isoformat() if response.date else ''}.")
        elif can_respond_to_audit(caller, audit):
            moves.append(_move("respond", "Record the stewards' response"))  # POST /safeguards/audits/:id/respond
        if getattr(audit, "self_assessment", False):
            parts.append("It is a self-assessment: a steward recorded it because no member who is not a steward could.")
        if not is_latest:
            parts.append("A newer audit has been published since.")
        state = "Published"
        decided_by = "Stewards of this ecosystem, by recording a response" if critical and response is None else None
    elif audit.status == _health.AUDIT_ABANDONED:
        abandoned = await _health.audit_record(session, audit.id, _health.AUDIT_ABANDON_SKILL)
        parts = ["It was abandoned as a draft and never counted"
                 + (f": {abandoned.recorder or 'a steward'} recorded why ({_clip(abandoned.ratio_decidendi, 160)})."
                    if abandoned is not None else ".")]
        state, decided_by = "Abandoned", None
    else:
        parts = ["It is a draft: it counts only once its auditor publishes it. Publishing freezes the computed values "
                 "beside the auditor's ratings; every indicator with data needs a rating. Its auditor or a steward "
                 "can abandon it with a reason."]
        state, decided_by = "Draft", f"Its auditor, {audit.auditor or 'the member recording it'}"
        if can_finish_audit(caller, audit):
            moves.append(_move("publish", "Publish audit"))
        if can_abandon_audit(caller, audit):
            moves.append(_move("abandon", "Abandon this draft"))  # POST /safeguards/audits/:id/abandon
    return _explanation(
        "audit", audit, key=audit.audit_id, title=_audit_title(ecosystem), ecosystem=ecosystem,
        state=state, next_step=" ".join(parts), decided_by=decided_by, due=due, due_label="Next audit due",
        open_=due is not None, your_moves=moves, waiting_on_you=waiting, clock=clock,
    )


_EXPLAINERS["audit"] = _explain_audit


# G-Onboard: newcomers in the queue, both directions; services/AGENTS.md "Member lifecycle (G-Onboard)"

from neos_agent.api.policy import can_manage_onboarding, can_move_member  # noqa: E402
from neos_agent.db.course_models import Quiz, QuizResult  # noqa: E402
from neos_agent.db.models import JourneyMap, UserJourneyProgress  # noqa: E402
from neos_agent.services.agreement_consent import missing_agreement_consents  # noqa: E402

NEWCOMER_DAYS = 30  # a member's first month: orientation and the entry quiz are offered in the queue
ROUTES.setdefault("newcomer", "/members")  # the record of a newcomer item is a member row
_JOIN_WHY = "Consenting to its membership agreements is what makes you an active member; nobody needs to approve you."


def _newcomer_item(row: Member, *, action: str, title: str, what: str, why: str, ecosystem: str | None, clock: Clock,
                   link_to: str, part: str | None = None) -> dict:
    """A queue item about a membership row; `link_to` is the page that acts on it."""
    item = _item("newcomer", row, action=action, title=title, what=what, why=why, ecosystem=ecosystem, clock=clock,
                 part=part)
    item["link"] = link_to
    return item


@item_source(("newcomer", 2))
async def joining_items(session, scope: QueueScope) -> list[dict]:
    """The caller's own pending memberships: one item per agreement left to consent to, else "finish joining"."""
    rows = [row for row in (await session.execute(select(Member).where(
        Member.user_id == scope.user_id, Member.current_status == "pending_consent",
    ).order_by(Member.created_at))).scalars() if scope.wanted is None or row.ecosystem_id in scope.wanted]
    names = await ecosystem_names(session, {row.ecosystem_id for row in rows})
    items: list[dict] = []
    for row in rows:
        ecosystem = names.get(row.ecosystem_id)
        missing = await missing_agreement_consents(session, row.id, row.ecosystem_id, "ecosystem")
        for agreement in missing:
            items.append(_newcomer_item(
                row, action="consent_to_join", part=str(agreement.id), title=f"Consent to {agreement.title}",
                what=f"Read and consent to {agreement.title} to finish joining {ecosystem}.", why=_JOIN_WHY,
                ecosystem=ecosystem, clock=scope.clock, link_to=link("agreement", agreement.id)))
        if not missing:
            items.append(_newcomer_item(
                row, action="finish_joining", title=f"Finish joining {ecosystem}",
                what="Nothing is left to consent to: check your membership to become active.", why=_JOIN_WHY,
                ecosystem=ecosystem, clock=scope.clock, link_to="/welcome/consent"))
    return items


@item_source(("newcomer", 2))
async def stuck_newcomer_items(session, scope: QueueScope) -> list[dict]:
    """Stewards step in only when a newcomer is stuck: pending with nothing left to consent to (owner decision)."""
    stewarded = {ecosystem_id: row for ecosystem_id, row in scope.callers.items()
                 if can_manage_onboarding(row, ecosystem_id)}  # FX-Onboard: founders included, as the Newcomers list
    if not stewarded:
        return []
    items: list[dict] = []
    for row in (await session.execute(select(Member).where(
        Member.ecosystem_id.in_(list(stewarded)), Member.current_status == "pending_consent",
    ).order_by(Member.created_at))).scalars():
        if not can_move_member(stewarded[row.ecosystem_id], row):
            continue
        if await missing_agreement_consents(session, row.id, row.ecosystem_id, "ecosystem"):
            continue  # consenting activates them by itself; nothing for a steward to do
        ecosystem = scope.names.get(row.ecosystem_id)
        items.append(_newcomer_item(
            row, action="confirm_membership", title=f"Confirm {row.display_name}'s membership",
            what=f"{row.display_name} is waiting to join {ecosystem} with nothing left to consent to.",
            why=("Consent makes newcomers active by itself, but their gate emptied after they asked to join "
                 f"(an agreement ended or stopped being required). Ask {row.display_name} to press Check my "
                 "membership on their consent page, which makes them active, or confirm them on their member page."),
            ecosystem=ecosystem, clock=scope.clock, link_to=f"/members/{row.id}"))
    return items


@item_source(("newcomer", 2))
async def first_month_items(session, scope: QueueScope) -> list[dict]:
    """A new active member's first steps (first 30 days): the orientation journey and the entry quiz, until done."""
    since = scope.clock.now - _dt.timedelta(days=NEWCOMER_DAYS)
    rows = [row for row in scope.callers.values()
            if row.created_at is not None and _dates.naive_utc(row.created_at) >= since]
    if not rows:
        return []
    eco_ids, row_ids = [row.ecosystem_id for row in rows], [row.id for row in rows]
    with_journeys = set((await session.scalars(select(JourneyMap.ecosystem_id).where(
        JourneyMap.ecosystem_id.in_(eco_ids), JourneyMap.is_active.is_(True)))).all())
    oriented = set((await session.scalars(select(UserJourneyProgress.member_id).where(
        UserJourneyProgress.member_id.in_(row_ids), UserJourneyProgress.status == "complete"))).all())
    entry_quizzes = {quiz.ecosystem_id: quiz for quiz in (await session.scalars(select(Quiz).where(
        Quiz.ecosystem_id.in_(eco_ids), Quiz.is_entry_quiz.is_(True), Quiz.is_published.is_(True),
    ).order_by(Quiz.created_at))).all()}
    passed = set((await session.execute(select(QuizResult.member_id, QuizResult.quiz_id).where(
        QuizResult.member_id.in_(row_ids), QuizResult.is_passed.is_(True)))).all())
    items: list[dict] = []
    for row in rows:  # the journey before the quiz that checks it: _STEP_ORDER keeps that order in the queue
        ecosystem = scope.names.get(row.ecosystem_id)
        orienting = row.ecosystem_id in with_journeys and row.id not in oriented
        if orienting:
            items.append(_newcomer_item(
                row, action="start_orientation", title=f"Walk through {ecosystem}'s orientation",
                what=f"Take the orientation journey to learn how {ecosystem} works.",
                why="New members get to know the ecosystem's ethos and ways of working in their first month.",
                ecosystem=ecosystem, clock=scope.clock, link_to=f"/orientation/{row.ecosystem_id}"))
        quiz = entry_quizzes.get(row.ecosystem_id)
        if quiz is not None and (row.id, quiz.id) not in passed:
            items.append(_newcomer_item(
                row, action="take_entry_quiz", part=str(quiz.id), title=f"Take {quiz.title}",
                what=f"{ecosystem}'s entry quiz checks what the orientation covered.",
                why=("Take it after you finish the orientation journey: it asks about what the journey covers. "
                     if orienting else "") + "Its stewards chose this quiz for newcomers.",
                ecosystem=ecosystem, clock=scope.clock, link_to=f"/quiz/take/{quiz.id}"))
    return items


# ---------------------------------------------------------------------------
# G-Exchange: answers to posts, "Still open?", collaboration approvals and reviews; services/AGENTS.md
# "Exchange (G-Exchange)"
# ---------------------------------------------------------------------------

from types import SimpleNamespace  # noqa: E402,F811  (a collaboration item names one side's ecosystem)

from neos_agent.api.policy import is_exchange_steward as _is_exchange_steward  # noqa: E402
from neos_agent.db.models import (  # noqa: E402
    Collaboration as _Collaboration,
    CollaborationApproval as _CollaborationApproval,
    ConversationLink as _ConversationLink,
    ConversationParticipant as _ConversationParticipant,
    Domain as _Domain,
    Message as _Message,
    SharesNeeds as _SharesNeeds,
)
from neos_agent.services import exchange as _exchange  # noqa: E402

ROUTES.setdefault("share_need", "/discover/shares-needs")
ROUTES.setdefault("collaboration", "/discover/collaborations")


def _post_link(post) -> str:
    """Discover opens a post's detail from ?post= (the client has no /discover/shares-needs/:id route)."""
    return f"/discover?tab=shares-needs&post={post.id}"


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


@item_source(("share_need", 7))
async def exchange_post_items(session, scope: QueueScope) -> list[dict]:
    """The author's queue: unread answers to their posts (one per conversation), and "Still open?" after 90 days."""
    authors = {row.id: row for row in scope.callers.values()}
    if not authors:
        return []
    items: list[dict] = []
    answers = (await session.execute(
        select(_ConversationLink.conversation_id, _ConversationLink.created_by, _SharesNeeds,
               _ConversationParticipant.last_read_at)
        .join(_SharesNeeds, _SharesNeeds.id == _ConversationLink.entity_id)
        .join(_ConversationParticipant, and_(
            _ConversationParticipant.conversation_id == _ConversationLink.conversation_id,
            _ConversationParticipant.member_id == _SharesNeeds.author_member_id))
        .where(_ConversationLink.entity_type == _exchange.SHARE_NEED_LINK,
               _SharesNeeds.author_member_id.in_(list(authors)))
        .order_by(_ConversationLink.created_at)
    )).all()
    responders = await _member_names(session, {row.created_by for row in answers})
    for conversation_id, responder_id, post, last_read in answers:
        unread = select(func.count(_Message.id)).where(
            _Message.conversation_id == conversation_id, _Message.deleted_at.is_(None),
            _Message.sender_id.notin_(list(authors)))
        if last_read is not None:
            unread = unread.where(_Message.created_at > last_read)
        count = (await session.execute(unread)).scalar() or 0
        if not count:
            continue
        who = responders.get(responder_id) or "Someone"
        item = _item("share_need", post, action="read_response", part=str(conversation_id), title=post.title,
                     what=f"{who} answered your {post.type}: {_clip(post.title)}",
                     why=(f"{_plural(count, 'unread message')} in Messages. Reply there, and mark the post "
                          "fulfilled once it is met."),
                     ecosystem=scope.names.get(post.ecosystem_id), clock=scope.clock, overdue=False)
        item["link"] = f"/messaging?conversation={conversation_id}"
        items.append(item)
    for post in (await session.execute(select(_SharesNeeds).where(
        _SharesNeeds.author_member_id.in_(list(authors)), _SharesNeeds.status == _exchange.OPEN,
        _SharesNeeds.hidden_at.is_(None),
    ).order_by(_SharesNeeds.created_at))).scalars():
        check_date = _exchange.open_since(post).date() + _dt.timedelta(days=_exchange.STALE_AFTER_DAYS)
        if scope.clock.today < check_date:
            continue
        item = _item("share_need", post, action="still_open", title=post.title,
                     what=f"Still open? {_clip(post.title)}",
                     why=(f"It has been open {_exchange.STALE_AFTER_DAYS} days or more. Keep it open, mark it "
                          "fulfilled, or withdraw it."),
                     ecosystem=scope.names.get(post.ecosystem_id), clock=scope.clock, due=None, overdue=False)  # the age is in the text; a past date would read as missed
        item["link"] = _post_link(post)
        items.append(item)
    return items


@item_source(("collaboration", 6))
async def exchange_collaboration_items(session, scope: QueueScope) -> list[dict]:
    """Stewards: approve a proposed collaboration for their side; review an active one once its review date passed."""
    side_domains = select(_Domain.id).where(_Domain.ecosystem_id.in_(list(scope.callers)))
    collaborations = (await session.execute(select(_Collaboration).where(
        _Collaboration.status.in_(("proposed", "active")),
        or_(_Collaboration.source_domain_id.in_(side_domains), _Collaboration.target_domain_id.in_(side_domains)),
    ).order_by(_Collaboration.created_at))).scalars().all()
    if not collaborations:
        return []
    domains = {d.id: d for d in (await session.execute(select(_Domain).where(_Domain.id.in_(
        {c.source_domain_id for c in collaborations} | {c.target_domain_id for c in collaborations})))).scalars()}
    approved: dict = {}
    for approval in (await session.execute(select(_CollaborationApproval).where(
            _CollaborationApproval.collaboration_id.in_([c.id for c in collaborations])))).scalars():
        approved.setdefault(approval.collaboration_id, set()).add(approval.ecosystem_id)
    proposer_ids = {c.proposed_by_member_id for c in collaborations if c.proposed_by_member_id}
    proposers = dict((await session.execute(
        select(Member.id, Member.user_id).where(Member.id.in_(proposer_ids)))).all()) if proposer_ids else {}
    items: list[dict] = []
    for collab in collaborations:
        source, target = domains.get(collab.source_domain_id), domains.get(collab.target_domain_id)
        if source is None or target is None:
            continue
        sides = _exchange.Sides(source=source, target=target)
        if collab.status == "proposed":
            for eco in sides.ecosystems:
                if eco in approved.get(collab.id, set()) or not _exchange._may_approve(
                        scope.callers.get(eco), eco, sides, proposers.get(collab.proposed_by_member_id)):
                    continue
                items.append(_item(
                    "collaboration", SimpleNamespace(id=collab.id, ecosystem_id=eco), action="approve_collaboration",
                    part=str(eco), title=collab.title,
                    what=f"Approve the collaboration “{_clip(collab.title)}” for {scope.names.get(eco)}",
                    why="It starts once a steward of each side approves; you can also end it with a reason.",
                    ecosystem=scope.names.get(eco), clock=scope.clock, overdue=False))
        elif collab.review_date is not None and scope.clock.past(collab.review_date):
            eco = next((e for e in sides.ecosystems if _is_exchange_steward(scope.callers.get(e), e)), None)
            if eco is not None:
                items.append(_item(
                    "collaboration", SimpleNamespace(id=collab.id, ecosystem_id=eco), action="review_collaboration",
                    title=collab.title, what=f"Review or end the collaboration “{_clip(collab.title)}”",
                    why=("Its review date has passed: record a review with the next review date, or end it as "
                         "completed or dissolved with a reason."),
                    ecosystem=scope.names.get(eco), clock=scope.clock, due=collab.review_date))
    return items
