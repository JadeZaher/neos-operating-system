---
name: authority-boundary-negotiation
description: "Resolve overlapping or ambiguous domain boundaries between roles or circles through structured integrative discussion -- so that authority disputes are resolved structurally, not through informal power or hierarchy."
layer: 2
version: 0.1.0
depends_on: [domain-mapping]
---

# authority-boundary-negotiation

## A. Structural Problem It Solves

Without a negotiation process, domain overlaps are resolved by informal power -- whoever has more influence, seniority, or persistence claims the contested territory. This produces hidden authority, resentment between circles, and precedent-based expansion that the domain contracts never sanctioned. The structural failure is not the overlap itself -- overlaps are inevitable as ecosystems grow and adapt -- but the absence of a process to resolve them structurally rather than politically. This skill provides an integrative process where all affected domains' core purposes are preserved, the structural source of the overlap is identified and addressed, and the resolution is recorded as precedent. Disputes resolved here are disputes resolved once.

## B. Domain Scope

This skill applies to any situation where two or more domain contracts claim authority over the same area, or where a decision or action falls in ambiguous territory between two or more domains. It applies within a single ETHOS and across ETHOS (with additional facilitator requirements). It does not apply to disagreements about how a steward performs within their domain -- that is handled by domain-review. It does not apply to personal conflicts between stewards -- that is Layer VI (Conflict & Repair). The scope is structural: the unit of analysis is the domain contract, not the people holding the roles.

## C. Trigger Conditions

- A steward explicitly raises a boundary dispute: another domain is exercising authority the steward believes falls within their domain
- Ambiguity discovered during an ACT process: a proposal touches two domains and neither steward is certain who holds the consent authority for it
- Overlap flagged during a domain-review: a domain's key responsibilities or deliverables are found to be duplicated in another active domain contract
- Conflict arising from competing domain claims in practice: two stewards have both taken action on the same matter, or neither has because each assumed the other would

## D. Required Inputs

- **Domain contracts of all involved domains** (mandatory): complete, active domain contracts from domain-mapping skill outputs
- **Specific overlap description** (mandatory): the exact responsibilities, deliverables, or customers being claimed by multiple domains -- stated in terms of the 11 domain contract elements, not as general complaints
- **Precedent from prior boundary resolutions** (optional): any boundary resolution records from the resolution registry that addressed similar overlaps
- **Context that surfaced the dispute** (mandatory): the specific event, decision, or observation that revealed the overlap -- provides scope so the negotiation stays focused

## E. Step-by-Step Process

1. **Identify the specific overlap.** Using the 11-element domain contract structure, identify exactly which elements are in conflict: which key responsibilities, deliverables, or customers are claimed by both domains? Which constraints are absent or vague enough to permit dual claims? The overlap must be stated precisely before the negotiation opens -- a vague "we do the same things" framing is not sufficient.

2. **Convene affected domain stewards and their delegating bodies.** All stewards whose domain contracts are in the overlap are required to participate. Their respective delegating bodies are invited observers with consent authority in Step 6. A neutral facilitator (not a steward of any involved domain, and not a member of any involved domain's delegating body) is appointed. Cross-ETHOS disputes require a facilitator from neither ETHOS.

3. **Map each domain's claim against the 11 elements.** The facilitator guides each steward through their domain contract, identifying precisely which elements generate the overlap. This step is analytical, not argumentative -- it produces a shared map of where the contracts conflict. The map is documented in writing before discussion begins.

4. **Identify the structural source of the overlap.** Four structural sources are possible:
   - *Shared responsibility*: both domains were explicitly given the same responsibility by their respective delegating bodies
   - *Unclear constraint*: one or both domain contracts have a constraint element that is insufficiently specific to prevent overlap
   - *Missing dependency*: the domains should depend on each other (one's output is the other's input) but neither lists the dependency
   - *Scope creep*: one domain expanded beyond its original definition through precedent rather than formal amendment
   Identifying the source determines the resolution direction.

5. **Integrative discussion.** The facilitator runs a structured discussion where both stewards explore options that preserve both domains' core purposes. The goal is a resolution neither domain loses, not a zero-sum transfer. Options to explore:
   - *Clarify constraints*: add specificity to one or both domain contracts' constraint elements to eliminate ambiguity
   - *Establish a dependency relationship*: one domain produces, the other reviews or audits -- the handoff point is defined explicitly
   - *Create a shared responsibility protocol*: both domains retain the responsibility but agree on a coordination mechanism (e.g., joint consent required for decisions in the contested area)
   - *Split the contested area*: create a sub-domain for the contested area and assign a steward from either party (requires domain-mapping)
   Discussion continues until all parties have proposed and responded to at least one option.

6. **Consent from all affected parties.** The proposed resolution is consented to by all domain stewards and their delegating bodies. Consent mode: standard consent (no reasoned objection) for disputes between peer domains. If the delegating bodies of the involved domains themselves conflict -- one delegating body wants one resolution, the other wants another -- escalation follows GAIA Level 4 (Coaching) before the consent round proceeds.

7. **Amend affected domain contracts.** The resolution is implemented by formally amending the domain contracts of all involved domains to reflect the agreed boundary. Amendments follow the domain-mapping amendment process. The amended contracts are registered with incremented version numbers.

8. **Register the boundary resolution as precedent.** The boundary resolution record (using `assets/boundary-resolution-template.yaml`) is registered in the resolution registry. Precedent tags are applied so future disputes in similar domains can reference this record. The resolution is shared with all adjacent domains listed in any of the involved domain contracts.

## F. Output Artifact

A boundary resolution record following `assets/boundary-resolution-template.yaml`, containing: unique resolution ID, date, facilitator identity, involved domains (IDs, stewards, delegating bodies), overlap description using 11-element language, structural source classification, discussion summary, resolution options considered, selected resolution, amended domain contract references, consent record ID, review trigger, and precedent tags. The record is registered in the boundary resolution registry and is readable by all active ecosystem participants. Amended domain contracts reference the resolution record in their amendment history.

## G. Authority Boundary Check

No domain can unilaterally claim contested territory outside this process. A steward who proceeds to act on disputed authority before a negotiation is concluded does so without governance standing -- the action is recorded but is subject to retroactive review. The negotiation requires consent from all affected domain stewards and their delegating bodies -- a majority of participants cannot impose a resolution on dissenting parties. If the delegating bodies of the involved domains conflict, the dispute escalates to GAIA Level 4 (Coaching) before consent is attempted. A neutral facilitator is required -- the facilitator cannot be a steward of any involved domain, a member of any involved delegating body, or a person with a personal interest in the outcome. The facilitator has process authority only and cannot impose a resolution.

## H. Capture Resistance Check

**Power asymmetry.** A larger, more established domain pressures a smaller or newer domain to cede territory. The integrative process structurally equalizes this: both domains' core purposes are treated as equally valid starting points, and the facilitator ensures both parties have equal speaking time in Step 5. The consent requirement in Step 6 means the smaller domain's steward cannot be overruled. If the smaller domain's steward is socially pressured to withdraw a legitimate objection, the facilitator flags this as a process integrity issue and pauses the session.

**Political alliances.** Multiple domains coordinate outside the negotiation to present a unified front that squeezes out a third domain. The 11-element mapping in Steps 3 and 4 grounds the discussion in structural evidence rather than coalitions. Each domain's claim is evaluated against its domain contract, not against its political relationships. The facilitator requires textual grounding -- "our domain contract says" not "we believe we should."

**Precedent manipulation.** A party cites prior boundary resolutions selectively to advantage their position. The boundary resolution registry contains the full record, not summaries. The facilitator retrieves the complete resolution record and ensures it is read in context, not excerpted. Precedents bind structurally similar situations, not analogically similar ones; the facilitator adjudicates scope of precedent.

**Stalling as strategy.** A domain with more informal power stalls the negotiation to exhaust the other party. The 3-session limit in Section I prevents indefinite delay. The escalation to GAIA Level 4 removes the dispute from bilateral negotiation and introduces a neutral third-party coach.

## I. Failure Containment Logic

**Stalled negotiation.** After 3 sessions without a proposed resolution that both parties are willing to consent to, the dispute automatically escalates to GAIA Level 4 (Coaching). The GAIA Level 4 coach has access to the full negotiation record, including the 11-element maps, the proposed options, and each party's stated concerns. The coach's role is to find a third solution that both parties' objections point toward.

**Contested resolution.** One or more parties do not consent to the proposed resolution at Step 6. The proposal returns to Step 5 for another integrative round. If three consent rounds fail, the dispute escalates to the involved delegating bodies for a joint decision. If the delegating bodies cannot agree, the dispute escalates to GAIA Level 5 (Systemic Review).

**Post-resolution relapse.** The same boundary dispute recurs within 6 months of a registered resolution. This triggers a structural review of whether the domains should be merged (via domain-mapping) rather than maintained as separate domains with a boundary agreement. Relapse within 6 months is treated as evidence that the structural source was not fully resolved.

**Steward exit during negotiation.** If a steward in an active boundary negotiation exits the ecosystem, their domain enters vacant status per role-assignment. The negotiation is paused until a new steward is assigned. The 30-day vacancy window applies. If no steward is assigned within 30 days, the delegating body assumes negotiation authority for that domain.

## J. Expiry / Review Condition

Boundary resolutions are reviewed alongside the next scheduled domain-review of either involved domain. The resolution record includes a review trigger field: either a specific date or the condition "trigger on next domain-review of either domain." If a resolution is older than 12 months and neither involved domain has been through a domain-review, a standalone resolution review is triggered. Resolution reviews confirm the boundary is still functioning as intended or recommend amendment if practice has drifted. Resolutions do not auto-expire -- they remain active precedent until formally superseded by a new resolution or a domain-mapping amendment.

## K. Exit Compatibility Check

When a steward exits the ecosystem during an active boundary negotiation, the negotiation is paused and does not proceed until a new steward is assigned. All agreements made within their domain during the negotiation period remain valid. If the resolution was completed before the exit, the resolution stands and binds the successor steward through the amended domain contract. The successor steward is not required to re-consent to a prior resolution -- the domain contract amendment carries forward authority. If the exiting steward was the neutral facilitator, a new facilitator is appointed and the negotiation resumes from Step 2.

## L. Cross-Unit Interoperability Impact

Cross-ETHOS boundary disputes follow the same 8-step process with two modifications: the neutral facilitator must be from neither ETHOS involved, and the resolution record is registered in both ETHOS' boundary resolution registries with linked entries. Notification of the resolution goes to all adjacent domains across both ETHOS. Cross-ETHOS resolutions carry higher structural weight as precedent because they establish inter-ETHOS boundary norms. When a cross-ETHOS resolution requires amending a domain contract in both ETHOS, both ETHOS' delegating bodies must consent to the respective amendments.

## OmniOne Walkthrough

The OmniOne AE has two active circles with overlapping authority claims. The Economics circle's domain contract lists "manage funding requests" and "coordinate with external partners on economic matters" as key responsibilities. The Stewardship circle's domain contract lists "ensure responsible resource stewardship" and "review resource usage for alignment with ecosystem values" as key responsibilities. The overlap surfaces concretely: Lena, a Builder, submits a funding request of 500 USDT for materials to build a community composting station. Both the Economics circle steward (Keoni) and the Stewardship circle steward (Mia) contact Lena separately to process the request. Lena does not know which circle has authority to approve it.

The dispute is formally raised. Keoni and Mia each file a boundary dispute notice with the AE. The AE appoints Tomás, a TH member with no role in either circle and no membership in either delegating body, as neutral facilitator. The facilitator convenes a negotiation session.

Step 1: The specific overlap is identified. The contested element is "approval authority for resource allocation requests below 10% of the total pool." Both domain contracts list responsibilities that logically encompass this function, but neither explicitly names it as their exclusive authority. Step 3: The facilitator maps each contract's claim. Economics: "manage funding requests" (responsibility element) + "cannot approve above 10% of pool without OSC consent" (constraint element). Stewardship: "ensure responsible resource stewardship" (responsibility element) + no constraint specifying which requests fall within their scope.

Step 4: The structural source is "shared responsibility" -- both delegating bodies (both were the AE, in this case) assigned overlapping responsibilities without defining the handoff point. Neither domain was wrong to claim authority; the domain contracts were insufficiently differentiated.

Step 5: The integrative discussion explores options. Option A: Economics approves, Stewardship reviews post-allocation. Option B: Stewardship approves any request touching ecosystem values, Economics approves all others. Option C: both must consent for all requests above 100 USDT. Keoni and Mia evaluate each option against their domains' core purposes. Option A preserves Economics' approval function and Stewardship's accountability function without creating a dual-consent bottleneck. Both stewards indicate willingness to consent to Option A.

Step 6: The AE (delegating body for both circles) consents to the proposed resolution. The AE runs a consent round: all eight AE members participate, no objections are raised.

Step 7: Both domain contracts are amended. Economics circle amendment: adds "approve funding requests below 10% of pool as the sole approval body" to the key responsibilities element. Stewardship circle amendment: adds "audit resource allocations post-disbursement; flag misalignments through the ACT process" to the key responsibilities element, and adds "Economics circle" to the dependencies element.

Step 8: The boundary resolution is registered as BRES-2026-001 with precedent tags: "resource-allocation-approval," "economics-stewardship-overlap." The resolution is shared with the OSC (who holds authority over the constraint that defines the 10% threshold) and the agreement registry (which holds the funding request records).

Edge case: Three months later, the Stewardship circle's audit of a 300 USDT allocation finds that the funds were used for a purpose not described in the original request. Mia proposes a clawback to the AE. The boundary resolution record is referenced: Stewardship can trigger a clawback proposal through the ACT process but cannot unilaterally reverse an allocation. Mia submits the clawback as an ACT proposal to the AE. The ACT process governs the decision, not Stewardship's unilateral authority.

## Stress-Test Results

### 1. Capital Influx

A major external funder offers OmniOne a large unrestricted grant on the condition that a single "Resource Authority" circle is created with consolidated approval authority over all allocations. The existing Economics and Stewardship circles both object: their domain contracts would be rendered subordinate to the new circle without a formal boundary process. The boundary negotiation skill structures the response: the proposed Resource Authority circle's creation goes through domain-mapping (requiring AE consent), and any authority claims it makes over the Economics and Stewardship domains immediately trigger this skill. The integrative discussion reveals that the funder's structural demand conflicts with NEOS's distributed authority principle -- no single circle should have unilateral approval authority over the full allocation pool. The resolution preserves both existing circles and creates a limited "major grant coordination" responsibility within the Economics circle's domain, funded by the grant. The funder's condition is met structurally without consolidating authority into a single capture point.

### 2. Emergency Crisis

A flash flood at SHUR Bali creates an urgent need: 2,000 USDT must be disbursed within 12 hours for emergency supplies, and both the Economics and Stewardship circles claim authority to authorize the emergency disbursement. Rather than stall on the boundary dispute, the facilitator invokes emergency negotiation: a single 90-minute session with both stewards and the AE present simultaneously. The 11-element mapping takes 20 minutes -- the overlap is immediately identified as "shared responsibility" (same structural source as the standard case). The integrative discussion produces Option A (Economics approves, Stewardship audits) within one round because both stewards recognize the emergency cannot wait for multiple sessions. The consent round is compressed to 24 hours, minimum 50% AE quorum. The emergency resolution is registered with a 30-day flag for full review once the crisis stabilizes. The emergency disbursement proceeds under Economics' authority. Post-crisis review confirms the resolution is structurally sound and converts it from emergency to permanent status.

### 3. Leadership Charisma Capture

A founding member who stewards the Stewardship circle uses their social standing to dominate the integrative discussion in Step 5, repeatedly reframing the Economics circle steward's proposals as "not understanding the ecosystem's values" and presenting their own position as the only values-aligned option. The facilitator identifies this as a process integrity issue and intervenes: the session is paused, the facilitator reminds all parties that positions must be grounded in domain contract language, and the founding member is asked to identify specifically which element of the Economics circle's domain contract creates a values misalignment. The founding member cannot produce a textual grounding. The facilitator reframes the discussion around the 11-element map rather than values language. The integrative discussion continues with structural evidence as the anchor. The founding member's social authority does not override the process -- the facilitator's process authority is sufficient to redirect. The final consent round requires explicit consent from the Economics circle steward, which cannot be compelled by social pressure.

### 4. High Conflict / Polarization

The Governance Infrastructure circle and the Community Experience circle have been in a prolonged boundary dispute over who holds authority to design and run community onboarding processes. Three sessions have not produced a resolution: the Governance Infrastructure steward argues onboarding is a governance function; the Community Experience steward argues it is a community function. Both positions are structurally defensible given their domain contracts. After three sessions without resolution, the dispute escalates to GAIA Level 4 per Section I. A GAIA coach reviews the negotiation record and identifies the underlying tension: both stewards are defending the importance of their domain's identity, not just the function itself. The coach maps a third solution: onboarding is a shared function with a formal handoff -- Governance Infrastructure owns the consent ceremony process (structural governance), Community Experience owns the relational integration process (community belonging). The contested area is split structurally along the axis both parties already value most. Both stewards consent to the domain-mapping amendment that formalize the split. The precedent is registered with tags enabling future onboarding disputes to reference this resolution.

### 5. Large-Scale Replication

OmniOne grows to 200 circles across 12 ETHOS. Boundary disputes are inevitable at this scale -- with 200 domain contracts and thousands of element combinations, some overlap will always exist. The boundary-resolution registry becomes the primary tool for scale management: before a negotiation begins, the facilitator queries the registry for precedent records with matching tags. In 60% of cases, a prior resolution addresses the same structural source in a similar domain type, and the integrative discussion can begin from the prior resolution as a starting proposal rather than from scratch. The 3-role cap and the domain-review cycle prevent the most common structural source (scope creep) from accumulating silently. At scale, cross-ETHOS disputes are the most complex -- but the process scales because the structural analysis (11-element mapping, source identification, integrative options) is the same regardless of the number of people affected.

### 6. External Legal Pressure

A government agency demands that OmniOne designate a single legal compliance officer with unilateral authority to override any governance decision for legal compliance reasons. This demand triggers an immediate boundary dispute: the authority claim is broader than any single domain in OmniOne's structure. The boundary negotiation skill is applied: the government's demand is mapped against all active domain contracts that touch compliance-adjacent functions (Economics, Governance Infrastructure, Stewardship). The 11-element analysis reveals no existing domain has a constraint that permits unilateral override. The integrative resolution is a domain-mapping amendment: a new "Regulatory Coordination" domain is created with a tightly scoped purpose (facilitate legal compliance reporting and communication) and an explicit constraint (no unilateral authority to override governance decisions). The domain contract's delegator responsibilities element specifies that the OSC provides legal compliance information to the Regulatory Coordination steward. The government's requirement is met through a named point of contact without creating the unilateral override authority that would violate NEOS's distributed authority principle.

### 7. Sudden Exit of 30% of Participants

Fifteen participants exit OmniOne, including three stewards with active boundary negotiations in progress. Each of the three active negotiations is paused immediately. For two of them, the exiting steward's domain enters vacant status and the delegating body assumes negotiation authority per Section I. The 30-day vacancy window activates. For the third negotiation, both stewards are still active -- only the facilitator departed. A new facilitator is appointed and the negotiation resumes from Step 2 with the prior session notes intact. The boundary resolution registry is unaffected by the exits: all completed resolutions remain valid precedent. Adjacent domains that received notification of in-progress negotiations are updated that the negotiations are paused. The ecosystem's governance does not collapse because boundary disputes are isolated processes -- each negotiation is self-contained and does not cascade into other skills or domains.
