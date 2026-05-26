---
name: participatory-allocation
description: "Run participatory budgeting assemblies where circle members collectively allocate funding pool resources through structured deliberation and consent -- not majority vote, not first-come-first-served, not steward fiat."
layer: 4
version: 0.1.0
depends_on: [resource-request, funding-pool-stewardship, act-consent-phase, consensus-check]
---

# participatory-allocation

## C. Trigger Conditions

- A funding pool's governance agreement specifies a periodic allocation cycle (quarterly, semi-annual)
- An unscheduled inflow significantly increases pool resources, warranting collective allocation
- Previously allocated resources are returned unused and the pool balance exceeds the threshold for collective allocation
- A governing circle requests a special allocation assembly to address emerging priorities
- An emergency reserve pool is replenished after a drawdown and the governing body decides to reallocate the replenished amount
- A pool review reveals that standing allocations no longer match ecosystem needs and reallocation is warranted

## D. Required Inputs

- **Pool identification**: which funding pool's resources are being allocated (mandatory, with current balance and governance rules from the pool governance agreement)
- **Allocation amount**: the total amount available for allocation in this assembly (mandatory, determined by the pool steward based on pool balance, standing commitments, and reserve requirements)
- **Proposal submissions**: resource allocation proposals from eligible participants, each following the resource-request template format (mandatory, minimum 2 proposals for an assembly to proceed)
- **Participant roster**: eligible participants for this allocation assembly, determined by the pool's governing circle membership (mandatory)
- **Facilitator assignment**: a designated facilitator who manages the assembly process but has no allocation authority (mandatory, assigned through role-assignment)
- **Conflict of interest disclosures**: each participant discloses any personal stake in submitted proposals (mandatory, submitted before deliberation begins)
- **Evaluation criteria**: the pool governance agreement's stated purpose, priority areas, and any ecosystem-level strategic priorities that inform allocation (mandatory)

## E. Step-by-Step Process

1. **Announce assembly.** The pool steward announces the allocation assembly at least 21 days before the assembly date. The announcement includes: pool balance, allocation amount, proposal submission deadline, eligibility criteria, and assembly schedule. The facilitator is confirmed.
2. **Open proposal window (days 1-14).** Eligible participants submit allocation proposals using the resource-request template. Each proposal must include: resource type, amount requested, rationale connecting to pool purpose, timeline, stewardship commitment, and expected outcomes. Proposals are visible to all eligible participants upon submission -- no hidden proposals.
3. **Conflict of interest disclosure (day 14).** Before deliberation begins, every assembly participant submits a conflict of interest disclosure identifying any personal stake in any submitted proposal. Participants with direct financial interest in a proposal may participate in deliberation but must abstain from the consent round on that specific proposal.
4. **Deliberation round 1 (days 15-18).** The facilitator presents all proposals to the full assembly. Each proposer has equal time to present their rationale. Participants ask clarifying questions. The facilitator ensures every proposal receives examination -- popular proposals do not crowd out smaller or less visible ones. Written feedback is collected for each proposal.
5. **Proposal refinement (days 18-19).** Proposers revise their submissions based on deliberation feedback. Proposers may reduce requested amounts, modify timelines, combine with other proposals, or withdraw. Revised proposals are published to all participants.
6. **Deliberation round 2 (days 19-21).** The assembly examines revised proposals. The facilitator maps the total requested amount against the available allocation amount. If total requests exceed available resources, the facilitator names the gap explicitly and opens discussion about prioritization. No proposal is eliminated by facilitator judgment -- prioritization emerges from the consent process.
7. **Allocation consent round.** Each proposal enters a consent round with the full eligible assembly (minus conflicted participants for their specific proposal). Proposals are considered in random order to prevent sequencing bias. For each proposal, positions are recorded: consent, stand aside, or objection with stated reason. Proposals that achieve consent are allocated. Proposals that receive objections enter integration rounds.
8. **Integration and third-solution rounds.** When a proposal receives an objection, the proposer and objector work with the facilitator to find an integration. If the objection concerns amount, the proposal may be reduced. If the objection concerns alignment, the proposal may be reframed. If two integration rounds fail, the assembly enters a third-solution round: the facilitator invites the full assembly to generate an alternative that addresses both the proposal's intent and the objection's concern. Third solutions are evaluated through a fresh consent round.
9. **Oversubscription resolution.** If consented proposals exceed the allocation amount, the assembly enters a proportional reduction round. All consented proposals are presented with their approved amounts. The facilitator proposes proportional reduction (each proposal reduced by the same percentage). Participants may consent to proportional reduction, or propose alternative distributions. The distribution method is decided by consent, not facilitator fiat.
10. **Ratification and recording.** The facilitator publishes the final allocation record using `assets/allocation-record-template.yaml`. The record documents: all proposals considered, deliberation summaries, consent positions, objections and integrations, final allocation amounts, dissenting positions, and the next review date. All participants review the record for accuracy. The record is registered in the agreement registry alongside the pool governance agreement.

## F. Output Artifact

An allocation record following `assets/allocation-record-template.yaml`. The document contains: assembly ID, pool ID, allocation date, total amount allocated, participant roster with attendance, complete list of proposals considered (including withdrawn), deliberation notes for each proposal, consent positions for each proposal, objection and integration records, final allocation amounts per proposal, any proportional reduction applied, dissenting positions (participants who stood aside with their reasons), facilitator notes, and the next scheduled allocation assembly date. The record is accessible to every ecosystem participant. Standing allocations from the assembly are reflected in the pool's transaction log.

## G. Authority Boundary Check

- **The facilitator** manages the assembly process but cannot approve, deny, or prioritize proposals on content grounds. The facilitator's authority is procedural: enforcing time limits, ensuring all proposals receive examination, and recording positions accurately.
- **No participant** receives allocation weight proportional to their economic contribution, seniority, or social status. Each eligible participant's consent or objection carries equal structural weight.
- **Proposers** cannot vote on their own proposals. They participate in deliberation and integration but abstain from the consent round on their specific proposal.
- **The pool steward** determines the allocation amount based on pool governance rules but does not influence which proposals receive funding. The steward's role in the assembly is administrative, not decisional.
- **OSC involvement** is required for ecosystem strategic pool allocations that exceed the pool's circle-level authority threshold (default 25% of pool balance in a single assembly).
- **Cross-ETHOS shared pool assemblies** require participation from all contributing ETHOS. No single ETHOS can dominate the allocation through higher participation numbers -- consent requires addressing objections from any participating unit.

## H. Capture Resistance Check

**Capital capture.** A wealthy participant funds the pool generously and then submits a proposal requesting resources back for their preferred project. The skill prevents this: contribution size creates no priority in the proposal queue, no expedited review, and no additional consent weight. The proposal is evaluated on its alignment with pool purpose, not on the proposer's contribution history. Conflict of interest disclosure requires the participant to declare their funding relationship with the pool.

**Charismatic capture.** An eloquent presenter's proposal receives disproportionate support because of delivery quality rather than proposal merit. The skill resists this through structural equalization: written proposals are distributed before oral presentations, equal presentation time prevents charismatic speakers from dominating, the facilitator ensures quieter participants contribute during deliberation, and the consent round records positions before group discussion can create social pressure. Objections must be reasoned and specific -- "I just feel uneasy" is explored for underlying concerns, not dismissed.

**Emergency capture.** A participant frames their proposal as urgent to pressure the assembly into allocation without full deliberation. The skill prevents this: all proposals follow the same timeline and deliberation process regardless of urgency framing. If a genuine emergency exists, it follows the emergency resource-request process -- it does not hijack a participatory allocation assembly.

**Informal capture.** Faction coordination where a group agrees in advance to consent to each other's proposals and object to competitors'. The facilitator monitors for coordinated voting patterns. Objections must state specific, reasoned concerns -- generic objections that appear coordinated are challenged by the facilitator for substantive reasoning. The written deliberation record creates accountability for each position.

## I. Failure Containment Logic

- **Insufficient proposals** (fewer than 2 submitted): the assembly is postponed by 14 days with a renewed call for proposals. If still insufficient, the allocation amount rolls into the next scheduled assembly and the steward processes any urgent needs through individual resource requests.
- **Quorum not met**: the assembly timeline extends by 7 days. Quorum is never lowered. If quorum is still not met after extension, the assembly is cancelled and a governance review examines whether the pool's governing circle scope matches its active membership.
- **All proposals receive objections**: the facilitator invokes third-solution rounds for each. If third solutions fail for all proposals, the allocation amount is preserved in the pool for the next assembly. The facilitator reports the systemic blockage to the governing circle, which may trigger a GAIA escalation to address underlying tensions.
- **Oversubscription consensus fails**: if the assembly cannot reach consent on a distribution method for oversubscribed proposals, the fallback is equal proportional reduction across all consented proposals. This default is stated in the pool governance agreement.
- **Facilitator bias detected**: any participant can challenge the facilitator's procedural decisions during the assembly. A challenge triggers a brief pause and a participant vote on the procedural question. If the challenge is sustained, the facilitator is replaced for the remainder of the assembly.

## J. Expiry / Review Condition

- Allocation records do not expire, but the allocations themselves have timelines defined in each proposal's stewardship commitment. Resources allocated but unused beyond the proposal's timeline revert to the pool.
- Each allocation assembly sets the date for the next assembly (default: next quarter). Missing the scheduled assembly date triggers a notification to the pool steward and governing circle.
- Standing allocations (multi-quarter commitments approved in a previous assembly) are reviewed at each subsequent assembly. The assembly may modify or revoke standing allocations through the consent process.
- The allocation assembly process itself is reviewed annually as part of the pool governance agreement review. The review examines: participation rates, proposal quality, deliberation effectiveness, and whether the assembly structure serves the pool's purpose.

## K. Exit Compatibility Check

When a participant who received an allocation exits the ecosystem:
- Unfulfilled allocations are cancelled. Resources revert to the pool for the next assembly.
- In-progress allocations enter the 30-day wind-down. Resources already disbursed for completed work are not clawed back. Resources for incomplete work revert to the pool.
- Stewardship commitments for allocated resources transfer to a designated successor or revert to the pool steward.
- The participant's deliberation contributions and consent positions remain in the assembly record as historical data.

When a facilitator exits:
- A replacement facilitator is appointed through role-assignment for any upcoming assembly.
- Past assembly records facilitated by the departing facilitator remain valid and unchanged.

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS shared pool allocation assemblies include participants from all contributing ETHOS. The facilitator ensures balanced representation -- no single ETHOS dominates presentation time or deliberation.
- Proposals from one ETHOS requesting shared pool resources for activities that affect another ETHOS require acknowledgment from the affected ETHOS during the advice phase.
- Allocation records for cross-ETHOS assemblies are registered in every participating ETHOS's agreement registry with synchronized records.
- When multiple ETHOS each run independent allocation assemblies for their own pools, the commons-monitoring skill tracks aggregate allocation patterns across the ecosystem to detect systemic imbalances.
