---
name: safeguard-trigger-design
description: "Design, install, and maintain measurable safeguard triggers -- automatic thresholds that activate specific governance interventions when governance health indicators cross defined boundaries."
layer: 7
version: 0.1.0
depends_on: [capture-pattern-recognition, act-consent-phase, agreement-creation]
---

# safeguard-trigger-design

## C. Trigger Conditions

- **New ecosystem setup**: when an ecosystem configures its initial governance structure, the starter trigger set is presented for customization and installation through the ACT process
- **Post-assessment recommendation**: when a Capture Assessment Report recommends activating or installing a new safeguard trigger
- **Participant proposal**: any ecosystem member proposes a new trigger through the ACT process, with the trigger design following this skill's framework
- **Trigger review date**: when an existing trigger reaches its scheduled review date, the trigger is re-evaluated through the ACT process (renewal, modification, or retirement)
- **Post-emergency review**: following an emergency declaration, all emergency-related triggers are reviewed for adequacy

## D. Required Inputs

- **Indicator definitions**: the governance health indicators from `assets/indicator-definitions.yaml` (governance-health-audit) that the trigger will monitor
- **Current trigger registry**: all existing active triggers for the scope, to prevent duplication and ensure coherence
- **Capture signature data**: the four capture type profiles from capture-pattern-recognition, to ensure triggers map to known capture patterns
- **ACT process access**: the trigger must be designed and installed through the Advice-Consent-Test decision protocol (Layer III)
- **Stakeholder input**: affected participants within the trigger's domain, who will provide consent during installation
- **Safeguard action definitions**: bounded intervention descriptions that specify what happens when a trigger fires

## E. Step-by-Step Process

1. **Identify the governance risk.** The trigger designer specifies which capture type or governance health risk the trigger addresses, referencing capture-pattern-recognition signatures. Each trigger maps to at least one specific capture type. Timeline: 1-3 days for research and design.
2. **Define the trigger anatomy.** The designer specifies all five components: (a) the monitored indicator (which GHI or capture confidence score), (b) the threshold value (the specific measurable criterion that fires the trigger), (c) the safeguard action (the bounded intervention that activates), (d) the notification recipients (who is informed when the trigger fires), (e) the review timeline (when the trigger itself is reviewed for continued relevance). The safeguard action must be specific and bounded -- "initiate mandatory leadership review" not "fix the problem."
3. **Evaluate the starter set.** For new ecosystems, review the recommended starter triggers (8 minimum, 2 per capture type) in `assets/trigger-registry-template.yaml`. Customize thresholds to the ecosystem's context. For existing ecosystems, evaluate whether the proposed trigger fills a gap in the current registry.
4. **Enter ACT Advice phase.** The trigger design is shared with affected stakeholders for advice per the act-advice-phase skill. Advisors evaluate: Is the threshold appropriate? Is the safeguard action proportionate? Are the notification recipients correct? Does the trigger overlap with existing triggers? Timeline: 5-10 days (default).
5. **Enter ACT Consent phase.** The trigger is presented for consent per the act-consent-phase skill. Consent means "no reasoned objection." Objections must reference specific structural concerns (e.g., "this threshold is too sensitive and will produce false positives" or "this safeguard action exceeds the intended scope"). Timeline: 5-7 days (default).
6. **Install the trigger.** Upon consent, the trigger is registered in the Safeguard Trigger Registry with a unique ID, installation date, and status "active." The trigger's monitoring begins at the next data collection cycle. Installation is logged as a governance event visible to all ecosystem members.
7. **Monitor and activate.** When the independent monitor's data collection shows that a trigger's threshold has been crossed, the trigger fires automatically. The safeguard action activates, notification recipients are informed, and the activation is logged in the trigger registry with the specific data that caused activation.
8. **Execute safeguard action.** The defined safeguard action is carried out within its stated bounds. Safeguard actions are interventions (review processes, escalation notices, diversity assessments), not punishments. The action initiator is the designated role in the trigger definition, not the monitor.
9. **Post-activation review.** Within the trigger's defined review timeline (default: 30 days), the affected body reviews the activation: Was the threshold crossing genuine? Was the safeguard action proportionate? Should the trigger be recalibrated? This review follows the ACT process.
10. **Periodic trigger review.** Every trigger has a review date (default: annual). On that date, the trigger enters the ACT process for renewal, modification, or retirement. Triggers cannot auto-renew without review. Triggers cannot be silently disabled -- disabling requires the same ACT process as installation.

## F. Output Artifact

A Safeguard Trigger Registry entry following `assets/trigger-registry-template.yaml`. Each entry contains: trigger ID, trigger name, associated capture type, monitored indicator, threshold value, safeguard action description, notification recipients, installation date, installed-by reference (ACT decision ID), review date, activation history (list of activation events with dates and data), current status (active/suspended/retired), and modification history. The full registry is accessible to all ecosystem members.

## G. Authority Boundary Check

- **Any ecosystem member** can propose a new safeguard trigger through the ACT process
- **The ACT consent process** determines whether a trigger is installed -- no individual or leadership body can install triggers unilaterally
- **No individual or body** can silently disable, modify, or retire a trigger -- all changes require the same ACT process as installation
- **Trigger activation is automatic** based on data thresholds -- no human gatekeeper decides whether a crossed threshold "really counts"
- **Safeguard actions are bounded interventions** defined in advance -- the action executor carries out the defined action, not an improvised response
- **The monitored body** cannot modify or suspend triggers that monitor it without going through the ACT process with the broader ecosystem
- **The OSC** is notified of all trigger activations but does not gate activation or safeguard execution

## H. Capture Resistance Check

**Capital capture.** Capital capture triggers monitor resource concentration (GHI-03) and funding-conditional proposal patterns. The trigger installation process prevents capital interests from blocking safeguard installation by requiring ACT consent from the full affected group, not just leadership or funders. A funder who objects to a capital capture trigger must provide a reasoned structural objection, not merely assert that the trigger is inconvenient. Trigger thresholds are calibrated to measurable indicators, not subjective assessments of funder influence.

**Charismatic capture.** Charisma capture triggers monitor approval rate disparity (GHI-02) and objection withdrawal patterns (GHI-06). The automatic activation mechanism removes the need for any individual to challenge a popular leader -- the trigger fires based on data, not courage. A charismatic leader cannot prevent trigger installation without participating in the ACT process on equal terms with other ecosystem members.

**Emergency capture.** Emergency capture triggers monitor declaration frequency, scope creep, and authority return timelines. These triggers cannot be suspended during emergencies -- they are specifically designed to fire during the conditions that create emergency capture risk. Post-emergency review of trigger adequacy ensures that emergency experiences inform trigger calibration.

**Informal capture.** All triggers are formally registered, publicly visible, and installed through consented process. The trigger registry itself is a transparency mechanism -- anyone can see what is being monitored, at what thresholds, with what consequences. There are no informal, undocumented, or secret triggers.

## I. Failure Containment Logic

- **Trigger fires on false positive**: the post-activation review (step 9) evaluates whether the threshold crossing was genuine. If the crossing resulted from data anomaly or benign explanation, the safeguard action is halted, the activation is logged as "false positive," and the trigger threshold is recalibrated through ACT process
- **Safeguard action cannot be executed**: if the designated action executor is unavailable or the action is structurally impossible (e.g., "initiate leadership review" when no review process exists), the activation is logged, the OSC is notified, and the ecosystem addresses the structural gap through the ACT process
- **Trigger registry becomes stale**: if no trigger review has occurred within 6 months past the scheduled review date, an automatic escalation notifies all ecosystem members that the trigger registry requires attention
- **Monitor data unavailable**: if the independent monitor has not produced data for a collection cycle, triggers cannot fire (no data, no threshold crossing). The data gap is itself flagged as a governance health event
- **Consent process stalls**: if a trigger proposal cannot achieve consent after two ACT rounds, the proposal is documented as "no consensus" and may be resubmitted with modifications. Existing triggers remain active during this process

## J. Expiry / Review Condition

Every trigger has a mandatory review date, set at installation (default: one year). On the review date, the trigger enters the ACT process for renewal, modification, or retirement. Triggers that are not reviewed within 60 days of their review date generate automatic escalation notices to all ecosystem members. Triggers do not auto-expire (an unreviewed trigger continues to fire), but the failure to review is itself a governance health indicator. Retired triggers are preserved in the registry with status "retired" and their activation history intact. The starter trigger set is reviewed comprehensively after the ecosystem's first year of operation to calibrate thresholds against actual governance data.

## K. Exit Compatibility Check

When a participant who designed or championed a trigger exits the ecosystem, the trigger remains active -- triggers are institutional safeguards, not personal preferences. If the exiting participant was the designated action executor for a safeguard action, a replacement executor is appointed via role-assignment before the exit is complete (within the 30-day wind-down period). Trigger registry entries authored by departed members remain valid historical records. If a mass exit (20%+ of participants) occurs, all triggers are flagged for expedited review to recalibrate thresholds against the reduced participant base. Exiting participants retain no authority over triggers they installed.

## L. Cross-Unit Interoperability Impact

The Safeguard Trigger Registry for each ETHOS is published to all ecosystem members, enabling cross-unit visibility into what governance health conditions are being monitored. When multiple ETHOS install triggers for the same indicator at different thresholds, the variance is informational -- it reflects domain-specific calibration, not inconsistency. Trigger activations in one ETHOS may prompt preventive reviews in structurally similar ETHOS. At ecosystem scale, the OSC reviews cross-ETHOS trigger patterns annually to identify gaps (e.g., an ETHOS that has not installed any capital capture triggers despite receiving external funding). When two NEOS ecosystems federate (Layer V, deferred), trigger design patterns may be shared, but each ecosystem installs and manages its own triggers through its own ACT process.
