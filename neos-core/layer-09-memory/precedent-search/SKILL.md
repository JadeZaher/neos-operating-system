---
name: precedent-search
description: "Query governance memory to find relevant precedents before making new decisions -- without search, decision records are inert data that no one can use."
layer: 9
version: 0.1.0
depends_on: [decision-record, semantic-tagging]
---

# precedent-search

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

Precedent search operates across all ETHOS in the ecosystem by default. A participant at SHUR Costa Rica can search for precedents from SHUR Bali and vice versa. Cross-ETHOS search uses the shared tagging taxonomy to filter by ecosystem_scope (single-ethos, cross-ethos, ecosystem-wide). When a governance decision at one ETHOS cites a precedent from another ETHOS, the precedent is classified as persuasive (different unit, reasoning informative) unless the deciding body explicitly adopts it as binding for their context. Cross-ecosystem precedent search (between two separate NEOS ecosystems) is deferred to Layer V federation, but the search query parameters and precedent classification framework are designed to be portable across ecosystems.
