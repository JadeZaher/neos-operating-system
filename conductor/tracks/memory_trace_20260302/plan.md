# Implementation Plan: Memory & Traceability Layer (Layer IX)

## Overview

This plan builds 5 governance skills for NEOS Layer IX plus a retroactive tagging integration phase, organized into 5 phases. The build order follows dependency: decision-record defines the universal wrapper, semantic-tagging defines the classification system, precedent-search makes records queryable, agreement-versioning extends the foundation's agreement-registry, and precedent-challenge completes the memory lifecycle.

**Total skills:** 5
**Total phases:** 5 (4 skill-building phases + 1 integration phase)
**Estimated scope:** 20-28 hours of focused implementation
**Prerequisites:** Foundation track (foundation_20260301) must be complete. Authority & Role track (authority_role_20260302) should be complete (Layer IX references domain contracts from Layer II, but can proceed with forward references if Layer II is still in progress).

### Build Order Rationale

Decision-record is the anchor because every other skill operates on decision records. Semantic-tagging comes second because search depends on tags. Precedent-search comes third because it queries tagged records. Agreement-versioning is fourth because it builds on the foundation's agreement-registry and the decision-record wrapper. Precedent-challenge is last because it requires all other skills to be defined (you challenge precedents found through search, documented as decision records, with tagged classification).

### Commit Strategy

- One commit per completed skill: `neos(layer-09): Add <skill-name> skill`
- Layer-level commit when all skills done: `neos(layer-09): Complete layer 09 - Memory & Traceability`
- Integration commits: `neos(layer-XX): Add retroactive decision records for Layer XX artifacts`

---

## Phase 1: Scaffolding and Anchor Skill

**Goal:** Create the Layer IX directory structure and build the anchor skill (decision-record) that defines the universal governance decision wrapper. After this phase, every other Layer IX skill has a concrete schema to reference.

### Tasks

- [ ] **Task 1.1: Create Layer IX directory scaffolding**
  Create the full directory tree:
  ```
  neos-core/
    layer-09-memory/
      README.md (empty placeholder)
      decision-record/      (SKILL.md, assets/, references/, scripts/)
      precedent-search/     (same structure)
      semantic-tagging/     (same structure)
      agreement-versioning/ (same structure)
      precedent-challenge/  (same structure)
  ```
  Each skill directory gets an empty `SKILL.md` and empty `assets/`, `references/`, `scripts/` subdirectories.
  **Acceptance:** All directories exist. `find neos-core/layer-09-memory -name SKILL.md | wc -l` returns 5.

- [ ] **Task 1.2: Draft decision-record SKILL.md -- sections A through F**
  Using the SKILL_TEMPLATE.md, fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without decision records, governance decisions exist only in the memories of those present. When participants change, institutional knowledge is lost. When similar questions arise, they are relitigated from scratch. When disputes arise about what was decided, there is no authoritative record. This skill provides the canonical schema for capturing any governance decision with sufficient context for future participants to understand, search, and apply it.
  - **B. Domain Scope:** Any governance decision produced by any NEOS skill in any layer. This includes: agreement creation and amendment, proposal outcomes, consent and consensus records, domain creation and review, boundary resolutions, role assignments and transfers, sunset decisions, and any future governance action. The scope is deliberately universal.
  - **C. Trigger Conditions:** A governance process completes with an outcome (adopted, rejected, modified, deferred). Specifically: any ACT phase completes, any agreement lifecycle event occurs, any domain lifecycle event occurs, any dispute is resolved, any escalation reaches resolution.
  - **D. Required Inputs:** The outcome of the governance process, the identity of participants, the source skill used, the domain in which the decision was made, the deliberation artifacts (advice log, discussion notes, consent record), and any dissent raised during the process.
  - **E. Step-by-Step Process:** (1) Within 48 hours of the decision, the designated recorder (the facilitator or a person delegated by the facilitator) drafts the decision record. (2) Holding: write a single clear statement of what was decided. Not a summary of the discussion -- the holding. Example: "The Economics circle's domain contract is amended to include post-allocation audit as a dependency on the Stewardship circle." (3) Ratio decidendi: write the reasoning that produced the holding. What arguments were decisive? What principles were applied? What trade-offs were made? (4) Obiter dicta: note any contextual observations that may be informative for future decisions but are not part of the holding. Example: "Several participants noted that the current funding pool size may require revisiting this threshold within 12 months." (5) Dissent record: document any objections that were raised, how they were addressed, and any unresolved dissent (stand-asides with documented reasons). (6) Link the source artifact: attach or reference the full output artifact from the originating skill (the consent record, the amended domain contract, etc.). (7) Apply initial semantic tags (per semantic-tagging skill). (8) Assign precedent classification: routine, governance, or constitutional (per the classification guide in assets). (9) Share the draft with all participants for factual accuracy verification -- a 72-hour window for corrections to factual errors only, not re-litigation. (10) Register the final decision record in governance memory.
  - **F. Output Artifact:** A complete decision record with unique ID, holding, ratio, obiter dicta, dissent, source artifact reference, semantic tags, precedent classification, and participant sign-off.
  Write with full substance. Use active voice per product guidelines.
  **Acceptance:** Sections A-F are substantive (3+ lines each). The holding/ratio/obiter dicta distinction is clearly explained with examples.

- [ ] **Task 1.3: Draft decision-record SKILL.md -- sections G through L**
  Complete the remaining structural sections:
  - **G. Authority Boundary Check:** The recorder writes the decision record but does not have authority to modify the holding. The holding reflects the outcome of the governance process, not the recorder's interpretation. Factual corrections can be requested by any participant within the 72-hour window. Precedent classification can be challenged by any participant through a lightweight consent process (the original deciding body or its delegate reviews the classification). No participant can suppress a decision record or remove it from governance memory. The governance memory steward (a role defined through domain-mapping) maintains system integrity but cannot modify record content.
  - **H. Capture Resistance Check:** Selective recording (recording only favorable decisions and "forgetting" unfavorable ones -- the trigger conditions make recording mandatory for all governance outcomes, not optional). Holding distortion (writing a holding that subtly differs from what was actually decided -- the 72-hour participant verification window catches this). Classification manipulation (tagging a constitutional-level decision as "routine" to reduce its visibility -- any participant can request reclassification). Dissent suppression (omitting objections from the record -- the dissent record section is mandatory, and participants can request additions during the verification window).
  - **I. Failure Containment Logic:** What happens when: the recorder fails to produce a record within 48 hours (any participant from the governance process can escalate to the governance memory steward, who assigns an alternate recorder), participants dispute the factual accuracy of a record (disputed elements are marked as "contested" with both versions preserved until resolution through the deciding body), a decision record contradicts another decision record (flag the contradiction and route to the deciding bodies of both records for resolution -- this may trigger a precedent-challenge).
  - **J. Expiry / Review Condition:** Decision records do not expire. They are permanent governance memory. However, their precedent classification may be reviewed: routine decisions are not reviewed unless specifically searched. Governance-level decisions are reviewed when the related domain undergoes domain-review. Constitutional-level decisions are reviewed alongside UAF reviews.
  - **K. Exit Compatibility Check:** When a participant exits, their decision records remain in governance memory (they are governance records, not personal property). The participant's name remains as a factual record of who participated. The participant cannot request deletion of their participation record.
  - **L. Cross-Unit Interoperability Impact:** Decisions that affect multiple AZPOs are tagged as "cross-AZPO" scope. Cross-unit decision records are shared with all affected AZPOs' governance memory. When governance memories from different AZPOs reference the same precedent, the decision record ID provides the canonical link.
  **Acceptance:** Sections G-L are substantive and structurally precise. The immutability principle is clearly stated.

- [ ] **Task 1.4: Write decision-record OmniOne walkthrough**
  Write a full narrative walkthrough:
  - Scenario: The authority-boundary-negotiation between the Economics circle and the Stewardship circle has concluded. The neutral facilitator (a TH member) is the designated recorder. Within 24 hours, they draft the decision record:
    - **Holding:** "The Economics circle has approval authority for resource allocation requests. The Stewardship circle has post-allocation audit authority and can trigger a review of any allocation through the ACT process. Neither circle can unilaterally reverse an allocation approved by the other."
    - **Ratio decidendi:** "Both circles had legitimate claims to resource oversight. The resolution separates the approval function (forward-looking, time-sensitive) from the accountability function (backward-looking, thoroughness-oriented). This separation preserves both domains' core purposes without creating a bottleneck. The ACT process for clawback proposals ensures accountability has teeth without undermining the efficiency of the approval process."
    - **Obiter dicta:** "The review body noted that the 10% threshold for OSC-level approval may need adjustment as the funding pool grows. This was not part of the current resolution but was flagged for the next domain-review of both circles."
    - **Dissent record:** "One AE member stood aside from the resolution, believing that the Stewardship circle should have co-approval authority rather than only post-allocation audit. The stand-aside was recorded with the member's rationale: 'Accountability after the fact is insufficient for large allocations.' The facilitator noted this as a potential future challenge ground."
    - **Source artifact:** Boundary resolution record BR-2026-003.
    - **Semantic tags:** domain: economics, stewardship; layer: 2; skill: authority-boundary-negotiation; precedent_level: governance; affected_parties: economics_circle, stewardship_circle; topic: resource_allocation, audit_authority.
    - **Precedent classification:** Governance (not routine because it establishes a structural pattern for future resource allocation disputes; not constitutional because it applies within a specific domain pair, not ecosystem-wide).
  - The record is shared with all participants. During the 72-hour window, the AE member who stood aside requests that their dissent rationale be expanded to include a specific example they mentioned during deliberation. The correction is accepted and the record is finalized.
  - Edge case: 6 months later, a different pair of circles has a similar boundary dispute about approval vs. audit authority. The precedent-search skill finds this decision record. The ratio decidendi (separation of approval and accountability functions) is directly applicable. The obiter dicta (threshold adjustment) has since been addressed by a separate decision.
  **Acceptance:** Walkthrough demonstrates all components of the decision record. Shows the verification process and the edge case of future application.

- [ ] **Task 1.5: Write decision-record stress-test results (all 7 scenarios)**
  Write full narrative stress tests:
  1. **Capital Influx:** A major donor's representative participates in a decision and then pressures the recorder to soften the holding to remove a constraint on donor influence. Walk through how the immutability principle and the 72-hour participant verification window (corrections are factual, not political) protect the record's integrity. The donor's pressure is itself recorded as a capture risk flag.
  2. **Emergency Crisis:** During a crisis, decisions are made rapidly. Walk through how the 48-hour recording window still applies (the decision itself may be expedited, but the record must be created). For truly emergency decisions, a provisional record with holding and minimal context is acceptable, with full context added within 7 days post-crisis.
  3. **Leadership Charisma Capture:** A charismatic leader makes an informal decision outside the governance process and pressures the recorder to create a decision record as if it went through proper channels. Walk through how the source artifact reference (which links to a specific ACT process record) prevents fabrication. No source process, no decision record.
  4. **High Conflict / Polarization:** A contentious decision produces strong dissent. The majority pressures the recorder to minimize the dissent record. Walk through how the mandatory dissent section and the 72-hour verification window allow dissenters to ensure their position is accurately captured.
  5. **Large-Scale Replication:** The ecosystem produces 500 decisions per year. Walk through how precedent classification (routine, governance, constitutional) ensures searchability -- most decisions are routine and do not clutter governance-level searches. Semantic tagging enables cross-cutting queries.
  6. **External Legal Pressure:** A government requests that certain decision records be sealed or modified. Walk through how the immutability principle prevents modification. If legal compliance requires restricted access, a note is appended to the record (not a modification) explaining the restriction, and the record itself is preserved in full.
  7. **Sudden Exit of 30%:** Many participants leave, taking institutional knowledge with them. Walk through how governance memory preserves all decision records regardless of participant status. The ratio decidendi sections become especially valuable because they capture the reasoning that exiting participants would otherwise take with them.
  Each scenario must be a full narrative paragraph (5+ sentences).
  **Acceptance:** All 7 scenarios are full narratives demonstrating how specific decision-record mechanisms handle each stress.

- [ ] **Task 1.6: Finalize decision-record SKILL.md and create assets**
  - Assemble SKILL.md from Tasks 1.2-1.5 with YAML frontmatter:
    ```yaml
    ---
    name: decision-record
    description: "Write a governance decision record that captures what was decided (holding), why (ratio decidendi), contextual observations (obiter dicta), any dissent, and the full implementation reference -- creating the permanent, searchable, immutable governance memory that prevents institutional knowledge loss."
    layer: 9
    version: 0.1.0
    depends_on: []
    ---
    ```
  - Create `assets/decision-record-template.yaml`:
    ```yaml
    record_id: ""
    date: ""
    recorder: ""
    holding: ""
    ratio_decidendi: ""
    obiter_dicta: ""
    dissent_record:
      - participant: ""
        position: stand_aside | objection
        rationale: ""
        addressed: true | false
        resolution: ""
    source:
      skill: ""
      layer: 0
      artifact_type: ""
      artifact_id: ""
    participants:
      - name: ""
        role: ""
    domain: ""
    precedent_level: routine | governance | constitutional
    semantic_tags:
      domain: []
      layer: []
      skill: []
      affected_parties: []
      topic: []
      ecosystem_scope: single_azpo | cross_azpo | ecosystem_wide
      urgency_at_time: normal | elevated | emergency
    verification:
      window_start: ""
      window_end: ""
      corrections_requested: []
      verified_by: []
    status: active | superseded | overruled
    overruled_by: ""
    related_records: []
    ```
  - Create `assets/precedent-classification-guide.md` with clear criteria and examples for each level:
    - **Routine:** Decisions that affect only the immediate participants and do not establish patterns. Examples: meeting schedule changes, minor process adjustments, individual role assignments.
    - **Governance:** Decisions that establish patterns, affect multiple domains, or change processes. Examples: new agreement types, domain boundary resolutions, process changes, policy updates.
    - **Constitutional:** Decisions that affect the entire ecosystem's structure or foundational commitments. Examples: UAF amendments, new NEOS principle interpretations, ecosystem-level restructuring.
  - Run `validate_skill.py` against the completed SKILL.md.
  **Acceptance:** SKILL.md passes validation. Under 500 lines (overflow stress tests to `references/stress-tests.md` if needed). Both assets are complete.

- [ ] **Verification 1: Run validate_skill.py against decision-record SKILL.md, confirm pass. Verify the generic wrapper design accommodates all artifact types from Layers I, II, and III. Confirm the holding/ratio/obiter dicta distinction is clear and consistently applied in the walkthrough and stress tests.** [checkpoint marker]

---

## Phase 2: Semantic Tagging and Precedent Search

**Goal:** Build the classification system (semantic-tagging) and the query system (precedent-search). After this phase, decision records can be tagged, searched, and applied to current governance situations.

### Tasks

- [ ] **Task 2.1: Draft semantic-tagging SKILL.md -- full skill (sections A-L)**
  Build the complete semantic-tagging skill:
  - **A.** Without classification, governance memory is a pile of undifferentiated records. Finding relevant precedent requires reading everything. Pattern detection is impossible. This skill provides the taxonomy that makes governance memory navigable and analyzable.
  - **B.** Every decision record produced by the decision-record skill. Tags are metadata on the record, not a separate document.
  - **C.** A new decision record is created (initial tagging), a tag is discovered to be inaccurate (tag correction), the taxonomy is found insufficient for a new type of decision (taxonomy evolution).
  - **D.** For initial tagging: the decision record, the tagging taxonomy. For tag correction: the correction proposal and rationale. For taxonomy evolution: the proposed new tag category and rationale.
  - **E.** Initial tagging: (1) The decision record author applies required tags (domain, layer, skill, precedent_level, affected_parties) and any applicable optional tags (topic, related_precedents, ecosystem_scope, urgency_at_time). (2) A second participant (tag reviewer -- any participant knowledgeable about the decision) verifies tag accuracy. (3) If discrepancies are found, the tag reviewer proposes corrections and the recorder and reviewer reach agreement. If they cannot agree, the disputed tag is flagged for resolution by the governance memory steward. Tag correction: (4) Any participant can propose a tag correction with rationale. (5) Routine tag corrections (fixing a typo, adding a missing affected party) are processed by the governance memory steward without a consent process. (6) Precedent-level reclassification requires consent from the original deciding body or its delegate. Taxonomy evolution: (7) Any participant can propose a new tag category. (8) The governance memory steward assesses whether existing categories are truly insufficient. (9) New categories are added through an ACT consent process among all domain stewards who produce decision records (since the taxonomy affects everyone's tagging process).
  - **F.** Tagged decision record (for initial tagging), correction record (for tag corrections), updated taxonomy (for taxonomy evolution).
  - **G.** Tag reviewers verify accuracy but cannot alter the decision record's content. The governance memory steward has authority over taxonomy maintenance but not over individual record content. Precedent-level classification is the most consequential tag -- reclassification requires the most formal process.
  - **H.** Strategic mistagging (addressed by tag review), tag proliferation (addressed by required/optional distinction and periodic taxonomy review), classification gaming (addressed by reclassification consent process).
  - **I-L.** Full structural sections. J: The taxonomy itself is reviewed annually. Tags on individual records are reviewed when the related domain undergoes domain-review.
  OmniOne walkthrough: Tag three decisions of different types as specified in AC-3.6. Show the tag review catching an error.
  All 7 stress tests.
  Include YAML frontmatter with `depends_on: [decision-record]`.
  **Acceptance:** Passes validation. Under 500 lines. Taxonomy is clearly defined with examples.

- [ ] **Task 2.2: Create semantic-tagging assets**
  Create `assets/tagging-taxonomy.yaml`:
  ```yaml
  taxonomy_version: "1.0.0"
  last_reviewed: ""
  required_tags:
    domain:
      description: "The domain(s) that produced or are affected by this decision"
      type: list_of_strings
      examples: ["economics", "stewardship", "community_engagement"]
    layer:
      description: "The NEOS layer(s) involved"
      type: list_of_integers
      valid_range: [1, 10]
    skill:
      description: "The NEOS skill(s) used to produce this decision"
      type: list_of_strings
      examples: ["agreement-creation", "act-consent-phase", "domain-review"]
    precedent_level:
      description: "The significance of this decision as precedent"
      type: enum
      values: [routine, governance, constitutional]
    affected_parties:
      description: "The circles, roles, or individual categories affected"
      type: list_of_strings
  optional_tags:
    topic:
      description: "Free-text keyword topics for cross-cutting search"
      type: list_of_strings
      examples: ["resource_allocation", "meeting_process", "onboarding"]
    related_precedents:
      description: "IDs of related decision records"
      type: list_of_strings
    ecosystem_scope:
      description: "Geographic or organizational scope"
      type: enum
      values: [single_azpo, cross_azpo, ecosystem_wide]
    urgency_at_time:
      description: "The urgency level when the decision was made"
      type: enum
      values: [normal, elevated, emergency]
  ```
  **Acceptance:** Taxonomy is comprehensive and referenced in SKILL.md.

- [ ] **Task 2.3: Draft precedent-search SKILL.md -- full skill (sections A-L)**
  Build the complete precedent-search skill:
  - **A.** Without search, governance memory is write-only -- records exist but cannot be found. Participants relitigate settled questions because they do not know what was decided before. AI agents cannot provide governance guidance because they have no access to institutional knowledge. This skill makes governance memory usable by defining query capabilities and precedent application guidelines.
  - **B.** The entire governance memory -- all decision records across all layers, domains, and time periods. Search access is open to all participants.
  - **C.** A participant is drafting a proposal and wants to know if similar proposals have been decided before, a facilitator is running a governance process and wants to apply relevant precedent, a dispute arises and parties need to determine whether precedent exists, an AI agent is assisting a participant and needs to reference governance history.
  - **D.** Search query parameters (keyword, domain, layer, skill, date range, precedent level, affected parties, topic tags, compound queries), the governance memory index.
  - **E.** (1) Formulate query: the searcher specifies parameters. Compound queries combine parameters with AND logic (e.g., "domain:economics AND skill:authority-boundary-negotiation AND precedent_level:governance"). (2) Execute search: governance memory returns matching decision records ranked by relevance. Relevance ranking: exact domain match > related domain; governance/constitutional level > routine; more recent > older; more semantic tag overlap > fewer. (3) Evaluate results: the searcher reviews each result's holding and ratio decidendi. For each result, determine applicability: binding precedent (same domain, same type of decision, ratio decidendi directly applies to current situation), persuasive precedent (different domain or different type, but reasoning is informative and potentially applicable), informative only (interesting context but not directly applicable). (4) Document application: if a precedent will be cited in a governance process, the searcher creates a precedent application report documenting which precedent is being cited, which aspects of the ratio decidendi apply, and how the current situation is analogous. (5) Note challenges: if the searcher believes a found precedent should be challenged, they flag it for the precedent-challenge skill.
  - **F.** Precedent application report (when applying precedent) or search results summary (for informational queries).
  - **G.** Search access is open to all participants -- no proprietary archives. Application of precedent is advisory, not automatic -- no precedent dictates an outcome without a governance process. Citation is explicit: if a precedent informs a governance decision, it must be cited by decision record ID in the new decision record.
  - **H.** Selective citation (addressed by the search system returning all relevant results, including unfavorable ones). Precedent lock-in (addressed by precedent-challenge providing an evolution mechanism). Search manipulation (addressed by open access -- all participants can run the same search and verify results).
  - **I-L.** Full structural sections. I: Search returns no results (the searcher documents "no precedent found" and the governance process proceeds on first principles). Search returns contradictory precedents (the searcher documents both and the contradiction may trigger a precedent-challenge). K: Search access remains available to exited participants for their own decision records (they can see what they participated in) but not for records they were not party to.
  OmniOne walkthrough: A TH member searches before proposing a new space agreement, as specified in AC-2.6. Show the three types of precedent (binding, persuasive, informative) in the results.
  All 7 stress tests.
  Include YAML frontmatter with `depends_on: [decision-record, semantic-tagging]`.
  **Acceptance:** Passes validation. Under 500 lines. All three precedent types clearly distinguished.

- [ ] **Task 2.4: Create precedent-search assets**
  Create `assets/search-query-template.yaml`:
  ```yaml
  query_id: ""
  searcher: ""
  date: ""
  purpose: ""  # why the search is being conducted
  parameters:
    keywords: []
    domain: []
    layer: []
    skill: []
    date_range:
      from: ""
      to: ""
    precedent_level: []
    affected_parties: []
    topic_tags: []
    ecosystem_scope: ""
  compound_logic: "AND"  # how parameters are combined
  ```
  Create `assets/precedent-application-template.yaml`:
  ```yaml
  application_id: ""
  governance_process_context: ""  # what process this precedent is being applied to
  precedent_cited:
    decision_record_id: ""
    holding: ""
    ratio_decidendi_excerpt: ""
  applicability_type: binding | persuasive | informative
  applicability_rationale: ""  # why this precedent applies to the current situation
  analogous_elements: []  # what aspects of the current situation mirror the precedent
  distinguishing_elements: []  # what aspects differ
  recommendation: ""  # how the precedent should inform the current decision
  challenge_flag: false  # true if the searcher believes this precedent should be challenged
  challenge_grounds: ""  # if flagged, what grounds
  ```
  **Acceptance:** Both templates complete and referenced in SKILL.md.

- [ ] **Verification 2: Run validate_skill.py against decision-record, semantic-tagging, and precedent-search. All must pass. Verify: semantic-tagging's taxonomy is used consistently in decision-record's template. Precedent-search's query parameters map to semantic-tagging's tag categories. The three precedent types (binding, persuasive, informative) are consistently defined across both search and application templates.** [checkpoint marker]

---

## Phase 3: Agreement Versioning and Precedent Challenge

**Goal:** Build the remaining two skills: agreement-versioning (Git-style version control for living agreements) and precedent-challenge (the mechanism for evolving governance norms). After this phase, all 5 Layer IX skills are complete.

### Tasks

- [ ] **Task 3.1: Draft agreement-versioning SKILL.md -- full skill (sections A-L)**
  Build the complete agreement-versioning skill:
  - **A.** Without version control, agreement changes are invisible. Participants cannot determine what changed, when, why, or by whose authority. Disputes about agreement content become unresolvable when there is no authoritative history. This skill provides Git-style immutable versioning: every change is a committed snapshot with a diff, author, date, rationale, and link to the approval process.
  - **B.** Every agreement tracked in the agreement-registry (Layer I). This skill extends the registry with formal versioning. It applies to: the UAF, space agreements, access agreements, organizational agreement fields, and any other agreement type.
  - **C.** An agreement is created (v1.0.0), an agreement is amended (version increment), an agreement-review results in changes (version increment), a rollback is proposed (new version that reverts to prior state).
  - **D.** For version creation: the agreement change (from agreement-creation, agreement-amendment, or agreement-review), the approval record (consent/consensus record ID), the author of the change. For history query: the agreement ID and optional version parameters. For rollback proposal: the target version to revert to, rationale, and the proposing party.
  - **E.** Version creation: (1) triggered automatically when agreement-creation, agreement-amendment, or agreement-review produces a change. (2) Snapshot: full text of the agreement at this version. (3) Diff: comparison with previous version (additions, deletions, modifications -- element-by-element for structured agreements). (4) Metadata: version number, author, date, rationale, source skill, approval record ID. (5) Immutable commit: the version record cannot be modified after creation. Version numbering follows semver: major (structural changes to agreement purpose or scope), minor (substantive amendments to terms), patch (clarifications, typo fixes, formatting). History query: (6) Full history: retrieve all versions in chronological order. (7) Specific version: retrieve the agreement text at any point in time. (8) Diff query: compare any two versions to see what changed. (9) Blame query: for any section of the current agreement, determine which version introduced it and why. Rollback proposal: (10) A participant proposes reverting to a previous version. (11) This is treated as a new amendment proposal through the ACT process -- it is not a silent undo. (12) If consented to, a new version is created that matches the target version's content, with a rationale documenting why the rollback was necessary.
  - **F.** Version record (for version creation), version history report (for queries), rollback amendment proposal (for rollback).
  - **G.** Version creation is automatic and mandatory -- no agreement change can bypass versioning. No participant can edit a historical version. The agreement-registry steward ensures version integrity but cannot modify content. Rollback requires full ACT process consent.
  - **H.** Retroactive editing (immutability prevents modification of historical versions). Version suppression (all versions are visible to all participants). Rollback abuse (each rollback is a new consent process, preventing rapid-fire reversals). Version manipulation (the diff is generated algorithmically from the snapshots, not written by a human -- ensuring accuracy).
  - **I-L.** Full structural sections. I: Version conflict (two amendments are proposed simultaneously -- the first to achieve consent is committed; the second must be rebased against the new version). Corrupted version (snapshot does not match the diff -- the governance memory steward flags the inconsistency and the original source artifacts are used to reconstruct).
  OmniOne walkthrough: Full version history of the SHUR Bali kitchen space agreement as specified in AC-4.6. Show all four versions, a diff query between v1.0.0 and v2.0.0, and the edge case of a member questioning the consent record for v1.1.0.
  All 7 stress tests.
  Include YAML frontmatter with `depends_on: [decision-record, agreement-creation, agreement-amendment, agreement-review, agreement-registry]`.
  **Acceptance:** Passes validation. Under 500 lines. Semver convention clearly defined.

- [ ] **Task 3.2: Create agreement-versioning assets**
  Create `assets/version-record-template.yaml`:
  ```yaml
  version_record_id: ""
  agreement_id: ""
  version: ""  # semver: major.minor.patch
  previous_version: ""
  snapshot: ""  # full text or structured content at this version
  diff:
    additions: []
    deletions: []
    modifications:
      - section: ""
        was: ""
        now: ""
  author: ""
  date: ""
  rationale: ""
  source_skill: ""  # agreement-creation | agreement-amendment | agreement-review
  approval_record_id: ""
  is_rollback: false
  rollback_target_version: ""  # if is_rollback is true
  immutable: true  # always true; included for schema clarity
  ```
  **Acceptance:** Template complete.

- [ ] **Task 3.3: Draft precedent-challenge SKILL.md -- full skill (sections A-L)**
  Build the complete precedent-challenge skill:
  - **A.** Without a challenge mechanism, precedent becomes inertia. Decisions made under past circumstances continue to bind even when those circumstances have changed. The governance system cannot learn or adapt. Worse, participants who believe a precedent is wrong have no legitimate channel and resort to informal workarounds, creating hidden governance. This skill provides the formal mechanism for evolving governance norms while maintaining a transparent record of why things changed.
  - **B.** Any decision record with a precedent classification of "governance" or "constitutional." Routine decisions can also be challenged but the process is lighter (the challenger and the original deciding body can resolve bilaterally without a full ACT process).
  - **C.** A participant identifies a precedent that they believe should be reconsidered. Grounds: changed circumstances, flawed rationale, harmful outcomes, conflicting precedent, better alternative (as defined in FR-5).
  - **D.** The decision record being challenged (by ID), the specific ground for challenge, evidence supporting the challenge, the proposed alternative, the challenger's identity and standing.
  - **E.** (1) Challenger drafts a challenge brief using the challenge-brief-template. (2) The brief identifies: the decision record ID, the holding being challenged, the specific ground (from the five defined grounds), the evidence (what has changed, what flaw was found, what harm has resulted, which precedent conflicts, what better alternative exists), and the proposed replacement (what should the new holding be?). (3) The challenge is submitted to the body that originally made the decision. If that body no longer exists, the challenge goes to its structural successor (identified through domain-mapping's delegation chain). If no successor exists, the challenge goes to OSC. (4) The deciding body reviews the challenge through an ACT process: advice from all parties impacted by the original precedent and all parties who would be impacted by the proposed change, consent round on the outcome. (5) Outcomes: upheld (the precedent stands -- the challenge brief and the deciding body's rationale are recorded), modified (the precedent's holding is partially changed -- a new decision record is created, the original is marked "modified by [new ID]"), overruled (the precedent's holding is fully replaced -- a new decision record is created with mandatory documentation: which precedent was overruled, why the original rationale no longer applies, the new rationale). (6) For constitutional-level precedents: challenge requires OSC consent regardless of which body originally made the decision. (7) Consolidation: if multiple challenges are filed against the same precedent, they are consolidated into a single review process.
  - **F.** Challenge dismissal record (precedent upheld) or overruling decision record (precedent overruled/modified).
  - **G.** Any participant has standing to challenge any precedent. The deciding body for the challenge is the original body or its successor, not the challenger. The challenger cannot unilaterally overrule precedent. The deciding body cannot refuse to hear a formally submitted challenge -- it must process through ACT within 30 days.
  - **H.** Frivolous challenges (the challenge must specify a defined ground with evidence -- "I disagree" is not a valid challenge). Challenge suppression (the 30-day processing requirement prevents indefinite delay). Selective overruling (the mandatory documentation in overruling records creates transparency about which precedents are being overruled and why -- patterns of selective overruling can be detected through precedent-search). Chilling effect (fear that challenging precedent is politically dangerous -- the skill normalizes challenge as a healthy governance function, and the standing is universal, not limited to affected parties).
  - **I.** Cascade effects (overruling a precedent that other decisions relied on -- the new decision record must address downstream impacts; related records are flagged for review). Simultaneously valid contradictory precedents (the conflicting-precedent ground specifically addresses this -- one must yield, or both must be modified to be consistent). Dead-body challenge (challenging a precedent whose original body no longer exists and has no successor -- OSC serves as the default deciding body).
  - **J.** Challenges do not have an expiry. A precedent can be challenged at any time. However, challenges on "changed circumstances" grounds carry more weight the more time has passed (circumstances are more likely to have changed), while challenges on "flawed rationale" grounds carry more weight the sooner they are filed (the flaw was more likely to have been present from the beginning).
  - **K.** An exited participant's challenge (filed before exit) is still processed. An exited participant cannot file new challenges.
  - **L.** Cross-AZPO precedent challenges require the deciding body to include representation from all affected AZPOs.
  OmniOne walkthrough: Challenge to the resource allocation threshold precedent as specified in AC-5.6. Include the consolidation of two simultaneous challenges.
  All 7 stress tests.
  Include YAML frontmatter with `depends_on: [decision-record, precedent-search]`.
  **Acceptance:** Passes validation. Under 500 lines. All 5 challenge grounds clearly defined with examples.

- [ ] **Task 3.4: Create precedent-challenge assets**
  Create `assets/challenge-brief-template.yaml`:
  ```yaml
  challenge_id: ""
  challenger: ""
  date: ""
  precedent_challenged:
    decision_record_id: ""
    holding: ""
    date_of_original_decision: ""
    original_deciding_body: ""
    precedent_level: governance | constitutional
  ground: changed_circumstances | flawed_rationale | harmful_outcomes | conflicting_precedent | better_alternative
  evidence:
    description: ""
    supporting_data: []
    timeline_of_change: ""  # for changed_circumstances
    identified_flaw: ""     # for flawed_rationale
    documented_harm: ""     # for harmful_outcomes
    conflicting_record_id: "" # for conflicting_precedent
    alternative_description: "" # for better_alternative
  proposed_replacement:
    new_holding: ""
    new_rationale: ""
  impacted_parties: []
  ```
  Create `assets/overruling-record-template.yaml`:
  ```yaml
  overruling_id: ""
  date: ""
  challenge_id: ""
  precedent_overruled:
    decision_record_id: ""
    original_holding: ""
    original_date: ""
  outcome: upheld | modified | overruled
  deciding_body: ""
  new_holding: ""  # if modified or overruled
  why_original_rationale_no_longer_applies: ""  # mandatory for overrule
  new_rationale: ""
  downstream_impacts:
    - related_record_id: ""
      impact: ""
      action_required: ""
  consent_record_id: ""
  ```
  **Acceptance:** Both templates complete.

- [ ] **Verification 3: Run validate_skill.py against all 5 completed skills. All must pass. Verify the complete memory lifecycle: a decision is recorded (decision-record), tagged (semantic-tagging), searchable (precedent-search), versioned if it involves agreements (agreement-versioning), and challengeable (precedent-challenge). Verify cross-references: precedent-challenge correctly references decision-record for the record being challenged and precedent-search for finding precedents. Agreement-versioning correctly references agreement-creation, agreement-amendment, and agreement-review from Layer I.** [checkpoint marker]

---

## Phase 4: Layer Integration and README

**Goal:** Write the Layer IX README, create retroactive decision records for key foundation and authority track artifacts, and verify all quality gates.

### Tasks

- [ ] **Task 4.1: Write Layer IX README.md**
  Create `neos-core/layer-09-memory/README.md` with:
  - Layer title and purpose: "The Memory & Traceability Layer defines how governance decisions are recorded, classified, searched, versioned, and challenged -- creating the institutional memory that prevents knowledge loss and enables governance evolution."
  - List of all 5 skills with one-sentence descriptions and dependency lists
  - Diagram of skill relationships:
    ```
    decision-record (anchor)
         |
         +---> semantic-tagging
         |         |
         +---> precedent-search
         |
         +---> agreement-versioning (extends Layer I agreement-registry)
         |
         +---> precedent-challenge
    ```
  - How this layer interacts with:
    - Layer I (agreements are versioned; agreement-registry is complemented by universal decision records)
    - Layer II (domain contracts and boundary resolutions are recorded as governance decisions)
    - Layer III (ACT process outputs are recorded; precedent informs future proposals)
  - Key design decisions: generic wrapper (type-agnostic envelope), two-layer memory (deliberation + decision), holding/ratio/obiter dicta separation, immutability, open access, precedent classification, formal challenge mechanism
  - Anti-patterns guarded against
  **Acceptance:** README provides a complete overview.

- [ ] **Task 4.2: Create retroactive tagging plan**
  Since Layer IX did not exist when foundation and authority track artifacts were produced, create a plan for retroactively wrapping key existing artifacts in decision records. This is a document (not code), stored at `neos-core/layer-09-memory/references/retroactive-tagging-plan.md`:
  - Identify which foundation artifacts should get decision records: UAF ratification, initial agreement-registry creation, any constitutional-level decisions documented in the skills themselves
  - Identify which authority artifacts should get decision records: initial domain definitions, the Trunk Council domain contract and sunset
  - Define the retroactive tagging process: create decision records with "retroactive: true" tag, use the skill's walkthrough scenarios as the source material for holdings and rationale
  - Note: actual retroactive decision records are created during implementation of the respective tracks, not by this plan. This plan provides guidance.
  **Acceptance:** Plan is actionable and identifies specific artifacts to be retroactively documented.

- [ ] **Task 4.3: Add Layer IX extensibility notes to foundation skills**
  For each Layer I and Layer III skill that produces an output artifact:
  - Add a brief note in section L (Cross-Unit Interoperability Impact) or as a subsection: "Governance memory integration: The output artifact from this skill should be wrapped in a decision record (see decision-record skill, Layer IX) to ensure it becomes part of searchable governance memory."
  - This is an advisory note, not a structural dependency. Foundation skills do not depend on Layer IX; they note the integration point.
  Do NOT add Layer IX to the `depends_on` lists of foundation skills (the dependency is optional, not structural).
  Run validate_skill.py against all updated skills.
  **Acceptance:** All updated skills still pass validation. Notes are minimal and advisory.

- [ ] **Task 4.4: Cross-layer review**
  Perform a systematic review across all 5 Layer IX skills:
  - Verify all `depends_on` lists are accurate and complete
  - Verify all cross-references by name are to skills that exist
  - Verify terminology is consistent (product-guidelines.md terminology table)
  - Verify no hidden authority exists (governance memory steward role authority is explicitly defined)
  - Verify immutability principle is consistently applied across all skills
  - Verify open access principle is consistently applied
  - Verify the generic wrapper design is consistently referenced
  - Fix any inconsistencies found
  **Acceptance:** All cross-references valid. Design principles consistently applied.

- [ ] **Task 4.5: Final validation run**
  Run `validate_skill.py` against the entire `neos-core/` directory with `--verbose` flag (this includes all layers -- Layers I, II, III, and IX). Document the output. All skills must pass.
  **Acceptance:** `python scripts/validate_skill.py neos-core/ --verbose` exits with code 0.

- [ ] **Verification 4: Final human review. Read through each of the 5 Layer IX SKILL.md files confirming: voice matches product guidelines, every process step is actionable, immutability is never violated, open access is never restricted, the generic wrapper accommodates all known artifact types, the precedent system is internally consistent (classification -> search -> application -> challenge). Verify retroactive tagging plan is actionable. Mark the track complete.** [checkpoint marker]

---

## Phase 5: Quality Gate

**Goal:** Complete the per-layer quality checklist and confirm the track is done.

### Tasks

- [ ] **Task 5.1: Per-layer quality gate checklist**
  Complete the per-layer checklist from workflow.md:

  Layer IX:
  - [ ] All 5 skills complete
  - [ ] Skills cross-reference each other correctly
  - [ ] Layer README summarizes skills and relationships
  - [ ] No circular authority dependencies
  - [ ] Generic wrapper design accommodates all artifact types from Layers I, II, and III
  - [ ] Immutability principle consistently applied
  - [ ] Open access principle consistently applied
  - [ ] Precedent classification criteria are unambiguous
  - [ ] All 5 asset template sets are complete

  Foundation Integration:
  - [ ] Advisory notes added to Layer I and III skills
  - [ ] No validation regressions
  - [ ] Retroactive tagging plan created

  **Acceptance:** All checklist items confirmed.

- [ ] **Verification 5: Track complete. All 5 Layer IX skills built, validated, and reviewed. Layer README complete. Retroactive tagging plan created. Foundation integration notes added. Quality gates passed.** [checkpoint marker]

---

## Summary

| Phase | Skills Built | Cumulative Total | Integration Items |
|-------|-------------|-----------------|-------------------|
| Phase 1: Anchor | 1 (decision-record) | 1 | 0 |
| Phase 2: Tagging + Search | 2 (semantic-tagging, precedent-search) | 3 | 0 |
| Phase 3: Versioning + Challenge | 2 (agreement-versioning, precedent-challenge) | 5 | 0 |
| Phase 4: Integration | 0 (README, retroactive plan, cross-review) | 5 | 11 advisory notes |
| Phase 5: Quality Gate | 0 (checklist, final verification) | 5 | confirmed |

**Total deliverables:** 5 SKILL.md files, 8 asset files (6 YAML templates + 1 classification guide + 1 retroactive tagging plan), 1 Layer README, advisory notes on 11 foundation skills.
