# Specification: Memory & Traceability Layer (Layer IX)

## Track ID
`memory_trace_20260302`

## Overview

This track builds **Layer IX (Memory & Traceability)** of the NEOS governance stack: the layer that defines how governance decisions are recorded, classified, searched, versioned, and challenged. Without this layer, the ecosystem has no institutional memory. Decisions are made, implemented, and forgotten. When a similar question arises later, participants relitigate from scratch because there is no way to find what was decided before, why it was decided, or whether the rationale still holds. Layer IX provides the structural memory that turns isolated decisions into a body of governance knowledge.

The primary framework is the **legal precedent system** (stare decisis): decisions have a holding (the actual ruling), ratio decidendi (the reasoning that produced the holding), and obiter dicta (contextual observations that are informative but not binding). Precedents are classified by scope (routine, governance, constitutional), can be searched semantically, and can be formally challenged when circumstances change. Secondary influences are **DAO on-chain governance memory** (two-layer architecture separating deliberation from decision) and **Git-style agreement versioning** (every change is a committed, diffable snapshot with full history).

This track produces 5 governance skills and supporting asset templates. It defines a generic decision-record schema that wraps any artifact type from any layer, providing flexibility without tight coupling to specific layer schemas.

## Background

### Why Memory & Traceability Is Priority 3

The workflow track ordering places Layer IX third because "every other layer needs it." The foundation track (Layers I + III) produces output artifacts -- agreement documents, proposal documents, advice logs, consent records, test reports, resolution records. The authority track (Layer II) produces domain contracts, assignment records, boundary resolutions, review records, and sunset records. All of these are governance decisions that future participants need to find, understand, and reference. Without Layer IX, these artifacts exist in isolation. With it, they become searchable, classifiable, versionable, and challengeable precedent.

The foundation track review identified that "agreement-registry" was designed as a Layer I skill. Layer IX extends this concept: where the agreement-registry tracks agreements specifically, Layer IX tracks all governance decisions universally. The two are complementary, not redundant. The agreement-registry is the specialized index for agreements; Layer IX's decision-record is the universal wrapper for any governance artifact.

### Design Patterns (From Research)

**Two-layer memory (deliberation + decision)**: Every governance decision has two components: the deliberation (advice logs, discussion records, objections raised, alternatives considered) and the decision itself (the holding, the consent record, the outcome). Both layers are preserved but clearly separated. Participants searching for what was decided can find the holding quickly; participants searching for why can find the deliberation.

**Ratio/context separation**: The holding of a decision (what was actually decided) is separated from the context (the circumstances that led to the decision). This prevents future actors from over-applying a decision beyond its intended scope. It also enables principled challenge: "The circumstances that produced this precedent no longer apply."

**Precedent classification**: Not all decisions are equal. Routine decisions (meeting schedule changes) are low-precedent. Governance decisions (new agreement types, process changes) are medium-precedent. Constitutional decisions (UAF amendments, principle changes) are high-precedent. The classification determines how prominently the decision appears in search results and how formally it must be challenged.

**Semantic tagging**: Decisions are tagged with domain, layer, skill used, affected parties, and topic keywords. This enables cross-cutting search: "Find all decisions that affected the Economics circle, regardless of which layer produced them."

**Mandatory overrule documentation**: When a precedent is challenged and overruled, the overruling decision must document: which precedent is being overruled, why the original rationale no longer applies, and what the new rationale is. This prevents silent erosion of governance norms.

### Anti-Patterns to Guard Against

**Everything-is-precedent**: If every decision is treated as binding precedent, the governance system becomes rigid and unable to adapt. Precedent classification prevents this by distinguishing routine decisions from governance-level and constitutional-level ones.

**Proprietary archives**: If governance memory is accessible only to certain participants (e.g., only council members can search precedent), information asymmetry creates hidden authority. Layer IX requires open search access for all participants.

**Memory without search**: Having records without the ability to find them is the same as having no records. The precedent-search skill defines query capabilities that make the memory system usable.

**Retroactive editing**: If decision records can be modified after the fact without versioning, the system's trustworthiness collapses. Agreement-versioning provides immutable snapshots with transparent change tracking.

### OmniOne Specifics

- Governance memory begins at ecosystem founding. The first decision records are the UAF ratification and the initial domain definitions for TH, AE, OSC, and GEV.
- OmniOne's deliberation layer includes meeting notes, proposal discussions, and advice logs from the ACT process.
- The Trunk Council transition (temporary authority to permanent circles) is a constitutional-level precedent that must be fully documented for future ecosystems to reference.
- OmniOne operates across multiple physical locations (Bali, Costa Rica, Mexico, Brazil). Memory must be accessible regardless of location.

---

## Functional Requirements

### FR-1: Decision Record (`decision-record`)

**Description:** Write a governance decision record that captures the holding (what was decided), the context (circumstances and deliberation), any dissent (objections raised and how they were addressed), and the implementation plan. The decision record is a generic wrapper that can contain the output artifact from any NEOS skill -- agreement documents, consent records, domain contracts, boundary resolutions, sunset records, and any future artifact type. This is the anchor skill for Layer IX.

**Acceptance Criteria:**
- AC-1.1: The skill defines the decision record schema with clear separation between: holding (the actual decision in a single statement), ratio decidendi (the reasoning -- why this was decided), obiter dicta (contextual observations not binding as precedent), deliberation summary (reference to advice logs, discussion records), dissent record (objections raised, how addressed, any unresolved dissent), implementation reference (link to the output artifact from the originating skill), and metadata (date, participants, skill used, domain, layer, precedent classification).
- AC-1.2: The step-by-step process covers: who writes the record (the facilitator or designated recorder of the governance process that produced the decision), when it is written (within 48 hours of the decision), what review it undergoes (the record is shared with all participants for factual accuracy verification, not re-litigation of the decision), and where it is registered (governance memory index).
- AC-1.3: The output artifact is a complete decision record document with a unique identifier, semantic tags, and precedent classification.
- AC-1.4: The generic wrapper design means the skill defines the envelope (holding, context, dissent, metadata) without prescribing the format of the wrapped artifact. An agreement document, a domain contract, and a consent record all fit inside the same wrapper.
- AC-1.5: The authority boundary check specifies who can write decision records (the responsible party from the governance process), who can request corrections (any participant in the process, for factual accuracy only -- not to change the holding), and who can reclassify precedent level (the body that made the decision, through a consent process).
- AC-1.6: An OmniOne walkthrough demonstrates writing a decision record for the Economics circle boundary resolution (from the authority-boundary-negotiation skill), showing how the boundary resolution record is wrapped in a decision record with holding, ratio, context, dissent, and semantic tags.
- AC-1.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Anchor skill. Every other Layer IX skill depends on decision records existing.

### FR-2: Precedent Search (`precedent-search`)

**Description:** Query governance memory to find relevant precedents and apply them to current governance situations. This skill defines the search capabilities, relevance ranking, and application guidelines. It is the primary interface between past decisions and present governance needs. Any participant can search; no governance memory is proprietary.

**Acceptance Criteria:**
- AC-2.1: The skill defines query parameters: keyword/topic search, domain filter, layer filter, skill filter, date range, precedent classification level, affected parties filter, semantic tag filter, and compound queries combining multiple parameters.
- AC-2.2: The step-by-step process covers: formulating a search query, evaluating results for relevance (is the precedent's ratio decidendi applicable to the current situation?), distinguishing binding precedent (same domain, same type of decision, ratio still applies) from persuasive precedent (different domain or different type, but reasoning is informative), and documenting how the precedent informs the current decision.
- AC-2.3: The output artifact is a precedent application report: which precedents were found, which are applicable, how they inform the current situation, and whether any should be challenged.
- AC-2.4: The authority boundary check specifies: search access is open to all participants (no proprietary archives). Application of precedent is advisory -- no precedent automatically dictates an outcome. A participant who applies a precedent in a governance process must cite it explicitly.
- AC-2.5: The capture resistance check addresses: selective citation (citing favorable precedents while ignoring unfavorable ones -- the search system returns all relevant results, not a curated selection), precedent lock-in (using a historical decision to block legitimate change -- the precedent-challenge skill provides the mechanism for overruling).
- AC-2.6: An OmniOne walkthrough demonstrates a TH member searching governance memory before proposing a new space agreement. The search finds 3 relevant precedents: a previous space agreement creation (binding -- same domain, same type), a boundary negotiation that touched resource allocation for spaces (persuasive -- different skill but relevant reasoning), and a sunset decision for an obsolete space agreement (informative -- shows what happens when agreements are no longer needed). The member cites all 3 in their proposal's rationale.
- AC-2.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Without search, decision records are inert data.

### FR-3: Semantic Tagging (`semantic-tagging`)

**Description:** Classify and tag governance decisions for archival and retrieval. Tags are the connective tissue of governance memory -- they enable cross-cutting search, pattern detection, and trend analysis. This skill defines the taxonomy, the tagging process, and the quality controls that prevent tag drift.

**Acceptance Criteria:**
- AC-3.1: The skill defines the tagging taxonomy with required and optional tag categories. Required: domain (which domain produced the decision), layer (which NEOS layer), skill (which skill was used), precedent_level (routine, governance, constitutional), affected_parties (who was impacted). Optional: topic (free-text keyword tags), related_precedents (links to related decision records), ecosystem_scope (single ETHOS, cross-ETHOS, ecosystem-wide), urgency_at_time (normal, elevated, emergency).
- AC-3.2: The step-by-step process covers: initial tagging (performed by the decision record author as part of decision-record creation), tag review (a lightweight verification by one additional participant to check tag accuracy), tag updates (when a decision's relevance changes over time, tags can be updated through a documented process), and taxonomy evolution (adding new tag categories when the existing ones prove insufficient, through an ACT consent process).
- AC-3.3: The output artifact is a tagged decision record (the tags are metadata on the decision record, not a separate document).
- AC-3.4: The authority boundary check specifies: any participant can propose tag corrections. Taxonomy changes (adding new categories) require consent from the body responsible for governance memory stewardship. Tag corrections are factual, not political -- changing a tag from "routine" to "governance" precedent level requires rationale.
- AC-3.5: The capture resistance check addresses: strategic mistagging (intentionally tagging a constitutional-level decision as "routine" to reduce its visibility -- the tag review process catches this), tag proliferation (so many tags that the system becomes useless -- the required/optional distinction and periodic taxonomy review prevent this).
- AC-3.6: An OmniOne walkthrough demonstrates tagging three different types of decisions: (a) a routine meeting schedule change (minimal tags: domain, layer, skill, routine classification), (b) a governance-level change to the consent process (full tags including related precedents and cross-domain impact), and (c) a constitutional-level UAF amendment (full tags plus mandatory ecosystem-wide scope tag). Show the tag review process catching an error in (b) -- the tagger missed an affected party.
- AC-3.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on decision-record existing. Tags are applied to decision records.

### FR-4: Agreement Versioning (`agreement-versioning`)

**Description:** Manage the versioned history of living agreements. Every agreement is a living document that changes over time through amendments, reviews, and partial sunsets. This skill provides Git-style version control for governance documents: every change is a committed snapshot with a diff, author, date, and rationale. The full history is preserved and queryable.

**Acceptance Criteria:**
- AC-4.1: The skill defines the versioning schema: version number (semver: major.minor.patch), snapshot (full text at this version), diff (what changed from the previous version), author (who made the change), date, rationale (why the change was made), source skill (which skill produced this change: agreement-creation for v1.0.0, agreement-amendment for subsequent versions, agreement-review for review-triggered changes), approval record (consent/consensus record ID).
- AC-4.2: The step-by-step process covers: (1) version creation (triggered automatically by agreement-creation, agreement-amendment, and agreement-review skills -- version is incremented and snapshot is taken), (2) diff generation (comparison between current and previous version, highlighting what changed), (3) history query (retrieve the full version history of an agreement, retrieve any specific version, retrieve the diff between any two versions), (4) rollback proposal (if a version is found to be problematic, a rollback to a previous version can be proposed through the ACT process -- this is a new amendment, not an undo).
- AC-4.3: The output artifact is a version record appended to the agreement's version history.
- AC-4.4: The authority boundary check specifies: version creation is automatic and cannot be bypassed (every change to an agreement produces a version). No participant can edit a historical version (immutability). Rollback requires a full ACT process (it is a new decision, not a silent revert).
- AC-4.5: The capture resistance check addresses: retroactive editing (someone alters a historical version to change what was agreed -- immutability prevents this), version suppression (hiding a version to obscure a controversial change -- the full history is always accessible to all participants), rollback abuse (repeatedly rolling back to undo legitimate changes -- each rollback is a new amendment requiring its own consent process).
- AC-4.6: An OmniOne walkthrough demonstrates the version history of the SHUR Bali kitchen space agreement: v1.0.0 (original creation), v1.1.0 (amendment to quiet hours clause following annual review), v1.2.0 (scope expansion to cover outdoor kitchen area), v2.0.0 (major revision following 30% resident turnover). Show a participant querying the diff between v1.0.0 and v2.0.0 to understand how the agreement evolved. Edge case: a member claims the quiet hours amendment (v1.1.0) was never properly consented to -- the version record's approval record ID links to the consent record, resolving the dispute.
- AC-4.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on decision-record existing. Extends the agreement-registry skill from Layer I with formal versioning.

### FR-5: Precedent Challenge (`precedent-challenge`)

**Description:** Formally challenge an existing precedent when circumstances have changed, when the original rationale is no longer valid, or when the precedent is producing harmful outcomes. This is the governance memory system's mechanism for evolution -- without it, precedent becomes inertia. With it, the governance system can learn and adapt while maintaining a record of why things changed.

**Acceptance Criteria:**
- AC-5.1: The skill defines challenge grounds: changed circumstances (the conditions that produced the original decision no longer exist), flawed rationale (the original reasoning contained an error that was not apparent at the time), harmful outcomes (the precedent is producing consequences that conflict with ecosystem principles or agreements), conflicting precedent (two existing precedents contradict each other and one must yield), better alternative (a demonstrably superior approach has been identified).
- AC-5.2: The step-by-step process covers: (1) challenger identifies the precedent to be challenged and the grounds for challenge, (2) challenger writes a challenge brief documenting: the precedent being challenged (by decision record ID), the specific ground for challenge, the evidence supporting the challenge, the proposed alternative (what should replace the precedent), (3) the challenge is submitted to the body that originally made the decision (or its successor), (4) the body reviews the challenge through an ACT process: advice from those impacted by the precedent, consent round on whether to uphold, modify, or overrule the precedent, (5) if overruled: the overruling decision record must document which precedent was overruled, why the original rationale no longer applies, and the new rationale. The original decision record is not modified -- it is marked as "overruled by [new decision record ID]" with a link.
- AC-5.3: The output artifact is either a challenge dismissal record (precedent upheld with reasoning) or an overruling decision record (new precedent replaces old).
- AC-5.4: The authority boundary check specifies: any participant can initiate a challenge (not just members of the original deciding body). The deciding body for the challenge is the body that made the original decision or its structural successor. Constitutional-level precedent challenges require OSC consent.
- AC-5.5: The capture resistance check addresses: frivolous challenges (using precedent-challenge to relitigate settled decisions without new evidence -- the challenge grounds must demonstrate a material change, not merely disagreement), challenge suppression (a body refusing to hear a challenge to protect its own prior decisions -- if the challenge is formally submitted with documented grounds, the body must process it through ACT within a defined timeline), selective overruling (overruling precedents that are inconvenient while preserving favorable ones -- the overruling record's mandatory documentation creates transparency about patterns of overruling).
- AC-5.6: An OmniOne walkthrough demonstrates a challenge to a 2-year-old precedent on resource allocation thresholds. The original decision set the threshold for OSC approval at 10% of total pool. The ecosystem has grown 5x since then, making 10% a much larger absolute amount. A Co-creator challenges on "changed circumstances" grounds: the absolute amount that now requires OSC approval is disproportionate to the original intent. The challenge brief proposes a tiered threshold based on absolute amounts. The OSC reviews, agrees the circumstances have changed, and overrules the original precedent with a new tiered threshold. The original decision record is marked "overruled" with a link to the new record. Edge case: another member challenges the same precedent on "flawed rationale" grounds at the same time -- the two challenges are consolidated into a single review process.
- AC-5.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on decision-record and precedent-search existing.

---

## Non-Functional Requirements

### NFR-1: Modularity
Each skill must function independently. Precedent-search and semantic-tagging operate on decision records but do not require decision-record to be "installed" to be understood. Each skill explains its relationship to the others but is self-contained.

### NFR-2: Line Limit
Each SKILL.md must be under 500 lines. Stress-test narratives may overflow to `references/stress-tests.md` per the foundation review recommendation.

### NFR-3: Portability
Every skill is NEOS-generic. OmniOne-specific examples (council names, specific precedents, Trunk Council transition) are clearly marked. Another ecosystem's governance memory would use the same schema with different content.

### NFR-4: No Hidden Authority
The governance memory steward role (who maintains the memory system's integrity) must have an explicit domain contract defined through the domain-mapping skill. No "memory administrator" with undefined authority.

### NFR-5: Open Access
All governance memory is searchable by all participants. There are no proprietary archives, no restricted precedent databases, and no tiered access to decision records. This is a non-negotiable design principle of Layer IX.

### NFR-6: Immutability
Historical decision records and agreement versions cannot be modified after creation. Corrections are appended as amendments, not edits. This provides the trustworthiness foundation that the entire memory system depends on.

### NFR-7: Validation
Every SKILL.md must pass automated validation via `scripts/validate_skill.py`. The same 12-section structure (A-L), OmniOne walkthrough, and 7 stress-test requirements apply.

---

## User Stories

### US-1: AI Agent Finds Relevant Precedent
**As** an AI agent assisting a participant who is drafting a proposal,
**I want** to search governance memory for relevant precedents,
**So that** the proposal can reference past decisions and avoid relitigating settled questions.

**Given** the participant is drafting a proposal related to resource allocation,
**When** the AI agent uses the precedent-search skill to query by domain and topic,
**Then** it receives a ranked list of relevant decision records with holdings, rationale, and applicability assessments.

### US-2: Facilitator Records a Decision
**As** a circle facilitator who just completed a consent round,
**I want** a clear process for writing the decision record,
**So that** the decision is captured accurately with holding, context, dissent, and proper classification.

**Given** a consent round has produced an outcome,
**When** the facilitator follows the decision-record skill within 48 hours,
**Then** a complete decision record is created, tagged, classified, and registered in governance memory.

### US-3: Participant Traces Agreement History
**As** a participant who wants to understand why an agreement says what it says,
**I want** to see the full version history with diffs and rationale for each change,
**So that** I can understand the evolution of the agreement and the reasoning behind its current form.

**Given** the participant has identified an agreement in the registry,
**When** they use the agreement-versioning skill to query the version history,
**Then** they receive a chronological list of versions with diffs, authors, dates, and rationale for each change.

### US-4: Steward Challenges an Outdated Precedent
**As** a domain steward who believes a 2-year-old precedent no longer applies,
**I want** a formal process for challenging the precedent,
**So that** the ecosystem can evolve its governance norms without silently ignoring past decisions.

**Given** the steward has identified a precedent with changed circumstances,
**When** they follow the precedent-challenge skill to submit a challenge brief,
**Then** the challenge enters an ACT process, and the outcome (upheld, modified, or overruled) is documented with full rationale.

### US-5: New Member Understands Governance History
**As** a new member who just completed onboarding,
**I want** to understand the major governance decisions that shaped the ecosystem,
**So that** I can participate meaningfully without relitigating settled questions.

**Given** the member has active status and search access,
**When** they search governance memory filtered by "constitutional" precedent level,
**Then** they receive the foundational decisions (UAF ratification, initial domain definitions, major policy changes) with clear holdings and rationale.

### US-6: Ecosystem Detects Decision Patterns
**As** the OSC reviewing governance health,
**I want** to see patterns across decision records (which domains produce the most disputes, which types of decisions are most frequently challenged),
**So that** we can proactively address systemic governance issues.

**Given** semantic tags are consistently applied to decision records,
**When** the OSC queries governance memory by tag patterns and frequencies,
**Then** they receive trend data that reveals structural patterns (e.g., 80% of boundary disputes involve the Economics circle, suggesting a domain scope problem).

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-09-memory/
    README.md
    decision-record/
      SKILL.md
      assets/
        decision-record-template.yaml
        precedent-classification-guide.md
      references/
      scripts/
    precedent-search/
      SKILL.md
      assets/
        search-query-template.yaml
        precedent-application-template.yaml
      references/
      scripts/
    semantic-tagging/
      SKILL.md
      assets/
        tagging-taxonomy.yaml
      references/
      scripts/
    agreement-versioning/
      SKILL.md
      assets/
        version-record-template.yaml
      references/
      scripts/
    precedent-challenge/
      SKILL.md
      assets/
        challenge-brief-template.yaml
        overruling-record-template.yaml
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name          # kebab-case, matches directory name
description: "..."        # Pushy description that errs toward triggering
layer: 9                  # Integer layer number
version: 0.1.0            # Semver
depends_on: []            # List of skill names this skill references
---
```

### Generic Wrapper Design

The decision-record skill defines an envelope schema that wraps any governance artifact:

```yaml
decision_record:
  # Envelope (universal)
  record_id: ""
  date: ""
  holding: ""           # Single-statement summary of what was decided
  ratio_decidendi: ""   # The reasoning that produced the holding
  obiter_dicta: ""      # Contextual observations, not binding
  dissent_record: []    # Objections raised and how addressed
  # Wrapped artifact (type-agnostic)
  source_skill: ""      # Which skill produced this decision
  source_layer: 0       # Which layer
  artifact_type: ""     # agreement | domain_contract | consent_record | etc.
  artifact_reference: "" # ID or path to the full artifact
  # Metadata
  participants: []
  domain: ""
  precedent_level: routine | governance | constitutional
  semantic_tags: {}
  # Lifecycle
  status: active | superseded | overruled
  overruled_by: ""      # decision record ID, if overruled
  related_records: []
```

This design means Layer IX does not need to import schemas from other layers. It wraps whatever they produce.

### Interleaving Strategy

Skills are built in dependency order:
1. `decision-record` (anchor) -- defines what a decision record looks like; all other skills reference this
2. `semantic-tagging` -- defines the tagging taxonomy applied to decision records
3. `precedent-search` -- queries the tagged decision records
4. `agreement-versioning` -- extends the agreement-registry with formal versioning
5. `precedent-challenge` -- challenges existing precedents found through search

### Relationship to Foundation Layer I

Layer IX complements but does not replace the agreement-registry skill (Layer I). The relationship:
- **agreement-registry** is the specialized index for agreements: tracks agreement status, version, affected parties, and supports agreement-specific queries.
- **decision-record** is the universal wrapper: every agreement creation, amendment, and review is also a governance decision that gets a decision record. The decision record adds holding, ratio, context, dissent, and semantic tags on top of the agreement-specific data.
- **agreement-versioning** extends the registry's version tracking with Git-style immutable snapshots, diffs, and rollback capabilities.

The two systems cross-reference each other by ID. Neither depends on the other's schema.

---

## Out of Scope

- **Software implementation** -- Layer IX defines the governance process for memory and traceability. Actual search infrastructure (databases, full-text search engines) is software implementation, not governance specification.
- **Automated pattern detection** -- US-6 describes pattern detection as a use case. The skills define how to produce tagged, queryable records. Automated analysis tools are software implementation.
- **Cross-ecosystem memory federation** -- When two ecosystems running NEOS need to share governance memory, the federation protocol is deferred to Layer V (Inter-Unit Coordination). Layer IX defines the record format and notes the extensibility point.
- **Natural language processing** -- The precedent-search skill defines query parameters and relevance criteria. How search is technically implemented (keyword matching, semantic similarity, etc.) is software implementation.
- **Archival retention policy** -- How long records are retained, storage formats, and backup procedures are infrastructure concerns, not governance skills.

---

## Open Questions

1. **Governance memory steward role**: Should Layer IX define a specific "memory steward" role responsible for tag quality, taxonomy maintenance, and system integrity? Recommendation: yes, as an explicit domain defined through domain-mapping, not as an informal responsibility.

2. **Precedent classification disputes**: When the recorder classifies a decision as "routine" but a participant believes it should be "governance" level, how is the dispute resolved? Recommendation: any participant can request reclassification, which is resolved through a lightweight consent process (the original deciding body or its delegate).

3. **Decision record for failed proposals**: Should rejected proposals (consent not achieved) get decision records? Recommendation: yes -- the holding is "Proposal X was not adopted" with full context. This prevents future proposers from unknowingly resubmitting the same proposal.

4. **Deliberation record completeness**: How much deliberation detail must be preserved? Full transcripts, summaries, or just the advice log? Recommendation: at minimum, the advice log and consent record from the ACT process. Full transcripts are optional and go in `references/`.

5. **Version numbering convention**: Should agreement versioning use strict semver (major.minor.patch) or a simpler scheme? Recommendation: semver with the convention that major = structural change, minor = substantive amendment, patch = clarification.

6. **Challenge standing**: Can a participant challenge a precedent from a domain they are not part of? Recommendation: yes -- any participant has standing to challenge any precedent, because governance norms affect the entire ecosystem. The deciding body is still the body that made the original decision.

7. **Retroactive tagging**: The tagging system starts with this track. Should existing foundation layer artifacts (produced before Layer IX exists) be retroactively tagged? Recommendation: yes, as a one-time integration task during the Layer IX integration phase. Use "retroactive" as a special tag to distinguish these from natively tagged records.
