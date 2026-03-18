---
name: safeguard-trigger-design
description: "Design, install, and maintain measurable safeguard triggers -- automatic thresholds that activate specific governance interventions when governance health indicators cross defined boundaries."
layer: 7
version: 0.1.0
depends_on: [capture-pattern-recognition, act-consent-phase, agreement-creation]
---

# safeguard-trigger-design

## A. Structural Problem It Solves

Detection without action is observation without consequence. The governance-health-audit skill measures governance health. The capture-pattern-recognition skill diagnoses capture patterns. But without structural triggers that convert threshold crossings into defined interventions, the ecosystem depends on individual courage to act on bad news -- and individual courage is exactly what capture suppresses. Robert Michels observed that oligarchies persist not because members are unaware of concentration, but because no structural mechanism forces a response. Safeguard triggers are that mechanism: measurable, automatic, consented-to thresholds that activate specific governance interventions when crossed. They transform passive monitoring into active structural defense, ensuring that governance health degradation produces institutional responses regardless of whether any individual is willing to raise the alarm.

## B. Domain Scope

This skill applies to any ETHOS or ecosystem where governance health indicators are being monitored. Triggers operate within the domain boundary defined by domain-mapping (Layer II) -- a trigger installed for SHUR Bali fires only on SHUR Bali data. Triggers are defined for specific indicators from the governance-health-audit indicator set (GHI-01 through GHI-08) and capture-pattern-recognition confidence scores. Out of scope: this skill designs and installs triggers but does not collect the monitoring data that feeds them (that is independent-monitoring) and does not interpret governance health data (that is governance-health-audit and capture-pattern-recognition). The skill defines the bridge between detection and response.

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

## OmniOne Walkthrough

It is May 2026, and the Q1 Capture Assessment Report for SHUR Bali has identified medium confidence for capital capture -- GEV funding constitutes 35% of resources and has been trending upward for three quarters. Nadia, an AE member, proposes installing a capital capture safeguard trigger.

**Trigger design.** Nadia specifies the trigger anatomy: (a) Monitored indicator: GHI-03, Resource Concentration Index. (b) Threshold: any single funding source reaches 40% of total resources for 2 consecutive quarters. (c) Safeguard action: initiate a mandatory funding diversification review through structural-diversity-maintenance, freeze new funding commitments from the concentrated source until the review completes, and notify all ecosystem members. (d) Notification recipients: all SHUR Bali members, OSC, and GEV financial steward. (e) Review timeline: trigger reviewed annually, first review in May 2027.

**ACT Advice phase.** Nadia shares the trigger design with SHUR Bali members. Dewa, the financial steward, advises that 40% is too sensitive for an early-stage ecosystem that naturally depends on founding support: "We should set it at 45% to avoid false positives during our first two years." Yuki, cross-ETHOS advisor from Costa Rica, notes that their location uses 40% and it has not produced false positives. The OSC advises adding a "grace period" clause: new ecosystems get 18 months before the trigger activates, to allow time for funding diversification.

**ACT Consent phase.** The revised trigger (threshold: 40%, with an 18-month grace period for new ETHOS) enters consent. Ketut, the circle steward, objects: "The freeze on new funding commitments could harm active projects mid-cycle." This is a reasoned structural objection. The group integrates: the freeze applies only to new commitments above the threshold, not to existing committed funds. Ketut withdraws the objection. Consent achieved.

**Installation.** The trigger is registered as SGT-SHUR-001 in the Safeguard Trigger Registry. Installation date: May 18, 2026. Status: active. Monitoring begins at the next data collection cycle.

**Edge case.** Three months later, GEV's funding share reaches 42% due to a delayed grant from another source that was expected to arrive in Q2. The trigger threshold (40% for 2 consecutive quarters) has been crossed for one quarter. The trigger does not fire -- it requires 2 consecutive quarters. The independent monitor publishes the data showing the 42% concentration. The next quarter, the delayed grant arrives and GEV's share drops to 31%. The trigger never fires because the threshold was not sustained. However, the data remains in the record, and the next capture assessment notes the temporary spike as context. If the delayed grant had not arrived and GEV's share stayed above 40% for Q3, the trigger would fire automatically, initiating the funding diversification review.

## Stress-Test Results

### 1. Capital Influx

A philanthropic foundation offers OmniOne $5 million annually, channeled through SHUR Bali, making the foundation the source of 65% of all resources. The capital capture trigger SGT-SHUR-001 fires immediately upon the second quarterly data collection showing concentration above 40%. The safeguard action activates: a mandatory funding diversification review begins through structural-diversity-maintenance, new funding commitments from the foundation above the threshold are frozen, and all ecosystem members receive notification. The foundation's representatives protest the freeze, arguing that their funding is unconditional. The trigger does not evaluate intentions -- it responds to measurable concentration. The post-activation review (within 30 days) examines whether the foundation's funding truly has no conditions attached and whether the concentration poses structural risk regardless of current conditions. Even if the funding is genuinely unconditional today, the structural dependency creates vulnerability that the diversification review addresses. The foundation cannot disable or modify the trigger -- that requires the full ACT process with the broader ecosystem. The trigger's automatic nature means that no individual had to muster the social courage to challenge a major funder.

### 2. Emergency Crisis

A severe monsoon disrupts SHUR Bali operations for six weeks. During the emergency, leadership invokes emergency authority for rapid decision-making. The emergency capture triggers remain active throughout -- they are designed for exactly this situation. The emergency scope trigger monitors whether decisions made under emergency authority stay within the declared emergency scope (flood response and member safety). When leadership approves three infrastructure improvement decisions unrelated to the immediate emergency, the scope creep trigger fires: more than 20% of emergency decisions (3 of 12) fall outside the declared scope. The safeguard action activates: the three out-of-scope decisions are flagged for post-emergency ACT review, and all members are notified. Critically, the trigger fires during the emergency, not after -- providing real-time structural feedback even when normal governance is compressed. The post-emergency review confirms that two of the three decisions were genuinely urgent but one could have waited for normal process. The trigger's threshold is validated as appropriate and renewed without modification. Emergency conditions did not and cannot suspend safeguard triggers.

### 3. Leadership Charisma Capture

Surya, a beloved founding member, has served as OSC representative for four consecutive cycles. The leadership tenure trigger (GHI-05 >= 4 cycles) fires. The safeguard action activates: a mandatory leadership review process begins, and all ecosystem members are notified. Surya responds graciously but supporters organize an informal campaign to "retire the trigger" -- arguing that Surya's continued leadership serves the community. The trigger cannot be retired without the full ACT process, and the campaign must present a reasoned structural objection, not merely assert that Surya is a good leader. During the ACT process to evaluate the trigger, three TH members raise objections to retirement: "The trigger exists to prevent exactly the pattern we are seeing -- a leader so popular that the system cannot rotate." The trigger is renewed. The leadership review proceeds. Surya agrees to transition to a mentorship role. The structural process achieved what social dynamics could not: a leadership rotation that no individual member was socially comfortable proposing.

### 4. High Conflict / Polarization

SHUR Bali is polarized over a proposed partnership with an international land trust. Both factions attempt to weaponize the safeguard trigger system. Faction A proposes a new trigger: "any rejection of partnership proposals triggers a review of the rejecting body for ossification capture." Faction B proposes: "any acceptance of external partnerships triggers a capital capture review." Both proposals enter the ACT process. During the consent phase, multiple members raise reasoned objections: Faction A's trigger conflates disagreement with capture (rejecting a proposal is healthy governance, not ossification), and Faction B's trigger conflates external engagement with capture (partnerships are not inherently capital capture). Neither trigger achieves consent because neither is grounded in measurable governance health indicators -- they are political instruments disguised as safeguards. The existing, consented-to triggers remain active and correctly monitor actual governance health indicators: participation decline (GHI-04) and objection integration rate (GHI-06), both of which are degrading due to the polarization. The GAIA escalation process is recommended for the underlying conflict. The trigger design process itself served as a filter, preventing subjective political triggers from entering the registry while preserving the structural triggers that address measurable degradation.

### 5. Large-Scale Replication

OmniOne scales to 5,000 members across 15 locations. Each ETHOS maintains its own Safeguard Trigger Registry, customized through local ACT processes. The starter trigger set provides baseline consistency -- all ETHOS begin with the same 8 triggers and customize thresholds to local context. The OSC conducts an annual cross-ETHOS trigger review and identifies that 3 of 15 locations have not installed any charisma capture triggers despite having leadership tenure above 3 cycles. The OSC cannot install triggers unilaterally but can recommend trigger proposals to the affected ETHOS and flag the gap publicly. Trigger design patterns that prove effective in one location are shared as templates for others. The trigger registry format is identical across all locations, enabling automated ecosystem-level monitoring at scale. No single location needs to understand the entire ecosystem's trigger landscape -- each manages its own registry within its domain. Cross-ETHOS trigger activations are visible to all members, creating peer transparency.

### 6. External Legal Pressure

Indonesian financial regulators require all co-living organizations to report financial governance controls. A government auditor reviews SHUR Bali's Safeguard Trigger Registry and requests that the capital capture trigger threshold be raised from 40% to 60% to "align with standard financial practices." The trigger modification cannot be made by leadership or external request alone -- it requires the full ACT process with the affected ecosystem members. The ecosystem can produce a compliance document explaining its trigger system in regulatory terminology without modifying the triggers themselves. The UAF sovereignty principle holds: external legal requirements are met through additional documentation, not by weakening internal safeguards. The trigger registry documents the regulatory request as context for the next review cycle, so the ecosystem can evaluate whether external pressure is influencing internal governance -- regulatory capture is itself a capture type. Individual members comply with local financial regulations as individuals; the ecosystem's trigger system is governed by its own consented agreements.

### 7. Sudden Exit of 30% of Participants

Following a divisive OSC restructuring decision, 13 of 40 SHUR Bali members exit within two weeks. The mass exit threshold (20%) triggers an automatic review of all active safeguard triggers. Several triggers need recalibration: the proposal authorship diversity trigger was set for a 40-member ecosystem and may produce false positives with 27 members (fewer unique authors is expected with fewer members). The participation trend trigger will inevitably fire due to the mass departure. The expedited review enters the ACT process with the remaining 27 members. The participation trigger fires as expected -- the safeguard action (initiate community engagement review) is appropriate even though the cause is known. Two triggers are recalibrated for the smaller member base: proposal diversity threshold adjusted from 35% unique authors to 30% for the next two quarters. The trigger for leadership tenure remains unchanged -- member count does not affect leadership rotation requirements. Existing trigger activation records remain valid. The mass exit itself becomes context data for future capture assessments. The trigger system demonstrates resilience: it adapts to changed conditions through consented process rather than breaking or becoming irrelevant.
