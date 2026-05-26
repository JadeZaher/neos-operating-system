---
name: decision-record
description: "Record a governance decision with its holding, reasoning, context, and dissent -- wrap any artifact from any layer into a searchable, classifiable, challengeable precedent."
layer: 9
version: 0.1.0
depends_on: [agreement-registry, domain-mapping, act-consent-phase]
---

# decision-record

## C. Trigger Conditions

- A governance process completes with an outcome (consent achieved, proposal rejected, boundary resolved, agreement created, amended, or sunset)
- A facilitator or designated recorder identifies that a decision was made without a corresponding record
- An ACT process produces a consent record that needs to be wrapped with holding, context, and classification
- A rejected proposal needs documentation to prevent unknowing re-submission of the same proposal
- An emergency governance action occurs and requires post-emergency documentation within 48 hours of resolution

## D. Required Inputs

- **Decision outcome**: the result of the governance process (what was decided, or that a proposal was not adopted)
- **Source artifact**: the output document from the originating skill (agreement, consent record, domain contract, etc.)
- **Deliberation summary**: reference to advice logs, discussion records, or meeting notes from the governance process
- **Participant list**: all participants in the governance process, their roles, and their positions (consent, stand-aside, objection)
- **Domain identification**: which domain produced the decision, verified against the domain-mapping registry
- **Recorder identity**: the facilitator or designated recorder from the governance process
- **Precedent classification**: the recorder's initial classification (routine, governance, constitutional), subject to review

## E. Step-by-Step Process

1. **Identify the decision.** Within 48 hours of a governance process completing, the facilitator or designated recorder identifies the decision outcome. Both adopted and rejected proposals receive records -- a rejection's holding is "Proposal X was not adopted" with full context.
2. **Draft the holding.** Write a single statement that captures what was decided. The holding must be specific enough to be applied as precedent: "The Economics circle's domain includes resource allocation for shared infrastructure" not "We talked about Economics boundaries."
3. **Write the ratio decidendi.** Document the reasoning that produced the holding. What arguments were persuasive? What principles were applied? What alternatives were considered and why were they rejected? This is the binding reasoning that future decisions can reference.
4. **Record obiter dicta.** Capture contextual observations that informed but did not determine the decision. These are informative for future reference but do not bind as precedent. Example: "Several participants noted that this issue may need revisiting when the ecosystem exceeds 200 members."
5. **Document dissent.** For each objection raised during the consent process, record: the objector, the objection, how it was resolved (integrated, stood-aside, or escalated), and any notes. Unresolved dissent that resulted in stand-asides is documented with the stand-aside rationale.
6. **Classify precedent level.** Apply the initial classification: routine (does not establish a new pattern), governance (establishes or modifies a governance norm), constitutional (affects the UAF or foundational principles). The recorder states the rationale for the classification.
7. **Apply semantic tags.** Tag the record with domain, layer, source skill, affected parties, topic keywords, ecosystem scope, and urgency level. Follow the tagging-taxonomy defined in the semantic-tagging skill.
8. **Verify factual accuracy.** Share the completed draft with all participants for a 72-hour factual accuracy review. Participants can correct factual errors (misattributed positions, incorrect dates, omitted objections) but cannot re-litigate the decision itself.
9. **Register.** Assign a unique record ID following the convention DR-[ECOSYSTEM]-[YEAR]-[SEQUENCE]. Enter the record into governance memory with all metadata and semantic tags. Link the record to the source artifact by ID.

## F. Output Artifact

A complete decision record document following `assets/decision-record-template.yaml`. The record contains: unique ID, holding, ratio decidendi, obiter dicta, dissent record, deliberation summary reference, source skill and layer, artifact type and reference, participant list with positions, domain, precedent classification, semantic tags, lifecycle status (active, superseded, or overruled), and authorship metadata. The record is immutable after verification -- corrections are appended as amendments, never edits. All participants and any ecosystem member can access the record through governance memory search.

## G. Authority Boundary Check

The facilitator or designated recorder of the governance process writes the decision record. No other participant can write the official record unilaterally, though any participant can propose corrections during the 72-hour verification window. No one can modify a finalized record -- corrections require an appended amendment with the corrector's identity and rationale. Precedent reclassification (changing routine to governance, or governance to constitutional) requires a consent process by the body that made the original decision. The recorder's authority extends to documenting what happened, not to interpreting or altering what was decided. Authority scopes are defined by the domain contract (see domain-mapping skill, Layer II). The governance memory steward (defined through domain-mapping) maintains system integrity but cannot alter individual records.

## H. Capture Resistance Check

**Capital capture.** Financial contributors cannot influence how decisions are recorded. The record documents what happened in the governance process, not what a funder wishes had happened. If a funder pressures the recorder to alter a holding or omit dissent, this is flagged as a capture attempt. The 72-hour verification by all participants catches any distortions.

**Charismatic capture.** A charismatic leader cannot ensure their preferred narrative dominates the decision record. The structured separation of holding, ratio, and dissent means objections are preserved even when socially unpopular. The recorder documents all positions, not just the majority view. The verification period allows any participant to flag omissions.

**Emergency capture.** Crisis conditions compress timelines but do not eliminate recording requirements. Emergency decisions receive records within 48 hours of the emergency subsiding. The record explicitly notes the emergency context and tags the decision with "emergency" urgency, ensuring post-emergency review. Emergency records cannot be finalized without the dissent section completed.

**Informal capture.** Unrecorded decisions have no standing as precedent. If a participant claims "we already decided this," the governance memory either contains a decision record confirming it or it does not. No verbal agreement, meeting sidebar, or email thread substitutes for a formal decision record.

## I. Failure Containment Logic

- **Recorder fails to write within 48 hours**: any participant in the governance process can request record creation. If no record exists after 7 days, the governance memory steward assigns a recorder from among the participants.
- **Factual accuracy dispute**: if a participant disputes a factual claim in the record during verification, the specific dispute is documented alongside the record as an unresolved annotation. The holding and ratio stand unless the body reconvenes to correct them.
- **Classification dispute**: if a participant believes the precedent level is wrong, they request reclassification through a lightweight consent process (the original deciding body or delegate). The dispute does not block record registration.
- **Missing deliberation records**: if advice logs or meeting notes are unavailable, the record notes "deliberation records unavailable" and the recorder writes a summary from memory. This is marked as a degraded record.
- **Recorder bias**: the 72-hour verification by all participants acts as a structural check. Persistent recorder bias triggers reassignment by the governance memory steward.

## J. Expiry / Review Condition

Decision records do not expire. They are permanent entries in governance memory. However, their relevance changes over time. Records are reviewed when: a precedent challenge is filed against them (per the precedent-challenge skill), a related agreement enters its scheduled review cycle, or the governance memory steward identifies records that may be affected by a significant ecosystem change. Constitutional-level records are reviewed during the annual UAF review. Governance-level records are reviewed every 2 years. Routine records are reviewed only when directly relevant to a new decision. Review does not modify the original record -- it may produce a new decision record that supersedes or overrules the original.

## K. Exit Compatibility Check

When a participant exits the ecosystem, decision records they authored remain valid and unchanged -- the record documents an ecosystem governance event, not a personal commitment. Records where the exiting participant was the sole recorder are flagged for verification by the governance memory steward to ensure institutional knowledge is not lost. The exiting participant's positions (consent, objection, stand-aside) remain in all decision records as historical fact. If the exiting participant held the governance memory steward role, the domain-mapping skill triggers reassignment within the 30-day wind-down period. No decision record is invalidated by a participant's departure.

## L. Cross-Unit Interoperability Impact

Decision records from one ETHOS are accessible to all participants across the ecosystem -- governance memory is not siloed by organizational unit. When a decision affects multiple ETHOS, the record's semantic tags include all affected units and the record is surfaced in cross-ETHOS searches. Cross-ETHOS decisions include participant lists from all affected units. When two NEOS ecosystems share governance space, their decision record schemas are compatible (same envelope structure) enabling cross-ecosystem precedent search. Full cross-ecosystem federation protocol is deferred to Layer V but the decision record format is designed for it: the record_id namespace includes the ecosystem identifier.
