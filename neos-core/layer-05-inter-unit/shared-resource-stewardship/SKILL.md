---
name: shared-resource-stewardship
description: "Govern jointly-held resources across multiple ETHOS -- shared pools, infrastructure, repositories, and services -- through multi-party consent with rotating stewardship and equitable access rules."
layer: 5
version: 0.1.0
depends_on: [cross-ethos-request, agreement-creation, funding-pool-stewardship, role-assignment]
---

# shared-resource-stewardship

## C. Trigger Conditions

- Two or more ETHOS identify a resource they want to share rather than duplicate
- An existing informally-shared resource needs governance formalization
- A federation agreement calls for the establishment of a shared resource
- A cross-ETHOS request reveals a resource that would benefit from joint stewardship

## D. Required Inputs

- **Participating ETHOS** -- all units that will share governance of the resource (mandatory)
- **Resource description** -- what the resource is, its current state, and its purpose (mandatory)
- **Resource type** -- pool, infrastructure, repository, or service (mandatory)
- **Proposed governance structure** -- stewardship model, access rules, contribution commitments, reporting schedule (mandatory)
- **Proposed review cycle** -- when the governance agreement will be reviewed (mandatory; minimum: annual)
- **Exit terms** -- what happens when an ETHOS withdraws (mandatory; default: 90-day notice with contribution wind-down)

## E. Step-by-Step Process

1. **Propose shared resource.** One or more ETHOS submit a cross-ETHOS request (per cross-ethos-request skill) proposing the establishment of a jointly governed resource.
2. **Negotiate governance terms.** Each participating ETHOS runs an internal advice phase on the proposal. Key terms are negotiated collaboratively: stewardship rotation, access rules, contribution commitments, reporting cadence, and exit provisions.
3. **Draft governance agreement.** The proposing parties draft a shared resource governance agreement using `assets/shared-resource-agreement-template.yaml`, incorporating negotiated terms.
4. **Each ETHOS ratifies through consent.** Every participating ETHOS runs its own consent round. No ETHOS is bound until it has completed its own ACT process. If one ETHOS's consent fails, the process returns to negotiation to address that ETHOS's concerns.
5. **Appoint first steward.** The governance agreement specifies which ETHOS provides the first steward. The appointed steward is confirmed through the role-assignment skill in their home ETHOS. A successor from a different ETHOS is named per the rotation schedule.
6. **Operate with reporting.** The steward manages day-to-day operations within the governance agreement's terms and produces regular reports visible to all participating ETHOS.
7. **Review at defined intervals.** All participating ETHOS review the governance agreement at the scheduled review date. Amendments follow the same multi-party consent process as establishment.

## F. Output Artifact

A shared resource governance agreement following `assets/shared-resource-agreement-template.yaml`, containing: agreement ID, resource name and description, resource type, participating ETHOS, access tiers, contribution commitments per ETHOS, stewardship rotation schedule, reporting cadence, review date, exit terms, and ratification records from each ETHOS. Registered in every participating ETHOS's agreement registry with linked entries.

## G. Authority Boundary Check

- **No single ETHOS controls** the shared resource regardless of contribution level. Contribution size does not grant proportional governance authority.
- **Steward authority** is limited to operational management within the governance agreement's terms. Strategic decisions (access rule changes, contribution adjustments, sunset) require consent from all participating ETHOS.
- **All participating ETHOS** must consent to governance agreement amendments. One ETHOS cannot unilaterally change access rules, contribution requirements, or stewardship terms.
- **The steward's home ETHOS** does not receive preferential access or reporting by virtue of hosting the steward role.

## H. Capture Resistance Check

**Contribution-proportional control.** A larger contributor claims more governance authority based on financial or material contribution. Resistance: the governance agreement explicitly states that governance authority is equal across participating ETHOS regardless of contribution level. Contribution commitments are documented but do not translate into differential governance rights.

**Steward capture.** The steward favors their home ETHOS in resource allocation, access decisions, or information sharing. Resistance: rotating stewardship limits any home-ETHOS advantage to the steward's term. Reporting requirements make allocation patterns visible to all ETHOS. Any ETHOS may request a steward review if favoritism is observed.

**Information asymmetry.** One ETHOS gains exclusive knowledge of the resource's state and uses it to shape governance decisions. Resistance: all participating ETHOS receive the same reporting data. Access to raw resource information is specified in the governance agreement and must be equitable.

**Free-rider dynamics.** An ETHOS benefits from the shared resource without meeting its contribution commitments. Resistance: contribution commitments are explicit with consequence clauses (review trigger, access suspension pending remediation). Persistent free-riding is treated as grounds for exit review.

## I. Failure Containment Logic

- **One ETHOS fails consent during ratification:** The process returns to negotiation to address that ETHOS's concerns. The agreement does not take effect until all participating ETHOS consent. Other ETHOS' prior consent holds but may be reaffirmed if negotiations exceed 90 days.
- **ETHOS withdraws from arrangement:** Per exit terms (default: 90-day notice, contribution wind-down). Access rights sunset at end of notice period. Resource continues under remaining participants' governance, triggering a review.
- **Steward misconduct:** Any participating ETHOS may request a steward review. If misconduct is confirmed, an interim steward from a different ETHOS is appointed pending full rotation.
- **Resource depleted or destroyed:** All participating ETHOS convene an emergency decision on next steps: reconstitute, wind down, or transfer remaining assets per exit terms.
- **Negotiation stalls:** Any participating ETHOS may withdraw from negotiations with documentation. This does not obligate remaining parties.

## J. Expiry / Review Condition

- **Annual review minimum.** The governance agreement must state a review date no more than 12 months from ratification.
- **Missed review:** Agreement enters a 60-day grace period. After 60 days without review, status changes to "under review" -- operational stewardship continues but no strategic decisions may be made.
- **Governance agreements do not auto-expire.** The resource continues under existing terms until review produces a new agreement or sunset decision.
- **Steward rotation:** Configurable per agreement; recommended 12-month terms with no ETHOS holding consecutive steward terms.

## K. Exit Compatibility Check

- **Exiting ETHOS's contributions** are handled per exit terms (default: contribution wind-down over notice period, no clawback of previously contributed resources)
- **Exiting ETHOS's access** ceases at end of notice period; content they contributed remains under the resource's governance (individual original works revert to creators per UAF)
- **In-progress stewardship** by an exiting ETHOS's member: steward completes handoff within notice period or resigns with interim appointment
- **Resource continues** under remaining participants' governance; review is triggered to assess terms for the smaller participant set
- **Last ETHOS standing:** If all but one ETHOS withdraws, the resource must either wind down or be formally transferred to the remaining ETHOS through a new governance process

## L. Cross-Unit Interoperability Impact

This skill is itself a cross-unit interoperability mechanism. It defines how ETHOS govern resources in the space between them. Outputs are registered in every participating ETHOS's agreement registry with linked entries. The skill references cross-ethos-request for initial proposals and federation-agreement for formalizing the broader relationship that shared resource governance is often embedded within. New ETHOS joining an existing arrangement follow the same ratification process and the existing agreement is amended to include them.
