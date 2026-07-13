"""Skill benchmark for the NEOS agent on an in-memory SQLite database.

Seeds the same test data as the pytest fixtures, then exercises every
governance tool and reports pass/fail results and timing.
"""

from __future__ import annotations

import asyncio
import sys
import time
import traceback
import uuid
from datetime import date
from pathlib import Path

# Make agent packages importable when run from agent/ directory
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from neos_agent.db.models import (
    Base,
    Agreement,
    Domain,
    DomainElement,
    Ecosystem,
    Member,
    Proposal,
    User,
)
from neos_agent.agent.governance_tools import GOVERNANCE_TOOLS, execute_tool


# Stable UUIDs (must match conftest.py for test reproducibility)
ECO_ID = uuid.UUID("00000000000000000000000000000001")
USER_LANI_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "test.user.lani")
USER_KAI_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "test.user.kai")
USER_MANU_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "test.user.manu")
MEMBER_STEWARD_ID = uuid.UUID("00000000000000000000000000000010")
MEMBER_BUILDER_ID = uuid.UUID("00000000000000000000000000000020")
MEMBER_TH_ID = uuid.UUID("00000000000000000000000000000030")
DOMAIN_ID = uuid.UUID("00000000000000000000000000000100")
AGREEMENT_ACTIVE_ID = uuid.UUID("00000000000000000000000000001000")
AGREEMENT_DRAFT_ID = uuid.UUID("00000000000000000000000000002000")
PROPOSAL_ID = uuid.UUID("00000000000000000000000000010000")


async def seed_database(session: AsyncSession) -> None:
    """Seed in-memory SQLite with the standard OmniOne governance test data."""
    eco = Ecosystem(id=ECO_ID, name="OmniOne", status="active")
    session.add(eco)

    user_lani = User(id=USER_LANI_ID, display_name="Lani")
    user_kai = User(id=USER_KAI_ID, display_name="Kai")
    user_manu = User(id=USER_MANU_ID, display_name="Manu")
    session.add_all([user_lani, user_kai, user_manu])
    await session.flush()

    lani = Member(
        id=MEMBER_STEWARD_ID,
        ecosystem_id=ECO_ID,
        user_id=USER_LANI_ID,
        member_id="MEM-001",
        display_name="Lani",
        current_status="active",
        profile="co_creator",
    )
    kai = Member(
        id=MEMBER_BUILDER_ID,
        ecosystem_id=ECO_ID,
        user_id=USER_KAI_ID,
        member_id="MEM-002",
        display_name="Kai",
        current_status="active",
        profile="builder",
    )
    manu = Member(
        id=MEMBER_TH_ID,
        ecosystem_id=ECO_ID,
        user_id=USER_MANU_ID,
        member_id="MEM-003",
        display_name="Manu",
        current_status="active",
        profile="townhall",
    )
    session.add_all([lani, kai, manu])

    domain = Domain(
        id=DOMAIN_ID,
        ecosystem_id=ECO_ID,
        domain_id="SHUR-KITCHEN",
        version="1.0",
        status="active",
        purpose="Community kitchen operations and scheduling",
        current_steward="Lani",
        steward_id=MEMBER_STEWARD_ID,
        elements={"primary_accountabilities": ["meal scheduling", "hygiene"]},
    )
    session.add(domain)

    de1 = DomainElement(
        id=uuid.uuid4(),
        domain_id=DOMAIN_ID,
        element_name="primary_accountabilities",
        element_value=["meal scheduling", "hygiene standards"],
    )
    de2 = DomainElement(
        id=uuid.uuid4(),
        domain_id=DOMAIN_ID,
        element_name="key_resources",
        element_value=["kitchen space", "cooking equipment"],
    )
    session.add_all([de1, de2])

    agr_active = Agreement(
        id=AGREEMENT_ACTIVE_ID,
        ecosystem_id=ECO_ID,
        agreement_id="AGR-SHUR-2026-001",
        type="space",
        title="SHUR Kitchen Scheduling Agreement",
        version="1.0",
        status="active",
        proposer="Kai",
        affected_parties=["Lani", "Kai", "Manu"],
        domain="SHUR Kitchen",
        text="Kitchen scheduling rules for OmniOne SHUR.",
        created_date=date(2026, 1, 15),
    )
    agr_draft = Agreement(
        id=AGREEMENT_DRAFT_ID,
        ecosystem_id=ECO_ID,
        agreement_id="AGR-GARD-2026-002",
        type="access",
        title="Garden Composting Access Agreement",
        version="0.1",
        status="draft",
        proposer="Manu",
        domain="Garden",
        text="Composting access rules.",
        created_date=date(2026, 2, 1),
    )
    session.add_all([agr_active, agr_draft])

    prop = Proposal(
        id=PROPOSAL_ID,
        ecosystem_id=ECO_ID,
        proposal_id="PROP-2026-001",
        type="agreement",
        decision_type="consent",
        title="Add evening kitchen hours",
        version="1.0",
        status="advice",
        proposer="Kai",
        affected_domain="SHUR-KITCHEN",
        created_date=date(2026, 2, 10),
    )
    session.add(prop)

    await session.commit()


# Test cases for each governance tool
# Format: list of (tool_name, args, expected_success)
TEST_CASES: list[tuple[str, dict, bool, str]] = [
    ("search_agreements", {"status": "active"}, True, "Find active agreement"),
    ("get_agreement", {"agreement_id": "AGR-SHUR-2026-001"}, True, "Get existing agreement"),
    ("get_agreement", {"agreement_id": "AGR-NOPE-9999-999"}, False, "Get missing agreement"),
    (
        "create_agreement_draft",
        {
            "title": "Yoga Studio Hours",
            "type": "space",
            "proposer": "Kai",
            "domain": "Wellness",
            "text": "Yoga studio hours.",
            "affected_parties": ["Lani", "Manu"],
        },
        True,
        "Create agreement draft",
    ),
    ("update_agreement_status", {"agreement_id": "AGR-GARD-2026-002", "new_status": "advice"}, True, "Transition draft to advice"),
    ("check_authority", {"member": "Lani", "domain": "SHUR-KITCHEN", "action": "update"}, True, "Lani is steward"),
    ("check_authority", {"member": "Kai", "domain": "SHUR-KITCHEN", "action": "update"}, True, "Kai is not steward"),
    ("get_member_roles", {"member": "Lani"}, True, "Get member roles"),
    (
        "create_proposal",
        {
            "title": "Expand kitchen hours",
            "type": "agreement",
            "proposer": "Kai",
            "proposed_change": "Extend kitchen hours to 10pm.",
            "rationale": "More members need evening access.",
            "affected_domain": "SHUR-KITCHEN",
        },
        True,
        "Create proposal",
    ),
    ("get_proposal", {"proposal_id": "PROP-2026-001"}, True, "Get existing proposal"),
    ("get_active_members", {}, True, "List active members"),
    ("list_ecosystems", {}, True, "List ecosystems"),
    ("get_ecosystem", {"name": "OmniOne"}, True, "Get ecosystem"),
    ("get_domain", {"domain_id": "SHUR-KITCHEN"}, True, "Get domain"),
    ("list_domains", {}, True, "List domains"),
    ("record_advice", {"proposal_id": "PROP-2026-001", "advisor": "Manu", "position": "support", "advice": "Good idea."}, True, "Record advice"),
    ("update_proposal_status", {"proposal_id": "PROP-2026-001", "new_status": "consent"}, True, "Advance proposal to consent"),
    ("record_consent_position", {"proposal_id": "PROP-2026-001", "participant": "Lani", "position": "consent"}, True, "Record consent"),
    ("check_quorum", {"proposal_id": "PROP-2026-001"}, True, "Check quorum"),
    ("create_decision_record", {"proposal_id": "PROP-2026-001", "holding": "approved", "rationale": "No objections and consent received."}, True, "Create decision record"),
    ("search_precedents", {"topic": "kitchen"}, True, "Search precedents"),
    ("get_member_roles", {"member": "Lani"}, True, "Get member roles by name"),
    ("create_conflict_case", {"title": "Schedule conflict", "description": "Kai and Manu disagree about scheduling.", "initiator": "Kai", "respondent": "Manu", "domain": "SHUR-KITCHEN"}, True, "Create conflict case"),
    ("get_emergency_state", {"ecosystem_id": str(ECO_ID)}, True, "Get emergency state"),
    ("declare_emergency", {"ecosystem_id": str(ECO_ID), "declarant": "Lani", "reason": "Storm damage"}, True, "Declare emergency"),
    ("create_exit_record", {"member_name": "Manu", "reason": "Relocation", "departure_notice": "2026-05-01"}, True, "Create exit record"),
    ("create_safeguard_audit", {"ecosystem_id": str(ECO_ID), "auditor": "Lani", "findings": "No capture risks detected."}, True, "Create safeguard audit"),
]


async def run_benchmark() -> None:
    """Create in-memory DB, seed it, run all skill test cases."""
    print("=" * 70)
    print("NEOS Agent Governance Skill Benchmark")
    print("=" * 70)

    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        await seed_database(session)
        print("✅ Database seeded with OmniOne governance test data")

    results = []
    total_start = time.perf_counter()

    for tool_name, args, expected_success, description in TEST_CASES:
        async with session_factory() as session:
            start = time.perf_counter()
            try:
                result = await execute_tool(tool_name, args, session, ecosystem_ids=[ECO_ID])
                success = result.get("success", False) == expected_success
                if success:
                    await session.commit()
                elapsed = time.perf_counter() - start
                status = "PASS" if success else "FAIL"
                results.append((tool_name, description, status, elapsed, result))
                print(f"  {status} {tool_name:30s} ({elapsed:.3f}s) {description}")
            except Exception as exc:
                elapsed = time.perf_counter() - start
                results.append((tool_name, description, "ERROR", elapsed, str(exc)))
                print(f"  ERROR {tool_name:30s} ({elapsed:.3f}s) {description}")
                print("        ", exc)

    total_elapsed = time.perf_counter() - total_start

    await engine.dispose()

    print("=" * 70)
    print("Results")
    print("=" * 70)
    passed = sum(1 for _, _, status, _, _ in results if status == "PASS")
    failed = sum(1 for _, _, status, _, _ in results if status != "PASS")
    print(f"  Total: {len(results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total time: {total_elapsed:.3f}s")

    if failed:
        print("\nFailed cases:")
        for tool_name, description, status, elapsed, result in results:
            if status != "PASS":
                print(f"  - {tool_name}: {description}")
                print(f"    {result}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(run_benchmark())
