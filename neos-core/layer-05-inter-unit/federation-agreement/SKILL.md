---
name: federation-agreement
description: "Draft, negotiate, and ratify bilateral or multilateral agreements between ETHOS -- defining terms, shared protocols, dispute handling, and graduated engagement tiers -- through each ETHOS's own ACT process."
layer: 5
version: 0.1.0
depends_on: [cross-ethos-request, agreement-creation, act-consent-phase]
---

# federation-agreement

## C. Trigger Conditions

- Two or more ETHOS decide to formalize an ongoing coordination relationship
- An existing informal cross-ETHOS arrangement needs structural grounding
- Cross-ETHOS request volume between ETHOS warrants standing protocols
- ETHOS want to define or change their engagement tier
- A shared resource stewardship arrangement requires a broader relationship framework

## D. Required Inputs

- **Participating ETHOS** -- all units involved in the agreement (mandatory)
- **Agreement type** -- bilateral cooperation, multilateral protocol, service-level, mutual recognition, or graduated engagement compact (mandatory)
- **Proposed terms** -- the substantive commitments each ETHOS would make (mandatory)
- **Negotiation mandate from each ETHOS** -- what each ETHOS's negotiators can and cannot agree to (mandatory)
- **Desired engagement tier** -- observe, cooperate, federate, or integrate (mandatory)
- **Proposed review schedule** -- when the agreement will be reviewed (mandatory)

## E. Step-by-Step Process

1. **Initiate.** One or more ETHOS propose formalizing their relationship through a cross-ETHOS request. The proposal states the desired agreement type and engagement tier.
2. **Define negotiation mandates.** Each participating ETHOS defines what its negotiators can agree to, explore, and commit to -- and what requires the full ETHOS's consent before the negotiator can accept. The mandate is approved through each ETHOS's own ACT process.
3. **Parallel advice phases.** Each ETHOS runs an internal advice phase to gather member input on the proposed terms. Advice is shared across ETHOS to inform negotiation.
4. **Collaborative drafting.** Negotiators from all participating ETHOS meet to draft the agreement using `assets/federation-agreement-template.yaml`. Drafting may be collaborative (simultaneous) or sequential (each ETHOS adds provisions). Disagreements are documented and negotiated within mandate limits.
5. **Mandate check.** If negotiation produces terms outside any negotiator's mandate, that negotiator pauses and returns to their ETHOS for mandate expansion or modification. No negotiator may accept terms beyond their mandate.
6. **Each ETHOS ratifies through consent.** The finalized draft is presented to each participating ETHOS for an independent consent round. If one ETHOS's consent fails, the process returns to Step 4 with the objecting ETHOS's concerns documented.
7. **Mutual registration.** The ratified agreement is registered in every participating ETHOS's agreement registry with linked entries and mutual ratification records.
8. **Review schedule begins.** The agreement's review cycle activates per the agreed schedule.

## F. Output Artifact

A federation agreement following `assets/federation-agreement-template.yaml`, containing: agreement ID, type, participating ETHOS, engagement tier, substantive terms, each ETHOS's negotiation mandate records, ratification records from each ETHOS, review schedule, amendment procedures, exit terms, and dispute resolution path. Registered in all participating ETHOS' registries.

## G. Authority Boundary Check

- **Negotiators operate within mandates.** Each ETHOS's negotiators can only agree to terms within their documented mandate. Commitments made outside the mandate are void until ratified by the home ETHOS.
- **No ETHOS can impose terms** on another. Every term requires mutual consent through each ETHOS's own ACT process.
- **Ratification is independent.** Each ETHOS runs its own consent round. One ETHOS's ratification does not bind another.
- **Amendment authority** follows the same process as original ratification -- all participating ETHOS must consent.
- **Engagement tier changes** require formal amendment, not unilateral declaration.

## H. Capture Resistance Check

**Power asymmetry.** A wealthier or larger ETHOS dictates terms during negotiation, leveraging its size to pressure smaller ETHOS into unfavorable provisions. Resistance: negotiation mandates are defined internally before negotiation begins, preventing mandate creep under social pressure. Each ETHOS's consent round evaluates terms independently. Size asymmetry is documented as context in the advice phase.

**Urgency pressure.** One ETHOS rushes ratification by framing delay as threatening the relationship. Resistance: each ETHOS controls its own consent timeline. No ETHOS can set deadlines for another's internal process. Urgency is documented but does not compress another ETHOS's consent process.

**Precedent capture.** Early agreements become de facto standards that constrain later-joining ETHOS. Resistance: new ETHOS joining an existing multilateral agreement negotiate their own terms and may propose amendments as a condition of joining. No ETHOS is bound by agreements it did not ratify through its own process.

**Informal capture.** Negotiators develop personal relationships that produce informal understandings outside the documented agreement. Resistance: only documented terms in the registered agreement are binding. Informal understandings have no governance standing.

## I. Failure Containment Logic

- **Negotiation stalls:** Any ETHOS may pause or withdraw from negotiation with documentation. Withdrawal does not create an obligation. The remaining ETHOS may continue with a reduced participant set.
- **Ratification fails in one ETHOS:** The process returns to drafting to address that ETHOS's concerns. Other ETHOS' prior ratification holds but may require reaffirmation if more than 90 days pass.
- **Mandate exceeded:** Commitments made outside mandate are void. The affected ETHOS runs an internal review and either expands the mandate or the term is removed from the draft.
- **Agreement violated:** The aggrieved ETHOS may invoke dispute resolution per the agreement's terms, escalating to polycentric-conflict-navigation if needed.
- **Engagement tier mismatch:** If one ETHOS wants to deepen engagement but another does not, the agreement reflects the lower tier. Deeper engagement requires mutual consent.

## J. Expiry / Review Condition

- **Review schedule:** Configurable per agreement. Bilateral cooperation agreements default to annual review. Multilateral protocols default to 18-month review. Minimum: 6 months.
- **Missed review:** Agreement enters a 60-day grace period. After 60 days, status changes to "under review" in all registries. The agreement remains operational but cannot be cited as authority for new commitments until reviewed.
- **Amendments:** Follow the same multi-party ratification process as the original agreement. Minor clarifications may use a simplified consent process if all participating ETHOS agree.
- **Federation agreements do not auto-expire** unless explicitly time-limited at ratification.

## K. Exit Compatibility Check

- **Unilateral exit:** Any ETHOS may exit a federation agreement with documented notice (default: 90 days). The exit does not invalidate the agreement for remaining participants.
- **Multilateral impact:** When one ETHOS exits a multilateral agreement, the remaining ETHOS convene a review to assess whether the agreement still functions. If not, they may wind down or restructure.
- **Obligations cease:** The exiting ETHOS's commitments under the agreement end at the close of the notice period. In-progress commitments receive a 30-day wind-down.
- **No retaliation clause:** Exit from a federation agreement does not trigger penalties or reduced standing in other agreements. Each agreement is structurally independent.

## L. Cross-Unit Interoperability Impact

Federation agreements are the primary mechanism for formalizing inter-ETHOS relationships. They reference cross-ethos-request (how the initial proposal was made), shared-resource-stewardship (how shared resources are governed within the federation framework), and inter-unit-liaison (how ongoing coordination roles are maintained). Changes to federation agreements must be announced to all participating ETHOS' registries simultaneously. New ETHOS joining a multilateral agreement negotiate and ratify on the same terms as the original parties.

### Graduated Engagement Tiers

Federation agreements operate within four engagement tiers (see `assets/engagement-tiers.yaml`):

- **Observe:** Mutual acknowledgment. No commitments. ETHOS recognize each other's existence and legitimacy. Default tier for new ETHOS relationships.
- **Cooperate:** Case-by-case collaboration through cross-ETHOS requests. No standing commitments. Each interaction is individually authorized.
- **Federate:** Formal agreement with shared protocols, regular coordination, and designated liaisons. Standing commitments and shared governance structures for specific domains.
- **Integrate:** Deep structural integration with shared governance bodies, joint decision-making on defined domains, and pooled resources. Highest commitment tier.

Transitions between tiers require a federation agreement amendment ratified by all participating ETHOS.
