---
name: act-advice-phase
description: "Run the Advice phase of the ACT process -- gather input from all impacted parties, document each piece of advice, and produce an advice log showing how the proposer integrated or responded to every input received."
layer: 3
version: 0.1.0
depends_on: [proposal-creation, domain-mapping]
---

# act-advice-phase

## A. Structural Problem It Solves

Without structured advice-gathering, decisions are made by whoever happens to be in the room — or worse, by whoever the proposer chooses to consult. This skill ensures all impacted voices are sought before consent is requested. It prevents the "nobody asked us" failure mode where affected parties discover changes after they have been decided. Every piece of advice is documented, and the proposer must account for how each input was addressed, creating a traceable record of inclusive deliberation.

## B. Domain Scope

Any proposal that has passed the synergy check and entered the ACT process. The advice phase applies regardless of proposal type (EcoPlan, GenPlan, amendment, resource request, policy change) and regardless of scope (circle-level, cross-circle, ecosystem-level). The depth and duration of advice-gathering scales with the proposal's scope and urgency.

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

An advice log following `assets/advice-log-template.yaml` containing: proposal ID, advice window dates, urgency level, all advice entries (advisor identity, role, AZPO, date, advice text, proposer response, integration status, rationale), non-respondent list with notification dates, summary of modifications, and proposer's overall integration narrative.

## G. Authority Boundary Check

- The proposer must demonstrably seek advice from ALL identified impacted parties, not just sympathetic ones. The facilitator verifies the advice-seeking list against the impacted parties list from the proposal.
- If an impacted party was missed (discovered during the advice window), the advice window must reopen for them — the minimum extension is 48 hours for normal urgency, 12 hours for emergency.
- Advice is non-binding: the proposer is not required to integrate every piece of advice, but they ARE required to document their response to each one.
- The facilitator cannot add or remove impacted parties unilaterally — changes to the impacted parties list require the proposer's agreement or a routing dispute resolution (default: broader scope).

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

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

- Cross-AZPO proposals require advice from representatives of each affected AZPO. The advice log includes the AZPO affiliation of each advisor.
- When a proposal affects multiple AZPOs, the advice window applies to all simultaneously — there is no sequential AZPO-by-AZPO process unless the AZPOs operate in significantly different time zones, in which case a 24-hour buffer is added.
- Federation extensibility: when two ecosystems share governance space, the advice phase can include advisors from both ecosystems with their ecosystem affiliation recorded.

## OmniOne Walkthrough

Suki, a TH member, has submitted a proposal to change the weekly TH meeting from a round-robin facilitation model to a trained-facilitator rotation. The proposal passed synergy check (no conflicting proposals found) and enters the Advice phase. Suki announces the proposal to all 35 TH members through the OmniOne governance channel, with a 7-day advice window.

Over the next week, 12 pieces of advice arrive. Jin, an AE member who frequently attends TH meetings, advises against the change: trained facilitators create a power imbalance because not everyone has equal access to training. Ola, a TH newcomer, supports the change: she felt lost and overwhelmed when it was her turn to facilitate last week, and the meeting suffered. An OSC observer, Reza, notes that this change might affect how TH decisions feed into OSC processes — if facilitators have more process authority, they might inadvertently filter which decisions reach the OSC.

Suki documents each response. She **partially integrates** Jin's concern: trained facilitators will rotate weekly and any TH member can request facilitator training at no cost — this addresses access inequality while maintaining quality. She **integrates** Ola's experience as evidence of the problem the proposal solves. She **partially integrates** Reza's OSC concern: the proposal now includes a clause that facilitators must forward all decision records to the OSC liaison unchanged, with no editorial discretion.

Three TH members who rarely attend meetings do not respond. Suki sends follow-up reminders at the midpoint. One responds (supporting the change). Two remain silent — documented as "notified, no response, follow-up sent."

Edge case: An AE member who is not on the TH roster but occasionally attends TH meetings contacts Suki saying they should have been consulted. The facilitator evaluates: is this person an impacted party? They attend occasionally but are not bound by TH process decisions. The facilitator determines they are not a required advisor but Suki voluntarily adds their input to the log as supplementary advice.

Suki compiles the advice log with all 12 entries, 2 non-respondent records, a summary of 3 modifications made to the proposal, and her decision to proceed to the Consent phase.

## Stress-Test Results

### 1. Capital Influx

A major OmniOne donor submits advice on a resource allocation proposal, arguing that the allocation should prioritize projects they have funded. The advice log records their input identically to every other advisor's — name, role, date, advice text. The proposer's response documents why the donor's preference is not integrated: resource allocation follows structural criteria defined in existing agreements, not funder preference. The donor's financial contribution does not elevate their advice above other participants'. The facilitator confirms all impacted parties were consulted, including those whose projects compete with the donor-funded ones. The complete advice log, visible to all participants, makes the equal treatment transparent. If the donor's advice has structural merit independent of their financial interest, it may be integrated on those grounds.

### 2. Emergency Crisis

A water contamination event at SHUR Bali requires an immediate proposal to reallocate emergency funds for water purification. The 24-hour emergency advice window opens. Of 15 impacted AE members, 8 respond within the window. The proposer documents all 8 responses and records the 7 non-respondents with notification timestamps. Despite the compressed timeline, each response receives a documented integration status. Two advisors recommend a different vendor — the proposer partially integrates by adding a clause for vendor evaluation within 48 hours post-adoption. The advice log is complete but abbreviated — full narrative responses are replaced by concise documented positions. The facilitator confirms that all impacted parties were notified through emergency channels. Non-response under emergency conditions is expected but does not reduce the consent quorum that follows.

### 3. Leadership Charisma Capture

A popular OmniOne leader submits a proposal and then selectively gathers advice only from their allies, ignoring three circle members known to be critical of the proposal. The facilitator catches the discrepancy during the impacted parties verification: the critics are on the impacted parties list from the synergy check but have not been notified. The facilitator reopens the advice window for 48 hours to include the missed parties. The leader objects — "they'll just slow things down." The facilitator's authority is process-based and non-negotiable: all impacted parties must be sought. The critics submit advice that contradicts the proposal. The leader must document their response to each critical input. The complete advice log, visible to all participants, reveals the initial selective consultation and its correction.

### 4. High Conflict / Polarization

A proposal to restructure OmniOne's onboarding generates deeply polarized advice. Half the advisors want stricter vetting; the other half want open access. The proposer faces contradictory advice that cannot be synthesized into a single modification. The proposer documents both positions honestly, notes the irreconcilable tension, and chooses a middle path with rationale. The advice log explicitly flags the polarization for the consent phase facilitator. During consent, the unresolved tension will likely surface as objections from both sides, which the integration rounds must address. The advice phase has done its job: it surfaced the conflict early, documented all positions, and ensured both factions had equal voice. The resolution will come through the consent phase's structural integration process, not through the proposer choosing a side.

### 5. Large-Scale Replication

At 5,000 members with 80 circles, a cross-circle proposal generates 150 pieces of advice from representatives across 12 affected circles. The advice log template handles scale through structured entries — each entry follows the same format regardless of volume. The proposer cannot individually respond to 150 entries with the same depth as 12. The skill accommodates this: the proposer may group related advice by theme and respond to themes, provided each individual entry is tagged with the theme it belongs to and no entry is left unaccounted for. The facilitator verifies completeness by cross-referencing the advice entries against the impacted parties list. The advice log summary synthesizes the 150 entries into major themes, minority positions, and the proposer's integration narrative.

### 6. External Legal Pressure

A government mandates public disclosure of all governance deliberations. An active advice phase contains sensitive internal discussions about resource allocation. The proposer and facilitator evaluate: the advice log is an internal governance document. Legal compliance may require disclosure to authorities but does not change the advice process itself. Participants are informed that their advice may be subject to external disclosure requirements, and they may adjust the specificity of their input accordingly. The structural integrity of the advice phase — comprehensive consultation, documented responses, inclusive notification — remains unchanged regardless of external observation. If participants are reluctant to provide honest advice under surveillance, this is flagged as an external pressure risk to be addressed at the ecosystem level.

### 7. Sudden Exit of 30% of Participants

During an active advice phase, 5 of 15 impacted parties exit OmniOne. Their already-submitted advice remains in the log. The impacted parties list is re-evaluated: are the remaining 10 still a representative cross-section? If the departed members represented a particular circle or perspective now absent, the facilitator may identify new impacted parties to fill the gap. The advice window may be extended by 48 hours for new parties. If the mass exit itself is related to the proposal (people leaving because they oppose the change), the facilitator documents this as a significant signal for the consent phase. The proposal may proceed with the reduced impacted parties list, but the consent phase quorum is calculated against the current (smaller) list, not the original.
