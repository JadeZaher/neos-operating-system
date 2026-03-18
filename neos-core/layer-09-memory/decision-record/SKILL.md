---
name: decision-record
description: "Record a governance decision with its holding, reasoning, context, and dissent -- wrap any artifact from any layer into a searchable, classifiable, challengeable precedent."
layer: 9
version: 0.1.0
depends_on: [agreement-registry, domain-mapping, act-consent-phase]
---

# decision-record

## A. Structural Problem It Solves

Without formal decision records, governance becomes amnesiac. Decisions are made, implemented, and forgotten. When a similar question arises six months later, participants relitigate from scratch because no one can find what was decided before, why it was decided, or whether the reasoning still holds. This failure mode compounds over time: the ecosystem accumulates invisible precedent (everyone "knows" how things work) that new members cannot access and existing members cannot challenge. The decision-record skill solves this by requiring every governance decision to be captured in a structured record that separates the holding (what was decided) from the ratio decidendi (why) from the obiter dicta (contextual observations). This separation prevents future actors from over-applying a decision beyond its intended scope, and it enables principled challenge when circumstances change.

## B. Domain Scope

This skill applies to every domain in the ecosystem where governance decisions are made. Any output from any NEOS skill -- agreement documents, consent records, domain contracts, boundary resolutions, sunset records, amendment records, review records -- can be wrapped in a decision record. The decision record is the universal envelope; the wrapped artifact is type-agnostic. The skill does not prescribe the format of the wrapped artifact. It covers decision records at all precedent levels: routine (meeting schedules, minor process adjustments), governance (new agreement types, process changes, domain boundary shifts), and constitutional (UAF amendments, principle changes, structural reforms). Out of scope: software implementation of storage or indexing, cross-ecosystem federation (deferred to Layer V), and automated pattern analysis.

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

## OmniOne Walkthrough

The OmniOne Economics circle has just completed a boundary negotiation with the Operations circle over who controls resource allocation for shared infrastructure (meeting rooms, internet, power systems at SHUR Bali). The ACT process produced a boundary resolution: the Economics circle manages budgeting and allocation frameworks, while Operations manages day-to-day maintenance within those frameworks. Facilitator Lena, an AE member who guided the negotiation, now writes the decision record.

Lena drafts the holding: "The Economics circle holds domain authority over resource allocation frameworks for shared infrastructure at SHUR Bali. The Operations circle holds domain authority over day-to-day maintenance execution within those frameworks. Neither circle can unilaterally alter the other's domain." She writes the ratio decidendi: "The boundary was drawn based on the principle of separating policy-setting authority (frameworks) from operational authority (execution). This prevents either circle from accumulating both strategic and tactical control over shared resources. The allocation-execution split was preferred over a unified model because it preserves checks between circles."

Lena records the obiter dicta: "Several participants noted that this boundary may need revisiting if OmniOne expands to multiple SHUR locations, as a single Economics circle managing allocation frameworks across sites may become a bottleneck." She documents dissent: OSC member Kaito objected that the split would create coordination overhead. During integration, the circles agreed to a monthly sync meeting, and Kaito changed his position to consent. TH member Priya stood aside, noting she was not directly affected but preferred a unified approach.

Lena classifies this as governance-level precedent: it establishes a new pattern for how domain boundaries between circles are drawn. She applies semantic tags: domain=Economics+Operations, layer=2, skill=authority-boundary-negotiation, affected_parties=[Economics circle, Operations circle, SHUR Bali residents], topic=[resource-allocation, domain-boundary, shared-infrastructure], ecosystem_scope=single-ethos. She shares the draft with all 14 participants for 72-hour verification.

During verification, Operations steward Marco notices the record omits his comment about seasonal budget variations. Lena adds this to the obiter dicta as a factual correction. No other corrections arise. The record is registered as DR-OMNI-2026-042 with status "active" and linked to the boundary resolution artifact BR-OMNI-2026-015.

Edge case: Three months later, a new TH member Suki asks why Operations cannot set its own budget. An AI agent searches governance memory and finds DR-OMNI-2026-042. The holding and ratio explain the structural reasoning. Suki reads the obiter dicta and notices the scaling concern -- she decides to propose a review rather than relitigate the original question, citing the precedent and its noted limitation.

## Stress-Test Results

### 1. Capital Influx

A major donor contributes $2 million to OmniOne and privately tells the Economics circle steward that their donation should be recorded as the "primary factor" in a recent resource allocation decision. The decision-record skill prevents this distortion because the recorder documents the actual governance process, not external narratives. The holding reflects what the consent round decided, the ratio documents the reasoning participants actually used, and the dissent section records all objections as they were raised. The 72-hour verification period means all 14 participants can flag any attempt to insert the donor's preferred framing. If the donor's contribution was discussed during the advice phase, it appears in the deliberation summary as context, not as a decision driver. The structured separation of holding from context means the donor's financial influence cannot be embedded in the binding precedent. Capital cannot purchase favorable historical records.

### 2. Emergency Crisis

A catastrophic infrastructure failure at SHUR Bali forces an emergency reallocation of shared resources. Three AE stewards invoke emergency rules and make allocation decisions within 6 hours. The decision-record skill requires these emergency decisions to be documented within 48 hours of the emergency subsiding, using the same structured format. The emergency record's holding captures what was decided under crisis conditions. The ratio documents the emergency reasoning. The obiter dicta explicitly notes the compressed timeline and which normal process steps were abbreviated. The record is tagged with urgency_at_time=emergency, triggering automatic post-emergency review. The consent round under emergency conditions still requires documentation of all positions, even if only 50% quorum participated. This prevents emergency decisions from becoming unexamined precedent -- the post-emergency review re-evaluates whether the emergency holding should become standing governance or be superseded by a decision made under normal conditions.

### 3. Leadership Charisma Capture

A charismatic OmniOne founder who led a successful domain boundary negotiation attempts to have the decision record reflect their personal vision rather than the collective deliberation. They pressure facilitator Lena to frame the ratio decidendi as endorsing their broader governance philosophy, not just the specific boundary question. The decision-record skill resists this because the ratio must document the reasoning actually used in the consent process, not a post-hoc narrative. The structured template requires specific fields (what arguments were persuasive, what alternatives were considered) that anchor the record to the actual deliberation. The 72-hour verification by all participants catches any inflation of the charismatic leader's influence. Dissent records preserve objections even when participants faced social pressure to withdraw them. The record documents the collective governance event, not any individual's interpretation of it.

### 4. High Conflict / Polarization

Two OmniOne factions deeply disagree about a resource allocation decision. The consent process escalates to GAIA Level 4 coaching, where a third solution emerges. The decision record must accurately capture both the polarization and the resolution. The dissent section records all objections from both factions, including those that were eventually integrated and those that resulted in stand-asides. The ratio decidendi documents how the third solution addressed both factions' core concerns, providing future governance actors with a template for navigating similar polarization. The obiter dicta notes the escalation path taken and the coaching techniques that proved effective. This record becomes a governance-level precedent for conflict resolution, searchable by future facilitators facing similar faction dynamics. The structured format prevents either faction from claiming the record supports only their position.

### 5. Large-Scale Replication

OmniOne scales from 50 to 5,000 members across 15 SHUR locations. Decision record volume grows proportionally, but the skill scales because records are domain-scoped. A kitchen agreement decision at SHUR Costa Rica involves only that location's participants and is tagged accordingly. The universal envelope structure remains identical at every scale. What changes is the governance memory index -- at 5,000 members with hundreds of decisions per year, semantic tagging and search become critical infrastructure. The decision-record schema supports this by requiring tags at creation time. Record IDs include location identifiers (DR-OMNI-SHUR-CR-2026-003) to enable location-scoped queries. The governance memory steward role scales to a circle with location-specific stewards, each responsible for record quality in their domain, coordinated through the domain-mapping skill.

### 6. External Legal Pressure

Indonesian authorities request access to OmniOne's governance records as part of a regulatory review of co-living organizations. The decision-record skill's design supports this scenario because records are structured, searchable, and transparent by default. The ecosystem can provide records relevant to the legal inquiry without exposing the entire governance memory. The holding and ratio of each record are clear enough for external review. However, external legal mandates do not automatically alter how records are written or classified. If the legal review requires changes to recording practices, those changes enter the normal ACT process and are themselves documented as decision records. The UAF's sovereignty principle means the ecosystem cooperates with legal requirements through its own governance process, not by subordinating its recording practices to external authority.

### 7. Sudden Exit of 30% of Participants

Fifteen of fifty OmniOne members depart following a contentious decision. Existing decision records remain valid and unchanged -- they document historical governance events that occurred when those participants were present. The departed members' positions (consent, objection, stand-aside) remain in the records as historical fact. Records where departed members were the sole recorder are flagged for verification by the governance memory steward. If the governance memory steward themselves departed, the domain-mapping skill triggers reassignment during the 30-day wind-down. The remaining participants inherit the full body of governance precedent. New members joining after the exodus access the same decision records and can understand the governance history through the structured holdings and rationale. The departure itself may warrant a constitutional-level decision record documenting the event and its governance implications.
