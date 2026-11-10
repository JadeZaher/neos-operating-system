"""Membership placement and recorded status moves: one path for sign-up, join, return and steward moves.

See services/AGENTS.md "Member lifecycle (G-Onboard)". Nothing here commits; callers own the transaction.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from neos_agent.api.errors import ApiError
from neos_agent.api.policy import MEMBER_MOVES, PROFILE_ADMINS, can_move_member
from neos_agent.db.models import (
    AgreementMemberConsent, Ecosystem, ExitRecord, Member, MemberAlignmentEvent, MemberStatusTransition,
)
from neos_agent.services import dates
from neos_agent.services.agreement_consent import missing_agreement_consents

# Transition triggers: one per kind of membership move (member_status_transitions.trigger).
SIGNUP = "signup"
JOINED = "joined"
GATE_CLEARED = "gate_cleared"
RE_ENTRY = "re_entry"
CONSENT_ACTIVATED = "consent"
CONSENT_WITHDRAWN = "consent_withdrawn"
STEWARD_MOVE = "steward_move"
EXIT_COMPLETED = "exit_completed"
ROLE_GRANT = "role_grant"  # role and profile changes: the member page's role history reads these two
PROFILE_GRANT = "profile_grant"
LEFT_ROLE = "user"  # a member who leaves comes back as a member: no tier, no admin profile, no standing consent

NEW_MEMBER_STATUS = "prospective"  # a first placement's from_status (the Member model's default)
_STATUS_LENGTH = 50  # members.current_status / member_status_transitions.to_status
_ONBOARDING_STATUS = {"pending_consent": "agreement_consent_required", "active": "complete"}

# Machine codes the client and the assistant branch on.
ALREADY_MEMBER = "ALREADY_MEMBER"
CONSENT_REQUIRED = "CONSENT_REQUIRED"
MEMBERSHIP_PAUSED = "MEMBERSHIP_PAUSED"
RE_ENTRY_CLOSED = "RE_ENTRY_CLOSED"
USE_EXIT_FLOW = "USE_EXIT_FLOW"

MOVE_DENIED = "Only a steward of this ecosystem who outranks this member can change their membership, never their own"
STATUS_WORDS = {
    "active": "active", "pending_consent": "waiting on consent", "suspended": "suspended",
    "inactive": "inactive", "exited": "ended", "prospective": "not started",
}


def counts_as_member():
    """A published member count includes a consented, active row and nothing else.

    Pending sign-ups (`pending_consent`), suspended rows, and departed rows (`exited`, `inactive`)
    stay out of the ecosystem, community, and dashboard counts.
    """
    return Member.current_status == "active"
# (from, to) -> (button label, confirmation sentence); {name} and {ecosystem} are filled in.
_MOVE_WORDS = {
    ("active", "suspended"): (
        "Suspend membership",
        "{name} will stop taking part in {ecosystem} (advice, consent, proposals) until a steward restores them.",
    ),
    ("suspended", "active"): ("Restore membership", "{name} becomes an active member of {ecosystem} again."),
    ("inactive", "active"): ("Reactivate membership", "{name} becomes an active member of {ecosystem} again."),
    ("pending_consent", "active"): (
        "Confirm membership",
        "{name} has nothing left to consent to. Confirming makes them an active member of {ecosystem}.",
    ),
}


def agreement_brief(agreement) -> dict:
    """The {id, title, version} shape every consent-gate payload uses."""
    return {"id": str(agreement.id), "title": agreement.title, "version": agreement.version}


def record_transition(session, member: Member, to_status: str, *, trigger: str, actor: Member | None = None,
                      notes: str | None = None) -> MemberStatusTransition | None:
    """Move `member` to `to_status` and add its one MemberStatusTransition; nothing when the status is unchanged."""
    from_status = member.current_status or NEW_MEMBER_STATUS
    if from_status == to_status:
        return None
    row = MemberStatusTransition(
        id=uuid.uuid4(), member_id=member.id, from_status=from_status, to_status=to_status, date=dates.utc_today(),
        trigger=trigger, notes=notes, actor_member_id=actor.id if actor is not None else None,
    )
    member.current_status = to_status
    member.onboarding_status = _ONBOARDING_STATUS.get(to_status, member.onboarding_status)
    session.add(row)
    return row


def grant_record(member: Member, trigger: str, old: str | None, new: str | None, *, actor: Member | None,
                 notes: str | None = None) -> MemberStatusTransition:
    """A recorded role (`ROLE_GRANT`) or profile (`PROFILE_GRANT`) change, "role:<tier>" / "profile:<value>"."""
    prefix = "role:" if trigger == ROLE_GRANT else "profile:"
    return MemberStatusTransition(
        id=uuid.uuid4(), member_id=member.id, date=dates.utc_today(), trigger=trigger, notes=notes,
        actor_member_id=actor.id if actor is not None else None,
        from_status=f"{prefix}{old or ''}"[:_STATUS_LENGTH], to_status=f"{prefix}{new or ''}"[:_STATUS_LENGTH],
    )


async def clear_standing(session, member: Member, *, actor: Member | None, reason: str) -> None:
    """A membership ending: role back to `user`, a co_creator/builder profile cleared, every live agreement consent
    withdrawn (alignment credit reversed, as a member's own withdrawal), each recorded; already clear writes nothing.

    See services/AGENTS.md "Member lifecycle" § FX-Onboard for why consents are withdrawn rather than ignored.
    """
    if member.role != LEFT_ROLE:
        session.add(grant_record(member, ROLE_GRANT, member.role, LEFT_ROLE, actor=actor, notes=reason))
        member.role = LEFT_ROLE
    if member.profile in PROFILE_ADMINS:
        session.add(grant_record(member, PROFILE_GRANT, member.profile, None, actor=actor, notes=reason))
        member.profile = None
    now = dates.utc_now()
    for consent in (await session.execute(select(AgreementMemberConsent).where(
        AgreementMemberConsent.member_id == member.id, AgreementMemberConsent.withdrawn_at.is_(None),
    ).with_for_update())).scalars():
        credit = int(await session.scalar(select(func.coalesce(func.sum(MemberAlignmentEvent.delta), 0)).where(
            MemberAlignmentEvent.agreement_consent_id == consent.id)) or 0)
        consent.revision += 1
        consent.withdrawn_at = now
        consent.withdrawal_reason = reason
        if credit:
            session.add(MemberAlignmentEvent(
                id=uuid.uuid4(), member_id=member.id, ecosystem_id=member.ecosystem_id,
                agreement_consent_id=consent.id, event_kind=f"state:{consent.revision}", delta=-credit, recorded_at=now,
            ))
            member.agreement_alignment_score = max(0, (member.agreement_alignment_score or 0) - credit)


async def end_membership(session, member: Member, *, actor: Member | None, notes: str) -> None:
    """A confirmed exit: the row becomes `exited` (one transition) and its standing is cleared (clear_standing)."""
    if member.current_status == "exited":
        return
    record_transition(session, member, "exited", trigger=EXIT_COMPLETED, actor=actor, notes=notes)
    await clear_standing(session, member, actor=actor, reason=f"Membership ended: {notes}")


@dataclass(frozen=True)
class Placement:
    """What placing a user in an ecosystem did: the row, which move (a trigger), what is left to consent to."""

    member: Member
    outcome: str  # SIGNUP | JOINED | GATE_CLEARED | RE_ENTRY
    missing: list
    created: bool
    join_gates: dict | None = None

    @property
    def status(self) -> str:
        if self.join_gates and self.join_gates["status"] in {"quiz_required", "quiz_unavailable"}:
            return self.join_gates["status"]
        return "consent_required" if self.missing else "joined"


async def _existing_row(session, user_id: uuid.UUID, ecosystem_id: uuid.UUID) -> Member | None:
    """The user's row there, row-locked so two returns or heals run one after the other."""
    return await session.scalar(
        select(Member).where(Member.user_id == user_id, Member.ecosystem_id == ecosystem_id).with_for_update()
    )


async def re_entry_open(session, member: Member) -> bool:
    """A leaver may return unless their latest exit record says otherwise (no record: they may). Nothing writes
    `re_entry_eligible = False` yet, so every leaver may return (services/AGENTS.md "Member lifecycle" § FX-Onboard)."""
    latest = await session.scalar(
        select(ExitRecord).where(ExitRecord.member_id == member.id)
        .order_by(ExitRecord.created_at.desc(), ExitRecord.id.desc()).limit(1)
    )
    return latest is None or bool(latest.re_entry_eligible)


async def place_member(session, *, user_id: uuid.UUID, ecosystem: Ecosystem, display_name: str, member_key: str,
                       trigger: str = JOINED, public_only: bool = True) -> Placement:
    """Sign-up, join and return share this: a new row, a healed pending row or a returning leaver, each with one
    transition; refusals are ApiError (404 private, 409 already in or paused, 403 return closed)."""
    row = await _existing_row(session, user_id, ecosystem.id)
    if row is None:
        if public_only and ecosystem.visibility != "public":
            raise ApiError(404, "Ecosystem not found")
        return await _create_row(session, user_id=user_id, ecosystem=ecosystem, display_name=display_name,
                                 member_key=member_key, trigger=trigger)
    name = ecosystem.name
    if row.current_status == "active":
        raise ApiError(409, f"You are already a member of {name}.", {"code": ALREADY_MEMBER})
    if row.current_status == "pending_consent":
        missing = await missing_agreement_consents(session, row.id, ecosystem.id, "ecosystem")
        from neos_agent.services.join_gates import join_gate_summary, require_join_gates
        gates = await join_gate_summary(session, ecosystem_id=ecosystem.id, member=row)
        require_join_gates(gates)
        if missing:
            raise ApiError(409, f"You have already joined {name}: consent to its agreements to finish.",
                           {"code": CONSENT_REQUIRED, "required_agreements": [agreement_brief(a) for a in missing]})
        record_transition(session, row, "active", trigger=GATE_CLEARED, notes="Nothing was left to consent to")
        from neos_agent.services.join_gates import record_quiz_bypass
        await record_quiz_bypass(session, row, gates)
        return Placement(row, GATE_CLEARED, [], False, gates)
    if row.current_status == "exited":
        if not await re_entry_open(session, row):
            raise ApiError(403, f"Your exit from {name} was recorded as final, so you cannot rejoin by yourself. "
                                f"Ask a steward of {name} if this should change.", {"code": RE_ENTRY_CLOSED})
        # A row that left before exits cleared it still holds its old role, profile and consents.
        await clear_standing(session, row, actor=None, reason="Returned after leaving: starts again as a member")
        missing = await missing_agreement_consents(session, row.id, ecosystem.id, "ecosystem")
        from neos_agent.services.join_gates import join_gate_summary
        gates = await join_gate_summary(session, ecosystem_id=ecosystem.id, member=row)
        record_transition(session, row, "active" if gates["eligible"] else "pending_consent", trigger=RE_ENTRY,
                          notes="Returned after leaving")
        if gates["eligible"]:
            from neos_agent.services.join_gates import record_quiz_bypass
            await record_quiz_bypass(session, row, gates)
        return Placement(row, RE_ENTRY, missing, False, gates)
    words = STATUS_WORDS.get(row.current_status, row.current_status)
    raise ApiError(409, f"Your membership in {name} is {words}. A steward of {name} can restore it.",
                   {"code": MEMBERSHIP_PAUSED})


async def _create_row(session, *, user_id, ecosystem: Ecosystem, display_name: str, member_key: str,
                      trigger: str) -> Placement:
    member = Member(
        id=uuid.uuid4(), user_id=user_id, ecosystem_id=ecosystem.id, member_id=member_key[:100],
        display_name=display_name, current_status=NEW_MEMBER_STATUS,
    )
    try:
        async with session.begin_nested():  # a concurrent join's insert wins; this one becomes a 409, nothing else rolls back
            session.add(member)
    except IntegrityError:
        raise ApiError(409, f"You are already a member of {ecosystem.name}.", {"code": ALREADY_MEMBER}) from None
    missing = await missing_agreement_consents(session, member.id, ecosystem.id, "ecosystem")
    from neos_agent.services.join_gates import join_gate_summary
    gates = await join_gate_summary(session, ecosystem_id=ecosystem.id, member=member)
    record_transition(session, member, "active" if gates["eligible"] else "pending_consent", trigger=trigger)
    if gates["eligible"]:
        from neos_agent.services.join_gates import record_quiz_bypass
        await record_quiz_bypass(session, member, gates)
    return Placement(member, trigger, missing, True, gates)


def placement_payload(placement: Placement, ecosystem_name: str) -> dict:
    """The join/sign-up response: status, outcome, the row's status, plain words and the agreements still to consent to."""
    if placement.join_gates and placement.join_gates["status"] in {"quiz_required", "quiz_unavailable"}:
        message = f"Your membership in {ecosystem_name} is pending. Complete its configured entry requirements to take part."
    elif placement.missing:
        message = (f"Welcome back to {ecosystem_name}. One step left: consent to its current agreements."
                   if placement.outcome == RE_ENTRY else f"One step left: consent to {ecosystem_name}'s agreements.")
    elif placement.outcome == RE_ENTRY:
        message = f"Welcome back to {ecosystem_name}. You are an active member again."
    elif placement.outcome == GATE_CLEARED:
        message = f"Your membership in {ecosystem_name} is active: nothing was left to consent to."
    else:
        message = f"Welcome to {ecosystem_name}! You are now an active member."
    return {
        "status": placement.status,
        "outcome": placement.outcome,
        "membership_status": placement.member.current_status,
        "message": message,
        "ecosystem_name": ecosystem_name,
        "required_agreements": [agreement_brief(agreement) for agreement in placement.missing],
        "join_gates": placement.join_gates,
    }


async def move_refusal(session, target: Member, to_status: str, *, caller: Member | None) -> ApiError | None:
    """Why `caller` cannot move `target` to `to_status` now (checked before a confirmation is asked), or None."""
    if not can_move_member(caller, target):
        return ApiError(403, MOVE_DENIED)
    allowed = sorted(MEMBER_MOVES.get(target.current_status, ()))
    if not isinstance(to_status, str) or not to_status.strip() or len(to_status) > _STATUS_LENGTH:
        return ApiError(400, "Choose one of the listed membership moves.", {"allowed": allowed})
    if to_status == "exited":
        return ApiError(400, "Leaving is the member's own exit, which a steward then completes on the exit page.",
                        {"code": USE_EXIT_FLOW, "allowed": allowed})
    if to_status not in allowed:
        words = STATUS_WORDS.get(target.current_status, target.current_status)
        return ApiError(400, f"A membership that is {words} cannot be set to {STATUS_WORDS.get(to_status, to_status)}.",
                        {"allowed": allowed})
    if to_status == "active":
        from neos_agent.services.join_gates import join_gate_summary, require_join_gates
        try:
            require_join_gates(await join_gate_summary(session, ecosystem_id=target.ecosystem_id, member=target))
        except ApiError as refusal:
            return refusal
    if target.current_status == "pending_consent":
        missing = await missing_agreement_consents(session, target.id, target.ecosystem_id, "ecosystem")
        if missing:
            return ApiError(409, f"{target.display_name} still has agreements to consent to; consenting makes them "
                                 "active, no confirmation needed.",
                            {"code": CONSENT_REQUIRED, "required_agreements": [agreement_brief(a) for a in missing]})
    return None


async def move_member(session, target: Member, to_status: str, *, caller: Member | None,
                      notes: str | None = None) -> MemberStatusTransition:
    """A steward's move through policy.MEMBER_MOVES, recorded with the steward as actor; raises the refusal."""
    refusal = await move_refusal(session, target, to_status, caller=caller)
    if refusal is not None:
        raise refusal
    if to_status == "active":
        from neos_agent.services.join_gates import join_gate_summary, record_quiz_bypass
        gates = await join_gate_summary(session, ecosystem_id=target.ecosystem_id, member=target)
        await record_quiz_bypass(session, target, gates, actor_user_id=caller.user_id if caller else None)
    return record_transition(session, target, to_status, trigger=STEWARD_MOVE, actor=caller,
                             notes=(notes or "").strip() or None)


async def caller_member_moves(session, target: Member, *, caller: Member | None, ecosystem_name: str) -> list[dict]:
    """The moves `caller` may make on `target` now, with the page's label and confirmation sentence."""
    moves = []
    for to_status in sorted(MEMBER_MOVES.get(target.current_status, ())):
        if await move_refusal(session, target, to_status, caller=caller) is not None:
            continue
        label, confirm = _MOVE_WORDS[(target.current_status, to_status)]
        moves.append({"status": to_status, "label": label,
                      "confirm": confirm.format(name=target.display_name, ecosystem=ecosystem_name)})
    return moves
