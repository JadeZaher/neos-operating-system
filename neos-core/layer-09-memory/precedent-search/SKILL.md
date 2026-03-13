---
name: precedent-search
description: "Query governance memory to find relevant precedents before making new decisions -- without search, decision records are inert data that no one can use."
layer: 9
version: 0.1.0
depends_on: [decision-record, semantic-tagging]
---

# precedent-search

## A. Structural Problem It Solves

Without the ability to search governance memory, an ecosystem relitigates every question from scratch. Participants propose agreements that duplicate existing ones, raise objections that were already resolved, and ignore precedents that directly address their situation. The failure mode is not malicious -- it is structural. If finding relevant past decisions requires reading every record sequentially, no one will do it, and governance memory becomes a write-only archive. The precedent-search skill solves this by defining query parameters, relevance criteria, and application guidelines that transform governance memory from a storage system into a usable knowledge base. It also addresses a subtler failure: selective citation, where participants cite favorable precedents while ignoring unfavorable ones. The search system returns all relevant results, not a curated selection, and the precedent application report documents what was found and how it applies.

## B. Domain Scope

This skill applies to any participant in any domain who needs to find relevant governance precedent. Search access is open to all participants -- no governance memory is proprietary, no archives are restricted, and no tier of access exists. The skill covers: formulating search queries using the semantic tag taxonomy, evaluating search results for relevance, distinguishing binding from persuasive from informative precedent, and documenting how precedent informs a current decision. The skill does not prescribe the technical search implementation (database, full-text search, AI-assisted retrieval) -- it defines the governance query interface and application process. Out of scope: writing decision records (see decision-record), tagging decisions (see semantic-tagging), challenging precedents (see precedent-challenge).

## C. Trigger Conditions

- A participant is preparing a proposal and wants to know if similar decisions have been made before
- A facilitator is guiding a governance process and needs to surface relevant precedent for participants to consider
- An AI agent assisting a participant queries governance memory on their behalf to inform a draft proposal
- A conflict arises about whether a past decision applies to a current situation
- A domain steward is reviewing their domain's governance history as part of a periodic review
- A new member wants to understand the governance decisions that shaped the ecosystem

## D. Required Inputs

- **Search query**: one or more query parameters specifying what the searcher is looking for (keyword, domain, layer, skill, date range, precedent level, affected parties, semantic tags, or a compound combination)
- **Searcher identity**: who is performing the search (for audit trail purposes only -- identity does not restrict results)
- **Current context**: a brief description of the governance situation motivating the search, to guide relevance evaluation
- **Governance memory index**: the full corpus of tagged decision records available for search (maintained by the governance memory steward)

## E. Step-by-Step Process

1. **Formulate the query.** The searcher defines one or more query parameters. Available parameters: keyword or topic (matches against holdings, ratio decidendi, topic tags, and obiter dicta), domain filter (returns records from a specific domain), layer filter (returns records from a specific NEOS layer), skill filter (returns records produced by a specific skill), date range (returns records from a specific time period), precedent_level filter (routine, governance, or constitutional), affected_parties filter (returns records affecting specific individuals or circles), semantic tag filter (matches any tag in the taxonomy), and compound queries combining multiple parameters with AND/OR logic. The searcher states their current context to anchor the search.

2. **Execute the search.** The search is run against the governance memory index. All matching records are returned -- the system does not pre-filter based on the searcher's domain, role, or any other attribute. Results are presented with: record ID, date, holding (the single-statement summary), precedent level, domain, and matching tags. The full record is accessible for any result.

3. **Evaluate relevance.** The searcher evaluates each result for applicability to their current situation. The key question is: does this precedent's ratio decidendi (reasoning) apply to the current circumstances? Relevance assessment considers: similarity of facts (is the current situation sufficiently similar to the precedent's context?), similarity of governance question (is the same type of decision being made?), currency (has anything changed since the precedent was established that might affect its applicability?), and scope (does the precedent's domain and scope match the current situation?).

4. **Classify precedent applicability.** For each relevant result, the searcher classifies it as: **Binding** -- same domain, same type of decision, ratio decidendi still applies. The precedent's holding directly informs the current decision. Departing from a binding precedent requires explicit justification. **Persuasive** -- different domain or different type of decision, but the reasoning is informative. The precedent suggests an approach but does not dictate it. **Informative** -- the precedent provides useful context (e.g., what happened when a similar agreement was sunset) but does not directly apply. The searcher documents the classification rationale for each precedent.

5. **Document the precedent application.** The searcher produces a precedent application report (see `assets/precedent-application-template.yaml`) documenting: which precedents were found, which are relevant, how each relevant precedent is classified (binding, persuasive, informative), how each informs the current situation, and whether any should be challenged. The report is attached to the governance process as an input -- it becomes part of the advice phase record.

6. **Cite in governance process.** When the searcher introduces the precedent in a governance process (proposal, ACT advice phase, consent round), they cite the specific decision record IDs and explain how each precedent applies. Selective citation -- citing favorable precedents while omitting unfavorable ones -- is addressed by the precedent application report, which documents all relevant results found.

## F. Output Artifact

A precedent application report following `assets/precedent-application-template.yaml`. The report contains: the search query parameters used, the current governance context, all results found (with record IDs, holdings, and relevance assessment), each relevant precedent classified as binding, persuasive, or informative with rationale, the application analysis (how each precedent informs the current decision), and any recommendations to challenge existing precedents. The report is advisory -- no precedent automatically dictates a governance outcome. The report is attached to the governance process record and referenced in the resulting decision record's deliberation summary.

## G. Authority Boundary Check

Search access is open to all participants. No governance memory is proprietary. No participant, circle, steward, or council can restrict another participant's search access or filter their results. The governance memory steward maintains the search index but cannot curate or suppress results. The precedent application report is advisory -- applying precedent in a governance process requires explicit citation, and the governance process's own consent round determines the outcome. No precedent automatically binds a governance decision; binding precedent means the decision-maker must explicitly justify departing from it, not that they cannot depart. Authority to challenge a precedent found through search belongs to any participant (see precedent-challenge skill).

## H. Capture Resistance Check

**Capital capture.** Financial contributors cannot influence search results. The search index contains all decision records regardless of who funded the decisions that produced them. A donor cannot suppress unfavorable precedents or boost favorable ones. The precedent application report documents all relevant results, making selective omission visible.

**Charismatic capture.** A charismatic leader cannot ensure that their preferred precedents dominate search results. The search operates on structured metadata (tags, holdings, domains), not on social influence. When a charismatic leader cites a precedent in a governance process, any participant can run the same search and surface additional relevant precedents that the leader omitted.

**Emergency capture.** Crisis framing cannot be used to skip precedent search. Even under emergency timelines, the search step takes minutes and prevents the ecosystem from making emergency decisions that contradict established precedent without knowing it. Post-emergency review includes verifying whether relevant precedent was considered.

**Informal capture.** Verbal claims of precedent ("we already decided this") have no standing unless backed by a searchable decision record. The search system is the single source of truth for what was decided. Claimed precedents that do not appear in search results are not precedent.

## I. Failure Containment Logic

- **Search returns no results**: the searcher documents that no relevant precedent exists. This is itself valuable information -- it means the governance question is novel and the decision will establish new precedent.
- **Search returns too many results**: the searcher narrows the query using compound filters (date range + domain + precedent level). The precedent application report can note that an exhaustive search was impractical and document the filtering rationale.
- **Searcher misclassifies precedent applicability**: the precedent application report is part of the advice phase record. Other participants in the governance process can review the classification and challenge it. Misclassification does not block the process.
- **Search index is incomplete**: if the governance memory steward identifies gaps (records exist but are not indexed), they flag the gaps. The searcher notes potential incompleteness in their report. Missing records are indexed as a maintenance priority.
- **Selective citation despite report**: if a participant cites favorable precedents but ignores unfavorable ones found in the same search, any other participant can reference the full precedent application report. The report exists specifically to prevent selective citation.

## J. Expiry / Review Condition

Precedent search queries do not expire -- a search can be run at any time. Precedent application reports are point-in-time documents; they reflect the state of governance memory when the search was conducted. If new decision records are added after a search, the report does not automatically update. For long-running governance processes (proposals that take weeks to move through ACT), the searcher should re-run the query before the consent round to capture any new precedent. The governance memory steward reviews search index completeness quarterly to ensure all registered decision records are searchable. Precedent classifications (binding, persuasive, informative) are the searcher's assessment at a point in time and can be re-evaluated in future searches.

## K. Exit Compatibility Check

When a participant exits, precedent application reports they authored remain valid as historical documents. The reports reference decision records by ID, and those records persist regardless of the searcher's departure. If the exiting participant was the governance memory steward responsible for index maintenance, the domain-mapping skill triggers reassignment within the 30-day wind-down period. Search access for remaining participants is unaffected by any departure. New members joining after departures have full search access from their first day of active status -- governance memory is a shared resource, not a seniority privilege.

## L. Cross-Unit Interoperability Impact

Precedent search operates across all AZPOs in the ecosystem by default. A participant at SHUR Costa Rica can search for precedents from SHUR Bali and vice versa. Cross-AZPO search uses the shared tagging taxonomy to filter by ecosystem_scope (single-azpo, cross-azpo, ecosystem-wide). When a governance decision at one AZPO cites a precedent from another AZPO, the precedent is classified as persuasive (different unit, reasoning informative) unless the deciding body explicitly adopts it as binding for their context. Cross-ecosystem precedent search (between two separate NEOS ecosystems) is deferred to Layer V federation, but the search query parameters and precedent classification framework are designed to be portable across ecosystems.

## OmniOne Walkthrough

TH member Ravi is preparing a proposal to create a new shared space agreement for the SHUR Bali rooftop area. Before drafting his proposal, he searches governance memory to find relevant precedents.

Ravi formulates his search query with compound parameters: domain=Town-Hall OR domain=Operations, topic=space-agreement OR topic=shared-space, precedent_level=governance OR precedent_level=constitutional. His current context: "Proposing creation of a new shared space agreement for the SHUR Bali rooftop, including usage hours, noise guidelines, and maintenance responsibilities."

The search returns 7 results. Ravi evaluates each for relevance and identifies 3 that directly apply:

**Precedent 1 (Binding): DR-OMNI-2025-019 -- SHUR Bali Kitchen Space Agreement creation.** Holding: "The kitchen shared space agreement establishes usage hours, cleaning responsibilities, and quiet hours for the SHUR Bali kitchen area, created through the agreement-creation skill with consent from all affected residents." This is binding precedent -- same domain (Town Hall), same type of decision (shared space agreement creation at SHUR Bali), and the ratio decidendi (establishing usage norms through resident consent with explicit quiet hours and maintenance duties) directly applies to the rooftop proposal. Ravi notes he should follow the same structural approach: usage hours, responsibility assignment, and quiet hours.

**Precedent 2 (Persuasive): DR-OMNI-2025-034 -- Economics/Operations boundary negotiation for shared infrastructure.** Holding: "The Economics circle manages resource allocation frameworks; Operations manages day-to-day maintenance execution." This is persuasive precedent -- different skill (boundary negotiation, not agreement creation) but the reasoning about separating policy-setting from operational execution is informative for the rooftop agreement. Ravi considers structuring the rooftop agreement to separate usage policy (set by residents through consent) from maintenance operations (delegated to a responsible steward).

**Precedent 3 (Informative): DR-OMNI-2026-011 -- Sunset of the outdoor yoga space agreement.** Holding: "The outdoor yoga space agreement is sunset because the space was physically reconfigured and the agreement's subject matter no longer exists." This is informative -- it shows what happens when a space agreement becomes obsolete, reminding Ravi to include a review clause and conditions for sunset in his rooftop proposal.

Ravi completes the precedent application report documenting all 7 results, the 3 relevant ones with their classifications, and how each informs his proposal. He attaches the report to his proposal draft and enters the ACT advice phase citing: "I followed the structure established in DR-OMNI-2025-019 (kitchen agreement, binding precedent), incorporated the policy/operations separation from DR-OMNI-2025-034 (persuasive), and added a sunset clause informed by DR-OMNI-2026-011 (informative)."

Edge case: During the advice phase, AE member Kenji points out that Ravi's search did not surface DR-OMNI-2025-027, a governance-level decision about noise standards across all SHUR shared spaces. Kenji runs his own search filtered by topic=noise-standards and finds the record. Ravi updates his precedent application report to include this additional binding precedent and revises his noise guidelines accordingly. The full report now documents 4 relevant precedents, and the advice phase record reflects that the search was iteratively refined -- a healthy governance practice, not a failure.

## Stress-Test Results

### 1. Capital Influx

A major donor has funded the construction of a new shared space at SHUR Bali and wants the space agreement to reflect their preferences. Before the proposal enters the ACT process, the donor's ally searches governance memory selectively, citing only precedents that support minimal restrictions on the space. The precedent-search skill counters this because any participant can run the same search and surface additional relevant precedents. The precedent application report documents all results, not just favorable ones. When another participant runs a broader search and finds precedents establishing noise standards, maintenance responsibilities, and resident consent requirements for all shared spaces, those precedents enter the advice phase alongside the selective citations. The structured classification (binding, persuasive, informative) makes clear which precedents are most applicable. The donor's financial contribution cannot suppress search results or alter the governance memory index. The search system returns the same results regardless of who is searching.

### 2. Emergency Crisis

A structural safety concern at SHUR Bali requires immediate closure of the rooftop shared space. The Operations steward invokes emergency authority to close the space. Is there precedent for emergency closures and what happens to the associated space agreement? A quick precedent search filtered by topic=emergency AND domain=Operations returns relevant records in minutes. Even under emergency timelines, the search step is fast and prevents contradictory emergency actions. If no precedent exists, the search documents that this is a novel situation -- the emergency decision will establish new precedent. Post-emergency review includes verifying that the emergency action was consistent with or consciously departed from existing precedent. The search system operates independently of crisis conditions and does not require special access or permissions during emergencies.

### 3. Leadership Charisma Capture

A charismatic OmniOne founder frequently cites their own past decisions as precedent in governance discussions, claiming "we already settled this." The precedent-search skill neutralizes this tactic because any participant can verify the claim by searching governance memory. If the claimed precedent exists, the search returns the actual holding and ratio -- which may differ from the founder's characterization. If the claimed precedent does not exist as a formal decision record, it has no standing as precedent regardless of who claims it. The search system operates on structured data (tags, holdings, record IDs), not on social authority. When the founder cites a precedent, any participant can immediately search for the record, read the actual holding, and evaluate whether the founder's characterization is accurate. This transforms "trust my memory" claims into verifiable, structured queries.

### 4. High Conflict / Polarization

Two polarized factions within OmniOne are debating a resource allocation change. Each faction searches governance memory and cites only the precedents that support their position. The precedent-search skill addresses this through the precedent application report, which documents all results found -- not just the ones the searcher wants to cite. When both factions produce reports, a facilitator can compare them and identify: precedents cited by one faction but omitted by the other, conflicting precedents that need resolution, and shared precedents both factions acknowledge. The GAIA escalation framework applies if the precedent dispute intensifies -- a Level 3 facilitator can guide both factions through a joint precedent review, identifying where the precedents genuinely conflict and where the conflict is about interpretation rather than fact. The structured classification (binding vs. persuasive vs. informative) helps separate genuine precedent conflicts from rhetorical positioning.

### 5. Large-Scale Replication

OmniOne scales to 5,000 participants across 15 SHUR locations. Governance memory contains thousands of decision records. The precedent-search skill scales because search is query-driven -- participants search for specific topics, domains, or tags, not browsing the entire archive. The compound query parameters (domain + topic + date range + precedent level) narrow results to manageable sets. Location-specific tags enable a participant at SHUR Mexico to search their local precedents without wading through records from 14 other locations. Cross-location search remains available for participants who need ecosystem-wide precedent. The governance memory steward circle (scaled from a single steward) maintains index quality across locations. Not every participant searches governance memory -- only those preparing proposals, guiding governance processes, or researching specific questions. The skill's per-query cost is constant regardless of ecosystem size.

### 6. External Legal Pressure

A government regulator requests that OmniOne demonstrate how its governance decisions are tracked and retrievable. The precedent-search skill supports this because governance memory is structured, tagged, and searchable -- the ecosystem can run filtered queries and produce precedent application reports that demonstrate governance traceability. The search system's open access principle means there are no hidden archives or restricted databases that the ecosystem must explain or justify to regulators. However, external parties do not have direct search access -- the ecosystem runs queries on behalf of external requests through its own governance process. The UAF sovereignty principle means the ecosystem decides which specific records to share with external authorities, using its own search infrastructure, not granting external access to the search system itself.

### 7. Sudden Exit of 30% of Participants

Fifteen of fifty OmniOne members depart. Governance memory and the search system remain intact -- decision records are ecosystem artifacts, not personal property. The departing members' precedent application reports remain valid as historical documents. The immediate impact is that some governance areas may have fewer participants who understand the local precedent history. The search system mitigates this by making all precedent discoverable regardless of who originally authored or searched for it. New members joining after the exodus can search governance memory from their first day, finding the same precedents that the departed members would have cited. The governance memory index is unaffected by departures. If the governance memory steward departed, the domain-mapping skill triggers reassignment to ensure index maintenance continues during the 30-day wind-down period.
