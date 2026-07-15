"""
Conflict cases at each triage tier (1-4), one with a repair agreement.

  - Tier 1: Direct Dialogue — noise complaint resolved by direct conversation
  - Tier 2: Coaching Intervention — repeated SHUR access violation
  - Tier 3: Harm Circle — agreement breach with repair agreement signed
  - Tier 4: Community Impact Assessment — cross-ETHOS resource dispute
"""

from __future__ import annotations

import uuid
from datetime import date

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

# ── Conflict IDs ───────────────────────────────────────────────────

CC_TIER1 = uuid.UUID("aba7b810-9dad-11d1-80b4-00c04fd430a1")
CC_TIER2 = uuid.UUID("aba7b810-9dad-11d1-80b4-00c04fd430a2")
CC_TIER3 = uuid.UUID("aba7b810-9dad-11d1-80b4-00c04fd430a3")
CC_TIER4 = uuid.UUID("aba7b810-9dad-11d1-80b4-00c04fd430a4")

REPAIR_AG_TIER3 = uuid.UUID("aba7b810-9dad-11d1-80b4-00c04fd430b3")

# ── Conflict Cases ─────────────────────────────────────────────────

CONFLICT_CASES: list[dict] = [
    # Tier 1: Noise complaint — resolved by direct dialogue
    {
        "id": CC_TIER1,
        "ecosystem_id": ECOSYSTEM_ID,
        "case_id": "CC-005",
        "title": "Late-night workshop noise at West SHUR",
        "description": (
            "On three consecutive nights in January 2025, a bamboo-working "
            "workshop at West SHUR ran past quiet hours (22:00-06:00, per "
            "SHUR Access Rules v1.1 clause 5).  The noise disturbed three "
            "overnight guests.  One guest (Budi Santoso) reported the issue "
            "to TH assembly."
        ),
        "reporter_id": None,  # set in run.py → Budi Santoso
        "status": "resolved",
        "severity": "low",
        "scope": "individual",
        "tier": 1,
        "root_cause_category": "communication_gap",
        "urgency": "low",
        "safety_flag": False,
        "parties": {
            "reporter": "Budi Santoso",
            "reported": "Gede Artha",
            "affected": ["Overnight guests (3)"],
        },
        "facilitator_id": None,  # Kai Nakamura — set in run.py
        "domain": "Applied Ecology ETHOS",
        "triage_notes": (
            "Kai's assessment: severity=low (noise, not harm), scope=individual "
            "(affected specific guests on specific nights), root_cause=communication "
            "(workshop leader unaware of quiet hours), safety_flag=false.  "
            "Routing: Tier 1 — direct dialogue sufficient.  No power imbalance "
            "(Gede and Budi are peers).  Recommendation: Gede and Budi discuss "
            "directly.  Gede to add quiet-hours reminder to workshop opening "
            "briefing."
        ),
        "resolution_summary": (
            "Gede and Budi met for coffee.  Gede apologized — he had genuinely "
            "forgotten the quiet-hours clause was added in the v1.1 amendment "
            "(he was used to the original access rules).  Gede added a 30-minute "
            "'wrap-up warning' to all workshops starting at 21:30.  Budi accepted.  "
            "No further incidents in the 12 months since."
        ),
        "resolved_date": date(2025, 2, 1),
    },

    # Tier 2: Coaching Intervention — repeated access violation
    {
        "id": CC_TIER2,
        "ecosystem_id": ECOSYSTEM_ID,
        "case_id": "CC-004",
        "title": "Repeated overnight booking violations at East SHUR",
        "description": (
            "An AE member (identity withheld per coaching confidentiality) "
            "booked overnight stays at East SHUR 4 times without the 48-hour "
            "advance notice required by SHUR Access Rules clause 2.  The member "
            "is a long-time community participant who treats the SHUR as "
            "'their space'.  The SHUR access steward reported the pattern "
            "after the 4th violation."
        ),
        "reporter_id": None,  # set in run.py → Lani Wijaya
        "status": "resolved",
        "severity": "medium",
        "scope": "individual",
        "tier": 2,
        "root_cause_category": "skill_gap",
        "urgency": "medium",
        "safety_flag": False,
        "parties": {
            "reporter": "Lani Wijaya (SHUR access steward)",
            "reported": "[withheld — coaching confidentiality]",
            "affected": ["SHUR guests who had bookings affected"],
        },
        "facilitator_id": None,  # Kai Nakamura
        "domain": "Applied Ecology ETHOS",
        "triage_notes": (
            "Kai's triage: severity=medium (4 violations shows pattern, but no "
            "harm to persons or property), scope=individual (one person's "
            "behavior), root_cause=skill_gap (the member does not understand "
            "why advance booking matters — they see it as bureaucratic, not "
            "as structural fairness).  Routing: Tier 2 — coaching intervention.  "
            "Not a harm circle because there is no intentional breach and the "
            "affected parties' harm is inconvenience, not injury."
        ),
        "resolution_summary": (
            "Kai conducted a 3-session coaching intervention.  Session 1: explored "
            "the member's perspective ('the SHUR feels like home, booking feels "
            "unnatural').  Session 2: reframed the booking system as structural "
            "fairness — it ensures that the family visiting from Java gets a bed "
            "even if they are less assertive.  Session 3: co-created a 'SHUR "
            "belonging without bypassing' practice.  No violations in the 8 "
            "months since."
        ),
        "resolved_date": date(2025, 4, 15),
    },

    # Tier 3: Harm Circle — agreement breach with repair agreement
    {
        "id": CC_TIER3,
        "ecosystem_id": ECOSYSTEM_ID,
        "case_id": "CC-003",
        "title": "Seed library contribution misused",
        "description": (
            "In October 2024, an AE member contributed 5 heirloom seed varieties "
            "to the community seed-sharing network (pre-dated the formal seed "
            "library proposal).  Another member took seeds for personal commercial "
            "nursery use, repackaged them under their own brand, and sold them at "
            "the Ubud organic market without attribution or returning seeds to the "
            "community.  The contributor discovered this when a friend recognized "
            "the rare varieties at the market stall."
        ),
        "reporter_id": None,  # set in run.py
        "status": "resolved",
        "severity": "high",
        "scope": "circle",
        "tier": 3,
        "root_cause_category": "agreement_breach",
        "urgency": "high",
        "safety_flag": False,
        "parties": {
            "reporter": "[contributor — name withheld per harm circle protocol]",
            "reported": "[name withheld]",
            "affected": ["Seed-sharing community", "Local organic farmers"],
        },
        "facilitator_id": None,  # Kai Nakamura
        "domain": "Town Hall ETHOS",
        "triage_notes": (
            "Kai's triage: severity=high (breach of trust in a commons system "
            "is structurally damaging — it undermines the willingness to share "
            "that the entire seed network depends on), scope=circle (affected the "
            "TH community's seed-sharing trust, with ripple effects at the market), "
            "root_cause=agreement_breach (the implicit agreement of seed-sharing "
            "is 'you may use freely but you must share back').  Routing: Tier 3 "
            "— harm circle.  Power dynamic note: the reported party has slightly "
            "higher economic status than the reporter — triage notes this."
        ),
        "resolution_summary": (
            "Harm circle convened 2024-11-10 with Kai facilitating.  The reported "
            "party acknowledged they did not understand the implicit agreement of "
            "seed-sharing and treated the seeds as a gift with no strings.  The "
            "reporter expressed hurt that their contribution was commercialized "
            "without consent.  After 3 sessions, a repair agreement was signed "
            "(see RA-001).  The resolution: (a) the reported party donated 50% "
            "of the market proceeds to the seed library fund; (b) all remaining "
            "seed stock returned to the community; (c) the reported party "
            "co-facilitated a seed-saving workshop to share their propagation "
            "skills; (d) the incident directly motivated the formal seed library "
            "proposal (PROP-004)."
        ),
        "resolved_date": date(2024, 12, 15),
    },

    # Tier 4: Community Impact Assessment — cross-ETHOS resource dispute
    {
        "id": CC_TIER4,
        "ecosystem_id": ECOSYSTEM_ID,
        "case_id": "CC-002",
        "title": "TH vs AE resource allocation values conflict",
        "description": (
            "A recurring tension between TH and AE ETHOS over resource pool "
            "priorities: AE favors land stewardship investments (water "
            "infrastructure, soil regeneration, permaculture expansion), while "
            "TH favors community infrastructure (gathering spaces, ceremonial "
            "facilities, digital tools).  The tension surfaced in three "
            "consecutive participatory allocation sessions where each ETHOS "
            "consistently ranked its own priorities as 'urgent' and the other "
            "ETHOS's as 'non-essential'.  This is not a personal conflict but "
            "a structural values difference affecting the entire ecosystem."
        ),
        "reporter_id": None,  # Ayu Pertiwi as inter-ETHOS liaison
        "status": "resolved",
        "severity": "medium",
        "scope": "ecosystem",
        "tier": 4,
        "root_cause_category": "structural_deficiency",
        "urgency": "medium",
        "safety_flag": False,
        "parties": {
            "reporter": "Ayu Pertiwi (inter-ETHOS liaison)",
            "units": ["TH ETHOS", "AE ETHOS"],
            "affected": ["All ecosystem participants"],
        },
        "facilitator_id": None,  # Kai Nakamura
        "domain": "OmniOne Ecosystem",
        "triage_notes": (
            "Kai's triage: severity=medium (not yet acute harm, but pattern is "
            "escalating), scope=ecosystem (affects the structural relationship "
            "between both ETHOS), root_cause=structural_deficiency (the "
            "participatory allocation process does not have a mechanism for "
            "resolving cross-ETHOS priority conflicts).  Routing: Tier 4 — "
            "community impact assessment.  This is not a harm circle because "
            "there is no individual harm — the community needs to assess the "
            "structural gap."
        ),
        "resolution_summary": (
            "Community impact assessment conducted January 2025 with both ETHOS "
            "assemblies.  Findings: (a) the allocation process lacks a shared "
            "values framework to adjudicate cross-ETHOS priorities; (b) each "
            "ETHOS is rationally advocating for its own domain but the process "
            "has no 'ecosystem lens'; (c) the absence of a cross-ETHOS decision "
            "protocol (which later became PROP-001, now GAIA-stalled) is the "
            "root structural gap.  Interim resolution: a joint allocation "
            "framework was adopted for 2025: 40% AE stewardship, 40% TH community, "
            "20% OSC discretionary for cross-ETHOS initiatives.  The long-term "
            "solution (PROP-001) is pending resolution of Putu's remaining "
            "objection."
        ),
        "resolved_date": date(2025, 2, 28),
    },
]


# ── Repair Agreement (Tier 3) ──────────────────────────────────────

REPAIR_AGREEMENTS: list[dict] = [
    {
        "id": REPAIR_AG_TIER3,
        "conflict_case_id": CC_TIER3,
        "title": "Seed Library Repair Agreement — RA-001",
        "commitments": {
            "financial": {
                "action": "Donate 50% of market proceeds (1.2M IDR) to seed library fund",
                "deadline": "2024-12-31",
                "status": "completed",
            },
            "material": {
                "action": "Return all remaining seed stock to community seed network",
                "deadline": "2024-11-30",
                "status": "completed",
            },
            "skill_sharing": {
                "action": "Co-facilitate one seed-saving workshop within 3 months",
                "deadline": "2025-03-15",
                "status": "completed",
            },
        },
        "responsible_party": "[name withheld per repair agreement confidentiality]",
        "status": "completed",
        "checkin_30_date": date(2025, 1, 15),
        "checkin_30_notes": (
            "Financial commitment paid (1.2M IDR transferred to seed library fund).  "
            "Seed stock returned.  Workshop scheduled for 2025-02-20."
        ),
        "checkin_60_date": date(2025, 2, 15),
        "checkin_60_notes": (
            "Workshop held 2025-02-20 — 18 participants from both ETHOS.  "
            "Feedback positive.  Contributor reports feeling 'heard and respected.'"
        ),
        "checkin_90_date": date(2025, 3, 15),
        "checkin_90_notes": (
            "All commitments fulfilled.  No further incidents.  Contributor and "
            "reported party have re-established cooperative relationship.  "
            "Case closed with Kai's sign-off."
        ),
        "completed_date": date(2025, 3, 15),
    },
]
