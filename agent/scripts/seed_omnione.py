"""Seed the database with comprehensive OmniOne ecosystem data for testing.

Usage:
    python -m agent.scripts.seed_omnione            # seed (idempotent)
    python -m agent.scripts.seed_omnione --purge     # drop all data then reseed

Reads DATABASE_URL from environment or .env file.
Idempotent: running twice does not create duplicates (unless --purge).

Seeds ALL 31 entity types (excludes AgentSession, AuthSession, AuthChallenge):
  Core (7):             Ecosystem, Member, MemberOnboarding, MemberStatusTransition,
                        Domain, DomainElement, DomainMetric
  Agreements (4):       Agreement, AgreementRatificationRecord, AmendmentRecord, ReviewRecord
  ACT (10):             Proposal, AdviceLog, AdviceEntry, AdviceNonRespondent,
                        ConsentRecord, ConsentParticipant, ConsentIntegrationRound,
                        ConsentObjectionAddressed, TestReport, TestSuccessCriterion
  Memory (4):           DecisionRecord, DecisionDissentRecord, DecisionParticipant,
                        DecisionSemanticTag
  Conflict & Repair (3): ConflictCase, RepairAgreementRecord, GovernanceHealthAudit
  Emergency (1):        EmergencyState
  Exit (1):             ExitRecord
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
    # Core
    Ecosystem,
    Member,
    MemberOnboarding,
    MemberStatusTransition,
    Domain,
    DomainElement,
    DomainMetric,
    # Agreements
    Agreement,
    AgreementRatificationRecord,
    AmendmentRecord,
    ReviewRecord,
    # ACT Process
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
    # Memory
    DecisionRecord,
    DecisionDissentRecord,
    DecisionParticipant,
    DecisionSemanticTag,
    # Conflict & Repair
    ConflictCase,
    RepairAgreementRecord,
    GovernanceHealthAudit,
    # Emergency
    EmergencyState,
    # Exit
    ExitRecord,
)


# ---------------------------------------------------------------------------
# Date helpers: spread seed data over the last 30 days
# ---------------------------------------------------------------------------
TODAY = date.today()
NOW = datetime.utcnow()


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def days_from_now(n: int) -> date:
    return TODAY + timedelta(days=n)


def hours_ago(n: int) -> datetime:
    return NOW - timedelta(hours=n)


# ---------------------------------------------------------------------------
# Purge function — delete all rows from all tables (reverse FK order)
# ---------------------------------------------------------------------------
# Tables ordered so children are deleted before parents (reverse of creation).
PURGE_ORDER = [
    "auth_challenges",
    "auth_sessions",
    "agent_sessions",
    "exit_records",
    "emergency_states",
    "governance_health_audits",
    "repair_agreement_records",
    "conflict_cases",
    "decision_semantic_tags",
    "decision_participants",
    "decision_dissent_records",
    "decision_records",
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
    "review_records",
    "amendment_records",
    "agreement_ratification_records",
    "agreements",
    "domain_metrics",
    "domain_elements",
    "domains",
    "member_status_transitions",
    "member_onboarding",
    "members",
    "ecosystems",
]


async def purge(database_url: str) -> None:
    """Delete all rows from all tables in reverse FK order.

    Creates missing tables first via metadata.create_all, then truncates.
    """
    engine = create_async_engine(database_url)

    # Ensure all tables exist before purging
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine.begin() as conn:
        for table in PURGE_ORDER:
            await conn.execute(text(f'DELETE FROM "{table}"'))
        print(f"Purged all data from {len(PURGE_ORDER)} tables.")

    await engine.dispose()


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
async def seed(database_url: str) -> None:
    """Create comprehensive seed data in the database."""
    engine = create_async_engine(database_url)

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # ---------------------------------------------------------------
        # Idempotency check
        # ---------------------------------------------------------------
        result = await session.execute(
            select(Ecosystem).where(Ecosystem.name == "OmniOne")
        )
        if result.scalar_one_or_none() is not None:
            print("OmniOne ecosystem already exists. Skipping seed.")
            await engine.dispose()
            return

        # ===============================================================
        # 1. ECOSYSTEM
        # ===============================================================
        ecosystem_id = uuid.uuid4()
        ecosystem = Ecosystem(
            id=ecosystem_id,
            name="OmniOne",
            description=(
                "First NEOS ecosystem, stewarded by Green Earth Vision (GEV). "
                "Located at SHUR regenerative community in Bali."
            ),
            status="active",
            location="Bali, Indonesia",
            website="https://omnione.earth",
            founded_date=days_ago(180),
            tags=["regenerative", "agriculture", "community", "governance"],
            contact_email="hello@omnione.earth",
            governance_summary=(
                "Consent-based decision-making using the ACT process "
                "(Advice, Consent, Test). Domain stewards hold delegated "
                "authority within S3-structured governance boundaries. "
                "GAIA 6-level escalation model for conflict resolution."
            ),
            visibility="public",
        )
        session.add(ecosystem)
        await session.flush()  # Ecosystem must exist before FK refs

        # ===============================================================
        # 2. MEMBERS (6 with varied statuses and profiles)
        # ===============================================================
        member_ids = {name: uuid.uuid4() for name in [
            "Manu", "Lani", "Kai", "Aroha", "Tane", "Hina"
        ]}

        members_spec = [
            # (name, member_id_str, status, profile, kyc, onboarding_status, notes, gov_activity_days_ago, skills_offered, skills_needed)
            ("Manu", "mem-osc-001", "active", "co_creator", "verified", "complete",
             "OSC co-creator and founding steward", 1,
             ["governance-design", "facilitation", "conflict-resolution"],
             ["permaculture", "digital-tools"]),
            ("Lani", "mem-ae-001", "active", "builder", "verified", "complete",
             "SHUR Kitchen domain steward and AE builder", 2,
             ["kitchen-management", "food-safety", "community-cooking"],
             ["accounting", "grant-writing"]),
            ("Kai", "mem-th-001", "active", "townhall", "verified", "complete",
             "Town Hall participant, active in governance proposals", 3,
             ["carpentry", "construction", "workshop-facilitation"],
             ["digital-literacy"]),
            ("Aroha", "mem-ae-002", "active", "builder", "verified", "complete",
             "Garden domain steward, AE builder focused on food systems", 5,
             ["permaculture", "composting", "seed-saving"],
             ["facilitation"]),
            ("Tane", "mem-th-002", "onboarding", "townhall", "pending", "in_progress",
             "New townhall member, currently in onboarding cooling-off period", None,
             ["solar-energy", "electrical-systems"],
             ["governance-basics", "consent-process"]),
            ("Hina", "mem-prospective-001", "prospective", None, None, None,
             "Prospective member, expressed interest in joining SHUR community", None,
             None, None),
        ]

        member_objs = {}
        for name, mid, status, profile, kyc, onb_status, notes, gov_days, skills_o, skills_n in members_spec:
            m = Member(
                id=member_ids[name],
                ecosystem_id=ecosystem_id,
                member_id=mid,
                display_name=name,
                current_status=status,
                profile=profile,
                kyc_status=kyc,
                onboarding_status=onb_status,
                notes=notes,
                last_governance_activity_date=days_ago(gov_days) if gov_days else None,
                skills_offered=skills_o,
                skills_needed=skills_n,
            )
            session.add(m)
            member_objs[name] = m

        await session.flush()  # Members must exist for onboarding/domain FKs

        # ===============================================================
        # 3. MEMBER ONBOARDING (one per member, varied completion %)
        # ===============================================================
        onboarding_spec = [
            # (member_name, facilitator, mentor_name, uaf_ver, consent_date_days_ago, cool_start, cool_end, completion%, section_consents, checklist)
            ("Manu", "System", None, "1.0", 28, 28, 21, 100,
             {"principles": True, "agreements": True, "roles": True, "exit": True},
             {"uaf_read": True, "mentor_assigned": True, "first_governance": True, "cooling_off_complete": True}),
            ("Lani", "Manu", "Manu", "1.0", 25, 25, 18, 100,
             {"principles": True, "agreements": True, "roles": True, "exit": True},
             {"uaf_read": True, "mentor_assigned": True, "first_governance": True, "cooling_off_complete": True}),
            ("Kai", "Manu", "Lani", "1.0", 22, 22, 15, 100,
             {"principles": True, "agreements": True, "roles": True, "exit": True},
             {"uaf_read": True, "mentor_assigned": True, "first_governance": True, "cooling_off_complete": True}),
            ("Aroha", "Lani", "Manu", "1.0", 20, 20, 13, 100,
             {"principles": True, "agreements": True, "roles": True, "exit": True},
             {"uaf_read": True, "mentor_assigned": True, "first_governance": True, "cooling_off_complete": True}),
            ("Tane", "Kai", "Aroha", "1.0", 5, 5, None, 60,
             {"principles": True, "agreements": True, "roles": False, "exit": False},
             {"uaf_read": True, "mentor_assigned": True, "first_governance": False, "cooling_off_complete": False}),
            ("Hina", None, None, None, None, None, None, 0,
             None, None),
        ]

        for name, fac, mentor_name, uaf_v, cd, cs, ce, pct, sc, cl in onboarding_spec:
            onb = MemberOnboarding(
                id=uuid.uuid4(),
                member_id=member_ids[name],
                facilitator=fac,
                mentor_id=member_ids[mentor_name] if mentor_name else None,
                uaf_version_consented=uaf_v,
                consent_date=days_ago(cd) if cd else None,
                cooling_off_start=days_ago(cs) if cs else None,
                cooling_off_end=days_ago(ce) if ce else None,
                completion_percentage=pct,
                section_consents=sc,
                checklist_items=cl,
            )
            session.add(onb)

        # ===============================================================
        # 4. MEMBER STATUS TRANSITIONS (history per member)
        # ===============================================================
        transitions_spec = [
            # Manu: prospective -> onboarding -> active (founder fast-track)
            ("Manu", "prospective", "onboarding", 30, "seed_founding", "Founding member"),
            ("Manu", "onboarding", "active", 21, "onboarding_complete", "Founding member fast-track"),
            # Lani: prospective -> onboarding -> active
            ("Lani", "prospective", "onboarding", 27, "application_accepted", None),
            ("Lani", "onboarding", "active", 18, "onboarding_complete", None),
            # Kai: prospective -> onboarding -> active
            ("Kai", "prospective", "onboarding", 24, "application_accepted", None),
            ("Kai", "onboarding", "active", 15, "onboarding_complete", None),
            # Aroha: prospective -> onboarding -> active
            ("Aroha", "prospective", "onboarding", 22, "application_accepted", None),
            ("Aroha", "onboarding", "active", 13, "onboarding_complete", None),
            # Tane: prospective -> onboarding (still onboarding)
            ("Tane", "prospective", "onboarding", 6, "application_accepted", "Awaiting cooling-off completion"),
            # Hina: no transitions yet (still prospective)
        ]

        for name, from_s, to_s, d, trigger, notes in transitions_spec:
            t = MemberStatusTransition(
                id=uuid.uuid4(),
                member_id=member_ids[name],
                from_status=from_s,
                to_status=to_s,
                date=days_ago(d),
                trigger=trigger,
                notes=notes,
            )
            session.add(t)

        await session.flush()  # Members + transitions done

        # ===============================================================
        # 5. DOMAINS (4 domains, one nested)
        # ===============================================================
        kitchen_id = uuid.uuid4()
        garden_id = uuid.uuid4()
        workshop_id = uuid.uuid4()
        energy_id = uuid.uuid4()

        domains_spec = [
            (kitchen_id, "dom-shur-kitchen-001", "active",
             "Manage communal kitchen operations, meal scheduling, and food safety compliance",
             "Lani", member_ids["Lani"], None, "Manu"),
            (garden_id, "dom-shur-garden-001", "active",
             "Manage garden operations, composting, crop rotation, and seed library",
             "Aroha", member_ids["Aroha"], None, "Lani"),
            (workshop_id, "dom-shur-workshop-001", "active",
             "Coordinate shared workshop space, tool maintenance, and building projects",
             "Kai", member_ids["Kai"], None, "Manu"),
            (energy_id, "dom-shur-energy-001", "active",
             "Solar panel management, battery maintenance, and energy distribution (sub-domain of Workshop)",
             "Tane", member_ids["Tane"], workshop_id, "Kai"),
        ]

        domain_objs = {}
        for did, domain_id, status, purpose, steward, steward_uuid, parent, creator in domains_spec:
            d = Domain(
                id=did,
                ecosystem_id=ecosystem_id,
                domain_id=domain_id,
                version="1.0",
                status=status,
                purpose=purpose,
                current_steward=steward,
                steward_id=steward_uuid,
                parent_domain_id=parent,
                created_by=creator,
            )
            session.add(d)
            domain_objs[domain_id] = d

        await session.flush()  # Domains must exist for elements/metrics FKs

        # ===============================================================
        # 6. DOMAIN ELEMENTS (2-3 per domain)
        # ===============================================================
        elements_spec = [
            # Kitchen
            (kitchen_id, "meal_schedule", {"type": "schedule", "frequency": "daily", "slots": ["breakfast", "lunch", "dinner"]}),
            (kitchen_id, "hygiene_standards", {"type": "policy", "inspection_frequency": "weekly", "responsible": "steward"}),
            (kitchen_id, "inventory_tracking", {"type": "process", "tool": "shared_spreadsheet", "reorder_threshold": "3_days_supply"}),
            # Garden
            (garden_id, "crop_plan", {"type": "plan", "season": "wet_2026", "beds_active": 12, "beds_fallow": 4}),
            (garden_id, "compost_system", {"type": "process", "bins": 3, "cycle_weeks": 8}),
            # Workshop
            (workshop_id, "tool_registry", {"type": "inventory", "total_tools": 47, "requiring_maintenance": 5}),
            (workshop_id, "safety_protocols", {"type": "policy", "induction_required": True, "fire_extinguishers": 2}),
            (workshop_id, "project_queue", {"type": "queue", "active_projects": 3, "pending": 2}),
            # Energy
            (energy_id, "solar_array", {"type": "asset", "panels": 24, "capacity_kw": 9.6, "installed": "2025-11"}),
            (energy_id, "battery_bank", {"type": "asset", "units": 4, "capacity_kwh": 40, "health_pct": 92}),
        ]

        for dom_id, name, value in elements_spec:
            session.add(DomainElement(
                id=uuid.uuid4(),
                domain_id=dom_id,
                element_name=name,
                element_value=value,
            ))

        # ===============================================================
        # 7. DOMAIN METRICS (1-2 per domain)
        # ===============================================================
        metrics_spec = [
            (kitchen_id, "Meals served per week", ">=80", "Weekly count from meal sign-up sheet"),
            (kitchen_id, "Food waste reduction %", "<=10% by weight", "Weekly weigh-in of compostable waste vs food purchased"),
            (garden_id, "Harvest yield (kg/week)", ">=30 kg", "Weigh at harvest, log in shared tracker"),
            (garden_id, "Compost cycle completion rate", ">=90%", "Track bins turned on schedule"),
            (workshop_id, "Tool availability rate", ">=95%", "Monthly inventory audit vs checkout log"),
            (energy_id, "Energy self-sufficiency %", ">=70%", "Monthly kWh generated vs consumed from grid meter"),
            (energy_id, "Battery health score", ">=85%", "Quarterly diagnostic from inverter dashboard"),
        ]

        for dom_id, metric, target, method in metrics_spec:
            session.add(DomainMetric(
                id=uuid.uuid4(),
                domain_id=dom_id,
                metric=metric,
                target=target,
                measurement_method=method,
            ))

        await session.flush()  # Elements + metrics must exist before agreements

        # ===============================================================
        # 8. AGREEMENTS (5 with varied types and statuses)
        # ===============================================================
        uaf_id = uuid.uuid4()
        agr_kitchen_id = uuid.uuid4()
        agr_garden_id = uuid.uuid4()
        agr_review_id = uuid.uuid4()
        agr_draft_id = uuid.uuid4()

        agreements_spec = [
            # UAF (universal, active)
            (uaf_id, "agr-omnione-uaf-001", "uaf",
             "OmniOne Universal Agreement Field", "1.0", "active",
             "Manu", None, "universal", None, None,
             "The foundational agreement defining OmniOne's shared principles, "
             "governance architecture, and member rights and responsibilities.",
             days_ago(28), days_ago(28), days_from_now(152), None,
             {"all_members": True}),
            # Kitchen operational agreement (domain, active)
            (agr_kitchen_id, "agr-shur-kitchen-001", "operational",
             "SHUR Kitchen Operations Agreement", "1.0", "active",
             "Lani", "SHUR Kitchen", "domain", uaf_id, None,
             "Defines meal scheduling, hygiene standards, cost-sharing, "
             "and cleanup rotation for the SHUR communal kitchen.",
             days_ago(20), days_ago(18), days_from_now(162), None,
             {"affected": ["kitchen_users", "AE_builders"]}),
            # Garden domain agreement (domain, active)
            (agr_garden_id, "agr-shur-garden-001", "domain",
             "SHUR Garden Stewardship Agreement", "1.0", "active",
             "Aroha", "SHUR Garden", "domain", uaf_id, None,
             "Governs crop planning, compost management, seed library access, "
             "and volunteer scheduling for the SHUR Garden domain.",
             days_ago(18), days_ago(15), days_from_now(165), None,
             {"affected": ["garden_volunteers", "AE_builders"]}),
            # Policy under review
            (agr_review_id, "agr-omnione-guest-001", "policy",
             "Guest and Visitor Policy", "1.0", "under_review",
             "Kai", None, "universal", uaf_id, None,
             "Policy governing short-term guests, visitor day-passes, "
             "and temporary participation rights within OmniOne.",
             days_ago(14), days_ago(10), None, days_from_now(30),
             {"affected": ["all_members", "visitors"]}),
            # Draft agreement
            (agr_draft_id, "agr-shur-energy-001", "operational",
             "SHUR Energy Distribution Agreement", "0.1", "draft",
             "Tane", "SHUR Energy", "domain", uaf_id, None,
             "Draft agreement for fair energy distribution, usage metering, "
             "and maintenance cost-sharing for the solar/battery system.",
             days_ago(3), None, None, None,
             {"affected": ["energy_users", "workshop_members"]}),
        ]

        for (aid, agr_id, atype, title, ver, status, proposer, domain_name,
             hier, parent, review_dt, text_val, created, ratified, review_date, sunset,
             affected) in agreements_spec:
            session.add(Agreement(
                id=aid,
                ecosystem_id=ecosystem_id,
                agreement_id=agr_id,
                type=atype,
                title=title,
                version=ver,
                status=status,
                proposer=proposer,
                domain=domain_name,
                hierarchy_level=hier,
                parent_agreement_id=parent,
                text=text_val,
                created_date=created,
                ratification_date=ratified,
                review_date=review_date,
                sunset_date=sunset,
                affected_parties=affected,
            ))

        # Set UAF reference on ecosystem
        ecosystem.uaf_agreement_id = uaf_id

        await session.flush()  # Agreements must exist before ratification/amendment/review FKs

        # ===============================================================
        # 9. AGREEMENT RATIFICATION RECORDS (for active agreements)
        # ===============================================================
        ratifications = [
            # UAF ratified by all active founding members
            (uaf_id, "Manu", "co_creator", "consent", days_ago(28)),
            (uaf_id, "Lani", "builder", "consent", days_ago(28)),
            (uaf_id, "Kai", "townhall", "consent", days_ago(28)),
            (uaf_id, "Aroha", "builder", "consent", days_ago(28)),
            # Kitchen agreement
            (agr_kitchen_id, "Lani", "domain_steward", "consent", days_ago(18)),
            (agr_kitchen_id, "Manu", "co_creator", "consent", days_ago(18)),
            (agr_kitchen_id, "Kai", "townhall", "consent", days_ago(18)),
            # Garden agreement
            (agr_garden_id, "Aroha", "domain_steward", "consent", days_ago(15)),
            (agr_garden_id, "Lani", "builder", "consent", days_ago(15)),
            (agr_garden_id, "Manu", "co_creator", "consent", days_ago(15)),
        ]

        for agr, participant, role, position, dt in ratifications:
            session.add(AgreementRatificationRecord(
                id=uuid.uuid4(),
                agreement_id=agr,
                participant=participant,
                role=role,
                position=position,
                date=dt,
            ))

        # ===============================================================
        # 10. AMENDMENT RECORDS (2: one approved, one proposed)
        # ===============================================================
        session.add(AmendmentRecord(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            amendment_id="amd-kitchen-001",
            parent_agreement_id=agr_kitchen_id,
            parent_agreement_version="1.0",
            amendment_type="minor",
            proposed_by="Kai",
            date=days_ago(10),
            changes={"section": "cleanup_rotation", "change": "Added Sunday deep-clean shift"},
            rationale="Weekend meals create more mess; need dedicated deep-clean slot.",
            act_level_used="consent",
            new_agreement_version="1.1",
            status="approved",
        ))

        session.add(AmendmentRecord(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            amendment_id="amd-garden-001",
            parent_agreement_id=agr_garden_id,
            parent_agreement_version="1.0",
            amendment_type="major",
            proposed_by="Aroha",
            date=days_ago(2),
            changes={"section": "seed_library", "change": "Expand seed library to include medicinal herbs"},
            rationale="Community request for medicinal herb garden section.",
            act_level_used="advice",
            status="proposed",
        ))

        # ===============================================================
        # 11. REVIEW RECORDS (2: one completed, one upcoming)
        # ===============================================================
        session.add(ReviewRecord(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            review_id="rev-kitchen-001",
            agreement_id=agr_kitchen_id,
            agreement_version="1.0",
            review_type="scheduled",
            trigger="90-day review cycle",
            review_body={"members": ["Lani", "Manu", "Kai"], "facilitator": "Manu"},
            date=days_ago(5),
            evaluation={
                "effectiveness": "high",
                "compliance": "good",
                "issues": ["Breakfast slot underutilized", "Need more vegetarian options"],
            },
            outcome="continue_with_amendments",
            next_review_date=days_from_now(85),
            follow_up_actions=[
                {"action": "Survey breakfast preferences", "assigned": "Lani", "due": str(days_from_now(14))},
                {"action": "Add vegetarian menu rotation", "assigned": "Kai", "due": str(days_from_now(21))},
            ],
        ))

        session.add(ReviewRecord(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            review_id="rev-garden-001",
            agreement_id=agr_garden_id,
            agreement_version="1.0",
            review_type="scheduled",
            trigger="90-day review cycle",
            review_body={"members": ["Aroha", "Lani", "Manu"], "facilitator": "Lani"},
            date=days_from_now(15),
            outcome=None,
            next_review_date=None,
        ))

        await session.flush()  # Agreements + amendments + reviews before proposals

        # ===============================================================
        # 12. PROPOSALS (4 in different ACT phases)
        # ===============================================================
        prop_draft_id = uuid.uuid4()
        prop_advice_id = uuid.uuid4()
        prop_consent_id = uuid.uuid4()
        prop_testing_id = uuid.uuid4()

        proposals_spec = [
            # Draft phase
            (prop_draft_id, "prop-omnione-004", "operational", "consent",
             "Community Tool Library Expansion", "1.0", "draft",
             "Kai", "SHUR Workshop", None, None,
             "Expand the shared tool library with power tools and create a booking system.",
             "Current tools are insufficient for building projects. A booking system "
             "prevents conflicts and ensures maintenance.",
             days_ago(2), None, None, None,
             ["Tane"], {"checked": False}),
            # Advice phase
            (prop_advice_id, "prop-omnione-003", "policy", "consent",
             "Quiet Hours Policy for SHUR Community", "1.0", "advice",
             "Aroha", None, "standard", {"affected": ["all_members"]},
             "Establish quiet hours (10pm-7am) across all SHUR zones.",
             "Multiple members have raised concerns about late-night noise "
             "impacting sleep and early-morning garden work.",
             days_ago(8), days_ago(6), days_from_now(1), None,
             None, None),
            # Consent phase
            (prop_consent_id, "prop-omnione-002", "domain", "consent",
             "Composting Process Standardization", "1.2", "consent",
             "Aroha", "SHUR Garden", "standard", {"affected": ["garden_volunteers", "kitchen_users"]},
             "Standardize the 3-bin composting process with clear signage and training.",
             "Inconsistent composting practices are reducing compost quality and "
             "attracting pests. Training will improve outcomes.",
             days_ago(15), days_ago(12), days_ago(5), "30 days",
             None, {"checked": True, "no_conflicts": True}),
            # Testing phase
            (prop_testing_id, "prop-omnione-001", "operational", "consent",
             "Solar Panel Cleaning Schedule", "1.0", "testing",
             "Tane", "SHUR Energy", "standard", {"affected": ["energy_users"]},
             "Bi-weekly solar panel cleaning rotation to maintain energy output.",
             "Panel efficiency dropped 15% due to dust and debris buildup. "
             "Regular cleaning restores output to rated capacity.",
             days_ago(25), days_ago(22), days_ago(18), "30 days",
             None, {"checked": True, "no_conflicts": True}),
        ]

        for (pid, prop_id, ptype, dec_type, title, ver, status, proposer,
             domain_name, urgency, impacted, change, rationale, created,
             adv_start, consent_dl, test_dur, co_sponsors, synergy) in proposals_spec:
            session.add(Proposal(
                id=pid,
                ecosystem_id=ecosystem_id,
                proposal_id=prop_id,
                type=ptype,
                decision_type=dec_type,
                title=title,
                version=ver,
                status=status,
                proposer=proposer,
                affected_domain=domain_name,
                urgency=urgency,
                impacted_parties=impacted,
                proposed_change=change,
                rationale=rationale,
                created_date=created,
                advice_deadline=adv_start,
                consent_deadline=consent_dl,
                test_duration=test_dur,
                co_sponsors=co_sponsors,
                synergy_check=synergy,
            ))

        await session.flush()  # Proposals must exist before advice logs FK

        # ===============================================================
        # 13. ADVICE LOGS (for advice-phase and consent-phase proposals)
        # ===============================================================
        advice_log_quiet_id = uuid.uuid4()
        advice_log_compost_id = uuid.uuid4()

        session.add(AdviceLog(
            id=advice_log_quiet_id,
            proposal_id=prop_advice_id,
            advice_window_start=days_ago(6),
            advice_window_end=days_from_now(1),
            urgency="standard",
            summary="Gathering input on proposed quiet hours. Most responses supportive with "
                    "suggested modifications to weekend timing.",
            proposer_modifications=None,
        ))

        session.add(AdviceLog(
            id=advice_log_compost_id,
            proposal_id=prop_consent_id,
            advice_window_start=days_ago(12),
            advice_window_end=days_ago(8),
            urgency="standard",
            summary="Advice phase complete. Strong support with minor adjustments to bin labeling. "
                    "Proposer integrated feedback into v1.2.",
            proposer_modifications="Updated bin labels from numeric to color-coded system per Kai's suggestion. "
                                   "Added training schedule per Manu's advice.",
        ))

        await session.flush()  # Advice logs must exist before entries/non-respondents FK

        # ===============================================================
        # 14. ADVICE ENTRIES (2-3 per log, varied integration_status)
        # ===============================================================
        advice_entries_spec = [
            # Quiet hours advice log
            (advice_log_quiet_id, "Manu", "co_creator", "OSC", days_ago(5),
             "Support the policy but suggest 9:30pm start on weeknights to accommodate evening circles.",
             "Will consider the 9:30pm option for weeknights.",
             "integrated", "Weeknight adjustment aligns with existing circle schedule."),
            (advice_log_quiet_id, "Kai", "townhall", "SHUR Workshop", days_ago(4),
             "Workshop sometimes needs evening hours for time-sensitive projects. Request exception process.",
             "Good point. Will add an exception request clause for essential work.",
             "integrated", "Exception clause prevents rigidity while maintaining spirit of quiet hours."),
            (advice_log_quiet_id, "Lani", "builder", "SHUR Kitchen", days_ago(3),
             "Kitchen cleanup after dinner events can extend past 10pm. Need flexibility for kitchen domain.",
             "Acknowledged. Kitchen cleanup sounds are different from recreational noise.",
             "acknowledged", "Will note kitchen exception but not formally integrate yet pending further input."),
            # Compost advice log
            (advice_log_compost_id, "Kai", "townhall", "SHUR Workshop", days_ago(11),
             "Color-coded bins would be more intuitive than numbered bins. Can build them in workshop.",
             "Excellent idea. Will update proposal to use color-coded system.",
             "integrated", "Color-coding is more accessible, especially for visitors."),
            (advice_log_compost_id, "Manu", "co_creator", "OSC", days_ago(10),
             "Suggest adding a training requirement for new members as part of onboarding checklist.",
             "Agreed. Will add composting training to onboarding.",
             "integrated", "Prevents recurring knowledge gaps."),
            (advice_log_compost_id, "Lani", "builder", "SHUR Kitchen", days_ago(9),
             "Kitchen scraps container needs to be clearly differentiated from general waste.",
             None,
             "not_integrated", "Kitchen already has separate bins; adding another label may cause confusion."),
        ]

        for (log_id, advisor, role, ethos, dt, advice, response,
             integration, rationale) in advice_entries_spec:
            session.add(AdviceEntry(
                id=uuid.uuid4(),
                advice_log_id=log_id,
                advisor=advisor,
                role=role,
                ethos=ethos,
                date=dt,
                advice_text=advice,
                proposer_response=response,
                integration_status=integration,
                rationale=rationale,
            ))

        # ===============================================================
        # 15. ADVICE NON-RESPONDENTS (1-2 per log)
        # ===============================================================
        session.add(AdviceNonRespondent(
            id=uuid.uuid4(),
            advice_log_id=advice_log_quiet_id,
            name="Aroha",
            notified_date=days_ago(6),
            follow_up_sent=True,
        ))
        session.add(AdviceNonRespondent(
            id=uuid.uuid4(),
            advice_log_id=advice_log_quiet_id,
            name="Tane",
            notified_date=days_ago(6),
            follow_up_sent=False,
        ))
        session.add(AdviceNonRespondent(
            id=uuid.uuid4(),
            advice_log_id=advice_log_compost_id,
            name="Tane",
            notified_date=days_ago(12),
            follow_up_sent=True,
        ))

        await session.flush()  # Advice entries + non-respondents before consent records

        # ===============================================================
        # 16. CONSENT RECORDS (for consent-phase proposal)
        # ===============================================================
        consent_record_id = uuid.uuid4()
        session.add(ConsentRecord(
            id=consent_record_id,
            proposal_id=prop_consent_id,
            consent_mode="consent",
            weighting_model="affected_parties",
            facilitator="Manu",
            date=days_ago(5),
            quorum_required="75%",
            quorum_met=True,
            outcome="consent_with_integration",
            escalation_level=None,
            final_proposal_version="1.2",
        ))

        await session.flush()  # Consent record must exist before participants FK

        # ===============================================================
        # 17. CONSENT PARTICIPANTS (4 with varied positions)
        # ===============================================================
        consent_participants_spec = [
            ("Manu", "co_creator", "OSC", "consent", None, 1),
            ("Lani", "builder", "SHUR Kitchen", "consent",
             "Fully support standardization. Kitchen compost quality will improve.", 1),
            ("Aroha", "domain_steward", "SHUR Garden", "consent",
             "As domain steward, I confirm this addresses key quality issues.", 1),
            ("Kai", "townhall", "SHUR Workshop", "objection",
             "Training requirement is too rigid. Workshop volunteers may not have "
             "time for a full training session. Suggest a shorter orientation option.", 1),
        ]

        for name, role, ethos, position, reason, rnd in consent_participants_spec:
            session.add(ConsentParticipant(
                id=uuid.uuid4(),
                consent_record_id=consent_record_id,
                name=name,
                role=role,
                ethos=ethos,
                position=position,
                reason=reason,
                round=rnd,
            ))

        await session.flush()  # Consent participants before integration rounds

        # ===============================================================
        # 18. CONSENT INTEGRATION ROUNDS (2 rounds)
        # ===============================================================
        integration_round_1_id = uuid.uuid4()
        integration_round_2_id = uuid.uuid4()

        session.add(ConsentIntegrationRound(
            id=integration_round_1_id,
            consent_record_id=consent_record_id,
            round_number=1,
            modifications_made="Added 15-minute quick orientation option alongside full training session.",
            outcome="partial_resolution",
        ))

        session.add(ConsentIntegrationRound(
            id=integration_round_2_id,
            consent_record_id=consent_record_id,
            round_number=2,
            modifications_made="Clarified that quick orientation covers safety only; full training for "
                               "unsupervised composting. Kai withdrew objection.",
            outcome="all_objections_resolved",
        ))

        await session.flush()  # Integration rounds must exist before objections FK

        # ===============================================================
        # 19. CONSENT OBJECTIONS ADDRESSED
        # ===============================================================
        session.add(ConsentObjectionAddressed(
            id=uuid.uuid4(),
            integration_round_id=integration_round_1_id,
            objector="Kai",
            objection="Training requirement is too rigid for workshop volunteers with limited time.",
            resolution="Added 15-minute quick orientation as alternative to full 1-hour training.",
        ))

        session.add(ConsentObjectionAddressed(
            id=uuid.uuid4(),
            integration_round_id=integration_round_2_id,
            objector="Kai",
            objection="Remaining concern about unsupervised access after quick orientation.",
            resolution="Quick orientation grants supervised-only access. Full training required "
                       "for unsupervised composting. Objection withdrawn.",
        ))

        await session.flush()  # Objections before test reports

        # ===============================================================
        # 20. TEST REPORT (for testing-phase proposal)
        # ===============================================================
        test_report_id = uuid.uuid4()
        session.add(TestReport(
            id=test_report_id,
            proposal_id=prop_testing_id,
            test_start_date=days_ago(14),
            test_end_date=days_from_now(16),
            midpoint_checkin_date=days_ago(0),
            revert_procedure="Remove cleaning rotation from shared calendar. "
                             "Return to ad-hoc cleaning by Tane only.",
            observations="Panel output increased 12% in first two weeks. "
                         "Rotation participation has been consistent.",
            midpoint_findings="Positive results so far. Output recovery is measurable. "
                              "One criterion (training completion) not yet met as Hina "
                              "has not completed orientation.",
            outcome=None,
            next_action="Continue test through completion. Schedule final review.",
            success_criteria_summary="2 of 3 criteria met at midpoint. Training criterion pending.",
            reviewer_notes="Tane is doing excellent work coordinating the rotation. "
                           "Consider formalizing the role.",
        ))

        await session.flush()  # Test report must exist before criteria FK

        # ===============================================================
        # 21. TEST SUCCESS CRITERIA (3: 2 met, 1 not met)
        # ===============================================================
        criteria_spec = [
            ("Panel output recovers to >= 95% of rated capacity within 30 days",
             True, "Output at 97% of rated capacity as of midpoint check (up from 82%)."),
            ("At least 80% of scheduled cleanings completed on time",
             True, "13 of 14 scheduled cleanings completed (93%). One rescheduled due to rain."),
            ("All rotation participants complete safety orientation",
             False, "4 of 5 participants completed orientation. Hina (prospective member) "
                    "has not yet completed orientation."),
        ]

        for criterion, met, evidence in criteria_spec:
            session.add(TestSuccessCriterion(
                id=uuid.uuid4(),
                test_report_id=test_report_id,
                criterion=criterion,
                met=met,
                evidence=evidence,
            ))

        await session.flush()  # Test criteria before decision records

        # ===============================================================
        # 22. DECISION RECORDS (3 with varied precedent levels)
        # ===============================================================
        dec_uaf_id = uuid.uuid4()
        dec_kitchen_id = uuid.uuid4()
        dec_compost_id = uuid.uuid4()

        decisions_spec = [
            # Foundational precedent from UAF ratification
            (dec_uaf_id, "dec-omnione-001", days_ago(28),
             "OmniOne UAF v1.0 ratified by founding members.",
             "Consent-based ratification by all founding members establishes the universal "
             "agreement field as the root governance document.",
             "Future UAF amendments require OSC-level consensus, not just consent.",
             "All four founding members participated. Discussion focused on cooling-off period "
             "duration (settled on 7 days) and exit rights (portable contributions guaranteed).",
             "agreement-registry", 1, "agreement", "agr-omnione-uaf-001",
             None, "binding", "active", None, None, None,
             days_from_now(152), "Manu", "co_creator", "Lani", days_ago(27)),
            # Domain-level decision
            (dec_kitchen_id, "dec-omnione-002", days_ago(18),
             "Kitchen operations agreement ratified with consent of affected parties.",
             "Domain-level agreements can be ratified by affected-party consent without "
             "requiring full ecosystem participation.",
             None,
             "Three of four active members participated (Aroha abstained as non-kitchen-user). "
             "Lani presented the proposal; Manu facilitated.",
             "act-process", 3, "agreement", "agr-shur-kitchen-001",
             "SHUR Kitchen", "advisory", "active", None, None, ["dec-omnione-001"],
             days_from_now(162), "Lani", "domain_steward", "Manu", days_ago(17)),
            # Recent decision with dissent
            (dec_compost_id, "dec-omnione-003", days_ago(5),
             "Composting standardization approved with integrated objection from Kai.",
             "Objections must be integrated before consent is granted. A tiered training "
             "approach (quick orientation vs full training) satisfies both accessibility "
             "and safety concerns.",
             "This decision may set precedent for other domain training requirements.",
             "Kai raised a valid objection about training rigidity. Two integration rounds "
             "produced a tiered solution. All participants consented after integration.",
             "act-process", 3, "proposal", "prop-omnione-002",
             "SHUR Garden", "advisory", "active", None, None, ["dec-omnione-001", "dec-omnione-002"],
             days_from_now(85), "Aroha", "domain_steward", "Manu", days_ago(4)),
        ]

        for (did, rec_id, dt, holding, ratio, obiter, deliberation,
             source_skill, source_layer, artifact_type, artifact_ref,
             domain_name, precedent, status, overruled, superseded, related,
             review_dt, recorder, recorder_role, verifier, verify_dt) in decisions_spec:
            session.add(DecisionRecord(
                id=did,
                ecosystem_id=ecosystem_id,
                record_id=rec_id,
                date=dt,
                holding=holding,
                ratio_decidendi=ratio,
                obiter_dicta=obiter,
                deliberation_summary=deliberation,
                source_skill=source_skill,
                source_layer=source_layer,
                artifact_type=artifact_type,
                artifact_reference=artifact_ref,
                domain=domain_name,
                precedent_level=precedent,
                status=status,
                overruled_by=overruled,
                superseded_by=superseded,
                related_records=related,
                review_date=review_dt,
                recorder=recorder,
                recorder_role=recorder_role,
                verification_by=verifier,
                verification_date=verify_dt,
            ))

        await session.flush()  # Decision records must exist before dissent/participants/tags FKs

        # ===============================================================
        # 23. DECISION DISSENT RECORDS (1 dissent on compost decision)
        # ===============================================================
        session.add(DecisionDissentRecord(
            id=uuid.uuid4(),
            decision_record_id=dec_compost_id,
            objector="Kai",
            objection="Training requirement as originally proposed was too rigid for "
                      "workshop volunteers with limited availability.",
            resolution="Tiered training approach adopted: 15-minute quick orientation for "
                       "supervised access, full 1-hour training for unsupervised composting.",
            notes="Objection was constructive and led to a better outcome. "
                  "Kai withdrew objection after round 2 integration.",
        ))

        # ===============================================================
        # 24. DECISION PARTICIPANTS (2-3 per decision)
        # ===============================================================
        decision_participants_spec = [
            # UAF decision
            (dec_uaf_id, "Manu", "co_creator", "proposer"),
            (dec_uaf_id, "Lani", "builder", "consent"),
            (dec_uaf_id, "Kai", "townhall", "consent"),
            (dec_uaf_id, "Aroha", "builder", "consent"),
            # Kitchen decision
            (dec_kitchen_id, "Lani", "domain_steward", "proposer"),
            (dec_kitchen_id, "Manu", "co_creator", "consent"),
            (dec_kitchen_id, "Kai", "townhall", "consent"),
            # Compost decision
            (dec_compost_id, "Aroha", "domain_steward", "proposer"),
            (dec_compost_id, "Manu", "co_creator", "consent"),
            (dec_compost_id, "Lani", "builder", "consent"),
            (dec_compost_id, "Kai", "townhall", "objection_then_consent"),
        ]

        for dec_id, name, role, position in decision_participants_spec:
            session.add(DecisionParticipant(
                id=uuid.uuid4(),
                decision_record_id=dec_id,
                name=name,
                role=role,
                position=position,
            ))

        # ===============================================================
        # 25. DECISION SEMANTIC TAGS (one per decision)
        # ===============================================================
        semantic_tags_spec = [
            (dec_uaf_id,
             {"primary": "governance-foundation", "secondary": ["uaf", "ratification", "founding"]},
             {"all_members": True},
             "ecosystem-wide", "standard",
             None),
            (dec_kitchen_id,
             {"primary": "domain-governance", "secondary": ["kitchen", "operations", "food-safety"]},
             {"domain": "SHUR Kitchen", "roles": ["builder", "townhall"]},
             "domain", "standard",
             ["dec-omnione-001"]),
            (dec_compost_id,
             {"primary": "domain-governance", "secondary": ["garden", "composting", "training", "objection-integration"]},
             {"domain": "SHUR Garden", "roles": ["builder", "townhall"]},
             "domain", "standard",
             ["dec-omnione-001", "dec-omnione-002"]),
        ]

        for dec_id, topic, affected, scope, urgency, precedents in semantic_tags_spec:
            session.add(DecisionSemanticTag(
                id=uuid.uuid4(),
                decision_record_id=dec_id,
                topic=topic,
                affected_parties=affected,
                ecosystem_scope=scope,
                urgency_at_time=urgency,
                related_precedents=precedents,
            ))

        await session.flush()  # Decision records done

        # ===============================================================
        # 26. CONFLICT CASES (2: one resolved, one active)
        # ===============================================================
        conflict_noise_id = uuid.uuid4()
        conflict_tool_id = uuid.uuid4()

        session.add(ConflictCase(
            id=conflict_noise_id,
            ecosystem_id=ecosystem_id,
            case_id="conf-omnione-001",
            title="Late-Night Noise Disturbance in Common Area",
            description=(
                "Multiple complaints about loud music and gatherings in the common area "
                "after 11pm on weeknights, disrupting sleep for garden workers who start at 6am."
            ),
            reporter_id=member_ids["Aroha"],
            status="resolved",
            severity="moderate",
            scope="interpersonal",
            tier=2,
            root_cause_category="boundary_disagreement",
            urgency="standard",
            safety_flag=False,
            parties={"involved": ["Kai", "Aroha", "Tane"], "affected": ["garden_workers"]},
            facilitator_id=member_ids["Manu"],
            domain="SHUR Common Areas",
            triage_notes="Pattern of repeated incidents over 2 weeks. Escalated to Tier 2 after "
                         "informal resolution attempts failed.",
            resolution_summary=(
                "Mediated dialogue produced a shared understanding. Parties agreed on "
                "10:30pm weeknight quiet threshold with pre-arranged exception process. "
                "This directly informed the Quiet Hours proposal (prop-omnione-003)."
            ),
            resolved_date=days_ago(9),
        ))

        session.add(ConflictCase(
            id=conflict_tool_id,
            ecosystem_id=ecosystem_id,
            case_id="conf-omnione-002",
            title="Workshop Tool Damage — Accountability Dispute",
            description=(
                "A power drill was returned damaged without notice. Kai (workshop steward) "
                "reported the issue. Tane acknowledged using it but disputes the damage was "
                "pre-existing."
            ),
            reporter_id=member_ids["Kai"],
            status="in_mediation",
            severity="low",
            scope="interpersonal",
            tier=1,
            root_cause_category="resource_dispute",
            urgency="standard",
            safety_flag=False,
            parties={"involved": ["Kai", "Tane"], "affected": ["workshop_users"]},
            facilitator_id=member_ids["Lani"],
            domain="SHUR Workshop",
            triage_notes="Tier 1: direct dialogue between parties. Lani volunteered to facilitate. "
                         "Tool checkout log shows Tane was last user.",
            resolution_summary=None,
            resolved_date=None,
        ))

        await session.flush()  # Conflict cases must exist before repair agreements

        # ===============================================================
        # 27. REPAIR AGREEMENT RECORDS (1 for the resolved conflict)
        # ===============================================================
        session.add(RepairAgreementRecord(
            id=uuid.uuid4(),
            conflict_case_id=conflict_noise_id,
            title="Noise Disturbance Repair Commitments",
            commitments=[
                {"party": "Kai", "commitment": "Notify garden workers 24h in advance of planned late events"},
                {"party": "Tane", "commitment": "Help enforce quiet hours during evening shifts"},
                {"party": "All", "commitment": "Support the Quiet Hours proposal through the ACT process"},
            ],
            responsible_party="Kai",
            status="active",
            checkin_30_date=days_from_now(21),
            checkin_30_notes=None,
            checkin_60_date=days_from_now(51),
            checkin_60_notes=None,
            checkin_90_date=days_from_now(81),
            checkin_90_notes=None,
            completed_date=None,
        ))

        # ===============================================================
        # 28. GOVERNANCE HEALTH AUDITS (2: one completed, one in progress)
        # ===============================================================
        session.add(GovernanceHealthAudit(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            audit_id="audit-omnione-001",
            audit_date=days_ago(15),
            auditor="Manu",
            capture_risk_indicators={
                "decision_concentration": {"score": 2, "note": "Manu facilitates most processes — single point of failure"},
                "participation_decline": {"score": 1, "note": "Stable participation, Tane onboarding adds capacity"},
                "agreement_staleness": {"score": 1, "note": "All agreements within review cycle"},
                "conflict_backlog": {"score": 1, "note": "One active conflict, one resolved recently"},
                "financial_opacity": {"score": 3, "note": "No formal budget tracking yet — flagged for attention"},
            },
            overall_health_score=78,
            findings=(
                "OmniOne governance is functioning well for a young ecosystem. "
                "Key strength: active use of ACT process with genuine consent practice. "
                "Key risk: over-reliance on Manu for facilitation and financial transparency gap."
            ),
            recommendations=[
                {"priority": "high", "action": "Train Lani and Aroha as backup facilitators", "due": str(days_from_now(30))},
                {"priority": "high", "action": "Establish transparent budget tracking process", "due": str(days_from_now(45))},
                {"priority": "medium", "action": "Document facilitation playbook for knowledge transfer", "due": str(days_from_now(60))},
            ],
            status="completed",
            next_audit_date=days_from_now(75),
        ))

        session.add(GovernanceHealthAudit(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            audit_id="audit-omnione-002",
            audit_date=days_from_now(75),
            auditor="Lani",
            capture_risk_indicators=None,
            overall_health_score=None,
            findings=None,
            recommendations=None,
            status="scheduled",
            next_audit_date=None,
        ))

        # ===============================================================
        # 29. EMERGENCY STATES (1 closed historical event)
        # ===============================================================
        session.add(EmergencyState(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            state="closed",
            declared_at=hours_ago(336),  # ~14 days ago
            declared_by="Manu",
            criteria_met={
                "trigger": "infrastructure_failure",
                "description": "Complete solar inverter failure during peak season — "
                               "no power to kitchen refrigeration or water pump",
                "affected_domains": ["SHUR Energy", "SHUR Kitchen"],
            },
            auto_revert_at=hours_ago(264),  # 72h window
            recovery_entered_at=hours_ago(312),  # ~1 day after declaration
            closed_at=hours_ago(240),  # ~4 days after declaration
            pre_authorized_roles=["energy_steward", "osc_member"],
            actions_log=[
                {"time": str(hours_ago(336)), "action": "Emergency declared by Manu (OSC)", "actor": "Manu"},
                {"time": str(hours_ago(335)), "action": "Tane authorized to bypass approval for emergency repair parts", "actor": "Manu"},
                {"time": str(hours_ago(330)), "action": "Temporary generator rented from Ubud", "actor": "Tane"},
                {"time": str(hours_ago(312)), "action": "Inverter replacement ordered, generator online — recovery mode", "actor": "Tane"},
                {"time": str(hours_ago(264)), "action": "New inverter installed and tested", "actor": "Tane"},
                {"time": str(hours_ago(240)), "action": "Emergency closed after 48h stable operation", "actor": "Manu"},
            ],
            post_review_status="completed",
            notes="Post-emergency review completed. Decision to add backup inverter and "
                  "establish emergency fund for critical infrastructure. See dec-omnione-003 "
                  "for related precedent.",
        ))

        # ===============================================================
        # 30. EXIT RECORDS (1 completed exit)
        # ===============================================================
        # Create a past member who exited — we don't add them to the active
        # members list but reference the existing Hina who is still prospective.
        # For realism, we simulate a former member "Rua" who already exited.
        rua_id = uuid.uuid4()
        session.add(Member(
            id=rua_id,
            ecosystem_id=ecosystem_id,
            member_id="mem-former-001",
            display_name="Rua",
            current_status="exited",
            profile="townhall",
            kyc_status="verified",
            onboarding_status="complete",
            notes="Former TH member. Left OmniOne voluntarily to start a new community project.",
            last_governance_activity_date=days_ago(45),
            skills_offered=["community-organizing", "event-planning"],
            skills_needed=None,
        ))
        await session.flush()

        session.add(ExitRecord(
            id=uuid.uuid4(),
            ecosystem_id=ecosystem_id,
            member_id=rua_id,
            exit_type="standard",
            status="completed",
            declared_date=days_ago(60),
            target_completion_date=days_ago(30),
            coordinator_id=member_ids["Manu"],
            commitment_inventory=[
                {"commitment": "Workshop Thursday shifts", "status": "transferred_to_Kai"},
                {"commitment": "Event planning role", "status": "transferred_to_Lani"},
                {"commitment": "Shared tool ownership (3 items)", "status": "returned"},
            ],
            unwinding_status={
                "commitments_unwound": 3,
                "commitments_total": 3,
                "data_exported": True,
                "contributions_documented": True,
            },
            data_export_requested=True,
            data_export_completed=days_ago(35),
            departure_notice=(
                "I'm grateful for my time at OmniOne and the governance skills I've developed. "
                "I'm leaving to help establish a sister community in Flores. "
                "I hope to stay connected and share learnings between our ecosystems."
            ),
            re_entry_eligible=True,
            completed_date=days_ago(30),
            notes="Clean exit. All commitments unwound. Rua remains a friend of the ecosystem.",
        ))

        # Also add a status transition for Rua
        session.add(MemberStatusTransition(
            id=uuid.uuid4(),
            member_id=rua_id,
            from_status="active",
            to_status="exiting",
            date=days_ago(60),
            trigger="voluntary_exit",
            notes="Rua declared intent to leave",
        ))
        session.add(MemberStatusTransition(
            id=uuid.uuid4(),
            member_id=rua_id,
            from_status="exiting",
            to_status="exited",
            date=days_ago(30),
            trigger="exit_complete",
            notes="All commitments unwound, data exported",
        ))

        # ===============================================================
        # COMMIT
        # ===============================================================
        await session.commit()

    await engine.dispose()

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print("Seed data created successfully:")
    print()
    print("  CORE (7 entity types)")
    print("    1  Ecosystem: OmniOne")
    print("    7  Members: Manu (OSC), Lani (AE), Kai (TH), Aroha (AE), Tane (TH), Hina (prospective), Rua (exited)")
    print("    6  MemberOnboarding records (varied completion 0%-100%)")
    print("   11  MemberStatusTransitions")
    print("    4  Domains: Kitchen, Garden, Workshop, Energy (child of Workshop)")
    print("   10  DomainElements")
    print("    7  DomainMetrics")
    print()
    print("  AGREEMENTS (4 entity types)")
    print("    5  Agreements: 1 UAF + 2 domain (active) + 1 policy (under_review) + 1 draft")
    print("   10  AgreementRatificationRecords")
    print("    2  AmendmentRecords: 1 approved, 1 proposed")
    print("    2  ReviewRecords: 1 completed, 1 upcoming")
    print()
    print("  ACT PROCESS (10 entity types)")
    print("    4  Proposals: draft, advice, consent, testing phases")
    print("    2  AdviceLogs")
    print("    6  AdviceEntries (integrated / acknowledged / not_integrated)")
    print("    3  AdviceNonRespondents")
    print("    1  ConsentRecord")
    print("    4  ConsentParticipants (3 consent + 1 objection)")
    print("    2  ConsentIntegrationRounds")
    print("    2  ConsentObjectionsAddressed")
    print("    1  TestReport (with midpoint findings)")
    print("    3  TestSuccessCriteria (2 met, 1 not met)")
    print()
    print("  MEMORY (4 entity types)")
    print("    3  DecisionRecords (binding + 2 advisory)")
    print("    1  DecisionDissentRecord")
    print("   11  DecisionParticipants")
    print("    3  DecisionSemanticTags")
    print()
    print("  CONFLICT & REPAIR (3 entity types)")
    print("    2  ConflictCases (1 resolved, 1 in_mediation)")
    print("    1  RepairAgreementRecord")
    print("    2  GovernanceHealthAudits (1 completed, 1 scheduled)")
    print()
    print("  EMERGENCY (1 entity type)")
    print("    1  EmergencyState (closed — solar inverter failure)")
    print()
    print("  EXIT (1 entity type)")
    print("    1  ExitRecord (completed — Rua's departure)")
    print()
    print("  TOTAL: 31 entity types, ~115 rows")


def main() -> None:
    """Entry point for the seed script."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed the NEOS database with OmniOne test data")
    parser.add_argument("--purge", action="store_true", help="Delete all data before seeding")
    args = parser.parse_args()

    try:
        from neos_agent.config import get_settings
        database_url = get_settings().DATABASE_URL
    except Exception:
        print("Error: DATABASE_URL not set. Set it as an environment variable or in agent/.env")
        sys.exit(1)

    if args.purge:
        print("Purging all data...")
        asyncio.run(purge(database_url))

    asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
