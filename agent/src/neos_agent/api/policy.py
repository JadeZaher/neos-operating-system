"""Authorization rules: one definition per governance action; see api/AGENTS.md "Handler contracts"."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import datetime
    import uuid

    from neos_agent.db.models import Agreement, Domain, Member, Proposal

# Policy pattern: pure predicates over the caller's Member row in the resource's ecosystem.

# Ordered lookup table: per-ecosystem role tiers by privilege.
ROLE_RANK = {"user": 0, "mod": 1, "admin": 2, "owner": 3}

# Global profiles that bootstrap administration until owners are designated.
PROFILE_ADMINS = frozenset({"co_creator", "builder"})

_NO_RANK = -1


def role_rank(member: Member | None) -> int:
    """The member's tier as a number; no member, or an unknown role, ranks below 'user'."""
    if member is None:
        return _NO_RANK
    return ROLE_RANK.get(member.role, _NO_RANK)


def has_role_at_least(member: Member | None, minimum_role: str) -> bool:
    """True when the member's tier is `minimum_role` or higher."""
    return role_rank(member) >= ROLE_RANK[minimum_role]


def is_profile_admin(member: Member | None) -> bool:
    """True for the co_creator/builder bootstrap profiles."""
    return member is not None and member.profile in PROFILE_ADMINS


def is_steward(member: Member | None) -> bool:
    """Moderator or above in the row's OWN ecosystem; pass a caller_in row (it checks no ecosystem)."""
    return has_role_at_least(member, "mod")


def is_steward_in(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """Moderator or above in `ecosystem_id`; a row from another ecosystem fails closed."""
    return member is not None and member.ecosystem_id == ecosystem_id and is_steward(member)


def _same_ecosystem(member: Member | None, resource) -> bool:
    """A row from another ecosystem never qualifies (request.ctx.member can be one)."""
    return member is not None and member.ecosystem_id == resource.ecosystem_id


def is_proposal_author(member: Member | None, proposal: Proposal) -> bool:
    """True when the member row is the proposal's recorded author."""
    return (
        member is not None
        and proposal.proposer_member_id is not None
        and member.id == proposal.proposer_member_id
    )


def can_manage_proposal(member: Member | None, proposal: Proposal) -> bool:
    """Edit or move a proposal: its author or a steward; no author link means steward-only."""
    if not _same_ecosystem(member, proposal):
        return False
    return is_proposal_author(member, proposal) or is_steward(member)


def is_domain_steward(member: Member | None, domain: Domain) -> bool:
    """True when the member row is the domain's recorded steward."""
    return member is not None and domain.steward_id == member.id


def can_edit_domain(member: Member | None, domain: Domain) -> bool:
    """Edit a domain: its steward or an ecosystem steward."""
    if not _same_ecosystem(member, domain):
        return False
    return is_domain_steward(member, domain) or is_steward(member)


def can_conduct_agreement_ceremony(member: Member | None, agreement: Agreement) -> bool:
    """Move an agreement through its ceremonies: an active admin or owner."""
    return (
        _same_ecosystem(member, agreement)
        and member.current_status == "active"
        and has_role_at_least(member, "admin")
    )


def can_bootstrap_roles(caller: Member | None, *, ecosystem_has_owner: bool, founder_id: uuid.UUID | None) -> bool:
    """Grant any tier before an owner exists: only the ecosystem's founder, holding a profile-admin profile."""
    return (
        not ecosystem_has_owner
        and is_profile_admin(caller)
        and founder_id is not None
        and caller.id == founder_id
    )


def can_assign_role(caller: Member | None, target: Member, new_role: str, *,
                    ecosystem_has_owner: bool = True, founder_id: uuid.UUID | None = None) -> bool:
    """Set `target`'s tier (owner decision): only below your own rank, and only an owner grants owner.

    You may step yourself down. The founder bootstraps while the ecosystem has no owner (api/AGENTS.md "Role grants").
    """
    if new_role not in ROLE_RANK or not _same_ecosystem(caller, target):
        return False
    if can_bootstrap_roles(caller, ecosystem_has_owner=ecosystem_has_owner, founder_id=founder_id):
        return True
    own_rank = role_rank(caller)
    if caller.id == target.id:
        return ROLE_RANK[new_role] < own_rank
    if role_rank(target) >= own_rank:
        return False
    if new_role == "owner":
        return own_rank == ROLE_RANK["owner"]
    return ROLE_RANK[new_role] < own_rank


# BE-Groups

def can_update_ecosystem(member: Member | None, *, stewards_a_domain: bool, member_count: int) -> bool:
    """Edit ecosystem settings: a domain steward there, or the founding sole member (pass a caller_in row)."""
    return member is not None and (stewards_a_domain or member_count <= 1)


def can_create_domain(member: Member | None) -> bool:
    """Create a domain: a moderator or above in the row's own ecosystem (pass a caller_in row)."""
    return is_steward(member)


# BE-ACT

def can_participate(member: Member | None, resource) -> bool:
    """Advise, record a consent position or report a test on `resource`: an ACTIVE member row in its ecosystem."""
    return _same_ecosystem(member, resource) and member.current_status == "active"


def is_consent_pending_in(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """The row waits on the consent gate in `ecosystem_id` (owner rule: a pending newcomer reads, never acts)."""
    return member is not None and member.ecosystem_id == ecosystem_id and member.current_status == "pending_consent"


def is_active_member_in(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """An ACTIVE membership in `ecosystem_id`: draft or edit agreements, record evidence, open cases (pass a caller_in row)."""
    return member is not None and member.ecosystem_id == ecosystem_id and member.current_status == "active"


def can_record_decision(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """Record a decision outside the ACT engine (assistant only; REST mints them through ACT): a steward there."""
    return is_steward_in(member, ecosystem_id)


def can_declare_emergency(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """Declare an emergency in `ecosystem_id`: any active member there (owner decision; a co-signer comes later)."""
    return is_active_member_in(member, ecosystem_id)


# G-Care

# Owner defaults, one line each: who triages conflicts, and whether named parties can read the case.
CONFLICT_TRIAGE_MIN_ROLE = "mod"
CONFLICT_PARTIES_CAN_VIEW = True


def conflict_party_ids(case) -> set[str]:
    """Member ids named as parties; free-text labels never authorize (display names are user-editable)."""
    stored = case.parties
    ids = stored.get("member_ids") if isinstance(stored, dict) else None
    return {str(item).lower() for item in ids or [] if isinstance(item, str)}


def is_conflict_party(member: Member | None, case) -> bool:
    """True when the member's id is among the case's party member ids."""
    return member is not None and str(member.id).lower() in conflict_party_ids(case)


def _active_in_case_ecosystem(member: Member | None, case) -> bool:
    return _same_ecosystem(member, case) and member.current_status == "active"


def can_triage_conflict(member: Member | None, case) -> bool:
    """Triage, move or repair a case: an active steward there or its facilitator, never a named party."""
    if not _active_in_case_ecosystem(member, case) or is_conflict_party(member, case):
        return False
    return has_role_at_least(member, CONFLICT_TRIAGE_MIN_ROLE) or member.id == case.facilitator_id


def can_view_conflict(member: Member | None, case) -> bool:
    """Read a case: its reporter, facilitator, named parties and triage stewards; everyone else sees nothing."""
    if not _active_in_case_ecosystem(member, case):
        return False
    if member.id in (case.reporter_id, case.facilitator_id):
        return True
    if CONFLICT_PARTIES_CAN_VIEW and is_conflict_party(member, case):
        return True
    return can_triage_conflict(member, case)


def can_finish_audit(member: Member | None, audit) -> bool:
    """Edit or publish a draft audit: the member recorded as its auditor (a human; the assistant may only draft)."""
    return (
        _active_in_case_ecosystem(member, audit)
        and str(member.id) in (audit.auditor_ids or [])
    )


# G-Safety

# Owner decision: any active member declares, a second active member co-signs; see api/AGENTS.md "Emergency and exit".
def emergency_actor_ids(emergency) -> set:
    """Member ids that declared, co-signed or ended the emergency (excluded from its review)."""
    actors = {emergency.declared_by_member_id, emergency.co_signer_member_id}
    for entry in emergency.actions_log if isinstance(emergency.actions_log, list) else []:
        if isinstance(entry, dict) and entry.get("action") == "half_open_transition" and entry.get("actor_member_id"):
            actors.add(str(entry["actor_member_id"]))
    return {str(actor) for actor in actors if actor is not None}


def can_cosign_emergency(member: Member | None, emergency) -> bool:
    """Co-sign a pending declaration: an active member there who is not the declarer."""
    return (
        can_declare_emergency(member, emergency.ecosystem_id)
        and member.id != emergency.declared_by_member_id
    )


def can_withdraw_emergency(member: Member | None, emergency) -> bool:
    """Withdraw a declaration still waiting for a co-signer: its declarer or a steward there."""
    return is_active_member_in(member, emergency.ecosystem_id) and (
        member.id == emergency.declared_by_member_id or is_steward(member)
    )


def can_end_emergency(member: Member | None, emergency) -> bool:
    """End emergency authority early (Recovery starts): the declarer, the co-signer or a steward there."""
    return is_active_member_in(member, emergency.ecosystem_id) and (
        member.id in (emergency.declared_by_member_id, emergency.co_signer_member_id) or is_steward(member)
    )


def can_review_emergency(member: Member | None, emergency) -> bool:
    """Record the post-emergency review: an active member there who did not declare, co-sign or end it."""
    return (
        is_active_member_in(member, emergency.ecosystem_id)
        and str(member.id) not in emergency_actor_ids(emergency)
    )


def can_complete_recovery(member: Member | None, emergency) -> bool:
    """Close Recovery once the review is complete: an active steward there."""
    return is_active_member_in(member, emergency.ecosystem_id) and is_steward(member)


def is_exit_leaver(member: Member | None, record) -> bool:
    """True when the member row is the one leaving."""
    return member is not None and member.id == record.member_id


def can_steward_exit(member: Member | None, record) -> bool:
    """Start the handoff or confirm the departure: an active steward there who is not the leaver."""
    return (
        is_active_member_in(member, record.ecosystem_id)
        and is_steward(member)
        and not is_exit_leaver(member, record)
    )


# G-ACT

def can_register_agreement(member: Member | None, proposal: Proposal) -> bool:
    """Register a ratified proposal as an agreement (new or amended): an active steward of its ecosystem."""
    return is_active_member_in(member, proposal.ecosystem_id) and is_steward(member)


def can_record_onboarding_consent(caller: Member | None, member: Member) -> bool:
    """Record onboarding section consent for `member`: the member themselves or a steward of their ecosystem."""
    return _same_ecosystem(caller, member) and (caller.id == member.id or is_steward(caller))


def assignable_roles(caller: Member | None, target: Member, *, ecosystem_has_owner: bool = True,
                     founder_id: uuid.UUID | None = None) -> list[str]:
    """Every tier `caller` may give `target` now, lowest first (the member page's role picker)."""
    return [role for role in ROLE_RANK
            if role != target.role and can_assign_role(caller, target, role, ecosystem_has_owner=ecosystem_has_owner,
                                                       founder_id=founder_id)]


def is_legacy_proposer_named(member: Member | None, proposal: Proposal) -> bool:
    """An unlinked (legacy) proposal whose proposer text is the member's name: a refusal signal only, never a grant."""
    if member is None or proposal.proposer_member_id is not None:
        return False
    name, proposer = (member.display_name or "").strip().lower(), (proposal.proposer or "").strip().lower()
    return bool(name) and name == proposer


def can_confirm_ratification(member: Member | None, proposal: Proposal) -> bool:
    """Confirm Test -> Ratified (owner decision): a steward of its ecosystem who did not write it; never self-certified."""
    return (
        is_steward_in(member, proposal.ecosystem_id)
        and not is_proposal_author(member, proposal)
        and not is_legacy_proposer_named(member, proposal)
    )


def advice_deadline_passed(proposal: Proposal, today: datetime.date) -> bool:
    """The advice deadline is set and has gone by (a date passes on the following day)."""
    return proposal.advice_deadline is not None and proposal.advice_deadline < today


def can_close_advice(member: Member | None, proposal: Proposal, today: datetime.date) -> bool:
    """Close advice (owner decision 2026-11-01): the proposer at any time; another steward only after the advice
    deadline (none set: never); a legacy proposal with no author link, its stewards. See services/AGENTS.md."""
    if not can_manage_proposal(member, proposal):
        return False
    if proposal.proposer_member_id is None or is_proposal_author(member, proposal):
        return True
    return advice_deadline_passed(proposal, today)


def can_set_advice_deadline(member: Member | None, proposal: Proposal) -> bool:
    """Move the advice deadline: only the author when the proposal has one (else a steward could backdate it
    and close advice); a legacy proposal with no author link, whoever can manage it."""
    if not can_manage_proposal(member, proposal):
        return False
    return proposal.proposer_member_id is None or is_proposal_author(member, proposal)


# Profiles that confer administration (PROFILE_ADMINS) are granted, never chosen; see api/AGENTS.md "Role grants".
MEMBER_PROFILES = ("co_creator", "builder", "collaborator", "townhall")


def can_choose_own_profile(member: Member | None, new_profile: str | None) -> bool:
    """Self-service profile edit: any profile that confers no authority, or the one you already hold."""
    return new_profile not in PROFILE_ADMINS or (member is not None and member.profile == new_profile)


def can_grant_profile(caller: Member | None, target: Member, *, ecosystem_has_owner: bool = True,
                      founder_id: uuid.UUID | None = None) -> bool:
    """Set another member's profile (it may confer administration): never your own; whoever may make them an admin."""
    return (
        caller is not None
        and caller.id != target.id
        and can_assign_role(caller, target, "admin", ecosystem_has_owner=ecosystem_has_owner, founder_id=founder_id)
    )
