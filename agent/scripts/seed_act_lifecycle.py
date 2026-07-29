"""Seed the full ACT lifecycle with declared gates, artifacts, and commitments.

Usage:
    python -m agent.scripts.seed_act_lifecycle
    python -m agent.scripts.seed_act_lifecycle --purge

Reflects how the system is actually used:

  Proposals (6 per ecosystem = 24) — every ACT stage, each with an act_policy
  declared at the proposal level, in gate-consistent states:
    draft     — gates declared, process not opened
    advice    — 1 of 2 declared advice rounds complete (gate pending)
    consent   — advice gate met; consent quorum short with one open objection
    test      — consent achieved; 2 of 3 declared test cases evidenced
    ratified  — all gates met; decision artifact minted (artifact_type
                "proposal", participants = the members' recorded commitments)
    withdrawn — withdrawn during advice with a documented reason

  Agreements (2 new per ecosystem = 8) — mid-flight ACT ceremonies with gates
  declared at the agreement level:
    consent stage — advice rounds complete, one consent still outstanding
    test stage    — consent complete, 1 of 2 declared test cases evidenced

  Commitments (1 per ecosystem = 4) — the existing ACTIVE decision-making
  protocol agreements get an explicit act_policy, full member consent rows,
  and a minted commitment decision artifact (artifact_type "commitment").

All records use deterministic UUIDs (neos.seed.*) so the seed is idempotent
and --purge removes exactly what it created.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import (
    Base,
    Agreement,
    AgreementCeremony,
    AgreementMemberConsent,
    Member,
    Proposal,
    AdviceLog,
    AdviceEntry,
    AdviceNonRespondent,
    ConsentRecord,
    ConsentParticipant,
    ConsentIntegrationRound,
    ConsentObjectionAddressed,
    TestReport,
    TestSuccessCriterion,
    DecisionRecord,
    DecisionParticipant,
    DecisionSemanticTag,
)
from neos_agent.services.agreement_consent import _PARTICIPATING_MEMBER_STATUSES


# ---------------------------------------------------------------------------
# Deterministic UUID helper -- must match seed_omnione
# ---------------------------------------------------------------------------
def _uid(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"neos.seed.{name}")


# ---------------------------------------------------------------------------
# Date / time helpers
# ---------------------------------------------------------------------------
TODAY = date.today()
NOW_NAIVE = datetime.utcnow()


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def days_from_now(n: int) -> date:
    return TODAY + timedelta(days=n)


def hours_ago(n: int) -> datetime:
    return NOW_NAIVE - timedelta(hours=n)


# ---------------------------------------------------------------------------
# Ecosystem / member / agreement IDs (must match seed_omnione)
# ---------------------------------------------------------------------------
eco_omni_id = _uid("eco.omnione")
eco_eb_id = _uid("eco.escherbridge")
eco_ps_id = _uid("eco.plansystems")
eco_oa_id = _uid("eco.oasis")

# (member display name, member role, member uuid) per ecosystem
MEMBERS = {
    "omni": [
        ("Josh Pasmore", "co_creator", _uid("mbr.omni.josh")),
        ("Nathan R", "builder", _uid("mbr.omni.nathan")),
        ("Ahmed (Jade Oni)", "townhall", _uid("mbr.omni.ahmed")),
    ],
    "eb": [
        ("Ahmed (Jade Oni)", "co_creator", _uid("mbr.eb.ahmed")),
        ("Kenny", "builder", _uid("mbr.eb.kenny")),
        ("Jak", "townhall", _uid("mbr.eb.jak")),
    ],
    "ps": [
        ("Rachel", "co_creator", _uid("mbr.ps.rachel")),
        ("Brandon", "builder", _uid("mbr.ps.brandon")),
        ("Drew", "townhall", _uid("mbr.ps.drew")),
    ],
    "oa": [
        ("Max Gershfield", "co_creator", _uid("mbr.oa.max")),
        ("David Ellams", "builder", _uid("mbr.oa.david")),
    ],
}

# Existing ACTIVE decision-making protocol agreements (seed_omnione) that
# receive an act_policy, full member consent, and a commitment artifact.
DECISION_AGREEMENTS = {
    "omni": _uid("agr.omni.decision"),
    "eb": _uid("agr.eb.decision"),
    "ps": _uid("agr.ps.decision"),
    "oa": _uid("agr.oa.decision"),
}
DECISION_AGREEMENT_BUSINESS_IDS = {
    "omni": "AGR-OMNI-002",
    "eb": "AGR-EB-002",
    "ps": "AGR-PS-002",
    "oa": "AGR-OA-002",
}

# ---------------------------------------------------------------------------
# Content spec — 6 proposal stages + 2 mid-flight agreements per ecosystem
# ---------------------------------------------------------------------------
ECOSYSTEMS = [
    (
        eco_omni_id, "omni", "OmniOne", "Core Operations",
        {
            "draft": ("Shared Tool Library Charter", "Establish a collectively managed tool library with lending rules and maintenance duties."),
            "advice": ("Water Management Cooperative Framework", "Establish shared water resource allocation across community plots."),
            "consent": ("Community Composting Protocol", "Standardize composting procedures and output distribution."),
            "test": ("Guest Visitor Policy", "Define guest access rights, duration limits, and sponsor responsibilities."),
            "ratified": ("Weekly Standup Tracker Agreement", "Adopt a shared standup tracker as the canonical record of weekly commitments."),
            "withdrawn": ("Food Forest Expansion Plan", "Proposal to convert shared meadow into food forest zones."),
        },
        {
            "consent": ("OmniOne Facilitation Rota", "Rotating facilitation duties for weekly governance calls."),
            "test": ("OmniOne Decision Log Practice", "Every ratified decision is logged with holding, rationale, and participants within 48 hours."),
        },
    ),
    (
        eco_eb_id, "eb", "Escherbridge", "Core Operations",
        {
            "draft": ("Studio Access Tier Proposal", "Tiered studio access based on contribution and residency status."),
            "advice": ("Exhibition Scheduling Governance", "Establish fair rotation and booking system for gallery exhibitions."),
            "consent": ("Artist Residency Program Structure", "Define selection criteria, duration, and resource allocation for residencies."),
            "test": ("Equipment Maintenance Protocol", "Shared responsibility framework for studio equipment upkeep."),
            "ratified": ("Workshop Revenue Sharing Rule", "Workshop revenue split: 60% facilitator, 40% studio commons fund."),
            "withdrawn": ("Workshop Fee Restructuring", "Proposal to restructure workshop participation fees."),
        },
        {
            "consent": ("Escherbridge Exhibition Jury Charter", "Standing jury of three for exhibition selection with rotating membership."),
            "test": ("Escherbridge Critique Circle Practice", "Monthly critique circle is mandatory for resident artists; notes feed the decision log."),
        },
    ),
    (
        eco_ps_id, "ps", "Plan Systems", "Systems Design Circle",
        {
            "draft": ("Client Engagement Boundary Policy", "Define which client requests require circle consent before commitment."),
            "advice": ("Open Source Contribution Policy", "Define IP boundaries and contribution guidelines for open source work."),
            "consent": ("Professional Training Program", "Structured training and mentorship for new systems designers."),
            "test": ("Revenue Sharing Framework", "Equitable revenue distribution model for collaborative projects."),
            "ratified": ("Wardley Mapping Standard", "Adopt Wardley Mapping as the standard strategic planning framework for client work."),
            "withdrawn": ("Flexible Office Hours Experiment", "Proposal to allow fully flexible working schedules."),
        },
        {
            "consent": ("Plan Systems Pairing Charter", "All client deliverables are paired: one lead, one reviewer."),
            "test": ("Plan Systems Retrospective Practice", "Fortnightly retrospectives produce at least one process improvement proposal."),
        },
    ),
    (
        eco_oa_id, "oa", "Oasis", "Protocol Development Circle",
        {
            "draft": ("Cross-Chain Bridge Security Policy", "Mandatory audit and staged rollout for any new chain bridge integration."),
            "advice": ("Token Distribution Governance", "Define transparent token allocation and vesting schedules."),
            "consent": ("Node Operator Requirements Update", "Updated minimum hardware and uptime requirements for node operators."),
            "test": ("Public API Access Policy", "Tiered API access framework with rate limits and contributor benefits."),
            "ratified": ("72-Hour Async Voting Windows", "Adopt 72-hour async voting windows for all governance proposals."),
            "withdrawn": ("Governance Reward Token", "Proposal to mint governance participation reward tokens."),
        },
        {
            "consent": ("Oasis Protocol Review Board", "Three-member board reviews protocol changes before consent rounds open."),
            "test": ("Oasis On-Chain Receipt Practice", "Every ratified governance decision is anchored as an on-chain receipt within one epoch."),
        },
    ),
]

TEST_CASES = {
    # Declared test cases for test-stage and ratified proposals (3 and 2).
    "test": [
        "Participation rate above 60% of eligible members",
        "No unresolved objections during test period",
        "Measurable improvement in process efficiency",
    ],
    "ratified": [
        "Pilot completed in one domain without unresolved objections",
        "Documented evidence reviewed by the governance circle",
    ],
}

AGREEMENT_TEST_CASES = [
    "Pilot completed in one domain",
    "Review notes logged to the decision record",
]

# ---------------------------------------------------------------------------
# Deterministic ID registries (for idempotency + purge)
# ---------------------------------------------------------------------------
ALL_PROPOSAL_IDS: list[uuid.UUID] = []
ALL_DECISION_IDS: list[uuid.UUID] = []
ALL_AGREEMENT_IDS: list[uuid.UUID] = []

for _eco_id, _prefix, *_ in ECOSYSTEMS:
    for _stage in ("draft", "advice", "consent", "test", "ratified", "withdrawn"):
        ALL_PROPOSAL_IDS.append(_uid(f"prop.{_prefix}.{_stage}"))
    ALL_DECISION_IDS.append(_uid(f"decact.{_prefix}.ratified"))
    ALL_DECISION_IDS.append(_uid(f"deccommit.{_prefix}"))
    ALL_AGREEMENT_IDS.append(_uid(f"agract.{_prefix}.consent"))
    ALL_AGREEMENT_IDS.append(_uid(f"agract.{_prefix}.test"))


# ---------------------------------------------------------------------------
# Purge — only remove data created by this script
# ---------------------------------------------------------------------------
async def purge(database_url: str) -> None:
    """Delete only records created by this script (and revert its updates)."""
    engine = create_async_engine(database_url)

    prop_ids = ", ".join(f"'{pid}'" for pid in ALL_PROPOSAL_IDS)
    dec_ids = ", ".join(f"'{did}'" for did in ALL_DECISION_IDS)
    agr_ids = ", ".join(f"'{aid}'" for aid in ALL_AGREEMENT_IDS)
    decision_agr_ids = ", ".join(f"'{aid}'" for aid in DECISION_AGREEMENTS.values())

    async with engine.begin() as conn:
        # Decision artifacts minted by this seed (participants/tags first)
        await conn.execute(text(
            f'DELETE FROM "decision_participants" WHERE decision_record_id IN ({dec_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "decision_semantic_tags" WHERE decision_record_id IN ({dec_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "decision_dissent_records" WHERE decision_record_id IN ({dec_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "decision_records" WHERE id IN ({dec_ids})'
        ))

        # Member consents added to pre-existing (decision protocol) agreements
        await conn.execute(text(
            f'DELETE FROM "agreement_member_consents" WHERE agreement_id IN ({decision_agr_ids})'
        ))
        # Ceremonies added to pre-existing agreements (seed_omnione writes none)
        await conn.execute(text(
            f'DELETE FROM "agreement_ceremonies" WHERE agreement_id IN ({decision_agr_ids})'
        ))
        # Revert act_policy updates on pre-existing agreements
        await conn.execute(text(
            f'UPDATE "agreements" SET act_policy = NULL WHERE id IN ({decision_agr_ids})'
        ))

        # Agreements created by this seed (ceremonies + consents first)
        await conn.execute(text(
            f'DELETE FROM "agreement_ceremonies" WHERE agreement_id IN ({agr_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "agreement_member_consents" WHERE agreement_id IN ({agr_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "agreement_versions" WHERE agreement_id IN ({agr_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "agreements" WHERE id IN ({agr_ids})'
        ))

        # Proposals and their ACT sub-records
        await conn.execute(text(
            f'DELETE FROM "test_success_criteria" WHERE test_report_id IN '
            f'(SELECT id FROM "test_reports" WHERE proposal_id IN ({prop_ids}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "test_reports" WHERE proposal_id IN ({prop_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "consent_objections_addressed" WHERE integration_round_id IN '
            f'(SELECT id FROM "consent_integration_rounds" WHERE consent_record_id IN '
            f'(SELECT id FROM "consent_records" WHERE proposal_id IN ({prop_ids})))'
        ))
        await conn.execute(text(
            f'DELETE FROM "consent_integration_rounds" WHERE consent_record_id IN '
            f'(SELECT id FROM "consent_records" WHERE proposal_id IN ({prop_ids}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "consent_participants" WHERE consent_record_id IN '
            f'(SELECT id FROM "consent_records" WHERE proposal_id IN ({prop_ids}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "consent_records" WHERE proposal_id IN ({prop_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "advice_non_respondents" WHERE advice_log_id IN '
            f'(SELECT id FROM "advice_logs" WHERE proposal_id IN ({prop_ids}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "advice_entries" WHERE advice_log_id IN '
            f'(SELECT id FROM "advice_logs" WHERE proposal_id IN ({prop_ids}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "advice_logs" WHERE proposal_id IN ({prop_ids})'
        ))
        await conn.execute(text(
            f'DELETE FROM "proposals" WHERE id IN ({prop_ids})'
        ))

    print(
        f"Purged {len(ALL_PROPOSAL_IDS)} proposals, {len(ALL_AGREEMENT_IDS)} agreements, "
        f"{len(ALL_DECISION_IDS)} decision artifacts and their consents/ceremonies."
    )
    await engine.dispose()


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------
def _policy(min_rounds: int, quorum: int | None, test_cases: list[str]) -> dict:
    return {
        "min_advice_rounds": min_rounds,
        "consent_required": True,
        "consent_quorum": quorum,
        "test_cases": test_cases,
    }


def _add_advice_round(session, counts, prop_id, prefix, stage, round_idx, entries, window_start, window_end, summary):
    log_id = _uid(f"advlog.{prefix}.{stage}.{round_idx}")
    session.add(AdviceLog(
        id=log_id,
        proposal_id=prop_id,
        advice_window_start=window_start,
        advice_window_end=window_end,
        urgency="standard",
        summary=summary,
    ))
    counts["advice_logs"] += 1
    for i, (advisor, role, text_, response) in enumerate(entries):
        session.add(AdviceEntry(
            id=_uid(f"adventry.{prefix}.{stage}.{round_idx}.{i}"),
            advice_log_id=log_id,
            advisor=advisor,
            role=role,
            date=window_start + timedelta(days=2 + i),
            advice_text=text_,
            proposer_response=response,
            integration_status="integrated" if response else "pending",
        ))
        counts["advice_entries"] += 1
    return log_id


def _add_consent_record(session, counts, prop_id, prefix, stage, positions, facilitator, when, outcome):
    cr_id = _uid(f"consent.{prefix}.{stage}")
    session.add(ConsentRecord(
        id=cr_id,
        proposal_id=prop_id,
        consent_mode="standard",
        facilitator=facilitator,
        date=when,
        quorum_required="all affected members",
        quorum_met=outcome == "consent_achieved",
        outcome=outcome,
        final_proposal_version="1.1",
    ))
    counts["consent_records"] += 1
    for j, (name, role, position, reason) in enumerate(positions):
        session.add(ConsentParticipant(
            id=_uid(f"cp.{prefix}.{stage}.{j}"),
            consent_record_id=cr_id,
            name=name,
            role=role,
            position=position,
            reason=reason,
            round=1,
        ))
        counts["consent_participants"] += 1
    return cr_id


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
async def seed(database_url: str) -> None:  # noqa: C901 — intentionally long
    """Create gate-consistent ACT lifecycle data across all four ecosystems."""
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        sentinel_id = _uid("prop.omni.draft")
        result = await session.execute(select(Proposal).where(Proposal.id == sentinel_id))
        if result.scalar_one_or_none() is not None:
            print("ACT lifecycle data already seeded. Skipping. Use --purge to reseed.")
            await engine.dispose()
            return

        counts = {"proposals": 0, "advice_logs": 0, "advice_entries": 0,
                  "consent_records": 0, "consent_participants": 0,
                  "integration_rounds": 0, "objections_addressed": 0,
                  "test_reports": 0, "success_criteria": 0,
                  "agreements": 0, "ceremonies": 0, "member_consents": 0,
                  "decisions": 0, "decision_participants": 0}

        for (eco_id, prefix, eco_name, domain, titles, agr_titles) in ECOSYSTEMS:
            members = MEMBERS[prefix]
            n_members = len(members)
            prop_num = 2  # 001 is from seed_omnione

            # Actual participating members of this ecosystem — agreement
            # consent completeness is evaluated against ALL of them.
            eco_members = list((await session.execute(
                select(Member)
                .where(
                    Member.ecosystem_id == eco_id,
                    Member.current_status.in_(_PARTICIPATING_MEMBER_STATUSES),
                )
                .order_by(Member.created_at)
            )).scalars().all())

            # ===========================================================
            # 1. DRAFT — gates declared, process not opened
            # ===========================================================
            title, change = titles["draft"]
            session.add(Proposal(
                id=_uid(f"prop.{prefix}.draft"),
                ecosystem_id=eco_id,
                proposal_id=f"PROP-{prefix.upper()}-{prop_num:03d}",
                type="policy", decision_type="consent",
                title=title, version="1.0", status="draft",
                proposer=members[0][0], affected_domain=domain, urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Draft under preparation by the {eco_name} governance circle; ACT gates declared up front.",
                created_date=days_ago(2),
                advice_deadline=days_from_now(12),
                act_policy=_policy(2, n_members, TEST_CASES["ratified"]),
            ))
            counts["proposals"] += 1
            prop_num += 1

            # ===========================================================
            # 2. ADVICE — 1 of 2 declared rounds complete (gate pending)
            # ===========================================================
            title, change = titles["advice"]
            prop_id = _uid(f"prop.{prefix}.advice")
            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=f"PROP-{prefix.upper()}-{prop_num:03d}",
                type="policy", decision_type="consent",
                title=title, version="1.0", status="advice",
                proposer=members[0][0], affected_domain=domain, urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Needed to improve governance clarity in {eco_name}.",
                created_date=days_ago(10),
                advice_deadline=days_from_now(7),
                act_policy=_policy(2, n_members, TEST_CASES["ratified"]),
            ))
            counts["proposals"] += 1
            prop_num += 1

            log_id = _add_advice_round(
                session, counts, prop_id, prefix, "advice", 1,
                [(m[0], m[1], f"Generally supportive. Suggests clearer implementation timeline. -- {m[0]}",
                  "Incorporated timeline suggestion.") for m in members[:2]],
                days_ago(9), days_from_now(7),
                "Round 1 of 2 complete. Awaiting a second advice round before consent opens.",
            )
            session.add(AdviceNonRespondent(
                id=_uid(f"advnr.{prefix}.advice"),
                advice_log_id=log_id,
                name=members[-1][0],
                notified_date=days_ago(8),
                follow_up_sent=True,
            ))
            prop_num += 1

            # ===========================================================
            # 3. CONSENT — advice gate met, open objection (gate pending)
            # ===========================================================
            title, change = titles["consent"]
            prop_id = _uid(f"prop.{prefix}.consent")
            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=f"PROP-{prefix.upper()}-{prop_num:03d}",
                type="policy", decision_type="consent",
                title=title, version="1.1", status="consent",
                proposer=members[0][0], affected_domain=domain, urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Operational improvement identified during {eco_name} retrospective.",
                created_date=days_ago(30),
                advice_deadline=days_ago(16),
                consent_deadline=days_from_now(5),
                act_policy=_policy(2, n_members, TEST_CASES["test"]),
            ))
            counts["proposals"] += 1
            prop_num += 1

            for rnd in (1, 2):
                _add_advice_round(
                    session, counts, prop_id, prefix, "consent", rnd,
                    [(m[0], m[1], f"Supportive with refinements (round {rnd}). -- {m[0]}",
                      "Refinements integrated.") for m in members[:2]],
                    days_ago(30 - (rnd - 1) * 7), days_ago(23 - (rnd - 1) * 7),
                    f"Advice round {rnd} of 2 complete.",
                )

            positions = [
                (members[0][0], members[0][1], "consent", "Fully aligned with the proposal."),
            ]
            if n_members > 2:
                positions.append(
                    (members[1][0], members[1][1], "consent", "No principled objection.")
                )
                positions.append(
                    (members[2][0], members[2][1], "object",
                     "Concerned about implementation timeline being too aggressive.")
                )
            # Two-member ecosystems: quorum is 2 and only 1 position is in —
            # the gate stays pending on quorum. Larger ones: pending on the
            # open objection below.
            cr_id = _add_consent_record(
                session, counts, prop_id, prefix, "consent", positions,
                members[0][0], days_ago(4), "pending_integration",
            )
            if n_members > 2:
                ir_id = _uid(f"ir.{prefix}.consent")
                session.add(ConsentIntegrationRound(
                    id=ir_id, consent_record_id=cr_id, round_number=1,
                    modifications_made="Extended implementation timeline from 2 weeks to 4 weeks.",
                    outcome="in_progress",
                ))
                counts["integration_rounds"] += 1
                session.add(ConsentObjectionAddressed(
                    id=_uid(f"oa.{prefix}.consent"),
                    integration_round_id=ir_id,
                    objector=positions[-1][0],
                    objection=positions[-1][3],
                    resolution="Timeline extended to 4 weeks with phased rollout.",
                ))
                counts["objections_addressed"] += 1

            # ===========================================================
            # 4. TEST — consent achieved, 2 of 3 declared cases evidenced
            # ===========================================================
            title, change = titles["test"]
            prop_id = _uid(f"prop.{prefix}.test")
            declared = TEST_CASES["test"]
            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=f"PROP-{prefix.upper()}-{prop_num:03d}",
                type="policy", decision_type="consent",
                title=title, version="1.1", status="test",
                proposer=members[1][0], affected_domain=domain, urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Long-standing need identified by {eco_name} governance circle.",
                created_date=days_ago(45),
                advice_deadline=days_ago(38),
                consent_deadline=days_ago(28),
                test_duration="30 days",
                act_policy=_policy(2, n_members, declared),
            ))
            counts["proposals"] += 1
            prop_num += 1

            for rnd in (1, 2):
                _add_advice_round(
                    session, counts, prop_id, prefix, "test", rnd,
                    [(m[0], m[1], f"Strong support; success metrics made explicit. -- {m[0]}",
                      "Added explicit success criteria.") for m in members[:2]],
                    days_ago(45 - (rnd - 1) * 7), days_ago(38 - (rnd - 1) * 7),
                    f"Advice round {rnd} of 2 complete.",
                )
            _add_consent_record(
                session, counts, prop_id, prefix, "test",
                [(m[0], m[1], "consent", "No principled objection. Safe enough to try.") for m in members],
                members[0][0], days_ago(30), "consent_achieved",
            )

            tr_id = _uid(f"tr.{prefix}.test")
            session.add(TestReport(
                id=tr_id,
                proposal_id=prop_id,
                test_start_date=days_ago(25),
                test_end_date=days_from_now(5),
                midpoint_checkin_date=days_ago(10),
                revert_procedure=f"Revert to previous {eco_name} protocol version if criteria not met.",
                observations="Initial implementation proceeding smoothly. Minor adjustments made at midpoint.",
                midpoint_findings="Two of three declared test cases on track. Third pending final data.",
                outcome=None,
                next_action="Complete final assessment at test end date.",
                success_criteria_summary="3 declared cases: 2 met, 1 pending.",
            ))
            counts["test_reports"] += 1
            criteria_outcomes = [
                (declared[0], True, "Current participation at 72%."),
                (declared[1], True, "Zero objections raised during the test window."),
                (declared[2], False, None),  # still pending — gate stays open
            ]
            for k, (criterion, met, evidence) in enumerate(criteria_outcomes):
                session.add(TestSuccessCriterion(
                    id=_uid(f"tsc.{prefix}.test.{k}"),
                    test_report_id=tr_id,
                    criterion=criterion,
                    met=met,
                    evidence=evidence,
                ))
                counts["success_criteria"] += 1

            # ===========================================================
            # 5. RATIFIED — all gates met; decision artifact minted
            # ===========================================================
            title, change = titles["ratified"]
            prop_id = _uid(f"prop.{prefix}.ratified")
            prop_id_str = f"PROP-{prefix.upper()}-{prop_num:03d}"
            declared = TEST_CASES["ratified"]
            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=prop_id_str,
                type="policy", decision_type="consent",
                title=title, version="1.2", status="ratified",
                proposer=members[0][0], affected_domain=domain, urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Long-standing need identified by {eco_name} governance circle.",
                created_date=days_ago(90),
                advice_deadline=days_ago(83),
                consent_deadline=days_ago(73),
                test_duration="30 days",
                act_policy=_policy(2, n_members, declared),
            ))
            counts["proposals"] += 1
            prop_num += 1

            for rnd in (1, 2):
                _add_advice_round(
                    session, counts, prop_id, prefix, "ratified", rnd,
                    [(m[0], m[1], f"Broad support (round {rnd}). -- {m[0]}",
                      "Integrated.") for m in members[:2]],
                    days_ago(90 - (rnd - 1) * 7), days_ago(83 - (rnd - 1) * 7),
                    f"Advice round {rnd} of 2 complete.",
                )
            ratified_positions = [
                (m[0], m[1], "consent", "No principled objection. Safe enough to try.")
                for m in members
            ]
            _add_consent_record(
                session, counts, prop_id, prefix, "ratified", ratified_positions,
                members[0][0], days_ago(70), "consent_achieved",
            )
            tr_id = _uid(f"tr.{prefix}.ratified")
            session.add(TestReport(
                id=tr_id,
                proposal_id=prop_id,
                test_start_date=days_ago(60),
                test_end_date=days_ago(30),
                midpoint_checkin_date=days_ago(45),
                revert_procedure=f"Revert to previous {eco_name} protocol if criteria regress.",
                observations="Test period completed. All declared cases evidenced.",
                outcome="passed",
                next_action="Ratified; decision artifact recorded.",
                success_criteria_summary=f"{len(declared)} declared cases: all met.",
            ))
            counts["test_reports"] += 1
            for k, criterion in enumerate(declared):
                session.add(TestSuccessCriterion(
                    id=_uid(f"tsc.{prefix}.ratified.{k}"),
                    test_report_id=tr_id,
                    criterion=criterion,
                    met=True,
                    evidence="Verified at test close.",
                ))
                counts["success_criteria"] += 1

            # The decision artifact — the browsable commitment record.
            # Flush first: the artifact FKs to the proposal row, and this
            # metadata carries an unrelated unresolvable FK that breaks
            # SQLAlchemy's table-level insert ordering.
            await session.flush()
            dec_id = _uid(f"decact.{prefix}.ratified")
            session.add(DecisionRecord(
                id=dec_id,
                ecosystem_id=eco_id,
                record_id=f"DEC-{prop_id_str}",
                date=days_ago(30),
                holding=f"{title} — ratified after completing the ACT process. {change}",
                ratio_decidendi=(
                    "Both declared advice rounds completed, consent achieved with no "
                    "unresolved objections, and every declared test case showed met "
                    "evidence. Status advanced automatically as each gate was satisfied."
                ),
                deliberation_summary=(
                    f"ACT gates declared at the proposal level (min advice rounds: 2, "
                    f"consent required, test cases: {len(declared)}). 2 advice rounds, "
                    f"{len(ratified_positions)} consent positions, 1 passing test report."
                ),
                source_skill="act-process",
                artifact_type="proposal",
                artifact_reference=prop_id_str,
                source_proposal_id=prop_id,
                domain=domain,
                precedent_level="binding",
                status="active",
                recorder=members[0][0],
                recorder_role="proposer",
                review_date=days_from_now(180),
            ))
            counts["decisions"] += 1
            for j, (name, role, position, _reason) in enumerate(ratified_positions):
                session.add(DecisionParticipant(
                    id=_uid(f"decpart.{prefix}.ratified.{j}"),
                    decision_record_id=dec_id,
                    name=name,
                    role=role,
                    position=position,
                ))
                counts["decision_participants"] += 1
            session.add(DecisionSemanticTag(
                id=_uid(f"dectag.{prefix}.ratified"),
                decision_record_id=dec_id,
                topic={"category": domain},
                affected_parties={"circle": domain},
                ecosystem_scope="internal",
                urgency_at_time="standard",
            ))

            # ===========================================================
            # 6. WITHDRAWN — withdrawn during advice
            # ===========================================================
            title, change = titles["withdrawn"]
            prop_id = _uid(f"prop.{prefix}.withdrawn")
            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=f"PROP-{prefix.upper()}-{prop_num:03d}",
                type="policy", decision_type="consent",
                title=title, version="1.0", status="withdrawn",
                proposer=members[1][0], affected_domain=domain, urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale="Withdrawn by the proposer after advice surfaced a conflict with an existing agreement.",
                created_date=days_ago(60),
                advice_deadline=days_ago(53),
                act_policy=_policy(1, None, []),
            ))
            counts["proposals"] += 1
            _add_advice_round(
                session, counts, prop_id, prefix, "withdrawn", 1,
                [(members[0][0], members[0][1],
                  "This overlaps with an existing agreement — recommend withdrawing and merging there.",
                  "Agreed; withdrawing this proposal."),
                 (members[1][0], members[1][1], "Support the intent, not the mechanism.", None)],
                days_ago(60), days_ago(53),
                "Advice surfaced a conflict with an existing agreement; proposer withdrew.",
            )

            # ===========================================================
            # 7. CONSENT-STAGE AGREEMENT — advice rounds done, one
            #    consent outstanding (gate pending)
            # ===========================================================
            agr_title, agr_text = agr_titles["consent"]
            agr_id = _uid(f"agract.{prefix}.consent")
            session.add(Agreement(
                id=agr_id,
                ecosystem_id=eco_id,
                agreement_id=f"AGR-{prefix.upper()}-ACT-001",
                type="operational",
                title=agr_title,
                version="1.0",
                status="consent",
                proposer=members[0][0],
                domain=domain,
                hierarchy_level="domain",
                text=agr_text,
                created_date=days_ago(21),
                affected_parties={"affected": ["all_members"]},
                requires_explicit_consent=True,
                act_policy=_policy(2, None, [AGREEMENT_TEST_CASES[0]]),
            ))
            counts["agreements"] += 1
            ceremony_spec = [
                ("advice", "opened", f"Advice ceremony opened by {members[0][0]}.", 20),
                ("advice", "round", "Advice round 1: supportive; wording clarified.", 19),
                ("advice", "round", "Advice round 2: no further concerns; text stabilized.", 17),
                ("consent", "opened", "Minimum advice rounds met — consent ceremony opened.", 15),
            ]
            for c, (stage, outcome, evidence, days) in enumerate(ceremony_spec):
                session.add(AgreementCeremony(
                    id=_uid(f"cer.{prefix}.consent.{c}"),
                    agreement_id=agr_id,
                    stage=stage,
                    completed_by_member_id=members[0][2],
                    outcome=outcome,
                    evidence=evidence,
                    completed_at=hours_ago(days * 24),
                ))
                counts["ceremonies"] += 1
            # All but one participating member have attested — gate pending.
            for i, eco_member in enumerate(eco_members[:-1]):
                session.add(AgreementMemberConsent(
                    id=_uid(f"amc.{prefix}.consent.{eco_member.id.hex}"),
                    agreement_id=agr_id,
                    member_id=eco_member.id,
                    agreement_version="1.0",
                    attestation=(
                        f"I consent to \"{agr_title}\" v1.0. -- {eco_member.display_name}"
                    ),
                    attested_at=hours_ago(12 * 24 - i),
                ))
                counts["member_consents"] += 1

            # ===========================================================
            # 8. TEST-STAGE AGREEMENT — consent complete, 1 of 2 declared
            #    test cases evidenced (gate pending)
            # ===========================================================
            agr_title, agr_text = agr_titles["test"]
            agr_id = _uid(f"agract.{prefix}.test")
            session.add(Agreement(
                id=agr_id,
                ecosystem_id=eco_id,
                agreement_id=f"AGR-{prefix.upper()}-ACT-002",
                type="protocol",
                title=agr_title,
                version="1.0",
                status="test",
                proposer=members[0][0],
                domain=domain,
                hierarchy_level="domain",
                text=agr_text,
                created_date=days_ago(40),
                affected_parties={"affected": ["all_members"]},
                requires_explicit_consent=True,
                act_policy=_policy(1, None, AGREEMENT_TEST_CASES),
            ))
            counts["agreements"] += 1
            ceremony_spec = [
                ("advice", "opened", "Advice ceremony opened.", 39),
                ("advice", "round", "Advice round 1: practice refined and adopted for trial.", 37),
                ("consent", "opened", "Advice gate met — consent ceremony opened.", 35),
                ("test", "started", "Consent complete — 30-day test started.", 30),
                ("test", "evidence", f"Test case evidenced: {AGREEMENT_TEST_CASES[0]}.", 10),
            ]
            for c, (stage, outcome, evidence, days) in enumerate(ceremony_spec):
                session.add(AgreementCeremony(
                    id=_uid(f"cer.{prefix}.test.{c}"),
                    agreement_id=agr_id,
                    stage=stage,
                    completed_by_member_id=members[0][2],
                    outcome=outcome,
                    evidence=evidence,
                    completed_at=hours_ago(days * 24),
                ))
                counts["ceremonies"] += 1
            # Every participating member attested — consent gate met.
            for i, eco_member in enumerate(eco_members):
                session.add(AgreementMemberConsent(
                    id=_uid(f"amc.{prefix}.test.{eco_member.id.hex}"),
                    agreement_id=agr_id,
                    member_id=eco_member.id,
                    agreement_version="1.0",
                    attestation=(
                        f"I consent to \"{agr_title}\" v1.0. -- {eco_member.display_name}"
                    ),
                    attested_at=hours_ago(32 * 24 - i),
                ))
                counts["member_consents"] += 1

            # ===========================================================
            # 9. COMMITMENT ARTIFACT — the ecosystem's ACTIVE decision
            #    protocol agreement gets its act_policy, full member
            #    consent, and a minted commitment decision record.
            # ===========================================================
            decision_agr_id = DECISION_AGREEMENTS[prefix]
            decision_agr = await session.scalar(
                select(Agreement).where(Agreement.id == decision_agr_id)
            )
            if decision_agr is None:
                print(f"  ! decision agreement missing for {prefix}; run seed_omnione first")
                continue
            decision_agr.act_policy = _policy(2, None, [])

            # Historical ceremonies so the activated agreement's gate panel
            # reflects the process it actually completed.
            decision_ceremonies = [
                ("advice", "opened", "Advice ceremony opened.", 60),
                ("advice", "round", "Advice round 1: protocol text refined.", 58),
                ("advice", "round", "Advice round 2: text stabilized.", 56),
                ("consent", "opened", "Advice gate met — consent ceremony opened.", 54),
                ("test", "started", "Consent complete — test period started.", 52),
                ("test", "evidence", "Test evidence reviewed; protocol adopted for trial.", 50),
                ("active", "passed", "All declared gates satisfied — agreement activated.", 45),
            ]
            for c, (stage, outcome, evidence, days) in enumerate(decision_ceremonies):
                session.add(AgreementCeremony(
                    id=_uid(f"cer.{prefix}.decision.{c}"),
                    agreement_id=decision_agr_id,
                    stage=stage,
                    completed_by_member_id=members[0][2],
                    outcome=outcome,
                    evidence=evidence,
                    completed_at=hours_ago(days * 24),
                ))
                counts["ceremonies"] += 1

            # Flush before minting the artifact (same ordering hazard).
            await session.flush()

            consenting = []
            for i, eco_member in enumerate(eco_members):
                session.add(AgreementMemberConsent(
                    id=_uid(f"amc.{prefix}.decision.{eco_member.id.hex}"),
                    agreement_id=decision_agr_id,
                    member_id=eco_member.id,
                    agreement_version=decision_agr.version,
                    attestation=(
                        f"I consent to \"{decision_agr.title}\" v{decision_agr.version} "
                        f"as the standing decision-making protocol. -- {eco_member.display_name}"
                    ),
                    attested_at=hours_ago(45 * 24 - i),
                ))
                counts["member_consents"] += 1
                consenting.append((eco_member.display_name, eco_member.role or "user"))

            dec_id = _uid(f"deccommit.{prefix}")
            business_id = DECISION_AGREEMENT_BUSINESS_IDS[prefix]
            session.add(DecisionRecord(
                id=dec_id,
                ecosystem_id=eco_id,
                record_id=f"DEC-{business_id}",
                date=days_ago(45),
                holding=(
                    f"The members of {eco_name} commit to \"{decision_agr.title}\" "
                    f"(v{decision_agr.version}). {(decision_agr.text or '').strip()}"
                ),
                ratio_decidendi=(
                    "The agreement completed the ACT process: declared advice rounds, "
                    "member consent to the ratified text, and test evidence were all "
                    "satisfied under the gate policy declared at the agreement level."
                ),
                deliberation_summary=(
                    f"{len(consenting)} member(s) attested to version "
                    f"{decision_agr.version}. This record is the standing commitment "
                    f"artifact produced by the agreement."
                ),
                source_skill="act-process",
                artifact_type="commitment",
                artifact_reference=business_id,
                source_agreement_id=decision_agr_id,
                domain=decision_agr.domain,
                precedent_level="binding",
                status="active",
                recorder=decision_agr.proposer,
                recorder_role="proposer",
                review_date=decision_agr.review_date,
            ))
            counts["decisions"] += 1
            for j, (name, role) in enumerate(consenting):
                session.add(DecisionParticipant(
                    id=_uid(f"decpart.{prefix}.decision.{j}"),
                    decision_record_id=dec_id,
                    name=name,
                    role=role,
                    position="consent",
                ))
                counts["decision_participants"] += 1
            session.add(DecisionSemanticTag(
                id=_uid(f"dectag.{prefix}.decision"),
                decision_record_id=dec_id,
                topic={"category": decision_agr.domain, "agreement_type": decision_agr.type},
                affected_parties=decision_agr.affected_parties,
                ecosystem_scope="internal",
                urgency_at_time="standard",
            ))

        await session.commit()

        print("ACT lifecycle seed complete:")
        for key, value in counts.items():
            print(f"  {key}: {value}")

    await engine.dispose()


def main() -> None:
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Seed ACT lifecycle data (gates, artifacts, commitments)")
    parser.add_argument("--purge", action="store_true", help="Delete this script's seed data and exit")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        try:
            from neos_agent.config import get_settings
            database_url = get_settings().DATABASE_URL
        except Exception:
            print("Error: DATABASE_URL not set.")
            sys.exit(1)

    if args.purge:
        asyncio.run(purge(database_url))
    else:
        asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
