---
name: role-assignment
description: "Assign a person to a defined governance domain with scoped authority -- verifying competency, checking conflicts of interest, recording consent, and ensuring the separation of role and person so that authority is explicit and traceable."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, member-lifecycle]
---

# role-assignment

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
