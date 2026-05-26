---
name: proposal-creation
description: "Create and submit a formal proposal to change agreements, processes, resources, or structure -- routing it through the appropriate ACT decision level with synergy check and impact analysis."
layer: 3
version: 0.1.0
depends_on: [domain-mapping]
---

# proposal-creation

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
- **Impacted parties**: all participants, circles, or ETHOS that will be affected
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

- Proposals affecting multiple ETHOS require representatives from each ETHOS in the synergy check and advice phases
- Cross-ETHOS proposals are tracked in all affected units' registries with linked entries
- Proposal numbering includes an ecosystem prefix for cross-ecosystem uniqueness (e.g., OMNI-PROP-2026-042)
- When two NEOS ecosystems need to coordinate, proposals use the inter-unit coordination protocol (Layer V, deferred). This skill notes the extensibility point: the routing logic in Step 4 can be extended to include cross-ecosystem routing when Layer V is available.
