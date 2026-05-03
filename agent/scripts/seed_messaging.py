"""Seed messaging data: conversations, messages, conversation links, push subscriptions.

Usage:
    python -m agent.scripts.seed_messaging
    python -m agent.scripts.seed_messaging --purge

Creates:
  8 conversations (2 per ecosystem: 1 DM, 1 group)
  48+ messages across conversations
  4 conversation links to governance entities
  8 push subscriptions
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from neos_agent.db.models import (
    Base,
    Conversation,
    ConversationParticipant,
    Message,
    ConversationLink,
    PushSubscription,
)


# ---------------------------------------------------------------------------
# Deterministic UUID helper — must match seed_omnione
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
# Proposal / Agreement IDs for conversation links (must match seed_omnione)
# ---------------------------------------------------------------------------
prop_omni = _uid("prop.omni.1")
prop_eb = _uid("prop.eb.1")
agr_omni_resource = _uid("agr.omni.resource")
agr_eb_unique = _uid("agr.eb.unique")


# ---------------------------------------------------------------------------
# Purge messaging-related tables
# ---------------------------------------------------------------------------
PURGE_ORDER = [
    "push_subscriptions",
    "conversation_links",
    "messages",
    "conversation_participants",
    "conversations",
]


async def purge(database_url: str) -> None:
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        for table in PURGE_ORDER:
            try:
                await conn.execute(text(f'DELETE FROM "{table}"'))
            except Exception:
                pass
    print(f"Purged messaging data from {len(PURGE_ORDER)} tables.")
    await engine.dispose()


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------
_NOW = datetime.utcnow()


def _ago(**kwargs) -> datetime:
    """Return a datetime offset from _NOW by the given timedelta kwargs."""
    return _NOW - timedelta(**kwargs)


# ---------------------------------------------------------------------------
# Per-ecosystem conversation definitions
# ---------------------------------------------------------------------------

ECOSYSTEMS = [
    {
        "eco_id": eco_omni_id,
        "eco_short": "omni",
        "eco_name": "OmniOne",
        "members": [m_josh_id, m_nathan_id, m_ahmed_id],
        "names": ["Josh", "Nathan", "Ahmed"],
        "dm": {
            "owner_idx": 0,
            "peer_idx": 1,
            "messages": [
                (0, "text", "Hey Nathan, have you had a chance to look at the energy sharing proposal yet?", 6, 12),
                (1, "text", "Just finished reading through it. The solar credit distribution section is solid but I have concerns about peak usage allocation.", 6, 8),
                (0, "text", "Yeah I had similar thoughts. The 70/30 split during peak hours seems aggressive for smaller households.", 6, 4),
                (1, "text", "Exactly. I think we should suggest a sliding scale based on historical usage patterns instead of a flat ratio.", 5, 18),
                (0, "text", "Good call. Want to draft an amendment together before the consent round on Thursday?", 5, 10),
                (1, "text", "Sounds good. I will put something together tonight and share it with you tomorrow morning.", 5, 2),
            ],
        },
        "group": {
            "title": "OmniOne Governance Circle",
            "messages": [
                (0, "text", "Team, reminder that we have the quarterly governance review coming up next Monday.", 7, 0),
                (1, "text", "Thanks Josh. I have been compiling the domain health metrics and everything looks on track.", 6, 18),
                (2, "text", "Quick question - are we including the new resource sharing agreement in this review cycle?", 6, 14),
                (0, "text", "Yes, it is on the agenda. We need to assess how the first 30-day test period went.", 6, 6),
                (1, "text", "The participation numbers have been strong. 87% engagement across all domains.", 5, 22),
                (0, "governance_link", "Linked: Energy Sharing Proposal - ready for consent round discussion", 5, 14),
                (2, "text", "Can we schedule a facilitated consent round for next Monday right after the review?", 4, 10),
                (0, "text", "Good idea. I will add it to the agenda and send out prep materials by Friday.", 4, 2),
            ],
        },
        "link_proposal": prop_omni,
        "link_agreement": agr_omni_resource,
    },
    {
        "eco_id": eco_eb_id,
        "eco_short": "eb",
        "eco_name": "Escherbridge",
        "members": [m_ahmed_eb_id, m_kenny_id, m_jak_id],
        "names": ["Ahmed", "Kenny", "Jak"],
        "dm": {
            "owner_idx": 0,
            "peer_idx": 1,
            "messages": [
                (0, "text", "Kenny, I wanted to chat about the creative commons licensing proposal before it goes to the full circle.", 7, 6),
                (1, "text", "Sure thing. I have been thinking about how it affects existing works versus new submissions.", 6, 20),
                (0, "text", "Right, we need a grandfather clause for works created before the policy change.", 6, 10),
                (1, "text", "Agreed. I also think we should offer dual licensing options - CC-BY-SA for collaborative works, CC-BY for individual pieces.", 5, 16),
                (0, "text", "That is a thoughtful distinction. Let me draft language for that and run it by the art domain steward.", 5, 8),
                (1, "text", "Perfect. I will prepare some examples of how each license type would work in practice for the presentation.", 4, 14),
            ],
        },
        "group": {
            "title": "Escherbridge Creative Council",
            "messages": [
                (0, "text", "Hello everyone. We need to finalize the resource allocation for next quarter's creative projects.", 7, 4),
                (2, "text", "I put together a spreadsheet comparing last quarter's allocations against actual usage. Sharing it now.", 6, 16),
                (1, "text", "Thanks Jak. Looking at the numbers, the digital art domain used only 40% of their allocation.", 6, 10),
                (0, "text", "That is a trend we should address. Maybe we can reallocate unused funds to the mentorship program.", 5, 20),
                (2, "text", "I support that. The mentorship waitlist has 12 people on it right now.", 5, 12),
                (1, "text", "What about a flexible pool system? Domains can draw from shared reserves if they exceed their baseline.", 4, 18),
                (0, "governance_link", "Linked: Q2 Resource Allocation Agreement - under review", 4, 8),
                (0, "text", "Great discussion. Let me compile these suggestions into a formal proposal by end of week.", 3, 14),
            ],
        },
        "link_proposal": prop_eb,
        "link_agreement": agr_eb_unique,
    },
    {
        "eco_id": eco_ps_id,
        "eco_short": "ps",
        "eco_name": "Plan Systems",
        "members": [m_rachel_id, m_brandon_id, m_drew_id],
        "names": ["Rachel", "Brandon", "Drew"],
        "dm": {
            "owner_idx": 0,
            "peer_idx": 1,
            "messages": [
                (0, "text", "Brandon, I want to get your input on integrating the PLAN-Unity SDK with our governance workflows.", 6, 22),
                (1, "text", "I have been prototyping a spatial collaboration space for consent rounds. Early results are promising.", 6, 14),
                (0, "text", "That sounds great. How does it handle asynchronous participation for members in different time zones?", 6, 4),
                (1, "text", "Each participant gets a persistent avatar that shows their current stance. They can update it anytime during the window.", 5, 18),
                (0, "text", "Clever approach. We should pilot it with the systems design domain first since they are already comfortable with spatial tools.", 5, 6),
                (1, "text", "Agreed. I will have a demo-ready version by next Wednesday for the domain meeting.", 4, 12),
            ],
        },
        "group": {
            "title": "Plan Systems Design Hub",
            "messages": [
                (0, "text", "Team check-in: where are we on the advisory council feedback integration?", 7, 8),
                (1, "text", "I finished mapping council recommendations to our existing domain structure. There are 3 areas of misalignment.", 6, 22),
                (2, "text", "Which areas? I want to make sure they align with what I heard in the stakeholder interviews.", 6, 12),
                (1, "text", "Decision authority boundaries, resource allocation thresholds, and conflict escalation timelines.", 5, 20),
                (0, "text", "The conflict escalation piece is critical. Our GAIA model timelines are much shorter than what the council suggested.", 5, 10),
                (2, "text", "I think our shorter timelines are actually better. The council's 30-day cooling period feels too long for urgent matters.", 4, 16),
                (0, "text", "Good point. Let us document our rationale clearly so we can present it confidently at the next joint session.", 4, 4),
                (1, "text", "I will draft a comparison document showing outcomes under both timeline models.", 3, 8),
            ],
        },
        "link_proposal": None,
        "link_agreement": None,
    },
    {
        "eco_id": eco_oa_id,
        "eco_short": "oa",
        "eco_name": "Oasis",
        "members": [m_max_id, m_david_id],
        "names": ["Max", "David"],
        "dm": {
            "owner_idx": 0,
            "peer_idx": 1,
            "messages": [
                (0, "text", "David, the cross-chain identity bridge is almost ready for testing. Want to review the protocol spec?", 6, 16),
                (1, "text", "Absolutely. I have been working on the holonic identity resolver on my end. We should make sure they mesh.", 6, 8),
                (0, "text", "Good thinking. The key challenge is maintaining identity continuity when members interact across ecosystem boundaries.", 5, 22),
                (1, "text", "I solved that with a merkle-tree approach for identity attestations. Each ecosystem node validates independently.", 5, 12),
                (0, "text", "Elegant. Let us schedule a technical review with the protocol engineering circle this week.", 4, 18),
                (1, "text", "Thursday works for me. I will prepare the architecture diagrams and sequence flows.", 4, 6),
            ],
        },
        "group": {
            "title": "Oasis Protocol Commons",
            "messages": [
                (0, "text", "Protocol update: the async ACT process implementation is now live on testnet.", 7, 2),
                (1, "text", "Nice work Max. I ran through the consent round flow and the UX is much smoother than the synchronous version.", 6, 14),
                (0, "text", "Thanks. The big win is that members can participate from any chain without bridging tokens first.", 6, 4),
                (1, "text", "Have we stress-tested the finality guarantees? Cross-chain consensus can be tricky with network partitions.", 5, 16),
                (0, "text", "Yes, we simulated 100-node partitions. Finality holds as long as 2/3 of validators are reachable.", 5, 4),
                (1, "text", "That is solid. We should document the failure modes for the governance transparency report.", 4, 14),
                (0, "text", "Agreed. I will add a section on Byzantine fault tolerance to the protocol spec.", 3, 20),
                (1, "text", "I can help draft the non-technical summary for the broader community.", 3, 6),
            ],
        },
        "link_proposal": None,
        "link_agreement": None,
    },
]


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

async def seed(database_url: str) -> None:
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Idempotency check
        existing = await session.execute(text("SELECT count(*) FROM conversations"))
        if existing.scalar() > 0:
            print("Conversations already seeded. Skipping. Use --purge to reseed.")
            await engine.dispose()
            return

        conv_count = 0
        msg_count = 0
        link_count = 0
        push_count = 0

        for eco in ECOSYSTEMS:
            eco_id = eco["eco_id"]
            eco_short = eco["eco_short"]
            members = eco["members"]

            # ---------------------------------------------------------------
            # DM conversation
            # ---------------------------------------------------------------
            dm_id = _uid(f"conv.{eco_short}.dm")
            dm_def = eco["dm"]
            owner_member = members[dm_def["owner_idx"]]
            peer_member = members[dm_def["peer_idx"]]

            session.add(Conversation(
                id=dm_id,
                ecosystem_id=eco_id,
                type="dm",
                title=None,
                created_by=owner_member,
            ))
            conv_count += 1

            # DM participants
            session.add(ConversationParticipant(
                id=_uid(f"cp.{eco_short}.dm.owner"),
                conversation_id=dm_id,
                member_id=owner_member,
                role="owner",
                joined_at=_ago(days=7),
                last_read_at=_ago(days=4),
            ))
            session.add(ConversationParticipant(
                id=_uid(f"cp.{eco_short}.dm.peer"),
                conversation_id=dm_id,
                member_id=peer_member,
                role="member",
                joined_at=_ago(days=7),
                last_read_at=None,
            ))

            # DM messages
            for i, (sender_idx, msg_type, content, days_ago, hours_ago) in enumerate(dm_def["messages"]):
                sender = members[sender_idx]
                session.add(Message(
                    id=_uid(f"msg.{eco_short}.dm.{i}"),
                    conversation_id=dm_id,
                    sender_id=sender,
                    content=content,
                    message_type=msg_type,
                    message_metadata=None,
                    created_at=_ago(days=days_ago, hours=hours_ago),
                ))
                msg_count += 1

            # ---------------------------------------------------------------
            # Group conversation
            # ---------------------------------------------------------------
            grp_id = _uid(f"conv.{eco_short}.group")
            grp_def = eco["group"]

            session.add(Conversation(
                id=grp_id,
                ecosystem_id=eco_id,
                type="group",
                title=grp_def["title"],
                created_by=members[0],
            ))
            conv_count += 1

            # Group participants
            for j, member in enumerate(members):
                role = "owner" if j == 0 else "member"
                session.add(ConversationParticipant(
                    id=_uid(f"cp.{eco_short}.grp.{j}"),
                    conversation_id=grp_id,
                    member_id=member,
                    role=role,
                    joined_at=_ago(days=7),
                    last_read_at=_ago(days=3) if j == 0 else None,
                ))

            # Group messages
            for i, (sender_idx, msg_type, content, days_ago, hours_ago) in enumerate(grp_def["messages"]):
                sender = members[sender_idx]
                metadata = None
                if msg_type == "governance_link":
                    # Point to the ecosystem's proposal if available
                    linked_id = eco.get("link_proposal") or _uid(f"prop.{eco_short}.placeholder")
                    metadata = {"entity_type": "proposal", "entity_id": str(linked_id)}

                session.add(Message(
                    id=_uid(f"msg.{eco_short}.grp.{i}"),
                    conversation_id=grp_id,
                    sender_id=sender,
                    content=content,
                    message_type=msg_type,
                    message_metadata=metadata,
                    created_at=_ago(days=days_ago, hours=hours_ago),
                ))
                msg_count += 1

            # ---------------------------------------------------------------
            # Conversation links (OmniOne and Escherbridge only)
            # ---------------------------------------------------------------
            if eco["link_proposal"] is not None:
                session.add(ConversationLink(
                    id=_uid(f"cl.{eco_short}.dm.proposal"),
                    conversation_id=dm_id,
                    entity_type="proposal",
                    entity_id=eco["link_proposal"],
                    created_by=members[0],
                ))
                link_count += 1

            if eco["link_agreement"] is not None:
                session.add(ConversationLink(
                    id=_uid(f"cl.{eco_short}.grp.agreement"),
                    conversation_id=grp_id,
                    entity_type="agreement",
                    entity_id=eco["link_agreement"],
                    created_by=members[0],
                ))
                link_count += 1

            # ---------------------------------------------------------------
            # Push subscriptions (first 2 members per ecosystem)
            # ---------------------------------------------------------------
            sub_members = members[:2]
            for k, member in enumerate(sub_members):
                short_name = eco["names"][k].lower()
                session.add(PushSubscription(
                    id=_uid(f"push.{eco_short}.{short_name}"),
                    member_id=member,
                    endpoint=f"https://fcm.googleapis.com/fcm/send/FAKE-{eco_short}-{short_name}",
                    p256dh_key=f"BFake{eco_short.upper()}{short_name.capitalize()}P256dhKeyBase64Padding0000000000==",
                    auth_key=f"FAKE{eco_short.upper()}{short_name.capitalize()}AuthKey==",
                    enabled=True,
                    notification_types=["proposal_update", "message", "emergency"],
                ))
                push_count += 1

        await session.commit()

    await engine.dispose()

    print()
    print("=== Messaging Seed Data ===")
    print(f"Conversations: {conv_count} (4 DM, 4 group)")
    print(f"Messages: {msg_count}")
    print(f"Conversation links: {link_count}")
    print(f"Push subscriptions: {push_count}")
    print(f"Ecosystems covered: OmniOne, Escherbridge, Plan Systems, Oasis")
    print("=== Done ===")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Seed messaging data for QA testing")
    parser.add_argument("--purge", action="store_true", help="Delete messaging data before seeding")
    args = parser.parse_args()

    try:
        from neos_agent.config import get_settings
        database_url = get_settings().DATABASE_URL
    except Exception:
        print("Error: DATABASE_URL not set. Set it as an environment variable or in agent/.env")
        sys.exit(1)

    if args.purge:
        print("Purging messaging data...")
        asyncio.run(purge(database_url))

    asyncio.run(seed(database_url))


if __name__ == "__main__":
    main()
