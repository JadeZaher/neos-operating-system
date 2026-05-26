---
name: coaching-intervention
description: "Design coaching responses for conflicts rooted in skill gaps rather than values conflicts -- identify the gap, select an appropriate coach, build a voluntary coaching plan, and assess whether the gap has closed before the conflict escalates further."
layer: 6
version: 0.1.0
depends_on: [role-assignment, domain-mapping]
---

# coaching-intervention

## C. Trigger Conditions

- The escalation-triage process identifies a skill gap as the primary root cause of a conflict
- A facilitator or steward observes a recurring behavioral pattern that disrupts governance processes and is attributable to a competency gap
- A participant self-identifies a skill gap and requests coaching support
- A repair agreement follow-up reveals that unfulfilled commitments stem from a skill deficit rather than unwillingness
- A community impact assessment identifies a widespread skill gap across multiple participants

## D. Required Inputs

- **Triage assessment record**: the escalation-triage record that routed the situation to coaching, including the root cause analysis. Format: linked record ID.
- **Skill gap identification**: specific description of the skills the participant lacks and how the gap manifests in governance interactions. Provided by the triager, facilitator, or the participant themselves.
- **Participant profile**: the person who will receive coaching, including their governance role, their experience level, and their own perspective on the situation.
- **Coach selection criteria**: the relevant skills needed from the coach, the requirement that the coach is not the participant's direct authority holder, and the pool of available coaches.
- **Affected parties input**: perspectives from people affected by the skill-gap behavior, to ensure the coaching plan addresses the actual impact and not only the coach's assessment.

## E. Step-by-Step Process

1. **Confirm coaching eligibility.** The coaching facilitator reviews the triage assessment to confirm that the root cause is a skill gap rather than a values conflict or intentional harm. If the facilitator determines the situation is misrouted, they return it to escalation-triage with their assessment. Timeline: within 48 hours of receiving the routing.
2. **Approach the participant.** The coaching facilitator approaches the participant with the coaching recommendation. The approach is framed as capacity-building, not punishment: "The triage process identified that some governance skills could help you be more effective in your role. Coaching is available if you are interested." The facilitator explains that coaching is voluntary. If the participant declines, the facilitator documents the declination and the consequences: the underlying conflict remains unresolved and may escalate through normal channels if the disruptive behavior continues.
3. **Select the coach.** A coach is selected based on three criteria: relevant expertise (they have the skills the participant needs to develop), independence (they are not the participant's direct authority holder, circle steward, or someone with a power dynamic that could distort the coaching relationship), and availability. The participant has input on coach selection -- if the participant is uncomfortable with the proposed coach, an alternative is offered. The coach is selected from within the ecosystem or from a qualified external pool.
4. **Design the coaching plan.** The coach meets with the participant to co-design the coaching plan. The plan identifies: specific skills to develop, current skill level (based on the participant's self-assessment and the affected parties' observations), target skill level, learning methods (observation, practice, feedback, mentoring), timeline (typically 4-12 weeks), check-in schedule (typically bi-weekly), and measurable progress indicators. The plan is documented using coaching-plan-template.yaml.
5. **Consult affected parties.** The coach shares the coaching plan's skill targets (not private coaching details) with the people affected by the skill-gap behavior. This consultation ensures the coaching addresses what the affected parties actually experienced, not only what the coach thinks is important. Affected parties may suggest specific skill areas to include.
6. **Execute the coaching.** The coach and participant meet according to the coaching plan schedule. Coaching sessions are private -- the content of coaching conversations is confidential between the coach and participant. Progress is assessed at each check-in against the measurable indicators defined in the plan. The coach provides feedback, the participant practices new approaches, and both document progress.
7. **Assess the outcome.** At the end of the coaching timeline, the coach and participant conduct a final assessment: have the target skills been developed? The assessment includes feedback from the affected parties -- do they observe behavioral change? The outcome is documented in the coaching plan record. Three possible outcomes: (a) skills developed, conflict resolved, case closed; (b) partial progress, coaching extended with modified plan; (c) skills not developed despite coaching, situation re-enters escalation-triage for potential rerouting to harm-circle or other process.
8. **Formalize repair agreement if needed.** If the coaching produced specific commitments for ongoing behavioral change, those commitments are formalized through the repair-agreement skill with appropriate follow-up schedules.

## F. Output Artifact

A coaching plan and outcome record following `assets/coaching-plan-template.yaml`, containing: unique coaching ID, date, participant identity and role, coach identity and qualifications, triage record link, identified skill gaps with current and target levels, coaching plan with methods and timeline, check-in schedule and results, affected parties' feedback, outcome assessment (skills developed / partial progress / not developed), and link to any resulting repair agreement. The record is accessible to the participant, the coach, the follow-up facilitator, and (for outcome summary only) the triager. Private coaching session content is not included in the record.

## G. Authority Boundary Check

- The **coach** has coaching authority only: they guide skill development through feedback, practice, and mentoring. The coach cannot impose behavioral mandates, cannot assign or remove governance roles, and cannot unilaterally determine the outcome of the coaching process.
- **Coaching is voluntary.** The participant cannot be forced to accept coaching. The consequence of declining coaching is documented and transparent: the underlying conflict remains unresolved, and if the disruptive behavior continues, the situation may escalate to a harm circle or other process. Declining coaching is not itself a violation.
- The coach **must not be the participant's direct authority holder**. A circle steward cannot coach a member of their own circle on governance skills because the power dynamic distorts the coaching relationship. The coach's independence is verified before the coaching plan is finalized.
- The **coaching process cannot be used as a soft punishment** or status demotion. Being coached is not a mark of failure -- it is a skill-building opportunity. The coaching facilitator monitors for framing that treats coaching as disciplinary action and corrects it.
- **Affected parties** have input on coaching plan targets but do not attend coaching sessions and do not determine the coaching outcome. Their role is to describe the impact of the skill gap and to provide feedback on observed behavioral change.

## H. Capture Resistance Check

**Capital capture.** A financially influential participant is routed to coaching but uses their financial position to select a sympathetic coach or to pressure the coaching facilitator into certifying skills as "developed" when they have not changed. The coach selection process prevents this: the coaching facilitator, not the participant, proposes coaches, and the participant can suggest alternatives but cannot dictate the selection. The outcome assessment includes affected parties' feedback -- if the affected parties report no behavioral change, the participant's financial status does not override that evidence.

**Charismatic capture.** A well-liked participant who is routed to coaching leverages their social standing to frame coaching as unnecessary -- "everyone knows I am great at this, the triage was wrong." The structural safeguard is the triage assessment record, which documents specific behavioral observations and affected parties' experiences. Coaching eligibility is determined by documented behavior, not by reputation. The coach assesses skill development against measurable indicators, not social perception.

**Emergency capture.** Crisis conditions are cited to skip coaching and "just let people get back to work." Emergency does not eliminate the skill gap. Under emergency conditions, coaching timelines may be deferred (the participant continues their role with interim support from a skilled partner), but the coaching plan is activated as soon as conditions stabilize. The deferral and interim support are documented.

**Informal capture.** "I already know how to do this, I was just having a bad day" is used to avoid coaching. The coaching facilitator distinguishes between an isolated incident (which would have been routed to direct dialogue, not coaching) and a pattern (which the triage identified based on multiple observations). The triage assessment documents the pattern, preventing a single self-reported explanation from overriding observed evidence.

## I. Failure Containment Logic

- **Participant declines coaching**: the declination is documented, the underlying conflict remains flagged, and the escalation-triage record notes that coaching was offered and declined. If the disruptive behavior continues, the next triage assessment accounts for the declined coaching.
- **Coach and participant relationship breaks down**: the participant can request a coach change at any point. The coaching facilitator assigns a new coach and the coaching plan restarts from the current progress point, not from zero.
- **Coaching does not produce skill development**: after the full coaching timeline, if the outcome assessment shows skills were not developed, the situation re-enters escalation-triage. The coaching record becomes input for the new triage, which may route to a harm circle (if the behavior is now causing harm that cannot be attributed to a fixable skill gap) or to a structural solution (the participant's role is adjusted to match their actual skills).
- **Coaching recommendation is consistently directed at marginalized members**: if a pattern emerges where coaching is disproportionately recommended for members of a particular group, this triggers a community-impact-assessment of the triage process itself. The assessment examines whether the triage criteria contain implicit bias.
- **Coach imposes personal governance preferences**: the coaching plan's skill targets are derived from the ecosystem's governance standards and the affected parties' feedback, not the coach's personal style. If the participant or coaching facilitator identifies that the coach is teaching their preferences rather than the ecosystem's protocols, the coach is replaced.

## J. Expiry / Review Condition

Coaching plans have a defined lifecycle: active from the start date, with bi-weekly check-ins, and a final assessment at the end of the coaching timeline (typically 4-12 weeks). If a check-in is missed, it is rescheduled within 7 days. Coaching plans do not auto-expire -- they are either completed (skills developed), extended (partial progress), or closed with rerouting (skills not developed). Completed coaching records remain in the governance registry as reference for future pattern analysis. The coaching-intervention skill itself is reviewed annually as part of the Layer VI review cycle. Minimum review interval for active coaching plans: bi-weekly check-ins.

## K. Exit Compatibility Check

When a participant exits the ecosystem during active coaching, the coaching plan is closed and documented as "incomplete -- participant exited." The coaching record is retained as a governance artifact. The underlying conflict that led to coaching is reassessed: if the exit resolves the conflict (the disruptive behavior ceases because the person left), the triage record is updated. If the exit does not resolve the community-level impact (the skill gap was symptomatic of a broader pattern), a community-impact-assessment may be triggered. When a **coach** exits mid-engagement, a replacement coach is assigned within 14 days. The coaching plan transfers to the new coach with the participant's consent.

## L. Cross-Unit Interoperability Impact

When a participant's skill-gap behavior affects multiple ETHOS, the coaching plan is designed to address the cross-unit impact. The coach may be selected from a third ETHOS to maintain neutrality. Affected parties from all impacted ETHOS provide input on the coaching plan targets. Check-in feedback is gathered across units. The coaching record is stored in the participant's home ETHOS with notification to affected ETHOS (outcome summary only, not private coaching content). If the coaching reveals that the skill gap is common across ETHOS (multiple participants from different units exhibiting similar gaps), the coaching facilitator escalates to community-impact-assessment to examine whether the ecosystem's onboarding or training processes have a structural deficit.
