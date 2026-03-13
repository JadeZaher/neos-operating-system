---
name: crisis-coordination
description: "Operate compressed decision timelines during an active emergency -- immediate, short-cycle, and deferred -- so the ecosystem acts quickly without abandoning structural accountability."
layer: 8
version: 0.1.0
depends_on: [pre-authorization-protocol, act-advice-phase]
---

# crisis-coordination

## A. Structural Problem It Solves

During a genuine emergency, normal governance timelines -- multi-day advice periods, week-long consent rounds -- are too slow for decisions that affect physical safety or organizational survival. But compressing governance is not the same as suspending it. Every emergency in history that became permanent began with the argument that "we don't have time for process." NEOS addresses this through structured compression: three decision timelines that match urgency to deliberative depth, a crisis operations log that documents every decision for post-emergency review, and an auto-reversion timer that begins the moment the emergency is declared. The circuit breaker is in the Open state. The ecosystem operates at emergency speed, but within pre-consented boundaries, with full documentation, and with a structural clock counting toward the moment when normal governance resumes.

## B. Domain Scope

This skill applies during an active emergency -- when one or more emergency criteria have been triggered (per emergency-criteria-design) and pre-authorized roles have activated (per pre-authorization-protocol). The skill governs how decisions are made during the Open state of the circuit breaker. It operates within the domain boundary defined by domain-mapping (Layer II). Out of scope: this skill does not define emergency criteria (that is emergency-criteria-design), does not define who holds emergency authority (that is pre-authorization-protocol), does not govern the return to normal operations (that is emergency-reversion), and does not conduct post-crisis assessment (that is post-emergency-review).

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

During an emergency affecting one AZPO, the Communications Coordinator's updates are published to all ecosystem members, providing cross-unit visibility into the crisis. Adjacent AZPOs' own pre-authorized roles may activate independently if the crisis affects their domain. Cross-AZPO mutual aid (if pre-authorized through joint ACT process) operates through each AZPO's own crisis-coordination process -- there is no unified command structure across AZPOs. The Crisis Operations Log format is identical across all AZPOs, enabling ecosystem-level analysis during post-emergency review. At federation scale, each ecosystem manages its own crisis operations independently, sharing situation reports through federation communication channels.

## OmniOne Walkthrough

It is June 2026, and heavy monsoon rains have caused severe flooding in the Bali SHUR area. Water has reached the ground floor of the SHUR facility. The entry criterion for ECR-SHUR-PS-01 (Natural Disaster) is met: BMKG has issued a Level 3 flood alert for the Bali region, and two independent assessments confirm the facility is unsafe for occupancy.

**Declaration and activation.** Ketut, as circle steward, confirms the threshold crossing against the emergency criteria registry and logs the declaration in the Crisis Operations Log at 14:00 on June 15. The circuit breaker transitions from Closed to Open. The auto-reversion timer starts: 14 days maximum duration. Ratu (Safety Coordinator) confirms availability within 30 minutes. Nadia (Resource Coordinator) confirms within 1 hour. Tomasz (Communications Coordinator) confirms within 45 minutes. All activations are logged.

**Immediate decisions.** Ratu classifies the evacuation as an immediate decision within her authority scope. She arranges transport to a hotel complex 12km from the flood zone, negotiates a group rate of $120/night for 32 members (6 members had already relocated independently), and coordinates with BPBD (Bali emergency services) for facility monitoring. Total immediate spending: $3,840 for first night. She reports all decisions to the ecosystem within 4 hours, well within the 24-hour requirement.

**Short-cycle decision.** On day 3, the hotel manager offers a 10-day block booking at a discounted rate of $2,800 total. This is cost-effective but approaches Nadia's $5,000-per-decision ceiling and commits resources for a longer period. Nadia classifies this as a short-cycle decision. She issues an advice request to all available members. Within 24 hours, 18 members respond with advice, mostly favorable. Emergency consent round: no reasoned objections within 12 hours. The booking is authorized and logged.

**Deferred decision.** On day 5, a local vendor contacts Ratu about repairing the SHUR facility's damaged solar panel system. The repair would cost $12,000 and take 3 weeks. This is not an immediate crisis response -- it is a facility improvement decision. Ratu classifies it as deferred and logs it in the deferred decision queue. The repair will be considered through normal ACT process after the emergency concludes.

**Communication cadence.** Tomasz issues daily updates to all 38 members and the OSC. Each update includes: flood status, facility condition, member welfare, decisions made since last update, ceiling utilization (Nadia at 62% of her total emergency spending ceiling), and auto-reversion timer status (day 5 of 14).

**Edge case -- duration extension.** On day 12, the flooding has subsided but BMKG maintains the Level 3 alert due to upstream dam concerns. Exit criteria require both the alert downgrade AND facility safety inspection. The safety inspection cannot be scheduled until BMKG clears the area. Ratu requests a duration extension through short-cycle emergency ACT consent: 7 additional days, citing the pending BMKG decision. Fifteen available members participate in emergency consent. Sari objects: "Seven days is too long -- request 4 days and reassess." The objection is integrated: extension of 4 days approved. Auto-reversion timer reset to day 18. On day 15, BMKG downgrades to Level 2. The safety inspection is scheduled for day 16. The inspection passes. Exit criteria met on day 16. Reversion process activates immediately.

## Stress-Test Results

### 1. Capital Influx

During an active emergency at SHUR Bali, a cryptocurrency foundation offers to cover all emergency costs "with no strings attached" if SHUR Bali agrees to host their annual conference. The Resource Coordinator cannot accept conditional funding under emergency authority -- her scope covers "essential operating expenditures," not partnership agreements. The conference proposal goes into the deferred decision queue. The foundation's unconditional emergency funding offer can be accepted within the Resource Coordinator's ceiling, logged in the crisis operations log, and reviewed post-emergency. The foundation cannot use the crisis to extract governance concessions because the pre-authorized authority scope prevents it, and every decision is logged and published. The compressed timelines do not compress standards -- they compress deliberation periods while maintaining structural boundaries.

### 2. Emergency Crisis

The Bali flooding scenario from the walkthrough demonstrates crisis-coordination under genuine emergency conditions. The three-timeline classification ensures that immediate safety decisions happen without delay, resource decisions above the ceiling receive compressed but genuine consent, and non-crisis decisions are deferred rather than smuggled through under emergency authority. The auto-reversion timer prevents open-ended emergency operations. The crisis operations log creates the accountability record that post-emergency review requires. The 24-hour communication cadence keeps all members informed even when they cannot actively participate in decisions. The system performs exactly as designed: fast action within bounds, full documentation, structural end date.

### 3. Leadership Charisma Capture

During the flooding emergency, Surya (who holds no emergency role) begins advising members to relocate to a specific resort owned by her close friend, rather than the hotel the Safety Coordinator has arranged. Several members follow Surya's advice. The crisis operations log shows that Ratu (Safety Coordinator) authorized the hotel relocation, not the resort. Members who relocated to the resort acted outside the authorized response. Post-emergency review identifies the discrepancy: informal authority displaced authorized authority for some members. The review does not punish Surya -- she gave advice as a concerned member. But it documents the structural gap and recommends that future emergency communications clarify which directives come from authorized role holders versus informal advice. The crisis operations log makes the displacement visible because only authorized decisions appear in the log.

### 4. High Conflict / Polarization

During a resource crisis emergency, the two polarized factions attempt to influence the Resource Coordinator's spending decisions. Faction A pressures Nadia to fund the partnership infrastructure; Faction B pressures her to cut partnership-related costs. The three-timeline classification resolves this: the partnership decision is not a crisis response and goes into the deferred queue. Nadia's authority scope covers "essential operating expenditures" -- keeping the facility operational, paying staff, maintaining basic services. Neither faction's agenda falls within her emergency scope. The conflict continues, but it cannot hijack emergency governance. Deferred decisions are processed through normal ACT process after the emergency, where the full community can deliberate without the pressure of compressed timelines.

### 5. Large-Scale Replication

At scale with 12 SHUR locations, each AZPO operates its own crisis-coordination process independently. When a regional disaster affects three adjacent SHURs simultaneously, each activates its own pre-authorized roles and follows its own compressed timelines. The Crisis Operations Log format is identical across locations, enabling the OSC to monitor three concurrent emergencies with consistent data. Cross-AZPO mutual aid operates through pre-authorized channels -- the Resource Coordinator in a non-affected AZPO can release pre-authorized mutual aid funds to an affected neighbor. No unified command structure is needed because each location's crisis-coordination is self-contained. The 24-hour communication cadence from each Communications Coordinator provides ecosystem-wide situational awareness.

### 6. External Legal Pressure

During an active emergency, Indonesian authorities issue a compliance order requiring the Safety Coordinator to submit daily reports to a government agency. The Communications Coordinator adds the government reporting to the communication cadence without modifying the internal crisis-coordination process. The government's reporting requirements are met as additional output, not as a replacement for internal governance communications. If the government demands authority over crisis decisions (e.g., mandating a specific evacuation route), the Safety Coordinator follows the government directive for physical compliance while logging it in the crisis operations log as an externally mandated action. Post-emergency review evaluates whether the government mandate was appropriate and whether the ecosystem's response maintained internal governance integrity while complying with external authority.

### 7. Sudden Exit of 30% of Participants

Ten members exit during an active emergency, citing dissatisfaction with crisis management decisions. The exits reduce the available member pool for short-cycle emergency ACT consent. The minimum threshold for emergency consent (3 members) is still met with 28 remaining members. The crisis operations log documents the exits and their stated reasons. The Communications Coordinator increases the communication cadence to rebuild trust with remaining members. The auto-reversion timer is not affected by member departures -- it continues counting toward the structural end of emergency authority. Post-emergency review examines whether the crisis management decisions that prompted exits were within authorized scope and ceilings. The departures are painful but do not structurally compromise the emergency response because the pre-authorized roles and compressed timelines continue operating with the remaining membership.
