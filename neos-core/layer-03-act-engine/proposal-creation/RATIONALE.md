---
skill: proposal-creation
type: rationale
---

# proposal-creation — Rationale & Design Notes

## A. Structural Problem It Solves

Without formal proposals, changes happen through informal influence — whoever has the loudest voice or most social capital drives change, and others discover the new reality after the fact. This skill ensures every proposed change has a clear author, rationale, affected scope, and enters a legitimate decision process. It prevents shadow governance where changes are made without traceable process and prevents the "someone decided this in a side conversation" failure mode.

## B. Domain Scope

This skill applies to any domain where a change to existing agreements, processes, resources, or structure is proposed. Proposal types include: EcoPlan proposals (ecosystem-level strategic changes), GenPlan proposals (generative plan changes within an ETHOS), agreement amendments (modifications to existing agreements, which then route to agreement-amendment), resource requests (allocation or reallocation of shared resources), and policy changes (modifications to governance processes themselves). The skill routes each type to the correct ACT level based on scope and impact.

## OmniOne Walkthrough

Kai, a Builder in the AE, has been coordinating resource distribution across multiple OmniOne circles and notices there is no dedicated circle for economic coordination — decisions about resource allocation happen ad hoc across various AE working groups, leading to duplication and conflicting commitments.

Kai drafts a proposal using the proposal-template: type=policy_change, decision_type=solution, domain=AE organizational structure, urgency=normal. The proposed change: create a new Economics Circle within the AE with a defined domain covering resource allocation, funding pool management, and inter-circle economic coordination. Kai identifies impacted parties: all AE members (the circle would live within AE), TH members who participate in resource discussions, and OSC (for structural alignment with the Master Plan).

During the synergy check, Kai queries the registry and discovers that another Builder, Lena, submitted a proposal last month for a "Resource Stewardship Circle" — related in scope but narrower (focused only on asset stewardship, not broader economic coordination). Kai contacts Lena directly. After discussion, they agree that Kai's proposal is broader and would subsume Lena's scope. Lena withdraws her proposal and joins as co-sponsor of Kai's expanded Economics Circle proposal. The synergy check documents this merger.

Because the proposal affects both AE (where the new circle would operate) and TH (whose members might participate), it routes to cross-circle ACT — representatives from both AE and TH will participate in the consent phase. Kai submits the proposal and it enters the Advice phase with a 7-day window. Twelve pieces of advice arrive from AE members, TH members, and an OSC observer.

Edge case: During advice, OSC member Reza raises a concern that the proposed Economics Circle's domain might overlap with the OSC's ecosystem-level resource authority. Specifically, who decides when a resource question is "circle-level" versus "ecosystem-level"? Kai must clarify the domain boundary in the proposal text before it can proceed to consent. Kai adds a clause: "The Economics Circle manages intra-AE resource allocation up to 10% of the total ecosystem fund. Allocations exceeding 10% or affecting non-AE domains require OSC-level ACT process." Reza's concern is documented as partially integrated with clear rationale.

The output artifact: proposal OMNI-PROP-2026-015, status=advice, with full synergy check record, 12 advice entries, and the documented merger with Lena's prior proposal.

## Stress-Test Results

### 1. Capital Influx

A crypto investor who recently donated significantly to OmniOne submits a proposal to create a "Venture Circle" with special authority over funding decisions for new projects. The synergy check reveals this would concentrate decision-making power in a body influenced by the donor's financial relationship. During the advice phase, multiple members flag that this contradicts the "Capital does not equal Power" core principle — financial contribution does not grant governance authority. The proposal's impacted parties include everyone who currently participates in resource decisions, ensuring broad input. The consent phase evaluates the proposal on structural merits: does a Venture Circle serve the ecosystem's aims, or does it serve the donor's interests? The capture resistance check flags the proposal as a capital capture risk. If the proposal is modified to remove the special authority provisions and create a standard circle with normal scoped authority, it may proceed. The donor's financial contribution is acknowledged but does not modify the consent threshold or process timeline.

### 2. Emergency Crisis

OmniOne's primary digital infrastructure fails, taking down communication tools used for governance coordination. Three AE members invoke the emergency proposal process to reallocate emergency funds for immediate infrastructure restoration. The synergy check runs at 24-hour compression — no conflicting proposals exist. The proposal enters emergency ACT: 24-hour advice window (5 of 12 impacted AE members respond — others cannot due to the infrastructure outage itself), emergency consent quorum (minimum 50% of reachable affected parties). The proposal is adopted with a 30-day auto-expiry. Once infrastructure is restored, the emergency proposal is flagged for re-proposal through normal channels. The post-emergency review evaluates whether the emergency declaration was warranted and whether the reallocation amount was appropriate. Any ongoing infrastructure changes require a standard-timeline proposal.

### 3. Leadership Charisma Capture

A popular OmniOne leader submits five proposals in a single week, all reinforcing their personal vision for the ecosystem's direction — restructuring three circles, changing the resource allocation formula, creating a new advisory role, amending two existing agreements, and modifying the meeting facilitation protocol. The proposal rate limit flags this: only 3 active proposals are permitted per person. The leader must withdraw or archive two proposals before new ones can be accepted. Other members report proposal fatigue — they cannot meaningfully engage with five major proposals simultaneously. The synergy check reveals overlapping scope between several proposals, requiring consolidation. The structural safeguard ensures that no individual, regardless of popularity, can dominate the governance agenda through volume. The leader's proposals each receive the same scrutiny through the full ACT process as any other member's proposals.

### 4. High Conflict / Polarization

Two factions within OmniOne submit competing proposals for new member onboarding. Faction A proposes strict vetting with a 90-day probation period and sponsor requirements. Faction B proposes open access with minimal barriers and a "learn by participating" philosophy. The synergy check flags the two proposals as directly conflicting and requires reconciliation before either proceeds to consent. The proposers meet but cannot agree. At GAIA Level 4, a coach identifies the core tensions: Faction A fears dilution of culture and values; Faction B fears exclusivity and gate-keeping. The coach facilitates a third solution: tiered access where new members have immediate TH access (satisfying openness) with a 60-day mentorship pathway to full AE participation (satisfying cultural integration concerns). Both factions contribute to refining the unified proposal. The process ensures that polarization is resolved through structural synthesis, not through one faction outvoting the other.

### 5. Large-Scale Replication

At 5,000 members across 15 locations and 80 circles, the proposal system handles hundreds of proposals per month. Domain routing through the registry ensures proposals reach the right scope — most proposals are circle-internal (Level 1-2, handled without formal ACT). Cross-circle proposals are routed by domain matching: the registry identifies which circles' domains are affected by a given proposal. The synergy check becomes essential at scale, preventing the same issue from generating 10 independent proposals across different circles. The proposal numbering system (ecosystem prefix + sequential ID) maintains uniqueness. OSC-level proposals remain rare — perhaps 2-3 per quarter — while circle-level proposals handle the bulk of day-to-day governance. Facilitator capacity scales through each circle maintaining its own trained facilitators.

### 6. External Legal Pressure

A regulatory body informs OmniOne that it must implement Know Your Customer (KYC) procedures for all members who participate in financial transactions within the ecosystem. An AE member submits a proposal to create a KYC compliance process. The proposal goes through the full ACT process despite originating from external pressure — regulatory requirements do not bypass governance. During the advice phase, members distinguish between legal compliance (necessary for the specific jurisdiction) and governance modification (how compliance is implemented). The consent phase evaluates implementation options: centralized identity verification versus self-sovereign identity tools versus third-party compliance service. The adopted approach satisfies the legal requirement while minimizing surveillance infrastructure. The proposal applies only to the jurisdiction requiring KYC — it does not become a global ecosystem policy unless separately proposed and consented to.

### 7. Sudden Exit of 30% of Participants

After a major disagreement over expansion strategy, 15 of 50 members exit OmniOne within two weeks. Multiple active proposals lose their proposers. The adoption mechanism activates: for each orphaned proposal, remaining impacted parties are notified and given 14 days to adopt the proposal. If adopted, the new steward inherits the proposal's current state and all documentation. If no one adopts, the proposal is archived with the reason "proposer exit, no adopter." Proposals where all impacted parties have departed are automatically archived — there is no constituency for the change. The proposal registry flags all entries associated with departed members. Active proposals that retain their proposers continue normally, with quorum thresholds recalculated based on current membership. New members joining after the exodus may propose fresh alternatives to archived proposals through normal process.
