---
name: role-sunset
description: "Dissolve a governance domain that has served its purpose -- inventorying all responsibilities and agreements, executing a disposition plan, archiving the domain contract, and providing a 90-day reactivation window so that defunct roles do not linger as zombie authority."
layer: 2
version: 0.1.0
depends_on: [domain-mapping, domain-review, role-transfer]
---

# role-sunset

## A. Structural Problem It Solves

Without a sunset process, defunct roles linger as zombies — technically existing but serving no purpose, sometimes reanimated by opportunistic actors to claim authority they no longer hold legitimately. A domain whose purpose is fulfilled but never formally dissolved becomes a persistent source of confusion: responsibilities double-assigned, agreements with no clear steward, and the implicit assumption that whoever last held the role still carries authority. This skill ensures that when a domain has served its purpose, it is formally dissolved with all responsibilities accounted for — no orphaned authority, no ambiguous successors, no structural ghost. Every element of the domain contract is explicitly resolved before the domain disappears from the active registry.

## B. Domain Scope

This skill applies to any active domain that meets a sunset trigger condition: a domain whose purpose has been achieved, whose responsibilities have been absorbed by other domains, that has been vacant for more than two consecutive review cycles, or that the delegating body proposes for dissolution. This skill does not apply to domain refinement (use domain-mapping), to role handoff between stewards (use role-transfer), or to domain evaluation that may result in a non-sunset outcome (use domain-review). The sunset process is terminal — after completion, the domain no longer exists as an active authority scope and cannot be exercised. The 90-day grace period (Section I) is the only post-sunset structural mechanism; after that window closes, reactivating an archived domain requires a full domain-mapping process.

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

## OmniOne Walkthrough

**Context.** The Trunk Council was OmniOne's temporary key-holding body during its formation phase — a domain created to hold centralized authority that would be distributed to permanent governance circles as the ecosystem matured. At its formation, the Trunk Council's domain contract stated its purpose explicitly: "Hold foundational ecosystem authority during the transition period until permanent governance councils are operational and have demonstrated stability." The domain's evaluation schedule specified a review at the 12-month mark or when all four permanent councils (TH, AE, OSC, GEV) had completed their first full governance cycle, whichever came first.

**Trigger.** Domain-review for the Trunk Council concludes in March 2026. The review body — the OSC, as the Trunk Council's delegating body — evaluates all 11 domain elements. Their finding: all four permanent councils are operational, have completed multiple governance cycles, and have demonstrated stability. The Trunk Council's purpose is achieved. The domain-review recommends sunset and produces a domain-review record (DRV-TC-2026-001) documenting this outcome. The sunset trigger is `review_recommendation`.

**Step 1 — Inventory.** The OSC assembles the complete inventory. The Trunk Council's domain contract lists four key responsibilities: (1) maintaining ecosystem signing authority for external agreements, (2) holding stewardship over the OmniOne Master Plan until OSC assumes this role, (3) approving budget allocations above $10,000, (4) serving as final escalation point for unresolved GAIA conflicts. Agreement registry query reveals two active agreements naming the Trunk Council as steward: AGR-TC-2025-001 (Bali land stewardship agreement) and AGR-TC-2025-003 (GEV 501c3 fiscal sponsorship agreement). Dependent domains: the Economics circle lists the Trunk Council as its escalation path for budget disputes. One pending commitment is identified: the Trunk Council was facilitating completion of the Economic Framework document, still 60% complete.

**Step 2 — Disposition plan.** The OSC drafts disposition for each item:
- Responsibility 1 (signing authority) → transferred to OSC
- Responsibility 2 (Master Plan stewardship) → transferred to OSC
- Responsibility 3 (budget approval) → transferred to Economics circle steward with OSC as appeal path
- Responsibility 4 (GAIA escalation) → absorbed by OSC (already their function at ecosystem level)
- AGR-TC-2025-001 (land stewardship) → transferred to OSC via agreement amendment
- AGR-TC-2025-003 (fiscal sponsorship) → transferred to GEV circle (GEV is the 501c3 holder)
- Economics circle dependency → redirected to OSC
- Pending commitment (Economic Framework) → transferred to Economics circle steward with a completion deadline of June 2026

**Step 3 — Notification.** OSC notifies: the Economics circle steward, GEV steward, the two agreement counterparties (Bali land council, fiscal sponsor foundation), and the former Trunk Council members. Fourteen-day notice period opens March 5, 2026.

**Step 4 — OSC consensus.** The Trunk Council was an ecosystem-level domain, so OSC consensus (all must agree) is required for dissolution. OSC convenes March 21, 2026. The former Trunk Council steward, Dara, participates in the discussion and affirms that the purpose is genuinely achieved. All OSC members reach consensus. Consent record: CST-OSC-2026-011.

**Step 5 — Execution.** Responsibilities and agreements are transferred per the plan. GEV updates the fiscal sponsorship agreement to name GEV as steward (agreement amendment AGR-TC-2025-003-A). Bali land stewardship agreement amended to name OSC. Economics circle domain contract updated to redirect their escalation dependency to OSC (domain amendment DMA-ECON-2026-002). Trunk Council domain contract archived with sunset date March 22, 2026 and rationale: "Purpose achieved — authority distributed to permanent governance structure." Dara's role assignment record is closed: RSN-TC-2026-001.

**Grace period edge case.** On May 20, 2026 — 59 days after sunset, within the 90-day window — the AE discovers that the Trunk Council held informal responsibility for emergency key rotation (changing access credentials if a steward's account was compromised). This responsibility appeared nowhere in the domain contract (an omission from the original domain-mapping) and was therefore not in the inventory. The 90-day grace period activates. The OSC convenes and assigns emergency key rotation responsibility to OSC through an expedited amendment to the OSC domain contract (DMA-OSC-2026-007). The sunset record is updated to document the late discovery. The Trunk Council is not reactivated — the responsibility is resolved through the receiving domain, not by resurrecting the dissolved one.

**Output artifact.** Sunset record SSR-TC-2026-001 is filed in the domain registry, containing the archived Trunk Council domain contract, complete disposition plan with all items marked resolved, consent record reference CST-OSC-2026-011, reactivation window end June 20, 2026, and `reactivation_used: true` (updated after the May 20 edge case).

## Stress-Test Results

### 1. Capital Influx

A major donor funding 40% of OmniOne's operating budget has a legal arrangement tied to the existence of a specific domain — the "Donor Relations Council" — that they helped create two years ago. When domain-review recommends sunsetting the Donor Relations Council (its responsibilities have been absorbed by the AE), the donor signals that dissolution would jeopardize the funding relationship. The sunset process proceeds regardless: the delegating body evaluates the disposition plan on structural merits, and the donor's funding condition is documented in the consent record as a capital capture attempt, not as a valid rationale for preserving a structurally redundant domain. The consent process requires demonstrated need for the domain's continued existence, not a funding agreement. The donor's leverage cannot create a governance rationale where none exists. The disposition plan identifies the AE as the recipient for all Donor Relations Council responsibilities; if the donor objects to working with the AE instead of a dedicated council, that is a relationship matter, not a governance matter. The sunset proceeds. If the donor withdraws funding as a result, that consequence is absorbed by the ecosystem — the alternative is allowing external capital to permanently preserve domains that have served their purpose.

### 2. Emergency Crisis

A severe infrastructure failure at OmniOne's primary digital platform triggers an ecosystem emergency while the AE Tech Operations domain is mid-sunset (step 3, notification period open). Three OSC members invoke provisional emergency rules to halt the sunset process and redirect the Tech Operations steward's attention to crisis response. The suspension is legitimate — emergency conditions may postpone sunset, but they do not dissolve the process. The sunset clock pauses at step 3; all notifications sent to date remain valid. The steward continues operating the domain under its existing authority for the duration of the emergency. When the emergency resolves (17 days later), the OSC formally restores the sunset process from where it paused, extending the notification period by 17 days to account for the interruption. The emergency did not create new responsibilities for the domain — it temporarily prevented disposition. Post-emergency, the domain-review record is updated to note the suspension and resumption. Sunset proceeds to completion.

### 3. Leadership Charisma Capture

Noa, a founding member of OmniOne with high social standing, stewarded the "Vision Keeper" domain — a role created to hold the founding ecosystem narrative and introduce new members to OmniOne's purpose. After three years, domain-review finds that Vision Keeper responsibilities have been distributed to the TH (member orientation) and OSC (ecosystem narrative stewardship). The review recommends sunset. Noa publicly expresses that the domain is central to OmniOne's identity and that dissolving it would signal a loss of soul. Several newer members, deeply influenced by Noa's facilitation, echo this sentiment informally. The sunset process does not treat charismatic reputation as a structural rationale: the disposition plan requires a concrete, unfilled need — not sentiment about a person's importance. During the consent step, Noa participates in the discussion and presents their view. Two OSC members express discomfort but cannot articulate a specific responsibility that is unaddressed. The facilitator distinguishes between emotional attachment to a role and structural necessity: if every responsibility is accounted for in the disposition plan, the domain has served its purpose. Consent is reached. The sunset record notes Noa's contribution explicitly — dissolution of the domain is not a statement about the person, and the ecosystem formally acknowledges the founding work in the consent record rationale.

### 4. High Conflict / Polarization

The "Resource Allocation Board" domain is proposed for sunset after its responsibilities are transferred to the Economics circle. Two factions form: one faction (led by AE members) supports sunset, arguing the Board was always a temporary workaround; the opposing faction (led by several Co-creators) argues the Board's independence from the AE was the point — folding its responsibilities into the AE creates a conflict of interest. The disposition plan itself is contested: the anti-sunset faction argues that transferred responsibilities to the AE cannot be neutral because the AE has a stake in resource decisions. The conflict routes to GAIA Level 4 (Coaching). A coach maps the tension: the pro-sunset faction's concern is structural redundancy; the anti-sunset faction's concern is concentration of authority. The coach proposes a third solution: the Economics circle is reconstituted as an independent domain with a mandate that explicitly prohibits AE members from voting on resource decisions above a threshold — preserving the independence principle without preserving the redundant domain. The third solution satisfies both factions' core concerns. The Resource Allocation Board is sunset; the Economics circle domain contract is amended to include the independence constraint. Both changes proceed through their respective processes.

### 5. Large-Scale Replication

OmniOne scales to 200+ active domains across 15 ETHOS. At this scale, multiple domains reach sunset conditions simultaneously — in one quarter, 12 domains are flagged for sunset through scheduled domain-reviews. The sunset process is not bottlenecked by this volume because each sunset is domain-scoped: the delegating body for each domain runs its own process independently. The challenge is coordination when a single domain has dependencies across multiple other domains being simultaneously sunset. The role-sunset skill addresses this through the inventory step: before any concurrent sunsets proceed to consent, the delegating bodies cross-reference their inventories to identify interdependencies. If Domain A is being sunset and Domain B (also being sunset) was named as a transfer destination for Domain A's responsibilities, the sequencing must be resolved — Domain A's disposition plan must redirect to a domain that will remain active. A registry-level flag is introduced at this scale: any domain in "sunset pending" status appears with a flag in the domain registry so that other concurrent sunset processes can detect and avoid naming it as a transfer destination. The 90-day grace period serves as a final catch for interdependency gaps that sequencing planning misses.

### 6. External Legal Pressure

A regulatory body in Indonesia notifies OmniOne that the domain governing SHUR Bali's space stewardship must be formally maintained with a named legal representative for compliance purposes — they will not recognize a domain transition. This external pressure cannot prevent the domain's sunset if the sunset conditions are met; it creates a legal obligation on individuals (the steward) independent of the governance domain. The distinction is structural: NEOS governance is a participant-consent system, not a legal jurisdiction. The OSC and the relevant legal advisors address the compliance requirement by ensuring that a named individual is registered with the regulatory body as the legal contact for SHUR Bali, independent of which governance domain holds stewardship authority. The SHUR Bali stewardship domain is sunset as planned; the legal contact registration is updated to reflect the new steward of the successor domain. The regulatory body's requirement applies to the physical jurisdiction — it shapes how individuals interact with external law, not how the ecosystem's governance domains are structured internally.

### 7. Sudden Exit of 30% of Participants

Following a contested OSC decision, 30% of OmniOne's Co-creators exit within three weeks. Among the departing members are stewards of four active domains. Three of those domains enter vacant status immediately; one domain's steward completes a role-transfer to a remaining member before departing. The three vacant domains are evaluated against the sunset trigger: two have been vacant for less than one review cycle and are placed in "steward search" status by the delegating body; the third was already approaching vacancy-timeout and the mass departure pushes it past the two-cycle threshold, triggering sunset automatically. The sudden-exit sunset proceeds through the standard process with the delegating body performing inventory without steward cooperation — they use the domain contract and agreement registry as their primary sources. Responsibilities are distributed across remaining active domains. The 90-day grace period is especially important in this scenario: the rush to process multiple sunsets simultaneously increases the likelihood of inventory gaps. The OSC assigns two dedicated reviewers to monitor all three vacant-domain situations and track any orphaned responsibilities discovered during the grace period.
