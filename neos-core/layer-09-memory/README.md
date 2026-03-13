# Layer IX: Memory & Traceability

Layer IX provides the structural memory that turns isolated governance decisions into a searchable, classifiable, versionable, and challengeable body of knowledge. Without this layer, the ecosystem is amnesiac -- decisions are made, implemented, and forgotten. When a similar question arises later, participants relitigate from scratch because no one can find what was decided before, why it was decided, or whether the reasoning still holds.

## Design Philosophy

Layer IX draws from three established frameworks:

**Legal precedent (stare decisis).** Every decision record separates the holding (what was decided) from the ratio decidendi (why it was decided) from the obiter dicta (contextual observations that are informative but not binding). This separation prevents future actors from over-applying a decision beyond its intended scope and enables principled challenge when circumstances change.

**DAO on-chain governance memory (two-layer architecture).** Every governance decision has two components: the deliberation (advice logs, discussion records, objections raised, alternatives considered) and the decision itself (the holding, the consent record, the outcome). Both layers are preserved but clearly separated. Participants searching for what was decided find the holding quickly; participants searching for why find the deliberation.

**Git-style versioning.** Every agreement change is a committed, diffable snapshot with full history. Version numbers follow semver (major.minor.patch). History is immutable -- rollback is a new amendment, not an undo.

## Skill Index

| Skill | Description | Depends On |
|-------|-------------|------------|
| [decision-record](decision-record/SKILL.md) | Record a governance decision with holding, reasoning, context, and dissent as a searchable precedent | agreement-registry, domain-mapping, act-consent-phase |
| [semantic-tagging](semantic-tagging/SKILL.md) | Classify and tag decisions for retrieval and pattern detection | decision-record, domain-mapping |
| [precedent-search](precedent-search/SKILL.md) | Query governance memory to find and apply relevant precedents | decision-record, semantic-tagging |
| [agreement-versioning](agreement-versioning/SKILL.md) | Track the full version history of living agreements with immutable snapshots and diffs | agreement-registry, agreement-amendment, agreement-review |
| [precedent-challenge](precedent-challenge/SKILL.md) | Formally challenge existing precedent when circumstances change or rationale no longer holds | precedent-search, decision-record, act-consent-phase |

## Two-Layer Memory Architecture

Layer IX preserves both layers of every governance decision:

**Deliberation layer.** The advice logs, discussion records, meeting notes, objections raised, and alternatives considered during the governance process. This layer answers the question: *what was the conversation?* Deliberation records are referenced by the decision record but stored separately (in the originating skill's output or in `references/`).

**Decision layer.** The holding, ratio decidendi, obiter dicta, dissent record, and approval record. This layer answers the question: *what was decided, and why?* Decision records are the primary unit of governance memory -- they are tagged, searchable, and challengeable.

The separation ensures that participants can find what was decided without wading through full deliberation records, while the deliberation remains accessible for those who need to understand the complete context.

## Precedent Classification System

Not all decisions carry equal precedent weight. Layer IX classifies every decision record at one of three levels:

**Routine.** Decisions that do not establish a new governance pattern. Examples: meeting schedule changes, minor process adjustments, individual resource allocations within established frameworks. Routine precedent is searchable but carries minimal binding weight. Challenge process: handled by the domain's circle.

**Governance.** Decisions that establish or modify a governance norm. Examples: new agreement types, process changes, domain boundary shifts, new roles or responsibilities. Governance precedent is binding within its domain and persuasive across the ecosystem. Challenge process: handled by the original deciding body. Review cycle: every 2 years.

**Constitutional.** Decisions that affect the UAF or foundational principles. Examples: UAF amendments, principle changes, structural reforms, sovereignty interpretations. Constitutional precedent is binding ecosystem-wide. Challenge process: requires OSC consent. Review cycle: annual UAF review.

## Generic Wrapper Design

The decision-record skill defines a universal envelope that wraps any governance artifact from any layer:

```
Decision Record Envelope
  +-- Holding (what was decided)
  +-- Ratio Decidendi (why)
  +-- Obiter Dicta (contextual observations)
  +-- Dissent Record (objections and resolutions)
  +-- Wrapped Artifact (type-agnostic reference)
  |     +-- source_skill, source_layer, artifact_type, artifact_reference
  +-- Metadata (participants, domain, precedent_level, semantic_tags)
  +-- Lifecycle (status, overruled_by, related_records)
```

This design means Layer IX does not need to import schemas from other layers. It wraps whatever they produce -- agreement documents, consent records, domain contracts, boundary resolutions, sunset records, amendment records, review records, or any future artifact type. The envelope is universal; the wrapped artifact is type-agnostic.

## Relationship to Layer I (Agreement Registry)

Layer IX complements but does not replace the agreement-registry skill (Layer I):

- **agreement-registry** is the specialized index for agreements: it tracks agreement status, version, affected parties, and supports agreement-specific queries.
- **decision-record** is the universal wrapper: every agreement creation, amendment, and review is also a governance decision that gets a decision record with holding, ratio, context, dissent, and semantic tags.
- **agreement-versioning** extends the registry's version tracking with Git-style immutable snapshots, diffs, and rollback capabilities.

The two systems cross-reference each other by ID. Neither depends on the other's schema. An ecosystem can operate the agreement-registry without Layer IX (losing governance memory) or Layer IX without the agreement-registry (losing agreement-specific indexing), though both are recommended.

## Cross-Layer References

Layer IX interacts with every other layer because it records decisions from all of them:

| Layer | Interaction |
|-------|-------------|
| **I (Agreement)** | Decision records wrap agreement artifacts; agreement-versioning extends agreement-registry |
| **II (Authority)** | Domain contracts, boundary resolutions, and sunset records become decision records; domain-mapping defines the governance memory steward role |
| **III (ACT Engine)** | Consent records and advice logs are wrapped in decision records; ACT processes drive precedent challenges |
| **IV (Onboarding)** | New member orientation includes governance memory access; onboarding decisions are recorded |
| **V (Inter-Unit)** | Cross-AZPO decisions are tagged with ecosystem_scope; federation protocol extensibility point |
| **VI (Economics)** | Resource allocation decisions are recorded and searchable; financial precedent is classifiable |
| **VII (Conflict)** | Conflict resolution outcomes become searchable precedent; GAIA escalation is referenced in challenges |
| **VIII (Ecology)** | Environmental governance decisions are recorded with domain-specific tags |
| **X (Monitoring)** | Decision pattern analysis draws on tagged, searchable governance memory |

## Open Access Principle

All governance memory is searchable by all participants. There are no proprietary archives, no restricted precedent databases, and no tiered access to decision records. This is a non-negotiable design principle of Layer IX. Information asymmetry creates hidden authority -- if only some participants can search precedent, those participants have structural advantage in governance processes.

## Immutability Principle

Historical decision records and agreement versions cannot be modified after creation. Corrections are appended as amendments, not edits. Overruled precedents are marked "overruled by [ID]" with a link -- the original record remains intact. This provides the trustworthiness foundation that the entire memory system depends on. If participants cannot trust that records accurately reflect what was decided, the governance memory system has no value.
