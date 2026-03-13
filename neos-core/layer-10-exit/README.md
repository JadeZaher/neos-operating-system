# Layer X: Exit & Portability

## Overview

Exit is governance's integrity test. A system that members cannot leave is not governance -- it is confinement. Layer X ensures that every individual and every collective unit can depart cleanly, carry their governance history, and return without penalty. This is not a concession to member convenience; it is a structural requirement for legitimate governance. As Albert Hirschman documented in *Exit, Voice, and Loyalty*, when exit is blocked, voice atrophies. Members who stay because they can leave bring genuine consent. Members who stay because they cannot leave bring resentment.

NEOS treats exit as a right, not a privilege. No approval is required. No justification is demanded. No punitive consequence follows. The only requirement is operational: commitments accumulated during membership are resolved through a structured handoff process, ensuring that departure is clean for the member and sustainable for the ecosystem.

## The Hirschman Framework: Exit, Voice, Loyalty

Layer X operationalizes Hirschman's insight that exit and voice are complementary, not opposing, forces:

- **Exit** (this layer): The right to leave, fully supported by structured departure, commitment unwinding, portable records, and re-entry pathways. Exit is the ultimate check on governance quality -- if the system degrades, members can leave.
- **Voice** (Layer III, ACT Engine): The right to participate in governance decisions, raise objections, and shape agreements. Voice is strengthened when exit is available, because staying becomes a meaningful choice rather than a default.
- **Loyalty** (Layer I, Agreement): Consent-based commitment to shared agreements. Loyalty in NEOS is structural (agreement-based), not emotional (relationship-based). It endures because members chose it, not because they are trapped.

When exit is clean and painless, voice becomes more powerful -- members who raise objections do so from genuine conviction, not from desperation. When voice is effective, exit becomes less necessary -- members do not need to leave to be heard. Layer X completes this cycle by ensuring exit is always available as the structural backstop.

## Graceful Degradation Principle

Layer X is built on the principle of graceful degradation: the ecosystem must be designed so that any departure -- individual or collective -- degrades operations gradually, never catastrophically. This means:

- No single member's departure can collapse governance (sole critical roles trigger emergency coverage, not exit prevention)
- No AZPO's dissolution can orphan ecosystem-level commitments (structured asset disposition and agreement amendment)
- No mass departure can invalidate prior governance decisions (decisions stand on their own legitimacy)
- No departure can trap a member's governance experience (portable records ensure knowledge travels with the person)

If a departure causes catastrophic failure, the structural fragility is the ecosystem's problem to solve -- never a reason to restrict exit.

## Exit Lifecycle

```
INDIVIDUAL EXIT                         COLLECTIVE EXIT
    |                                       |
    v                                       v
voluntary-exit                         azpo-dissolution
  (declaration,                          (trigger, consent,
   coordinator,                           impact assessment)
   timeline)                                |
    |                                       |
    v                                       v
commitment-unwinding  <---- shared ---->  commitment-unwinding
  (roles, agreements,                     (AZPO-level settlement,
   economic, proposals,                    member transitions)
   conflicts)                               |
    |                                       |
    v                                       v
portable-record                        portable-record
  (structured export,                    (for each transitioning
   privacy controls,                      member)
   verification hash)                       |
    |                                       |
    v                                       v
DEPARTED                               DISSOLVED
  (clean record,                         (archived history,
   re-entry eligible)                     members transitioned)
    |
    v (optional)
re-entry-integration
  (record verification,
   current-agreement consent,
   orientation, integration)
    |
    v
RETURNED
  (full member,
   historical context,
   current agreements)
```

## Skill Index

| # | Skill | Priority | Purpose | Dependencies |
|---|-------|----------|---------|-------------|
| 1 | [voluntary-exit](voluntary-exit/SKILL.md) | P0 | Complete individual departure with commitment handoff, data export, and clean governance record | agreement-registry, role-assignment, commitment-unwinding |
| 2 | [commitment-unwinding](commitment-unwinding/SKILL.md) | P0 | Systematic resolution of every outstanding commitment held by a departing member | voluntary-exit, agreement-creation, role-assignment |
| 3 | [portable-record](portable-record/SKILL.md) | P0 | Structured, machine-readable governance participation history owned by the member | decision-record, semantic-tagging, voluntary-exit |
| 4 | [azpo-dissolution](azpo-dissolution/SKILL.md) | P1 | Orderly dissolution of an entire AZPO with asset settlement, member transition, and record archival | voluntary-exit, commitment-unwinding, agreement-amendment |
| 5 | [re-entry-integration](re-entry-integration/SKILL.md) | P1 | Structured return with historical context, current-agreement consent, and equitable integration | voluntary-exit, portable-record, member-lifecycle |

## Design Principles

**Exit is a right, not a request.** No approval, no justification, no waiting period beyond the operational handoff. The 30-day default (7-day urgent) handoff exists to protect the ecosystem's operational continuity, not to create a retention window.

**No hostage commitments.** No commitment can extend the departure timeline beyond 30 days. Unresolved obligations transfer to the ecosystem, not to the departing member. The ecosystem bears the cost of its own complexity.

**Data belongs to members.** Portable records are the member's property. The ecosystem cannot withhold, restrict, or condition governance participation data. Members carry their experience with them.

**Return is not second-class.** Returning members follow a standardized process that acknowledges their history without granting preferential treatment. They consent to current agreements, complete a standard orientation, and enter as full members.

**Dissolution is not punishment.** AZPOs that can no longer sustain themselves dissolve with dignity. No external body can unilaterally force dissolution, and the process ensures every member transitions cleanly.

## Relationship to Other Layers

- **Layer I (Agreement):** Exit triggers agreement amendments. Returning members consent to current agreements. The UAF's departure clause is executed during voluntary exit.
- **Layer II (Authority):** Role obligations are unwound during departure. Role tenure is documented in portable records. Returning members go through standard role-assignment.
- **Layer III (ACT Engine):** Pending proposals are resolved during commitment unwinding. ACT participation history is captured in portable records.
- **Layer IV (Economic):** Economic commitments are settled during unwinding. Resource allocations are returned or transferred. Current-See history is portable.
- **Layer V (Federation):** Cross-ecosystem portability enables members to carry records between federated NEOS ecosystems.
- **Layer VI (Conflict):** Active conflict resolutions are handled during commitment unwinding. Re-entry rejection is challengeable through conflict resolution.
- **Layer VII (Safeguard):** Mass exit triggers governance health audits. Exit patterns are governance health indicators. Departure friction is a capture signal.
- **Layer VIII (Emergency):** Sole critical role departures trigger emergency coverage protocols. Emergency conditions accommodate urgent exit timelines.
- **Layer IX (Memory):** Departure records, unwinding ledgers, and dissolution records are archived in governance memory. Portable records draw from memory layer data.

## Cross-Layer References

Departure Record template: `voluntary-exit/assets/departure-record-template.yaml`. Commitment Unwinding Ledger template: `commitment-unwinding/assets/commitment-unwinding-ledger-template.yaml`. Portable Record schema: `portable-record/assets/portable-record-schema.yaml`. Dissolution Record template: `azpo-dissolution/assets/dissolution-record-template.yaml`. Re-Entry Record template: `re-entry-integration/assets/re-entry-record-template.yaml`.
