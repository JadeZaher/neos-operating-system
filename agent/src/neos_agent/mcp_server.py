"""MCP server: NEOS governance tools for a logged-in user's own agents.

Exposes permissioned agreement-building work over the Model Context
Protocol (streamable HTTP). Agents authenticate with a bearer token minted
via POST /api/v1/agent-tokens; the token is bound to the auth session it
came from, so logout/revocation ends the agent's access — agent authority
is always session-scoped, and every tool re-resolves the user's live
memberships and roles.

Run:
    python -m neos_agent.mcp_server --port 8100
    # then connect any MCP client to http://<host>:8100/mcp with
    # Authorization: Bearer neos_agt_<token>
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from mcp.server.fastmcp import Context, FastMCP

from neos_agent.config import get_settings
from neos_agent.api.agreements import _snapshot_agreement
from neos_agent.db.models import (
    AdviceEntry,
    AdviceLog,
    AgentToken,
    Agreement,
    AgreementCeremony,
    AgreementMemberConsent,
    AuthSession,
    ConsentParticipant,
    ConsentRecord,
    DecisionRecord,
    Ecosystem,
    Member,
    Proposal,
    TestReport,
    TestSuccessCriterion,
    User,
)
from neos_agent.services.act_gates import (
    agreement_gate_status,
    maybe_auto_advance_agreement,
    maybe_auto_advance_proposal,
    normalize_act_policy,
    proposal_gate_status,
    record_agreement_commitment,
)
from neos_agent.services.agreement_consent import (
    _PARTICIPATING_MEMBER_STATUSES,
    synchronize_agreement_requirements,
)
from neos_agent.services.fingerprint import generate_fingerprint

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "neos-governance",
    instructions=(
        "NEOS governance tools. You act as the token owner's agent inside "
        "their ecosystems: build agreements and proposals through the ACT "
        "process (advice rounds, consent, test cases). Gates are declared on "
        "the record (or inherited from a proposal's governing agreement) and "
        "status advances automatically when conditions are met. Completing "
        "the process mints a browsable decision artifact. You may only act "
        "in ecosystems where the owner is a participating member."
    ),
)

_engine = None
_session_factory: async_sessionmaker | None = None


def _db() -> async_sessionmaker:
    global _engine, _session_factory
    if _session_factory is None:
        _engine = create_async_engine(get_settings().DATABASE_URL)
        _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _session_factory


# ---------------------------------------------------------------------------
# Auth + permission helpers
# ---------------------------------------------------------------------------


@dataclass
class Caller:
    user: User
    token: AgentToken


async def _caller(ctx: Context) -> Caller:
    """Resolve the bearer token to a user — session-scoped authority.

    A token is valid only while: not revoked, not expired, AND the auth
    session it was minted from is still alive. Logout kills the agent.
    """
    request = getattr(ctx.request_context, "request", None)
    if request is None:
        raise ValueError("MCP transport unavailable for authentication")
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ValueError("Authorization: Bearer <agent token> required")
    digest = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()

    now = datetime.now(timezone.utc)
    async with _db()() as s:
        agent_token = await s.scalar(
            select(AgentToken).where(AgentToken.token_hash == digest)
        )
        if (
            agent_token is None
            or agent_token.revoked_at is not None
            or agent_token.expires_at <= now
        ):
            raise ValueError("Agent token invalid, expired, or revoked")
        parent_alive = await s.scalar(
            select(AuthSession.id).where(
                AuthSession.id == agent_token.auth_session_id,
                AuthSession.expires_at > now,
            )
        )
        if parent_alive is None:
            raise ValueError("The session this agent token belongs to has ended — mint a new token")
        user = await s.get(User, agent_token.user_id)
        if user is None:
            raise ValueError("Token owner no longer exists")
        # Throttled liveness stamp (at most one write per minute).
        if agent_token.last_used_at is None or agent_token.last_used_at < now - timedelta(minutes=1):
            agent_token.last_used_at = now
            await s.commit()
        return Caller(user=user, token=agent_token)


async def _member(s: AsyncSession, user_id: uuid.UUID, ecosystem_id: uuid.UUID) -> Member:
    """The caller's Member row in the ecosystem, or a clear refusal."""
    member = await s.scalar(
        select(Member).where(Member.user_id == user_id, Member.ecosystem_id == ecosystem_id)
    )
    if member is None:
        raise ValueError("The token owner is not a member of this ecosystem")
    if member.current_status not in _PARTICIPATING_MEMBER_STATUSES:
        raise ValueError(
            f"The token owner's membership status is '{member.current_status}' — only participating members may act"
        )
    return member


async def _resolve(s: AsyncSession, model, id_or_business_id: str, business_field: str):
    """Accept a UUID or a business id (PROP-/AGR-/DEC-...)."""
    raw = id_or_business_id.strip()
    try:
        return await s.get(model, uuid.UUID(raw))
    except ValueError:
        pass
    return await s.scalar(select(model).where(getattr(model, business_field) == raw))


async def _load_agreement(s: AsyncSession, id_or_business_id: str) -> Agreement | None:
    """Resolve an agreement with the relationships the ACT engine touches.

    Without selectinload, engine access to agreement.ceremonies /
    ratification_records triggers a lazy load that crashes async sessions
    ("greenlet_spawn has not been called").
    """
    raw = id_or_business_id.strip()
    stmt = select(Agreement).options(
        selectinload(Agreement.ratification_records),
        selectinload(Agreement.ceremonies),
    )
    try:
        stmt = stmt.where(Agreement.id == uuid.UUID(raw))
    except ValueError:
        stmt = stmt.where(Agreement.agreement_id == raw)
    return (await s.execute(stmt)).scalar_one_or_none()


def _gates_error(prefix: str, gates: dict) -> ValueError:
    return ValueError(f"{prefix}. Current gates: {gates}")


# Mirrors api/agreements.py — the ACT lifecycle plus review/sunset chain.
_AGREEMENT_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"advice"},
    "advice": {"consent"},
    "consent": {"test"},
    "test": {"active"},
    "active": {"under_review"},
    "under_review": {"sunset", "active"},
    "sunset": {"archived"},
}


def _parse_cases(test_cases: list[str] | None) -> list[str]:
    return [c.strip() for c in (test_cases or []) if c and c.strip()][:20]


# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_my_ecosystems(ctx: Context) -> list[dict]:
    """List the ecosystems the token owner belongs to, with their role and status."""
    caller = await _caller(ctx)
    async with _db()() as s:
        rows = (await s.execute(
            select(Member, Ecosystem)
            .join(Ecosystem, Ecosystem.id == Member.ecosystem_id)
            .where(Member.user_id == caller.user.id)
            .order_by(Ecosystem.name)
        )).all()
        return [
            {
                "ecosystem_id": str(eco.id),
                "name": eco.name,
                "member_role": m.role,
                "member_status": m.current_status,
                "member_display_name": m.display_name,
                "can_act": m.current_status in _PARTICIPATING_MEMBER_STATUSES,
            }
            for m, eco in rows
        ]


@mcp.tool()
async def list_agreements(ecosystem_id: str, ctx: Context, status: str | None = None) -> list[dict]:
    """List agreements in one of the owner's ecosystems (optionally by status)."""
    caller = await _caller(ctx)
    eco_uuid = uuid.UUID(ecosystem_id)
    async with _db()() as s:
        await _member(s, caller.user.id, eco_uuid)
        stmt = select(Agreement).where(Agreement.ecosystem_id == eco_uuid).order_by(Agreement.created_at.desc())
        if status:
            stmt = stmt.where(Agreement.status == status)
        agreements = (await s.execute(stmt.limit(100))).scalars().all()
        return [
            {
                "id": str(a.id),
                "agreement_id": a.agreement_id,
                "title": a.title,
                "type": a.type,
                "status": a.status,
                "version": a.version,
            }
            for a in agreements
        ]


@mcp.tool()
async def get_agreement_gates(agreement_id: str, ctx: Context) -> dict:
    """Live ACT gate status for an agreement (advice/consent/test conditions)."""
    caller = await _caller(ctx)
    async with _db()() as s:
        agreement = await _load_agreement(s, agreement_id)
        if agreement is None:
            raise ValueError("Agreement not found")
        await _member(s, caller.user.id, agreement.ecosystem_id)
        gates = await agreement_gate_status(s, agreement)
        return {"agreement_id": agreement.agreement_id, "status": agreement.status, "gates": gates}


@mcp.tool()
async def list_proposals(ecosystem_id: str, ctx: Context, status: str | None = None) -> list[dict]:
    """List proposals in one of the owner's ecosystems (optionally by status)."""
    caller = await _caller(ctx)
    eco_uuid = uuid.UUID(ecosystem_id)
    async with _db()() as s:
        await _member(s, caller.user.id, eco_uuid)
        stmt = select(Proposal).where(Proposal.ecosystem_id == eco_uuid).order_by(Proposal.created_at.desc())
        if status:
            stmt = stmt.where(Proposal.status == status)
        proposals = (await s.execute(stmt.limit(100))).scalars().all()
        return [
            {
                "id": str(p.id),
                "proposal_id": p.proposal_id,
                "title": p.title,
                "type": p.type,
                "status": p.status,
                "version": p.version,
            }
            for p in proposals
        ]


@mcp.tool()
async def get_proposal_gates(proposal_id: str, ctx: Context) -> dict:
    """Live ACT gate status for a proposal, including whether gates are
    declared on the proposal or inherited from its governing agreement."""
    caller = await _caller(ctx)
    async with _db()() as s:
        proposal = await _resolve(s, Proposal, proposal_id, "proposal_id")
        if proposal is None:
            raise ValueError("Proposal not found")
        await _member(s, caller.user.id, proposal.ecosystem_id)
        gates = await proposal_gate_status(s, proposal)
        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "governing_agreement_id": str(proposal.governing_agreement_id) if proposal.governing_agreement_id else None,
            "gates": gates,
        }


@mcp.tool()
async def list_decision_artifacts(ecosystem_id: str, ctx: Context, artifact_type: str | None = None) -> list[dict]:
    """Browse decision artifacts minted by completed ACT processes.

    artifact_type: "proposal" (ratified proposals) or "commitment"
    (activated agreements — members' positions are the commitments).
    """
    caller = await _caller(ctx)
    eco_uuid = uuid.UUID(ecosystem_id)
    async with _db()() as s:
        await _member(s, caller.user.id, eco_uuid)
        stmt = select(DecisionRecord).where(DecisionRecord.ecosystem_id == eco_uuid).order_by(DecisionRecord.date.desc())
        if artifact_type:
            stmt = stmt.where(DecisionRecord.artifact_type == artifact_type)
        records = (await s.execute(stmt.limit(100))).scalars().all()
        return [
            {
                "id": str(r.id),
                "record_id": r.record_id,
                "artifact_type": r.artifact_type,
                "date": r.date.isoformat() if r.date else None,
                "holding": r.holding,
                "source_proposal_id": str(r.source_proposal_id) if r.source_proposal_id else None,
                "source_agreement_id": str(r.source_agreement_id) if r.source_agreement_id else None,
            }
            for r in records
        ]


# ---------------------------------------------------------------------------
# Agreement write tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_agreement(
    ecosystem_id: str,
    type: str,
    title: str,
    ctx: Context,
    text: str | None = None,
    domain: str | None = None,
    min_advice_rounds: int | None = None,
    test_cases: list[str] | None = None,
) -> dict:
    """Create a DRAFT agreement declaring its ACT gates.

    The process opens with a manual advice ceremony; status then advances
    automatically as the declared conditions are met. min_advice_rounds
    defaults to 1; test_cases are the declared success criteria.
    """
    caller = await _caller(ctx)
    eco_uuid = uuid.UUID(ecosystem_id)
    async with _db()() as s:
        member = await _member(s, caller.user.id, eco_uuid)
        policy = normalize_act_policy({
            "min_advice_rounds": min_advice_rounds if min_advice_rounds is not None else 1,
            "consent_required": True,
            "test_cases": _parse_cases(test_cases),
        })
        agreement = Agreement(
            id=uuid.uuid4(),
            ecosystem_id=eco_uuid,
            agreement_id=f"AGR-{uuid.uuid4().hex[:8].upper()}",
            type=type.strip(),
            title=title.strip(),
            version="1.0",
            status="draft",
            proposer=member.display_name,
            domain=domain,
            text=text,
            hierarchy_level="domain",
            created_date=date.today(),
            requires_explicit_consent=True,
            prerequisite_scopes=[],
            prerequisite_domain_ids=[],
            alignment_points=5,
            act_policy=policy,
        )
        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )
        s.add(agreement)
        await s.flush()
        await synchronize_agreement_requirements(s, agreement)
        await s.commit()
        return {
            "id": str(agreement.id),
            "agreement_id": agreement.agreement_id,
            "status": agreement.status,
            "act_policy": agreement.act_policy,
            "next": "Open the advice stage with transition_agreement(status='advice') — deliberate openings stay manual.",
        }


@mcp.tool()
async def record_agreement_ceremony(agreement_id: str, stage: str, note: str, ctx: Context) -> dict:
    """Record an advice round (stage='advice') or test-case evidence
    (stage='test') against an agreement. Status auto-advances when the
    declared gate conditions are met."""
    caller = await _caller(ctx)
    stage = stage.strip().lower()
    if stage not in {"advice", "test"}:
        raise ValueError("stage must be 'advice' or 'test'")
    if len(note.strip()) < 3:
        raise ValueError("note must describe the round or evidence (min 3 chars)")
    async with _db()() as s:
        agreement = await _load_agreement(s, agreement_id)
        if agreement is None:
            raise ValueError("Agreement not found")
        member = await _member(s, caller.user.id, agreement.ecosystem_id)
        s.add(AgreementCeremony(
            id=uuid.uuid4(),
            agreement_id=agreement.id,
            stage=stage,
            completed_by_member_id=member.id,
            outcome={"advice": "round", "test": "evidence"}[stage],
            evidence=note.strip(),
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        ))
        advance = await maybe_auto_advance_agreement(s, agreement, actor_member_id=member.id)
        await s.commit()
        return {
            "agreement_id": agreement.agreement_id,
            "status": agreement.status,
            "auto_transitions": advance["transitions"],
            "gates": advance["gates"],
            "decision_record_id": advance["decision_record_id"],
        }


@mcp.tool()
async def attest_agreement_consent(agreement_id: str, attestation: str, ctx: Context) -> dict:
    """Attest the token owner's consent to an agreement at its current
    version. Consent completeness covers ALL participating members; status
    auto-advances when the consent gate is met."""
    caller = await _caller(ctx)
    if len(attestation.strip()) < 8:
        raise ValueError("attestation must be a meaningful statement (min 8 chars)")
    async with _db()() as s:
        agreement = await _load_agreement(s, agreement_id)
        if agreement is None:
            raise ValueError("Agreement not found")
        member = await _member(s, caller.user.id, agreement.ecosystem_id)
        consent = await s.scalar(
            select(AgreementMemberConsent).where(
                AgreementMemberConsent.agreement_id == agreement.id,
                AgreementMemberConsent.member_id == member.id,
                AgreementMemberConsent.agreement_version == agreement.version,
            ).with_for_update()
        )
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if consent is None:
            s.add(AgreementMemberConsent(
                id=uuid.uuid4(),
                agreement_id=agreement.id,
                member_id=member.id,
                agreement_version=agreement.version,
                attestation=attestation.strip(),
                attested_at=now,
            ))
            await s.flush()
        else:
            consent.attestation = attestation.strip()
            consent.attested_at = now
            if consent.withdrawn_at is not None:
                consent.revision += 1
            consent.withdrawn_at = None
            consent.withdrawal_reason = None
        advance = await maybe_auto_advance_agreement(s, agreement, actor_member_id=member.id)
        await s.commit()
        return {
            "agreement_id": agreement.agreement_id,
            "status": agreement.status,
            "auto_transitions": advance["transitions"],
            "gates": advance["gates"],
            "decision_record_id": advance["decision_record_id"],
        }


@mcp.tool()
async def transition_agreement(agreement_id: str, status: str, evidence: str, ctx: Context) -> dict:
    """Conduct the ceremony moving an agreement through the ACT sequence.

    Mirrors the UI rules: only an active ecosystem steward (admin/owner) may
    conduct; forward ceremonies need documented evidence (min 8 chars);
    forward moves past draft require the declared gate for that stage to be
    met — the error reports exactly what is missing. Activation mints the
    commitment decision artifact.
    """
    caller = await _caller(ctx)
    target = status.strip().lower()
    evidence = (evidence or "").strip()
    async with _db()() as s:
        agreement = await _load_agreement(s, agreement_id)
        if agreement is None:
            raise ValueError("Agreement not found")
        actor = await s.scalar(
            select(Member).where(
                Member.user_id == caller.user.id,
                Member.ecosystem_id == agreement.ecosystem_id,
            ).with_for_update()
        )
        if actor is None or actor.current_status != "active" or actor.role not in {"admin", "owner"}:
            raise ValueError("Only an active ecosystem steward (admin or owner) may conduct this ceremony")

        allowed = _AGREEMENT_TRANSITIONS.get(agreement.status, set())
        if target not in allowed:
            raise ValueError(f"Invalid transition: {agreement.status} -> {target}")
        if target in {"advice", "consent", "test", "active"} and len(evidence) < 8:
            raise ValueError(f"Documented evidence is required for the {target} ceremony (min 8 chars)")

        gate_key = {"consent": "advice", "test": "consent", "active": "test"}.get(target)
        if gate_key:
            gates = await agreement_gate_status(s, agreement)
            if not gates[gate_key]["met"]:
                raise _gates_error(
                    f"The {gate_key} gate is not satisfied — the agreement's declared ACT conditions must be met first",
                    gates,
                )

        s.add(_snapshot_agreement(
            agreement,
            change_reason=f"Status transition: {agreement.status} -> {target}",
            changed_by=actor.display_name,
        ))
        agreement.status = target
        if target == "active" and agreement.ratification_date is None:
            agreement.ratification_date = date.today()
        s.add(AgreementCeremony(
            id=uuid.uuid4(),
            agreement_id=agreement.id,
            stage=target,
            completed_by_member_id=actor.id,
            outcome={"advice": "opened", "consent": "opened", "test": "started", "active": "passed"}.get(target, "completed"),
            evidence=evidence or None,
            completed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        ))
        agreement.version_fingerprint = generate_fingerprint(
            agreement.title, agreement.text, agreement.version, agreement.status
        )
        if target == "active":
            await record_agreement_commitment(s, agreement)
        advance = await maybe_auto_advance_agreement(s, agreement, actor_member_id=actor.id)
        if advance["transitions"]:
            s.add(_snapshot_agreement(
                agreement,
                change_reason="Auto-advanced by ACT gate engine: " + ", ".join(advance["transitions"]),
                changed_by="ACT gate engine",
            ))
            agreement.version_fingerprint = generate_fingerprint(
                agreement.title, agreement.text, agreement.version, agreement.status
            )
        await s.commit()
        return {
            "agreement_id": agreement.agreement_id,
            "status": agreement.status,
            "auto_transitions": advance["transitions"],
            "decision_record_id": advance["decision_record_id"],
        }


# ---------------------------------------------------------------------------
# Proposal write tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_proposal(
    ecosystem_id: str,
    title: str,
    ctx: Context,
    type: str = "policy",
    proposed_change: str | None = None,
    rationale: str | None = None,
    affected_domain: str | None = None,
    governing_agreement_id: str | None = None,
    min_advice_rounds: int | None = None,
    test_cases: list[str] | None = None,
) -> dict:
    """Create a DRAFT proposal. By default it inherits ACT gates from its
    governing agreement; pass min_advice_rounds / test_cases to declare an
    override at the proposal level."""
    caller = await _caller(ctx)
    eco_uuid = uuid.UUID(ecosystem_id)
    async with _db()() as s:
        member = await _member(s, caller.user.id, eco_uuid)
        governing_uuid = None
        if governing_agreement_id:
            governing = await _resolve(s, Agreement, governing_agreement_id, "agreement_id")
            if governing is None or governing.ecosystem_id != eco_uuid:
                raise ValueError("Governing agreement must exist in the proposal's ecosystem")
            governing_uuid = governing.id
        override = min_advice_rounds is not None or test_cases
        policy = normalize_act_policy({
            "min_advice_rounds": min_advice_rounds if min_advice_rounds is not None else 1,
            "consent_required": True,
            "test_cases": _parse_cases(test_cases),
        }) if override else None
        proposal = Proposal(
            id=uuid.uuid4(),
            ecosystem_id=eco_uuid,
            proposal_id=f"PROP-{uuid.uuid4().hex[:8].upper()}",
            type=type.strip(),
            decision_type="consent",
            title=title.strip(),
            version="1.0",
            status="draft",
            proposer=member.display_name,
            affected_domain=affected_domain,
            urgency="standard",
            proposed_change=proposed_change,
            rationale=rationale,
            created_date=date.today(),
            act_policy=policy,
            governing_agreement_id=governing_uuid,
        )
        s.add(proposal)
        await s.commit()
        gates = await proposal_gate_status(s, proposal)
        return {
            "id": str(proposal.id),
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "policy_source": gates["policy_source"],
            "act_policy": gates["policy"],
            "next": "Open the process with transition_proposal(status='advice') — openings stay manual.",
        }


@mcp.tool()
async def record_proposal_advice(proposal_id: str, advice_text: str, ctx: Context, new_round: bool = False) -> dict:
    """Add advice to the current round (or open a new round with
    new_round=true). Completing the declared number of rounds auto-advances
    the proposal to consent."""
    caller = await _caller(ctx)
    if len(advice_text.strip()) < 3:
        raise ValueError("advice_text is too short")
    async with _db()() as s:
        proposal = await _resolve(s, Proposal, proposal_id, "proposal_id")
        if proposal is None:
            raise ValueError("Proposal not found")
        member = await _member(s, caller.user.id, proposal.ecosystem_id)
        if proposal.status != "advice":
            raise ValueError(f"Advice can only be recorded while the proposal is in advice (currently '{proposal.status}')")
        log = await s.scalar(
            select(AdviceLog)
            .where(AdviceLog.proposal_id == proposal.id)
            .order_by(AdviceLog.created_at.desc())
            .limit(1)
        )
        if log is None or new_round:
            log = AdviceLog(id=uuid.uuid4(), proposal_id=proposal.id, advice_window_start=date.today())
            s.add(log)
            await s.flush()
        s.add(AdviceEntry(
            id=uuid.uuid4(),
            advice_log_id=log.id,
            advisor=member.display_name,
            advice_text=advice_text.strip(),
        ))
        advance = await maybe_auto_advance_proposal(s, proposal)
        await s.commit()
        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "auto_transitions": advance["transitions"],
            "gates": advance["gates"],
        }


@mcp.tool()
async def submit_proposal_consent(proposal_id: str, position: str, ctx: Context, objection_text: str | None = None) -> dict:
    """Record the owner's consent position (consent / stand_aside / object).
    The consent gate needs quorum and zero open objections; status
    auto-advances when met."""
    caller = await _caller(ctx)
    position = position.strip().lower()
    if position not in {"consent", "stand_aside", "object"}:
        raise ValueError("position must be consent, stand_aside, or object")
    if position == "object" and not (objection_text and objection_text.strip()):
        raise ValueError("objection_text is required when objecting")
    async with _db()() as s:
        proposal = await _resolve(s, Proposal, proposal_id, "proposal_id")
        if proposal is None:
            raise ValueError("Proposal not found")
        member = await _member(s, caller.user.id, proposal.ecosystem_id)
        if proposal.status != "consent":
            raise ValueError(f"Consent can only be recorded while the proposal is in consent (currently '{proposal.status}')")
        record = await s.scalar(
            select(ConsentRecord)
            .where(ConsentRecord.proposal_id == proposal.id)
            .order_by(ConsentRecord.created_at.desc())
            .limit(1)
        )
        if record is None:
            record = ConsentRecord(
                id=uuid.uuid4(),
                proposal_id=proposal.id,
                consent_mode=proposal.decision_type or "consent",
                outcome="pending",
            )
            s.add(record)
            await s.flush()
        s.add(ConsentParticipant(
            id=uuid.uuid4(),
            consent_record_id=record.id,
            name=member.display_name,
            position=position,
            reason=objection_text.strip() if objection_text else None,
        ))
        advance = await maybe_auto_advance_proposal(s, proposal)
        await s.commit()
        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "auto_transitions": advance["transitions"],
            "gates": advance["gates"],
        }


@mcp.tool()
async def submit_test_report(
    proposal_id: str,
    status: str,
    ctx: Context,
    summary: str | None = None,
    met_criteria: list[str] | None = None,
) -> dict:
    """Submit a test report (status: passed/failed/blocked) with the declared
    test-case names that are met. All declared cases met (or one passed
    report when none are declared) auto-advances to ratification."""
    caller = await _caller(ctx)
    status = status.strip().lower()
    if status not in {"passed", "failed", "blocked"}:
        raise ValueError("status must be passed, failed, or blocked")
    async with _db()() as s:
        proposal = await _resolve(s, Proposal, proposal_id, "proposal_id")
        if proposal is None:
            raise ValueError("Proposal not found")
        member = await _member(s, caller.user.id, proposal.ecosystem_id)
        if proposal.status != "test":
            raise ValueError(f"Test reports can only be filed while the proposal is in test (currently '{proposal.status}')")
        report = TestReport(
            id=uuid.uuid4(),
            proposal_id=proposal.id,
            test_start_date=date.today(),
            outcome=status,
            observations=summary.strip() if summary else None,
        )
        s.add(report)
        await s.flush()
        for name in _parse_cases(met_criteria):
            s.add(TestSuccessCriterion(
                id=uuid.uuid4(),
                test_report_id=report.id,
                criterion=name,
                met=True,
            ))
        advance = await maybe_auto_advance_proposal(s, proposal)
        await s.commit()
        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "auto_transitions": advance["transitions"],
            "decision_record_id": advance["decision_record_id"],
            "gates": advance["gates"],
        }


@mcp.tool()
async def transition_proposal(proposal_id: str, status: str, ctx: Context) -> dict:
    """Move a proposal through the ACT sequence. Forward moves require the
    declared (or inherited) gates to be met; withdrawals stay free."""
    caller = await _caller(ctx)
    target = status.strip().lower()
    async with _db()() as s:
        proposal = await _resolve(s, Proposal, proposal_id, "proposal_id")
        if proposal is None:
            raise ValueError("Proposal not found")
        await _member(s, caller.user.id, proposal.ecosystem_id)
        chain = ["draft", "advice", "consent", "test", "ratified"]
        if target not in chain and target != "withdrawn":
            raise ValueError(f"status must be one of {chain + ['withdrawn']}")
        current = proposal.status
        if target == current:
            return {"proposal_id": proposal.proposal_id, "status": current, "auto_transitions": []}
        if target == "withdrawn":
            proposal.status = "withdrawn"
            await s.commit()
            return {"proposal_id": proposal.proposal_id, "status": "withdrawn", "auto_transitions": []}
        if current not in chain or chain.index(target) < chain.index(current):
            raise ValueError(f"Cannot move proposal from '{current}' to '{target}'")
        # Opening the process (draft -> advice) is a deliberate manual move.
        if current == "draft" and target == "advice":
            proposal.status = "advice"
            await s.commit()
            return {"proposal_id": proposal.proposal_id, "status": "advice", "auto_transitions": []}
        advance = await maybe_auto_advance_proposal(s, proposal)
        if proposal.status != target:
            await s.rollback()
            raise _gates_error(
                f"Gate conditions not met to move '{proposal.status}' toward '{target}'",
                advance["gates"],
            )
        await s.commit()
        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "auto_transitions": advance["transitions"],
            "decision_record_id": advance["decision_record_id"],
        }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="NEOS governance MCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
