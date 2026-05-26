---
skill: crisis-coordination
type: rationale
---

# crisis-coordination — Rationale & Design Notes

## A. Structural Problem It Solves

During a genuine emergency, normal governance timelines -- multi-day advice periods, week-long consent rounds -- are too slow for decisions that affect physical safety or organizational survival. But compressing governance is not the same as suspending it. Every emergency in history that became permanent began with the argument that "we don't have time for process." NEOS addresses this through structured compression: three decision timelines that match urgency to deliberative depth, a crisis operations log that documents every decision for post-emergency review, and an auto-reversion timer that begins the moment the emergency is declared. The circuit breaker is in the Open state. The ecosystem operates at emergency speed, but within pre-consented boundaries, with full documentation, and with a structural clock counting toward the moment when normal governance resumes.

## B. Domain Scope

This skill applies during an active emergency -- when one or more emergency criteria have been triggered (per emergency-criteria-design) and pre-authorized roles have activated (per pre-authorization-protocol). The skill governs how decisions are made during the Open state of the circuit breaker. It operates within the domain boundary defined by domain-mapping (Layer II). Out of scope: this skill does not define emergency criteria (that is emergency-criteria-design), does not define who holds emergency authority (that is pre-authorization-protocol), does not govern the return to normal operations (that is emergency-reversion), and does not conduct post-crisis assessment (that is post-emergency-review).

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

At scale with 12 SHUR locations, each ETHOS operates its own crisis-coordination process independently. When a regional disaster affects three adjacent SHURs simultaneously, each activates its own pre-authorized roles and follows its own compressed timelines. The Crisis Operations Log format is identical across locations, enabling the OSC to monitor three concurrent emergencies with consistent data. Cross-ETHOS mutual aid operates through pre-authorized channels -- the Resource Coordinator in a non-affected ETHOS can release pre-authorized mutual aid funds to an affected neighbor. No unified command structure is needed because each location's crisis-coordination is self-contained. The 24-hour communication cadence from each Communications Coordinator provides ecosystem-wide situational awareness.

### 6. External Legal Pressure

During an active emergency, Indonesian authorities issue a compliance order requiring the Safety Coordinator to submit daily reports to a government agency. The Communications Coordinator adds the government reporting to the communication cadence without modifying the internal crisis-coordination process. The government's reporting requirements are met as additional output, not as a replacement for internal governance communications. If the government demands authority over crisis decisions (e.g., mandating a specific evacuation route), the Safety Coordinator follows the government directive for physical compliance while logging it in the crisis operations log as an externally mandated action. Post-emergency review evaluates whether the government mandate was appropriate and whether the ecosystem's response maintained internal governance integrity while complying with external authority.

### 7. Sudden Exit of 30% of Participants

Ten members exit during an active emergency, citing dissatisfaction with crisis management decisions. The exits reduce the available member pool for short-cycle emergency ACT consent. The minimum threshold for emergency consent (3 members) is still met with 28 remaining members. The crisis operations log documents the exits and their stated reasons. The Communications Coordinator increases the communication cadence to rebuild trust with remaining members. The auto-reversion timer is not affected by member departures -- it continues counting toward the structural end of emergency authority. Post-emergency review examines whether the crisis management decisions that prompted exits were within authorized scope and ceilings. The departures are painful but do not structurally compromise the emergency response because the pre-authorized roles and compressed timelines continue operating with the remaining membership.
