---
name: agreement-creation
description: "Create a new binding agreement -- space agreement, access agreement, agreement field, or UAF -- through a structured, consent-based process that prevents unilateral imposition and ensures traceability."
layer: 1
version: 0.1.0
depends_on: [domain-mapping]
---

# agreement-creation

## C. Trigger Conditions

- A participant identifies a need for a new binding commitment that does not yet exist in the agreement registry
- A new space, circle, or ETHOS is formed and needs founding agreements
- An ecosystem is established and needs its initial UAF (one-time event, uses this skill)
- A cross-ETHOS interaction requires a new agreement to govern shared resources or access
- An emergency requires temporary agreements under compressed timelines

## D. Required Inputs

- **Proposer identity**: who is proposing, their role, and their authority scope
- **Agreement type**: space, access, organizational, or UAF (determines routing and consent threshold)
- **Affected parties**: all participants who will be bound by or impacted by the agreement
- **Domain scope**: the boundary within which the agreement operates
- **Proposed text**: the draft agreement content, using the agreement-template.yaml structure
- **Proposed review date**: when the agreement will be reviewed (defaults apply per Section J)
- **Rationale**: why this agreement is needed, what problem it solves

## E. Step-by-Step Process

1. **Identify need.** The proposer determines that a binding commitment is needed and that no existing agreement in the registry covers the need.
2. **Draft agreement.** The proposer writes the agreement text using `assets/agreement-template.yaml`, filling in all required fields including type, affected parties, domain, proposed review date, and the agreement text itself.
3. **Synergy check.** The proposer queries the agreement registry for existing agreements in the same domain. If a related agreement exists, the proposer must document the relationship (complements, supersedes, or conflicts) and resolve any conflicts before proceeding.
4. **Route to ACT level.** Based on agreement type and scope:
   - *Space or access agreement* (single circle): circle-level ACT with affected parties consenting
   - *Organizational agreement field* (ETHOS-wide): full ACT cycle with all circle members in the ETHOS
   - *Ecosystem-level agreement*: OSC-level ACT with consensus mode
   - *UAF*: OSC consensus — used only at ecosystem founding; amendments use agreement-amendment
5. **Enter Advice phase.** Per the act-advice-phase skill: the proposal is announced to all affected parties, an advice window opens, and input is gathered and documented.
6. **Enter Consent phase.** Per the act-consent-phase skill: the proposal (modified by advice) is presented, positions are recorded, objections are integrated through structured rounds.
7. **Enter Test phase (if applicable).** New structural agreements (new circle formation, new resource allocation frameworks) enter a time-limited test per act-test-phase. Renewals of existing patterns or simple space agreements may skip testing by consent of the deciding body.
8. **Ratification.** All participants' consent positions are recorded in the ratification record. The agreement text is finalized with the version number and ratification date.
9. **Registration.** The completed agreement is entered into the agreement registry with a unique ID, full metadata, and status set to "active."

## F. Output Artifact

A versioned agreement document following `assets/agreement-template.yaml`, containing: unique agreement ID, type, title, full text, version number, status, proposer, affected parties list, domain, created date, ratification date and record, review date, and position in the agreement hierarchy. The ratification record lists every participant's position (consent, stand-aside, or objection) with timestamps.

## G. Authority Boundary Check

- **No individual** can unilaterally create a binding agreement outside their domain, regardless of role or seniority
- **Circle-internal agreements** require consent of all active members of the circle
- **Cross-circle agreements** require consent from representatives of each affected circle
- **Ecosystem-level agreements** require OSC consensus
- **UAF creation** requires consensus of all founding members (one-time event)
- The **proposer's authority scope** must be stated in the draft — a TH member proposes within TH scope; proposing changes to AE processes requires cross-circle routing
- **Facilitators** have process authority only (managing the ACT phases) and cannot approve or reject agreements on content grounds
- Authority scopes are formally defined by the domain-mapping and role-assignment skills in Layer II (Authority & Role).

## H. Capture Resistance Check

**Capital capture.** A wealthy donor conditions funding on favorable agreement terms. The skill prevents this because: the agreement enters the full ACT process regardless of funding conditions, affected parties evaluate terms on their merits, and the capture risk is flagged explicitly in the proposal documentation. Funding conditions that would distort agreement terms are documented as a capture vector during the advice phase.

**Charismatic capture.** A popular leader pushes an agreement through by framing objections as obstruction. The consent phase structurally protects objectors: every objection must be formally recorded, integration rounds require substantive engagement, and the facilitator cannot declare consent until all objections are addressed or the maximum rounds are exhausted.

**Emergency capture.** A crisis is used to rush agreements through without proper process. Emergency timelines (24-hour advice, compressed consent) still require a formal consent round with a minimum 50% quorum. Emergency agreements auto-expire in 30 days and are flagged for post-emergency review.

**Informal capture.** "Everyone knows we agreed to this" is not an agreement. No binding commitment exists until it passes through this skill and is registered. Unregistered agreements have no standing in the governance system.

## I. Failure Containment Logic

- **Consent fails** (objections cannot be integrated after maximum rounds): the proposal escalates to the next GAIA level per proposal-resolution. The agreement does not come into existence.
- **Quorum not met**: the consent timeline extends by 7 days. The quorum threshold is never lowered. If quorum is still not met, the proposal is flagged for review — it may indicate the agreement's scope is incorrectly defined.
- **Agreement text is ambiguous**: any participant can request a mandatory clarification round before ratification. Ambiguous terms must be resolved in writing, not left to interpretation.
- **Synergy check reveals conflict**: the proposer must resolve the conflict with the existing agreement's steward before proceeding. Options: amend the existing agreement, narrow the new agreement's scope, or document why both agreements can coexist.
- **Partial ratification** (some affected circles consent, others do not in a cross-circle agreement): the agreement cannot take effect. It returns to advice phase with the objecting circles' concerns documented.

## J. Expiry / Review Condition

Default review intervals by agreement type (configurable during creation, with mandatory minimums):
- **Space agreements**: annual review (minimum: 6 months)
- **Access agreements**: 6-month review (minimum: 3 months)
- **Organizational agreement fields**: 2-year review (minimum: 1 year)
- **UAF**: annual review by OSC, never auto-expires
- **Culture codes**: at circle's discretion (minimum: annual)

Missed review triggers an automatic sunset warning sent to all affected parties — the agreement is not auto-invalidated but enters a 60-day grace period during which the agreement-review skill must be invoked. If still not reviewed after 60 days, the agreement's status changes to "under review" in the registry with a prominent flag.

## K. Exit Compatibility Check

When a participant exits the ecosystem, their obligations under agreements created through this skill cease, with these exceptions:
- **Stewarded asset return**: any assets held in stewardship must be returned or transferred within the 30-day wind-down period
- **In-progress commitments**: obligations actively underway get a 30-day wind-down for handoff
- **Exit-specific clauses**: if the agreement itself contains exit provisions, those are honored
- **Original works**: the exiting participant retains full rights to works they created individually

Agreements the departing participant proposed remain valid — authorship does not create ongoing obligation. If the departing participant was the sole steward, the agreement-review skill is triggered to assign a new steward.

## L. Cross-Unit Interoperability Impact

- Agreements created in one ETHOS that affect participants or resources in another ETHOS trigger **cross-unit notification** — the affected ETHOS must be informed before the consent phase begins
- The affected ETHOS must consent through their own ACT process before the agreement can bind their members
- Cross-ETHOS agreements are registered in both ETHOS' registries with linked entries
