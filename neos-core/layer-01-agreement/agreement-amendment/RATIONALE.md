---
skill: agreement-amendment
type: rationale
---

# agreement-amendment — Rationale & Design Notes

## A. Structural Problem It Solves

Without a formal amendment process, agreements either become stale (never updated because no one knows how) or are changed informally (someone rewrites the text without process, and affected parties discover the change after the fact). This skill ensures every modification to an existing agreement has a clear scope, proper authorization proportional to the change's impact, and a full ACT process that produces a traceable version history. It prevents the "who changed this and when?" failure mode.

## B. Domain Scope

Any existing active agreement in the agreement registry. Amendment types: minor clarification (fixing ambiguous language without changing meaning), substantive change (modifying terms, adding or removing commitments), scope expansion (extending the agreement to cover additional parties or domains), and scope reduction (narrowing the agreement's applicability). Each type maps to a different minimum ACT level.

## OmniOne Walkthrough

The AE realizes that the existing ETHOS agreement field for the Education circle needs updating. The current agreement specifies that "all educational materials produced within the circle are shared works" — but a new contributor, Naia, has brought a proprietary curriculum she developed independently before joining OmniOne. The existing language would retroactively classify her pre-existing work as shared, which contradicts the UAF's original works protections.

An AE steward, Ravi, proposes an amendment: change the clause to "educational materials co-created within the circle are shared works; materials brought by individual contributors retain their original-works designation as defined in the UAF." Amendment type: substantive change (modifying a core IP commitment). The facilitator verifies the classification — this is not a minor clarification because it changes what work falls under shared stewardship.

The amendment routes to full ACT: 7-day advice phase with all 8 Education circle members plus Naia. During advice, one member raises a concern: this could create a two-tier system where new contributors' pre-existing work is protected but collaborative work building on it becomes shared. Ravi integrates this concern by adding: "Emergent works that incorporate an original work are co-stewarded, with the original work's creator credited and retaining rights to the original components."

Consent phase: 7 of 8 circle members present (quorum met). In Round 1, one member objects: the amendment is too complex and could be exploited by someone contributing minimal original work and claiming exemption for all their output. Integration round: Ravi modifies to add a clear definition — "original works must be documented and timestamped as pre-existing before being used in circle projects." Round 2: all consent. The amendment is ratified, the ETHOS agreement field version increments to 1.1.0, and the registry links the amendment record with the full consent record.

## Stress-Test Results

### 1. Capital Influx

A donor who funded the Education circle's infrastructure pressures an amendment to the ETHOS agreement that would give them oversight of how funded resources are used. The amendment enters normal ACT process. During advice, multiple circle members identify this as capital capture — oversight authority in exchange for funding contradicts NEOS principles. The consent phase records objections grounded in the structural principle that financial contribution does not grant governance authority. The amendment fails at consent. The existing agreement remains unchanged. The donor's contribution stands independently of governance structure — they funded infrastructure, not authority.

### 2. Emergency Crisis

A critical safety incident at SHUR requires immediate amendment of a space access agreement to restrict access to a damaged area. Three circle members invoke emergency provisions. The amendment enters emergency ACT: 24-hour advice, compressed consent with 50% minimum quorum. The amendment is ratified within 36 hours with clear revert conditions: access restrictions expire when structural assessment confirms safety. The emergency amendment auto-expires in 30 days. The permanent resolution (if the damage requires long-term changes) requires a new full-process amendment.

### 3. Leadership Charisma Capture

A respected leader proposes a series of three "minor clarification" amendments to the AE operating agreement over two months. Each change is small, but cumulatively they shift decision-making authority toward the leader's circle. The facilitator reviews the amendment history in the registry and reclassifies the third amendment as a substantive change — the cumulative effect exceeds minor clarification threshold. The amendment must now go through full ACT with all affected parties, not just the abbreviated process. The registry's version history makes the pattern visible to all participants, preventing incremental authority capture.

### 4. High Conflict / Polarization

Two factions disagree on an amendment to the resource-sharing agreement. One wants to increase the minimum allocation to smaller circles; the other wants performance-based allocation. The consent phase produces objections from both sides. After three integration rounds, no synthesis emerges. The amendment escalates to GAIA Level 4 coaching. The coach identifies that both factions share a concern about fairness — they disagree on the mechanism. The third solution: a hybrid model with a guaranteed minimum floor (addressing the equity concern) plus a performance bonus pool (addressing the incentive concern). The synthesized amendment returns to consent and passes.

### 5. Large-Scale Replication

At scale, the ecosystem has 400+ active agreements, with amendments proposed weekly. The registry's version history system handles amendment volume through structured records and domain-based routing. Most amendments are circle-internal (minor clarifications handled quickly). Cross-circle amendments are less frequent but follow the same process at broader scope. The classification system ensures that each amendment receives process proportional to its impact — minor clarifications don't burden the full ecosystem, while substantive changes get full scrutiny.

### 6. External Legal Pressure

A regulation requires modifying a data-handling agreement to include mandatory retention periods. The amendment is proposed through normal ACT process — external legal requirements do not bypass governance. During advice, participants evaluate how to implement the legal requirement while minimizing surveillance infrastructure. The amendment is scoped to the specific jurisdiction requiring compliance and does not modify the agreement globally. Other locations using the same agreement template are notified but not bound by the jurisdiction-specific amendment.

### 7. Sudden Exit of 30% of Participants

After a mass departure, several agreements have amendments in progress. Amendments where the proposer has departed are adopted by remaining affected parties or archived if no one adopts. Amendments where the affected-party composition has significantly changed are flagged for re-evaluation — the departure may have changed the context that motivated the amendment. Agreements that lost their primary stewards are flagged for the agreement-review skill to assign new stewards before amendments proceed.
