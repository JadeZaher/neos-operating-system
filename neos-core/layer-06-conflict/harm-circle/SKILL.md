---
name: harm-circle
description: "Convene a restorative circle when harm has occurred -- bring together the person harmed, the person who caused harm, and affected community members to understand impact, surface needs, and produce a consent-based repair agreement."
layer: 6
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, domain-mapping]
---

# harm-circle

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

When a participant exits the ecosystem, harm circle dynamics shift depending on role. If the **person harmed** exits, existing repair agreements remain valid -- the community's structural commitments continue even without the individual's presence, though personal reconciliation elements cease. If the **person who caused harm** exits, their unfulfilled repair commitments are documented as incomplete, and the community-level repair actions (structural changes, agreement amendments) continue. The exiting participant's statements in the harm circle record remain part of the governance record (they consented to the record at the time). No participant can be compelled to return for a harm circle after exit.

## L. Cross-Unit Interoperability Impact

When harm involves participants from different ETHOS, the harm circle requires co-facilitation or mutual recognition between the affected units. The convener is selected from neither ETHOS (or from a neutral facilitation pool if one exists). The resulting repair agreement is registered in both ETHOS' agreement registries with linked entries. Notification requirements: both ETHOS' stewards are informed that a cross-unit harm circle is convening (without disclosing private details). If the harm reveals a structural gap in cross-ETHOS interaction, the community-impact-assessment skill is triggered to address the systemic issue. Cross-ecosystem harm circles (between different NEOS ecosystems) follow the inter-ecosystem coordination protocol when Layer V is fully operational.
