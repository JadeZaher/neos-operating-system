---
name: role-sunset
description: "Dissolve a governance domain that has served its purpose -- inventorying all responsibilities and agreements, executing a disposition plan, archiving the domain contract, and providing a 90-day reactivation window so that defunct roles do not linger as zombie authority."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, domain-review, role-transfer]
---

# role-sunset

## C. Trigger Conditions

- **Domain-review recommends sunset**: the review body determines the domain no longer serves a necessary function or all responsibilities are better held elsewhere
- **Purpose achieved**: the domain was created for a specific, time-bounded purpose and that purpose is now demonstrably complete
- **Responsibilities transferred**: all key responsibilities from the domain contract have been formally moved to other active domains through documented agreements
- **Vacancy timeout**: the domain has been without an assigned steward for more than two consecutive review cycles (default: 12 months) with no candidate emerging
- **Delegating body proposes dissolution**: the body that created the domain initiates sunset independent of a scheduled domain-review

Emergency conditions do not bypass the sunset process — they may postpone it but a domain cannot be sunset under emergency compression because dissolution requires full accountability of all responsibilities and agreements.

## D. Required Inputs

- **Domain contract** (mandatory): the most recent version from the domain-mapping skill, all 11 elements
- **Active agreements list** (mandatory): all agreements held by this domain or referencing this domain as a party, from the agreement registry — who provides: the delegating body queries the registry
- **Dependent domains list** (mandatory): all other domains that list this domain as a dependency in their domain contracts — who provides: the delegating body or a designated reviewer
- **Current steward** (if assigned): identity and any pending commitments they hold in this role
- **Proposed disposition plan** (mandatory): for each responsibility, agreement, and dependent domain — the proposed outcome (transferred, ended, archived, redirected) and the destination domain or rationale
- **Domain-review record** (if sunset follows a review): the review outcome record from domain-review skill; if no recent review exists, the delegating body documents the sunset rationale directly

## E. Step-by-Step Process

1. **Inventory all pending items.** The delegating body (or steward, if initiating) assembles the complete inventory: all pending commitments still in progress, all active agreements held by the domain or naming it as steward, and all domains that list this domain as a dependency. No step proceeds until the inventory is complete and verified against the agreement registry.

2. **Draft disposition plan.** For each item in the inventory, the delegating body proposes a disposition:
   - *Responsibilities*: transferred to a named destination domain, formally ended (no successor needed), or absorbed by the delegating body itself
   - *Agreements*: transferred to a successor domain (requires agreement-review or amendment per Layer I skills), sunset through the agreement-review skill, or archived if the obligation is fully discharged
   - *Dependent domains*: dependency removed (they update their domain contract to remove this dependency) or redirected (dependency transfers to a named replacement domain)

3. **Notify all affected parties.** The delegating body notifies every party named in the disposition plan — stewards of destination domains, parties to transferred agreements, dependent domain stewards — with a minimum 14-day notice period before the consent step. Notification documents the proposed disposition for each affected item and invites substantive response (not consent, but the opportunity to surface objections before formal process).

4. **Delegating body runs consent process.** The delegating body runs an ACT consent round for the dissolution and its full disposition plan. For domains at the ecosystem level (held by OSC or analogous body), OSC consensus is required. For ETHOS-level domains, circle-level consent among the delegating body is sufficient. The steward may participate in the discussion but is not a member of the deciding body for this step — they have a right to be heard, not a right to block.

5. **Execute disposition.** Upon consent:
   - Transfer each responsibility and agreement per the approved plan; recipient domains confirm receipt
   - Notify dependent domains to update their domain contracts (removing or redirecting the dependency through domain-mapping amendment)
   - Archive the domain contract with the sunset date, sunset trigger, and rationale appended
   - Update the former steward's assignment record (role assignment closed, sunset date recorded)
   - Mark the domain as "archived" in the domain registry — not deleted, but no longer active or exercisable

6. **Open 90-day grace period.** From the sunset date, a 90-day reactivation window opens. If any orphaned responsibility is discovered — a commitment that was missed in the inventory or an agreement that was not properly transferred — the discovery triggers reactivation of the domain through an expedited amendment process (no full domain-mapping required) rather than leaving the responsibility unattributed. After 90 days, the archived domain contract is locked and reactivation requires a full domain-mapping process.

Default timeline: steps 1-3 completed within 30 days of trigger; consent (step 4) within 14 days of notification period; execution (step 5) within 7 days of consent.

## F. Output Artifact

A sunset record following `assets/sunset-record-template.yaml`, containing: unique sunset ID, the archived domain contract (full 11-element version at time of sunset), the sunset trigger and rationale, the complete disposition plan with each responsibility and agreement accounted for, the consent record ID, the reactivation window end date, and a flag indicating whether the reactivation mechanism was used. The sunset record is stored in the domain registry alongside the archived domain contract. Both remain permanently accessible for historical reference — dissolution is not erasure.

## G. Authority Boundary Check

- **Only the delegating body** can execute a domain sunset. The body that created the domain is the body that dissolves it — authority is symmetric.
- **The steward can propose sunset** but cannot execute it unilaterally. A steward who believes their domain should be dissolved initiates the process with the delegating body; the delegating body decides.
- **The steward cannot be forced to continue** operating a domain they believe should sunset. If the delegating body refuses to sunset and the steward no longer wants the role, they step down through role-transfer, leaving the domain vacant. The vacancy rule (2 consecutive review cycles without steward) provides a structural path to sunset regardless of delegating body preference.
- **Recipient domains must consent** to receiving transferred responsibilities or agreements — no domain can be assigned new obligations without its steward's acceptance.
- **No individual** can archive or dissolve a domain outside this process. Informal sunset — simply stopping work and assuming the domain has dissolved — is not a valid governance action.

## H. Capture Resistance Check

**Premature sunset (political removal).** A faction within the delegating body uses the sunset process to eliminate a domain whose steward holds opposing views. The consent process requires demonstrated rationale — not political convenience. The steward has the right to present a rebuttal during the consent discussion. If the domain still has unresolved responsibilities, the disposition plan will be incomplete, blocking the sunset (step 1 gate). GAIA escalation is available if the steward contests the sunset as politically motivated.

**Sunset resistance (personal authority preservation).** A steward resists sunset of their domain because dissolving it eliminates their governance position. The vacancy rule provides a structural path: the delegating body does not require the steward's cooperation to sunset a domain — they can allow the role to remain vacant through two review cycles and then execute sunset on vacancy-timeout grounds. The steward's refusal to cooperate delays but cannot permanently block the process.

**Zombie resurrection.** After sunset, someone attempts to reactivate the domain informally to claim the authority it once held — "I used to steward this domain, so I still have authority here." The 90-day reactivation window is explicit and closed after that point. Any authority claim based on an archived domain has no standing. After 90 days, reactivating the domain requires a full domain-mapping process with delegating body consent — there is no informal resurrection path.

**Capital capture.** An external funder conditions continued funding on preserving a domain (or dissolving a competing domain). The consent process evaluates the disposition plan on its structural merits. Funding conditions do not constitute a rationale for blocking or accelerating sunset. The capture risk is explicitly documented in the consent record if raised during the process.

## I. Failure Containment Logic

**Orphaned responsibilities discovered post-sunset (within 90 days).** The 90-day grace period activates. The delegating body convenes to assign the orphaned responsibility through an expedited amendment: the responsibility is transferred to an existing active domain, the sunset record is updated to note the late discovery and resolution, and no full domain-mapping process is required. The reactivation mechanism does not resurrect the domain — it resolves the gap and closes it again.

**Contested sunset.** The steward or a dependent domain formally objects that the disposition plan is incomplete, the rationale is insufficient, or the process was flawed. The objection routes to GAIA escalation: Level 3 (Dialogue) for process disputes, Level 4 (Coaching) if structural conflict between parties cannot be resolved through dialogue. Sunset is blocked until the objection is resolved or the GAIA process produces an outcome.

**Incomplete disposition plan.** A responsibility or agreement in the inventory has no proposed disposition. Sunset is blocked at step 2 — the delegating body cannot proceed to the consent step with an unresolved inventory item. The block is not circumventable by consent; every item must have an explicit disposition before the process advances.

**Recipient domain refuses transfer.** A domain named as the transfer destination for a responsibility or agreement declines to accept it. The delegating body must find an alternative disposition (different destination domain, absorption by the delegating body, or formally ending the responsibility if appropriate) before the consent step.

**No response from dependent domains.** A dependent domain does not respond to the 14-day notification. After the notification period, the process proceeds; the dependent domain's failure to respond is documented. Their domain contract remains their responsibility to update — the sunset proceeds and their unupdated dependency creates a gap they must address through domain-mapping amendment.

## J. Expiry / Review Condition

Sunset itself is a terminal state — there is no review interval for a sunset record because there is nothing to review. The archived domain contract is a historical record, not an active governance document. The 90-day grace period is the only temporal element: after it closes, the domain is locked and cannot be reactivated without a full domain-mapping process. Sunset records and archived domain contracts are permanently retained in the registry for audit purposes and are never auto-deleted.

## K. Exit Compatibility Check

If the steward of a domain being sunset exits the ecosystem during the sunset process, the delegating body takes over disposition planning in full. The exiting steward's cooperation is preferred but not required — the delegating body has the domain contract, the agreement registry, and the authority to execute disposition without steward participation. The steward's exit does not accelerate or block the sunset timeline. Any pending commitments the steward held in the role are treated as orphaned responsibilities and resolved through the disposition plan (or, if discovered post-sunset, through the 90-day grace period mechanism). The exiting steward retains rights to their original works — dissolution of the domain does not transfer those rights.

## L. Cross-Unit Interoperability Impact

Cross-ETHOS domain sunset requires notification to all ETHOS that contain domains with a dependency on the domain being sunset. This notification occurs in step 3 alongside notification to individual dependent domain stewards. Disposition may redirect dependencies to domains in other ETHOS — those redirections are registered in both ETHOS' domain registries. If the sunset domain held agreements that span multiple ETHOS, those agreements route through the agreement-review skill in each affected ETHOS before transfer or sunset. The extensibility point for cross-ecosystem federation (Layer V, deferred) applies here: if a domain holds obligations to participants in a federated ecosystem, the inter-ecosystem coordination protocol governs those transfers when Layer V is available.
