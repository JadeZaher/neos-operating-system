# Specification: Exit & Portability (Layer X)

## Track ID
`exit_portability_20260302`

## Overview

This track builds the five skills of **Layer X: Exit & Portability**. Exit is the capstone layer of the NEOS governance stack. If participants cannot leave freely, every other governance mechanism is undermined: consent becomes coercion, agreements become traps, and voice degrades because it has no alternative. This layer ensures that exit is structurally treated as a right, not a failure; that departure is graceful rather than destructive; and that participation history travels with the departing member.

The layer draws on Albert Hirschman's Exit, Voice, and Loyalty framework (when exit is costly, Voice degrades; when exit is too easy, Voice is abandoned -- the design goal is genuine choice), GDPR Article 20 on data portability (structured, machine-readable format), cooperative dissolution precedents (Exit to Community model, Twin Oaks dissolution protocol), and graceful degradation engineering (no single departure should be catastrophic).

This is the final functional layer of the skill stack. It references all earlier layers because exit intersects with every governance domain: agreements must be unwound (Layer I), authority must be transferred (Layer II), pending decisions must be handled (Layer III), economic commitments must be settled (Layer IV), inter-unit relationships must be notified (Layer V), active conflicts must be resolved or transferred (Layer VI), monitoring data must be preserved (Layer VII and IX), and emergency roles must have succession (Layer VIII).

## Background

### Hirschman's Exit, Voice, and Loyalty

Hirschman's framework identifies Exit and Voice as the two primary mechanisms through which participants influence organizations. Loyalty mediates between them -- loyal members prefer Voice (trying to change the organization) over Exit (leaving). The design insight for NEOS: when exit is too costly (financially, socially, or logistically), members cannot credibly threaten departure, which means their Voice carries no weight, which means governance degrades into compliance. Conversely, when exit is too easy (no commitments, no handoff, no consequences), members abandon Voice for Exit at the first disagreement, preventing the organization from developing resilience.

NEOS designs for genuine choice: exit is always possible, but it involves an orderly process that respects existing commitments without trapping the departing member.

### Data Portability as Governance Right

GDPR Article 20 establishes the right to receive personal data "in a structured, commonly used and machine-readable format." NEOS extends this principle beyond legal compliance to governance philosophy: a participant's governance history -- their proposals, votes, agreements, conflict resolution participation, resource contributions, and role tenure -- belongs to them. This portable record functions as governance reputation across NEOS ecosystems.

In OmniOne specifically, Current-See records, SHUR participation history, and ETHOS membership records travel with the departing member.

### Graceful Degradation

From engineering: a system designed for graceful degradation continues to function at reduced capacity when components fail, rather than failing catastrophically. Applied to governance: no single member's departure -- not even the most active, most connected, or most authoritative member -- should cause governance to collapse. If it would, that is a capture indicator (single point of failure = capture by indispensability).

### Exit to Community and Dissolution Precedents

The Exit to Community model reframes organizational departure as transition rather than termination. Twin Oaks commune's dissolution protocol provides a concrete precedent: supermajority vote to dissolve, ordered asset liquidation, debt settlement, member distribution.

---

## Functional Requirements

### FR-1: Voluntary Exit (`voluntary-exit`)

**Description:** Manage the full process of an individual member voluntarily departing the ecosystem. This skill covers the decision to leave, the notification process, the handoff of responsibilities, the data export, and the formal departure record. Exit is treated as a right, not as a failure or punishment.

**Acceptance Criteria:**
- AC-1.1: The skill defines all required inputs (departing member identity, departure timeline -- immediate or scheduled, reason -- optional and never required, active commitments list, active roles list, active agreements list).
- AC-1.2: The step-by-step process includes: departure notification (to all affected circles and parties), commitment inventory (comprehensive list of what the member is currently obligated to), handoff plan (for each commitment: transfer to another member, wind down, or formally close), data export (portable record generation), formal departure record (registered, not suppressed), re-entry provision (the member is not blacklisted -- departure does not preclude future return).
- AC-1.3: The output artifact is a Departure Record documenting: the member's departure date, the commitment handoff plan, the portable record export confirmation, and the re-entry eligibility status.
- AC-1.4: The authority boundary check specifies that no one can prevent a member from exiting. No approval is required to leave. The handoff process can be expedited (30-day default, 7-day minimum for urgent departure) but not used as a hostage mechanism.
- AC-1.5: The failure containment logic addresses what happens when: a member departs without completing the handoff process (commitments enter emergency-transfer protocol, not abandonment), a member is the sole holder of a critical role (graceful degradation -- the role's responsibilities are distributed among remaining members until a new holder is appointed), multiple members depart simultaneously (triggers governance health audit from Layer VII).
- AC-1.6: The capture resistance check addresses exit as punishment (departure must never trigger punitive consequences -- no loss of earned resources, no public shaming, no blacklisting), exit as hostage-taking (commitments cannot be designed to be so onerous that exit is practically impossible), and silent departure (the process is designed to be acknowledged and recorded, not hidden).
- AC-1.7: An OmniOne walkthrough demonstrates an AE member voluntarily departing the Bali SHUR.
- AC-1.8: All 7 stress-test scenarios documented.

**Priority:** P0 -- Core exit right, built first.

### FR-2: Commitment Unwinding (`commitment-unwinding`)

**Description:** Systematically close, transfer, or wind down all of a departing member's active obligations. This skill is the detailed operational process that sits within the voluntary-exit flow, handling the specifics of what happens to each type of commitment.

**Acceptance Criteria:**
- AC-2.1: The skill defines commitment categories and their unwinding protocols: role obligations (transfer to successor or distribute among circle), agreement obligations (transfer party status to replacement or remove party with consent of remaining parties), economic commitments (settle outstanding obligations, return stewarded assets, transfer access rights), pending proposals (withdraw or transfer authorship), active conflict resolutions (complete if near resolution, transfer mediator role if applicable, formally pause with documented context).
- AC-2.2: The step-by-step process specifies a commitment-by-commitment review: inventory all commitments, classify each by category, apply the appropriate unwinding protocol, get acknowledgment from receiving parties, document each unwinding in the Departure Record.
- AC-2.3: The output artifact is a Commitment Unwinding Ledger linked to the Departure Record, documenting each commitment's original state, unwinding action, and receiving party.
- AC-2.4: The authority boundary check specifies that the departing member cannot be required to fulfill commitments beyond the departure timeline (30-day default). If a commitment requires more than 30 days to unwind, the skill defines how to create a wind-down agreement with a defined end date -- the departing member is not held indefinitely.
- AC-2.5: The failure containment logic addresses orphaned commitments (commitments with no willing recipient enter an emergency-transfer queue managed by the affected circle), contested obligations (disputes about what is owed are referred to Layer VI conflict resolution with expedited timeline), and cascading unwinding (one commitment's unwinding triggers the need to unwind a dependent commitment).
- AC-2.6: An OmniOne walkthrough demonstrates unwinding the commitments of a departing AE member who holds two circle roles, is party to three agreements, has an outstanding resource allocation, and is mid-way through a proposal's ACT process.
- AC-2.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Operational core of graceful exit.

### FR-3: Portable Record (`portable-record`)

**Description:** Maintain and export a structured, machine-readable record of a member's governance participation history. This record travels with the member and functions as portable governance reputation across NEOS ecosystems.

**Acceptance Criteria:**
- AC-3.1: The skill defines the portable record schema: member identity, ecosystem(s) participated in, roles held (with tenure dates), agreements consented to and participated in, proposals authored and their outcomes, ACT participation record (advice given, consent positions, objections raised and their integration), conflict resolution participation, resource contributions and allocations, Current-See transaction history (OmniOne-specific), governance health audit participation, and departure record(s).
- AC-3.2: The step-by-step process specifies: record compilation (assembling data from agreement registry, proposal registry, decision logs, role registry, resource ledger), privacy review (the member chooses which elements to include in their export -- mandatory elements are limited to identity verification and departure status; all governance participation details are opt-in for export), format export (structured YAML or JSON, human-readable markdown summary), verification (the exported record is signed or checksummed against the source registries to confirm authenticity without requiring ongoing connection to the originating ecosystem).
- AC-3.3: The output artifact is a Portable Governance Record in structured format with a human-readable summary.
- AC-3.4: The authority boundary check specifies that no one can prevent a member from exporting their own participation record. The ecosystem can choose what data it maintains, but the member's right to export their own history is absolute.
- AC-3.5: The capture resistance check addresses data hostage-taking (using data retention as leverage to prevent exit), selective record export (ecosystem filtering unfavorable records from the export -- the member controls what they export, not the ecosystem), and record falsification (the verification mechanism prevents modification after export).
- AC-3.6: The cross-unit interoperability section defines how a portable record from one ecosystem is recognized by another NEOS ecosystem -- the record format is standardized, but the importing ecosystem decides what weight to give it.
- AC-3.7: An OmniOne walkthrough demonstrates a departing member exporting their 2-year participation record, including Current-See transaction history, and presenting it when joining a new ETHOS in Costa Rica.
- AC-3.8: All 7 stress-test scenarios documented.

**Priority:** P0 -- Enables genuine portability across ecosystems.

### FR-4: ETHOS Dissolution (`ethos-dissolution`)

**Description:** Define the formal process for dissolving an ETHOS (Emergent Thriving Holonic Organizational Structure). Dissolution is the collective exit -- when an entire organizational unit ceases to exist. The skill handles the supermajority vote, asset disposition, commitment settlement, member transition, and record preservation.

**Acceptance Criteria:**
- AC-4.1: The skill defines dissolution triggers: supermajority vote of ETHOS members (recommended: 2/3 consent), governance incapacity (the ETHOS cannot achieve decision-making quorum for a defined period), ecosystem-level intervention (only under extreme circumstances through full ecosystem ACT process -- this is not a unilateral ecosystem power).
- AC-4.2: The step-by-step process specifies: dissolution proposal (submitted through normal ACT process with extended advice period), impact assessment (what happens to members, agreements, assets, commitments, inter-unit relationships), consent round (supermajority threshold), asset disposition (ordered process: settle debts, return stewarded assets to stewards, distribute remaining assets per pre-agreed formula or consent of remaining members), commitment settlement (all active agreements reviewed: transfer to receiving entities, sunset with notice, or formally close), member transition (each member follows voluntary-exit or transfers to another ETHOS), record preservation (all ETHOS governance records are archived and accessible), formal dissolution record (registered in ecosystem records).
- AC-4.3: The output artifact is a Dissolution Record documenting: the dissolution vote record, asset disposition ledger, commitment settlement ledger, member transition records, and archive reference.
- AC-4.4: The authority boundary check specifies that no external body can unilaterally dissolve an ETHOS. Even ecosystem-level intervention requires a full ACT process with the ETHOS's members as affected parties with voice in the decision.
- AC-4.5: The failure containment logic addresses: contested dissolution (a minority objects -- the supermajority threshold protects minority voice but does not give it veto), incomplete asset settlement (unsettled assets enter escrow managed by the ecosystem until resolved), members who refuse to transition (they are treated as voluntary exits from the dissolving ETHOS), and cascading effects on other ETHOS (inter-unit agreements with the dissolving ETHOS trigger review in affected ETHOS).
- AC-4.6: An OmniOne walkthrough demonstrates the dissolution of a small ETHOS in Bali that has dwindled to 4 members and can no longer sustain operations.
- AC-4.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Important but less frequent than individual exit.

### FR-5: Re-Entry Integration (`re-entry-integration`)

**Description:** Define the process for welcoming a returning member who previously departed. The skill handles record verification, commitment re-establishment, role eligibility, and the recognition of portable governance history. Re-entry is not treated as a second-class onboarding but as a structured return with historical context.

**Acceptance Criteria:**
- AC-5.1: The skill defines re-entry eligibility: any member who departed through the voluntary-exit process is eligible for re-entry. Members who were removed through conflict resolution outcomes may have re-entry conditions defined by the resolution.
- AC-5.2: The step-by-step process specifies: re-entry request (member presents portable record), record verification (ecosystem verifies the record against its archived data), agreement review (the returning member reviews current UAF and relevant agreements -- the ecosystem may have changed since their departure), consent to current agreements (not the agreements that existed when they left), role eligibility assessment (previous role tenure is acknowledged but does not guarantee reinstatement -- current role holders are not displaced), commitment establishment (new commitments are established through normal processes), re-entry record (registered, linked to original departure record and portable record).
- AC-5.3: The output artifact is a Re-Entry Record documenting: the returning member's identity, verified portable record reference, agreements consented to, initial role assignments (if any), and linked departure record.
- AC-5.4: The authority boundary check specifies that re-entry cannot be denied arbitrarily. Rejection requires a specific, stated reason that is subject to Layer VI conflict resolution if contested.
- AC-5.5: The capture resistance check addresses: re-entry as gatekeeping (using the re-entry process to selectively exclude returning members based on political alignment), re-entry as preferential treatment (fast-tracking allies while slow-walking others -- the process timelines are standardized), and history erasure (ignoring the member's portable record and treating them as a completely new participant).
- AC-5.6: The cross-unit interoperability section defines how a member can use a portable record from one ETHOS to enter a different ETHOS within the same or different ecosystem.
- AC-5.7: An OmniOne walkthrough demonstrates a former AE member returning after 18 months, presenting their portable record, discovering the UAF has been amended, consenting to the current UAF, and being integrated into a circle where their previous expertise is relevant.
- AC-5.8: All 7 stress-test scenarios documented.

**Priority:** P1 -- Completes the exit lifecycle but is less urgent than exit itself.

---

## Non-Functional Requirements

### NFR-1: Modularity

Each skill must function independently. A participant reading voluntary-exit should be able to process a departure without loading commitment-unwinding (though they would benefit from it). Skills reference each other by name but do not require co-loading.

### NFR-2: Line Limit

Each SKILL.md must be under 500 lines. Record schemas, unwinding protocol details, and dissolution checklists go in `assets/`.

### NFR-3: Portability

All skills are NEOS-generic at the structural level. OmniOne-specific elements (Current-See records, SHUR membership, ETHOS names) appear as clearly marked examples.

### NFR-4: Exit as Right, Not Failure

Every skill in this layer must frame exit positively or neutrally. No skill may impose punitive consequences for departure. The language must reflect that exit is a structural right, not a moral failing.

### NFR-5: Data Sovereignty

Members own their participation data. The portable record skill must give members control over what data they export. The ecosystem retains its own records (for governance continuity) but cannot prevent members from exporting their own history.

### NFR-6: Graceful Degradation

No single member's departure should cause governance to collapse. If the voluntary-exit skill identifies that a departure would create a single point of failure, this is treated as a governance health issue (Layer VII) to be addressed, not as a reason to prevent the departure.

### NFR-7: Validation

Every SKILL.md must pass automated validation via `scripts/validate_skill.py`.

---

## User Stories

### US-1: Member Departs Voluntarily
**As** an AE member who has decided to leave the ecosystem,
**I want** a clear, dignified process for departing that handles my commitments and preserves my record,
**So that** I can leave without guilt, without burning bridges, and with my participation history intact.

**Given** the member has active roles, agreements, and resource commitments,
**When** they initiate the voluntary-exit process,
**Then** a departure plan is created with handoff assignments, a portable record is generated, and a formal departure is registered.

### US-2: AI Agent Processes Commitment Unwinding
**As** an AI agent assisting with a member's departure,
**I want** to inventory all active commitments and generate an unwinding plan,
**So that** no commitment is orphaned and every obligation is properly transferred or closed.

**Given** the departing member's identity and the commitment registries,
**When** the AI agent follows the commitment-unwinding skill,
**Then** a comprehensive Commitment Unwinding Ledger is produced with specific handoff assignments for every commitment.

### US-3: Departing Member Exports Portable Record
**As** a departing member who may join another NEOS ecosystem,
**I want** to export my governance participation history in a portable format,
**So that** my new ecosystem can recognize my experience without requiring me to start from zero.

**Given** the member has 2 years of governance participation history,
**When** they follow the portable-record skill to compile and export,
**Then** they receive a structured record with a human-readable summary, with privacy choices respected and verification integrity maintained.

### US-4: ETHOS Members Vote to Dissolve
**As** a member of a small ETHOS that can no longer sustain operations,
**I want** a structured dissolution process that settles all obligations fairly,
**So that** the dissolution does not harm other ETHOS, creditors, or departing members.

**Given** the ETHOS has 4 remaining members and cannot achieve quorum for decisions,
**When** a dissolution proposal is submitted and achieves supermajority consent,
**Then** assets are disposed of in order, commitments are settled, members transition to other ETHOS or exit, and records are archived.

### US-5: Former Member Requests Re-Entry
**As** a former member who left 18 months ago and now wishes to return,
**I want** my previous participation history to be recognized and the re-entry process to be clear and fair,
**So that** I can rejoin without being treated as a stranger or being penalized for having left.

**Given** the returning member has a verified portable record from their previous participation,
**When** they follow the re-entry-integration skill,
**Then** their record is verified, they consent to current (possibly amended) agreements, and they are integrated with their history acknowledged.

### US-6: Ecosystem Handles Sudden Mass Departure
**As** an ecosystem steward facing the departure of 30% of participants,
**I want** the exit process to scale without collapse,
**So that** governance continues to function for remaining participants.

**Given** multiple members initiate voluntary exit simultaneously,
**When** the departure process is followed for each,
**Then** the commitment unwinding process identifies systemic handoff needs, Layer VII governance health audit is triggered, and governance continuity is maintained through graceful degradation.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-10-exit/
    README.md
    voluntary-exit/
      SKILL.md
      assets/
        departure-record-template.yaml
        departure-checklist.yaml
      references/
      scripts/
    commitment-unwinding/
      SKILL.md
      assets/
        commitment-unwinding-ledger-template.yaml
        unwinding-protocols-by-type.yaml
      references/
      scripts/
    portable-record/
      SKILL.md
      assets/
        portable-record-schema.yaml
        portable-record-example.yaml
      references/
      scripts/
    ethos-dissolution/
      SKILL.md
      assets/
        dissolution-record-template.yaml
        dissolution-checklist.yaml
      references/
      scripts/
    re-entry-integration/
      SKILL.md
      assets/
        re-entry-record-template.yaml
        re-entry-checklist.yaml
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name
description: "..."
layer: 10
version: 0.1.0
depends_on: []
---
```

### Cross-Layer Dependencies

Layer X is the capstone and references all earlier layers:
- **Layer I (Agreement):** Departure triggers agreement review for affected agreements. Dissolution requires agreement settlement.
- **Layer II (Authority):** Departure requires role transfer. Dissolution requires authority redistribution.
- **Layer III (ACT Engine):** Pending proposals must be withdrawn or transferred. Dissolution uses ACT process.
- **Layer IV (Economic):** Economic commitments must be settled. Stewarded assets must be returned.
- **Layer V (Inter-Unit):** Inter-ETHOS relationships affected by departure or dissolution must be notified.
- **Layer VI (Conflict):** Active conflicts involving the departing member must be resolved or formally paused.
- **Layer VII (Safeguard):** Mass departure triggers governance health audit. Departure of a monitor requires succession.
- **Layer VIII (Emergency):** Departure of an emergency role holder requires succession update.
- **Layer IX (Memory):** Departure records are preserved in governance memory. Portable records are compiled from memory layer data.

### Portable Record Format

The portable record format is defined in `assets/portable-record-schema.yaml` and follows these principles:
- Structured (YAML primary, JSON alternative)
- Human-readable summary in markdown
- Member controls which participation details to include (privacy by design)
- Verification hash against source registries (integrity without ongoing dependency)
- Standardized across NEOS ecosystems (any NEOS ecosystem can read the format)

---

## Out of Scope

- **Legal compliance specifics** -- GDPR Article 20 is referenced as a principle, but jurisdiction-specific legal compliance is configuration, not core skill.
- **Financial settlement mechanics** -- The skills define the process for identifying and transferring economic obligations, not the accounting details.
- **Emotional or relational aspects of departure** -- The skills define structural processes. Community rituals, farewell practices, and emotional support are cultural, not structural.
- **Software implementation** -- No automated record export systems, APIs, or databases.
- **Involuntary removal** -- Expulsion is a conflict resolution outcome (Layer VI), not an exit process. This layer handles voluntary exit and dissolution only.

---

## Open Questions

1. **Departure timeline flexibility**: The default 30-day handoff period may be too long for members in crisis situations or too short for members with complex commitments. Should the timeline be role-dependent (e.g., 7 days for TH, 30 days for AE, 60 days for OSC)?

2. **Portable record privacy vs. verification**: How do you verify a portable record's authenticity while respecting the member's choice to redact certain participation details? The current design uses a hash against source registries, but this may reveal what was redacted through differential analysis.

3. **Dissolution of the last ETHOS**: If all ETHOS dissolve, what happens to the ecosystem-level agreements and infrastructure? This edge case touches on ecosystem dissolution, which may need a separate skill or be addressed as a configuration of ETHOS dissolution at ecosystem scale.

4. **Re-entry after conflict-based removal**: The spec states that members removed through conflict resolution may have re-entry conditions. Who defines those conditions, and are they time-limited? Recommendation: conditions are defined by the conflict resolution outcome, are time-limited (maximum 2 years), and are reviewable through normal ACT process.

5. **Cross-ecosystem portable record trust**: When a member presents a portable record from a different NEOS ecosystem, how much trust should the receiving ecosystem place in it? The verification hash confirms the record was not modified after export, but the receiving ecosystem may not trust the originating ecosystem's data quality. This is deferred to Layer V (Inter-Unit Coordination) but should be noted in the portable-record skill.
