---
name: emergency-reversion
description: "Return governance from emergency to normal operations through a mandatory recovery state -- authority ceases immediately, crisis decisions face ratification, and the circuit breaker cannot skip Half-Open."
layer: 8
version: 0.1.0
depends_on: [crisis-coordination, emergency-criteria-design]
---

# emergency-reversion

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
