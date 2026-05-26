---
name: act-consent-phase
description: "Run the Consent phase of the ACT process -- present the advised proposal to the deciding body, record each member's position (consent, stand-aside, or objection), integrate objections through structured rounds, and produce a consent record documenting the legitimate outcome."
layer: 3
version: 0.1.0
depends_on: [act-advice-phase, proposal-creation, domain-mapping]
---

# act-consent-phase

## C. Trigger Conditions

- The Advice phase closes with a completed advice log
- The proposer decides to proceed (rather than withdraw)
- The facilitator confirms the advice log is complete (all impacted party responses documented)

## D. Required Inputs

- The **proposal** as modified by advice integration
- The **advice log** from the act-advice-phase skill
- The **list of consent participants** (the deciding body — which may differ from the advice participants)
- The **consent mode**: consent (default) or consensus (for OSC/Master Plan/UAF decisions)
- A **neutral facilitator** who does not have a stake in the proposal outcome

## E. Step-by-Step Process

1. **Convene.** The facilitator convenes the deciding body and confirms quorum: 2/3 of affected parties for consent mode, ALL members for consensus mode.
2. **Present.** The facilitator presents the final proposal (post-advice) and summarizes the advice log, highlighting modifications made and objections not integrated.
3. **Round 1 — Positions.** Each participant states their position:
   - **Consent**: "I have no reasoned objection to this proposal."
   - **Stand-aside** (consent mode only): "I have concerns but will not block. My reason: [stated]." Stand-asides are recorded but do not prevent the proposal from proceeding.
   - **Objection**: "I have a reasoned, paramount objection. This proposal would harm our aim because: [stated]." Objections must be grounded in structural harm, not personal preference.
4. **If no objections** → consent (or consensus) is achieved. Record all positions and proceed to Step 7.
5. **If objections exist — Integration round.** The facilitator works with the objector(s) and proposer to find modifications that address the objection while preserving the proposal's core intent. This is the search for a "third solution" — not a compromise that weakens both positions, but a synthesis that addresses both concerns.
6. **Subsequent rounds.** The modified proposal is presented and all participants state their position again. Maximum 3 integration rounds for normal urgency (2 for emergency). After maximum rounds, if objections remain, the proposal escalates to the next GAIA level per the proposal-resolution skill.
7. **Record.** All positions from every round are recorded in the consent record per `assets/consent-record-template.yaml`. The final outcome (consented, consensus_reached, or escalated) is documented with the final proposal version.

## F. Output Artifact

A consent record following `assets/consent-record-template.yaml` containing: proposal ID, consent mode, weighting model, facilitator identity, date, quorum verification, each participant's position with stated reasons (for stand-asides and objections), integration round details (objections addressed, modifications made, round outcomes), final outcome, and the final proposal version number.

## G. Authority Boundary Check

- The **facilitator cannot override objections** or declare false consent. The facilitator manages the process (speaking order, time, round progression) but has zero authority over the outcome.
- If the **facilitator has a stake** in the proposal, a different neutral facilitator must be found before the consent round begins.
- **No one can consent on behalf of another** without written proxy delegation. In consent mode, proxy is allowed with documentation. In consensus mode, proxy is NOT allowed — every member must be present and state their own position.
- The facilitator ensures **every participant speaks** — silence is not counted as consent. Each person must actively state their position.
- Authority scopes are formally defined by the domain-mapping and role-assignment skills in Layer II (Authority & Role).

## H. Capture Resistance Check

**Charismatic pressure to withdraw objections.** Objections are recorded in writing before any discussion begins. Once recorded, an objection can only be resolved through an integration round — it cannot simply be "withdrawn under pressure." If an objector chooses to withdraw after integration, they must re-state their position in a separate round, ensuring the withdrawal is voluntary and documented.

**Social punishment of objectors.** The facilitator explicitly states at the start of every consent round that objections are a legitimate and valued structural contribution to governance. Objecting is not obstruction — it is the mechanism by which proposals improve. Any retaliatory behavior toward objectors is itself a violation of the UAF's conflict provisions.

**Urgency framing to skip integration.** Emergency timelines compress the number of integration rounds from 3 to 2 but CANNOT eliminate integration entirely. Even at maximum compression, at least one integration round must occur when objections are raised. A consent round with zero integration is structurally illegitimate.

**False consensus (silence as agreement).** Every participant must actively state their position. The facilitator polls each person individually. "I didn't hear any objections" is not consent — each person's "I consent" is recorded by name.

## I. Failure Containment Logic

- **Consent fails after maximum rounds**: the proposal escalates to GAIA Level 4 (Coaching) via the proposal-resolution skill. The consent record documents the unresolved objections for the coaching process.
- **Quorum not met**: reschedule within 7 days. If quorum is still not met after rescheduling, expand notification and attempt once more. The quorum threshold is NEVER lowered — it is safer to delay than to decide with insufficient representation.
- **Facilitator bias detected**: any participant can request facilitator replacement mid-round. The round pauses, a new facilitator is found, and the round restarts from the current position.
- **Partial consent in cross-circle proposal**: all affected circles must consent through their own consent rounds. One circle's consent does not bind another. If one circle consents and another does not, the proposal cannot proceed — it returns to advice with the objecting circle's concerns documented.

## J. Expiry / Review Condition

- The consent round must occur within 14 days of the advice phase closing (7 days for elevated urgency, 48 hours for emergency).
- If the consent deadline expires without a round being held, the proposal returns to the advice phase — the advice may be stale and must be refreshed.
- Consent records do not expire independently — they are part of the proposal's lifecycle and follow the proposal's status through to test or adoption.

## K. Exit Compatibility Check

- If a consent participant **exits mid-round**, their recorded position from that round stands. For subsequent rounds, quorum is recalculated based on remaining participants.
- If **mass exit drops quorum below minimum** during a consent round, the round is suspended. The facilitator documents the suspension and the proposal returns to advice phase for impacted-party reassessment.
- Consent records for completed rounds remain valid even if participants later exit — they reflected the legitimate positions at the time.

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS consent requires each affected ETHOS's deciding body to conduct its own consent round. One ETHOS's consent does not bind another.
- The consent records from each ETHOS are linked in the proposal tracking system. The proposal proceeds only when all affected ETHOS have reached consent.
