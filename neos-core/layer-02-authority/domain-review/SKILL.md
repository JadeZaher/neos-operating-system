---
name: domain-review
description: "Evaluate an existing governance domain through scheduled review -- assessing each of the 11 contract elements, steward effectiveness, and domain health to determine whether to reaffirm, refine, reassign, merge, or sunset the domain."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, role-assignment]
---

# domain-review

## C. Trigger Conditions

- **Scheduled evaluation date** reaches the date specified in the domain contract's evaluation schedule element — this is the default, self-perpetuating trigger
- **Steward requests early review**: the steward identifies that their domain contract no longer reflects actual conditions and requests a review before the scheduled date
- **Delegating body requests review**: the body that created the domain determines a review is warranted outside the normal schedule
- **Threshold event**: 30% or more of the ecosystem participants exit (triggering review of all affected domains), major organizational restructuring, or a pattern of boundary disputes involving this domain (3 or more boundary resolutions referencing this domain within one review cycle)

## D. Required Inputs

- **Domain contract**: the current active version with all 11 elements
- **Steward performance data**: records of metric performance against the targets specified in element 11 of the domain contract (e.g., time-to-decision, output quality surveys, throughput counts)
- **Customer and dependent domain feedback**: qualitative and quantitative input from the parties the domain serves and the domains that depend on it
- **Boundary resolution records**: any authority-boundary-negotiation records involving this domain since the last review
- **Audit or compliance observations**: any external or internal observations relevant to the domain's operation

## E. Step-by-Step Process

1. **Convene the review body.** The review body consists of: delegating body members (voting), the domain steward (participating but not voting on the outcome), and representatives from dependent domains (advisory — they provide input but do not vote). The review is chaired by a facilitator who is not the steward. For cross-ETHOS domains, representatives from all affected ETHOS participate.

2. **Element-by-element evaluation.** The review body evaluates each of the 11 domain elements against current conditions:
   - *Purpose*: Is it still relevant? Has the ecosystem's need changed?
   - *Key responsibilities*: Are these still accurate? Has anything drifted in or out informally?
   - *Customers*: Have the parties this domain serves changed?
   - *Deliverables*: Are deliverables being produced? Are they still the right deliverables?
   - *Dependencies*: Are listed dependencies still accurate? Are there unlisted dependencies in practice?
   - *Constraints*: Are constraints being respected? Have any been informally expanded?
   - *Challenges*: Have known challenges changed? Have new ones emerged?
   - *Resources*: Are resources adequate? Have any been reduced or increased without contract update?
   - *Delegator responsibilities*: Has the delegating body fulfilled its obligations to this domain? (Element 9 is often the most overlooked — delegators have duties too.)
   - *Competencies*: Does the current steward meet the requirements? Have competency needs changed?
   - *Metrics and evaluation schedule*: Are the metrics still the right measures? Is the cadence appropriate?

3. **Steward effectiveness assessment.** Direct feedback from customers and dependent domains, metric performance data, and the review body's qualitative assessment of domain health. The steward presents their own self-assessment first. Customer and dependent domain feedback is solicited before the review session, not during — this prevents social pressure from shaping feedback in the room.

4. **Determine outcome.** The review body reaches a consent decision on one of five outcomes:
   - *Reaffirm*: the domain contract is sound, the steward is effective — set the next evaluation date and close
   - *Refine*: one or more elements need amendment — trigger domain-mapping for the specific amendments
   - *Reassign*: the domain is sound but the steward should change — trigger role-transfer
   - *Merge*: the domain's purpose would be better served combined with another domain — trigger authority-boundary-negotiation and then domain-mapping for the merged domain
   - *Sunset*: the domain has served its purpose or is no longer viable — trigger role-sunset

5. **Document the review record.** Using `assets/domain-review-template.yaml`: record the element-by-element evaluation, steward assessment, outcome decision, and all follow-up actions with responsible parties and deadlines.

6. **Update the domain contract.** Set the next evaluation date. If the outcome is Refine, the domain contract is not yet updated — that happens through the domain-mapping amendment process, which references the review record as the source of the amendment.

## F. Output Artifact

A domain review record following `assets/domain-review-template.yaml`, containing: review ID, domain ID, domain contract version reviewed, review type and trigger, review body composition, date, element-by-element evaluation with assessments (adequate / needs refinement / outdated / not applicable) and notes for each element, steward effectiveness assessment (metric performance data, customer feedback summary, dependent domain feedback summary, qualitative assessment), outcome decision with consent record ID, follow-up actions with responsible parties and deadlines, and next evaluation date.

## G. Authority Boundary Check

- The **review body must include the delegating body** — the steward cannot self-review without oversight. A steward-only review has no standing.
- The **steward participates in the review but does not vote on the outcome**. Participation means presenting context, answering questions, and offering their own self-assessment. It does not mean veto.
- The **outcome is a consent decision among the delegating body members**. An outcome that cannot achieve consent routes to GAIA escalation — the review does not fail, it escalates.
- **Reassignment (triggering role-transfer) requires consent on the reassignment decision** — it is not a unilateral act by the delegating body. The steward's objection to reassignment is handled through the failure containment path, not by suppressing the objection.
- **Merge and Sunset outcomes** require the same consent threshold as the original domain creation (Merge: consent; Sunset: consent with the steward's input formally received).

## H. Capture Resistance Check

**Stewards resisting review.** A steward delays, postpones, or argues the scheduled review date is not appropriate. Review dates are structural, not optional — they are written into the domain contract's evaluation schedule element. A missed review date triggers the failure containment path automatically. The steward can request an early review but cannot delay a scheduled one without delegating body consent.

**Delegating bodies weaponizing review.** The delegating body uses the review as a tool for political removal — targeting a steward they dislike by finding minor element deficiencies and amplifying them. The review is element-by-element against the domain contract — not a popularity assessment, not a confidence vote. Reassignment requires demonstrated metric failure, constraint violations, or steward effectiveness concerns grounded in evidence. The review record must document the specific grounds.

**Review fatigue.** A delegating body calls reviews too frequently — every 6 weeks — disrupting productive stewardship. The domain contract's evaluation schedule element sets the cadence, and the minimum interval between reviews is 3 months. Any review called before the minimum interval requires delegating body consensus, not just consent, to prevent harassment-by-review.

**Delegator neglect disguised as steward failure.** Element 9 (delegator responsibilities) is assessed in every review. If the delegating body has not fulfilled its obligations — withheld information, failed to provide promised resources, not attended joint sessions — this is noted in the review record. Steward performance cannot be fairly assessed when delegator obligations are unmet.

## I. Failure Containment Logic

**Missed review date.** The domain-mapping skill flags the evaluation as overdue. The delegating body receives an escalation notice. A 30-day grace period begins — during this period, the domain continues operating but is flagged as "review overdue" in the registry. If the review has not occurred after 30 days, the delegating body is required to convene within the next 14 days or the domain enters "under review" status, pausing new commitments until the review is complete.

**Contested outcome.** A delegating body member cannot achieve consent on the outcome (e.g., 3 members want Reaffirm, 2 want Reassign). The contested outcome routes to GAIA Level 4 (Coaching), where a coach facilitates a structured conversation to find a resolution. The domain continues operating under its current contract during escalation. If escalation is not resolved within 30 days, the domain enters a supervised operating status: no new commitments, existing commitments fulfilled, pending the review outcome.

**Insufficient data.** Metric data is unavailable, customer feedback was not collected, or the steward's record is incomplete. The review body cannot reach a fair assessment. The review is extended by up to 30 days with a mandatory data collection action — named responsible parties and a specific data collection protocol. If data is still insufficient after 30 days, the outcome defaults to "Refine with data collection mandate" — the domain contract is amended to improve measurement mechanisms.

**Steward exit triggers review.** If the steward exits the ecosystem or steps down, an immediate review is triggered (or the vacancy protocol activates if the exit is sudden). The review assesses whether to reassign or sunset.

## J. Expiry / Review Condition

Reviews are self-perpetuating: each review sets the next review date as part of Step 6. The default cadence is 6 months; the minimum is 3 months; the maximum is 12 months. A domain that goes 12 months without a review is flagged by the agreement registry as critically overdue. The review record itself does not expire — it is a historical record. Follow-up actions from the review have individual deadlines specified in the record; if those deadlines are missed, they trigger their own escalation paths (domain-mapping amendment overdue, role-transfer not initiated, etc.).

## K. Exit Compatibility Check

If the **steward exits** during a review in progress: the review continues with the delegating body acting as temporary steward. The outcome may now default to Reassign or Sunset depending on whether a qualified successor exists. The exiting steward's self-assessment is still included in the record if available; if not, it is noted as "unavailable — steward exit."

If **delegating body members exit** in numbers that impair quorum: the review may be extended until replacements are identified, or the next-level body (e.g., OSC) steps in as interim reviewing body. Reviews cannot be indefinitely delayed due to delegating body vacancies — a 60-day maximum extension applies.

The domain review record is a governance artifact that survives participant exit and ecosystem restructuring. Its historical role is permanent: it documents the condition of the domain at a specific point in time, regardless of subsequent changes.

## L. Cross-Unit Interoperability Impact

**Cross-ETHOS domains** — domains whose purpose, dependencies, or customers span multiple ETHOS — are reviewed with representatives from all affected ETHOS participating. Each ETHOS's representative provides feedback on how the domain is performing from their perspective. The review record is registered in all affected ETHOS' registries. If the review outcome is Merge or Sunset, all affected ETHOS must reach consent from their own delegating bodies. Cross-ETHOS reviews are coordinated by a neutral facilitator who is not a member of either ETHOS's governance bodies.
