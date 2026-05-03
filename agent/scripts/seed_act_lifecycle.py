"""Seed full ACT lifecycle proposals: consent, test, ratified, and withdrawn stages.

Usage:
    python -m agent.scripts.seed_act_lifecycle
    python -m agent.scripts.seed_act_lifecycle --purge

Creates (per ecosystem):
  1 proposal in "consent" stage (with advice log + consent record + participants)
  1 proposal in "test" stage (with advice log + consent record + test report + criteria)
  1 proposal in "ratified" stage (with full history: advice + consent + test + ratification)
  1 proposal in "withdrawn" stage (with advice log showing why it was withdrawn)
  = 16 new proposals total across 4 ecosystems
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import (
    Base,
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
)


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
# Ecosystem IDs (must match seed_omnione)
# ---------------------------------------------------------------------------
eco_omni_id = _uid("eco.omnione")
eco_eb_id = _uid("eco.escherbridge")
eco_ps_id = _uid("eco.plansystems")
eco_oa_id = _uid("eco.oasis")

# ---------------------------------------------------------------------------
# Member IDs (must match seed_omnione)
# ---------------------------------------------------------------------------
m_josh_id = _uid("mbr.omni.josh")
m_nathan_id = _uid("mbr.omni.nathan")
m_ahmed_id = _uid("mbr.omni.ahmed")

m_ahmed_eb_id = _uid("mbr.eb.ahmed")
m_kenny_id = _uid("mbr.eb.kenny")
m_jak_id = _uid("mbr.eb.jak")

m_rachel_id = _uid("mbr.ps.rachel")
m_brandon_id = _uid("mbr.ps.brandon")
m_drew_id = _uid("mbr.ps.drew")

m_max_id = _uid("mbr.oa.max")
m_david_id = _uid("mbr.oa.david")


# ---------------------------------------------------------------------------
# All new proposal IDs (for idempotency check and purge)
# ---------------------------------------------------------------------------
ALL_PROPOSAL_IDS = []

ECOSYSTEMS = [
    # (eco_id, prefix, eco_name,
    #  members: [(name, role), ...],
    #  titles: {consent, test, ratified, withdrawn},
    #  domain)
    (
        eco_omni_id, "omni", "OmniOne",
        [("Josh Pasmore", "co_creator"), ("Nathan R", "builder"), ("Ahmed (Jade Oni)", "co_creator")],
        {
            "consent": ("Water Management Cooperative Framework", "Establish shared water resource allocation across community plots."),
            "test": ("Community Composting Protocol", "Standardize composting procedures and output distribution."),
            "ratified": ("Guest Visitor Policy", "Define guest access rights, duration limits, and sponsor responsibilities."),
            "withdrawn": ("Food Forest Expansion Plan", "Proposal to convert shared meadow into food forest zones."),
        },
        "Core Operations",
    ),
    (
        eco_eb_id, "eb", "Escherbridge",
        [("Ahmed (Jade Oni)", "co_creator"), ("Kenny", "builder"), ("Jak", "co_creator")],
        {
            "consent": ("Exhibition Scheduling Governance", "Establish fair rotation and booking system for gallery exhibitions."),
            "test": ("Artist Residency Program Structure", "Define selection criteria, duration, and resource allocation for residencies."),
            "ratified": ("Equipment Maintenance Protocol", "Shared responsibility framework for studio equipment upkeep."),
            "withdrawn": ("Workshop Fee Restructuring", "Proposal to restructure workshop participation fees."),
        },
        "Core Operations",
    ),
    (
        eco_ps_id, "ps", "Plan Systems",
        [("Rachel", "co_creator"), ("Brandon", "builder"), ("Drew", "townhall")],
        {
            "consent": ("Open Source Contribution Policy", "Define IP boundaries and contribution guidelines for open source work."),
            "test": ("Professional Training Program", "Structured training and mentorship for new systems designers."),
            "ratified": ("Revenue Sharing Framework", "Equitable revenue distribution model for collaborative projects."),
            "withdrawn": ("Flexible Office Hours Experiment", "Proposal to allow fully flexible working schedules."),
        },
        "Systems Design Circle",
    ),
    (
        eco_oa_id, "oa", "Oasis",
        [("Max Gershfield", "co_creator"), ("David Ellams", "builder")],
        {
            "consent": ("Token Distribution Governance", "Define transparent token allocation and vesting schedules."),
            "test": ("Node Operator Requirements Update", "Updated minimum hardware and uptime requirements for node operators."),
            "ratified": ("Public API Access Policy", "Tiered API access framework with rate limits and contributor benefits."),
            "withdrawn": ("Governance Reward Token", "Proposal to mint governance participation reward tokens."),
        },
        "Protocol Development Circle",
    ),
]


def _build_proposal_ids():
    """Pre-compute all proposal IDs for use in purge and idempotency."""
    for eco_id, prefix, *_ in ECOSYSTEMS:
        for stage in ("consent", "test", "ratified", "withdrawn"):
            ALL_PROPOSAL_IDS.append(_uid(f"prop.{prefix}.{stage}"))


_build_proposal_ids()


# ---------------------------------------------------------------------------
# Purge — only remove data created by this script
# ---------------------------------------------------------------------------
PURGE_TABLES = [
    "test_success_criteria",
    "test_reports",
    "consent_objections_addressed",
    "consent_integration_rounds",
    "consent_participants",
    "consent_records",
    "advice_non_respondents",
    "advice_entries",
    "advice_logs",
    "proposals",
]


async def purge(database_url: str) -> None:
    """Delete only proposals and sub-records created by this script."""
    engine = create_async_engine(database_url)

    prop_id_literals = ", ".join(f"'{str(pid)}'" for pid in ALL_PROPOSAL_IDS)

    async with engine.begin() as conn:
        # Delete child records via proposal FK chain
        # test_success_criteria -> test_reports -> proposal
        await conn.execute(text(
            f'DELETE FROM "test_success_criteria" WHERE test_report_id IN '
            f'(SELECT id FROM "test_reports" WHERE proposal_id IN ({prop_id_literals}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "test_reports" WHERE proposal_id IN ({prop_id_literals})'
        ))

        # consent chain: objections -> rounds -> participants -> records
        await conn.execute(text(
            f'DELETE FROM "consent_objections_addressed" WHERE integration_round_id IN '
            f'(SELECT id FROM "consent_integration_rounds" WHERE consent_record_id IN '
            f'(SELECT id FROM "consent_records" WHERE proposal_id IN ({prop_id_literals})))'
        ))
        await conn.execute(text(
            f'DELETE FROM "consent_integration_rounds" WHERE consent_record_id IN '
            f'(SELECT id FROM "consent_records" WHERE proposal_id IN ({prop_id_literals}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "consent_participants" WHERE consent_record_id IN '
            f'(SELECT id FROM "consent_records" WHERE proposal_id IN ({prop_id_literals}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "consent_records" WHERE proposal_id IN ({prop_id_literals})'
        ))

        # advice chain: non_respondents, entries -> logs
        await conn.execute(text(
            f'DELETE FROM "advice_non_respondents" WHERE advice_log_id IN '
            f'(SELECT id FROM "advice_logs" WHERE proposal_id IN ({prop_id_literals}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "advice_entries" WHERE advice_log_id IN '
            f'(SELECT id FROM "advice_logs" WHERE proposal_id IN ({prop_id_literals}))'
        ))
        await conn.execute(text(
            f'DELETE FROM "advice_logs" WHERE proposal_id IN ({prop_id_literals})'
        ))

        # Finally, the proposals themselves
        await conn.execute(text(
            f'DELETE FROM "proposals" WHERE id IN ({prop_id_literals})'
        ))

    print(f"Purged {len(ALL_PROPOSAL_IDS)} ACT lifecycle proposals and all sub-records.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
async def seed(database_url: str) -> None:  # noqa: C901
    """Create 16 proposals across 4 ACT lifecycle stages in 4 ecosystems."""
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # ---------------------------------------------------------------
        # Idempotency: skip if the first proposal already exists
        # ---------------------------------------------------------------
        sentinel_id = _uid("prop.omni.consent")
        result = await session.execute(
            select(Proposal).where(Proposal.id == sentinel_id)
        )
        if result.scalar_one_or_none() is not None:
            print("ACT lifecycle proposals already seeded. Skipping. Use --purge to reseed.")
            await engine.dispose()
            return

        counts = {"proposals": 0, "advice_logs": 0, "advice_entries": 0,
                  "non_respondents": 0, "consent_records": 0, "consent_participants": 0,
                  "integration_rounds": 0, "objections_addressed": 0,
                  "test_reports": 0, "success_criteria": 0}

        for (eco_id, prefix, eco_name, members, titles, domain) in ECOSYSTEMS:
            prop_num = 2  # start at 002 (001 is from seed_omnione)

            # ===== A: CONSENT STAGE =====
            stage = "consent"
            prop_id = _uid(f"prop.{prefix}.{stage}")
            prop_id_str = f"PROP-{prefix.upper()}-{prop_num:03d}"
            title, change = titles[stage]
            prop_num += 1

            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=prop_id_str,
                type="policy",
                decision_type="consent",
                title=title,
                version="1.0",
                status="consent",
                proposer=members[0][0],
                affected_domain=domain,
                urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Needed to improve governance clarity in {eco_name}.",
                created_date=days_ago(21),
                advice_deadline=days_ago(14),
                consent_deadline=days_from_now(7),
                test_duration=None,
            ))
            counts["proposals"] += 1

            # Advice log (completed)
            al_id = _uid(f"advlog.{prefix}.{stage}")
            session.add(AdviceLog(
                id=al_id,
                proposal_id=prop_id,
                advice_window_start=days_ago(21),
                advice_window_end=days_ago(14),
                urgency="standard",
                summary="Advice collection complete. Two integrated responses; one non-respondent.",
                proposer_modifications="Minor language clarifications based on feedback.",
            ))
            counts["advice_logs"] += 1

            # 2 advice entries (integrated)
            for i, (advisor, role) in enumerate(members[:2]):
                session.add(AdviceEntry(
                    id=_uid(f"adventry.{prefix}.{stage}.{i}"),
                    advice_log_id=al_id,
                    advisor=advisor,
                    role=role,
                    date=days_ago(18 - i),
                    advice_text=f"Generally supportive. Suggests clearer implementation timeline. -- {advisor}",
                    proposer_response=f"Incorporated timeline suggestion from {advisor}.",
                    integration_status="integrated",
                ))
                counts["advice_entries"] += 1

            # 1 non-respondent
            nr_name = members[-1][0] if len(members) > 2 else "Community Observer"
            session.add(AdviceNonRespondent(
                id=_uid(f"advnr.{prefix}.{stage}"),
                advice_log_id=al_id,
                name=nr_name,
                notified_date=days_ago(20),
                follow_up_sent=True,
            ))
            counts["non_respondents"] += 1

            # Consent record (in progress — has an objection)
            cr_id = _uid(f"consent.{prefix}.{stage}")
            session.add(ConsentRecord(
                id=cr_id,
                proposal_id=prop_id,
                consent_mode="standard",
                facilitator=members[0][0],
                date=days_ago(7),
                quorum_required="2/3",
                quorum_met=True,
                outcome="pending_integration",
                final_proposal_version="1.0",
            ))
            counts["consent_records"] += 1

            # Consent participants: 2 consent + 1 object
            consent_participants = [
                (members[0][0], members[0][1], "consent", "Fully aligned with the proposal."),
                (members[1][0], members[1][1], "consent", "No principled objection."),
            ]
            if len(members) > 2:
                consent_participants.append(
                    (members[2][0], members[2][1], "object",
                     "Concerned about implementation timeline being too aggressive.")
                )
            else:
                consent_participants.append(
                    (members[1][0] + " (second round)", members[1][1], "object",
                     "Concerned about resource allocation during transition period.")
                )

            for j, (name, role, position, reason) in enumerate(consent_participants):
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

            # 1 integration round addressing the objection
            ir_id = _uid(f"ir.{prefix}.{stage}")
            session.add(ConsentIntegrationRound(
                id=ir_id,
                consent_record_id=cr_id,
                round_number=1,
                modifications_made="Extended implementation timeline from 2 weeks to 4 weeks.",
                outcome="in_progress",
            ))
            counts["integration_rounds"] += 1

            session.add(ConsentObjectionAddressed(
                id=_uid(f"oa.{prefix}.{stage}"),
                integration_round_id=ir_id,
                objector=consent_participants[-1][0],
                objection=consent_participants[-1][3],
                resolution="Timeline extended to 4 weeks with phased rollout.",
            ))
            counts["objections_addressed"] += 1

            # ===== B: TEST STAGE =====
            stage = "test"
            prop_id = _uid(f"prop.{prefix}.{stage}")
            prop_id_str = f"PROP-{prefix.upper()}-{prop_num:03d}"
            title, change = titles[stage]
            prop_num += 1

            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=prop_id_str,
                type="policy",
                decision_type="consent",
                title=title,
                version="1.1",
                status="test",
                proposer=members[1][0],
                affected_domain=domain,
                urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Operational improvement identified during {eco_name} retrospective.",
                created_date=days_ago(45),
                advice_deadline=days_ago(38),
                consent_deadline=days_ago(28),
                test_duration="30 days",
            ))
            counts["proposals"] += 1

            # Advice log (completed)
            al_id = _uid(f"advlog.{prefix}.{stage}")
            session.add(AdviceLog(
                id=al_id,
                proposal_id=prop_id,
                advice_window_start=days_ago(45),
                advice_window_end=days_ago(38),
                urgency="standard",
                summary="Advice period complete. Strong consensus with minor refinements.",
            ))
            counts["advice_logs"] += 1

            for i, (advisor, role) in enumerate(members[:2]):
                session.add(AdviceEntry(
                    id=_uid(f"adventry.{prefix}.{stage}.{i}"),
                    advice_log_id=al_id,
                    advisor=advisor,
                    role=role,
                    date=days_ago(42 - i),
                    advice_text=f"Strong support. Recommends success metrics be explicit. -- {advisor}",
                    proposer_response="Added explicit success criteria.",
                    integration_status="integrated",
                ))
                counts["advice_entries"] += 1

            # Consent record (passed)
            cr_id = _uid(f"consent.{prefix}.{stage}")
            session.add(ConsentRecord(
                id=cr_id,
                proposal_id=prop_id,
                consent_mode="standard",
                facilitator=members[0][0],
                date=days_ago(30),
                quorum_required="2/3",
                quorum_met=True,
                outcome="consent_achieved",
                final_proposal_version="1.1",
            ))
            counts["consent_records"] += 1

            for j, (name, role) in enumerate(members[:2]):
                session.add(ConsentParticipant(
                    id=_uid(f"cp.{prefix}.{stage}.{j}"),
                    consent_record_id=cr_id,
                    name=name,
                    role=role,
                    position="consent",
                    reason="No principled objection. Proposal is safe enough to try.",
                    round=1,
                ))
                counts["consent_participants"] += 1

            if len(members) > 2:
                session.add(ConsentParticipant(
                    id=_uid(f"cp.{prefix}.{stage}.2"),
                    consent_record_id=cr_id,
                    name=members[2][0],
                    role=members[2][1],
                    position="consent",
                    reason="Aligned with the direction. Looking forward to test results.",
                    round=1,
                ))
                counts["consent_participants"] += 1

            # Test report (in progress)
            tr_id = _uid(f"tr.{prefix}.{stage}")
            test_start = days_ago(25)
            test_end = days_from_now(5)
            session.add(TestReport(
                id=tr_id,
                proposal_id=prop_id,
                test_start_date=test_start,
                test_end_date=test_end,
                midpoint_checkin_date=days_ago(10),
                revert_procedure=f"Revert to previous {eco_name} protocol version if criteria not met.",
                observations="Initial implementation proceeding smoothly. Minor adjustments made at midpoint.",
                midpoint_findings="Two of three criteria on track. Third criterion pending final data.",
                outcome=None,  # still in progress
                next_action="Complete final assessment at test end date.",
                success_criteria_summary="3 criteria defined: 2 on track, 1 pending.",
            ))
            counts["test_reports"] += 1

            # 3 success criteria (2 met, 1 pending)
            criteria_specs = [
                ("Participation rate above 60% of eligible members", True,
                 "Current participation at 72%."),
                ("No unresolved objections during test period", True,
                 "Zero objections raised during test window."),
                ("Measurable improvement in process efficiency", None, None),  # pending
            ]
            for k, (criterion, met, evidence) in enumerate(criteria_specs):
                session.add(TestSuccessCriterion(
                    id=_uid(f"tsc.{prefix}.{stage}.{k}"),
                    test_report_id=tr_id,
                    criterion=criterion,
                    met=met if met is not None else False,
                    evidence=evidence,
                ))
                counts["success_criteria"] += 1

            # ===== C: RATIFIED STAGE =====
            stage = "ratified"
            prop_id = _uid(f"prop.{prefix}.{stage}")
            prop_id_str = f"PROP-{prefix.upper()}-{prop_num:03d}"
            title, change = titles[stage]
            prop_num += 1

            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=prop_id_str,
                type="policy",
                decision_type="consent",
                title=title,
                version="1.2",
                status="ratified",
                proposer=members[0][0],
                affected_domain=domain,
                urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Long-standing need identified by {eco_name} governance circle.",
                created_date=days_ago(90),
                advice_deadline=days_ago(83),
                consent_deadline=days_ago(73),
                test_duration="30 days",
            ))
            counts["proposals"] += 1

            # Advice log (completed)
            al_id = _uid(f"advlog.{prefix}.{stage}")
            session.add(AdviceLog(
                id=al_id,
                proposal_id=prop_id,
                advice_window_start=days_ago(90),
                advice_window_end=days_ago(83),
                urgency="standard",
                summary="Advice complete. Broad support. Integrated two refinements.",
            ))
            counts["advice_logs"] += 1

            for i, (advisor, role) in enumerate(members[:2]):
                session.add(AdviceEntry(
                    id=_uid(f"adventry.{prefix}.{stage}.{i}"),
                    advice_log_id=al_id,
                    advisor=advisor,
                    role=role,
                    date=days_ago(87 - i),
                    advice_text=f"Full support. Minor wording suggestions applied. -- {advisor}",
                    proposer_response="Wording updated per suggestion.",
                    integration_status="integrated",
                ))
                counts["advice_entries"] += 1

            # Consent record (passed)
            cr_id = _uid(f"consent.{prefix}.{stage}")
            session.add(ConsentRecord(
                id=cr_id,
                proposal_id=prop_id,
                consent_mode="standard",
                facilitator=members[0][0],
                date=days_ago(75),
                quorum_required="2/3",
                quorum_met=True,
                outcome="consent_achieved",
                final_proposal_version="1.2",
            ))
            counts["consent_records"] += 1

            for j, (name, role) in enumerate(members[:2]):
                session.add(ConsentParticipant(
                    id=_uid(f"cp.{prefix}.{stage}.{j}"),
                    consent_record_id=cr_id,
                    name=name,
                    role=role,
                    position="consent",
                    reason="No objection. Well-considered proposal.",
                    round=1,
                ))
                counts["consent_participants"] += 1

            if len(members) > 2:
                session.add(ConsentParticipant(
                    id=_uid(f"cp.{prefix}.{stage}.2"),
                    consent_record_id=cr_id,
                    name=members[2][0],
                    role=members[2][1],
                    position="consent",
                    reason="Consent given. Appreciate the thorough advice process.",
                    round=1,
                ))
                counts["consent_participants"] += 1

            # Test report (completed, success)
            tr_id = _uid(f"tr.{prefix}.{stage}")
            session.add(TestReport(
                id=tr_id,
                proposal_id=prop_id,
                test_start_date=days_ago(70),
                test_end_date=days_ago(40),
                midpoint_checkin_date=days_ago(55),
                revert_procedure="Standard revert to prior agreement version.",
                observations="Test period completed successfully. All criteria met.",
                midpoint_findings="Strong positive indicators across all criteria at midpoint.",
                outcome="success",
                next_action="Ratify and add to agreement registry.",
                success_criteria_summary="All 3 criteria met. Proposal ratified.",
                reviewer_notes="Exemplary governance process. Recommend as template.",
            ))
            counts["test_reports"] += 1

            # All 3 criteria met
            ratified_criteria = [
                ("Member satisfaction score above 70%", True,
                 "Survey returned 84% satisfaction."),
                ("No safety or wellbeing concerns raised", True,
                 "Zero incidents reported during test."),
                ("Operational efficiency maintained or improved", True,
                 "Process time reduced by 15%."),
            ]
            for k, (criterion, met, evidence) in enumerate(ratified_criteria):
                session.add(TestSuccessCriterion(
                    id=_uid(f"tsc.{prefix}.{stage}.{k}"),
                    test_report_id=tr_id,
                    criterion=criterion,
                    met=met,
                    evidence=evidence,
                ))
                counts["success_criteria"] += 1

            # ===== D: WITHDRAWN STAGE =====
            stage = "withdrawn"
            prop_id = _uid(f"prop.{prefix}.{stage}")
            prop_id_str = f"PROP-{prefix.upper()}-{prop_num:03d}"
            title, change = titles[stage]
            prop_num += 1

            session.add(Proposal(
                id=prop_id,
                ecosystem_id=eco_id,
                proposal_id=prop_id_str,
                type="policy",
                decision_type="consent",
                title=title,
                version="0.1",
                status="withdrawn",
                proposer=members[1][0] if len(members) > 1 else members[0][0],
                affected_domain=domain,
                urgency="standard",
                impacted_parties={"affected": ["all_members"]},
                proposed_change=change,
                rationale=f"Exploratory proposal for {eco_name} community consideration.",
                created_date=days_ago(30),
                advice_deadline=days_ago(23),
                consent_deadline=None,
                test_duration=None,
            ))
            counts["proposals"] += 1

            # Advice log (showing concerns that led to withdrawal)
            al_id = _uid(f"advlog.{prefix}.{stage}")
            session.add(AdviceLog(
                id=al_id,
                proposal_id=prop_id,
                advice_window_start=days_ago(30),
                advice_window_end=days_ago(23),
                urgency="standard",
                summary="Significant concerns raised during advice. Proposer chose to withdraw.",
            ))
            counts["advice_logs"] += 1

            session.add(AdviceEntry(
                id=_uid(f"adventry.{prefix}.{stage}.0"),
                advice_log_id=al_id,
                advisor=members[0][0],
                role=members[0][1],
                date=days_ago(27),
                advice_text=f"Concerned this may conflict with existing agreements. Needs more research. -- {members[0][0]}",
                integration_status="acknowledged",
            ))
            counts["advice_entries"] += 1

            second_advisor = members[1][0] if len(members) > 1 else members[0][0]
            session.add(AdviceEntry(
                id=_uid(f"adventry.{prefix}.{stage}.1"),
                advice_log_id=al_id,
                advisor=second_advisor,
                role=members[1][1] if len(members) > 1 else members[0][1],
                date=days_ago(26),
                advice_text=f"Timing is premature. Suggest revisiting after current initiatives complete. -- {second_advisor}",
                integration_status="acknowledged",
            ))
            counts["advice_entries"] += 1

        await session.commit()

    await engine.dispose()

    print()
    print("=== ACT Lifecycle Seed Data ===")
    print(f"Proposals:             {counts['proposals']}")
    print(f"Advice logs:           {counts['advice_logs']}")
    print(f"Advice entries:        {counts['advice_entries']}")
    print(f"Non-respondents:       {counts['non_respondents']}")
    print(f"Consent records:       {counts['consent_records']}")
    print(f"Consent participants:  {counts['consent_participants']}")
    print(f"Integration rounds:    {counts['integration_rounds']}")
    print(f"Objections addressed:  {counts['objections_addressed']}")
    print(f"Test reports:          {counts['test_reports']}")
    print(f"Success criteria:      {counts['success_criteria']}")
    print(f"Ecosystems covered:    OmniOne, Escherbridge, Plan Systems, Oasis")
    print("=== Done ===")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed ACT lifecycle proposals for QA testing")
    parser.add_argument("--purge", action="store_true", help="Delete ACT lifecycle data before seeding")
    args = parser.parse_args()

    try:
        from neos_agent.config import get_settings
        database_url = get_settings().DATABASE_URL
    except Exception:
        print("Error: DATABASE_URL not set. Set it as an environment variable or in agent/.env")
        sys.exit(1)

    if args.purge:
        print("Purging ACT lifecycle data...")
        asyncio.run(purge(database_url))

    asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
