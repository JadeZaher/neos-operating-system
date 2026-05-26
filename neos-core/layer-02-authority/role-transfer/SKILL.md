---
name: role-transfer
description: "Hand off a governance role from one steward to another without losing institutional knowledge or continuity -- structured handover with overlap period, commitment inventory, and formal reassignment through the assigning body."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, role-assignment]
---

# role-transfer

## C. Trigger Conditions

- Voluntary step-down: the current steward declares intent to leave the role
- Scheduled rotation: the domain contract specifies a term length and the term is ending
- Domain-review recommendation: a review body determines reassignment serves the domain
- Steward inactive status: per the member-lifecycle skill, the steward has been inactive for 1 month and the domain cannot remain vacant
- Role-sunset creating a successor role: responsibilities are transferring to a new domain that requires formal handover

## D. Required Inputs

- **Outgoing steward identity**: the current steward and their active assignment record
- **Incoming steward identity**: identified through the role-assignment process; must be in active lifecycle status
- **Domain contract**: the current version including all 11 elements — especially pending metrics, active constraints, and evaluation schedule
- **Active agreements held**: any agreements where this role is listed as steward, party, or responsible party
- **Pending commitments inventory**: open commitments, in-progress deliverables, scheduled decisions, and unresolved escalations
- **Relationship map**: list of adjacent and dependent domains with named contacts

## E. Step-by-Step Process

1. **Outgoing steward creates handover document.** Using the handover-checklist (`assets/handover-checklist.md`), the outgoing steward inventories: all pending commitments with current status and deadlines, all active agreements held by this role, decision context (why current practices exist, background on ongoing situations), a relationship map of adjacent and dependent domain stewards, known challenges the incoming steward should anticipate, and upcoming deadlines within the next 60 days. The handover document is not optional — the transfer cannot proceed without it.

2. **Incoming steward reviews domain contract and handover document.** The incoming steward reads the full domain contract and the handover document and raises any questions or concerns in writing. Open items must be acknowledged explicitly — silence does not count as informed acceptance.

3. **Overlap period — minimum 2 weeks.** During the overlap, both stewards attend governance sessions together. The outgoing steward introduces the incoming steward to adjacent domain stewards. The outgoing steward remains responsible for decisions until formal transfer is complete but begins delegating to the incoming steward. If the incoming steward raises concern about any open item they are not willing to inherit without resolution, the outgoing steward must resolve it or obtain the incoming steward's explicit written acceptance before the transfer finalizes.

4. **Incoming steward formally accepts the domain contract.** The incoming steward signs off on the domain contract using the same acceptance process as role-assignment, including any outstanding open items that were explicitly documented and accepted.

5. **Assigning body consents to the transfer.** The delegating body runs a consent round on the transfer. Consent covers the transfer of role authority, not a re-evaluation of the incoming steward's competency (assessed during role-assignment). The outgoing steward does not vote in this round.

6. **Assignment records updated.** The outgoing steward's assignment record is marked "transferred" with the transfer date. The incoming steward's assignment record is created with start date, review date (inherited from or reset per the domain contract), and a link to the transfer record.

7. **Notify dependent and adjacent domains.** All domains listed in the relationship map receive formal notification of the transfer with the incoming steward's name and contact. This is structural courtesy, not a request for approval.

8. **30-day post-transfer check-in.** The incoming steward and delegating body confirm the transfer is operationally complete: all pending commitments have been actioned, no orphaned items have surfaced, and the incoming steward has the access and context needed to operate independently.

## F. Output Artifact

A transfer record following `assets/transfer-record-template.yaml`, containing: transfer ID, domain ID, domain contract version, outgoing steward, incoming steward, transfer trigger, handover document summary (pending commitments, active agreements, decision context, relationship map, known challenges, upcoming deadlines), overlap period dates and sessions attended together, consent record ID from the assigning body, transfer date, and post-transfer check-in date and status. The transfer record is linked to both stewards' assignment records.

## G. Authority Boundary Check

- Only the **assigning body (delegating body)** can authorize the transfer. The outgoing steward cannot unilaterally name their successor — they can recommend but the delegating body decides.
- The **incoming steward must undergo the full role-assignment acceptance process**, including domain contract review and acceptance, even if they are already a member of the same circle. There is no abbreviated succession.
- **No one can be forced into a role they do not accept.** If the proposed incoming steward declines, the transfer process pauses and the delegating body identifies an alternative candidate.
- **During the overlap period**, authority formally remains with the outgoing steward until Step 5 (assigning body consent) is complete. The incoming steward has learning access, not decision authority.
- For **OSC-level roles**, the consent process uses consensus mode rather than standard consent, per the role-assignment skill.

## H. Capture Resistance Check

**Knowledge hoarding.** An outgoing steward withholds information — leaving out decision context, suppressing knowledge of a pending problem, or describing the relationship map incompletely. The mandatory handover checklist specifies required fields, and the 30-day post-transfer check-in surfaces gaps. If the incoming steward discovers material omissions after transfer, the outgoing steward can be called back for supplemental handover.

**Successor capture.** A powerful faction uses the vacancy to install their preferred person by bypassing the role-assignment process. This skill requires the incoming steward to go through full role-assignment — the delegating body cannot skip competency verification or the candidate's domain contract review.

**Forced transfer.** A steward is pressured out of their role without cause, with the transfer framed as voluntary. The transfer trigger field in the transfer record must accurately reflect whether the transfer is voluntary, a rotation, or a reassignment. Involuntary transfers (where the steward objects) route to GAIA escalation before proceeding.

**Overlap theater.** The overlap period is treated as a formality — a brief handoff called "2 weeks." The overlap period is measured by sessions attended together, documented in the transfer record, not by calendar days alone.

## I. Failure Containment Logic

**Involuntary transfer (steward objects to being replaced).** The transfer is paused. The objection routes to the delegating body for structured review. If unresolved, it escalates to GAIA Level 4 (Coaching). No transfer proceeds against a steward's explicit, documented objection without either resolution of the objection or OSC-level consensus.

**No qualified incoming steward.** If the role-assignment process cannot identify a qualified candidate, the domain enters "vacant" status. The delegating body assumes temporary stewardship — enough to keep critical commitments from collapsing — and has 30 days to identify a candidate before triggering domain-review.

**Incomplete handover document.** The handover document must pass the mandatory checklist before the overlap period begins. If the outgoing steward submits an incomplete handover, the delegating body can require supplemental documentation. The transfer timeline pauses; the outgoing steward's responsibility does not.

**Outgoing steward exits unexpectedly during transfer.** Handover responsibilities fall to the delegating body, which reconstructs the handover document from available records and marks the transfer "emergency handover" in the transfer record. The incoming steward's 30-day check-in is mandatory in this scenario.

**Incoming steward exits during transfer.** If the incoming steward leaves before taking authority, the transfer reverses. The outgoing steward resumes full responsibility if available, or the domain enters vacant status.

## J. Expiry / Review Condition

The transfer record is a historical record, not an ongoing agreement, and has no review cycle of its own. The **incoming steward's assignment** carries a review date per the domain contract's evaluation schedule. If the domain contract was reset during transfer (e.g., following a domain-review that triggered the reassignment), the new review date is established at that point. The 30-day post-transfer check-in is a mandatory milestone confirming operational completeness — it is not a full domain review.

## K. Exit Compatibility Check

If the **outgoing steward exits the ecosystem** during or after the transfer: handover responsibilities transfer to the delegating body if the transfer is not yet complete; the outgoing steward retains rights to any original works they created in the role; post-transfer obligations (supplemental handover questions, 30-day check-in participation) are best-effort and cannot be compelled after exit.

If the **incoming steward exits within the 30-day post-transfer window**, the domain re-enters vacant status and the role-assignment process restarts. Pending commitments accepted in the transfer record remain the incoming steward's personal obligations for the 30-day wind-down period unless formally transferred to the delegating body.

## L. Cross-Unit Interoperability Impact

**Cross-ETHOS transfers** — where a role bridges or moves between ETHOS — require coordination between both ETHOS' delegating bodies. Each delegating body must consent from their side. The relationship map in the handover document must explicitly include all cross-ETHOS contacts. Transfer records for cross-ETHOS roles are registered in both ETHOS' registries with linked entries. Notification of dependent and adjacent domains includes all cross-ETHOS parties in the relationship map.
