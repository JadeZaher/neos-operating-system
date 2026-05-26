---
name: agreement-versioning
description: "Track the full version history of every living agreement with immutable snapshots, diffs, and rationale -- so no one can claim a change was never consented to."
layer: 9
version: 0.1.0
depends_on: [agreement-registry, agreement-amendment, agreement-review]
---

# agreement-versioning

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

When a participant exits, version records they authored remain valid and unchanged -- the records document agreement changes that were consented to by the ecosystem, not personal commitments. The exiting participant's name remains in author fields as historical attribution. If the exiting participant authored the current version of a critical agreement, the agreement-registry flags it for review by the responsible circle to ensure institutional knowledge transfer. Agreements themselves are ecosystem artifacts; their version histories survive any participant's departure.

## L. Cross-Unit Interoperability Impact

When an agreement spans multiple ETHOS (e.g., a cross-ETHOS resource sharing agreement), its version history is maintained in the ecosystem-wide governance memory, not in any single ETHOS's records. All affected ETHOS can query the version history. When one ETHOS proposes an amendment to a cross-ETHOS agreement, the version record documents which ETHOS participated in the consent process. Diff queries across versions enable any ETHOS to see how the agreement changed and whether changes affected their unit specifically. Cross-ecosystem version compatibility (when two NEOS ecosystems share agreement formats) is deferred to Layer V, but the version record schema is designed for portability: the semver convention, snapshot format, and diff structure are NEOS-generic, not OmniOne-specific.
