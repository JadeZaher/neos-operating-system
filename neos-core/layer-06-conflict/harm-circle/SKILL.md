---
name: harm-circle
description: "Convene a restorative circle when harm has occurred -- bring together the person harmed, the person who caused harm, and affected community members to understand impact, surface needs, and produce a consent-based repair agreement."
layer: 6
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, domain-mapping]
---

# harm-circle

## A. Structural Problem It Solves

Without a structured harm-response process, communities default to whoever has the most social capital, the loudest voice, or the willingness to escalate furthest. The person harmed either suffers in silence or leaves. The person who caused harm either faces informal mob justice or faces nothing at all. Bystanders lose trust in the governance system's ability to protect participants. This skill provides a repeatable, consent-based restorative process that centers the experience of the person harmed, maintains structural accountability, and produces a trackable repair agreement. It prevents vigilante justice, swept-under-the-rug dynamics, and the corrosive "nothing ever happens" cycle that kills community trust.

## B. Domain Scope

This skill applies to interpersonal harm within any ETHOS or across ETHOS within the same ecosystem. Harm includes actions that violate agreements, damage trust, cause emotional or material injury, or undermine a participant's ability to engage in governance. The scope covers harm between individuals, harm by an individual affecting a group, and patterns of harm revealed through repeated incidents. Out of scope: structural disputes between ETHOS about authority or resources (those belong to Layer V polycentric-conflict-navigation), legal matters requiring judicial intervention, and therapeutic needs beyond governance scope. The harm-circle addresses the governance dimension of harm -- restoring relationships and agreements -- not clinical treatment.

## C. Trigger Conditions

- A participant reports harm through the escalation-triage process and is routed to a harm circle
- A pattern of harm is identified by a facilitator, steward, or the affected person directly
- A breach of an existing agreement causes material or relational damage to one or more participants
- The escalation-triage skill determines that a situation exceeds the scope of direct dialogue or coaching
- An emergency safety concern requires immediate convening (compressed timeline per emergency rules)

## D. Required Inputs

- **Harm report**: a description of what happened, provided by the person harmed or a witness, including the specific impact experienced
- **Affected parties list**: the person harmed, the person who caused harm (if identified), and any community members directly affected
- **Convener identity**: the person calling the circle -- typically a trained facilitator, never the person harmed or the person who caused harm
- **Facilitation plan**: how the circle will be structured, including safety measures, speaking order, and time allocation
- **Safety assessment**: an evaluation of whether the person harmed can safely participate in the same space as the person who caused harm, with alternative arrangements if needed
- **Domain reference**: the ETHOS and circle context where the harm occurred, verified against domain-mapping

## E. Step-by-Step Process

1. **Receive harm report.** The convener receives the harm report through escalation-triage or direct request. The convener confirms the situation is within harm-circle scope (not a structural ETHOS dispute, not a coaching-eligible skill gap). Timeline: within 48 hours of report.
2. **Conduct preparation conversations.** The convener holds separate, private conversations with the person harmed, the person who caused harm (if willing), and key affected community members. Each conversation covers: what happened from their perspective, what impact they experienced, what they need, and whether they are willing to participate. Timeline: 3-7 days.
3. **Assess safety and willingness.** The convener determines whether all parties can safely participate. If the person who caused harm declines, the circle proceeds without them -- the process shifts to community acknowledgment and unilateral repair planning. If the person harmed declines, the circle does not proceed (their participation is never compelled). Timeline: concurrent with step 2.
4. **Design the circle.** The convener creates the facilitation plan: speaking order (person harmed speaks first), round structure, ground rules (no interrupting, no evaluative language, no pressure to forgive), time allocation, and physical/virtual arrangement. The convener shares the plan with all participants for consent before the circle.
5. **Facilitate the circle.** The circle follows three structured rounds. Round 1 -- What Happened: each participant describes what they observed and experienced, starting with the person harmed. Round 2 -- Impact and Needs: each participant describes how the harm affected them and what they need for repair. Round 3 -- Repair Actions: participants collectively identify concrete repair actions that address the stated needs. The convener holds process authority only -- they manage speaking order, time, and safety, but do not determine outcomes.
6. **Draft repair agreement.** The convener documents the agreed repair actions using the repair-agreement skill, including specific commitments, timelines, follow-up check-in dates, and completion criteria. All parties review and consent to the repair agreement before it is finalized.
7. **Register and schedule follow-up.** The repair agreement is registered per the agreement-registry skill. Follow-up check-ins are scheduled (typically at 30, 60, and 90 days). The harm circle record is created documenting the process (not private disclosures) and linked to the repair agreement.

## F. Output Artifact

A harm circle record following `assets/harm-circle-template.yaml`, containing: unique circle ID, date and location, convener identity, list of participants and their roles (person harmed, person who caused harm, affected community members, observers), summary of the process followed (rounds completed, modifications made), the repair agreement ID (linked to the separate repair agreement artifact), follow-up schedule, and any safety accommodations made. The record documents the process, not private emotional disclosures -- individual statements are included only with the explicit consent of the person who made them.

## G. Authority Boundary Check

- The **convener/facilitator** has process authority only: managing the circle structure, speaking order, time, and safety. The facilitator cannot determine the repair outcome, cannot declare what repair "should" look like, and cannot override any participant's stated needs.
- **No participant** can impose repair actions on a non-consenting party. All repair commitments require the explicit consent of the person making the commitment.
- The **circle cannot impose sanctions or punishments.** It produces repair agreements, not penalties. Removal authority belongs to Layer II and requires a separate process.
- **Authority scope verification**: before convening, the convener confirms via domain-mapping that the harm falls within the relevant ETHOS's domain and that the convener has facilitation authority in that domain.
- **OSC involvement** is required only when the harm involves an OSC member or affects ecosystem-level agreements. The OSC does not have override authority over circle-level harm processes.

## H. Capture Resistance Check

**Capital capture.** A financially influential participant who caused harm pressures the circle to minimize repair commitments by implying funding consequences. The circle process prevents this: the facilitator holds process authority independent of participants' financial status, repair actions are determined by the stated needs of the person harmed (not by what the person who caused harm is willing to offer), and any attempt to leverage financial position during the circle is documented as a capture risk and flagged for Layer VII safeguard review.

**Charismatic capture.** A well-liked community member who caused harm uses their social standing to generate sympathy and reframe themselves as the victim. The structured rounds prevent this: the person harmed speaks first in every round, the facilitator enforces the observation/impact/needs structure so that charm cannot substitute for accountability, and the repair actions must address the person harmed's stated needs regardless of community sentiment toward the person who caused harm.

**Emergency capture.** A crisis is invoked to rush through a harm circle without proper preparation conversations. Even under compressed emergency timelines, preparation conversations with the person harmed are mandatory (the timeline compresses from 3-7 days to 24-48 hours, not eliminated). The person harmed's safety assessment cannot be skipped. Emergency harm circles auto-trigger a 30-day follow-up review.

**Informal capture.** "We already talked about it and it's fine" is used to avoid a formal process when the person harmed has been socially pressured into dropping their report. The harm circle process requires explicit confirmation from the person harmed that they choose not to proceed -- the convener verifies this in a private conversation, not in the presence of the person who caused harm or their allies.

## I. Failure Containment Logic

- **Person who caused harm refuses to participate**: the circle proceeds as a community acknowledgment process. The person harmed still describes the impact, community members still identify needs, and a unilateral repair plan is created for the community's response (without imposing obligations on the absent party). The refusal is documented.
- **Person harmed withdraws mid-circle**: the circle pauses immediately. The convener checks in privately with the person harmed. The circle resumes only if the person harmed consents to continue. If they withdraw permanently, partial repair actions already identified are documented and the process transitions to community-level response.
- **No agreement on repair actions**: the circle documents the unresolved needs and escalates to the next tier per escalation-triage (typically a facilitated panel with additional community representation). The lack of agreement does not mean the harm is dismissed.
- **Safety concern during circle**: the convener has authority to pause or end the circle immediately if any participant's safety is at risk. The circle reconvenes only after the safety concern is addressed.
- **Facilitator bias detected**: any participant can request a different facilitator. The request triggers a facilitator change without requiring justification. The new facilitator reviews the preparation notes and restarts from the current round.

## J. Expiry / Review Condition

Harm circle records do not expire -- they are permanent governance records. The linked repair agreement has its own review schedule (typically 30/60/90 day check-ins with a final review at completion). If all repair agreement commitments are fulfilled, the repair agreement status changes to "completed." If the follow-up reveals that repair actions were insufficient, a new harm circle or escalation can be convened. Harm circle records are reviewed as part of community-impact-assessment when pattern analysis is triggered. Minimum review interval for active repair agreements: 30 days.

## K. Exit Compatibility Check

When a participant exits the ecosystem, harm circle dynamics shift depending on role. If the **person harmed** exits, existing repair agreements remain valid -- the community's structural commitments continue even without the individual's presence, though personal reconciliation elements cease. If the **person who caused harm** exits, their unfulfilled repair commitments are documented as incomplete, and the community-level repair actions (structural changes, agreement amendments) continue. The 30-day wind-down period applies to any active repair commitments. The exiting participant's statements in the harm circle record remain part of the governance record (they consented to the record at the time). No participant can be compelled to return for a harm circle after exit.

## L. Cross-Unit Interoperability Impact

When harm involves participants from different ETHOS, the harm circle requires co-facilitation or mutual recognition between the affected units. The convener is selected from neither ETHOS (or from a neutral facilitation pool if one exists). The resulting repair agreement is registered in both ETHOS' agreement registries with linked entries. Notification requirements: both ETHOS' stewards are informed that a cross-unit harm circle is convening (without disclosing private details). If the harm reveals a structural gap in cross-ETHOS interaction, the community-impact-assessment skill is triggered to address the systemic issue. Cross-ecosystem harm circles (between different NEOS ecosystems) follow the inter-ecosystem coordination protocol when Layer V is fully operational.

## OmniOne Walkthrough

Lena, a TH member at the SHUR Bali residency, has experienced a pattern over three months: during weekly circle meetings, Dayo, an AE member who also participates in her circle, consistently interrupts her proposals, dismisses her input as "not strategic enough," and once publicly said her ideas "waste the circle's time." Lena has tried direct dialogue (per Tier 1), but Dayo responded that he was "just being honest" and that Lena needed "thicker skin." After the third meeting where Dayo cut her off mid-sentence, Lena files a harm report through escalation-triage. The triage assessment routes the situation to a harm circle based on severity (pattern of behavior, not isolated incident), scope (affecting Lena's ability to participate and other circle members' willingness to speak up), and root cause (values conflict about respectful engagement, not a skill gap).

Facilitator Mika, a trained circle convener from a different ETHOS, is assigned to convene the harm circle. Mika holds preparation conversations over five days. In Lena's conversation, Lena describes feeling silenced and devalued, and states her need: she wants Dayo to acknowledge the pattern, commit to not interrupting, and let her finish speaking before responding. In Dayo's conversation, Dayo acknowledges he has been "direct" but says he did not intend harm -- he believes the circle's time is valuable and weak proposals waste it. Mika notes that intent does not negate impact. Mika also speaks with three other circle members who witnessed the pattern: Amina (TH), Rafi (AE), and Juno (TH). All three confirm the pattern and say it has made them less willing to propose ideas.

The circle convenes with six participants: Lena, Dayo, Amina, Rafi, Juno, and Mika (facilitating). In Round 1, Lena speaks first and describes the three specific incidents, the pattern of dismissal, and her experience of being silenced. Dayo listens without interrupting (a ground rule). When Dayo speaks, he acknowledges the specific incidents but frames them as "high standards." Amina, Rafi, and Juno each describe what they observed and the chilling effect on the circle.

In Round 2, Lena states her needs: acknowledgment that the behavior was harmful, a commitment to not interrupt, and a structural change so that all proposals get a minimum uninterrupted presentation time. Dayo initially resists -- he says acknowledgment "feels like an admission of guilt." Mika clarifies that acknowledgment of impact is not a legal admission; it is recognizing how actions affected another person. Dayo then acknowledges that his behavior silenced Lena, even though that was not his intent.

Edge case: during Round 3, Dayo proposes that Lena "also commit to making her proposals more concise." Mika flags this as a deflection that shifts responsibility to the person harmed. The circle's purpose is to repair the harm Dayo's behavior caused, not to negotiate Lena's communication style. Dayo withdraws the counter-request.

The circle produces a repair agreement: Dayo commits to (1) not interrupting any circle member mid-proposal, (2) reframing critical feedback as questions rather than dismissals, and (3) acknowledging publicly at the next circle meeting that his past behavior was harmful. The circle also recommends a structural change: all proposals receive a minimum 3-minute uninterrupted presentation window, to be proposed through ACT as a circle agreement. Check-ins are scheduled at 30, 60, and 90 days. The repair agreement is registered as RPR-SHUR-2026-007 in the agreement registry.

## Stress-Test Results

### 1. Capital Influx

A major donor to OmniOne, Karsten, is the subject of a harm report after he pressured a TH member, Elif, into withdrawing her proposal by threatening to redirect his funding to a different ETHOS. Elif files a harm report and the triage routes it to a harm circle. Karsten's financial counsel sends a message to the facilitator suggesting that "a formal process could jeopardize ongoing funding relationships." The facilitator documents this message as a capital capture attempt and proceeds with the circle. During preparation conversations, the facilitator explicitly states that financial contributions do not grant process exemptions. The circle convenes normally. In the repair round, Karsten's financial status is irrelevant to the repair actions -- the circle addresses Elif's stated needs (acknowledgment, commitment to not use funding as leverage, and a structural safeguard requiring that funding conditions be disclosed transparently in all proposals). The repair agreement includes a clause that any future attempt to leverage funding in governance decisions will be flagged as a capture risk for Layer VII review. The circle demonstrates that financial power does not insulate a participant from accountability.

### 2. Emergency Crisis

A severe earthquake damages the SHUR Bali compound, displacing residents into temporary shared quarters where personal boundaries are compressed. Within 72 hours, three harm reports emerge: two residents report that a third, under extreme stress, made threatening statements and destroyed shared supplies. The escalation-triage routes this to an emergency harm circle with compressed timelines. The facilitator conducts preparation conversations within 24 hours instead of the standard 3-7 days. The safety assessment is heightened -- the person who caused harm is housed separately during the process. The circle convenes within 48 hours of the reports. Consent is maintained: the person harmed chooses to participate, the person who caused harm agrees to attend. The circle acknowledges the extraordinary stress context while holding that stress does not erase the impact of harm. The repair agreement includes immediate behavioral commitments, a referral to support resources outside governance scope, and an automatic 30-day review. The emergency circle record is flagged for post-crisis community-impact-assessment to examine whether temporary housing arrangements need structural safeguards.

### 3. Leadership Charisma Capture

OmniOne's most respected founder, a person who conceived the Solutionary Culture framework, is the subject of a harm circle after three TH members report that the founder used private meetings to pressure them into withdrawing objections during ACT consent phases. The founder's social standing creates enormous pressure on the facilitator and circle participants to minimize the harm. The structural protections activate: the facilitator is selected from outside the founder's social orbit, the preparation conversations are conducted confidentially so that witnesses are not pressured to recant, and the circle's structured rounds ensure the person harmed speaks first regardless of the other party's status. During the circle, the founder attempts to reframe the situation as "mentorship" rather than pressure. The facilitator holds the observation/impact/needs structure -- the question is not what the founder intended but what impact the three members experienced. The repair agreement addresses the stated harm regardless of the founder's reputation. Community members who witnessed the circle later report that seeing the process hold firm against a high-status member increased their trust in the governance system.

### 4. High Conflict / Polarization

Two factions within an OmniOne ETHOS are deeply polarized over land use: one faction wants to expand food production and the other wants to preserve natural habitat. The tension has become personal -- members of each faction have made dismissive public comments about the other side's values, and two members report feeling personally attacked. The harm circle convenes not to resolve the policy dispute (that belongs in ACT) but to address the interpersonal harm caused by the polarized atmosphere. The facilitator references GAIA escalation levels to separate the structural disagreement (Level 3-4, policy coaching) from the interpersonal harm (Level 2, harm circle). In the circle, participants discover that their core needs are not as opposed as their positions suggest: the food production advocates need food security assurance, and the habitat advocates need ecological integrity. The repair agreement addresses the interpersonal harm (commitments to stop personal attacks, acknowledgment of impact) while routing the policy question to ACT with a facilitated advice phase. The circle demonstrates that addressing interpersonal harm first creates the conditions for productive structural disagreement.

### 5. Large-Scale Replication

OmniOne grows to 5,000 participants across 15 locations. Harm circles scale through domain-scoped facilitation: a harm circle at SHUR Costa Rica involves only the participants in that location's domain, not all 5,000 members. Each SHUR location maintains a pool of trained facilitators (minimum three per location) who can convene circles within their domain. Cross-location harm circles (a participant at SHUR Bali harmed by someone visiting from SHUR Portugal) require a neutral facilitator from a third location. The harm-circle-template.yaml structure remains identical at every scale -- what changes is the facilitation pool size and the cross-unit coordination complexity. Pattern detection across locations triggers community-impact-assessment at the ecosystem level: if three SHUR locations report similar harm patterns, the systemic analysis spans all three. The agreement registry tracks harm circle records with location metadata, enabling pattern queries without exposing private details. Facilitator training scales through a train-the-trainer model embedded in each ETHOS's capacity-building domain.

### 6. External Legal Pressure

Indonesian labor authorities investigate a complaint filed by a former OmniOne participant who claims the harm circle process violated their rights by "forcing" them into a mediation they did not consent to. The external legal pressure tests the voluntariness principle: the governance record shows that the participant explicitly consented to the circle (documented in the preparation conversation notes), that they were informed of their right to decline, and that the process produced a repair agreement signed by all parties. The facilitator's documentation of the consent process becomes the ecosystem's legal evidence. The legal inquiry does not modify the harm circle process -- NEOS conflict resolution operates within its governance domain while acknowledging that participants retain their individual legal rights. If the legal authority requires changes to the process (for example, mandatory written consent forms), those requirements enter the ecosystem through agreement-creation as jurisdictional compliance, not as modifications to the harm-circle skill itself. The distinction between governance repair and legal liability is maintained: the harm circle addresses relational and governance repair; legal matters proceed through external channels.

### 7. Sudden Exit of 30% of Participants

Following a contentious ecosystem decision, 15 of 50 OmniOne members exit within two weeks. Three active harm circles are in progress. For circles where the person harmed has exited: the community-level repair actions continue (structural changes, agreement amendments) even though the personal reconciliation element ends. For circles where the person who caused harm has exited: their unfulfilled repair commitments are documented as incomplete, and the community response proceeds without their participation. For circles where the facilitator has exited: a replacement facilitator is assigned from the remaining pool within 7 days. All active harm circle records and repair agreements are flagged for review under the reduced participant count. Quorum for follow-up check-ins recalculates based on current membership. The harm circle process itself does not change -- the structural process is resilient to membership changes because it is role-based (person harmed, person who caused harm, affected community, facilitator), not personality-based.
