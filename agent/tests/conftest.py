"""Shared test fixtures for the NEOS agent test suite."""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from neos_agent.db.models import (
    Base,
    Agreement,
    Conversation,
    ConversationLink,
    ConversationParticipant,
    Domain,
    DomainElement,
    Ecosystem,
    Member,
    Message,
    Proposal,
)


NEOS_CORE_PATH = Path(__file__).resolve().parent.parent.parent / "neos-core"


@pytest.fixture
def neos_core_path() -> Path:
    """Path to the actual neos-core directory."""
    return NEOS_CORE_PATH


SAMPLE_SKILL_MD = '''---
name: test-skill
description: "A test skill for unit testing the loader"
layer: 1
version: 0.1.0
depends_on: [domain-mapping]
---

# test-skill

## A. Structural Problem It Solves

This skill prevents unstructured governance decisions from being made informally.
It ensures all governance actions are traceable and legitimate.
Without this skill, decisions could be made outside the formal process.

## B. Domain Scope

This skill applies to all domains within a single ETHOS.
It covers governance decisions related to agreement management.
Out of scope: cross-ecosystem decisions (handled by Layer V skills).

## C. Trigger Conditions

This skill is triggered when a governance decision needs to be recorded.
Routine trigger: weekly governance review cycle.
Exceptional trigger: urgent decision requiring formal documentation.

## D. Required Inputs

The proposer must provide the decision context and rationale.
The affected domain steward must confirm domain boundaries.
Optional: supporting documentation from prior discussions.

## E. Step-by-Step Process

1. Proposer submits the governance action request.
2. Domain steward reviews scope and confirms applicability.
3. Facilitator initiates the consent process.
4. Participants review and provide positions.
5. Outcome is recorded in the decision registry.

## F. Output Artifact

The output is a decision-record YAML file stored in the governance registry.
Fields: decision_id, date, holding, participants, outcome.
Access: all ecosystem members can read; only recorder can write.

## G. Authority Boundary Check

Only domain stewards can initiate actions within their domain.
No individual can unilaterally override a consent decision.
OSC consensus is required for ecosystem-level changes.
Cross-domain actions require explicit authorization from all affected stewards.

## H. Capture Resistance Check

Capital capture: financial contributions do not grant additional governance weight.
Charismatic capture: all decisions require formal consent, not informal agreement.
Emergency capture: emergency provisions auto-expire after 72 hours.
Informal capture: all agreements must be registered to be valid.

## I. Failure Containment Logic

If consent fails, the proposal returns to the advice phase.
If quorum is not met, the decision is deferred, not auto-approved.
Process stalls trigger escalation to the next GAIA level.
Ambiguous outcomes are resolved by the facilitator with documented rationale.

## J. Expiry / Review Condition

All outputs are reviewed every 12 months by default.
Missed reviews trigger an escalation notice, not auto-invalidation.
Configurable review intervals with a minimum of 3 months.
Auto-expiry applies only to emergency provisions.

## K. Exit Compatibility Check

When a participant exits, their prior decisions remain valid.
In-progress commitments have a 30-day wind-down period.
Participants retain rights to their original works upon exit.
Exit does not retroactively invalidate previously consented decisions.

## L. Cross-Unit Interoperability Impact

Cross-ETHOS effects require notification to affected units.
Outputs are registered in a shared cross-unit registry.
Federation extensibility is noted but deferred to Layer V.
Inter-unit disputes follow the inter-unit resolution skill.

## OmniOne Walkthrough

In OmniOne, a TH (Town Hall) member named Kai proposes a new kitchen scheduling agreement for the SHUR Kitchen domain. Kai submits the proposal through the governance platform. The domain steward for SHUR Kitchen, an AE (Agent of Ecosystem) named Lani, reviews the scope and confirms it falls within the kitchen domain. The OSC (OMNI Steward Council) facilitator, Manu, initiates the consent round. Three TH members and two AE members participate in the consent process. One AE member raises a reasoned objection about overlap with the garden composting schedule. The facilitator integrates the objection by adjusting the scheduling windows. After integration, all participants consent. The decision is recorded in the governance registry as DEC-SHUR-KITCHEN-2026-001. GEV (Green Earth Vision) is notified as the legal steward but does not participate in the consent decision.

## Stress-Test Results

### 1. Capital Influx

When a significant external donor offers $500,000 to OmniOne contingent on specific kitchen policies, this skill ensures the donation cannot influence the governance outcome. The consent process weights all participants equally regardless of financial contribution. The facilitator must document any external pressure in the advice log. If the donor attempts to condition funding on a specific decision, the proposal is flagged for capture resistance review. The structural safeguard of equal weighting and mandatory documentation prevents capital from distorting the consent process.

### 2. Emergency Crisis

During a severe storm that damages the SHUR Kitchen, this skill operates under compressed timelines per the provisional emergency expediting rules. The advice window shrinks from 14 days to 48 hours, but consent is still required from affected participants. The facilitator ensures all accessible participants are notified through available channels. Emergency provisions auto-expire after 72 hours, requiring formal follow-up through standard timelines. Even at maximum compression, no decision is made without at least one consent round.

### 3. Leadership Charisma Capture

When a highly charismatic OSC member advocates strongly for a particular kitchen policy, the skill prevents personality-driven override. The consent process requires each participant to state their position independently, not in response to the charismatic leader. The facilitator ensures discussion follows structured rounds, not open debate where social pressure dominates. Anonymous position submissions are available as an option when social pressure is identified. The structural requirement for reasoned objections means positions must be substantiated, not merely popular.

### 4. High Conflict / Polarization

When the kitchen scheduling proposal deeply polarizes the community between early-morning and late-night preferences, the skill handles conflict through GAIA escalation levels. At Level 1, the facilitator coaches participants toward third solutions. At Level 2, a neutral mediator is engaged. The skill ensures polarized positions are documented without judgment, and integration rounds seek creative alternatives. If no resolution emerges after two integration rounds, the proposal may be split into separate domain-specific agreements that accommodate both preferences.

### 5. Large-Scale Replication

As OmniOne scales from 50 to 5,000 participants, this skill adapts through domain-scoped action. Not all 5,000 participants engage with every kitchen scheduling decision. Only members within the SHUR Kitchen domain and directly affected parties participate in consent. The registry-based routing system directs proposals to the relevant subset of participants. Domain stewards manage scope boundaries, ensuring decisions remain tractable even at scale.

### 6. External Legal Pressure

When Indonesian health regulations require specific food handling procedures, this skill distinguishes between individual legal compliance and ecosystem-level agreements. Individual members comply with legal requirements as personal obligations. The ecosystem-level agreement references but does not replicate legal requirements. The UAF sovereignty principle ensures the ecosystem can set higher but not lower standards than legal minimums. External legal mandates are documented in the advice log as contextual input, not as overriding directives.

### 7. Sudden Exit of 30% of Participants

If 30% of SHUR Kitchen domain members suddenly exit OmniOne, this skill triggers automatic review of all active kitchen agreements. Quorum thresholds adapt proportionally — if the original quorum was 60% of 20 members (12), it becomes 60% of 14 members (9). Existing decisions remain valid until formally reviewed under the new composition. Orphaned steward roles trigger the domain stewardship succession process. The 30-day wind-down period ensures in-progress commitments are honored by departing members.
'''


@pytest.fixture
def sample_skill_md() -> str:
    """Sample SKILL.md content for testing."""
    return SAMPLE_SKILL_MD


@pytest_asyncio.fixture
async def db_engine():
    """Create an async in-memory SQLite engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create an async session for testing."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


# ===================================================================
# Governance tool test fixtures: seeded DB with ecosystem, members,
# agreements, domain, and proposal.
# ===================================================================

# Stable UUIDs for seed data
ECO_ID = uuid.UUID("00000000000000000000000000000001")
MEMBER_STEWARD_ID = uuid.UUID("00000000000000000000000000000010")
MEMBER_BUILDER_ID = uuid.UUID("00000000000000000000000000000020")
MEMBER_TH_ID = uuid.UUID("00000000000000000000000000000030")
DOMAIN_ID = uuid.UUID("00000000000000000000000000000100")
AGREEMENT_ACTIVE_ID = uuid.UUID("00000000000000000000000000001000")
AGREEMENT_DRAFT_ID = uuid.UUID("00000000000000000000000000002000")
PROPOSAL_ID = uuid.UUID("00000000000000000000000000010000")

# Messaging seed data UUIDs
DM_CONVERSATION_ID = uuid.UUID("00000000000000000000000000100000")
GROUP_CONVERSATION_ID = uuid.UUID("00000000000000000000000000200000")


@pytest_asyncio.fixture
async def seeded_db(db_engine):
    """Session pre-loaded with governance seed data.

    Creates:
    - 1 ecosystem (OmniOne)
    - 3 active members: Lani (steward/co_creator), Kai (builder), Manu (townhall)
    - 2 agreements: 1 active (SHUR Kitchen schedule), 1 draft (Garden compost)
    - 1 domain (SHUR-KITCHEN) with Lani as steward + 2 domain elements
    - 1 proposal in advice phase
    """
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        # Ecosystem
        eco = Ecosystem(id=ECO_ID, name="OmniOne", status="active")
        session.add(eco)

        # Members
        lani = Member(
            id=MEMBER_STEWARD_ID,
            ecosystem_id=ECO_ID,
            member_id="MEM-001",
            display_name="Lani",
            current_status="active",
            profile="co_creator",
        )
        kai = Member(
            id=MEMBER_BUILDER_ID,
            ecosystem_id=ECO_ID,
            member_id="MEM-002",
            display_name="Kai",
            current_status="active",
            profile="builder",
        )
        manu = Member(
            id=MEMBER_TH_ID,
            ecosystem_id=ECO_ID,
            member_id="MEM-003",
            display_name="Manu",
            current_status="active",
            profile="townhall",
        )
        session.add_all([lani, kai, manu])

        # Domain
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

        # Domain elements (S3-style)
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

        # Agreement: active
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

        # Agreement: draft
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

        # Proposal: in advice phase
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

    # Yield a fresh session for the test
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def seeded_messaging_db(db_engine):
    """Session pre-loaded with governance seed data PLUS messaging data.

    Extends seeded_db with:
    - 1 DM conversation between Lani and Kai
    - 1 group conversation ("Kitchen Planning") with all 3 members
    - 5 sample messages in the DM
    - 3 sample messages in the group
    - 1 governance link (group linked to proposal PROP-2026-001)
    """
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        # -- Governance seed data (same as seeded_db) --
        eco = Ecosystem(id=ECO_ID, name="OmniOne", status="active")
        session.add(eco)

        lani = Member(
            id=MEMBER_STEWARD_ID, ecosystem_id=ECO_ID,
            member_id="MEM-001", display_name="Lani",
            current_status="active", profile="co_creator",
        )
        kai = Member(
            id=MEMBER_BUILDER_ID, ecosystem_id=ECO_ID,
            member_id="MEM-002", display_name="Kai",
            current_status="active", profile="builder",
        )
        manu = Member(
            id=MEMBER_TH_ID, ecosystem_id=ECO_ID,
            member_id="MEM-003", display_name="Manu",
            current_status="active", profile="townhall",
        )
        session.add_all([lani, kai, manu])

        domain = Domain(
            id=DOMAIN_ID, ecosystem_id=ECO_ID,
            domain_id="SHUR-KITCHEN", version="1.0", status="active",
            purpose="Community kitchen operations and scheduling",
            current_steward="Lani", steward_id=MEMBER_STEWARD_ID,
            elements={"primary_accountabilities": ["meal scheduling", "hygiene"]},
        )
        session.add(domain)

        agr_active = Agreement(
            id=AGREEMENT_ACTIVE_ID, ecosystem_id=ECO_ID,
            agreement_id="AGR-SHUR-2026-001", type="space",
            title="SHUR Kitchen Scheduling Agreement", version="1.0",
            status="active", proposer="Kai",
            affected_parties=["Lani", "Kai", "Manu"],
            domain="SHUR Kitchen",
            text="Kitchen scheduling rules for OmniOne SHUR.",
            created_date=date(2026, 1, 15),
        )
        agr_draft = Agreement(
            id=AGREEMENT_DRAFT_ID, ecosystem_id=ECO_ID,
            agreement_id="AGR-GARD-2026-002", type="access",
            title="Garden Composting Access Agreement", version="0.1",
            status="draft", proposer="Manu", domain="Garden",
            text="Composting access rules.",
            created_date=date(2026, 2, 1),
        )
        session.add_all([agr_active, agr_draft])

        prop = Proposal(
            id=PROPOSAL_ID, ecosystem_id=ECO_ID,
            proposal_id="PROP-2026-001", type="agreement",
            decision_type="consent", title="Add evening kitchen hours",
            version="1.0", status="advice", proposer="Kai",
            affected_domain="SHUR-KITCHEN",
            created_date=date(2026, 2, 10),
        )
        session.add(prop)

        # -- Messaging seed data --

        # DM conversation: Lani <-> Kai
        dm_convo = Conversation(
            id=DM_CONVERSATION_ID, ecosystem_id=ECO_ID,
            type="dm", created_by=MEMBER_STEWARD_ID,
        )
        session.add(dm_convo)
        session.add_all([
            ConversationParticipant(
                conversation_id=DM_CONVERSATION_ID,
                member_id=MEMBER_STEWARD_ID, role="member",
            ),
            ConversationParticipant(
                conversation_id=DM_CONVERSATION_ID,
                member_id=MEMBER_BUILDER_ID, role="member",
            ),
        ])

        # Group conversation: Kitchen Planning (all 3 members)
        group_convo = Conversation(
            id=GROUP_CONVERSATION_ID, ecosystem_id=ECO_ID,
            type="group", title="Kitchen Planning",
            created_by=MEMBER_STEWARD_ID,
        )
        session.add(group_convo)
        session.add_all([
            ConversationParticipant(
                conversation_id=GROUP_CONVERSATION_ID,
                member_id=MEMBER_STEWARD_ID, role="owner",
            ),
            ConversationParticipant(
                conversation_id=GROUP_CONVERSATION_ID,
                member_id=MEMBER_BUILDER_ID, role="member",
            ),
            ConversationParticipant(
                conversation_id=GROUP_CONVERSATION_ID,
                member_id=MEMBER_TH_ID, role="member",
            ),
        ])

        # 5 DM messages
        dm_messages = [
            Message(
                conversation_id=DM_CONVERSATION_ID,
                sender_id=MEMBER_STEWARD_ID,
                content="Hey Kai, can we discuss the kitchen schedule?",
                message_type="text",
            ),
            Message(
                conversation_id=DM_CONVERSATION_ID,
                sender_id=MEMBER_BUILDER_ID,
                content="Sure! I was thinking about extending evening hours.",
                message_type="text",
            ),
            Message(
                conversation_id=DM_CONVERSATION_ID,
                sender_id=MEMBER_STEWARD_ID,
                content="That aligns with the proposal. Let me check the details.",
                message_type="text",
            ),
            Message(
                conversation_id=DM_CONVERSATION_ID,
                sender_id=MEMBER_BUILDER_ID,
                content="I'll draft a schedule and share it in the group.",
                message_type="text",
            ),
            Message(
                conversation_id=DM_CONVERSATION_ID,
                sender_id=MEMBER_STEWARD_ID,
                content="Perfect, thanks!",
                message_type="text",
            ),
        ]
        session.add_all(dm_messages)

        # 3 group messages
        group_messages = [
            Message(
                conversation_id=GROUP_CONVERSATION_ID,
                sender_id=MEMBER_STEWARD_ID,
                content="Lani created this conversation",
                message_type="system",
            ),
            Message(
                conversation_id=GROUP_CONVERSATION_ID,
                sender_id=MEMBER_BUILDER_ID,
                content="Here's my draft for the evening kitchen schedule.",
                message_type="text",
            ),
            Message(
                conversation_id=GROUP_CONVERSATION_ID,
                sender_id=MEMBER_TH_ID,
                content="Looks good! I have a few suggestions.",
                message_type="text",
            ),
        ]
        session.add_all(group_messages)

        # Governance link: group convo linked to proposal PROP-2026-001
        link = ConversationLink(
            conversation_id=GROUP_CONVERSATION_ID,
            entity_type="proposal",
            entity_id=PROPOSAL_ID,
            created_by=MEMBER_STEWARD_ID,
        )
        session.add(link)

        await session.commit()

    # Yield a fresh session for the test
    async with session_factory() as session:
        yield session
