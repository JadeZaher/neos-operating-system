---
name: proposal-creation
description: "Create and submit a formal proposal to change agreements, processes, resources, or structure -- routing it through the appropriate ACT decision level with synergy check and impact analysis."
layer: 3
version: 0.1.0
depends_on: [domain-mapping]
---

# proposal-creation

## A. Structural Problem It Solves

Without formal proposals, changes happen through informal influence — whoever has the loudest voice or most social capital drives change, and others discover the new reality after the fact. This skill ensures every proposed change has a clear author, rationale, affected scope, and enters a legitimate decision process. It prevents shadow governance where changes are made without traceable process and prevents the "someone decided this in a side conversation" failure mode.

## B. Domain Scope

This skill applies to any domain where a change to existing agreements, processes, resources, or structure is proposed. Proposal types include: EcoPlan proposals (ecosystem-level strategic changes), GenPlan proposals (generative plan changes within an AZPO), agreement amendments (modifications to existing agreements, which then route to agreement-amendment), resource requests (allocation or reallocation of shared resources), and policy changes (modifications to governance processes themselves). The skill routes each type to the correct ACT level based on scope and impact.

## C. Trigger Conditions

- A participant identifies a need for change that cannot be resolved through existing agreements or circle-internal culture code
- An existing agreement needs amendment (the proposal then links to the agreement-amendment skill)
- A new resource allocation or structural change is needed that affects participants beyond a single circle
- A conflict has been identified that requires a structural solution, not just interpersonal mediation
- An emergency requires a structural response under compressed timelines

## D. Required Inputs

- **Proposer identity**: who is proposing, their role, and their authority scope
- **Proposal type**: ecoplan, genplan, amendment, resource_request, or policy_change
- **Decision type**: preference (no structural impact, may resolve at Level 1-2) or solution (structural impact, requires full ACT from Level 3)
- **Affected domain**: the boundary within which the change operates
- **Proposed change text**: what specifically will change, written clearly enough for any participant to understand
- **Rationale**: why this change is needed, what problem it solves, what happens if nothing changes
- **Impacted parties**: all participants, circles, or AZPOs that will be affected
- **Urgency level**: normal (standard timelines), elevated (compressed but not emergency), or emergency (maximum compression, provisional rules apply)
- **Desired timeline**: when the proposer hopes to see the change implemented

## E. Step-by-Step Process

1. **Identify need.** The proposer determines whether this is a preference decision (matters of taste or convenience with no structural impact, resolvable at GAIA Level 1-2 without formal ACT) or a solution decision (matters with structural, resource, or authority impact requiring full ACT starting at Level 3).
2. **Draft proposal.** Using `assets/proposal-template.yaml`, the proposer fills in all required fields. Co-sponsors may be added — co-sponsorship demonstrates broader support but does not bypass any process step.
3. **Synergy check (GAIA Level 3).** The proposer queries the agreement registry for existing or in-progress proposals in the same domain. The check asks: Is this already being addressed? Does it conflict with active proposals? Does it duplicate existing agreements? If a related proposal exists, the proposer documents the relationship (complements, supersedes, or conflicts) and may be asked to merge with the existing proposal's author.
4. **Route to ACT level** based on scope:
   - *Preference decisions within a single circle*: resolve at Level 1-2 (circle discussion, no formal ACT)
   - *Solution decisions within a single circle*: circle-level ACT
   - *Solution decisions affecting multiple circles*: cross-circle ACT with representatives
   - *Ecosystem-level changes*: OSC-level ACT
   - *UAF amendments*: OSC consensus mode (routes to agreement-amendment)
5. **Submit.** The proposal enters the Advice phase per the act-advice-phase skill, with all impacted parties notified and an advice window opened based on urgency level.
6. **Status tracking.** The proposal status updates at each phase transition: draft → synergy_check → advice → consent → test → adopted (or reverted/withdrawn/archived).

## F. Output Artifact

A numbered, versioned proposal document following `assets/proposal-template.yaml`. Contains: unique proposal ID, type, decision type, title, full text of proposed change, rationale, proposer and co-sponsors, affected domain, impacted parties list, urgency level, status, synergy check results, and linked records for advice log, consent record, and test report as the proposal moves through ACT phases.

## G. Authority Boundary Check

- Proposers can only submit proposals within their domain. A TH member proposes within TH scope; proposing changes to AE processes requires cross-circle routing.
- No one can submit a proposal on behalf of another without written delegation documented in the proposal.
- The facilitator receiving the proposal checks domain alignment but cannot reject on content grounds — only on process grounds (missing required fields, incorrect routing).
- Emergency proposals can be submitted by any 3 circle members acting jointly under provisional emergency rules (pending Layer VIII formalization).
- Proposal rate limits apply per proposer: maximum 3 active proposals per person (ecosystem configurable). This prevents any individual from flooding the decision process.
- Authority scopes are formally defined by the domain-mapping and role-assignment skills in Layer II (Authority & Role).

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

## H. Capture Resistance Check

**Capital capture.** A wealthy stakeholder submits proposals restructuring resource access in their favor. The synergy check flags proposals that would concentrate resources or decision-making power. Affected parties include all who would lose access, ensuring broad input during the advice phase.

**Charismatic capture / proposal fatigue.** A popular leader submits proposals frequently, creating fatigue where others stop engaging. The proposal rate limit (3 active per person) structurally prevents flooding. The synergy check ensures each proposal addresses a distinct need.

**Emergency capture.** "Urgent" framing used to skip the synergy check. Emergency proposals still require a synergy check — compressed to 24 hours but not eliminated. Emergency urgency must be declared by 3 circle members acting jointly, not by the proposer alone.

**Informal capture.** A decision is made informally and a proposal is submitted after-the-fact to rubber-stamp it. The proposal must be submitted BEFORE implementation. Retroactive proposals are flagged in the status tracking system and require explicit justification during the advice phase.

## I. Failure Containment Logic

- **Synergy check reveals conflict**: proposer must address the conflict before proceeding — resolve with the conflicting proposal's author, merge proposals, or document why both should proceed independently
- **Impacted parties cannot be identified**: expand scope upward until a clear domain boundary is found; when in doubt, include rather than exclude
- **Proposer withdraws**: proposal is archived with the withdrawal reason, and all impacted parties are notified
- **Proposal stalls** (no activity for 30 days): automatic reminder sent to proposer; after 60 days total inactivity, proposal is archived
- **Routing dispute** (proposer claims circle-level, affected parties claim ecosystem-level): default to the broader scope — it is safer to over-consult than under-consult

## J. Expiry / Review Condition

- Proposals that have not entered the Advice phase within 30 days of creation are automatically archived
- Proposals in active ACT phases follow the timelines defined in those phase skills
- Emergency proposals auto-expire in 30 days even if adopted — they are flagged for re-proposal through normal process for permanent adoption
- The proposal status tracking field must be updated at each phase transition; stale status triggers alerts

## K. Exit Compatibility Check

- If the proposer exits mid-process, another impacted party may adopt the proposal with consent of remaining impacted parties. The adopter inherits the proposal's current state and documentation.
- If all impacted parties exit, the proposal is automatically archived — there is no one left to be affected by the change.
- Proposals do not create ongoing obligations for the proposer beyond the ACT process itself.
- Adopted proposals become agreements (registered via agreement-creation) and follow agreement exit rules from that point forward.

## L. Cross-Unit Interoperability Impact

- Proposals affecting multiple AZPOs require representatives from each AZPO in the synergy check and advice phases
- Cross-AZPO proposals are tracked in all affected units' registries with linked entries
- Proposal numbering includes an ecosystem prefix for cross-ecosystem uniqueness (e.g., OMNI-PROP-2026-042)
- When two NEOS ecosystems need to coordinate, proposals use the inter-unit coordination protocol (Layer V, deferred). This skill notes the extensibility point: the routing logic in Step 4 can be extended to include cross-ecosystem routing when Layer V is available.

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
