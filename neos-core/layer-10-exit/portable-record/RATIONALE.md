---
skill: portable-record
type: rationale
---

# portable-record — Rationale & Design Notes

## A. Structural Problem It Solves

Governance experience is invisible outside the system where it was earned. A member who spent three years stewarding circles, resolving conflicts, and building agreements leaves with nothing but their own memory. The next ecosystem they join has no way to understand their governance literacy, and the member starts from zero -- as if their years of participation never happened. This creates two structural failures: ecosystems cannot benefit from incoming members' proven experience, and members have no portable proof of their governance contributions. Traditional organizations solve this with reference letters (subjective, gatekept) or LinkedIn profiles (self-reported, unverifiable). This skill produces a structured, verifiable governance record that the member owns, controls, and can present to any receiving ecosystem -- turning governance participation into portable, machine-readable credentials.

## B. Domain Scope

This skill applies to any departing ecosystem member who requests a portable governance record. The record covers the member's full participation history within the departing ecosystem: identity, ecosystems participated in, roles held, agreements created or joined, proposals authored and their outcomes, ACT participation records, conflict resolution involvement, resource stewardship, Current-See history, and departure records. The skill interacts with the decision-record skill (Layer IX) for ACT participation data, the semantic-tagging skill (Layer IX) for record classification, and the voluntary-exit skill for departure context. Out of scope: the record does not include subjective evaluations, peer reviews, or performance ratings. It documents participation, not quality judgments.

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
