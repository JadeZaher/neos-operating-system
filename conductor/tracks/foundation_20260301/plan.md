# Implementation Plan: Foundation -- Agreement Layer + ACT Decision Engine

## Overview

This plan builds 11 governance skills across 2 NEOS layers plus a global validation tool, organized into 6 phases. The interleaved build order ensures that cross-references between Layer I (Agreement) and Layer III (ACT Engine) are grounded in already-written skills rather than forward references.

**Total skills:** 11 (5 in Layer I, 6 in Layer III)
**Total phases:** 6
**Estimated scope:** 30-40 hours of focused implementation

### Build Order Rationale

Layer I and Layer III are co-dependent. Agreements are created through ACT decisions; ACT decisions produce agreements. Rather than building one layer fully before the other, we interleave: start with one anchor skill from each layer, then alternate so each new skill can reference concrete, already-written skills.

### Commit Strategy

- One commit per completed skill: `neos(layer-XX): Add <skill-name> skill`
- Layer-level commits when all skills in a layer are done: `neos(layer-XX): Complete layer XX - <layer-name>`
- Validation script commit: `neos(scripts): Add validate_skill.py`

---

## Phase 1: Tooling and Scaffolding

**Goal:** Create the directory structure, build the global validation script, and establish the SKILL.md template so all subsequent phases have a quality gate.

### Tasks

- [x] **Task 1.1: Create directory scaffolding**
  Create the full `neos-core/` directory tree as specified in the tech-stack:
  ```
  neos-core/
    layer-01-agreement/
      agreement-creation/  (SKILL.md, assets/, references/, scripts/)
      agreement-amendment/ (same structure)
      agreement-review/    (same structure)
      agreement-registry/  (same structure)
      universal-agreement-field/ (same structure)
    layer-03-act-engine/
      act-advice-phase/    (same structure)
      act-consent-phase/   (same structure)
      act-test-phase/      (same structure)
      proposal-creation/   (same structure)
      proposal-resolution/ (same structure)
      consensus-check/     (same structure)
  scripts/
  ```
  Each skill directory gets empty `SKILL.md`, empty `assets/`, `references/`, and `scripts/` subdirectories. Layer directories get empty `README.md` files.
  **Acceptance:** All directories exist. `find neos-core -name SKILL.md | wc -l` returns 11.

- [x] **Task 1.2: Write validate_skill.py -- define test cases first (TDD Red)**
  Before writing the validator, write a test file `scripts/test_validate_skill.py` that defines the expected behavior:
  - Test: valid SKILL.md with all sections passes validation
  - Test: SKILL.md missing YAML frontmatter fails with specific error
  - Test: SKILL.md missing required frontmatter field (name, description, layer, version, depends_on) fails
  - Test: SKILL.md missing any of the 12 sections (A-L) fails with the missing section identified
  - Test: SKILL.md with empty section (header only, no content) fails
  - Test: SKILL.md missing OmniOne walkthrough fails
  - Test: SKILL.md missing any of the 7 stress-test scenarios fails
  - Test: validator accepts a directory path and recursively finds all SKILL.md files
  - Test: validator returns exit code 0 on pass, 1 on fail
  Create a `scripts/fixtures/` directory with `valid_skill.md` and several `invalid_*.md` test fixtures.
  **Acceptance:** Test file runs, all tests fail (Red).

- [x] **Task 1.3: Implement validate_skill.py (TDD Green)**
  Write `scripts/validate_skill.py` using only Python stdlib. The validator must:
  - Parse YAML frontmatter (between `---` delimiters)
  - Check required frontmatter fields: `name` (string), `description` (string), `layer` (int), `version` (string matching semver pattern), `depends_on` (list)
  - Scan for all 12 section headers (A through L) using the canonical titles:
    - A. Structural Problem It Solves
    - B. Domain Scope
    - C. Trigger Conditions
    - D. Required Inputs
    - E. Step-by-Step Process
    - F. Output Artifact
    - G. Authority Boundary Check
    - H. Capture Resistance Check
    - I. Failure Containment Logic
    - J. Expiry / Review Condition
    - K. Exit Compatibility Check
    - L. Cross-Unit Interoperability Impact
  - Check each section has at least 3 lines of content below its header (not just the header)
  - Scan for "OmniOne Walkthrough" or "OmniOne Example" section
  - Scan for all 7 stress-test scenario names (Capital Influx, Emergency Crisis, Leadership Charisma Capture, High Conflict / Polarization, Large-Scale Replication, External Legal Pressure, Sudden Exit of 30%)
  - Accept CLI arguments: `python validate_skill.py <path>` where path is a SKILL.md file or directory
  - Print structured output: `PASS: <path>` or `FAIL: <path> -- <reason1>, <reason2>, ...`
  - Exit 0 if all files pass, 1 if any fail
  **Acceptance:** All tests from Task 1.2 pass (Green).

- [x] **Task 1.4: Refactor validate_skill.py (TDD Refactor)**
  Review the validator for:
  - Clean function decomposition (separate functions for frontmatter validation, section validation, stress-test validation)
  - Helpful error messages that tell the author exactly what to fix
  - Consistent output format
  - Add a `--verbose` flag that shows all checks performed, not just failures
  **Acceptance:** All tests still pass. Code is clean and well-structured.

- [x] **Task 1.5: Create SKILL.md template**
  Write a template file at `neos-core/SKILL_TEMPLATE.md` that contains:
  - YAML frontmatter with placeholder values
  - All 12 section headers (A-L) with brief guidance comments under each
  - OmniOne Walkthrough section with guidance
  - Stress-Test Results section with all 7 scenario headers
  This template is the starting point for every skill implementation.
  **Acceptance:** Template passes `validate_skill.py` when placeholder guidance is treated as content.

- [x] **Verification 1: Run validate_skill.py against template, confirm pass. Run against empty SKILL.md files, confirm fail with helpful messages.** [checkpoint marker]

---

## Phase 2: Anchor Skills

**Goal:** Build the two anchor skills that define the fundamental shapes: what an agreement looks like (agreement-creation) and what a proposal looks like (proposal-creation). All subsequent skills reference these.

### Tasks

- [x] **Task 2.1: Draft agreement-creation SKILL.md -- sections A through F**
  **Source docs to load:** `EcoSystemPlanTempalte.md`, `conductor/product.md` (agreement types), `conductor/product-guidelines.md` (terminology).
  Using the template, fill in the first 6 sections for `agreement-creation`:
  - **A. Structural Problem It Solves:** Without a formal creation process, agreements emerge informally and unevenly. This skill ensures every agreement has a traceable origin, defined scope, and legitimate ratification.
  - **B. Domain Scope:** Any domain where binding commitments between participants are needed. Types: space agreements, access agreements, organizational agreement fields, UAF.
  - **C. Trigger Conditions:** A participant identifies a need for a new binding commitment that does not yet exist in the agreement registry.
  - **D. Required Inputs:** Proposer identity, agreement type, affected parties, domain scope, proposed text, proposed expiry/review date, rationale.
  - **E. Step-by-Step Process:** Draft, synergy check, route to appropriate ACT level, advice phase, consent phase, test phase (if applicable), ratification, registration.
  - **F. Output Artifact:** Versioned agreement document with unique ID, full text, ratification record, review date, status.
  Write with full substance -- no placeholders. Use active voice per product guidelines.
  **Acceptance:** Sections A-F are substantive (3+ lines each), terminology matches product-guidelines.md.

- [x] **Task 2.2: Draft agreement-creation SKILL.md -- sections G through L**
  Complete the remaining structural sections:
  - **G. Authority Boundary Check:** No individual can unilaterally create binding agreements outside their domain. Circle-internal agreements require circle consent. Cross-circle agreements require consent from all affected circles. Ecosystem-level agreements require OSC consensus.
  - **H. Capture Resistance Check:** Address capital influx (wealthy donor conditioning participation on favorable agreement terms), charismatic capture (leader pushing agreements without proper process), emergency capture (crisis used to rush agreements).
  - **I. Failure Containment Logic:** What happens when: consent fails (proposal returns to advice), quorum is not met (extend timeline, do not lower threshold), agreement text is ambiguous (mandatory clarification round before ratification).
  - **J. Expiry / Review Condition:** Default review intervals by type: space agreements (annual), access agreements (6 months), organizational agreement fields (2 years), UAF (annual review, never auto-expires).
  - **K. Exit Compatibility Check:** When a participant exits, their obligations under agreements cease except for: stewarded asset return, in-progress commitment completion (30-day wind-down), and any exit-specific clauses in the agreement itself.
  - **L. Cross-Unit Interoperability Impact:** Agreements created in one AZPO that affect another AZPO trigger cross-unit notification. The affected AZPO must consent through their own ACT process.
  **Acceptance:** Sections G-L are substantive and structurally precise.

- [x] **Task 2.3: Write agreement-creation OmniOne walkthrough**
  Write a full narrative walkthrough:
  - Scenario: A TH member proposes a new space agreement for the Bali SHUR co-living kitchen.
  - Walk through: trigger (kitchen conflicts), drafting (proposer writes terms), synergy check (checks if a kitchen agreement already exists), advice phase (consults all SHUR residents), one resident raises a concern about quiet hours, proposer modifies, consent phase (circle consents with one stand-aside), ratification, registration.
  - Include an edge case: a non-resident AE member who uses the kitchen occasionally -- do they get consulted? (Yes, as an impacted party.)
  - End with the output artifact: the completed agreement document snippet.
  **Acceptance:** Walkthrough names specific roles, shows complete flow, includes edge case, ends with artifact.

- [x] **Task 2.4: Write agreement-creation stress-test results (all 7 scenarios)**
  Write full narrative stress tests (not brief summaries):
  1. **Capital Influx:** A donor offers $500K contingent on a specific agreement being created that favors their interests. Walk through how the skill's authority boundary check and capture resistance prevent this. The agreement still goes through full ACT process; the funding condition is flagged as a capture risk.
  2. **Emergency Crisis:** A natural disaster hits the SHUR and temporary shelter agreements are needed within 24 hours. Walk through expedited timeline provisions while maintaining consent integrity.
  3. **Leadership Charisma Capture:** A charismatic leader pushes a new agreement through by framing objections as "blocking progress." Walk through how the consent phase structurally protects objectors.
  4. **High Conflict / Polarization:** Two factions want mutually exclusive agreement terms. Walk through how the coaching escalation (GAIA Level 4) finds third solutions.
  5. **Large-Scale Replication:** The ecosystem grows from 50 to 5,000 members. Walk through how agreement creation scales (domain-scoped creation, not ecosystem-wide consent for local agreements).
  6. **External Legal Pressure:** A government demands the ecosystem create an agreement that contradicts NEOS principles. Walk through the sovereignty boundary and how the skill handles external mandates.
  7. **Sudden Exit of 30%:** Nearly a third of participants leave. Walk through how existing agreements remain valid, review is triggered, and quorum thresholds adapt.
  **Acceptance:** Each scenario is a full narrative paragraph (5+ sentences), not a bullet-point summary.

- [x] **Task 2.5: Finalize agreement-creation SKILL.md and create assets**
  - Assemble SKILL.md from Tasks 2.1-2.4 with proper YAML frontmatter:
    ```yaml
    ---
    name: agreement-creation
    description: "Create a new binding agreement -- space agreement, access agreement, agreement field, or UAF -- through a structured, consent-based process that prevents unilateral imposition and ensures traceability."
    layer: 1
    version: 0.1.0
    depends_on: []
    ---
    ```
  - Create `assets/agreement-template.yaml` defining the agreement document schema:
    ```yaml
    agreement_id: ""
    type: ""  # space | access | organizational | uaf
    title: ""
    version: "1.0.0"
    status: draft | advice | consent | test | active | sunset
    proposer: ""
    affected_parties: []
    domain: ""
    created_date: ""
    ratification_date: ""
    review_date: ""
    sunset_date: ""
    text: ""
    ratification_record: []
    amendment_history: []
    ```
  - Run `validate_skill.py` against the completed SKILL.md.
  **Acceptance:** SKILL.md passes validation. Under 500 lines. Asset template is complete.

- [x] **Task 2.6: Draft proposal-creation SKILL.md -- full skill (sections A-L)**
  **Source docs to load:** `ACT Sense Making Process.docx` (GAIA levels, synergy check, coaching), `conductor/tracks/foundation_20260301/spec.md` (GAIA model, Provisional Emergency Rules, OQ-10 synergy check, OQ-13 preference vs solution decisions).
  Build the complete `proposal-creation` skill in a single task (second anchor, pattern is established):
  - **A:** Without formal proposals, changes happen through informal influence. This skill ensures every proposed change has a clear author, rationale, affected scope, and enters a legitimate decision process.
  - **B:** Any domain where a change to existing agreements, processes, resources, or structure is proposed.
  - **C:** A participant identifies a need for change that cannot be resolved through existing agreements or circle-internal culture code.
  - **D:** Proposer identity, proposal type (EcoPlan, GenPlan, amendment, resource request, policy change), affected domain, proposed change text, rationale, identified impacted parties, urgency level, desired timeline.
  - **E:** Draft proposal, synergy check (GAIA Level 3 -- is this already being addressed? Does it conflict with active proposals?), route to appropriate ACT level based on scope, enter advice phase.
  - **F:** Numbered, versioned proposal document with status tracking.
  - **G-L:** Full structural sections following the same depth as agreement-creation.
  Include YAML frontmatter with `depends_on: []`.
  **Acceptance:** All 12 sections substantive. Under 500 lines (before walkthrough and stress tests).

- [x] **Task 2.7: Write proposal-creation OmniOne walkthrough and stress tests**
  - Walkthrough: A Builder proposes creating a new Economics circle within the AE. Show the full flow from identifying the need, drafting the proposal, synergy check (discovering a related proposal from another Builder), combining forces, submitting, and entering the advice phase. Edge case: the proposal affects both AE and TH domains -- how is dual-domain routing handled?
  - All 7 stress tests as full narratives, each specific to proposal creation.
  **Acceptance:** Walkthrough + stress tests complete. Full SKILL.md passes validation.

- [x] **Task 2.8: Create proposal-creation assets**
  Create `assets/proposal-template.yaml`:
  ```yaml
  proposal_id: ""
  type: ""  # ecoplan | genplan | amendment | resource_request | policy_change
  title: ""
  version: "1.0.0"
  status: draft | synergy_check | advice | consent | test | adopted | reverted | withdrawn
  proposer: ""
  affected_domain: ""
  impacted_parties: []
  urgency: normal | elevated | emergency
  proposed_change: ""
  rationale: ""
  created_date: ""
  advice_deadline: ""
  consent_deadline: ""
  test_duration: ""
  related_proposals: []
  advice_log: []
  consent_record: []
  test_report: {}
  ```
  **Acceptance:** Template is complete and referenced in SKILL.md.

- [x] **Verification 2: Run validate_skill.py against both completed skills. Confirm both pass. Review cross-references -- agreement-creation should reference "proposal-creation" by name where relevant, and vice versa.** [checkpoint marker]

---

## Phase 3: UAF and ACT Core Phases

**Goal:** Build the root agreement (UAF) and the three ACT phases (Advice, Consent, Test). After this phase, the complete ACT cycle is defined and the foundational agreement exists.

### Tasks

- [x] **Task 3.1: Draft universal-agreement-field SKILL.md -- sections A through F**
  **Source docs to load:** `fieldagreementexample.md` (real OmniOne field agreement — primary source for UAF structure and language), `conductor/tracks/foundation_20260301/spec.md` (Agreement Hierarchy section, AC-5.8, AC-5.9).
  - **A:** Without a root agreement, participants operate on assumed norms that vary by individual. The UAF makes baseline commitments explicit, equal, and traceable.
  - **B:** The entire ecosystem. The UAF applies to every participant regardless of role, circle, or AZPO.
  - **C:** New ecosystem formation, new participant onboarding, or periodic review of the existing UAF.
  - **D:** The ecosystem's founding values, the field agreement example document, the identified domains of commitment (accountability, processes, conflict, stewardship, sovereignty).
  - **E:** Draft from founding values, structured review by founding council, consent of all founding members (consensus mode for UAF), registration as agreement #001, onboarding integration.
  - **F:** The UAF document itself -- a versioned, structured agreement with sections covering all domains of participant commitment.
  Reference the OmniOne field agreement example as the concrete basis.
  **Acceptance:** Sections A-F complete, grounded in the real field agreement example.

- [x] **Task 3.2: Draft universal-agreement-field SKILL.md -- sections G through L**
  - **G:** Only OSC consensus can amend the UAF. No individual, no circle, no council below OSC can modify the root agreement. New participants consent to the UAF as a condition of entry; they do not negotiate it.
  - **H:** Capital capture (donor demands UAF weakening), charismatic capture (leader reinterprets UAF without formal amendment), emergency capture (crisis used to suspend UAF provisions). Each must be structurally blocked.
  - **I:** What happens when: a participant claims they did not understand a UAF provision (onboarding must include explicit consent checkpoint), a UAF provision conflicts with local law (the legal compliance clause takes precedence for that jurisdiction, the UAF provision is not suspended globally).
  - **J:** Annual review by OSC. The UAF never auto-expires. Missed review triggers escalation notice, not suspension.
  - **K:** When a participant exits, UAF obligations cease immediately except: stewarded asset return and in-progress commitment wind-down. The participant retains the right to take their original works.
  - **L:** When the ecosystem federates with another ecosystem, each ecosystem's UAF remains sovereign. Cross-ecosystem interactions are governed by inter-unit agreements, not by merging UAFs.
  **Acceptance:** Sections G-L complete, structurally precise, no hidden authority.

- [x] **Task 3.3: Write universal-agreement-field walkthrough and stress tests**
  - Walkthrough: A new member completes the NEXUS onboarding for OmniOne. They receive the UAF document. The onboarding facilitator walks through each section. The new member asks about the conflict resolution commitments -- what if they disagree with the process? The facilitator explains: consent to the UAF is consent to the process, not to every future outcome. The member signs. The registry records their consent. Edge case: a member later claims they were pressured into signing during onboarding -- the skill's consent record and cooling-off period address this.
  - All 7 stress tests, with special attention to Scenario 5 (Large-Scale Replication -- how does the UAF onboarding scale to 5,000 members?) and Scenario 7 (30% exit -- does the UAF need re-ratification?).
  **Acceptance:** Walkthrough + stress tests complete. Full narrative depth.

- [x] **Task 3.4: Create universal-agreement-field assets**
  **Source docs to load:** `fieldagreementexample.md` (direct basis for template — preserve section structure, generalize "I agree to..." commitments).
  Create `assets/uaf-template.md` -- a generalized UAF template derived from the OmniOne field agreement example:
  - Section 1: Agreements and Accountability (generalized from OmniOne example)
  - Section 2: Processes (generalized)
  - Section 3: Conflict (generalized)
  - Section 4: Stewardship and Contribution (generalized)
  - Section 5: Sovereignty and Evolution (generalized)
  - Section 6: Sovereignty, Freedom, and Responsibility (generalized)
  Each section has NEOS-generic commitments with `[ECOSYSTEM: OmniOne example]` blocks showing the OmniOne-specific language from the field agreement example.
  **Acceptance:** Template is structurally complete, OmniOne examples clearly marked, another ecosystem could fork and replace.

- [x] **Task 3.5: Finalize universal-agreement-field SKILL.md**
  Assemble with frontmatter:
  ```yaml
  ---
  name: universal-agreement-field
  description: "The root agreement every ecosystem participant consents to upon entry -- defines baseline commitments for accountability, processes, conflict, stewardship, and sovereignty that all other agreements inherit from."
  layer: 1
  version: 0.1.0
  depends_on: [agreement-creation]
  ---
  ```
  Run validation. Confirm under 500 lines.
  **Acceptance:** Passes validate_skill.py. Under 500 lines.

- [x] **Task 3.6: Draft act-advice-phase SKILL.md -- full skill**
  **Source docs to load:** `ACT Sense Making Process.docx` (advice process details, panel of experts), `conductor/tracks/foundation_20260301/spec.md` (Provisional Emergency Rules for compressed timelines).
  Build the complete Advice phase skill:
  - **A:** Without structured advice-gathering, decisions are made by whoever is in the room. This skill ensures all impacted voices are sought before consent is requested.
  - **B:** Any proposal that has passed synergy check and entered the ACT process.
  - **C:** A proposal enters the Advice phase (status transition from synergy_check to advice).
  - **D:** The proposal document, the list of impacted parties, the advice timeline.
  - **E:** Announce proposal to all impacted parties, open advice window (default: 7 days for normal, 3 days for elevated, 24 hours for emergency), collect input, proposer documents each piece of advice and their response (integrated, partially integrated with rationale, not integrated with rationale), close advice window, produce advice log.
  - **F:** Advice log with entries: advisor identity, advice text, proposer response, integration status.
  - **G-L:** Full structural sections.
  Walkthrough: TH proposal to change meeting facilitation protocols. One AE member gives advice that contradicts a TH member's advice. Proposer must document how both are addressed.
  Stress tests: all 7, full narratives.
  **Acceptance:** Passes validation. Under 500 lines.

- [x] **Task 3.7: Create act-advice-phase assets**
  Create `assets/advice-log-template.yaml`:
  ```yaml
  proposal_id: ""
  advice_window_start: ""
  advice_window_end: ""
  urgency: normal | elevated | emergency
  entries:
    - advisor: ""
      role: ""
      date: ""
      advice_text: ""
      proposer_response: ""
      integration_status: integrated | partially_integrated | not_integrated
      rationale: ""
  summary: ""
  ```
  **Acceptance:** Template complete and referenced in SKILL.md.

- [x] **Task 3.8: Draft act-consent-phase SKILL.md -- full skill**
  **Source docs to load:** `ACT Sense Making Process.docx` (consent mechanics, objection integration), `conductor/tracks/foundation_20260301/spec.md` (Consent vs Consensus section, Provisional Authority Assumptions, OQ-1 quorum, OQ-2 proxy).
  Build the complete Consent phase skill:
  - **A:** Without structured consent, decisions default to loudest voice or informal authority. This skill ensures every affected participant's position is recorded and objections are structurally integrated.
  - **B:** Any proposal that has completed the Advice phase.
  - **C:** Advice phase closes with completed advice log.
  - **D:** The proposal (as modified by advice integration), the advice log, the list of consent participants, the consent mode (consent or consensus).
  - **E:** Present final proposal, round 1 (each participant states: consent, stand-aside with reason, or objection with reason), if objections exist: integration round (facilitator works with objector and proposer to find third solution), round 2 with modified proposal, maximum 3 integration rounds before escalation to next GAIA level. For consensus mode: all must actively agree, no stand-asides.
  - **F:** Consent record documenting each participant's position and the outcome.
  - **G:** Facilitator cannot override objections or declare false consent. Facilitator's role is process stewardship, not decision authority. If facilitator has a stake, a neutral facilitator must be found.
  - **H:** Address charismatic pressure to withdraw objections, social punishment of objectors, "urgency" framing to skip integration rounds.
  - **I-L:** Full structural sections.
  Walkthrough: AE resource allocation proposal. One member objects because the proposal would reduce their circle's budget. Integration round finds a phased approach. Consent achieved on round 2.
  Stress tests: all 7 with particular attention to Scenario 4 (High Conflict).
  **Acceptance:** Passes validation. Under 500 lines. Consent vs. consensus modes clearly distinguished.

- [x] **Task 3.9: Create act-consent-phase assets**
  Create `assets/consent-record-template.yaml`:
  ```yaml
  proposal_id: ""
  consent_mode: consent | consensus
  facilitator: ""
  date: ""
  participants:
    - name: ""
      role: ""
      position: consent | stand_aside | objection
      reason: ""  # required for stand_aside and objection
  integration_rounds:
    - round_number: 1
      objections_addressed: []
      modifications_made: ""
  outcome: consented | consensus_reached | escalated
  final_proposal_version: ""
  ```
  **Acceptance:** Template complete.

- [x] **Task 3.10: Draft act-test-phase SKILL.md -- full skill**
  Build the complete Test phase skill:
  - **A:** Without structured testing, decisions become permanent by default. This skill ensures every consented change is implemented reversibly with a defined review point.
  - **B:** Any proposal that has achieved consent/consensus.
  - **C:** Consent phase completes with positive outcome.
  - **D:** The consented proposal, test duration, success criteria, review body, revert procedure.
  - **E:** Implement change on reversible basis, set start and end dates, set midpoint check-in for tests longer than 60 days, at review date: review body evaluates against success criteria, outcome options: adopt permanently (enters agreement registry), extend test (with new end date, max 1 extension), modify and re-test (returns to advice phase with modifications), revert (original state restored). If review date passes without action: automatic 30-day extension with escalation notice, then auto-revert.
  - **F:** Test report documenting implementation, observations, success criteria evaluation, review body decision.
  - **G-L:** Full structural sections.
  Walkthrough: 90-day test of a new resource distribution formula in OmniOne. Midpoint check-in reveals an issue with how emergency funds are allocated. Review body modifies and extends for 45 more days. Final review: adopted with one modification.
  Stress tests: all 7, full narratives.
  **Acceptance:** Passes validation. Under 500 lines. Auto-revert mechanism clearly defined.

- [x] **Task 3.11: Create act-test-phase assets**
  Create `assets/test-report-template.yaml`:
  ```yaml
  proposal_id: ""
  test_start_date: ""
  test_end_date: ""
  midpoint_checkin_date: ""
  success_criteria:
    - criterion: ""
      met: true | false
      evidence: ""
  review_body: []
  review_date: ""
  observations: ""
  outcome: adopt | extend | modify_retest | revert
  modifications: ""
  next_action: ""
  ```
  **Acceptance:** Template complete.

- [x] **Verification 3: Run validate_skill.py against all 6 completed skills (agreement-creation, proposal-creation, universal-agreement-field, act-advice-phase, act-consent-phase, act-test-phase). All must pass. Verify that the complete ACT cycle is coherent: a proposal can flow from creation through advice, consent, and test using only the defined skills. Check cross-references are accurate. Verify the agreement hierarchy from AC-5.8 is embedded in the UAF skill.** [checkpoint marker]

---

## Phase 4: Amendment, Consensus, and Review

**Goal:** Build the skills that modify existing agreements and provide the consensus-checking utility. After this phase, agreements can be changed and the full decision toolkit is available.

### Tasks

- [x] **Task 4.1: Draft agreement-amendment SKILL.md -- full skill**
  Build the complete amendment skill:
  - **A:** Without a formal amendment process, agreements either become stale (never updated) or are changed informally (no traceability). This skill ensures every modification has a clear scope, proper authorization, and full ACT process.
  - **B:** Any existing active agreement in the registry.
  - **C:** A participant identifies that an existing agreement needs modification (outdated terms, new circumstances, identified gaps, conflict with another agreement).
  - **D:** Amendment proposer, parent agreement ID, amendment type (minor clarification, substantive change, scope expansion, scope reduction), proposed changes (diff format: what was, what will be), rationale.
  - **E:** Classify amendment type, route to minimum ACT level (minor clarification: circle consent; substantive change: full ACT; scope expansion: full ACT + affected-party consent; UAF amendment: OSC consensus), run appropriate ACT phases, produce versioned amendment record, update registry.
  - **F:** Amendment record linked to parent agreement with version increment.
  - **G:** Amendment scope cannot exceed the amending body's domain. A circle cannot amend an ecosystem-level agreement. UAF amendments require OSC consensus. Amendment cannot create authority that the original agreement did not grant.
  - **H-L:** Full structural sections.
  Walkthrough: The AE proposes amending an existing ETHOS agreement field to add a new stewardship commitment. Walk through classification (substantive change), full ACT process, one objection during consent (the commitment is too vague), integration (specific language added), consent achieved, registry updated with version 1.1.0.
  Stress tests: all 7 with particular attention to Scenario 1 (Capital Influx -- donor pressures amendment to weaken accountability terms).
  **Acceptance:** Passes validation. Under 500 lines. Amendment types clearly mapped to ACT levels.

- [x] **Task 4.2: Create agreement-amendment assets**
  Create `assets/amendment-record-template.yaml`:
  ```yaml
  amendment_id: ""
  parent_agreement_id: ""
  parent_agreement_version: ""
  amendment_type: minor_clarification | substantive_change | scope_expansion | scope_reduction
  proposed_by: ""
  date: ""
  changes:
    - section: ""
      was: ""
      now: ""
  rationale: ""
  act_level_used: ""
  consent_record_id: ""
  new_agreement_version: ""
  status: proposed | in_process | ratified | rejected
  ```
  **Acceptance:** Template complete and referenced in SKILL.md.

- [x] **Task 4.3: Draft consensus-check SKILL.md -- full skill**
  Build the complete consensus-check utility skill:
  - **A:** Other skills reference "check for consent" or "verify consensus" without defining the mechanics. This skill provides the reusable procedure for determining whether a group agrees.
  - **B:** Any decision point in any skill that requires verification of group agreement.
  - **C:** Another skill or process requires a formal check of whether affected parties agree. Called by: act-consent-phase, agreement-amendment (for UAF), proposal-resolution.
  - **D:** The question or proposal being checked, the list of participants, the mode (consent or consensus), quorum requirements.
  - **E:** For consent mode: poll each participant (consent, stand-aside, objection), result is "consent achieved" if zero objections regardless of stand-asides, minimum 2/3 of affected parties must participate. For consensus mode: poll each participant (agree, disagree), result is "consensus achieved" only if all participants actively agree, no abstentions allowed, no proxy allowed. Handle edge cases: absent with notice (consent mode: counted as implicit consent if notified and did not respond within window; consensus mode: must be present or meeting is rescheduled), absent without notice (consent mode: not counted toward quorum; consensus mode: blocks consensus until contacted).
  - **F:** Consensus/Consent Record.
  - **G-L:** Full structural sections.
  Walkthrough: OSC running a consensus check on a proposed UAF amendment. 5 of 6 OSC members are present. The 6th is traveling. For consensus mode, the check cannot proceed -- the meeting is rescheduled. At the rescheduled meeting, all 6 are present. 5 agree, 1 has concerns. The concern is addressed through a modification. All 6 agree. Consensus achieved.
  Stress tests: all 7 with particular attention to Scenario 7 (30% exit -- how do quorum thresholds adapt when the participant pool shrinks?).
  **Acceptance:** Passes validation. Under 500 lines. Both modes clearly distinguished with different rules for absent members.

- [x] **Task 4.4: Create consensus-check assets**
  Create `assets/consensus-record-template.yaml`:
  ```yaml
  check_id: ""
  mode: consent | consensus
  question: ""
  date: ""
  quorum_required: ""
  quorum_met: true | false
  participants:
    - name: ""
      role: ""
      present: true | false
      position: consent | stand_aside | objection | agree | disagree | absent_with_notice | absent_without_notice
      reason: ""
  result: consent_achieved | consensus_achieved | not_achieved | quorum_not_met
  notes: ""
  ```
  **Acceptance:** Template complete.

- [x] **Task 4.5: Draft agreement-review SKILL.md -- full skill**
  Build the complete agreement review skill:
  - **A:** Without periodic review, agreements become stale, outdated, or misaligned with current conditions. This skill ensures every agreement is regularly re-validated and either renewed, revised, or sunset.
  - **B:** Any active agreement in the registry that has a review date.
  - **C:** Scheduled review date arrives, a participant requests early review, or a threshold event occurs (30% participant exit, major policy change, conflict arising from the agreement).
  - **D:** The agreement to be reviewed, current participant feedback, any conflicts or issues logged against the agreement, registry data on the agreement's usage and amendment history.
  - **E:** Convene review body (the same body that ratified the agreement, or their successors), evaluate against current conditions (Is the agreement still relevant? Are the terms still appropriate? Has the context changed?), determine outcome: renew as-is (set new review date), revise (trigger agreement-amendment skill with identified changes), sunset (trigger graceful deprecation with 60-day notice to all affected parties).
  - **F:** Review record documenting the evaluation, the outcome, and next actions.
  - **G-L:** Full structural sections.
  Walkthrough: Scheduled annual review of the SHUR Bali kitchen space agreement. 3 of 5 original ratifiers are still present, 2 have exited and been replaced by new residents. Review body includes current affected parties. Agreement is mostly working but one clause about quiet hours is generating friction. Outcome: revise -- triggers agreement-amendment for the quiet hours clause. New review date set for 1 year.
  Stress tests: all 7 with particular attention to Scenario 2 (Emergency Crisis -- can a review be triggered immediately during a crisis?) and Scenario 5 (Large-Scale Replication -- how does review scale when there are 500 active agreements?).
  **Acceptance:** Passes validation. Under 500 lines. Review outcomes clearly mapped to subsequent skill triggers.

- [x] **Task 4.6: Create agreement-review assets**
  Create `assets/review-record-template.yaml`:
  ```yaml
  review_id: ""
  agreement_id: ""
  agreement_version: ""
  review_type: scheduled | requested | threshold_event
  trigger: ""
  review_body: []
  date: ""
  evaluation:
    relevance: ""
    appropriateness: ""
    context_changes: ""
    conflicts_logged: []
  outcome: renew | revise | sunset
  next_review_date: ""
  follow_up_actions:
    - action: ""
      responsible: ""
      deadline: ""
  ```
  **Acceptance:** Template complete.

- [x] **Verification 4: Run validate_skill.py against all 8 completed skills. All must pass. Verify: agreement-amendment correctly references agreement-creation and ACT phases; consensus-check is referenced by act-consent-phase and agreement-amendment; agreement-review correctly triggers agreement-amendment for revisions.** [checkpoint marker]

---

## Phase 5: Registry and Resolution

**Goal:** Build the final two skills: the agreement registry (single source of truth) and proposal resolution (GAIA escalation). After this phase, all 11 skills are complete.

### Tasks

- [x] **Task 5.1: Draft agreement-registry SKILL.md -- full skill**
  Build the complete agreement registry skill:
  - **A:** Without a registry, participants cannot determine what agreements exist, which ones apply to them, or whether an agreement has been superseded. This skill provides the single source of truth for all agreements.
  - **B:** The entire ecosystem. The registry holds every active, sunset, and archived agreement.
  - **C:** An agreement is created, amended, reviewed, or sunset. Also triggered by participant queries.
  - **D:** For writes: output artifacts from agreement-creation, agreement-amendment, agreement-review. For queries: query parameters (type, domain, affected party, status, date range).
  - **E:** For writes: validate the incoming artifact, assign or update registry entry, update version history, notify affected parties of changes. For queries: accept query parameters, return matching agreements with metadata, support compound queries (e.g., "all active space agreements in SHUR Bali domain created in the last year").
  - **F:** For writes: updated registry state. For queries: query result set with agreement summaries and links to full text.
  - **G:** Only agreement-creation, agreement-amendment, and agreement-review outputs can write to the registry. No direct writes. Query access is open to all participants. Registry steward (a role, not a person) maintains registry integrity but cannot modify agreement content.
  - **H-L:** Full structural sections. Special attention to L (Cross-Unit Interoperability) -- how do registries federate across AZPOs?
  Walkthrough: An AE member queries the registry to find all active agreements affecting the Economics circle. The query returns 4 agreements: the UAF, the ETHOS agreement field, a resource stewardship agreement, and a cross-circle collaboration agreement. The member reads the summaries and follows the link to the full resource stewardship agreement. Edge case: a sunset agreement is still showing as "active" due to a missed review -- the registry flags this inconsistency.
  Stress tests: all 7 with particular attention to Scenario 5 (replication -- registry performance at scale) and Scenario 7 (30% exit -- registry entries for departed participants' agreements).
  **Acceptance:** Passes validation. Under 500 lines. Read vs. write access clearly separated.

- [x] **Task 5.2: Create agreement-registry assets**
  Create `assets/registry-schema.yaml`:
  ```yaml
  registry:
    entries:
      - agreement_id: ""
        type: space | access | organizational | uaf
        title: ""
        current_version: ""
        status: active | under_review | sunset | archived
        domain: ""
        created_date: ""
        last_amended_date: ""
        next_review_date: ""
        sunset_date: ""
        affected_parties: []
        parent_agreement_id: ""  # null for root agreements
        version_history:
          - version: ""
            date: ""
            change_type: creation | amendment | review_renewal
            record_id: ""
        full_text_path: ""
  query_capabilities:
    - by_type
    - by_domain
    - by_affected_party
    - by_status
    - by_date_range
    - compound
  ```
  **Acceptance:** Schema is comprehensive and referenced in SKILL.md.

- [x] **Task 5.3: Draft proposal-resolution SKILL.md -- full skill**
  **Source docs to load:** `ACT Sense Making Process.docx` (full GAIA 6-level model, Futurist Playground Value Decision Model, Doing Both Solution, coaching process), `conductor/tracks/foundation_20260301/spec.md` (updated GAIA section with Next Steps Process, OQ-11 Wisdom Council, OQ-12 Lawful Formation, OQ-13 preference vs solution).
  Build the complete proposal resolution skill (GAIA 6-level escalation):
  - **A:** Without a defined escalation path, stalled proposals either die or are resolved through informal power. This skill provides 6 levels of escalation, each with clear entry criteria, process, and handoff to the next level.
  - **B:** Any proposal that has not been resolved at the standard ACT level.
  - **C:** A proposal stalls at any ACT phase: advice cannot be integrated, consent cannot be achieved after maximum integration rounds, or test results are disputed.
  - **D:** The proposal, its current status, the advice log, the consent record (if applicable), the specific point of stalling.
  - **E:** The 6 GAIA levels with entry criteria and process:
    - Level 1 (Consensus): All agree within Master Plan scope. Entry: proposal is within a single circle's domain and aligned with existing plans. Process: circle discussion, consensus check. Exit: consensus achieved or escalate to Level 2.
    - Level 2 (Culture Code): Circle-internal decision using circle's chosen process. Entry: Level 1 fails or proposal is purely internal. Process: whatever the circle has agreed to. Exit: resolved or escalate to Level 3 when the decision touches the larger collective.
    - Level 3 (Advice + Panel): Pre-proposal synergy check, then formal proposal. Entry: proposal affects parties beyond the originating circle. Process: advice phase with expert panel input. Exit: advice integrated and ready for consent, or escalate to Level 4.
    - Level 4 (Coaching): Finding third solutions. Entry: Level 3 produces irreconcilable competing options. Process: a coach maps the proposal against collective, community, and private domains; facilitates synthesis of a third option. Exit: third solution found and ready for consent, or escalate to Level 5.
    - Level 5 (Alignment Sense Making): Check against policies, agreements, values. Entry: Level 4 coaching does not resolve. Process: compare proposal impact against existing policy framework; may delegate to a circle with specific agency or convene a Wisdom Council. Exit: aligned proposal ready for consent, or escalate to Level 6.
    - Level 6 (Decision Resolution): Value decision model. Entry: all other levels exhausted. Process: structured comparison chart evaluating the proposal against ecosystem values, affected parties' interests, precedent, and long-term impact. The deciding body (OSC for ecosystem-level, originating council for domain-level) makes a final determination. Exit: proposal adopted, modified, or rejected with full record.
  - **F:** Decision Resolution Record (at Level 6) or resolution record at whichever level succeeds.
  - **G:** No level can be skipped except by consent of all affected parties. The Level 6 deciding body must include representatives from all affected domains. No individual can unilaterally resolve a proposal at any level.
  - **H-L:** Full structural sections. H is critical -- address the risk of powerful individuals forcing rapid escalation to bypass lower-level consent.
  Walkthrough: A contentious proposal to restructure how emergency funds are allocated in OmniOne. The proposal affects AE, TH, and OSC. Level 3: advice is gathered but two AE circles give contradictory advice. Level 4: a coach identifies that the core tension is between rapid access (AE wants) and accountability (TH wants). The coach proposes a third solution: rapid access with 48-hour retroactive consent. Level 5: the third solution is checked against existing stewardship agreements -- no conflict found. Consent is achieved at Level 5 without needing Level 6.
  Stress tests: all 7 with particular attention to Scenario 3 (Charisma Capture -- leader tries to force escalation to Level 6 where they have more influence).
  **Acceptance:** Passes validation. Under 500 lines. All 6 GAIA levels clearly defined with entry, process, and exit criteria.

- [x] **Task 5.4: Create proposal-resolution assets**
  Create `assets/decision-resolution-template.yaml`:
  ```yaml
  resolution_id: ""
  proposal_id: ""
  resolution_level: 1 | 2 | 3 | 4 | 5 | 6
  escalation_history:
    - level: 1
      entry_date: ""
      exit_date: ""
      outcome: resolved | escalated
      notes: ""
  level_6_comparison_chart:  # only populated if Level 6 is reached
    values_alignment: ""
    affected_parties_impact: ""
    precedent_analysis: ""
    long_term_impact: ""
    deciding_body: []
    determination: adopt | modify | reject
  final_outcome: adopted | modified | rejected
  record_date: ""
  ```
  **Acceptance:** Template complete.

- [x] **Verification 5: Run validate_skill.py against all 11 completed skills. All must pass. Verify the complete dependency graph: agreement-creation has no dependencies, proposal-creation has no dependencies, universal-agreement-field depends on agreement-creation, all ACT phases form a coherent sequence, agreement-amendment references ACT phases, consensus-check is a utility referenced by consent phase and amendment, agreement-review triggers amendment for revisions, agreement-registry accepts writes from creation/amendment/review, proposal-resolution references all ACT phases and consensus-check.** [checkpoint marker]

---

## Phase 6: Layer Integration and Finalization

**Goal:** Write the Layer README files, perform cross-layer review, verify all quality gates, and prepare the track for completion.

### Tasks

- [x] **Task 6.1: Write Layer I README.md**
  Create `neos-core/layer-01-agreement/README.md` with:
  - Layer title and purpose: "The Agreement Layer defines how binding commitments are created, modified, reviewed, and tracked within the ecosystem."
  - List of skills with one-sentence descriptions and dependencies
  - Diagram of skill relationships (text-based):
    ```
    universal-agreement-field
          |
    agreement-creation --> agreement-registry <-- agreement-review
          |                                           |
    agreement-amendment --(triggers)--> agreement-review
    ```
  - How this layer interacts with Layer III (agreements are created and modified through ACT decisions)
  - Key design decisions (consent vs. consensus modes, expiry defaults, registry as single source of truth)
  **Acceptance:** README provides a complete overview. A new reader can understand the layer without reading individual skills.

- [x] **Task 6.2: Write Layer III README.md**
  Create `neos-core/layer-03-act-engine/README.md` with:
  - Layer title and purpose: "The ACT Decision Engine defines how proposals are created, debated, consented to, tested, and resolved through the Advice-Consent-Test process with GAIA 6-level escalation."
  - List of skills with one-sentence descriptions and dependencies
  - Diagram of skill relationships:
    ```
    proposal-creation --> act-advice-phase --> act-consent-phase --> act-test-phase
                                                    |
                                              consensus-check
                                                    |
                                           proposal-resolution (GAIA escalation)
    ```
  - How this layer interacts with Layer I (ACT produces agreements, agreements define who participates in ACT)
  - Key design decisions (consent vs. consensus, GAIA escalation levels, maximum integration rounds, auto-revert)
  **Acceptance:** README provides a complete overview.

- [x] **Task 6.3: Cross-layer review**
  Perform a systematic review across all 11 skills:
  - Verify all `depends_on` lists are accurate and complete
  - Verify all cross-references by name are to skills that exist
  - Verify terminology is consistent (use product-guidelines.md terminology table)
  - Verify no hidden authority exists in any skill (every judgment call has a stated authority scope)
  - Verify every skill has a review/expiry condition
  - Verify exit compatibility is addressed in every skill
  - Fix any inconsistencies found
  **Acceptance:** All cross-references are valid. Terminology is consistent. No hidden authority.

- [x] **Task 6.4: Final validation run**
  Run `validate_skill.py` against the entire `neos-core/` directory with `--verbose` flag. Document the output. All 11 skills must pass with zero failures.
  **Acceptance:** `python scripts/validate_skill.py neos-core/ --verbose` exits with code 0.

- [x] **Task 6.5: Per-layer quality gate checklist**
  Complete the per-layer checklist from workflow.md for both layers:

  Layer I:
  - [ ] All 5 skills complete
  - [ ] Skills cross-reference each other correctly
  - [ ] Layer README summarizes skills and relationships
  - [ ] No circular authority dependencies

  Layer III:
  - [ ] All 6 skills complete
  - [ ] Skills cross-reference each other correctly
  - [ ] Layer README summarizes skills and relationships
  - [ ] No circular authority dependencies
  **Acceptance:** All checklist items confirmed.

- [x] **Verification 6: Final human review. Read through each SKILL.md confirming: voice matches product guidelines, every process step is actionable (not philosophical), boundaries are stated as constraints (not permissions), degradation paths exist for every failure mode. Mark the track complete.** [checkpoint marker]

---

## Summary

| Phase | Skills Built | Cumulative Total |
|-------|-------------|-----------------|
| Phase 1: Tooling | 0 (validator + template) | 0 |
| Phase 2: Anchors | 2 (agreement-creation, proposal-creation) | 2 |
| Phase 3: UAF + ACT | 4 (universal-agreement-field, act-advice, act-consent, act-test) | 6 |
| Phase 4: Amendment + Consensus + Review | 3 (agreement-amendment, consensus-check, agreement-review) | 9 |
| Phase 5: Registry + Resolution | 2 (agreement-registry, proposal-resolution) | 11 |
| Phase 6: Integration | 0 (READMEs, review, validation) | 11 |

**Total deliverables:** 11 SKILL.md files, 11 asset templates, 2 Layer READMEs, 1 SKILL_TEMPLATE.md, 1 validate_skill.py with tests, 1 test fixture set.
