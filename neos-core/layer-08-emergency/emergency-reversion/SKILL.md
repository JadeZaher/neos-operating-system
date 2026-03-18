---
name: emergency-reversion
description: "Return governance from emergency to normal operations through a mandatory recovery state -- authority ceases immediately, crisis decisions face ratification, and the circuit breaker cannot skip Half-Open."
layer: 8
version: 0.1.0
depends_on: [crisis-coordination, emergency-criteria-design]
---

# emergency-reversion

## A. Structural Problem It Solves

The most dangerous moment in emergency governance is not the crisis itself but the transition back to normal. History shows that temporary authority becomes permanent not through dramatic seizure but through quiet continuation: the emergency "isn't quite over," the situation "still needs coordination," the return to normal governance "can wait until things stabilize." Carl Schmitt and Giorgio Agamben both documented how the state of exception persists by making reversion optional rather than structural. NEOS makes reversion mandatory and automatic. The circuit breaker model requires a Half-Open (recovery) state that cannot be skipped. Emergency authority ceases the moment the reversion process begins. Crisis decisions auto-revert if not ratified through normal ACT process within 30 days. The ecosystem structurally prevents the quiet continuation of emergency authority by making the end of emergency as automatic as its beginning.

## B. Domain Scope

This skill applies when an active emergency transitions out of the Open state -- whether because exit criteria were met, the auto-reversion timer expired, or the ecosystem consented to early reversion. The skill governs the Half-Open (recovery) state of the circuit breaker, covering authority cessation, decision review, and the transition to Closed (normal operations). It operates within the domain boundary defined by domain-mapping (Layer II). Out of scope: this skill does not conduct the full post-emergency retrospective (that is post-emergency-review) -- it manages the structural transition and ensures that all emergency actions are queued for review.

## C. Trigger Conditions

- **Exit criteria met**: when the exit threshold defined in the emergency criteria registry is satisfied, as confirmed by the data source specified in the criterion
- **Auto-reversion timer expired**: when the maximum duration (including any approved extensions) is reached, regardless of whether exit criteria have been met
- **Early reversion consent**: when the ecosystem consents to end the emergency before exit criteria are met or the timer expires, through emergency ACT consent process
- **Irreducible constraint violation**: when a role holder violates an irreducible constraint, triggering immediate authority suspension for that role (partial reversion)

## D. Required Inputs

- **Crisis Operations Log**: the complete decision record from the emergency (from crisis-coordination)
- **Emergency criteria**: the specific criterion whose exit threshold has been met or whose timer has expired (from emergency-criteria-design)
- **Pre-authorization registry**: the active roles whose authority must now cease (from pre-authorization-protocol)
- **Reversion Record template**: the structured record for documenting the reversion process (from `assets/reversion-record-template.yaml`)
- **Circuit breaker state definitions**: the formal state definitions for the Open-to-Half-Open and Half-Open-to-Closed transitions (from `assets/circuit-breaker-states.yaml`)

## E. Step-by-Step Process

1. **Confirm reversion trigger.** Verify which reversion trigger activated: exit criteria met (with confirming data), auto-reversion timer expired (with timestamp), or early reversion consent (with ACT decision ID). Log the trigger in the Reversion Record with timestamp and confirming data.
2. **Cease all emergency authority immediately.** All pre-authorized emergency roles deactivate. Role holders' emergency authority ends at the moment the reversion trigger is confirmed. This is not negotiable and not gradual -- authority ceases immediately. Any decision made by a role holder after reversion is triggered is unauthorized. Log the authority cessation with timestamps for each role.
3. **Transition circuit breaker to Half-Open.** The ecosystem enters the Recovery state. Normal governance processes resume. The Half-Open state cannot be skipped -- the ecosystem does not return directly from Open (emergency) to Closed (normal). The Recovery state has a defined duration: 30 days from reversion trigger, during which crisis decisions are reviewed.
4. **Inventory all emergency decisions.** Extract the complete decision record from the Crisis Operations Log. Categorize each decision: (a) within scope and within ceiling -- routine ratification, (b) within scope but ceiling exceeded -- review required, (c) outside scope -- mandatory review, (d) irreducible constraint violation -- immediate review.
5. **Queue crisis decisions for ratification.** All emergency decisions that remain in effect must be ratified through normal ACT process within 30 days of the reversion trigger. Decisions not ratified within 30 days auto-revert: contracts are terminated at the earliest permitted date, resource allocations are reversed, commitments are unwound. The auto-revert default prevents emergency decisions from becoming permanent by inaction.
6. **Process the deferred decision queue.** All decisions that were deferred during the emergency (per crisis-coordination) enter normal ACT process. Deferred decisions are processed in the order they were logged, with priority given to time-sensitive items.
7. **Restore normal role assignments.** Emergency role holders return to their normal governance roles. Any temporary arrangements made during the emergency (e.g., delegated responsibilities) are unwound. Role holders cannot retain any emergency authority by claiming ongoing need.
8. **Schedule post-emergency review.** The post-emergency review (per post-emergency-review) must be scheduled within 14 days of the reversion trigger and conducted within 30 days. The review is mandatory and cannot be deferred indefinitely.
9. **Document the full reversion.** Complete the Reversion Record with: reversion trigger, authority cessation timestamps, decision inventory, ratification schedule, deferred decision queue status, post-emergency review date, and circuit breaker state transition timestamps.
10. **Transition to Closed.** When the post-emergency review is complete and all ratification decisions have been processed, the circuit breaker transitions from Half-Open to Closed. Normal governance is fully restored. If some ratification decisions are still pending at 30 days, they auto-revert per step 5.

## F. Output Artifact

A Reversion Record following `assets/reversion-record-template.yaml`. The record contains: reversion ID, emergency ID reference, reversion trigger type and confirming data, authority cessation timestamps for each role, complete decision inventory with categorization, ratification schedule and outcomes, deferred decision queue status, post-emergency review date, circuit breaker transition timestamps (Open-to-Half-Open, Half-Open-to-Closed), and any auto-reverted decisions. The record is published to all ecosystem members.

## G. Authority Boundary Check

- **No role holder** retains any emergency authority after the reversion trigger -- cessation is immediate and structural
- **No individual or body** can delay, postpone, or prevent reversion once a reversion trigger fires
- **The 30-day ratification window** is a hard deadline -- decisions not ratified auto-revert
- **The Half-Open (Recovery) state** cannot be skipped -- direct transition from Open to Closed is structurally prevented
- **Emergency role holders** have no special authority during the Recovery state -- they are regular members
- **The post-emergency review** is mandatory -- no body can cancel or indefinitely defer it
- **Auto-reverted decisions** are processed through normal governance -- they do not simply disappear

## H. Capture Resistance Check

**Capital capture.** Emergency resource allocations that favored a particular funder or financial interest must be ratified through normal ACT process within 30 days. If the ecosystem does not ratify a funding arrangement made during the emergency, it auto-reverts. This prevents emergency conditions from being used to lock in financial arrangements that would not survive normal deliberation. The Resource Coordinator's spending decisions are itemized in the Reversion Record for transparent review.

**Charismatic capture.** Authority cessation is immediate and structural -- a charismatic leader who held an emergency role cannot gradually transition back to normal while retaining emergency influence. The moment reversion triggers, the leader is a regular member with no emergency authority. Any attempt to continue directing operations after reversion is structurally visible because the Reversion Record timestamps authority cessation. Post-emergency review specifically examines whether role holders attempted to extend informal authority after formal cessation.

**Emergency capture.** This skill is the structural core of emergency capture resistance. The auto-reversion timer ensures that every emergency has a hard end date. The mandatory Recovery state prevents the "things haven't fully stabilized" justification for continuing emergency authority. The 30-day ratification requirement with auto-revert default prevents emergency decisions from becoming permanent by default. The prohibition on skipping the Half-Open state prevents the narrative that "we can go straight back to normal" which actually means "we keep the parts of emergency authority that are convenient."

**Informal capture.** The Reversion Record creates a formal, published document that makes the end of emergency authority unambiguous. Every role cessation is timestamped. Every decision is inventoried. The community can verify that emergency authority has actually ended, not just been renamed or informally continued.

## I. Failure Containment Logic

- **Role holder refuses to cease authority**: the reversion trigger is structural, not dependent on role holder cooperation. The role holder's authority is revoked in the registry. Any decisions made after revocation are unauthorized and documented as governance violations for post-emergency review
- **Exit criteria disputed**: if there is disagreement about whether exit criteria have been met, the most conservative measurement applies (same principle as emergency-criteria-design). If the auto-reversion timer expires during the dispute, reversion proceeds regardless
- **Ratification fails for a critical decision**: if a crisis decision that cannot be easily reversed (e.g., an emergency contract already executed) fails ratification, the ecosystem processes the consequences through normal ACT process, treating the situation as a governance failure to be addressed, not ignored
- **Post-emergency review cannot be scheduled**: if the review cannot be scheduled within 14 days due to member availability, the deadline extends to 21 days with automatic OSC notification. Beyond 21 days, the non-occurrence triggers a Layer VII safeguard
- **Multiple simultaneous reversions**: each emergency reverts independently through its own Reversion Record. If two emergencies end simultaneously, both reversion processes run in parallel with separate decision inventories

## J. Expiry / Review Condition

Reversion Records do not expire -- they are permanent historical documents. The Recovery state (Half-Open) has a structural duration of 30 days, after which the circuit breaker transitions to Closed regardless of whether all ratification decisions are complete (unratified decisions auto-revert). The reversion process itself is not subject to periodic review -- it is a structural transition that operates identically each time. The circuit breaker state definitions in `assets/circuit-breaker-states.yaml` are reviewed annually alongside emergency criteria and pre-authorization reviews.

## K. Exit Compatibility Check

When a former emergency role holder exits the ecosystem during the Recovery state, their departure does not affect the reversion process. Their emergency decisions remain in the ratification queue and are reviewed by the ecosystem without the departed member's participation. If the departing member's emergency decisions are not ratified, they auto-revert per the standard process. The departing member retains no ongoing obligation related to emergency decisions -- the ecosystem assumes responsibility for processing the consequences. Past Reversion Records involving departed members remain valid historical documents.

## L. Cross-Unit Interoperability Impact

Reversion processes in one ETHOS are published to all ecosystem members, providing cross-unit visibility into how emergencies conclude. When an emergency affected multiple ETHOS, each conducts its own reversion independently. The Recovery state duration is consistent across ETHOS (30 days), enabling ecosystem-level tracking of concurrent reversions. Cross-ETHOS mutual aid agreements activated during an emergency are reviewed during each ETHOS's reversion process independently. At federation scale, each ecosystem manages its own reversions through its own processes.

## OmniOne Walkthrough

It is July 2026. The Bali flooding emergency that began on June 15 is concluding. On day 16 (July 1), BMKG downgrades the flood alert to Level 2 and a qualified assessor confirms the SHUR facility is structurally safe for reoccupancy. All displaced members confirm safe shelter. The exit criteria for ECR-SHUR-PS-01 are met.

**Reversion trigger.** Ketut confirms the exit criteria against the emergency criteria registry: BMKG alert below Level 3 for 48+ consecutive hours (confirmed June 30 at 10:00, now 48+ hours), facility safety inspection passed (confirmed July 1 at 09:00), all displaced members confirmed safe (confirmed July 1 at 14:00). The reversion trigger fires at 14:00 on July 1. Ketut logs the trigger in the Reversion Record.

**Authority cessation.** At 14:01, all emergency authority ceases. Ratu (Safety Coordinator), Nadia (Resource Coordinator), and Tomasz (Communications Coordinator) are notified that their emergency roles are deactivated. Ratu was in the middle of arranging a follow-up inspection -- she logs the pending inspection in the deferred decision queue and steps back from the Safety Coordinator role. The Reversion Record logs cessation timestamps for all three roles.

**Decision inventory.** The Crisis Operations Log shows 23 decisions made during the 16-day emergency: 18 immediate decisions (all within scope and ceiling), 3 short-cycle decisions (hotel booking, food supply contract, generator rental -- all consented), 1 ceiling-exceeding decision (Nadia exceeded her per-decision ceiling by $800 on day 8 for emergency water delivery), and 1 deferred decision (solar panel repair). Categorization: 21 decisions in category (a) routine ratification, 1 in category (b) ceiling exceeded, 0 in category (c) outside scope, 0 in category (d) irreducible constraint violation.

**Ratification process.** The 21 routine decisions enter a batch ratification process through normal ACT. Given the volume, the ecosystem groups them into three categories: safety decisions (12), resource decisions (8), and communications decisions (1). Each group goes through a 7-day Advice period and 5-day Consent period. The ceiling-exceeding water delivery decision enters separate review. Nadia provides context: the only available water supplier charged above her ceiling, and the alternative was no potable water for 32 members. The ecosystem ratifies the decision and notes the ceiling gap for pre-authorization review.

**Post-emergency review scheduling.** Ketut schedules the post-emergency review for July 12, within the 14-day window. The review body will be composed of TH members who did not hold emergency roles (per post-emergency-review).

**Edge case -- role holder argues continued authority.** On July 2, Ratu contacts Ketut arguing that she should retain Safety Coordinator authority for another week because "the facility needs ongoing monitoring and I am the most qualified person." The reversion structure prevents this: Ratu's authority ceased at 14:01 on July 1. Ongoing facility monitoring is a normal governance function, not an emergency function. Ketut explains that Ratu can propose a facility monitoring role through normal role-assignment process, but she cannot retain emergency authority. The Reversion Record documents Ratu's request and its resolution, providing post-emergency review with evidence of how authority cessation was handled.

## Stress-Test Results

### 1. Capital Influx

During the Bali flooding emergency, the Resource Coordinator accepted $15,000 in emergency funding from a cryptocurrency foundation under a verbal agreement to "discuss future collaboration." During reversion, this emergency funding decision enters the ratification queue. The ecosystem reviews the terms: the verbal agreement to "discuss" is vague and potentially creates a future obligation. The ecosystem ratifies the emergency funding acceptance (the money was needed) but explicitly rejects any implied collaboration commitment. The verbal agreement is documented as a non-binding expression of interest. The reversion process prevents an emergency funding decision from silently becoming a post-emergency partnership commitment. If the foundation had imposed written conditions during the emergency, those conditions would auto-revert at 30 days if not ratified through normal ACT process.

### 2. Emergency Crisis

The circuit breaker model is tested by the flooding emergency concluding and reversion proceeding through the mandatory Half-Open state. The Recovery period catches the ceiling violation (water delivery), surfaces the verbal funding agreement, and processes the deferred solar panel repair through normal governance. Without the mandatory Recovery state, these items would have been lost between the urgency of the crisis and the normalcy of resumed operations. The Half-Open state is not bureaucratic delay -- it is structural accountability that ensures every emergency action is consciously carried forward or consciously reversed by the ecosystem.

### 3. Leadership Charisma Capture

After the emergency, Surya proposes that the "proven" emergency leadership team should be formalized into a permanent "crisis readiness committee" with standing authority to make rapid decisions. The reversion structure prevents this: emergency authority ceases at reversion, and any new authority must be proposed and consented through normal ACT process. During the Consent phase for Surya's proposal, three members object: "Standing authority for rapid decisions bypasses the ACT process and creates a permanent exception that mirrors the emergency authority structure." The proposal fails consent. The reversion process ensures that the social capital earned during a successful emergency response cannot be converted into permanent structural authority without full deliberation. The post-emergency review specifically examines whether the emergency created informal authority patterns that persist after formal authority ceased.

### 4. High Conflict / Polarization

During the Recovery state, the two polarized factions disagree on whether to ratify certain emergency decisions. Faction A argues that the emergency hotel booking should be ratified because it was cost-effective; Faction B argues it should auto-revert because the hotel is owned by a Faction A supporter. The ratification follows normal ACT process: the decision is evaluated on structural merits (was it within scope? within ceiling? necessary for crisis response?), not factional alignment. The hotel booking was within scope, within ceiling, and necessary. It is ratified. Faction B's objection about the hotel owner's factional alignment is noted but does not constitute a reasoned structural objection to the emergency decision itself. The reversion process provides a structured container for processing polarized reactions to emergency decisions without either suppressing dissent or allowing factional obstruction of legitimate ratification.

### 5. Large-Scale Replication

At scale, 12 SHUR locations may experience overlapping emergencies and reversions. Each ETHOS manages its own reversion independently, using the same Reversion Record template and circuit breaker state definitions. The OSC monitors concurrent Recovery states across the ecosystem, identifying systemic patterns: if multiple ETHOS show ceiling violations during emergencies, the pre-authorization ceilings may need ecosystem-wide recalibration. The consistent 30-day Recovery period across all ETHOS enables ecosystem-level timeline tracking. The auto-revert default for unratified decisions ensures that no ETHOS's reversion stalls indefinitely, even if member engagement is low during the recovery period.

### 6. External Legal Pressure

Indonesian authorities request access to SHUR Bali's Reversion Record as part of a regulatory review of the flooding response. The Reversion Record is a published document available to all ecosystem members -- providing it to external authorities does not compromise internal governance. The ecosystem can share the Reversion Record while noting that it is an internal governance document that reflects NEOS principles, not regulatory compliance. If the authorities identify decisions they consider non-compliant, those decisions are addressed through normal ACT process (they may already be in the ratification queue). The reversion process does not modify itself for external requirements -- it produces a complete internal record that can serve as evidence of structured governance for external review.

### 7. Sudden Exit of 30% of Participants

Twelve members exit during the Recovery state, frustrated by how the emergency was handled. The departures reduce the member pool for ratification ACT processes. The minimum consent threshold still applies: if fewer than the required participants are available for a ratification decision, the timeline extends but cannot exceed 30 days from the reversion trigger. At 30 days, unratified decisions auto-revert. The departing members' emergency decisions (if they held no emergency roles) are unaffected. The departures are documented in the Reversion Record and flagged for the post-emergency review, which will examine whether emergency management contributed to the exits. The reversion process is not structurally compromised by departures because the auto-revert default ensures that decisions are processed even with reduced participation.
