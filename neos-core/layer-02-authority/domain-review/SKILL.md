---
name: domain-review
description: "Evaluate an existing governance domain through scheduled review -- assessing each of the 11 contract elements, steward effectiveness, and domain health to determine whether to reaffirm, refine, reassign, merge, or sunset the domain."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, role-assignment]
---

# domain-review

## A. Structural Problem It Solves

Without periodic review, domains accumulate scope creep as stewards act in ways that feel natural but exceed their original authority. Domain contracts drift from actual practice — the document says one thing, the steward does another, and after a year no one remembers what was agreed. Stewards become entrenched not through malice but through inertia; the evaluation schedule in the domain contract exists precisely to prevent tenure by default. This skill is the authority layer's immune system: it catches decay — scope creep, steward mismatch, constraint drift, and delegator neglect — before it calculates into structural damage. Without domain-review, every other Layer II skill operates on a foundation that silently degrades. With it, every domain contract is a living document that stays honest.

## B. Domain Scope

This skill applies to any active domain contract that carries an evaluation schedule (element 11 of the domain contract). This includes all domains created through the domain-mapping skill, regardless of scope (circle, cross-circle, AZPO-level, or ecosystem-level). Provisional domains (incomplete, operating under the 30-day window from domain-mapping) are reviewed by completing their outstanding elements before the 30-day window expires — that is not a domain-review, it is domain-mapping completion. Sunset domains are archived records, not eligible for review. Vacant domains trigger a simplified review: the delegating body reviews whether to reassign (role-assignment), sunset (role-sunset), or temporarily absorb the domain.

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

1. **Convene the review body.** The review body consists of: delegating body members (voting), the domain steward (participating but not voting on the outcome), and representatives from dependent domains (advisory — they provide input but do not vote). The review is chaired by a facilitator who is not the steward. For cross-AZPO domains, representatives from all affected AZPOs participate.

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

**Cross-AZPO domains** — domains whose purpose, dependencies, or customers span multiple AZPOs — are reviewed with representatives from all affected AZPOs participating. Each AZPO's representative provides feedback on how the domain is performing from their perspective. The review record is registered in all affected AZPOs' registries. If the review outcome is Merge or Sunset, all affected AZPOs must reach consent from their own delegating bodies. Cross-AZPO reviews are coordinated by a neutral facilitator who is not a member of either AZPO's governance bodies.

## OmniOne Walkthrough

Six months after the Community Engagement circle was formally defined through domain-mapping, its scheduled review arrives. The AE (delegating body) convenes the review body: three AE members (voting), the Community Engagement circle steward Aiko (participating, not voting), and two representatives from dependent domains — the Media circle and the Events coordination team (advisory).

The element-by-element evaluation proceeds:
- *Key responsibilities*: The review body notices that event coordination — listed as a Community Engagement responsibility — has been informally handled by the Media circle for the past 3 months. Neither circle made a formal boundary adjustment. The assessment: "needs refinement."
- *Delegator responsibilities (element 9)*: The AE failed to provide timely information on ecosystem-wide events to the Community Engagement circle for 2 of the past 6 months. The Media circle representative confirms this created coordination gaps. The assessment: "needs refinement — delegator action required."
- All other elements are assessed as adequate.

**Steward effectiveness assessment:** Aiko's metric performance is strong — community feedback scores are above target, event attendance at community-organized events improved. Customer feedback (from TH members who interact with the circle) is positive. The dependent domain feedback from Media is constructive: "the drift in event coordination was structural, not a failure of Aiko's stewardship." The qualitative assessment: Aiko has been effective within the domain as defined; the domain contract has drifted from practice.

**Outcome decision:** Refine — two amendments needed: (1) remove event coordination from Community Engagement's key responsibilities; (2) note the delegating body's remediation commitment for element 9. The boundary negotiation to formally add event coordination to Media's domain contract will be triggered separately through the authority-boundary-negotiation skill.

**Edge case:** One AE member objects to simply removing event coordination without first confirming Media can absorb it. The consent round surfaces this concern. The resolution: the review record specifies that the Community Engagement amendment does not take effect until the authority-boundary-negotiation with Media is complete — the two processes are linked. Consent achieved.

**Output artifact:** Domain review record REV-CE-2026-001: element evaluations, steward assessment (positive), outcome (Refine), follow-up actions (domain-mapping amendment, authority-boundary-negotiation with Media, AE remediation commitment for element 9), next evaluation date: September 2026.

## Stress-Test Results

### 1. Capital Influx

A major funder conditions a significant grant on the outcome of a domain review — they want the Economics circle's domain contract amended to include "external funder liaison" as a key responsibility, effectively expanding the circle's authority to interface with funders on their terms. The domain-review process evaluates element-by-element against current conditions, not against funder preference. The proposed amendment to key responsibilities would be assessed: does "external funder liaison" reflect actual work already happening? If yes, the refinement is structural and legitimate. If no, it is a funder-driven scope expansion. The capture resistance mechanism is in the review body's composition: the delegating body (AE) includes the funder's preferred amendment in the element assessment, flags it as externally motivated, and evaluates it on structural grounds alone. The consent decision is among AE members — no funder representative has a vote. The funder's financial offer is documented in the review record as contextual background, not as a factor in the outcome.

### 2. Emergency Crisis

A sudden infrastructure failure disrupts 40% of OmniOne's operations, and three domain reviews are scheduled to occur during the crisis period. The delegating body may defer scheduled reviews during declared emergencies — but only for the duration of the emergency and with a mandatory review within 30 days of the emergency ending. The domains continue operating under their existing contracts; no new authority expansions are permitted during the deferral period. The crisis itself may trigger threshold-event reviews for domains whose stewards are affected. Emergency reviews follow a compressed process: the review body convenes with available members (minimum: delegating body lead + steward), element-by-element evaluation is summarized rather than exhaustive, and outcome is limited to Reaffirm or Reassign — Merge and Sunset require full process and cannot be conducted under emergency compression.

### 3. Leadership Charisma Capture

A popular and long-serving steward is approaching their domain-review. The delegating body informally signals that the review is "just a formality" — everyone admires the steward's work. The review proceeds anyway: element-by-element evaluation is mandatory, not optional, regardless of the steward's reputation. The customer feedback is solicited in writing before the review session, ensuring it is not shaped by the steward's presence in the room. If the structured evaluation surfaces no concerns, the outcome is Reaffirm and the reputation is vindicated structurally, not assumed. If the evaluation surfaces legitimate concerns — say, metric performance below target — those are addressed through the normal outcome process. Social admiration does not override structural assessment; the review record stands regardless of the steward's standing in the community.

### 4. High Conflict / Polarization

The delegating body is split on the outcome of a domain review: half believe the steward should be reassigned based on cultural fit concerns; the other half believe reassignment is politically motivated. The domain-review process requires that Reassign outcomes be grounded in evidence from the element-by-element evaluation and steward effectiveness assessment — not in cultural preference or political alignment. If the split cannot be resolved through consent integration, the contested outcome routes to GAIA Level 4 (Coaching). The coach maps the underlying tension: the concern about cultural fit may reflect a legitimate competency concern (competencies element) or may be a proxy for factional conflict. The element-by-element record makes the difference visible — either there is documented evidence for the concern or there is not. The coach works toward a resolution that the review body can consent to based on structural grounds.

### 5. Large-Scale Replication

OmniOne grows to 300 active domains across 20 AZPOs. At the default 6-month cadence, approximately 50 domain reviews occur each month. The domain-review process scales because it is domain-local: each review involves only the delegating body, the steward, and dependent domain representatives — not the entire ecosystem. The agreement registry tracks review dates and sends automated notices when reviews are approaching or overdue. The element-by-element structure provides consistency: a reviewer in one AZPO follows the same 11-element checklist as a reviewer in another, enabling quality-comparable reviews without central coordination. The OSC receives aggregate review reports quarterly — not individual review records — to maintain ecosystem-level visibility without micromanagement.

### 6. External Legal Pressure

A government regulation requires that all governance roles with financial authority be audited annually by an external party. This does not replace the domain-review; it is incorporated into it. The domain contract's evaluation schedule is updated to align with the external audit timeline. The external audit findings are added to the "Required Inputs" for the domain-review — audit observations become input data for the element-by-element evaluation. The review body uses the audit findings to assess the relevant elements (particularly constraints, deliverables, and metrics). The external requirement adds rigor to the review but does not change its structure: the delegating body still reaches the outcome through consent, the steward still participates without voting, and the review record is still a NEOS governance artifact alongside the external audit record.

### 7. Sudden Exit of 30% of Participants

A significant participant departure affects 6 of OmniOne's 20 active domains — the departed participants were stewards or delegating body members. All 6 domains trigger immediate reviews under the threshold-event rule. The delegating body for each domain is reconstituted as quickly as possible with remaining members; if a delegating body falls below quorum, the next-level body (OSC) steps in as interim reviewer. Reviews for the 6 domains are prioritized by criticality: domains with active pending commitments, active agreements, or cross-AZPO dependencies are reviewed first. The outcome for domains with departed stewards is typically Reassign (triggering role-transfer emergency handover). The sudden exit is documented as the trigger in all 6 review records, providing a clear historical record of how the ecosystem managed the transition.
