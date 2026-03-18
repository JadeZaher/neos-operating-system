# Specification: Foundation -- Agreement Layer + ACT Decision Engine

## Track ID
`foundation_20260301`

## Overview

This track builds the two foundational skill layers of the NEOS governance stack: **Layer I (Agreement Layer)** and **Layer III (ACT Decision Engine)**. Every other NEOS layer depends on these two. Agreements define what participants consent to. The ACT engine defines how participants change what they have consented to. Together they form the bedrock protocol: you cannot have authority without agreements, you cannot have economics without decisions, and you cannot have conflict resolution without both.

This is a greenfield effort. No prior NEOS skills exist. The deliverables are markdown SKILL.md files with YAML frontmatter, supporting asset templates, and a global validation script. The first ecosystem instantiation is OmniOne.

## Background

### Why Agreement Layer First

NEOS operates on explicit agreements rather than implicit rules. Every relationship between participants, every resource allocation, every role boundary is defined by a traceable agreement. Without a structural mechanism for creating, amending, reviewing, and registering agreements, governance devolves into informal authority -- the exact failure mode NEOS exists to prevent.

The Universal Agreement Field (UAF) is the root agreement. It defines the baseline commitments every participant makes upon entering the ecosystem. All other agreements inherit from and must not contradict the UAF.

### Why ACT Engine Alongside It

Agreements are not static. They must be proposed, debated, modified, and tested. The ACT (Advice, Consent, Test) decision engine is the protocol through which agreements come into existence and change over time. Building agreements without the decision engine would produce static documents with no legitimate way to evolve them. Building the decision engine without agreements would produce a process with nothing to govern.

The two layers are co-dependent and must be built in an interleaved fashion.

### Consent vs. Consensus

NEOS uses two distinct decision modes:
- **Consent** (default for ACT decisions): "No one present has a reasoned, paramount objection." The bar is the absence of objections grounded in harm to the circle's aim, not the presence of enthusiasm.
- **Consensus** (required for OSC-level and Master Plan decisions): "All members of the deciding body actively agree." This higher bar applies to foundational decisions that affect the entire ecosystem.

Each skill must clearly state which mode applies at each decision point.

### GAIA 6-Level Escalation Model

The ACT process follows a graduated escalation. This model is attributed to the "Futurist Playground" Value Decision Model and adapted for NEOS:

1. **Consensus** -- All agree within the scope of the Master Plan or Sub Master Plan. Note: this level uses consensus (active agreement from all), distinct from consent (absence of reasoned objection) used in standard ACT decisions.
2. **Culture Code** -- Circle-internal decisions using the circle's own chosen process; escalates when the decision touches the larger collective.
3. **Next Steps Process / Advice Process + Panel of Experts** -- Pre-proposal synergy check, then formal proposal for alignment. The "Next Steps Process" from the source material is incorporated here as the structured transition from culture-code-level discussion to formal advice-gathering.
4. **Coaching** -- Finding a third solution between competing options; coach maps collective vs. community vs. private domain. At this level, a "Doing Both Solution" is an explicit resolution option where competing proposals are synthesized rather than choosing one.
5. **Alignment Sense Making** -- Check against policies, agreements, values; compare impact; may delegate to a circle with agency or a Wisdom Council. Wisdom Council composition is an open question (OQ-11).
6. **Decision Resolution** -- Value decision model comparison chart (Futurist Playground attribution) when no other level resolves the matter.

**Distinction:** "Preference Decisions" (matters of taste or convenience with no structural impact) may be resolved at Level 1-2 without formal ACT process. "Solution Decisions" (matters with structural, resource, or authority impact) require the full ACT cycle starting at Level 3. See OQ-13.

---

## Functional Requirements

### Layer I: Agreement Layer

#### FR-1: Agreement Creation (`agreement-creation`)

**Description:** Enable any authorized participant to draft, propose, and ratify a new agreement. Agreement types include space agreements, access agreements, organizational agreement fields, and the Universal Agreement Field. The skill defines the full lifecycle from draft to ratification.

**Acceptance Criteria:**
- AC-1.1: The skill defines all required inputs (proposer identity, agreement type, affected parties, domain scope, proposed text, expiry date).
- AC-1.2: The step-by-step process routes the draft through the appropriate ACT decision level based on agreement scope.
- AC-1.3: The output artifact is a complete, versioned agreement document with unique identifier, ratification record, and review date.
- AC-1.4: The authority boundary check prevents any individual from unilaterally creating binding agreements outside their domain.
- AC-1.5: The capture resistance check addresses capital influx influence on agreement terms.
- AC-1.6: An OmniOne walkthrough demonstrates a TH member proposing a new space agreement for a SHUR residency.
- AC-1.7: All 7 stress-test scenarios are documented with full narrative results.

**Priority:** P0 -- Anchor skill, built first.

#### FR-2: Agreement Amendment (`agreement-amendment`)

**Description:** Enable modification of an existing agreement through proper process. Amendments must reference the original agreement, specify what changes, and route through the appropriate ACT decision level. Amendments to the UAF require consensus of the OSC.

**Acceptance Criteria:**
- AC-2.1: The skill defines amendment types (minor clarification, substantive change, scope expansion, scope reduction).
- AC-2.2: Each amendment type maps to a minimum ACT decision level.
- AC-2.3: The output artifact is a versioned amendment record linked to the parent agreement.
- AC-2.4: The authority boundary check prevents amendments that would expand authority beyond the amending body's domain.
- AC-2.5: The failure containment logic defines what happens when an amendment is partially ratified (some affected parties consent, others object).
- AC-2.6: An OmniOne walkthrough demonstrates the AE proposing an amendment to an existing ETHOS agreement field.
- AC-2.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Required for agreement evolution.

#### FR-3: Agreement Review (`agreement-review`)

**Description:** Define the periodic review cycle for all agreements. Every agreement must have a review date. The review process re-validates the agreement against current conditions, checks for staleness, and triggers renewal, revision, or sunset.

**Acceptance Criteria:**
- AC-3.1: The skill defines review triggers (scheduled date, participant request, threshold event such as 30% exit).
- AC-3.2: Review outcomes are enumerated: renew as-is, revise (triggers amendment skill), sunset (triggers graceful deprecation).
- AC-3.3: The expiry/review condition section defines default review intervals by agreement type.
- AC-3.4: The failure containment logic addresses what happens when a review is missed (automatic sunset warning, not automatic invalidation).
- AC-3.5: An OmniOne walkthrough demonstrates a scheduled annual review of the SHUR space agreement.
- AC-3.6: All 7 stress-test scenarios documented.

**Priority:** P1 -- Important but depends on FR-1 and FR-2 existing.

#### FR-4: Agreement Registry (`agreement-registry`)

**Description:** Maintain and query the registry of all active agreements. The registry is the single source of truth for what agreements exist, their status, version history, and relationships. Any participant can query the registry. Only authorized processes can write to it.

**Acceptance Criteria:**
- AC-4.1: The skill defines the registry schema (agreement ID, type, status, version, parent agreement, affected parties, domain, created date, review date, sunset date).
- AC-4.2: Query capabilities include: by type, by domain, by affected party, by status, by date range.
- AC-4.3: Write operations are restricted to outputs of agreement-creation, agreement-amendment, and agreement-review skills.
- AC-4.4: The cross-unit interoperability section defines how registries federate across ETHOS.
- AC-4.5: An OmniOne walkthrough demonstrates an AE member querying the registry to find all active agreements affecting the Economics circle.
- AC-4.6: All 7 stress-test scenarios documented.

**Priority:** P1 -- Registry supports all other agreement skills.

#### FR-5: Universal Agreement Field (`universal-agreement-field`)

**Description:** Define the master agreement that all ecosystem participants consent to upon entry. The UAF establishes baseline commitments (honesty, accountability, consent-based process, conflict resolution, stewardship, sovereignty). It is the root node of the agreement hierarchy. Amendment requires OSC consensus.

**Acceptance Criteria:**
- AC-5.1: The skill defines the UAF structure with sections: Agreements and Accountability, Processes, Conflict, Stewardship and Contribution, Sovereignty and Evolution, Sovereignty Freedom and Responsibility.
- AC-5.2: The UAF template in `assets/` is derived from the OmniOne field agreement example and generalized for NEOS portability.
- AC-5.3: The authority boundary check specifies that only OSC consensus can amend the UAF.
- AC-5.4: The exit compatibility check defines what happens to a participant's obligations under the UAF when they exit.
- AC-5.5: The capture resistance check addresses attempts to weaken UAF commitments through capital pressure or charismatic leadership.
- AC-5.6: An OmniOne walkthrough demonstrates a new member onboarding and consenting to the UAF.
- AC-5.7: All 7 stress-test scenarios documented.
- AC-5.8: The skill defines the agreement hierarchy (Universal > Ecosystem > Access > Stewardship > ETHOS > Culture Code > Personal) and the override rule: no lower-level agreement may contradict a higher-level one.
- AC-5.9: The skill references the "I agree to..." personal commitment format from the OmniOne field agreement as the default language pattern.

**Priority:** P0 -- Root agreement, conceptual anchor for the entire stack.

---

### Layer III: ACT Decision Engine

#### FR-6: Proposal Creation (`proposal-creation`)

**Description:** Enable any authorized participant to create and submit a proposal. Proposal types include EcoPlan proposals, GenPlan proposals, agreement amendments, resource requests, and policy changes. The skill defines the structure of a valid proposal and routes it to the correct ACT phase.

**Acceptance Criteria:**
- AC-6.1: The skill defines all required inputs (proposer identity, proposal type, affected domain, proposed change, rationale, impacted parties, urgency level).
- AC-6.2: The step-by-step process includes pre-submission synergy check (GAIA Level 3).
- AC-6.3: The output artifact is a numbered, versioned proposal document with status tracking.
- AC-6.4: The authority boundary check ensures proposers can only submit proposals within their domain or escalate through proper channels.
- AC-6.5: An OmniOne walkthrough demonstrates a Builder creating a proposal to establish a new Economics circle.
- AC-6.6: All 7 stress-test scenarios documented.

**Priority:** P0 -- Anchor skill for ACT Engine.

#### FR-7: ACT Advice Phase (`act-advice-phase`)

**Description:** Run the Advice phase of the ACT process. The proposer gathers input from all parties who will be impacted by the proposal. Advice is non-binding but must be demonstrably sought and considered. The proposer documents how each piece of advice was integrated or why it was not.

**Acceptance Criteria:**
- AC-7.1: The skill defines who must be consulted (all parties within the affected domain, plus any parties identified during synergy check).
- AC-7.2: The step-by-step process includes a timeline for advice gathering with clear start and end dates.
- AC-7.3: The output artifact is an advice log documenting each input received and the proposer's response.
- AC-7.4: The failure containment logic addresses what happens when impacted parties do not respond within the advice window.
- AC-7.5: An OmniOne walkthrough demonstrates the Advice phase for a proposal to change meeting facilitation protocols in the TH.
- AC-7.6: All 7 stress-test scenarios documented.

**Priority:** P0 -- First phase of ACT.

#### FR-8: ACT Consent Phase (`act-consent-phase`)

**Description:** Run the Consent phase of the ACT process. The proposal (informed by advice) is presented to the deciding body. Members may consent, stand aside, or raise a reasoned objection. Objections must be grounded in harm to the circle's aim. The facilitator integrates objections by modifying the proposal to find a "third solution." For OSC-level or Master Plan decisions, full consensus is required instead of consent.

**Acceptance Criteria:**
- AC-8.1: The skill defines the consent threshold (no reasoned objections for standard decisions; active agreement from all members for OSC/Master Plan decisions).
- AC-8.2: The step-by-step process includes objection integration rounds with a defined maximum iteration count before escalation.
- AC-8.3: The output artifact records each member's position (consent, stand-aside with reason, objection with reason) and the final amended proposal.
- AC-8.4: The authority boundary check prevents the facilitator from overriding objections or declaring false consent.
- AC-8.5: The capture resistance check addresses charismatic leaders pressuring members to withdraw valid objections.
- AC-8.6: An OmniOne walkthrough demonstrates the Consent phase for a resource allocation proposal in the AE, including one objection that leads to proposal modification.
- AC-8.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Core decision mechanism.

#### FR-9: ACT Test Phase (`act-test-phase`)

**Description:** Run the Test phase of the ACT process. The consented proposal is implemented on a reversible, time-limited basis. A review date is set at the start. At review, the test is evaluated against success criteria defined in the proposal. The outcome is: adopt permanently, extend the test, modify and re-test, or revert.

**Acceptance Criteria:**
- AC-9.1: The skill defines the test parameters (duration, success criteria, review body, revert procedure).
- AC-9.2: The step-by-step process includes a midpoint check-in for long-duration tests.
- AC-9.3: The output artifact is a test report documenting what happened, whether success criteria were met, and the review body's decision.
- AC-9.4: The failure containment logic defines automatic revert if the review does not occur by the test expiry date.
- AC-9.5: The exit compatibility check addresses what happens if 30% of participants exit during a test period.
- AC-9.6: An OmniOne walkthrough demonstrates a 90-day test of a new resource distribution formula.
- AC-9.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Completes the ACT cycle.

#### FR-10: Proposal Resolution (`proposal-resolution`)

**Description:** Resolve proposals through the GAIA 6-level escalation when standard ACT phases do not achieve resolution. This skill orchestrates escalation from Level 1 (in-circle consensus) through Level 6 (value decision model) and defines the handoff criteria between levels.

**Acceptance Criteria:**
- AC-10.1: The skill defines the trigger conditions for each escalation level (what must fail at the current level to trigger the next).
- AC-10.2: The step-by-step process maps each GAIA level to specific actions, responsible parties, and timelines.
- AC-10.3: The output artifact at Level 6 is a Decision Resolution Record showing the value comparison chart and the final determination.
- AC-10.4: The authority boundary check prevents any single level from being skipped except by consent of all affected parties.
- AC-10.5: The capture resistance check addresses the risk of powerful individuals forcing rapid escalation to bypass lower-level consent.
- AC-10.6: An OmniOne walkthrough demonstrates a contentious proposal that escalates from Level 3 through Level 5 before resolution.
- AC-10.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on FR-7, FR-8, FR-9 existing.

#### FR-11: Consensus Check (`consensus-check`)

**Description:** Verify whether consensus exists among affected parties. This is a utility skill used by other skills (especially agreement-amendment for UAF changes, and proposal-resolution at GAIA Level 1). It defines the mechanics of checking for consensus vs. consent, recording the result, and handling edge cases (absent members, abstentions, conditional agreement).

**Acceptance Criteria:**
- AC-11.1: The skill defines both consensus mode and consent mode with clear structural differences.
- AC-11.2: The step-by-step process handles: full attendance, partial attendance with quorum, absent members with proxy, and absent members without proxy.
- AC-11.3: The output artifact is a Consensus/Consent Record with each participant's position and the determination.
- AC-11.4: The failure containment logic defines the fallback when consensus cannot be reached (escalation to next GAIA level).
- AC-11.5: An OmniOne walkthrough demonstrates the OSC running a consensus check on a proposed UAF amendment.
- AC-11.6: All 7 stress-test scenarios documented.

**Priority:** P1 -- Utility skill referenced by others.

---

## Non-Functional Requirements

#### NFR-1: Modularity

Each skill must function independently. A participant or AI agent reading a single SKILL.md must be able to understand and execute the described process without requiring other SKILL.md files to be loaded. Skills may reference each other by name but must not depend on another skill being "installed."

#### NFR-2: Line Limit

Each SKILL.md must be under 500 lines. This forces precision and prevents bloat. Supporting material goes in `references/` or `assets/`.

#### NFR-3: Portability

Every skill is NEOS-generic at its structural level. OmniOne-specific details appear as clearly marked examples, defaults, or configuration blocks. Another ecosystem must be able to fork and replace the example blocks with their own configuration.

#### NFR-4: No Hidden Authority

If a step in any skill requires someone to make a judgment call, that person's authority scope must be explicitly stated. No "the administrator decides" without defining the administrator's domain, appointment process, and review cycle.

#### NFR-5: Reversibility Default

All skills must prefer reversible actions. Irreversible actions (such as permanent agreement sunset or permanent participant removal) require higher consent thresholds, which must be stated in the authority boundary check.

#### NFR-6: Expiry by Default

All agreements, authority expansions, and test implementations must have a review date. The skill must define what happens if the review date passes without action.

#### NFR-7: Validation

Every SKILL.md must pass automated validation via `scripts/validate_skill.py`. The validator checks: YAML frontmatter presence and required fields, all 12 sections (A-L) present with substantive content, OmniOne walkthrough present, all 7 stress-test scenarios present.

---

## User Stories

### US-1: Ecosystem Architect Creates an Agreement
**As** an ecosystem architect configuring NEOS for a new community,
**I want** a clear, step-by-step process for creating a binding agreement,
**So that** I can establish the governance foundation without relying on informal authority.

**Given** the architect has identified a need for a new space agreement,
**When** they follow the agreement-creation skill process,
**Then** a versioned agreement document is produced, registered, and traceable.

### US-2: AI Agent Navigates a Decision
**As** an AI agent assisting a participant,
**I want** to determine which ACT phase a proposal is in and what the next required action is,
**So that** I can guide the participant through the correct process step.

**Given** a proposal exists in the system with a recorded status,
**When** the AI agent reads the proposal-creation and relevant ACT phase skills,
**Then** it can identify the current phase, the required participants, and the next action.

### US-3: Participant Proposes a Change
**As** a TH member who believes a process is unfair,
**I want** to submit a formal proposal to change that process,
**So that** my concern is addressed through legitimate structural channels rather than informal lobbying.

**Given** the participant has a specific process change in mind,
**When** they follow the proposal-creation skill to draft and submit,
**Then** the proposal enters the Advice phase with all impacted parties identified.

### US-4: OSC Amends the Universal Agreement Field
**As** the OSC responding to ecosystem growth,
**I want** to amend the UAF to address a gap identified through experience,
**So that** the root agreement evolves with the ecosystem.

**Given** the OSC has identified a UAF gap,
**When** they follow the agreement-amendment skill with UAF-specific requirements,
**Then** the amendment reaches consensus among all OSC members and is versioned in the registry.

### US-5: Participant Queries Active Agreements
**As** a new ecosystem participant completing onboarding,
**I want** to see all agreements that apply to my roles and spaces,
**So that** I know exactly what I have consented to.

**Given** the participant has been assigned roles and spaces,
**When** they query the agreement registry by their identity,
**Then** they receive a list of all active agreements with links to full text.

### US-6: Facilitator Runs a Consent Round
**As** a circle facilitator running a decision meeting,
**I want** clear instructions for conducting the consent phase,
**So that** I can integrate objections fairly and reach a legitimate outcome.

**Given** a proposal has completed the Advice phase,
**When** the facilitator follows the act-consent-phase skill,
**Then** each member's position is recorded, objections are integrated, and the outcome is documented.

### US-7: Ecosystem Handles a Stalled Proposal
**As** a proposer whose proposal has stalled at GAIA Level 3,
**I want** to understand the escalation path and what triggers the next level,
**So that** I can either resolve at the current level or escalate properly.

**Given** the proposal has received conflicting advice that cannot be reconciled,
**When** the proposer reads the proposal-resolution skill,
**Then** they understand the criteria for escalation to Level 4 (Coaching) and the process at that level.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-01-agreement/
    README.md
    agreement-creation/
      SKILL.md
      assets/
        agreement-template.yaml
      references/
    agreement-amendment/
      SKILL.md
      assets/
      references/
    agreement-review/
      SKILL.md
      assets/
      references/
    agreement-registry/
      SKILL.md
      assets/
        registry-schema.yaml
      references/
    universal-agreement-field/
      SKILL.md
      assets/
        uaf-template.md
      references/
  layer-03-act-engine/
    README.md
    act-advice-phase/
      SKILL.md
      assets/
        advice-log-template.yaml
      references/
    act-consent-phase/
      SKILL.md
      assets/
        consent-record-template.yaml
      references/
    act-test-phase/
      SKILL.md
      assets/
        test-report-template.yaml
      references/
    proposal-creation/
      SKILL.md
      assets/
        proposal-template.yaml
      references/
    proposal-resolution/
      SKILL.md
      assets/
        decision-resolution-template.yaml
      references/
    consensus-check/
      SKILL.md
      assets/
        consensus-record-template.yaml
      references/
scripts/
  validate_skill.py
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name          # kebab-case, matches directory name
description: "..."        # Pushy description that errs toward triggering
layer: 1                  # Integer layer number
version: 0.1.0            # Semver
depends_on: []            # List of skill names this skill references
---
```

### Validation Script Requirements

`scripts/validate_skill.py` must:
- Accept a path to a SKILL.md file (or a directory to scan recursively)
- Validate YAML frontmatter contains required fields (name, description, layer, version, depends_on)
- Validate all 12 sections (A through L) are present with substantive content (not just headers)
- Validate OmniOne walkthrough section exists
- Validate all 7 stress-test scenarios are present
- Output pass/fail with specific failure reasons
- Exit code 0 for pass, 1 for fail
- Use only Python stdlib (no external dependencies)

### Interleaving Strategy

Skills are built in this order to ground cross-references:
1. `agreement-creation` (Layer I anchor) -- establishes what an agreement looks like
2. `proposal-creation` (Layer III anchor) -- establishes what a proposal looks like
3. `universal-agreement-field` (Layer I) -- the root agreement, references agreement-creation
4. `act-advice-phase` (Layer III) -- first ACT phase
5. `act-consent-phase` (Layer III) -- second ACT phase, references consensus-check concepts
6. `act-test-phase` (Layer III) -- third ACT phase, completes the cycle
7. `agreement-amendment` (Layer I) -- modifying agreements, references full ACT cycle
8. `consensus-check` (Layer III) -- utility skill, references consent phase
9. `agreement-review` (Layer I) -- review cycle, references amendment and registry
10. `agreement-registry` (Layer I) -- registry, references all agreement skills
11. `proposal-resolution` (Layer III) -- GAIA escalation, references all ACT phases

---

## Source Concepts Deferred

The following concepts from the OmniOne source documents are explicitly **not** in this track. Each is mapped to the layer that will formalize it. Skills in this track may reference these concepts provisionally but must not depend on them structurally.

| Concept | Source | Deferred To | Notes |
|---------|--------|-------------|-------|
| Current-Sees (111 influence currencies) | OMNI ONE Foundational Docs | Layer IV (Economic Coordination) | ACT skills should note extensibility points where Current-See weighting could modify consent thresholds |
| Inactive Member Protocol (1-month rule) | Field Agreement Example | Layer II (Authority & Role, member-lifecycle) | Consent/consensus quorum calculations in this track assume all registered members are active |
| Removal Protocol ("all but one by consensus") | Field Agreement Example | Layer VI (Conflict & Repair) | This track does not define involuntary removal; exit is always voluntary here |
| IP Framework (original/emergent/shared works) | Field Agreement Example | Layer IV (Economic Coordination) | UAF references IP categories from field agreement but does not define the full framework |
| Solutionary Culture methodology | OMNI ONE Foundational Docs | Layer VI (Conflict & Repair) | Referenced in ACT coaching (GAIA Level 4) but not formally defined |
| NEXUS onboarding process | OMNI ONE Foundational Docs | Layer II (Authority & Role, member-lifecycle) | UAF walkthrough references onboarding but does not define the full process |
| Trunk Council transition | OMNI ONE Foundational Docs | OmniOne configuration | Not NEOS core; ecosystem-specific governance transition |
| Lawful Formation alternative | OMNI ONE Foundational Docs | Open Question (OQ-12) | Alternative decision path mentioned in source; relationship to ACT undefined |

### Terminology Notes

- **ETHOS**: Used in OmniOne source docs as the term for an organizational unit's agreement field. In NEOS-generic context, this maps to "ETHOS Agreement Field." Skills should use the NEOS-generic term with OmniOne's "ETHOS" noted in the example blocks.
- **Moneyless Society**: Predecessor organization referenced in `fieldagreementexample.md`. OmniOne skills should acknowledge this lineage where relevant but not depend on it structurally.

### Agreement Hierarchy (Load-Bearing)

The following hierarchy from the source documents defines which agreements override which. This hierarchy **is** in scope for this track and must be embedded in the `universal-agreement-field` skill (FR-5) and referenced by `agreement-creation` (FR-1) and `agreement-registry` (FR-4):

```
Universal Agreement Field (UAF)
  └── Ecosystem Agreement (e.g., OmniOne Master Plan)
       └── Access Agreement (e.g., SHUR space agreement)
            └── Stewardship Agreement (e.g., role-specific commitments)
                 └── ETHOS Agreement Field (organizational unit agreements)
                      └── Culture Code (circle-internal norms)
                           └── Personal Commitments
```

**Rule:** No agreement at a lower level may contradict an agreement at a higher level. Conflicts are resolved upward: the higher-level agreement prevails until formally amended through its own ACT process.

---

## Out of Scope

- **Layer II (Authority and Role)** -- Deferred to the next track. This track assumes authority scopes are stated inline within each skill rather than referencing a formal authority layer. See "Provisional Authority Assumptions" below.
- **Layer IX (Memory and Traceability)** -- Deferred. This track produces output artifacts but does not define the versioning and search infrastructure.
- **Software implementation** -- NEOS is a governance specification, not a software application. No databases, APIs, or UIs are in scope.
- **Space agreements** -- The UAF skill defines the organizational agreement field. Individual space agreements are configuration, not core skills.
- **OmniOne-specific policy decisions** -- The skills define the process for making decisions, not the decisions themselves.

---

## Provisional Authority Assumptions

Until Layer II (Authority & Role) is built, all 11 skills in this track use the following provisional authority model. Layer II will formalize and may amend these assumptions; at that point, all 11 skills must be updated (this is tracked as Phase 5 of the authority_role track).

| Authority Scope | Who Holds It | Review/Appointment |
|----------------|-------------|-------------------|
| Circle-internal decisions | All active members of the circle | Membership defined by current participant roster |
| Cross-circle decisions | Representatives from each affected circle | Representatives selected by their circles |
| Ecosystem-level decisions | OSC (OMNI Steward Council in OmniOne) | OSC composition defined by ecosystem founding docs |
| UAF amendments | OSC by consensus | Cannot be delegated |
| Facilitation | Any trained member, rotated per meeting | Circle selects; facilitator has process authority only, not decision authority |
| Registry stewardship | Designated steward role | Appointed by consent of the body the registry serves |
| Emergency authority | Provisionally: any 3 circle members acting jointly | Formalized in Layer VIII |

**Constraint:** No authority scope in this track is permanent. Every scope stated above is subject to review at the interval defined in the relevant skill's Section J (Expiry / Review Condition).

---

## Provisional Emergency Expediting Rules

Stress-test scenarios (especially Emergency Crisis and Sudden Exit of 30%) require provisions for expedited decision-making. Layer VIII (Emergency Handling) will formalize the full emergency governance framework. Until then, skills in this track use these provisional minimums:

| Parameter | Normal | Emergency (Provisional) |
|-----------|--------|------------------------|
| Advice window | 7 days | 24 hours |
| Consent quorum | 2/3 of affected parties | Cannot go below 50% even in emergency |
| Maximum integration rounds | 3 | 2 |
| Auto-revert window | Per test phase duration | 30 days maximum; auto-reverts to pre-emergency state |
| Who can declare emergency | Not defined in this track | Provisionally: any 3 circle members acting jointly, ratified by relevant council within 48 hours |

**Constraint:** Emergency expediting cannot bypass consent entirely. Even at maximum compression, a formal consent round must occur. Any decision made under emergency expediting is automatically flagged for post-emergency review when Layer VIII is available.

---

## Open Questions

1. **OQ-1: Quorum for consent decisions**: What is the minimum participation threshold for a consent round to be valid? The source docs do not specify a number. Recommendation: define per agreement type in the agreement-creation asset template, with a default of 2/3 of affected parties present.

2. **OQ-2: Proxy voting in consensus checks**: Can an absent OSC member delegate their consensus position to another member? The source docs are silent. Recommendation: no proxy for consensus (too high stakes), proxy allowed for consent with written delegation.

3. **OQ-3: Cross-ecosystem agreement federation**: When two ecosystems both running NEOS need to form an agreement, which registry holds it? Deferred to Layer V (Inter-Unit Coordination), but the agreement-registry skill should note the extensibility point.

4. **OQ-4: Digital vs. physical agreement signing**: The skills describe the governance process but not the medium of consent recording. Should skills specify acceptable formats (digital signature, recorded verbal consent, physical signature)? Recommendation: leave medium-agnostic in NEOS core, let ecosystem configuration specify.

5. **OQ-5: Agreement hierarchy conflict resolution**: When a lower-level agreement is discovered to contradict a higher-level agreement (see Agreement Hierarchy above), what is the resolution mechanism? Options: (a) lower agreement is automatically suspended pending amendment, (b) lower agreement remains active with a conflict flag until formally resolved through ACT, (c) registry raises a blocking alert. Recommendation: option (b) with mandatory resolution timeline.

6. **OQ-6: Current-See integration with ACT**: Should the ACT consent/consensus skills define extensibility points where Current-See weighting could modify voting weight or quorum thresholds? This is deferred to Layer IV but the structural hooks should be present in this track. Recommendation: add a `weighting_model: equal | configurable` field to the consent record template with default `equal`.

7. **OQ-7: Emergency expediting authority**: Who has the authority to invoke emergency timelines? The provisional rules above suggest "any 3 circle members acting jointly" but this is a placeholder. Layer VIII will formalize; this track should state the provisional rule clearly in each stress test.

8. **OQ-8: Inactive member threshold**: The source docs specify a 1-month inactivity threshold for member status change. Should consent/consensus quorum calculations in this track exclude inactive members? Recommendation: yes, with the definition of "inactive" deferred to Layer II (member-lifecycle).

9. **OQ-9: Agreement language standard**: The OmniOne field agreement uses "I agree to..." personal commitment format. Should the NEOS-generic UAF template mandate this format, or allow ecosystems to choose their own voice? Recommendation: mandate first-person commitment format in the template as a structural choice (it reinforces personal agency), mark as configurable in the OmniOne example block.

10. **OQ-10: Synergy check scope and mechanism**: The synergy check at GAIA Level 3 checks whether a proposal conflicts with or duplicates active proposals. What defines the scope of the check (same circle? same domain? ecosystem-wide?) and who performs it? Recommendation: registry query by domain + human review by a designated synergy steward.

11. **OQ-11: Wisdom Council composition**: GAIA Level 5 may convene a Wisdom Council. Who sits on it? How are they selected? The source docs do not specify. Recommendation: defer detailed composition to Layer II (role-assignment) but state that Wisdom Council members must not be parties to the proposal under review.

12. **OQ-12: "Lawful Formation" alternative decision path**: The source material references a "Lawful Formation" as an alternative to the standard ACT process. Its relationship to the 6-level GAIA model is unclear. Recommendation: document as a known concept requiring clarification from the ecosystem architect before implementation.

13. **OQ-13: "Preference Decisions" vs "Solution Decisions" distinction**: The source material distinguishes between decisions that are matters of preference (no structural impact) and decisions that require structural solutions. Should this distinction be formalized in proposal-creation as a routing criterion? Recommendation: yes, add a `decision_type: preference | solution` field to the proposal template that determines minimum ACT level required.
