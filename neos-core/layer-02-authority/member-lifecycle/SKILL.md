---
name: member-lifecycle
description: "Track and manage ecosystem participant status transitions -- onboarding consent ceremony, active participation, inactivity detection, reactivation, and exit -- so that governance always knows who is participating and what their status means."
layer: 2
version: 0.1.0
depends_on: [universal-agreement-field]
---

# member-lifecycle

## C. Trigger Conditions

- **Onboarding request:** A prospective member formally requests to join the ecosystem (or is invited through NEXUS onboarding flow). Triggers the onboarding consent ceremony.
- **Activity threshold breach:** A participant's participation log shows no governance activity (no consent rounds participated in, no advice given, no proposals submitted, no meeting attendance) for the inactivity threshold period (default: 1 calendar month; configurable 2 weeks minimum, 3 months maximum). Triggers inactivity notification.
- **Inactivity notice lapse:** A member who received an inactivity notification does not respond within the 14-day response window. Triggers transition to inactive status.
- **Reactivation request:** An inactive member notifies the ecosystem of intent to return and attends one governance session. Triggers reactivation.
- **Voluntary exit declaration:** An active or inactive member formally declares intent to exit. Triggers the exiting status and begins wind-down.

## D. Required Inputs

**For onboarding:**
- Prospective member identity (name, contact, any ecosystem-specific identifier)
- Current ratified UAF document (version number required)
- Facilitator identity (a trained AE member or equivalent)
- Proposed profile assignment (proposed by facilitator, consented by relevant council)

**For inactivity detection:**
- Participation log for the member covering the threshold period (meeting attendance records, consent-round participation records, proposal submission records, advice-given records)
- The configured inactivity threshold for the ecosystem (default: 1 month)

**For reactivation:**
- Member's reactivation notification (written or in-session)
- Attendance record from one governance session occurring after the notification

**For voluntary exit:**
- Member's voluntary exit declaration (written)
- Inventory of in-progress commitments and roles held (from lifecycle record)

## E. Step-by-Step Process

**Lifecycle states:**

```
prospective → onboarding → active → inactive → reactivating → active (loop)
                                  → exiting → exited
```

---

**Onboarding consent ceremony (prospective → onboarding → active):**

1. Prospective member submits joining request. Status sets to `prospective`.
2. Ecosystem schedules onboarding session with a facilitator. Status sets to `onboarding`.
3. Facilitator presents the current ratified UAF document in full. Prospective member receives a copy to review before the session.
4. Facilitated walkthrough: the facilitator guides the member through each UAF section, inviting questions. The facilitator has process authority -- they clarify and explain, they do not modify UAF provisions or grant exceptions.
5. Cooling-off period: a minimum 48 hours must pass between the walkthrough session and the consent recording. The member takes the UAF and reflects independently.
6. Consent recording: the member returns for section-by-section explicit consent. For each UAF section, the member states consent or raises a reasoned objection. Blanket consent ("I agree to all of it") is not accepted -- section-by-section confirmation is required.
7. If any section receives a reasoned objection: the objection is documented in the lifecycle record as a review item. The member is not denied entry solely on this basis unless the objection constitutes a fundamental incompatibility with the ecosystem's non-negotiable commitments. The facilitator and relevant council assess compatibility. If incompatible, the member exits the onboarding flow with the objection noted for UAF review consideration.
8. Consent record is registered in the agreement registry, cross-referenced to the UAF version consented to, with facilitator name, date, and cooling-off confirmation.
9. Profile assignment: the facilitator proposes a profile (Co-creator, Builder, Collaborator, TownHall). The proposal is consented to by the relevant council (AE for Co-creator/Builder/Collaborator; TH for TownHall profile). Default assignment if no objection: Builder.
10. Status transitions to `active`. Lifecycle record is created.

---

**Active to inactive:**

1. Participation tracking system flags a member when the inactivity threshold has elapsed with no recorded governance activity.
2. Notification is sent to the member stating: their last recorded activity date, the threshold applied, the 14-day response window, and the consequence of no response (inactive status).
3. If the member responds within 14 days -- either by contesting the record (section I) or by resuming activity -- the inactivity flag is cleared.
4. If no response within 14 days: status transitions to `inactive`. Lifecycle record updated. The member is removed from active quorum calculations. Existing agreements and consent records remain valid and in force.

---

**Inactive to reactivating to active:**

1. Inactive member notifies the ecosystem of intent to return (written or in-session).
2. Status transitions to `reactivating`.
3. Member attends one governance session (any active consent round, meeting, or advice process).
4. Attendance is recorded. Status transitions to `active`. Participation log resets to the reactivation date as the new baseline.

---

**Active to exiting to exited:**

1. Member submits voluntary exit declaration.
2. Status transitions to `exiting`. Lifecycle record generates a wind-down checklist: roles held, in-progress commitments, stewarded assets.
3. 30-day wind-down period: roles are transferred per the role-transfer skill; in-progress commitments are handed off or documented; stewarded assets are returned.
4. At wind-down completion (or at 30 days, whichever comes first): status transitions to `exited`. Consent record is archived, not deleted. Member is removed from all active quorum pools.

## F. Output Artifact

A lifecycle record for each participant, following `assets/lifecycle-record-template.yaml`, containing: member identity, current status, proposed and assigned profile, onboarding record (facilitator, UAF version, consent date, cooling-off dates, section-by-section consent results), all status transitions with dates and triggers, roles held (cross-reference to role-assignment records), last governance activity date, and inactivity notice date if applicable. The lifecycle record is the authoritative source for a member's current participation status and is referenced by all quorum calculations.

## G. Authority Boundary Check

**Facilitator:** Process authority only. The facilitator guides the walkthrough, records responses, proposes profile, and confirms cooling-off. The facilitator cannot modify UAF provisions, waive sections, override a member's objection, or unilaterally assign a non-default profile without council consent.

**Profile assignment:** Proposed by the facilitator. Consented by the relevant council (AE for Builder/Co-creator/Collaborator; TH for TownHall profile). No individual may assign their own profile or unilaterally reassign another member's profile.

**Inactivity status:** Triggered by participation data against the configured threshold. No individual has authority to selectively flag or unflag members for inactivity. The threshold applies uniformly.

**No one** may: pressured-close an onboarding session before the 48-hour cooling-off period, deny entry to a prospective member for reasons other than UAF incompatibility, or block a reactivation request without a structural basis.

## H. Capture Resistance Check

**Pressured onboarding.** An ecosystem with a fundraising milestone tied to member count pressures facilitators to rush consent ceremonies. The 48-hour minimum cooling-off period is non-negotiable and recorded in the lifecycle record with start and end timestamps. A consent recorded before 48 hours have elapsed is structurally defective and must be repeated. No external incentive, deadline, or authority figure can compress this period.

**Selective inactivity enforcement.** A council member dislikes a participant and wants them removed from active quorum. Inactivity status is triggered by the participation log, not by anyone's judgment. The threshold is configured ecosystem-wide and applies uniformly. Selective enforcement (flagging some members while ignoring others with identical participation records) is a data inconsistency, detectable and contestable through the 14-day response window.

**Gate-keeping.** An influential member attempts to block a prospective participant's onboarding for political reasons. The onboarding process is open to any prospective member. The only legitimate basis for failing an onboarding is a documented UAF incompatibility (an objection to a section that constitutes a fundamental incompatibility). Gate-keeping rationales that do not reference UAF incompatibility have no standing in this skill.

**Informal capture.** Someone begins participating in governance without completing the onboarding ceremony. Without a lifecycle record showing `active` status, a participant's consent, objection, or advice cannot be counted in any ACT process. The quorum check references the lifecycle record. Informal participation has no structural weight.

## I. Failure Containment Logic

**Failed onboarding -- UAF section objection:** The objection is documented in the lifecycle record. The facilitator and the relevant council (AE or OSC depending on the section) assess whether the objection is a fundamental incompatibility or a clarification need. If clarification resolves it, the onboarding continues. If the incompatibility persists, the prospective member exits the flow. The objection is forwarded as a UAF review item -- a single member's objection can seed an amendment proposal, but does not by itself trigger one.

**Contested inactivity:** A member receives an inactivity notice but believes their activity was not properly recorded (they attended a session that was not logged). The 14-day response window is specifically for this purpose. The member submits their activity evidence; the participation log is reviewed and corrected if warranted. If the record is confirmed accurate, the inactivity transition proceeds. If corrected, the inactivity flag clears.

**Onboarding abandonment:** A prospective member completes the walkthrough but does not return for the consent session within 30 days. Status reverts to `prospective` and is flagged as dormant. The prospective member may restart the onboarding process at any time.

**Mass exit (30% of active members):** When 30% or more of the active participant pool exits within a 60-day window, an automatic quorum recalculation is triggered across all open consent processes. Any consent process where previously-counted members have exited must be reassessed before closing. The OSC is notified and may convene a special review session.

## J. Expiry / Review Condition

Active status has no expiry -- a member remains active until the inactivity threshold is crossed or they initiate exit. The inactivity threshold is checked continuously against the participation log (default: 1 calendar month; minimum: 2 weeks; maximum: 3 months). The threshold is ecosystem-configurable and documented in the ecosystem's configuration record.

Profile assignments are reviewed when: the member requests a change, the relevant council initiates a review, or the member's participation pattern substantively changes. Profiles do not auto-expire.

The lifecycle record itself is archived upon exit and retained indefinitely for historical consent traceability. Archived records are not subject to expiry.

## K. Exit Compatibility Check

On voluntary exit, the following align with the UAF exit clauses:

- **Original works:** The exiting member retains full rights to individual creations made prior to and during ecosystem participation, per UAF Section 4.
- **In-progress commitments:** 30-day wind-down period. Commitments that cannot be completed within 30 days are formally handed off per the role-transfer skill, with the handoff documented in the lifecycle record.
- **Roles held:** All active role assignments are transferred per the role-transfer skill before or at the 30-day mark. A role that cannot be transferred is held temporarily by the delegating body until a steward is assigned.
- **Agreements co-signed:** Agreements the exiting member co-signed remain in force. Their obligations under those agreements may survive exit if explicitly specified in the agreement (per the agreement-review skill). The lifecycle record documents which agreements remain active.
- **Consent record:** Archived with exit date. If the member rejoins, they consent to the then-current UAF version and a new onboarding is conducted.

## L. Cross-Unit Interoperability Impact

A participant may be active in multiple ETHOS simultaneously. Each ETHOS maintains an independent lifecycle record for that participant. Active status in one ETHOS does not imply active status in another. Inactivity in one ETHOS does not automatically trigger inactivity in another -- each record is checked against the relevant ETHOS's participation log independently.

Cross-ETHOS profile assignments may differ. A member may hold a Co-creator profile in ETHOS-A and a Builder profile in ETHOS-B, reflecting their different levels of engagement in each unit.

When a participant exits the ecosystem entirely (not just an ETHOS), all ETHOS lifecycle records are updated to `exited` status on the same date. The wind-down process covers all ETHOS simultaneously.

The extensibility point for cross-ecosystem federation (Layer V, deferred): when a participant is active in two federated NEOS ecosystems, each ecosystem maintains its own lifecycle record. Federated status recognition (auto-accepting onboarding from a trusted ecosystem) is a Layer V configuration, not defined here.
