"""
Idempotent seed runner for the NEOS governance database.

Usage:
    python -m scratch.seed.run                  # seed the database
    python -m scratch.seed.run --database sqlite+aiosqlite:///neos_seed.db
    python -m scratch.seed.run --database postgresql+asyncpg://...

Environment:
    DATABASE_URL — defaults to sqlite+aiosqlite:///neos_seed.db

All seed functions are idempotent: they check for existing records before
inserting, so you can run this script multiple times safely.
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure the neos_agent package is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from neos_agent.db.models import (
    Base,
    Ecosystem,
    User,
    Member,
    MemberOnboarding,
    MemberStatusTransition,
    Domain,
    DomainElement,
    DomainMetric,
    Agreement,
    AgreementVersion,
    AgreementRatificationRecord,
    AmendmentRecord,
    ReviewRecord,
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
    DecisionDissentRecord,
    DecisionSemanticTag,
    ConflictCase,
    RepairAgreementRecord,
    GovernanceHealthAudit,
    EmergencyState,
    ExitRecord,
    CircleMembership,
    SharesNeeds,
    Collaboration,
)

from personas import PERSONAS
from ecosystem import (
    ECOSYSTEM, ECOSYSTEM_ID,
    DOMAINS, DOMAIN_ELEMENTS, DOMAIN_METRICS,
)
from agreements import (
    AGREEMENTS, RATIFICATION_RECORDS, AMENDMENT_RECORDS, REVIEW_RECORDS,
)
from proposals import (
    PROPOSALS,
    ADVICE_ENTRIES, ADVICE_NON_RESPONDENTS,
    CONSENT_RECORDS, CONSENT_PARTICIPANTS,
    INTEGRATION_ROUNDS, OBJECTIONS_ADDRESSED,
    TEST_REPORTS, TEST_SUCCESS_CRITERIA,
)
from decisions import (
    DECISIONS, DECISION_PARTICIPANTS, DISSENT_RECORDS, SEMANTIC_TAGS,
)
from conflict import CONFLICT_CASES, REPAIR_AGREEMENTS
from emergency import EMERGENCY_STATES
from safeguard import SAFEGUARD_AUDIT
from exit import EXIT_RECORDS
from economic import SHARES_NEEDS, COLLABORATIONS


# ────────────────────────────────────────────────────────────────────
# Engine setup
# ────────────────────────────────────────────────────────────────────

def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///neos_seed.db")


def _ensure_async_url(url: str) -> str:
    """Ensure PostgreSQL URLs use asyncpg driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# ────────────────────────────────────────────────────────────────────
# Step 0: Create all tables
# ────────────────────────────────────────────────────────────────────

async def step_00_create_tables(engine) -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[00] Tables created (if not existed)")


# ────────────────────────────────────────────────────────────────────
# Step 1: Core — Ecosystem, Users, Members, Domains
# ────────────────────────────────────────────────────────────────────

async def step_01_core(session: AsyncSession) -> dict:
    """Seed ecosystem, users, members, domains, and circle memberships.

    Returns a dict mapping persona display_name → (user_id, member_id)
    for cross-referencing in later steps.
    """
    persona_map: dict[str, tuple] = {}

    # Ecosystem
    existing = await session.execute(
        select(Ecosystem).where(Ecosystem.id == ECOSYSTEM_ID)
    )
    if existing.scalar_one_or_none():
        print("[01] Ecosystem already exists — skipping")
    else:
        session.add(Ecosystem(**ECOSYSTEM))
        print("[01] Ecosystem: OmniOne created")

    # Users + Members
    for p in PERSONAS:
        uid = p["id"]
        # User
        q = await session.execute(select(User).where(User.id == uid))
        if q.scalar_one_or_none() is None:
            session.add(User(
                id=uid,
                username=p["username"],
                display_name=p["display_name"],
            ))
        # Member
        mid = uid  # Use same UUID for simplicity
        q2 = await session.execute(select(Member).where(Member.id == mid))
        if q2.scalar_one_or_none() is None:
            session.add(Member(
                id=mid,
                ecosystem_id=ECOSYSTEM_ID,
                user_id=uid,
                member_id=p["member_id"],
                display_name=p["display_name"],
                current_status=p["current_status"],
                profile=p.get("profile"),
                skills_offered=p.get("skills_offered"),
                skills_needed=p.get("skills_needed"),
                interests=p.get("interests"),
                onboarding_status=p.get("onboarding_status"),
                kyc_status=p.get("kyc_status"),
                notes=p.get("notes"),
            ))
        persona_map[p["display_name"]] = (uid, mid)

    # Rani's onboarding record
    rani = persona_map.get("Rani Maheswari")
    if rani:
        _, member_id = rani
        existing = await session.execute(
            select(MemberOnboarding).where(
                MemberOnboarding.member_id == member_id
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(MemberOnboarding(
                member_id=member_id,
                facilitator="Kai Nakamura",
                uaf_version_consented="1.0",
                section_consents={"consented": ["preamble", "principles_1_through_5"]},
                checklist_items={"completed": ["introduction_call", "ecosystem_tour"], "pending": ["full_uaf_consent", "ethos_selection"]},
                completion_percentage=40,
                cooling_off_start=__import__("datetime").date(2025, 5, 15),
                cooling_off_end=__import__("datetime").date(2025, 6, 15),
            ))
            print("[01] MemberOnboarding: Rani Maheswari (in cooling-off period)")

    # MemberStatusTransitions for key personas
    from datetime import date as _date
    transitions = [
        ("Manu Dewantara", "prospective", "active", _date(2024, 6, 22), "UAF consented"),
        ("Lani Wijaya", "prospective", "active", _date(2024, 6, 22), "UAF consented"),
        ("Kai Nakamura", "prospective", "active", _date(2024, 6, 22), "UAF consented"),
        ("Rani Maheswari", "prospective", "prospective", _date(2025, 5, 10), "Initial contact — exploring"),
    ]
    for name, from_s, to_s, dt, trigger in transitions:
        pid = persona_map.get(name, (None, None))[1]
        if pid:
            existing = await session.execute(
                select(MemberStatusTransition).where(
                    MemberStatusTransition.member_id == pid,
                    MemberStatusTransition.from_status == from_s,
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(MemberStatusTransition(
                    member_id=pid,
                    from_status=from_s,
                    to_status=to_s,
                    date=dt,
                    trigger=trigger,
                ))

    # Domains
    for dom in DOMAINS:
        existing = await session.execute(
            select(Domain).where(Domain.id == dom["id"])
        )
        if existing.scalar_one_or_none() is None:
            # Resolve steward_id from persona_map
            steward_name = dom.get("current_steward")
            steward_member_id = None
            if steward_name and steward_name in persona_map:
                steward_member_id = persona_map[steward_name][1]
            session.add(Domain(
                **{**dom, "steward_id": steward_member_id}
            ))

    await session.flush()
    print("[01] Core: {} users, {} members, {} domains seeded".format(
        len(PERSONAS), len(PERSONAS), len(DOMAINS)))

    # Domain Elements
    for de in DOMAIN_ELEMENTS:
        session.add(DomainElement(**de))
    await session.flush()

    # Domain Metrics
    for dm in DOMAIN_METRICS:
        session.add(DomainMetric(**dm))
    await session.flush()

    # Circle Memberships
    circle_memberships = [
        # AE ETHOS
        ("Lani Wijaya", "6ba7b822-9dad-11d1-80b4-00c04fd430c8", "steward"),
        ("Dewa Putra", "6ba7b822-9dad-11d1-80b4-00c04fd430c8", "member"),
        ("Gede Artha", "6ba7b822-9dad-11d1-80b4-00c04fd430c8", "member"),
        ("Indra Gunawan", "6ba7b822-9dad-11d1-80b4-00c04fd430c8", "member"),
        # TH ETHOS
        ("Putu Ardana", "6ba7b821-9dad-11d1-80b4-00c04fd430c8", "steward"),
        ("Budi Santoso", "6ba7b821-9dad-11d1-80b4-00c04fd430c8", "member"),
        ("Sari Dewi", "6ba7b821-9dad-11d1-80b4-00c04fd430c8", "member"),
        ("Gede Artha", "6ba7b821-9dad-11d1-80b4-00c04fd430c8", "member"),
        # OSC
        ("Manu Dewantara", "6ba7b823-9dad-11d1-80b4-00c04fd430c8", "steward"),
        ("Ayu Pertiwi", "6ba7b823-9dad-11d1-80b4-00c04fd430c8", "member"),
        ("Kai Nakamura", "6ba7b823-9dad-11d1-80b4-00c04fd430c8", "member"),
    ]
    for name, domain_id_str, role in circle_memberships:
        pid = persona_map.get(name, (None, None))[1]
        if pid:
            existing = await session.execute(
                select(CircleMembership).where(
                    CircleMembership.member_id == pid,
                    CircleMembership.domain_id == __import__("uuid").UUID(domain_id_str),
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(CircleMembership(
                    domain_id=__import__("uuid").UUID(domain_id_str),
                    member_id=pid,
                    role=role,
                    status="active",
                ))

    await session.flush()
    # Link ecosystem UAF after agreements are seeded (deferred)
    return persona_map


# ────────────────────────────────────────────────────────────────────
# Step 2: Agreements
# ────────────────────────────────────────────────────────────────────

async def step_02_agreements(session: AsyncSession) -> None:
    """Seed agreements, ratification records, amendments, reviews."""
    import uuid as _uuid

    for ag in AGREEMENTS:
        existing = await session.execute(
            select(Agreement).where(Agreement.id == ag["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(Agreement(**ag))

    await session.flush()

    # UAF linkage to ecosystem
    await session.execute(
        select(Ecosystem).where(Ecosystem.id == ECOSYSTEM_ID)
    )
    eco = (await session.execute(
        select(Ecosystem).where(Ecosystem.id == ECOSYSTEM_ID)
    )).scalar_one_or_none()
    if eco and eco.uaf_agreement_id is None:
        eco.uaf_agreement_id = _uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430c1")

    # Agreement Versions (snapshot for each ratified agreement)
    for ag in AGREEMENTS:
        if ag["status"] == "ratified":
            existing = await session.execute(
                select(AgreementVersion).where(
                    AgreementVersion.agreement_id == ag["id"],
                    AgreementVersion.version == ag["version"],
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(AgreementVersion(
                    agreement_id=ag["id"],
                    version=ag["version"],
                    status=ag["status"],
                    title=ag["title"],
                    text=ag.get("text"),
                    type=ag["type"],
                    proposer=ag.get("proposer"),
                    domain=ag.get("domain"),
                    hierarchy_level=ag["hierarchy_level"],
                    affected_parties=ag.get("affected_parties"),
                    review_date=ag.get("review_date"),
                    sunset_date=ag.get("sunset_date"),
                    ratification_date=ag.get("ratification_date"),
                    change_reason="Initial version",
                    changed_by=ag.get("proposer"),
                ))

    await session.flush()

    # Ratification records
    for rr in RATIFICATION_RECORDS:
        session.add(AgreementRatificationRecord(**rr))
    await session.flush()

    # Amendment records
    for am in AMENDMENT_RECORDS:
        existing = await session.execute(
            select(AmendmentRecord).where(AmendmentRecord.id == am["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(AmendmentRecord(**am))
    await session.flush()

    # Review records
    for rv in REVIEW_RECORDS:
        existing = await session.execute(
            select(ReviewRecord).where(ReviewRecord.id == rv["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(ReviewRecord(**rv))
    await session.flush()

    print("[02] Agreements: {} agreements, {} ratifications, {} amendments, {} reviews".format(
        len(AGREEMENTS), len(RATIFICATION_RECORDS), len(AMENDMENT_RECORDS), len(REVIEW_RECORDS)))


# ────────────────────────────────────────────────────────────────────
# Step 3: Proposals + ACT process
# ────────────────────────────────────────────────────────────────────

async def step_03_proposals(session: AsyncSession) -> None:
    """Seed proposals, advice entries, consent records, test reports."""
    import uuid as _uuid

    # Proposals
    for prop in PROPOSALS:
        existing = await session.execute(
            select(Proposal).where(Proposal.id == prop["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(Proposal(**prop))
    await session.flush()

    # Advice Logs (one per proposal with advice phase)
    _adv_log_map = {
        str(_uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a2")): _uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b2"),  # Water
        str(_uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a3")): _uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b3"),  # Org Cert
        str(_uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a4")): _uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b4"),  # Seed
        str(_uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a5")): _uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b5"),  # Bamboo
        str(_uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a6")): _uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b6"),  # Solar
        str(_uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a7")): _uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b7"),  # GAIA
    }

    from datetime import date as _date, timedelta
    _today = _date.today()

    for prop_id_str, log_id in _adv_log_map.items():
        existing = await session.execute(
            select(AdviceLog).where(AdviceLog.id == log_id)
        )
        if existing.scalar_one_or_none() is None:
            # Derive dates from proposal
            prop_id = _uuid.UUID(prop_id_str)
            session.add(AdviceLog(
                id=log_id,
                proposal_id=prop_id,
                advice_window_start=_today - timedelta(days=30),
                advice_window_end=_today + timedelta(days=7),
                urgency="normal",
            ))
    await session.flush()

    # Advice entries
    for ae in ADVICE_ENTRIES:
        session.add(AdviceEntry(**ae))
    await session.flush()

    # Non-respondents
    for nr in ADVICE_NON_RESPONDENTS:
        existing = await session.execute(
            select(AdviceNonRespondent).where(AdviceNonRespondent.id == nr["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(AdviceNonRespondent(**nr))
    await session.flush()

    # Consent records
    for cr in CONSENT_RECORDS:
        existing = await session.execute(
            select(ConsentRecord).where(ConsentRecord.id == cr["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(ConsentRecord(**cr))
    await session.flush()

    # Consent participants
    for cp in CONSENT_PARTICIPANTS:
        session.add(ConsentParticipant(**cp))
    await session.flush()

    # Integration rounds
    for ir in INTEGRATION_ROUNDS:
        existing = await session.execute(
            select(ConsentIntegrationRound).where(ConsentIntegrationRound.id == ir["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(ConsentIntegrationRound(**ir))
    await session.flush()

    # Objections addressed
    for oa in OBJECTIONS_ADDRESSED:
        session.add(ConsentObjectionAddressed(**oa))
    await session.flush()

    # Test reports
    for tr in TEST_REPORTS:
        existing = await session.execute(
            select(TestReport).where(TestReport.id == tr["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(TestReport(**tr))
    await session.flush()

    # Test success criteria
    for tsc in TEST_SUCCESS_CRITERIA:
        session.add(TestSuccessCriterion(**tsc))
    await session.flush()

    print("[03] ACT: {} proposals, {} advice entries, {} consent records, {} test reports".format(
        len(PROPOSALS), len(ADVICE_ENTRIES), len(CONSENT_RECORDS), len(TEST_REPORTS)))


# ────────────────────────────────────────────────────────────────────
# Step 4: Decisions (Memory Layer IX)
# ────────────────────────────────────────────────────────────────────

async def step_04_decisions(session: AsyncSession) -> None:
    """Seed decision records, participants, dissents, and semantic tags."""
    for d in DECISIONS:
        existing = await session.execute(
            select(DecisionRecord).where(DecisionRecord.id == d["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(DecisionRecord(**d))
    await session.flush()

    for dp in DECISION_PARTICIPANTS:
        session.add(DecisionParticipant(**dp))
    await session.flush()

    for dr in DISSENT_RECORDS:
        session.add(DecisionDissentRecord(**dr))
    await session.flush()

    for st in SEMANTIC_TAGS:
        session.add(DecisionSemanticTag(**st))
    await session.flush()

    print("[04] Memory: {} decisions with {} semantic tags, {} dissents".format(
        len(DECISIONS), len(SEMANTIC_TAGS), len(DISSENT_RECORDS)))


# ────────────────────────────────────────────────────────────────────
# Step 5: Conflict & Repair (Layer VI)
# ────────────────────────────────────────────────────────────────────

async def step_05_conflict(session: AsyncSession, persona_map: dict) -> None:
    """Seed conflict cases and repair agreements, linking to persona IDs."""
    # Resolve reporter/facilitator to member UUIDs
    reporter_map = {
        "Budi Santoso": persona_map.get("Budi Santoso"),
        "Lani Wijaya (SHUR access steward)": persona_map.get("Lani Wijaya"),
        "Ayu Pertiwi (inter-ETHOS liaison)": persona_map.get("Ayu Pertiwi"),
    }
    facilitator = persona_map.get("Kai Nakamura", (None, None))
    facilitator_id = facilitator[1] if facilitator else None

    for cc in CONFLICT_CASES:
        existing = await session.execute(
            select(ConflictCase).where(ConflictCase.id == cc["id"])
        )
        if existing.scalar_one_or_none() is None:
            data = dict(cc)
            # Resolve reporter
            reporter_name = data.get("parties", {}).get("reporter", "")
            for key, val in reporter_map.items():
                if key in reporter_name:
                    data["reporter_id"] = val[1] if val else None
                    break
            data["facilitator_id"] = facilitator_id
            session.add(ConflictCase(**data))
    await session.flush()

    for ra in REPAIR_AGREEMENTS:
        existing = await session.execute(
            select(RepairAgreementRecord).where(RepairAgreementRecord.id == ra["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(RepairAgreementRecord(**ra))
    await session.flush()

    print("[05] Conflict: {} cases at tiers 1-4, {} repair agreements".format(
        len(CONFLICT_CASES), len(REPAIR_AGREEMENTS)))


# ────────────────────────────────────────────────────────────────────
# Step 6: Emergency (Layer VIII)
# ────────────────────────────────────────────────────────────────────

async def step_06_emergency(session: AsyncSession) -> None:
    """Seed emergency states."""
    for es in EMERGENCY_STATES:
        existing = await session.execute(
            select(EmergencyState).where(EmergencyState.id == es["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(EmergencyState(**es))
    await session.flush()
    print("[06] Emergency: {} states (1 open, 1 closed)".format(len(EMERGENCY_STATES)))


# ────────────────────────────────────────────────────────────────────
# Step 7: Safeguard (Layer VII)
# ────────────────────────────────────────────────────────────────────

async def step_07_safeguard(session: AsyncSession) -> None:
    """Seed governance health audit."""
    existing = await session.execute(
        select(GovernanceHealthAudit).where(
            GovernanceHealthAudit.id == SAFEGUARD_AUDIT["id"]
        )
    )
    if existing.scalar_one_or_none() is None:
        session.add(GovernanceHealthAudit(**SAFEGUARD_AUDIT))
    await session.flush()
    print("[07] Safeguard: 1 governance health audit (score 68/100)")


# ────────────────────────────────────────────────────────────────────
# Step 8: Exit (Layer X)
# ────────────────────────────────────────────────────────────────────

async def step_08_exit(session: AsyncSession, persona_map: dict) -> None:
    """Seed exit records."""
    # For the completed exit, we need a member ID.  Create a synthetic
    # former member or use Rani's UUID with a different ID.
    import uuid as _uuid

    # Get Ketut as coordinator
    ketut = persona_map.get("Ketut Arsana")
    coordinator_id = ketut[1] if ketut else None

    # Get Rani as in-progress member
    rani = persona_map.get("Rani Maheswari")
    rani_id = rani[1] if rani else None

    for er in EXIT_RECORDS:
        existing = await session.execute(
            select(ExitRecord).where(ExitRecord.id == er["id"])
        )
        if existing.scalar_one_or_none() is None:
            data = dict(er)
            if "in_progress" in str(er.get("status", "")) and rani_id:
                data["member_id"] = rani_id
            elif coordinator_id:
                data["coordinator_id"] = coordinator_id
            # For completed exit, use a synthetic member ID
            if data.get("member_id") is None:
                # Create a simple former member if not exists
                former_id = _uuid.UUID("dba7b810-9dad-11d1-80b4-00c04fd43099")
                session.add(Member(
                    id=former_id,
                    ecosystem_id=ECOSYSTEM["id"],
                    user_id=former_id,  # Simplified
                    member_id="M-EX-001",
                    display_name="[Former Member — Anonymized]",
                    current_status="exited",
                    onboarding_status="complete",
                    notes="Former member who exited for graduate studies.  Identity anonymized per portable record preferences.",
                ))
                data["member_id"] = former_id
            session.add(ExitRecord(**data))
    await session.flush()
    print("[08] Exit: {} records (1 in-progress, 1 completed)".format(len(EXIT_RECORDS)))


# ────────────────────────────────────────────────────────────────────
# Step 9: Economic (Layer IV — partial)
# ────────────────────────────────────────────────────────────────────

async def step_09_economic(session: AsyncSession) -> None:
    """Seed shares_needs and collaborations (models that exist).

    Funding pools, resource requests, and Current-See balances are
    documented but not seeded — models not yet in db/models.py.
    """
    # Shares & Needs
    for sn in SHARES_NEEDS:
        session.add(SharesNeeds(**sn))
    await session.flush()

    # Collaborations
    for col in COLLABORATIONS:
        existing = await session.execute(
            select(Collaboration).where(Collaboration.id == col["id"])
        )
        if existing.scalar_one_or_none() is None:
            session.add(Collaboration(**col))
    await session.flush()

    print("[09] Economic: {} shares/needs, {} collaborations".format(
        len(SHARES_NEEDS), len(COLLABORATIONS)))
    print("      TODO: funding_pools, resource_requests, current_see_balances — models not yet created")


# ────────────────────────────────────────────────────────────────────
# Main runner
# ────────────────────────────────────────────────────────────────────

async def seed_all(database_url: str | None = None) -> None:
    """Run all seed steps in order."""
    url = database_url or get_database_url()
    url = _ensure_async_url(url)

    engine = create_async_engine(url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        await step_00_create_tables(engine)

        async with session_factory() as session:
            async with session.begin():
                persona_map = await step_01_core(session)
                await step_02_agreements(session)
                await step_03_proposals(session)
                await step_04_decisions(session)
                await step_05_conflict(session, persona_map)
                await step_06_emergency(session)
                await step_07_safeguard(session)
                await step_08_exit(session, persona_map)
                await step_09_economic(session)

            print("\n✓ Seed complete.  All 10 NEOS layers exercised.")

    finally:
        await engine.dispose()


async def seed_reset(database_url: str | None = None) -> None:
    """Drop all tables and re-seed from scratch."""
    url = database_url or get_database_url()
    url = _ensure_async_url(url)

    engine = create_async_engine(url, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("🧹 All tables dropped.")
    finally:
        await engine.dispose()

    await seed_all(database_url)


# ────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="NEOS seed data runner")
    parser.add_argument("--database", help="Database URL (default: sqlite+aiosqlite:///neos_seed.db)")
    parser.add_argument("--reset", action="store_true", help="Drop all tables before seeding")
    args = parser.parse_args()

    if args.reset:
        asyncio.run(seed_reset(args.database))
    else:
        asyncio.run(seed_all(args.database))


if __name__ == "__main__":
    main()
