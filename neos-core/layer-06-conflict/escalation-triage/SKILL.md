---
name: escalation-triage
description: "Assess conflict severity, scope, root cause, and safety to route each situation to the right resolution tier -- direct dialogue, coaching, harm circle, or community-wide assessment -- so that no conflict is over-escalated or swept aside."
layer: 6
version: 0.1.0
depends_on: [harm-circle, nvc-dialogue, coaching-intervention, domain-mapping]
---

# escalation-triage

## C. Trigger Conditions

- A participant files a conflict report or harm report
- A facilitator observes an emerging conflict pattern that has not been self-reported
- A circle steward identifies a recurring tension affecting circle functioning
- A previous direct dialogue attempt has failed and the parties seek next-tier support
- A safety concern is flagged by any participant, requiring immediate assessment
- A repair agreement follow-up reveals that the underlying conflict was not adequately addressed

## D. Required Inputs

- **Conflict report or observation**: a description of the situation from the reporting party, including what happened, who is involved, and what impact has been experienced. Format: written or verbal, documented by the triager.
- **Reporting party identity**: who brought the conflict forward -- the person harmed, a witness, a facilitator, or a steward. The relationship of the reporter to the conflict affects the assessment.
- **Domain reference**: the ETHOS, circle, and governance context where the conflict is occurring, verified against domain-mapping.
- **Prior resolution attempts**: any direct dialogue, informal conversation, or previous triage that has already occurred, including outcomes and why the conflict persists.
- **Safety flag** (optional but prioritized): any indication that a participant's physical, emotional, or psychological safety is at immediate risk.

## E. Step-by-Step Process

1. **Receive the report.** The triager receives the conflict report through any channel -- direct request, facilitator referral, or self-report. The triager acknowledges receipt within 24 hours and confirms whether the situation falls within Layer VI scope (interpersonal/intra-ETHOS) or should be redirected to Layer V (structural inter-ETHOS). Timeline: within 24 hours.
2. **Assess safety.** If a safety flag is present, the triager conducts an immediate safety assessment. Safety-critical situations bypass the standard triage timeline and activate emergency protocols: separation of parties if needed, interim safety measures, and compressed process timelines. Timeline: immediate for safety-flagged reports.
3. **Evaluate triage dimensions.** The triager assesses the situation along six dimensions using the triage-assessment-template.yaml. **Severity**: is the harm isolated, patterned, or systemic? **Scope**: does the impact extend beyond the direct parties to the circle, the ETHOS, or the ecosystem? **Parties**: who is involved, what are the power dynamics, and are authority holders implicated? **Root cause type**: is this a values conflict, a skill gap, an agreement breach, a communication breakdown, or a structural deficiency? **Urgency**: is the situation deteriorating, stable, or already resolved? **Safety**: are there ongoing risks to any participant?
4. **Determine the routing.** Based on the six-dimension assessment, the triager recommends one of four pathways. **Tier 1 -- Direct Dialogue**: low severity, limited scope, no safety concern, parties willing and capable. The triager may suggest NVC support. **Tier 2 -- Coaching Intervention**: root cause is a skill gap rather than a values conflict or intentional harm. Route to coaching-intervention. **Tier 3 -- Harm Circle**: significant harm, pattern of behavior, or agreement breach affecting trust. Route to harm-circle. **Tier 4 -- Community Impact Assessment**: harm extends beyond direct parties, pattern of similar conflicts revealed, or structural gap exposed. Route to community-impact-assessment, often in parallel with a harm circle for the direct parties.
5. **Consult the affected parties.** The triager shares the routing recommendation with the person who filed the report and the other affected parties. The triager explains the rationale. If the affected parties disagree with the routing, the triager documents the disagreement and adjusts if the parties present additional information that changes the assessment. The parties cannot be forced into a process they do not consent to, but the triager documents cases where parties choose a lower tier than recommended.
6. **Document and hand off.** The triager creates the triage assessment record using the triage-assessment-template.yaml and hands off to the appropriate skill. The record includes the assessment, the routing decision, the rationale, and any party objections. The triage record is linked to the subsequent process record.

## F. Output Artifact

A triage assessment record following `assets/triage-assessment-template.yaml`, containing: unique triage ID, date, reporting party, triager identity, situation summary, assessment across all six dimensions (severity, scope, parties, root cause, urgency, safety), routing decision with rationale, party consultation outcomes (agreement or disagreement with routing), handoff target (which skill and facilitator), and linked records (prior triage, related conflict records). The record is accessible to the triager, the parties, and the facilitator of the next-tier process.

## G. Authority Boundary Check

- The **triager** has assessment and recommendation authority. The triager evaluates the situation and recommends a routing. The triager does not have resolution authority -- they do not determine the outcome of the conflict.
- The triager **cannot override the affected parties' process preferences**. If parties want direct dialogue, the triager cannot force them into a harm circle. The triager can document their concern that the chosen tier is insufficient, and if the conflict re-escalates, the prior triage recommendation is reviewed.
- The triager **cannot dismiss a report**. Every report receives a triage assessment. If the triager determines the situation is outside Layer VI scope, they redirect to the appropriate layer with documentation, not discard the report.
- **Authority holder conflicts** receive heightened scrutiny. When the person reported is a steward, OSC member, or other authority holder, the triager documents the power dynamics in the assessment and routes to a process where the authority holder's position does not distort the outcome.
- **Multiple triagers** may be consulted for complex situations. If a single triager has a relationship with one of the parties, a second triager conducts a parallel assessment.

## H. Capture Resistance Check

**Capital capture.** A financially influential participant is reported for harmful behavior. The triager routes the situation to Tier 1 (direct dialogue) citing "low severity" when the six-dimension assessment clearly indicates Tier 3 (harm circle). The capture resistance mechanism: triage records are reviewable, and any party can request a second triage from a different triager. If a pattern of under-routing for high-status members emerges, it triggers a community-impact-assessment of the triage process itself. The triager's financial relationship to any party is a disqualifying conflict of interest.

**Charismatic capture.** A well-liked community member is reported, and social pressure pushes the triager to minimize the assessment. The six-dimension framework is the structural safeguard: the triager assesses severity, scope, parties, root cause, urgency, and safety using documented criteria, not personal affinity. The triage-assessment-template.yaml requires written justification for each dimension, making "gut feeling" routing visible and challengeable.

**Emergency capture.** A crisis is invoked to skip triage entirely -- "we do not have time to assess, just deal with it." Emergency does not eliminate triage; it compresses the timeline. Emergency triage uses the same six dimensions but completes the assessment within hours rather than days. The emergency triage record is flagged for post-crisis review.

**Informal capture.** "This has already been handled informally" is used to prevent a formal triage. The triager verifies informal resolution by consulting the person harmed directly and privately. If the person harmed confirms satisfaction, the triage records the resolution. If the person harmed was pressured into accepting informal resolution, the triage proceeds formally.

## I. Failure Containment Logic

- **Triager bias detected**: any party can request a second triage from a different triager. The second triage is independent -- the second triager reviews the situation from scratch, not the first triager's assessment. Both triage records are retained.
- **Parties reject the routing**: the triager documents the disagreement and the parties' preferred process. If the preferred process fails to resolve the conflict, the original triage recommendation is revisited without prejudice.
- **Report is ambiguous**: the triager requests additional information from the reporting party and may conduct brief confidential conversations with other involved parties. The triage timeline extends by the time needed to gather information, documented in the record.
- **Multiple conflicts entangled**: the triager separates the conflicts into distinct triage assessments, each routed independently. Shared systemic factors are noted and may trigger a community-impact-assessment.
- **Triager unavailable**: if no triager is available within 48 hours, any trained facilitator in the ecosystem can conduct an interim triage, flagged for review by the designated triager pool within 7 days.

## J. Expiry / Review Condition

Triage assessment records do not expire -- they are permanent governance records that inform pattern analysis. The routing recommendation has a 14-day activation window: if the recommended process has not begun within 14 days, the triager follows up with the parties and the designated facilitator. If the situation has changed, a re-triage is conducted. The triage process itself is reviewed every 6 months as part of the Layer VI review cycle. Pattern analysis across triage records is conducted quarterly to identify systematic routing biases. Minimum review interval for unactioned triage recommendations: 14 days.

## K. Exit Compatibility Check

When a participant exits the ecosystem, active triage assessments involving that participant are updated. If the **reporting party** exits, the triage record is retained and the underlying situation is assessed for community impact -- the person's departure does not erase the reported concern. If the **reported party** exits, the triage record is archived with the exit noted, and any ongoing community-level concerns continue through the appropriate process. If the **triager** exits, their active assessments are reassigned to another triager within 7 days. Triage records involving exited participants remain valid governance artifacts.

## L. Cross-Unit Interoperability Impact

When a conflict involves participants from different ETHOS, the triage requires input from both ETHOS' facilitation pools. The triager is selected from neither ETHOS (or from a neutral pool). The triage assessment must evaluate scope across both units and determine whether the conflict is interpersonal (Layer VI, handled jointly) or structural (Layer V, redirected). Cross-unit triage records are stored in both ETHOS' conflict registries with linked entries. Notification requirements: both ETHOS' stewards are informed that a cross-unit conflict has been triaged (without disclosing details). When one ETHOS's triage process differs in configuration from another's, the more protective standard applies to cross-unit situations.
