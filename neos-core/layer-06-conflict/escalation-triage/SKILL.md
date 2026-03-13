---
name: escalation-triage
description: "Assess conflict severity, scope, root cause, and safety to route each situation to the right resolution tier -- direct dialogue, coaching, harm circle, or community-wide assessment -- so that no conflict is over-escalated or swept aside."
layer: 6
version: 0.1.0
depends_on: [harm-circle, nvc-dialogue, coaching-intervention, domain-mapping]
---

# escalation-triage

## A. Structural Problem It Solves

Without a triage process, communities respond to conflict in one of two dysfunctional ways: everything becomes a major incident requiring the heaviest process, or everything gets minimized into "just talk it out" regardless of severity. Over-escalation burns community capacity and treats minor disagreements as crises. Under-escalation abandons the person harmed by routing serious harm into informal conversations where power imbalances dominate. Both responses erode trust. This skill provides a structured assessment framework that evaluates conflict along six dimensions -- severity, scope, parties, root cause type, urgency, and safety -- and routes each situation to the appropriate resolution tier. The triage itself is fast (Ostrom Principle 6 demands low-cost, accessible entry), transparent (the triager documents their assessment and rationale), and reviewable (any party can challenge a routing decision).

## B. Domain Scope

This skill applies to any conflict, dispute, or harm report that arises within the ecosystem. It serves as the intake gateway for the entire Layer VI conflict and repair system. Scope includes: interpersonal disputes within a circle, cross-circle tensions within an AZPO, behavioral patterns flagged by facilitators or participants, agreement breaches, and reports of harm. Out of scope: structural disputes between AZPOs about authority, resources, or domain boundaries (those belong to Layer V polycentric-conflict-navigation), legal matters requiring external adjudication, and clinical or therapeutic needs beyond governance scope. The triage does not resolve conflicts -- it assesses and routes them.

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
- **Domain reference**: the AZPO, circle, and governance context where the conflict is occurring, verified against domain-mapping.
- **Prior resolution attempts**: any direct dialogue, informal conversation, or previous triage that has already occurred, including outcomes and why the conflict persists.
- **Safety flag** (optional but prioritized): any indication that a participant's physical, emotional, or psychological safety is at immediate risk.

## E. Step-by-Step Process

1. **Receive the report.** The triager receives the conflict report through any channel -- direct request, facilitator referral, or self-report. The triager acknowledges receipt within 24 hours and confirms whether the situation falls within Layer VI scope (interpersonal/intra-AZPO) or should be redirected to Layer V (structural inter-AZPO). Timeline: within 24 hours.
2. **Assess safety.** If a safety flag is present, the triager conducts an immediate safety assessment. Safety-critical situations bypass the standard triage timeline and activate emergency protocols: separation of parties if needed, interim safety measures, and compressed process timelines. Timeline: immediate for safety-flagged reports.
3. **Evaluate triage dimensions.** The triager assesses the situation along six dimensions using the triage-assessment-template.yaml. **Severity**: is the harm isolated, patterned, or systemic? **Scope**: does the impact extend beyond the direct parties to the circle, the AZPO, or the ecosystem? **Parties**: who is involved, what are the power dynamics, and are authority holders implicated? **Root cause type**: is this a values conflict, a skill gap, an agreement breach, a communication breakdown, or a structural deficiency? **Urgency**: is the situation deteriorating, stable, or already resolved? **Safety**: are there ongoing risks to any participant?
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

When a participant exits the ecosystem, active triage assessments involving that participant are updated. If the **reporting party** exits, the triage record is retained and the underlying situation is assessed for community impact -- the person's departure does not erase the reported concern. If the **reported party** exits, the triage record is archived with the exit noted, and any ongoing community-level concerns continue through the appropriate process. If the **triager** exits, their active assessments are reassigned to another triager within 7 days. The 30-day wind-down period applies to in-progress triage conversations. Triage records involving exited participants remain valid governance artifacts.

## L. Cross-Unit Interoperability Impact

When a conflict involves participants from different AZPOs, the triage requires input from both AZPOs' facilitation pools. The triager is selected from neither AZPO (or from a neutral pool). The triage assessment must evaluate scope across both units and determine whether the conflict is interpersonal (Layer VI, handled jointly) or structural (Layer V, redirected). Cross-unit triage records are stored in both AZPOs' conflict registries with linked entries. Notification requirements: both AZPOs' stewards are informed that a cross-unit conflict has been triaged (without disclosing details). When one AZPO's triage process differs in configuration from another's, the more protective standard applies to cross-unit situations.

## OmniOne Walkthrough

Three conflicts arrive in the same week at OmniOne's SHUR Bali location, and each follows a different triage path.

**Scenario A -- Minor TH Disagreement.** Priya, a TH member, reports that she and Tomasz, another TH member, had a heated argument during a circle meeting about the interpretation of a shared agreement. Priya says she felt dismissed but acknowledges it was a one-time event and that she and Tomasz generally work well together. Triager Kai receives the report and assesses: severity is low (isolated incident, no ongoing pattern), scope is limited (two individuals, no broader impact observed), root cause is a communication breakdown (not a skill gap or values conflict), urgency is low (situation is stable), and safety is not a concern. Kai recommends Tier 1 -- Direct Dialogue with NVC support. Kai offers to arrange an NVC-supported conversation between Priya and Tomasz. Both agree. Kai creates triage record ET-SHUR-2026-012 and connects Priya and Tomasz with Ines, an NVC facilitator. The dialogue resolves the misunderstanding and no further escalation is needed.

**Scenario B -- Recurring AE Meeting Domination.** Facilitator Rafi flags a pattern: over the past two months, AE member Dmitri has consistently dominated steering meetings, speaking for 60% of available time, cutting off other speakers, and making decisions without the advice phase. Two AE members have privately told Rafi they feel unable to contribute. Kai assesses: severity is moderate (pattern, not isolated), scope affects the entire AE circle's functioning, root cause is a skill gap (Dmitri comes from a corporate background where directive leadership was expected -- this is not malice, it is a behavioral pattern from a previous organizational culture), urgency is moderate (circle functioning is degrading), and safety is not an immediate concern. Kai recommends Tier 2 -- Coaching Intervention. Kai notes that this is a skill gap, not a values conflict, so a harm circle would be inappropriate. Dmitri is approached with the recommendation. Kai creates triage record ET-SHUR-2026-013 and routes to coaching-intervention, specifying facilitation and collaborative decision-making as the target skills.

**Scenario C -- OSC Field Agreement Breach.** Three TH members file reports that Yara, an OSC member, made a significant decision about resource allocation without consulting the affected circles, violating the field agreement's commitment to the advice process. The decision redirected community funds in a way that disadvantaged the food production circle. Kai assesses: severity is high (agreement breach by an authority holder), scope is ecosystem-wide (OSC decisions affect all participants, and trust in governance is at stake), root cause is an agreement breach with potential structural factors (why did the OSC process not catch this?), urgency is high (the funding has already been redirected and the food production circle is affected now), and safety is not a physical concern but governance trust is at risk. Kai recommends Tier 3 -- Harm Circle for the direct parties (Yara and the three TH members who experienced the impact), plus Tier 4 -- Community Impact Assessment to examine whether the OSC decision-making process has a structural gap that allowed this breach. Kai documents the dual routing with rationale: the harm circle addresses the relational harm, while the community-impact-assessment addresses the systemic question.

Edge case: Yara, the OSC member, objects to the routing, arguing that the decision was within her authority and no harm occurred. Kai documents the objection but maintains the routing based on the six-dimension assessment -- the affected parties experienced harm regardless of Yara's intent, and the agreement breach is documented. Yara's participation in the harm circle is voluntary, but the community-impact-assessment proceeds regardless because it examines the structural question, not Yara's individual conduct.

The triage records (ET-SHUR-2026-012, -013, -014) are linked to their respective downstream processes and stored in the conflict registry for pattern analysis.

## Stress-Test Results

### 1. Capital Influx

A major funder, Henrike, is reported by two TH members for using financial leverage to suppress objections during an ACT consent phase. The triager receives the report and assesses severity as high -- financial coercion in governance is a direct capture vector. The triager routes to Tier 3 (harm circle) for the interpersonal harm and flags the situation for Layer VII safeguard review. Henrike's financial counsel contacts the triager suggesting that "formalizing this could affect the funding relationship." The triager documents this contact as a capital capture attempt within the triage record. The six-dimension assessment framework prevents financial status from influencing the routing: the triage-assessment-template.yaml requires written justification for each dimension, making it visible if severity is being minimized. The triage record becomes evidence if a pattern of funder-related under-routing is later detected. The structural safeguard is the reviewability of all triage records and the availability of second-triage requests from any affected party.

### 2. Emergency Crisis

A severe infrastructure failure at SHUR Bali forces 40 residents into shared temporary housing for two weeks. Interpersonal tensions spike and seven conflict reports arrive within four days. The triager applies emergency triage protocols: compressed timelines (assessment within 4 hours instead of 24), batch assessment of related reports (grouping the seven into clusters by root cause), and prioritization by safety flag. Three reports involve safety concerns and are routed immediately to emergency harm circles with compressed preparation. Two reports are stress-related communication breakdowns routed to NVC-supported direct dialogue. Two reveal a pre-existing pattern that the crisis intensified, routed to coaching-intervention with post-crisis follow-up. Emergency triage does not reduce the quality of assessment -- it compresses the timeline while maintaining the six-dimension framework. All emergency triage records are flagged for post-crisis review to determine whether the emergency routing was appropriate.

### 3. Leadership Charisma Capture

OmniOne's most visible founder is reported for pressuring participants in private meetings. The triager, who personally admires the founder, must assess the situation using the six-dimension framework rather than personal sentiment. Severity: high (pattern of behavior, power differential). Scope: ecosystem-wide (the founder's influence affects all governance processes). Root cause: values conflict (the founder believes their private guidance is helpful, but the affected parties experience it as pressure). The triage routes to Tier 3 -- harm circle. Social pressure emerges: other community members tell the triager the report is "probably a misunderstanding." The structural protection is the written, dimension-by-dimension assessment: the triager cannot minimize severity without documenting the justification, and that documentation is reviewable. If the triager does route to a lower tier, any affected party can request a second triage from an independent triager. The system does not depend on any single triager's immunity to charismatic influence.

### 4. High Conflict / Polarization

Two factions within an AZPO have been in escalating tension over governance philosophy -- one faction favors faster decision-making, the other insists on broader consultation. The tension has produced six conflict reports from both sides, each framing the other as "blocking progress" or "ignoring voices." The triager separates the interpersonal harm (personal attacks, exclusion from meetings) from the structural disagreement (governance philosophy). The interpersonal harm reports are triaged individually: some route to direct dialogue (isolated heated comments), one routes to a harm circle (a member was systematically excluded from three meetings). The structural disagreement is redirected to ACT as a governance proposal, not treated as a conflict. The triager references GAIA escalation levels to identify that the polarization has reached Level 3 (coaching) where a third solution could emerge. The triage demonstrates that not all disagreements are conflicts -- structural disagreements belong in governance processes, while interpersonal harm from how people pursue those disagreements belongs in conflict resolution.

### 5. Large-Scale Replication

OmniOne scales to 5,000 participants across 15 SHUR locations. Triage volume increases proportionally, and no single triager can handle all reports. The triage system scales through domain-scoped triager pools: each SHUR location maintains a pool of three or more trained triagers who handle local reports. Cross-location conflicts are triaged by a neutral triager from a third location. Pattern analysis scales through the triage record database: quarterly reviews of all triage records across locations detect systematic routing biases (one location consistently under-routing, another over-routing). AI agents assist by flagging reports that match patterns seen at other locations. The triage-assessment-template.yaml remains identical at all scales; what changes is the triager pool size and the cross-location coordination logistics. Triager training scales through a peer-learning model with standardized assessment exercises.

### 6. External Legal Pressure

A government labor inspection agency requests access to all conflict reports and triage records as part of an investigation into workplace conditions at SHUR Bali. The triage process distinguishes between the governance record (situation assessment, routing decision, rationale) and private details (individual statements, emotional disclosures). The governance record can be shared with legal authorities if required by applicable law -- the triage-assessment-template.yaml is designed to document the process without embedding private disclosures. If legal authorities mandate changes to the triage process (for example, mandatory reporting of certain types of harm), those requirements enter the ecosystem through agreement-creation as jurisdictional compliance. The triage skill itself does not change its assessment framework; it adds a jurisdictional compliance check for the specific legal requirement. Individual participants retain their right to engage with legal processes independently of the governance triage.

### 7. Sudden Exit of 30% of Participants

Fifteen of fifty OmniOne members exit within two weeks following a contentious ecosystem decision. Six active triage assessments are in progress. For each assessment, the triager reviews whether the exit changes the assessment: if the reported party exited, the triage is archived (the interpersonal conflict ceases, though community-level concerns may persist). If the reporting party exited, the triage assesses whether the reported concern has community implications beyond the departed individual. If the triager exited, the assessment is reassigned within 7 days. The mass departure itself may trigger new triage assessments as remaining members report distress, blame, or governance confusion. The triager pool recalculates based on current membership -- if the pool drops below minimum (three triagers per location), emergency cross-location coverage is activated. The triage process remains structurally identical; the membership change affects pool capacity and pattern analysis scope, not the assessment framework.
