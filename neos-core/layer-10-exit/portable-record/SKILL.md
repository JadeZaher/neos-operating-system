---
name: portable-record
description: "Generate a structured, machine-readable governance participation history that a departing member owns and carries -- run this during any departure to ensure governance experience travels with the person, not trapped in the ecosystem they leave."
layer: 10
version: 0.1.0
depends_on: [decision-record, semantic-tagging, voluntary-exit]
---

# portable-record

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
