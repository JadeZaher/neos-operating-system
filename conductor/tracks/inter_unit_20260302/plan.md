# Implementation Plan: Layer V -- Inter-Unit Coordination

## Overview

This plan builds 5 governance skills for NEOS Layer V (Inter-Unit Coordination), organized into 4 phases. The build order progresses from basic cross-unit interactions to complex coordination structures: requests, shared resources, federation agreements, liaison roles, and polycentric conflict navigation.

**Total skills:** 5
**Total phases:** 4
**Estimated scope:** 20-30 hours of focused implementation

### Build Order Rationale

Layer V skills form a complexity gradient. The cross-ETHOS request skill defines the basic interaction shape that all other skills build upon. Shared resource stewardship adds resource governance to cross-unit interactions. Federation agreements formalize multi-unit relationships. Liaison roles maintain those relationships. Polycentric conflict navigation resolves the structural disputes that emerge from all the coordination structures. Each skill references the patterns established by the previous ones.

### Commit Strategy

- One commit per completed skill: `neos(layer-05): Add <skill-name> skill`
- Layer-level commit when all skills are done: `neos(layer-05): Complete layer 05 - Inter-Unit Coordination`

### Dependencies

This track assumes the following are complete or in progress:
- Layer I skills (agreement-creation, agreement-amendment, agreement-registry) from `foundation_20260301`
- Layer III skills (proposal-creation, act-advice-phase, act-consent-phase, act-test-phase) from `foundation_20260301`
- Layer II skills (authority-assignment, role-definition, domain-boundary) from `authority_role_20260302`
- Layer IV skills (resource-request, funding-pool-stewardship) from `economic_coord_20260302`

---

## Phase 1: Scaffolding and Anchor Skill

**Goal:** Create the Layer V directory structure and build the anchor skill -- cross-ethos-request -- that defines the fundamental cross-unit interaction shape all other Layer V skills build upon.

### Tasks

- [ ] **Task 1.1: Create Layer V directory scaffolding**
  Create the full `neos-core/layer-05-inter-unit/` directory tree:
  ```
  neos-core/
    layer-05-inter-unit/
      README.md
      cross-ethos-request/        (SKILL.md, assets/, references/, scripts/)
      shared-resource-stewardship/ (same structure)
      federation-agreement/       (same structure)
      inter-unit-liaison/         (same structure)
      polycentric-conflict-navigation/ (same structure)
  ```
  Each skill directory gets empty `SKILL.md`, empty `assets/`, `references/`, and `scripts/` subdirectories.
  **Acceptance:** All directories exist. `find neos-core/layer-05-inter-unit -name SKILL.md | wc -l` returns 5.

- [ ] **Task 1.2: Draft cross-ethos-request SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without a formal cross-unit request process, coordination between ETHOS depends on personal connections, informal channels, or implicit hierarchy. This skill ensures every cross-ETHOS interaction has a traceable origin, dual-consent routing, and transparent status tracking. It prevents larger or wealthier ETHOS from leveraging informal pressure and ensures silence is never treated as consent.
  - **B. Domain Scope:** Any interaction where a participant or body in one ETHOS needs something from another ETHOS. Request types: resource requests (financial, physical, expertise), information requests, collaboration proposals, service requests, and member transfer requests.
  - **C. Trigger Conditions:** A participant identifies a need that can only be met by another ETHOS, or a circle's work requires coordination with a circle in another ETHOS, or a federation agreement triggers a specific cross-unit action.
  - **D. Required Inputs:** Requester identity, originating ETHOS, target ETHOS, request type, request content, rationale, desired timeline, authority basis (what gives the requester standing to make this request), originating ETHOS's outbound authorization.
  - **E. Step-by-Step Process:** Draft request, obtain outbound authorization from originating ETHOS (circle-level consent or steward authorization depending on request type), transmit to target ETHOS's inbound contact, target ETHOS routes through their own ACT process, response returned with documentation, requester ETHOS acknowledges and acts on response.
  - **F. Output Artifact:** Cross-ETHOS request record with unique ID, both ETHOS named, request content, status (submitted/acknowledged/processing/responded/completed/withdrawn), response documentation, and resolution timeline.
  **Acceptance:** Sections A-F substantive, dual-consent routing clearly defined.

- [ ] **Task 1.3: Draft cross-ethos-request SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G. Authority Boundary Check:** Requester must have standing (membership in originating ETHOS plus circle/steward authorization for the request type). No ETHOS can compel another ETHOS to respond or act. Target ETHOS processes the request through its own governance -- the originating ETHOS has zero authority over the target's internal process. No individual can make cross-ETHOS requests that bypass their own ETHOS's outbound authorization.
  - **H. Capture Resistance Check:** Size pressure (large ETHOS leveraging volume of requests to overwhelm smaller ETHOS's processing capacity), wealth pressure (conditioning cooperation on economic contribution), urgency manipulation (framing routine requests as emergencies to bypass normal processing), reciprocity pressure (implying that past cooperation creates obligation for future compliance).
  - **I. Failure Containment Logic:** Target ETHOS does not respond within timeline (requester may send a single follow-up, then escalate to liaison if one exists, then document non-response -- but cannot force a response). Request denied (requester may modify and resubmit once, or accept the denial). Request creates unintended obligation (any ETHOS can invoke review of the request's scope).
  - **J. Expiry / Review Condition:** Open requests that receive no response within 30 days are marked stale and the requester is notified. Completed requests are reviewed if their outcomes created ongoing commitments (review date set at completion).
  - **K. Exit Compatibility Check:** If the requester exits their ETHOS, open requests are voided unless the originating ETHOS designates a new requester. If a participating ETHOS dissolves, all open cross-ETHOS requests involving that ETHOS are closed with documentation.
  - **L. Cross-Unit Interoperability Impact:** This skill IS the cross-unit interaction primitive. It defines the protocol that all other cross-ETHOS skills use for their interactions. Other Layer V skills reference this skill's request format and routing logic.
  **Acceptance:** Sections G-L structurally precise, explicitly preventing unilateral imposition.

- [ ] **Task 1.4: Write cross-ethos-request OmniOne walkthrough and stress tests**
  - Walkthrough: The Bali SHUR Education circle wants to adapt a conflict resolution training module that the Costa Rica SHUR developed. Walk through: trigger (Bali Education circle identifies the module), drafting (circle member drafts a request specifying what they want -- access to the module and permission to adapt it), outbound authorization (Bali Education circle gives consent for the request), transmission (request sent to Costa Rica SHUR's inbound contact), Costa Rica routing (their Education circle reviews through advice and consent -- one member raises concern about adaptation quality, proposing they review adaptations before use), response (access granted with adaptation review clause), Bali acknowledges. Edge case: the Costa Rica SHUR is still developing the module -- they respond with a timeline and a counter-proposal to co-develop rather than share a finished product. How does the counter-proposal route back through Bali's ACT process?
  - All 7 stress-test scenarios with full narrative paragraphs.
  **Acceptance:** Walkthrough demonstrates dual-consent routing with OmniOne roles. Stress tests are substantive.

- [ ] **Task 1.5: Finalize cross-ethos-request SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter:
    ```yaml
    ---
    name: cross-ethos-request
    description: "Initiate and track requests across ETHOS boundaries -- resource, information, collaboration, or service requests -- through dual-consent routing that respects both units' autonomy."
    layer: 5
    version: 0.1.0
    depends_on: [agreement-creation, act-consent-phase, authority-assignment]
    ---
    ```
  - Create `assets/cross-ethos-request-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 1: Run validate_skill.py against cross-ethos-request. Verify the dual-consent routing is structurally complete (no shortcut that allows one ETHOS to impose on another). Confirm the skill can be understood standalone.** [checkpoint marker]

---

## Phase 2: Shared Resources and Federation

**Goal:** Build the shared-resource-stewardship and federation-agreement skills that define how ETHOS jointly govern resources and formalize their ongoing relationships.

### Tasks

- [ ] **Task 2.1: Draft shared-resource-stewardship SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** When multiple ETHOS share resources without formal governance, the largest contributor tends to claim control, or the resource falls into a governance vacuum where no one is accountable. This skill ensures shared resources have explicit governance agreements that all participating ETHOS ratified through their own processes, with rotating stewardship and equitable access rules.
  - **B. Domain Scope:** Any resource jointly held by two or more ETHOS. Types: shared funding pools, shared physical infrastructure (co-located SHUR facilities), shared knowledge repositories, shared services (training, facilitation, technical support).
  - **C. Trigger Conditions:** Two or more ETHOS identify a resource they want to share, or an existing informally-shared resource needs formalization, or a federation agreement calls for shared resource establishment.
  - **D. Required Inputs:** Participating ETHOS, resource description, proposed governance structure (stewardship model, access rules, contribution commitments, reporting), proposed review cycle.
  - **E. Step-by-Step Process:** Propose shared resource through cross-ETHOS request, negotiate governance terms through each ETHOS's advice phase, draft shared resource governance agreement, each ETHOS ratifies through its own consent process, appoint stewards (rotating across ETHOS), operate with regular reporting, review at defined intervals.
  - **F. Output Artifact:** Shared resource governance agreement registered in each participating ETHOS's agreement registry, plus steward appointment records and initial reporting schedule.
  **Acceptance:** Sections A-F substantive, emphasizing multi-party consent.

- [ ] **Task 2.2: Draft shared-resource-stewardship SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G.** No single ETHOS controls the shared resource regardless of contribution level. Steward authority limited to operational management within the governance agreement's terms. Strategic decisions (access rule changes, contribution changes, sunset) require consent from all participating ETHOS.
  - **H.** Contribution-proportional control (larger contributor claiming more governance authority), steward capture (steward favoring their home ETHOS), information asymmetry (one ETHOS knowing more about the resource's state), free-rider dynamics (ETHOS benefiting without contributing).
  - **I.** One ETHOS wants to withdraw (follow exit provisions in governance agreement -- typically 90-day notice with contribution wind-down). Steward misconduct (trigger review, appoint interim from different ETHOS). Resource depleted (all participating ETHOS jointly decide next steps through ACT).
  - **J.** Shared resource governance agreements reviewed annually at minimum. Steward roles rotate per governance agreement schedule (recommended every 12 months).
  - **K.** When an ETHOS exits the shared resource arrangement, their contribution is handled per the governance agreement's exit terms. The resource continues under remaining participants' governance.
  - **L.** This skill IS a cross-unit interoperability mechanism. It references cross-ethos-request for the initial proposal and federation-agreement for formalization of ongoing shared governance.
  **Acceptance:** Sections G-L structurally precise.

- [ ] **Task 2.3: Write shared-resource-stewardship OmniOne walkthrough and stress tests**
  - Walkthrough: The Bali and Costa Rica SHURs establish a shared knowledge repository for governance best practices. Walk through: initial proposal (Bali SHUR's Governance circle proposes via cross-ETHOS request), Costa Rica's advice phase (they want to include their conflict resolution modules), negotiation (three rounds of collaborative drafting to define access rules, contribution expectations, and stewardship rotation), each SHUR runs its own consent round (Costa Rica has one objection about editing permissions -- resolved by distinguishing read access from edit access), governance agreement ratified, first steward appointed from Bali with Costa Rica successor named. Edge case: a third SHUR (Mexico) wants to join the shared resource 6 months later -- how does the onboarding work?
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates multi-party governance. Stress tests are substantive.

- [ ] **Task 2.4: Finalize shared-resource-stewardship SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: [cross-ethos-request, agreement-creation, funding-pool-stewardship, authority-assignment]`
  - Create `assets/shared-resource-agreement-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Task 2.5: Draft federation-agreement SKILL.md -- full skill (sections A-L)**
  Build the complete `federation-agreement` skill:
  - **A.** Without formal federation agreements, inter-ETHOS relationships are ad hoc, creating inconsistency and ambiguity about what each unit has committed to. This skill ensures multi-unit relationships are documented, mutually ratified, version-controlled, and reviewable -- the same structural discipline applied to intra-ETHOS agreements extended to the inter-unit level.
  - **B.** Any ongoing relationship between two or more ETHOS that goes beyond one-time requests.
  - **C.** Two or more ETHOS decide to formalize an ongoing coordination relationship, or an existing informal arrangement needs structural grounding.
  - **D.** Participating ETHOS, agreement type (bilateral cooperation, multilateral protocol, service-level, mutual recognition, graduated engagement compact), proposed terms, negotiation mandate from each ETHOS, desired engagement tier.
  - **E.** Mandate definition (each ETHOS defines what its negotiators can and cannot agree to), parallel advice phases, collaborative or sequential drafting, each ETHOS runs its own consent round, mutual registration, review schedule.
  - **F.** Federation agreement with mutual ratification records, registered in each ETHOS's agreement registry.
  - **G-L.** Full structural sections addressing negotiator mandate limits, power asymmetry in negotiation, failure modes (negotiation stalls, ratification fails in one ETHOS), expiry and review, exit provisions for ETHOS leaving a federation agreement, and impact on other ETHOS in multilateral arrangements.
  Include graduated engagement tiers: observe (mutual acknowledgment, no commitments), cooperate (case-by-case collaboration through cross-ETHOS requests), federate (formal agreement with shared protocols and regular coordination), integrate (deep structural integration with shared governance bodies).
  **Acceptance:** All 12 sections substantive. Engagement tiers clearly defined.

- [ ] **Task 2.6: Write federation-agreement OmniOne walkthrough and stress tests**
  - Walkthrough: Three SHUR communities (Bali, Costa Rica, Mexico) draft a multilateral protocol for member transfers. Walk through: mandate definition (each SHUR's circle defines what transfer terms they can accept), parallel advice phases (each SHUR consults its members), collaborative drafting session (liaisons from all three SHURs meet to draft), Mexico objects to a provision requiring 30-day notice for transfers (they want 14 days for their more mobile community), negotiation round (compromise at 21 days with flexibility clause for documented emergencies), each SHUR runs consent, Costa Rica initially fails consent (one member objects to housing guarantee language), revision round, second consent attempt succeeds, agreement registered in all three registries.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates real negotiation complexity. Stress tests are substantive.

- [ ] **Task 2.7: Finalize federation-agreement SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: [cross-ethos-request, agreement-creation, act-consent-phase]`
  - Create `assets/federation-agreement-template.yaml` and `assets/engagement-tiers.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 2: Run validate_skill.py against shared-resource-stewardship and federation-agreement. Verify both skills reference cross-ethos-request correctly. Confirm no skill creates an apex authority or allows unilateral imposition.** [checkpoint marker]

---

## Phase 3: Liaison Roles and Conflict Navigation

**Goal:** Build the inter-unit-liaison and polycentric-conflict-navigation skills that maintain ongoing coordination relationships and resolve structural disputes between ETHOS.

### Tasks

- [ ] **Task 3.1: Draft inter-unit-liaison SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without designated liaison roles, cross-ETHOS coordination either depends on whoever happens to know someone in the other unit (informal channels) or falls to leadership figures who accumulate inter-unit authority. This skill creates formal liaison roles with explicit mandate boundaries so coordination is accountable, distributed, and does not become a bottleneck.
  - **B. Domain Scope:** Any ongoing coordination relationship between ETHOS that benefits from a designated point person. Liaison types: bilateral (between two ETHOS), multilateral coordinator (across several ETHOS for a specific domain), domain-specific (focused on a particular area like education, economics, or resource sharing).
  - **C. Trigger Conditions:** Two ETHOS establish a federation agreement that calls for ongoing coordination, or a shared resource stewardship arrangement needs a coordination contact, or cross-ETHOS request volume between two units warrants a dedicated liaison.
  - **D. Required Inputs:** Participating ETHOS, liaison type, proposed mandate (what the liaison can communicate, explore, recommend, and what requires ETHOS-level consent), proposed reporting cadence, proposed term duration.
  - **E. Step-by-Step Process:** Propose liaison role through each ETHOS's ACT process (using authority-assignment), define mandate boundaries collaboratively, appoint liaison, operate with regular reporting back to home ETHOS, review at term end, rotate or extend.
  - **F. Output Artifact:** Liaison role agreement specifying the person, mandate boundaries, reporting requirements, term dates, and review schedule.
  **Acceptance:** Sections A-F substantive, mandate boundaries clearly defined.

- [ ] **Task 3.2: Draft inter-unit-liaison SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G.** Liaison cannot make binding commitments on behalf of their ETHOS without explicit authorization for the specific commitment. Liaison role does not grant any intra-ETHOS authority (the liaison is a communication and coordination channel, not a decision-maker). Other members can still communicate across ETHOS boundaries -- the liaison does not become a gatekeeper.
  - **H.** Information asymmetry capture (liaison knows more about inter-ETHOS affairs than anyone else, gaining informal power), relationship capture (personal relationships with counterparts override structural accountability), bottleneck capture (liaison becomes the only channel, creating a single point of failure and power), home ETHOS capture (liaison prioritizes their home ETHOS's interests over neutral coordination).
  - **I.** Liaison exceeds mandate (affected ETHOS can void any commitment made outside mandate, liaison faces review). Liaison role vacant (coordination continues through direct cross-ETHOS requests until replacement appointed). Liaison conflicts with counterpart (escalate to polycentric-conflict-navigation skill).
  - **J.** Liaison terms are 12 months with option for one 12-month extension. Mandatory rotation after maximum term. Reporting cadence defined in liaison agreement (recommended monthly).
  - **K.** When a liaison exits their ETHOS or the ecosystem, the role is vacated and a successor appointed through the standard process. In-progress coordination items are documented and handed over.
  - **L.** Liaison roles are inherently cross-unit. The liaison agreement is registered in both participating ETHOS' agreement registries.
  **Acceptance:** Sections G-L structurally precise, preventing liaison power accumulation.

- [ ] **Task 3.3: Write inter-unit-liaison OmniOne walkthrough and stress tests**
  - Walkthrough: The Bali SHUR appoints a liaison to the Economics circle's cross-SHUR coordination group (which includes representatives from Bali, Costa Rica, and Mexico SHURs). Walk through: need identification (growing volume of resource-sharing discussions across SHURs), mandate definition (Bali's Economics circle defines what the liaison can discuss, explore, and recommend -- specifically, they can share Bali's resource flow data and discuss shared pool possibilities, but cannot commit Bali to any resource-sharing arrangement without circle consent), appointment through Bali's authority-assignment process, first coordination meeting (the liaison explores a shared emergency fund concept), liaison returns to Bali circle to report and request mandate extension for the emergency fund negotiation, Bali circle grants specific negotiation mandate. Edge case: the liaison develops a close working relationship with the Costa Rica counterpart and begins sharing information about Bali's internal circle dynamics that was not part of the mandate. How does the reporting requirement catch this, and what is the graduated response?
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates clear mandate boundaries. Stress tests are substantive.

- [ ] **Task 3.4: Finalize inter-unit-liaison SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: [cross-ethos-request, federation-agreement, authority-assignment]`
  - Create `assets/liaison-mandate-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Task 3.5: Draft polycentric-conflict-navigation SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** When two autonomous units have conflicting authority claims, contradictory agreements, or competing resource interests, there is no sovereign authority to resolve the dispute. Without a structural protocol, conflicts either escalate indefinitely, result in fragmentation, or are resolved by whoever has more power. This skill provides a three-tier lateral resolution protocol that preserves both units' autonomy while creating pathways to agreement.
  - **B. Domain Scope:** Any structural conflict between two or more ETHOS. Conflict types: authority overlap (both ETHOS claim governance authority over the same domain), agreement contradiction (ETHOS A's agreements conflict with ETHOS B's), resource competition (both ETHOS need the same limited resource), boundary dispute (unclear which ETHOS's rules apply in a shared or overlapping space), protocol divergence (ETHOS following incompatible processes for the same coordination need).
  - **C. Trigger Conditions:** An ETHOS identifies that another ETHOS's actions or agreements conflict with its own, or a cross-ETHOS request reveals incompatible expectations, or a liaison reports a structural incompatibility, or a participant operating in both ETHOS encounters contradictory requirements.
  - **D. Required Inputs:** Affected ETHOS, conflict description (specific claims from each side), conflict type, supporting documentation (relevant agreements, authority scopes, resource records), desired resolution timeline.
  - **E. Step-by-Step Process:** Three-tier resolution: Tier 1 -- direct negotiation between affected ETHOS (designated representatives meet, share positions, seek mutual solution through good-faith dialogue); Tier 2 -- facilitated dialogue with a mutually agreed neutral party from a third ETHOS (neutral party facilitates but does not decide); Tier 3 -- structural resolution through federation agreement amendment or new agreement that addresses the underlying structural incompatibility. Each tier's outcome must be ratified through each ETHOS's own ACT process.
  - **F. Output Artifact:** Polycentric conflict resolution record documenting the dispute, positions, resolution process (which tier reached resolution), outcome agreement, any federation agreement amendments, and review date.
  **Acceptance:** Sections A-F substantive, three-tier resolution clearly defined with no imposed outcomes.

- [ ] **Task 3.6: Draft polycentric-conflict-navigation SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G.** No ETHOS, body, or individual can impose a resolution. Neutral facilitators (Tier 2) have process authority only (managing dialogue), not outcome authority. Resolution outcomes require mutual consent through each ETHOS's ACT process. If no resolution is reached at any tier, the ETHOS may choose to reduce their engagement tier (from federate to cooperate, or from cooperate to observe) rather than being forced into a resolution they did not consent to.
  - **H.** Size leverage (larger ETHOS pressuring smaller through implied consequences of non-resolution), facilitator bias (neutral party developing structural bias toward one side), resolution fatigue (one side capitulating to end the process rather than genuinely consenting), precedent weaponization (citing past resolutions to constrain future autonomy), escalation avoidance (ETHOS avoiding Tier 2 or 3 because the process is too burdensome, letting conflicts fester).
  - **I.** No resolution reached (ETHOS may agree to disagree and reduce engagement tier -- this is a legitimate outcome, not a failure). Neutral party unavailable (extend Tier 1 direct negotiation with documented good-faith attempts). Resolution agreement violated (trigger review, return to appropriate tier).
  - **J.** Conflict resolution records reviewed 6 months after resolution to check whether the outcome is holding. Federation agreement amendments triggered by conflict resolution follow the federation agreement's own review cycle.
  - **K.** If one ETHOS exits the ecosystem during conflict navigation, the process concludes with documentation. Remaining ETHOS adjust their governance as needed.
  - **L.** This skill is the capstone cross-unit mechanism. It references cross-ethos-request (how the conflict was identified), federation-agreement (how structural resolutions are formalized), and inter-unit-liaison (how liaisons flag emerging conflicts).
  **Acceptance:** Sections G-L structurally precise, explicitly allowing "agree to disagree" as a legitimate outcome.

- [ ] **Task 3.7: Write polycentric-conflict-navigation OmniOne walkthrough and stress tests**
  - Walkthrough: The Bali SHUR and Costa Rica SHUR have a boundary dispute about which SHUR's space agreements apply to a traveling member (Maria) who spends 3 months in each SHUR annually. Walk through: conflict identification (Maria encounters contradictory quiet-hours rules and does not know which applies), Tier 1 direct negotiation (representatives from both SHURs meet, Bali says their space agreement applies when Maria is physically present, Costa Rica says Maria's home SHUR agreement should follow her), no resolution at Tier 1 (fundamental disagreement about "home SHUR" concept), Tier 2 facilitated dialogue (Mexico SHUR steward facilitates, surfaces the underlying issue -- no protocol exists for member presence across SHURs), resolution emerges (create a "visiting member" protocol as a federation agreement amendment), both SHURs run consent, Bali needs a modification to the visiting member duration threshold (30 days, not 14), revised protocol consented to by both, federation agreement amended and registered. Edge case: what if the Mexico facilitator has a personal relationship with the Costa Rica representatives?
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates full three-tier escalation with realistic OmniOne scenario.

- [ ] **Task 3.8: Finalize polycentric-conflict-navigation SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: [cross-ethos-request, federation-agreement, inter-unit-liaison, act-consent-phase]`
  - Create `assets/conflict-resolution-record-template.yaml` and `assets/resolution-tiers.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 3: Run validate_skill.py against inter-unit-liaison and polycentric-conflict-navigation. Verify neither skill creates an apex authority. Confirm the conflict navigation skill explicitly allows "agree to disagree" as a legitimate outcome.** [checkpoint marker]

---

## Phase 4: Layer Integration and Finalization

**Goal:** Finalize the layer with a README, cross-skill consistency review, and quality gates.

### Tasks

- [ ] **Task 4.1: Write Layer V README.md**
  Create `neos-core/layer-05-inter-unit/README.md` summarizing:
  - Layer purpose and relationship to NEOS principles (especially polycentric governance, no sovereign authority)
  - All 5 skills with brief descriptions and relationships
  - Theoretical foundations mapping (Ostrom polycentric governance, millet system analogy with critical modifications, Holochain agent-centric architecture, federation models)
  - Engagement tiers overview (observe, cooperate, federate, integrate)
  - Cross-layer dependencies (references to Layers I, II, III, IV)
  - OmniOne configuration notes (SHUR network, TH/AE/OSC coordination surfaces)
  - The "no Sultan" principle: explicit statement that this layer provides coordination without apex authority
  **Acceptance:** README accurately summarizes the layer and its design philosophy.

- [ ] **Task 4.2: Cross-skill review and quality gates**
  Review all 5 skills against the per-skill checklist:
  - [ ] All 12 sections (A-L) present and substantive
  - [ ] OmniOne walkthrough included with specific roles
  - [ ] At least one edge case documented per skill
  - [ ] Stress-tested against all 7 scenarios
  - [ ] No hidden sovereign authority
  - [ ] No skill allows unilateral imposition across ETHOS boundaries
  - [ ] Exit compatibility confirmed
  - [ ] Cross-unit interoperability impact stated
  - [ ] Dual-consent requirement maintained throughout
  Additionally:
  - Verify cross-references between Layer V skills are consistent
  - Verify the engagement tiers in federation-agreement are referenced correctly by other skills
  - Verify terminology matches product-guidelines.md throughout
  - Verify no skill exceeds 500 lines
  - Verify the millet system analogy is used correctly (structural pattern borrowed, apex authority explicitly rejected)
  **Acceptance:** All 5 skills pass all quality gates. Layer is internally consistent.

- [ ] **Verification 4: Run validate_skill.py against entire layer-05-inter-unit/ directory. All 5 skills pass. README exists. Cross-references verified. Layer is complete.** [checkpoint marker]
