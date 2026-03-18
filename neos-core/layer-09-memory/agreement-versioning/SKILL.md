---
name: agreement-versioning
description: "Track the full version history of every living agreement with immutable snapshots, diffs, and rationale -- so no one can claim a change was never consented to."
layer: 9
version: 0.1.0
depends_on: [agreement-registry, agreement-amendment, agreement-review]
---

# agreement-versioning

## A. Structural Problem It Solves

Agreements change over time through amendments, reviews, and partial sunsets, but without formal versioning, the history of those changes disappears. A participant who joined after three amendments cannot determine what the original agreement said, why it changed, or whether each change was properly consented to. Disputes arise: "This clause was never part of the agreement" or "That amendment was never approved." Without version control, these disputes devolve into competing memories with no structural resolution. The agreement-versioning skill solves this by applying Git-style version control to governance documents. Every change is a committed snapshot with a diff, author, date, rationale, and approval record. The full history is preserved, immutable, and queryable. Rollback is never an undo -- it is a new amendment through the ACT process, preserving the complete chain of governance decisions.

## B. Domain Scope

This skill applies to every agreement registered through the agreement-registry skill (Layer I), across all domains and ETHOS. It covers: version creation when agreements are created, amended, or reviewed; diff generation between any two versions; history queries; and rollback proposals. The skill extends the agreement-registry with formal versioning but does not replace it -- the registry tracks agreement status and affected parties; versioning tracks the document's evolution over time. Out of scope: versioning of non-agreement governance artifacts (decision records, domain contracts) -- those are tracked through the decision-record skill's lifecycle fields. Also out of scope: the technical implementation of diff algorithms or storage systems.

## C. Trigger Conditions

- An agreement is created through the agreement-creation skill -- version 1.0.0 is automatically generated
- An agreement is amended through the agreement-amendment skill -- a new minor or major version is generated
- An agreement-review produces changes -- a new version is generated reflecting the review outcome
- A participant queries the version history of an agreement to understand its evolution
- A participant requests a diff between two versions to see what changed
- A participant proposes a rollback to a previous version through the ACT process

## D. Required Inputs

- **Agreement identifier**: the agreement's unique ID from the agreement-registry (provided by the originating skill)
- **Current agreement text**: the full text of the agreement at this version (provided by the originating skill's output artifact)
- **Previous version**: the immediately preceding version's snapshot, for diff generation (retrieved from the version history)
- **Change rationale**: why this change was made (provided by the amendment or review process)
- **Source skill**: which skill produced this version (agreement-creation, agreement-amendment, or agreement-review)
- **Approval record**: the consent or consensus record ID that authorized this change (from the ACT process)
- **Author**: the participant who authored or facilitated the change

## E. Step-by-Step Process

1. **Generate version number.** When a new version is triggered, assign a semver number following the convention: **major** (X.0.0) for structural changes that alter the agreement's fundamental scope, parties, or governance mechanism; **minor** (x.Y.0) for substantive amendments that add, remove, or modify clauses within the existing structure; **patch** (x.y.Z) for clarifications, typo corrections, or formatting changes that do not alter governance meaning. The version number assignment is documented with rationale.

2. **Create snapshot.** Capture the full text of the agreement at this version as an immutable snapshot. The snapshot is the complete agreement document as it stands after the change is applied -- not a fragment or a diff-only record. The snapshot is timestamped and linked to the author and source skill.

3. **Generate diff.** Compare the current snapshot against the immediately preceding version's snapshot. The diff identifies: added text, removed text, and modified text with surrounding context. For version 1.0.0 (initial creation), the diff is marked "initial version -- no prior version exists." The diff is human-readable, not a raw technical diff.

4. **Record metadata.** Attach the version record to the agreement's version history. The record includes: version number, snapshot, diff, author, date, rationale, source skill, approval record ID, and the version number convention rationale. See `assets/version-record-template.yaml` for the full schema.

5. **Verify immutability.** Once a version record is created, it cannot be modified. No participant can edit a historical snapshot, alter a diff, change the author attribution, or modify the approval record reference. The governance memory steward monitors for any attempted retroactive edits. If an error is discovered in a version record (e.g., wrong approval record ID), the correction is appended as an annotation, not an edit to the original record.

6. **Enable history queries.** Any participant can query the version history of any agreement. Available queries: retrieve all versions in chronological order, retrieve a specific version by number, retrieve the diff between any two versions (not just consecutive ones), retrieve the current (latest) version, and retrieve all versions that changed a specific clause or section (if the agreement uses a structured format).

7. **Process rollback proposals.** If a participant believes a version is problematic and the agreement should revert to a previous version's state, they propose a rollback. The rollback is not an undo -- it is a new amendment through the ACT process. The proposal references the target version, explains why the current version is problematic, and justifies reverting. If consent is achieved, a new version is created with the target version's content as its snapshot. The version history shows the full chain: v1.0.0 -> v1.1.0 (problematic) -> v1.2.0 (rollback to v1.0.0 content). The rollback version's rationale documents what happened and why.

## F. Output Artifact

A version record appended to the agreement's version history, following `assets/version-record-template.yaml`. The record contains: version number (semver), full agreement snapshot, diff from previous version, author, date, change rationale, source skill, approval record ID, and version number convention rationale. The version history is an ordered, immutable sequence of these records. Any participant can access any version record for any agreement. The agreement-registry links to the version history, and the version history links back to the registry entry. Version records are referenced by agreement ID and version number (e.g., AGR-OMNI-2025-007-v1.1.0).

## G. Authority Boundary Check

Version creation is automatic and mandatory -- it is triggered by agreement-creation, agreement-amendment, and agreement-review, and cannot be bypassed. The author of the version record is the facilitator or author of the originating skill process. No participant can suppress a version (omitting a version from the history). No participant can edit a historical version -- immutability is absolute. The governance memory steward monitors version history integrity but cannot alter records. Rollback authority follows the same consent process as agreement-amendment: the circle or body that holds domain authority over the agreement processes the rollback proposal through ACT. Version number assignment follows the convention defined in Step 1; disputes about version number classification (is this a minor or major change?) are resolved by the original deciding body.

## H. Capture Resistance Check

**Capital capture.** Financial contributors cannot influence version histories. A donor who funded an amendment cannot suppress the version record showing what the agreement said before their preferred change. The immutable snapshot chain means every state of the agreement is permanently visible, regardless of who funded changes.

**Charismatic capture.** A charismatic leader cannot rewrite agreement history to erase unpopular changes they championed. The version record's author field, approval record link, and change rationale document who changed what and why. The immutable diff makes every change attributable and transparent.

**Emergency capture.** Emergency amendments still produce version records. Even if an agreement is amended under emergency timelines, the version record captures the emergency rationale and the compressed approval process. Post-emergency review includes checking whether the emergency version should be superseded by a version produced under normal conditions.

**Informal capture.** Changes to agreements that bypass the formal amendment process do not produce version records and therefore have no governance standing. If someone claims an agreement was modified informally, the version history is the authoritative record. The latest version in the history is the agreement's current text.

## I. Failure Containment Logic

- **Version creation fails or is delayed**: the agreement-registry flags the agreement as "version-pending." The amendment is valid (it was consented to) but the version record has not been created. The governance memory steward assigns a recorder to create the version record within 7 days.
- **Diff generation error**: the version record is created with the snapshot and metadata intact, and the diff marked as "generation pending." A corrected diff is appended later. The snapshot is always the primary record; the diff is a convenience, not the source of truth.
- **Version number dispute**: if participants disagree about whether a change is major, minor, or patch, the dispute is documented in the version record's rationale field. The deciding body resolves the classification. The version number can be corrected by appending a reclassification annotation, not by editing the original record.
- **Rollback proposal rejected**: the current version stands. The rejection itself is documented as a decision record, establishing precedent that the current version was affirmed.
- **Orphaned version history**: if the agreement-registry entry is sunset but the version history exists, the history remains accessible as an archived record. Sunset agreements retain their full version history for future reference.

## J. Expiry / Review Condition

Version records never expire -- they are permanent entries in the agreement's history. The version history is reviewed whenever the agreement itself enters a scheduled review cycle (per the agreement-review skill). During review, reviewers can examine the full version history to understand how the agreement evolved and whether the trajectory suggests structural issues. If no version has been added for a period exceeding the agreement's review interval, this triggers an automatic review check. The versioning skill itself (its conventions and processes) is reviewed when the governance memory steward identifies systemic issues -- for example, if version number assignments are inconsistent across domains. All review intervals are configurable by the responsible circle but must have mandatory minimums as defined in the agreement-review skill.

## K. Exit Compatibility Check

When a participant exits, version records they authored remain valid and unchanged -- the records document agreement changes that were consented to by the ecosystem, not personal commitments. The exiting participant's name remains in author fields as historical attribution. If the exiting participant authored the current version of a critical agreement, the agreement-registry flags it for review by the responsible circle to ensure institutional knowledge transfer. Agreements themselves are ecosystem artifacts; their version histories survive any participant's departure. During the 30-day wind-down, any version records in progress (pending diff generation, pending verification) are completed by the governance memory steward or a designee.

## L. Cross-Unit Interoperability Impact

When an agreement spans multiple ETHOS (e.g., a cross-ETHOS resource sharing agreement), its version history is maintained in the ecosystem-wide governance memory, not in any single ETHOS's records. All affected ETHOS can query the version history. When one ETHOS proposes an amendment to a cross-ETHOS agreement, the version record documents which ETHOS participated in the consent process. Diff queries across versions enable any ETHOS to see how the agreement changed and whether changes affected their unit specifically. Cross-ecosystem version compatibility (when two NEOS ecosystems share agreement formats) is deferred to Layer V, but the version record schema is designed for portability: the semver convention, snapshot format, and diff structure are NEOS-generic, not OmniOne-specific.

## OmniOne Walkthrough

The SHUR Bali kitchen shared space agreement has evolved through four versions over 18 months. Governance memory steward Nia uses this agreement to demonstrate how versioning works in practice.

**v1.0.0 -- Original creation.** TH member Davi facilitated the agreement-creation process. Fifteen SHUR Bali residents consented to the kitchen agreement establishing: usage hours (6 AM - 10 PM), cleaning responsibilities (rotating weekly schedule), quiet hours (after 9 PM), and guest policies (residents responsible for their guests). The version record captures: version=1.0.0, source_skill=agreement-creation, approval_record=CR-OMNI-2025-031, author=Davi, rationale="Initial kitchen shared space agreement for SHUR Bali." The snapshot contains the full agreement text. The diff notes "initial version."

**v1.1.0 -- Quiet hours amendment.** Six months later, the annual review surfaces a complaint: quiet hours starting at 9 PM is too early for residents who eat dinner late. AE steward Kenji facilitates an amendment through ACT. The consent round agrees to change quiet hours to 10 PM. Version record: version=1.1.0 (minor -- substantive clause modification within existing structure), diff shows the change from "quiet hours: 9 PM - 6 AM" to "quiet hours: 10 PM - 6 AM", source_skill=agreement-amendment, approval_record=CR-OMNI-2025-047, author=Kenji, rationale="Shifted quiet hours one hour later following resident feedback during annual review."

**v1.2.0 -- Scope expansion.** Three months after that, the community builds an outdoor kitchen extension. TH member Priya proposes expanding the agreement to cover the outdoor area. The ACT process produces consent. Version record: version=1.2.0 (minor -- scope expansion within existing structure), diff shows addition of "Section 5: Outdoor Kitchen Extension" with usage guidelines, source_skill=agreement-amendment, approval_record=CR-OMNI-2025-058, author=Priya, rationale="Extended kitchen agreement to cover newly built outdoor kitchen area."

**v2.0.0 -- Major revision after turnover.** Six months later, 30% of SHUR Bali residents have turned over. The new residents find the existing agreement confusing because it was amended twice without restructuring. The agreement-review process triggers a major revision. Facilitator Lena guides a full rewrite through ACT, consolidating all sections and updating responsibilities for the current resident composition. Version record: version=2.0.0 (major -- structural rewrite affecting scope, parties, and governance mechanism), diff shows extensive changes across all sections, source_skill=agreement-review, approval_record=CR-OMNI-2026-012, author=Lena, rationale="Comprehensive revision following 30% resident turnover. Consolidated amendments v1.1.0 and v1.2.0 into a unified structure. Updated responsible parties for current composition."

**Diff query.** New resident Suki arrives after v2.0.0 and wants to understand how the agreement evolved. She queries the diff between v1.0.0 and v2.0.0. The system returns a comprehensive diff showing all changes across the agreement's lifespan: the quiet hours shift, the outdoor kitchen addition, and the structural rewrite. Suki can see exactly how each clause changed and why by reading the rationale in each version record.

**Edge case: Consent dispute.** Returning resident Marco claims the quiet hours change in v1.1.0 was never properly consented to -- he was traveling and says he was not notified. Governance memory steward Nia retrieves version record v1.1.0 and follows the approval_record link to CR-OMNI-2025-047. The consent record shows the participant list, notification dates, and consent positions. Marco's name appears with status "notified, did not participate" -- he was notified per the agreement's notification requirements but did not respond within the consent window. The version record's immutable link to the approval record resolves the dispute structurally: the amendment followed the correct process, and the consent record proves notification occurred. Marco's recourse is to propose a new amendment through ACT if he disagrees with the quiet hours, not to challenge the historical record.

## Stress-Test Results

### 1. Capital Influx

A major donor funds renovations to the SHUR Bali kitchen and insists that the kitchen agreement be updated to include "donor recognition" signage and usage priority during events. The donor's preferred changes enter the normal amendment process through ACT. If consent is achieved, a new version record documents exactly what changed, who authored the amendment, the donor-driven rationale, and the approval record. If future participants question the donor recognition clause, the version history shows when it was added, why, and who consented. The immutable history prevents the donor from later claiming the clause was always part of the agreement or from suppressing the version that preceded their amendment. If the consent round rejects the donor's proposal, the rejection is documented in a decision record, and no version is created -- the agreement's version history reflects only consented changes, not donor preferences.

### 2. Emergency Crisis

A kitchen fire at SHUR Bali requires immediate safety modifications to the kitchen agreement: usage hours are restricted, cleaning protocols are changed, and the outdoor kitchen becomes the primary cooking area. The Operations steward invokes emergency authority and the agreement is amended under compressed timelines. The agreement-versioning skill requires a version record for this emergency amendment. The version record captures the emergency rationale, the compressed consent process, and the urgency_at_time=emergency tag. Post-emergency review evaluates whether the emergency version should be superseded by a version produced under normal deliberation. If the community decides to revert to pre-emergency terms after repairs, the rollback is a new version (not an undo), preserving the complete chain: v2.0.0 (pre-emergency) -> v2.1.0 (emergency modifications) -> v2.2.0 (post-emergency reversion, referencing v2.0.0 content with updates for new safety requirements).

### 3. Leadership Charisma Capture

A charismatic community leader championed the v2.0.0 major revision and now claims the revision was their personal vision rather than a collective governance outcome. They reference "my agreement" in community discussions. The agreement-versioning skill counters this because the version record's author field documents who facilitated the process, but the approval_record links to the consent record showing all participants' positions. The diff shows the specific textual changes, not a narrative about whose vision they represent. The version history demonstrates that v2.0.0 built on three prior versions and a consent process with documented rationale -- it is an institutional artifact, not a personal document. Any participant can review the version history and see the collective nature of the agreement's evolution.

### 4. High Conflict / Polarization

Two factions at SHUR Bali deeply disagree about the outdoor kitchen section added in v1.2.0. One faction wants to expand outdoor kitchen hours; the other wants to restrict them due to noise. The version history is valuable here because both factions can read the original rationale in v1.2.0 and the integration of the outdoor area into the broader agreement in v2.0.0. The version records show the reasoning behind current terms, preventing the dispute from devolving into "we never agreed to this." If the conflict escalates through GAIA levels and a facilitator coaches a third solution (perhaps seasonal hour variations), the resolution becomes a new version with its own rationale documenting how the third solution emerged. The full version history preserves the polarization, the mediation, and the resolution for future reference -- governance learning is not lost.

### 5. Large-Scale Replication

OmniOne scales to 15 SHUR locations, each with its own kitchen agreement (and dozens of other shared space agreements). The agreement-versioning skill scales because version records are per-agreement, not per-ecosystem. Each location's kitchen agreement has its own version history, managed by the local governance memory steward. The semver convention is consistent across locations, enabling cross-location comparison: a steward at SHUR Mexico can query SHUR Bali's kitchen agreement version history for inspiration when drafting their own. At ecosystem scale, hundreds of agreements produce thousands of version records, but each version history is self-contained. The governance memory index enables search across version histories (e.g., "find all agreements amended more than 3 times in the past year" for proactive governance review). The skill's structure remains identical at every scale.

### 6. External Legal Pressure

Indonesian food safety regulators require that kitchen usage agreements at co-living facilities include specific hygiene clauses. The regulatory requirement enters OmniOne's governance process through a proposal to amend the kitchen agreement. If consent is achieved, the amendment produces a new version with the regulatory-driven rationale documented. The version history shows exactly when and why the regulatory clause was added, enabling future participants to distinguish between self-governed clauses and externally mandated ones. If the regulation changes later, the version history provides clear evidence of which clauses were added for regulatory compliance. The UAF sovereignty principle means the ecosystem adds regulatory clauses through its own consent process rather than accepting external edits to its agreements. The version record documents this sovereignty: the rationale says "added to comply with Indonesian regulation X" within a consent process, not "modified by external authority."

### 7. Sudden Exit of 30% of Participants

Fifteen of fifty members depart from SHUR Bali. Agreements remain valid -- they are ecosystem artifacts, not personal commitments. Version histories are unaffected by departures. However, the mass departure may trigger agreement reviews for agreements where many affected parties have left. The agreement-review skill identifies agreements where more than 25% of named affected parties have departed and flags them for review. When the review produces changes (updating responsible parties, adjusting scope for the smaller community), a new version record documents the changes with rationale: "Revised following departure of 30% of affected parties. Updated responsible party assignments and adjusted scope for current community composition." The version history preserves the pre-departure agreement state, enabling the community to understand what changed and why if new members later restore the population.
