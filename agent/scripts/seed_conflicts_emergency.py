"""Seed additional conflicts, repair agreements, emergencies, and exit records.

Usage:
    python -m agent.scripts.seed_conflicts_emergency
    python -m agent.scripts.seed_conflicts_emergency --purge

Creates:
  8 additional conflict cases (2 per ecosystem in various states)
  4 repair agreement records
  3 additional emergency states (1 open, 1 recovery, 1 with pending review)
  3 additional exit records in different states
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import (
    Base,
    ConflictCase,
    RepairAgreementRecord,
    EmergencyState,
    ExitRecord,
)


# ---------------------------------------------------------------------------
# Deterministic UUID helper — uuid5 for idempotency
# ---------------------------------------------------------------------------
def _uid(name: str) -> uuid.UUID:
    """Generate a deterministic UUID based on a seed name."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"neos.seed.{name}")


# ---------------------------------------------------------------------------
# Date / time helpers
# ---------------------------------------------------------------------------
TODAY = date.today()
NOW = datetime.now(timezone.utc)
NOW_NAIVE = datetime.utcnow()  # naive UTC for TIMESTAMP WITHOUT TIME ZONE columns


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def days_from_now(n: int) -> date:
    return TODAY + timedelta(days=n)


def hours_ago(n: int) -> datetime:
    """Return naive UTC datetime for DB columns without timezone."""
    return NOW_NAIVE - timedelta(hours=n)


def hours_from_now(n: int) -> datetime:
    """Return naive UTC datetime for DB columns without timezone."""
    return NOW_NAIVE + timedelta(hours=n)


# ---------------------------------------------------------------------------
# IDs — must match seed_omnione.py
# ---------------------------------------------------------------------------
# Ecosystems
eco_omni_id = _uid("eco.omnione")
eco_eb_id = _uid("eco.escherbridge")
eco_ps_id = _uid("eco.plansystems")
eco_oa_id = _uid("eco.oasis")

# Members
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
# All IDs created by THIS script (for purge)
# ---------------------------------------------------------------------------
CONFLICT_IDS = [
    _uid("conflict.omni.2"),
    _uid("conflict.omni.3"),
    _uid("conflict.eb.2"),
    _uid("conflict.eb.3"),
    _uid("conflict.ps.2"),
    _uid("conflict.ps.3"),
    _uid("conflict.oa.2"),
    _uid("conflict.oa.3"),
]

REPAIR_IDS = [
    _uid("repair.omni.2"),
    _uid("repair.eb.2"),
    _uid("repair.ps.2"),
    _uid("repair.oa.2"),
]

EMERGENCY_IDS = [
    _uid("emerg.eb.flood"),
    _uid("emerg.ps.infra"),
    _uid("emerg.oa.vuln"),
]

EXIT_IDS = [
    _uid("exit.eb.kenny"),
    _uid("exit.ps.drew"),
    _uid("exit.oa.david"),
]


# ---------------------------------------------------------------------------
# Purge — delete only records created by THIS script
# ---------------------------------------------------------------------------
async def purge(database_url: str) -> None:
    """Delete only the records seeded by this script."""
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Delete in FK-safe order: repairs before conflicts, exits/emergencies standalone
        for rid in REPAIR_IDS:
            await session.execute(
                delete(RepairAgreementRecord).where(RepairAgreementRecord.id == rid)
            )
        for cid in CONFLICT_IDS:
            await session.execute(
                delete(ConflictCase).where(ConflictCase.id == cid)
            )
        for eid in EMERGENCY_IDS:
            await session.execute(
                delete(EmergencyState).where(EmergencyState.id == eid)
            )
        for xid in EXIT_IDS:
            await session.execute(
                delete(ExitRecord).where(ExitRecord.id == xid)
            )
        await session.commit()

    await engine.dispose()
    print("Purged conflicts/emergencies/exits seed data (this script only).")


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
async def seed(database_url: str) -> None:  # noqa: C901
    """Create additional conflict, repair, emergency, and exit records."""
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # ---------------------------------------------------------------
        # Idempotency: skip if first new conflict already exists
        # ---------------------------------------------------------------
        result = await session.execute(
            select(ConflictCase).where(ConflictCase.id == _uid("conflict.omni.2"))
        )
        if result.scalar_one_or_none() is not None:
            print("Additional conflict seed data already exists. Skipping.")
            await engine.dispose()
            return

        # ===============================================================
        # 1. CONFLICT CASES — 8 (2 per ecosystem)
        # ===============================================================

        # --- OmniOne: 2 additional conflicts ---

        # OmniOne #2 — in_mediation, medium severity
        session.add(ConflictCase(
            id=_uid("conflict.omni.2"),
            ecosystem_id=eco_omni_id,
            case_id="CONF-OMNI-002",
            title="Shared Kitchen Use Dispute",
            description=(
                "Ongoing tension between members over shared kitchen scheduling, "
                "food storage space allocation, and cleanup responsibilities. "
                "Multiple informal complaints escalated to a formal case."
            ),
            reporter_id=m_nathan_id,
            facilitator_id=m_josh_id,
            status="in_mediation",
            severity="medium",
            scope="domain",
            tier=2,
            root_cause_category="resource_allocation",
            urgency="standard",
            safety_flag=False,
            domain="Community Stewardship Circle",
            parties=[
                {"member_id": str(m_nathan_id), "name": "Nathan R", "role": "complainant"},
                {"member_id": str(m_ahmed_id), "name": "Ahmed (Jade Oni)", "role": "respondent"},
            ],
            triage_notes="Both parties willing to engage in mediation. Facilitator assigned.",
        ))

        # OmniOne #3 — resolved, low severity
        session.add(ConflictCase(
            id=_uid("conflict.omni.3"),
            ecosystem_id=eco_omni_id,
            case_id="CONF-OMNI-003",
            title="Noise Complaint During Community Hours",
            description=(
                "A member raised concerns about noise levels from construction "
                "work during designated quiet community hours."
            ),
            reporter_id=m_ahmed_id,
            facilitator_id=m_josh_id,
            status="resolved",
            severity="low",
            scope="ecosystem",
            tier=1,
            root_cause_category="behavioral",
            urgency="standard",
            safety_flag=False,
            domain="Core Operations",
            parties=[
                {"member_id": str(m_ahmed_id), "name": "Ahmed (Jade Oni)", "role": "complainant"},
                {"member_id": str(m_nathan_id), "name": "Nathan R", "role": "respondent"},
            ],
            triage_notes="Low severity, resolved through direct conversation.",
            resolution_summary=(
                "Parties agreed to revised construction hours (9am-4pm only). "
                "Nathan acknowledged the community hours policy and committed to compliance."
            ),
            resolved_date=days_ago(5),
        ))

        # --- Escherbridge: 2 additional conflicts ---

        # Escherbridge #2 — in_mediation, high severity, safety_flag
        session.add(ConflictCase(
            id=_uid("conflict.eb.2"),
            ecosystem_id=eco_eb_id,
            case_id="CONF-EB-002",
            title="Equipment Damage Responsibility Dispute",
            description=(
                "Dispute over responsibility for damage to shared studio equipment "
                "(laser cutter valued at $4,500). One party alleges misuse, the other "
                "claims manufacturing defect. Safety concerns raised about equipment "
                "maintenance protocols."
            ),
            reporter_id=m_jak_id,
            facilitator_id=m_ahmed_eb_id,
            status="in_mediation",
            severity="high",
            scope="domain",
            tier=2,
            root_cause_category="resource_damage",
            urgency="urgent",
            safety_flag=True,
            domain="Digital Arts & Technology Circle",
            parties=[
                {"member_id": str(m_jak_id), "name": "Jak", "role": "complainant"},
                {"member_id": str(m_kenny_id), "name": "Kenny", "role": "respondent"},
            ],
            triage_notes=(
                "Safety flag raised due to equipment malfunction risk. "
                "Equipment taken offline pending investigation. Mediation scheduled."
            ),
        ))

        # Escherbridge #3 — escalated, high severity, tier 3
        session.add(ConflictCase(
            id=_uid("conflict.eb.3"),
            ecosystem_id=eco_eb_id,
            case_id="CONF-EB-003",
            title="IP Ownership Disagreement on Collaborative Work",
            description=(
                "Fundamental disagreement over intellectual property rights for a "
                "collaborative digital art installation created by two members. "
                "One member wants to sell commercially; the other insists it should "
                "remain commons-licensed per ecosystem values."
            ),
            reporter_id=m_kenny_id,
            facilitator_id=m_ahmed_eb_id,
            status="escalated",
            severity="high",
            scope="ecosystem",
            tier=3,
            root_cause_category="governance_design",
            urgency="urgent",
            safety_flag=False,
            domain="Governance Circle",
            parties=[
                {"member_id": str(m_kenny_id), "name": "Kenny", "role": "complainant"},
                {"member_id": str(m_jak_id), "name": "Jak", "role": "respondent"},
            ],
            triage_notes=(
                "Escalated to tier 3 after mediation failed to reach agreement. "
                "Requires full governance circle review of IP policy."
            ),
        ))

        # --- Plan Systems: 2 additional conflicts ---

        # Plan Systems #2 — resolved, medium severity, with repair agreement
        session.add(ConflictCase(
            id=_uid("conflict.ps.2"),
            ecosystem_id=eco_ps_id,
            case_id="CONF-PS-002",
            title="Client Confidentiality Boundary Concern",
            description=(
                "Concern raised that a member shared client-specific strategic data "
                "during an external presentation without explicit permission. "
                "No malice suspected, but boundary was crossed."
            ),
            reporter_id=m_rachel_id,
            facilitator_id=m_brandon_id,
            status="resolved",
            severity="medium",
            scope="ecosystem",
            tier=2,
            root_cause_category="boundary",
            urgency="standard",
            safety_flag=False,
            domain="Systems Design Circle",
            parties=[
                {"member_id": str(m_drew_id), "name": "Drew", "role": "respondent"},
                {"member_id": str(m_rachel_id), "name": "Rachel", "role": "complainant"},
            ],
            triage_notes="Drew acknowledged the boundary issue immediately and cooperated fully.",
            resolution_summary=(
                "Drew apologized and agreed to a repair agreement including "
                "confidentiality refresher training and a 60-day checkin cycle. "
                "Client was notified and accepted the resolution."
            ),
            resolved_date=days_ago(20),
        ))

        # Plan Systems #3 — reported, low severity
        session.add(ConflictCase(
            id=_uid("conflict.ps.3"),
            ecosystem_id=eco_ps_id,
            case_id="CONF-PS-003",
            title="Meeting Facilitation Style Feedback",
            description=(
                "A member expressed concern that meeting facilitation style "
                "was not inclusive of quieter participants, leading to "
                "decisions being dominated by more vocal members."
            ),
            reporter_id=m_drew_id,
            status="reported",
            severity="low",
            scope="domain",
            tier=1,
            root_cause_category="process",
            urgency="standard",
            safety_flag=False,
            domain="Governance Circle",
            parties=[
                {"member_id": str(m_drew_id), "name": "Drew", "role": "complainant"},
                {"member_id": str(m_brandon_id), "name": "Brandon", "role": "respondent"},
            ],
            triage_notes="Initial report received. Awaiting facilitator assignment.",
        ))

        # --- Oasis: 2 additional conflicts ---

        # Oasis #2 — in_mediation, medium severity
        session.add(ConflictCase(
            id=_uid("conflict.oa.2"),
            ecosystem_id=eco_oa_id,
            case_id="CONF-OA-002",
            title="Node Resource Allocation Fairness",
            description=(
                "Dispute about whether validator node resources are being "
                "allocated fairly across contributors, with concerns that "
                "early participants receive disproportionate benefits."
            ),
            reporter_id=m_david_id,
            facilitator_id=m_max_id,
            status="in_mediation",
            severity="medium",
            scope="ecosystem",
            tier=2,
            root_cause_category="resource_allocation",
            urgency="standard",
            safety_flag=False,
            domain="Protocol Development Circle",
            parties=[
                {"member_id": str(m_david_id), "name": "David Ellams", "role": "complainant"},
                {"member_id": str(m_max_id), "name": "Max Gershfield", "role": "respondent"},
            ],
            triage_notes="Mediation in progress. Both parties engaged constructively.",
        ))

        # Oasis #3 — resolved, low severity
        session.add(ConflictCase(
            id=_uid("conflict.oa.3"),
            ecosystem_id=eco_oa_id,
            case_id="CONF-OA-003",
            title="Communication Channel Governance",
            description=(
                "Disagreement over which communication channels should be "
                "official for governance discussions versus informal chat."
            ),
            reporter_id=m_max_id,
            facilitator_id=m_david_id,
            status="resolved",
            severity="low",
            scope="ecosystem",
            tier=1,
            root_cause_category="governance_design",
            urgency="standard",
            safety_flag=False,
            domain="Governance Circle",
            parties=[
                {"member_id": str(m_max_id), "name": "Max Gershfield", "role": "complainant"},
                {"member_id": str(m_david_id), "name": "David Ellams", "role": "respondent"},
            ],
            triage_notes="Quickly resolved through consensus on channel policy.",
            resolution_summary=(
                "Agreed to designate Discord #governance as the official channel for "
                "binding discussions, with Telegram remaining for informal coordination."
            ),
            resolved_date=days_ago(10),
        ))

        await session.flush()

        # ===============================================================
        # 2. REPAIR AGREEMENT RECORDS — 4
        # ===============================================================

        # OmniOne — active, for kitchen dispute (conflict.omni.2)
        session.add(RepairAgreementRecord(
            id=_uid("repair.omni.2"),
            conflict_case_id=_uid("conflict.omni.2"),
            title="Kitchen Use Mediation Agreement",
            status="active",
            responsible_party="Nathan R and Ahmed (Jade Oni)",
            commitments=[
                {"commitment": "Create shared kitchen schedule posted weekly", "owner": "Nathan R"},
                {"commitment": "Establish cleanup rota with accountability buddy system", "owner": "Ahmed (Jade Oni)"},
                {"commitment": "Monthly kitchen circle meeting to surface issues early", "owner": "Both"},
            ],
            checkin_30_date=days_from_now(20),
        ))

        # Escherbridge — pending, for equipment dispute (conflict.eb.2)
        session.add(RepairAgreementRecord(
            id=_uid("repair.eb.2"),
            conflict_case_id=_uid("conflict.eb.2"),
            title="Equipment Responsibility and Safety Protocol Agreement",
            status="pending",
            responsible_party="Jak and Kenny",
            commitments=[
                {"commitment": "Split repair costs 50/50 pending investigation outcome", "owner": "Both"},
                {"commitment": "Complete equipment safety certification before reuse", "owner": "Both"},
                {"commitment": "Draft updated equipment usage policy for circle review", "owner": "Kenny"},
            ],
        ))

        # Plan Systems — completed, for confidentiality case (conflict.ps.2)
        session.add(RepairAgreementRecord(
            id=_uid("repair.ps.2"),
            conflict_case_id=_uid("conflict.ps.2"),
            title="Confidentiality Boundary Repair Agreement",
            status="completed",
            responsible_party="Drew",
            commitments=[
                {"commitment": "Complete confidentiality refresher training", "owner": "Drew", "status": "done"},
                {"commitment": "Review and sign updated NDA addendum", "owner": "Drew", "status": "done"},
                {"commitment": "Present learnings to team in retrospective", "owner": "Drew", "status": "done"},
            ],
            checkin_30_date=days_ago(15),
            checkin_30_notes=(
                "Drew completed training on schedule. No further incidents. "
                "Team feedback positive on the retrospective presentation."
            ),
            checkin_60_date=days_ago(2),
            checkin_60_notes=(
                "All commitments fulfilled. Drew has been exemplary in maintaining "
                "boundaries since the incident. Agreement marked complete."
            ),
            completed_date=days_ago(2),
        ))

        # Oasis — active, for node resource dispute (conflict.oa.2)
        session.add(RepairAgreementRecord(
            id=_uid("repair.oa.2"),
            conflict_case_id=_uid("conflict.oa.2"),
            title="Node Resource Rebalancing Agreement",
            status="active",
            responsible_party="Max Gershfield and David Ellams",
            commitments=[
                {"commitment": "Publish transparent resource allocation formula", "owner": "Max Gershfield"},
                {"commitment": "Implement quarterly rebalancing mechanism", "owner": "David Ellams"},
                {"commitment": "Create community dashboard for resource visibility", "owner": "Both"},
            ],
            checkin_30_date=days_from_now(25),
        ))

        await session.flush()

        # ===============================================================
        # 3. EMERGENCY STATES — 3 additional
        # ===============================================================

        # Escherbridge — OPEN emergency (studio flood)
        session.add(EmergencyState(
            id=_uid("emerg.eb.flood"),
            ecosystem_id=eco_eb_id,
            state="open",
            declared_at=hours_ago(6),
            declared_by="Ahmed (Jade Oni)",
            criteria_met={
                "trigger": "infrastructure_damage",
                "category": "facility_emergency",
                "affected_zones": ["main_studio", "storage"],
            },
            auto_revert_at=hours_from_now(42),  # 48h from declaration
            pre_authorized_roles=["co_creator", "builder"],
            actions_log=[
                {
                    "time": str(hours_ago(6)),
                    "action": "Emergency declared: studio flood from burst pipe in main studio",
                    "actor": "Ahmed (Jade Oni)",
                },
                {
                    "time": str(hours_ago(5)),
                    "action": "Water supply shut off. Emergency plumber contacted. Equipment moved to dry storage.",
                    "actor": "Kenny",
                },
            ],
            notes="Active emergency. Main studio and storage area affected. Plumber en route.",
        ))

        # Plan Systems — RECOVERY phase (server failure)
        session.add(EmergencyState(
            id=_uid("emerg.ps.infra"),
            ecosystem_id=eco_ps_id,
            state="recovery",
            declared_at=hours_ago(18),
            declared_by="Rachel",
            criteria_met={
                "trigger": "infrastructure_failure",
                "category": "technology",
                "affected_systems": ["primary_server", "client_portal", "demo_environment"],
            },
            auto_revert_at=hours_from_now(30),
            recovery_entered_at=hours_ago(12),
            pre_authorized_roles=["co_creator", "builder"],
            actions_log=[
                {
                    "time": str(hours_ago(18)),
                    "action": "Emergency declared: server infrastructure failure during live client demo",
                    "actor": "Rachel",
                },
                {
                    "time": str(hours_ago(16)),
                    "action": "Failover to backup server initiated. Client notified of disruption.",
                    "actor": "Brandon",
                },
                {
                    "time": str(hours_ago(12)),
                    "action": "Primary services restored on backup. Entered recovery phase for full migration.",
                    "actor": "Drew",
                },
            ],
            notes=(
                "Recovery phase: primary services restored on backup infrastructure. "
                "Full migration back to primary server pending hardware replacement."
            ),
        ))

        # Oasis — CLOSED with pending post-review (smart contract vulnerability)
        session.add(EmergencyState(
            id=_uid("emerg.oa.vuln"),
            ecosystem_id=eco_oa_id,
            state="closed",
            declared_at=hours_ago(96),  # ~4 days ago
            declared_by="Max Gershfield",
            criteria_met={
                "trigger": "security_vulnerability",
                "category": "smart_contract",
                "affected_systems": ["governance_contract_v2", "token_bridge"],
            },
            auto_revert_at=hours_ago(48),
            recovery_entered_at=hours_ago(72),
            closed_at=hours_ago(24),
            pre_authorized_roles=["co_creator"],
            actions_log=[
                {
                    "time": str(hours_ago(96)),
                    "action": "Emergency declared: critical vulnerability discovered in governance smart contract",
                    "actor": "Max Gershfield",
                },
                {
                    "time": str(hours_ago(90)),
                    "action": "All contract interactions paused. Vulnerability analysis initiated.",
                    "actor": "David Ellams",
                },
                {
                    "time": str(hours_ago(72)),
                    "action": "Patch deployed to testnet. Entered recovery phase for audit.",
                    "actor": "Max Gershfield",
                },
                {
                    "time": str(hours_ago(48)),
                    "action": "External audit confirms patch is sound. Mainnet deployment approved.",
                    "actor": "David Ellams",
                },
                {
                    "time": str(hours_ago(24)),
                    "action": "Patched contract deployed to mainnet. Emergency closed.",
                    "actor": "Max Gershfield",
                },
            ],
            post_review_status="pending",
            notes=(
                "Emergency closed after successful patch. Post-review pending to assess "
                "how the vulnerability was introduced and improve audit processes. "
                "No funds were lost; vulnerability was discovered before exploitation."
            ),
        ))

        await session.flush()

        # ===============================================================
        # 4. EXIT RECORDS — 3 additional
        # ===============================================================

        # Escherbridge — in_progress (Kenny)
        session.add(ExitRecord(
            id=_uid("exit.eb.kenny"),
            ecosystem_id=eco_eb_id,
            member_id=m_kenny_id,
            exit_type="standard",
            status="in_progress",
            declared_date=days_ago(14),
            target_completion_date=days_from_now(16),
            coordinator_id=m_ahmed_eb_id,
            commitment_inventory=[
                {
                    "commitment": "Digital Arts Circle lead role",
                    "status": "transferred_to_Jak",
                },
                {
                    "commitment": "Shared equipment maintenance schedule",
                    "status": "pending_transfer",
                },
            ],
            unwinding_status={
                "commitments_unwound": 1,
                "commitments_total": 2,
                "data_exported": False,
                "contributions_documented": False,
            },
            data_export_requested=True,
            departure_notice=(
                "Thank you for an incredible creative journey at Escherbridge. "
                "I'm moving to focus on independent art practice but hope to "
                "collaborate on future projects."
            ),
            re_entry_eligible=True,
            notes="In progress. One commitment transferred, one pending. Data export queued.",
        ))

        # Plan Systems — cooling_off (Drew)
        session.add(ExitRecord(
            id=_uid("exit.ps.drew"),
            ecosystem_id=eco_ps_id,
            member_id=m_drew_id,
            exit_type="standard",
            status="cooling_off",
            declared_date=days_ago(3),
            target_completion_date=days_from_now(27),
            commitment_inventory=[],
            unwinding_status={
                "commitments_unwound": 0,
                "commitments_total": 0,
                "data_exported": False,
                "contributions_documented": False,
            },
            data_export_requested=False,
            departure_notice=(
                "I need some time to reflect on my participation. "
                "Entering the cooling-off period before making a final decision."
            ),
            re_entry_eligible=True,
            notes="Cooling-off period initiated. No unwinding started yet.",
        ))

        # Oasis — contested (David, involuntary)
        session.add(ExitRecord(
            id=_uid("exit.oa.david"),
            ecosystem_id=eco_oa_id,
            member_id=m_david_id,
            exit_type="involuntary",
            status="contested",
            declared_date=days_ago(7),
            target_completion_date=days_from_now(23),
            coordinator_id=m_max_id,
            commitment_inventory=[
                {
                    "commitment": "Protocol Development Circle contributor",
                    "status": "frozen",
                },
                {
                    "commitment": "Smart contract audit reviewer",
                    "status": "frozen",
                },
            ],
            unwinding_status={
                "commitments_unwound": 0,
                "commitments_total": 2,
                "data_exported": False,
                "contributions_documented": False,
                "contested": True,
                "linked_conflict_case": "CONF-OA-002",
            },
            data_export_requested=True,
            re_entry_eligible=False,
            notes=(
                "Exit contested by member. Linked to conflict case CONF-OA-002 "
                "(Node Resource Allocation Fairness). Data export requested but "
                "not completed pending resolution of contest."
            ),
        ))

        # ===============================================================
        # COMMIT
        # ===============================================================
        await session.commit()

    await engine.dispose()

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print()
    print("=== NEOS Conflict/Emergency/Exit Seed Data ===")
    print("Conflicts: 8 additional (2 per ecosystem in various states)")
    print("  OmniOne: in_mediation + resolved")
    print("  Escherbridge: in_mediation (safety_flag) + escalated (tier 3)")
    print("  Plan Systems: resolved + reported")
    print("  Oasis: in_mediation + resolved")
    print("Repair Agreements: 4 (active, pending, completed, active)")
    print("Emergency States: 3 additional")
    print("  Escherbridge: open (studio flood)")
    print("  Plan Systems: recovery (server failure)")
    print("  Oasis: closed with pending post-review (smart contract vuln)")
    print("Exit Records: 3 additional")
    print("  Escherbridge: in_progress (Kenny)")
    print("  Plan Systems: cooling_off (Drew)")
    print("  Oasis: contested/involuntary (David)")
    print("=== Done ===")


def main() -> None:
    """Entry point for the seed script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed additional conflicts, emergencies, and exits for QA testing"
    )
    parser.add_argument(
        "--purge", action="store_true",
        help="Delete only the records created by this script, then re-seed",
    )
    args = parser.parse_args()

    try:
        from neos_agent.config import get_settings
        database_url = get_settings().DATABASE_URL
    except Exception:
        print("Error: DATABASE_URL not set. Set it as an environment variable or in agent/.env")
        sys.exit(1)

    if args.purge:
        print("Purging conflict/emergency/exit seed data...")
        asyncio.run(purge(database_url))

    asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
