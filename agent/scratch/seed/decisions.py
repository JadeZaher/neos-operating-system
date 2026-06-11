"""
Historical governance decisions with semantic tags, participants, and
dissent records.

Four decisions covering different layers:
  1. Decision to adopt bamboo standards (Layer III → Layer I registration)
  2. Decision to create the conflict triage pool (Layer VI)
  3. Decision on emergency criteria activation (Layer VIII)
  4. Decision on portable record format (Layer X)

Each demonstrates precedent-search capability and semantic tagging.
"""

from __future__ import annotations

import uuid
from datetime import date

ECOSYSTEM_ID = uuid.UUID("6ba7b819-9dad-11d1-80b4-00c04fd430c8")

# ── Decision IDs ───────────────────────────────────────────────────

DEC_BAMBOO       = uuid.UUID("9ba7b810-9dad-11d1-80b4-00c04fd430a1")
DEC_TRIAGE_POOL  = uuid.UUID("9ba7b810-9dad-11d1-80b4-00c04fd430a2")
DEC_EMERGENCY    = uuid.UUID("9ba7b810-9dad-11d1-80b4-00c04fd430a3")
DEC_PORTABLE     = uuid.UUID("9ba7b810-9dad-11d1-80b4-00c04fd430a4")

# ── Decisions ──────────────────────────────────────────────────────

DECISIONS: list[dict] = [
    # 1. Bamboo Standards Adoption
    {
        "id": DEC_BAMBOO,
        "ecosystem_id": ECOSYSTEM_ID,
        "record_id": "DEC-001",
        "date": date(2025, 6, 15),
        "holding": (
            "AE ETHOS consents to adopting the Bamboo Construction Standards "
            "(PROP-003) as mandatory for all new SHUR facility construction.  "
            "The test phase demonstrated that bamboo harvested at the correct "
            "moon phase with pegged mortise-and-tenon joinery eliminates pest "
            "infestation and structural failure common in previous builds."
        ),
        "ratio_decidendi": (
            "The decision was reached because: (a) empirical test results showed "
            "zero beetle infestation over 6 months; (b) structural joints survived "
            "full rainy season without loosening; (c) the standards codify "
            "generations of Balinese bamboo engineering knowledge that was being "
            "lost through informal transmission; (d) no participant raised a "
            "reasoned objection that the standards would harm the shared aim."
        ),
        "obiter_dicta": (
            "The OSC noted that these standards should be shared with other "
            "ETHOS and ecosystems building with bamboo.  This is not a binding "
            "obligation but a recommendation for cross-ecosystem knowledge transfer."
        ),
        "deliberation_summary": (
            "ACT process: proposal submitted by Gede Artha, advice gathered from "
            "AE and TH members (4 advisors), consent achieved in 1 round with "
            "all 3 AE participants consenting.  90-day test period at West SHUR.  "
            "Test report confirmed all 3 success criteria met.  Decision ratified "
            "by AE ETHOS consent on 2025-06-15."
        ),
        "source_skill": "proposal-creation",
        "source_layer": 3,
        "artifact_type": "proposal",
        "artifact_reference": "PROP-003",
        "domain": "Applied Ecology ETHOS",
        "precedent_level": "persuasive",
        "status": "active",
        "overruled_by": None,
        "superseded_by": None,
        "related_records": {
            "proposal": "PROP-003",
            "test_report": str(uuid.UUID("8ba7b810-9dad-11d1-80b4-00c04fd430f5")),
            "agreement_registry": "AG-ACC-002",
        },
        "review_date": date(2026, 6, 15),
        "recorder": "Sari Dewi",
        "recorder_role": "proposal steward",
        "verification_by": "Lani Wijaya",
        "verification_date": date(2025, 6, 20),
    },

    # 2. Conflict Triage Pool Creation
    {
        "id": DEC_TRIAGE_POOL,
        "ecosystem_id": ECOSYSTEM_ID,
        "record_id": "DEC-002",
        "date": date(2024, 8, 1),
        "holding": (
            "OmniOne establishes a conflict triage pool of trained facilitators "
            "drawn from both ETHOS.  The pool initially comprises Kai Nakamura "
            "(lead triager), Nirmala Sari, and Melati Kusuma.  Every conflict "
            "report must be triaged within 48 hours using the six-dimension "
            "assessment framework.  No conflict report may be dismissed without "
            "a documented triage assessment."
        ),
        "ratio_decidendi": (
            "During OmniOne's first 2 months of operation, two interpersonal "
            "conflicts were 'handled informally' and both re-escalated, causing "
            "deeper harm.  The ecosystem recognized that informal handling of "
            "conflicts is a structural failure mode — it allows power dynamics "
            "to determine outcomes and creates no governance record.  A formal "
            "triage pool with documented assessments is the structural remedy."
        ),
        "obiter_dicta": (
            "Kai recommended that the triage pool should eventually include at "
            "least one member from each ETHOS to ensure cultural competency "
            "across TH and AE contexts."
        ),
        "deliberation_summary": (
            "ACT process at ecosystem level.  Proposal by Kai Nakamura, co-sponsored "
            "by Manu Dewantara.  Advice phase received strong support from both "
            "ETHOS.  Consent achieved in 1 round.  No objections."
        ),
        "source_skill": "escalation-triage",
        "source_layer": 6,
        "artifact_type": "decision",
        "artifact_reference": "PROP-010 (historical, pre-seed)",
        "domain": "OmniOne Ecosystem",
        "precedent_level": "binding",  # Structural decision — creates institutional capacity
        "status": "active",
        "overruled_by": None,
        "superseded_by": None,
        "related_records": {
            "conflict_cases_referenced": ["CC-001 (historical)", "CC-002 (historical)"],
        },
        "review_date": date(2025, 8, 1),
        "recorder": "Kai Nakamura",
        "recorder_role": "conflict facilitator",
        "verification_by": "Manu Dewantara",
        "verification_date": date(2024, 8, 5),
    },

    # 3. Emergency Criteria Activation — Mount Agung Alert
    {
        "id": DEC_EMERGENCY,
        "ecosystem_id": ECOSYSTEM_ID,
        "record_id": "DEC-003",
        "date": date(2025, 3, 10),
        "holding": (
            "On 2025-03-08, the Mount Agung volcanic alert was raised to Level 3 "
            "(Siaga/Watch) by Indonesia's PVMBG.  Dewa Putra, as emergency "
            "coordinator, verified that this met the pre-defined emergency "
            "criteria for 'Volcanic Activity within 50km of SHUR Facilities' "
            "(criterion EC-003).  The OSC consented to activating the Crisis "
            "state for a maximum duration of 14 days with auto-reversion on "
            "2025-03-22.  Dewa Putra was activated as pre-authorized Emergency "
            "Coordinator with scope limited to evacuation logistics and "
            "communication."
        ),
        "ratio_decidendi": (
            "The PVMBG alert met objective, measurable criteria defined in "
            "the Emergency Criteria Registry (EC-003).  The activation was "
            "a verification of facts, not a discretionary decision.  No OSC "
            "member objected because the criteria decided, not the people."
        ),
        "obiter_dicta": (
            "This was OmniOne's first emergency activation.  The post-emergency "
            "review identified that the evacuation communication protocol "
            "needed a backup channel — radio repeaters were unreliable in the "
            "ash-fall zone.  A satellite-messaging backup was recommended."
        ),
        "deliberation_summary": (
            "Crisis state declared by Dewa Putra at 14:00 2025-03-08, confirmed "
            "by OSC consent at 16:00 (compressed 2-hour timeline per emergency "
            "protocol).  Auto-reversion timer set for 14 days.  No governance "
            "authority was expanded beyond pre-authorized emergency scope.  "
            "Alert downgraded to Level 2 on 2025-03-18.  Recovery state entered "
            "on 2025-03-20.  Closed on 2025-03-22."
        ),
        "source_skill": "crisis-coordination",
        "source_layer": 8,
        "artifact_type": "emergency_activation",
        "artifact_reference": "EM-001",
        "domain": "OmniOne Ecosystem",
        "precedent_level": "persuasive",
        "status": "active",
        "overruled_by": None,
        "superseded_by": None,
        "related_records": {
            "emergency_state": "EM-001",
            "criteria_reference": "EC-003",
        },
        "review_date": date(2026, 3, 10),
        "recorder": "Dewa Putra",
        "recorder_role": "emergency coordinator",
        "verification_by": "Manu Dewantara",
        "verification_date": date(2025, 3, 25),
    },

    # 4. Portable Record Format Decision
    {
        "id": DEC_PORTABLE,
        "ecosystem_id": ECOSYSTEM_ID,
        "record_id": "DEC-004",
        "date": date(2025, 1, 20),
        "holding": (
            "OmniOne adopts the NEOS Portable Record Format v1.0 as the standard "
            "data export format for departing members.  The format includes: "
            "(a) member identity and departure metadata; (b) governance "
            "participation history (agreements consented, proposals submitted, "
            "decisions participated in); (c) resource pool transactions where "
            "the member was a recipient or steward; (d) conflict case involvement "
            "as reporter, participant, or facilitator.  All data is in "
            "machine-readable JSON with a human-readable summary.  Members may "
            "choose which non-mandatory sections to include."
        ),
        "ratio_decidendi": (
            "The UAF (Article 10) guarantees exit as a structural right.  GDPR "
            "Article 20 establishes data portability as a fundamental right.  "
            "The Portable Record Format fulfills both obligations and exceeds "
            "the legal minimum by including governance participation history "
            "that allows the departing member to demonstrate their governance "
            "experience in future ecosystems."
        ),
        "obiter_dicta": (
            "Ketut noted that the format should be extensible — future ecosystems "
            "may run different NEOS configurations with different record types.  "
            "The format includes an extension mechanism for ecosystem-specific data."
        ),
        "deliberation_summary": (
            "Proposal by Ketut Arsana, co-sponsored by Indra Gunawan.  Advice "
            "from 5 members.  Consent in 1 round — no objections.  The decision "
            "was uncontroversial because it implements a UAF guarantee."
        ),
        "source_skill": "portable-record",
        "source_layer": 10,
        "artifact_type": "decision",
        "artifact_reference": "PROP-012 (historical, pre-seed)",
        "domain": "OmniOne Ecosystem",
        "precedent_level": "binding",
        "status": "active",
        "overruled_by": None,
        "superseded_by": None,
        "related_records": {
            "uaf_article": "Article 10",
            "gdpr_reference": "GDPR Article 20",
        },
        "review_date": date(2026, 1, 20),
        "recorder": "Ketut Arsana",
        "recorder_role": "exit coordinator",
        "verification_by": "Manu Dewantara",
        "verification_date": date(2025, 1, 25),
    },
]


# ── Decision Participants ──────────────────────────────────────────

DECISION_PARTICIPANTS: list[dict] = [
    # Bamboo decision
    {"decision_record_id": DEC_BAMBOO, "name": "Gede Artha", "role": "proposer", "position": "consent"},
    {"decision_record_id": DEC_BAMBOO, "name": "Lani Wijaya", "role": "AE steward", "position": "consent"},
    {"decision_record_id": DEC_BAMBOO, "name": "Dewa Putra", "role": "advisor", "position": "consent"},
    {"decision_record_id": DEC_BAMBOO, "name": "Sari Dewi", "role": "facilitator", "position": "consent"},

    # Triage pool decision
    {"decision_record_id": DEC_TRIAGE_POOL, "name": "Kai Nakamura", "role": "proposer", "position": "consent"},
    {"decision_record_id": DEC_TRIAGE_POOL, "name": "Manu Dewantara", "role": "co-sponsor", "position": "consent"},
    {"decision_record_id": DEC_TRIAGE_POOL, "name": "Nirmala Sari", "role": "nominated triager", "position": "consent"},
    {"decision_record_id": DEC_TRIAGE_POOL, "name": "Melati Kusuma", "role": "nominated triager", "position": "consent"},

    # Emergency decision
    {"decision_record_id": DEC_EMERGENCY, "name": "Dewa Putra", "role": "emergency coordinator", "position": "consent"},
    {"decision_record_id": DEC_EMERGENCY, "name": "Manu Dewantara", "role": "OSC member", "position": "consent"},
    {"decision_record_id": DEC_EMERGENCY, "name": "Lani Wijaya", "role": "OSC member", "position": "consent"},
    {"decision_record_id": DEC_EMERGENCY, "name": "Putu Ardana", "role": "OSC member", "position": "consent"},

    # Portable record decision
    {"decision_record_id": DEC_PORTABLE, "name": "Ketut Arsana", "role": "proposer", "position": "consent"},
    {"decision_record_id": DEC_PORTABLE, "name": "Indra Gunawan", "role": "co-sponsor", "position": "consent"},
    {"decision_record_id": DEC_PORTABLE, "name": "Manu Dewantara", "role": "verifier", "position": "consent"},
]

# ── Dissent Records ────────────────────────────────────────────────
# The bamboo decision had a minor dissent from TH

DISSENT_RECORDS: list[dict] = [
    {
        "decision_record_id": DEC_BAMBOO,
        "objector": "Putu Ardana",
        "objection": (
            "The decision mandates bamboo standards for AE construction.  I do "
            "not object to the standards — they are excellent.  However, the "
            "moon-phase harvesting requirement implicitly relies on the Balinese "
            "Sasih calendar.  This is culturally appropriate for Bali but should "
            "be documented as a cultural dependency, not a universal requirement.  "
            "If these standards are shared with other ecosystems, they should "
            "know that 'correct moon phase' is defined by the Balinese agricultural "
            "calendar, not the Gregorian calendar."
        ),
        "resolution": (
            "Noted and added as obiter dicta.  The standards document now includes "
            "a cultural context section explaining the Sasih calendar reference.  "
            "Putu's objection did not block consent — it was a dissent on "
            "documentation, not on substance."
        ),
        "notes": "Putu: 'Dissent recorded, not blocking.  This is about cultural legibility.'",
    },
    # Triage pool decision — minor dissent on scope
    {
        "decision_record_id": DEC_TRIAGE_POOL,
        "objector": "Nirmala Sari",
        "objection": (
            "The triage pool of 3 members is adequate for 50 participants but "
            "will not scale to 500.  The decision should include a trigger for "
            "automatic expansion when participant count exceeds 150."
        ),
        "resolution": (
            "The objection was integrated.  The triage pool now includes an "
            "automatic review trigger at 150 participants."
        ),
        "notes": "Nirmala: 'This is structural foresight, not disagreement.'",
    },
]

# ── Semantic Tags ──────────────────────────────────────────────────

SEMANTIC_TAGS: list[dict] = [
    # Bamboo decision tags
    {
        "decision_record_id": DEC_BAMBOO,
        "topic": {"primary": "construction standards", "secondary": ["bamboo", "traditional knowledge"]},
        "affected_parties": {"ethos": ["AE"], "roles": ["builder"]},
        "ecosystem_scope": "AE ETHOS",
        "urgency_at_time": "normal",
        "related_precedents": None,
    },
    # Triage pool decision tags
    {
        "decision_record_id": DEC_TRIAGE_POOL,
        "topic": {"primary": "conflict resolution infrastructure", "secondary": ["triage", "facilitation"]},
        "affected_parties": {"scope": "all_ecosystem_participants"},
        "ecosystem_scope": "OmniOne Ecosystem",
        "urgency_at_time": "elevated",
        "related_precedents": None,
    },
    # Emergency decision tags
    {
        "decision_record_id": DEC_EMERGENCY,
        "topic": {"primary": "emergency activation", "secondary": ["volcanic hazard", "crisis coordination"]},
        "affected_parties": {"ethos": ["AE", "TH"], "geographic": "Mount Agung zone"},
        "ecosystem_scope": "OmniOne Ecosystem",
        "urgency_at_time": "emergency",
        "related_precedents": {"references": ["EC-003"]},
    },
    # Portable record decision tags
    {
        "decision_record_id": DEC_PORTABLE,
        "topic": {"primary": "data portability", "secondary": ["exit", "GDPR", "governance memory"]},
        "affected_parties": {"scope": "all_ecosystem_participants"},
        "ecosystem_scope": "OmniOne Ecosystem",
        "urgency_at_time": "normal",
        "related_precedents": {"legal": ["GDPR Article 20"]},
    },
]
