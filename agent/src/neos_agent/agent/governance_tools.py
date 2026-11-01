"""29 governance MCP-style tools for the NEOS agent.

Each tool is an async function with signature:
    async def handler(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict
State-changing tools also take a keyword-only `caller_user_id` (see CALLER_SCOPED_TOOLS).

Returns {"success": True, "data": {...}} or {"success": False, "error": "..."}.

The module also exports:
- GOVERNANCE_TOOLS: list[ToolDef] with all 29 tool definitions
- get_tool_definitions(): tool defs in Claude API format
- execute_tool(name, args, db_session, ecosystem_ids, caller_user_id): dispatch by name;
  CALLER_SCOPED_TOOLS act as (and refuse without) the signed-in member
"""

from __future__ import annotations

import logging
import math
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import func, select, or_
from sqlalchemy.exc import DataError, IntegrityError, StatementError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from neos_agent.db.models import (
    Agreement,
    AdviceEntry,
    AdviceLog,
    ConflictCase,
    ConsentParticipant,
    ConsentRecord,
    DecisionDissentRecord,
    DecisionParticipant,
    DecisionRecord,
    DecisionSemanticTag,
    Domain,
    Ecosystem,
    EmergencyState,
    ExitRecord,
    GovernanceHealthAudit,
    Member,
    Proposal,
    RepairAgreementRecord,
    User,
)
from neos_agent.api.agreements import transition_agreement as conduct_agreement_transition
from neos_agent.api.domains import CREATE_DENIED as DOMAIN_CREATE_DENIED
from neos_agent.api.policy import (
    can_declare_emergency,
    can_participate,
    can_record_decision,
    is_active_member_in,
    is_proposal_author,
    is_steward_in,
)
from neos_agent.api.proposals import SELF_ADVICE_DENIED
from neos_agent.services.act_gates import TransitionRefused, consent_position, transition_proposal
from neos_agent.services.fingerprint import generate_fingerprint

# Caller-scoped tools act as the signed-in member; see api/AGENTS.md "Chat assistant tools".
CALLER_REQUIRED = "This action needs a signed-in member."
MEMBER_REQUIRED = "Only an active member of this ecosystem can do this."
DECISION_DENIED = "Only an ecosystem steward can record a decision outside the ACT process."
EXIT_SELF_ONLY = "The assistant can only start the signed-in member's own exit."


# Agreement status moves live in services/act_gates.py AGREEMENT_LIFECYCLE (update_agreement_status uses it).

# Default review periods by agreement type (in months)
_REVIEW_MONTHS: dict[str, int] = {
    "space": 12,
    "access": 6,
    "organizational": 24,
    "uaf": 12,
    "culture_code": 12,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today() -> date:
    return date.today()


def _status_priority(status: str) -> int:
    """Lower number = higher priority for search ordering."""
    order = {"active": 0, "test": 1, "consent": 2, "advice": 3, "draft": 4,
             "under_review": 5, "sunset": 6, "archived": 7}
    return order.get(status, 99)


async def _find_member_by_display_name(
    db: AsyncSession, name: str, ecosystem_ids: list | None = None
) -> Member | None:
    """Find an active member by display_name (case-insensitive)."""
    stmt = select(Member).where(
        func.lower(Member.display_name) == name.lower(),
        Member.current_status == "active",
    )
    if ecosystem_ids:
        stmt = stmt.where(Member.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(stmt)
    return result.scalars().first()


async def _find_member_by_member_id(
    db: AsyncSession, member_id: str, ecosystem_ids: list | None = None
) -> Member | None:
    """Find an active member by business key member_id."""
    stmt = select(Member).where(
        Member.member_id == member_id,
        Member.current_status == "active",
    )
    if ecosystem_ids:
        stmt = stmt.where(Member.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(stmt)
    return result.scalars().first()


async def _resolve_member(
    db: AsyncSession, identifier: str, ecosystem_ids: list | None = None
) -> Member | None:
    """Resolve a member by member_id first, then display_name."""
    member = await _find_member_by_member_id(db, identifier, ecosystem_ids)
    if member is None:
        member = await _find_member_by_display_name(db, identifier, ecosystem_ids)
    return member


async def _get_first_ecosystem_id(
    db: AsyncSession, ecosystem_ids: list | None = None
) -> uuid.UUID | None:
    """Return the first ecosystem ID from the caller's scope.

    If no scope is provided (single-ecosystem deployments, internal/test
    callers), fall back to looking up the lone active ecosystem in the DB.
    Returns None only when no scope is given AND the DB doesn't contain
    exactly one ecosystem — callers must handle that as an error.
    """
    if ecosystem_ids:
        return ecosystem_ids[0]
    stmt = select(Ecosystem.id).limit(2)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    if len(rows) == 1:
        return rows[0]
    return None


async def _scoped_ecosystem_id(db: AsyncSession, ecosystem_ids: list | None) -> uuid.UUID | None:
    """The ecosystem a creating tool acts in (first of the scope), as a UUID."""
    eco_id = await _get_first_ecosystem_id(db, ecosystem_ids)
    return uuid.UUID(str(eco_id)) if eco_id is not None else None


async def _caller_row(db: AsyncSession, caller_user_id: uuid.UUID | None, ecosystem_id) -> Member | None:
    """The signed-in user's Member row in `ecosystem_id` (the request-free guards.caller_in)."""
    if caller_user_id is None or ecosystem_id is None:
        return None
    return await db.scalar(select(Member).where(
        Member.user_id == caller_user_id,
        Member.ecosystem_id == uuid.UUID(str(ecosystem_id)),
    ))


async def _find_proposal(db: AsyncSession, key: str, ecosystem_ids: list | None, *options) -> Proposal | None:
    """A proposal by business key (PROP-...) or UUID, as the page links it, within the scope."""
    try:
        match = Proposal.id == uuid.UUID(str(key).strip())
    except ValueError:
        match = Proposal.proposal_id == key
    stmt = select(Proposal).options(*options).where(match)
    if ecosystem_ids:
        stmt = stmt.where(Proposal.ecosystem_id.in_(ecosystem_ids))
    return (await db.execute(stmt)).scalars().first()


def _refusal_text(refusal: TransitionRefused) -> str:
    """The engine's REST refusal as one assistant-readable sentence."""
    allowed = refusal.extra.get("allowed")
    return refusal.message + (f". Allowed: {', '.join(allowed)}." if allowed else "")


# ===================================================================
# TOOL 1: search_agreements
# ===================================================================

async def search_agreements(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Search agreements by type, domain, status, affected_party, date_range."""
    stmt = select(Agreement).options(selectinload(Agreement.ecosystem))

    if ecosystem_ids:
        # Include agreements owned by or shared with the selected ecosystems
        stmt = stmt.where(
            or_(
                Agreement.ecosystem_id.in_(ecosystem_ids),
                Agreement.shared_ecosystem_ids.isnot(None),
            )
        )

    if "type" in args and args["type"]:
        stmt = stmt.where(Agreement.type == args["type"])
    if "status" in args and args["status"]:
        stmt = stmt.where(Agreement.status == args["status"])
    if "domain" in args and args["domain"]:
        stmt = stmt.where(Agreement.domain.ilike(f"%{args['domain']}%"))
    # NOTE: affected_party filtering is done in post-processing below (see affected_party_filter)
    # because JSON containment syntax differs between SQLite and PostgreSQL.
    _affected_party_filter = args.get("affected_party") if "affected_party" in args else None
    if "date_from" in args and args["date_from"]:
        stmt = stmt.where(Agreement.created_date >= args["date_from"])
    if "date_to" in args and args["date_to"]:
        stmt = stmt.where(Agreement.created_date <= args["date_to"])

    stmt = stmt.limit(20)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    # Post-filter shared ecosystem agreements: keep if any selected ecosystem
    # appears in the agreement's shared_ecosystem_ids list
    if ecosystem_ids:
        eco_id_strs = {str(eid) for eid in ecosystem_ids}
        filtered = []
        for a in rows:
            # Always keep agreements owned by a selected ecosystem
            if str(a.ecosystem_id) in eco_id_strs:
                filtered.append(a)
            elif a.shared_ecosystem_ids:
                # Keep if any shared ID overlaps with selected
                shared = {str(sid) for sid in a.shared_ecosystem_ids}
                if shared & eco_id_strs:
                    filtered.append(a)
        rows = filtered

    # Post-filter by affected_party: check if the party name appears in the JSON list
    if _affected_party_filter:
        ap_lower = _affected_party_filter.lower()
        rows = [
            a for a in rows
            if a.affected_parties
            and isinstance(a.affected_parties, list)
            and any(ap_lower in str(p).lower() for p in a.affected_parties)
        ]

    if not rows:
        return {
            "success": True,
            "data": {
                "agreements": [],
                "count": 0,
                "message": "No agreements found matching the search criteria.",
            },
        }

    # Sort in Python for portable status-priority ordering
    rows_sorted = sorted(
        rows,
        key=lambda a: (_status_priority(a.status), -(a.created_date or date.min).toordinal()),
    )

    agreements = [
        {
            "agreement_id": a.agreement_id,
            "title": a.title,
            "type": a.type,
            "status": a.status,
            "domain": a.domain,
            "ecosystem_name": a.ecosystem.name if a.ecosystem else None,
            "ecosystem_id": str(a.ecosystem_id),
            "shared_ecosystem_ids": a.shared_ecosystem_ids,
            "created_date": str(a.created_date) if a.created_date else None,
        }
        for a in rows_sorted
    ]
    return {"success": True, "data": {"agreements": agreements, "count": len(agreements)}}


# ===================================================================
# TOOL 2: get_agreement
# ===================================================================

async def get_agreement(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Get full agreement by business-key agreement_id."""
    agreement_id = args.get("agreement_id", "")
    if not agreement_id:
        return {"success": False, "error": "agreement_id is required."}

    stmt = (
        select(Agreement)
        .options(selectinload(Agreement.ratification_records), selectinload(Agreement.ecosystem))
        .where(Agreement.agreement_id == agreement_id)
    )
    if ecosystem_ids:
        # Allow access if owned by or shared with any selected ecosystem
        eco_id_strs = [str(eid) for eid in ecosystem_ids]
        stmt = stmt.where(
            or_(
                Agreement.ecosystem_id.in_(ecosystem_ids),
                Agreement.shared_ecosystem_ids.isnot(None),
            )
        )
    result = await db.execute(stmt)
    agr = result.scalars().first()

    # Post-filter shared access
    if agr and ecosystem_ids:
        eco_id_strs_set = {str(eid) for eid in ecosystem_ids}
        if str(agr.ecosystem_id) not in eco_id_strs_set:
            shared = {str(sid) for sid in (agr.shared_ecosystem_ids or [])}
            if not (shared & eco_id_strs_set):
                agr = None

    if agr is None:
        return {"success": False, "error": f"Agreement '{agreement_id}' not found."}

    ratifications = [
        {
            "participant": r.participant,
            "role": r.role,
            "position": r.position,
            "date": str(r.date) if r.date else None,
        }
        for r in agr.ratification_records
    ]

    data = {
        "agreement_id": agr.agreement_id,
        "title": agr.title,
        "type": agr.type,
        "version": agr.version,
        "status": agr.status,
        "proposer": agr.proposer,
        "affected_parties": agr.affected_parties,
        "domain": agr.domain,
        "text": agr.text,
        "hierarchy_level": agr.hierarchy_level,
        "ecosystem_name": agr.ecosystem.name if agr.ecosystem else None,
        "ecosystem_id": str(agr.ecosystem_id),
        "shared_ecosystem_ids": agr.shared_ecosystem_ids,
        "review_date": str(agr.review_date) if agr.review_date else None,
        "sunset_date": str(agr.sunset_date) if agr.sunset_date else None,
        "ratification_date": str(agr.ratification_date) if agr.ratification_date else None,
        "created_date": str(agr.created_date) if agr.created_date else None,
        "ratification_records": ratifications,
    }
    return {"success": True, "data": data}


# ===================================================================
# TOOL 3: create_agreement_draft
# ===================================================================

async def create_agreement_draft(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Create a new agreement in draft status (an active member of the ecosystem, as REST POST /agreements)."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    required = ("title", "type", "domain", "text")
    for field in required:
        if not args.get(field):
            return {"success": False, "error": f"'{field}' is required."}

    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}
    author = await _caller_row(db, caller_user_id, eco_id)
    if not is_active_member_in(author, eco_id):
        return {"success": False, "error": MEMBER_REQUIRED}

    # The proposer text defaults to the caller; a named proposer must be an active member.
    proposer_text = str(args.get("proposer") or "").strip() or author.display_name
    if args.get("proposer") and await _resolve_member(db, proposer_text, ecosystem_ids) is None:
        return {
            "success": False,
            "error": f"Proposer '{proposer_text}' is not an active member.",
        }

    # Validate affected parties
    affected = args.get("affected_parties", [])
    if affected:
        for party in affected:
            member = await _resolve_member(db, party, ecosystem_ids)
            if member is None:
                return {
                    "success": False,
                    "error": f"Affected party '{party}' is not an active member.",
                }

    # Resolve parent_agreement_id (business key → UUID)
    parent_uuid = None
    parent_agreement_id_str = args.get("parent_agreement_id")
    if parent_agreement_id_str:
        parent_stmt = select(Agreement).where(Agreement.agreement_id == parent_agreement_id_str)
        if ecosystem_ids:
            parent_stmt = parent_stmt.where(Agreement.ecosystem_id.in_(ecosystem_ids))
        parent_result = await db.execute(parent_stmt)
        parent_agr = parent_result.scalars().first()
        if parent_agr is None:
            return {"success": False, "error": f"Parent agreement '{parent_agreement_id_str}' not found."}
        parent_uuid = parent_agr.id

    # Generate business key: AGR-{domain_prefix}-{year}-{seq}
    domain_prefix = args["domain"][:4].upper().replace(" ", "")
    year = _today().year
    last_result = await db.execute(
        select(Agreement.agreement_id)
        .where(Agreement.ecosystem_id == eco_id)
        .where(Agreement.agreement_id.like(f"AGR-{domain_prefix}-{year}-%"))
        .order_by(Agreement.agreement_id.desc())
        .limit(1)
    )
    last_id = last_result.scalar_one_or_none()
    next_num = (int(last_id.split("-")[-1]) + 1) if last_id else 1
    agreement_id = f"AGR-{domain_prefix}-{year}-{next_num:03d}"

    # Review date by type
    review_months = _REVIEW_MONTHS.get(args["type"], 12)
    review_date = _today() + timedelta(days=review_months * 30)

    # Parse optional sunset_date
    sunset_date = None
    if args.get("sunset_date"):
        try:
            sunset_date = date.fromisoformat(args["sunset_date"])
        except ValueError:
            return {"success": False, "error": f"Invalid sunset_date format: '{args['sunset_date']}'. Use YYYY-MM-DD."}

    agr = Agreement(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        agreement_id=agreement_id,
        type=args["type"],
        title=args["title"],
        version="0.1",
        status="draft",
        proposer=proposer_text,
        affected_parties=affected if affected else None,
        domain=args["domain"],
        text=args.get("text"),
        hierarchy_level=args.get("hierarchy_level", "domain"),
        review_date=review_date,
        sunset_date=sunset_date,
        parent_agreement_id=parent_uuid,
        shared_ecosystem_ids=args.get("shared_ecosystem_ids"),
        created_date=_today(),
    )
    db.add(agr)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(agr.id),
            "agreement_id": agreement_id,
            "status": "draft",
            "version": "0.1",
            "review_date": str(review_date),
            "sunset_date": str(sunset_date) if sunset_date else None,
            "message": f"Agreement draft '{agreement_id}' created.",
        },
    }


# ===================================================================
# TOOL 4: update_agreement_status
# ===================================================================

async def update_agreement_status(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Conduct an agreement ceremony through the REST/MCP engine (api/agreements.transition_agreement).

    Same rules as REST POST /agreements/:id/status: ceremony steward, lifecycle
    table, documented evidence, declared gate; then the automatic cascade. A
    status change never bumps the version (consent is bound to it).
    """
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    agreement_id = args.get("agreement_id", "")
    new_status = str(args.get("new_status") or "").strip().lower()
    if not agreement_id or not new_status:
        return {"success": False, "error": "agreement_id and new_status are required."}

    stmt = select(Agreement).where(Agreement.agreement_id == agreement_id)
    if ecosystem_ids:
        stmt = stmt.where(Agreement.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(stmt)
    agr = result.scalars().first()
    if agr is None:
        return {"success": False, "error": f"Agreement '{agreement_id}' not found."}

    conductor = await _caller_row(db, caller_user_id, agr.ecosystem_id)
    current = agr.status
    try:
        outcome = await conduct_agreement_transition(
            db, agr, to=new_status, caller=conductor, evidence=args.get("evidence"),
        )
    except TransitionRefused as refusal:
        return {"success": False, "error": _refusal_text(refusal)}
    await db.flush()

    return {
        "success": True,
        "data": {
            "agreement_id": agreement_id,
            "previous_status": current,
            "new_status": outcome.status,
            "version": agr.version,
            "auto_transitions": outcome.auto_transitions,
            "decision_record_id": outcome.decision_record_id,
        },
    }


# ===================================================================
# TOOL 5: check_authority
# ===================================================================

async def check_authority(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Check if a member has authority for an action in a domain.

    Since explicit role-assignment models are not in the DB schema,
    we check if the member is the current_steward of the domain.
    """
    member_name = args.get("member", "")
    domain_name = args.get("domain", "")
    action = args.get("action", "")

    if not member_name or not domain_name:
        return {"success": False, "error": "member and domain are required."}

    member = await _resolve_member(db, member_name, ecosystem_ids)
    if member is None:
        return {
            "success": True,
            "data": {
                "authorized": False,
                "reason": f"Member '{member_name}' not found or not active.",
                "role_source": None,
                "domain_contract": None,
            },
        }

    # Find domain
    domain_stmt = select(Domain).where(
        func.lower(Domain.domain_id) == domain_name.lower()
    )
    if ecosystem_ids:
        domain_stmt = domain_stmt.where(Domain.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(domain_stmt)
    domain = result.scalars().first()
    if domain is None:
        # Try partial match
        domain_stmt2 = select(Domain).where(Domain.domain_id.ilike(f"%{domain_name}%"))
        if ecosystem_ids:
            domain_stmt2 = domain_stmt2.where(Domain.ecosystem_id.in_(ecosystem_ids))
        result = await db.execute(domain_stmt2)
        domain = result.scalars().first()

    if domain is None:
        return {
            "success": True,
            "data": {
                "authorized": False,
                "reason": f"Domain '{domain_name}' not found.",
                "role_source": None,
                "domain_contract": None,
            },
        }

    # Check stewardship
    is_steward = (
        domain.steward_id == member.id
        or (domain.current_steward and domain.current_steward.lower() == member.display_name.lower())
    )

    if is_steward:
        return {
            "success": True,
            "data": {
                "authorized": True,
                "reason": f"{member.display_name} is the domain steward.",
                "role_source": "domain_steward",
                "domain_contract": domain.domain_id,
            },
        }

    return {
        "success": True,
        "data": {
            "authorized": False,
            "reason": (
                f"Member '{member.display_name}' has no stewardship role "
                f"in domain '{domain.domain_id}'. Action '{action}' not authorized."
            ),
            "role_source": None,
            "domain_contract": domain.domain_id,
        },
    }


# ===================================================================
# TOOL 6: get_member_roles
# ===================================================================

async def get_member_roles(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Get all active role assignments for a member.

    Derives roles from domain stewardship assignments.
    """
    member_name = args.get("member", "")
    if not member_name:
        return {"success": False, "error": "member is required."}

    member = await _resolve_member(db, member_name, ecosystem_ids)
    if member is None:
        return {"success": False, "error": f"Member '{member_name}' not found or not active."}

    # Find all domains where this member is steward
    domain_stmt = select(Domain).where(
        or_(
            Domain.steward_id == member.id,
            func.lower(Domain.current_steward) == member.display_name.lower(),
        )
    )
    if ecosystem_ids:
        domain_stmt = domain_stmt.where(Domain.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(domain_stmt)
    domains = result.scalars().all()

    roles = [
        {
            "role_name": "domain_steward",
            "domain": d.domain_id,
            "scope": d.purpose or "Full domain stewardship",
            "assigned_date": str(d.created_at.date()) if d.created_at else None,
            "review_date": None,
        }
        for d in domains
    ]

    # Add member profile as a role
    if member.profile:
        roles.append({
            "role_name": member.profile,
            "domain": "ecosystem-wide",
            "scope": f"Member profile: {member.profile}",
            "assigned_date": str(member.created_at.date()) if member.created_at else None,
            "review_date": None,
        })

    return {
        "success": True,
        "data": {
            "member": member.display_name,
            "member_id": member.member_id,
            "roles": roles,
        },
    }


# ===================================================================
# TOOL 7: create_proposal
# ===================================================================

async def create_proposal(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Create a draft ACT proposal authored by the calling member."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    required = ("title", "type", "proposed_change", "rationale")
    for field in required:
        if not args.get(field):
            return {"success": False, "error": f"'{field}' is required."}

    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}

    # The caller is the author (manage rule); `proposer` is display text that
    # may name someone else and defaults to the caller's name.
    author = await _caller_row(db, caller_user_id, eco_id)
    if author is None:
        return {"success": False, "error": "Only a member of this ecosystem can create a proposal here."}
    proposer_text = str(args.get("proposer") or "").strip() or author.display_name

    # Generate proposal ID using MAX approach
    year = _today().year
    last_result = await db.execute(
        select(Proposal.proposal_id)
        .where(Proposal.ecosystem_id == eco_id)
        .where(Proposal.proposal_id.like(f"PROP-{year}-%"))
        .order_by(Proposal.proposal_id.desc())
        .limit(1)
    )
    last_id = last_result.scalar_one_or_none()
    next_num = (int(last_id.split("-")[-1]) + 1) if last_id else 1
    proposal_id = f"PROP-{year}-{next_num:03d}"

    # Auto-set consent mode
    scope = args.get("scope", "").lower()
    decision_type_val = args.get("decision_type", "").lower()
    if "osc" in scope or "uaf" in scope or "osc" in decision_type_val or "uaf" in decision_type_val:
        consent_mode = "consensus"
    else:
        consent_mode = "consent"

    # Parse optional deadlines
    advice_deadline = None
    if args.get("advice_deadline"):
        try:
            advice_deadline = date.fromisoformat(args["advice_deadline"])
        except ValueError:
            return {"success": False, "error": f"Invalid advice_deadline format: '{args['advice_deadline']}'. Use YYYY-MM-DD."}

    consent_deadline = None
    if args.get("consent_deadline"):
        try:
            consent_deadline = date.fromisoformat(args["consent_deadline"])
        except ValueError:
            return {"success": False, "error": f"Invalid consent_deadline format: '{args['consent_deadline']}'. Use YYYY-MM-DD."}

    prop = Proposal(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        proposal_id=proposal_id,
        type=args["type"],
        decision_type=consent_mode,
        title=args["title"],
        version="1.0",
        status="draft",
        proposer=proposer_text,
        proposer_member_id=author.id,
        co_sponsors=args.get("co_sponsors"),
        affected_domain=args.get("affected_domain"),
        impacted_parties=args.get("impacted_parties"),
        urgency=args.get("urgency"),
        proposed_change=args.get("proposed_change"),
        rationale=args.get("rationale"),
        advice_deadline=advice_deadline,
        consent_deadline=consent_deadline,
        created_date=_today(),
    )
    db.add(prop)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(prop.id),
            "proposal_id": proposal_id,
            "consent_mode": consent_mode,
            "status": "draft",
            "proposer": proposer_text,
            "message": f"Proposal '{proposal_id}' created as a draft. Open it for advice when ready.",
        },
    }


# ===================================================================
# TOOL 8: record_advice
# ===================================================================

async def record_advice(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Record the calling member's advice on a proposal (never on their own)."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    proposal_id = args.get("proposal_id", "")
    advice_text = str(args.get("advice_text") or "").strip()

    if not proposal_id:
        return {"success": False, "error": "proposal_id is required."}
    if not advice_text:
        # A blank entry would still count toward the advice gate.
        return {"success": False, "error": "Advice text is required."}

    prop = await _find_proposal(db, proposal_id, ecosystem_ids)
    if prop is None:
        return {"success": False, "error": f"Proposal '{proposal_id}' not found."}

    if prop.status != "advice":
        return {
            "success": False,
            "error": f"Proposal is in '{prop.status}' phase, not 'advice'.",
        }

    # The advisor is the caller: their row in the proposal's ecosystem, else
    # (shared-ecosystem advice, as in REST) their row in a scoped ecosystem.
    advisor_member = await _caller_row(db, caller_user_id, prop.ecosystem_id)
    if is_proposal_author(advisor_member, prop):
        return {"success": False, "error": SELF_ADVICE_DENIED}
    if advisor_member is None:
        fallback = select(Member).where(Member.user_id == caller_user_id, Member.current_status == "active")
        if ecosystem_ids:
            fallback = fallback.where(Member.ecosystem_id.in_(ecosystem_ids))
        advisor_member = (await db.execute(fallback.order_by(Member.created_at, Member.id))).scalars().first()
    if advisor_member is None:
        return {"success": False, "error": "Only a member can give advice on this proposal."}

    # Latest advice round (the unit the advice gate counts), or open the first.
    advice_log = (await db.execute(
        select(AdviceLog)
        .where(AdviceLog.proposal_id == prop.id)
        .order_by(AdviceLog.created_at.desc())
        .limit(1)
    )).scalars().first()
    if advice_log is None:
        advice_log = AdviceLog(
            id=uuid.uuid4(),
            proposal_id=prop.id,
            advice_window_start=_today(),
        )
        db.add(advice_log)
        await db.flush()

    entry = AdviceEntry(
        id=uuid.uuid4(),
        advice_log_id=advice_log.id,
        advisor=advisor_member.display_name,
        role=advisor_member.profile,
        date=_today(),
        advice_text=advice_text,
        integration_status="pending",
    )
    db.add(entry)
    await db.flush()
    outcome = await transition_proposal(db, prop, caller=advisor_member)

    return {
        "success": True,
        "data": {
            "proposal_id": prop.proposal_id,
            "advisor": advisor_member.display_name,
            "recorded_date": str(_today()),
            "status": outcome.status,
            "auto_transitions": outcome.auto_transitions,
            "message": "Advice recorded successfully.",
        },
    }


# ===================================================================
# TOOL 9: record_consent_position
# ===================================================================

async def record_consent_position(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Record the signed-in member's consent position; the consent gate then advances as in REST."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    proposal_id = args.get("proposal_id", "")
    raw_position = str(args.get("position") or "")
    position = consent_position(raw_position)  # "objection" -> "object", the value the gate blocks on
    reason = args.get("reason")
    consent_round = args.get("round", 1)

    if not proposal_id or not position:
        return {
            "success": False,
            "error": "proposal_id and position are required.",
        }

    if position not in {"consent", "stand_aside", "object"}:
        return {
            "success": False,
            "error": f"Invalid position '{raw_position}'. Must be one of: consent, stand_aside, objection.",
        }

    prop = await _find_proposal(db, proposal_id, ecosystem_ids)
    if prop is None:
        return {"success": False, "error": f"Proposal '{proposal_id}' not found."}

    if prop.status != "consent":
        return {
            "success": False,
            "error": f"Proposal is in '{prop.status}' phase, not 'consent'.",
        }

    # The participant is always the caller; any name argument is ignored.
    participant = await _caller_row(db, caller_user_id, prop.ecosystem_id)
    if not can_participate(participant, prop):
        return {"success": False, "error": "Only a member of this proposal's ecosystem can record a consent position."}

    consent_mode = prop.decision_type or "consent"

    # Reject stand_aside in consensus mode
    if position == "stand_aside" and consent_mode == "consensus":
        return {
            "success": False,
            "error": "Stand-aside is not permitted in consensus mode. All participants must consent or object.",
        }

    # Require reason for stand_aside and objection
    if position in ("stand_aside", "object") and not reason:
        return {
            "success": False,
            "error": f"A reason is required for '{raw_position.strip().lower()}'.",
        }

    # The latest consent record is the one the gate counts.
    consent_rec = (await db.execute(
        select(ConsentRecord)
        .options(selectinload(ConsentRecord.participants))
        .where(ConsentRecord.proposal_id == prop.id)
        .order_by(ConsentRecord.created_at.desc())
        .limit(1)
    )).scalars().first()
    if consent_rec is None:
        consent_rec = ConsentRecord(
            id=uuid.uuid4(),
            proposal_id=prop.id,
            consent_mode=consent_mode,
            date=_today(),
        )
        db.add(consent_rec)
        await db.flush()
        prior_positions = []
    else:
        prior_positions = consent_rec.participants

    name = participant.display_name
    if any(p.name.lower() == name.lower() and p.round == consent_round for p in prior_positions):
        return {
            "success": False,
            "error": f"'{name}' has already recorded a position in round {consent_round}.",
        }

    db.add(ConsentParticipant(
        id=uuid.uuid4(),
        consent_record_id=consent_rec.id,
        name=name,
        position=position,
        reason=reason,
        round=consent_round,
    ))
    await db.flush()
    outcome = await transition_proposal(db, prop, caller=participant)

    return {
        "success": True,
        "data": {
            "proposal_id": prop.proposal_id,
            "participant": name,
            "position": position,
            "round": consent_round,
            "status": outcome.status,
            "auto_transitions": outcome.auto_transitions,
            "gates": outcome.gates,
            "message": f"Position '{position}' recorded for '{name}'.",
        },
    }


# ===================================================================
# TOOL 10: check_quorum
# ===================================================================

async def check_quorum(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Check if quorum is met for a proposal's consent round."""
    proposal_id = args.get("proposal_id", "")
    if not proposal_id:
        return {"success": False, "error": "proposal_id is required."}

    prop_stmt = (
        select(Proposal)
        .options(selectinload(Proposal.consent_records).selectinload(ConsentRecord.participants))
        .where(Proposal.proposal_id == proposal_id)
    )
    if ecosystem_ids:
        prop_stmt = prop_stmt.where(Proposal.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(prop_stmt)
    prop = result.scalars().first()
    if prop is None:
        return {"success": False, "error": f"Proposal '{proposal_id}' not found."}

    consent_mode = prop.decision_type or "consent"
    is_emergency = (prop.urgency or "").lower() == "critical"

    # Count total deciding body = active members in ecosystem
    member_count_stmt = select(func.count()).select_from(Member).where(
        Member.current_status == "active",
    )
    if ecosystem_ids:
        member_count_stmt = member_count_stmt.where(Member.ecosystem_id.in_(ecosystem_ids))
    else:
        member_count_stmt = member_count_stmt.where(Member.ecosystem_id == prop.ecosystem_id)
    eco_result = await db.execute(member_count_stmt)
    total_deciding_body = eco_result.scalar() or 0

    # Count present (participants who recorded a position)
    present_count = 0
    if prop.consent_records:
        # Count distinct participants in latest round
        participants = prop.consent_records[0].participants
        present_names = {p.name.lower() for p in participants}
        present_count = len(present_names)

    # Calculate threshold
    if is_emergency:
        required_fraction = 0.5
    elif consent_mode == "consensus":
        required_fraction = 1.0
    else:
        required_fraction = 2 / 3

    required_count = math.ceil(total_deciding_body * required_fraction)

    quorum_met = present_count >= required_count

    return {
        "success": True,
        "data": {
            "quorum_met": quorum_met,
            "required_threshold": required_fraction,
            "present_count": present_count,
            "required_count": required_count,
            "total_deciding_body": total_deciding_body,
            "consent_mode": consent_mode,
        },
    }


# ===================================================================
# TOOL 11: create_decision_record
# ===================================================================

async def create_decision_record(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Record a decision outside the ACT engine (an ecosystem steward), recorded by the caller."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    holding = args.get("holding", "")
    rationale = args.get("rationale", "")
    if not holding:
        return {"success": False, "error": "'holding' is required."}
    if not rationale:
        return {"success": False, "error": "'rationale' is required."}

    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}
    recorder = await _caller_row(db, caller_user_id, eco_id)
    if not can_record_decision(recorder, eco_id):
        return {"success": False, "error": DECISION_DENIED}

    # Generate record ID using MAX approach
    year = _today().year
    last_result = await db.execute(
        select(DecisionRecord.record_id)
        .where(DecisionRecord.ecosystem_id == eco_id)
        .where(DecisionRecord.record_id.like(f"DR-{year}-%"))
        .order_by(DecisionRecord.record_id.desc())
        .limit(1)
    )
    last_id = last_result.scalar_one_or_none()
    next_num = (int(last_id.split("-")[-1]) + 1) if last_id else 1
    record_id = f"DR-{year}-{next_num:04d}"

    dr = DecisionRecord(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        record_id=record_id,
        date=_today(),
        holding=holding,
        ratio_decidendi=rationale,
        obiter_dicta=args.get("obiter_dicta"),
        deliberation_summary=args.get("deliberation_summary"),
        source_skill=args.get("source_skill"),
        source_layer=args.get("source_layer"),
        artifact_type=args.get("artifact_type"),
        artifact_reference=args.get("artifact_reference"),
        domain=args.get("domain"),
        precedent_level=args.get("precedent_level", "domain"),
        status="active",
        recorder=recorder.display_name,
        recorder_role=args.get("recorder_role") or recorder.role,
    )
    db.add(dr)
    await db.flush()

    # Store semantic tags if provided
    tags = args.get("tags", [])
    if tags:
        st = DecisionSemanticTag(
            id=uuid.uuid4(),
            decision_record_id=dr.id,
            topic=tags,
            ecosystem_scope=args.get("domain"),
        )
        db.add(st)
        await db.flush()

    # Store participants if provided
    participants = args.get("participants", [])
    for p in participants:
        member_name = p.get("member_name", "")
        position = p.get("position", "")
        if member_name:
            dp = DecisionParticipant(
                id=uuid.uuid4(),
                decision_record_id=dr.id,
                name=member_name,
                position=position,
            )
            db.add(dp)

    # Store dissents if provided
    dissents = args.get("dissents", [])
    for d in dissents:
        member_name = d.get("member_name", "")
        dissent_rationale = d.get("rationale", "")
        if member_name:
            ddr = DecisionDissentRecord(
                id=uuid.uuid4(),
                decision_record_id=dr.id,
                objector=member_name,
                objection=dissent_rationale,
            )
            db.add(ddr)

    if participants or dissents:
        await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(dr.id),
            "record_id": record_id,
            "source_skill": args.get("source_skill"),
            "source_layer": args.get("source_layer"),
            "tags": tags,
            "participants_recorded": len(participants),
            "dissents_recorded": len(dissents),
            "message": f"Decision record '{record_id}' created.",
        },
    }


# ===================================================================
# TOOL 12: search_precedents
# ===================================================================

async def search_precedents(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Search decision records by skill, domain, tags, text."""
    stmt = select(DecisionRecord).options(
        selectinload(DecisionRecord.semantic_tags)
    )

    if ecosystem_ids:
        stmt = stmt.where(DecisionRecord.ecosystem_id.in_(ecosystem_ids))

    if args.get("skill"):
        stmt = stmt.where(DecisionRecord.source_skill == args["skill"])
    if args.get("domain"):
        stmt = stmt.where(DecisionRecord.domain.ilike(f"%{args['domain']}%"))
    if args.get("text"):
        text_pattern = f"%{args['text']}%"
        stmt = stmt.where(
            or_(
                DecisionRecord.holding.ilike(text_pattern),
                DecisionRecord.ratio_decidendi.ilike(text_pattern),
            )
        )

    limit = args.get("limit", 10)
    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    records = result.scalars().all()

    # If tag filter requested, filter in Python (JSON column)
    search_tags = args.get("tags", [])
    if search_tags:
        filtered = []
        for r in records:
            tag_match_count = 0
            for st in r.semantic_tags:
                topics = st.topic or []
                for t in search_tags:
                    if t in topics:
                        tag_match_count += 1
            if tag_match_count > 0:
                filtered.append((tag_match_count, r))
        # Sort by tag match count desc, then recency
        filtered.sort(key=lambda x: (-x[0], -(x[1].date or date.min).toordinal()))
        records = [r for _, r in filtered]

    data = [
        {
            "record_id": r.record_id,
            "date": str(r.date) if r.date else None,
            "holding": r.holding,
            "domain": r.domain,
            "source_skill": r.source_skill,
            "source_layer": r.source_layer,
            "precedent_level": r.precedent_level,
            "tags": [t.topic for t in r.semantic_tags] if r.semantic_tags else [],
        }
        for r in records
    ]

    return {"success": True, "data": {"records": data, "count": len(data)}}


# ===================================================================
# TOOL 13: get_domain
# ===================================================================

async def get_domain(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Get full domain contract with all S3 elements."""
    domain_id = args.get("domain_id", "")
    if not domain_id:
        return {"success": False, "error": "domain_id is required."}

    stmt = (
        select(Domain)
        .options(selectinload(Domain.domain_elements))
        .where(Domain.domain_id == domain_id)
    )
    if ecosystem_ids:
        stmt = stmt.where(Domain.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(stmt)
    domain = result.scalars().first()

    if domain is None:
        # Try partial match
        stmt2 = (
            select(Domain)
            .options(selectinload(Domain.domain_elements))
            .where(Domain.domain_id.ilike(f"%{domain_id}%"))
        )
        if ecosystem_ids:
            stmt2 = stmt2.where(Domain.ecosystem_id.in_(ecosystem_ids))
        result2 = await db.execute(stmt2)
        domain = result2.scalars().first()

    if domain is None:
        return {"success": False, "error": f"Domain '{domain_id}' not found."}

    elements_list = [
        {"element_name": e.element_name, "element_value": e.element_value}
        for e in domain.domain_elements
    ]

    data = {
        "domain_id": domain.domain_id,
        "version": domain.version,
        "status": domain.status,
        "purpose": domain.purpose,
        "current_steward": domain.current_steward,
        "elements": domain.elements,
        "domain_elements": elements_list,
        "metric_definitions": domain.metric_definitions,
    }
    return {"success": True, "data": data}


# ===================================================================
# TOOL 14: get_active_members
# ===================================================================

async def get_active_members(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Get active members, optionally filtered by profile."""
    stmt = select(Member).where(Member.current_status == "active")

    if ecosystem_ids:
        stmt = stmt.where(Member.ecosystem_id.in_(ecosystem_ids))

    if args.get("profile"):
        stmt = stmt.where(Member.profile == args["profile"])

    result = await db.execute(stmt)
    members = result.scalars().all()

    data = [
        {
            "member_id": m.member_id,
            "display_name": m.display_name,
            "profile": m.profile,
            "status": m.current_status,
        }
        for m in members
    ]

    return {
        "success": True,
        "data": {
            "members": data,
            "count": len(data),
        },
    }


# ===================================================================
# TOOL 15: create_conflict_case
# ===================================================================

async def create_conflict_case(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Report a new conflict or harm requiring governance process; the caller is the reporter."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    title = args.get("title", "")
    description = args.get("description", "")
    if not title:
        return {"success": False, "error": "'title' is required."}
    if not description:
        return {"success": False, "error": "'description' is required."}

    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}
    reporter = await _caller_row(db, caller_user_id, eco_id)
    if not is_active_member_in(reporter, eco_id):
        return {"success": False, "error": MEMBER_REQUIRED}

    # Resolve facilitator_id (UUID string to member.id)
    facilitator_uuid = None
    facilitator_id_str = args.get("facilitator_id")
    if facilitator_id_str:
        try:
            facilitator_uuid_val = uuid.UUID(facilitator_id_str)
            facilitator_uuid = facilitator_uuid_val
        except ValueError:
            return {"success": False, "error": f"Invalid facilitator_id UUID: '{facilitator_id_str}'."}

    case = ConflictCase(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        case_id=f"CONF-{uuid.uuid4().hex[:8].upper()}",
        title=title,
        description=description,
        severity=args.get("severity", "medium"),
        scope=args.get("scope", "interpersonal"),
        urgency=args.get("urgency", "normal"),
        safety_flag=args.get("safety_flag", False),
        parties=args.get("parties"),
        reporter_id=reporter.id,
        facilitator_id=facilitator_uuid,
        domain=args.get("domain"),
        triage_notes=args.get("triage_notes"),
        status="reported",
    )
    db.add(case)
    await db.flush()
    return {"success": True, "data": {"id": str(case.id), "case_id": case.case_id, "message": f"Conflict case {case.case_id} created."}}


# ===================================================================
# TOOL 16: triage_conflict
# ===================================================================

async def triage_conflict(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Assess and route a conflict to a resolution tier (an active member there, as REST PUT /conflicts)."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    case_id = args.get("case_id", "")
    if not case_id:
        return {"success": False, "error": "case_id is required."}
    case_stmt = select(ConflictCase).where(ConflictCase.case_id == case_id)
    if ecosystem_ids:
        case_stmt = case_stmt.where(ConflictCase.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(case_stmt)
    case = result.scalar_one_or_none()
    if not case:
        return {"success": False, "error": f"Conflict case '{case_id}' not found."}
    if not is_active_member_in(await _caller_row(db, caller_user_id, case.ecosystem_id), case.ecosystem_id):
        return {"success": False, "error": MEMBER_REQUIRED}
    case.tier = args.get("tier", 1)
    case.severity = args.get("severity", case.severity)
    case.scope = args.get("scope", case.scope)
    case.root_cause_category = args.get("root_cause_category")
    case.triage_notes = args.get("triage_notes")
    case.status = "triaged"
    await db.flush()
    tier_names = {1: "NVC Dialogue", 2: "Coaching Intervention", 3: "Harm Circle", 4: "Community Impact Assessment"}
    return {"success": True, "data": {"case_id": case.case_id, "tier": case.tier, "tier_name": tier_names.get(case.tier, "Unknown"), "message": f"Triaged to Tier {case.tier}: {tier_names.get(case.tier, 'Unknown')}."}}


# ===================================================================
# TOOL 17: get_emergency_state
# ===================================================================

async def get_emergency_state(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Check the current circuit breaker state."""
    eco_id = await _get_first_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}
    result = await db.execute(
        select(EmergencyState)
        .where(EmergencyState.ecosystem_id == eco_id)
        .order_by(EmergencyState.created_at.desc())
        .limit(1)
    )
    state = result.scalar_one_or_none()
    if not state or state.state == "closed":
        return {"success": True, "data": {"state": "closed", "message": "Circuit breaker is CLOSED (normal operations)."}}
    return {"success": True, "data": {
        "state": state.state,
        "declared_at": str(state.declared_at) if state.declared_at else None,
        "auto_revert_at": str(state.auto_revert_at) if state.auto_revert_at else None,
        "message": f"Circuit breaker is {state.state.upper()}.",
    }}


# ===================================================================
# TOOL 18: declare_emergency
# ===================================================================

async def declare_emergency(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Declare an emergency and open the circuit breaker; the declarer is the caller (policy.can_declare_emergency)."""
    # Local import to avoid module-level circular dep with the API layer.
    from neos_agent.api.emergency import ACTIVE_STATES

    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}
    declarer = await _caller_row(db, caller_user_id, eco_id)
    if not can_declare_emergency(declarer, eco_id):
        return {"success": False, "error": MEMBER_REQUIRED}
    result = await db.execute(
        select(EmergencyState).where(
            EmergencyState.ecosystem_id == eco_id,
            EmergencyState.state.in_(ACTIVE_STATES),
        ).limit(1)
    )
    if result.scalar_one_or_none():
        return {"success": False, "error": "An emergency is already active."}
    now = datetime.now(timezone.utc)
    declared_by = declarer.display_name
    state = EmergencyState(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        state="open",
        declared_at=now,
        declared_by=declared_by,
        criteria_met=args.get("criteria_met"),
        auto_revert_at=now + timedelta(days=30),
        notes=args.get("notes"),
        pre_authorized_roles=[],
        actions_log=[
            {
                "action": "declared",
                "actor": declared_by,
                "at": now.isoformat(),
                "auto_revert_at": (now + timedelta(days=30)).isoformat(),
            }
        ],
    )
    db.add(state)
    await db.flush()
    return {"success": True, "data": {"id": str(state.id), "state": "open", "auto_revert_at": str(state.auto_revert_at), "message": "EMERGENCY DECLARED — Circuit breaker OPEN."}}


# ===================================================================
# TOOL 19: create_exit_record
# ===================================================================

async def create_exit_record(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Start the signed-in member's own voluntary exit process."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    departure_notice = args.get("departure_notice", "")
    if not departure_notice:
        return {"success": False, "error": "'departure_notice' is required."}
    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    member = await _caller_row(db, caller_user_id, eco_id)
    if not is_active_member_in(member, eco_id):
        return {"success": False, "error": MEMBER_REQUIRED}
    named = str(args.get("member_name") or "").strip().lower()
    if named and named not in {member.display_name.lower(), (member.member_id or "").lower()}:
        return {"success": False, "error": EXIT_SELF_ONLY}
    exit_type = args.get("exit_type", "standard")
    days = 30 if exit_type == "standard" else 7

    # Resolve coordinator if provided
    coordinator_uuid = None
    coordinator_name = args.get("coordinator")
    if coordinator_name:
        coordinator_member = await _resolve_member(db, coordinator_name, ecosystem_ids)
        if coordinator_member is None:
            return {"success": False, "error": f"Coordinator '{coordinator_name}' is not an active member."}
        coordinator_uuid = coordinator_member.id

    # Normalize commitment_inventory to a JSON-serializable value
    commitment_inventory = args.get("commitment_inventory")

    record = ExitRecord(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        member_id=member.id,
        exit_type=exit_type,
        status="declared",
        declared_date=_today(),
        target_completion_date=_today() + timedelta(days=days),
        data_export_requested=args.get("data_export", False),
        departure_notice=departure_notice,
        commitment_inventory=commitment_inventory if isinstance(commitment_inventory, (dict, list)) else ({"description": commitment_inventory} if commitment_inventory else None),
        coordinator_id=coordinator_uuid,
    )
    db.add(record)
    await db.flush()
    return {"success": True, "data": {"id": str(record.id), "member": member.display_name, "exit_type": exit_type, "target_date": str(record.target_completion_date), "message": f"Exit process started for {member.display_name} ({exit_type}, {days}-day timeline)."}}


# ===================================================================
# TOOL 20: create_domain_draft
# ===================================================================

async def create_domain_draft(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Create a new domain contract in draft status (ecosystem stewards, mod+, only)."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    domain_id = args.get("domain_id", "")
    purpose = args.get("purpose", "")
    if not domain_id or not purpose:
        return {"success": False, "error": "'domain_id' and 'purpose' are required."}

    # Validate elements if provided: must contain at minimum drivers and deliverables
    elements = args.get("elements")
    if elements is not None:
        if not isinstance(elements, dict):
            return {"success": False, "error": "'elements' must be an object with at least 'drivers' and 'deliverables' keys."}
        if "drivers" not in elements:
            return {"success": False, "error": "'elements.drivers' is required (list of strings motivating work in this domain)."}
        if "deliverables" not in elements:
            return {"success": False, "error": "'elements.deliverables' is required (list of concrete outputs)."}

    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}

    # Same rule as REST POST /domains: the caller's own row must be mod+ here.
    creator = await _caller_row(db, caller_user_id, eco_id)
    if not is_steward_in(creator, eco_id):
        return {"success": False, "error": DOMAIN_CREATE_DENIED}

    # Check for duplicates
    existing = await db.execute(
        select(Domain).where(
            Domain.domain_id == domain_id,
            Domain.ecosystem_id == eco_id,
        )
    )
    if existing.scalars().first():
        return {"success": False, "error": f"Domain '{domain_id}' already exists."}

    # Resolve steward if provided
    steward_id = None
    steward_name = args.get("steward")
    if steward_name:
        steward = await _resolve_member(db, steward_name, ecosystem_ids)
        if steward is None:
            return {"success": False, "error": f"Steward '{steward_name}' is not an active member."}
        steward_id = steward.id
        steward_name = steward.display_name

    # Resolve parent domain if provided
    parent_uuid = None
    parent_domain_id = args.get("parent_domain_id")
    if parent_domain_id:
        parent_stmt = select(Domain).where(Domain.domain_id == parent_domain_id)
        if ecosystem_ids:
            parent_stmt = parent_stmt.where(Domain.ecosystem_id.in_(ecosystem_ids))
        parent_result = await db.execute(parent_stmt)
        parent = parent_result.scalars().first()
        if parent is None:
            return {"success": False, "error": f"Parent domain '{parent_domain_id}' not found."}
        parent_uuid = parent.id

    domain = Domain(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        domain_id=domain_id,
        version="0.1",
        status="draft",
        name=str(args.get("name") or "").strip() or None,
        purpose=purpose,
        current_steward=steward_name,
        steward_id=steward_id,
        parent_domain_id=parent_uuid,
        created_by=creator.display_name,
        metric_definitions=args.get("metric_definitions"),
        elements=args.get("elements"),
    )
    db.add(domain)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(domain.id),
            "domain_id": domain_id,
            "status": "draft",
            "version": "0.1",
            "steward": steward_name,
            "message": f"Domain draft '{domain_id}' created.",
        },
    }


# ===================================================================
# TOOL 21: create_ecosystem
# ===================================================================

async def create_ecosystem(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Create a new ecosystem founded by the caller (as REST POST /ecosystems: founding member + core domain)."""
    founder = await db.get(User, caller_user_id) if caller_user_id is not None else None
    if founder is None:
        return {"success": False, "error": CALLER_REQUIRED}
    name = args.get("name", "")
    if not name:
        return {"success": False, "error": "'name' is required."}

    # Check for duplicates
    existing = await db.execute(
        select(Ecosystem).where(func.lower(Ecosystem.name) == name.lower())
    )
    if existing.scalars().first():
        return {"success": False, "error": f"Ecosystem '{name}' already exists."}

    eco = Ecosystem(
        id=uuid.uuid4(),
        name=name,
        description=args.get("description"),
        status="active",
        location=args.get("location"),
        website=args.get("website"),
        founded_date=_today(),
        tags=args.get("tags"),
        contact_email=args.get("contact_email"),
        governance_summary=args.get("governance_summary"),
        visibility=args.get("visibility", "public"),
    )
    db.add(eco)
    await db.flush()

    # Mirrors api/ecosystems.create_ecosystem until one shared founding helper exists.
    founding_member = Member(
        ecosystem_id=eco.id,
        user_id=founder.id,
        member_id=f"did-{founder.did[-12:]}" if founder.did else f"usr-{str(founder.id)[:12]}",
        display_name=founder.display_name,
        current_status="active",
        profile="co_creator",
    )
    db.add(founding_member)
    await db.flush()
    core_domain = Domain(
        id=uuid.uuid4(),
        ecosystem_id=eco.id,
        domain_id=f"DOM-{uuid.uuid4().hex[:8].upper()}",
        version="1.0",
        status="active",
        purpose=f"Core governance domain for {eco.name}",
        current_steward=founding_member.display_name,
        steward_id=founding_member.id,
        created_by=founding_member.display_name,
    )
    core_domain.version_fingerprint = generate_fingerprint(
        core_domain.domain_id, core_domain.purpose or "", core_domain.version, core_domain.status
    )
    db.add(core_domain)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(eco.id),
            "name": name,
            "status": "active",
            "message": f"Ecosystem '{name}' created.",
        },
    }


# ===================================================================
# TOOL 22: create_safeguard_audit
# ===================================================================

async def create_safeguard_audit(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Create a governance health audit draft (Layer VII safeguard), recorded by the caller."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    findings = args.get("findings", "")
    if not findings:
        return {"success": False, "error": "'findings' is required."}

    eco_id = await _scoped_ecosystem_id(db, ecosystem_ids)
    if eco_id is None:
        return {"success": False, "error": "No ecosystem configured."}
    requester = await _caller_row(db, caller_user_id, eco_id)
    if not is_active_member_in(requester, eco_id):
        return {"success": False, "error": MEMBER_REQUIRED}
    auditor = requester.display_name

    # Generate audit ID using MAX approach
    year = _today().year
    last_result = await db.execute(
        select(GovernanceHealthAudit.audit_id)
        .where(GovernanceHealthAudit.ecosystem_id == eco_id)
        .where(GovernanceHealthAudit.audit_id.like(f"GHA-{year}-%"))
        .order_by(GovernanceHealthAudit.audit_id.desc())
        .limit(1)
    )
    last_id = last_result.scalar_one_or_none()
    next_num = (int(last_id.split("-")[-1]) + 1) if last_id else 1
    audit_id = f"GHA-{year}-{next_num:03d}"

    # Parse optional date fields
    audit_period_start = None
    if args.get("audit_period_start"):
        try:
            audit_period_start = date.fromisoformat(args["audit_period_start"])
        except ValueError:
            return {"success": False, "error": f"Invalid audit_period_start format: '{args['audit_period_start']}'. Use YYYY-MM-DD."}

    audit_period_end = None
    if args.get("audit_period_end"):
        try:
            audit_period_end = date.fromisoformat(args["audit_period_end"])
        except ValueError:
            return {"success": False, "error": f"Invalid audit_period_end format: '{args['audit_period_end']}'. Use YYYY-MM-DD."}

    overall_health_score = args.get("overall_health_score")
    if overall_health_score is not None:
        try:
            overall_health_score = int(overall_health_score)
            if not (0 <= overall_health_score <= 100):
                return {"success": False, "error": "overall_health_score must be between 0 and 100."}
        except (TypeError, ValueError):
            return {"success": False, "error": "overall_health_score must be a number between 0 and 100."}

    audit = GovernanceHealthAudit(
        id=uuid.uuid4(),
        ecosystem_id=eco_id,
        audit_id=audit_id,
        audit_date=_today(),
        auditor=auditor,
        capture_risk_indicators=args.get("capture_risk_indicators"),
        findings=findings,
        recommendations=args.get("recommendations"),
        overall_health_score=overall_health_score,
        audit_scope=args.get("audit_scope"),
        audit_period_start=audit_period_start,
        audit_period_end=audit_period_end,
        structured_recommendations=args.get("structured_recommendations"),
        status="draft",
    )
    db.add(audit)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(audit.id),
            "audit_id": audit_id,
            "status": "draft",
            "message": f"Governance health audit '{audit_id}' created.",
        },
    }


# ===================================================================
# TOOL 23: create_repair_agreement
# ===================================================================

async def create_repair_agreement(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Create a repair agreement for a conflict case (an active member of the case's ecosystem, as REST)."""
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    case_id = args.get("case_id", "")
    title = args.get("title", "")
    if not case_id or not title:
        return {"success": False, "error": "'case_id' and 'title' are required."}

    # Validate commitments: must be an array with at least one item
    commitments = args.get("commitments", [])
    if not isinstance(commitments, list) or len(commitments) == 0:
        return {"success": False, "error": "'commitments' must be a non-empty array of commitment objects."}
    for i, c in enumerate(commitments):
        if not isinstance(c, dict):
            return {"success": False, "error": f"commitments[{i}] must be an object with 'commitment' and 'owner' keys."}
        if not c.get("commitment"):
            return {"success": False, "error": f"commitments[{i}].commitment is required."}
        if not c.get("owner"):
            return {"success": False, "error": f"commitments[{i}].owner is required."}

    # Find the conflict case
    case_stmt = select(ConflictCase).where(ConflictCase.case_id == case_id)
    if ecosystem_ids:
        case_stmt = case_stmt.where(ConflictCase.ecosystem_id.in_(ecosystem_ids))
    result = await db.execute(case_stmt)
    case = result.scalar_one_or_none()
    if not case:
        return {"success": False, "error": f"Conflict case '{case_id}' not found."}
    if not is_active_member_in(await _caller_row(db, caller_user_id, case.ecosystem_id), case.ecosystem_id):
        return {"success": False, "error": MEMBER_REQUIRED}

    # Parse optional completed_date
    completed_date = None
    if args.get("completed_date"):
        try:
            completed_date = date.fromisoformat(args["completed_date"])
        except ValueError:
            return {"success": False, "error": f"Invalid completed_date format: '{args['completed_date']}'. Use YYYY-MM-DD."}

    # Auto-set 30/60/90-day check-in dates from today
    today = _today()
    repair = RepairAgreementRecord(
        id=uuid.uuid4(),
        conflict_case_id=case.id,
        title=title,
        commitments=commitments,
        responsible_party=args.get("responsible_party"),
        status="active",
        checkin_30_date=today + timedelta(days=30),
        checkin_30_notes=args.get("checkin_1_notes"),
        checkin_60_date=today + timedelta(days=60),
        checkin_60_notes=args.get("checkin_2_notes"),
        checkin_90_date=today + timedelta(days=90),
        checkin_90_notes=args.get("checkin_3_notes"),
        completed_date=completed_date,
    )
    db.add(repair)
    await db.flush()

    return {
        "success": True,
        "data": {
            "id": str(repair.id),
            "case_id": case_id,
            "title": title,
            "status": "active",
            "commitments_count": len(commitments),
            "checkin_30": str(repair.checkin_30_date),
            "checkin_60": str(repair.checkin_60_date),
            "checkin_90": str(repair.checkin_90_date),
            "message": f"Repair agreement '{title}' created for case {case_id}.",
        },
    }


# ===================================================================
# TOOL 24: list_ecosystems
# ===================================================================

async def list_ecosystems(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """List all ecosystems, optionally filtered by name, status, or visibility."""
    stmt = select(Ecosystem).order_by(Ecosystem.name)

    if args.get("name"):
        stmt = stmt.where(Ecosystem.name.ilike(f"%{args['name']}%"))
    if args.get("status"):
        stmt = stmt.where(Ecosystem.status == args["status"])
    if args.get("visibility"):
        stmt = stmt.where(Ecosystem.visibility == args["visibility"])

    result = await db.execute(stmt)
    ecosystems = result.scalars().all()

    data = [
        {
            "id": str(e.id),
            "name": e.name,
            "description": e.description,
            "status": e.status,
            "location": e.location,
            "website": e.website,
            "visibility": e.visibility,
            "founded_date": str(e.founded_date) if e.founded_date else None,
            "governance_summary": e.governance_summary,
        }
        for e in ecosystems
    ]

    return {
        "success": True,
        "data": {
            "ecosystems": data,
            "count": len(data),
        },
    }


# ===================================================================
# TOOL 25: get_ecosystem
# ===================================================================

async def get_ecosystem(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Get full ecosystem details by name, including member count, domain count, and agreement count."""
    name = args.get("name", "")
    if not name:
        return {"success": False, "error": "'name' is required."}

    stmt = select(Ecosystem).where(func.lower(Ecosystem.name) == name.lower())
    result = await db.execute(stmt)
    eco = result.scalars().first()

    if eco is None:
        # Try partial match
        stmt2 = select(Ecosystem).where(Ecosystem.name.ilike(f"%{name}%"))
        result2 = await db.execute(stmt2)
        eco = result2.scalars().first()

    if eco is None:
        return {"success": False, "error": f"Ecosystem '{name}' not found."}

    # Count members
    member_count = await db.execute(
        select(func.count()).select_from(Member).where(
            Member.ecosystem_id == eco.id,
            Member.current_status == "active",
        )
    )
    member_count = member_count.scalar() or 0

    # Count domains
    domain_count = await db.execute(
        select(func.count()).select_from(Domain).where(Domain.ecosystem_id == eco.id)
    )
    domain_count = domain_count.scalar() or 0

    # Count agreements
    agr_count = await db.execute(
        select(func.count()).select_from(Agreement).where(Agreement.ecosystem_id == eco.id)
    )
    agr_count = agr_count.scalar() or 0

    return {
        "success": True,
        "data": {
            "id": str(eco.id),
            "name": eco.name,
            "description": eco.description,
            "status": eco.status,
            "location": eco.location,
            "website": eco.website,
            "contact_email": eco.contact_email,
            "visibility": eco.visibility,
            "founded_date": str(eco.founded_date) if eco.founded_date else None,
            "tags": eco.tags,
            "governance_summary": eco.governance_summary,
            "active_member_count": member_count,
            "domain_count": domain_count,
            "agreement_count": agr_count,
        },
    }


# ===================================================================
# TOOL 26: search_proposals
# ===================================================================

async def search_proposals(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Search proposals by type, domain, status, proposer, or ecosystem. Returns up to 30 results."""
    stmt = select(Proposal).options(selectinload(Proposal.ecosystem))

    if ecosystem_ids:
        stmt = stmt.where(Proposal.ecosystem_id.in_(ecosystem_ids))

    if "type" in args and args["type"]:
        stmt = stmt.where(Proposal.type == args["type"])
    if "status" in args and args["status"]:
        stmt = stmt.where(Proposal.status == args["status"])
    if "proposer" in args and args["proposer"]:
        stmt = stmt.where(Proposal.proposer.ilike(f"%{args['proposer']}%"))
    if "affected_domain" in args and args["affected_domain"]:
        stmt = stmt.where(Proposal.affected_domain.ilike(f"%{args['affected_domain']}%"))
    if "ecosystem_name" in args and args["ecosystem_name"]:
        stmt = stmt.join(Ecosystem).where(Ecosystem.name.ilike(f"%{args['ecosystem_name']}%"))

    stmt = stmt.order_by(Proposal.created_date.desc()).limit(30)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        return {
            "success": True,
            "data": {
                "proposals": [],
                "count": 0,
                "message": "No proposals found matching the search criteria.",
            },
        }

    proposals = [
        {
            "proposal_id": p.proposal_id,
            "title": p.title,
            "type": p.type,
            "status": p.status,
            "decision_type": p.decision_type,
            "proposer": p.proposer,
            "affected_domain": p.affected_domain,
            "urgency": p.urgency,
            "ecosystem_name": p.ecosystem.name if p.ecosystem else None,
            "created_date": str(p.created_date) if p.created_date else None,
            "version": p.version,
        }
        for p in rows
    ]

    return {"success": True, "data": {"proposals": proposals, "count": len(proposals)}}


# ===================================================================
# TOOL 27: get_proposal
# ===================================================================

async def get_proposal(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """Get full proposal details by business ID, including advice logs, consent records, and test reports."""
    proposal_id = args.get("proposal_id", "")
    if not proposal_id:
        return {"success": False, "error": "'proposal_id' is required."}

    prop = await _find_proposal(
        db, proposal_id, ecosystem_ids,
        selectinload(Proposal.ecosystem),
        selectinload(Proposal.advice_logs).selectinload(AdviceLog.entries),
        selectinload(Proposal.advice_logs).selectinload(AdviceLog.non_respondents),
        selectinload(Proposal.consent_records).selectinload(ConsentRecord.participants),
    )

    if prop is None:
        return {"success": False, "error": f"Proposal '{proposal_id}' not found."}

    advice_data = []
    for log in prop.advice_logs:
        advice_data.append({
            "advice_log_id": str(log.id),
            "window_start": str(log.advice_window_start) if log.advice_window_start else None,
            "window_end": str(log.advice_window_end) if log.advice_window_end else None,
            "urgency": log.urgency,
            "summary": log.summary,
            "proposer_modifications": log.proposer_modifications,
            "entries": [
                {
                    "advisor": e.advisor,
                    "role": e.role,
                    "date": str(e.date) if e.date else None,
                    "advice_text": e.advice_text,
                }
                for e in log.entries
            ],
            "non_respondents": [
                {
                    "name": nr.name,
                    "date_notified": str(nr.date_notified) if nr.date_notified else None,
                    "round": nr.round,
                }
                for nr in log.non_respondents
            ],
        })

    consent_data = []
    for rec in prop.consent_records:
        consent_data.append({
            "consent_mode": rec.consent_mode,
            "date": str(rec.date) if rec.date else None,
            # Rounds live on the positions; the record has no round column.
            "round": max((p.round for p in rec.participants if p.round is not None), default=None),
            "participants": [
                {
                    "name": p.name,
                    "position": p.position,
                    "reason": p.reason,
                    "round": p.round,
                }
                for p in rec.participants
            ],
        })

    data = {
        "proposal_id": prop.proposal_id,
        "title": prop.title,
        "type": prop.type,
        "version": prop.version,
        "status": prop.status,
        "decision_type": prop.decision_type,
        "proposer": prop.proposer,
        "co_sponsors": prop.co_sponsors,
        "affected_domain": prop.affected_domain,
        "impacted_parties": prop.impacted_parties,
        "urgency": prop.urgency,
        "proposed_change": prop.proposed_change,
        "rationale": prop.rationale,
        "created_date": str(prop.created_date) if prop.created_date else None,
        "advice_deadline": str(prop.advice_deadline) if prop.advice_deadline else None,
        "consent_deadline": str(prop.consent_deadline) if prop.consent_deadline else None,
        "test_duration": prop.test_duration,
        "related_proposals": prop.related_proposals,
        "synergy_check": prop.synergy_check,
        "ecosystem_name": prop.ecosystem.name if prop.ecosystem else None,
        "ecosystem_id": str(prop.ecosystem_id),
        "advice_logs": advice_data,
        "consent_records": consent_data,
    }
    return {"success": True, "data": data}


# ===================================================================
# TOOL 28: update_proposal_status
# ===================================================================

async def update_proposal_status(
    args: dict, db: AsyncSession, ecosystem_ids: list | None = None, *, caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Manual ACT move (draft→advice, gated forward moves, withdraw) by the author or a steward.

    Same rules as REST POST /proposals/:id/status: manage rule, transition
    table, then the declared ACT gates; satisfied gates cascade.
    """
    if caller_user_id is None:
        return {"success": False, "error": CALLER_REQUIRED}
    proposal_id = args.get("proposal_id", "")
    new_status = str(args.get("new_status") or "").strip().lower()
    if not proposal_id or not new_status:
        return {"success": False, "error": "'proposal_id' and 'new_status' are required."}

    prop = await _find_proposal(db, proposal_id, ecosystem_ids)
    if prop is None:
        return {"success": False, "error": f"Proposal '{proposal_id}' not found."}

    caller = await _caller_row(db, caller_user_id, prop.ecosystem_id)
    current = prop.status
    try:
        outcome = await transition_proposal(db, prop, to=new_status, caller=caller)
    except TransitionRefused as refusal:
        return {"success": False, "error": _refusal_text(refusal)}
    await db.flush()

    return {
        "success": True,
        "data": {
            "proposal_id": prop.proposal_id,
            "previous_status": current,
            "new_status": outcome.status,
            "auto_transitions": outcome.auto_transitions,
            "decision_record_id": outcome.decision_record_id,
        },
    }


# ===================================================================
# TOOL 29: list_domains
# ===================================================================

async def list_domains(args: dict, db: AsyncSession, ecosystem_ids: list | None = None) -> dict:
    """List domains, optionally filtered by ecosystem, status, or parent. Returns up to 50 results."""
    stmt = select(Domain).order_by(Domain.domain_id)

    if ecosystem_ids:
        stmt = stmt.where(Domain.ecosystem_id.in_(ecosystem_ids))

    if "status" in args and args["status"]:
        stmt = stmt.where(Domain.status == args["status"])

    if "ecosystem_name" in args and args["ecosystem_name"]:
        stmt = stmt.join(Ecosystem).where(Ecosystem.name.ilike(f"%{args['ecosystem_name']}%"))

    if "parent_domain_id" in args and args["parent_domain_id"]:
        # Join parent domain
        parent_alias = Domain
        stmt = stmt.join(parent_alias, Domain.parent_domain_id == parent_alias.id)
        stmt = stmt.where(parent_alias.domain_id.ilike(f"%{args['parent_domain_id']}%"))

    stmt = stmt.limit(50)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        return {
            "success": True,
            "data": {
                "domains": [],
                "count": 0,
                "message": "No domains found matching the criteria.",
            },
        }

    domains = [
        {
            "domain_id": d.domain_id,
            "version": d.version,
            "status": d.status,
            "purpose": d.purpose,
            "current_steward": d.current_steward,
            "ecosystem_id": str(d.ecosystem_id),
            "parent_domain_id": str(d.parent_domain_id) if d.parent_domain_id else None,
        }
        for d in rows
    ]

    return {"success": True, "data": {"domains": domains, "count": len(domains)}}


# ===================================================================
# TOOL REGISTRY
# ===================================================================

@dataclass(frozen=True)
class ToolDef:
    """Definition of a single governance tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable


GOVERNANCE_TOOLS: list[ToolDef] = [
    # 1
    ToolDef(
        name="search_agreements",
        description="Search governance agreements by type, domain, status, affected party, or date range. Returns up to 20 results ordered by status priority (active first) then recency.",
        parameters={
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Agreement type filter (uaf, ecosystem, access, stewardship, ethos, culture_code, space, organizational, policy, protocol, role_definition, domain_contract, guideline)."},
                "domain": {"type": "string", "description": "Partial domain name match."},
                "status": {"type": "string", "description": "Agreement status filter."},
                "affected_party": {"type": "string", "description": "Name of an affected party."},
                "date_from": {"type": "string", "description": "Start date (YYYY-MM-DD)."},
                "date_to": {"type": "string", "description": "End date (YYYY-MM-DD)."},
            },
            "required": [],
        },
        handler=search_agreements,
    ),
    # 2
    ToolDef(
        name="get_agreement",
        description="Get the full details of a governance agreement by its business ID (e.g. AGR-SHUR-2026-001), including ratification records.",
        parameters={
            "type": "object",
            "properties": {
                "agreement_id": {"type": "string", "description": "The agreement business key."},
            },
            "required": ["agreement_id"],
        },
        handler=get_agreement,
    ),
    # 3
    ToolDef(
        name="create_agreement_draft",
        description="Create a new governance agreement in draft status as the signed-in member (who must be an active member of the ecosystem). Generates a unique ID, validates any named proposer and affected parties as active members, and sets default review dates.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Concise, action-oriented title (5-15 words) describing what this agreement establishes."},
                "type": {"type": "string", "description": "Agreement type. Valid values: uaf (Universal Agreement Field), ecosystem, access (access-control agreements), stewardship, ethos, culture_code (cultural norms and code of conduct agreements), space (workspace/resource agreements), organizational (org-structure agreements), policy, protocol, role_definition, domain_contract, guideline."},
                "proposer": {"type": "string", "description": "Optional proposer name or member_id (must be an active member); defaults to the signed-in member."},
                "domain": {"type": "string", "description": "Domain this agreement applies to."},
                "text": {"type": "string", "description": "Full agreement body, 200-2000 words. Must include: purpose, scope, parties, terms, exceptions, sunset criteria."},
                "affected_parties": {"type": "array", "items": {"type": "string"}, "description": "List of affected member names or IDs."},
                "hierarchy_level": {"type": "string", "description": "Hierarchy level (default: domain)."},
                "sunset_date": {"type": "string", "description": "When this agreement expires unless renewed (ISO date, YYYY-MM-DD)."},
                "parent_agreement_id": {"type": "string", "description": "If this amends or supersedes an existing agreement, its business key (e.g. AGR-XXXX-2026-001)."},
                "shared_ecosystem_ids": {"type": "array", "items": {"type": "string"}, "description": "Other ecosystems this agreement applies to (list of ecosystem UUID strings)."},
            },
            "required": ["title", "type", "domain", "text"],
        },
        handler=create_agreement_draft,
    ),
    # 4
    ToolDef(
        name="update_agreement_status",
        description="Conduct an agreement ceremony along its ACT lifecycle (draft -> advice -> consent -> test -> active; active -> under_review -> sunset -> archived). Only an active ecosystem admin or owner may conduct it. Forward ceremonies need documented evidence (at least 8 characters) and the declared gate for that stage; satisfied gates then advance automatically. The version does not change.",
        parameters={
            "type": "object",
            "properties": {
                "agreement_id": {"type": "string", "description": "The agreement business key."},
                "new_status": {"type": "string", "description": "Target status."},
                "evidence": {"type": "string", "description": "What happened at the ceremony (required for advice, consent, test and active; at least 8 characters)."},
            },
            "required": ["agreement_id", "new_status"],
        },
        handler=update_agreement_status,
    ),
    # 5
    ToolDef(
        name="check_authority",
        description="Check whether a member has authority to perform a specific action in a given domain. Returns authorization status, reason, and role source.",
        parameters={
            "type": "object",
            "properties": {
                "member": {"type": "string", "description": "Member name or member_id."},
                "domain": {"type": "string", "description": "Domain ID or name."},
                "action": {"type": "string", "description": "The action to check authorization for."},
            },
            "required": ["member", "domain"],
        },
        handler=check_authority,
    ),
    # 6
    ToolDef(
        name="get_member_roles",
        description="Get all active role assignments for a member, including domain stewardships and ecosystem profile roles.",
        parameters={
            "type": "object",
            "properties": {
                "member": {"type": "string", "description": "Member name or member_id."},
            },
            "required": ["member"],
        },
        handler=get_member_roles,
    ),
    # 7
    ToolDef(
        name="create_proposal",
        description="Create a new ACT (Advice-Consent-Test) proposal as a draft authored by the signed-in member. Auto-sets consent mode to consensus for OSC/UAF scope, consent otherwise.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Proposal title."},
                "type": {"type": "string", "description": "Proposal type."},
                "proposer": {"type": "string", "description": "Optional display name of who the proposal is on behalf of; defaults to the signed-in member. The signed-in member is always the author."},
                "proposed_change": {"type": "string", "description": "3-10 sentences describing exactly what changes (policy, allocation, structure). Concrete and actionable, not aspirational."},
                "rationale": {"type": "string", "description": "3-10 sentences explaining WHY this change is needed, what problem it solves, and the expected impact."},
                "scope": {"type": "string", "description": "Decision scope (used for consent-mode auto-detection)."},
                "decision_type": {"type": "string", "description": "Explicit decision type hint."},
                "affected_domain": {"type": "string", "description": "Domain affected by this proposal."},
                "impacted_parties": {"type": "array", "items": {"type": "string"}, "description": "List of impacted parties."},
                "urgency": {"type": "string", "description": "Urgency level (low, medium, high, critical)."},
                "co_sponsors": {"type": "array", "items": {"type": "string"}, "description": "Member names co-sponsoring this proposal."},
                "advice_deadline": {"type": "string", "description": "When advice-gathering closes (ISO date, YYYY-MM-DD)."},
                "consent_deadline": {"type": "string", "description": "When consent voting closes (ISO date, YYYY-MM-DD)."},
            },
            "required": ["title", "type", "proposed_change", "rationale"],
        },
        handler=create_proposal,
    ),
    # 8
    ToolDef(
        name="record_advice",
        description="Record the signed-in member's advice on a proposal in the advice phase. The advisor is always the signed-in member; the proposal's author cannot advise their own proposal. Completing the declared advice rounds advances it to consent.",
        parameters={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "Proposal business key (PROP-...) or id."},
                "advice_text": {"type": "string", "description": "The advice content (required, not blank)."},
            },
            "required": ["proposal_id", "advice_text"],
        },
        handler=record_advice,
    ),
    # 9
    ToolDef(
        name="record_consent_position",
        description="Record the signed-in member's own consent position (consent, stand_aside, or objection) on a proposal in the consent phase. The participant is always the signed-in member. Stand-aside disallowed in consensus mode. Reason required for stand_aside and objection. The consent gate then advances the proposal as in the app.",
        parameters={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "Proposal business key (PROP-...) or id."},
                "position": {"type": "string", "description": "Position: consent, stand_aside, or objection."},
                "reason": {"type": "string", "description": "Reason (required for stand_aside and objection)."},
                "round": {"type": "integer", "description": "Consent round number (default: 1)."},
            },
            "required": ["proposal_id", "position"],
        },
        handler=record_consent_position,
    ),
    # 10
    ToolDef(
        name="check_quorum",
        description="Check if quorum is met for a proposal's consent round. Consent mode: 2/3 threshold. Consensus mode: 100%. Emergency: 50%.",
        parameters={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "Proposal business key."},
            },
            "required": ["proposal_id"],
        },
        handler=check_quorum,
    ),
    # 11
    ToolDef(
        name="create_decision_record",
        description="Record a decision outside the ACT process (ecosystem stewards only; the signed-in member is the recorder) with auto-generated ID, layer/skill tagging, and semantic tags.",
        parameters={
            "type": "object",
            "properties": {
                "holding": {"type": "string", "description": "1-3 sentences stating the decision outcome (what was decided)."},
                "rationale": {"type": "string", "description": "3-8 sentences explaining the reasoning behind the decision (ratio decidendi)."},
                "source_skill": {"type": "string", "description": "NEOS skill that produced this decision."},
                "source_layer": {"type": "integer", "description": "NEOS layer number (1-10)."},
                "artifact_type": {"type": "string", "description": "Type of source artifact."},
                "artifact_reference": {"type": "string", "description": "Reference to source artifact."},
                "domain": {"type": "string", "description": "Domain context."},
                "precedent_level": {"type": "string", "description": "Precedent level (default: domain)."},
                "recorder_role": {"type": "string", "description": "Role of the person recording, e.g. 'facilitator', 'secretary'."},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Semantic tags for discoverability."},
                "deliberation_summary": {"type": "string", "description": "Summary of the deliberation that led to this decision, 2-5 sentences."},
                "obiter_dicta": {"type": "string", "description": "Side remarks or non-binding observations."},
                "participants": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "member_name": {"type": "string", "description": "Member display name."},
                            "position": {"type": "string", "description": "Their position (e.g. consent, stand_aside, objection)."}
                        },
                        "required": ["member_name"]
                    },
                    "description": "Members who participated in the decision."
                },
                "dissents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "member_name": {"type": "string", "description": "Member display name."},
                            "rationale": {"type": "string", "description": "Their reasoning for dissenting."}
                        },
                        "required": ["member_name"]
                    },
                    "description": "Recorded dissents with reasoning."
                },
            },
            "required": ["holding", "rationale"],
        },
        handler=create_decision_record,
    ),
    # 12
    ToolDef(
        name="search_precedents",
        description="Search decision records by skill, domain, semantic tags, or text. Results ordered by tag relevance then recency.",
        parameters={
            "type": "object",
            "properties": {
                "skill": {"type": "string", "description": "Source skill filter."},
                "domain": {"type": "string", "description": "Domain filter (partial match)."},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Semantic tag filter (OR logic)."},
                "text": {"type": "string", "description": "Case-insensitive text search in holding and rationale."},
                "limit": {"type": "integer", "description": "Max results (default: 10)."},
            },
            "required": [],
        },
        handler=search_precedents,
    ),
    # 13
    ToolDef(
        name="get_domain",
        description="Get the full domain contract including all S3 elements, domain elements, metric definitions, and current steward.",
        parameters={
            "type": "object",
            "properties": {
                "domain_id": {"type": "string", "description": "Domain business key or partial name."},
            },
            "required": ["domain_id"],
        },
        handler=get_domain,
    ),
    # 14
    ToolDef(
        name="get_active_members",
        description="Get all active ecosystem members. Supports optional profile filter (co_creator, builder, collaborator, townhall).",
        parameters={
            "type": "object",
            "properties": {
                "profile": {"type": "string", "enum": ["co_creator", "builder", "collaborator", "townhall"], "description": "Filter by member profile."},
            },
            "required": [],
        },
        handler=get_active_members,
    ),
    # 15
    ToolDef(
        name="create_conflict_case",
        description="Report a new conflict or harm requiring governance process, as the signed-in member (the reporter). Routes through Layer VI conflict resolution.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Concise neutral framing (5-15 words). Avoid blame language."},
                "description": {"type": "string", "description": "Full description of the conflict: what happened, when, who was involved, what's at stake. 3-10 sentences minimum."},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Severity level."},
                "scope": {"type": "string", "enum": ["individual", "interpersonal", "role", "domain", "cross-domain", "circle", "cross-circle", "ecosystem", "cross-ecosystem", "structural"], "description": "Scope of conflict."},
                "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Urgency level."},
                "safety_flag": {"type": "boolean", "description": "True if safety is at risk."},
                "parties": {"type": "array", "items": {"type": "string"}, "description": "Names of involved parties."},
                "facilitator_id": {"type": "string", "description": "UUID of the assigned facilitator if known."},
                "domain": {"type": "string", "description": "Affected domain or area of work."},
                "triage_notes": {"type": "string", "description": "Initial triage observations."},
            },
            "required": ["title", "description"],
        },
        handler=create_conflict_case,
    ),
    # 16
    ToolDef(
        name="triage_conflict",
        description="Assess and route a conflict to the appropriate resolution tier (1=NVC Dialogue, 2=Coaching, 3=Harm Circle, 4=Community Impact Assessment).",
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Conflict case business key."},
                "tier": {"type": "integer", "description": "Resolution tier (1-4)."},
                "severity": {"type": "string", "description": "Updated severity."},
                "scope": {"type": "string", "description": "Updated scope."},
                "root_cause_category": {"type": "string", "description": "Root cause category."},
                "triage_notes": {"type": "string", "description": "Triage assessment notes."},
            },
            "required": ["case_id", "tier"],
        },
        handler=triage_conflict,
    ),
    # 17
    ToolDef(
        name="get_emergency_state",
        description="Check the current circuit breaker state (closed=normal, open=emergency, half_open=recovery).",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=get_emergency_state,
    ),
    # 18
    ToolDef(
        name="declare_emergency",
        description="Declare an emergency as the signed-in member (an active member of the ecosystem) and open the circuit breaker. Auto-expires in 30 days. Cannot be called if an emergency is already active.",
        parameters={
            "type": "object",
            "properties": {
                "criteria_met": {"type": "object", "description": "Which emergency criteria were met."},
                "notes": {"type": "string", "description": "Additional notes."},
            },
            "required": [],
        },
        handler=declare_emergency,
    ),
    # 19
    ToolDef(
        name="create_exit_record",
        description="Start the signed-in member's own voluntary exit process. Creates a 30-day (standard) or 7-day (urgent) departure timeline. It cannot start anyone else's exit.",
        parameters={
            "type": "object",
            "properties": {
                "departure_notice": {"type": "string", "description": "Explanation of reason for departure, what the member intends to do with their commitments, transition timeline. 3-10 sentences."},
                "exit_type": {"type": "string", "enum": ["standard", "urgent"], "description": "Exit type (standard=30d, urgent=7d)."},
                "data_export": {"type": "boolean", "description": "Whether to request portable data export."},
                "commitment_inventory": {"type": ["string", "array"], "description": "List or description of in-flight commitments the member is leaving behind."},
                "coordinator": {"type": "string", "description": "Name or member_id of the departure coordinator (must be active member)."},
            },
            "required": ["departure_notice"],
        },
        handler=create_exit_record,
    ),
    # 20
    ToolDef(
        name="create_domain_draft",
        description="Create a new domain contract in draft status. Only an ecosystem steward (moderator or above) can create domains. Validates steward as active member and checks for duplicate domain IDs.",
        parameters={
            "type": "object",
            "properties": {
                "domain_id": {"type": "string", "description": "Unique domain identifier (business key, e.g. 'operations', 'governance')."},
                "name": {"type": "string", "description": "Human name of the domain, shown instead of the business key."},
                "purpose": {"type": "string", "description": "Purpose statement for the domain."},
                "steward": {"type": "string", "description": "Name or member_id of the domain steward (must be active member)."},
                "parent_domain_id": {"type": "string", "description": "Parent domain business key (for nested domains)."},
                "elements": {
                    "type": "object",
                    "description": "S3 domain definition. Required keys: drivers (list of strings — what motivates work in this domain), deliverables (list of strings — concrete outputs), domain_owner (string — accountable role), sub_domains (list of strings, optional). Example: {\"drivers\": [\"Need to coordinate resources\"], \"deliverables\": [\"Monthly budget report\"], \"domain_owner\": \"Finance Lead\", \"sub_domains\": []}",
                    "properties": {
                        "drivers": {"type": "array", "items": {"type": "string"}, "description": "What motivates work in this domain."},
                        "deliverables": {"type": "array", "items": {"type": "string"}, "description": "Concrete outputs of this domain."},
                        "domain_owner": {"type": "string", "description": "Accountable role for this domain."},
                        "sub_domains": {"type": "array", "items": {"type": "string"}, "description": "Sub-domains nested under this domain."}
                    },
                    "required": ["drivers", "deliverables"]
                },
                "metric_definitions": {
                    "type": "object",
                    "description": "Dict mapping metric name to definition: {metric_name: {description: str, unit: str, target: number|null, frequency: str}}. Example: {\"on_time_delivery\": {\"description\": \"% deliverables on time\", \"unit\": \"percent\", \"target\": 90, \"frequency\": \"monthly\"}}."
                },
            },
            "required": ["domain_id", "purpose"],
        },
        handler=create_domain_draft,
    ),
    # 21
    ToolDef(
        name="create_ecosystem",
        description="Create a new NEOS ecosystem founded by the signed-in member, who joins it with a core governance domain they steward. Checks for duplicate names. Sets founded date to today.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Ecosystem name (must be unique)."},
                "description": {"type": "string", "description": "Description of the ecosystem."},
                "location": {"type": "string", "description": "Physical location or region."},
                "website": {"type": "string", "description": "Website URL."},
                "contact_email": {"type": "string", "description": "Primary contact email."},
                "governance_summary": {"type": "string", "description": "Brief governance model summary."},
                "tags": {"type": "object", "description": "Descriptive tags."},
                "visibility": {"type": "string", "enum": ["public", "private", "unlisted"], "description": "Visibility (default: public)."},
            },
            "required": ["name"],
        },
        handler=create_ecosystem,
    ),
    # 22
    ToolDef(
        name="create_safeguard_audit",
        description="Create a governance health audit draft (Layer VII safeguard). Auto-generates audit ID. Used to assess capture risk, governance health, and structural diversity.",
        parameters={
            "type": "object",
            "properties": {
                "findings": {"type": "string", "description": "Detailed findings from the audit, 5-20 sentences covering observed health, risks, and patterns."},
                "audit_scope": {"type": "string", "description": "What was audited (specific safeguard, domain, or ecosystem-wide)."},
                "audit_period_start": {"type": "string", "description": "Start of the audit period (ISO date, YYYY-MM-DD)."},
                "audit_period_end": {"type": "string", "description": "End of the audit period (ISO date, YYYY-MM-DD)."},
                "overall_health_score": {"type": "number", "minimum": 0, "maximum": 100, "description": "Aggregate health score (0-100)."},
                "capture_risk_indicators": {"type": "object", "description": "Capture risk indicator assessments."},
                "recommendations": {"type": "object", "description": "General recommendations for governance improvements."},
                "structured_recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "recommendation": {"type": "string", "description": "The recommendation text."},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level."},
                            "owner": {"type": "string", "description": "Who is responsible for acting on this."}
                        },
                        "required": ["recommendation", "priority", "owner"]
                    },
                    "description": "Structured recommendations with priority and owner."
                },
            },
            "required": ["findings"],
        },
        handler=create_safeguard_audit,
    ),
    # 23
    ToolDef(
        name="create_repair_agreement",
        description="Create a repair agreement for a conflict case (Layer VI). Auto-sets 30/60/90-day check-in dates. Links to an existing conflict case.",
        parameters={
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Conflict case business key (e.g. CONF-XXXXXXXX)."},
                "title": {"type": "string", "description": "Title of the repair agreement."},
                "commitments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "commitment": {"type": "string", "description": "What will be done."},
                            "owner": {"type": "string", "description": "Who is responsible."},
                            "deadline": {"type": "string", "description": "By when (ISO date, YYYY-MM-DD, optional)."}
                        },
                        "required": ["commitment", "owner"]
                    },
                    "description": "Binding repair commitments. Each item must have 'commitment' (what) and 'owner' (who), and optionally 'deadline' (by when). At least one commitment is required."
                },
                "responsible_party": {"type": "string", "description": "Name of the primary party responsible for repair."},
                "checkin_1_notes": {"type": "string", "description": "Notes from the first (30-day) check-in if already completed."},
                "checkin_2_notes": {"type": "string", "description": "Notes from the second (60-day) check-in if already completed."},
                "checkin_3_notes": {"type": "string", "description": "Notes from the third (90-day) check-in if already completed."},
                "completed_date": {"type": "string", "description": "Date the repair agreement was completed (ISO date, YYYY-MM-DD)."},
            },
            "required": ["case_id", "title", "commitments"],
        },
        handler=create_repair_agreement,
    ),
    # 24
    ToolDef(
        name="list_ecosystems",
        description="List all NEOS ecosystems. Supports optional filters by name (partial match), status, or visibility. Use this to discover available ecosystems like Escherbridge, OmniOne, etc.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Partial name match (e.g. 'escher' matches Escherbridge)."},
                "status": {"type": "string", "enum": ["active", "forming", "inactive"], "description": "Filter by ecosystem status."},
                "visibility": {"type": "string", "enum": ["public", "private", "unlisted"], "description": "Filter by visibility."},
            },
            "required": [],
        },
        handler=list_ecosystems,
    ),
    # 25
    ToolDef(
        name="get_ecosystem",
        description="Get full details of an ecosystem by name, including description, location, website, active member count, domain count, and agreement count. Use this to get details about a specific ecosystem like Escherbridge or OmniOne.",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Ecosystem name (exact or partial match, case-insensitive)."},
            },
            "required": ["name"],
        },
        handler=get_ecosystem,
    ),
    # 26
    ToolDef(
        name="search_proposals",
        description="Search proposals by type, domain, status, proposer, or ecosystem name. Returns up to 30 results ordered by recency (newest first). Supports filtering to find proposals in specific ecosystems or domains.",
        parameters={
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "Proposal type filter."},
                "status": {"type": "string", "description": "Proposal status filter (draft, created, advice, consent, test, ratified, implemented, rejected, withdrawn, archived)."},
                "proposer": {"type": "string", "description": "Partial proposer name match."},
                "affected_domain": {"type": "string", "description": "Partial affected domain match."},
                "ecosystem_name": {"type": "string", "description": "Partial ecosystem name match (e.g. 'escher' for Escherbridge)."},
            },
            "required": [],
        },
        handler=search_proposals,
    ),
    # 27
    ToolDef(
        name="get_proposal",
        description="Get full proposal details by its business ID (e.g. PROP-2026-001), including title, type, status, decision type, rationale, proposed change, advice logs with entries, and consent records with participant positions. Use to inspect a specific proposal in detail.",
        parameters={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "The proposal business key (e.g. PROP-2026-001) or id."},
            },
            "required": ["proposal_id"],
        },
        handler=get_proposal,
    ),
    # 28
    ToolDef(
        name="update_proposal_status",
        description="Move a proposal through the ACT lifecycle (draft → advice → consent → test → ratified) or withdraw it. Only the proposal's author or an ecosystem steward may do this, and forward moves require the declared ACT gates to be met.",
        parameters={
            "type": "object",
            "properties": {
                "proposal_id": {"type": "string", "description": "The proposal business key or id."},
                "new_status": {"type": "string", "description": "Target status (advice, consent, test, ratified, withdrawn)."},
            },
            "required": ["proposal_id", "new_status"],
        },
        handler=update_proposal_status,
    ),
    # 29
    ToolDef(
        name="list_domains",
        description="List domains, optionally filtered by ecosystem name, status, or parent domain. Returns up to 50 results with domain ID, purpose, steward, and nesting info. Use to discover domains in ecosystems like Escherbridge (Creative Tech Studio, Creative Arts Studio, Creative Fabrication Lab).",
        parameters={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Domain status filter (draft, active, archived)."},
                "ecosystem_name": {"type": "string", "description": "Partial ecosystem name match (e.g. 'escher' for Escherbridge)."},
                "parent_domain_id": {"type": "string", "description": "Partial parent domain ID match (for sub-domains)."},
            },
            "required": [],
        },
        handler=list_domains,
    ),
]


def get_tool_definitions() -> list[dict]:
    """Return tool definitions in Claude API format."""
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.parameters,
        }
        for t in GOVERNANCE_TOOLS
    ]


# ---------------------------------------------------------------------------
# Error-mapping helpers for execute_tool
# ---------------------------------------------------------------------------

def _friendly_integrity_error(e: IntegrityError) -> str:
    """Parse a SQLAlchemy IntegrityError into a human-readable message."""
    orig_str = str(getattr(e, "orig", e))
    # NOT NULL violation: psycopg2 format: 'null value in column "col" ...'
    not_null = re.search(r'null value in column ["\']?(\w+)["\']?', orig_str, re.IGNORECASE)
    if not_null:
        return f"Required field missing: {not_null.group(1)}"
    # UNIQUE violation: 'duplicate key value violates unique constraint "..."'
    unique = re.search(r'duplicate key.*?Detail:\s*Key \(([^)]+)\)=\(([^)]+)\)', orig_str, re.IGNORECASE | re.DOTALL)
    if unique:
        return f"Already exists: {unique.group(1)}={unique.group(2)}"
    # Simpler unique without detail
    unique2 = re.search(r'UNIQUE constraint failed: (\S+)', orig_str, re.IGNORECASE)
    if unique2:
        return f"Already exists: {unique2.group(1)}"
    # FK violation: 'insert or update on table ... violates foreign key constraint'
    fk = re.search(r'foreign key constraint.*?Key \(([^)]+)\)', orig_str, re.IGNORECASE | re.DOTALL)
    if fk:
        return f"Referenced record does not exist: {fk.group(1)}"
    # SQLite FK
    fk2 = re.search(r'FOREIGN KEY constraint failed', orig_str, re.IGNORECASE)
    if fk2:
        return "Referenced record does not exist (foreign key constraint)."
    return f"Database integrity error: {orig_str[:200]}"


def _sanitize_db_error(s: str) -> str:
    """Strip SQL fragments and parameter dumps from error strings."""
    # Remove [SQL: ...] blocks
    s = re.sub(r'\[SQL:.*', '', s, flags=re.DOTALL).strip()
    # Remove [parameters: ...] blocks
    s = re.sub(r'\[parameters:.*', '', s, flags=re.DOTALL).strip()
    return s[:200]


# ---------------------------------------------------------------------------
# Tool dispatch registry (keyed by name for O(1) lookup)
# ---------------------------------------------------------------------------

_TOOL_HANDLERS: dict[str, Callable] = {t.name: t.handler for t in GOVERNANCE_TOOLS}

# Every state-changing tool acts as the signed-in member and refuses to run without one.
CALLER_SCOPED_TOOLS = frozenset({
    "create_agreement_draft",
    "update_agreement_status",
    "create_proposal",
    "record_advice",
    "record_consent_position",
    "create_decision_record",
    "create_conflict_case",
    "triage_conflict",
    "declare_emergency",
    "create_exit_record",
    "create_domain_draft",
    "create_ecosystem",
    "create_safeguard_audit",
    "create_repair_agreement",
    "update_proposal_status",
})


async def execute_tool(
    name: str,
    args: dict,
    db_session: AsyncSession,
    ecosystem_ids: list | None = None,
    caller_user_id: uuid.UUID | None = None,
) -> dict:
    """Execute a governance tool by name with friendly error mapping."""
    handler = _TOOL_HANDLERS.get(name)
    if not handler:
        return {"success": False, "error": f"Unknown tool: {name}"}
    if not isinstance(args, dict):
        args = {}
    try:
        if name in CALLER_SCOPED_TOOLS:
            return await handler(args, db_session, ecosystem_ids=ecosystem_ids, caller_user_id=caller_user_id)
        return await handler(args, db_session, ecosystem_ids=ecosystem_ids)
    except IntegrityError as e:
        msg = _friendly_integrity_error(e)
        await db_session.rollback()
        return {"success": False, "error": msg}
    except (DataError, StatementError) as e:
        await db_session.rollback()
        return {"success": False, "error": f"Validation failed: {_sanitize_db_error(str(e))}"}
    except Exception as e:
        logger.exception("Tool handler crashed: %s", name)
        return {"success": False, "error": f"Tool failed: {type(e).__name__}"}
