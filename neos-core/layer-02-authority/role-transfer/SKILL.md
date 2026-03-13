---
name: role-transfer
description: "Hand off a governance role from one steward to another without losing institutional knowledge or continuity -- structured handover with overlap period, commitment inventory, and formal reassignment through the assigning body."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, role-assignment]
---

# role-transfer

## A. Structural Problem It Solves

Without a transfer process, role changes are abrupt. The outgoing steward leaves and takes their context with them — pending commitments fall through cracks, adjacent domains discover the change only when their counterpart stops responding, and the incoming steward inherits a domain they do not understand. Institutional knowledge is not a luxury; it is the accumulated memory of why things are the way they are. This skill ensures that no role changes stewards without a structured handover that captures pending commitments, active agreements, decision context, and the relationship map of adjacent domains. It also ensures the assigning body formally authorizes the transfer rather than allowing informal succession, which is the entry point for capture.

## B. Domain Scope

This skill applies to any role assignment that is changing stewards — whether the outgoing steward is stepping down voluntarily, rotating out on schedule, being reassigned following a domain-review, transitioning to inactive status per the member-lifecycle skill, or handing off responsibilities because a predecessor role is being sunset. The scope covers the period from transfer initiation through the 30-day post-transfer check-in. It does not cover: the creation of a new role (domain-mapping), the initial assignment to a new role (role-assignment), the decision to reassign based on performance (domain-review), or the dissolution of a role with no successor (role-sunset).

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

**Cross-AZPO transfers** — where a role bridges or moves between AZPOs — require coordination between both AZPOs' delegating bodies. Each delegating body must consent from their side. The relationship map in the handover document must explicitly include all cross-AZPO contacts. Transfer records for cross-AZPO roles are registered in both AZPOs' registries with linked entries. Notification of dependent and adjacent domains includes all cross-AZPO parties in the relationship map.

## OmniOne Walkthrough

The OSC meeting facilitator role operates on a 6-month rotation. Kenji, who has served as facilitator for one term, is rotating out. Malia has been selected through the role-assignment process and has accepted the domain contract.

Kenji prepares the handover document using the checklist. He inventories: three agenda items in active deliberation (one GAIA Level 3 escalation, one proposed OSC policy, one pending boundary resolution between two AE circles), relationship notes for each of the five council members (what each person values in facilitation, who tends to need extra time in rounds), and a known challenge — one council member communicates primarily in Bahasa Indonesia and English summaries sometimes lose nuance.

During the overlap period (3 weeks, matching the OSC's bi-weekly meeting cadence), Malia attends two OSC sessions with Kenji. Kenji runs the first; Malia runs the second with Kenji present. Kenji formally introduces Malia to each council member and to the AE circle stewards involved in the pending boundary resolution.

**Edge case:** During overlap, Malia reviews the pending GAIA Level 3 escalation and realizes it is unresolved and approaching its 30-day window — the escalation was triggered 28 days ago. She flags this to Kenji: "I am not willing to accept this transfer with an unresolved escalation at day 28 unless we either resolve it before transfer or you remain on record as responsible through resolution." The OSC convenes an expedited session, resolves the escalation, and the transfer proceeds. The transfer record notes the resolution.

The OSC consents to the transfer. Malia's assignment record is created. All council members and relevant AE stewards are notified. Thirty days later, Malia and the OSC confirm the check-in: all deliberation items are resolved or in active process, no orphaned commitments have surfaced, and a bilingual note-taker has been added to address the language challenge.

**Output artifact:** Transfer record TRF-OSC-FACIL-2026-001 with handover summary, overlap session log (2 joint sessions), consent record, and post-transfer check-in status: complete.

## Stress-Test Results

### 1. Capital Influx

A major donor offers to fund OmniOne's operations for two years on the condition that their preferred candidate — a person affiliated with their foundation — is placed into the vacant Economics circle steward role. The role-transfer skill's authority structure prevents this: the delegating body (AE) controls role-assignment and the assigning body controls transfer authorization, neither of which can be delegated to a funder. The incoming steward must pass competency verification independently, and the consent process evaluates the candidate on domain contract grounds, not on the donor's preference. If the donor's candidate does happen to qualify through the role-assignment process legitimately, the transfer proceeds normally — but the donor's financial offer is not a factor in the consent round and is documented as a capture risk in the transfer record. The handover document is produced by the outgoing steward, not the donor, ensuring no external party can shape what institutional knowledge is passed on.

### 2. Emergency Crisis

A flood displaces the SHUR Bali coordinator mid-role, making them unavailable. The role-transfer skill's emergency handover clause activates: the delegating body assumes temporary stewardship and reconstructs the handover document from available records (agreement registry, prior governance session logs, pending commitment trackers). A qualified incoming steward is identified through an expedited role-assignment process — compressed timelines apply but competency verification is not skipped. The overlap period is shortened to the minimum viable window given the crisis, with sessions conducted remotely. The transfer record is marked "emergency handover" and the post-transfer check-in at 30 days is mandatory to surface any items the reconstructed handover document missed. The temporary delegating body stewardship does not become permanent: once the incoming steward is assigned, full domain authority transfers.

### 3. Leadership Charisma Capture

A well-respected OSC member — widely considered the "heart" of the council — announces they are stepping down as meeting facilitator and publicly names their preferred successor, creating social pressure for the AE to simply ratify their choice. The role-transfer skill holds: the outgoing steward can recommend a successor but the delegating body runs the role-assignment process independently. If the recommended candidate does not pass competency verification or the consent round surfaces objections that cannot be integrated, the transfer does not proceed on social goodwill alone. The outgoing steward is explicitly excluded from the assigning body's consent round on the transfer (Step 5), preventing their endorsement from functioning as a vote. Participants who feel social pressure to consent to the transfer without objection are protected by the consent structure: an objection is a structural contribution, not an insult to the departing steward.

### 4. High Conflict / Polarization

Two factions within the AE have opposing views on who should steward the Economics circle after the previous steward steps down. Faction A supports a candidate with strong financial transparency experience; Faction B supports a candidate with stronger community relationships. The role-assignment process evaluates both candidates against the domain contract's competency element — not against faction preference. If neither candidate achieves consent in the role-assignment round, the delegating body escalates to GAIA Level 4 (Coaching), where a coach helps the AE identify whether the conflict is genuinely about competency or about factional positioning. The coach may surface a third option — a temporary joint-stewardship arrangement or a modified domain contract that allows a phased assignment. Whatever path is chosen, the transfer record accurately reflects the trigger and the consent process used, creating a precedent record for future reference.

### 5. Large-Scale Replication

OmniOne grows to 200 circles across 15 AZPOs, and role transfers happen continuously — an estimated 3-5 per week at steady state. The role-transfer skill scales because the process is document-driven: each transfer produces a self-contained transfer record that does not require ecosystem-wide awareness. The handover checklist is standardized, so incoming stewards everywhere receive consistent information regardless of which circle they are joining. The relationship map and notification requirement ensure that at-scale transfers do not create information voids in adjacent domains — the burden is on the transferring role, not on adjacent domains to notice the change. The delegating body's consent requirement keeps transfers locally authorized without requiring OSC involvement except for OSC-level roles.

### 6. External Legal Pressure

An Indonesian regulatory body requires that any governance role with financial authority must be held by a registered Indonesian legal entity, not an individual. This external constraint does not automatically trigger a forced transfer — it enters the ecosystem as information, surfaces during the next domain-review, and triggers a deliberate transfer process. The affected role's domain contract is refined to reflect the legal constraint (adding it to the constraints element), and the role-assignment process identifies a qualified entity or representative who satisfies both the legal requirement and the domain's competency requirements. The transfer record documents the legal trigger alongside the standard governance process, maintaining the full paper trail. The UAF sovereignty principle applies: individual members comply with their local legal obligations without those requirements automatically overriding NEOS governance structures.

### 7. Sudden Exit of 30% of Participants

Following a major disagreement about OmniOne's expansion strategy, 15 of 50 participants exit within two weeks, including 4 active role stewards. All 4 domains enter vacant status simultaneously. The delegating body assumes temporary stewardship across all 4 and prioritizes by domain criticality: the two domains with the most active pending commitments receive role-assignment urgency. The remaining two domains are assessed — one can be temporarily absorbed by an adjacent domain, the other can sustain vacancy for 30 days without critical commitments collapsing. The handover documents for the departed stewards are reconstructed from available records; the 30-day post-transfer check-ins for all four eventual incoming stewards are staggered but all are mandatory. The sudden exit is itself a threshold event that triggers domain-review for all four affected domains — the incoming stewards step into domains that are freshly evaluated, not domains operating on stale domain contracts.
