---
name: semantic-tagging
description: "Classify and tag every governance decision for retrieval, pattern detection, and cross-domain search -- without tags, governance memory is a warehouse with no shelving system."
layer: 9
version: 0.1.0
depends_on: [decision-record, domain-mapping]
---

# semantic-tagging

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

2. **Apply optional tags.** The author applies optional tags where relevant. Optional tags: topic (free-text keywords describing the decision's subject matter, maximum 5), related_precedents (decision record IDs of related or relevant prior decisions), ecosystem_scope (single-ethos, cross-ethos, or ecosystem-wide), urgency_at_time (normal, elevated, or emergency). Optional tags left blank are omitted, not filled with placeholder values.

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

Tags use a shared taxonomy across all ETHOS in the ecosystem, enabling cross-unit search. When a decision at one ETHOS affects another, the ecosystem_scope tag is set to "cross-ethos" and affected_parties includes participants from all affected units. The tagging taxonomy is ecosystem-wide -- individual ETHOS do not maintain separate taxonomies, which would fragment search. When NEOS is adopted by multiple ecosystems, each ecosystem maintains its own taxonomy but the required tag categories (domain, layer, skill, precedent_level, affected_parties) are structurally identical, enabling cross-ecosystem search on shared categories. Full cross-ecosystem taxonomy federation is deferred to Layer V.
