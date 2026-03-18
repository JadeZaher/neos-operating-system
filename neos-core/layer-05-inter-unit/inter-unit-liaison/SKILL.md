---
name: inter-unit-liaison
description: "Define and maintain ongoing cross-ETHOS coordination through designated liaison roles -- with explicit mandate boundaries, accountability structures, and mandatory rotation to prevent information capture."
layer: 5
version: 0.1.0
depends_on: [cross-ethos-request, federation-agreement, role-assignment]
---

# inter-unit-liaison

## A. Structural Problem It Solves

Without designated liaison roles, cross-ETHOS coordination depends on whoever happens to know someone in the other unit -- informal channels that concentrate information and influence in a few well-connected individuals. Alternatively, coordination falls to leadership figures who accumulate inter-unit authority through reputation rather than mandate. This skill creates formal liaison roles with explicit mandate boundaries so coordination is accountable, distributed, and does not become a bottleneck. Mandatory rotation prevents any individual from becoming the irreplaceable bridge between ETHOS.

## B. Domain Scope

This skill applies to any ongoing coordination relationship between ETHOS that benefits from a designated point person. Liaison types include:

- **Bilateral liaison** -- between two ETHOS for general or domain-specific coordination
- **Multilateral coordinator** -- across three or more ETHOS for a shared domain (e.g., economics, education, governance)
- **Domain-specific liaison** -- focused on a particular area like resource sharing, member mobility, or conflict resolution

The liaison role does not replace the cross-ethos-request process. Other members can still communicate across ETHOS boundaries directly. The liaison is not a gatekeeper.

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

## OmniOne Walkthrough

The Bali, Costa Rica, and Mexico SHURs have increasing cross-SHUR conversations about resource sharing through their Economics circles. These discussions are happening informally through personal connections. Nadia, Bali's Economics circle steward, proposes formalizing a liaison role.

**Mandate definition.** Nadia drafts a four-layer mandate for Bali's internal review. During advice, Marco worries a liaison might make informal commitments; Priya worries a too-narrow mandate will be useless. Nadia integrates both by drafting explicitly:
- **Can communicate freely:** Bali's resource flow data (aggregate), current shared resource commitments, public circle priorities
- **Can explore and discuss:** shared pool possibilities, learning fund structures, traveling member resource access protocols
- **Can recommend to Bali circle:** any concept from cross-SHUR discussion that warrants deliberation
- **Requires circle consent:** any resource commitment, any agreement to a sharing structure, any representation of Bali's position on contested issues

Costa Rica requests one addition: quarterly summary reports shared with all three circles. Mexico has no changes. Bali consents to Costa Rica's addition.

**Appointment.** Rafi, an AE member with Economics circle membership and three years of SHUR experience, is appointed through role-assignment. The liaison agreement (`LIA-ECON-2026-001`) is registered in all three registries.

**First coordination meeting.** Rafi joins the cross-SHUR Economics call. On traveling member learning fund access, Rafi shares Bali's fund structure (within "can communicate" layer) and explores protocol options. On a shared emergency fund concept, Rafi tells the group: "I can develop this concept with you and bring it to Bali for deliberation, but I cannot represent Bali's position on contributions. That requires circle consent."

**Mandate extension.** Rafi presents the emergency fund concept to Bali's circle. They grant a specific negotiation mandate: he can discuss contribution levels between 3-8% of the monthly learning fund, trigger conditions, and a 12-month sunset. This extension is appended to his liaison agreement.

**Edge case: relationship capture.** By June, Rafi has a close working relationship with Valentina from Costa Rica. His May reporting log reveals he has been sharing information about Bali's internal circle dynamics -- specifically that two members have reservations about the emergency fund triggers. This was not in his "can communicate freely" layer. Priya flags it. The circle convenes a mandate review -- not punitive, but structural. Two actions: (1) a formal note to Costa Rica and the registry that out-of-scope communications should be flagged; (2) clarification that internal circle deliberations are not in scope unless explicitly authorized. Rafi acknowledges and adjusts. First instance documented.

**Output.** `LIA-ECON-2026-001`, registered in all three registries, with mandate scope, April extension, May reporting log, and June clarification addendum.

## Stress-Test Results

### 1. Capital Influx

A wealthy donor pledges funding to Bali contingent on Bali's liaison promoting the donor's preferred resource-sharing model to the coordination group. The mandate structure immediately surfaces the incompatibility: the liaison's mandate does not include advocating for positions determined by external parties. Bali's circle would need to adopt the model as their position before Rafi could represent it. The funding condition is documented as a capital capture risk. If the circle rejects the model on its merits, Rafi cannot represent it regardless of the funding offer. The structural separation between donor pressure and mandate scope protects the coordination group from external capital distortion.

### 2. Emergency Crisis

Flooding displaces Costa Rica SHUR members, creating urgent need for inter-SHUR resource coordination. Rafi's mandate covers communicating Bali's resource availability and exploring support options. For specific commitments (dollar amounts, hosting), Rafi flags to Bali's circle and requests an emergency consent session. The circle convenes within 24 hours under compressed timelines. They grant Rafi a time-limited emergency mandate extension. Throughout the crisis, Rafi operates as a rapid communication channel rather than a unilateral decision point. The emergency extension expires automatically at 30 days.

### 3. Leadership Charisma Capture

Rafi is widely liked across all three SHURs. Other ETHOS begin directing non-Economics requests to him -- housing, governance, member transfers. Rafi enjoys the expanded role. His June report lists topics outside the Economics domain. Bali's circle convenes a review: the mandate is scoped to Economics, and the informal expansion is not sanctioned. The circle communicates to other SHURs that cross-domain requests should route through cross-ethos-request or domain-specific liaisons. The mid-term check becomes mandatory. The rotation provision ensures this pattern cannot persist beyond the maximum 24-month term.

### 4. High Conflict

A significant policy disagreement emerges between Bali and Costa Rica about traveling member resource access. Rafi and Valentina find themselves as the coordination channel but cannot resolve the substantive dispute. Rafi's correct action: document the conflict in his reporting log, bring both positions accurately to Bali's circle, and flag polycentric-conflict-navigation as the appropriate escalation. The liaison role surfaces and routes conflicts; it does not absorb or informally resolve them. The coordination group continues on other topics while the conflict follows its own resolution path.

### 5. Large-Scale Replication

OmniOne grows to 15 SHURs with 5 coordination domains. The skill scales through two provisions: (a) domain-specific types mean each domain has its own liaison with its own mandate (recommended: one active liaison role per person at a time); (b) multilateral coordinators allow one person per ETHOS per domain rather than needing separate bilateral liaisons for each pair. With 15 SHURs and 5 domains, total roles are manageable. The agreement registry's cross-linked entries make the liaison network visible. Mandatory rotation prevents a permanent liaison class from forming.

### 6. External Legal Pressure

Indonesia requires inter-organizational coordination bodies to designate a legally recognized contact with authority to respond to government communications. This conflicts with the liaison's structural mandate (coordination without binding authority). Bali's response: designate a separate legal contact role through governance (not the liaison role), scoped specifically to regulatory communication. The liaison role remains structurally intact. External legal requirements do not reshape the liaison's mandate scope without going through Bali's consent process.

### 7. Sudden Exit of 30% of Participants

Six liaison role-holders across three SHURs exit simultaneously. The cross-ethos-request process handles all coordination during vacancies. Each home ETHOS documents in-progress threads within 14 days. Successor appointments begin within 30 days. No in-progress coordination thread creates binding obligation simply because a liaison was exploring it. The 30-day documentation period allows coordination groups to assess whether all vacant roles need immediate refilling or whether some can be consolidated.
