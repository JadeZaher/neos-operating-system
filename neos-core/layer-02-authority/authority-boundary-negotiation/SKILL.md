---
name: authority-boundary-negotiation
description: "Resolve overlapping or ambiguous domain boundaries between roles or circles through structured integrative discussion -- so that authority disputes are resolved structurally, not through informal power or hierarchy."
layer: 2
version: 0.1.0
depends_on: [domain-mapping]
---

# authority-boundary-negotiation

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
