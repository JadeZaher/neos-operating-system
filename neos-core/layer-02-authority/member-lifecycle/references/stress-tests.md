# Stress-Test Results: member-lifecycle

**Skill:** member-lifecycle (Layer II)
**Reference from:** SKILL.md, Stress-Test Results section

All 7 scenarios tested against the member-lifecycle skill. Each scenario runs as a full narrative demonstrating how the skill's structural mechanisms activate under adversarial or extreme conditions.

---

## 1. Capital Influx

A major funder announces a $1.5 million contribution to OmniOne contingent on the ecosystem demonstrating 500 active members within 90 days. The current active count is 310. Pressure mounts on the AE to accelerate onboarding and relax the consent ceremony requirements -- specifically, to allow batch onboarding where the facilitator reads the UAF aloud to groups of 20 and members sign immediately at the end. An AE member advocates for this approach, arguing that the funding will benefit everyone and the ceremony is "just a formality."

The member-lifecycle skill's structural safeguards block every proposed shortcut. The 48-hour cooling-off period is a hard minimum recorded in the lifecycle record with start and end timestamps -- a consent session held the same day as the walkthrough produces a structurally defective record that the agreement registry will flag. Section-by-section consent cannot be replaced with a group signing because the lifecycle record requires an individual entry per section per member. The profile assignment requires a consent round from AE or TH for each member -- batch profile assignment by declaration is not a process this skill defines. An AI agent or any participant auditing the registry can identify defective onboarding records by checking cooling-off timestamps. The AE facilitators who follow proper process are protected from pressure: the structural requirements are not within their authority to waive, and that fact is stated in section G. OmniOne reaches 420 active members through properly conducted onboarding within the 90-day window, not 500. The funding condition is not met. The funder must decide whether to contribute without the condition.

---

## 2. Emergency Crisis

A significant natural disaster affects the region where many OmniOne members are based. Communications are disrupted for three weeks. Forty active members go dark -- no participation in any governance process. The 1-month inactivity threshold is approaching for 20 of them, and the participation tracking system begins flagging records.

The member-lifecycle skill handles this through its configurable threshold and notice mechanics, not through suspension of the process. The ecosystem does not suspend inactivity tracking -- it responds through the 14-day response window, which exists precisely for situations where absence has a legitimate cause. When communications are restored, the AE issues a collective notice: all members whose inactivity notices were sent during the disruption period have their 14-day window reset to the date communications resumed. The reasoning: the notice is only meaningful if the member can receive and respond to it, and the skill's intent is to distinguish genuine disengagement from circumstantial absence. Members who resume contact within the extended window are cleared. Members who remain uncontactable after a further 14 days transition to inactive status, as their absence now extends beyond any reasonable disruption window. The ecosystem's quorum calculations are adjusted during the disruption period using the pre-disruption active count for continuity. No emergency suspension of the UAF or the lifecycle process is invoked -- the existing flexibility within the skill is sufficient.

---

## 3. Leadership Charisma Capture

OmniOne's most prominent co-founder, who holds a widely respected Builder profile and a steward role in the Community circle, informally begins conducting "fast onboardings" for people they personally vouch for. The process: a one-hour conversation, immediate profile assignment by the founder's declaration, and the new member is told they are "now part of OmniOne." No lifecycle record is created. No facilitator is assigned. No UAF walkthrough occurs. Several new members believe they are active participants and begin joining consent rounds.

When an AE member checks the agreement registry to verify quorum for a consent process, they find that three participants in the round have no lifecycle records showing active status. The quorum check fails. The AE investigates and discovers the informal onboarding pattern. The structural protection: without a lifecycle record showing `active` status with a completed onboarding consent record, a participant's contributions to any governance process (consent, objection, advice) cannot be counted. The consent round is suspended pending proper documentation. The founder is informed that their vouching carries no structural weight in lieu of the ceremony. The three informally onboarded members are given the opportunity to undergo a proper onboarding ceremony from the start -- their previous "acceptance" has no standing in the registry. The founder's intent to grow the ecosystem is acknowledged; the method is structurally corrected without personal accusation.

---

## 4. High Conflict / Polarization

OmniOne experiences a deep values fracture over a proposed expansion into a new geography. One faction believes the expansion aligns with the ecosystem's founding mission; another believes it will dilute OmniOne's community cohesion. The conflict becomes interpersonal. Two AE members on opposite sides of the dispute both submit inactivity notices for each other -- each claiming the other has been "absent from productive governance" and should be flagged as inactive. This is an attempt to use the inactivity mechanism as a political weapon.

The member-lifecycle skill's inactivity trigger is not activated by member reports -- it is activated by participation log data against the configured threshold. Both members have participation records showing active engagement (the dispute itself has generated significant governance activity). The attempt to weaponize the inactivity process fails because the triggering mechanism is data-driven, not petition-driven. The AE facilitates a conflict resolution process through GAIA Level 3 (Mediation), acknowledging that the expansion disagreement is a legitimate governance question requiring a structured process (ACT), not a question of membership status. The member-lifecycle skill's role in this scenario is to remain inert -- no lifecycle transitions occur because neither member crosses the actual inactivity threshold. The conflict is routed to the appropriate process (conflict resolution skill, Layer VI), and the lifecycle records of both members remain unchanged.

---

## 5. Large-Scale Replication

OmniOne grows from 300 members to 3,000 members across 12 AZPOs over three years. The onboarding consent ceremony must scale without losing structural integrity. At 300 members, one or two facilitators handle all onboarding. At 3,000, the facilitation load requires a trained facilitator pool distributed across AZPOs.

The member-lifecycle skill scales without modification to its structural requirements. What scales is the implementation layer: OmniOne develops a facilitator training program (outside the scope of this skill but referenced by it), maintains a registry of certified facilitators, and distributes the facilitation load across AZPOs. Each AZPO maintains its own participation log for members active within that AZPO, enabling independent inactivity tracking without requiring a central body to monitor all 3,000 members simultaneously. The inactivity detection system becomes partially automated: the participation log is queried at the configured threshold interval and inactivity notices are generated by the registry without requiring manual review of every member's record. Section-by-section consent remains individual -- it cannot be batched or automated. At 3,000 members, the 14-day response windows and reactivation processes continue to work because they are per-member events, not ecosystem-wide events. The only scaling consideration that requires a structural change: at ecosystem-level consent processes (OSC-level), the active member count must be retrievable quickly enough to set quorum before a time-sensitive process closes. A well-maintained registry with current_status fields queryable by date makes this possible.

---

## 6. External Legal Pressure

A government authority in one jurisdiction where several OmniOne members are based issues a directive requiring that any "membership organization" operating in their jurisdiction must maintain a public registry of members, including names and participation dates. The OmniOne lifecycle record contains exactly this kind of data. The OSC must determine whether compliance requires changing the lifecycle record structure or the onboarding process.

The member-lifecycle skill's design separates two concerns: the structural requirements of the record (what the skill mandates) and the jurisdiction-specific handling of that record (an ecosystem policy question). The skill requires that lifecycle records exist and contain specific fields -- it does not mandate how those records are stored, who can access them, or what jurisdictional laws govern them. The OSC convenes to assess compliance requirements. Their determination: members in the affected jurisdiction are individually subject to local law as individuals; the ecosystem does not incorporate external mandates into its universal onboarding process. Members in that jurisdiction are notified of the legal context at onboarding (an addendum to the facilitator's session notes) and can make informed decisions about participation. The ecosystem does not create a separate public registry for the jurisdiction -- doing so would require a UAF amendment (changing how consent records are handled), which requires OSC consensus. The OSC finds no consensus for the amendment. The jurisdiction-specific compliance question is left to individual members. The lifecycle record structure is unchanged.

---

## 7. Sudden Exit of 30%

Within six weeks, 95 of OmniOne's 310 active members exit -- roughly 30% of the active pool -- following a major governance decision that a significant faction opposed. Exits are voluntary and properly processed: each departing member submits an exit declaration, receives a 30-day wind-down, and their roles are transferred. But the volume strains the ecosystem.

The member-lifecycle skill's mass exit provision activates at the 30% threshold. An automatic quorum recalculation is triggered across all open consent processes. Seven ongoing ACT processes are in mid-flow; all seven must pause and reassess whether their previously counted active participants are still active. Three processes had departing members counted in their current-quorum figures -- these three processes are suspended pending quorum reassessment against the reduced active pool. The OSC is notified immediately. Two of the three suspended processes are close enough to completion that they proceed with the adjusted quorum. The third process, which required a supermajority that is no longer mathematically achievable with the reduced pool, is formally paused and will resume when the ecosystem has stabilized its active count. The 30-day wind-down periods for the 95 departing members run concurrently, creating a significant role-transfer load for the role-assignment and role-transfer skills. The AE prioritizes transfer of roles with active responsibilities. Roles that cannot be transferred within 30 days are held temporarily by the delegating body. The ecosystem's active count stabilizes at 215. All lifecycle records of departing members are archived. The UAF and existing agreements of remaining members are unaffected.
