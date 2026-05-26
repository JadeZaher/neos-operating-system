---
name: domain-mapping
description: "Define or refine a governance domain using the 11-element contract -- purpose, responsibilities, customers, deliverables, dependencies, constraints, challenges, resources, delegator responsibilities, competencies, metrics, evaluation schedule -- so that authority scope is explicit, bounded, and reviewable."
layer: 2
version: 0.1.0
depends_on: []
---

# domain-mapping

## C. Trigger Conditions

- A new circle or role is formed through an ACT consent process and requires a formal domain contract before operating
- An existing role or circle has been functioning without a documented domain and needs structural legitimacy
- A domain-review evaluation recommends refinement of an existing domain contract
- An authority-boundary-negotiation requires formal amendment of one or both domain contracts involved
- The founding body of a new ecosystem defines the initial domain structure (consensus process, one-time event)

## D. Required Inputs

- **Delegating body identity:** the circle or council that holds authority to create this domain (mandatory)
- **Proposed domain purpose:** a plain-language statement of why this domain exists and what it is responsible for (mandatory)
- **Ecosystem context:** parent domain, adjacent domains, known dependencies (mandatory — at minimum, "no known dependencies" must be stated explicitly)
- **Draft constraint list:** initial list of what this domain cannot do, even within its scope (mandatory — vague or absent constraints flag provisional status)
- **Proposed steward candidate:** the person or group being assigned (optional at creation — domains may be created before a steward is assigned)

## E. Step-by-Step Process

1. **Identify need.** The delegating body confirms that no existing domain contract covers the proposed scope. Query the domain registry for related domains before drafting.
2. **Draft all 11 elements.** Fill in each element of the domain contract (see Section F and the asset template). For each element, consult existing domain contracts to identify dependencies and potential overlaps. Vague constraints must be made specific — "act in the ecosystem's interest" is not a constraint.
3. **Adjacent domain review.** Present the draft to all stewards of adjacent domains for structural feedback. This is not a consent round — it is a dependencies and overlap check. Any overlap identified is documented and routed to authority-boundary-negotiation before the consent round proceeds.
4. **Delegating body consent round.** The delegating body runs an ACT consent process on the complete domain contract. The question posed: "Does this domain contract clearly bound authority in a way no one has a reasoned objection to?" Adjacent domain stewards' feedback is included in the advice record.
5. **Registration.** The completed, consented domain contract is entered in the domain registry with a unique domain ID, version 1.0.0, status "active," and a linked evaluation schedule.
6. **Notification.** All adjacent and dependent domains are notified. Cross-ETHOS dependencies trigger notification to those ETHOS' registries as well.

## F. Output Artifact

A versioned domain contract document following `assets/domain-contract-template.yaml`. The contract contains: domain ID, version (starting at 1.0.0), status, creation date, delegating body, all 11 elements filled, current steward (null if vacant), assignment history, and amendment history. The domain contract is the single source of truth for what this domain can and cannot do. Every downstream skill that references authority — role-assignment, domain-review, role-sunset — reads from this document.

**The 11 elements:**
1. **Purpose** — why this domain exists; the governance function it performs
2. **Key responsibilities** — what the domain must do; the actions it is accountable for
3. **Customers** — who the domain serves; participants or bodies that depend on its outputs
4. **Deliverables** — the concrete outputs others can expect from this domain
5. **Dependencies** — other domains or resources this domain requires to function
6. **Constraints** — what this domain explicitly cannot do, even within its scope
7. **Challenges** — known risks, tensions, or structural difficulties
8. **Resources** — what the domain can draw on: budget, time, information, tools
9. **Delegator responsibilities** — what the delegating body owes this domain: information access, non-interference, evaluation support
10. **Competencies** — what the steward must understand or be able to do
11. **Metrics + evaluation schedule** — how effectiveness is measured and when the domain is formally reviewed

## G. Authority Boundary Check

Only a delegating body can create a domain through an ACT consent process. No individual can self-declare a domain — a domain created outside this process has no standing in the governance system. A domain holder cannot expand their own domain; scope expansion requires the delegating body to consent to amended domain contract elements. Minor updates (metric adjustments, resource changes) use circle-level consent. Structural changes (purpose, key responsibilities, constraints) use the full ACT process.

**Meta-authority:** The founding body of a new ecosystem (analogous to OmniOne's OSC) defines the initial domain structure through consensus before this skill is operative. Once the initial structure exists, all subsequent domain creation follows this skill. This makes the skill self-referentially consistent: the authority to define authority is explicitly stated rather than assumed.

## H. Capture Resistance Check

**Authority creep by precedent.** A domain holder acts beyond their defined constraints repeatedly and, when unchallenged, cites this as established practice. The constraints element explicitly bounds authority — precedent does not amend constraints. The domain-review cycle catches drift by comparing actual behavior against the contract.

**Charismatic capture through vague constraints.** A trusted leader defines their domain with deliberately broad language ("do whatever is needed for ecosystem health") to maximize discretion. Adjacent domain stewards flag overlap risk during the review step. The ACT advice phase requires constraint specificity. Any domain with constraints that do not exclude specific actions is flagged for revision before consent proceeds.

**Domain hoarding.** One body creates many domains to consolidate influence. The domain registry tracks domains-per-delegating-body. Domain-review evaluations include a load assessment — a delegating body stewarding more domains than it can meaningfully evaluate is flagged for restructuring.

## I. Failure Containment Logic

**Incomplete domain contract.** Any missing element at consent time flags the domain as "provisional." A provisional domain may operate for 30 days but must complete all elements or revert to its delegating body for holding. Provisional status is visible in the registry.

**Contested domain.** Two bodies simultaneously claim authority to create a domain over the same scope. Neither contract proceeds to consent. The conflict routes to authority-boundary-negotiation, which produces a resolution before either domain can be finalized.

**Abandoned domain.** A steward stops fulfilling responsibilities without triggering a formal exit. The domain-review process catches this at the evaluation date. If responsibilities are visibly unmet before that date, the delegating body can call an emergency review and route to role-transfer or role-sunset.

**Adjacent domain review stalls.** If an adjacent domain steward fails to engage within 14 days, the delegating body may proceed to consent with the stall documented. The non-responsive steward's domain is flagged for a boundary review at its next evaluation.

## J. Expiry / Review Condition

Every domain contract must include an evaluation schedule (element 11). The default cadence is 6 months. Domains without an evaluation schedule are flagged as incomplete in the registry and cannot hold "active" status. If the evaluation date passes without a review being convened, the domain enters a 30-day grace period with an escalation notice to the delegating body. After 30 days, domain status changes to "under_review" with a registry flag. Domain contracts do not auto-expire — expiry without review is a governance failure, not a design feature.

## K. Exit Compatibility Check

When a domain steward exits the ecosystem, the domain enters "vacant" status immediately — it does not dissolve. The delegating body holds 30 days to assign a new steward via role-assignment or trigger role-sunset. During the vacant window, the delegating body holds temporary stewardship for urgent matters only, with all such actions documented in the amendment history. The exiting steward must produce a handover inventory: pending commitments, active agreements held by the domain, and relationship context for adjacent domains. If the steward exits without producing this inventory, the delegating body initiates a 14-day reconstruction period before operating in the domain.

## L. Cross-Unit Interoperability Impact

Domains within one ETHOS may have dependencies on domains in another ETHOS. Cross-unit dependencies must be listed explicitly in the dependencies element — "no cross-ETHOS dependencies" must be stated rather than omitted. When a domain is created or refined in one ETHOS, all cross-ETHOS dependent domains are notified before the consent round concludes. Cross-ETHOS domain conflicts follow the authority-boundary-negotiation process with facilitators drawn from neither ETHOS. Resolution records are registered in both ETHOS' registries. Cross-ecosystem domain dependencies follow the same structure with an additional inter-ecosystem notification step when Layer V federation is available.
