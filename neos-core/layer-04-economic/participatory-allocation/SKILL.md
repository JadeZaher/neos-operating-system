---
name: participatory-allocation
description: "Run participatory budgeting assemblies where circle members collectively allocate funding pool resources through structured deliberation and consent -- not majority vote, not first-come-first-served, not steward fiat."
layer: 4
version: 0.1.0
depends_on: [resource-request, funding-pool-stewardship, act-consent-phase, consensus-check]
---

# participatory-allocation

## A. Structural Problem It Solves

Without a structured allocation process, funding pools distribute resources through one of three failure modes: steward fiat (one person decides who gets what), lobbying (the loudest or best-connected proposals win), or first-come-first-served (early proposals drain the pool before later proposals are even heard). Each failure mode concentrates resources among insiders and undermines collective ownership of the pool. Participatory allocation solves this by requiring all proposals to be submitted, reviewed, and decided within a structured assembly process. The Porto Alegre participatory budgeting model proves that large groups can make collective allocation decisions when the process is structured, transparent, and iterative. This skill adapts that model for consent-based governance: instead of majority voting on allocation, the assembly uses consent rounds to ensure no proposal advances over a reasoned objection. The result is allocation that reflects collective stewardship rather than individual influence.

## B. Domain Scope

This skill applies whenever a funding pool's resources are allocated collectively rather than through individual resource requests. It covers periodic allocation assemblies (quarterly, semi-annual), special allocation assemblies (triggered by windfall inflows or emergency replenishment), and reallocation assemblies (redistributing previously allocated but unused resources). Pool types that use this skill include circle operational pools, ecosystem strategic pools, cross-AZPO shared pools, and project-specific pools. Emergency reserve pools are excluded -- emergency disbursements follow the compressed resource-request process, not the deliberative allocation assembly. Out of scope: individual resource requests that fall within steward discretionary thresholds (see resource-request), pool creation and governance structure (see funding-pool-stewardship), and monitoring of allocation outcomes (see commons-monitoring).

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
- **Cross-AZPO shared pool assemblies** require participation from all contributing AZPOs. No single AZPO can dominate the allocation through higher participation numbers -- consent requires addressing objections from any participating unit.

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

- Cross-AZPO shared pool allocation assemblies include participants from all contributing AZPOs. The facilitator ensures balanced representation -- no single AZPO dominates presentation time or deliberation.
- Proposals from one AZPO requesting shared pool resources for activities that affect another AZPO require acknowledgment from the affected AZPO during the advice phase.
- Allocation records for cross-AZPO assemblies are registered in every participating AZPO's agreement registry with synchronized records.
- When multiple AZPOs each run independent allocation assemblies for their own pools, the commons-monitoring skill tracks aggregate allocation patterns across the ecosystem to detect systemic imbalances.
- Cross-ecosystem allocation assemblies (between separate NEOS ecosystems) use the inter-unit coordination protocol (Layer V, deferred).

## OmniOne Walkthrough

The AE circle at OmniOne runs its quarterly participatory allocation assembly for the AE Operational Pool. The pool balance is 3,200 Current-Sees (AE type) plus $4,800 in accepted currency routed through H.A.R.T. Yuki, the pool steward, announces that 2,500 Current-Sees and $3,500 are available for allocation after reserving funds for standing commitments and the emergency buffer.

The proposal window opens and five proposals arrive within 14 days:
- **Proposal A** (Keoni): $1,200 for governance facilitation training, 400 Current-Sees for participant time compensation
- **Proposal B** (Farid): $800 for open-source collaboration tools annual subscription
- **Proposal C** (Maren): 600 Current-Sees for a cross-circle knowledge exchange program with the Education circle
- **Proposal D** (Dayo): $1,500 for a community gathering space rental for three months
- **Proposal E** (Priya): $700 for a pilot project testing peer-to-peer resource sharing within AE

Total requested: $4,200 and 1,000 Current-Sees. Available: $3,500 and 2,500 Current-Sees. Financial proposals are oversubscribed by $700; Current-See proposals are under-subscribed.

The facilitator, Soren (assigned through role-assignment, not an AE circle member to avoid conflicts), opens deliberation round 1. Each proposer presents for 10 minutes. During deliberation, several points surface: Farid's tool subscription overlaps with a Technology circle initiative that might fund the same tools. Dayo's space rental is the largest single request and participants want clarity on whether the space serves only AE or the broader ecosystem.

Proposal refinement: Farid reduces his request to $500 after confirming the Technology circle will cover the remaining $300 through a cross-circle arrangement. Dayo clarifies the space will be available to all OmniOne circles two days per week, and he adds a co-stewardship arrangement with the Community circle. Total financial requests drop to $3,900 -- still $400 oversubscribed.

Deliberation round 2 examines the revised proposals. Soren names the $400 gap explicitly. The assembly discusses prioritization.

The consent round proceeds in randomized order. Proposals B (Farid, $500), C (Maren, 600 CS), and E (Priya, $700) achieve consent without objection. Proposal A (Keoni, $1,200) receives one objection from Lina: "The training cost is high relative to pool size and similar training was funded last quarter. I request the amount be reduced or cost-shared with the Education circle." Keoni and Lina enter integration: Keoni agrees to request $600 from AE and $600 from the Education circle through a separate resource request, reducing the AE ask to $600. Round 2: consent achieved.

Proposal D (Dayo, $1,500) receives two objections. Maren objects that a three-month commitment consumes 43% of the available financial allocation for a single initiative. Priya objects that the space primarily benefits members near the Bali location, not distributed AE members. Two integration rounds do not resolve the tension. Soren invokes the third-solution round. The assembly generates an alternative: fund one month ($500) as a pilot, with continuation contingent on a utilization report showing cross-circle and distributed-member benefit. Dayo consents to the pilot framing. Fresh consent round on the third solution: all eligible members consent.

Final allocations: Keoni $600, Farid $500, Maren 600 CS, Dayo $500, Priya $700. Total: $2,300 and 600 Current-Sees -- within budget. The remaining $1,200 and 1,900 Current-Sees stay in the pool for individual resource requests. Soren publishes the allocation record. Every OmniOne participant can read it.

## Stress-Test Results

### 1. Capital Influx

A corporate partner donates $50,000 to the OmniOne ecosystem strategic pool just before a scheduled allocation assembly, and submits a proposal requesting $20,000 for a corporate social responsibility project branded with their logo. The donation makes the pool five times larger overnight. The facilitator flags the timing and scale during deliberation round 1: the proposal effectively requests back 40% of the donor's own contribution. Conflict of interest disclosure requires the corporate partner's representative to declare the donation-request relationship. The assembly evaluates the CSR project on its alignment with OmniOne's ecosystem purpose, not on gratitude for the donation. Several participants object that branding contradicts OmniOne's commons-oriented identity. The integration round produces a modified proposal: $8,000 for the project without corporate branding, framed as a commons initiative. The donor's $50,000 contribution creates no priority, no expedited process, and no additional weight in the consent round. The remaining $42,000 is governed by normal allocation processes.

### 2. Emergency Crisis

A natural disaster disrupts three SHUR locations simultaneously, and the ecosystem strategic pool receives pressure to skip the scheduled allocation assembly and disburse funds directly to affected communities. The participatory-allocation skill holds firm: emergency disbursements follow the resource-request emergency process, not the allocation assembly. The assembly is not cancelled or hijacked. Emergency resource requests are processed through compressed ACT timelines within 24-48 hours. The scheduled allocation assembly proceeds on its normal timeline to address non-emergency priorities. If the emergency has depleted the pool significantly, the assembly adjusts its allocation amount to reflect the reduced balance. The facilitator ensures that emergency sympathy does not override deliberative process for the remaining allocation decisions -- each non-emergency proposal is evaluated on its own merits, not compared to the crisis response.

### 3. Leadership Charisma Capture

Rani, a founding member of OmniOne, presents a proposal at the allocation assembly with characteristic passion and vision. Her 10-minute presentation is compelling; the other proposers' presentations are more modest. During deliberation, several participants express enthusiasm for Rani's proposal without examining its specifics. The facilitator intervenes structurally: written feedback forms are collected before open discussion, ensuring every participant evaluates each proposal independently before social dynamics take hold. The facilitator reminds the assembly that presentation quality is not an evaluation criterion -- alignment with pool purpose, feasibility, and stewardship commitment are. During the consent round, two participants who initially expressed enthusiasm register objections after reading Rani's written proposal more carefully: the deliverables are vague and the timeline is ambitious without contingency. Rani's social capital does not exempt her proposal from the same scrutiny applied to every other submission. The integration rounds require Rani to specify measurable deliverables and add a mid-point review.

### 4. High Conflict / Polarization

The Technology circle's allocation assembly becomes a proxy war between open-source advocates and pragmatists who prefer commercial tools. Three proposals request open-source development funding; two proposals request commercial software licenses. During deliberation, the factions talk past each other, each framing their position as fundamental to OmniOne's values. The facilitator recognizes escalating polarization and invokes GAIA Level 3 structured dialogue: each faction states the other faction's position in terms the other faction accepts before advancing their own argument. This reframing reveals shared ground: both factions want effective tools that serve the circle's purpose. At GAIA Level 4, a coach facilitates a third-solution exploration for the most contested proposal. The resulting allocation splits the disputed amount: fund an open-source tool evaluation alongside a time-limited commercial license, with a structured comparison after 90 days. The coach ensures neither faction's framing dominates the comparison criteria. The assembly achieves consent on all five proposals after modification.

### 5. Large-Scale Replication

OmniOne scales to 5,000 participants across 80 circles, each running its own quarterly allocation assembly. The participatory-allocation skill scales through domain scoping: the Agriculture circle at SHUR Bali runs its own assembly independently of the Agriculture circle at SHUR Portugal. Each assembly involves only the members of its governing circle, typically 8-20 people -- not 5,000. Ecosystem strategic pool assemblies require broader participation but use representative participation: each circle sends one delegate to the ecosystem-level assembly. The allocation-record-template ensures structural consistency across 80+ assemblies per quarter. The commons-monitoring skill aggregates allocation patterns across all assemblies to detect ecosystem-wide trends: are certain types of proposals consistently funded while others are neglected? Facilitator capacity scales through trained facilitators in each circle -- the skill's procedural clarity means facilitators do not need to improvise.

### 6. External Legal Pressure

Indonesian regulations require that collective allocation decisions for amounts exceeding a threshold be documented with individual participant identification for tax reporting purposes. The allocation record already captures participant identity and positions as part of its standard structure -- the skill's transparency requirement aligns naturally with the legal mandate. The pool steward at SHUR Bali adds a compliance addendum to the allocation record template: participant tax identification numbers (where legally required) are stored in a separate compliance document linked to the allocation record. The compliance document is accessible only to the steward and relevant authorities -- it does not become part of the ecosystem-wide public record. The allocation process itself does not change. The legal requirement is absorbed at the local level per the UAF sovereignty principle: Indonesian compliance rules do not propagate to allocation assemblies in Portugal or Costa Rica.

### 7. Sudden Exit of 30% of Participants

After a divisive ecosystem decision, 1,500 members exit OmniOne. Several allocation assemblies are in progress. In-progress assemblies recalculate quorum based on current membership: a circle that had 15 members now has 10, and quorum adjusts to 2/3 of 10. Proposals from departed members are withdrawn; if the departed member's proposal had already received consent, the allocation is cancelled and resources revert to the pool. Assemblies that lose their assigned facilitator are paused until a replacement is appointed through role-assignment. The reduced membership may mean fewer proposals in subsequent assemblies, but the process remains structurally identical. Pool balances may shrink as departing members' contributions to inflows cease. The steward adjusts the allocation amount for the next assembly to reflect the reduced pool. Standing allocations from previous assemblies that were assigned to departed members are reviewed: completed work is honored, incomplete allocations revert. The assembly process resumes as soon as quorum is achievable, demonstrating that the process depends on structure, not on specific individuals.
