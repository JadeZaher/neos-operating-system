---
name: inter-unit-liaison
description: "Define and maintain ongoing cross-ETHOS coordination through designated liaison roles -- with explicit mandate boundaries, accountability structures, and mandatory rotation to prevent information capture."
layer: 5
version: 0.1.0
depends_on: [cross-ethos-request, federation-agreement, role-assignment]
---

# inter-unit-liaison

## C. Trigger Conditions

- A federation agreement specifies that participating ETHOS designate liaison contacts for ongoing coordination
- A shared resource stewardship arrangement generates recurring cross-ETHOS communication exceeding what ad-hoc requests can efficiently handle
- Cross-ETHOS request volume between two ETHOS warrants a standing coordination point
- A multilateral coordination group needs a named point person from each participating ETHOS

## D. Required Inputs

- **Participating ETHOS** -- all units involved in the liaison relationship (mandatory)
- **Liaison type** -- bilateral, multilateral, or domain-specific (mandatory)
- **Proposed mandate scope** -- defined in four layers: (a) can communicate freely, (b) can explore and discuss, (c) can recommend to home ETHOS, (d) requires home ETHOS consent before proceeding (mandatory)
- **Proposed person** -- named individual, must be a member in good standing of their home ETHOS (mandatory)
- **Reporting cadence** -- how often the liaison reports to their home ETHOS (mandatory; default: monthly)
- **Term duration** -- proposed term length (default: 12 months; maximum: 24 months total with one extension)

## E. Step-by-Step Process

1. **Identify coordination need.** One or more ETHOS recognize that ongoing cross-unit coordination warrants a standing liaison role. The trigger condition is documented.
2. **Draft liaison proposal.** The proposing ETHOS drafts the proposal specifying type, proposed person, mandate scope in four layers, reporting cadence, and term. The four-layer mandate makes authority boundaries explicit.
3. **Mandate review by all participating ETHOS.** Each ETHOS runs an internal advice phase on the mandate scope. Each may propose adjustments. The mandate is collaboratively refined until all ETHOS consent to the boundary definitions.
4. **Appoint liaison through role-assignment.** The home ETHOS appoints the liaison using the role-assignment skill, with the mandate as the authority scope. Appointment recorded in the home ETHOS's registry.
5. **Register in all participating ETHOS' registries.** The liaison role agreement is registered in every participating ETHOS's registry with linked entries.
6. **Operate with regular reporting.** The liaison reports on: topics discussed, items explored, recommendations made, items escalated for home ETHOS consent, and mandate boundary questions encountered.
7. **Mid-term check (optional).** At 6 months, the home ETHOS reviews the reporting log and confirms the mandate remains appropriate. Mandate adjustments require re-running Step 3.
8. **Term review.** At term end, the home ETHOS reviews mandate adherence, reporting quality, and coordination outcomes. Options: conclude the role, extend for one additional 12-month term, or rotate to a new liaison.
9. **Rotation.** At the mandatory rotation point, the outgoing liaison documents all in-progress coordination items. The successor is appointed through Steps 3-5 with a fresh mandate review.

## F. Output Artifact

A liaison role agreement following `assets/liaison-mandate-template.yaml`, containing: role ID, liaison name, home ETHOS, participating ETHOS, liaison type, four-layer mandate scope, reporting cadence, term dates, maximum term date, review schedule, and designated successor process. Registered in all participating ETHOS' registries with linked entries.

## G. Authority Boundary Check

- **No binding commitments** without explicit authorization for the specific commitment. Commitments outside the mandate are void.
- **No intra-ETHOS authority** in any participating ETHOS except within the mandate scope. The liaison is a coordination channel, not a decision-maker.
- **Others can still communicate** across ETHOS boundaries without routing through the liaison. The liaison does not become a gatekeeper or exclusive channel.
- **Mandate scope requires mutual consent** from all participating ETHOS. One ETHOS cannot unilaterally expand the liaison's authority.
- **Maximum term is structurally enforced.** No individual holds the same liaison role for more than 24 months. This is not configurable above 24 months.

## H. Capture Resistance Check

**Information asymmetry capture.** The liaison accumulates knowledge about inter-ETHOS affairs that no other person holds, gaining informal influence beyond their mandate. Resistance: monthly reporting requires sharing information with the home ETHOS. Reports are visible to participating ETHOS. Omissions surface as reviewable gaps. The mandatory rotation ensures no individual is the permanent keeper of inter-unit knowledge.

**Relationship capture.** The liaison develops personal relationships with counterparts that override structural accountability -- sharing information outside mandate scope, making informal commitments, or softening positions to maintain personal goodwill. Resistance: reporting logs document what topics were discussed and positions taken. Patterns deviating from mandate scope become visible over time. Mid-term checks review this explicitly.

**Bottleneck capture.** The liaison becomes the only practical channel for cross-ETHOS communication, creating a single point of failure and concentrated informal power. Resistance: the skill affirms that any member can use cross-ethos-request directly. If a liaison actively discourages direct cross-ETHOS contact, this is treated as mandate overreach.

**Home ETHOS capture.** The liaison prioritizes their home ETHOS's interests, making them an ineffective coordination channel. Resistance: the mandate is defined collaboratively by all participating ETHOS, not just the liaison's home unit. Multilateral coordinators are reviewed by all participating ETHOS, not just the home ETHOS.

## I. Failure Containment Logic

- **Liaison exceeds mandate:** Any commitment outside the four-layer scope is void. The affected ETHOS notifies the liaison's home ETHOS. First instance: documented warning and mandate clarification. Second instance: role review and possible early rotation.
- **Liaison role becomes vacant:** Cross-ETHOS coordination continues through direct cross-ethos-request process. The vacancy does not suspend coordination. Successor appointment begins within 30 days.
- **Liaison conflicts with counterpart:** The liaison flags the conflict in their reporting log. If structural (not personal), escalation goes to polycentric-conflict-navigation.
- **Mandate scope contested:** A participating ETHOS believes the liaison acted within mandate but the receiving ETHOS disagrees. Joint review of the specific incident against the documented mandate. If unresolved, escalate to polycentric-conflict-navigation.

## J. Expiry / Review Condition

- **Default term:** 12 months with one 12-month extension. Maximum total: 24 months.
- **Mandatory rotation:** After maximum term, the same person cannot hold the same role for at least 12 months.
- **Reporting cadence:** Monthly recommended. Two consecutive missed reports trigger a mandatory check-in with the home ETHOS's relevant circle.
- **Term review** uses the role-assignment review process. If the role continues, a new liaison is appointed (rotation) or the current liaison is extended through a fresh consent round.

## K. Exit Compatibility Check

- **Liaison exits ETHOS or ecosystem:** Role vacated immediately. Home ETHOS notifies participating ETHOS within 7 days. In-progress coordination items are documented by the home ETHOS within 14 days. Successor appointment begins immediately.
- **No binding obligations survive exit.** Explorations are not commitments. Items that reached the "requires ETHOS consent" layer but did not receive consent are treated as open threads for the successor.
- **Home ETHOS responsibility:** Documentation of in-progress items is the home ETHOS's obligation, not solely the departing liaison's. This ensures institutional memory survives exit.

## L. Cross-Unit Interoperability Impact

The liaison role agreement is registered in all participating ETHOS' registries. No ETHOS is the "owner" of the liaison relationship. Changes to the mandate require consent from all participating ETHOS. When the role spans more than two ETHOS, the agreement lists all participants and is registered in each. The liaison skill references cross-ethos-request (fallback when no liaison exists), federation-agreement (the broader framework within which liaison roles often operate), and role-assignment (how the liaison is formally appointed).
