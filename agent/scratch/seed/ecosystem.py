"""
OmniOne ecosystem + UAF Agreement + 2 ETHOS units.

Creates:
  - 1 ecosystem record (OmniOne)
  - 4 domains (OmniOne Ecosystem, TH ETHOS, AE ETHOS, OSC)
  - Domain elements and metrics for each
  - Circle memberships for key personas
"""

from __future__ import annotations

import uuid

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

# Domain IDs
DOMAIN_OMNIONE  = uuid.UUID("6ba7b820-9dad-11d1-80b4-00c04fd430c8")
DOMAIN_TH_ETHOS = uuid.UUID("6ba7b821-9dad-11d1-80b4-00c04fd430c8")
DOMAIN_AE_ETHOS = uuid.UUID("6ba7b822-9dad-11d1-80b4-00c04fd430c8")
DOMAIN_OSC      = uuid.UUID("6ba7b823-9dad-11d1-80b4-00c04fd430c8")

# ── Ecosystem record ──────────────────────────────────────────────

ECOSYSTEM = {
    "id": ECOSYSTEM_ID,
    "name": "OmniOne",
    "description": (
        "OmniOne is a non-sovereign coordination network stewarded by Green Earth "
        "Vision (GEV), operating out of Bali, Indonesia.  It is the first ecosystem "
        "running on the NEOS governance skill stack.  OmniOne's purpose is to coordinate "
        "resources, land stewardship, cultural preservation, and community governance "
        "across autonomous ETHOS units without centralized authority.  The ecosystem "
        "currently spans two ETHOS (Town Hall and Applied Ecology) and serves "
        "approximately 50 active participants across Bali."
    ),
    "uaf_agreement_id": None,  # Set after agreements seed runs
    "status": "active",
    "location": "Bali, Indonesia",
    "website": "https://omnione.org",
    "logo_url": None,
    "founded_date": "2024-06-15",
    "tags": {
        "sectors": ["regenerative agriculture", "cultural preservation", "community governance"],
        "scale": "local",
        "region": "southeast-asia",
        "languages": ["en", "id", "ban"],
    },
    "contact_email": "stewardship@omnione.org",
    "governance_summary": (
        "OmniOne operates under the NEOS governance skill stack (10 layers).  "
        "Decisions follow the ACT protocol (Advice, Consent, Test).  Authority is "
        "scoped and reviewable — no permanent sovereign power.  Economic coordination "
        "follows Ostrom's eight commons principles with a structural firewall between "
        "capital contribution and governance authority.  The ecosystem supports "
        "two ETHOS units (TH and AE) coordinated through the OmniOne Stewardship "
        "Council (OSC).  Exit is a structural right with portable governance records."
    ),
    "visibility": "public",
}

# ── Domains ─────────────────────────────────────────────────────────

DOMAINS: list[dict] = [
    {
        "id": DOMAIN_OMNIONE,
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": "D-OMNIONE-001",
        "version": "1.0",
        "status": "active",
        "purpose": (
            "The root domain for the OmniOne ecosystem.  Governs ecosystem-level "
            "agreements, resource pools, ACT decisions that cross ETHOS boundaries, "
            "and the Universal Agreement Field."
        ),
        "current_steward": "Manu Dewantara",
        "steward_id": None,  # set in run.py
        "parent_domain_id": None,
        "created_by": "Manu Dewantara",
        "metric_definitions": {
            "participant_count": "Active members in ecosystem",
            "agreement_coverage": "% of governance domains covered by active agreements",
            "proposal_velocity": "Proposals processed/month through ACT",
            "conflict_resolution_rate": "% conflicts resolved within 90 days",
        },
    },
    {
        "id": DOMAIN_TH_ETHOS,
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": "D-TH-ETHOS-001",
        "version": "1.0",
        "status": "active",
        "purpose": (
            "The Town Hall (TH) ETHOS — the civic participation and cultural governance "
            "unit.  TH handles community decisions, cultural preservation, local "
            "coordination, and the Culture Code.  TH members include builders, farmers, "
            "artisans, and community organizers."
        ),
        "current_steward": "Putu Ardana",
        "steward_id": None,
        "parent_domain_id": DOMAIN_OMNIONE,
        "created_by": "Manu Dewantara",
        "metric_definitions": {
            "townhall_attendance": "Average attendance at TH assemblies",
            "culture_code_reviews": "Culture Code review completions/year",
            "member_satisfaction": "Surveyed satisfaction score (1-5)",
        },
    },
    {
        "id": DOMAIN_AE_ETHOS,
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": "D-AE-ETHOS-001",
        "version": "1.0",
        "status": "active",
        "purpose": (
            "The Applied Ecology (AE) ETHOS — the land stewardship and regenerative "
            "agriculture unit.  AE manages SHUR facilities, coordinates permaculture "
            "projects, stewards shared land resources, and runs the resource pool."
        ),
        "current_steward": "Lani Wijaya",
        "steward_id": None,
        "parent_domain_id": DOMAIN_OMNIONE,
        "created_by": "Manu Dewantara",
        "metric_definitions": {
            "land_under_stewardship": "Hectares actively managed",
            "water_commons_health": "Water quality and availability index",
            "pool_utilization": "% of resource pool deployed",
        },
    },
    {
        "id": DOMAIN_OSC,
        "ecosystem_id": ECOSYSTEM_ID,
        "domain_id": "D-OSC-001",
        "version": "1.0",
        "status": "active",
        "purpose": (
            "The OmniOne Stewardship Council (OSC) — the cross-ETHOS coordination body.  "
            "The OSC ensures that TH and AE decisions do not conflict, facilitates "
            "cross-unit requests, and handles GAIA escalation for stalled proposals.  "
            "The OSC has coordination authority but not override authority — it cannot "
            "impose decisions on either ETHOS."
        ),
        "current_steward": "Ayu Pertiwi",
        "steward_id": None,
        "parent_domain_id": DOMAIN_OMNIONE,
        "created_by": "Manu Dewantara",
        "metric_definitions": {
            "cross_ethos_requests": "Cross-unit requests processed/month",
            "gaia_escalations": "GAIA escalations handled/quarter",
            "osc_consent_rate": "% OSC decisions passed by consent",
        },
    },
]

# ── Domain Elements (S3 eleven-element contract) ────────────────────

DOMAIN_ELEMENTS: list[dict] = []
for dom in DOMAINS:
    elements = [
        ("domain_description", {"text": dom["purpose"]}),
        ("primary_driver", {"text": dom["purpose"][:100]}),
        ("key_responsibilities", {
            "items": [
                "Maintain active agreements within domain",
                "Process ACT decisions for domain scope",
                "Report metrics per review schedule",
                "Coordinate with parent domain",
            ]
        }),
        ("key_deliverables", {
            "items": [
                "Quarterly domain review report",
                "Updated agreement registry entries",
                "Decision records for all ACT outcomes",
            ]
        }),
        ("competencies_required", {
            "items": ["Facilitation", "Domain expertise", "ACT process knowledge"]
        }),
        ("resources", {
            "items": ["Access to agreement registry", "Facilitation support from OSC"]
        }),
        ("constraints", {
            "items": [
                "Cannot override parent domain agreements",
                "Cannot change domain scope without ACT consent from parent",
                "Steward term limited to 12 months before review",
            ]
        }),
        ("evaluation_criteria", {
            "metrics": list(dom.get("metric_definitions", {}).keys())
        }),
    ]
    for name, value in elements:
        DOMAIN_ELEMENTS.append({
            "domain_id": dom["id"],
            "element_name": name,
            "element_value": value,
        })

# ── Domain Metrics ──────────────────────────────────────────────────

DOMAIN_METRICS: list[dict] = [
    {"domain_id": DOMAIN_OMNIONE, "metric": "participant_count",
     "target": ">=50 active", "measurement_method": "Count members with status=active"},
    {"domain_id": DOMAIN_OMNIONE, "metric": "agreement_coverage",
     "target": ">=90%", "measurement_method": "Review agreement registry against domain map"},
    {"domain_id": DOMAIN_OMNIONE, "metric": "proposal_velocity",
     "target": ">=4/month", "measurement_method": "Count proposals entering ACT advice per month"},
    {"domain_id": DOMAIN_OMNIONE, "metric": "conflict_resolution_rate",
     "target": ">=80% within 90 days", "measurement_method": "Audit conflict_cases resolved_date vs created_at"},

    {"domain_id": DOMAIN_TH_ETHOS, "metric": "townhall_attendance",
     "target": ">=60% of members", "measurement_method": "Attendance records from TH assemblies"},
    {"domain_id": DOMAIN_TH_ETHOS, "metric": "culture_code_reviews",
     "target": ">=1/year", "measurement_method": "Review record count for Culture Code agreement"},
    {"domain_id": DOMAIN_TH_ETHOS, "metric": "member_satisfaction",
     "target": ">=4.0 average", "measurement_method": "Quarterly survey 1-5 Likert scale"},

    {"domain_id": DOMAIN_AE_ETHOS, "metric": "land_under_stewardship",
     "target": ">=5 ha", "measurement_method": "GIS mapping of SHUR managed parcels"},
    {"domain_id": DOMAIN_AE_ETHOS, "metric": "water_commons_health",
     "target": "meets subak standards", "measurement_method": "Subak water quality protocol"},
    {"domain_id": DOMAIN_AE_ETHOS, "metric": "pool_utilization",
     "target": "60-80% deployed", "measurement_method": "Resource pool balance vs commitments"},

    {"domain_id": DOMAIN_OSC, "metric": "cross_ethos_requests",
     "target": "<5 pending at any time", "measurement_method": "Open cross-unit request count"},
    {"domain_id": DOMAIN_OSC, "metric": "gaia_escalations",
     "target": "<2/quarter", "measurement_method": "Count of GAIA Level 4+ escalations"},
    {"domain_id": DOMAIN_OSC, "metric": "osc_consent_rate",
     "target": ">=90%", "measurement_method": "Proportion of OSC decisions passing consent"},
]
