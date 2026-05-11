"""Seed orientation data: journey maps and ethos user access records.

Usage:
    python -m agent.scripts.seed_orientation
    python -m agent.scripts.seed_orientation --purge

Creates:
  8 journey maps (2 per ecosystem: Explorer + Ready to Join)
    - 7 active, 1 inactive (Oasis Ready to Join) for include_inactive filter testing
  11 ethos_user_access records (all active members)
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import (
    Base,
    EthosUserAccess,
    JourneyMap,
)


# ---------------------------------------------------------------------------
# Deterministic UUID helper -- must match seed_omnione
# ---------------------------------------------------------------------------
def _uid(name: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"neos.seed.{name}")


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
# OmniOne
m_josh_id = _uid("mbr.omni.josh")
m_nathan_id = _uid("mbr.omni.nathan")
m_ahmed_id = _uid("mbr.omni.ahmed")

# Escherbridge
m_ahmed_eb_id = _uid("mbr.eb.ahmed")
m_kenny_id = _uid("mbr.eb.kenny")
m_jak_id = _uid("mbr.eb.jak")

# Plan Systems
m_rachel_id = _uid("mbr.ps.rachel")
m_brandon_id = _uid("mbr.ps.brandon")
m_drew_id = _uid("mbr.ps.drew")

# Oasis
m_max_id = _uid("mbr.oa.max")
m_david_id = _uid("mbr.oa.david")

# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------
_NOW = datetime.utcnow()


# ---------------------------------------------------------------------------
# Journey Map content sequences
# ---------------------------------------------------------------------------

# ===== OMNIONE =====
OMNIONE_EXPLORER_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Welcome to OmniOne",
        "description": "Meet the community that's building a new way to live together in Bali.",
        "video_url": "/assets/orientation/omnione-welcome.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "What Brings You Here?",
        "description": "Help us understand your path so we can guide you better.",
        "choices": [
            {"value": "live", "label": "I want to live at OmniOne", "description": "Full-time community membership"},
            {"value": "collaborate", "label": "I want to collaborate remotely", "description": "Contribute skills and participate in governance from anywhere"},
            {"value": "learn", "label": "I'm here to learn", "description": "Explore governance and community models"},
            {"value": "visit", "label": "I'm planning a visit", "description": "Short-term stay to experience the community"},
        ],
        "required": True,
        "section_key": "motivation",
    },
    {
        "step": 2,
        "type": "reflection",
        "title": "Your Vision for Community",
        "description": "Take a moment to reflect on what you hope to find or create here.",
        "reflection_prompt": "What does thriving community look like to you? What would you contribute, and what do you need?",
        "required": True,
    },
    {
        "step": 3,
        "type": "ai_conversation",
        "title": "Governance Introduction",
        "description": "Have a conversation with our AI guide about how governance works at OmniOne.",
        "ai_prompt_template": (
            "You are an orientation guide for OmniOne, a self-governing community in Bali. "
            "Introduce the participant to the ACT (Advice-Consent-Test) governance process. "
            "Explain that decisions are made through gathering advice, checking for consent "
            "(not unanimous agreement, but absence of paramount objections), and testing in "
            "practice. Be warm, welcoming, and use simple language. Ask them if they have "
            "questions about how decisions are made here."
        ),
        "required": True,
    },
    {
        "step": 4,
        "type": "choice",
        "title": "Your Skills & Interests",
        "description": "What do you bring to the community? Select all that resonate.",
        "choices": [
            {"value": "permaculture", "label": "Permaculture & Regenerative Agriculture"},
            {"value": "building", "label": "Natural Building & Construction"},
            {"value": "tech", "label": "Technology & Digital Systems"},
            {"value": "education", "label": "Education & Facilitation"},
            {"value": "healing", "label": "Healing & Wellness"},
            {"value": "art", "label": "Arts & Culture"},
            {"value": "governance", "label": "Governance & Organizational Design"},
            {"value": "economics", "label": "Economics & Resource Management"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 5,
        "type": "confirmation",
        "title": "Community Agreements",
        "description": (
            "OmniOne operates on consent-based governance. By proceeding, you acknowledge "
            "that you'll participate in governance processes that affect you, respect the ACT "
            "decision protocol, and engage with conflicts through our repair-based resolution process."
        ),
        "confirmation_label": "I understand and am ready to participate",
        "required": True,
    },
    {
        "step": 6,
        "type": "reflection",
        "title": "Your First 30 Days",
        "description": "Imagine your first month as part of this community.",
        "reflection_prompt": "What's one thing you'd like to accomplish or experience in your first 30 days? What support would help you get there?",
        "required": False,
    },
    {
        "step": 7,
        "type": "confirmation",
        "title": "Welcome Aboard!",
        "description": (
            "You've completed the OmniOne orientation. Your profile has been created and you "
            "can now participate in governance, propose ideas, and connect with community members."
        ),
        "confirmation_label": "Let's begin!",
        "required": True,
    },
]

OMNIONE_READY_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Quick Welcome",
        "description": "A brief introduction to OmniOne for those ready to dive in.",
        "video_url": "/assets/orientation/omnione-quick.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "Your Skills & Interests",
        "description": "What do you bring to the community?",
        "choices": [
            {"value": "permaculture", "label": "Permaculture & Regenerative Agriculture"},
            {"value": "building", "label": "Natural Building & Construction"},
            {"value": "tech", "label": "Technology & Digital Systems"},
            {"value": "education", "label": "Education & Facilitation"},
            {"value": "healing", "label": "Healing & Wellness"},
            {"value": "art", "label": "Arts & Culture"},
            {"value": "governance", "label": "Governance & Organizational Design"},
            {"value": "economics", "label": "Economics & Resource Management"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 2,
        "type": "confirmation",
        "title": "Community Agreements",
        "description": (
            "By proceeding you acknowledge that you'll participate in consent-based governance, "
            "respect the ACT decision protocol, and engage with conflicts through repair-based resolution."
        ),
        "confirmation_label": "I agree to the community agreements",
        "required": True,
    },
    {
        "step": 3,
        "type": "confirmation",
        "title": "Welcome Aboard!",
        "description": "You're all set. Jump into governance, connect with members, and start contributing.",
        "confirmation_label": "Let's begin!",
        "required": True,
    },
]

# ===== ESCHERBRIDGE =====
ESCHERBRIDGE_EXPLORER_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Welcome to Escherbridge",
        "description": "Discover how our technology cooperative bridges vision and code.",
        "video_url": "/assets/orientation/escherbridge-welcome.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "Your Role",
        "description": "How do you see yourself contributing to Escherbridge?",
        "choices": [
            {"value": "developer", "label": "Software Developer", "description": "Build and ship products with the team"},
            {"value": "designer", "label": "Designer / Creative", "description": "Shape user experience and creative direction"},
            {"value": "strategist", "label": "Strategist / Product", "description": "Guide product direction and client relationships"},
            {"value": "contributor", "label": "Open Source Contributor", "description": "Contribute to our public projects"},
        ],
        "required": True,
        "section_key": "motivation",
    },
    {
        "step": 2,
        "type": "ai_conversation",
        "title": "Technical Governance",
        "description": "Learn how we make technical decisions as a cooperative.",
        "ai_prompt_template": (
            "You are an orientation guide for Escherbridge, a technology cooperative. "
            "Explain how technical decisions are made using the ACT process adapted for "
            "software teams: code reviews as advice gathering, RFC proposals for architectural "
            "changes, and test-driven validation. Discuss how we balance individual autonomy "
            "with collective code ownership. Be friendly and technical."
        ),
        "required": True,
    },
    {
        "step": 3,
        "type": "choice",
        "title": "Technical Skills",
        "description": "What technologies and domains are you experienced with?",
        "choices": [
            {"value": "fullstack", "label": "Full-Stack Web Development"},
            {"value": "ai_ml", "label": "AI / Machine Learning / Agents"},
            {"value": "blockchain", "label": "Blockchain & Web3"},
            {"value": "vr_ar", "label": "VR / AR / Spatial Computing"},
            {"value": "devops", "label": "DevOps & Infrastructure"},
            {"value": "mobile", "label": "Mobile Development"},
            {"value": "design", "label": "UX / UI Design"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 4,
        "type": "reflection",
        "title": "Open Source Philosophy",
        "description": "Reflect on how you approach collaborative development.",
        "reflection_prompt": (
            "What does good code review culture look like to you? How do you handle "
            "technical disagreements in a team?"
        ),
        "required": True,
    },
    {
        "step": 5,
        "type": "confirmation",
        "title": "Cooperative Agreements",
        "description": (
            "Escherbridge operates as a cooperative. By proceeding, you agree to participate "
            "in governance decisions, contribute to open source projects under our shared "
            "licensing model, and follow our code of conduct for inclusive collaboration."
        ),
        "confirmation_label": "I understand and agree",
        "required": True,
    },
    {
        "step": 6,
        "type": "confirmation",
        "title": "Welcome to the Team!",
        "description": (
            "You've completed the Escherbridge orientation. Set up your dev environment, "
            "review active projects, and join the next sprint planning session."
        ),
        "confirmation_label": "Let's build!",
        "required": True,
    },
]

ESCHERBRIDGE_READY_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Quick Onboarding",
        "description": "A fast intro for developers ready to start contributing.",
        "video_url": "/assets/orientation/escherbridge-quick.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "Technical Skills",
        "description": "Select your areas of expertise.",
        "choices": [
            {"value": "fullstack", "label": "Full-Stack Web Development"},
            {"value": "ai_ml", "label": "AI / Machine Learning / Agents"},
            {"value": "blockchain", "label": "Blockchain & Web3"},
            {"value": "vr_ar", "label": "VR / AR / Spatial Computing"},
            {"value": "devops", "label": "DevOps & Infrastructure"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 2,
        "type": "confirmation",
        "title": "Cooperative Agreements",
        "description": "Agree to our cooperative code of conduct and open source licensing model.",
        "confirmation_label": "I agree to the cooperative agreements",
        "required": True,
    },
    {
        "step": 3,
        "type": "confirmation",
        "title": "Welcome!",
        "description": "You're in. Check the project board and pick up your first issue.",
        "confirmation_label": "Let's build!",
        "required": True,
    },
]

# ===== PLAN SYSTEMS =====
PLANSYSTEMS_EXPLORER_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Welcome to Plan Systems",
        "description": "Learn about our mission to build spatial collaboration tools for communities.",
        "video_url": "/assets/orientation/plansystems-welcome.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "Your Interest Area",
        "description": "What aspect of Plan Systems interests you most?",
        "choices": [
            {"value": "broadband", "label": "Community Broadband & 5G", "description": "Affordable connectivity infrastructure"},
            {"value": "spatial", "label": "Spatial Collaboration (PLAN 3D)", "description": "3D digital twins and community planning tools"},
            {"value": "education", "label": "STEM Education", "description": "Teaching next-gen tech skills to communities"},
            {"value": "emergency", "label": "Emergency Response", "description": "Coordination tools for disaster preparedness"},
            {"value": "agriculture", "label": "Regenerative Agriculture", "description": "Data-driven farming and land stewardship"},
        ],
        "required": True,
        "section_key": "motivation",
    },
    {
        "step": 2,
        "type": "ai_conversation",
        "title": "Participatory Design",
        "description": "Explore how Plan Systems uses participatory design to build better tools.",
        "ai_prompt_template": (
            "You are an orientation guide for Plan Systems, a nonprofit building spatial "
            "collaboration tools. Explain participatory design: how community members co-create "
            "the tools they use. Discuss the PLAN 3D platform and how digital twins help "
            "communities visualize and plan infrastructure. Mention the advisory council's role "
            "in strategic planning. Be enthusiastic about civic technology."
        ),
        "required": True,
    },
    {
        "step": 3,
        "type": "choice",
        "title": "Your Skills",
        "description": "What skills can you bring to Plan Systems?",
        "choices": [
            {"value": "planning", "label": "Urban / Community Planning"},
            {"value": "engineering", "label": "Engineering & Infrastructure"},
            {"value": "data", "label": "Data Science & Visualization"},
            {"value": "education", "label": "Education & Training"},
            {"value": "policy", "label": "Policy & Advocacy"},
            {"value": "3d", "label": "3D Modeling & Spatial Design"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 4,
        "type": "reflection",
        "title": "Community Infrastructure",
        "description": "Think about the infrastructure challenges in your community.",
        "reflection_prompt": (
            "What infrastructure challenge in your community or city would you most like "
            "to address? How could spatial collaboration tools help?"
        ),
        "required": True,
    },
    {
        "step": 5,
        "type": "confirmation",
        "title": "Participation Agreement",
        "description": (
            "Plan Systems operates as a 501(c)(3) nonprofit. By proceeding, you agree to our "
            "open data principles, participate constructively in advisory processes, and respect "
            "the communities we serve."
        ),
        "confirmation_label": "I understand and agree to participate",
        "required": True,
    },
    {
        "step": 6,
        "type": "confirmation",
        "title": "Welcome to Plan Systems!",
        "description": (
            "Your orientation is complete. Explore active projects, review community proposals, "
            "and join the next planning session."
        ),
        "confirmation_label": "Let's plan!",
        "required": True,
    },
]

PLANSYSTEMS_READY_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Quick Start",
        "description": "A brief overview for contributors ready to engage.",
        "video_url": "/assets/orientation/plansystems-quick.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "Your Skills",
        "description": "Select your areas of expertise.",
        "choices": [
            {"value": "planning", "label": "Urban / Community Planning"},
            {"value": "engineering", "label": "Engineering & Infrastructure"},
            {"value": "data", "label": "Data Science & Visualization"},
            {"value": "education", "label": "Education & Training"},
            {"value": "policy", "label": "Policy & Advocacy"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 2,
        "type": "confirmation",
        "title": "Participation Agreement",
        "description": "Agree to our open data principles and community participation guidelines.",
        "confirmation_label": "I agree",
        "required": True,
    },
    {
        "step": 3,
        "type": "confirmation",
        "title": "Welcome!",
        "description": "You're set up. Dive into active proposals and community projects.",
        "confirmation_label": "Let's plan!",
        "required": True,
    },
]

# ===== OASIS =====
OASIS_EXPLORER_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Welcome to Oasis",
        "description": "Discover the universal cross-chain interoperability platform for digital sovereignty.",
        "video_url": "/assets/orientation/oasis-welcome.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "Your Path in Oasis",
        "description": "How do you want to engage with the Oasis ecosystem?",
        "choices": [
            {"value": "build", "label": "Protocol Developer", "description": "Build on the HyperDrive routing and Universal Asset Bridge"},
            {"value": "govern", "label": "Governance Participant", "description": "Shape the decentralized governance layer"},
            {"value": "create", "label": "Digital Creator", "description": "Mint GeoNFTs and build spatial experiences"},
            {"value": "steward", "label": "Data Steward", "description": "Manage holonic identity and data sovereignty"},
        ],
        "required": True,
        "section_key": "motivation",
    },
    {
        "step": 2,
        "type": "ai_conversation",
        "title": "Decentralized Governance",
        "description": "Learn how governance works in a remote-first, blockchain-native ecosystem.",
        "ai_prompt_template": (
            "You are an orientation guide for Oasis, a Web4 platform for digital sovereignty. "
            "Explain how the ACT governance process is adapted for asynchronous, cross-timezone "
            "decision-making. Discuss on-chain voting, proposal lifecycle, and how holonic "
            "identity enables participation without sacrificing privacy. Mention the STAR CLI "
            "metaverse generator. Be forward-thinking and accessible."
        ),
        "required": True,
    },
    {
        "step": 3,
        "type": "choice",
        "title": "Your Technical Background",
        "description": "What Web3/Web4 skills do you bring?",
        "choices": [
            {"value": "smart_contracts", "label": "Smart Contract Development"},
            {"value": "protocol", "label": "Protocol Design & Cryptography"},
            {"value": "frontend", "label": "dApp Frontend Development"},
            {"value": "infra", "label": "Node Operations & Infrastructure"},
            {"value": "tokenomics", "label": "Tokenomics & Economic Design"},
            {"value": "spatial", "label": "Spatial Computing & Metaverse"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 4,
        "type": "reflection",
        "title": "Digital Sovereignty",
        "description": "Reflect on what digital sovereignty means to you.",
        "reflection_prompt": (
            "What does owning your own data and digital identity mean to you? "
            "How could cross-chain interoperability change how communities govern themselves?"
        ),
        "required": True,
    },
    {
        "step": 5,
        "type": "confirmation",
        "title": "Platform Agreements",
        "description": (
            "Oasis operates on decentralized governance principles. By proceeding, you agree to "
            "participate in async governance, respect data sovereignty norms, and contribute to "
            "the open protocol under our shared licensing model."
        ),
        "confirmation_label": "I understand and agree",
        "required": True,
    },
    {
        "step": 6,
        "type": "confirmation",
        "title": "Welcome to the Oasis!",
        "description": (
            "Orientation complete. Explore active governance proposals, set up your holonic "
            "identity, and connect with the distributed team."
        ),
        "confirmation_label": "Let's decentralize!",
        "required": True,
    },
]

OASIS_READY_STEPS = [
    {
        "step": 0,
        "type": "video",
        "title": "Quick Onboarding",
        "description": "A fast-track intro for Web3 builders ready to contribute.",
        "video_url": "/assets/orientation/oasis-quick.mp4",
        "required": True,
    },
    {
        "step": 1,
        "type": "choice",
        "title": "Your Technical Background",
        "description": "Select your areas of expertise.",
        "choices": [
            {"value": "smart_contracts", "label": "Smart Contract Development"},
            {"value": "protocol", "label": "Protocol Design & Cryptography"},
            {"value": "frontend", "label": "dApp Frontend Development"},
            {"value": "infra", "label": "Node Operations & Infrastructure"},
            {"value": "tokenomics", "label": "Tokenomics & Economic Design"},
        ],
        "required": True,
        "section_key": "skills",
    },
    {
        "step": 2,
        "type": "confirmation",
        "title": "Platform Agreements",
        "description": "Agree to decentralized governance norms and open protocol licensing.",
        "confirmation_label": "I agree",
        "required": True,
    },
    {
        "step": 3,
        "type": "confirmation",
        "title": "Welcome!",
        "description": "Jump in. Check active proposals and pick up your first contribution.",
        "confirmation_label": "Let's decentralize!",
        "required": True,
    },
]


# ---------------------------------------------------------------------------
# Exit packages per ecosystem
# ---------------------------------------------------------------------------
def _exit_package(eco_name: str, eco_slug: str) -> dict:
    """Generate a tailored exit package for an ecosystem."""
    return {
        "docs": [
            {"title": f"{eco_name} Handbook", "url": f"/docs/{eco_slug}/handbook"},
            {"title": "Governance Quick Reference", "url": f"/docs/{eco_slug}/governance-guide"},
        ],
        "tools": [
            {"name": "Proposal Creator", "description": "Start your first governance proposal", "url": "/proposals/new"},
            {"name": "Member Directory", "description": "Find and connect with community members", "url": "/members"},
        ],
        "next_steps": [
            "Explore active proposals and add your advice",
            "Set up your profile with skills and interests",
            "Join your first governance circle meeting",
        ],
        "omnibot_prompt": (
            f"Welcome! You've completed orientation for {eco_name}. "
            "I can help you navigate governance, find proposals to contribute to, "
            "or answer questions about how things work here."
        ),
    }


# ---------------------------------------------------------------------------
# Purge orientation tables
# ---------------------------------------------------------------------------
PURGE_ORDER = [
    "user_journey_progress",
    "ethos_user_access",
    "journey_maps",
]


async def purge(database_url: str) -> None:
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        for table in PURGE_ORDER:
            try:
                await conn.execute(text(f'DELETE FROM "{table}"'))
            except Exception:
                pass
    print(f"Purged orientation data from {len(PURGE_ORDER)} tables.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# Seed function
# ---------------------------------------------------------------------------
async def seed(database_url: str) -> None:
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Idempotency check
        existing = await session.execute(text("SELECT count(*) FROM journey_maps"))
        if existing.scalar() > 0:
            print("Journey maps already seeded. Skipping. Use --purge to reseed.")
            await engine.dispose()
            return

        jm_count = 0
        access_count = 0

        # ===============================================================
        # 1. JOURNEY MAPS -- 2 per ecosystem (8 total)
        # ===============================================================
        journey_specs = [
            # OmniOne
            {
                "id": _uid("jm.omnione.explorer"),
                "slug": "omnione-explorer",
                "title": "OmniOne Explorer Path",
                "description": "Discover what it means to be part of a regenerative community in Bali. Learn about consent-based governance, meet the community, and find your role.",
                "ecosystem_id": eco_omni_id,
                "content_sequence": OMNIONE_EXPLORER_STEPS,
                "exit_package": _exit_package("OmniOne", "omnione"),
                "step_count": len(OMNIONE_EXPLORER_STEPS),
                "is_default": True,
                "is_active": True,
                "sector_alignment": ["regenerative", "governance", "community"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
            {
                "id": _uid("jm.omnione.ready"),
                "slug": "omnione-ready-to-join",
                "title": "OmniOne Ready to Join",
                "description": "Fast-track orientation for those already familiar with OmniOne who are ready to become active members.",
                "ecosystem_id": eco_omni_id,
                "content_sequence": OMNIONE_READY_STEPS,
                "exit_package": _exit_package("OmniOne", "omnione"),
                "step_count": len(OMNIONE_READY_STEPS),
                "is_default": False,
                "is_active": True,
                "sector_alignment": ["regenerative", "governance", "community"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
            # Escherbridge
            {
                "id": _uid("jm.escherbridge.explorer"),
                "slug": "escherbridge-explorer",
                "title": "Escherbridge Explorer Path",
                "description": "Learn how our technology cooperative works, from code review culture to cooperative governance. Find your place in the team.",
                "ecosystem_id": eco_eb_id,
                "content_sequence": ESCHERBRIDGE_EXPLORER_STEPS,
                "exit_package": _exit_package("Escherbridge", "escherbridge"),
                "step_count": len(ESCHERBRIDGE_EXPLORER_STEPS),
                "is_default": True,
                "is_active": True,
                "sector_alignment": ["technology", "creative-arts", "collaboration"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
            {
                "id": _uid("jm.escherbridge.ready"),
                "slug": "escherbridge-ready-to-join",
                "title": "Escherbridge Ready to Join",
                "description": "Quick onboarding for developers and creatives ready to start contributing immediately.",
                "ecosystem_id": eco_eb_id,
                "content_sequence": ESCHERBRIDGE_READY_STEPS,
                "exit_package": _exit_package("Escherbridge", "escherbridge"),
                "step_count": len(ESCHERBRIDGE_READY_STEPS),
                "is_default": False,
                "is_active": True,
                "sector_alignment": ["technology", "creative-arts", "collaboration"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
            # Plan Systems
            {
                "id": _uid("jm.plansystems.explorer"),
                "slug": "plansystems-explorer",
                "title": "Plan Systems Explorer Path",
                "description": "Discover how Plan Systems builds spatial collaboration tools through participatory design. Learn about community broadband, digital twins, and civic tech.",
                "ecosystem_id": eco_ps_id,
                "content_sequence": PLANSYSTEMS_EXPLORER_STEPS,
                "exit_package": _exit_package("Plan Systems", "plansystems"),
                "step_count": len(PLANSYSTEMS_EXPLORER_STEPS),
                "is_default": True,
                "is_active": True,
                "sector_alignment": ["systems-thinking", "planning", "cooperative"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
            {
                "id": _uid("jm.plansystems.ready"),
                "slug": "plansystems-ready-to-join",
                "title": "Plan Systems Ready to Join",
                "description": "Fast-track for contributors ready to engage with community planning projects.",
                "ecosystem_id": eco_ps_id,
                "content_sequence": PLANSYSTEMS_READY_STEPS,
                "exit_package": _exit_package("Plan Systems", "plansystems"),
                "step_count": len(PLANSYSTEMS_READY_STEPS),
                "is_default": False,
                "is_active": True,
                "sector_alignment": ["systems-thinking", "planning", "cooperative"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
            # Oasis
            {
                "id": _uid("jm.oasis.explorer"),
                "slug": "oasis-explorer",
                "title": "Oasis Explorer Path",
                "description": "Explore the Web4 platform for digital sovereignty. Learn about decentralized governance, cross-chain interoperability, and holonic identity.",
                "ecosystem_id": eco_oa_id,
                "content_sequence": OASIS_EXPLORER_STEPS,
                "exit_package": _exit_package("Oasis", "oasis"),
                "step_count": len(OASIS_EXPLORER_STEPS),
                "is_default": True,
                "is_active": True,
                "sector_alignment": ["web4", "decentralized", "digital-sovereignty"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
            {
                "id": _uid("jm.oasis.ready"),
                "slug": "oasis-ready-to-join",
                "title": "Oasis Ready to Join",
                "description": "Quick onboarding for Web3 builders ready to contribute to the decentralized platform.",
                "ecosystem_id": eco_oa_id,
                "content_sequence": OASIS_READY_STEPS,
                "exit_package": _exit_package("Oasis", "oasis"),
                "step_count": len(OASIS_READY_STEPS),
                "is_default": False,
                "is_active": False,  # Inactive: tests include_inactive filter
                "sector_alignment": ["web4", "decentralized", "digital-sovereignty"],
                "role_types": ["co_creator", "builder", "townhall"],
                "min_alignment_score": None,
            },
        ]

        for spec in journey_specs:
            session.add(JourneyMap(
                id=spec["id"],
                slug=spec["slug"],
                title=spec["title"],
                description=spec["description"],
                ecosystem_id=spec["ecosystem_id"],
                content_sequence=spec["content_sequence"],
                exit_package=spec["exit_package"],
                step_count=spec["step_count"],
                is_default=spec["is_default"],
                is_active=spec["is_active"],
                sector_alignment=spec["sector_alignment"],
                role_types=spec["role_types"],
                min_alignment_score=spec["min_alignment_score"],
            ))
            jm_count += 1

        await session.flush()

        # ===============================================================
        # 2. ETHOS USER ACCESS -- all active members get access to their ecosystem
        # ===============================================================
        # (member_id, ecosystem_id, role, access_level, granted_by)
        ethos_specs = [
            # OmniOne
            (m_josh_id, eco_omni_id, "steward", "admin", None),
            (m_nathan_id, eco_omni_id, "member", "member", m_josh_id),
            (m_ahmed_id, eco_omni_id, "member", "member", m_josh_id),
            # Escherbridge
            (m_ahmed_eb_id, eco_eb_id, "steward", "admin", None),
            (m_kenny_id, eco_eb_id, "member", "member", m_ahmed_eb_id),
            (m_jak_id, eco_eb_id, "member", "member", m_ahmed_eb_id),
            # Plan Systems
            (m_rachel_id, eco_ps_id, "steward", "admin", None),
            (m_brandon_id, eco_ps_id, "member", "member", m_rachel_id),
            (m_drew_id, eco_ps_id, "member", "member", m_rachel_id),
            # Oasis
            (m_max_id, eco_oa_id, "steward", "admin", None),
            (m_david_id, eco_oa_id, "member", "member", m_max_id),
        ]

        for mid, eco_id, role, level, granted_by in ethos_specs:
            session.add(EthosUserAccess(
                id=_uid(f"ethos.{mid}.{eco_id}"),
                member_id=mid,
                ecosystem_id=eco_id,
                role_in_ethos=role,
                access_level=level,
                granted_at=_NOW,
                granted_by=granted_by,
            ))
            access_count += 1

        await session.commit()

    await engine.dispose()

    print()
    print("=== Orientation Seed Data ===")
    print(f"Journey maps: {jm_count} (2 per ecosystem: Explorer + Ready to Join)")
    print(f"Ethos user access records: {access_count}")
    print("Ecosystems covered: OmniOne, Escherbridge, Plan Systems, Oasis")
    print("=== Done ===")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed orientation data for QA testing")
    parser.add_argument("--purge", action="store_true", help="Delete orientation data before seeding")
    args = parser.parse_args()

    try:
        from neos_agent.config import get_settings
        database_url = get_settings().DATABASE_URL
    except Exception:
        print("Error: DATABASE_URL not set. Set it as an environment variable or in agent/.env")
        sys.exit(1)

    if args.purge:
        print("Purging orientation data...")
        asyncio.run(purge(database_url))

    asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
