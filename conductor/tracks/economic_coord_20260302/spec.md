# Specification: Layer IV -- Economic Coordination

## Track ID
`economic_coord_20260302`

## Overview

This track builds **Layer IV (Economic Coordination)** of the NEOS governance stack: the skill layer that governs how resources flow through the ecosystem without conflating economic contribution with governance authority. The layer encompasses resource requests, funding pool stewardship, participatory allocation, commons monitoring, and the staged transition from currency-based to access-based economics.

The economic layer is structurally downstream from agreements (Layer I), authority and roles (Layer II), and the ACT decision engine (Layer III). Every economic action in NEOS is an agreement. Every resource allocation is a decision. Every funding pool has scoped authority. This track builds on those foundations rather than reimagining them.

**Total skills:** 5
**Layers:** IV (Economic Coordination)
**Dependencies:** foundation_20260301 (Layers I, III), authority_role_20260302 (Layer II)

## Background

### Why Economic Coordination Needs Its Own Layer

Capital is the most common vector for governance capture. In traditional organizations, whoever controls the money controls the decisions. In token-governed DAOs, wealth literally equals voting power. NEOS exists partly to prevent this failure mode. The economic layer must be structurally designed so that:
- Resource allocation decisions go through ACT process, not unilateral authority
- Economic contribution does not grant additional governance power
- Commons resources are governed by Ostrom's principles, not market logic
- Monitoring and accountability are community-driven, not opaque

### Theoretical Foundations

**Elinor Ostrom's 8 Principles for Commons Governance:**
1. Clearly defined boundaries (who can access which resource pools)
2. Congruence between local conditions and rules (resource rules match local realities)
3. Collective-choice arrangements (participatory rule-making for resource governance)
4. Monitoring by community members (not external auditors)
5. Graduated sanctions for rule violations (not binary punishment)
6. Accessible conflict resolution mechanisms
7. Recognition of self-governance rights (external authorities do not override local resource decisions)
8. Nested enterprises for large-scale systems (resource governance at multiple scales)

**Participatory Budgeting (Porto Alegre model):** Citizens directly decide budget allocation through structured assembly processes. Adapted for NEOS as participatory allocation assemblies where circle members allocate funding pool resources.

**Commons-Based Peer Production (Benkler):** Production organized around shared resources and voluntary contribution rather than wage labor. Relevant for how NEOS tracks contribution without commodifying it.

**HYPHA DHO Three-Token System:** Utility token, governance token, and voice token as separate instruments. NEOS does not replicate this but learns from the separation of economic and governance functions.

### OmniOne Economic Context

OmniOne uses **Current-Sees** -- influence currencies distributed equally (111 per person). Multiple Current-See types exist:
- **NEXUS Alpha** -- Onboarding gateway
- **TH (Town Hall)** -- Ecosystem participation
- **AE (Agents of the Ecosystem)** -- Active builder participation
- **OSC (OMNI Steward Council)** -- Deep stewardship
- **GEV** -- Organizational design
- **Mission-Metrics** -- Outcome tracking
- **Energy** -- Vitality/engagement measure
- **Reputation** -- Track record
- **Contribution** -- Work performed
- **Time Bank** -- Hour-for-hour exchange

Funding pools operate at circle and ecosystem levels. The H.A.R.T. (Holistic Allocation of Resources and Treasuries) system governs resource distribution. OmniOne's long-term trajectory moves from accepted currencies at each stage toward a full access economy where resources flow by need and stewardship rather than exchange.

### Design Principles for This Layer

**Use:** Nested funding pools with clear boundaries. Participatory allocation assemblies for budget decisions. Graduated access tiers tied to participation level. Full transparency monitoring where every allocation is visible to every participant.

**Avoid:** Tokenizing influence prematurely (Current-Sees are influence signals, not purchasable assets). Majority-controlled pooling (allocation by consent, not majority vote). Zero-sum framing (resource allocation as abundance management, not scarcity competition). Opaque formulas (no black-box algorithms deciding who gets what).

---

## Functional Requirements

### FR-1: Resource Request (`resource-request`)

**Description:** Enable any authorized participant to formally request resources from ecosystem funding pools. Resource types include financial resources, physical assets, time allocations, access permissions, and expertise commitments. The skill defines the full lifecycle from request drafting through ACT decision to fulfillment tracking.

**Acceptance Criteria:**
- AC-1.1: The skill defines all required inputs (requester identity, resource type, amount/scope, funding pool target, rationale, timeline, stewardship commitment, domain scope).
- AC-1.2: The step-by-step process routes the request through the appropriate ACT decision level based on resource amount thresholds and pool governance rules.
- AC-1.3: The output artifact is a versioned resource request document with unique identifier, approval record, fulfillment status, and stewardship accountability.
- AC-1.4: The authority boundary check prevents requests outside the requester's domain and prevents self-approval of one's own resource requests.
- AC-1.5: The capture resistance check addresses scenarios where capital donors condition funding on preferred resource allocation, and where high-status members receive preferential treatment.
- AC-1.6: An OmniOne walkthrough demonstrates an AE member requesting funding from their circle's pool to attend a governance training, including the H.A.R.T. routing.
- AC-1.7: All 7 stress-test scenarios are documented with full narrative results.

**Priority:** P0 -- Anchor skill for economic coordination.

### FR-2: Funding Pool Stewardship (`funding-pool-stewardship`)

**Description:** Define the governance structure for managing circle and ecosystem-level resource pools. This includes pool creation, boundary definition, inflow/outflow rules, transparency requirements, and steward accountability. Every funding pool is an agreement -- creating one invokes the agreement-creation skill from Layer I.

**Acceptance Criteria:**
- AC-2.1: The skill defines pool types (circle operational, ecosystem strategic, cross-ETHOS shared, project-specific, emergency reserve) with governance rules for each.
- AC-2.2: The step-by-step process covers pool creation through ACT, steward appointment through authority-assignment (Layer II), reporting cycles, and pool sunset procedures.
- AC-2.3: The output artifact is a funding pool governance document specifying boundaries, inflow sources, outflow rules, steward roles, transparency schedule, and review date.
- AC-2.4: The authority boundary check prevents any steward from unilateral allocation decisions above a defined threshold and prevents pool capture through steward collusion.
- AC-2.5: The capture resistance check addresses capital concentration (single source providing majority of pool inflow gaining outsized influence) and emergency capture (crisis used to bypass pool governance).
- AC-2.6: An OmniOne walkthrough demonstrates the Economics circle creating a new operational funding pool using Current-Sees and accepted currencies, with H.A.R.T. distribution rules.
- AC-2.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Structural foundation for all economic coordination.

### FR-3: Participatory Allocation (`participatory-allocation`)

**Description:** Run participatory budgeting-style allocation assemblies where circle members collectively decide how funding pool resources are distributed. The skill adapts the Porto Alegre participatory budgeting model for consent-based governance: proposals are submitted, discussed, modified, and allocated through structured rounds rather than majority voting.

**Acceptance Criteria:**
- AC-3.1: The skill defines the assembly structure (preparation phase, proposal submission window, deliberation rounds, allocation round using consent, ratification).
- AC-3.2: The step-by-step process includes rules for proposal eligibility, conflict of interest disclosure, deliberation facilitation, and allocation mechanics (consent-based, not voting).
- AC-3.3: The output artifact is an allocation record documenting all proposals considered, deliberation notes, final allocations, dissenting positions, and review date.
- AC-3.4: The authority boundary check prevents facilitators from steering allocation outcomes and prevents wealthy contributors from receiving proportionally larger allocations.
- AC-3.5: The capture resistance check addresses faction coordination (organized blocs pushing allocation toward their preferred projects) and charismatic persuasion (eloquent presenters receiving more regardless of merit).
- AC-3.6: An OmniOne walkthrough demonstrates an AE circle running a quarterly participatory allocation assembly for their operational budget, including one contested allocation that requires a third-solution round.
- AC-3.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on FR-1 and FR-2 establishing resource request and pool structures.

### FR-4: Commons Monitoring (`commons-monitoring`)

**Description:** Track resource use patterns across funding pools and commons resources, detect over-draw or misuse, and trigger graduated responses. Monitoring is performed by community members (Ostrom Principle 4), not external auditors or opaque algorithms. The skill defines what gets monitored, by whom, how often, and what thresholds trigger what responses.

**Acceptance Criteria:**
- AC-4.1: The skill defines monitoring dimensions (flow rate, concentration, reciprocity, sustainability, accessibility) and thresholds for each.
- AC-4.2: The step-by-step process covers monitoring cycles (regular reporting, community review sessions, threshold alerts, investigation triggers).
- AC-4.3: The output artifact is a commons health report documenting resource flow patterns, any threshold breaches, community observations, and recommended actions.
- AC-4.4: The authority boundary check prevents monitors from becoming gatekeepers (monitoring informs decisions, does not make them) and prevents surveillance creep (monitoring resource flows, not individual behavior).
- AC-4.5: The capture resistance check addresses scenarios where monitors are captured by interests they should be tracking, and where monitoring data is weaponized for political purposes.
- AC-4.6: An OmniOne walkthrough demonstrates the TH community reviewing a quarterly commons health report that reveals one circle has drawn 40% of ecosystem resources, triggering a participatory review.
- AC-4.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on FR-2 establishing pool governance structures to monitor.

### FR-5: Access Economy Transition (`access-economy-transition`)

**Description:** Manage the staged transition from currency-based resource exchange to access-based resource flow. OmniOne's long-term vision moves from traditional currency acceptance through Current-See integration to a full access economy. This skill defines the transition stages, readiness criteria for advancing between stages, and governance of the transition itself.

**Acceptance Criteria:**
- AC-5.1: The skill defines transition stages (currency-dependent, hybrid currency/Current-See, Current-See primary, access economy) with clear structural characteristics of each stage.
- AC-5.2: The step-by-step process covers readiness assessment, transition proposals through ACT, pilot testing at circle level, ecosystem-level adoption, and rollback procedures.
- AC-5.3: The output artifact is a transition stage assessment document showing current stage, readiness indicators, pilot results, and recommended next actions.
- AC-5.4: The authority boundary check prevents forced transitions (no circle can be compelled to advance stages faster than its capacity) and prevents regression capture (stakeholders with currency advantages blocking transition).
- AC-5.5: The capture resistance check addresses capital holders resisting transition to protect their economic advantage, and premature transition enthusiasm that destabilizes functioning exchange systems.
- AC-5.6: An OmniOne walkthrough demonstrates a SHUR community assessing readiness to move from hybrid currency/Current-See to Current-See primary for housing resource allocation.
- AC-5.7: All 7 stress-test scenarios documented.

**Priority:** P2 -- Long-term structural skill. Depends on FR-1 through FR-4 being operational.

---

## Non-Functional Requirements

### NFR-1: Capital-Power Separation

Every skill in this layer must structurally prevent economic contribution from translating into governance authority. Financial contribution creates no additional decision-making weight. Current-Sees are distributed equally (111 per person) regardless of economic contribution level. Each skill's authority boundary check must explicitly address this.

### NFR-2: Modularity

Each skill must function independently. A participant or AI agent reading a single SKILL.md must be able to understand and execute the described process without requiring other Layer IV skills to be loaded. Skills may reference each other by name but must not depend on another being "installed."

### NFR-3: Line Limit

Each SKILL.md must be under 500 lines. Supporting material (allocation assembly guides, monitoring templates, transition stage definitions) goes in `references/` or `assets/`.

### NFR-4: Portability

Every skill is NEOS-generic at its structural level. OmniOne-specific details (Current-See types, H.A.R.T. system, specific currency stages) appear as clearly marked examples and configuration blocks. Another ecosystem must be able to fork and replace these with their own economic configuration.

### NFR-5: Transparency Default

All resource flows, pool balances, allocation decisions, and monitoring reports must be structurally accessible to all ecosystem participants. No economic decision occurs behind closed doors. Each skill must define what artifacts are public and how they are accessed.

### NFR-6: Graduated Response

Following Ostrom's Principle 5, all skills that detect resource misuse or threshold breaches must trigger graduated responses (notification, review, restriction, suspension), never binary punishment. The graduated response ladder must be defined in each relevant skill.

### NFR-7: Validation

Every SKILL.md must pass automated validation via `scripts/validate_skill.py`. The validator checks: YAML frontmatter presence and required fields, all 12 sections (A-L) present with substantive content, OmniOne walkthrough present, all 7 stress-test scenarios present.

---

## User Stories

### US-1: Participant Requests Resources
**As** an AE member who needs resources for a project,
**I want** a clear, structured process for requesting funds from my circle's pool,
**So that** I can access resources through legitimate channels rather than informal connections.

**Given** the participant has identified a resource need within their domain,
**When** they follow the resource-request skill process,
**Then** a versioned request enters the appropriate ACT decision track with full transparency.

### US-2: AI Agent Guides Pool Stewardship
**As** an AI agent assisting a funding pool steward,
**I want** to understand the governance rules for the pool and the steward's authority boundaries,
**So that** I can help the steward make allocation decisions within their scope and flag decisions that exceed it.

**Given** a funding pool exists with defined governance rules,
**When** the AI agent reads the funding-pool-stewardship skill,
**Then** it can identify the steward's authority limits, reporting obligations, and escalation triggers.

### US-3: Circle Runs Participatory Allocation
**As** a circle facilitator preparing for a quarterly budget allocation,
**I want** a step-by-step assembly process that ensures all voices are heard and no faction dominates,
**So that** resource allocation reflects collective wisdom rather than lobbying power.

**Given** the circle has a funding pool with resources to allocate and proposals submitted,
**When** the facilitator follows the participatory-allocation skill process,
**Then** a consent-based allocation is produced with documented deliberation and dissenting positions.

### US-4: Community Reviews Commons Health
**As** a TH member concerned about resource concentration,
**I want** to access transparent monitoring reports that show how resources flow across the ecosystem,
**So that** I can participate in accountability discussions with full information.

**Given** monitoring cycles have produced commons health reports,
**When** the participant accesses the reports,
**Then** they can see resource flow patterns, threshold breaches, and recommended actions.

### US-5: Ecosystem Architect Configures Economic Layer
**As** an ecosystem architect adapting NEOS for a new community,
**I want** economic coordination skills that are generic enough to configure for my community's economic model,
**So that** I can establish resource governance without reinventing the structural design.

**Given** the architect has a community with different currency types and pool structures,
**When** they review the Layer IV skills and replace OmniOne example blocks,
**Then** the skills function correctly with their community's economic configuration.

### US-6: SHUR Community Assesses Transition Readiness
**As** a SHUR steward exploring the access economy transition,
**I want** clear readiness criteria and a structured pilot process,
**So that** our community can progress toward the access economy at a pace that matches our capacity.

**Given** the SHUR community is operating in hybrid currency/Current-See stage,
**When** they follow the access-economy-transition skill to assess readiness,
**Then** they receive a structured assessment showing which criteria are met, which are not, and what pilots would test the gaps.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-04-economic/
    README.md
    resource-request/
      SKILL.md
      assets/
        resource-request-template.yaml
      references/
      scripts/
    funding-pool-stewardship/
      SKILL.md
      assets/
        pool-governance-template.yaml
        pool-types.yaml
      references/
      scripts/
    participatory-allocation/
      SKILL.md
      assets/
        allocation-assembly-template.yaml
        allocation-record-template.yaml
      references/
      scripts/
    commons-monitoring/
      SKILL.md
      assets/
        commons-health-report-template.yaml
        monitoring-thresholds.yaml
      references/
      scripts/
    access-economy-transition/
      SKILL.md
      assets/
        transition-stages.yaml
        readiness-assessment-template.yaml
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name
description: "Pushy description..."
layer: 4
version: 0.1.0
depends_on: []  # Layer IV skills reference Layer I, II, III by name but do not require them to be loaded
---
```

### Build Order Rationale

Skills are built in dependency order:
1. `resource-request` -- Anchor skill, defines what a resource request looks like
2. `funding-pool-stewardship` -- Defines the pools that requests draw from
3. `participatory-allocation` -- Defines how pools get allocated (references requests and pools)
4. `commons-monitoring` -- Defines how pools and flows get tracked (references pools and allocations)
5. `access-economy-transition` -- Long-range transition skill (references all previous skills)

### Cross-Layer References

Each skill will reference Layer I-III skills by name:
- `agreement-creation` -- Every funding pool is an agreement
- `act-consent-phase` -- Resource allocations use consent process
- `authority-assignment` -- Pool stewards are roles with scoped authority
- `agreement-review` -- Pool governance agreements have review cycles

These are informational references, not loading dependencies.

---

## Out of Scope

- **Specific OmniOne budget figures** -- The skills define the process for allocating resources, not the amounts or specific OmniOne budget decisions.
- **Current-See protocol design** -- The skills reference Current-Sees as an existing mechanism. Designing the Current-See protocol itself is not in scope.
- **H.A.R.T. system implementation** -- H.A.R.T. appears as the OmniOne example configuration. The underlying system design is OmniOne-specific, not a NEOS core skill.
- **Investment or external fundraising** -- How the ecosystem acquires resources from external sources is not covered. This layer governs internal resource governance.
- **Layer VII (Safeguard) integration** -- Capture detection at the systemic level belongs to Layer VII. This layer's capture resistance checks are self-contained within each skill.

---

## Open Questions

1. **Resource request threshold tiers**: What amount thresholds determine whether a resource request needs circle-level consent vs. ecosystem-level consent? Recommendation: define threshold tiers as configuration in the pool governance agreement, with suggested defaults (circle steward discretion up to 5% of pool, circle consent up to 25%, ecosystem consent above 25%).

2. **Current-See fungibility**: Can Current-Sees of different types be exchanged or converted? The source docs are ambiguous. Recommendation: treat Current-See types as non-fungible within the skill definitions, note the question as ecosystem configuration.

3. **Monitor selection process**: How are commons monitors selected? Random rotation, volunteer, role assignment? Recommendation: define as a role assigned through the authority-assignment skill (Layer II), with mandatory rotation to prevent monitor capture.

4. **Access economy rollback triggers**: What conditions would force a stage regression in the access economy transition? Recommendation: define rollback triggers as part of the transition proposal (each advance includes its own rollback criteria), reviewed through ACT test phase.
