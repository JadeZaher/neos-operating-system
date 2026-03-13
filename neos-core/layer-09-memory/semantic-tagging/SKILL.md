---
name: semantic-tagging
description: "Classify and tag every governance decision for retrieval, pattern detection, and cross-domain search -- without tags, governance memory is a warehouse with no shelving system."
layer: 9
version: 0.1.0
depends_on: [decision-record, domain-mapping]
---

# semantic-tagging

## A. Structural Problem It Solves

Without structured tagging, governance memory degrades into an unsearchable archive. Decisions pile up with no classification, no cross-referencing, and no way to detect patterns across domains. A facilitator searching for "all decisions that affected shared infrastructure" must read every record manually. Worse, without tag quality controls, strategic actors can bury constitutional-level decisions under routine labels, hiding their significance from future searchers. The semantic-tagging skill solves this by defining a mandatory tagging taxonomy applied to every decision record at creation time, a lightweight review process that catches misclassification, and a governed evolution mechanism so the taxonomy adapts without drifting into incoherence. Tags are the connective tissue of governance memory -- they transform isolated records into a queryable body of knowledge.

## B. Domain Scope

This skill applies to every decision record created through the decision-record skill, regardless of which domain, layer, or skill produced the underlying decision. Tags are metadata on the decision record envelope, not a separate document. The taxonomy covers required tags (applied to every record) and optional tags (applied when relevant). The skill scope includes: defining the tag categories and valid values, the tagging process at record creation, the tag review process, tag correction procedures, and taxonomy evolution. Out of scope: the search engine that queries tags (see precedent-search), the decision record format itself (see decision-record), and automated tag suggestion algorithms (software implementation).

## C. Trigger Conditions

- A new decision record is created through the decision-record skill and requires initial tagging before registration
- A participant identifies a tagging error on an existing decision record and requests correction
- The governance memory steward identifies tag quality issues during a periodic review
- A participant or circle proposes a new tag category or value because the existing taxonomy is insufficient
- Retroactive tagging is needed for pre-existing governance artifacts that were created before Layer IX was established

## D. Required Inputs

- **Decision record draft**: the record to be tagged, with holding, ratio, domain, and source skill already specified (provided by the decision-record author)
- **Tagging taxonomy**: the current valid taxonomy including required and optional categories (maintained by the governance memory steward, see `assets/tagging-taxonomy.yaml`)
- **Domain registry**: the current list of recognized domains to validate the domain tag (from domain-mapping, Layer II)
- **Participant registry**: active participants and their domain memberships, for validating affected_parties tags (from the ecosystem's participant records)
- **Tag reviewer identity**: one participant other than the record author who verifies tag accuracy (assigned by convention within the authoring domain or by the governance memory steward)

## E. Step-by-Step Process

1. **Apply required tags.** The decision record author applies all required tags during record creation. Required tags: domain (which domain produced the decision, validated against domain registry), layer (which NEOS layer, integer 1-10), skill (which skill was used, kebab-case name), precedent_level (routine, governance, or constitutional -- with stated rationale), affected_parties (list of individuals, circles, or participant classes impacted by the decision). The author references the tagging taxonomy for valid values.

2. **Apply optional tags.** The author applies optional tags where relevant. Optional tags: topic (free-text keywords describing the decision's subject matter, maximum 5), related_precedents (decision record IDs of related or relevant prior decisions), ecosystem_scope (single-azpo, cross-azpo, or ecosystem-wide), urgency_at_time (normal, elevated, or emergency). Optional tags left blank are omitted, not filled with placeholder values.

3. **Tag review.** Within 48 hours of the decision record draft being shared for factual verification (Step 8 of decision-record), one participant other than the author reviews the tags for accuracy. The reviewer checks: correct domain assignment, appropriate precedent level classification, complete affected_parties list, accurate layer and skill references, and reasonable topic keywords. The reviewer may add missing optional tags.

4. **Resolve tag disputes.** If the reviewer disagrees with a tag (especially precedent_level), they document the disagreement with rationale. The author and reviewer attempt resolution. If they cannot agree, the dispute is surfaced to the governance memory steward or resolved through a lightweight consent process by the original deciding body. Tag disputes do not block record registration -- the record is registered with the disputed tag flagged.

5. **Register tagged record.** Once tags are applied and reviewed, the decision record is registered in governance memory with its full tag set. Tags become part of the immutable record. Future tag corrections follow Step 6.

6. **Correct tags on existing records.** Any participant can propose a tag correction on a registered record. The proposer states which tag is incorrect, what the correct value should be, and why. The governance memory steward or original recorder reviews the correction. Approved corrections are appended as tag amendments (the original tags remain visible with the correction noted), preserving the audit trail. Corrections to precedent_level require consent from the original deciding body.

7. **Evolve the taxonomy.** When participants consistently need a tag category that does not exist, any participant can propose a taxonomy addition. The proposal enters a consent process facilitated by the governance memory steward. Approved additions are documented in the taxonomy with an effective date. Existing records are not retroactively re-tagged unless explicitly scoped in the consent decision. Taxonomy changes are themselves documented as governance-level decision records.

## F. Output Artifact

A tagged decision record -- the decision record with semantic tags populated in its metadata section, following the taxonomy defined in `assets/tagging-taxonomy.yaml`. The tags are not a separate document but fields within the decision record envelope. The output includes: all required tags validated against the taxonomy, optional tags where applicable, the reviewer's identity and verification date, and any tag dispute annotations. Tag amendments on existing records produce a tag correction annotation appended to the record with the corrector's identity, date, original value, corrected value, and rationale.

## G. Authority Boundary Check

The decision record author has authority to apply initial tags. One designated reviewer verifies tags -- this is a factual accuracy check, not a gatekeeping role. No single participant can unilaterally reclassify a record's precedent level after registration; reclassification requires consent from the original deciding body. The governance memory steward maintains the taxonomy and resolves tag disputes, but cannot alter tags on individual records without following the correction process. Taxonomy evolution (adding new categories) requires consent from the body responsible for governance memory stewardship. No participant can remove tags from a finalized record -- corrections are appended, not deletions.

## H. Capture Resistance Check

**Capital capture.** Financial contributors cannot influence how decisions are tagged. Tags reflect the decision's actual characteristics (domain, layer, affected parties), not a funder's preferred framing. A funder cannot pressure the tagger to classify a governance-level decision as "routine" to reduce its visibility. The tag review by a second participant catches any financially motivated misclassification.

**Charismatic capture.** A charismatic leader cannot ensure their favored decisions receive inflated precedent classifications (marking routine decisions as "constitutional" to elevate their legacy). The required rationale for precedent_level classification and the independent tag review prevent personality-driven inflation or deflation of decision significance.

**Emergency capture.** Emergency decisions receive the urgency_at_time=emergency tag, which triggers post-emergency review. Crisis framing cannot be used to skip the tagging process -- emergency decisions still receive full tags, applied within 48 hours of the emergency subsiding, consistent with the decision-record emergency timeline.

**Informal capture.** Untagged decision records are incomplete and flagged during registration. The tagging process is mandatory, not optional. Records without required tags cannot be registered in governance memory, preventing informal bypass of the classification system.

## I. Failure Containment Logic

- **Author fails to tag within 48 hours**: the governance memory steward assigns a tagger from among the decision's participants. The record is registered with a "pending-tags" flag visible in search results.
- **No reviewer available**: the governance memory steward serves as reviewer of last resort. If the steward authored the record, any participant from the affected domain can review.
- **Tag dispute blocks registration**: the record is registered with the disputed tag flagged. The dispute is resolved through the normal process without delaying access to the record.
- **Taxonomy proves insufficient**: participants document the gap and propose a taxonomy evolution through Step 7. In the interim, they use the closest existing tags and add a free-text topic tag describing the missing category.
- **Retroactive tagging overload**: when Layer IX is first established, existing records need tagging. The governance memory steward prioritizes constitutional-level records first, governance-level second, routine third. Records tagged retroactively carry a "retroactive" annotation.

## J. Expiry / Review Condition

Tags do not expire but the taxonomy requires periodic review. The tagging taxonomy is reviewed annually by the governance memory steward and the body responsible for governance memory, through a consent process. The review evaluates: tag categories that are never used (candidates for removal), free-text topic tags that appear frequently (candidates for promotion to the formal taxonomy), precedent_level distributions (if 95% of records are "routine," the classification may lack nuance), and feedback from participants who search governance memory on tag usefulness. Taxonomy review produces a decision record documenting any changes. Individual tag corrections on records have no expiry -- a tag error can be corrected at any time through the documented process.

## K. Exit Compatibility Check

When a participant exits, tags they applied to decision records remain valid and unchanged -- tags describe the decision's characteristics, not the tagger's personal status. If the exiting participant was the governance memory steward, the domain-mapping skill triggers reassignment within the 30-day wind-down period. The exiting participant's name remains in tag reviewer fields as historical record. Tags referencing the exiting participant in affected_parties remain accurate (they were affected at the time of the decision). No tag is invalidated by a participant's departure. If the exiting participant was the only qualified reviewer in a domain, the governance memory steward designates a replacement for future tag reviews.

## L. Cross-Unit Interoperability Impact

Tags use a shared taxonomy across all AZPOs in the ecosystem, enabling cross-unit search. When a decision at one AZPO affects another, the ecosystem_scope tag is set to "cross-azpo" and affected_parties includes participants from all affected units. The tagging taxonomy is ecosystem-wide -- individual AZPOs do not maintain separate taxonomies, which would fragment search. When NEOS is adopted by multiple ecosystems, each ecosystem maintains its own taxonomy but the required tag categories (domain, layer, skill, precedent_level, affected_parties) are structurally identical, enabling cross-ecosystem search on shared categories. Full cross-ecosystem taxonomy federation is deferred to Layer V.

## OmniOne Walkthrough

The OmniOne governance memory steward Nia needs to ensure three recent decisions are properly tagged. The decisions vary in scope and significance, testing the full tagging taxonomy.

**Decision 1: Routine meeting schedule change.** TH member Davi facilitated a consent round to move the weekly Community Circle meeting from Tuesday to Thursday. The decision record DR-OMNI-2026-051 is straightforward. Davi applies required tags: domain=Town-Hall, layer=3, skill=act-consent-phase, precedent_level=routine (rationale: "schedule change with no governance implications"), affected_parties=[Community Circle members, approximately 30 people]. He applies one optional tag: topic=[meeting-schedule]. No related precedents, scope is single-azpo (SHUR Bali), urgency is normal. Tag reviewer Amara, another TH member, confirms the tags in 20 minutes. Record is registered.

**Decision 2: Governance-level consent process change.** AE steward Kenji facilitated a consent round that modified how stand-asides are documented in OmniOne consent processes. The decision record DR-OMNI-2026-052 is more significant. Kenji applies required tags: domain=Agents-of-Ecosystem, layer=3, skill=act-consent-phase, precedent_level=governance (rationale: "modifies a governance norm affecting all future consent processes"), affected_parties=[all active OmniOne participants]. Optional tags: topic=[consent-process, stand-aside-documentation], related_precedents=[DR-OMNI-2025-008 (original consent process definition)], ecosystem_scope=ecosystem-wide, urgency_at_time=normal.

Tag reviewer Priya reviews and catches an error: Kenji listed affected_parties as "all active OmniOne participants" but missed that this change also affects the onboarding process, which references the consent documentation format. Priya adds "Onboarding circle" to affected_parties and adds related_precedents=[DR-OMNI-2025-022 (onboarding documentation standards)]. Kenji agrees with both corrections. The record is registered with Priya's additions.

**Decision 3: Constitutional-level UAF amendment.** The OSC facilitated a consent round amending the UAF's sovereignty clause to clarify how OmniOne interacts with local legal frameworks in different countries. Decision record DR-OMNI-2026-053. OSC recorder Tomoko applies required tags: domain=OSC, layer=1, skill=agreement-amendment, precedent_level=constitutional (rationale: "amends the foundational governance document"), affected_parties=[all OmniOne participants, all AZPOs, GEV]. Optional tags: topic=[sovereignty, legal-framework, UAF-amendment, international-operations], related_precedents=[DR-OMNI-2025-001 (original UAF ratification), DR-OMNI-2025-031 (previous sovereignty interpretation)], ecosystem_scope=ecosystem-wide, urgency_at_time=normal. This record receives mandatory review by a second OSC member, who confirms all tags.

Edge case: Six months later, governance memory steward Nia runs a taxonomy review and notices that 14 decisions have been tagged with the free-text topic "resource-allocation" but this is not a formal taxonomy entry. She proposes adding "resource-allocation" as a formal topic keyword through a consent process. The AE circle consents, and Nia documents the taxonomy update as decision record DR-OMNI-2026-089. She does not retroactively change the 14 existing records -- they already use the correct term as a free-text tag.

## Stress-Test Results

### 1. Capital Influx

A large external donor contributes significant funds to OmniOne and attempts to influence how financial decisions are tagged. The donor privately suggests to the Economics circle recorder that resource allocation decisions benefiting the donor's preferred projects should be tagged as "routine" rather than "governance" to reduce their visibility and avoid scrutiny. The semantic-tagging skill prevents this because precedent_level classification requires a stated rationale, and the independent tag reviewer would flag a governance-scope resource allocation decision misclassified as routine. If the reviewer misses it, any participant can propose a tag correction at any time with documented reasoning. The governance memory steward's periodic taxonomy review would also surface unusual patterns -- a cluster of resource allocation decisions all tagged "routine" despite their governance implications would raise questions. The immutability of the tag audit trail means that even if a misclassification temporarily succeeds, the correction process documents who tagged it, when, and what the original tag was, creating accountability for strategic mistagging.

### 2. Emergency Crisis

A natural disaster at SHUR Bali forces emergency governance decisions about resource reallocation, temporary authority expansions, and operational changes. Multiple decisions are made within hours under crisis conditions. The semantic-tagging skill requires all emergency decisions to be tagged within 48 hours of the emergency subsiding, consistent with the decision-record emergency timeline. The urgency_at_time=emergency tag is mandatory for all crisis decisions, which triggers automatic post-emergency review of both the decisions and their tags. Under emergency conditions, the tag review step can be deferred (the record is registered with a "pending-review" flag) but cannot be skipped entirely. The governance memory steward ensures all emergency records receive tag review within 7 days of the emergency subsiding. This prevents emergency decisions from entering governance memory with inaccurate classifications that could distort future precedent searches.

### 3. Leadership Charisma Capture

A charismatic OmniOne co-founder consistently tags their decisions with elevated precedent levels -- marking routine circle decisions as "governance" to inflate their significance in governance memory. The semantic-tagging skill resists this through the independent tag review process. The reviewer examines the precedent_level rationale and challenges inflated classifications. If the charismatic leader pressures the reviewer socially, any participant can propose a tag correction after registration, creating a structural check beyond the initial review. The governance memory steward's periodic review examines precedent_level distributions by author -- if one person's decisions are disproportionately classified as governance or constitutional, this pattern is surfaced for community discussion. The structured rationale requirement means the leader must justify each classification in writing, not merely assert it through social authority. Tag corrections preserve the original classification alongside the corrected one, making inflation attempts permanently visible.

### 4. High Conflict / Polarization

Two OmniOne factions disagree intensely about a resource allocation decision. The losing faction claims the decision record was strategically mistagged to minimize its precedent value -- tagged as "routine" when it should be "governance." The semantic-tagging skill handles this through the tag correction process. Any participant can propose a reclassification with documented rationale. The proposal goes to the original deciding body (or its successor) for a lightweight consent process. The GAIA escalation framework applies if the tag dispute itself becomes polarized -- a facilitator coaches both sides toward a third solution, perhaps recognizing that the decision has governance-level implications for one domain but routine implications for others. The correction process documents both positions, the rationale for the final classification, and any dissent. This transforms a polarizing dispute about tags into a structured governance process with a recorded outcome that future participants can reference.

### 5. Large-Scale Replication

OmniOne scales from 50 to 5,000 participants across 15 SHUR locations. Decision volume increases proportionally, making tag quality critical for search usability. The semantic-tagging skill scales because tagging is distributed -- each decision's author and reviewer handle their own tags, not a centralized tagger. The shared taxonomy provides consistency across locations without requiring coordination. Location-specific domains (SHUR-Bali-Operations, SHUR-CR-Operations) appear in the domain tag, enabling location-scoped search. The governance memory steward role scales to a Memory circle with location-specific stewards who coordinate taxonomy reviews. The required/optional tag distinction prevents tag proliferation -- at 5,000 participants, the temptation to add dozens of optional categories grows, but the annual taxonomy review evaluates which tags actually improve search quality. Free-text topic tags absorb new concepts without requiring taxonomy changes, while frequently used topics are promoted to formal categories during reviews.

### 6. External Legal Pressure

A government regulator in Indonesia demands that OmniOne classify certain governance decisions using the regulator's own taxonomy (e.g., labeling decisions as "financial," "operational," or "compliance-related" for regulatory reporting). The semantic-tagging skill handles this without compromising its own taxonomy. The ecosystem can add a "regulatory_classification" optional tag category through the taxonomy evolution process, applying regulator-required labels alongside the NEOS taxonomy. The NEOS taxonomy is not altered to match external requirements -- the ecosystem's own governance memory system operates according to its own principles. The UAF's sovereignty principle means the ecosystem cooperates with legal requirements through its own governance process: a proposal to add regulatory tags enters the ACT process, the consent round evaluates whether it serves the ecosystem's interests, and the outcome is documented as a decision record. External pressure cannot unilaterally alter how the ecosystem classifies its own decisions.

### 7. Sudden Exit of 30% of Participants

Fifteen of fifty OmniOne members depart following a contentious decision. Several departing members were primary taggers and tag reviewers in their domains. The semantic-tagging skill handles this because tags on existing records are immutable -- they remain valid regardless of who applied them. The departing members' names remain in reviewer fields as historical record. The immediate challenge is ensuring ongoing decisions have qualified taggers and reviewers. The governance memory steward identifies domains where departures have left gaps and assigns replacement reviewers from remaining participants. If the governance memory steward themselves departed, the domain-mapping skill triggers reassignment during the 30-day wind-down. New members joining after the exodus inherit the full tagged governance memory and can search it immediately. The taxonomy itself is unaffected by departures -- it is an ecosystem artifact, not dependent on any individual's continued participation.
