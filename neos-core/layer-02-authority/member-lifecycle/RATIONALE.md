---
skill: member-lifecycle
type: rationale
---

# member-lifecycle — Rationale & Design Notes

## A. Structural Problem It Solves

Without formal lifecycle tracking, ecosystems cannot distinguish active participants from disengaged ones. Quorum calculations silently break: a consent round requires eight active members, but three of the eight have not engaged in four months. The system counts them, the quorum appears met, and the decision lacks legitimate grounding. Consent records accumulate ghost signatories whose engagement has ended. Profile assignments drift out of sync with actual participation. The UAF onboarding ceremony is referenced by the universal-agreement-field skill but is never structurally defined until this skill exists. Member-lifecycle closes these gaps by providing a canonical record of who is a participant, what their current status is, and what every status transition requires. Governance structures that depend on knowing who is in the room can now answer that question reliably.

## B. Domain Scope

Every individual participant in the ecosystem, across all ETHOS and circles. This skill governs status transitions between lifecycle states -- it does not govern governance authority (which is domain-mapping and role-assignment) or platform access (which is determined by profile). A participant may be active in multiple ETHOS simultaneously; each ETHOS carries an independent lifecycle record for that participant.

**Inside scope:** status tracking, onboarding consent ceremony process, inactivity detection and notification, reactivation, voluntary exit initiation, profile assignment at onboarding.

**Outside scope:** involuntary removal (Layer VI, Conflict and Repair), Current-See accounting (Layer IV), role authority assignment (role-assignment skill), IP ownership at exit (handled by UAF exit clause and Layer IV).

**Profile vs. role distinction (explicit):** Profiles (Co-creator, Builder, Collaborator, TownHall) are participation tiers that govern platform access levels -- Co-creators have editing access; Builders have commenting access. Profiles are assigned at onboarding and can be changed through AE or TH consent. Roles are authority scopes defined by domain contracts (domain-mapping skill) and assigned through the role-assignment skill. A Builder-profile participant who holds a steward role exercises full governance authority within that domain regardless of their profile's platform access level. Profile changes do not automatically grant or remove domain authority.

## OmniOne Walkthrough

### Scenario A: Priya's Onboarding Consent Ceremony

Priya, a permaculture designer from Kerala, has completed OmniOne's NEXUS orientation modules and is ready for the UAF consent ceremony. Her assigned facilitator is Dex, a trained AE member who has conducted over a dozen onboarding sessions.

Dex sends Priya the OmniOne UAF (version 2.1.0) three days before their scheduled session, giving her time to read it in advance. In the walkthrough session, they move through each section. When they reach Section 4 (Stewardship and Contribution), Priya pauses: "I create permaculture designs for clients outside of OmniOne. Does consenting to this section mean OmniOne has claims on that work?" Dex clarifies: designs she creates independently, outside any OmniOne ETHOS context, are her original works and carry no OmniOne claims. Only co-created works within an ETHOS context are emergent works. Priya is satisfied and they continue.

In Section 5 (Sovereignty and Evolution), Priya raises a harder objection: "I cannot agree to the clause stating that I accept the mediation process as the first step in any dispute. I have experienced mediation processes used to protect institutions, not people. I need to understand who mediates and whether I can withdraw from the process mid-way." Dex records this as a reasoned objection to Section 5. He explains the OmniOne conflict resolution structure (GAIA model, independent facilitators, right to escalate). After Dex provides the conflict resolution documentation and Priya reads it, she resolves her objection -- she was concerned about a process she did not have information on, not about the principle. The objection is documented as resolved with the date and context noted.

The 48-hour cooling-off period begins after the session. Two days later, Priya returns. She has one new question about Section 2 (Processes) -- she wants to understand what "active participation" means in practice before she commits. Dex explains that active participation means engaging in governance processes: attending sessions, participating in consent rounds, or submitting advice or proposals. Priya confirms she can meet this standard.

Section-by-section consent proceeds: Priya explicitly confirms each section. Dex records: facilitator (Dex, AE), UAF version 2.1.0, consent date (2026-02-18), cooling-off window (2026-02-16 to 2026-02-18, 48 hours honored). The consent record is registered in the agreement registry as the second entry in Priya's member record. Dex proposes a Builder profile -- Priya is joining as a contributor who will comment and advise on design projects before seeking Co-creator access. The AE runs a brief consent round on the profile proposal; no objections are raised. Priya's status transitions to `active`, Builder profile.

**Edge case:** Three weeks into onboarding a different prospective member, Theo, the facilitator discovers that Theo's 48-hour window was not properly honored -- the consent session was held 30 hours after the walkthrough. The consent is structurally defective. The facilitator notifies the AE, resets Theo's status to `onboarding`, and schedules a proper consent session with a new cooling-off period. Theo's consent from the earlier session is voided; a note is added to the lifecycle record documenting the defective onboarding and the corrective action.

---

### Scenario B: Kai's Inactivity and Reactivation

Kai is an active OmniOne member with a Builder profile who joined eight months ago. Over the past five weeks, Kai has not appeared in any meeting attendance records, participated in no consent rounds, submitted no proposals, and given no advice -- a full calendar month of zero governance activity against OmniOne's configured 1-month threshold.

The participation tracking system flags Kai's record. An inactivity notification is sent: "Your last recorded governance activity was 2025-12-28. The OmniOne inactivity threshold is 1 calendar month. You have 14 days to respond or resume participation before your status transitions to inactive. Inactive members retain all agreements and may reactivate at any time by notifying the ecosystem and attending one governance session."

Kai does not respond within 14 days. Status transitions to `inactive` on 2026-02-11. Kai is removed from active quorum calculations. All agreements Kai co-signed remain in force. Kai's Builder profile is retained in the lifecycle record but flagged as inactive.

Three months later, in May 2026, Kai sends a message to the AE: "I was traveling for an extended period. I'm back and want to rejoin active participation." Kai's status transitions to `reactivating`. Two days later, Kai attends the weekly AE governance session -- attendance is recorded. Kai's status transitions back to `active`. The participation log resets with 2026-05-14 as the new baseline for inactivity threshold tracking. Kai resumes participation with the Builder profile intact, all prior agreements in force, no new onboarding required.

## Stress-Test Results

See `references/stress-tests.md` for all 7 full narrative stress-test scenarios. Scenario titles for reference:

1. Capital Influx
2. Emergency Crisis
3. Leadership Charisma Capture
4. High Conflict / Polarization
5. Large-Scale Replication
6. External Legal Pressure
7. Sudden Exit of 30%
