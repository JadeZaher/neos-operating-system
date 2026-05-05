"""Seed the database with 4 ecosystems for production-like testing.

Usage:
    python -m agent.scripts.seed_omnione            # seed (idempotent)
    python -m agent.scripts.seed_omnione --purge     # drop all data then reseed

Creates:
  4 ecosystems (OmniOne, Escherbridge, Plan Systems, Oasis)
  10 unique people, 11 member records (Ahmed appears in both OmniOne and Escherbridge) + 1 exited
  12 domains (3 per ecosystem)
  26 agreements (5 per ecosystem base + 6 varied-status extras)
  12 proposals (4 advice + 2 draft + 2 consent + 2 test + 1 ratified + 1 withdrawn)
  6 conflict cases (4 base + 2 additional) with 2 repair agreements
  12 decision records (8 base + 4 linked to ratified proposals)
  1 emergency state (OmniOne, closed)
  1 exit record (OmniOne)
  4 governance health audits (1 per ecosystem)
  33 circle memberships (3 members x 3 domains for OmniOne/Escherbridge/Plan Systems, 2 members x 3 domains for Oasis)
  16 shares/needs (4 per ecosystem: 2 shares, 2 needs)
  4 cross-ecosystem collaborations
  4 compliance summaries (1 per ecosystem)
  11 member onboarding records (all complete)
  5 quizzes with SurveyJS content + quiz results
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.course_models import Quiz, QuizResult
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
    # Collaboration
    CircleMembership,
    SharesNeeds,
    Collaboration,
    ComplianceSummary,
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


# ---------------------------------------------------------------------------
# Purge — delete all rows from all tables in reverse FK order
# ---------------------------------------------------------------------------
PURGE_ORDER = [
    # Quiz / course data
    "profile_tiles",
    "user_badges",
    "user_tags",
    "quiz_progress",
    "quiz_results",
    "quizzes",
    "courses",
    # Messaging
    "push_subscriptions",
    # Collaboration & governance
    "compliance_summaries",
    "collaborations",
    "shares_needs",
    "circle_memberships",
    "conversation_links",
    "messages",
    "conversation_participants",
    "conversations",
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
    """Delete all rows from all tables in reverse FK order."""
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        for table in PURGE_ORDER:
            try:
                await conn.execute(text(f'DELETE FROM "{table}"'))
            except Exception:
                pass  # table may not exist yet
        print(f"Purged all data from {len(PURGE_ORDER)} tables.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# Deterministic DIDs for all 12 members + 1 exited
# ---------------------------------------------------------------------------
# OmniOne (Ahmed's DID is shared with Escherbridge)
DID_JOSH = "did:neos:" + _uid("did.josh").hex[:32]
DID_NATHAN = "did:neos:" + _uid("did.nathan").hex[:32]
DID_AHMED = "did:neos:" + _uid("did.ahmed").hex[:32]  # same person in OmniOne & Escherbridge
# Escherbridge (DID_AHMED reused from above)
DID_KENNY = "did:neos:" + _uid("did.kenny").hex[:32]
DID_JAK = "did:neos:" + _uid("did.jak").hex[:32]
# Plan Systems
DID_RACHEL = "did:neos:" + _uid("did.rachel").hex[:32]
DID_BRANDON = "did:neos:" + _uid("did.brandon").hex[:32]
DID_DREW = "did:neos:" + _uid("did.drew").hex[:32]
# Oasis
DID_MAX = "did:neos:" + _uid("did.max").hex[:32]
DID_DAVID = "did:neos:" + _uid("did.david").hex[:32]
# Exited
DID_RUA = "did:neos:" + _uid("did.rua").hex[:32]


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
async def seed(database_url: str) -> None:  # noqa: C901 — intentionally long
    """Create comprehensive seed data across 4 ecosystems."""
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Migrate: add columns that create_all won't add to existing tables
    migrations = [
        ("members", "username", "ALTER TABLE members ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE"),
        ("members", "password_hash", "ALTER TABLE members ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"),
        ("quizzes", "ecosystem_id", "ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS ecosystem_id UUID REFERENCES ecosystems(id)"),
        ("quizzes", "domain_id", "ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS domain_id UUID REFERENCES domains(id)"),
        ("quizzes", "is_entry_quiz", "ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS is_entry_quiz BOOLEAN DEFAULT FALSE NOT NULL"),
    ]
    for table, column, ddl in migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(ddl))
                print(f"  migrated: {table}.{column}")
        except Exception:
            pass  # column already exists

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # ---------------------------------------------------------------
        # Idempotency: skip if OmniOne already exists
        # ---------------------------------------------------------------
        result = await session.execute(
            select(Ecosystem).where(Ecosystem.name == "OmniOne")
        )
        if result.scalar_one_or_none() is not None:
            print("OmniOne ecosystem already exists. Skipping seed.")
            await engine.dispose()
            return

        # ===============================================================
        # 1. ECOSYSTEMS (4)
        # ===============================================================
        eco_omni_id = _uid("eco.omnione")
        eco_eb_id = _uid("eco.escherbridge")
        eco_ps_id = _uid("eco.plansystems")
        eco_oa_id = _uid("eco.oasis")

        eco_omnione = Ecosystem(
            id=eco_omni_id,
            name="OmniOne",
            description=(
                "Regenerative community governance ecosystem in Bali, hosted by "
                "Escherbridge. OmniOne stewards consent-based governance using the "
                "ACT process (Advice, Consent, Test) within an S3-structured "
                "domain architecture for land, food, and community stewardship."
            ),
            status="active",
            location="Bali, Indonesia",
            website="https://escherbridge.com/",
            founded_date=days_ago(180),
            tags=["regenerative", "governance", "community", "bali"],
            contact_email="omnione@escherbridge.com",
            governance_summary=(
                "Consent-based decision-making using the ACT process "
                "(Advice, Consent, Test). Domain stewards hold delegated "
                "authority within S3-structured governance boundaries. "
                "GAIA 6-level escalation model for conflict resolution."
            ),
            visibility="public",
        )

        eco_escherbridge = Ecosystem(
            id=eco_eb_id,
            name="Escherbridge",
            description=(
                "Software consultancy founded by Ahmed Zaher specializing in "
                "transforming complex technical challenges into scalable solutions. "
                "Escherbridge bridges vision and code through full-stack development, "
                "AI agentic systems, blockchain platforms (Ardanova on Algorand), "
                "VR experiences (ComeAlongSide), and fractional CTO services."
            ),
            status="active",
            location="Amsterdam, Netherlands",
            website="https://escherbridge.com/",
            founded_date=days_ago(120),
            tags=["creative-arts", "technology", "digital-art", "collaboration"],
            contact_email="hello@escherbridge.com",
            governance_summary=(
                "ACT governance adapted for creative collectives. "
                "Domain stewards rotate quarterly. Strong emphasis on "
                "open creative commons and transparent resource allocation."
            ),
            visibility="public",
        )

        eco_plansystems = Ecosystem(
            id=eco_ps_id,
            name="Plan Systems",
            description=(
                "501(c)(3) nonprofit providing affordable 5G broadband and spatial "
                "collaboration software (PLAN 3D). Focused on STEM education, emergency "
                "response coordination, regenerative agriculture, and community digital twins "
                "using the PLAN-Unity SDK and spatial linking infrastructure."
            ),
            status="active",
            location="Portland, Oregon, USA",
            website="https://plan-systems.org/",
            founded_date=days_ago(90),
            tags=["systems-thinking", "planning", "cooperative", "organizational-development"],
            contact_email="info@plan-systems.org",
            governance_summary=(
                "Hybrid governance model blending systems thinking frameworks "
                "with NEOS ACT process. Advisory council holds review authority "
                "on strategic planning matters."
            ),
            visibility="public",
        )

        eco_oasis = Ecosystem(
            id=eco_oa_id,
            name="Oasis",
            description=(
                "Universal cross-chain interoperability platform — one API, all chains. "
                "Oasis provides holonic identity-first data infrastructure, HyperDrive "
                "intelligent routing, cross-chain NFTs (GeoNFTs), Universal Asset Bridge "
                "with atomic swaps, and the STAR CLI metaverse generator. Integrates 50+ "
                "blockchain and cloud providers for digital sovereignty and Web4 governance."
            ),
            status="active",
            location="Global / Remote",
            website="https://www.oasisweb4.com/",
            founded_date=days_ago(60),
            tags=["web4", "decentralized", "community-platform", "digital-sovereignty"],
            contact_email="hello@oasisweb4.com",
            governance_summary=(
                "Distributed governance model for a remote-first collective. "
                "ACT process adapted for asynchronous decision-making. "
                "Emphasis on digital sovereignty and decentralized coordination."
            ),
            visibility="public",
        )

        session.add_all([eco_omnione, eco_escherbridge, eco_plansystems, eco_oasis])
        await session.flush()

        # ===============================================================
        # 2. MEMBERS — 11 records (Ahmed in both OmniOne & Escherbridge) + 1 exited
        # ===============================================================
        # OmniOne
        m_josh_id = _uid("mbr.omni.josh")
        m_nathan_id = _uid("mbr.omni.nathan")
        m_ahmed_id = _uid("mbr.omni.ahmed")
        # Escherbridge (Ahmed has a separate member record but same DID)
        m_ahmed_eb_id = _uid("mbr.eb.ahmed")
        m_kenny_id = _uid("mbr.eb.kenny")
        m_jak_id = _uid("mbr.eb.jak")
        # Plan Systems
        m_rachel_id = _uid("mbr.ps.rachel")
        m_brandon_id = _uid("mbr.ps.brandon")
        m_drew_id = _uid("mbr.ps.drew")
        # Oasis (only 2 members)
        m_max_id = _uid("mbr.oa.max")
        m_david_id = _uid("mbr.oa.david")
        # Exited (OmniOne)
        m_rua_id = _uid("mbr.omni.rua")

        # fmt: off
        members_spec = [
            # (id, eco_id, member_id_str, did, display_name, status, profile, skills_offered, skills_needed, notes, gov_days_ago)
            # ── OmniOne ──
            (m_josh_id,  eco_omni_id, "MBR-OMNI-001", DID_JOSH,  "Josh Pasmore",  "active", "co_creator",
             ["governance-design", "facilitation", "conflict-resolution"], ["permaculture"],
             "OmniOne founding steward and primary facilitator", 1),
            (m_nathan_id, eco_omni_id, "MBR-OMNI-002", DID_NATHAN, "Nathan R", "active", "builder",
             ["community-building", "event-coordination", "outreach"], ["digital-tools"],
             "Community builder and engagement coordinator", 2),
            (m_ahmed_id, eco_omni_id, "MBR-OMNI-003", DID_AHMED, "Ahmed (Jade Oni)", "active", "townhall",
             ["governance-specialist", "multi-ecosystem-coordination", "workshop-facilitation"], ["permaculture"],
             "Multi-ecosystem participant and governance specialist; also active in Escherbridge", 3),

            # ── Escherbridge ──
            (m_ahmed_eb_id, eco_eb_id, "MBR-EB-001", DID_AHMED, "Ahmed (Jade Oni)", "active", "co_creator",
             ["creative-direction", "governance-design", "facilitation"], ["systems-thinking"],
             "Escherbridge owner and co-creator; also active in OmniOne", 1),
            (m_kenny_id,  eco_eb_id, "MBR-EB-002", DID_KENNY,  "Kenny",  "active", "builder",
             ["creative-technology", "interactive-installations", "creative-coding"], ["grant-writing"],
             "Creative technologist at Escherbridge", 2),
            (m_jak_id, eco_eb_id, "MBR-EB-003", DID_JAK, "Jak", "active", "townhall",
             ["3d-printing", "digital-fabrication", "documentation"], ["accounting"],
             "Digital fabrication specialist at Escherbridge", 3),

            # ── Plan Systems ──
            (m_rachel_id,  eco_ps_id, "MBR-PS-001", DID_RACHEL,  "Rachel",  "active", "co_creator",
             ["strategic-planning", "systems-design", "organizational-development"], ["technology"],
             "Plan Systems lead and strategic planning specialist", 1),
            (m_brandon_id, eco_ps_id, "MBR-PS-002", DID_BRANDON, "Brandon", "active", "builder",
             ["systems-design", "data-visualization", "process-automation"], ["facilitation"],
             "Systems design specialist building planning tools", 2),
            (m_drew_id,    eco_ps_id, "MBR-PS-003", DID_DREW,    "Drew",    "active", "townhall",
             ["documentation", "knowledge-management", "process-mapping"], ["strategic-planning"],
             "Knowledge management specialist and process documentarian", 4),

            # ── Oasis (2 members) ──
            (m_max_id, eco_oa_id, "MBR-OA-001", DID_MAX, "Max Gershfield", "active", "co_creator",
             ["decentralized-governance", "protocol-design", "community-building"], ["legal-frameworks"],
             "Oasis founder and Web4 protocol architect", 1),
            (m_david_id, eco_oa_id, "MBR-OA-002", DID_DAVID, "David Ellams", "active", "builder",
             ["distributed-systems", "smart-contracts", "infrastructure-engineering"], ["facilitation"],
             "Distributed systems engineer", 2),
        ]
        # fmt: on

        default_privacy = {
            "is_profile_public": True,
            "show_badges": True,
            "show_tags": True,
            "show_quiz_results": True,
            "allow_discovery": True,
        }

        for (mid, eco_id, member_id_str, did, name, status, profile,
             skills_o, skills_n, notes, gov_days) in members_spec:
            session.add(Member(
                id=mid,
                ecosystem_id=eco_id,
                member_id=member_id_str,
                did=did,
                display_name=name,
                current_status=status,
                profile=profile,
                kyc_status="verified",
                onboarding_status="complete",
                skills_offered=skills_o,
                skills_needed=skills_n,
                notes=notes,
                last_governance_activity_date=days_ago(gov_days),
                privacy=default_privacy,
            ))

        # Exited member Rua (OmniOne)
        rua = Member(
            id=m_rua_id,
            ecosystem_id=eco_omni_id,
            member_id="MBR-OMNI-EX-001",
            did=DID_RUA,
            display_name="Rua",
            current_status="exited",
            profile="townhall",
            kyc_status="verified",
            onboarding_status="complete",
            notes="Former TH member. Left OmniOne voluntarily to start a new community project.",
            last_governance_activity_date=days_ago(45),
            skills_offered=["community-organizing", "event-planning"],
            privacy={"is_profile_public": False, "show_badges": False, "show_tags": False,
                     "show_quiz_results": False, "allow_discovery": False},
        )
        session.add(rua)
        await session.flush()

        # ===============================================================
        # 3. MEMBER ONBOARDING — one per active member (11 total)
        # ===============================================================
        full_consents = {"principles": True, "agreements": True, "roles": True, "exit": True}
        full_checklist = {"uaf_read": True, "mentor_assigned": True, "first_governance": True, "cooling_off_complete": True}

        all_member_ids = [
            m_josh_id, m_nathan_id, m_ahmed_id,
            m_ahmed_eb_id, m_kenny_id, m_jak_id,
            m_rachel_id, m_brandon_id, m_drew_id,
            m_max_id, m_david_id,
        ]

        for mid_val in all_member_ids:
            session.add(MemberOnboarding(
                id=_uid(f"onb.{mid_val}"),
                member_id=mid_val,
                facilitator="System",
                uaf_version_consented="1.0",
                consent_date=days_ago(60),
                cooling_off_start=days_ago(60),
                cooling_off_end=days_ago(53),
                completion_percentage=100,
                section_consents=full_consents,
                checklist_items=full_checklist,
            ))

        # ===============================================================
        # 4. MEMBER STATUS TRANSITIONS
        # ===============================================================
        for mid_val in all_member_ids:
            session.add(MemberStatusTransition(
                id=_uid(f"trans.pending.{mid_val}"),
                member_id=mid_val,
                from_status="pending",
                to_status="active",
                date=days_ago(55),
                trigger="onboarding_complete",
            ))

        # Rua exit transitions
        session.add(MemberStatusTransition(
            id=_uid("trans.rua.active"),
            member_id=m_rua_id,
            from_status="active",
            to_status="exiting",
            date=days_ago(60),
            trigger="voluntary_exit",
            notes="Rua declared intent to leave",
        ))
        session.add(MemberStatusTransition(
            id=_uid("trans.rua.exited"),
            member_id=m_rua_id,
            from_status="exiting",
            to_status="exited",
            date=days_ago(30),
            trigger="exit_complete",
            notes="All commitments unwound, data exported",
        ))

        await session.flush()

        # ===============================================================
        # 5. DOMAINS — 3 per ecosystem (12 total)
        # Standard: Core Operations, Governance Circle, Specialty Circle
        # ===============================================================
        # OmniOne domains
        dom_omni_ops_id = _uid("dom.omni.ops")
        dom_omni_gov_id = _uid("dom.omni.gov")
        dom_omni_regen_id = _uid("dom.omni.regen")

        # Escherbridge domains
        dom_eb_ops_id = _uid("dom.eb.ops")
        dom_eb_gov_id = _uid("dom.eb.gov")
        dom_eb_art_id = _uid("dom.eb.art")

        # Plan Systems domains
        dom_ps_ops_id = _uid("dom.ps.ops")
        dom_ps_gov_id = _uid("dom.ps.gov")
        dom_ps_design_id = _uid("dom.ps.design")

        # Oasis domains
        dom_oa_ops_id = _uid("dom.oa.ops")
        dom_oa_gov_id = _uid("dom.oa.gov")
        dom_oa_protocol_id = _uid("dom.oa.protocol")

        # fmt: off
        domains_spec = [
            # (id, eco_id, domain_id_str, purpose, steward_name, steward_uuid, parent, creator)
            # ── OmniOne ──
            (dom_omni_ops_id,   eco_omni_id, "dom-omni-ops-001",
             "Core Operations (SHUR) — main operational circle managing housing, shared facilities, and land stewardship in Bali",
             "Josh Pasmore", m_josh_id, None, "Josh Pasmore"),
            (dom_omni_gov_id,   eco_omni_id, "dom-omni-gov-001",
             "Governance Circle — manages ACT processes, decision-making, onboarding, and constitutional reviews",
             "Josh Pasmore", m_josh_id, dom_omni_ops_id, "Josh Pasmore"),
            (dom_omni_regen_id, eco_omni_id, "dom-omni-regen-001",
             "Regenerative Agriculture Circle — permaculture, food forest, seed library, and community garden management",
             "Nathan R", m_nathan_id, dom_omni_ops_id, "Josh Pasmore"),

            # ── Escherbridge ──
            (dom_eb_ops_id,  eco_eb_id, "dom-eb-ops-001",
             "Core Operations (HQ) — shared studios, exhibition space, workshops, and community coordination in Amsterdam",
             "Ahmed (Jade Oni)", m_ahmed_eb_id, None, "Ahmed (Jade Oni)"),
            (dom_eb_gov_id,  eco_eb_id, "dom-eb-gov-001",
             "Governance Circle — manages decision-making, artist agreements, onboarding, and resource allocation",
             "Ahmed (Jade Oni)", m_ahmed_eb_id, dom_eb_ops_id, "Ahmed (Jade Oni)"),
            (dom_eb_art_id,  eco_eb_id, "dom-eb-art-001",
             "Digital Arts & Technology Circle — interactive installations, creative coding, projection mapping, and immersive experiences",
             "Kenny", m_kenny_id, dom_eb_ops_id, "Ahmed (Jade Oni)"),

            # ── Plan Systems ──
            (dom_ps_ops_id,    eco_ps_id, "dom-ps-ops-001",
             "Core Operations (HQ) — co-working space, meeting rooms, resource library, and cooperative administration",
             "Rachel", m_rachel_id, None, "Rachel"),
            (dom_ps_gov_id,    eco_ps_id, "dom-ps-gov-001",
             "Governance Circle — manages decision-making, member agreements, onboarding, and strategic reviews",
             "Rachel", m_rachel_id, dom_ps_ops_id, "Rachel"),
            (dom_ps_design_id, eco_ps_id, "dom-ps-design-001",
             "Systems Design Circle — strategic planning frameworks, organizational modeling, and facilitation methods",
             "Rachel", m_rachel_id, dom_ps_ops_id, "Rachel"),

            # ── Oasis ──
            (dom_oa_ops_id,      eco_oa_id, "dom-oa-ops-001",
             "Core Operations (HQ) — distributed coordination, platform infrastructure, and community management for the global network",
             "Max Gershfield", m_max_id, None, "Max Gershfield"),
            (dom_oa_gov_id,      eco_oa_id, "dom-oa-gov-001",
             "Governance Circle — manages asynchronous decision-making, digital sovereignty agreements, and member onboarding",
             "Max Gershfield", m_max_id, dom_oa_ops_id, "Max Gershfield"),
            (dom_oa_protocol_id, eco_oa_id, "dom-oa-protocol-001",
             "Protocol Development Circle — Web4 protocol design, smart contracts, tokenomics research, and decentralized infrastructure",
             "David Ellams", m_david_id, dom_oa_ops_id, "Max Gershfield"),
        ]
        # fmt: on

        for (did, eco_id, domain_id_str, purpose, steward_name,
             steward_uuid, parent, creator) in domains_spec:
            session.add(Domain(
                id=did,
                ecosystem_id=eco_id,
                domain_id=domain_id_str,
                version="1.0",
                status="active",
                purpose=purpose,
                current_steward=steward_name,
                steward_id=steward_uuid,
                parent_domain_id=parent,
                created_by=creator,
            ))

        await session.flush()

        # ===============================================================
        # 6. DOMAIN ELEMENTS — 2 per domain
        # ===============================================================
        elements_spec = [
            # OmniOne
            (dom_omni_ops_id, "land_map", {"type": "asset", "hectares": 5.2, "zones": ["housing", "farm", "forest", "commons"]}),
            (dom_omni_ops_id, "facilities", {"type": "inventory", "buildings": 8, "shared_spaces": 3}),
            (dom_omni_gov_id, "meeting_schedule", {"type": "schedule", "frequency": "weekly", "day": "Monday"}),
            (dom_omni_gov_id, "facilitation_roster", {"type": "roster", "facilitators": ["Josh Pasmore", "Ahmed (Jade Oni)"]}),
            (dom_omni_regen_id, "crop_plan", {"type": "plan", "season": "wet_2026", "beds_active": 12}),
            (dom_omni_regen_id, "seed_library", {"type": "inventory", "varieties": 45, "native_species": 18}),
            # Escherbridge
            (dom_eb_ops_id, "studio_layout", {"type": "asset", "studios": 6, "exhibition_space_sqm": 200, "workshop_rooms": 2}),
            (dom_eb_ops_id, "artist_registry", {"type": "registry", "active_members": 3, "resident_artists": 1}),
            (dom_eb_gov_id, "meeting_schedule", {"type": "schedule", "frequency": "biweekly", "day": "Wednesday"}),
            (dom_eb_gov_id, "governance_handbook", {"type": "document", "version": "1.2", "last_updated": str(days_ago(15))}),
            (dom_eb_art_id, "installation_inventory", {"type": "inventory", "projectors": 8, "led_panels": 12, "sensors": 24}),
            (dom_eb_art_id, "creative_coding_tools", {"type": "inventory", "frameworks": ["Processing", "TouchDesigner", "openFrameworks"]}),
            # Plan Systems
            (dom_ps_ops_id, "coworking_space", {"type": "asset", "desks": 15, "meeting_rooms": 3, "capacity": 25}),
            (dom_ps_ops_id, "resource_library", {"type": "inventory", "books": 200, "frameworks": 15, "templates": 40}),
            (dom_ps_gov_id, "meeting_schedule", {"type": "schedule", "frequency": "weekly", "day": "Thursday"}),
            (dom_ps_gov_id, "decision_log", {"type": "registry", "total_decisions": 42, "this_quarter": 8}),
            (dom_ps_design_id, "framework_catalog", {"type": "inventory", "frameworks": ["Viable System Model", "Cynefin", "DSRP", "Wardley Maps"]}),
            (dom_ps_design_id, "client_portfolio", {"type": "registry", "active_clients": 4, "completed_projects": 12}),
            # Oasis
            (dom_oa_ops_id, "platform_infrastructure", {"type": "inventory", "nodes": 12, "regions": 4, "uptime_target": "99.9%"}),
            (dom_oa_ops_id, "community_channels", {"type": "registry", "discord_members": 850, "forum_threads": 230}),
            (dom_oa_gov_id, "async_schedule", {"type": "schedule", "voting_windows": "72h", "proposal_cadence": "rolling"}),
            (dom_oa_gov_id, "governance_handbook", {"type": "document", "version": "2.0", "last_updated": str(days_ago(10))}),
            (dom_oa_protocol_id, "protocol_roadmap", {"type": "plan", "current_phase": "testnet-v2", "next": "mainnet-beta"}),
            (dom_oa_protocol_id, "smart_contracts", {"type": "inventory", "deployed": 5, "audited": 3, "in_review": 2}),
        ]

        for dom_id, name, value in elements_spec:
            session.add(DomainElement(
                id=_uid(f"elem.{dom_id}.{name}"),
                domain_id=dom_id,
                element_name=name,
                element_value=value,
            ))

        # ===============================================================
        # 7. DOMAIN METRICS — 1-2 per domain
        # ===============================================================
        metrics_spec = [
            # OmniOne
            (dom_omni_ops_id, "Member satisfaction score", ">=80%", "Quarterly survey"),
            (dom_omni_gov_id, "Governance participation rate", ">=70%", "Meeting attendance tracking"),
            (dom_omni_gov_id, "ACT process completion time", "<=21 days", "Process log timestamps"),
            (dom_omni_regen_id, "Harvest yield (kg/week)", ">=30 kg", "Weigh at harvest"),
            # Escherbridge
            (dom_eb_ops_id, "Studio utilization rate", ">=70%", "Booking system logs"),
            (dom_eb_gov_id, "Decision turnaround time", "<=14 days", "Process log timestamps"),
            (dom_eb_art_id, "Exhibition attendance (per show)", ">=150 visitors", "Door count and registration"),
            (dom_eb_art_id, "Artist collaboration index", ">=3 cross-discipline projects/quarter", "Project tracking"),
            # Plan Systems
            (dom_ps_ops_id, "Cooperative revenue (monthly)", ">=8000 USD", "Accounting ledger"),
            (dom_ps_gov_id, "Member engagement rate", ">=75%", "Meeting and vote participation tracking"),
            (dom_ps_design_id, "Client satisfaction score", ">=85%", "Post-engagement surveys"),
            (dom_ps_design_id, "Framework adoption rate", ">=60%", "Client follow-up audits"),
            # Oasis
            (dom_oa_ops_id, "Platform uptime", ">=99.9%", "Monitoring dashboard"),
            (dom_oa_gov_id, "Async voting participation", ">=60%", "On-chain voting analytics"),
            (dom_oa_protocol_id, "Protocol test coverage", ">=90%", "CI/CD pipeline reports"),
            (dom_oa_protocol_id, "Smart contract audit score", ">=95/100", "Third-party audit reports"),
        ]

        for dom_id, metric, target, method in metrics_spec:
            session.add(DomainMetric(
                id=_uid(f"metric.{dom_id}.{metric[:20]}"),
                domain_id=dom_id,
                metric=metric,
                target=target,
                measurement_method=method,
            ))

        await session.flush()

        # ===============================================================
        # 8. AGREEMENTS — 5 per ecosystem (20 total)
        # Standard per ecosystem:
        #   1. UAF (active, ecosystem-level)
        #   2. Decision-Making Protocol (active, domain-level for governance)
        #   3. Membership Agreement (active, ecosystem-level)
        #   4. Resource Sharing Framework (advice stage, domain-level)
        #   5. Unique agreement (draft or under_review)
        # ===============================================================
        # OmniOne agreements
        agr_omni_uaf = _uid("agr.omni.uaf")
        agr_omni_decision = _uid("agr.omni.decision")
        agr_omni_membership = _uid("agr.omni.membership")
        agr_omni_resource = _uid("agr.omni.resource")
        agr_omni_unique = _uid("agr.omni.unique")

        # Escherbridge agreements
        agr_eb_uaf = _uid("agr.eb.uaf")
        agr_eb_decision = _uid("agr.eb.decision")
        agr_eb_membership = _uid("agr.eb.membership")
        agr_eb_resource = _uid("agr.eb.resource")
        agr_eb_unique = _uid("agr.eb.unique")

        # Plan Systems agreements
        agr_ps_uaf = _uid("agr.ps.uaf")
        agr_ps_decision = _uid("agr.ps.decision")
        agr_ps_membership = _uid("agr.ps.membership")
        agr_ps_resource = _uid("agr.ps.resource")
        agr_ps_unique = _uid("agr.ps.unique")

        # Oasis agreements
        agr_oa_uaf = _uid("agr.oa.uaf")
        agr_oa_decision = _uid("agr.oa.decision")
        agr_oa_membership = _uid("agr.oa.membership")
        agr_oa_resource = _uid("agr.oa.resource")
        agr_oa_unique = _uid("agr.oa.unique")

        # fmt: off
        agreements_spec = [
            # (id, eco_id, agr_id_str, type, title, version, status, proposer, domain, hierarchy, parent, text, created, ratified, review_date, sunset, affected, fingerprint)
            # ── OmniOne ──
            (agr_omni_uaf, eco_omni_id, "AGR-OMNI-001", "constitutional",
             "OmniOne Universal Agreement Field", "1.0", "active",
             "Josh Pasmore", None, "ecosystem", None,
             "The foundational agreement defining OmniOne's shared principles, governance architecture, and member rights within the Bali regenerative community.",
             days_ago(170), days_ago(165), days_from_now(195), None,
             {"all_members": True}, "uaf-omni-v1-sha256abc"),
            (agr_omni_decision, eco_omni_id, "AGR-OMNI-002", "operational",
             "OmniOne Decision-Making Protocol", "1.0", "active",
             "Josh Pasmore", "Governance Circle", "domain", agr_omni_uaf,
             "Protocol governing how decisions are made within the governance circle using the ACT process, including quorum requirements and escalation paths.",
             days_ago(160), days_ago(155), days_from_now(200), None,
             {"affected": ["governance_circle"]}, "dmp-omni-v1-sha256def"),
            (agr_omni_membership, eco_omni_id, "AGR-OMNI-003", "policy",
             "OmniOne Membership Agreement", "1.0", "active",
             "Josh Pasmore", None, "ecosystem", agr_omni_uaf,
             "Defines member rights, responsibilities, onboarding requirements, cooling-off periods, and exit procedures for all OmniOne participants.",
             days_ago(165), days_ago(160), days_from_now(200), None,
             {"all_members": True}, "mem-omni-v1-sha256ghi"),
            (agr_omni_resource, eco_omni_id, "AGR-OMNI-004", "resource",
             "NEOS Operating System Integration Framework", "0.2", "advice",
             "Ahmed (Jade Oni)", "Core Operations", "domain", agr_omni_uaf,
             "Framework for integrating the NEOS governance operating system into OmniOne's daily operations. "
             "Covers self-sovereign identity (DID-based auth), on-chain consent records, "
             "and interoperability with Oasis Web4 holonic data infrastructure for cross-ecosystem governance portability.",
             days_ago(10), None, None, None,
             {"affected": ["all_members", "neos_contributors"]}, None),
            (agr_omni_unique, eco_omni_id, "AGR-OMNI-005", "operational",
             "Digital Twin Community Mapping Charter", "0.1", "draft",
             "Nathan R", "Regenerative Agriculture Circle", "domain", agr_omni_uaf,
             "Draft charter for building a spatial digital twin of the OmniOne Bali site using Plan Systems' PLAN 3D platform. "
             "Covers geo-spatial mapping of land zones, regenerative agriculture beds, and community infrastructure "
             "into a navigable 3D model with real-time sensor data overlays and governance domain boundaries.",
             days_ago(5), None, None, None,
             {"affected": ["regen_circle", "all_members", "plan_systems_collab"]}, None),

            # ── Escherbridge ──
            (agr_eb_uaf, eco_eb_id, "AGR-EB-001", "constitutional",
             "Escherbridge Universal Agreement Field", "1.0", "active",
             "Ahmed (Jade Oni)", None, "ecosystem", None,
             "Foundational agreement for the Escherbridge collective, integrating creative commons principles with NEOS governance.",
             days_ago(110), days_ago(105), days_from_now(255), None,
             {"all_members": True}, "uaf-eb-v1-sha256jkl"),
            (agr_eb_decision, eco_eb_id, "AGR-EB-002", "operational",
             "Escherbridge Decision-Making Protocol", "1.0", "active",
             "Ahmed (Jade Oni)", "Governance Circle", "domain", agr_eb_uaf,
             "Decision-making protocol for the Escherbridge governance circle, with emphasis on creative consent and quarterly steward rotation.",
             days_ago(105), days_ago(100), days_from_now(260), None,
             {"affected": ["governance_circle"]}, "dmp-eb-v1-sha256mno"),
            (agr_eb_membership, eco_eb_id, "AGR-EB-003", "policy",
             "Escherbridge Membership Agreement", "1.0", "active",
             "Ahmed (Jade Oni)", None, "ecosystem", agr_eb_uaf,
             "Membership agreement covering artist rights, studio access, creative commons licensing, and collective responsibilities.",
             days_ago(105), days_ago(100), days_from_now(260), None,
             {"all_members": True}, "mem-eb-v1-sha256pqr"),
            (agr_eb_resource, eco_eb_id, "AGR-EB-004", "resource",
             "Metaverse Experience Development Framework", "0.3", "advice",
             "Jak", "Core Operations", "domain", agr_eb_uaf,
             "Framework for Escherbridge's metaverse and immersive experience development pipeline. "
             "Covers VR/AR creative tooling (building on ComeAlongSide VR heritage), spatial computing integrations, "
             "and collaboration with Oasis Web4 for cross-chain NFT provenance of digital art installations. "
             "Includes IP licensing under creative commons for collaborative metaverse assets.",
             days_ago(8), None, None, None,
             {"affected": ["studio_users", "metaverse_devs", "oasis_collab"]}, None),
            (agr_eb_unique, eco_eb_id, "AGR-EB-005", "policy",
             "Web3 Platform Integration & Agentic Systems Charter", "0.1", "under_review",
             "Kenny", "Digital Arts & Technology Circle", "domain", agr_eb_uaf,
             "Charter governing Escherbridge's integration of AI agentic systems and blockchain infrastructure. "
             "Covers the Ardanova gamified token platform (Algorand), AI-assisted creative tooling using LLMs, "
             "and NEOS governance integration for transparent resource allocation across client consulting engagements. "
             "Defines data sovereignty boundaries for enterprise clients and fractional CTO engagements.",
             days_ago(15), None, days_ago(2), days_from_now(90),
             {"affected": ["tech_team", "consulting_clients", "neos_integration"]}, None),

            # ── Plan Systems ──
            (agr_ps_uaf, eco_ps_id, "AGR-PS-001", "constitutional",
             "Plan Systems Universal Agreement Field", "1.0", "active",
             "Rachel", None, "ecosystem", None,
             "Foundational agreement integrating systems thinking principles with NEOS governance architecture for the Portland cooperative.",
             days_ago(85), days_ago(80), days_from_now(280), None,
             {"all_members": True}, "uaf-ps-v1-sha256stu"),
            (agr_ps_decision, eco_ps_id, "AGR-PS-002", "operational",
             "Plan Systems Decision-Making Protocol", "1.0", "active",
             "Rachel", "Governance Circle", "domain", agr_ps_uaf,
             "Decision-making protocol for the Plan Systems governance circle, blending systems thinking with ACT process.",
             days_ago(80), days_ago(75), days_from_now(285), None,
             {"affected": ["governance_circle"]}, "dmp-ps-v1-sha256vwx"),
            (agr_ps_membership, eco_ps_id, "AGR-PS-003", "policy",
             "Plan Systems Membership Agreement", "1.0", "active",
             "Rachel", None, "ecosystem", agr_ps_uaf,
             "Cooperative membership agreement covering member equity, profit sharing, and knowledge ownership.",
             days_ago(80), days_ago(75), days_from_now(285), None,
             {"all_members": True}, "mem-ps-v1-sha256yza"),
            (agr_ps_resource, eco_ps_id, "AGR-PS-004", "resource",
             "PLAN 3D Spatial Collaboration & Digital Twin Framework", "0.2", "advice",
             "Brandon", "Systems Design Circle", "domain", agr_ps_uaf,
             "Framework governing the development and deployment of Plan Systems' PLAN 3D spatial collaboration platform. "
             "Covers real-time 3D space creation, spatial linking (next-gen hyperlinks), and the PLAN-Unity SDK "
             "for packaging 3D models into deployable Crates. Defines data sovereignty for geo-spatial mapping, "
             "emergency response coordination data (Maui Fires, Kerr Floods heritage), and community digital twin assets. "
             "Integrates with NEOS governance for consent-based access control on spatial data.",
             days_ago(7), None, None, None,
             {"affected": ["design_circle", "broadband_users", "emergency_responders"]}, None),
            (agr_ps_unique, eco_ps_id, "AGR-PS-005", "operational",
             "NEOS x PLAN Systems Interoperability Protocol", "0.1", "draft",
             "Brandon", "Systems Design Circle", "domain", agr_ps_uaf,
             "Draft protocol for bidirectional interoperability between the NEOS governance OS and Plan Systems' "
             "distributed infrastructure. Covers 5G broadband service integration, STEM education platform governance, "
             "and community workforce operations managed through NEOS ACT process. "
             "Defines how Plan Systems' nonprofit 501(c)(3) service model intersects with NEOS ecosystem sovereignty.",
             days_ago(4), None, None, None,
             {"affected": ["design_circle", "broadband_communities", "neos_core"]}, None),

            # ── Oasis ──
            (agr_oa_uaf, eco_oa_id, "AGR-OA-001", "constitutional",
             "Oasis Universal Agreement Field", "1.0", "active",
             "Max Gershfield", None, "ecosystem", None,
             "Foundational agreement defining Oasis shared principles of digital sovereignty, decentralized governance, and Web4 community standards.",
             days_ago(55), days_ago(50), days_from_now(310), None,
             {"all_members": True}, "uaf-oa-v1-sha256bcd"),
            (agr_oa_decision, eco_oa_id, "AGR-OA-002", "operational",
             "Oasis Decision-Making Protocol", "1.0", "active",
             "Max Gershfield", "Governance Circle", "domain", agr_oa_uaf,
             "Async-first decision-making protocol with 72-hour voting windows and on-chain consent records.",
             days_ago(50), days_ago(45), days_from_now(315), None,
             {"affected": ["governance_circle"]}, "dmp-oa-v1-sha256efg"),
            (agr_oa_membership, eco_oa_id, "AGR-OA-003", "policy",
             "Oasis Membership Agreement", "1.0", "active",
             "Max Gershfield", None, "ecosystem", agr_oa_uaf,
             "Digital membership agreement covering DID-based identity, token governance rights, and data portability.",
             days_ago(50), days_ago(45), days_from_now(315), None,
             {"all_members": True}, "mem-oa-v1-sha256hij"),
            (agr_oa_resource, eco_oa_id, "AGR-OA-004", "resource",
             "Holonic Interoperability & Cross-Chain Governance Framework", "0.2", "advice",
             "David Ellams", "Protocol Development Circle", "domain", agr_oa_uaf,
             "Framework governing Oasis's holonic data architecture for cross-chain interoperability. "
             "Covers the holon identity-first data model, HyperDrive intelligent routing with auto-replication, "
             "cross-chain NFT support (Web4 OASIS NFTs, GeoNFTs), and the Universal Asset Bridge with atomic swaps. "
             "Defines how NEOS governance records are persisted across 50+ blockchain and cloud providers "
             "(Ethereum, Solana, Polygon, MongoDB, IPFS) through Oasis's unified API layer.",
             days_ago(6), None, None, None,
             {"affected": ["node_operators", "protocol_circle", "neos_integration"]}, None),
            (agr_oa_unique, eco_oa_id, "AGR-OA-005", "policy",
             "Metaverse Governance & Digital Sovereignty Charter", "0.2", "under_review",
             "Max Gershfield", "Governance Circle", "domain", agr_oa_uaf,
             "Charter defining governance of metaverse spaces and digital twins built on the Oasis Web4 stack. "
             "Covers the STAR CLI low/no-code metaverse generator, multi-chain smart contract deployment "
             "(Ethereum, Solana, Radix), and DID-based avatar identity with karma and wallet management. "
             "Integrates NEOS ACT process for consent-based governance of shared virtual spaces "
             "and defines digital sovereignty principles for community-owned metaverse infrastructure.",
             days_ago(12), None, days_ago(1), days_from_now(180),
             {"affected": ["token_holders", "metaverse_participants", "all_members"]}, None),
        ]
        # fmt: on

        for (aid, eco_id, agr_id_str, atype, title, ver, status, proposer,
             domain, hier, parent, text_val, created, ratified, review_date,
             sunset, affected, fingerprint) in agreements_spec:
            session.add(Agreement(
                id=aid,
                ecosystem_id=eco_id,
                agreement_id=agr_id_str,
                type=atype,
                title=title,
                version=ver,
                status=status,
                proposer=proposer,
                domain=domain,
                hierarchy_level=hier,
                parent_agreement_id=parent,
                text=text_val,
                created_date=created,
                ratification_date=ratified,
                review_date=review_date,
                sunset_date=sunset,
                affected_parties=affected,
                version_fingerprint=fingerprint,
            ))

        # Link UAFs to ecosystems
        eco_omnione.uaf_agreement_id = agr_omni_uaf
        eco_escherbridge.uaf_agreement_id = agr_eb_uaf
        eco_plansystems.uaf_agreement_id = agr_ps_uaf
        eco_oasis.uaf_agreement_id = agr_oa_uaf

        await session.flush()

        # ===============================================================
        # 9. AGREEMENT RATIFICATION RECORDS (for active agreements)
        # ===============================================================
        ratification_spec = [
            # OmniOne UAF
            (agr_omni_uaf, "Josh Pasmore", "co_creator", "consent", days_ago(165)),
            (agr_omni_uaf, "Nathan R", "builder", "consent", days_ago(165)),
            (agr_omni_uaf, "Ahmed (Jade Oni)", "townhall", "consent", days_ago(165)),
            # OmniOne Decision Protocol
            (agr_omni_decision, "Josh Pasmore", "co_creator", "consent", days_ago(155)),
            (agr_omni_decision, "Nathan R", "builder", "consent", days_ago(155)),
            (agr_omni_decision, "Ahmed (Jade Oni)", "townhall", "consent", days_ago(155)),
            # OmniOne Membership
            (agr_omni_membership, "Josh Pasmore", "co_creator", "consent", days_ago(160)),
            (agr_omni_membership, "Nathan R", "builder", "consent", days_ago(160)),
            (agr_omni_membership, "Ahmed (Jade Oni)", "townhall", "consent", days_ago(160)),
            # Escherbridge UAF
            (agr_eb_uaf, "Ahmed (Jade Oni)", "co_creator", "consent", days_ago(105)),
            (agr_eb_uaf, "Kenny", "builder", "consent", days_ago(105)),
            (agr_eb_uaf, "Jak", "townhall", "consent", days_ago(105)),
            # Escherbridge Decision Protocol
            (agr_eb_decision, "Ahmed (Jade Oni)", "co_creator", "consent", days_ago(100)),
            (agr_eb_decision, "Kenny", "builder", "consent", days_ago(100)),
            # Escherbridge Membership
            (agr_eb_membership, "Ahmed (Jade Oni)", "co_creator", "consent", days_ago(100)),
            (agr_eb_membership, "Kenny", "builder", "consent", days_ago(100)),
            (agr_eb_membership, "Jak", "townhall", "consent", days_ago(100)),
            # Plan Systems UAF
            (agr_ps_uaf, "Rachel", "co_creator", "consent", days_ago(80)),
            (agr_ps_uaf, "Brandon", "builder", "consent", days_ago(80)),
            (agr_ps_uaf, "Drew", "townhall", "consent", days_ago(80)),
            # Plan Systems Decision Protocol
            (agr_ps_decision, "Rachel", "co_creator", "consent", days_ago(75)),
            (agr_ps_decision, "Brandon", "builder", "consent", days_ago(75)),
            # Plan Systems Membership
            (agr_ps_membership, "Rachel", "co_creator", "consent", days_ago(75)),
            (agr_ps_membership, "Brandon", "builder", "consent", days_ago(75)),
            (agr_ps_membership, "Drew", "townhall", "consent", days_ago(75)),
            # Oasis UAF (2 members only)
            (agr_oa_uaf, "Max Gershfield", "co_creator", "consent", days_ago(50)),
            (agr_oa_uaf, "David Ellams", "builder", "consent", days_ago(50)),
            # Oasis Decision Protocol
            (agr_oa_decision, "Max Gershfield", "co_creator", "consent", days_ago(45)),
            (agr_oa_decision, "David Ellams", "builder", "consent", days_ago(45)),
            # Oasis Membership
            (agr_oa_membership, "Max Gershfield", "co_creator", "consent", days_ago(45)),
            (agr_oa_membership, "David Ellams", "builder", "consent", days_ago(45)),
        ]

        for agr, participant, role, position, dt in ratification_spec:
            session.add(AgreementRatificationRecord(
                id=_uid(f"rat.{agr}.{participant}"),
                agreement_id=agr,
                participant=participant,
                role=role,
                position=position,
                date=dt,
            ))

        await session.flush()

        # ===============================================================
        # 10. PROPOSALS — 1 per ecosystem (4 total, all advice stage)
        # ===============================================================
        prop_omni = _uid("prop.omni.1")
        prop_eb = _uid("prop.eb.1")
        prop_ps = _uid("prop.ps.1")
        prop_oa = _uid("prop.oa.1")

        # fmt: off
        proposals_spec = [
            # (id, eco_id, prop_id_str, type, decision_type, title, version, status, proposer, domain, urgency, impacted, change, rationale, created, adv_deadline, consent_deadline, test_dur)
            (prop_omni, eco_omni_id, "PROP-OMNI-001", "policy", "consent",
             "Community Energy Sharing Protocol", "0.2", "advice",
             "Ahmed (Jade Oni)", "Core Operations", "standard", {"affected": ["energy_users", "all_members"]},
             "Establish fair distribution of solar energy credits among community members.",
             "Energy production exceeds individual use; need equitable sharing framework.",
             days_ago(10), days_ago(8), days_from_now(5), None),

            (prop_eb, eco_eb_id, "PROP-EB-001", "policy", "consent",
             "Studio Space and Equipment Sharing Protocol", "0.3", "advice",
             "Jak", "Core Operations", "standard", {"affected": ["studio_users", "exhibiting_artists"]},
             "Equitable studio time allocation and equipment booking framework.",
             "Growing membership requires clearer allocation of shared creative spaces.",
             days_ago(8), days_ago(6), days_from_now(7), None),

            (prop_ps, eco_ps_id, "PROP-PS-001", "policy", "consent",
             "Client Data Sovereignty Protocol", "0.2", "advice",
             "Brandon", "Systems Design Circle", "standard", {"affected": ["design_circle", "clients"]},
             "Establish ethical client data handling and knowledge ownership boundaries.",
             "Growing client base requires clear data sovereignty framework.",
             days_ago(7), days_ago(5), days_from_now(8), None),

            (prop_oa, eco_oa_id, "PROP-OA-001", "policy", "consent",
             "Node Operator Resource Sharing Protocol", "0.2", "advice",
             "David Ellams", "Protocol Development Circle", "standard", {"affected": ["node_operators", "protocol_circle"]},
             "Shared infrastructure costs and node operation responsibility framework.",
             "Scaling node network requires clear resource allocation.",
             days_ago(6), days_ago(4), days_from_now(9), None),
        ]
        # fmt: on

        for (pid, eco_id, prop_id_str, ptype, decision_type, title, ver,
             status, proposer, domain, urgency, impacted, change, rationale,
             created, adv_deadline, consent_deadline, test_dur) in proposals_spec:
            session.add(Proposal(
                id=pid,
                ecosystem_id=eco_id,
                proposal_id=prop_id_str,
                type=ptype,
                decision_type=decision_type,
                title=title,
                version=ver,
                status=status,
                proposer=proposer,
                affected_domain=domain,
                urgency=urgency,
                impacted_parties=impacted,
                proposed_change=change,
                rationale=rationale,
                created_date=created,
                advice_deadline=adv_deadline,
                consent_deadline=consent_deadline,
                test_duration=test_dur,
            ))

        await session.flush()

        # ===============================================================
        # 11. ADVICE LOGS — one per proposal
        # ===============================================================
        for prop_id, eco_prefix, members in [
            (prop_omni, "omni", [("Josh Pasmore", "co_creator"), ("Nathan R", "builder")]),
            (prop_eb, "eb", [("Ahmed (Jade Oni)", "co_creator"), ("Kenny", "builder")]),
            (prop_ps, "ps", [("Rachel", "co_creator"), ("Drew", "townhall")]),
            (prop_oa, "oa", [("Max Gershfield", "co_creator"), ("David Ellams", "builder")]),
        ]:
            al_id = _uid(f"advlog.{eco_prefix}.1")
            session.add(AdviceLog(
                id=al_id,
                proposal_id=prop_id,
                advice_window_start=days_ago(7),
                advice_window_end=days_from_now(7),
                urgency="standard",
                summary="Advice collection in progress",
            ))
            for advisor, role in members:
                session.add(AdviceEntry(
                    id=_uid(f"adventry.{eco_prefix}.{advisor}"),
                    advice_log_id=al_id,
                    advisor=advisor,
                    role=role,
                    date=days_ago(3),
                    advice_text=f"Supportive of the proposal direction with minor suggestions for clarity. — {advisor}",
                    integration_status="pending",
                ))

        await session.flush()

        # ===============================================================
        # 12. CONFLICT CASES — 1 per ecosystem (4 total)
        # ===============================================================
        # Map of first member per eco for reporter, second for facilitator
        conflict_spec = [
            # (eco_id, prefix, case_id, title, desc, reporter_id, facilitator_id, status, severity, tier, root_cause, domain)
            (eco_omni_id, "omni", "CONF-OMNI-001",
             "Resource allocation disagreement in community garden",
             "Disagreement between members about water allocation priorities during dry season.",
             m_nathan_id, m_josh_id, "in_progress", "medium", 2, "resource_allocation",
             "Regenerative Agriculture Circle"),
            (eco_eb_id, "eb", "CONF-EB-001",
             "Studio scheduling conflict between projects",
             "Overlapping booking claims for the main exhibition space during preparation period.",
             m_kenny_id, m_ahmed_eb_id, "reported", "low", 1, "scheduling",
             "Core Operations"),
            (eco_ps_id, "ps", "CONF-PS-001",
             "Client engagement boundary disagreement",
             "Disagreement about appropriate scope of systems design consulting engagement.",
             m_brandon_id, m_rachel_id, "in_progress", "medium", 2, "boundary",
             "Systems Design Circle"),
            (eco_oa_id, "oa", "CONF-OA-001",
             "Token governance weight dispute",
             "Dispute about proportional voting weight of early contributors versus new members.",
             m_david_id, m_max_id, "reported", "medium", 2, "governance_design",
             "Governance Circle"),
        ]

        for (eco_id, prefix, case_id, title, desc, reporter_id, facilitator_id,
             status, severity, tier, root_cause, domain) in conflict_spec:
            session.add(ConflictCase(
                id=_uid(f"conf.{prefix}"),
                ecosystem_id=eco_id,
                case_id=case_id,
                title=title,
                description=desc,
                reporter_id=reporter_id,
                facilitator_id=facilitator_id,
                status=status,
                severity=severity,
                scope="domain",
                tier=tier,
                root_cause_category=root_cause,
                urgency="standard",
                safety_flag=False,
                domain=domain,
            ))

        await session.flush()

        # ===============================================================
        # 13. DECISION RECORDS — 2 per ecosystem (8 total)
        # ===============================================================
        decision_spec = [
            # (eco_id, prefix, idx, record_id, date_offset, holding, ratio, domain, recorder, participants)
            # OmniOne
            (eco_omni_id, "omni", 1, "DEC-OMNI-001", 30,
             "Adopt weekly governance meetings on Mondays at 10am Bali time",
             "Regular meeting cadence ensures all members can participate in governance",
             "Governance Circle", "Josh Pasmore",
             [("Josh Pasmore", "co_creator", "consent"), ("Nathan R", "builder", "consent"), ("Ahmed (Jade Oni)", "townhall", "consent")]),
            (eco_omni_id, "omni", 2, "DEC-OMNI-002", 20,
             "Approve Nathan R as steward of the Regenerative Agriculture Circle",
             "Nathan has demonstrated strong community building skills and land stewardship commitment",
             "Core Operations", "Josh Pasmore",
             [("Josh Pasmore", "co_creator", "consent"), ("Ahmed (Jade Oni)", "townhall", "consent")]),
            # Escherbridge
            (eco_eb_id, "eb", 1, "DEC-EB-001", 25,
             "Adopt quarterly steward rotation for all domain circles",
             "Rotation prevents concentration of authority and develops leadership capacity",
             "Governance Circle", "Ahmed (Jade Oni)",
             [("Ahmed (Jade Oni)", "co_creator", "consent"), ("Kenny", "builder", "consent"), ("Jak", "townhall", "consent")]),
            (eco_eb_id, "eb", 2, "DEC-EB-002", 15,
             "Approve Kenny as lead for the Digital Arts & Technology Circle",
             "Kenny brings deep creative technology expertise in interactive installations and creative coding",
             "Core Operations", "Ahmed (Jade Oni)",
             [("Ahmed (Jade Oni)", "co_creator", "consent"), ("Jak", "townhall", "consent")]),
            # Plan Systems
            (eco_ps_id, "ps", 1, "DEC-PS-001", 22,
             "Adopt Wardley Mapping as standard strategic planning framework",
             "Wardley Maps provide clear visualization of value chains and strategic positioning",
             "Systems Design Circle", "Rachel",
             [("Rachel", "co_creator", "consent"), ("Brandon", "builder", "consent"), ("Drew", "townhall", "consent")]),
            (eco_ps_id, "ps", 2, "DEC-PS-002", 12,
             "Approve open-source release of the planning dashboard toolkit",
             "Open-sourcing builds community reputation and attracts talent to the cooperative",
             "Governance Circle", "Rachel",
             [("Rachel", "co_creator", "consent"), ("Brandon", "builder", "consent")]),
            # Oasis (2 members only)
            (eco_oa_id, "oa", 1, "DEC-OA-001", 18,
             "Adopt 72-hour async voting windows for all governance proposals",
             "72 hours balances urgency with global timezone coverage for remote participants",
             "Governance Circle", "Max Gershfield",
             [("Max Gershfield", "co_creator", "consent"), ("David Ellams", "builder", "consent")]),
            (eco_oa_id, "oa", 2, "DEC-OA-002", 10,
             "Approve testnet-v2 launch with smart contract governance module",
             "Testnet-v2 enables on-chain consent records and transparent decision audit trails",
             "Protocol Development Circle", "Max Gershfield",
             [("Max Gershfield", "co_creator", "consent"), ("David Ellams", "builder", "consent")]),
        ]

        for (eco_id, prefix, idx, record_id, date_offset, holding, ratio,
             domain, recorder, participants) in decision_spec:
            dec_id = _uid(f"dec.{prefix}.{idx}")
            session.add(DecisionRecord(
                id=dec_id,
                ecosystem_id=eco_id,
                record_id=record_id,
                date=days_ago(date_offset),
                holding=holding,
                ratio_decidendi=ratio,
                domain=domain,
                precedent_level="binding",
                status="active",
                recorder=recorder,
                recorder_role="co_creator" if recorder in ("Josh Pasmore", "Ahmed (Jade Oni)", "Rachel", "Max Gershfield") else "builder",
                review_date=days_from_now(180),
            ))
            for pname, prole, pposition in participants:
                session.add(DecisionParticipant(
                    id=_uid(f"decpart.{prefix}.{idx}.{pname}"),
                    decision_record_id=dec_id,
                    name=pname,
                    role=prole,
                    position=pposition,
                ))
            session.add(DecisionSemanticTag(
                id=_uid(f"dectag.{prefix}.{idx}"),
                decision_record_id=dec_id,
                topic={"category": domain},
                affected_parties={"circle": domain},
                ecosystem_scope="internal",
                urgency_at_time="standard",
            ))

        await session.flush()

        # ===============================================================
        # 14. GOVERNANCE HEALTH AUDITS — 1 per ecosystem (4 total)
        # ===============================================================
        audit_spec = [
            (eco_omni_id, "omni", "AUD-OMNI-001", "Josh Pasmore", 85,
             "Strong governance participation. ACT process well understood. Minor gap in documentation practices.",
             ["Improve decision record documentation", "Establish peer review for agreements"]),
            (eco_eb_id, "eb", "AUD-EB-001", "Ahmed (Jade Oni)", 78,
             "Good creative engagement but governance participation uneven. Steward rotation working well.",
             ["Increase townhall participation in governance meetings", "Standardize proposal templates"]),
            (eco_ps_id, "ps", "AUD-PS-001", "Rachel", 82,
             "Solid systems-based governance. Strong documentation culture. Client boundary clarity could improve.",
             ["Formalize client engagement boundaries", "Add quarterly retrospectives"]),
            (eco_oa_id, "oa", "AUD-OA-001", "Max Gershfield", 75,
             "Async governance working but participation lag is a concern. Token governance model still maturing.",
             ["Shorten voting windows for low-impact decisions", "Improve onboarding for governance participation"]),
        ]

        for eco_id, prefix, audit_id, auditor, score, findings, recs in audit_spec:
            session.add(GovernanceHealthAudit(
                id=_uid(f"audit.{prefix}"),
                ecosystem_id=eco_id,
                audit_id=audit_id,
                audit_date=days_ago(15),
                auditor=auditor,
                capture_risk_indicators={"power_concentration": "low", "participation_gap": "moderate"},
                overall_health_score=score,
                findings=findings,
                recommendations=recs,
                status="completed",
                next_audit_date=days_from_now(75),
            ))

        await session.flush()

        # ===============================================================
        # 15. CIRCLE MEMBERSHIPS — all 3 members in all 3 domains per eco
        # ===============================================================
        eco_member_domain_map = [
            # OmniOne: Josh, Nathan, Ahmed in all 3 domains
            (m_josh_id,   [dom_omni_ops_id, dom_omni_gov_id, dom_omni_regen_id]),
            (m_nathan_id, [dom_omni_ops_id, dom_omni_gov_id, dom_omni_regen_id]),
            (m_ahmed_id,  [dom_omni_ops_id, dom_omni_gov_id, dom_omni_regen_id]),
            # Escherbridge: Ahmed(EB), Kenny, Jak in all 3 domains
            (m_ahmed_eb_id, [dom_eb_ops_id, dom_eb_gov_id, dom_eb_art_id]),
            (m_kenny_id,   [dom_eb_ops_id, dom_eb_gov_id, dom_eb_art_id]),
            (m_jak_id,     [dom_eb_ops_id, dom_eb_gov_id, dom_eb_art_id]),
            # Plan Systems: Rachel, Brandon, Drew in all 3 domains
            (m_rachel_id,  [dom_ps_ops_id, dom_ps_gov_id, dom_ps_design_id]),
            (m_brandon_id, [dom_ps_ops_id, dom_ps_gov_id, dom_ps_design_id]),
            (m_drew_id,    [dom_ps_ops_id, dom_ps_gov_id, dom_ps_design_id]),
            # Oasis: Max, David in all 3 domains (2 members only)
            (m_max_id,   [dom_oa_ops_id, dom_oa_gov_id, dom_oa_protocol_id]),
            (m_david_id, [dom_oa_ops_id, dom_oa_gov_id, dom_oa_protocol_id]),
        ]

        # Stewards for role assignment
        steward_domains = {
            dom_omni_ops_id: m_josh_id, dom_omni_gov_id: m_josh_id, dom_omni_regen_id: m_nathan_id,
            dom_eb_ops_id: m_ahmed_eb_id, dom_eb_gov_id: m_ahmed_eb_id, dom_eb_art_id: m_kenny_id,
            dom_ps_ops_id: m_rachel_id, dom_ps_gov_id: m_rachel_id, dom_ps_design_id: m_rachel_id,
            dom_oa_ops_id: m_max_id, dom_oa_gov_id: m_max_id, dom_oa_protocol_id: m_david_id,
        }

        for member_id, domain_ids in eco_member_domain_map:
            for dom_id in domain_ids:
                role = "steward" if steward_domains.get(dom_id) == member_id else "member"
                session.add(CircleMembership(
                    id=_uid(f"cm.{member_id}.{dom_id}"),
                    domain_id=dom_id,
                    member_id=member_id,
                    role=role,
                    joined_date=days_ago(50),
                    status="active",
                ))

        await session.flush()

        # ===============================================================
        # 16. SHARES & NEEDS — 2 per ecosystem (1 share, 1 need) = 8 total
        # ===============================================================
        shares_needs_spec = [
            # (eco_id, domain_id, prefix, type, title, desc, category, capacity, tags)
            (eco_omni_id, dom_omni_regen_id, "omni.share", "share",
             "Regenerative Community Digital Twin Data",
             "OmniOne can share geo-spatial land zone data, permaculture design patterns, and real-time sensor feeds "
             "for building spatial digital twins of regenerative community sites.",
             "knowledge", "ongoing",
             ["digital-twin", "geo-spatial", "permaculture", "sensor-data"]),
            (eco_omni_id, dom_omni_ops_id, "omni.need", "need",
             "NEOS Platform & Metaverse Integration Development",
             "OmniOne needs help building its NEOS governance platform integration and connecting "
             "spatial digital twin data to Web4 cross-chain infrastructure.",
             "skill", "high",
             ["neos-platform", "web3", "metaverse", "cross-chain"]),

            (eco_eb_id, dom_eb_art_id, "eb.share", "share",
             "Metaverse Creative Technology & VR Experience Development",
             "Escherbridge can contribute immersive VR/AR experiences, AI agentic creative tooling, "
             "and full-stack development expertise for metaverse and digital twin platforms.",
             "skill", "quarterly",
             ["metaverse", "vr-ar", "agentic-ai", "creative-coding", "full-stack"]),
            (eco_eb_id, dom_eb_ops_id, "eb.need", "need",
             "Cross-Chain NFT & Digital Sovereignty Infrastructure",
             "Escherbridge needs Web4 cross-chain interoperability for digital art provenance, "
             "NFT minting across multiple chains, and holonic data persistence for creative assets.",
             "knowledge", "moderate",
             ["cross-chain", "nft", "digital-sovereignty", "web4"]),

            (eco_ps_id, dom_ps_design_id, "ps.share", "share",
             "PLAN 3D Spatial Collaboration Platform & Digital Twin SDK",
             "Plan Systems can share its PLAN 3D platform for real-time spatial collaboration, "
             "PLAN-Unity SDK for 3D model packaging, and spatial linking infrastructure "
             "for next-gen hyperlinks in digital twin environments.",
             "resource", "ongoing",
             ["plan-3d", "digital-twin", "spatial-collaboration", "unity-sdk"]),
            (eco_ps_id, dom_ps_ops_id, "ps.need", "need",
             "Decentralized Governance & Web3 Identity Integration",
             "Plan Systems needs DID-based identity and NEOS governance integration for its "
             "5G broadband communities and STEM education platforms.",
             "skill", "moderate",
             ["did-identity", "neos-governance", "web3", "community-broadband"]),

            (eco_oa_id, dom_oa_protocol_id, "oa.share", "share",
             "Web4 Holonic Cross-Chain Infrastructure & Metaverse Toolkit",
             "Oasis can share its holonic interoperability layer, Universal Asset Bridge, "
             "STAR CLI metaverse generator, and cross-chain smart contract deployment across "
             "50+ providers (Ethereum, Solana, IPFS, MongoDB, etc.).",
             "resource", "ongoing",
             ["web4", "holonic", "cross-chain", "metaverse", "smart-contracts"]),
            (eco_oa_id, dom_oa_ops_id, "oa.need", "need",
             "Physical Community Digital Twin & Spatial Governance Data",
             "Oasis needs real-world community governance data and spatial digital twin assets "
             "to validate its Web4 metaverse governance model against place-based communities.",
             "knowledge", "high",
             ["digital-twin", "spatial-governance", "place-based", "real-world-data"]),
        ]

        for (eco_id, domain_id, prefix, sn_type, title, desc, category,
             capacity, tags) in shares_needs_spec:
            session.add(SharesNeeds(
                id=_uid(f"sn.{prefix}"),
                ecosystem_id=eco_id,
                domain_id=domain_id,
                type=sn_type,
                title=title,
                description=desc,
                category=category,
                capacity=capacity,
                tags=tags,
                visibility="public",
                status="active",
            ))

        await session.flush()

        # ===============================================================
        # 17. COLLABORATIONS — 2 cross-ecosystem
        # ===============================================================
        # OmniOne <-> Plan Systems (active, cooperate tier)
        # Digital twin of OmniOne Bali site using PLAN 3D
        session.add(Collaboration(
            id=_uid("collab.omni_ps"),
            source_domain_id=dom_omni_gov_id,
            target_domain_id=dom_ps_design_id,
            title="OmniOne Digital Twin & PLAN 3D Spatial Governance",
            description=(
                "Active collaboration to build a spatial digital twin of the OmniOne Bali community "
                "using Plan Systems' PLAN 3D platform. OmniOne provides governance domain data and "
                "geo-spatial land zone maps; Plan Systems contributes PLAN-Unity SDK for 3D model packaging "
                "into deployable Crates with spatial linking. The digital twin enables real-time governance "
                "visualization, emergency response coordination, and NEOS ACT process spatial overlays. "
                "Broadband connectivity provided through Plan Systems' 5G infrastructure."
            ),
            status="active",
            engagement_tier="cooperate",
            terms={"meetings": "biweekly", "knowledge_sharing": True, "joint_workshops": 3,
                   "deliverables": ["3d_site_model", "spatial_governance_overlay", "emergency_response_map"]},
            linked_shares_needs={"source_need": str(_uid("sn.omni.need")), "target_share": str(_uid("sn.ps.share"))},
            started_date=days_ago(30),
            review_date=days_from_now(60),
            version_fingerprint="collab-omni-ps-v1",
        ))

        # Escherbridge <-> Oasis (proposed, observe tier)
        # Metaverse art + Web4 cross-chain NFT provenance
        session.add(Collaboration(
            id=_uid("collab.eb_oa"),
            source_domain_id=dom_eb_art_id,
            target_domain_id=dom_oa_protocol_id,
            title="Metaverse Art Provenance & Web4 Cross-Chain NFT Pipeline",
            description=(
                "Proposed collaboration between Escherbridge's creative technology studio and "
                "Oasis's Web4 protocol infrastructure. Escherbridge contributes immersive art installations, "
                "VR experiences (ComeAlongSide heritage), and AI-powered creative tooling. "
                "Oasis provides holonic cross-chain interoperability for NFT provenance across Ethereum, "
                "Solana, and Polygon via the Universal Asset Bridge. Goal: a consent-governed metaverse gallery "
                "where digital art ownership and provenance are managed through NEOS governance and "
                "Oasis GeoNFTs with spatial metadata from Plan Systems' PLAN 3D."
            ),
            status="proposed",
            engagement_tier="observe",
            terms={"initial_call": True, "exploration_period": "90 days",
                   "poc_deliverable": "cross_chain_nft_gallery_prototype"},
            linked_shares_needs={"source_share": str(_uid("sn.eb.share")), "target_share": str(_uid("sn.oa.share"))},
            started_date=None,
            review_date=days_from_now(90),
            version_fingerprint="collab-eb-oa-v1",
        ))

        await session.flush()

        # ===============================================================
        # 18. COMPLIANCE SUMMARIES — 1 per ecosystem (4 total)
        # ===============================================================
        compliance_spec = [
            (eco_omni_id, "omni",
             "OmniOne governance compliance is strong. All core agreements are active and ratified. "
             "Resource sharing framework is in advice stage. Land stewardship charter in draft.",
             {"overall": 88, "agreement_coverage": 85, "participation": 90, "documentation": 80},
             {"UAF": "compliant", "Decision Protocol": "compliant", "Membership": "compliant"},
             {"Core Operations": "healthy", "Governance Circle": "healthy", "Regen Circle": "healthy"},
             [{"issue": "Resource sharing framework not yet ratified", "severity": "low"}]),
            (eco_eb_id, "eb",
             "Escherbridge governance is functioning well with creative adaptations. "
             "Artist residency charter under review. Studio allocation framework in advice stage.",
             {"overall": 82, "agreement_coverage": 80, "participation": 78, "documentation": 85},
             {"UAF": "compliant", "Decision Protocol": "compliant", "Membership": "compliant"},
             {"Core Operations": "healthy", "Governance Circle": "moderate", "Digital Arts": "healthy"},
             [{"issue": "Governance circle participation below target", "severity": "medium"}]),
            (eco_ps_id, "ps",
             "Plan Systems governance is well-structured with strong documentation practices. "
             "Client data sovereignty framework in advice stage. Certification program in draft.",
             {"overall": 85, "agreement_coverage": 82, "participation": 85, "documentation": 92},
             {"UAF": "compliant", "Decision Protocol": "compliant", "Membership": "compliant"},
             {"Core Operations": "healthy", "Governance Circle": "healthy", "Systems Design": "healthy"},
             [{"issue": "Client engagement boundaries need formalization", "severity": "low"}]),
            (eco_oa_id, "oa",
             "Oasis governance is adapting well to async-first model. Token governance charter "
             "under review. Node operator resource framework in advice stage.",
             {"overall": 78, "agreement_coverage": 75, "participation": 72, "documentation": 80},
             {"UAF": "compliant", "Decision Protocol": "compliant", "Membership": "compliant"},
             {"Core Operations": "healthy", "Governance Circle": "moderate", "Protocol Dev": "healthy"},
             [{"issue": "Async voting participation below target", "severity": "medium"},
              {"issue": "Token governance model needs broader ratification", "severity": "medium"}]),
        ]

        for eco_id, prefix, summary, scores, agreement_cov, domain_health, flagged in compliance_spec:
            session.add(ComplianceSummary(
                id=_uid(f"compliance.{prefix}"),
                ecosystem_id=eco_id,
                generated_at=hours_ago(24),
                summary=summary,
                score_data=scores,
                agreement_coverage=agreement_cov,
                domain_health=domain_health,
                flagged_issues=flagged,
            ))

        await session.flush()

        # ===============================================================
        # 19. EMERGENCY STATE — 1 (OmniOne, closed)
        # ===============================================================
        session.add(EmergencyState(
            id=_uid("emerg.omni.storm"),
            ecosystem_id=eco_omni_id,
            state="closed",
            declared_at=hours_ago(336),  # ~14 days ago
            declared_by="Josh Pasmore",
            criteria_met={"trigger": "severe_weather", "category": "natural_disaster", "affected_zones": ["farm", "housing"]},
            auto_revert_at=hours_ago(264),  # auto-revert was set 3 days after declaration
            recovery_entered_at=hours_ago(312),  # recovery entered 1 day after declaration
            closed_at=hours_ago(288),  # closed after 48h stable conditions
            pre_authorized_roles=["steward", "emergency_coordinator"],
            actions_log=[
                {"time": str(hours_ago(336)), "action": "Emergency declared: tropical storm approaching", "actor": "Josh Pasmore"},
                {"time": str(hours_ago(330)), "action": "Secured outdoor equipment and garden infrastructure", "actor": "Nathan R"},
                {"time": str(hours_ago(324)), "action": "Opened community shelter in main hall", "actor": "Ahmed (Jade Oni)"},
                {"time": str(hours_ago(312)), "action": "Storm passed, entered recovery phase", "actor": "Josh Pasmore"},
                {"time": str(hours_ago(288)), "action": "Emergency closed after 48h stable conditions", "actor": "Josh Pasmore"},
            ],
            post_review_status="completed",
            notes=(
                "Post-emergency review completed. Storm damage was manageable due to "
                "quick response. Decision to improve drainage and add storm shutters. "
                "Emergency fund of 500 USD allocated for future weather events."
            ),
        ))

        # ===============================================================
        # 20. EXIT RECORD — 1 (OmniOne, Rua)
        # ===============================================================
        session.add(ExitRecord(
            id=_uid("exit.omni.rua"),
            ecosystem_id=eco_omni_id,
            member_id=m_rua_id,
            exit_type="standard",
            status="completed",
            declared_date=days_ago(60),
            target_completion_date=days_ago(30),
            coordinator_id=m_josh_id,
            commitment_inventory=[
                {"commitment": "Workshop Thursday shifts", "status": "transferred_to_Nathan"},
                {"commitment": "Event planning role", "status": "transferred_to_Ahmed"},
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

        # ===============================================================
        # 21. ADDITIONAL PROPOSALS — 8 more across different ACT phases
        # ===============================================================
        # 2 draft proposals
        prop_omni_draft = _uid("prop.omni.draft1")
        prop_ps_draft = _uid("prop.ps.draft1")
        # 2 consent proposals
        prop_eb_consent = _uid("prop.eb.consent1")
        prop_oa_consent = _uid("prop.oa.consent1")
        # 2 test proposals
        prop_omni_test = _uid("prop.omni.test1")
        prop_eb_test = _uid("prop.eb.test1")
        # 1 ratified proposal
        prop_ps_ratified = _uid("prop.ps.ratified1")
        # 1 withdrawn proposal
        prop_oa_withdrawn = _uid("prop.oa.withdrawn1")

        # fmt: off
        extra_proposals_spec = [
            # ── Draft proposals ──
            (prop_omni_draft, eco_omni_id, "PROP-OMNI-002", "policy", "consent",
             "Permaculture Knowledge Commons Charter", "0.1", "draft",
             "Nathan R", "Regenerative Agriculture Circle", "standard",
             {"affected": ["regen_circle", "all_members"]},
             "Create an open knowledge commons for permaculture practices, seed-saving protocols, and harvest data.",
             "Community knowledge is currently siloed; a shared commons would accelerate learning and food sovereignty.",
             days_ago(3), None, None, None),

            (prop_ps_draft, eco_ps_id, "PROP-PS-002", "operational", "consent",
             "5G Community Broadband Governance Framework", "0.1", "draft",
             "Drew", "Core Operations", "standard",
             {"affected": ["broadband_users", "design_circle"]},
             "Establish governance rules for community-owned 5G broadband infrastructure including fair-use policies.",
             "Expanding broadband service to new neighborhoods requires clear governance and cost-sharing rules.",
             days_ago(2), None, None, None),

            # ── Consent proposals (need advice logs + advice entries) ──
            (prop_eb_consent, eco_eb_id, "PROP-EB-002", "policy", "consent",
             "Artist Residency and Exhibition Revenue Sharing", "0.4", "consent",
             "Kenny", "Digital Arts & Technology Circle", "standard",
             {"affected": ["studio_users", "exhibiting_artists", "all_members"]},
             "Define revenue sharing model for exhibitions and artist residency fees to sustain creative spaces.",
             "Current ad-hoc arrangements lead to disputes; a transparent model builds trust.",
             days_ago(20), days_ago(18), days_from_now(3), None),

            (prop_oa_consent, eco_oa_id, "PROP-OA-002", "operational", "consent",
             "Cross-Chain Identity Verification Protocol", "0.3", "consent",
             "Max Gershfield", "Governance Circle", "high",
             {"affected": ["all_members", "node_operators"]},
             "Implement DID-based identity verification across all supported blockchains for governance participation.",
             "Growing network requires consistent identity verification to prevent sybil attacks in governance votes.",
             days_ago(18), days_ago(15), days_from_now(5), None),

            # ── Test proposals (need advice logs, consent records, consent participants) ──
            (prop_omni_test, eco_omni_id, "PROP-OMNI-003", "resource", "consent",
             "Shared Solar Energy Credit Distribution System", "1.0", "test",
             "Josh Pasmore", "Core Operations", "standard",
             {"affected": ["energy_users", "all_members"]},
             "Implement a solar credit system distributing surplus energy credits proportionally based on household size.",
             "Solar array produces 40%% surplus; fair distribution needed before wet season maintenance.",
             days_ago(45), days_ago(42), days_ago(25), "60 days"),

            (prop_eb_test, eco_eb_id, "PROP-EB-003", "operational", "consent",
             "Creative Commons Licensing Framework for Collaborative Works", "1.0", "test",
             "Ahmed (Jade Oni)", "Governance Circle", "standard",
             {"affected": ["studio_users", "exhibiting_artists"]},
             "Adopt CC BY-SA 4.0 as default license for collaborative works created in Escherbridge studios.",
             "Multiple artists contributing to installations need clear IP framework to prevent future disputes.",
             days_ago(40), days_ago(38), days_ago(20), "90 days"),

            # ── Ratified proposal (needs full ACT chain: advice, consent, test report) ──
            (prop_ps_ratified, eco_ps_id, "PROP-PS-003", "policy", "consent",
             "Open-Source Contribution and Attribution Policy", "1.0", "ratified",
             "Rachel", "Governance Circle", "standard",
             {"affected": ["all_members", "design_circle"]},
             "Codify attribution requirements and contribution guidelines for all Plan Systems open-source projects.",
             "Growing open-source portfolio needs clear contributor agreement and attribution standards.",
             days_ago(60), days_ago(55), days_ago(35), "30 days"),

            # ── Withdrawn proposal ──
            (prop_oa_withdrawn, eco_oa_id, "PROP-OA-003", "policy", "consent",
             "Mandatory Token Staking for Governance Votes", "0.2", "withdrawn",
             "David Ellams", "Protocol Development Circle", "standard",
             {"affected": ["token_holders", "all_members"]},
             "Require minimum token stake of 100 OASIS tokens to participate in governance voting.",
             "Prevent low-commitment spam votes on protocol changes.",
             days_ago(30), days_ago(28), None, None),
        ]
        # fmt: on

        for (pid, eco_id, prop_id_str, ptype, decision_type, title, ver,
             status, proposer, domain, urgency, impacted, change, rationale,
             created, adv_deadline, consent_deadline, test_dur) in extra_proposals_spec:
            session.add(Proposal(
                id=pid,
                ecosystem_id=eco_id,
                proposal_id=prop_id_str,
                type=ptype,
                decision_type=decision_type,
                title=title,
                version=ver,
                status=status,
                proposer=proposer,
                affected_domain=domain,
                urgency=urgency,
                impacted_parties=impacted,
                proposed_change=change,
                rationale=rationale,
                created_date=created,
                advice_deadline=adv_deadline,
                consent_deadline=consent_deadline,
                test_duration=test_dur,
            ))

        await session.flush()

        # ===============================================================
        # 22. ADVICE LOGS & ENTRIES for consent/test/ratified proposals
        # ===============================================================
        extra_advice_spec = [
            # (proposal_id, eco_prefix, idx, advisors, window_start_ago, window_end_ago, summary)
            (prop_eb_consent, "eb", "consent1",
             [("Ahmed (Jade Oni)", "co_creator"), ("Jak", "townhall")],
             18, 10, "Advice collected. Revenue sharing percentages debated; consensus forming around 70/30 split."),
            (prop_oa_consent, "oa", "consent1",
             [("David Ellams", "builder")],
             15, 8, "Advice collected. Technical feasibility confirmed. Privacy concerns raised and addressed."),
            (prop_omni_test, "omni", "test1",
             [("Nathan R", "builder"), ("Ahmed (Jade Oni)", "townhall")],
             42, 30, "Advice phase completed. Strong support for proportional distribution model."),
            (prop_eb_test, "eb", "test1",
             [("Kenny", "builder"), ("Jak", "townhall")],
             38, 28, "Advice phase completed. CC BY-SA 4.0 preferred over more restrictive alternatives."),
            (prop_ps_ratified, "ps", "ratified1",
             [("Brandon", "builder"), ("Drew", "townhall")],
             55, 45, "Advice phase completed. Strong consensus on Apache-2.0 compatible attribution model."),
        ]

        for (prop_id, prefix, idx, advisors, ws_ago, we_ago, summary) in extra_advice_spec:
            al_id = _uid(f"advlog.{prefix}.{idx}")
            session.add(AdviceLog(
                id=al_id,
                proposal_id=prop_id,
                advice_window_start=days_ago(ws_ago),
                advice_window_end=days_ago(we_ago),
                urgency="standard",
                summary=summary,
            ))
            for advisor, role in advisors:
                session.add(AdviceEntry(
                    id=_uid(f"adventry.{prefix}.{idx}.{advisor}"),
                    advice_log_id=al_id,
                    advisor=advisor,
                    role=role,
                    date=days_ago(we_ago + 2),
                    advice_text=f"Reviewed proposal thoroughly. Supportive with minor amendments suggested. -- {advisor}",
                    integration_status="integrated",
                ))

        await session.flush()

        # ===============================================================
        # 23. CONSENT RECORDS & PARTICIPANTS for test/ratified proposals
        # ===============================================================
        consent_spec = [
            # (proposal_id, prefix, idx, mode, facilitator, date_ago, outcome, version,
            #  participants: [(name, role, ethos, position, reason)])
            (prop_omni_test, "omni", "test1", "standard", "Josh Pasmore", 25, "consent_given", "1.0",
             [("Josh Pasmore", "co_creator", "steward", "consent", "Proportional model is fair and transparent"),
              ("Nathan R", "builder", "builder", "consent", "Aligns with regenerative values"),
              ("Ahmed (Jade Oni)", "townhall", "participant", "consent", "Good starting point for energy equity")]),
            (prop_eb_test, "eb", "test1", "standard", "Ahmed (Jade Oni)", 20, "consent_given", "1.0",
             [("Ahmed (Jade Oni)", "co_creator", "steward", "consent", "CC BY-SA protects collective while enabling sharing"),
              ("Kenny", "builder", "builder", "consent", "Standard license reduces friction for collaborations"),
              ("Jak", "townhall", "participant", "consent", "Clear framework prevents future IP disputes")]),
            (prop_ps_ratified, "ps", "ratified1", "standard", "Rachel", 35, "consent_given", "1.0",
             [("Rachel", "co_creator", "steward", "consent", "Essential for scaling our open-source portfolio"),
              ("Brandon", "builder", "builder", "consent", "Clear attribution builds contributor trust"),
              ("Drew", "townhall", "participant", "consent", "Good documentation standard for the cooperative")]),
        ]

        for (prop_id, prefix, idx, mode, facilitator, date_ago, outcome, version, participants) in consent_spec:
            cr_id = _uid(f"consent.{prefix}.{idx}")
            session.add(ConsentRecord(
                id=cr_id,
                proposal_id=prop_id,
                consent_mode=mode,
                facilitator=facilitator,
                date=days_ago(date_ago),
                quorum_required="all_active",
                quorum_met=True,
                outcome=outcome,
                final_proposal_version=version,
            ))
            for pname, prole, pethos, pposition, preason in participants:
                session.add(ConsentParticipant(
                    id=_uid(f"cpart.{prefix}.{idx}.{pname}"),
                    consent_record_id=cr_id,
                    name=pname,
                    role=prole,
                    ethos=pethos,
                    position=pposition,
                    reason=preason,
                    round=1,
                ))

        await session.flush()

        # ===============================================================
        # 24. TEST REPORTS & SUCCESS CRITERIA for test/ratified proposals
        # ===============================================================
        test_report_spec = [
            # (proposal_id, prefix, idx, start_ago, end_ago_or_future, midpoint_ago, outcome,
            #  observations, midpoint_findings, criteria: [(criterion, met, evidence)])
            (prop_omni_test, "omni", "test1", 24, -36, 12,
             "in_progress",
             "Solar credit distribution running smoothly. Two minor adjustments to household size calculations.",
             "Midpoint: 85% member satisfaction. Minor recalibration needed for multi-unit households.",
             [("Energy credits distributed within 24h of generation", True, "Automated system logs show consistent <12h distribution"),
              ("No member receives less than base allocation", True, "All 3 active members above minimum threshold"),
              ("System handles seasonal variation", False, "Wet season data collection still in progress")]),
            (prop_eb_test, "eb", "test1", 19, -71, 10,
             "in_progress",
             "CC BY-SA 4.0 adoption proceeding well. Two collaborative pieces created under new framework.",
             "Midpoint: Artists report clearer expectations. One edge case with pre-existing IP needs resolution.",
             [("All new collaborative works tagged with CC BY-SA 4.0 metadata", True, "3 of 3 new works correctly tagged"),
              ("Attribution chain traceable for all contributors", True, "Contributor log maintained per work"),
              ("No IP disputes during test period", True, "Zero disputes filed; one pre-existing case grandfathered")]),
            (prop_ps_ratified, "ps", "ratified1", 34, 4, 20,
             "passed",
             "Attribution policy tested across 3 open-source releases. Strong contributor adoption.",
             "Midpoint: All releases compliant. Contributors report clarity improvement over previous ad-hoc approach.",
             [("All releases include CONTRIBUTORS.md with proper attribution", True, "3/3 releases compliant"),
              ("New contributor onboarding time reduced by 30%", True, "Average onboarding: 2 days vs previous 4 days"),
              ("Zero attribution disputes during test period", True, "No disputes filed in 30-day window")]),
        ]

        for (prop_id, prefix, idx, start_ago, end_offset, mid_ago,
             outcome, observations, midpoint, criteria) in test_report_spec:
            tr_id = _uid(f"testreport.{prefix}.{idx}")
            end_date = days_ago(-end_offset) if end_offset < 0 else days_ago(end_offset)
            session.add(TestReport(
                id=tr_id,
                proposal_id=prop_id,
                test_start_date=days_ago(start_ago),
                test_end_date=end_date,
                midpoint_checkin_date=days_ago(mid_ago),
                revert_procedure=f"Revert to previous process within 48 hours if test fails.",
                observations=observations,
                midpoint_findings=midpoint,
                outcome=outcome,
                success_criteria_summary=f"{sum(1 for _, m, _ in criteria if m)}/{len(criteria)} criteria met",
            ))
            for criterion, met, evidence in criteria:
                session.add(TestSuccessCriterion(
                    id=_uid(f"tsc.{prefix}.{idx}.{criterion[:20]}"),
                    test_report_id=tr_id,
                    criterion=criterion,
                    met=met,
                    evidence=evidence,
                ))

        await session.flush()

        # ===============================================================
        # 25. ADDITIONAL AGREEMENTS — varied statuses
        # ===============================================================
        agr_omni_advice = _uid("agr.omni.advice1")
        agr_eb_advice = _uid("agr.eb.advice1")
        agr_ps_review = _uid("agr.ps.review1")
        agr_oa_review = _uid("agr.oa.review1")
        agr_omni_sunset = _uid("agr.omni.sunset1")
        agr_eb_archived = _uid("agr.eb.archived1")

        # fmt: off
        extra_agreements_spec = [
            # ── Advice status ──
            (agr_omni_advice, eco_omni_id, "AGR-OMNI-006", "operational",
             "Water Catchment and Irrigation Sharing Protocol", "0.2", "advice",
             "Nathan R", "Regenerative Agriculture Circle", "domain", agr_omni_uaf,
             "Protocol for equitable distribution of rainwater catchment and irrigation resources across garden zones.",
             days_ago(12), None, None, None,
             {"affected": ["regen_circle", "all_members"]}, None),
            (agr_eb_advice, eco_eb_id, "AGR-EB-006", "policy",
             "AI-Assisted Creative Tooling Ethics Charter", "0.1", "advice",
             "Kenny", "Digital Arts & Technology Circle", "domain", agr_eb_uaf,
             "Ethical guidelines for using AI generative tools in collaborative art projects, covering attribution and consent.",
             days_ago(9), None, None, None,
             {"affected": ["studio_users", "tech_team"]}, None),

            # ── Under review status ──
            (agr_ps_review, eco_ps_id, "AGR-PS-006", "operational",
             "Remote Work and Async Collaboration Policy", "1.1", "under_review",
             "Brandon", "Core Operations", "domain", agr_ps_uaf,
             "Updated policy for remote work arrangements, async communication norms, and meeting-free deep work blocks.",
             days_ago(30), days_ago(25), days_ago(5), days_from_now(60),
             {"affected": ["all_members"]}, "remote-ps-v1.1-sha256xyz"),
            (agr_oa_review, eco_oa_id, "AGR-OA-006", "resource",
             "Node Operator SLA and Uptime Commitment", "1.0", "under_review",
             "David Ellams", "Protocol Development Circle", "domain", agr_oa_uaf,
             "Service level agreement defining minimum uptime, response times, and penalty framework for node operators.",
             days_ago(25), days_ago(20), days_ago(3), days_from_now(45),
             {"affected": ["node_operators", "protocol_circle"]}, "sla-oa-v1-sha256qrs"),

            # ── Sunset status ──
            (agr_omni_sunset, eco_omni_id, "AGR-OMNI-007", "operational",
             "Temporary Visitor Accommodation Guidelines (v1)", "1.0", "sunset",
             "Josh Pasmore", "Core Operations", "domain", agr_omni_uaf,
             "Original visitor accommodation guidelines being replaced by updated version with capacity limits.",
             days_ago(150), days_ago(145), days_ago(10), days_from_now(20),
             {"affected": ["all_members"]}, "visitor-omni-v1-sha256sun"),

            # ── Archived status ──
            (agr_eb_archived, eco_eb_id, "AGR-EB-007", "policy",
             "Pop-Up Gallery Event Protocol (2025)", "1.0", "archived",
             "Ahmed (Jade Oni)", "Core Operations", "domain", agr_eb_uaf,
             "Archived protocol from 2025 pop-up gallery series. Superseded by permanent exhibition space agreement.",
             days_ago(200), days_ago(195), days_ago(60), days_ago(30),
             {"affected": ["exhibiting_artists"]}, "popup-eb-v1-sha256arc"),
        ]
        # fmt: on

        for (aid, eco_id, agr_id_str, atype, title, ver, status, proposer,
             domain, hier, parent, text_val, created, ratified, review_date,
             sunset, affected, fingerprint) in extra_agreements_spec:
            session.add(Agreement(
                id=aid,
                ecosystem_id=eco_id,
                agreement_id=agr_id_str,
                type=atype,
                title=title,
                version=ver,
                status=status,
                proposer=proposer,
                domain=domain,
                hierarchy_level=hier,
                parent_agreement_id=parent,
                text=text_val,
                created_date=created,
                ratification_date=ratified,
                review_date=review_date,
                sunset_date=sunset,
                affected_parties=affected,
                version_fingerprint=fingerprint,
            ))

        await session.flush()

        # ===============================================================
        # 26. ADDITIONAL CONFLICTS + REPAIR AGREEMENTS
        # ===============================================================
        # 2 more conflicts
        conf_omni_2 = _uid("conf.omni.2")
        conf_ps_2 = _uid("conf.ps.2")

        session.add(ConflictCase(
            id=conf_omni_2,
            ecosystem_id=eco_omni_id,
            case_id="CONF-OMNI-002",
            title="Visitor accommodation policy disagreement",
            description=(
                "Disagreement about maximum visitor stays and whether long-term visitors "
                "should transition to formal membership after 30 days."
            ),
            reporter_id=m_ahmed_id,
            facilitator_id=m_josh_id,
            status="resolved",
            severity="low",
            scope="ecosystem",
            tier=1,
            root_cause_category="policy_gap",
            urgency="standard",
            safety_flag=False,
            domain="Core Operations",
        ))

        session.add(ConflictCase(
            id=conf_ps_2,
            ecosystem_id=eco_ps_id,
            case_id="CONF-PS-002",
            title="Open-source contribution credit dispute",
            description=(
                "Dispute over attribution of a major framework contribution between "
                "two members who collaborated on the work asynchronously."
            ),
            reporter_id=m_drew_id,
            facilitator_id=m_rachel_id,
            status="in_progress",
            severity="high",
            scope="domain",
            tier=3,
            root_cause_category="attribution",
            urgency="high",
            safety_flag=False,
            domain="Systems Design Circle",
        ))

        await session.flush()

        # Repair agreements for the resolved OmniOne conflict and the original EB conflict
        session.add(RepairAgreementRecord(
            id=_uid("repair.omni.2"),
            conflict_case_id=conf_omni_2,
            title="Visitor Accommodation Policy Repair Commitments",
            commitments={
                "items": [
                    "Update visitor policy with 30-day maximum stay clause",
                    "Create visitor-to-member transition pathway document",
                    "Host community discussion on welcoming practices",
                ]
            },
            responsible_party="Josh Pasmore",
            status="completed",
            checkin_30_date=days_ago(30),
            checkin_30_notes="Policy updated and shared with all members. Positive reception.",
            checkin_60_date=days_ago(5),
            checkin_60_notes="Two visitors have used the transition pathway successfully.",
            completed_date=days_ago(5),
        ))

        session.add(RepairAgreementRecord(
            id=_uid("repair.eb.1"),
            conflict_case_id=_uid("conf.eb"),  # the original Escherbridge conflict
            title="Studio Scheduling Repair Commitments",
            commitments={
                "items": [
                    "Implement shared calendar with 48h advance booking requirement",
                    "Designate priority slots for exhibition prep (2 weeks before opening)",
                    "Monthly check-in on studio utilization fairness",
                ]
            },
            responsible_party="Kenny",
            status="active",
            checkin_30_date=days_from_now(25),
            checkin_30_notes=None,
        ))

        await session.flush()

        # ===============================================================
        # 27. ADDITIONAL DECISION RECORDS — linked to ratified proposals
        # ===============================================================
        extra_decision_spec = [
            # (eco_id, prefix, idx, record_id, date_offset, holding, ratio, domain, recorder, proposal_ref, participants)
            (eco_ps_id, "ps", 3, "DEC-PS-003", 4,
             "Ratify Open-Source Contribution and Attribution Policy as binding agreement",
             "30-day test period passed all success criteria; strong contributor adoption validates the policy",
             "Governance Circle", "Rachel",
             [("Rachel", "co_creator", "consent"), ("Brandon", "builder", "consent"), ("Drew", "townhall", "consent")]),
            (eco_omni_id, "omni", 3, "DEC-OMNI-003", 15,
             "Approve solar energy credit distribution system for 60-day test phase",
             "Advice phase showed strong support; proportional model aligns with community equity principles",
             "Core Operations", "Josh Pasmore",
             [("Josh Pasmore", "co_creator", "consent"), ("Nathan R", "builder", "consent"), ("Ahmed (Jade Oni)", "townhall", "consent")]),
            (eco_eb_id, "eb", 3, "DEC-EB-003", 12,
             "Approve CC BY-SA 4.0 as default license for collaborative works during 90-day test",
             "Consent round unanimous; license protects collective while enabling open sharing",
             "Governance Circle", "Ahmed (Jade Oni)",
             [("Ahmed (Jade Oni)", "co_creator", "consent"), ("Kenny", "builder", "consent"), ("Jak", "townhall", "consent")]),
            (eco_oa_id, "oa", 3, "DEC-OA-003", 8,
             "Reject mandatory token staking proposal and archive for future consideration",
             "Proposal withdrawn by proposer after advice phase revealed accessibility concerns; archived for future review",
             "Governance Circle", "Max Gershfield",
             [("Max Gershfield", "co_creator", "consent"), ("David Ellams", "builder", "noted_objection")]),
        ]

        for (eco_id, prefix, idx, record_id, date_offset, holding, ratio,
             domain, recorder, participants) in extra_decision_spec:
            dec_id = _uid(f"dec.{prefix}.{idx}")
            session.add(DecisionRecord(
                id=dec_id,
                ecosystem_id=eco_id,
                record_id=record_id,
                date=days_ago(date_offset),
                holding=holding,
                ratio_decidendi=ratio,
                domain=domain,
                precedent_level="binding",
                status="active",
                recorder=recorder,
                recorder_role="co_creator" if recorder in ("Josh Pasmore", "Ahmed (Jade Oni)", "Rachel", "Max Gershfield") else "builder",
                review_date=days_from_now(180),
            ))
            for pname, prole, pposition in participants:
                session.add(DecisionParticipant(
                    id=_uid(f"decpart.{prefix}.{idx}.{pname}"),
                    decision_record_id=dec_id,
                    name=pname,
                    role=prole,
                    position=pposition,
                ))
            session.add(DecisionSemanticTag(
                id=_uid(f"dectag.{prefix}.{idx}"),
                decision_record_id=dec_id,
                topic={"category": domain},
                affected_parties={"circle": domain},
                ecosystem_scope="internal",
                urgency_at_time="standard",
            ))

        await session.flush()

        # ===============================================================
        # 28. QUIZZES — 5 quizzes with SurveyJS content + quiz results
        # ===============================================================
        quiz_governance = _uid("quiz.governance_basics")
        quiz_act = _uid("quiz.act_process")
        quiz_conflict = _uid("quiz.conflict_resolution")
        quiz_onboarding_omni = _uid("quiz.onboarding_omni")
        quiz_digital_sov = _uid("quiz.digital_sovereignty")

        quizzes_spec = [
            # (id, title, description, mode, survey_json, passing_score, created_by, eco_id, is_entry, is_published)
            (quiz_governance, "Governance Fundamentals",
             "Test your understanding of NEOS governance principles, consent-based decision-making, and domain stewardship.",
             "standard",
             {
                 "pages": [{
                     "elements": [
                         {"type": "radiogroup", "name": "q1",
                          "title": "What is the primary decision-making method in NEOS governance?",
                          "choices": ["Majority vote", "Consent-based (ACT process)", "Executive decision", "Random selection"],
                          "correctAnswer": "Consent-based (ACT process)"},
                         {"type": "radiogroup", "name": "q2",
                          "title": "What does ACT stand for in the governance process?",
                          "choices": ["Action, Collaboration, Trust", "Advice, Consent, Test", "Assess, Create, Track", "Align, Commit, Transform"],
                          "correctAnswer": "Advice, Consent, Test"},
                         {"type": "radiogroup", "name": "q3",
                          "title": "Who holds delegated authority within a domain?",
                          "choices": ["All members equally", "The ecosystem founder", "The domain steward", "External advisors"],
                          "correctAnswer": "The domain steward"},
                         {"type": "text", "name": "q4",
                          "title": "In your own words, why is consent-based governance different from consensus?"},
                     ]
                 }]
             },
             75, m_josh_id, None, False, True),

            (quiz_act, "ACT Process Deep Dive",
             "Detailed assessment of the Advice-Consent-Test lifecycle for proposals.",
             "standard",
             {
                 "pages": [{
                     "elements": [
                         {"type": "radiogroup", "name": "q1",
                          "title": "During the Advice phase, who should the proposer consult?",
                          "choices": ["Only the domain steward", "All affected parties and subject-matter experts", "The governance circle only", "No one — advice is optional"],
                          "correctAnswer": "All affected parties and subject-matter experts"},
                         {"type": "radiogroup", "name": "q2",
                          "title": "What is required for consent to be given?",
                          "choices": ["Everyone must agree enthusiastically", "No paramount objections remain", "At least 51% approval", "Unanimous agreement"],
                          "correctAnswer": "No paramount objections remain"},
                         {"type": "radiogroup", "name": "q3",
                          "title": "What happens if a test phase fails its success criteria?",
                          "choices": ["The proposal is automatically ratified anyway", "The proposal reverts and may be revised", "The proposer is penalized", "Nothing — tests are informational only"],
                          "correctAnswer": "The proposal reverts and may be revised"},
                         {"type": "text", "name": "q4",
                          "title": "Describe a scenario where you would escalate a proposal to a higher governance tier."},
                     ]
                 }]
             },
             80, m_josh_id, None, False, True),

            (quiz_conflict, "Conflict Resolution and GAIA Model",
             "Assessment of conflict resolution skills using the GAIA 6-level escalation model.",
             "standard",
             {
                 "pages": [{
                     "elements": [
                         {"type": "radiogroup", "name": "q1",
                          "title": "What is the first tier in the GAIA conflict resolution model?",
                          "choices": ["Mediation committee", "Direct dialogue between parties", "Community tribunal", "External arbitration"],
                          "correctAnswer": "Direct dialogue between parties"},
                         {"type": "radiogroup", "name": "q2",
                          "title": "When should a safety flag be raised on a conflict case?",
                          "choices": ["For any disagreement", "When physical safety or wellbeing is at risk", "Only for financial disputes", "Never — conflicts are always safe"],
                          "correctAnswer": "When physical safety or wellbeing is at risk"},
                         {"type": "text", "name": "q3",
                          "title": "What is the purpose of a repair agreement in conflict resolution?"},
                         {"type": "text", "name": "q4",
                          "title": "Describe how you would facilitate a conflict between two domain stewards."},
                     ]
                 }]
             },
             70, m_ahmed_id, None, False, True),

            (quiz_onboarding_omni, "OmniOne Community Onboarding",
             "Entry quiz for new OmniOne members covering community values, land stewardship, and shared resource protocols.",
             "standard",
             {
                 "pages": [{
                     "elements": [
                         {"type": "radiogroup", "name": "q1",
                          "title": "What is OmniOne's primary focus?",
                          "choices": ["Profit maximization", "Regenerative community governance", "Technology development", "Real estate investment"],
                          "correctAnswer": "Regenerative community governance"},
                         {"type": "radiogroup", "name": "q2",
                          "title": "How long is the cooling-off period for new members?",
                          "choices": ["1 day", "7 days", "30 days", "90 days"],
                          "correctAnswer": "7 days"},
                         {"type": "radiogroup", "name": "q3",
                          "title": "What document must all members consent to?",
                          "choices": ["Terms of Service", "Universal Agreement Field (UAF)", "Non-Disclosure Agreement", "Employment Contract"],
                          "correctAnswer": "Universal Agreement Field (UAF)"},
                         {"type": "text", "name": "q4",
                          "title": "Why is regenerative agriculture important to the OmniOne community?"},
                     ]
                 }]
             },
             80, m_josh_id, eco_omni_id, True, True),

            (quiz_digital_sov, "Digital Sovereignty Fundamentals",
             "Assessment of decentralized identity, data ownership, and Web4 governance principles for Oasis members.",
             "standard",
             {
                 "pages": [{
                     "elements": [
                         {"type": "radiogroup", "name": "q1",
                          "title": "What does DID stand for in the context of digital identity?",
                          "choices": ["Digital Information Database", "Decentralized Identifier", "Data Integration Driver", "Distributed Index Directory"],
                          "correctAnswer": "Decentralized Identifier"},
                         {"type": "radiogroup", "name": "q2",
                          "title": "What is the core principle of digital sovereignty?",
                          "choices": ["Government control of data", "Corporate data ownership", "Individual control over personal data", "Open access to all data"],
                          "correctAnswer": "Individual control over personal data"},
                         {"type": "radiogroup", "name": "q3",
                          "title": "What does Oasis's holonic architecture enable?",
                          "choices": ["Centralized data storage", "Cross-chain interoperability", "Single-chain optimization", "Data deletion"],
                          "correctAnswer": "Cross-chain interoperability"},
                         {"type": "text", "name": "q4",
                          "title": "Explain why data portability matters for governance participation across ecosystems."},
                     ]
                 }]
             },
             75, m_max_id, eco_oa_id, True, True),
        ]

        for (qid, title, desc, mode, survey_json, passing, created_by, eco_id,
             is_entry, is_published) in quizzes_spec:
            session.add(Quiz(
                id=qid,
                title=title,
                description=desc,
                mode=mode,
                survey_json=survey_json,
                passing_score=passing,
                allow_retakes=True,
                visibility="public",
                is_published=is_published,
                created_by=created_by,
                ecosystem_id=eco_id,
                is_entry_quiz=is_entry,
            ))

        await session.flush()

        # Quiz results for various members
        quiz_results_spec = [
            # (quiz_id, member_id, prefix, score, passed, time_spent, answers)
            (quiz_governance, m_josh_id, "gov.josh", 100.0, True, 180,
             {"q1": "Consent-based (ACT process)", "q2": "Advice, Consent, Test", "q3": "The domain steward", "q4": "Consent only requires no paramount objections, while consensus requires full agreement."}),
            (quiz_governance, m_nathan_id, "gov.nathan", 75.0, True, 240,
             {"q1": "Consent-based (ACT process)", "q2": "Advice, Consent, Test", "q3": "All members equally", "q4": "Consent is about tolerability, consensus is about agreement."}),
            (quiz_governance, m_kenny_id, "gov.kenny", 50.0, False, 300,
             {"q1": "Majority vote", "q2": "Advice, Consent, Test", "q3": "The domain steward", "q4": "Not sure of the difference."}),
            (quiz_act, m_ahmed_id, "act.ahmed", 100.0, True, 200,
             {"q1": "All affected parties and subject-matter experts", "q2": "No paramount objections remain", "q3": "The proposal reverts and may be revised", "q4": "When the proposal crosses domain boundaries or affects ecosystem-level agreements."}),
            (quiz_act, m_rachel_id, "act.rachel", 80.0, True, 220,
             {"q1": "All affected parties and subject-matter experts", "q2": "No paramount objections remain", "q3": "The proposal reverts and may be revised", "q4": "Escalation when impact crosses multiple domains."}),
            (quiz_onboarding_omni, m_nathan_id, "onb.nathan", 100.0, True, 150,
             {"q1": "Regenerative community governance", "q2": "7 days", "q3": "Universal Agreement Field (UAF)", "q4": "Food sovereignty and soil regeneration are core to community resilience."}),
            (quiz_digital_sov, m_max_id, "digsov.max", 100.0, True, 160,
             {"q1": "Decentralized Identifier", "q2": "Individual control over personal data", "q3": "Cross-chain interoperability", "q4": "Without data portability, members are locked into single platforms and lose governance agency."}),
            (quiz_digital_sov, m_david_id, "digsov.david", 75.0, True, 280,
             {"q1": "Decentralized Identifier", "q2": "Individual control over personal data", "q3": "Cross-chain interoperability", "q4": "Portability ensures members can migrate governance participation across ecosystems."}),
        ]

        for (qid, mid, prefix, score, passed, time_spent, answers) in quiz_results_spec:
            session.add(QuizResult(
                id=_uid(f"qresult.{prefix}"),
                quiz_id=qid,
                member_id=mid,
                survey_results=answers,
                score=score,
                is_passed=passed,
                time_spent=time_spent,
                completed_at=hours_ago(48),
            ))

        await session.flush()

        # ===============================================================
        # 29. ADDITIONAL SHARES & NEEDS — 8 more (2 per ecosystem)
        # ===============================================================
        extra_sn_spec = [
            # OmniOne — additional
            (eco_omni_id, dom_omni_gov_id, "omni.share2", "share",
             "Consent-Based Governance Workshop Facilitation",
             "OmniOne offers trained facilitators for ACT-process governance workshops, "
             "conflict resolution circles, and onboarding ceremony guidance for new communities.",
             "skill", "monthly",
             ["facilitation", "governance", "workshops", "consent-process"]),
            (eco_omni_id, dom_omni_regen_id, "omni.need2", "need",
             "Solar Microgrid Monitoring & IoT Sensors",
             "Need IoT sensor integration for monitoring community solar microgrid output, "
             "water systems, and composting facilities in real-time dashboards.",
             "resource", "urgent",
             ["iot", "solar", "monitoring", "microgrid", "sensors"]),

            # Escherbridge — additional
            (eco_eb_id, dom_eb_art_id, "eb.share2", "share",
             "AI-Powered Creative Collaboration Tools",
             "Escherbridge shares its suite of AI agentic creative tools for collaborative "
             "art production, including style transfer, generative design, and co-creative AI agents.",
             "skill", "ongoing",
             ["ai-art", "generative-design", "co-creative", "collaboration"]),
            (eco_eb_id, dom_eb_ops_id, "eb.need2", "need",
             "Affordable Studio & Exhibition Space",
             "Escherbridge needs affordable physical studio spaces and exhibition venues "
             "for member artists, including shared workshop areas and gallery access.",
             "space", "high",
             ["studio", "exhibition", "gallery", "workspace", "affordable"]),

            # Plan Systems — additional
            (eco_ps_id, dom_ps_design_id, "ps.share2", "share",
             "5G Community Broadband Network Expertise",
             "Plan Systems shares expertise in deploying nonprofit 5G broadband networks "
             "for underserved communities, including spectrum management and municipal partnerships.",
             "knowledge", "quarterly",
             ["5g", "broadband", "nonprofit", "digital-equity", "spectrum"]),
            (eco_ps_id, dom_ps_ops_id, "ps.need2", "need",
             "STEM Education Content & Curriculum Design",
             "Need curriculum designers and educators to create STEM content for the "
             "Plan Systems education platform serving broadband communities.",
             "skill", "moderate",
             ["stem", "education", "curriculum", "content-creation"]),

            # Oasis — additional
            (eco_oa_id, dom_oa_protocol_id, "oa.share2", "share",
             "Multi-Chain Smart Contract Templates",
             "Oasis provides battle-tested smart contract templates for governance DAOs, "
             "token distribution, and consent-based voting across Ethereum, Solana, and Polygon.",
             "knowledge", "ongoing",
             ["smart-contracts", "dao", "multi-chain", "templates", "voting"]),
            (eco_oa_id, dom_oa_gov_id, "oa.need2", "need",
             "Real-World Governance Case Studies",
             "Oasis needs documented case studies of real-world cooperative and regenerative "
             "community governance to validate its digital governance models.",
             "knowledge", "moderate",
             ["case-studies", "cooperative", "regenerative", "governance-research"]),
        ]

        for (eco_id, domain_id, prefix, sn_type, title, desc, category,
             capacity, tags) in extra_sn_spec:
            session.add(SharesNeeds(
                id=_uid(f"sn.{prefix}"),
                ecosystem_id=eco_id,
                domain_id=domain_id,
                type=sn_type,
                title=title,
                description=desc,
                category=category,
                capacity=capacity,
                tags=tags,
                visibility="public",
                status="active",
            ))

        await session.flush()

        # ===============================================================
        # 30. ADDITIONAL COLLABORATIONS — 2 more cross-ecosystem
        # ===============================================================
        # Plan Systems <-> Oasis (active, federate tier)
        session.add(Collaboration(
            id=_uid("collab.ps_oa"),
            source_domain_id=dom_ps_design_id,
            target_domain_id=dom_oa_protocol_id,
            title="Decentralized Broadband Governance & Cross-Chain Identity",
            description=(
                "Active collaboration integrating Plan Systems' 5G broadband infrastructure "
                "with Oasis's Web4 identity and cross-chain governance layer. Members of broadband "
                "communities receive DID-based identities managed through NEOS governance with "
                "on-chain consent records via Oasis's holonic data architecture."
            ),
            status="active",
            engagement_tier="federate",
            terms={"meetings": "weekly", "shared_infrastructure": True,
                   "deliverables": ["did_broadband_id", "governance_bridge", "community_dashboard"]},
            started_date=days_ago(20),
            review_date=days_from_now(40),
            version_fingerprint="collab-ps-oa-v1",
        ))

        # OmniOne <-> Escherbridge (proposed, cooperate tier)
        session.add(Collaboration(
            id=_uid("collab.omni_eb"),
            source_domain_id=dom_omni_regen_id,
            target_domain_id=dom_eb_art_id,
            title="Regenerative Community Art & Cultural Documentation",
            description=(
                "Proposed collaboration for Escherbridge artists to document and visualize "
                "OmniOne's regenerative community practices through immersive art installations, "
                "VR experiences of permaculture sites, and AI-generated educational content "
                "about sustainable governance."
            ),
            status="proposed",
            engagement_tier="cooperate",
            terms={"artist_residency": "3_months", "documentation_outputs": 5},
            version_fingerprint="collab-omni-eb-v1",
        ))

        await session.flush()

        # ===============================================================
        # COMMIT
        # ===============================================================
        await session.commit()

    await engine.dispose()

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print()
    print("=== NEOS Seed Data ===")
    print("Ecosystems: 4 (OmniOne, Escherbridge, Plan Systems, Oasis)")
    print("Members: 11 records (10 unique people; Ahmed in OmniOne + Escherbridge) + 1 exited")
    print("Domains: 12 (3 per ecosystem: Core Ops, Governance, Specialty)")
    print("Agreements: 26 (5 per eco base + 2 advice + 2 under_review + 1 sunset + 1 archived)")
    print("Proposals: 12 (4 advice + 2 draft + 2 consent + 2 test + 1 ratified + 1 withdrawn)")
    print("Conflicts: 6 (4 base + 2 additional) with 2 repair agreements")
    print("Decisions: 12 (8 base + 4 linked to ratified/test/withdrawn proposals)")
    print("Emergency: 1 (OmniOne, closed)")
    print("Exit: 1 (OmniOne, Rua)")
    print("Audits: 4 (1 per ecosystem)")
    print("Circle Memberships: 33 (3x3 OmniOne + 3x3 Escherbridge + 3x3 Plan Systems + 2x3 Oasis)")
    print("Shares & Needs: 16 (2 shares + 2 needs per ecosystem)")
    print("Collaborations: 4 (OmniOne-PlanSystems active, Escherbridge-Oasis proposed, PlanSystems-Oasis federate, OmniOne-Escherbridge proposed)")
    print("Compliance Summaries: 4 (1 per ecosystem)")
    print("Onboarding Records: 11 (all complete)")
    print("Quizzes: 5 (governance, ACT, conflict, OmniOne onboarding, digital sovereignty)")
    print("Quiz Results: 8 (across various members)")
    print("=== Done ===")


def main() -> None:
    """Entry point for the seed script."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed the NEOS database with multi-ecosystem test data")
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
