---
name: act-advice-phase
description: "Run the Advice phase of the ACT process -- gather input from all impacted parties, document each piece of advice, and produce an advice log showing how the proposer integrated or responded to every input received."
layer: 3
version: 0.1.0
depends_on: [proposal-creation, domain-mapping]
---

# act-advice-phase

## C. Trigger Conditions

- A proposal transitions from synergy_check status to advice status in the proposal tracking system
- The proposal-creation skill has identified all impacted parties and set the urgency level
- The facilitator has confirmed that all required proposal fields are complete

## D. Required Inputs

- The **proposal document** (from proposal-creation) with all required fields complete
- The **list of impacted parties** identified during proposal creation and synergy check
- The **advice timeline** based on urgency: 7 days (normal), 3 days (elevated), 24 hours (emergency)
- The **communication channels** through which impacted parties will be notified

## E. Step-by-Step Process

1. **Announce.** The proposer (or facilitator) announces the proposal to all impacted parties through designated communication channels. The announcement includes: proposal summary, full text link, advice window dates, and how to submit advice.
2. **Open advice window.** The clock starts. Duration by urgency: 7 days (normal), 3 days (elevated), 24 hours (emergency).
3. **Gather input.** Each impacted party may submit advice in any accessible form — written, recorded audio/video, or in-person (documented by the facilitator). There is no required format; the bar is accessibility, not formality.
4. **Document responses.** The proposer reviews each piece of advice and records their response using one of three statuses:
   - **Integrated**: the advice is adopted and the proposal is modified accordingly
   - **Partially integrated**: some aspects are adopted, with written rationale for what was not
   - **Not integrated**: the advice is heard but not adopted, with written rationale explaining why
5. **Follow up on non-respondents.** For impacted parties who have not responded, the proposer sends one follow-up reminder at the midpoint of the advice window. Non-response is documented as "notified, no response" — it is not treated as consent or opposition.
6. **Close advice window.** At the deadline, the advice window closes. No late advice is accepted for the current round (it may inform future rounds if the proposal returns to advice after consent failure).
7. **Produce advice log.** The proposer compiles the complete advice log per `assets/advice-log-template.yaml`, including all entries, non-respondent documentation, a summary of modifications made, and the proposer's overall assessment.
8. **Decision point.** The proposer may choose to withdraw the proposal based on advice received (archived with reason) or proceed to the Consent phase with the modified proposal.

## F. Output Artifact

An advice log following `assets/advice-log-template.yaml` containing: proposal ID, advice window dates, urgency level, all advice entries (advisor identity, role, ETHOS, date, advice text, proposer response, integration status, rationale), non-respondent list with notification dates, summary of modifications, and proposer's overall integration narrative.

## G. Authority Boundary Check

- The proposer must demonstrably seek advice from ALL identified impacted parties, not just sympathetic ones. The facilitator verifies the advice-seeking list against the impacted parties list from the proposal.
- If an impacted party was missed (discovered during the advice window), the advice window must reopen for them — the minimum extension is 48 hours for normal urgency, 12 hours for emergency.
- Advice is non-binding: the proposer is not required to integrate every piece of advice, but they ARE required to document their response to each one.
- The facilitator cannot add or remove impacted parties unilaterally — changes to the impacted parties list require the proposer's agreement or a routing dispute resolution (default: broader scope).

## H. Capture Resistance Check

**Capital capture.** A wealthy advisor's input receives the same documentation treatment as any other participant's. The advice log does not weight entries by financial contribution, social status, or seniority. The proposer's response to each piece of advice is visible to all participants.

**Charismatic capture / selective consultation.** The proposer only consults allies and ignores critics. The facilitator's verification of the impacted parties list prevents this — if critics are on the list, they must be notified. The advice log's non-respondent section makes omissions visible.

**Urgency capture.** "Emergency" urgency declared to shrink the advice window and limit input. Emergency urgency requires declaration by 3 circle members acting jointly (not the proposer alone), and even the 24-hour window must include notification to all impacted parties.

## I. Failure Containment Logic

- **Impacted party does not respond within window**: documented as "notified, no response" in the log. Non-response is not consent — the consent phase will address participation separately. The proposer cannot claim silence as agreement.
- **All advice contradicts the proposal**: the proposer may still proceed but must document all contradicting input. The consent phase will likely surface these as formal objections — the advice log becomes evidence.
- **Contradictory advice** (advisor A says X, advisor B says not-X): the proposer documents both, chooses an integration path, and notes the contradiction explicitly for the consent phase facilitator.
- **Proposer does not respond to advice entries**: the facilitator flags incomplete entries before the advice window closes. An advice log with undocumented responses cannot proceed to consent.

## J. Expiry / Review Condition

- The advice window has a hard deadline based on urgency. No extensions for normal urgency unless new impacted parties are discovered.
- One extension allowed for elevated urgency (up to 3 additional days) if new impacted parties are identified during the window.
- Emergency timelines cannot be extended.
- If the proposer does not produce the advice log within 7 days of the window closing, the proposal stalls and the 30-day inactivity archive rule from proposal-creation applies.

## K. Exit Compatibility Check

- If the proposer exits during the advice phase, another impacted party may adopt the proposal per proposal-creation exit rules. The adopter inherits the advice already gathered and continues the process.
- If an advisor exits after submitting advice, their advice remains in the log — it was freely given and does not depend on ongoing participation.
- If enough impacted parties exit that the affected domain changes significantly, the facilitator may require the impacted parties list to be re-evaluated before proceeding to consent.

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS proposals require advice from representatives of each affected ETHOS. The advice log includes the ETHOS affiliation of each advisor.
- When a proposal affects multiple ETHOS, the advice window applies to all simultaneously — there is no sequential ETHOS-by-ETHOS process unless the ETHOS operate in significantly different time zones, in which case a 24-hour buffer is added.
