---
name: repair-agreement
description: "Formalize conflict resolution outcomes into trackable, versioned governance agreements -- transform verbal commitments from harm circles, coaching, and dialogue into registered artifacts with timelines, follow-up schedules, and completion criteria."
layer: 6
version: 0.1.0
depends_on: [agreement-creation, agreement-registry, harm-circle]
---

# repair-agreement

## C. Trigger Conditions

- A harm circle reaches the repair-actions round and produces agreed commitments
- A coaching intervention produces a coaching plan with specific skill-building commitments
- An NVC-facilitated dialogue surfaces requests that all parties consent to
- A community impact assessment produces governance change recommendations
- A direct dialogue with mediator support results in mutual commitments
- A prior repair agreement reaches its review date and requires renewal or modification

## D. Required Inputs

- **Originating process record**: the harm circle record, coaching plan, dialogue record, or assessment report that produced the commitments being formalized. Format: linked record ID.
- **Parties to the agreement**: all participants who are making or receiving commitments. Each party's role in the originating conflict is documented.
- **Specific commitments**: the concrete actions each party agrees to undertake. Each commitment must be observable, measurable, and time-bound.
- **Timeline**: start date, milestone dates, and completion date for each commitment.
- **Follow-up schedule**: dates for check-in conversations (typically 30, 60, and 90 days) and who conducts them.
- **Completion criteria**: how each party and the community will know the commitment has been fulfilled.
- **Consent verification**: documented consent from every party to every commitment. No party can have obligations imposed on them without their explicit consent.

## E. Step-by-Step Process

1. **Receive commitments from the originating process.** The repair agreement drafter (typically the facilitator of the originating process) collects the verbal commitments from the harm circle, coaching session, dialogue, or assessment. The drafter confirms each commitment with the person who made it. Timeline: within 48 hours of the originating process.
2. **Classify the repair agreement type.** The drafter categorizes each commitment by type: behavioral commitment, structural change, resource restitution, role adjustment, relationship boundary, or community practice change. Different types have different requirements. Behavioral commitments require observable indicators. Structural changes require a proposal through ACT. Resource restitution requires specific quantities and timelines. Role adjustments require role-assignment updates.
3. **Draft the agreement.** Using the repair-agreement-template.yaml, the drafter creates the formal agreement document including: all commitments with specific language, the timeline and milestones, the follow-up schedule, completion criteria for each commitment, and the link to the originating process record. The drafter uses "I agree to..." language for each commitment, attributed to the specific person.
4. **Review with all parties.** The drafter shares the draft agreement with every party for review. Each party confirms that the written agreement accurately reflects what they agreed to verbally. Parties may request wording adjustments that preserve the substance of the commitment. If a party objects to the written form of a commitment they verbally agreed to, the drafter facilitates a brief clarification conversation. Timeline: 3-5 days for review.
5. **Obtain consent.** Each party provides explicit, documented consent to the agreement. Consent means: "I understand these commitments and I agree to fulfill my part." No party signs under pressure. The drafter verifies consent in a separate conversation if there is any indication of social pressure.
6. **Register the agreement.** The finalized repair agreement is registered in the agreement registry using the standard agreement-creation process. The agreement receives a unique ID (format: RPR-[ETHOS]-[YEAR]-[NUMBER]), is linked to the originating process record, and is accessible to all parties and the follow-up facilitator.
7. **Schedule and conduct follow-up.** The follow-up facilitator (who may or may not be the same person as the originating process facilitator) conducts check-ins at the scheduled intervals. Each check-in assesses: is the commitment being fulfilled, is additional support needed, has the situation changed in ways that affect the agreement, and does the person harmed feel the repair is adequate. Check-in results are documented as amendments to the repair agreement record.
8. **Complete or renew.** When all completion criteria are met, the repair agreement status changes to "completed." If some criteria are unmet at the final review, the agreement is either renewed with adjusted commitments or escalated to the next conflict tier. Completion is confirmed by both parties, not unilaterally declared by the person who made the commitment.

## F. Output Artifact

A repair agreement following `assets/repair-agreement-template.yaml`, containing: unique agreement ID, date, originating process (type and record ID), all parties with roles, agreement type classification, each commitment with verbatim language and attributed party, timeline with milestones, follow-up schedule with designated facilitator, completion criteria, consent records, and status (active, completed, renewed, escalated). The agreement is registered in the agreement registry and linked to the originating conflict process record.

## G. Authority Boundary Check

- The **drafter/facilitator** has documentation authority. They translate verbal commitments into written form. They cannot add commitments that were not agreed to in the originating process, cannot modify the substance of commitments, and cannot declare completion without party confirmation.
- **No party** can impose obligations on a non-consenting party. Every commitment in the repair agreement requires the explicit consent of the person making the commitment. The person harmed defines what repair they need; they do not define what the other party must do without that party's consent.
- Repair agreements **cannot override existing agreements** without going through the agreement-amendment process. If a repair commitment conflicts with an active agreement, the conflict is resolved through ACT, not by the repair agreement unilaterally superseding.
- **Structural change commitments** (community practice changes, governance modifications) are documented in the repair agreement as intentions but must be formalized through the standard proposal-creation and ACT process. The repair agreement commits the party to proposing the change, not to implementing it unilaterally.
- The **follow-up facilitator** has assessment authority during check-ins but cannot unilaterally modify the agreement. Modifications require consent from all parties.

## H. Capture Resistance Check

**Capital capture.** A financially powerful party negotiates a repair agreement that protects their position -- for example, committing to "be more mindful" rather than concrete behavioral changes with observable indicators. The capture resistance mechanism is the completion criteria requirement: every commitment must have observable, measurable criteria. "Be more mindful" fails this test. The drafter requires specific language: "I agree to pause for 30 seconds before responding to objections in ACT phases, and to ask at least one clarifying question before stating my position." The person harmed's stated needs are the benchmark for adequacy, not what the person who caused harm is willing to offer.

**Charismatic capture.** A well-liked participant's repair agreement receives soft follow-up because the follow-up facilitator does not want to hold a popular person accountable. The structural safeguard is the documented completion criteria: the follow-up check-in assesses the criteria, not the facilitator's subjective impression. If the criteria are not met, the agreement is not completed regardless of the participant's social standing. The person harmed has access to the check-in records and can challenge an inadequate follow-up.

**Emergency capture.** Crisis conditions are used to rush through a repair agreement without proper review and consent. Even under emergency timelines, the consent verification step is mandatory. The timeline compresses (48-hour review instead of 3-5 days), but consent cannot be skipped. Emergency repair agreements are flagged for post-crisis review within 30 days.

**Informal capture.** "We already worked it out" is used to avoid formalizing a repair agreement, leaving the person harmed without documentation or follow-up. The skill requires that any conflict resolution process that produces commitments must also produce a repair agreement. The originating process facilitator is responsible for initiating the drafting process. If parties mutually agree that no formal agreement is needed, the facilitator documents this decision and the person harmed's explicit statement that they are satisfied.

## I. Failure Containment Logic

- **Party refuses to consent to the written agreement**: the drafter facilitates a clarification conversation to identify the discrepancy between the verbal and written commitments. If the party fundamentally retracts their verbal commitment, the repair agreement documents the retraction and the situation escalates to the next conflict tier.
- **Commitment is not fulfilled at follow-up**: the follow-up facilitator documents the unfulfilled commitment and initiates a graduated response: first, a reminder and support conversation; second, a formal check-in with the person harmed present; third, escalation to re-triage through escalation-triage with the repair agreement failure as new information.
- **Person harmed reports repair is inadequate**: the follow-up facilitator documents the inadequacy assessment and facilitates a conversation about what additional repair is needed. If the additional repair requires new commitments, a supplementary repair agreement is drafted. If the parties cannot agree, the situation escalates.
- **Agreement conflicts with an existing agreement**: the conflict is documented and routed to agreement-amendment through ACT. The repair agreement commitment is paused until the amendment process resolves the conflict.
- **Follow-up facilitator is unavailable**: a replacement is assigned from the facilitator pool within 7 days. Scheduled check-ins are not skipped; they are rescheduled within a 7-day window.

## J. Expiry / Review Condition

Repair agreements have a defined lifecycle: they are active from the consent date, reviewed at each scheduled check-in (typically 30, 60, and 90 days), and completed when all criteria are met. If a check-in is missed, the follow-up facilitator reschedules within 7 days -- missed check-ins trigger an escalation flag, not auto-invalidation. Repair agreements do not auto-expire. If all check-ins pass and criteria are met, the agreement status changes to "completed." If the agreement reaches its final review date with unfulfilled criteria, it is either renewed with modified commitments (requiring fresh consent) or escalated. Completed repair agreements remain in the registry as permanent governance records. Minimum review interval: 30 days.

## K. Exit Compatibility Check

When a participant exits the ecosystem, their repair agreement obligations are handled as follows. If the **person who made commitments** exits: behavioral commitments cease (they no longer participate in governance interactions), structural change commitments that were already proposed through ACT continue through the governance process without the individual, resource restitution commitments are addressed during the 30-day wind-down period. If the **person harmed** exits: the repair agreement remains valid -- community-level commitments continue because they serve the community's governance health, not only the individual's. If the **follow-up facilitator** exits: a replacement is assigned within 14 days. All repair agreement records survive participant exit and remain valid governance artifacts. The exiting participant retains their rights to original works and personal contributions.

## L. Cross-Unit Interoperability Impact

Repair agreements from cross-ETHOS conflicts are registered in both ETHOS' agreement registries with linked entries. The follow-up facilitator for cross-unit repair agreements is selected from neither ETHOS (or from a neutral pool). Notification requirements: both ETHOS' stewards are informed that a cross-unit repair agreement has been registered (without disclosing the specific commitments unless the parties consent). If a repair agreement includes structural change commitments affecting both ETHOS, the proposals must go through each ETHOS's ACT process independently. Cross-ecosystem repair agreements (between different NEOS ecosystems) follow the standard inter-ecosystem coordination protocol for agreement registration.
