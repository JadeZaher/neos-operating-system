---
name: agreement-registry
description: "Maintain and query the single source of truth for all active agreements -- handling writes from agreement-creation, amendment, and review, and providing open query access to any participant."
layer: 1
version: 0.1.0
depends_on: [agreement-creation, agreement-amendment, domain-mapping]
---

# agreement-registry

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
