# Layer II: Authority & Role

The Authority & Role Layer defines how governance authority is scoped, assigned, negotiated, transferred, reviewed, and dissolved within the ecosystem. It answers one foundational question at every stage of an ecosystem's life: who has the right to act, within what boundary, and on whose behalf?

Without this layer, authority is ambient — assumed by whoever is most confident, most senior, or most persistent. The Agreement Layer (Layer I) can create binding commitments, and the ACT Engine (Layer III) can run consent processes, but neither can answer "who is authorized to initiate this action?" That question is the exclusive territory of Layer II.

## Skills

| Skill | Description | Dependencies |
|-------|-------------|-------------|
| **domain-mapping** | Define or refine a governance domain using the 11-element contract so that authority scope is explicit, bounded, and reviewable | None |
| **member-lifecycle** | Track ecosystem participant status transitions — onboarding, active, inactive, reactivation, exit — so governance always knows who is participating and what their status means | universal-agreement-field |
| **role-assignment** | Assign a person to a defined domain with scoped authority, verifying competency, checking conflicts of interest, and separating role from person | domain-mapping, member-lifecycle |
| **authority-boundary-negotiation** | Resolve overlapping or ambiguous domain boundaries through structured integrative discussion so that authority disputes are settled structurally, not through informal power | domain-mapping |
| **role-transfer** | Hand off a governance role from one steward to another without losing institutional knowledge or continuity, through structured handover with overlap period and formal reassignment | domain-mapping, role-assignment |
| **domain-review** | Evaluate an existing domain through scheduled review — assessing each of the 11 contract elements, steward effectiveness, and domain health to determine whether to reaffirm, refine, reassign, merge, or sunset | domain-mapping, role-assignment |
| **role-sunset** | Dissolve a governance domain that has served its purpose — inventorying all responsibilities and agreements, executing a disposition plan, and archiving the domain contract with a 90-day reactivation window | domain-mapping, domain-review, role-transfer |

## Skill Relationships

```
domain-mapping (anchor)
     |
     +---> role-assignment <--- member-lifecycle
     |         |
     |    role-transfer
     |
     +---> authority-boundary-negotiation
     |
     +---> domain-review
               |
          role-sunset
```

**domain-mapping** is the anchor. Every other skill in this layer either reads from or writes back to a domain contract. A domain must be formally defined before it can be assigned, disputed, transferred, reviewed, or dissolved.

**member-lifecycle** and **domain-mapping** are parallel foundations: member-lifecycle establishes who is a participant; domain-mapping establishes what authority exists. Both are prerequisites for role-assignment.

**role-assignment** is where the two foundations converge: it binds a verified participant (active lifecycle status) to a defined domain (complete contract). It also feeds role-transfer — every transfer begins with an active assignment record.

**authority-boundary-negotiation** operates horizontally across peer domains. It can be triggered at any point in the lifecycle: during domain-mapping (overlap flagged before consent), during role-assignment (conflict-of-interest check), or at any time a disputed action surfaces.

**domain-review** is the layer's maintenance loop. It consumes domain contracts and generates outcomes that feed back into other skills: Refine returns to domain-mapping, Reassign triggers role-transfer, Merge routes through authority-boundary-negotiation then domain-mapping, Sunset triggers role-sunset.

**role-sunset** is the terminal skill — it closes domains cleanly so they do not linger as zombie authority.

## Interaction with Other Layers

### Layer I: Agreement Layer

Agreements and authority are structurally interdependent but governed separately.

- **Agreements define who participates in governance.** The UAF (universal-agreement-field) is the root agreement all participants consent to upon onboarding — this is the entry point for member-lifecycle. Without a valid onboarding consent record, a participant's votes and objections carry no structural weight.
- **Authority defines who can create and modify agreements.** Every agreement creation or amendment act in Layer I references an authorized body. That authorization traces to a domain contract in Layer II. "Authorized" without a domain contract is an ungrounded claim.
- **Domain contracts are themselves a type of agreement.** They pass through ACT consent processes, are registered (as artifacts, not as Layer I agreements), and are subject to the same anti-capture logic. The distinction: Layer I agreements bind *what participants commit to*; Layer II domain contracts bound *who can act and within what scope*.

### Layer III: ACT Decision Engine

The ACT Engine is the mechanism through which Layer II authority becomes operational.

- **Domain creation is an ACT process.** A new domain contract passes through proposal-creation, act-advice-phase, and act-consent-phase before registration. There is no out-of-band path to create a domain.
- **Role assignment uses ACT consent.** The assigning body runs a consent round on each steward assignment. OSC-level roles use consensus mode.
- **Domain review outcomes that change the domain contract are ACT processes.** A Refine outcome from domain-review triggers a proposal-creation and amendment cycle in Layer I, governed by Layer III's consent mechanics.
- **Authority-boundary-negotiation produces ACT proposals.** When the negotiation resolves a boundary dispute, the resulting domain contract amendments flow through the ACT process for each affected domain.
- **GAIA escalation is the shared resolution path.** When authority disputes, contested reviews, or failed assignments exhaust in-process integration, they escalate through the same six GAIA levels defined in proposal-resolution (Layer III). Neither layer defines its own separate escalation model.

## Key Design Decisions

**S3 11-element domain contract.** The sociocracy 3.0 domain model is adapted as the canonical authority schema throughout this layer. All 11 elements (purpose, key responsibilities, customers, deliverables, dependencies, constraints, challenges, resources, delegator responsibilities, competencies, metrics + evaluation schedule) must be present before any domain carries active status. Partial domains are provisional and cannot receive steward assignments. The completeness requirement prevents informal authority accumulation.

**Blanket authority within defined scope.** A steward does not need permission for each decision within their domain — that would recreate bureaucracy under another name. The constraints element defines what the steward *cannot* do, and within those bounds, stewards act with full authority. The structure inverts the default assumption: authority is present until explicitly constrained, not absent until explicitly granted.

**Separation of role and person.** The domain exists independently of whoever currently holds it. A steward holds authority on behalf of the ecosystem, not as personal property. This means domains survive exits (entering vacant status), transfers do not require re-creating the domain, and domain reviews assess the *domain contract* and steward fit independently. Authority cannot be accumulated by holding roles long enough to become personally identified with them.

**Evaluation cadence as a structural requirement.** Every domain contract must include an evaluation schedule (default: 6 months; minimum: 3 months; maximum: 12 months). Domains without a review date cannot hold active status. This makes entrenchment structurally impossible: every domain is on a clock, and the clock restarts only if the review body explicitly consents to reaffirm.

**Profiles vs. roles.** Profiles (Co-creator, Builder, Collaborator, TownHall) are participation tiers that govern platform access levels — editing, commenting, reading. Roles are governance authority scopes defined by domain contracts. A Builder-profile participant who holds a steward role exercises full governance authority within that domain, regardless of their platform access level. The two systems are structurally independent. Profile changes do not grant or remove domain authority; role assignments do not change profile tiers.

## Design Patterns Used

- **Anchored delegation.** Every domain traces upward to a delegating body. Authority is granted downward through explicit consent, not assumed laterally from peers or inferred from organizational position.
- **Structural dispute resolution before action.** Authority-boundary-negotiation must resolve before a contested domain can proceed to consent. Acting on disputed authority produces a governance record that is subject to retroactive review — there is no advantage to racing to claim territory.
- **Forced inventory at closure.** Role-sunset requires complete disposition of every responsibility and agreement before the process can advance past step 1. Dissolution cannot be rushed; every item must have an explicit fate.
- **Overlap period as knowledge transfer mechanism.** Role-transfer mandates a minimum 2-week overlap where both outgoing and incoming stewards attend sessions together. Institutional knowledge is a governance artifact — losing it through abrupt transition is treated as a structural failure.
- **Self-perpetuating review loops.** Each domain-review sets the next review date as part of its output. Reviews are never one-time events; they are self-renewing gates.

## Anti-Patterns Guarded Against

- **Permission-seeking default.** The temptation to ask the delegating body for approval on every decision within scope is the opposite of what this layer intends. Stewards are expected to act within their domain — that is what the domain contract authorizes. Persistent permission-seeking is a signal that the constraints element is either too vague or that the steward does not have confidence in their authorization.
- **Undifferentiated domains.** Creating a domain with a broad purpose and no specific constraints leaves authority effectively unchecked. The 11-element schema's constraints element is mandatory. The adjacent domain review step in domain-mapping requires that vague constraints be made specific before consent proceeds. "Act in the ecosystem's best interest" is not a constraint.
- **Permanent role tenure.** No domain can exist without a review date. No assignment can exist without a review date. The evaluation cadence requirement makes tenure-by-inertia structurally impossible — stewards must be reaffirmed, not merely un-challenged.
- **Authority creep by precedent.** A steward who acts beyond their constraints and, when unchallenged, cites this as established practice has not amended their domain contract. Precedent does not modify constraints. Domain-review's element-by-element evaluation catches constraint drift by comparing actual behavior against the contract. The resolution is a domain-mapping amendment through the ACT process, not retroactive legitimation of overreach.
