# Specification: Layer V -- Inter-Unit Coordination

## Track ID
`inter_unit_20260302`

## Overview

This track builds **Layer V (Inter-Unit Coordination)** of the NEOS governance stack: the skill layer that governs how autonomous units (AZPOs) coordinate with each other without requiring centralized mediation or hub-and-spoke authority. The layer encompasses cross-AZPO requests, shared resource stewardship, federation agreements, liaison relationships, and polycentric conflict navigation.

NEOS is designed for polycentric governance -- multiple overlapping decision centers with no apex authority. This layer is where that design principle becomes most structurally demanding. AZPOs must be able to cooperate, share resources, resolve boundary disputes, and form multilateral agreements while maintaining their internal autonomy.

**Total skills:** 5
**Layers:** V (Inter-Unit Coordination)
**Dependencies:** foundation_20260301 (Layers I, III), authority_role_20260302 (Layer II), economic_coord_20260302 (Layer IV)

## Background

### Why Inter-Unit Coordination Is Distinct from Internal Governance

Layers I through IV govern how things work within an AZPO or within the ecosystem as a single entity. Layer V governs the relationships between autonomous units that each have their own agreements, authority structures, decision processes, and resource pools. The structural challenge is different: there is no shared authority that can compel compliance. Coordination must emerge from mutual agreement, not hierarchical mandate.

This is the hardest governance problem in any non-sovereign system. Without a central arbiter, cross-unit disputes can escalate indefinitely or result in fragmentation. Layer V must provide enough structure for productive coordination while respecting the autonomy that makes AZPOs meaningful.

### Theoretical Foundations

**Ostrom's Polycentric Governance:** Multiple governing authorities at different scales, each with defined scope, operating independently but coordinating through shared protocols. The key insight is that governance does not require a single center -- it requires clear boundaries, shared protocols, and accessible dispute resolution.

**Ottoman Millet System (Analogy with Critical Modification):** The Ottoman millet system allowed religious communities internal autonomy while sharing a common administrative framework. Each millet governed its own internal affairs (education, marriage, property) while the shared framework handled inter-community matters. NEOS borrows the structural pattern -- internal autonomy plus shared coordination protocols -- but explicitly rejects the millet system's central authority (the Sultan). There is no apex sovereign in NEOS. Inter-unit coordination is lateral, not hierarchical.

**Holochain Agent-Centric Architecture:** Each agent maintains a sovereign source chain (their own data and decisions) while participating in a distributed hash table for shared state. The architectural principle -- sovereign agents coordinating through shared protocols without a central server -- maps directly to NEOS's AZPO coordination model.

**Federated Governance Models:** Drawing from federation patterns in both political science (Swiss cantons, EU subsidiarity principle) and technology (ActivityPub, Matrix protocol). The key structural elements are: bilateral/multilateral agreements between autonomous units, shared interoperability standards, and graduated engagement tiers.

### Design Principles for This Layer

**Use:** Mutual-signature cross-AZPO agreements where both sides must consent through their own ACT process. Inter-AZPO liaison roles that maintain ongoing coordination relationships. Interoperability standards at the SHUR layer (shared protocols that all AZPOs agree to). Graduated engagement tiers (observe, cooperate, federate, integrate). Intermediate collaborative forums for multi-AZPO discussions.

**Avoid:** Hub-and-spoke coordination where one AZPO or body routes all cross-unit communication. Silent defaults as consent (if an AZPO does not respond to a coordination request, this is NOT consent). Jurisdiction ambiguity (unclear which AZPO's rules apply in shared spaces). The millet failure mode of needing a central mediator when two AZPOs cannot agree -- instead, provide structural protocols for lateral resolution.

### OmniOne Context

OmniOne's multi-site structure (Bali, planned Costa Rica, Mexico, Brazil) creates natural inter-unit coordination needs between SHUR communities. Different SHURs may have different space agreements, different resource pools, and different circle structures, but they share the Universal Agreement Field and the NEOS coordination protocols. The TH, AE, and OSC bodies provide ecosystem-wide coordination surfaces, but these do not override individual SHUR or AZPO autonomy.

---

## Functional Requirements

### FR-1: Cross-AZPO Request (`cross-azpo-request`)

**Description:** Enable any authorized participant to initiate and track a request that crosses AZPO boundaries -- a request from one autonomous unit to another. This includes resource requests, information requests, collaboration proposals, and service requests. The skill defines how requests are routed, how the receiving AZPO processes them through their own governance, and how outcomes are tracked across both units.

**Acceptance Criteria:**
- AC-1.1: The skill defines all required inputs (requester identity, originating AZPO, target AZPO, request type, request content, rationale, desired timeline, authority basis for the request).
- AC-1.2: The step-by-step process routes the request through the originating AZPO's outbound authorization and the target AZPO's inbound processing, with each AZPO using its own ACT process.
- AC-1.3: The output artifact is a cross-AZPO request record visible to both units, with status tracking and response documentation.
- AC-1.4: The authority boundary check ensures the requester has authorization from their own AZPO to make the request and that neither AZPO can unilaterally impose obligations on the other.
- AC-1.5: The capture resistance check addresses scenarios where a larger or wealthier AZPO pressures a smaller one through volume or implied leverage.
- AC-1.6: An OmniOne walkthrough demonstrates the Bali SHUR requesting access to a governance training module developed by the Costa Rica SHUR, including the dual-ACT routing.
- AC-1.7: All 7 stress-test scenarios documented with full narrative results.

**Priority:** P0 -- Anchor skill, defines the basic cross-unit interaction shape.

### FR-2: Shared Resource Stewardship (`shared-resource-stewardship`)

**Description:** Govern jointly-held resources that span multiple AZPOs. This includes shared funding pools, shared physical infrastructure, shared knowledge repositories, and shared services. The skill defines how shared resources are established, how stewardship responsibilities are divided, how access rules are set, and how disputes about shared resource use are resolved.

**Acceptance Criteria:**
- AC-2.1: The skill defines shared resource types (shared pool, shared infrastructure, shared repository, shared service) with governance rules for each.
- AC-2.2: The step-by-step process covers shared resource establishment (mutual agreement through each AZPO's ACT process), stewardship appointment (rotating or shared), access rules (equitable across contributing AZPOs), reporting, and sunset.
- AC-2.3: The output artifact is a shared resource governance agreement signed through each participating AZPO's consent process.
- AC-2.4: The authority boundary check prevents any single AZPO from claiming exclusive control over shared resources and prevents stewards from favoring their home AZPO.
- AC-2.5: The capture resistance check addresses larger AZPOs claiming proportional control based on larger contribution, and steward capture by their home unit.
- AC-2.6: An OmniOne walkthrough demonstrates the Bali and Costa Rica SHURs establishing a shared knowledge repository for governance best practices, including the governance structure and one dispute about access permissions.
- AC-2.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Required for any meaningful inter-unit resource sharing.

### FR-3: Federation Agreement (`federation-agreement`)

**Description:** Draft, negotiate, and ratify bilateral or multilateral agreements between AZPOs. Federation agreements define the terms of ongoing coordination -- what each AZPO commits to, what shared protocols apply, how disputes are handled, and how the agreement evolves. Every federation agreement goes through each participating AZPO's own ACT process for ratification.

**Acceptance Criteria:**
- AC-3.1: The skill defines federation agreement types (bilateral cooperation, multilateral protocol, service-level agreement, mutual recognition, graduated engagement compact) with structural requirements for each.
- AC-3.2: The step-by-step process covers negotiation (parallel advice phases in each AZPO), drafting (collaborative or sequential), ratification (each AZPO runs its own consent round), registration (in each AZPO's agreement registry plus a shared registry if one exists), and review.
- AC-3.3: The output artifact is a federation agreement registered in all participating AZPOs' registries with mutual ratification records.
- AC-3.4: The authority boundary check ensures no AZPO's negotiators exceed their mandate (negotiation authority must be explicitly scoped by the sending AZPO).
- AC-3.5: The capture resistance check addresses power asymmetry (wealthier or larger AZPO dictating terms), urgency pressure (rushing ratification), and precedent capture (early agreements becoming de facto standards that constrain later-joining AZPOs).
- AC-3.6: An OmniOne walkthrough demonstrates three SHUR communities drafting a multilateral protocol for member transfers between SHURs, including one SHUR that initially objects to a provision and the negotiation process to resolve it.
- AC-3.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on FR-1 establishing the basic cross-unit interaction pattern.

### FR-4: Inter-Unit Liaison (`inter-unit-liaison`)

**Description:** Define and maintain ongoing cross-AZPO coordination relationships through designated liaison roles. Liaisons are authorized to communicate across AZPO boundaries, track shared commitments, flag emerging coordination needs, and serve as first points of contact for cross-unit requests. The skill defines liaison authority scope, appointment process, accountability, and the distinction between liaison communication and binding decisions.

**Acceptance Criteria:**
- AC-4.1: The skill defines liaison role types (bilateral liaison, multilateral coordinator, domain-specific liaison) with authority scope for each.
- AC-4.2: The step-by-step process covers liaison appointment (through authority-assignment in each AZPO), mandate definition (what the liaison can communicate, explore, and recommend vs. what requires AZPO-level consent), reporting cadence, and role review.
- AC-4.3: The output artifact is a liaison role agreement specifying mandate, boundaries, reporting requirements, and review date.
- AC-4.4: The authority boundary check prevents liaisons from making binding commitments on behalf of their AZPO without explicit authorization and prevents the liaison role from becoming a bottleneck (others can still communicate across AZPO boundaries).
- AC-4.5: The capture resistance check addresses liaisons developing personal relationships that override structural accountability, and liaison roles accumulating informal power through information asymmetry.
- AC-4.6: An OmniOne walkthrough demonstrates the Bali SHUR appointing a liaison to the Economics circle's cross-SHUR coordination group, including the mandate definition and one situation where the liaison needs to check back with their SHUR before committing.
- AC-4.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Supports ongoing coordination, depends on FR-1 and FR-3 patterns.

### FR-5: Polycentric Conflict Navigation (`polycentric-conflict-navigation`)

**Description:** Resolve disputes where two or more AZPOs' authority claims conflict, their agreements contradict, or their resource decisions affect each other adversely. This is distinct from Layer VI (Conflict and Repair) which handles interpersonal and intra-AZPO conflict. Polycentric conflict navigation handles structural conflicts between autonomous units that each have legitimate governance authority within their domains.

**Acceptance Criteria:**
- AC-5.1: The skill defines conflict types (authority overlap, agreement contradiction, resource competition, boundary dispute, protocol divergence) with resolution paths for each.
- AC-5.2: The step-by-step process provides a three-tier resolution approach: direct negotiation between affected AZPOs, facilitated dialogue with a mutually agreed neutral party (from a third AZPO or the liaison pool), and structural resolution through federation agreement amendment.
- AC-5.3: The output artifact is a polycentric conflict resolution record documenting the dispute, resolution process, outcome agreement, and any federation agreement amendments.
- AC-5.4: The authority boundary check ensures no AZPO or body can impose a resolution on another -- all resolutions require mutual consent through each AZPO's own ACT process.
- AC-5.5: The capture resistance check addresses larger AZPOs leveraging their size to pressure resolution outcomes, neutral parties developing structural bias toward one AZPO, and resolution fatigue leading to capitulation rather than genuine consent.
- AC-5.6: An OmniOne walkthrough demonstrates a boundary dispute between the Bali SHUR and the Costa Rica SHUR about which SHUR's space agreements apply to a traveling member who spends time in both, including escalation from direct negotiation to facilitated dialogue and the resulting protocol clarification.
- AC-5.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on all other Layer V skills establishing the coordination structures that generate conflicts.

---

## Non-Functional Requirements

### NFR-1: No Apex Authority

No skill in this layer may create, imply, or require a central authority that resolves inter-unit disputes by fiat. All resolution is lateral -- between the affected AZPOs themselves, optionally with facilitation but never with imposed outcomes. This is the millet system lesson: shared protocols without a Sultan.

### NFR-2: Dual-Consent Requirement

Every cross-AZPO action requires consent from both (or all) participating AZPOs through their own internal ACT processes. No AZPO can be bound by another's decision. Silence is not consent.

### NFR-3: Modularity

Each skill must function independently. A participant or AI agent reading a single SKILL.md must be able to understand and execute the described process without requiring other Layer V skills to be loaded. Skills may reference each other by name but must not depend on another being "installed."

### NFR-4: Line Limit

Each SKILL.md must be under 500 lines. Supporting material (federation agreement templates, liaison mandate guides, conflict navigation protocols) goes in `references/` or `assets/`.

### NFR-5: Portability

Every skill is NEOS-generic at its structural level. OmniOne-specific details (SHUR network, TH/AE/OSC bodies, specific multi-site geography) appear as clearly marked examples and configuration blocks. Another ecosystem with different autonomous units must be able to fork and replace these.

### NFR-6: Graduated Engagement

Inter-AZPO relationships must support multiple engagement tiers. Not every AZPO needs to be tightly federated with every other. Skills must accommodate relationships ranging from minimal (mutual acknowledgment) to deep (shared governance structures).

### NFR-7: Validation

Every SKILL.md must pass automated validation via `scripts/validate_skill.py`. The validator checks: YAML frontmatter presence and required fields, all 12 sections (A-L) present with substantive content, OmniOne walkthrough present, all 7 stress-test scenarios present.

---

## User Stories

### US-1: SHUR Requests Cross-Unit Collaboration
**As** a Bali SHUR member who wants to adapt a governance innovation from the Costa Rica SHUR,
**I want** a clear process for making a formal request across AZPO boundaries,
**So that** my request is routed properly through both SHURs' governance processes rather than depending on personal connections.

**Given** the member has identified a governance practice in another SHUR they want to adopt,
**When** they follow the cross-azpo-request skill process,
**Then** a tracked request is visible to both SHURs with clear status and response documentation.

### US-2: AI Agent Navigates Inter-Unit Request
**As** an AI agent assisting a participant with a cross-AZPO request,
**I want** to understand the dual-consent routing and which AZPO's process applies at each stage,
**So that** I can guide the participant through the correct steps on both sides.

**Given** a cross-AZPO request has been initiated,
**When** the AI agent reads the cross-azpo-request skill,
**Then** it can identify the originating AZPO's outbound process, the target AZPO's inbound process, and the current status.

### US-3: Multiple SHURs Establish Shared Resources
**As** stewards from three SHUR communities,
**We want** a structured process for establishing and governing a shared resource,
**So that** no single SHUR controls the shared resource and all have equitable access.

**Given** three SHURs have identified a resource they want to share,
**When** they follow the shared-resource-stewardship skill process,
**Then** a governance agreement is produced and ratified through each SHUR's own consent process.

### US-4: SHURs Draft Federation Protocol
**As** the liaison group from four SHUR communities,
**We want** to draft a multilateral agreement defining how members transfer between SHURs,
**So that** member mobility is governed by clear, mutually agreed protocols.

**Given** multiple SHURs want to formalize member transfer procedures,
**When** they follow the federation-agreement skill process,
**Then** a multilateral agreement is negotiated, ratified by each SHUR, and registered in all parties' agreement registries.

### US-5: Liaison Maintains Cross-SHUR Coordination
**As** a designated liaison between the Bali and Mexico SHURs,
**I want** clear boundaries on what I can communicate and explore vs. what requires my SHUR's formal consent,
**So that** I can be effective in my coordination role without overstepping my mandate.

**Given** the liaison has been appointed with a defined mandate,
**When** they encounter a situation at the boundary of their authority,
**Then** the inter-unit-liaison skill tells them whether they can proceed or must check back with their SHUR.

### US-6: Two SHURs Resolve a Boundary Dispute
**As** representatives from two SHURs whose authority claims overlap,
**We want** a structured resolution process that does not require a central authority to decide for us,
**So that** we can resolve our dispute while maintaining our respective autonomy.

**Given** two SHURs have a structural conflict about overlapping authority claims,
**When** they follow the polycentric-conflict-navigation skill process,
**Then** a resolution is reached through mutual consent with documentation of the dispute, process, and outcome.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-05-inter-unit/
    README.md
    cross-azpo-request/
      SKILL.md
      assets/
        cross-azpo-request-template.yaml
      references/
      scripts/
    shared-resource-stewardship/
      SKILL.md
      assets/
        shared-resource-agreement-template.yaml
      references/
      scripts/
    federation-agreement/
      SKILL.md
      assets/
        federation-agreement-template.yaml
        engagement-tiers.yaml
      references/
      scripts/
    inter-unit-liaison/
      SKILL.md
      assets/
        liaison-mandate-template.yaml
      references/
      scripts/
    polycentric-conflict-navigation/
      SKILL.md
      assets/
        conflict-resolution-record-template.yaml
        resolution-tiers.yaml
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name
description: "Pushy description..."
layer: 5
version: 0.1.0
depends_on: []
---
```

### Build Order Rationale

Skills are built from basic interaction to complex coordination:
1. `cross-azpo-request` -- Anchor skill, defines the basic cross-unit interaction shape
2. `shared-resource-stewardship` -- Defines shared resource governance (requires cross-unit interaction pattern)
3. `federation-agreement` -- Defines formal multi-unit agreements (requires both interaction and shared resource patterns)
4. `inter-unit-liaison` -- Defines ongoing coordination roles (requires all previous patterns to understand what liaisons coordinate)
5. `polycentric-conflict-navigation` -- Resolves structural conflicts (requires all coordination structures to be defined, as conflicts emerge from them)

### Cross-Layer References

Each skill will reference skills from earlier layers:
- `agreement-creation` -- Federation agreements are agreements
- `act-consent-phase` -- Cross-AZPO decisions use consent
- `authority-assignment` -- Liaisons are roles with scoped authority
- `funding-pool-stewardship` -- Shared resource pools reference pool governance
- `resource-request` -- Cross-AZPO resource requests reference the request pattern

These are informational references, not loading dependencies.

---

## Out of Scope

- **Inter-ecosystem coordination** -- This layer handles AZPO-to-AZPO coordination within a single NEOS ecosystem. Coordination between two separate ecosystems both running NEOS is a future extension.
- **Technical interoperability** -- The skills define governance protocols for cross-unit coordination, not technical infrastructure (APIs, shared databases, communication platforms).
- **SHUR-specific operational details** -- How SHURs manage day-to-day operations (housing allocation, meal scheduling, facility maintenance) is OmniOne configuration, not NEOS core.
- **Layer VII (Safeguard) integration** -- Capture detection at the inter-unit level is referenced in each skill's capture resistance check but the systemic safeguard mechanisms belong to Layer VII.

---

## Open Questions

1. **Default engagement tier for new AZPOs**: When a new AZPO forms within the ecosystem, what is its default relationship with existing AZPOs? Recommendation: default to "mutual acknowledgment" (observe tier) with active opt-in required for deeper engagement.

2. **Federation agreement registry location**: Where does a cross-AZPO agreement live? In each AZPO's registry? In a shared registry? Both? Recommendation: registered in each participating AZPO's registry (federated storage) with a shared index maintained by the liaison coordination body (if one exists).

3. **Neutral party selection for conflict navigation**: How is a neutral facilitator selected when two AZPOs cannot agree on one? Recommendation: each AZPO proposes three candidates from other AZPOs, overlapping names are selected, if no overlap both lists are combined and random selection is used.

4. **Liaison term limits**: Should liaison roles have mandatory term limits or just review dates? Recommendation: mandatory rotation every 12 months with option for one 12-month extension, to prevent information concentration and informal power accumulation.
