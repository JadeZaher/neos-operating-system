# Implementation Plan: Emergency Handling (Layer VIII)

## Overview

This plan builds 5 governance skills for Layer VIII plus layer-level integration, organized into 4 phases. The build order follows the circuit breaker lifecycle: define entry criteria, define pre-authorized roles, define crisis operations, define reversion, and define post-emergency review. This sequence ensures each skill can reference the prior skill's outputs as inputs.

**Total skills:** 5
**Total phases:** 4
**Estimated scope:** 20-28 hours of focused implementation

### Build Order Rationale

The skills follow the emergency lifecycle chronologically: criteria must be defined before roles can be pre-authorized against them, roles must exist before crisis coordination can reference them, crisis operations must produce logs before reversion can review them, and reversion must occur before post-emergency review can evaluate the full cycle. Building in lifecycle order ensures each skill's inputs are already defined by a preceding skill.

### Commit Strategy

- One commit per completed skill: `neos(layer-08): Add <skill-name> skill`
- Layer-level commit: `neos(layer-08): Complete layer 08 - Emergency Handling`

---

## Phase 1: Scaffolding and Entry Criteria

**Goal:** Create the Layer VIII directory structure and build the first two skills that define how emergencies are declared and what authority activates. After this phase, the ecosystem can enter emergency mode with pre-defined criteria and pre-authorized roles.

### Tasks

- [ ] **Task 1.1: Create Layer VIII directory scaffolding**
  Create the full directory tree:
  ```
  neos-core/
    layer-08-emergency/
      README.md (empty placeholder)
      emergency-criteria-design/   (SKILL.md, assets/, references/, scripts/)
      pre-authorization-protocol/  (same structure)
      crisis-coordination/         (same structure)
      emergency-reversion/         (same structure)
      post-emergency-review/       (same structure)
  ```
  Each skill directory gets empty `SKILL.md`, empty `assets/`, `references/`, and `scripts/` subdirectories.
  **Acceptance:** All directories exist. `find neos-core/layer-08-emergency -name SKILL.md | wc -l` returns 5.

- [ ] **Task 1.2: Draft emergency-criteria-design SKILL.md -- sections A through F**
  Using the SKILL_TEMPLATE.md, fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without objective emergency criteria, emergencies are declared by whoever has the loudest voice or the most authority, enabling Agamben's state of exception. This skill ensures emergency mode is entered only when measurable conditions are met, and exited when those conditions reverse.
  - **B. Domain Scope:** Any governance body that may need to operate under emergency conditions. Criteria are defined per AZPO or at ecosystem level, never informally.
  - **C. Trigger Conditions:** Ecosystem formation (initial criteria definition), periodic review of existing criteria, a governance health audit reveals a gap in emergency preparedness, or a post-emergency review recommends criteria refinement.
  - **D. Required Inputs:** The risk category to address, proposed observable condition, proposed measurement method, proposed threshold, proposed exit condition, proposed maximum duration, and the affected governance bodies.
  - **E. Step-by-Step Process:** Identify risk category, draft criterion with observable condition and measurement method, define threshold (what level constitutes emergency), define exit condition (equally measurable), define maximum duration (hard cap), submit through ACT process (criteria are agreements), consent achieved, install in Emergency Criteria Registry, define review cadence (annual minimum).
  - **F. Output Artifact:** Emergency Criteria Registry entry with: criterion ID, risk category, observable condition, measurement method, threshold, exit condition, maximum duration, consent record, installation date, review date, activation history.
  Write with full substance, active voice. Reference Agamben's warning and the circuit breaker Closed-to-Open transition.
  **Acceptance:** Sections A-F substantive (3+ lines each), terminology matches product-guidelines.md.

- [ ] **Task 1.3: Draft emergency-criteria-design SKILL.md -- sections G through L**
  Complete the remaining structural sections:
  - **G. Authority Boundary Check:** Criteria installation requires consent through normal ACT process. No individual can unilaterally define what constitutes an emergency. Criteria cannot be so broad that normal operational difficulties qualify. The skill defines specificity requirements: the observable condition must be verifiable by any ecosystem member, not just leadership.
  - **H. Capture Resistance Check:** Address vague criteria (the primary capture vector -- "any situation the council deems threatening" is explicitly prohibited; criteria must reference observable conditions, not judgment calls). Address criteria inflation (adding criteria for every minor risk until emergency mode becomes frequent). Address criteria suppression (removing criteria that would inconvenience leadership).
  - **I. Failure Containment Logic:** What happens when: an event occurs that no criterion covers (the ecosystem must operate under normal governance until a new criterion can be designed through ACT -- this is by design, not a bug), criteria are met but no one declares the emergency (any ecosystem member can invoke the criterion check), criteria seem met but measurement is disputed (the skill defines a verification protocol using independent data from the monitoring role).
  - **J. Expiry / Review Condition:** Criteria are reviewed annually at minimum. Criteria that have never been activated in 3 years receive a relevance review. Criteria that have been activated more than twice in a year receive a threshold review (is the threshold too sensitive?).
  - **K. Exit Compatibility Check:** When a participant exits, the emergency criteria remain valid. The exit itself may trigger a criterion check (does departure of key participants constitute a governance incapacity criterion?).
  - **L. Cross-Unit Interoperability Impact:** Each AZPO defines its own emergency criteria. Ecosystem-level criteria are defined through the OSC. An emergency in one AZPO does not automatically constitute an emergency in another, but ecosystem-level criteria may reference cross-AZPO cascading effects.
  **Acceptance:** Sections G-L are substantive and structurally precise. Agamben's trap is explicitly addressed.

- [ ] **Task 1.4: Write emergency-criteria-design OmniOne walkthrough and stress tests**
  Walkthrough: The OSC designs emergency criteria for the Bali SHUR. They define two criteria: (1) Physical safety -- observable condition: structural damage to SHUR facilities OR natural disaster warning from government authority; measurement: official government warning or independent structural assessment; threshold: imminent physical risk to residents; exit condition: government all-clear OR structural assessment confirming safety; maximum duration: 30 days. (2) Resource crisis -- observable condition: loss of funding exceeding 50% of operating budget within a 60-day period; measurement: financial records verified by independent monitor; threshold: 50% budget loss; exit condition: replacement funding secured or operating costs reduced to match available budget; maximum duration: 90 days.
  During ACT consent, one member objects that the 50% resource threshold is too high -- by the time you lose 50%, it is too late. Integration: add an early warning criterion at 30% that activates a subset of emergency roles (resource coordination only) while the 50% criterion activates full emergency response.
  All 7 stress tests as full narratives specific to emergency criteria:
  1. Capital Influx -- a major donor threatens withdrawal if emergency criteria include capital concentration triggers; walk through how criteria are protected by ACT process
  2. Emergency Crisis -- a crisis occurs that was not anticipated by any criterion; walk through the gap-handling protocol
  3-7. Continue with full narratives.
  **Acceptance:** Walkthrough names specific OmniOne roles, includes edge case (threshold objection and integration), stress tests are full narratives.

- [ ] **Task 1.5: Finalize emergency-criteria-design SKILL.md and create assets**
  Assemble SKILL.md with YAML frontmatter:
  ```yaml
  ---
  name: emergency-criteria-design
  description: "Define objective, measurable emergency criteria that trigger governance mode changes -- with matching exit conditions that make permanent emergency structurally impossible."
  layer: 8
  version: 0.1.0
  depends_on: []
  ---
  ```
  Create `assets/emergency-criteria-template.yaml` (criterion ID, risk category, observable condition, measurement method, threshold, exit condition, maximum duration, consent record ID, installation date, review date, activation history).
  Create `assets/starter-criteria.yaml` (5 starter categories with example criteria: physical safety, resource crisis, governance incapacity, external legal threat, infrastructure failure).
  Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines. Both asset files complete.

- [ ] **Task 1.6: Draft pre-authorization-protocol SKILL.md -- full skill**
  Build the complete pre-authorization skill:
  - **A:** Without pre-authorized roles, emergency response defaults to whoever seizes initiative -- typically the most powerful or charismatic person. This skill ensures emergency authority is distributed, scoped, and consented to in advance.
  - **B:** Any governance body that has defined emergency criteria. Pre-authorization roles map to specific criteria.
  - **C:** Emergency criteria have been installed and the ecosystem has not yet defined corresponding emergency roles, a post-emergency review reveals gaps in pre-authorization, or a periodic review of emergency preparedness identifies new needs.
  - **D:** The emergency criterion this role responds to, the proposed role title, the proposed authority scope, the proposed authority ceiling (what the role cannot do), the proposed maximum duration, and the accountability requirements.
  - **E:** Draft role definition, map to specific emergency criterion, define authority scope (minimum necessary), define irreducible constraints (UAF amendment, AZPO dissolution, member expulsion, criteria modification are always prohibited), define duration (must not exceed the linked criterion's maximum duration), define accountability requirements (real-time logging, post-emergency review participation as witness not reviewer), submit through ACT process, install in Pre-Authorization Registry.
  - **F:** Pre-Authorization Registry entry.
  - **G:** No single role receives all emergency authority. Authority is distributed across multiple roles with non-overlapping scopes. Role holders are pre-selected through normal governance (not self-appointed during crisis). If a designated role holder is unavailable, the skill defines a succession protocol.
  - **H:** Address authority concentration, scope creep, "just in case" retention, and the succession being captured by a clique.
  - **I-L:** Full structural sections.
  - Walkthrough: AE defines three pre-authorized roles for the SHUR physical safety criterion. Safety Coordinator: can order evacuation, close facilities, redirect residents to backup locations; cannot spend more than emergency fund cap, cannot terminate vendor contracts. Resource Coordinator: can release emergency funds up to cap, can authorize emergency purchases; cannot change ongoing financial agreements, cannot access non-emergency funds. Communications Coordinator: can issue external statements within pre-approved message templates; cannot make binding commitments, cannot speak for the ecosystem beyond the specific crisis. During consent, one member raises: what if all three role holders are personally affected by the emergency? Integration: add backup role holders from a different AZPO.
  - All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. Irreducible constraints are clearly defined. Minimum necessary authority principle is operationalized.

- [ ] **Task 1.7: Create pre-authorization-protocol assets**
  Create `assets/pre-authorization-template.yaml` (role ID, linked criterion ID, role title, authority scope, authority ceiling, irreducible constraints, maximum duration, designated holder, backup holder, accountability requirements, consent record ID, installation date, review date).
  Create `assets/irreducible-constraints.yaml` (the list of actions that no emergency role can ever take, regardless of crisis severity: UAF amendment, AZPO dissolution, member expulsion, emergency criteria modification, safeguard trigger modification).
  **Acceptance:** Both templates complete.

- [ ] **Verification 1: Run validate_skill.py against both completed skills. Confirm both pass. Verify that pre-authorization roles reference specific emergency criteria. Verify irreducible constraints are consistent between both skills. Review for Agamben's trap in any formulation.** [checkpoint marker]

---

## Phase 2: Crisis Operations and Reversion

**Goal:** Build the operational skills for running governance during crisis and transitioning back to normal. After this phase, the full circuit breaker lifecycle is defined except for retrospective review.

### Tasks

- [ ] **Task 2.1: Draft crisis-coordination SKILL.md -- sections A through F**
  - **A:** During crisis, normal governance timelines are too slow. Without a structured acceleration, participants either bypass governance entirely (unilateral action) or freeze (no action). This skill defines how governance operates faster while maintaining structural constraints.
  - **B:** Any governance body operating in the Open (Crisis) state of the circuit breaker. Only active when emergency criteria have been verified as met and pre-authorized roles have activated.
  - **C:** Emergency criteria are verified as met, pre-authorized roles activate, and the auto-reversion timer starts.
  - **D:** The verified emergency criterion, the activated pre-authorized roles with their scopes, the compressed timeline parameters, and the Crisis Operations Log (initially empty).
  - **E:** Verify criterion (must be confirmed by two independent sources for criteria requiring measurement), activate roles (notify all ecosystem members of emergency activation, role holders, and their scopes), start auto-reversion timer (displayed prominently in all crisis communications), operate under compressed ACT timelines (immediate decisions within role scope: act and log within 24h; short-cycle decisions requiring abbreviated consent: 24h advice, 24h consent; deferred decisions outside scope: queue for recovery), maintain Crisis Operations Log (every decision logged with: timestamp, decision maker, authorization reference, decision, rationale), monitor exit criteria at defined cadence (minimum every 48 hours), communicate status updates to all ecosystem members at defined cadence.
  - **F:** Crisis Operations Log (timestamped decision records with authorization references).
  **Acceptance:** Sections A-F complete, compressed timelines are specific, logging requirements are mandatory.

- [ ] **Task 2.2: Draft crisis-coordination SKILL.md -- sections G through L, walkthrough, and stress tests**
  - **G:** Crisis coordination does not grant new authority. It compresses timelines for pre-authorized authority. If a decision falls outside any pre-authorized scope, it must either wait for recovery or go through an emergency-expansion request (abbreviated consent from a defined body -- not unilateral expansion). The emergency-expansion request is itself logged and subject to post-emergency review.
  - **H:** Address normalization of crisis mode (the compressed timeline is deliberately less thorough than normal governance -- it should produce decisions that feel provisional, encouraging reversion). Address crisis decisions as precedent (explicitly tagged as emergency-context, not binding for normal operations). Address the decision-maker expanding their own scope during crisis (every decision is logged against the specific authorization reference -- scope creep is visible in the log).
  - **I:** What happens when: a decision is needed outside any pre-authorized scope (emergency-expansion request or defer to recovery), a role holder is incapacitated (backup role holder activates from succession list), the auto-reversion timer is about to expire but the crisis continues (extension request requires abbreviated consent, maximum 1 extension of 50% original duration), ecosystem members disagree about whether the crisis is real (the criterion measurement is objective -- if it is met, emergency proceeds; if disputed, the verification protocol from emergency-criteria-design applies).
  - **J-L:** Full structural sections.
  - Walkthrough: Bali flooding event. Government issues disaster warning (physical safety criterion met). Two independent confirmations: government warning and onsite assessment. Pre-authorized roles activate. Auto-reversion timer: 30 days. Safety Coordinator orders evacuation of ground-floor units (within scope -- logged at 14:00 with reference to pre-authorization SA-001). Resource Coordinator releases Rp 50M from emergency fund for temporary housing (within scope and cap -- logged at 14:30). A SHUR resident asks: can we terminate the landscaping contract to free up funds? No -- contract termination is outside pre-authorized scope. Decision deferred to recovery. Day 5: exit criteria check -- flooding continues, government warning still active. Day 12: water recedes, government issues all-clear. Exit criterion met. Emergency reversion begins. Edge case: Resource Coordinator spent Rp 52M, exceeding the Rp 50M cap by 4%. This overage is logged and flagged for post-emergency review. The decision was arguably necessary (no cheaper temporary housing available), but the overage must be formally addressed.
  - All 7 stress tests, with particular attention to: Scenario 2 (Emergency Crisis -- this IS the emergency scenario, so test a more severe version where multiple criteria are met simultaneously), Scenario 4 (High Conflict -- factions disagree about whether the emergency response is proportionate), Scenario 7 (30% exit during an active emergency).
  **Acceptance:** Passes validation. Under 500 lines. Every decision in the walkthrough references a specific authorization.

- [ ] **Task 2.3: Create crisis-coordination assets**
  Create `assets/crisis-operations-log-template.yaml` (emergency ID, criterion ID, activation timestamp, auto-reversion timestamp, entries: timestamp, decision maker, role reference, authorization reference, decision, rationale, within scope: yes/no/expansion request, status updates log, exit criteria check log).
  Create `assets/compressed-act-timelines.yaml` (decision categories: immediate/within-scope, short-cycle/abbreviated-consent, deferred/outside-scope, with specific timelines and process requirements for each).
  **Acceptance:** Both templates complete.

- [ ] **Task 2.4: Draft emergency-reversion SKILL.md -- full skill**
  Build the complete emergency reversion skill:
  - **A:** The transition from emergency to normal is where Agamben's capture most commonly occurs. Without a structured, mandatory reversion process, emergency authority persists through inertia, institutional convenience, or the psychological comfort of centralized decision-making. This skill makes reversion automatic, mandatory, and irreversible.
  - **B:** Any governance body currently in the Open (Crisis) state that has met its exit criteria or whose auto-reversion timer has expired.
  - **C:** Emergency exit criteria are met (verified by the same measurement process that confirmed the emergency), the auto-reversion timer expires, or the ecosystem consents to early reversion through abbreviated ACT process.
  - **D:** The reversion trigger (which of the three types), the Crisis Operations Log, the list of crisis decisions pending normal ratification, and the post-emergency review scheduling requirements.
  - **E:** Announce reversion (notify all ecosystem members that emergency mode is ending), deactivate emergency roles (authority expansion ceases immediately -- this is not gradual), enter Half-Open/Recovery state, restore normal ACT timelines, generate list of crisis decisions requiring ratification (each decision made under emergency authority must be ratified through normal consent, modified, or reversed within 30 days -- unratified decisions auto-revert), schedule mandatory post-emergency review (within 14 days of entering Recovery), wind down any ongoing emergency operations through handoff to normal governance structures, complete Recovery (all decisions ratified or reverted, post-emergency review completed) and return to Closed/Normal state.
  - **F:** Reversion Record (trigger type, timestamp, role deactivation confirmation, decision ratification queue, post-emergency review date, recovery completion date).
  - **G:** No emergency role holder retains expanded authority after entering Recovery. If they believe continued authority is needed, they must propose it through normal ACT process as a non-emergency authority expansion. The reversion cannot be blocked, delayed, or conditioned on anything other than the technical process of role deactivation and handoff.
  - **H:** Address "just one more week" capture (reversion is automatic, not negotiable), address partial reversion (some authority retained "temporarily" -- not permitted; reversion is complete), address reversion resistance masked as safety concern (if the safety concern is real, the emergency criterion will still be met and a new emergency can be properly declared).
  - **I-L:** Full structural sections.
  - Walkthrough: Bali flooding -- government all-clear issued on Day 12. Exit criterion met. Reversion process begins immediately. Emergency roles deactivate at 16:00. Recovery state entered. Crisis decisions queued: evacuation order (ratify: it was correct and already complete), fund release of Rp 52M (ratify with amendment: approve overage, increase cap for future), temporary housing arrangements (ratify: convert to normal agreement for remaining lease term). Post-emergency review scheduled for Day 26. Edge case: the Resource Coordinator argues that their role should continue for 2 more weeks to manage the temporary housing transition. The skill's structure: no -- the role deactivates. The housing management transfers to normal governance. If normal governance is unable to handle it, that is a separate problem to be addressed through normal channels.
  - All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. Auto-reversion is non-negotiable in the skill's structure.

- [ ] **Task 2.5: Create emergency-reversion assets**
  Create `assets/reversion-record-template.yaml` (emergency ID, reversion trigger type, reversion timestamp, role deactivation confirmations, decision ratification queue with status, post-emergency review date, recovery completion date, handoff records).
  Create `assets/circuit-breaker-states.yaml` (three states: Closed/Normal, Open/Crisis, Half-Open/Recovery; transitions: Closed-to-Open criteria, Open-to-Half-Open criteria, Half-Open-to-Closed criteria; forbidden transitions: Open-to-Closed directly, Closed-to-Half-Open).
  **Acceptance:** Both templates complete. Circuit breaker state machine is clear.

- [ ] **Verification 2: Run validate_skill.py against all 4 completed skills. Confirm all pass. Verify lifecycle coherence: emergency-criteria-design outputs feed pre-authorization-protocol inputs, pre-authorization outputs feed crisis-coordination inputs, crisis-coordination outputs feed emergency-reversion inputs. Verify the circuit breaker state machine is consistent across all skills. Verify auto-reversion is structurally mandatory in every skill's formulation.** [checkpoint marker]

---

## Phase 3: Post-Emergency Review and Layer Integration

**Goal:** Build the mandatory post-emergency review skill and complete layer-level integration.

### Tasks

- [ ] **Task 3.1: Draft post-emergency-review SKILL.md -- full skill**
  Build the complete post-emergency review skill:
  - **A:** Without mandatory retrospective, emergency authority use is unaccountable and unrepeatable lessons are lost. Each emergency is unique, but the patterns of authority use, scope compliance, and structural adequacy are generalizable. This skill ensures every emergency produces learning.
  - **B:** Any emergency that has concluded and entered the Recovery state. The review operates during the Half-Open/Recovery state and must complete before the full return to Closed/Normal.
  - **C:** Recovery state is entered. The review is mandatory and automatically scheduled. It cannot be deferred beyond 14 days from recovery start without ecosystem-level escalation notice.
  - **D:** The Crisis Operations Log, the Reversion Record, the original emergency criteria and pre-authorization definitions, the decision ratification outcomes, and testimony from affected participants (not just role holders).
  - **E:** Convene review body (must include participants affected by emergency decisions who did not hold emergency roles; must exclude emergency role holders -- they participate as witnesses providing testimony, not as reviewers), review the Crisis Operations Log entry by entry (was each decision within scope? was the authorization reference correct? was the outcome proportionate?), evaluate emergency criteria (were the trigger and exit criteria adequate? did they fire at the right time? were they too sensitive or too insensitive?), evaluate pre-authorization scopes (were they sufficient? were any ceilings tested or breached? were backup succession protocols needed?), evaluate overall response (was the response timely? was it proportionate? were all ecosystem members adequately informed?), produce Post-Emergency Review Report, submit recommendations through normal ACT process.
  - **F:** Post-Emergency Review Report (emergency timeline, decision-by-decision review, authority compliance assessment, criteria adequacy evaluation, pre-authorization scope evaluation, recommendations with ACT proposal references).
  - **G:** The review produces a report and recommendations. It has no authority to discipline, reward, or override normal governance. Recommendations must go through ACT. The review body has investigative authority (access to logs, ability to request testimony) but no punitive authority.
  - **H:** Address review capture by emergency role holders (they are excluded from the review body), address review suppression (non-occurrence of the review triggers a Layer VII safeguard), address weaponization of the review (the review evaluates decisions against pre-defined scopes, not personal judgment -- was the decision within the authorized scope, yes or no?), address "move on" pressure (the review is mandatory and its findings are public; the ecosystem cannot choose to skip accountability).
  - **I:** What happens when: the review body cannot agree on findings (majority finding is published with dissenting views documented), a review reveals potential misconduct (the review documents the finding and refers it to Layer VI conflict resolution -- the review body does not adjudicate), a new emergency interrupts the review (review is paused, not cancelled, and resumes in the next recovery period).
  - **J-L:** Full structural sections.
  - Walkthrough: Post-emergency review of the Bali flooding response. Review body: 4 TH members and 1 AE member who were affected by the evacuation but did not hold emergency roles. The 3 emergency role holders participate as witnesses. Review of Crisis Operations Log: evacuation decision -- within scope, proportionate, timely (COMPLIANT). Fund release -- within scope but exceeded cap by 4% (OVERAGE -- review recommends increasing cap by 20% or adding abbreviated consent requirement for overages above 5%). Deferred vendor decision -- correctly deferred (COMPLIANT). Communication -- within parameters (COMPLIANT). Criteria evaluation: physical safety criterion triggered correctly. Exit criterion (government all-clear) was met 2 days before reversion actually occurred -- review recommends adding a mandatory 48-hour exit-criteria check cadence during crisis. Pre-authorization evaluation: Safety and Communications roles adequate. Resource role cap was too low -- recommend adjustment. Overall: response was effective, proportionate, and well-logged. Recommendations submitted through ACT.
  - All 7 stress tests with specific attention to: Scenario 3 (Charisma Capture -- the charismatic leader was the emergency role holder and the review must evaluate their decisions without personal deference), Scenario 6 (External Legal Pressure -- a government demands access to the Crisis Operations Log).
  **Acceptance:** Passes validation. Under 500 lines. Review body composition rules are structurally enforced.

- [ ] **Task 3.2: Create post-emergency-review assets**
  Create `assets/post-emergency-review-template.yaml` (emergency ID, review body members and roles, emergency role holders as witnesses, timeline, decision-by-decision review entries, criteria evaluation, pre-authorization evaluation, overall assessment, recommendations with ACT proposal references, dissenting views).
  Create `assets/review-checklist.yaml` (structured checklist: was each decision within scope, was each authorization reference valid, were irreducible constraints respected, was the auto-reversion timer honored, were exit criteria checked at the defined cadence, was the Crisis Operations Log maintained, were all ecosystem members notified at the defined cadence).
  **Acceptance:** Both templates complete.

- [ ] **Task 3.3: Write layer-08-emergency README.md**
  Write the layer README summarizing:
  - Layer purpose: Structured emergency governance with auto-reversion
  - The circuit breaker model: Closed (Normal), Open (Crisis), Half-Open (Recovery)
  - The 5 skills mapped to the circuit breaker lifecycle
  - Cross-layer dependencies (especially the Layer VII/VIII relationship)
  - The irreducible constraints (what emergency authority can never do)
  - Agamben's warning and how the layer structurally addresses it
  **Acceptance:** README accurately describes all 5 skills, the circuit breaker model, and the anti-capture engineering.

- [ ] **Verification 3: Run validate_skill.py against all 5 completed skills. All must pass. Verify the complete circuit breaker lifecycle: a governance body can define criteria, pre-authorize roles, operate during crisis, revert to normal, and conduct post-emergency review using only the defined skills. Verify irreducible constraints are consistent across all 5 skills. Verify that auto-reversion is structurally mandatory and cannot be bypassed in any skill's formulation.** [checkpoint marker]

---

## Phase 4: Cross-Layer Verification and Final Quality Gate

**Goal:** Verify all cross-layer references and complete quality gate review.

### Tasks

- [ ] **Task 4.1: Cross-layer reference verification**
  Review all 5 SKILL.md files for:
  - References to Layer I (Agreement) skills use correct skill names
  - References to Layer II (Authority) concepts are forward-compatible
  - References to Layer III (ACT Engine) skills use correct skill names and accurately describe compressed timelines
  - References to Layer VII (Safeguard) describe the watchdog relationship correctly
  - References to Layer IX (Memory) describe log storage correctly
  - No circular authority dependencies
  - The Layer VII/VIII relationship is symmetric: Layer VII monitors Layer VIII, Layer VIII does not modify Layer VII
  **Acceptance:** All cross-references verified.

- [ ] **Task 4.2: Run full validation and quality gate review**
  Run `validate_skill.py` against all 5 skills. Review against per-skill and per-layer checklists:
  Per-skill:
  - [ ] All 12 sections (A-L) present and substantive
  - [ ] OmniOne walkthrough included with specific roles
  - [ ] At least one edge case documented
  - [ ] Stress-tested against 7 scenarios
  - [ ] No hidden sovereign authority
  - [ ] Exit compatibility confirmed
  - [ ] Cross-unit interoperability impact stated
  Per-layer:
  - [ ] All 5 skills complete
  - [ ] Skills cross-reference each other correctly
  - [ ] Layer README summarizes skills and relationships
  - [ ] No circular authority dependencies
  - [ ] Circuit breaker state machine is coherent
  **Acceptance:** All checks pass. Layer VIII is complete.

- [ ] **Verification 4: Final layer review. All 5 skills pass validation. README is complete. The layer implements Agamben-resistant emergency governance with auto-reversion at every level. Cross-layer references are accurate. Commit: `neos(layer-08): Complete layer 08 - Emergency Handling`** [checkpoint marker]
