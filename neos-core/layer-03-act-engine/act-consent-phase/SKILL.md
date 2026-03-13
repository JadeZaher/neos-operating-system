---
name: act-consent-phase
description: "Run the Consent phase of the ACT process -- present the advised proposal to the deciding body, record each member's position (consent, stand-aside, or objection), integrate objections through structured rounds, and produce a consent record documenting the legitimate outcome."
layer: 3
version: 0.1.0
depends_on: [act-advice-phase, proposal-creation, domain-mapping]
---

# act-consent-phase

## A. Structural Problem It Solves

Without structured consent, decisions default to the loudest voice, the most persistent advocate, or informal authority. Silence is treated as agreement, objections are dismissed as obstructionism, and the outcome reflects social power rather than collective wisdom. This skill ensures every affected participant's position is formally recorded and that objections are structurally integrated rather than suppressed. It distinguishes between two decision modes — consent (no reasoned objection) and consensus (all actively agree) — and applies each where structurally appropriate.

## B. Domain Scope

Any proposal that has completed the Advice phase with a finalized advice log. The consent phase applies to all proposal types at all scope levels, with the consent mode (consent vs. consensus) determined by the proposal's scope and the affected agreements.

**Consent mode** (default): "No one present has a reasoned, paramount objection grounded in harm to the circle's aim." Stand-asides are permitted.
**Consensus mode** (OSC/Master Plan/UAF decisions): "All members of the deciding body actively agree." No stand-asides. All must be present.

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

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

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

- Cross-AZPO consent requires each affected AZPO's deciding body to conduct its own consent round. One AZPO's consent does not bind another.
- The consent records from each AZPO are linked in the proposal tracking system. The proposal proceeds only when all affected AZPOs have reached consent.
- Federation extensibility: when two ecosystems share governance space, each ecosystem conducts its own consent round under its own consent rules, and results are linked in both registries.

## OmniOne Walkthrough

The AE has completed the Advice phase on a proposal to reallocate 20% of the community development fund toward building a new maker space at SHUR Bali. Fifteen AE members are affected. Facilitator Mara — a trained facilitator with no stake in the proposal — convenes the consent round.

Mara confirms quorum: 11 of 15 AE members are present (11/15 = 73%, exceeding the 2/3 threshold). Consent mode applies (this is an AE-internal resource decision, not an OSC/Master Plan matter). Mara presents the proposal as modified during the advice phase, summarizing the 9 pieces of advice received and the proposer's integration decisions.

Round 1: Mara polls each participant individually. Nine members consent. One member, Dara, stands aside — she does not use the SHUR facilities but has no structural objection. She states her reason: "I'm not affected and have no opinion on the allocation." One member, Tomas, objects: "This reallocation would reduce my circle's (Education) quarterly budget by 30%, jeopardizing the mentorship program that serves 12 active mentees. The harm to Education's aim is direct and measurable."

Mara records all positions and initiates Integration Round 1. She facilitates a conversation between Tomas and the proposer, Kai. The core tension: the maker space serves the ecosystem's building capacity, but not at the cost of destroying an active educational program. The search for a third solution produces: phase the reallocation over two quarters (10% each quarter), giving Education two additional months to secure alternative funding from a different resource pool. This preserves the maker space timeline while protecting the mentorship program's continuity.

Mara presents the modified proposal. Round 2: 10 consent (including Tomas, whose Education circle concern is addressed by the phased approach). Dara stands aside again. Consent achieved.

The consent record is filed with: all 11 participants' positions from both rounds, the integration round details (Tomas's objection, the phased solution, the modification to the proposal), and the final proposal version (v1.2, reflecting advice and consent modifications).

Edge case: If Tomas had found the phased approach insufficient and a second integration round had produced another objection from a different member about maker space design priorities, the proposal would have one more round (Round 3) before escalating to GAIA Level 4 (Coaching) via proposal-resolution.

## Stress-Test Results

### 1. Capital Influx

A proposal to accept a large donation with conditions (donor gets naming rights and advisory board seat) reaches the consent phase. Several members object: the advisory board seat grants governance influence in exchange for money, violating the "Capital does not equal Power" principle. During the integration round, the proposer modifies: naming rights are accepted but the advisory board seat is replaced with a observer role without decision authority. One member still objects — even naming rights create implicit influence. The second integration round produces: naming rights for 5 years with the option not renewed automatically. The objector consents. The consent record documents every position and modification, making the donor's influence attempt and the structural response fully transparent.

### 2. Emergency Crisis

An emergency proposal to evacuate and temporarily relocate SHUR residents reaches consent with a 48-hour deadline. Facilitator convenes an emergency consent round with 8 of 12 affected residents (67%, above the emergency 50% minimum). The proposal is straightforward — relocation logistics with a 30-day auto-revert. Round 1: 7 consent, 1 objects (the relocation plan does not account for residents with mobility challenges). Emergency integration round: the proposer adds an accessibility clause with specific transport arrangements. Round 2: all 8 consent. Total time from convening to consent: 4 hours. The consent record notes the emergency conditions and flags the decision for post-emergency review.

### 3. Leadership Charisma Capture

A charismatic leader proposes restructuring circle authority in ways that would expand their own domain. During the consent round, two newer members raise objections but immediately face social pressure — the leader's allies suggest the objectors "don't understand the bigger picture." The facilitator intervenes: objections are recorded before any discussion, the facilitator explicitly validates the objectors' structural contribution, and the integration round must address the substance of the objections, not the objectors' understanding. The leader cannot declare that objections are invalid — only the integration process can resolve them. When one objector feels continued pressure and considers withdrawing, the facilitator requires the withdrawal to occur in a separate round with explicit re-statement, ensuring it is voluntary. The structural protections prevent charisma from overriding process.

### 4. High Conflict / Polarization

A deeply polarized proposal about resource allocation reaches consent with two opposing factions. Five members consent, three object from one faction (allocation is too aggressive), and two object from the other faction (allocation is too conservative). The integration rounds face competing objections that cannot be simultaneously resolved. Round 1 addresses the "too aggressive" faction with a phased approach — 2 of 3 now consent. Round 2 addresses the "too conservative" faction by adding a review trigger at 6 months — 1 of 2 now consents. Round 3 faces the final objector from the conservative faction who believes any reallocation is premature. The three rounds are exhausted and the proposal escalates to GAIA Level 4. The consent record documents every position from every round, providing the coaching process with complete information about each faction's concerns.

### 5. Large-Scale Replication

At 5,000 members, a cross-circle proposal affects 8 circles with a combined deciding body of 120 members. Each circle conducts its own consent round (not one massive 120-person session). The 2/3 quorum applies per circle. Seven circles reach consent. The eighth circle's consent round surfaces an objection that was not raised during advice. The cross-circle consent record links all 8 individual consent records. The proposal cannot proceed until the eighth circle resolves — the other seven circles' consent stands but does not bind the eighth. The facilitator network coordinates across circles to ensure consistent process application and shared understanding of integration round outcomes.

### 6. External Legal Pressure

A consent round on a privacy-related proposal occurs while a government investigation is requesting access to governance records. Participants are concerned that their objection positions might be disclosed to authorities. The facilitator addresses this: consent records are internal governance documents. Participants' right to object is a structural mechanism, not a political statement. The consent round proceeds normally — positions are recorded internally. If external disclosure is required by law, the ecosystem's legal compliance provisions apply, but the consent process itself is not modified by external pressure. Participants who are uncomfortable may stand aside rather than consent or object, but silence is still not an option — every participant must state a position.

### 7. Sudden Exit of 30% of Participants

During an active consent round with 15 members, 5 members exit OmniOne over the course of the week between Round 1 and Round 2 (the integration round was scheduled for the following meeting). Their Round 1 positions are recorded and stand. For Round 2, quorum is recalculated: 10 remaining members, 2/3 threshold = 7 must be present. If 7+ attend, the round proceeds. If the mass exit was prompted by the proposal itself, the facilitator documents this as a significant signal — a proposal that drives 33% of affected parties to exit rather than object through the process may need fundamental reconsideration. The facilitator may recommend the proposer withdraw and resubmit after understanding the exodus. The consent record documents the mid-process departure and its potential relationship to the proposal.
