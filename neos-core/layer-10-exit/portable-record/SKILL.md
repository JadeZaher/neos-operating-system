---
name: portable-record
description: "Generate a structured, machine-readable governance participation history that a departing member owns and carries -- run this during any departure to ensure governance experience travels with the person, not trapped in the ecosystem they leave."
layer: 10
version: 0.1.0
depends_on: [decision-record, semantic-tagging, voluntary-exit]
---

# portable-record

## A. Structural Problem It Solves

Governance experience is invisible outside the system where it was earned. A member who spent three years stewarding circles, resolving conflicts, and building agreements leaves with nothing but their own memory. The next ecosystem they join has no way to understand their governance literacy, and the member starts from zero -- as if their years of participation never happened. This creates two structural failures: ecosystems cannot benefit from incoming members' proven experience, and members have no portable proof of their governance contributions. Traditional organizations solve this with reference letters (subjective, gatekept) or LinkedIn profiles (self-reported, unverifiable). This skill produces a structured, verifiable governance record that the member owns, controls, and can present to any receiving ecosystem -- turning governance participation into portable, machine-readable credentials.

## B. Domain Scope

This skill applies to any departing ecosystem member who requests a portable governance record. The record covers the member's full participation history within the departing ecosystem: identity, ecosystems participated in, roles held, agreements created or joined, proposals authored and their outcomes, ACT participation records, conflict resolution involvement, resource stewardship, Current-See history, and departure records. The skill interacts with the decision-record skill (Layer IX) for ACT participation data, the semantic-tagging skill (Layer IX) for record classification, and the voluntary-exit skill for departure context. Out of scope: the record does not include subjective evaluations, peer reviews, or performance ratings. It documents participation, not quality judgments.

## C. Trigger Conditions

- **Voluntary exit**: the departing member requests a portable record as part of the voluntary-exit process (offered by default during every departure)
- **Periodic export**: any active member may request a current snapshot of their portable record at any time, without departing
- **ETHOS dissolution**: all members of a dissolving ETHOS receive portable records as part of the dissolution process
- **Federation request**: when a member applies to join a federated NEOS ecosystem, they may generate a current portable record for presentation

## D. Required Inputs

- **Member identity**: confirmed ecosystem identity of the member requesting the record
- **Ecosystem records**: data from the agreement-registry, role-assignment records, decision logs, conflict resolution logs, resource allocation ledger, and Current-See ledger
- **Privacy preferences**: the member's explicit choices about which categories and details to include (mandatory minimum: identity and departure status)
- **Record period**: the time range to cover (default: full membership tenure)
- **Output format preference**: YAML (primary), JSON (alternative), or markdown summary

## E. Step-by-Step Process

1. **Receive export request.** The departing member (or active member requesting a snapshot) submits a portable record request to the departure coordinator or any governance facilitator. The request specifies privacy preferences and desired format.
2. **Query source registries.** The coordinator or automated system queries all relevant registries for the member's participation data: agreement-registry (agreements created, joined, amended), role-assignment records (roles held with tenure dates), decision logs (proposals authored, ACT participation, consent positions), conflict resolution logs (disputes, mediations, outcomes), resource allocation ledger (stewardship, Current-See history), and departure records (if any prior departures exist).
3. **Apply privacy filters.** The member's privacy preferences are applied to the raw data. The mandatory minimum is identity and departure status -- everything else is opt-in. The member may include or exclude any category or specific record. Categories: roles (full detail, summary, or excluded), agreements (full detail, summary, or excluded), proposals (full detail, summary, or excluded), ACT participation (full detail, summary, or excluded), conflict resolution (full detail, summary, or excluded), resources (full detail, summary, or excluded), Current-See history (full detail, summary, or excluded).
4. **Generate structured record.** The system compiles the filtered data into the portable record schema (`assets/portable-record-schema.yaml`). Each entry includes a source reference (which registry, which record ID) to enable verification without ongoing dependency on the source ecosystem.
5. **Generate verification hash.** A cryptographic hash is computed over the record contents and the source registry state at the time of generation. The hash allows a receiving ecosystem to verify that the record has not been tampered with, without needing to contact the source ecosystem. The source ecosystem retains a copy of the hash for independent verification if requested.
6. **Deliver record to member.** The completed portable record is delivered to the member in their requested format. The member receives the record file and the verification hash. The member owns the record and may share it with anyone at their discretion.
7. **Archive generation event.** The ecosystem records that a portable record was generated (date, member, scope, format) in the governance memory (Layer IX). The ecosystem does not retain a copy of the record contents -- only the generation metadata and verification hash.

## F. Output Artifact

A Portable Governance Record following `assets/portable-record-schema.yaml`. The record contains: record ID, generation date, member identity, ecosystem identity, verification hash, and sections for each included category (roles, agreements, proposals, ACT participation, conflict resolution, resources, Current-See history, departure records). Each section includes individual entries with source references. A markdown summary is appended for human readability regardless of the primary format. The record is the member's property -- the ecosystem has no authority over its distribution after delivery.

## G. Authority Boundary Check

- **Any member** can request their own portable record at any time, with no approval required
- **No individual or body** can deny, delay, or condition a portable record request
- **The member** has sole authority over privacy preferences -- no one can compel inclusion or exclusion of specific records
- **The ecosystem** must provide data from its registries when queried for a portable record; it cannot withhold governance data that the member participated in
- **Receiving ecosystems** decide independently how much weight to give a portable record -- the source ecosystem has no authority over how the record is used after delivery
- **The verification hash** enables integrity checking without requiring ongoing cooperation from the source ecosystem

## H. Capture Resistance Check

**Information capture.** The portable record prevents ecosystems from holding governance experience hostage. A member's participation history belongs to them, not to the ecosystem. The mandatory minimum (identity and departure status) ensures that even a member who chooses maximum privacy still leaves with proof of their governance participation.

**Narrative capture.** The record contains structured data, not subjective evaluations. No one can append "not recommended" or "left under difficult circumstances" to a portable record. The data speaks for itself: roles held, proposals authored, conflicts resolved. Interpretation is left to the receiving ecosystem.

**Verification capture.** The cryptographic hash enables verification without ongoing dependency on the source ecosystem. A hostile or defunct source ecosystem cannot retroactively invalidate a member's record by refusing to respond to verification requests. The hash is self-contained.

**Privacy capture.** The member controls what is included. A member who participated in a sensitive conflict resolution can exclude that record. A member who wants to showcase their proposal track record can include full detail. No one else makes these choices.

## I. Failure Containment Logic

- **Registry data incomplete**: if any source registry has gaps (e.g., early participation before digital record-keeping), the portable record notes the gap with the known time period and available data; the record is not blocked by incomplete data
- **Privacy preference conflict**: if the member requests inclusion of a record that involves other members' identities (e.g., a conflict resolution with a named counterpart), the other party's identity is anonymized by default unless that party consents to inclusion
- **Verification hash generation fails**: the record is delivered without a hash, with a notation that verification is unavailable; the member can request hash generation later once the technical issue is resolved
- **Member requests record post-departure**: if a former member requests an updated record after leaving, the ecosystem generates it from archived data; the former member's right to their record does not expire with membership
- **Format conversion error**: if the requested format cannot be generated, the record is delivered in YAML (the primary format) with instructions for manual conversion

## J. Expiry / Review Condition

Portable governance records do not expire. The record represents historical fact -- it cannot become invalid over time. The portable record schema (`assets/portable-record-schema.yaml`) is versioned and reviewed annually through the ACT consent process to ensure it remains compatible with evolving governance structures. Older records generated under previous schema versions remain valid; receiving ecosystems should support backward-compatible parsing. The verification hash remains valid indefinitely against the archived registry state.

## K. Exit Compatibility Check

This skill is a core component of the exit process. The portable record is generated during every voluntary exit and ETHOS dissolution, ensuring that no member leaves empty-handed. The record captures the output of the commitment-unwinding process (if the member chooses to include it) and the departure record. The skill ensures that exit is not just operationally clean but informationally complete -- the member carries their governance history with them.

## L. Cross-Unit Interoperability Impact

The portable record schema is standardized across all NEOS ecosystems, enabling cross-ecosystem portability. A member who departs OmniOne and joins a new ETHOS in a different NEOS ecosystem presents a record that the receiving ecosystem can parse, verify, and evaluate using the same schema. Cross-ecosystem portability is informational, not prescriptive: the receiving ecosystem decides how much weight to give the record's contents. The verification hash enables trust without requiring the receiving ecosystem to contact the source ecosystem. When two NEOS ecosystems federate (Layer V, deferred), portable records may be exchanged automatically as part of member transfer protocols.

## OmniOne Walkthrough

Rina, the departing AE member from the Bali SHUR, requests a full portable record as part of her voluntary exit. Her departure coordinator Kadek initiates the portable-record process on day 15 of Rina's 30-day handoff period.

Kadek queries the OmniOne registries for Rina's 14-month participation history. The queries return: 2 roles held (Comms Steward, Proposal Reviewer) with tenure dates, 3 agreements (UAF, comms protocol, equipment stewardship) with her role in each, 4 proposals authored (2 consented, 1 withdrawn, 1 transferred to Dewa during commitment unwinding), 18 ACT participation records showing her consent positions on circle proposals, 1 conflict mediation where she served as a volunteer mediator, 45 Current-Sees allocated (now returned during unwinding), and her full Current-See participation history (14 months of equal-influence governance participation).

Rina reviews the privacy options. She chooses full detail for roles, agreements, proposals, and Current-See history -- she wants to showcase her governance experience. She chooses summary-only for ACT participation (she does not want every consent position visible). She excludes the conflict mediation record entirely -- the dispute was sensitive and she prefers it remain private. The departure coordinator applies her preferences.

The system generates Portable Governance Record PGR-OMNI-2026-RINA following the schema. Each entry includes a source reference (e.g., "agreement-registry:UAF-2025-001") enabling verification. A verification hash is computed over the record contents and the current registry state. Rina receives the YAML file and the hash.

**Edge case**: Rina plans to present her record to a new ETHOS forming in Costa Rica. The Costa Rica ecosystem runs on NEOS but is not yet federated with OmniOne. The Costa Rica onboarding facilitator receives Rina's portable record, parses the YAML, and verifies the hash against the embedded registry references. The hash confirms the record has not been tampered with. The facilitator notes Rina's 14 months of governance experience, her two circle roles, and her proposal track record. The Costa Rica ETHOS does not automatically grant Rina a role, but her experience informs their role-assignment process -- she is not starting from zero. Rina's excluded conflict mediation record remains invisible; the Costa Rica ETHOS has no way to know it existed.

Rina receives her portable record on day 18 of the handoff period, alongside a markdown summary she can share informally. She carries 14 months of verified governance experience in a structured file that she owns and controls.

## Stress-Test Results

### 1. Capital Influx

A major funder demands access to departing members' portable records as a condition of continued funding, claiming the need to "assess governance quality." The portable record skill is structurally immune: the record belongs to the departing member, not the ecosystem. The ecosystem cannot share, aggregate, or analyze member records for external parties. The funder receives the same answer regardless of their financial leverage: individual members may voluntarily share their records, but the ecosystem has no authority to compel disclosure or provide aggregated data. If the funder wants governance quality metrics, those come from governance health audits (Layer VII), which are published to all members but do not contain individual participation records.

### 2. Emergency Crisis

During an emergency evacuation, three members depart urgently with 7-day timelines. The portable-record skill generates abbreviated records based on available data -- some registry queries may be incomplete due to disrupted systems. The records are delivered with a "generated under emergency conditions" notation and a list of registries that were unavailable. Post-emergency, the ecosystem offers to regenerate complete records from restored archives. The members' right to their records is not suspended by the emergency. The verification hashes are generated against available data, with a notation that completeness may be affected. Receiving ecosystems that parse these records can see the emergency notation and request updated records from the member once full archives are restored.

### 3. Leadership Charisma Capture

A charismatic leader attempts to influence portable records by asking the governance facilitator to add positive annotations to loyalists' records and negative annotations to critics' records. The portable-record skill's structure makes this impossible: the record contains only structured data from registries (roles held, proposals authored, agreements joined) -- there is no field for subjective evaluation or annotation. The leader cannot inject narrative into a format that only contains participation facts. Even if the leader controls the governance facilitator role, the facilitator has no mechanism to modify registry data for portable record purposes. The verification hash would expose any tampering, since it is computed against the actual registry state at the time of generation.

### 4. High Conflict / Polarization

Members from both factions in a polarized ecosystem depart simultaneously and request portable records. Each departing member controls their own privacy preferences -- faction A members cannot see what faction B members included or excluded. The records contain the same structured data regardless of factional alignment. If both factions were involved in the same conflict resolution process, each departing member independently decides whether to include that record. The portable record does not become a factional weapon because it contains no narrative framing, no evaluative language, and no information about other members' records. Each member's record tells their own governance story, not the faction's.

### 5. Large-Scale Replication

At 4,000 members across 12 SHUR locations, portable record generation becomes a routine operation. The standardized schema ensures every record has the same structure regardless of which ETHOS generated it. Registry queries scale across ETHOS boundaries when a member participated in multiple locations. Automated generation reduces coordinator burden -- the coordinator reviews privacy preferences and initiates the query, but compilation and hash generation are systematic. Cross-ecosystem portability becomes valuable as members move between NEOS networks: a member departing OmniOne in Bali and joining a NEOS-governed cooperative in Portugal presents a record that the Portuguese ecosystem can parse using the same schema, even though the two ecosystems have never communicated. The schema is the interoperability layer.

### 6. External Legal Pressure

A government agency requires disclosure of members' governance participation as part of a civil investigation. The portable record skill does not interact with external legal demands directly -- the ecosystem cannot produce individual records for external parties because the records belong to members. If a court order compels a specific member to disclose their record, that is the member's legal obligation, not the ecosystem's. If a court order targets the ecosystem's registries directly, the ecosystem's legal entity (GEV) responds through legal channels. The portable record skill's design -- where the ecosystem retains only generation metadata and a verification hash, not the record contents -- limits what the ecosystem can disclose even if compelled. The member's privacy preferences are sovereign within the governance system; external legal authority operates through different channels.

### 7. Sudden Exit of 30% of Participants

Twelve members depart simultaneously, each requesting portable records. The generation process scales linearly -- each member's record is an independent query against the same registries. The main bottleneck is coordinator review of privacy preferences, which can be parallelized across multiple coordinators. If the system is overwhelmed, members can receive preliminary records (identity and departure status only -- the mandatory minimum) immediately, with full records delivered within 14 days post-departure. The members' right to their records does not expire with departure -- they can request complete records at any point afterward. The mass departure does not degrade individual record quality; each member receives the same structured, verified, complete (or explicitly noted as incomplete) record they would receive in a single-departure scenario.
