---
name: agreement-registry
description: "Maintain and query the single source of truth for all active agreements -- handling writes from agreement-creation, amendment, and review, and providing open query access to any participant."
layer: 1
version: 0.1.0
depends_on: [agreement-creation, agreement-amendment, domain-mapping]
---

# agreement-registry

## A. Structural Problem It Solves

Without a registry, participants cannot determine what agreements exist, which ones apply to them, or whether an agreement has been superseded by a newer version. Governance becomes archaeology — digging through past decisions to reconstruct the current state. This skill provides the single source of truth for all agreements: their status, version history, relationships, and full text. Any participant can query the registry. Only authorized processes can write to it. The registry makes governance transparent and navigable.

## B. Domain Scope

The entire ecosystem. The registry holds every agreement at every level of the hierarchy: UAF, ecosystem agreements, access agreements, stewardship agreements, ETHOS agreement fields, culture codes, and personal commitments (where formally registered). The registry spans all ETHOS within the ecosystem and maintains links to cross-ETHOS agreements.

## C. Trigger Conditions

**Write triggers:**
- An agreement is created through the agreement-creation skill (new entry)
- An agreement is amended through the agreement-amendment skill (version update)
- An agreement is reviewed through the agreement-review skill (status update, new review date, or sunset)

**Query triggers:**
- Any participant queries for agreements that apply to their roles, domains, or spaces
- The synergy check in proposal-creation queries for existing or conflicting agreements
- The onboarding process queries for all agreements a new participant must consent to
- Any skill that references the agreement registry for validation or context

## D. Required Inputs

**For writes:** the output artifact from the invoking skill (agreement-creation, agreement-amendment, or agreement-review). No direct writes to the registry are permitted from any other source.

**For queries:** query parameters including any combination of: agreement type, domain, affected party identity, status (active/under_review/sunset/archived), date range (created, amended, review due), and compound queries combining multiple parameters.

## E. Step-by-Step Process

**Write operations:**
1. **Validate incoming artifact.** Confirm the artifact comes from an authorized skill (agreement-creation, amendment, or review). Reject any direct write attempts.
2. **Assign or update entry.** For new agreements: generate a unique agreement ID following the ecosystem's naming convention (e.g., AGR-SHUR-2026-003). For amendments: increment the version number and link the amendment record. For reviews: update status and review date.
3. **Update version history.** Add an entry to the agreement's version history documenting the change type, date, and linked record ID.
4. **Notify affected parties.** All participants listed as affected parties receive notification of the registry change.
5. **Cross-reference check.** Verify the agreement does not conflict with any higher-level agreement in the hierarchy. If a potential conflict is detected, flag it (but do not reject — the conflict must be resolved through proper ACT process).

**Query operations:**
1. **Accept query parameters.** Parse the query: by type, by domain, by affected party, by status, by date range, or compound.
2. **Return matching agreements.** Results include: agreement ID, title, type, status, current version, domain, review date, and a link to full text. Results are sorted by relevance (domain match first, then recency).
3. **Support compound queries.** Example: "all active space agreements in the SHUR Bali domain created in the last year" combines type=space, status=active, domain=SHUR Bali, created_date>2025-03-01.

## F. Output Artifact

**For writes:** the updated registry state with the new or modified entry, plus notifications sent to affected parties.
**For queries:** a result set containing agreement summaries with metadata and links to full text. Empty result sets are valid (no matching agreements found).

## G. Authority Boundary Check

- **Write access** is restricted to output artifacts from agreement-creation, agreement-amendment, and agreement-review. No individual, circle, or council can directly modify registry entries. This is the registry's integrity guarantee.
- **Query access** is open to all ecosystem participants with no restrictions. Transparency is a structural principle — no secret agreements.
- The **registry steward** (a role, not a permanent person) maintains registry integrity — ensuring entries are properly formatted, cross-references are valid, and flags are addressed. The steward cannot modify agreement content; they maintain the infrastructure.
- The registry steward is appointed by consent of the body the registry serves and is subject to review per the provisional authority model.

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

## H. Capture Resistance Check

**Registry manipulation.** Someone with registry steward access modifies an agreement's text directly without going through the amendment process. The registry's version history creates an immutable trail — every change is timestamped and linked to an authorizing record (creation, amendment, or review). A direct modification would appear as an unlinked change, detectable by any participant comparing the registry entry to the linked records.

**Selective visibility.** An agreement is hidden from certain participants' queries. The registry provides equal query access to all participants. The steward cannot create tiered access levels. If an agreement exists in the registry, any participant can find it with the right query.

**Registry neglect.** The steward stops maintaining the registry, allowing entries to become stale or inconsistent. The automatic review date tracking means stale entries generate their own escalation notices. Other skills that query the registry will surface inconsistencies (e.g., an agreement marked "active" that references a sunset parent agreement).

## I. Failure Containment Logic

- **Conflicting entries detected** (two agreements in the same domain with contradictory terms): the registry flags both entries and generates a notification to the affected parties. Resolution follows: the higher-level agreement prevails per the hierarchy. The lower-level agreement enters automatic review.
- **Write from unauthorized source**: the write is rejected and logged. The steward investigates the attempted unauthorized modification.
- **Registry becomes unavailable** (technical failure in whatever system hosts it): agreements remain in effect regardless of registry accessibility. The registry is a record, not the source of authority — agreements are authoritative documents that exist independently of the registry's operational status. The steward works to restore access.
- **Stale entry** (agreement marked "active" but review date passed): automatic flag visible to all querying participants. The flag triggers the agreement-review escalation process.

## J. Expiry / Review Condition

- The registry itself does not expire. Individual entries have their own review dates tracked by the registry.
- The registry steward role is reviewed annually by the body the registry serves.
- The registry schema (the set of fields tracked) can be amended through normal ACT process if additional fields are needed.

## K. Exit Compatibility Check

- When a participant exits, the registry updates their affected-party status across all relevant agreements. Agreements do not become invalid because a party exited — they are flagged for review if the exit changes the agreement's context significantly.
- The exiting participant's consent records are archived (not deleted) with an exit date.
- If the registry steward exits, a replacement is appointed by consent of the body the registry serves before the steward's departure takes effect (30-day wind-down).

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS agreements are maintained in each affected ETHOS's registry with linked entries. A change in one registry automatically triggers a synchronization notification to the other registries.
- When two ETHOS merge or split, their registry entries are migrated according to the reorganization agreement.
- **Federation:** when two NEOS ecosystems share governance space, each maintains its own registry. Cross-ecosystem agreements are entered in both registries with a federation link. Query access between ecosystems is defined by the inter-unit coordination protocol (Layer V, deferred). The registry schema includes a federation_link field (not active in this version) to support future cross-ecosystem queries.

## OmniOne Walkthrough

Kira, a newly onboarded AE member assigned to the Economics circle, wants to understand all the agreements that apply to her work. She queries the OmniOne agreement registry.

**Query 1:** "All active agreements affecting the Economics circle."

The registry returns 4 results:
1. **AGR-OMNI-001** (UAF, v2.1.0, universal) — the root agreement all participants operate under
2. **AGR-AE-2025-012** (ETHOS Agreement Field, v1.1.0, organizational) — the AE's operating agreement including stewardship and contribution commitments
3. **AGR-AE-2025-018** (Resource Stewardship Agreement, v1.0.0, stewardship) — specific commitments about how circle resources are managed
4. **AGR-ECON-2026-001** (Cross-Circle Collaboration Agreement, v1.0.0, access) — defining how the Economics circle coordinates with the Infrastructure circle on shared budget decisions

Kira reads the summaries and opens the full text of the resource stewardship agreement. She notices the agreement's review date was two weeks ago and it has not been reviewed — the registry displays a visible flag: "REVIEW OVERDUE — last review date: 2026-02-15."

Kira follows up with the Economics circle steward, who convenes the overdue review using the agreement-review skill. The review body determines the agreement is still appropriate (renew as-is) and sets the next review date for August 2026.

**Query 2:** Kira runs a compound query: "all sunset agreements in the Economics domain in the past 6 months." The registry returns 1 result: a pilot project agreement that was tested for 90 days and reverted. The sunset record includes the test report explaining why the pilot did not meet its success criteria.

Edge case: While reviewing results, Kira notices that the cross-circle collaboration agreement (AGR-ECON-2026-001) references a budget formula defined in AGR-AE-2025-018. But AGR-AE-2025-018 was amended last month (v1.0.0 → v1.1.0), and the amendment changed the budget formula. The cross-reference is now stale — AGR-ECON-2026-001 references v1.0.0 of a formula that no longer exists. Kira flags this to the registry steward, who generates a consistency notification to both agreements' affected parties. The cross-circle agreement enters review to update its reference.

## Stress-Test Results

### 1. Capital Influx

A major donor queries the registry to identify all agreements they can influence through funding conditions. The query returns accurate results — the registry does not distinguish between donor-motivated queries and any other query. However, the registry's transparency works both ways: other participants can query the same information and monitor whether donor-affiliated proposals target specific agreements. The registry steward cannot create a private view for the donor. If the donor attempts to modify agreements directly through the steward (bypassing ACT process), the write validation rejects the attempt and logs it.

### 2. Emergency Crisis

During an emergency, multiple temporary agreements are created under compressed timelines. The registry handles emergency entries with an "emergency" tag and the 30-day auto-expiry noted in the entry. The registry sends automatic reminders as expiry approaches. When the emergency passes, the registry facilitates systematic review: a query for "all emergency-tagged active agreements" returns the list for post-emergency evaluation. The registry's structure prevents emergency agreements from silently becoming permanent — the auto-expiry and review flags ensure they are addressed.

### 3. Leadership Charisma Capture

A respected leader who also serves as registry steward subtly modifies agreement text to expand their authority — changing "the circle decides" to "the circle lead decides" in a stewardship agreement. The version history detects this: the modification has no linked amendment record. Any participant comparing the registry entry's current text to the last amendment record can identify the unauthorized change. The discrepancy triggers a formal investigation. The registry's structural integrity depends on the link between every change and its authorizing process — unlinked changes are by definition unauthorized.

### 4. High Conflict / Polarization

Two factions query the registry to support their opposing positions. Faction A claims an agreement supports their view; Faction B claims the same agreement says the opposite. The registry provides the canonical text — the actual agreement as ratified. Both factions' interpretations are evaluated against the registry's version. If the agreement is genuinely ambiguous, the registry's conflict-flagging mechanism surfaces the ambiguity, triggering a review. The registry does not adjudicate — it provides the authoritative text from which adjudication proceeds.

### 5. Large-Scale Replication

At 5,000 members with 500+ active agreements, the registry handles volume through structured metadata and domain-based taxonomy. Queries return relevant results through domain matching, not full-text search through every agreement. The registry steward role may expand to a registry stewardship circle with multiple members maintaining different domain segments. The schema remains the same; what scales is the stewardship capacity. Automated consistency checks run periodically to detect stale cross-references and overdue reviews across the full registry.

### 6. External Legal Pressure

A government demands access to the full registry as part of a regulatory audit. The registry is a record of governance agreements — it does not contain personal data beyond participant names on consent records. The ecosystem's legal advisors evaluate what can be disclosed under the relevant jurisdiction's laws. The registry's transparency principle means its contents are not secret from internal participants, but external disclosure follows the UAF's legal compliance provisions. The registry steward cooperates with legal counsel but cannot unilaterally grant external access without ecosystem-level consent.

### 7. Sudden Exit of 30% of Participants

The mass departure triggers registry-wide impact assessment. The steward runs a query: "all active agreements where departed members constitute more than 25% of affected parties." The results are flagged for immediate review. Agreements where all affected parties have departed are automatically status-changed to "under_review." The registry generates a summary report for the OSC showing the scope of agreement disruption. The steward coordinates with the agreement-review process to prioritize the most impacted agreements. The registry's version history preserves all records — departed participants' consent records are archived, not deleted, maintaining the full governance trail.
