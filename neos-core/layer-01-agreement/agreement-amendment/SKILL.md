---
name: agreement-amendment
description: "Modify an existing agreement through proper process -- classifying the amendment type, routing through the appropriate ACT level, and producing a versioned amendment record that maintains the full change history."
layer: 1
version: 0.1.0
depends_on: [agreement-creation, act-advice-phase, act-consent-phase, act-test-phase, domain-mapping]
---

# agreement-amendment

## A. Structural Problem It Solves

Without a formal amendment process, agreements either become stale (never updated because no one knows how) or are changed informally (someone rewrites the text without process, and affected parties discover the change after the fact). This skill ensures every modification to an existing agreement has a clear scope, proper authorization proportional to the change's impact, and a full ACT process that produces a traceable version history. It prevents the "who changed this and when?" failure mode.

## B. Domain Scope

Any existing active agreement in the agreement registry. Amendment types: minor clarification (fixing ambiguous language without changing meaning), substantive change (modifying terms, adding or removing commitments), scope expansion (extending the agreement to cover additional parties or domains), and scope reduction (narrowing the agreement's applicability). Each type maps to a different minimum ACT level.

## C. Trigger Conditions

- A participant identifies that an existing agreement needs modification due to outdated terms, new circumstances, identified gaps, or conflict with another agreement
- The agreement-review skill produces a "revise" outcome, triggering this skill with specific changes identified
- A conflict resolution process identifies an agreement provision as the source of tension
- An agreement at a higher level in the hierarchy is amended, requiring lower-level agreements to be checked for consistency

## D. Required Inputs

- **Amendment proposer**: identity, role, and authority scope
- **Parent agreement ID**: the specific agreement being amended, with its current version number
- **Amendment type**: minor_clarification, substantive_change, scope_expansion, or scope_reduction
- **Proposed changes**: in diff format — what the text currently says and what it will say after amendment
- **Rationale**: why the change is needed, what problem it addresses, what happens if the agreement remains as-is
- **Affected parties**: all parties currently bound by the agreement plus any new parties affected by the amendment

## E. Step-by-Step Process

1. **Classify amendment type.** The proposer identifies the amendment type. The facilitator verifies the classification — a proposer cannot classify a scope expansion as a minor clarification to avoid fuller process.
2. **Route to minimum ACT level** based on type:
   - *Minor clarification* (fixing ambiguous language): circle-level consent of parties bound by the agreement. Advice phase is abbreviated (3 days).
   - *Substantive change* (modifying terms): full ACT cycle with all affected parties.
   - *Scope expansion* (adding parties or domains): full ACT cycle including both current and proposed-new affected parties.
   - *Scope reduction* (narrowing applicability): full ACT cycle with parties who will lose coverage — they must consent to the change.
   - *UAF amendment*: OSC consensus mode (all steward council members must actively agree). No abbreviated process regardless of amendment type.
3. **Run appropriate ACT phases.** Per the act-advice-phase, act-consent-phase, and act-test-phase skills. The test phase applies to substantive changes and scope changes; minor clarifications may skip testing by consent.
4. **Produce amendment record.** Per `assets/amendment-record-template.yaml`: amendment ID, parent agreement ID, amendment type, proposer, diff of changes, rationale, ACT level used, consent record ID, new agreement version number.
5. **Update registry.** The agreement in the registry is updated to the new version with the amendment record linked. The prior version is archived (not deleted) in the version history.

## F. Output Artifact

An amendment record per `assets/amendment-record-template.yaml` linked to the parent agreement, plus the updated agreement document with incremented version number. The registry reflects: the new version, the amendment date, the amendment type, and a link to the full amendment record including the consent record from the ACT process.

## G. Authority Boundary Check

- **Amendment scope cannot exceed the amending body's domain.** A circle cannot amend an ecosystem-level agreement. An ETHOS cannot amend another ETHOS's agreement field.
- **UAF amendments require OSC consensus** — this cannot be delegated to any sub-body. The highest-bar decision process applies to the highest-level agreement.
- **Amendment cannot create authority** that the original agreement did not grant. If the original agreement defines circle-level authority, an amendment cannot expand that to ecosystem-level authority without going through the appropriate ecosystem-level ACT process.
- **The proposer cannot reclassify** the amendment type after ACT routing — if the facilitator determines a "minor clarification" is actually a substantive change, the process escalates to the appropriate level.

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

## H. Capture Resistance Check

**Capital capture.** A donor pressures amendment of an accountability agreement to weaken oversight of funded projects. The full ACT process ensures all affected parties evaluate the amendment on structural merits. The donor's financial contribution does not modify the consent threshold or grant them special standing in the consent round.

**Amendment laundering.** A series of "minor clarifications" that cumulatively constitute a substantive change. The facilitator tracks amendment history and may reclassify an amendment as substantive if the cumulative effect crosses the threshold. The registry's version history makes the pattern visible.

**Emergency amendment.** A crisis is used to push through amendments under compressed timelines. Emergency timelines apply but the consent round cannot be eliminated. Emergency amendments auto-expire per provisional emergency rules and must be re-proposed through normal process for permanent effect.

## I. Failure Containment Logic

- **Consent fails on amendment**: the existing agreement remains unchanged. The amendment proposal may be revised and re-proposed.
- **Amendment creates conflict with higher-level agreement**: identified during synergy check or advice phase. The amendment cannot proceed until the conflict is resolved — either by amending the higher-level agreement first (through its own process) or by modifying the proposed amendment to be consistent.
- **Partial ratification** (some affected parties consent, others object): the amendment does not take effect. It returns to advice with the objectors' specific concerns documented.
- **Amendment proposer loses authority** (role change during process): another party within the domain may adopt the amendment proposal per standard adoption rules.

## J. Expiry / Review Condition

- Amendments do not have separate review dates — they modify the parent agreement, which retains its own review schedule.
- If an amendment expands the agreement's scope, the parent agreement's review date may be brought forward by the review body.
- Emergency amendments auto-expire in 30 days and must be re-proposed through normal process for permanence.

## K. Exit Compatibility Check

- If the amendment proposer exits, the amendment process continues if adopted by another party. The amendment's merit does not depend on the proposer's ongoing participation.
- If parties affected by the amendment exit, the amendment's affected-party list is re-evaluated. If the amendment becomes moot (e.g., scope reduction for parties who have all departed), it may be archived.
- Amendments ratified before a participant's exit remain in effect for remaining parties.

## L. Cross-Unit Interoperability Impact

- Amendments to agreements that span multiple ETHOS require consent from each affected ETHOS's deciding body.
- When a parent agreement is amended, the registry notifies all ETHOS that hold linked entries (child agreements that reference the parent).
- Cross-ecosystem agreement amendments follow inter-unit coordination (Layer V, deferred). Both ecosystems must consent through their own processes.

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
