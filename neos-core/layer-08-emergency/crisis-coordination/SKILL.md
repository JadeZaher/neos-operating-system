---
name: crisis-coordination
description: "Operate compressed decision timelines during an active emergency -- immediate, short-cycle, and deferred -- so the ecosystem acts quickly without abandoning structural accountability."
layer: 8
version: 0.1.0
depends_on: [pre-authorization-protocol, act-advice-phase]
---

# crisis-coordination

## C. Trigger Conditions

- **Emergency declaration**: when an emergency criterion's entry threshold is crossed and the circuit breaker transitions from Closed to Open
- **Concurrent emergency**: when a second emergency criterion triggers while the first is still active, requiring coordination across multiple emergency response tracks
- **Duration extension request**: when the initial maximum duration is approaching and conditions prevent safe reversion, prompting emergency ACT consent for extension

## D. Required Inputs

- **Active emergency declaration**: the specific criterion ID and entry data confirming the emergency threshold has been crossed
- **Activated pre-authorizations**: the specific role IDs, holders, authority scopes, and ceilings now active (from pre-authorization-protocol)
- **Crisis Operations Log template**: the structured log for documenting all emergency decisions (from `assets/crisis-operations-log-template.yaml`)
- **Compressed ACT timelines**: the pre-defined compressed decision timelines for emergency conditions (from `assets/compressed-act-timelines.yaml`)
- **Irreducible constraints**: the absolute boundaries that no emergency decision can cross (from pre-authorization-protocol `assets/irreducible-constraints.yaml`)
- **Auto-reversion timer**: the maximum duration from the triggering criterion, which begins counting at declaration

## E. Step-by-Step Process

1. **Confirm emergency declaration.** Verify that the entry threshold has been crossed using the data source and measurement method defined in the emergency criteria registry. Log the declaration with timestamp, criterion ID, entry data, and confirming authority in the Crisis Operations Log.
2. **Activate pre-authorized roles.** Notify all designated role holders. Primary holders confirm availability within 2 hours; if unavailable, alternates activate. Log all activations with timestamps in the Crisis Operations Log. Start the auto-reversion timer.
3. **Classify decisions into three timelines.** Every decision during the emergency falls into one of three categories:
   - **Immediate** (act now, report within 24 hours): decisions within the role holder's pre-authorized scope that directly address the active crisis. The role holder acts, then reports the decision and rationale to all ecosystem members within 24 hours.
   - **Short-cycle** (24-hour advice, emergency consent): decisions that exceed one role holder's scope or approach a ceiling. A compressed ACT process runs: 24 hours for advice from available members, followed by emergency consent (no reasoned objection within 12 hours = consent).
   - **Deferred** (outside emergency scope): decisions that do not address the active crisis are placed in the deferred decision queue for normal ACT process after the emergency concludes. Emergency authority cannot be used for deferred decisions.
4. **Tag every decision "emergency context."** All decisions made during the emergency are explicitly tagged as emergency-context decisions in the Crisis Operations Log. This tag means: the decision was made under compressed timelines and carries no precedent for normal operations. The tag ensures that post-emergency review can identify and evaluate every emergency decision.
5. **Maintain the Crisis Operations Log.** Every decision, communication, resource expenditure, and external interaction is logged in real time using the Crisis Operations Log template. The log includes: timestamp, decision-maker (role ID), decision description, timeline classification (immediate/short-cycle/deferred), authority scope reference, ceiling utilization, and any irreducible constraint checks.
6. **Monitor ceiling utilization.** As role holders make decisions, track cumulative spending and commitment against their hard ceilings. When a role holder reaches 80% of any ceiling, automatic notification goes to all ecosystem members. When a ceiling is reached, further decisions in that category require short-cycle emergency ACT consent.
7. **Process duration extensions.** If the maximum duration is approaching and exit criteria have not been met, the role holders can request a duration extension through short-cycle emergency ACT consent. The extension request must specify: why exit criteria have not been met, the proposed extension duration (maximum: equal to the original maximum duration), and updated exit criteria assessment. Extensions are logged in the Crisis Operations Log.
8. **Maintain communication cadence.** The Communications Coordinator issues status updates to all ecosystem members at least every 24 hours during the emergency. Updates include: current crisis status, decisions made since last update, ceiling utilization, auto-reversion timer status, and deferred decision queue contents.
9. **Monitor exit criteria continuously.** The role holders continuously assess whether exit criteria have been met. When exit criteria are met, the emergency-reversion skill activates immediately -- the role holders do not choose when to end the emergency; the criteria determine the end.
10. **Transfer to reversion.** When exit criteria are met or the auto-reversion timer expires, all emergency authority ceases. The Crisis Operations Log is closed and transferred to the emergency-reversion process. Deferred decisions enter normal ACT process.

## F. Output Artifact

A Crisis Operations Log following `assets/crisis-operations-log-template.yaml`. The log contains: emergency declaration data (criterion ID, entry data, declaration timestamp), activated roles (role IDs, holders, activation timestamps), complete decision record (every decision with timeline classification, authority reference, and ceiling utilization), communication log (all status updates issued), duration extension records (if any), exit criteria monitoring data, reversion trigger (exit criteria met or timer expired), and total resource expenditure. The log is published to all ecosystem members immediately upon emergency conclusion and is the primary input to emergency-reversion and post-emergency-review.

## G. Authority Boundary Check

- **Role holders** can only make decisions within their pre-authorized scope and under their defined ceilings -- crisis conditions do not expand authority
- **Immediate decisions** require reporting within 24 hours -- acting without reporting is a boundary violation logged for post-emergency review
- **Short-cycle ACT consent** requires participation from available members, not just role holders -- emergency authority does not replace collective governance, it compresses it
- **Deferred decisions** cannot be made under emergency authority -- attempting to make a non-crisis decision using emergency timelines is a boundary violation
- **The auto-reversion timer** is structural, not discretionary -- no role holder can pause, reset, or ignore the timer
- **Duration extensions** require emergency ACT consent -- role holders cannot unilaterally extend their own authority

## H. Capture Resistance Check

**Capital capture.** The Resource Coordinator's spending ceilings prevent emergency conditions from being used to redirect financial flows. All expenditures are logged in real time and published to all ecosystem members within 24 hours. A funder cannot use an emergency to pressure the Resource Coordinator into favorable spending decisions because the ceiling and scope prevent it, and the log makes every decision visible.

**Charismatic capture.** The three-timeline structure prevents a charismatic leader from using the emergency to make decisions outside the crisis scope. Deferred decisions cannot be processed under emergency authority, regardless of who advocates for them. The 24-hour reporting requirement for immediate decisions ensures that a charismatic role holder's decisions are visible to all members within a day.

**Emergency capture.** The auto-reversion timer is the core defense. From the moment of declaration, the clock is running toward the end of emergency authority. Duration extensions require emergency ACT consent -- they cannot be granted by the role holders themselves. The "emergency context" tag on every decision prevents emergency decisions from becoming precedent for normal operations. The crisis operations log creates a complete record that post-emergency review uses to evaluate whether authority was exercised within bounds.

**Informal capture.** All decisions are logged, classified, and published. Informal authority during the emergency is structurally visible because authorized decisions are logged while unauthorized decisions are not. If members follow informal direction over authorized role holder decisions, the discrepancy appears in the crisis operations log and is addressed in post-emergency review.

## I. Failure Containment Logic

- **Role holder makes a decision outside their scope**: the decision is logged as an unauthorized action. It stands if reversing it would cause greater harm, but the role holder bears the burden of justification in post-emergency review
- **Communication cadence missed**: if no status update is issued for 48 hours, automatic escalation notifies the OSC and all ecosystem members. Extended communication blackout triggers a welfare check on role holders
- **Ceiling exceeded**: the excess action stands but is flagged as a ceiling violation in the crisis operations log. Further decisions in that category require short-cycle ACT consent
- **Exit criteria met but role holder continues acting**: any decision made after exit criteria are met is unauthorized. The auto-reversion process activates immediately upon exit criteria being met, regardless of role holder actions
- **ACT consent cannot be gathered during compressed timeline**: if fewer than 3 ecosystem members are available for emergency consent, the decision is logged as "insufficient consent" and deferred if possible. If truly urgent, the role holder may act within their ceiling with the action flagged for post-emergency ratification

## J. Expiry / Review Condition

Crisis operations expire structurally: the auto-reversion timer ends all emergency authority at the maximum duration, and exit criteria trigger reversion when met. The Crisis Operations Log does not expire -- it is a permanent historical record. The compressed ACT timelines defined in `assets/compressed-act-timelines.yaml` are reviewed annually alongside the emergency criteria and pre-authorization reviews. If post-emergency review identifies systemic issues with timeline compression (too fast for adequate advice, too slow for genuine urgency), the timelines are recalibrated through normal ACT process.

## K. Exit Compatibility Check

When a role holder exits the ecosystem during an active emergency, their alternate assumes authority immediately. The exiting member's decisions remain in the crisis operations log as authorized actions. If no alternate is available, the OSC designates a temporary holder from the eligible member pool. The crisis operations log documents the transition. Post-emergency review evaluates the handover for continuity gaps. Members who exit during a non-emergency period have no impact on crisis-coordination -- their pre-authorization status is handled by the pre-authorization-protocol skill.

## L. Cross-Unit Interoperability Impact

During an emergency affecting one ETHOS, the Communications Coordinator's updates are published to all ecosystem members, providing cross-unit visibility into the crisis. Adjacent ETHOS' own pre-authorized roles may activate independently if the crisis affects their domain. Cross-ETHOS mutual aid (if pre-authorized through joint ACT process) operates through each ETHOS's own crisis-coordination process -- there is no unified command structure across ETHOS. The Crisis Operations Log format is identical across all ETHOS, enabling ecosystem-level analysis during post-emergency review. At federation scale, each ecosystem manages its own crisis operations independently, sharing situation reports through federation communication channels.
