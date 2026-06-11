"""
Proposals in each ACT state, exercising the full proposal lifecycle.

ACT states covered:
  1. draft         — still being written
  2. advice        — advice window open, entries in progress
  3. consent       — consent phase with active integration round
  4. test          — in test phase with timer and success criteria
  5. ratified      — adopted and registered
  6. withdrawn     — withdrawn by proposer

One proposal is eligible for GAIA escalation (stalled at Level 3).

Every proposal has associated advice entries, consent records,
integration rounds, and test reports as appropriate for its state.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

TODAY = date.today()

# ── Proposal IDs ───────────────────────────────────────────────────

PROP_DRAFT       = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a1")
PROP_ADVICE_OPEN = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a2")
PROP_CONSENT     = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a3")
PROP_TESTING     = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a4")
PROP_RATIFIED    = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a5")
PROP_WITHDRAWN   = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a6")
PROP_GAIA_STALL  = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430a7")

# ── Proposals ──────────────────────────────────────────────────────

PROPOSALS: list[dict] = [
    # 1. DRAFT — Compost Toilet Initiative (still being written)
    {
        "id": PROP_DRAFT,
        "ecosystem_id": ECOSYSTEM_ID,
        "proposal_id": "PROP-007",
        "type": "resource_request",
        "decision_type": "solution",
        "title": "Compost Toilet Construction at East SHUR",
        "version": "1.0",
        "status": "draft",
        "proposer": "Budi Santoso",
        "co_sponsors": {"names": ["Gede Artha"]},
        "affected_domain": "Applied Ecology ETHOS",
        "impacted_parties": {
            "ethos": ["AE", "TH"],
            "specific": ["East SHUR residents", "maintenance crew"],
        },
        "urgency": "normal",
        "proposed_change": (
            "Construct two compost toilets at the East SHUR facility to replace "
            "the chemical toilets currently in use.  Budget: 15M IDR from the "
            "resource pool.  Construction by Gede Artha with volunteer labor."
        ),
        "rationale": (
            "The current chemical toilets at East SHUR require monthly chemical "
            "refills (200k IDR/month) and produce waste that must be transported "
            "off-site.  Compost toilets produce usable compost for the permaculture "
            "garden and eliminate the ongoing chemical cost.  This aligns with AE's "
            "land-first principle."
        ),
        "created_date": TODAY - timedelta(days=3),
        "advice_deadline": None,
        "consent_deadline": None,
        "test_duration": "90 days",
        "related_proposals": None,
        "synergy_check": {
            "status": "no_conflicts",
            "related": [],
            "checked_date": str(TODAY - timedelta(days=3)),
        },
    },

    # 2. ADVICE OPEN — Water Commons Access Expansion
    {
        "id": PROP_ADVICE_OPEN,
        "ecosystem_id": ECOSYSTEM_ID,
        "proposal_id": "PROP-006",
        "type": "policy_change",
        "decision_type": "solution",
        "title": "Expand Subak Water Access to Kintamani Farmers",
        "version": "1.0",
        "status": "advice",
        "proposer": "Lani Wijaya",
        "co_sponsors": {"names": ["Budi Santoso"]},
        "affected_domain": "Applied Ecology ETHOS",
        "impacted_parties": {
            "ethos": ["AE"],
            "external": ["Kintamani farming community"],
        },
        "urgency": "normal",
        "proposed_change": (
            "Extend OmniOne's subak-aligned water sharing to include up to 10 "
            "smallholder farmers from the Kintamani highlands.  This requires a "
            "new diversion agreement with the local subak and a water-use "
            "monitoring protocol."
        ),
        "rationale": (
            "The Kintamani highlands experience 3-4 months of dry-season water "
            "shortage annually.  OmniOne's SHUR facilities sit within a subak "
            "that has surplus flow during these months.  Sharing water aligns "
            "with the UAF's pluralism principle and builds goodwill with the "
            "surrounding farming community."
        ),
        "created_date": TODAY - timedelta(days=21),
        "advice_deadline": TODAY + timedelta(days=7),
        "consent_deadline": TODAY + timedelta(days=21),
        "test_duration": "180 days (one growing season)",
        "related_proposals": None,
        "synergy_check": {
            "status": "clear",
            "related": [],
            "checked_date": str(TODAY - timedelta(days=21)),
        },
    },

    # 3. CONSENT with active integration round — Organic Certification Fund
    {
        "id": PROP_CONSENT,
        "ecosystem_id": ECOSYSTEM_ID,
        "proposal_id": "PROP-005",
        "type": "resource_request",
        "decision_type": "solution",
        "title": "Organic Certification Transition Fund",
        "version": "1.2",  # modified after advice
        "status": "consent",
        "proposer": "Budi Santoso",
        "co_sponsors": {"names": ["Lani Wijaya"]},
        "affected_domain": "Applied Ecology ETHOS",
        "impacted_parties": {
            "ethos": ["AE", "TH"],
            "specific": ["Kintamani member farmers"],
        },
        "urgency": "normal",
        "proposed_change": (
            "Allocate 25M IDR from the resource pool to support up to 5 smallholder "
            "farmers in transitioning to organic certification.  Funds cover "
            "certification fees, soil testing, and a 3-month transition income "
            "supplement.  Recipients must agree to share knowledge at quarterly "
            "AE knowledge-sharing sessions for 2 years."
        ),
        "rationale": (
            "Organic certification opens access to premium markets (30-50% price "
            "increase).  Smallholder farmers in Kintamani cannot afford the "
            "transition costs on their own.  This fund is structured as a "
            "repayable grant — recipients contribute 10% of their premium "
            "earnings back to the fund for 2 years.  Knowledge-sharing "
            "requirement multiplies the investment across the ecosystem."
        ),
        "created_date": TODAY - timedelta(days=60),
        "advice_deadline": TODAY - timedelta(days=40),
        "consent_deadline": TODAY + timedelta(days=7),
        "test_duration": "12 months",
        "related_proposals": {"complements": [str(PROP_RATIFIED)]},
        "synergy_check": {
            "status": "complements_existing",
            "related": [str(PROP_RATIFIED)],
            "checked_date": str(TODAY - timedelta(days=60)),
        },
    },

    # 4. TEST with timer — Seed Library Registration Protocol
    {
        "id": PROP_TESTING,
        "ecosystem_id": ECOSYSTEM_ID,
        "proposal_id": "PROP-004",
        "type": "policy_change",
        "decision_type": "solution",
        "title": "Seed Library Registration and Borrowing Protocol",
        "version": "1.1",
        "status": "test",
        "proposer": "Budi Santoso",
        "co_sponsors": {"names": ["Lani Wijaya", "Putu Ardana"]},
        "affected_domain": "Town Hall ETHOS",
        "impacted_parties": {
            "ethos": ["TH", "AE"],
        },
        "urgency": "normal",
        "proposed_change": (
            "Establish a community seed library managed by TH, with a "
            "registration and borrowing protocol: (a) all seeds registered "
            "with variety name, source, harvest date, and germination rate; "
            "(b) borrowing limit of 5 varieties per member per season; "
            "(c) return obligation of 2x seeds borrowed from the harvest; "
            "(d) seed-saving workshops offered quarterly."
        ),
        "rationale": (
            "OmniOne members currently share seeds informally but tracking is "
            "non-existent.  Several heirloom varieties from elder farmers are "
            "at risk of being lost.  A structured seed library preserves "
            "agrobiodiversity, reduces dependency on commercial seed suppliers, "
            "and builds intergenerational knowledge transfer."
        ),
        "created_date": TODAY - timedelta(days=120),
        "advice_deadline": TODAY - timedelta(days=100),
        "consent_deadline": TODAY - timedelta(days=80),
        "test_duration": "180 days",
        "related_proposals": None,
        "synergy_check": {
            "status": "clear",
            "related": [],
            "checked_date": str(TODAY - timedelta(days=120)),
        },
    },

    # 5. RATIFIED — Bamboo Construction Standards
    {
        "id": PROP_RATIFIED,
        "ecosystem_id": ECOSYSTEM_ID,
        "proposal_id": "PROP-003",
        "type": "policy_change",
        "decision_type": "solution",
        "title": "Bamboo Construction Standards for SHUR Facilities",
        "version": "1.0",
        "status": "ratified",
        "proposer": "Gede Artha",
        "co_sponsors": {"names": ["Dewa Putra"]},
        "affected_domain": "Applied Ecology ETHOS",
        "impacted_parties": {
            "ethos": ["AE"],
            "roles": ["builder"],
        },
        "urgency": "normal",
        "proposed_change": (
            "Adopt the following bamboo construction standards for all SHUR "
            "facilities: (1) bamboo must be harvested at the correct moon phase "
            "(dark moon, Sasih Kelima) for maximum pest resistance; (2) all "
            "structural joints must use pegged mortise-and-tenon, not nails; "
            "(3) roof pitch minimum 35° for tropical rainfall runoff; "
            "(4) foundation must elevate the lowest bamboo member at least 40 cm "
            "above ground level.  These standards are mandatory for new construction "
            "and recommended for retrofits."
        ),
        "rationale": (
            "Three previous SHUR builds used inconsistent methods.  Bamboo harvested "
            "at the wrong moon phase suffered powder-post beetle infestation within "
            "6 months.  Nailed joints loosened during the rainy season.  These "
            "standards codify Gede's 20+ years of bamboo engineering experience."
        ),
        "created_date": TODAY - timedelta(days=365),
        "advice_deadline": TODAY - timedelta(days=340),
        "consent_deadline": TODAY - timedelta(days=320),
        "test_duration": "90 days",
        "related_proposals": None,
        "synergy_check": {
            "status": "clear",
            "related": [],
            "checked_date": str(TODAY - timedelta(days=365)),
        },
    },

    # 6. WITHDRAWN — Solar Microgrid Proposal
    {
        "id": PROP_WITHDRAWN,
        "ecosystem_id": ECOSYSTEM_ID,
        "proposal_id": "PROP-002",
        "type": "resource_request",
        "decision_type": "solution",
        "title": "Solar Microgrid for All SHUR Facilities",
        "version": "1.0",
        "status": "withdrawn",
        "proposer": "Indra Gunawan",
        "co_sponsors": None,
        "affected_domain": "Applied Ecology ETHOS",
        "impacted_parties": {
            "ethos": ["AE"],
        },
        "urgency": "normal",
        "proposed_change": (
            "Install solar microgrids at all three SHUR facilities.  Budget: 150M IDR.  "
            "Panels sourced from a Jakarta supplier with 5-year warranty."
        ),
        "rationale": (
            "SHUR facilities rely on the Bali grid, which experiences 2-3 "
            "blackouts per month during rainy season.  Solar microgrids would "
            "provide energy independence and reduce the carbon footprint."
        ),
        "created_date": TODAY - timedelta(days=500),
        "advice_deadline": TODAY - timedelta(days=480),
        "consent_deadline": None,
        "test_duration": None,
        "related_proposals": None,
        "synergy_check": {
            "status": "clear",
            "related": [],
            "checked_date": str(TODAY - timedelta(days=500)),
        },
    },

    # 7. GAIA-STALLED — Cross-ETHOS Decision Protocol
    {
        "id": PROP_GAIA_STALL,
        "ecosystem_id": ECOSYSTEM_ID,
        "proposal_id": "PROP-001",
        "type": "policy_change",
        "decision_type": "solution",
        "title": "Cross-ETHOS Decision Coordination Protocol",
        "version": "1.3",
        "status": "consent",  # stuck in consent after 2 integration rounds
        "proposer": "Ayu Pertiwi",
        "co_sponsors": {"names": ["Manu Dewantara", "Kai Nakamura"]},
        "affected_domain": "OmniOne Stewardship Council",
        "impacted_parties": {
            "ethos": ["TH", "AE", "OSC"],
        },
        "urgency": "elevated",
        "proposed_change": (
            "Establish a formal protocol for decisions that affect both TH and AE: "
            "(1) joint advice phase with representatives from both ETHOS; "
            "(2) parallel consent in each ETHOS, with objections from either "
            "triggering a joint integration round; (3) OSC facilitates but does "
            "not decide — deadlocks escalate to GAIA Level 5 ecosystem-wide "
            "deliberation; (4) test-phase decisions apply in the ETHOS that "
            "consented, not forced on the objecting ETHOS."
        ),
        "rationale": (
            "Two recent proposals affecting both ETHOS (water access and seed "
            "library) revealed no formal cross-ETHOS protocol exists.  Ayu, as "
            "inter-ETHOS liaison, has been improvising coordination.  This "
            "protocol closes a structural gap identified by Kai during conflict "
            "triage pattern analysis."
        ),
        "created_date": TODAY - timedelta(days=90),
        "advice_deadline": TODAY - timedelta(days=70),
        "consent_deadline": TODAY - timedelta(days=14),
        "test_duration": "180 days",
        "related_proposals": {
            "addresses_gap_revealed_by": [str(PROP_ADVICE_OPEN), str(PROP_TESTING)],
        },
        "synergy_check": {
            "status": "no_conflicts",
            "related": [],
            "checked_date": str(TODAY - timedelta(days=90)),
        },
    },
]

# ── Advice Entries ─────────────────────────────────────────────────

ADVICE_ENTRIES: list[dict] = []

# Advice for Water Commons (PROP_ADVICE_OPEN)
_advice_log_water = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b2")
_advices_water: list[dict] = [
    {
        "advice_log_id": _advice_log_water,
        "advisor": "Budi Santoso",
        "role": "farmer",
        "date": TODAY - timedelta(days=10),
        "advice_text": (
            "The 10-farmer cap is reasonable but include a priority criterion: "
            "farmers who have already participated in OmniOne workshops should "
            "get first access.  This rewards engagement and reduces risk of "
            "water misuse by unknown parties."
        ),
        "integration_status": "integrated",
        "rationale": "Proposer added priority criterion to proposal text.",
    },
    {
        "advice_log_id": _advice_log_water,
        "advisor": "Manu Dewantara",
        "role": "ecosystem architect",
        "date": TODAY - timedelta(days=8),
        "advice_text": (
            "The diversion agreement must explicitly state that OmniOne's access "
            "is subordinate to the subak's internal allocation during drought.  "
            "This is both legally prudent and consistent with the UAF's pluralism "
            "principle — we do not impose on existing governance systems."
        ),
        "integration_status": "integrated",
        "rationale": "Added subordination clause.",
    },
    {
        "advice_log_id": _advice_log_water,
        "advisor": "Dewa Putra",
        "role": "emergency coordinator",
        "date": TODAY - timedelta(days=5),
        "advice_text": (
            "What happens during a drought emergency?  If we have a water-sharing "
            "agreement with external farmers when an emergency is declared, does "
            "the agreement suspend?  Need to add an emergency suspension clause."
        ),
        "integration_status": "pending",
        "rationale": None,
    },
]
for a in _advices_water:
    ADVICE_ENTRIES.append(a)

# Advice for Organic Cert Fund (PROP_CONSENT)
_advice_log_org = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b3")
_advices_org: list[dict] = [
    {
        "advice_log_id": _advice_log_org,
        "advisor": "Melati Kusuma",
        "role": "governance auditor",
        "date": TODAY - timedelta(days=45),
        "advice_text": (
            "The 10% payback over 2 years is generous — too generous.  If all 5 "
            "farmers succeed, the fund gets back ~5M IDR out of 25M.  Consider "
            "15% payback or 3-year term to improve fund sustainability."
        ),
        "integration_status": "integrated",
        "rationale": "Adjusted to 15% payback, 3 years.  Proposal now v1.2.",
    },
    {
        "advice_log_id": _advice_log_org,
        "advisor": "Putu Ardana",
        "role": "culture code steward",
        "date": TODAY - timedelta(days=42),
        "advice_text": (
            "Knowledge-sharing requirement is excellent but should include "
            "a provision for sharing in Balinese, not just English/Indonesian.  "
            "The farmers who need this most may not be comfortable presenting "
            "in English."
        ),
        "integration_status": "integrated",
        "rationale": "Added 'presentations may be in Balinese with interpretation.'",
    },
]
for a in _advices_org:
    ADVICE_ENTRIES.append(a)

# Advice for Seed Library (PROP_TESTING)
_advice_log_seed = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b4")
_advices_seed: list[dict] = [
    {
        "advice_log_id": _advice_log_seed,
        "advisor": "Putu Ardana",
        "role": "culture code steward",
        "date": TODAY - timedelta(days=95),
        "advice_text": (
            "Include a register of sacred seeds (padi bali, sacred rice varieties).  "
            "These should not be 'borrowed' in the conventional sense — they are "
            "held in trust, and their use should require TH assembly consent."
        ),
        "integration_status": "integrated",
        "rationale": "Added sacred seeds register and consent requirement.",
    },
]
for a in _advices_seed:
    ADVICE_ENTRIES.append(a)

# Advice for Bamboo Standards (PROP_RATIFIED)
_advice_log_bamboo = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b5")
_advices_bamboo: list[dict] = [
    {
        "advice_log_id": _advice_log_bamboo,
        "advisor": "Dewa Putra",
        "role": "emergency coordinator",
        "date": TODAY - timedelta(days=335),
        "advice_text": (
            "Good standards.  Confirm that the 40 cm elevation also provides "
            "adequate flood clearance for the 10-year flood level at each SHUR "
            "location.  The earthquake resilience is also critical — bamboo "
            "performs well but only if joinery is correct."
        ),
        "integration_status": "integrated",
        "rationale": "Added flood-level verification requirement per SHUR site.",
    },
]
for a in _advices_bamboo:
    ADVICE_ENTRIES.append(a)

# Advice for Solar Microgrid (withdrawn)
_advice_log_solar = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b6")
_advices_solar: list[dict] = [
    {
        "advice_log_id": _advice_log_solar,
        "advisor": "Lani Wijaya",
        "role": "resource steward",
        "date": TODAY - timedelta(days=475),
        "advice_text": (
            "150M IDR is 40% of the resource pool.  This is too concentrated "
            "for a single project.  Consider phasing: one SHUR at a time over "
            "3 budget cycles.  Also, what is the maintenance plan?  Solar panels "
            "degrade and inverters fail — the budget must include ongoing "
            "maintenance, not just installation."
        ),
        "integration_status": "not_integrated",
        "rationale": (
            "Proposer chose to withdraw rather than re-scope.  See withdrawal "
            "note: 'After advice, I agree the proposal is premature.  Will "
            "re-submit as a phased approach after the resource pool grows.'"
        ),
    },
]
for a in _advices_solar:
    ADVICE_ENTRIES.append(a)

# Advice for Cross-ETHOS Protocol (GAIA-stalled)
_advice_log_gaia = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430b7")
_advices_gaia: list[dict] = [
    {
        "advice_log_id": _advice_log_gaia,
        "advisor": "Lani Wijaya",
        "role": "resource steward",
        "date": TODAY - timedelta(days=65),
        "advice_text": (
            "The parallel consent model is interesting but what happens when AE "
            "consents and TH objects?  The proposal says 'test applies in AE only' "
            "— but what if the decision inherently requires both ETHOS to function?  "
            "Example: a shared resource commitment.  The protocol needs a joint "
            "implementation tier, not just parallel consent."
        ),
        "integration_status": "partially_integrated",
        "rationale": "Proposer added joint implementation tier but AE objects to wording.",
    },
    {
        "advice_log_id": _advice_log_gaia,
        "advisor": "Putu Ardana",
        "role": "culture code steward",
        "date": TODAY - timedelta(days=60),
        "advice_text": (
            "TH supports this protocol.  However, the GAIA Level 5 escalation "
            "to 'ecosystem-wide deliberation' is undefined — what does that "
            "actually look like?  Who facilitates?  How long does it take?  "
            "This needs to be specified or it will become the place proposals "
            "go to die."
        ),
        "integration_status": "not_integrated",
        "rationale": "Disagreement on GAIA Level 5 mechanics — unresolved.",
    },
]
for a in _advices_gaia:
    ADVICE_ENTRIES.append(a)

# ── Non-respondents (Water Commons) ────────────────────────────────

ADVICE_NON_RESPONDENTS: list[dict] = [
    {
        "id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430c1"),
        "advice_log_id": _advice_log_water,
        "name": "Ketut Arsana",
        "notified_date": TODAY - timedelta(days=12),
        "follow_up_sent": True,
    },
]

# ── Consent Records ─────────────────────────────────────────────────

CONSENT_RECORDS: list[dict] = []

# Consent for Organic Cert Fund (PROP_CONSENT — active integration round)
_crec_org = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430d3")
CONSENT_RECORDS.append({
    "id": _crec_org,
    "proposal_id": PROP_CONSENT,
    "consent_mode": "consent",
    "weighting_model": "one_person_one_objection",
    "facilitator": "Sari Dewi",
    "date": TODAY - timedelta(days=14),
    "quorum_required": ">=60% of AE ETHOS + TH representatives",
    "quorum_met": True,
    "outcome": "in_progress",
    "escalation_level": None,
    "final_proposal_version": "1.2",
})

# Consent for Seed Library (PROP_TESTING)
_crec_seed = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430d4")
CONSENT_RECORDS.append({
    "id": _crec_seed,
    "proposal_id": PROP_TESTING,
    "consent_mode": "consent",
    "weighting_model": "one_person_one_objection",
    "facilitator": "Sari Dewi",
    "date": TODAY - timedelta(days=80),
    "quorum_required": ">=60% of TH ETHOS",
    "quorum_met": True,
    "outcome": "consented",
    "escalation_level": None,
    "final_proposal_version": "1.1",
})

# Consent for Bamboo Standards (PROP_RATIFIED)
_crec_bamboo = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430d5")
CONSENT_RECORDS.append({
    "id": _crec_bamboo,
    "proposal_id": PROP_RATIFIED,
    "consent_mode": "consent",
    "weighting_model": "one_person_one_objection",
    "facilitator": "Sari Dewi",
    "date": TODAY - timedelta(days=320),
    "quorum_required": ">=60% of AE ETHOS",
    "quorum_met": True,
    "outcome": "consented",
    "escalation_level": None,
    "final_proposal_version": "1.0",
})

# Consent for Cross-ETHOS Protocol (GAIA-stalled)
_crec_gaia = uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430d7")
CONSENT_RECORDS.append({
    "id": _crec_gaia,
    "proposal_id": PROP_GAIA_STALL,
    "consent_mode": "consent",
    "weighting_model": "one_person_one_objection",
    "facilitator": "Kai Nakamura",
    "date": TODAY - timedelta(days=14),
    "quorum_required": ">=60% of both TH and AE ETHOS + OSC all",
    "quorum_met": False,
    "outcome": "stalled",
    "escalation_level": "GAIA-3",
    "final_proposal_version": None,
})

# ── Consent Participants ────────────────────────────────────────────

CONSENT_PARTICIPANTS: list[dict] = [
    # Organic Cert Fund — consent in progress
    {"consent_record_id": _crec_org, "name": "Lani Wijaya", "role": "resource steward",
     "ethos": "AE", "position": "consent", "reason": None, "round": 1},
    {"consent_record_id": _crec_org, "name": "Dewa Putra", "role": "emergency coordinator",
     "ethos": "AE", "position": "objection", "reason": (
        "The fund requires recipients to share knowledge quarterly.  What if a "
        "recipient's farm is in crisis — drought, pest outbreak — and they cannot "
        "fulfill this?  Add a force majeure clause for agricultural emergencies."
    ), "round": 1},
    {"consent_record_id": _crec_org, "name": "Putu Ardana", "role": "TH steward",
     "ethos": "TH", "position": "consent", "reason": None, "round": 1},

    # Seed Library — consented
    {"consent_record_id": _crec_seed, "name": "Putu Ardana", "role": "TH steward",
     "ethos": "TH", "position": "consent", "reason": None, "round": 1},
    {"consent_record_id": _crec_seed, "name": "Budi Santoso", "role": "proposer",
     "ethos": "TH", "position": "consent", "reason": None, "round": 1},
    {"consent_record_id": _crec_seed, "name": "Gede Artha", "role": "builder",
     "ethos": "TH", "position": "consent", "reason": None, "round": 1},

    # Bamboo Standards — consented
    {"consent_record_id": _crec_bamboo, "name": "Lani Wijaya", "role": "AE steward",
     "ethos": "AE", "position": "consent", "reason": None, "round": 1},
    {"consent_record_id": _crec_bamboo, "name": "Dewa Putra", "role": "emergency coordinator",
     "ethos": "AE", "position": "consent", "reason": None, "round": 1},
    {"consent_record_id": _crec_bamboo, "name": "Gede Artha", "role": "proposer",
     "ethos": "AE", "position": "consent", "reason": None, "round": 1},

    # Cross-ETHOS Protocol — stalled (both ETHOS have objectors)
    {"consent_record_id": _crec_gaia, "name": "Ayu Pertiwi", "role": "proposer / OSC liaison",
     "ethos": "OSC", "position": "consent", "reason": None, "round": 1},
    {"consent_record_id": _crec_gaia, "name": "Lani Wijaya", "role": "AE steward",
     "ethos": "AE", "position": "objection", "reason": (
        "Joint implementation tier is underspecified.  The protocol says "
        "'coordinate' but doesn't define budget authority — if a joint "
        "decision requires pooled resources, who disburses?  AE controls "
        "the resource pool but should not have unilateral disbursement "
        "authority for joint decisions."
    ), "round": 1},
    {"consent_record_id": _crec_gaia, "name": "Putu Ardana", "role": "TH steward",
     "ethos": "TH", "position": "objection", "reason": (
        "GAIA Level 5 is undefined.  'Ecosystem-wide deliberation' could "
        "mean anything from a 2-hour workshop to a 3-month process.  TH "
        "needs a defined timeline and facilitation protocol before consenting."
    ), "round": 1},
    {"consent_record_id": _crec_gaia, "name": "Manu Dewantara", "role": "ecosystem architect",
     "ethos": "OSC", "position": "consent", "reason": None, "round": 1},
    {"consent_record_id": _crec_gaia, "name": "Kai Nakamura", "role": "facilitator",
     "ethos": "OSC", "position": "consent", "reason": None, "round": 1},
]

# ── Integration Rounds ─────────────────────────────────────────────

INTEGRATION_ROUNDS: list[dict] = [
    # Organic Cert Fund — Round 1: one objection (Dewa)
    {
        "id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430e3"),
        "consent_record_id": _crec_org,
        "round_number": 1,
        "modifications_made": (
            "Added force majeure clause: knowledge-sharing obligation is suspended "
            "if the recipient's farm is under a declared emergency (drought, pest "
            "outbreak, flood).  Abeyance period: until emergency is resolved + 30 "
            "days grace.  Accumulated obligations are not waived — they are deferred."
        ),
        "outcome": "objection_resolved",
    },
    # Cross-ETHOS Protocol — Round 1: two objections unresolved
    {
        "id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430e7a"),
        "consent_record_id": _crec_gaia,
        "round_number": 1,
        "modifications_made": (
            "Added joint budget authority clause: for cross-ETHOS decisions "
            "requiring resource pool funds, a joint TH-AE-OSC sub-circle reviews "
            "the disbursement within 7 days.  If no consensus, the request "
            "escalates to OSC facilitation with no unilateral AE authority."
        ),
        "outcome": "partial",
    },
    # Cross-ETHOS Protocol — Round 2: Lani's objection resolved, Putu's remains
    {
        "id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430e7b"),
        "consent_record_id": _crec_gaia,
        "round_number": 2,
        "modifications_made": (
            "Refined GAIA Level 5 definition: ecosystem-wide deliberation is "
            "a facilitated 2-day assembly (max) with representatives from each "
            "ETHOS and OSC.  If no resolution after 2 days, the proposal is "
            "archived and a new proposal must be submitted addressing the "
            "identified deadlock."
        ),
        "outcome": "partial",  # Putu still objects — wants 3-day max + external facilitator
    },
]

# ── Objections Addressed ────────────────────────────────────────────

OBJECTIONS_ADDRESSED: list[dict] = [
    # Organic Cert Fund — Dewa's objection resolved
    {
        "integration_round_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430e3"),
        "objector": "Dewa Putra",
        "objection": (
            "No force majeure clause for agricultural emergencies affecting "
            "knowledge-sharing obligation."
        ),
        "resolution": (
            "Force majeure clause added.  Knowledge-sharing obligation suspended "
            "during declared emergencies with deferred (not waived) obligations.  "
            "Dewa confirmed resolution satisfactory."
        ),
    },
    # Cross-ETHOS Round 1 — Lani's objection partially resolved
    {
        "integration_round_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430e7a"),
        "objector": "Lani Wijaya",
        "objection": (
            "Joint implementation tier underspecified — no budget authority "
            "definition for cross-ETHOS resource decisions."
        ),
        "resolution": (
            "Joint sub-circle review added with 7-day timeline.  Lani confirmed "
            "resolution in Round 2."
        ),
    },
    # Cross-ETHOS Round 2 — Putu's objection still open
    {
        "integration_round_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430e7b"),
        "objector": "Putu Ardana",
        "objection": (
            "GAIA Level 5 definition: 2-day assembly is insufficient.  TH "
            "requests 3-day minimum with external facilitator option."
        ),
        "resolution": None,  # Unresolved — GAIA escalation eligible
    },
]

# ── Test Reports ────────────────────────────────────────────────────

TEST_REPORTS: list[dict] = [
    # Seed Library test is active
    {
        "id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f4"),
        "proposal_id": PROP_TESTING,
        "test_start_date": TODAY - timedelta(days=60),
        "test_end_date": TODAY + timedelta(days=120),
        "midpoint_checkin_date": TODAY,
        "revert_procedure": (
            "Return all borrowed seeds to their original depositors.  "
            "Transfer seed library inventory list to TH assembly for "
            "informal continuation.  Remove registration requirement."
        ),
        "observations": (
            "15 seed varieties registered.  8 members have borrowed seeds.  "
            "One variety (black rice, Cendana) had low germination rate (40%) "
            "— flagged for seed-saving workshop.  Positive response from elder "
            "farmers who contributed heirloom varieties."
        ),
        "midpoint_findings": (
            "Registration process works but the paper form is a bottleneck.  "
            "Indra has volunteered to build a digital registry.  Borrowing "
            "protocol followed in all cases.  No disputes."
        ),
        "outcome": None,
        "extension_end_date": None,
        "modifications": None,
        "next_action": "Continue test phase.  Add digital registration option in month 4.",
        "agreement_registry_id": None,  # Not yet registered — still testing
        "success_criteria_summary": (
            "3 of 4 success criteria met at midpoint.  Criterion 2 (80% germination "
            "rate across all borrowed seeds) not yet evaluable — need harvest data."
        ),
        "reviewer_notes": "Promising.  Check germination criterion at test end.",
    },
    # Bamboo Standards test completed and ratified
    {
        "id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f5"),
        "proposal_id": PROP_RATIFIED,
        "test_start_date": TODAY - timedelta(days=300),
        "test_end_date": TODAY - timedelta(days=210),
        "midpoint_checkin_date": TODAY - timedelta(days=255),
        "revert_procedure": (
            "Building constructed under test standards remains.  Future "
            "builds revert to pre-standard ad hoc methods."
        ),
        "observations": (
            "West SHUR pergola built to standards during test.  Bamboo harvested "
            "at correct moon phase showed zero beetle infestation at 6-month "
            "inspection.  Mortise-and-tenon joints remained tight through full "
            "rainy season.  40 cm elevation adequate for observed flooding."
        ),
        "midpoint_findings": "Construction progressing on schedule.  No issues.",
        "outcome": "ratified",
        "extension_end_date": None,
        "modifications": None,
        "next_action": (
            "Register bamboo standards as mandatory for new AE construction.  "
            "Add to builder onboarding materials."
        ),
        "agreement_registry_id": "AG-ACC-002",
        "success_criteria_summary": "All 3 success criteria met.",
        "reviewer_notes": (
            "Standards performed well.  Gede's 20+ years of experience validated "
            "in controlled test."
        ),
    },
]

# ── Test Success Criteria ───────────────────────────────────────────

TEST_SUCCESS_CRITERIA: list[dict] = [
    # Seed Library test criteria
    {"test_report_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f4"),
     "criterion": "At least 10 seed varieties registered within 60 days", "met": True,
     "evidence": "15 varieties registered as of day 55."},
    {"test_report_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f4"),
     "criterion": "At least 80% germination rate across all borrowed seeds at harvest", "met": False,
     "evidence": None},
    {"test_report_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f4"),
     "criterion": "No disputes or reported misuse of borrowed seeds", "met": True,
     "evidence": "Zero conflict cases filed related to seed library."},
    {"test_report_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f4"),
     "criterion": "At least 5 members borrow seeds during test period", "met": True,
     "evidence": "8 unique borrowers as of midpoint."},

    # Bamboo Standards test criteria
    {"test_report_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f5"),
     "criterion": "No structural joint failure during rainy season", "met": True,
     "evidence": "All joints inspected after 3 months of heavy rain — no loosening."},
    {"test_report_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f5"),
     "criterion": "No pest infestation within 6 months of construction", "met": True,
     "evidence": "Bi-monthly inspections — zero powder-post beetle activity."},
    {"test_report_id": uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f5"),
     "criterion": "Builder reports satisfaction with standards clarity", "met": True,
     "evidence": "Gede Artha: 'First time I didn't have to explain everything verbally.'"},
]
