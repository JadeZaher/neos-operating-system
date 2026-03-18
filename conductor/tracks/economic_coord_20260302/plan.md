# Implementation Plan: Layer IV -- Economic Coordination

## Overview

This plan builds 5 governance skills for NEOS Layer IV (Economic Coordination), organized into 4 phases. The build order follows dependency chains: resource requests define the basic unit, funding pools define the containers, participatory allocation defines the distribution process, commons monitoring defines the accountability loop, and access economy transition defines the long-range trajectory.

**Total skills:** 5
**Total phases:** 4
**Estimated scope:** 20-30 hours of focused implementation

### Build Order Rationale

Economic coordination skills form a dependency chain rather than the interleaved pattern used in the foundation track. Resource requests and funding pools are co-dependent (you request from a pool, but pools need to handle requests), so they are built in the same phase with the request skill first to establish the shape of what flows through the system.

### Commit Strategy

- One commit per completed skill: `neos(layer-04): Add <skill-name> skill`
- Layer-level commit when all skills are done: `neos(layer-04): Complete layer 04 - Economic Coordination`

### Dependencies

This track assumes the following are complete or in progress:
- Layer I skills (agreement-creation, agreement-amendment, agreement-review, agreement-registry) from `foundation_20260301`
- Layer III skills (proposal-creation, act-advice-phase, act-consent-phase, act-test-phase) from `foundation_20260301`
- Layer II skills (authority-assignment, role-definition, domain-boundary) from `authority_role_20260302`

---

## Phase 1: Scaffolding and Anchor Skills

**Goal:** Create the Layer IV directory structure and build the two anchor skills -- resource-request and funding-pool-stewardship -- that define the fundamental economic shapes: what a resource request looks like and how funding pools are governed.

### Tasks

- [ ] **Task 1.1: Create Layer IV directory scaffolding**
  Create the full `neos-core/layer-04-economic/` directory tree:
  ```
  neos-core/
    layer-04-economic/
      README.md
      resource-request/       (SKILL.md, assets/, references/, scripts/)
      funding-pool-stewardship/ (same structure)
      participatory-allocation/ (same structure)
      commons-monitoring/      (same structure)
      access-economy-transition/ (same structure)
  ```
  Each skill directory gets empty `SKILL.md`, empty `assets/`, `references/`, and `scripts/` subdirectories. Layer directory gets an empty `README.md`.
  **Acceptance:** All directories exist. `find neos-core/layer-04-economic -name SKILL.md | wc -l` returns 5.

- [ ] **Task 1.2: Draft resource-request SKILL.md -- sections A through F**
  Using the SKILL_TEMPLATE.md, fill in the first 6 sections for `resource-request`:
  - **A. Structural Problem It Solves:** Without a formal resource request process, resources flow through informal networks -- people who know the right person get funded, others do not. This skill ensures every resource request has a traceable origin, clear rationale, defined stewardship commitment, and passes through legitimate consent-based decision making. It structurally prevents economic contribution from translating into preferential access.
  - **B. Domain Scope:** Any domain where participants need to draw from shared resource pools. Applies to circle operational pools, ecosystem strategic pools, project-specific pools, and cross-ETHOS shared pools. Covers financial resources, physical assets, time allocations, access permissions, and expertise commitments.
  - **C. Trigger Conditions:** A participant identifies a resource need that cannot be met from their existing personal or role-based allocation. The need has a clear connection to ecosystem, circle, or project objectives.
  - **D. Required Inputs:** Requester identity, resource type, amount/scope, target funding pool, rationale connecting the request to ecosystem purpose, timeline for use, stewardship commitment (how the resource will be accounted for), domain scope, and any conflict-of-interest disclosures.
  - **E. Step-by-Step Process:** Draft request using template, verify target pool exists and has capacity, submit to pool steward for initial routing, route through appropriate ACT level based on pool-defined thresholds (steward discretion for small amounts, circle consent for medium, ecosystem consent for large), track fulfillment, and report stewardship outcomes.
  - **F. Output Artifact:** Versioned resource request document with unique ID, approval status, fulfillment record, stewardship report, and traceability link to the pool governance agreement.
  Write with full substance. Use active voice per product guidelines.
  **Acceptance:** Sections A-F are substantive (3+ lines each), terminology matches product-guidelines.md.

- [ ] **Task 1.3: Draft resource-request SKILL.md -- sections G through L**
  Complete the remaining structural sections:
  - **G. Authority Boundary Check:** Requesters can only request from pools within their domain or pools explicitly open to their participation level. No self-approval: requests above steward discretion threshold require consent from parties other than the requester. Pool stewards cannot approve requests that benefit their own projects without circle consent.
  - **H. Capture Resistance Check:** Capital influx (donor conditions funding on specific allocation patterns), charismatic capture (high-status members receiving rubber-stamp approvals), emergency capture (crisis framing used to bypass normal request process), faction capture (coordinated requests draining pool toward one interest group).
  - **I. Failure Containment Logic:** Request denied (requester may revise and resubmit or escalate through GAIA). Pool depleted (requests enter queue, no new approvals until next allocation cycle). Stewardship violation (graduated response: reporting reminder, pool access pause, stewardship review, resource return requirement).
  - **J. Expiry / Review Condition:** Approved requests that are not fulfilled within their stated timeline auto-expire. Fulfilled requests require stewardship reports within 30 days of completion. Resource requests creating ongoing commitments include review dates.
  - **K. Exit Compatibility Check:** When a requester exits, unfulfilled requests are voided. Resources already disbursed follow the stewardship terms of the original request. In-progress projects receive a 30-day wind-down to return or transition stewardship.
  - **L. Cross-Unit Interoperability Impact:** Requests targeting cross-ETHOS pools trigger notification to all contributing ETHOS. Cross-ETHOS requests require consent from the shared pool governance body, not just the requester's home circle.
  **Acceptance:** Sections G-L are substantive and structurally precise.

- [ ] **Task 1.4: Write resource-request OmniOne walkthrough**
  Write a full narrative walkthrough:
  - Scenario: An AE member in the Education circle requests funding from the circle's operational pool to attend a governance training workshop in Costa Rica.
  - Walk through: trigger (training opportunity identified), drafting (requester fills out request template with costs, rationale, stewardship commitment to share learnings), routing (pool steward reviews -- amount is above steward discretion threshold, routes to circle ACT), advice phase (other circle members weigh in, one suggests a virtual alternative), requester modifies to hybrid attendance, consent phase (circle consents with one stand-aside), fulfillment (funds disbursed through H.A.R.T.), stewardship report (requester presents learnings at next circle meeting).
  - Include edge case: the requester is also the pool steward. Self-approval is structurally blocked; the request routes to the circle directly.
  - End with the output artifact: the completed request document snippet.
  **Acceptance:** Walkthrough names specific OmniOne roles, shows complete flow, includes edge case, ends with artifact.

- [ ] **Task 1.5: Write resource-request stress-test results (all 7 scenarios)**
  Write full narrative stress tests:
  1. **Capital Influx:** A major donor contributes $200K to the ecosystem and expects their preferred projects to receive priority funding. Walk through how the request process treats all requests equally regardless of funding source, and how the pool governance agreement structurally separates contribution from allocation authority.
  2. **Emergency Crisis:** A SHUR location faces urgent repair needs. Walk through how the emergency reserve pool handles expedited requests while maintaining steward accountability and post-crisis review.
  3. **Leadership Charisma Capture:** A beloved community leader submits resource requests that routinely receive uncritical approval. Walk through how the consent process requires substantive engagement from each member and how commons monitoring detects patterns of uncritical approval.
  4. **High Conflict / Polarization:** Two factions compete for a limited pool. Walk through how the participatory allocation process (reference to that skill) prevents zero-sum framing and seeks third solutions.
  5. **Large-Scale Replication:** The ecosystem grows from 5 circles to 50. Walk through how the nested pool structure scales (each circle governs its own pool, ecosystem-level pool handles cross-circle needs).
  6. **External Legal Pressure:** A government demands disclosure of all resource flows. Walk through how the transparency-by-default design means most information is already accessible, and how the ecosystem handles requests for data it structurally collects vs. data it does not.
  7. **Sudden Exit of 30%:** A third of participants leave. Walk through how resource requests in progress are handled (unfulfilled requests from exiting members voided, pool balances recalculated, stewardship obligations transitioned).
  **Acceptance:** Each scenario is a full narrative paragraph (5+ sentences).

- [ ] **Task 1.6: Finalize resource-request SKILL.md and create assets**
  - Assemble SKILL.md from Tasks 1.2-1.5 with proper YAML frontmatter:
    ```yaml
    ---
    name: resource-request
    description: "Request resources from ecosystem funding pools -- financial, physical, time, access, or expertise -- through a consent-based process with stewardship accountability and full transparency."
    layer: 4
    version: 0.1.0
    depends_on: [agreement-creation, act-consent-phase, authority-assignment]
    ---
    ```
  - Create `assets/resource-request-template.yaml` defining the request document schema.
  - Run `validate_skill.py` against the completed SKILL.md.
  **Acceptance:** SKILL.md passes validation. Under 500 lines. Asset template is complete.

- [ ] **Task 1.7: Draft funding-pool-stewardship SKILL.md -- full skill (sections A-L)**
  Build the complete `funding-pool-stewardship` skill with all 12 sections:
  - **A:** Without formal pool governance, resource containers become power centers. This skill ensures every funding pool has transparent boundaries, accountable stewards, community oversight, and consent-based governance rules.
  - **B:** Any domain where shared resources are collected and distributed. Pool types: circle operational, ecosystem strategic, cross-ETHOS shared, project-specific, emergency reserve.
  - **C:** A circle or ecosystem body identifies the need for a shared resource container, or an existing informal pool needs to be formalized.
  - **D:** Pool name, type, boundary definition (who can contribute, who can request), inflow rules, outflow rules (threshold tiers), steward role definition, reporting cycle, review date.
  - **E:** Propose pool creation through ACT (using agreement-creation), define governance rules, appoint stewards through authority-assignment, establish reporting cadence, conduct regular reviews, sunset when purpose is fulfilled.
  - **F:** Pool governance document (an agreement) with all rules, steward appointments, reporting schedule, and current balance transparency.
  - **G-L:** Full structural sections addressing authority limits on stewards, capture resistance for pool governance, failure modes (steward incapacity, pool depletion, rule violations), expiry and review cycles, exit impact on pool contributions, and cross-unit pool federation.
  Include YAML frontmatter with `depends_on: [agreement-creation, authority-assignment, act-consent-phase]`.
  **Acceptance:** All 12 sections substantive. Under 500 lines (before walkthrough and stress tests).

- [ ] **Task 1.8: Write funding-pool-stewardship OmniOne walkthrough and stress tests**
  - Walkthrough: The Economics circle creates a new operational funding pool for the Bali SHUR. Walk through pool creation as an agreement, steward appointment (two co-stewards for accountability), defining threshold tiers using H.A.R.T. principles, first reporting cycle, and one edge case -- what happens when one co-steward exits and a replacement must be appointed mid-cycle.
  - All 7 stress-test scenarios with full narrative paragraphs.
  **Acceptance:** Walkthrough and stress tests meet all quality standards.

- [ ] **Task 1.9: Finalize funding-pool-stewardship SKILL.md and create assets**
  - Assemble full SKILL.md. Create `assets/pool-governance-template.yaml` and `assets/pool-types.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines. Asset templates complete.

- [ ] **Verification 1: Run validate_skill.py against both completed skills. Verify cross-references between resource-request and funding-pool-stewardship are accurate. Confirm both skills independently describe their processes without requiring the other to be loaded.** [checkpoint marker]

---

## Phase 2: Participatory Allocation

**Goal:** Build the participatory allocation skill that defines how funding pool resources are distributed through structured, consent-based assembly processes.

### Tasks

- [ ] **Task 2.1: Draft participatory-allocation SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A:** Without a structured allocation process, funding decisions concentrate in stewards or default to first-come-first-served. This skill ensures resources are allocated through participatory assemblies where every eligible member has voice and allocation decisions are made by consent.
  - **B:** Any domain where a funding pool's resources need to be distributed among competing proposals. Primarily used for circle operational budgets and ecosystem strategic allocations.
  - **C:** A funding pool reaches its allocation cycle date, or the pool steward calls an allocation assembly when accumulated requests exceed discretionary threshold.
  - **D:** Pool governance rules, submitted proposals/resource requests, pool balance, eligible participants, facilitation plan, conflict-of-interest register.
  - **E:** Assembly preparation (announcement, proposal submission window, eligibility verification), deliberation rounds (each proposal presented, questions, concerns), synthesis round (identify overlaps, third solutions for conflicts), allocation round (consent-based, not voting), ratification, documentation.
  - **F:** Allocation record with all proposals considered, deliberation notes, final allocation amounts, consenting positions, stand-asides, and review date.
  **Acceptance:** Sections A-F substantive, describing a complete participatory process.

- [ ] **Task 2.2: Draft participatory-allocation SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G:** Facilitator authority limited to process management (cannot influence allocation outcomes). No participant's allocation weight exceeds any other's regardless of economic contribution. Stewards participate as equals during assembly, not as decision-makers.
  - **H:** Faction coordination (organized blocs pushing allocation), eloquence bias (polished presenters receiving more), urgency manipulation (framing one's request as more urgent to jump queue), steward favoritism (pre-assembly signaling).
  - **I:** Consensus not reached on any allocation (park the item, extend deliberation, do not force). Quorum not met (reschedule, do not lower threshold). Allocation exceeds pool balance (proportional reduction across all approved items or re-deliberate).
  - **J:** Allocation records reviewed at next allocation cycle. Pool governance agreement defines assembly frequency (recommended quarterly).
  - **K:** Exiting members' approved-but-undisbursed allocations are returned to the pool. In-progress allocations follow original stewardship terms.
  - **L:** Cross-ETHOS allocation assemblies require representation from all contributing ETHOS. Facilitation rotates among ETHOS to prevent any one unit from controlling the process.
  **Acceptance:** Sections G-L structurally precise with Ostrom principles embedded.

- [ ] **Task 2.3: Write participatory-allocation OmniOne walkthrough and stress tests**
  - Walkthrough: The AE circle runs its quarterly allocation assembly. Six proposals have been submitted including one from the facilitator (who must recuse from facilitation for that item). Walk through the full assembly: preparation, deliberation (one proposal is controversial -- builds a yoga studio when others want technical infrastructure), third-solution round (the group finds a multi-use space compromise), consent round, one stand-aside documented, allocation record produced.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough and stress tests meet quality standards.

- [ ] **Task 2.4: Finalize participatory-allocation SKILL.md and create assets**
  - Assemble full SKILL.md with frontmatter: `depends_on: [resource-request, funding-pool-stewardship, act-consent-phase]`
  - Create `assets/allocation-assembly-template.yaml` and `assets/allocation-record-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 2: Run validate_skill.py against participatory-allocation. Verify the assembly process references resource-request and funding-pool-stewardship correctly. Confirm the skill can be understood standalone.** [checkpoint marker]

---

## Phase 3: Commons Monitoring

**Goal:** Build the commons monitoring skill that closes the accountability loop by tracking resource flows, detecting over-draw, and triggering graduated community responses.

### Tasks

- [ ] **Task 3.1: Draft commons-monitoring SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A:** Without community monitoring, resource governance becomes opaque and trust erodes. This skill implements Ostrom's Principle 4 (monitoring by community members) by defining transparent tracking of resource flows, community-accessible reporting, and threshold-based alerts that trigger graduated responses rather than punitive action.
  - **B:** Any domain where shared resources are pooled and distributed. Monitors the outputs of resource-request, funding-pool-stewardship, and participatory-allocation skills.
  - **C:** Regular monitoring cycle (defined in pool governance agreement), threshold breach alert, community member concern filing, or annual ecosystem-wide resource review.
  - **D:** Pool governance records, resource request fulfillment records, allocation records, previous monitoring reports, defined thresholds (concentration, flow rate, reciprocity).
  - **E:** Data gathering (compile flows from all pool records), pattern analysis (concentration, sustainability, accessibility), community review session (present findings, gather observations), threshold check (compare against defined limits), report generation, action recommendations (if thresholds breached, trigger graduated response).
  - **F:** Commons health report documenting resource flow patterns, threshold status, community observations, and recommended actions.
  **Acceptance:** Sections A-F substantive, implementing Ostrom principles.

- [ ] **Task 3.2: Draft commons-monitoring SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G:** Monitors have observation authority only, not decision authority. Monitor findings inform ACT decisions but do not trigger automatic actions (except threshold alerts). Monitor role rotates to prevent capture.
  - **H:** Monitor capture (monitors compromised by interests they track), surveillance creep (monitoring expanding from resource flows to individual behavior), data weaponization (monitoring reports used for political attacks rather than governance improvement), monitor fatigue (role becomes burdensome, quality declines).
  - **I:** Monitor role vacant (steward assumes temporary reporting, escalates to circle for appointment). Data incomplete (report what is available, flag gaps). Threshold breach ignored (automatic escalation to next governance level after one cycle).
  - **J:** Monitoring reports are produced per pool governance agreement cycle (recommended quarterly). Monitor role appointments reviewed annually.
  - **K:** Exiting monitors complete their current cycle report. Successor appointed through authority-assignment.
  - **L:** Cross-ETHOS resource flows monitored by representatives from all involved ETHOS. Ecosystem-wide monitoring reports aggregate circle-level reports.
  **Acceptance:** Sections G-L structurally precise.

- [ ] **Task 3.3: Write commons-monitoring OmniOne walkthrough and stress tests**
  - Walkthrough: TH community reviews the quarterly commons health report. The report reveals that the Technology circle has consumed 40% of ecosystem resources over two quarters while representing 15% of membership. Walk through: data presentation (transparent, factual, no blame), community discussion (Technology circle explains infrastructure build phase), threshold comparison (concentration threshold is 30%, breached), graduated response (first breach triggers a participatory review of Technology circle's multi-quarter plan, not punishment), action item (Technology circle submits a resource trajectory proposal to next ecosystem allocation assembly).
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates graduated response, not punitive action.

- [ ] **Task 3.4: Finalize commons-monitoring SKILL.md and create assets**
  - Assemble full SKILL.md with frontmatter: `depends_on: [funding-pool-stewardship, resource-request, participatory-allocation]`
  - Create `assets/commons-health-report-template.yaml` and `assets/monitoring-thresholds.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 3: Run validate_skill.py against commons-monitoring. Verify the skill references earlier Layer IV skills correctly. Confirm monitoring is observation-only with no hidden decision authority.** [checkpoint marker]

---

## Phase 4: Access Economy Transition and Layer Integration

**Goal:** Build the access economy transition skill and finalize the layer with a README, cross-skill review, and quality gates.

### Tasks

- [ ] **Task 4.1: Draft access-economy-transition SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A:** Without a structured transition process, the move from currency-based to access-based economics happens either chaotically (destabilizing existing exchange systems) or never (status quo inertia). This skill defines clear stages, readiness criteria, pilot mechanisms, and rollback procedures so the transition is intentional, testable, and reversible.
  - **B:** Any ecosystem-level or circle-level domain where the economic model is evolving. Primarily applies to SHUR communities and resource-sharing agreements.
  - **C:** A circle or ecosystem body proposes advancing to the next transition stage, or a scheduled readiness assessment is due, or external conditions change the viability of the current stage.
  - **D:** Current stage assessment, readiness indicators for target stage, pilot proposals, rollback criteria, affected agreements, participating circles.
  - **E:** Readiness assessment (evaluate current stage health and target stage prerequisites), proposal through ACT (propose stage advancement with specific pilot scope), pilot execution (test at circle level with defined duration and success criteria using act-test-phase), evaluation, full advancement or rollback decision through ACT.
  - **F:** Transition stage assessment document showing current stage, readiness indicator scores, pilot results (if applicable), and recommended next actions.
  **Acceptance:** Sections A-F substantive, describing a reversible, testable transition process.

- [ ] **Task 4.2: Draft access-economy-transition SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G:** No circle can be compelled to advance stages by another circle or ecosystem body. Transition decisions within a circle use circle-level consent. Ecosystem-wide transitions require ecosystem-level consent. Capital holders have no additional authority over transition timing.
  - **H:** Capital capture (those with currency advantages blocking transition to protect their position), premature enthusiasm (ideological pressure to advance before readiness criteria are met), regression weaponization (threatening rollback to force compliance), external pressure (funders conditioning support on specific transition timelines).
  - **I:** Pilot fails (revert to previous stage, document learnings, no stigma). Readiness assessment incomplete (extend assessment period, do not guess). Circle refuses to advance (their autonomy is respected; they continue at current stage while others advance if ready).
  - **J:** Transition stage assessments conducted annually at minimum. Pilots have defined end dates (recommended 90-180 days). Stage advancement decisions include automatic review dates (recommended 12 months).
  - **K:** Exiting participants' departure does not trigger automatic stage regression. Readiness criteria are reassessed after significant exit events (threshold: 20%+ of participating circle exits).
  - **L:** Different ETHOS may be at different transition stages simultaneously. Inter-ETHOS resource flows use the more conservative stage's protocols (if one ETHOS is at stage 2 and another at stage 3, cross-ETHOS flows use stage 2 rules).
  **Acceptance:** Sections G-L structurally precise, emphasizing reversibility and autonomy.

- [ ] **Task 4.3: Write access-economy-transition OmniOne walkthrough and stress tests**
  - Walkthrough: The Bali SHUR community assesses readiness to move from stage 2 (hybrid currency/Current-See) to stage 3 (Current-See primary) for housing resource allocation. Walk through: readiness assessment (most criteria met, but external vendor relationships still require currency), proposal modification (advance to stage 3 for internal resource flows, maintain stage 2 for external vendor payments), ACT process (advice from all SHUR residents, consent with one reasoned objection about food sourcing -- resolved by carving out food budget), 180-day pilot with defined success criteria, mid-pilot check-in, evaluation.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates nuanced, partial transition rather than all-or-nothing.

- [ ] **Task 4.4: Finalize access-economy-transition SKILL.md and create assets**
  - Assemble full SKILL.md with frontmatter: `depends_on: [funding-pool-stewardship, act-test-phase, agreement-creation]`
  - Create `assets/transition-stages.yaml` and `assets/readiness-assessment-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Task 4.5: Write Layer IV README.md**
  Create `neos-core/layer-04-economic/README.md` summarizing:
  - Layer purpose and relationship to NEOS principles (especially Principle 4: Capital does not equal Power)
  - All 5 skills with brief descriptions and relationships
  - Ostrom principles mapping (which skills implement which Ostrom principles)
  - Cross-layer dependencies (references to Layers I, II, III)
  - OmniOne configuration notes (Current-See types, H.A.R.T. system, transition stages)
  **Acceptance:** README accurately summarizes the layer and its skills.

- [ ] **Task 4.6: Cross-skill review and quality gates**
  Review all 5 skills against the per-skill checklist:
  - [ ] All 12 sections (A-L) present and substantive
  - [ ] OmniOne walkthrough included with specific roles
  - [ ] At least one edge case documented per skill
  - [ ] Stress-tested against all 7 scenarios
  - [ ] No hidden sovereign authority
  - [ ] Exit compatibility confirmed
  - [ ] Cross-unit interoperability impact stated
  - [ ] Capital-power separation explicitly addressed
  Additionally:
  - Verify cross-references between Layer IV skills are consistent
  - Verify terminology matches product-guidelines.md throughout
  - Verify no skill exceeds 500 lines
  **Acceptance:** All 5 skills pass all quality gates. Layer is internally consistent.

- [ ] **Verification 4: Run validate_skill.py against entire layer-04-economic/ directory. All 5 skills pass. README exists. Cross-references verified. Layer is complete.** [checkpoint marker]
