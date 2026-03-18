---
name: role-assignment
description: "Assign a person to a defined governance domain with scoped authority -- verifying competency, checking conflicts of interest, recording consent, and ensuring the separation of role and person so that authority is explicit and traceable."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, member-lifecycle]
---

# role-assignment

## A. Structural Problem It Solves

Without formal assignment, people assume roles informally. Authority scope remains undefined, and when disputes arise there is no record of who was authorized to act. The ecosystem defaults to whoever has the most confidence or social capital, which concentrates informal power and makes accountability impossible. This skill ensures every steward has explicit, consented-to authority -- traceable to a domain contract, a named assigning body, and a dated consent record. It enforces the principle that the role is a structural element and the person is assigned to it: the domain exists independently of any individual, and authority is held on behalf of the ecosystem, not accrued to the person.

## B. Domain Scope

This skill applies to any domain (as defined by the domain-mapping skill) that requires a human steward. It governs the moment of assignment -- the structural handoff of authority from an assigning body to a person. It does not govern ongoing role performance (that is domain-review) or role transitions (that is role-transfer). It references domain-mapping for the domain contract schema and member-lifecycle for participant status verification. Profiles (Co-creator, Builder, Collaborator, TownHall) are participation tiers and are outside this skill's scope -- domain authority is independent of platform access level.

## C. Trigger Conditions

- A new domain is created through the domain-mapping skill and requires a steward
- A domain becomes vacant: the previous steward has exited the ecosystem, completed a role-transfer, or a role-sunset of a predecessor role has created a successor domain
- A domain-review recommends reassignment of the current steward
- A delegating body identifies that an active domain has been operating without a formally assigned steward (informal role capture detected)

## D. Required Inputs

- **Domain contract** (mandatory): complete, not provisional -- all 11 elements must be filled; obtained from domain-mapping skill output
- **Candidate person** (mandatory): an individual in "active" lifecycle status per member-lifecycle records
- **Assigning body identity** (mandatory): the delegating body that created the domain and holds authority to assign its steward
- **Proposed assignment duration** (mandatory): specific term or "until next domain-review" -- no open-ended assignments
- **Conflict-of-interest disclosure** (mandatory): a list of all other active steward roles the candidate currently holds
- **Competency evidence** (optional): documentation the candidate or assigning body provides to demonstrate the domain contract's competency requirements are met

## E. Step-by-Step Process

1. **Verify domain contract completeness.** The assigning body confirms the domain contract has all 11 elements filled and its status is "active" (not "provisional"). A provisional domain contract must be completed before assignment proceeds.

2. **Verify candidate lifecycle status.** Confirm the candidate is in "active" status in the member-lifecycle registry. Inactive, onboarding, or exiting members cannot be assigned. If the candidate is in reactivating status, wait until the reactivation is complete.

3. **Check competency requirements.** The assigning body evaluates the candidate against the competency element of the domain contract. Verification method: the assigning body makes the determination, with input from any outgoing steward. No external certification is required. Partial competency (meets some but not all requirements) is permitted if the candidate commits to addressing gaps within the first review period, documented in the assignment record.

4. **Candidate reviews and accepts the domain contract.** The candidate reads the full domain contract -- especially constraints, metrics, and evaluation schedule. The candidate formally accepts or negotiates terms. Negotiable items: metric targets (within a defined first-period window), resource adjustments, and clarifications to deliverables. Non-negotiable: purpose, constraints that bound the domain, or delegator responsibilities. If the candidate proposes changes to non-negotiable elements, those changes must route through the domain-mapping amendment process before assignment proceeds.

5. **Conflict-of-interest check.** The candidate discloses all other active steward roles. The assigning body maps each against the candidate domain's 11 elements. If domain overlap exists (shared responsibilities, shared customers, or shared deliverables), the overlap is flagged in the assignment record and an authority-boundary-negotiation is scheduled. The assignment may proceed with the flag recorded, but the boundary negotiation must be completed within 30 days.

6. **Assigning body consent process.** The assigning body runs a consent round on the proposed assignment. Standard domains: consent (no reasoned objection). OSC-level roles (roles whose domain was delegated by the OSC): consensus (all OSC members agree). Self-nomination requires extra scrutiny -- the consent round must explicitly surface reasons the candidate is better positioned than alternatives. Self-assignment (where the candidate is the sole decision-maker) is prohibited.

7. **Register the assignment.** Record the assignment using the role-assignment-template.yaml asset. Fields: assignment ID, domain ID, domain contract version, assignee member ID, assigning body, assignment date, review date, assignment duration, status, competency verification record, conflict-of-interest record, and consent record ID.

8. **Notify adjacent domains.** All domains listed in the assigned domain's dependencies element receive notification of the new steward. Adjacent stewards are named in the assignment record.

## F. Output Artifact

A role assignment record following `assets/role-assignment-template.yaml`, containing: unique assignment ID, linked domain ID and contract version, assignee member ID, assigning body identity, assignment date, review date, assignment duration, status (active), competency verification summary, conflict-of-interest disclosure and any flagged overlaps, and the consent record ID. The record is registered in the ecosystem's assignment registry and linked to the domain contract's assignment history. Access: readable by all active ecosystem participants, editable only by the assigning body.

## G. Authority Boundary Check

Only the delegating body that created the domain (per the domain contract's "created_by" field) can assign its steward. No individual steward can self-assign to a domain. The delegating body cannot assign a steward to a domain they did not create without first obtaining authority transfer through the domain-mapping amendment process. Role cap: no individual should hold more than 3 active steward roles simultaneously -- this is the recommended maximum, configurable per ecosystem, with a floor of 1. Dual-role overlap must be disclosed at assignment time; the assigning body cannot waive the disclosure requirement. Competency verification authority rests with the assigning body; it cannot be delegated to the candidate themselves.

## H. Capture Resistance Check

**Role accumulation capture.** A single person collects multiple steward roles to consolidate informal power. The 3-role cap limits accumulation. The conflict-of-interest disclosure surfaces overlaps. Domain-review cycles evaluate whether a steward's multi-role holding is creating decision-making concentration; if so, role-transfer is recommended.

**Competency theater.** The assigning body rubber-stamps competency verification to assign a preferred candidate regardless of qualifications. The competency element in the domain contract is written by the delegating body before the candidate is known -- this pre-commitment prevents post-hoc tailoring. Any partial-competency finding must be documented and the gap-closure plan made explicit.

**Forced assignment.** Someone is pressured into accepting a steward role they do not want. Step 4 requires explicit candidate acceptance -- a candidate can decline without stated reason and the process terminates. The assigning body must find a willing candidate.

**Informal role holding.** Someone acts as a steward without formal assignment, building precedent-based authority. This skill provides the structural remedy: informal role holding is detected during domain-review and triggers a retroactive role-assignment process or domain-mapping clarification. Unregistered stewards have no standing in governance decisions.

## I. Failure Containment Logic

**Domain contract is incomplete (provisional).** The assignment process halts at Step 1. The assigning body must complete the domain contract before assignment can proceed. The domain remains vacant during this period.

**Candidate is inactive.** The assignment process halts at Step 2. If the assigning body had an informal arrangement with this candidate, that arrangement is not a valid assignment. The assigning body must identify a new candidate or trigger member-lifecycle reactivation.

**Candidate declines after reviewing domain contract.** The process terminates at Step 4. The domain returns to vacant status. The assigning body may open a new candidate selection. Persistent vacancy (no candidate found within one review cycle) triggers an escalation to the delegating body to evaluate whether the domain-mapping should be revised to attract a steward, or whether role-sunset is appropriate.

**Consent fails.** If the assigning body does not reach consent on the proposed assignment, the domain remains vacant. The assigning body may bring a different candidate or revise the domain contract to address objections. Escalation to GAIA Level 4 if two assignment attempts fail.

**Conflict-of-interest boundary negotiation not completed within 30 days.** The assignment record is flagged as overdue. The assigning body is notified. If not resolved within 60 days, the assignment is suspended pending negotiation.

## J. Expiry / Review Condition

Every assignment has a defined review date set at registration. Default review cadence: aligned with the domain's evaluation schedule (default 6 months). The assignment expires at the review date unless renewed through a domain-review outcome that confirms reassignment of the same person. A renewed assignment creates a new assignment record version (same assignment ID, incremented version). Assignments without review dates are flagged as incomplete by validate_skill.py. If a review date is missed, the assigning body receives a 14-day escalation notice; if still not addressed, the domain-review skill is triggered automatically.

## K. Exit Compatibility Check

When a steward exits the ecosystem, their role assignment enters "transferring" status immediately. The domain enters "vacant" status after 30 days if no role-transfer has been completed. Pending commitments held under the role (active agreements, in-progress decisions) are inventoried by the exiting steward as part of the exit process; inventory is stored in the assignment record. The exiting steward's authority ceases at the formal transfer date, not at the announcement of their exit. All governance decisions made by the exiting steward while their assignment was active remain valid.

## L. Cross-Unit Interoperability Impact

When a steward role spans two ETHOS (a domain that serves participants in multiple organizational units), the assignment requires consent from the delegating bodies of both ETHOS. The assignment record is registered in both ETHOS' registries with linked entries. Notification goes to all adjacent domains across all ETHOS in which the assigned domain has listed dependencies. Cross-ETHOS role assignments are tagged in the registry for cross-unit coordination review at the 6-month evaluation.

## OmniOne Walkthrough

The AE has just ratified a new Economics circle domain contract through the domain-mapping skill. The domain contract is complete: all 11 elements filled, status "active," created by the AE, with a 6-month evaluation schedule. The AE, as the delegating body, opens a steward assignment process.

Keoni, a Co-creator with three years of experience coordinating commons-based resource pools in another ETHOS, is nominated. The AE facilitator runs Step 2: the member-lifecycle registry confirms Keoni's status is "active." Step 3: the AE reviews the Economics circle's competency element -- "understanding of commons-based economics, facilitation skills, financial transparency practices." Keoni's prior ETHOS work is presented as evidence. The AE finds competency met on the first two requirements and partial on the third (financial transparency practices). The partial finding is documented: Keoni will attend two ecosystem transparency training sessions within the first 60 days. The gap-closure commitment goes into the assignment record.

Step 4: Keoni reviews the full domain contract. Keoni accepts the purpose and constraints without objection but requests one metric adjustment: the time-to-decision target of 14 days extended to 21 days for the first evaluation period, given the circle is new and building process. The AE agrees this is a metric-level negotiation (not a structural change) and accepts the amendment. The domain contract is updated accordingly.

Step 5: Keoni's conflict-of-interest disclosure lists one other active role -- steward of the Partnerships circle. The AE maps the two domain contracts against each other. The Partnerships circle lists "coordinate with external partners on economic matters" as a key responsibility; the Economics circle also lists "coordinate with external partners on economic matters." The overlap is flagged. The assignment proceeds with the flag documented, and an authority-boundary-negotiation between Economics and Partnerships is scheduled for the following week.

Step 6: The AE runs a consent round. Eight AE members participate. Mia raises a concern: "Keoni is our best contributor but three roles feels like too much -- they also steward the Design sprint process." The facilitator clarifies: the role cap is 3 active steward roles, and this would be Keoni's third. The concern is noted in the record. Integration round: Mia and the AE discuss whether to proceed or find an alternative candidate. Mia's concern is acknowledged but not a blocking objection -- Keoni is willing, meets competency, and the 3-role situation will be revisited at the 6-month review. Consent achieved.

Step 7: The assignment is registered. Assignment ID: ASGN-ECON-2026-001. Review date: 2026-09-03. Steps 8: The Stewardship circle (listed as a dependency in the Economics domain contract) is notified that Keoni is now the Economics circle steward.

Edge case: Keoni holds a Builder profile (commenting-level platform access), not Co-creator (editing access). This does not affect governance authority. Domain authority is conferred by the assignment record, not by platform access level. Keoni can steward the Economics circle -- making funding decisions, running consent rounds, registering agreements -- regardless of their platform editing permissions. The two systems are structurally independent.

## Stress-Test Results

### 1. Capital Influx

A major donor offers to fund OmniOne on the condition that their designated representative is assigned as steward of the Economics circle. The role-assignment process structurally prevents this: Step 6 requires the assigning body (the AE) to run a consent round -- the donor's funding condition does not grant the donor's representative proposal-routing privileges or bypass the competency check. During Step 3, the AE evaluates the designated representative against the Economics domain's competency element. If the representative does not meet the competency requirements, the assignment halts regardless of funding at stake. During the consent round, any AE member can raise a reasoned objection that the proposed assignment was initiated under capital pressure rather than structural merit -- that objection must be substantively addressed before consent is achieved. The capture vector is documented in the assignment record as a conflict-of-interest flag: the candidate's primary affiliation creates a financial interest in the domain's decisions. The AE may decline the assignment and invite the donor's representative to apply through normal nomination channels.

### 2. Emergency Crisis

A flood damages SHUR Bali, the Economics circle steward (Keoni) is unreachable, and three urgent funding requests need a decision-maker. The assigning body (AE) invokes an emergency assignment under compressed timeline: the domain contract already exists, so Step 1 is immediate. The AE identifies an alternate candidate (Priya, a Co-creator with financial coordination experience) and runs an emergency consent round with 24-hour window and a minimum 50% AE quorum. Competency verification is abbreviated but not waived -- the AE records that Priya meets the minimum competency threshold for emergency scope. The emergency assignment is registered with a 30-day expiry and a flag requiring full review when Keoni is reachable. If Keoni returns within 30 days, the emergency assignment is superseded and the original assignment is reinstated. If Keoni cannot return, a standard role-transfer process begins. Emergency assignments are structurally reversible by design.

### 3. Leadership Charisma Capture

A well-respected OmniOne founder proposes to assign themselves as steward of the newly created Governance Infrastructure circle. Self-nomination is permitted, but self-assignment is not: Step 6 explicitly prohibits the candidate from being the sole decision-maker in the consent round. The AE facilitator runs the consent round -- the founder's social capital does not translate into consent-phase authority. Two AE members raise reasoned objections: the founder already stewards two other circles (at the 3-role cap), and their history of informal authority-expansion creates a structural risk. The integration rounds require the founder to substantively address both concerns, not merely reassure. The first objection is addressed: the founder proposes sunsetting one existing role within 60 days if assigned. The second objection requires the AE to document the domain's constraints explicitly and schedule a 3-month check-in in addition to the 6-month review. With both objections addressed structurally, consent is achieved. The 3-month check-in is built into the assignment record -- social capital does not eliminate the structural safeguard.

### 4. High Conflict / Polarization

Two factions within the AE disagree about who should steward the Stewardship circle. Faction A nominates Lena, a long-term Co-creator with deep community trust. Faction B nominates Ryo, a newer Co-creator with stronger process expertise. Both candidates meet competency requirements. The consent round produces objections from both factions about the other's candidate. After two integration rounds fail to resolve the deadlock, the assigning body escalates to GAIA Level 4 (Coaching). A coach maps the underlying tension: Faction A values continuity and relational trust; Faction B values process rigor. The coach facilitates a structural resolution: the Stewardship circle domain contract is amended to split the role into two steward positions (permitted under domain-mapping) -- Lena holds the community stewardship function and Ryo holds the process accountability function. Both candidates are assigned to their respective sub-roles through separate consent rounds. The factional deadlock dissolves because both concerns are honored in the domain structure rather than resolved through political victory.

### 5. Large-Scale Replication

OmniOne grows from 30 participants across 8 circles to 800 participants across 90 circles. Role assignment scales through the same process because it is domain-scoped: assigning a steward to a small Design sprint circle involves only the 5 members of that circle's delegating body, not all 800 participants. The assignment registry becomes the navigational tool: any participant or AI agent can query it by domain ID to find the current steward. The 3-role cap prevents any single person from becoming a bottleneck across many domains. At 90 circles, the ecosystem has approximately 30+ active stewards (assuming some dual-role situations), distributing governance load structurally. The conflict-of-interest check becomes more computationally complex at scale but remains algorithmically straightforward: map all domains held by a candidate against the target domain's 11 elements. The validate_skill.py pattern applies uniformly: every assignment record must be registered, every domain must have a review date, every conflict must be documented.

### 6. External Legal Pressure

The Indonesian government issues a regulation requiring all co-living community resource managers to hold a government-registered certification. The Economics circle steward role falls within this scope for the SHUR Bali ETHOS. The certification requirement does not modify the role-assignment process -- it adds a new competency to the Economics domain's competency element, which the AE updates through the domain-mapping amendment process. Future role assignments for the Economics steward role (SHUR Bali ETHOS only) include the certification as a competency requirement. Existing assignments are grandfathered with a 90-day compliance window documented in their assignment records. The regulation applies to the SHUR Bali ETHOS specifically; it does not propagate to Economics roles in other ETHOS unless those ETHOS fall under the same jurisdiction. NEOS governance principles and the legal compliance requirement coexist: the certification is a competency check, not a governance override.

### 7. Sudden Exit of 30% of Participants

Fifteen of fifty active participants exit OmniOne within two weeks following a contentious ecosystem decision. Seven of the exits include active stewards across multiple circles. Each exiting steward's role enters "transferring" status. The 30-day vacancy window activates for each domain. The assigning bodies prioritize by domain criticality: the Economics and Stewardship steward vacancies are addressed first (P0 functions), the Design sprint and Culture Code steward vacancies are addressed second. Where no qualified candidate is immediately available, the delegating body assumes temporary stewardship authority per the domain contract's "delegator responsibilities" element. All governance decisions made by departing stewards while their assignments were valid remain valid -- departure does not retroactively invalidate their authority. The assignment registry flags all seven vacancies and tracks the 30-day window. If no steward is assigned within 30 days, the domain formally escalates to the delegating body for a sunset decision.
