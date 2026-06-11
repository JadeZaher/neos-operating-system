"""
Economic coordination data (Layer IV).

Seeds the minimal economic data that existing models support, with TODO
comments where models have not yet been built.

Currently implemented models:
  - shares_needs  (domain-level resource sharing/needs declarations)
  - collaborations (cross-domain collaboration agreements)

Models needed but not yet present in db/models.py:
  - TODO: funding_pools       — Pool governance with balances, inflow/outflow rules
  - TODO: resource_requests   — Formal resource requests through ACT
  - TODO: current_see_balances — Influence currency (111 Current-Sees per person)
  - TODO: pool_transactions   — Individual disbursements from funding pools
  - TODO: commons_indicators  — Ostrom commons monitoring indicators
"""

from __future__ import annotations

import uuid
from datetime import date

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

# Domain references from ecosystem.py
DOMAIN_OMNIONE  = uuid.UUID("6ba7b820-9dad-11d1-80b4-00c04fd430c8")
DOMAIN_TH_ETHOS = uuid.UUID("6ba7b821-9dad-11d1-80b4-00c04fd430c8")
DOMAIN_AE_ETHOS = uuid.UUID("6ba7b822-9dad-11d1-80b4-00c04fd430c8")
DOMAIN_OSC      = uuid.UUID("6ba7b823-9dad-11d1-80b4-00c04fd430c8")


# ── Funding Pool (narrative — no model yet) ────────────────────────
#
# TODO: When funding_pools table is added to models.py:
#
# FUNDING_POOL = {
#     "id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430a1"),
#     "ecosystem_id": ECOSYSTEM_ID,
#     "name": "OmniOne General Resource Pool",
#     "type": "ecosystem_strategic",
#     "governing_domain_id": DOMAIN_AE_ETHOS,
#     "steward_id": MEMBER_LANI,
#     "current_balance": 280_000_000,  # 280M IDR
#     "currency": "IDR",
#     "inflow_sources": {
#         "GEV_grant": {"amount": 250_000_000, "period": "annual"},
#         "community_contributions": {"amount": 30_000_000, "period": "annual"},
#         "workshop_fees": {"amount": 15_000_000, "period": "annual"},
#     },
#     "outflow_rules": {
#         "steward_discretionary": {"max_per_request": 14_000_000, "max_per_month": 28_000_000},
#         "circle_consent_required": {"min": 14_000_001},
#         "ecosystem_consent_required": {"min": 70_000_000},
#     },
#     "emergency_reserve_min_percent": 10,
#     "current_reserve": 28_000_000,
#     "status": "active",
#     "transparency_schedule": "monthly",
#     "review_date": date(2026, 6, 1),
# }
#
# Note: The review date is overdue per governance health audit GHA-001.


# ── Resource Request (narrative — no model yet) ────────────────────
#
# TODO: When resource_requests table is added to models.py:
#
# RESOURCE_REQUESTS = [
#     # Current request: Compost Toilet Construction (PROP-007, draft)
#     {
#         "id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430b1"),
#         "proposal_id": PROP_DRAFT,  # Compost Toilet
#         "pool_id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430a1"),
#         "amount": 15_000_000,  # 15M IDR
#         "type": "one_time",
#         "status": "draft",
#         "requested_by": "Budi Santoso",
#         "requested_date": TODAY - timedelta(days=3),
#     },
#     # Approved: Organic Certification Fund (PROP-005, in consent)
#     {
#         "id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430b2"),
#         "proposal_id": PROP_CONSENT,
#         "pool_id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430a1"),
#         "amount": 25_000_000,
#         "type": "revolving_fund",
#         "status": "pending_consent",
#         "requested_by": "Budi Santoso",
#         "requested_date": TODAY - timedelta(days=60),
#     },
#     # Completed: Emergency water procurement
#     {
#         "id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430b3"),
#         "proposal_id": None,
#         "pool_id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430a1"),
#         "amount": 3_000_000,
#         "type": "emergency",
#         "status": "disbursed",
#         "requested_by": "Lani Wijaya",
#         "requested_date": date(2025, 7, 2),
#         "approved_by": "Dewa Putra (emergency coordinator)",
#         "approved_date": date(2025, 7, 2),
#     },
# ]


# ── Current-See Balances (narrative — no model yet) ────────────────
#
# TODO: When current_see_balances table is added to models.py:
#
# Every OmniOne participant receives 111 Current-Sees on joining.
# Current-Sees express governance preferences but do not confer
# decision-making authority — decisions are made through ACT, not voting.
#
# CURRENT_SEE_BALANCES = {
#     "total_issued": 111 * 12,  # 12 active members = 1,332
#     "per_person": 111,
#     "used_in": "preference indication during advice phase",
#     "not_used_in": "consent decisions (ACT consent is not a vote)",
#     "note": (
#         "Current-Sees are influence currency, not governance currency.  "
#         "They answer the question 'how strongly do you feel about this?'  "
#         "not 'what should we decide?'  The decision is made through ACT "
#         "consent, not Current-See tallying."
#     ),
# }


# ── Shares & Needs (existing model — seed data) ────────────────────

SHARES_NEEDS: list[dict] = [
    # AE ETHOS shares
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_AE_ETHOS,
        "type": "share",
        "title": "Bamboo construction expertise",
        "description": (
            "AE can provide bamboo engineering and construction services "
            "from Gede Artha, with 20+ years of experience in traditional "
            "Balinese bamboo joinery."
        ),
        "category": "skill",
        "capacity": "available",
        "tags": {"skills": ["bamboo", "construction", "traditional knowledge"]},
        "visibility": "public",
        "status": "active",
    },
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_AE_ETHOS,
        "type": "share",
        "title": "Permaculture garden space and knowledge",
        "description": (
            "AE maintains 0.5 ha of permaculture demonstration garden with "
            "over 40 food plant species.  Available for workshops, research, "
            "and seed-sharing."
        ),
        "category": "knowledge",
        "capacity": "shared",
        "tags": {"skills": ["permaculture", "seed-saving", "food sovereignty"]},
        "visibility": "public",
        "status": "active",
    },
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_AE_ETHOS,
        "type": "need",
        "title": "Soil science expertise",
        "description": (
            "AE needs a soil scientist or agronomist for baseline soil health "
            "assessment at East SHUR.  The volcanic soil varies dramatically "
            "within 100 meters and current knowledge is anecdotal."
        ),
        "category": "knowledge",
        "capacity": None,
        "tags": {"skills": ["soil science", "agronomy", "volcanic soils"]},
        "visibility": "ecosystem",
        "status": "active",
    },
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_AE_ETHOS,
        "type": "need",
        "title": "Legal advisory for commons trusts",
        "description": (
            "AE needs legal expertise in Indonesian commons law to structure "
            "the subak water-sharing agreement and potential land trust.  "
            "Nirmala has environmental law background but needs a commons-law "
            "specialist."
        ),
        "category": "knowledge",
        "capacity": None,
        "tags": {"skills": ["commons law", "land trusts", "Indonesian legal system"]},
        "visibility": "ecosystem",
        "status": "active",
    },

    # TH ETHOS shares
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_TH_ETHOS,
        "type": "share",
        "title": "Conflict facilitation and mediation",
        "description": (
            "TH can provide conflict triage, NVC facilitation, and harm circle "
            "facilitation through Kai Nakamura and the triage pool.  Available "
            "to other ecosystems running NEOS."
        ),
        "category": "skill",
        "capacity": "available",
        "tags": {"skills": ["conflict resolution", "NVC", "restorative justice"]},
        "visibility": "public",
        "status": "active",
    },
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_TH_ETHOS,
        "type": "share",
        "title": "Governance facilitation and ACT process guidance",
        "description": (
            "TH can provide proposal stewardship and ACT facilitation through "
            "Sari Dewi.  Available to support other ecosystems in setting up "
            "their own ACT processes."
        ),
        "category": "skill",
        "capacity": "limited",
        "tags": {"skills": ["governance", "ACT protocol", "facilitation"]},
        "visibility": "public",
        "status": "active",
    },
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_TH_ETHOS,
        "type": "need",
        "title": "Graphic design for governance visualization",
        "description": (
            "TH needs a graphic designer to create visual explanations of the "
            "ACT process for non-English-speaking participants.  Current "
            "documentation is text-heavy and English-only."
        ),
        "category": "skill",
        "capacity": None,
        "tags": {"skills": ["graphic design", "visual communication", "information design"]},
        "visibility": "ecosystem",
        "status": "active",
    },

    # OSC shares
    {
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": DOMAIN_OSC,
        "type": "share",
        "title": "Cross-ecosystem NEOS architecture consultation",
        "description": (
            "OSC members (Manu, Ayu) can provide ecosystem architecture "
            "consultation for communities setting up NEOS.  Includes domain "
            "mapping, agreement hierarchy design, and stress-testing."
        ),
        "category": "knowledge",
        "capacity": "limited",
        "tags": {"skills": ["NEOS architecture", "ecosystem design", "governance stress-testing"]},
        "visibility": "public",
        "status": "active",
    },
]


# ── Collaborations (existing model — seed data) ────────────────────

COLLABORATIONS: list[dict] = [
    {
        "id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430c1"),
        "source_domain_id": DOMAIN_TH_ETHOS,
        "target_domain_id": DOMAIN_AE_ETHOS,
        "title": "Seed Library Cross-ETHOS Collaboration",
        "description": (
            "TH manages the seed library registration and community engagement.  "
            "AE provides the growing space, permaculture expertise, and seed-saving "
            "workshop facilitation.  This collaboration was formalized as part of "
            "the Seed Library Protocol test phase (PROP-004)."
        ),
        "status": "active",
        "engagement_tier": "cooperate",
        "terms": {
            "TH_responsibilities": [
                "Maintain seed registry and borrowing protocol",
                "Host quarterly seed-saving workshops",
                "Manage community engagement and outreach",
            ],
            "AE_responsibilities": [
                "Provide 0.5 ha permaculture garden for seed trials",
                "Supply propagation expertise",
                "Monitor germination rates for registered varieties",
            ],
            "shared": [
                "Joint quarterly review of seed library health",
                "Co-facilitate annual seed exchange event",
            ],
        },
        "linked_shares_needs": {
            "TH_share": "Governance facilitation and ACT process guidance",
            "AE_share": "Permaculture garden space and knowledge",
        },
        "started_date": date(2025, 3, 15),
        "review_date": date(2026, 3, 15),
    },
    {
        "id": uuid.UUID("eba7b810-9dad-11d1-80b4-00c04fd430c2"),
        "source_domain_id": DOMAIN_TH_ETHOS,
        "target_domain_id": DOMAIN_OSC,
        "title": "Governance Visualization Project",
        "description": (
            "TH and OSC are collaborating to create visual, multi-language "
            "explanations of the ACT process, agreement hierarchy, and "
            "conflict triage pathways.  This addresses TH's identified need "
            "for graphic design support and OSC's goal of governance accessibility."
        ),
        "status": "proposed",
        "engagement_tier": "cooperate",
        "terms": {
            "TH_provides": ["Content expertise on ACT process and triage pathways", "Language review (Indonesian and Balinese)"],
            "OSC_provides": ["Architecture validation of governance diagrams", "Coordination with Indra for digital implementation"],
            "shared": ["Identify a graphic designer (internal or contracted)"],
        },
        "linked_shares_needs": {
            "TH_need": "Graphic design for governance visualization",
            "OSC_share": "Cross-ecosystem NEOS architecture consultation",
        },
        "started_date": None,
        "review_date": date(2026, 1, 15),
    },
]


# ── Narrative-only economic data (commented — no models yet) ────────

ECONOMIC_NARRATIVE = """
Layer IV Economic Coordination — Current State (2025-12-01):

**Resource Pool.**
  - Total pool: ~380M IDR
  - GEV annual grant: 250M IDR (80% of inflows)
  - Community contributions: 30M IDR
  - Workshop fees: 15M IDR
  - Emergency reserve: 28M IDR (maintained above 10% minimum)
  - Largest single disbursement: 25M IDR (Organic Certification Fund, pending consent)
  - Emergency disbursement: 3M IDR (drought water procurement, 2025-07-02)
  - Steward discretionary limit: 5% of pool balance per request (currently ~19M IDR)

**Influence Currency (Current-Sees).**
  - 1,332 Current-Sees issued (111 × 12 active members)
  - Used during advice phases for preference indication
  - NOT used for consent decisions (ACT consent is qualitative, not quantitative)
  - TODO: current_see_balances model needed

**Commons Monitoring.**
  - Water commons: subak-aligned sharing with Kintamani expansion proposed (PROP-006)
  - Seed commons: formalized in seed library test phase (PROP-004)
  - Land commons: 5 ha under AE stewardship, soil assessment needed
  - TODO: commons_indicators model needed

**Structural Firewall.**
  - Capital contribution ≠ governance authority (verified by GHA-001 audit)
  - GEV grant agreement explicitly waives governance authority
  - No correlation between economic contribution and proposal pass-through rate
  - Single-source funding risk identified (80% GEV) — mitigation plan due 2026-03-01
"""
