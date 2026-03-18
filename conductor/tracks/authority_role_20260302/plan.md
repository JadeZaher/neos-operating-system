# Implementation Plan: Authority & Role Layer (Layer II)

## Overview

This plan builds 7 governance skills for NEOS Layer II plus a foundation integration phase, organized into 6 phases. The interleaved build order ensures the anchor skill (domain-mapping) is established first, then skills are built in dependency order so each new skill can reference concrete, already-written skills.

**Total skills:** 7
**Total phases:** 6 (5 skill-building phases + 1 integration phase)
**Estimated scope:** 25-35 hours of focused implementation
**Prerequisite:** Foundation track (foundation_20260301) must be complete. All 11 Layer I and Layer III skills, validate_skill.py, and the SKILL_TEMPLATE.md must exist.

### Build Order Rationale

Domain-mapping is the anchor -- every other skill references the 11-element domain contract it defines. Member-lifecycle comes second because you need to know who is a participant before you can assign them roles. Role-assignment comes third because role-transfer, domain-review, and role-sunset all reference assigned roles. Authority-boundary-negotiation is built early because overlaps are inevitable once domains are mapped. The lifecycle order mirrors the real-world sequence: define the domain, identify the person, assign them, handle disputes, transfer when needed, review periodically, sunset when done.

### Commit Strategy

- One commit per completed skill: `neos(layer-02): Add <skill-name> skill`
- Layer-level commit when all skills done: `neos(layer-02): Complete layer 02 - Authority & Role`
- Integration commits: `neos(layer-XX): Update <skill-name> with Layer II authority references`

---

## Phase 1: Scaffolding and Anchor Skill

**Goal:** Create the Layer II directory structure and build the anchor skill (domain-mapping) that defines the 11-element domain contract. After this phase, every other Layer II skill has a concrete schema to reference.

### Tasks

- [x] **Task 1.1: Create Layer II directory scaffolding**
  Create the full directory tree:
  ```
  neos-core/
    layer-02-authority/
      README.md (empty placeholder)
      domain-mapping/         (SKILL.md, assets/, references/, scripts/)
      authority-boundary-negotiation/ (same structure)
      role-assignment/        (same structure)
      role-transfer/          (same structure)
      domain-review/          (same structure)
      role-sunset/            (same structure)
      member-lifecycle/       (same structure)
  ```
  Each skill directory gets an empty `SKILL.md` and empty `assets/`, `references/`, `scripts/` subdirectories.
  **Acceptance:** All directories exist. `find neos-core/layer-02-authority -name SKILL.md | wc -l` returns 7.

- [x] **Task 1.2: Draft domain-mapping SKILL.md -- sections A through F**
  Using the SKILL_TEMPLATE.md, fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without formal domain definitions, authority is assumed, informal, and inconsistent. Participants do not know the boundaries of their decision-making scope. Disputes become personal because there is no structural reference to adjudicate. This skill provides the canonical schema for defining what authority looks like.
  - **B. Domain Scope:** Any circle, role, or structural body that exercises governance authority within the ecosystem. Applies to new domain creation and refinement of existing domains.
  - **C. Trigger Conditions:** A new circle or role is formed, an existing role lacks a formal domain definition, a domain-review recommends refinement, an authority-boundary-negotiation requires domain contract amendments.
  - **D. Required Inputs:** The delegating body identity, the proposed domain purpose, the context in which the domain operates (parent domain, adjacent domains, ecosystem structure).
  - **E. Step-by-Step Process:** (1) Delegating body identifies the need for a new domain or refinement. (2) Drafting: fill in all 11 elements of the domain contract. For each element, the drafter consults existing domain contracts to identify dependencies and potential overlaps. (3) Review: present the draft to the delegating body and any adjacent domain stewards for feedback. (4) Consent: delegating body runs an ACT consent process on the domain contract. (5) Registration: the completed domain contract is registered and linked to any role assignment. (6) Notification: all adjacent domains are notified of the new or refined domain.
  - **F. Output Artifact:** A complete domain contract document with all 11 elements. The contract is versioned (starting at 1.0.0) and has a unique domain ID.
  Write with full substance. Reference S3 framework by name but make the process NEOS-native.
  **Acceptance:** Sections A-F are substantive (3+ lines each), terminology matches product-guidelines.md.

- [x] **Task 1.3: Draft domain-mapping SKILL.md -- sections G through L**
  Complete the remaining structural sections:
  - **G. Authority Boundary Check:** Only a delegating body can create a domain through an ACT consent process. No individual can self-declare a domain. The domain-mapping skill itself operates under a meta-authority: the initial domain structure of a new ecosystem is defined by the founding body through consensus. Subsequent domains are created by existing bodies through consent. A domain holder cannot expand their own domain -- expansion must be consented to by the delegating body.
  - **H. Capture Resistance Check:** Authority creep by precedent (acting beyond scope and claiming it as established practice -- the constraints element explicitly bounds authority, domain-review catches drift). Charismatic capture (a leader defines their domain with deliberately vague constraints to maximize discretion -- the review process evaluates constraint specificity). Domain hoarding (one body creates many domains to accumulate influence -- domain count per body is tracked and reviewed).
  - **I. Failure Containment Logic:** Incomplete domain contract (any missing element flags the domain as "provisional" -- it can operate for 30 days but must be completed or it reverts to its delegating body). Contested domain (two bodies claim authority to create the same domain -- routes to authority-boundary-negotiation). Abandoned domain (steward stops fulfilling responsibilities -- domain-review triggers reassignment or sunset).
  - **J. Expiry / Review Condition:** Every domain contract must include an evaluation schedule (element 12 of the S3 model, incorporated as element 11 here). Default: 6-month evaluation cycle. Domains without evaluation schedules are flagged by validate_skill.py as incomplete. If the evaluation date passes without review: 30-day grace period with escalation notice, then the delegating body is required to convene a review.
  - **K. Exit Compatibility Check:** When a domain steward exits the ecosystem, the domain does not dissolve. It enters "vacant" status. The delegating body has 30 days to assign a new steward (via role-assignment) or trigger role-sunset. Pending commitments held by the exiting steward are inventoried and transferred.
  - **L. Cross-Unit Interoperability Impact:** Domains in one ETHOS may have dependencies on domains in another ETHOS. The domain contract's dependencies element must explicitly list cross-unit dependencies. When a domain is created or refined in one ETHOS, dependent domains in other ETHOS are notified.
  **Acceptance:** Sections G-L are substantive and structurally precise. Meta-authority for domain creation is explicitly addressed.

- [x] **Task 1.4: Write domain-mapping OmniOne walkthrough**
  Write a full narrative walkthrough:
  - Scenario: The AE decides to create a new Economics circle. The AE (delegating body) drafts a domain contract:
    - Purpose: Steward the ecosystem's economic coordination, including resource allocation, funding pool management, and economic policy proposals.
    - Key Responsibilities: Manage funding requests, maintain economic transparency, propose resource distribution changes, coordinate with external partners on economic matters.
    - Customers: All ecosystem participants who request or receive resources, ETHOS with budgets.
    - Deliverables: Monthly economic transparency reports, funding request decisions, economic policy proposals.
    - Dependencies: Depends on OSC for ecosystem-level economic policy approval, depends on agreement-registry for tracking economic agreements.
    - Constraints: Cannot approve funding above 10% of total pool without OSC consent. Cannot create economic agreements that contradict the UAF. Cannot grant Current-See advantages to any role.
    - Challenges: Balancing rapid resource access with accountability, maintaining transparency at scale, preventing capital capture.
    - Resources: Access to ecosystem financial data, one dedicated meeting slot per week, budget for external economic consultation.
    - Delegator Responsibilities: AE provides the Economics circle with timely information on ecosystem-level economic decisions, reviews the domain at the scheduled evaluation, does not micromanage circle-internal decisions.
    - Competencies: Understanding of commons-based economics, facilitation skills, financial transparency practices.
    - Metrics: Time-to-decision on funding requests (target: 14 days), participant satisfaction with economic transparency (quarterly survey), percentage of funding requests processed within the cycle.
    - Evaluation Schedule: Every 6 months, first evaluation 6 months from creation date.
  - Edge case: During the consent round, an AE member points out that the "external partners" responsibility overlaps with the existing Partnerships circle's domain. The AE notes this as a dependency rather than a responsibility and schedules an authority-boundary-negotiation between the new Economics circle and the Partnerships circle.
  - Output: The completed domain contract document.
  **Acceptance:** Walkthrough names specific roles, shows all 11 elements filled, includes edge case, ends with artifact.

- [x] **Task 1.5: Write domain-mapping stress-test results (all 7 scenarios)**
  Write full narrative stress tests:
  1. **Capital Influx:** A major donor offers to fund the ecosystem contingent on a new "Donor Relations" domain being created with deliberately broad constraints (allowing the donor's representative to influence resource allocation). Walk through how the domain-mapping process structurally prevents this: the constraints element must be specific, the consent process flags the capture risk, and the domain-review cycle provides ongoing check.
  2. **Emergency Crisis:** A natural disaster requires rapid creation of an "Emergency Coordination" domain. Walk through expedited domain creation with provisional status (30-day operation window), minimal but complete domain contract, and mandatory full review once the crisis stabilizes.
  3. **Leadership Charisma Capture:** A charismatic leader defines their domain with vague constraints ("do whatever is needed for ecosystem health") to maximize discretion. Walk through how the consent process challenges vague constraints, how adjacent domain stewards flag the overlap risk, and how domain-review catches scope creep.
  4. **High Conflict / Polarization:** Two factions want the same domain defined differently (one faction wants a centralized economics domain, the other wants distributed sub-domains). Walk through how the consent process surfaces both perspectives, how the coaching escalation (GAIA Level 4) finds a structural third solution (federated sub-domains with a coordination layer).
  5. **Large-Scale Replication:** The ecosystem grows from 5 domains to 200. Walk through how domain-mapping scales: domain contracts are self-documenting, the dependencies element creates a navigable graph, domain-review cycles prevent stale domains, and nested delegation keeps any single body's domain count manageable.
  6. **External Legal Pressure:** A government requires the ecosystem to have a "compliance officer" role with authority that contradicts NEOS principles (unilateral override power). Walk through how the domain contract's constraints element structurally prevents unilateral authority, while the domain can be defined to include regulatory compliance responsibilities within NEOS-compatible boundaries.
  7. **Sudden Exit of 30%:** Nearly a third of domain stewards leave simultaneously. Walk through how the vacant domain protocol activates, delegating bodies prioritize essential domains for reassignment, non-essential domains are fast-tracked through role-sunset, and the 30-day assignment window prevents governance paralysis.
  Each scenario must be a full narrative paragraph (5+ sentences).
  **Acceptance:** All 7 scenarios are full narratives. Each demonstrates how a specific domain-mapping mechanism handles the stress.

- [x] **Task 1.6: Finalize domain-mapping SKILL.md and create assets**
  - Assemble SKILL.md from Tasks 1.2-1.5 with YAML frontmatter:
    ```yaml
    ---
    name: domain-mapping
    description: "Define or refine a governance domain using the 11-element contract -- purpose, responsibilities, customers, deliverables, dependencies, constraints, challenges, resources, delegator responsibilities, competencies, metrics, evaluation schedule -- so that authority scope is explicit, bounded, and reviewable."
    layer: 2
    version: 0.1.0
    depends_on: []
    ---
    ```
  - Create `assets/domain-contract-template.yaml`:
    ```yaml
    domain_id: ""
    version: "1.0.0"
    status: draft | provisional | active | under_review | vacant | sunset | archived
    created_date: ""
    created_by: ""  # delegating body
    elements:
      purpose: ""
      key_responsibilities: []
      customers: []
      deliverables: []
      dependencies: []
      constraints: []
      challenges: []
      resources: []
      delegator_responsibilities: []
      competencies: []
      metrics:
        - metric: ""
          target: ""
          measurement_method: ""
      evaluation_schedule:
        cadence: "6 months"
        next_evaluation_date: ""
        review_body: []
    current_steward: ""  # null if vacant
    assignment_history: []
    amendment_history: []
    ```
  - Run `validate_skill.py` against the completed SKILL.md.
  **Acceptance:** SKILL.md passes validation. Under 500 lines (overflow stress tests to `references/stress-tests.md` if needed). Asset template is complete.

- [x] **Verification 1: Run validate_skill.py against domain-mapping SKILL.md, confirm pass. Verify the 11-element domain contract is complete and internally consistent. Confirm the asset template matches the elements described in the skill.** [checkpoint marker]

---

## Phase 2: Member Lifecycle and Role Assignment

**Goal:** Build the two skills that establish who is a participant (member-lifecycle) and how people are assigned to domains (role-assignment). After this phase, the ecosystem can define domains, track members, and assign stewards.

### Tasks

- [x] **Task 2.1: Draft member-lifecycle SKILL.md -- sections A through F**
  - **A. Structural Problem It Solves:** Without formal lifecycle tracking, ecosystems cannot distinguish active participants from disengaged ones. Quorum calculations become unreliable. Consent records include people who have effectively left. This skill provides structural clarity on who is participating and what their status means.
  - **B. Domain Scope:** Every individual participant in the ecosystem. This skill governs transitions between lifecycle states, not governance authority (which is governed by role-assignment and domain-mapping).
  - **C. Trigger Conditions:** A prospective member requests to join, a member's participation drops below the activity threshold, an inactive member requests reactivation, a member initiates voluntary exit.
  - **D. Required Inputs:** For onboarding: prospective member identity, UAF document, facilitator identity. For inactivity: participation log showing no governance activity for the threshold period. For reactivation: reactivation request and attendance at one governance session. For exit: voluntary exit declaration.
  - **E. Step-by-Step Process:** Define the full process for each transition: prospective-to-onboarding, onboarding-to-active, active-to-inactive, inactive-to-reactivating, reactivating-to-active, active-to-exiting, exiting-to-exited. The onboarding consent ceremony is the most detailed: (1) prospective member receives UAF, (2) facilitated walkthrough with Q&A, (3) 48-hour cooling-off period, (4) explicit section-by-section consent, (5) consent recorded in agreement registry, (6) profile assignment, (7) status transitions to active.
  - **F. Output Artifact:** Lifecycle record documenting: member identity, current status, all status transitions with dates and triggers, consent record from onboarding, profile assignment, roles held (cross-reference to role-assignment records).
  **Acceptance:** Sections A-F complete. All lifecycle states and transitions defined. Onboarding consent ceremony is detailed enough for a facilitator to follow.

- [x] **Task 2.2: Draft member-lifecycle SKILL.md -- sections G through L, walkthrough, and stress tests**
  - **G.** The facilitator running the onboarding ceremony has process authority but not content authority -- they cannot modify the UAF or waive sections. Profile assignment is proposed by the onboarding facilitator and consented to by the relevant council (TH for TownHall profile, AE for Builder/Co-creator). Inactive status is triggered automatically by participation data, not by anyone's judgment call.
  - **H.** Capture: pressured onboarding (rushing the consent ceremony to inflate member counts -- the 48-hour cooling-off period prevents this). Selective inactivity enforcement (targeting certain members for inactivity while ignoring others -- the 1-month threshold is applied uniformly by participation data, not by discretion). Gate-keeping (blocking onboarding for political reasons -- the consent ceremony process is open to anyone; the only bar is UAF consent).
  - **I-L.** Full structural sections addressing: failed onboarding (prospective member cannot consent to a UAF section -- they are not denied entry but the specific objection is recorded and may surface as a UAF review item), contested inactivity (member claims they were active but their activity was not recorded -- 14-day response window allows correction), mass exit impact (30% exit triggers quorum recalculation across all active consent processes).
  - OmniOne walkthrough (dual scenario as specified in AC-7.6).
  - All 7 stress tests as full narratives.
  **Acceptance:** Full SKILL.md passes validation. Under 500 lines (overflow to references/ if needed).

- [x] **Task 2.3: Create member-lifecycle assets**
  Create `assets/lifecycle-record-template.yaml`:
  ```yaml
  member_id: ""
  display_name: ""
  current_status: prospective | onboarding | active | inactive | reactivating | exiting | exited
  profile: co_creator | builder | collaborator | townhall
  onboarding_record:
    facilitator: ""
    uaf_version_consented: ""
    consent_date: ""
    cooling_off_start: ""
    cooling_off_end: ""
    section_consents:
      - section: ""
        consented: true | false
        notes: ""
  status_transitions:
    - from_status: ""
      to_status: ""
      date: ""
      trigger: ""
      notes: ""
  roles_held: []  # cross-reference to role-assignment records
  last_governance_activity_date: ""
  inactivity_notice_date: ""
  ```
  Create `assets/onboarding-checklist.md` with a step-by-step facilitator guide for the consent ceremony.
  **Acceptance:** Both assets complete. Template referenced in SKILL.md.

- [x] **Task 2.4: Draft role-assignment SKILL.md -- full skill (sections A-L)**
  Build the complete role-assignment skill:
  - **A.** Without formal assignment, people assume roles informally. Authority scope is undefined. When disputes arise, there is no record of who was authorized to do what. This skill ensures every steward has explicit, consented-to authority.
  - **B.** Any domain that requires a human steward. References domain-mapping for the domain contract and member-lifecycle for participant status verification.
  - **C.** A new domain is created and needs a steward, a domain becomes vacant (steward exit, role-transfer, or role-sunset of a predecessor role), a domain-review recommends reassignment.
  - **D.** Domain contract (complete, not provisional), candidate person (must be in "active" lifecycle status), assigning body identity, proposed assignment duration, conflict-of-interest disclosure.
  - **E.** (1) Verify domain contract completeness (all 11 elements). (2) Verify candidate is in "active" status via member-lifecycle. (3) Check candidate against competency requirements (domain contract element 10). (4) Candidate reviews full domain contract -- especially constraints and metrics -- and formally accepts or negotiates terms. (5) Conflict-of-interest check: if candidate holds other roles, flag any domain overlaps. (6) Assigning body runs consent process (or consensus for OSC-level roles). (7) Assignment registered with start date, review date, and link to domain contract. (8) Adjacent domains notified.
  - **F.** Role assignment record linking person to domain with defined term.
  - **G.** Only the delegating body can assign. Self-assignment prohibited. Role cap: recommended maximum of 3 active steward roles per person (configurable per ecosystem). Dual-role overlap must be disclosed and reviewed.
  - **H.** Role accumulation capture (one person collects roles to consolidate informal power), competency theater (assigning body rubber-stamps competency verification), forced assignment (pressuring someone to accept a role they do not want).
  - **I-L.** Full structural sections.
  Include YAML frontmatter with `depends_on: [domain-mapping, member-lifecycle]`.
  **Acceptance:** Passes validation. Under 500 lines.

- [x] **Task 2.5: Write role-assignment OmniOne walkthrough and stress tests**
  - Walkthrough: A Co-creator is nominated to steward the newly defined Economics circle. Walk through: competency verification (the candidate has experience with commons-based economics), candidate reviews the domain contract and negotiates one metric target (request to extend time-to-decision from 14 to 21 days for the first evaluation period), AE runs consent round, one member raises a concern about the candidate already holding the Partnerships circle steward role -- conflict-of-interest check reveals potential overlap on "external partner" responsibilities. The overlap is noted and an authority-boundary-negotiation is scheduled. Assignment proceeds with the overlap flagged. Edge case: the candidate holds Builder profile (commenting access) but is assigned a steward role -- domain authority is independent of platform access level.
  - All 7 stress tests, each specific to role-assignment dynamics.
  **Acceptance:** Walkthrough and stress tests complete. Full SKILL.md passes validation.

- [x] **Task 2.6: Create role-assignment assets**
  Create `assets/role-assignment-template.yaml`:
  ```yaml
  assignment_id: ""
  domain_id: ""
  domain_contract_version: ""
  assignee_member_id: ""
  assigning_body: ""
  assignment_date: ""
  review_date: ""
  assignment_duration: ""
  status: active | under_review | transferred | ended
  competency_verification:
    verified_by: ""
    date: ""
    competencies_met: []
    competencies_partial: []
    notes: ""
  conflict_of_interest:
    other_roles_held: []
    overlaps_identified: []
    mitigation: ""
  consent_record_id: ""
  candidate_acceptance_date: ""
  ```
  **Acceptance:** Template complete and referenced in SKILL.md.

- [x] **Verification 2: Run validate_skill.py against domain-mapping, member-lifecycle, and role-assignment. All must pass. Verify cross-references: role-assignment references domain-mapping for domain contracts and member-lifecycle for status checks. Confirm the onboarding consent ceremony in member-lifecycle correctly references the UAF from Layer I.** [checkpoint marker]

---

## Phase 3: Boundary Negotiation and Role Transfer

**Goal:** Build the skills that handle domain disputes (authority-boundary-negotiation) and role handoffs (role-transfer). After this phase, the ecosystem can create domains, assign stewards, resolve overlaps, and transfer roles.

### Tasks

- [x] **Task 3.1: Draft authority-boundary-negotiation SKILL.md -- full skill (sections A-L)**
  Build the complete boundary negotiation skill:
  - **A.** Without a negotiation process, domain overlaps are resolved by informal power -- whoever has more influence claims the territory. This skill provides an integrative process where both domains' core purposes are preserved.
  - **B.** Any situation where two or more domain contracts claim authority over the same area, or where a decision or action falls in ambiguous territory between domains.
  - **C.** Explicit boundary dispute raised by a steward, ambiguity discovered during an ACT process (e.g., a proposal touches two domains and neither is sure who consents), overlap flagged during domain-review, conflict arising from competing domain claims in practice.
  - **D.** The domain contracts of all involved domains, the specific area of overlap or ambiguity, any precedent from prior boundary resolutions, the context that surfaced the dispute.
  - **E.** (1) Identify the specific overlap using domain contract elements (which responsibilities, deliverables, or customers are claimed by both?). (2) Convene affected domain stewards and their delegating bodies. (3) Map each domain's claim against their 11 elements -- where does the overlap appear? (4) Identify the structural source: shared responsibility (both domains were given the same responsibility), unclear constraint (one domain's boundary is not specific enough), missing dependency (the domains should depend on each other but neither lists it), scope creep (one domain expanded beyond its original definition). (5) Integrative discussion: brainstorm resolution options that preserve both domains' core purposes. Options include: clarify boundaries (make constraints more specific), create a shared responsibility protocol, split the contested area into sub-domains, establish a dependency relationship. (6) Consent: the resolution is consented to by all affected domain stewards and their delegating bodies. (7) Amend affected domain contracts to reflect the resolution. (8) Register the boundary resolution as a precedent for future disputes.
  - **F.** Boundary resolution record documenting overlap, discussion, resolution, and amended domain contracts.
  - **G.** No single domain can unilaterally claim contested territory. The negotiation requires consent from all affected parties. If the delegating bodies themselves conflict, escalation follows GAIA Level 4 (Coaching). A neutral facilitator (not a steward of either domain) is required.
  - **H.** Power asymmetry (larger domain pressures smaller to cede territory -- the facilitator ensures both domains' purposes are structurally equal in the discussion). Political alliances (multiple domains coordinate to squeeze out a third -- each domain is evaluated on its own contract, not on political alignment). Precedent manipulation (citing prior boundary resolutions selectively to advantage one party -- the full resolution record is referenced, not summaries).
  - **I.** Stalled negotiation: after 3 sessions without resolution, automatic escalation to GAIA Level 4. Contested resolution: one party does not consent -- escalation to delegating bodies or GAIA Level 5. Post-resolution relapse: same boundary dispute recurs within 6 months -- triggers a structural review of whether the domains should be merged.
  - **J.** Boundary resolutions are reviewed alongside the domain-review of either involved domain. If a resolution is older than 12 months and neither domain has been reviewed, a standalone review is triggered.
  - **K.** If a steward in a boundary dispute exits, their domain enters vacant status. The dispute is paused until a new steward is assigned or the domain is sunset.
  - **L.** Cross-ETHOS boundary disputes follow the same process but require facilitators from neither ETHOS. Resolution records are shared with both ETHOS' registries.
  Include YAML frontmatter with `depends_on: [domain-mapping]`.
  **Acceptance:** Passes validation. Under 500 lines.

- [x] **Task 3.2: Write authority-boundary-negotiation walkthrough and stress tests**
  - Walkthrough: The Economics circle and the Stewardship circle in OmniOne both claim authority over resource allocation approval. The Economics circle's domain contract lists "manage funding requests" as a key responsibility. The Stewardship circle's domain contract lists "ensure responsible resource stewardship" as a key responsibility. A Builder submits a funding request of 500 USDT and both circles believe they should approve it. A neutral facilitator (from TH, not a member of either circle) convenes the negotiation. Mapping reveals: Economics has approval authority for amounts under 10% of pool; Stewardship has audit and accountability authority for all resource usage. The structural source is "shared responsibility" -- both were given resource-related responsibilities without clear handoff. Resolution: Economics approves funding requests; Stewardship audits resource usage post-allocation and can trigger a review if stewardship principles are violated. Domain contracts are amended with a dependency: Economics depends on Stewardship for post-allocation review. Edge case: what if the Stewardship audit finds a problem with an already-disbursed allocation? The resolution record specifies that Stewardship can trigger a clawback proposal through the ACT process but cannot unilaterally reverse an allocation.
  - All 7 stress tests as full narratives.
  **Acceptance:** Walkthrough and stress tests complete. Full SKILL.md passes validation.

- [x] **Task 3.3: Create authority-boundary-negotiation assets**
  Create `assets/boundary-resolution-template.yaml`:
  ```yaml
  resolution_id: ""
  date: ""
  facilitator: ""
  involved_domains:
    - domain_id: ""
      steward: ""
      delegating_body: ""
  overlap_description: ""
  structural_source: shared_responsibility | unclear_constraint | missing_dependency | scope_creep
  discussion_summary: ""
  resolution_options_considered: []
  selected_resolution: ""
  domain_contract_amendments:
    - domain_id: ""
      elements_amended: []
      amendment_summary: ""
  consent_record_id: ""
  review_trigger: ""  # date or condition for reviewing this resolution
  precedent_tags: []  # for Layer IX memory integration
  ```
  **Acceptance:** Template complete.

- [x] **Task 3.4: Draft role-transfer SKILL.md -- full skill (sections A-L)**
  Build the complete role-transfer skill:
  - **A.** Without a transfer process, role changes are abrupt. Institutional knowledge is lost. Pending commitments fall through cracks. Dependent domains are surprised by sudden changes in their counterpart. This skill ensures continuity through structured handover.
  - **B.** Any role assignment that is changing stewards, whether voluntarily or through reassignment.
  - **C.** Voluntary step-down by current steward, scheduled rotation per domain contract, domain-review recommendation for reassignment, current steward transitions to inactive status (per member-lifecycle), role-sunset that creates a successor role requiring transfer of responsibilities.
  - **D.** Current steward identity, incoming steward identity (from role-assignment process), domain contract, all active agreements held by the current steward in this role, all pending commitments, relationship map (adjacent domains, dependent domains).
  - **E.** (1) Outgoing steward creates handover document: inventory of pending commitments, active agreements held, decision context (why things are the way they are), relationship map, known challenges, upcoming deadlines. (2) Incoming steward reviews domain contract and handover document. (3) Overlap period: minimum 2 weeks recommended; during overlap, both stewards attend governance sessions, outgoing introduces incoming to adjacent domain stewards. (4) Incoming steward formally accepts the domain contract (same process as role-assignment acceptance). (5) Assigning body consents to the transfer. (6) Assignment record updated: outgoing steward's record marked as "transferred," incoming steward's record created. (7) Notification to all dependent and adjacent domains. (8) 30-day post-transfer check-in: incoming steward and delegating body confirm the transfer is complete.
  - **F.** Transfer record with handover summary, consent record, and updated assignment records for both stewards.
  - **G-L.** Full structural sections. Special attention to I (Failure Containment): involuntary transfer (steward objects), no qualified successor (vacant status with temporary delegating body stewardship), incomplete handover (mandatory minimum checklist).
  Include OmniOne walkthrough: Scheduled rotation of the OSC meeting facilitator role. The outgoing facilitator prepares a handover document listing pending agenda items, ongoing GAIA escalations, and relationship notes with each council member. The incoming facilitator shadows 2 meetings during the overlap period. Edge case: the incoming facilitator raises a concern about one pending agenda item that they believe should have been resolved before transfer -- the handover process requires explicit acknowledgment of open items, and the outgoing steward cannot transfer until all items are either resolved or explicitly accepted by the incoming steward.
  All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. Handover process is detailed enough for practical use.

- [x] **Task 3.5: Create role-transfer assets**
  Create `assets/transfer-record-template.yaml`:
  ```yaml
  transfer_id: ""
  domain_id: ""
  domain_contract_version: ""
  outgoing_steward: ""
  incoming_steward: ""
  transfer_trigger: voluntary | rotation | reassignment | inactivity | sunset_successor
  handover_document:
    pending_commitments: []
    active_agreements_held: []
    decision_context: ""
    relationship_map: []
    known_challenges: []
    upcoming_deadlines: []
  overlap_period:
    start_date: ""
    end_date: ""
    sessions_attended_together: 0
  consent_record_id: ""
  transfer_date: ""
  post_transfer_checkin_date: ""
  post_transfer_checkin_status: complete | issues_identified
  ```
  Create `assets/handover-checklist.md` with a structured checklist for outgoing stewards.
  **Acceptance:** Both assets complete.

- [x] **Verification 3: Run validate_skill.py against all 5 completed skills. All must pass. Verify: authority-boundary-negotiation correctly references domain-mapping for domain contracts, role-transfer correctly references role-assignment for the incoming steward's assignment process. Check that the handover checklist in role-transfer assets covers all items mentioned in the skill's step-by-step process.** [checkpoint marker]

---

## Phase 4: Domain Review and Role Sunset

**Goal:** Build the skills that close the lifecycle loop: scheduled domain evaluation (domain-review) and domain dissolution (role-sunset). After this phase, all 7 Layer II skills are complete.

### Tasks

- [x] **Task 4.1: Draft domain-review SKILL.md -- full skill (sections A-L)**
  Build the complete domain-review skill:
  - **A.** Without periodic review, domains accumulate scope creep, stewards become entrenched, and the domain contract drifts from actual practice. This skill is the authority layer's immune system -- it catches decay before it becomes structural damage.
  - **B.** Any active domain contract with an evaluation schedule.
  - **C.** Scheduled evaluation date arrives (from the domain contract's evaluation schedule element), domain steward requests early review, delegating body requests review, threshold event (30% participant exit, major restructuring, pattern of boundary disputes involving this domain).
  - **D.** The domain contract, the steward's performance data against defined metrics, feedback from customers and dependent domains, any boundary resolution records involving this domain, any audit or compliance observations.
  - **E.** (1) Convene review body: delegating body members + domain steward + representatives from dependent domains (advisory, not voting). (2) Element-by-element evaluation: Is the purpose still relevant? Are responsibilities still accurate? Have customers changed? Are deliverables being produced? Are dependencies current? Are constraints being respected? Have new challenges emerged? Are resources adequate? Is the delegating body fulfilling its responsibilities? Does the steward meet competency requirements? Are metrics being met? (3) Steward effectiveness assessment: direct feedback from customers and dependent domains, metric performance, qualitative assessment of domain health. (4) Determine outcome: reaffirm (set new review date, no changes), refine (amend specific domain contract elements, trigger domain-mapping for the amendments), reassign (trigger role-transfer with a new steward), merge (combine with another domain, trigger authority-boundary-negotiation to define the merged domain), sunset (trigger role-sunset). (5) Document the review record. (6) Update the domain contract with new evaluation date.
  - **F.** Domain review record documenting element-by-element evaluation, steward assessment, outcome, and next actions.
  - **G.** Review body must include the delegating body -- the steward cannot self-review without oversight. The steward participates in the review but does not have veto power over the outcome. The review is a consent process among the delegating body members.
  - **H.** Stewards resisting review to maintain authority (review dates are structural, not optional -- missed review triggers automatic escalation). Delegating bodies weaponizing review for political removal (the review is element-by-element against the domain contract, not a popularity vote -- removal requires demonstrated metric failure or constraint violation). Review fatigue (too-frequent reviews disrupting productive work -- minimum 3-month interval between reviews, default 6-month cycle).
  - **I-L.** Full structural sections.
  OmniOne walkthrough: 6-month domain review of the Community Engagement circle. The review reveals that one key responsibility (event coordination) has been informally handled by the Media circle for the past 3 months. The review body decides to refine: remove event coordination from Community Engagement's domain contract and trigger an authority-boundary-negotiation to formally add it to Media's domain. Steward assessment is positive -- the drift was structural, not a steward failure. Edge case: the delegating body's own responsibilities (element 9) have not been met -- they failed to provide timely information on ecosystem events. The review body notes this and the delegating body commits to a remediation action.
  All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines.

- [x] **Task 4.2: Create domain-review assets**
  Create `assets/domain-review-template.yaml`:
  ```yaml
  review_id: ""
  domain_id: ""
  domain_contract_version: ""
  review_type: scheduled | requested_by_steward | requested_by_delegator | threshold_event
  trigger: ""
  review_body:
    - name: ""
      role: ""  # delegator | steward | dependent_domain | advisory
  date: ""
  element_evaluation:
    - element: ""  # purpose, key_responsibilities, etc.
      current_state: ""
      assessment: adequate | needs_refinement | outdated | not_applicable
      notes: ""
  steward_assessment:
    metric_performance:
      - metric: ""
        target: ""
        actual: ""
        met: true | false
    customer_feedback_summary: ""
    dependent_domain_feedback_summary: ""
    qualitative_assessment: ""
  outcome: reaffirm | refine | reassign | merge | sunset
  follow_up_actions:
    - action: ""
      type: domain_mapping | role_transfer | authority_boundary_negotiation | role_sunset
      responsible: ""
      deadline: ""
  next_evaluation_date: ""
  ```
  **Acceptance:** Template complete.

- [x] **Task 4.3: Draft role-sunset SKILL.md -- full skill (sections A-L)**
  Build the complete role-sunset skill:
  - **A.** Without a sunset process, defunct roles linger as zombies -- technically existing but serving no purpose, sometimes reanimated by opportunistic actors to claim authority. This skill ensures that when a domain has served its purpose, it is formally dissolved with all responsibilities accounted for.
  - **B.** Any domain that is no longer needed, has been absorbed by other domains, or has been vacant for longer than 2 review cycles.
  - **C.** Domain-review recommends sunset, the domain's purpose has been explicitly achieved, all key responsibilities have been formally transferred to other domains, the domain has been vacant for longer than 2 consecutive review cycles (default: 12 months), the delegating body proposes dissolution.
  - **D.** The domain contract, the list of all active agreements held by or referencing this domain, the list of all dependent domains, the current steward (if any), the proposed disposition for each responsibility and agreement.
  - **E.** (1) Inventory: list all pending commitments, active agreements, and dependent domains. (2) Disposition plan: for each responsibility, specify where it goes (transferred to named domain, explicitly ended, or absorbed by delegating body). For each agreement, specify: transferred to successor domain, sunset through agreement-review, or archived. For each dependent domain, specify: dependency removed (the dependency no longer exists) or dependency redirected (to a different domain). (3) Notify all affected parties of the proposed sunset and disposition plan. (4) Delegating body runs consent process on the sunset. For ecosystem-level domains, OSC consensus is required. (5) Execute disposition: transfer responsibilities and agreements, update dependent domain contracts, archive the domain contract with sunset date, rationale, and disposition record. (6) 90-day grace period: if orphaned responsibilities are discovered within 90 days, the domain can be reactivated by the delegating body without a full creation process.
  - **F.** Sunset record with archived domain contract, disposition plan, consent record, and 90-day reactivation window.
  - **G.** Only the delegating body can sunset a domain. The steward can propose sunset but cannot execute it unilaterally. The steward cannot be forced to continue operating a domain they believe should be sunset -- they can step down through role-transfer, leaving the domain vacant, which eventually triggers sunset through the 2-cycle vacancy rule.
  - **H.** Premature sunset to remove an inconvenient domain (the consent process requires demonstrated rationale, not political convenience). Sunset resistance to preserve personal authority (the vacancy rule provides a structural path to sunset regardless of steward preference). Zombie resurrection (reactivating a sunset domain to claim historical authority -- the 90-day grace period is explicit, after which reactivation requires a full domain-mapping process).
  - **I-L.** Full structural sections.
  OmniOne walkthrough: Sunsetting the temporary Trunk Council key-holding role. The Trunk Council was created to hold decision-making authority during OmniOne's formation phase, with an explicit sunset condition: "when permanent circles are established and can hold these responsibilities." Domain-review confirms all 4 permanent councils (TH, AE, OSC, GEV) are operational. Disposition plan: each Trunk Council responsibility is mapped to a permanent council. Two agreements held by the Trunk Council are transferred to OSC. One pending commitment (completion of the economic framework) is transferred to the Economics circle. Consent is achieved by OSC consensus. The Trunk Council domain contract is archived with the note: "Purpose achieved -- authority distributed to permanent governance structure." Edge case: 60 days after sunset, a dependent domain discovers that one responsibility (emergency key rotation) was not included in the disposition plan. The 90-day grace period activates: the responsibility is assigned to OSC through an expedited domain-mapping amendment rather than reactivating the Trunk Council.
  All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines.

- [x] **Task 4.4: Create role-sunset assets**
  Create `assets/sunset-record-template.yaml`:
  ```yaml
  sunset_id: ""
  domain_id: ""
  domain_contract_version: ""
  sunset_date: ""
  sunset_trigger: review_recommendation | purpose_achieved | responsibilities_transferred | vacancy_timeout | delegator_proposal
  rationale: ""
  disposition_plan:
    responsibilities:
      - responsibility: ""
        disposition: transferred | ended | absorbed_by_delegator
        destination_domain_id: ""
    agreements:
      - agreement_id: ""
        disposition: transferred | sunset | archived
        destination_domain_id: ""
    dependent_domains:
      - domain_id: ""
        dependency_disposition: removed | redirected
        redirected_to_domain_id: ""
  consent_record_id: ""
  reactivation_window_end: ""  # sunset_date + 90 days
  reactivation_used: false
  archived_domain_contract: {}  # full domain contract at time of sunset
  ```
  **Acceptance:** Template complete.

- [x] **Verification 4: Run validate_skill.py against all 7 completed skills. All must pass. Verify the complete domain lifecycle: a domain can be created (domain-mapping), a member can join (member-lifecycle), a steward can be assigned (role-assignment), boundaries can be negotiated (authority-boundary-negotiation), the role can be transferred (role-transfer), the domain can be reviewed (domain-review), and the domain can be sunset (role-sunset). Check that every skill's depends_on list is accurate. Confirm all asset templates are consistent with their SKILL.md descriptions.** [checkpoint marker]

---

## Phase 5: Layer Integration and README

**Goal:** Write the Layer II README, update foundation track skills (Layers I and III) to reference the formal authority model, and verify all quality gates.

### Tasks

- [x] **Task 5.1: Write Layer II README.md**
  Create `neos-core/layer-02-authority/README.md` with:
  - Layer title and purpose: "The Authority & Role Layer defines how governance authority is scoped, assigned, negotiated, transferred, reviewed, and dissolved within the ecosystem."
  - List of all 7 skills with one-sentence descriptions and dependency lists
  - Diagram of skill relationships:
    ```
    domain-mapping (anchor)
         |
         +---> role-assignment <--- member-lifecycle
         |         |
         |    role-transfer
         |
         +---> authority-boundary-negotiation
         |
         +---> domain-review
                   |
              role-sunset
    ```
  - How this layer interacts with Layer I (agreements define what participants consent to; authority defines who can create and modify those agreements) and Layer III (ACT decisions are the mechanism for creating, assigning, and reviewing authority)
  - Key design decisions: S3 11-element domain contract, blanket authority within scope, separation of role and person, evaluation cadence, profiles vs. roles distinction
  - Design patterns used and anti-patterns guarded against
  **Acceptance:** README provides a complete overview. A new reader can understand the layer without reading individual skills.

- [x] **Task 5.2: Update foundation Layer I skills with Layer II authority references**
  For each of the 5 Layer I skills (agreement-creation, agreement-amendment, agreement-review, agreement-registry, universal-agreement-field):
  - Review the "G. Authority Boundary Check" section
  - Where the skill says "authorized participant" or "authorized body," add a reference: "Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain."
  - Add `domain-mapping` to the `depends_on` list in the YAML frontmatter
  - Do NOT rewrite the skills -- add minimal, targeted references
  Run validate_skill.py against all 5 updated skills.
  **Acceptance:** All 5 Layer I skills still pass validation. Authority references are consistent and minimal.

- [x] **Task 5.3: Update foundation Layer III skills with Layer II authority references**
  For each of the 6 Layer III skills (proposal-creation, act-advice-phase, act-consent-phase, act-test-phase, proposal-resolution, consensus-check):
  - Review the "G. Authority Boundary Check" section
  - Add the same targeted authority references as Task 5.2
  - Add `domain-mapping` to `depends_on` where authority checks are performed
  Run validate_skill.py against all 6 updated skills.
  **Acceptance:** All 6 Layer III skills still pass validation.

- [x] **Task 5.4: Update foundation Layer READMEs**
  Update `neos-core/layer-01-agreement/README.md` and `neos-core/layer-03-act-engine/README.md`:
  - Add a "Dependencies" section noting the relationship with Layer II
  - Add a note: "Authority scopes referenced in this layer's skills are formally defined by the domain-mapping skill in Layer II (Authority & Role)."
  **Acceptance:** Both READMEs updated.

- [x] **Task 5.5: Cross-layer review**
  Perform a systematic review across all 7 Layer II skills plus the 11 updated foundation skills:
  - Verify all `depends_on` lists are accurate and complete
  - Verify all cross-references by name are to skills that exist
  - Verify terminology is consistent (product-guidelines.md terminology table)
  - Verify no hidden authority exists (every judgment call has a stated authority scope -- and now those scopes reference domain contracts)
  - Verify every skill has a review/expiry condition
  - Verify exit compatibility is addressed in every skill
  - Verify the profiles-vs-roles distinction is consistently applied
  - Fix any inconsistencies found
  **Acceptance:** All cross-references valid. Terminology consistent. No hidden authority.

- [x] **Task 5.6: Final validation run**
  Run `validate_skill.py` against the entire `neos-core/` directory with `--verbose` flag (this includes Layers I, II, and III -- all 18 skills). Document the output. All 18 skills must pass.
  **Acceptance:** `python scripts/validate_skill.py neos-core/ --verbose` exits with code 0.

- [x] **Verification 5: Final human review. Read through each of the 7 Layer II SKILL.md files confirming: voice matches product guidelines, every process step is actionable, boundaries are stated as constraints, degradation paths exist for every failure mode. Verify that the foundation skill updates are minimal and targeted, not rewrites. Mark the track complete.** [checkpoint marker]

---

## Phase 6: Quality Gate

**Goal:** Complete the per-layer quality checklist and confirm the track is done.

### Tasks

- [x] **Task 6.1: Per-layer quality gate checklist**
  Complete the per-layer checklist from workflow.md:

  Layer II:
  - [ ] All 7 skills complete
  - [ ] Skills cross-reference each other correctly
  - [ ] Layer README summarizes skills and relationships
  - [ ] No circular authority dependencies
  - [ ] Domain-mapping skill is self-referentially consistent (its own authority model is defined)
  - [ ] Profiles vs. roles distinction is consistently applied across all skills
  - [ ] All 7 asset templates are complete and consistent with SKILL.md descriptions

  Foundation Integration:
  - [ ] All 11 Layer I and III skills updated with authority references
  - [ ] No validation regressions (all 18 skills pass)
  - [ ] Foundation Layer READMEs updated

  **Acceptance:** All checklist items confirmed.

- [x] **Verification 6: Track complete. All 7 Layer II skills built, validated, and reviewed. All 11 foundation skills updated with authority references. Layer README complete. Quality gates passed.** [checkpoint marker]

---

## Summary

| Phase | Skills Built | Cumulative Total | Foundation Updates |
|-------|-------------|-----------------|-------------------|
| Phase 1: Anchor | 1 (domain-mapping) | 1 | 0 |
| Phase 2: Members + Assignment | 2 (member-lifecycle, role-assignment) | 3 | 0 |
| Phase 3: Negotiation + Transfer | 2 (authority-boundary-negotiation, role-transfer) | 5 | 0 |
| Phase 4: Review + Sunset | 2 (domain-review, role-sunset) | 7 | 0 |
| Phase 5: Integration | 0 (README, foundation updates, cross-review) | 7 | 11 skills updated |
| Phase 6: Quality Gate | 0 (checklist, final verification) | 7 | confirmed |

**Total deliverables:** 7 SKILL.md files, 8 asset files (7 YAML templates + 2 markdown checklists), 1 Layer README, 11 foundation skill updates, 2 foundation README updates.
