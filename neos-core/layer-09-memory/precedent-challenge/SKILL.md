---
name: precedent-challenge
description: "Formally challenge an existing precedent when circumstances have changed or the original rationale no longer holds -- without this, precedent becomes inertia and governance cannot learn."
layer: 9
version: 0.1.0
depends_on: [precedent-search, decision-record, act-consent-phase]
---

# precedent-challenge

## C. Trigger Conditions

- A participant identifies an existing precedent whose rationale no longer applies due to changed circumstances
- A participant discovers a flaw in the original reasoning of a precedent that was not apparent at the time
- A precedent is producing harmful outcomes that conflict with ecosystem principles or active agreements
- Two existing precedents contradict each other and one must yield for governance coherence
- A demonstrably superior alternative to an existing precedent has been identified through experience or research
- A precedent search (per the precedent-search skill) surfaces a precedent that the searcher believes should be challenged

## D. Required Inputs

- **Precedent to challenge**: the specific decision record ID, with the holding and ratio decidendi quoted from the record
- **Challenge ground**: one or more of the defined grounds (changed circumstances, flawed rationale, harmful outcomes, conflicting precedent, better alternative) with evidence
- **Evidence**: documented support for the challenge -- data, changed conditions, identified flaws, or demonstrated harm
- **Proposed alternative**: what should replace the precedent if it is overruled (a new holding and rationale, or a modification to the existing holding)
- **Challenger identity**: who is filing the challenge (any active participant)
- **Precedent level of the challenged record**: determines the review body and process requirements

## E. Step-by-Step Process

1. **Identify the precedent.** The challenger uses the precedent-search skill to locate the decision record they intend to challenge. They read the full record, including the holding, ratio decidendi, obiter dicta, and dissent record, to understand the original decision's scope and reasoning. The challenger confirms the record is active (not already overruled or superseded).

2. **Select challenge ground.** The challenger selects one or more grounds from the defined list. **Changed circumstances**: the conditions that produced the original decision no longer exist -- the ecosystem has grown, structures have changed, or external conditions have shifted. **Flawed rationale**: the original reasoning contained an error that was not apparent at the time -- a factual assumption was wrong, a logical step was invalid, or information was missing. **Harmful outcomes**: the precedent is producing consequences that conflict with ecosystem principles, active agreements, or participant wellbeing. **Conflicting precedent**: two existing precedents contradict each other and cannot both stand. **Better alternative**: experience or research has revealed a demonstrably superior approach. The challenger must demonstrate a material basis, not merely disagreement with the outcome.

3. **Write the challenge brief.** The challenger produces a written challenge brief following `assets/challenge-brief-template.yaml`. The brief documents: the precedent being challenged (by decision record ID, with holding and ratio quoted), the specific ground for challenge with evidence, the proposed alternative (new holding and rationale), and the impact analysis (who is affected by the challenge and how). The brief must demonstrate that the challenge is substantive, not a relitigation of a settled question without new evidence.

4. **Submit the challenge.** The challenge brief is submitted to the body that originally made the decision. For routine-level precedent, the submitting domain's circle handles the challenge. For governance-level precedent, the original deciding body (or its successor) reviews. For constitutional-level precedent, the OSC reviews with a consensus process. If the original body no longer exists, the governance memory steward identifies the structural successor based on domain-mapping records.

5. **ACT review process.** The challenge enters an ACT process adapted for precedent review. **Advice phase**: those impacted by the precedent (identified from the decision record's affected_parties and the challenge brief's impact analysis) provide advice. The original participants in the precedent (if still active) have a particular perspective but no veto. **Consent phase**: the deciding body evaluates the challenge and determines the outcome: **Uphold** (the precedent stands, the challenge is dismissed with documented reasoning), **Modify** (the precedent's holding or scope is adjusted while its core reasoning is preserved), or **Overrule** (the precedent is replaced by the challenger's proposed alternative or a revised alternative that emerged during the ACT process).

6. **Document the outcome.** If the challenge is **upheld**, a challenge dismissal record is created as a decision record documenting: the challenged precedent ID, the grounds raised, the reasoning for dismissal, and the body's reaffirmation of the precedent. The original record is not modified. If the precedent is **modified**, a new decision record is created with the modified holding and ratio. The original record is marked "modified by [new record ID]" with a link. If the precedent is **overruled**, the overruling decision record must document: which precedent was overruled, why the original rationale no longer applies, and the new rationale. The original decision record is marked "overruled by [new record ID]" with a link. The original record is never deleted or edited -- the overruling annotation is appended.

7. **Apply semantic tags.** The outcome record (dismissal, modification, or overruling) receives semantic tags per the semantic-tagging skill. Tags include the challenged precedent's ID in related_precedents. The precedent_level of the new record is at least as high as the challenged precedent (overruling a governance-level precedent produces a governance-level record).

## F. Output Artifact

Either a challenge dismissal record (if the precedent is upheld) or an overruling/modification decision record (if the precedent is overruled or modified). Both follow the decision-record template with additional fields: challenged_precedent_id (the record being challenged), challenge_grounds (the grounds raised), challenge_outcome (upheld, modified, or overruled). The overruling record also includes: superseded_rationale (why the original reasoning no longer applies) and new_rationale (the replacement reasoning). All output artifacts are registered in governance memory through the decision-record skill's registration process. See `assets/challenge-brief-template.yaml` for the input artifact.

## G. Authority Boundary Check

Any active participant can initiate a challenge -- standing is universal. The deciding body is determined by the challenged precedent's level: routine challenges are decided by the domain's circle, governance challenges by the original deciding body or successor, and constitutional challenges by the OSC. The challenger has no special authority beyond initiating -- they participate in the ACT process as any other participant would. The deciding body cannot refuse to hear a formally submitted challenge with documented grounds; they must process it through ACT within 30 days of submission (14 days for routine, 30 days for governance, 60 days for constitutional). No individual can unilaterally dismiss a challenge. The governance memory steward ensures the process is followed but does not adjudicate challenges.

## H. Capture Resistance Check

**Capital capture.** Financial contributors cannot use challenges to overturn precedents that limit their influence. The challenge grounds must demonstrate material change, not merely financial preference. The ACT review includes advice from all affected parties, not just the challenger or funders. A donor who challenges a resource allocation precedent because it limits their spending authority must demonstrate changed circumstances, flawed rationale, or harmful outcomes -- not merely that the precedent is inconvenient for their financial plans.

**Charismatic capture.** A charismatic leader cannot use their social influence to ensure a challenge succeeds. The consent phase requires the deciding body to evaluate the challenge on its documented grounds, not on the challenger's personality. The challenge brief's written format ensures the argument stands on its own merits. If the same leader repeatedly challenges unfavorable precedents, the pattern of challenges is visible in governance memory and can itself be surfaced during advice phases.

**Emergency capture.** Crisis framing cannot be used to rush a precedent challenge through without proper review. Precedent challenges follow the standard ACT timeline, not emergency timelines, unless the challenged precedent is itself creating an emergency situation. If a challenge is genuinely urgent, the provisional emergency expediting rules apply, but the consent phase still requires all positions documented and dissent preserved.

**Informal capture.** Precedents cannot be informally overruled through practice drift -- participants ignoring a precedent does not overrule it. Only a formal challenge produces an overruling record. If participants notice that a precedent is being routinely ignored, this is grounds for a formal challenge (under "changed circumstances" or "better alternative"), not evidence that the precedent has already been overruled.

## I. Failure Containment Logic

- **Challenge brief is insufficient**: the deciding body can request additional evidence or clarification before proceeding to the consent phase. The challenge is not dismissed for procedural deficiency -- the challenger has 14 days to supplement their brief.
- **Deciding body does not process within timeline**: if the 30-day processing deadline passes, the governance memory steward escalates to the deciding body's parent circle or the OSC. The challenge remains open until processed.
- **Consent phase produces no clear outcome**: if the deciding body cannot reach consent on upheld, modified, or overruled, the challenge is escalated through the GAIA framework. At Level 4, a facilitator coaches the body toward a resolution. The precedent remains active during the challenge process.
- **Challenger withdraws**: the withdrawal is documented but does not prevent the deciding body from continuing the review if they believe the challenge has merit. Precedent health is a systemic concern, not solely the challenger's.
- **Simultaneous challenges**: if multiple challenges target the same precedent, they are consolidated into a single review process. All challenge briefs are presented together, and the deciding body evaluates all grounds simultaneously. The outcome addresses all challenges in a single decision record.

## J. Expiry / Review Condition

Challenge outcomes do not expire. A precedent that is upheld can be challenged again, but the new challenge must demonstrate different grounds or new evidence -- relitigation on the same grounds is not permitted unless the challenger can show that circumstances have changed since the previous challenge was heard. The challenge dismissal record serves as a reference point: subsequent challengers must distinguish their challenge from the previously dismissed one. Overruling records are subject to the same review schedule as any governance-level decision record. The precedent-challenge skill itself is reviewed when the governance memory steward identifies patterns that suggest the process is being used for capture (repeated frivolous challenges to delay governance) or is insufficiently accessible (valid challenges are not being filed because the process is too burdensome).

## K. Exit Compatibility Check

When a challenger exits during an active challenge process, the challenge remains open. The deciding body continues processing the challenge on its documented merits -- the challenge brief speaks for itself. If the exiting participant was the sole source of evidence, the deciding body notes this limitation and evaluates the challenge on available information. When a member of the deciding body exits, quorum rules apply per the act-consent-phase skill. If too many members have exited for quorum, the governance memory steward identifies the structural successor body. Challenge outcomes involving departed participants remain valid historical records. The departing participant's right to challenge expires with their active status, but challenges already submitted are processed to completion.

## L. Cross-Unit Interoperability Impact

A participant at one ETHOS can challenge a precedent established at another ETHOS if the precedent affects them (e.g., a cross-ETHOS resource allocation precedent). The deciding body is the body that made the original decision, regardless of which ETHOS the challenger belongs to. Cross-ETHOS challenges include participants from all affected units in the advice phase. When a precedent is overruled, the overruling record is visible across all ETHOS. If an ETHOS-specific precedent is overruled, only that ETHOS is directly affected, but other ETHOS may reference the overruling as persuasive precedent in their own governance. Cross-ecosystem precedent challenges (challenging a precedent in a different NEOS ecosystem) are not supported -- each ecosystem's governance memory is sovereign. Cross-ecosystem precedent influence is advisory only, handled through Layer V federation.
