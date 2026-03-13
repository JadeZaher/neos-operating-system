---
name: consensus-check
description: "Verify whether consent or consensus exists among affected parties -- the reusable procedure for determining group agreement, handling quorum, absent members, and edge cases across both decision modes."
layer: 3
version: 0.1.0
depends_on: [proposal-creation, domain-mapping]
---

# consensus-check

## A. Structural Problem It Solves

Other skills reference "check for consent" or "verify consensus" without defining the mechanics. How exactly do you determine whether a group agrees? What happens when someone is absent? What counts as a quorum? What is the difference between "no one objects" and "everyone agrees"? This utility skill provides the reusable, precise procedure for both consent and consensus checks, ensuring that every skill that needs group agreement uses the same structural rules. It prevents the "we thought we agreed" ambiguity.

## B. Domain Scope

Any decision point in any skill that requires verification of group agreement. Called by: act-consent-phase (as its core mechanism), agreement-amendment (for UAF changes requiring OSC consensus), proposal-resolution (at GAIA Level 1 for in-circle consensus), and any future skill that needs a formal group agreement check. This is a utility skill — it does not stand alone as a governance process but is invoked by other skills.

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

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

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

- Cross-AZPO consensus checks require each AZPO to conduct its own check. The results are linked but each AZPO's quorum is calculated independently.
- When a consensus check involves participants from multiple AZPOs, each participant's AZPO affiliation is recorded.
- Federation: cross-ecosystem consensus checks follow each ecosystem's own rules, with results linked in both registries.

## OmniOne Walkthrough

The OSC needs to check consensus on a proposed UAF amendment that would add a new commitment about digital privacy practices. The OSC has 6 members. Consensus mode applies (UAF amendment = highest bar).

The facilitator, Yara (an AE member trained in process facilitation, not an OSC member herself), schedules the consensus check. At the scheduled time, 5 of 6 OSC members are present. Member #6, Desta, is traveling and sends a message: "I support the amendment but can't attend." Under consensus mode rules, Desta's remote support is NOT sufficient — consensus requires presence (physical or virtual) and an actively stated position. The check cannot proceed. Yara reschedules for two days later when Desta can join via video call.

At the rescheduled meeting, all 6 OSC members are present (Desta via video). Yara reads the proposed amendment text and asks each member to state their position. Members 1-4 agree. Member 5, Kofi, disagrees: "The proposed language is too broad — it would prevent any data sharing between circles, which would break our collaborative resource tracking system. I need the language narrowed to specify external data sharing only." Desta, who previously expressed support, now agrees with Kofi's concern after hearing it articulated.

Consensus is not achieved (2 disagreements). The result is recorded: 4 agree, 2 disagree (with reasons). The invoking skill (agreement-amendment) receives the "not achieved" result. The amendment proposer now has clear feedback: narrow the privacy commitment to external data sharing. They revise the amendment text and request a new consensus check at the next OSC meeting.

At the next meeting, all 6 are present. The revised amendment specifies "external data sharing with non-ecosystem entities." All 6 agree. Consensus achieved. The record documents both the failed check and the successful one, creating a complete deliberation trail.

## Stress-Test Results

### 1. Capital Influx

A donor who funds a significant portion of OmniOne's infrastructure is present during a consent check on a resource allocation proposal. Their "consent" carries the same structural weight as any other participant's — the consensus-check skill does not weight positions by financial contribution. The weighting_model field in the consent record is set to "equal" by default. If a future layer introduces configurable weighting (e.g., Current-See integration from Layer IV), the extensibility point exists in the template but is not active in this version. The donor's financial position creates social pressure but not structural privilege.

### 2. Emergency Crisis

An emergency consent check runs under compressed timelines — the scheduling window is 24 hours instead of the normal week. The quorum requirements do not change: 2/3 for consent mode, 100% for consensus mode. If consensus mode is required (UAF amendment during crisis), ALL members must still be present. The emergency may justify video attendance where in-person was the norm, but it does not justify proxy, absence, or lowered thresholds. If a consensus check cannot be conducted under emergency conditions (members unreachable), the amendment cannot proceed — the existing agreement stands.

### 3. Leadership Charisma Capture

A charismatic leader serves as facilitator for a consent check on their own proposal. This is a process violation — the facilitator must not have a stake in the outcome. Any participant can challenge the facilitator's neutrality and request a replacement. If the leader is both proposer and facilitator, the check is invalid. The skill requires a neutral facilitator precisely to prevent the person with the most social influence from controlling the polling process. A captured facilitator might subtly pressure participants, skip hesitant members, or misrecord positions — all prevented by the requirement of individual polling with written records.

### 4. High Conflict / Polarization

A consent check on a polarizing proposal reveals 6 consents, 2 stand-asides, and 3 objections. The objections are substantive and grounded. Consent is not achieved. The record documents all positions clearly, giving the invoking skill (act-consent-phase) the specific information needed for integration rounds. The polarization is visible in the record — both factions' positions are documented with equal weight. The consensus-check skill does not resolve the polarization; it accurately measures and records it for the integration process to address.

### 5. Large-Scale Replication

At 5,000 members, consent checks happen dozens of times weekly across 80 circles. Each check follows the same structural rules regardless of circle size. A 5-person circle has a 2/3 quorum of 4. An 80-person cross-circle body has a 2/3 quorum of 54. The mechanics scale linearly — larger groups take longer to poll but the rules are identical. The record template handles any number of participants. Persistent quorum failures in larger groups signal that the affected-parties list may be too broad and should be refined.

### 6. External Legal Pressure

A government subpoenas consensus check records as part of an investigation into the ecosystem's governance. The records are factual documents — they show who participated and what positions they took. The skill does not change its mechanics in response to external observation. If participants are concerned about their positions being disclosed, they may still exercise their full rights (consent, stand-aside, objection) — the structural protections exist within the governance system regardless of external scrutiny. The facilitator informs participants of any known disclosure requirements before the check begins.

### 7. Sudden Exit of 30% of Participants

After a mass departure, several scheduled consensus checks lose participants. For consent mode: quorum is recalculated against the current participant list. If the remaining participants meet the 2/3 threshold, the check proceeds. For consensus mode: if any departing member was part of the deciding body (e.g., an OSC member), the body's composition must be reconstituted before consensus checks can proceed. The departure of an OSC member during a UAF amendment process halts the consensus check until the vacancy is filled through the ecosystem's succession mechanism. This prevents consensus from being achieved by attrition.
