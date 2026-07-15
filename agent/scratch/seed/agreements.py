"""
One agreement at each level of the NEOS agreement hierarchy:

  1. UAF (Universal Agreement Field)
  2. Ecosystem Agreement (OmniOne Master Plan)
  3. Access Agreement (SHUR Facility Access Rules)
  4. Stewardship Agreement (Resource Pool Steward Commitment)
  5. ETHOS Agreement Field (TH Culture Code)
  6. (Personal Commitments are out of scope for seed — tracked via member profile)

Each agreement has ratification records, at least one has amendments,
and at least one has review records.
"""

from __future__ import annotations

import uuid
from datetime import date

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

# ── Agreement IDs ──────────────────────────────────────────────────

AG_UAF            = uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430c1")
AG_MASTER_PLAN    = uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430c2")
AG_SHUR_ACCESS    = uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430c3")
AG_POOL_STEWARD   = uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430c4")
AG_TH_CULTURE     = uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430c5")
AG_AE_CULTURE     = uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430c6")

# ── Agreement definitions ──────────────────────────────────────────

AGREEMENTS: list[dict] = [
    # 1. UAF — root agreement, every participant consents on entry
    {
        "id": AG_UAF,
        "ecosystem_id": ECOSYSTEM_ID,
        "agreement_id": "AG-UAF-001",
        "type": "uaf",
        "title": "OmniOne Universal Agreement Field (UAF) v1.0",
        "version": "1.0",
        "status": "ratified",
        "proposer": "Manu Dewantara",
        "affected_parties": {"scope": "all_ecosystem_participants"},
        "domain": "OmniOne Ecosystem",
        "text": (
            "**Preamble.**  By entering the OmniOne ecosystem, every participant "
            "consents to this Universal Agreement Field.  The UAF is the root of the "
            "agreement hierarchy — all other agreements derive their authority from "
            "their structural alignment with the UAF.\n\n"
            "**Core Commitments.**\n"
            "1. **No sovereign authority.**  I acknowledge that no person, council, "
            "or token holds permanent override power in OmniOne.\n"
            "2. **Scoped authority.**  I accept that all authority exists within "
            "defined, reviewable domains.\n"
            "3. **Voluntary participation.**  I understand that my participation is "
            "voluntary and that exit is always structurally possible.\n"
            "4. **Capital ≠ governance.**  I agree that economic contribution does "
            "not purchase governance authority.\n"
            "5. **Solutionary decisions.**  I commit to the Advice-Consent-Test "
            "process for structural decisions.\n"
            "6. **Local failure containment.**  I accept that my ETHOS's failures "
            "are contained within that unit.\n"
            "7. **Explicit agreements.**  I understand that nothing governs by "
            "implication — if it is not written, it is not binding.\n"
            "8. **Capture resistance.**  I support the ongoing structural detection "
            "and resistance to governance capture.\n"
            "9. **Pluralism.**  I acknowledge that multiple value systems coexist "
            "through shared agreements, not shared beliefs.\n"
            "10. **Emergency contraction.**  I accept that emergency authority "
            "auto-expires and cannot become permanent.\n\n"
            "**Consent.**  By signing below, I consent to these ten structural "
            "principles and enter the OmniOne ecosystem."
        ),
        "hierarchy_level": "foundational",
        "parent_agreement_id": None,
        "review_date": date(2026, 12, 15),
        "sunset_date": None,
        "ratification_date": date(2024, 6, 22),
        "created_date": date(2024, 6, 15),
    },

    # 2. Ecosystem Agreement — OmniOne Master Plan
    {
        "id": AG_MASTER_PLAN,
        "ecosystem_id": ECOSYSTEM_ID,
        "agreement_id": "AG-ECO-001",
        "type": "ecosystem",
        "title": "OmniOne Master Plan v1.0",
        "version": "1.0",
        "status": "ratified",
        "proposer": "Manu Dewantara",
        "affected_parties": {"scope": "all_ecosystem_participants"},
        "domain": "OmniOne Ecosystem",
        "text": (
            "The OmniOne Master Plan establishes the ecosystem's strategic direction, "
            "ETHOS structure, and coordination framework.\n\n"
            "**ETHOS Units.**  OmniOne currently operates two ETHOS:\n"
            "- **Town Hall (TH):** Civic participation, cultural governance, and "
            "community decisions.\n"
            "- **Applied Ecology (AE):** Land stewardship, permaculture, and "
            "resource pool management.\n\n"
            "**Coordination.**  The OmniOne Stewardship Council (OSC) coordinates "
            "cross-ETHOS decisions.  The OSC has coordination authority, not "
            "override authority.\n\n"
            "**Resource Pool.**  A shared resource pool stewarded by AE supports "
            "ecosystem operations.  The pool is governed by the Funding Pool "
            "Stewardship agreement.\n\n"
            "**Influence Currency.**  Every participant receives 111 Current-Sees "
            "(influence units) distributed equally.  Current-Sees express governance "
            "preferences but do not confer decision-making authority — decisions "
            "are made through ACT, not voting.\n\n"
            "**Review.**  This Master Plan is reviewed annually through the ACT process."
        ),
        "hierarchy_level": "operational",
        "parent_agreement_id": AG_UAF,
        "review_date": date(2026, 12, 15),
        "sunset_date": None,
        "ratification_date": date(2024, 7, 1),
        "created_date": date(2024, 6, 20),
    },

    # 3. Access Agreement — SHUR Facility Access Rules
    {
        "id": AG_SHUR_ACCESS,
        "ecosystem_id": ECOSYSTEM_ID,
        "agreement_id": "AG-ACC-001",
        "type": "access",
        "title": "SHUR Facility Access Rules v1.1",
        "version": "1.1",
        "status": "ratified",
        "proposer": "Gede Artha",
        "affected_parties": {
            "ethos": ["TH", "AE"],
            "roles": ["builder", "townhall"],
        },
        "domain": "Applied Ecology ETHOS",
        "text": (
            "SHUR (Shelter-Hub-Utility-Resilience) facilities are shared physical "
            "spaces operated within the AE ETHOS.\n\n"
            "**Access Rules.**\n"
            "1. All OmniOne participants may use SHUR common areas during daylight "
            "hours (06:00-20:00) without prior booking.\n"
            "2. Overnight stays require 48-hour advance booking through the SHUR "
            "access steward.\n"
            "3. Workshop/event space requires 7-day advance booking and ACT consent "
            "from AE if the event involves >20 people.\n"
            "4. Construction/modification of SHUR facilities requires a formal "
            "proposal through the ACT process.\n"
            "5. Quiet hours: 22:00-06:00.\n\n"
            "**Responsibilities.**  All users leave spaces as they found them.  "
            "Damage is reported, not hidden.  Repeated access violations trigger "
            "a coaching intervention."
        ),
        "hierarchy_level": "domain",
        "parent_agreement_id": AG_MASTER_PLAN,
        "review_date": date(2026, 9, 1),
        "sunset_date": None,
        "ratification_date": date(2024, 9, 15),
        "created_date": date(2024, 8, 10),
    },

    # 4. Stewardship Agreement — Resource Pool Steward Commitment
    {
        "id": AG_POOL_STEWARD,
        "ecosystem_id": ECOSYSTEM_ID,
        "agreement_id": "AG-STEW-001",
        "type": "stewardship",
        "title": "Resource Pool Steward Commitment v1.0",
        "version": "1.0",
        "status": "ratified",
        "proposer": "Lani Wijaya",
        "affected_parties": {
            "ethos": ["AE"],
            "roles": ["resource_steward"],
        },
        "domain": "Applied Ecology ETHOS",
        "text": (
            "As Resource Pool Steward, I commit to:\n\n"
            "1. **Transparency.**  Publish pool balance and transaction log monthly.\n"
            "2. **Discretionary limit.**  Disburse no more than 5% of pool balance "
            "per request without circle consent.\n"
            "3. **No self-dealing.**  Never authorize a disbursement to myself or "
            "my immediate family.\n"
            "4. **Participatory allocation.**  Run participatory allocation sessions "
            "quarterly for requests above the discretionary threshold.\n"
            "5. **Reserve maintenance.**  Maintain a minimum 10% emergency reserve.\n"
            "6. **Rotation.**  Step down after 12 months and support a smooth "
            "transition to the next steward.\n\n"
            "This commitment is reviewed every 6 months by the AE ETHOS."
        ),
        "hierarchy_level": "local",
        "parent_agreement_id": AG_SHUR_ACCESS,
        "review_date": date(2026, 6, 1),
        "sunset_date": None,
        "ratification_date": date(2024, 10, 1),
        "created_date": date(2024, 9, 20),
    },

    # 5. ETHOS Agreement — TH Culture Code
    {
        "id": AG_TH_CULTURE,
        "ecosystem_id": ECOSYSTEM_ID,
        "agreement_id": "AG-ETHOS-TH-001",
        "type": "ethos",
        "title": "Town Hall Culture Code v1.0",
        "version": "1.0",
        "status": "ratified",
        "proposer": "Putu Ardana",
        "affected_parties": {
            "ethos": ["TH"],
        },
        "domain": "Town Hall ETHOS",
        "text": (
            "The TH Culture Code defines how we work together within the Town Hall "
            "ETHOS.  It is subordinate to the UAF and the Master Plan but governs "
            "day-to-day interactions within TH.\n\n"
            "**Our Practices.**\n"
            "1. **Assembly rhythm.**  TH holds a general assembly every new moon "
            "(Tilem).  Attendance is encouraged but not mandatory.\n"
            "2. **Decision-making.**  Decisions within TH follow ACT.  Preference "
            "decisions (minor or personal scope) may resolve at circle level.\n"
            "3. **Hospitality.**  Every assembly begins with offerings (canang) and "
            "shared food.  This is not ceremonial overhead — it is structural "
            "relationship maintenance.\n"
            "4. **Language accessibility.**  All TH agreements and proposals are "
            "available in Balinese and Indonesian, not only English.\n"
            "5. **Intergenerational bridge.**  TH members commit to mentoring at "
            "least one younger participant and learning from at least one elder.\n"
            "6. **Conflict.**  Interpersonal conflict within TH is first addressed "
            "through direct dialogue.  If unresolved, escalate to Kai for triage.\n"
            "7. **Exit from TH.**  A member may leave TH at any time.  Leaving TH "
            "does not automatically mean leaving OmniOne."
        ),
        "hierarchy_level": "domain",
        "parent_agreement_id": AG_MASTER_PLAN,
        "review_date": date(2026, 6, 15),
        "sunset_date": None,
        "ratification_date": date(2024, 11, 1),
        "created_date": date(2024, 10, 15),
    },

    # 5b. ETHOS Agreement — AE Culture Code
    {
        "id": AG_AE_CULTURE,
        "ecosystem_id": ECOSYSTEM_ID,
        "agreement_id": "AG-ETHOS-AE-001",
        "type": "ethos",
        "title": "Applied Ecology Culture Code v1.0",
        "version": "1.0",
        "status": "ratified",
        "proposer": "Lani Wijaya",
        "affected_parties": {
            "ethos": ["AE"],
        },
        "domain": "Applied Ecology ETHOS",
        "text": (
            "The AE Culture Code governs how the Applied Ecology ETHOS works "
            "together in stewarding land and resources.\n\n"
            "**Our Practices.**\n"
            "1. **Land-first principle.**  Every AE decision asks: 'What serves "
            "the health of the land?' before 'What serves our convenience?'\n"
            "2. **Subak alignment.**  AE water management aligns with the subak "
            "system's water distribution principles.\n"
            "3. **Seasonal rhythm.**  AE follows the Balinese agricultural calendar "
            "(Sasih) for planning cycles.\n"
            "4. **Resource transparency.**  Every AE member can see the resource "
            "pool balance at any time.\n"
            "5. **Knowledge sharing.**  AE members commit to teaching one skill "
            "to the community per quarter.\n"
            "6. **Conflict.**  Disputes over land or resource use route through "
            "Kai's triage process before escalating."
        ),
        "hierarchy_level": "domain",
        "parent_agreement_id": AG_MASTER_PLAN,
        "review_date": date(2026, 6, 15),
        "sunset_date": None,
        "ratification_date": date(2024, 11, 1),
        "created_date": date(2024, 10, 15),
    },
]

# ── Ratification Records ───────────────────────────────────────────

RATIFICATION_RECORDS: list[dict] = []

# UAF — ratified by all persona members (completed onboarding)
from personas import PERSONAS
for p in PERSONAS:
    if p["current_status"] == "active" and p["onboarding_status"] == "complete":
        RATIFICATION_RECORDS.append({
            "agreement_id": AG_UAF,
            "participant": p["display_name"],
            "role": p["profile"],
            "position": "consent",
            "date": date(2024, 6, 22) if p["display_name"] in (
                "Manu Dewantara", "Lani Wijaya", "Nirmala Sari"
            ) else date(2024, 7, 1),
        })

# SHUR Access — ratification records
for name in ["Lani Wijaya", "Gede Artha", "Dewa Putra", "Budi Santoso"]:
    RATIFICATION_RECORDS.append({
        "agreement_id": AG_SHUR_ACCESS,
        "participant": name,
        "role": "builder",
        "position": "consent",
        "date": date(2024, 9, 15),
    })

# TH Culture Code — ratified by TH members
for name in ["Putu Ardana", "Gede Artha", "Budi Santoso", "Sari Dewi"]:
    RATIFICATION_RECORDS.append({
        "agreement_id": AG_TH_CULTURE,
        "participant": name,
        "role": "member",
        "position": "consent",
        "date": date(2024, 11, 1),
    })

# AE Culture Code — ratified by AE members
for name in ["Lani Wijaya", "Dewa Putra", "Indra Gunawan"]:
    RATIFICATION_RECORDS.append({
        "agreement_id": AG_AE_CULTURE,
        "participant": name,
        "role": "member",
        "position": "consent",
        "date": date(2024, 11, 1),
    })

# ── Amendment Records ──────────────────────────────────────────────
# SHUR Access was amended from v1.0 to v1.1 (added quiet hours)

AMENDMENT_RECORDS: list[dict] = [
    {
        "id": uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430d1"),
        "ecosystem_id": ECOSYSTEM_ID,
        "amendment_id": "AM-001",
        "parent_agreement_id": AG_SHUR_ACCESS,
        "parent_agreement_version": "1.0",
        "amendment_type": "modification",
        "proposed_by": "Gede Artha",
        "date": date(2025, 2, 15),
        "changes": {
            "added": ["Quiet hours 22:00-06:00 (clause 5)"],
            "modified": ["Overnight booking notice reduced from 72h to 48h (clause 2)"],
        },
        "rationale": (
            "After 5 months of operation, overnight guests reported inconsistent "
            "experiences with late-night noise.  The quiet hours clause was added "
            "in response to three separate TH assembly discussions.  The booking "
            "notice reduction reflects actual usage patterns — 48 hours proved "
            "sufficient for coordinator response."
        ),
        "act_level_used": "GAIA-3",
        "consent_record_id": None,  # linked in run.py
        "new_agreement_version": "1.1",
        "status": "ratified",
    },
]

# ── Review Records ─────────────────────────────────────────────────

REVIEW_RECORDS: list[dict] = [
    {
        "id": uuid.UUID("7ba7b810-9dad-11d1-80b4-00c04fd430e1"),
        "ecosystem_id": ECOSYSTEM_ID,
        "review_id": "REV-001",
        "agreement_id": AG_SHUR_ACCESS,
        "agreement_version": "1.1",
        "review_type": "scheduled",
        "trigger": "Annual review cycle",
        "review_body": {
            "reviewers": ["Lani Wijaya", "Gede Artha", "Kai Nakamura"],
            "methodology": "Inspection of access logs, user survey (n=15), steward interview",
        },
        "date": date(2025, 9, 15),
        "evaluation": {
            "compliance": "high — 92% of bookings followed procedure",
            "conflicts": "2 minor access disputes resolved at Tier 1",
            "recommendations": [
                "Consider adding workshop cleanup checklist",
                "Review booking system for mobile accessibility",
            ],
        },
        "outcome": "renewed_with_modifications",
        "next_review_date": date(2026, 9, 1),
        "follow_up_actions": {
            "cleanup_checklist": "Assigned to Gede Artha, due 2025-10-15",
        },
    },
]
