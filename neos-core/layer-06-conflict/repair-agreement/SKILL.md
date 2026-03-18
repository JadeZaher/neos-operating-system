---
name: repair-agreement
description: "Formalize conflict resolution outcomes into trackable, versioned governance agreements -- transform verbal commitments from harm circles, coaching, and dialogue into registered artifacts with timelines, follow-up schedules, and completion criteria."
layer: 6
version: 0.1.0
depends_on: [agreement-creation, agreement-registry, harm-circle]
---

# repair-agreement

## A. Structural Problem It Solves

Conflict resolution processes produce verbal commitments that evaporate within weeks. A participant agrees to change their behavior during a harm circle, but without a documented agreement specifying what they committed to, by when, and how follow-up will work, the commitment has no structural weight. The person harmed has no reference point to evaluate whether repair actually happened. The community has no record of what was agreed. When the same conflict recurs, there is no documentation to demonstrate that prior repair was attempted and either succeeded or failed. This skill transforms conflict resolution outcomes into proper governance agreements -- versioned, registered, trackable, and reviewable -- using the same infrastructure as any other agreement in the ecosystem. Repair agreements close the gap between "we talked about it" and "we have a structural commitment."

## B. Domain Scope

This skill applies to any conflict resolution outcome that produces commitments, across all ETHOS and governance contexts within the ecosystem. Repair agreements can originate from: harm circles, coaching interventions, NVC-facilitated dialogues, direct dialogue with mediator support, community impact assessment recommendations, or any other Layer VI process that produces actionable commitments. Repair agreement types include: behavioral commitments (personal conduct changes), structural changes (governance process modifications), resource restitution (returning or compensating misallocated resources), role adjustments (changes to authority or responsibility), relationship boundaries (agreed limits on interaction), and community practice changes (new norms adopted by a group). Out of scope: agreements that address structural inter-ETHOS disputes (those use Layer V agreement mechanisms), and therapeutic or clinical commitments (governance repair, not personal healing).

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

## OmniOne Walkthrough

Following a coaching intervention (documented in coaching-intervention), circle steward Dmitri at SHUR Bali has completed a coaching arc addressing his overly directive stewardship style. During the coaching outcome conversation, Dmitri, his coach Amara, and the two AE members most affected by the behavior -- Suki and Ravi -- agree on specific repair commitments. The coaching-intervention facilitator, Amara, transitions to the repair agreement drafting process.

Amara collects the verbal commitments made during the coaching outcome session. Dmitri agreed to three behavioral changes and one structural change. Amara classifies the agreement: primarily behavioral commitment with one structural change component.

Amara drafts the repair agreement using the template. The agreement reads:

Commitment 1 (behavioral): "I, Dmitri, agree to present all decisions affecting the AE circle's operations as proposals for circle consent rather than as announcements. Before each weekly steering meeting, I agree to circulate a written agenda with decision items marked as 'for consent' rather than 'for information.'"

Commitment 2 (behavioral): "I, Dmitri, agree to implement a 'pause and ask' practice: when I notice I am about to make a unilateral decision, I agree to pause, name the decision aloud, and ask the circle whether this requires a consent process or falls within my delegated authority."

Commitment 3 (behavioral): "I, Dmitri, agree to solicit input from at least two circle members before finalizing any resource allocation above 500 Current-Sees, and to document the advice received in the decision record."

Commitment 4 (structural change): "I, Dmitri, agree to propose through ACT an amendment to the AE circle's operating agreement that defines which decisions require full circle consent and which fall within the steward's delegated authority, with a clear boundary chart."

The follow-up schedule is set at 30, 60, and 90 days, with Amara as the follow-up facilitator. Completion criteria for each commitment are defined: for Commitment 1, evidence of written agendas with consent-marked items for at least 80% of meetings; for Commitment 2, self-reports and circle member feedback; for Commitment 3, documented advice records; for Commitment 4, the ACT proposal submitted within 60 days.

Edge case: at the 30-day check-in, Suki reports that Dmitri has consistently circulated agendas (Commitment 1 is on track) but made two resource decisions without consulting anyone (Commitment 3 is lagging). Amara facilitates a conversation. Dmitri acknowledges the lapses and attributes them to "time pressure" -- he reverted to old habits when deadlines loomed. Rather than declaring the agreement failed, Amara documents the partial progress, adjusts the support structure (Dmitri agrees to set a calendar reminder before resource decisions), and schedules an additional check-in at day 45. At the 60-day check-in, all behavioral commitments are on track and the ACT proposal for Commitment 4 has been submitted. At the 90-day review, all criteria are met. The repair agreement status is changed to "completed" and registered as RPR-SHUR-2026-004 in the agreement registry.

## Stress-Test Results

### 1. Capital Influx

A major donor to OmniOne is the subject of a repair agreement after a harm circle found that the donor used funding leverage to influence circle decisions. The repair agreement includes a commitment to disclose all funding conditions transparently in governance contexts. At the 30-day check-in, the donor has technically complied but has shifted to using informal one-on-one conversations to influence decisions -- a behavior not covered by the original agreement. The follow-up facilitator documents this as a new concern: the letter of the commitment is met but the spirit is violated. The facilitator initiates a supplementary repair conversation. The structural safeguard is the completion criteria: "the person harmed feels the repair is adequate" is a criterion, and if the person harmed reports ongoing influence attempts, the agreement is not completed regardless of technical compliance. The repair agreement's integration with the agreement registry means the pattern of donor influence is documented and available for Layer VII safeguard review.

### 2. Emergency Crisis

During a natural disaster, an emergency harm circle produces rapid repair commitments -- a participant who hoarded shared supplies during the crisis agrees to return the supplies and commit to equitable resource sharing. The repair agreement is drafted under emergency timelines (24 hours instead of 48) but the consent verification is not skipped. The commitments are concrete and measurable: return specific items within 24 hours, participate in a community resource-sharing protocol. The follow-up schedule is compressed: 7-day and 30-day check-ins instead of the standard 30/60/90 cycle. The emergency repair agreement is flagged for post-crisis review to assess whether the commitments were appropriate given the extraordinary stress conditions. If the post-crisis review finds that the commitments were excessive given the circumstances, the agreement can be amended with fresh consent from all parties.

### 3. Leadership Charisma Capture

A charismatic OSC member's repair agreement after a harm circle includes commitments to stop using private meetings to pressure participants. At the 30-day check-in, the follow-up facilitator -- who personally respects the OSC member -- reports "good progress" without documenting specific evidence against the completion criteria. The person harmed challenges the check-in record, noting that the OSC member held two private meetings during the period that felt pressuring. The structural protection activates: the completion criteria are documented in the agreement and the check-in must assess against those criteria specifically. The follow-up facilitator's subjective "good progress" assessment does not satisfy the requirement for evidence-based evaluation. A second check-in is conducted with the criteria explicitly reviewed, and the OSC member's private meetings are documented and assessed. Charisma cannot shortcut documented, criteria-based accountability.

### 4. High Conflict / Polarization

A deeply polarized ETHOS produces a repair agreement after a harm circle addressing personal attacks between faction leaders. The repair agreement includes mutual commitments: both leaders agree to refrain from personal attacks and to frame disagreements structurally. At the 30-day check-in, both parties accuse the other of violating the agreement while claiming they have complied. The follow-up facilitator applies the completion criteria: were there documented instances of personal attacks from either party? The facilitator reviews meeting records and consults witnesses. The evidence shows both parties reduced personal attacks but one party engaged in passive-aggressive behavior not covered by the original language. The facilitator documents the gap and drafts a supplementary agreement with more specific behavioral criteria. The repair agreement process handles polarization by anchoring to documented evidence and specific criteria rather than subjective perceptions of compliance. GAIA Level 4 coaching is referenced: the facilitator helps both parties see that their shared need for respectful governance creates common ground for the supplementary agreement.

### 5. Large-Scale Replication

At 5,000 participants across 15 locations, the repair agreement registry contains hundreds of active agreements. The system scales through registry-based management: each SHUR location manages its own repair agreements with standardized templates, and cross-location pattern analysis identifies systemic trends (are behavioral commitments in one area consistently unfulfilled, suggesting a cultural rather than individual issue?). Follow-up facilitator capacity scales with the facilitator pool at each location. AI agents assist by tracking follow-up schedules and sending automated reminders before check-in dates. The repair-agreement-template.yaml remains identical at all scales; what changes is the volume of active agreements and the value of aggregate pattern analysis. Repair agreement completion rates become a governance health metric: locations with low completion rates trigger community-impact-assessment to examine structural barriers to repair.

### 6. External Legal Pressure

A government authority requests access to repair agreements as part of a labor dispute investigation, arguing they constitute "binding workplace agreements." The repair agreement process maintains the distinction between governance repair and legal contracts: repair agreements are voluntary commitments within a governance framework, not employment contracts. The agreement registry can provide anonymized or redacted records if legally required, preserving the privacy of individual disclosures while demonstrating the governance process. If legal authorities mandate that certain repair commitments be formalized as legal contracts, those requirements enter through agreement-creation as jurisdictional compliance. Individual participants retain their right to seek legal remedies independently of the governance repair process -- the repair agreement does not waive legal rights.

### 7. Sudden Exit of 30% of Participants

A mass departure leaves eight active repair agreements in flux. Three agreements involve departed parties who made commitments: their behavioral commitments cease upon exit, their structural change proposals continue through ACT if already submitted, and any resource restitution is addressed during the 30-day wind-down. Two agreements involve departed persons harmed: the community-level commitments continue because they serve governance health. Three agreements involve departed follow-up facilitators: replacements are assigned within 14 days from the reduced facilitator pool. Scheduled check-ins are rescheduled but not skipped. All affected repair agreements are flagged for review under the changed membership conditions. The mass departure may reveal that some repair agreements addressed symptoms of the systemic issue that caused the departure, triggering community-impact-assessment. Existing repair agreement records remain valid governance artifacts regardless of membership changes.
