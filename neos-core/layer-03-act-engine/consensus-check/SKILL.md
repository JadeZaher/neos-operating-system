---
name: consensus-check
description: "Verify whether consent or consensus exists among affected parties -- the reusable procedure for determining group agreement, handling quorum, absent members, and edge cases across both decision modes."
layer: 3
version: 0.1.0
depends_on: [proposal-creation, domain-mapping]
---

# consensus-check

## C. Trigger Conditions

- Another skill or process requires a formal check of whether affected parties agree on a question or proposal
- The act-consent-phase skill invokes this skill to execute the mechanical polling process
- The agreement-amendment skill invokes this skill with consensus mode for UAF changes
- A facilitator needs to formally record a group's position on any governance question

## D. Required Inputs

- **The question or proposal** being checked — the specific statement participants are agreeing or objecting to
- **The list of participants** who must be polled
- **The mode**: consent (no reasoned objection) or consensus (all actively agree)
- **Quorum requirements**: minimum participation threshold (default: 2/3 for consent mode, 100% for consensus mode)

## E. Step-by-Step Process

**Consent mode (default for most ACT decisions):**
1. Verify quorum: at least 2/3 of affected parties must participate. If quorum is not met, the check cannot proceed — reschedule.
2. Poll each participant individually. Acceptable responses:
   - **Consent**: "I have no reasoned objection."
   - **Stand-aside**: "I have concerns but will not block." Reason must be stated and recorded. Stand-asides do not prevent the proposal from proceeding.
   - **Objection**: "I have a reasoned, paramount objection." The objection must be grounded in harm to the circle's aim, not personal preference.
3. Determine result: consent is achieved if zero objections are recorded, regardless of the number of stand-asides. If any objection exists, consent is not achieved.
4. Record all positions in the consensus/consent record per `assets/consensus-record-template.yaml`.

**Consensus mode (OSC/Master Plan/UAF decisions):**
1. Verify attendance: ALL members of the deciding body must be present. No exceptions, no proxy. If any member is absent, the check cannot proceed — reschedule.
2. Poll each member individually. Acceptable responses:
   - **Agree**: "I actively agree with this proposal."
   - **Disagree**: "I do not agree." Reason must be stated.
3. Determine result: consensus is achieved ONLY if every member actively agrees. No stand-asides. No abstentions. One disagreement blocks consensus.
4. Record all positions.

**Handling absent members:**
- *Consent mode, absent with notice*: the member notified in advance that they cannot attend. Their absence is NOT counted as implicit consent — silence is not a position (per act-consent-phase Section H). They are not counted toward quorum, which means their absence makes quorum harder to achieve, not easier. The proposer may request a written position from a notified absentee; any position submitted in writing before the check is recorded explicitly in the consensus/consent record. If no written position is submitted, the member has no recorded position for that check. If persistent quorum failures result from recurrent absences, the invoking skill should re-scope the impacted-parties list to include only those who can reliably participate.
- *Consent mode, absent without notice*: not counted toward quorum. If their absence causes quorum failure, the check is rescheduled.
- *Consensus mode, absent with notice*: the check CANNOT proceed. The meeting is rescheduled to a time all members can attend. Consensus requires physical/virtual presence.
- *Consensus mode, absent without notice*: the check CANNOT proceed. The absent member is contacted and a new meeting is scheduled.

## F. Output Artifact

A consensus/consent record per `assets/consensus-record-template.yaml` containing: check ID, mode (consent/consensus), the question or proposal text, date, quorum requirement and whether it was met, each participant's identity, role, presence status, position, and stated reason (for stand-asides, objections, and disagreements), and the overall result.

## G. Authority Boundary Check

- The facilitator conducting the check has process authority only — they manage the polling order and recording but cannot influence positions or declare results that contradict the recorded positions.
- No participant can cast a position on behalf of another. In consent mode, written proxy is allowed for the consent position only (you can delegate "I consent" but not "I object on the following grounds"). In consensus mode, no proxy is allowed at all.
- The facilitator cannot reclassify an objection as a stand-aside or a disagreement as an agreement. Each participant's stated position is recorded as given.

## H. Capture Resistance Check

**Quorum manipulation.** Strategically ensuring certain participants are absent to change the quorum calculation. The quorum is calculated against the full affected-parties list, not just those present. Absent-without-notice members are not counted toward quorum, which means their absence makes quorum harder to achieve, not easier. This prevents exclusionary tactics.

**Pressure to change positions.** Between rounds (in skills that use multiple rounds, like act-consent-phase), participants may face pressure to change from objection to consent. The consensus-check records positions as stated at the time of polling. Position changes between rounds must be re-stated in the new round with documented rationale.

**False urgency.** Declaring emergency to compress the check process. Emergency timelines (from the invoking skill) may compress the scheduling window but do not modify the quorum requirements or the polling mechanics. A consensus check under emergency conditions follows the same structural rules.

## I. Failure Containment Logic

- **Quorum not met**: the check is rescheduled. The quorum threshold is never lowered. If quorum is repeatedly not met (3 consecutive attempts), the invoking skill is notified and the issue is escalated — persistent quorum failure may indicate the affected-parties list needs redefinition.
- **Consensus cannot be reached**: the existing state remains unchanged. The invoking skill receives a "not achieved" result and determines the next action (typically escalation to the next GAIA level).
- **Participant refuses to state a position**: in consent mode, refusal to state a position is treated as absence (not counted toward quorum). In consensus mode, refusal blocks consensus — the member must be present AND state a position.
- **Facilitator error** (miscounted positions, missed a participant): any participant can request a recount. The record is corrected before the result is finalized.

## J. Expiry / Review Condition

- Consensus/consent records do not expire independently — they are part of the invoking skill's lifecycle.
- The consensus-check skill itself is reviewed as part of the Layer III review cycle.
- If the quorum calculation rules prove inadequate (persistent failures or disputes), an amendment can be proposed through normal ACT process.

## K. Exit Compatibility Check

- If a participant exits after a check is recorded, their position stands for that check — it was their legitimate position at the time.
- If a participant exits before a scheduled check, they are removed from the participants list and quorum is recalculated.
- Mass exit between a consent check and the subsequent ACT phase may trigger a re-check if the composition has changed significantly.

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS consensus checks require each ETHOS to conduct its own check. The results are linked but each ETHOS's quorum is calculated independently.
- When a consensus check involves participants from multiple ETHOS, each participant's ETHOS affiliation is recorded.
