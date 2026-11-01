"""Authorization rules: one definition per governance action; see api/AGENTS.md "Handler contracts"."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
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


def can_assign_role(caller: Member | None, target: Member, new_role: str) -> bool:
    """Set `target`'s tier: owner or profile admin any; self-demotion; admin only below admin."""
    if new_role not in ROLE_RANK or not _same_ecosystem(caller, target):
        return False
    if is_profile_admin(caller) or role_rank(caller) == ROLE_RANK["owner"]:
        return True
    if caller.id == target.id and ROLE_RANK[new_role] <= role_rank(caller):
        return True
    if role_rank(caller) == ROLE_RANK["admin"]:
        return role_rank(target) < ROLE_RANK["admin"] and ROLE_RANK[new_role] < ROLE_RANK["admin"]
    return False

# BE-Groups

def can_update_ecosystem(member: Member | None, *, stewards_a_domain: bool, member_count: int) -> bool:
    """Edit ecosystem settings: a domain steward there, or the founding sole member (pass a caller_in row)."""
    return member is not None and (stewards_a_domain or member_count <= 1)


def can_create_domain(member: Member | None) -> bool:
    """Create a domain: a moderator or above in the row's own ecosystem (pass a caller_in row)."""
    return is_steward(member)


# BE-ACT

def can_participate(member: Member | None, resource) -> bool:
    """Advise, record a consent position or report a test on `resource`: any member row in its ecosystem."""
    return _same_ecosystem(member, resource)


def is_active_member_in(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """An ACTIVE membership in `ecosystem_id`: draft or edit agreements, record evidence, open cases (pass a caller_in row)."""
    return member is not None and member.ecosystem_id == ecosystem_id and member.current_status == "active"


def can_record_decision(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """Record a decision outside the ACT engine (assistant only; REST mints them through ACT): a steward there."""
    return is_steward_in(member, ecosystem_id)


def can_declare_emergency(member: Member | None, ecosystem_id: uuid.UUID | None) -> bool:
    """Declare an emergency in `ecosystem_id`: any active member there (owner decision; a co-signer comes later)."""
    return is_active_member_in(member, ecosystem_id)
