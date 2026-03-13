---
name: agreement-creation
description: "Create a new binding agreement -- space agreement, access agreement, agreement field, or UAF -- through a structured, consent-based process that prevents unilateral imposition and ensures traceability."
layer: 1
version: 0.1.0
depends_on: [domain-mapping]
---

# agreement-creation

## A. Structural Problem It Solves

Without a formal creation process, agreements emerge informally and unevenly — whoever has social capital or persistence sets the terms, and others discover their obligations after the fact. This skill ensures every agreement has a traceable origin, a defined scope, and a legitimate ratification process. It prevents hidden agreements, unilateral imposition, and the "we all assumed we agreed" failure mode that corrodes trust in governance systems. Every binding commitment in the ecosystem passes through this process or it does not exist.

## B. Domain Scope

This skill applies to any domain where binding commitments between participants are needed. Agreement types follow the hierarchy (no lower-level agreement may contradict a higher-level one):

1. **Universal Agreement Field (UAF)** — root agreement, all participants
2. **Ecosystem Agreement** — e.g., OmniOne Master Plan
3. **Access Agreement** — e.g., SHUR space agreements
4. **Stewardship Agreement** — role-specific commitments
5. **AZPO Agreement Field** — organizational unit agreements (called "ETHOS" in OmniOne)
6. **Culture Code** — circle-internal norms
7. **Personal Commitments** — individual-level agreements

The skill covers creation of agreements at every level. UAF creation is rare (typically only at ecosystem founding) — most UAF changes use the agreement-amendment skill.

## C. Trigger Conditions

- A participant identifies a need for a new binding commitment that does not yet exist in the agreement registry
- A new space, circle, or AZPO is formed and needs founding agreements
- An ecosystem is established and needs its initial UAF (one-time event, uses this skill)
- A cross-AZPO interaction requires a new agreement to govern shared resources or access
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
   - *Organizational agreement field* (AZPO-wide): full ACT cycle with all circle members in the AZPO
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

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

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

- Agreements created in one AZPO that affect participants or resources in another AZPO trigger **cross-unit notification** — the affected AZPO must be informed before the consent phase begins
- The affected AZPO must consent through their own ACT process before the agreement can bind their members
- Cross-AZPO agreements are registered in both AZPOs' registries with linked entries
- When two NEOS ecosystems share a physical or digital space, agreements governing that space use the inter-unit coordination protocol (Layer V, deferred). This skill notes the extensibility point: the routing logic in Step 4 can be extended to include cross-ecosystem routing when Layer V is available.

## OmniOne Walkthrough

Amara, a TH member living at the SHUR Bali co-living residency, has been dealing with recurring kitchen conflicts — unclear expectations about shared cooking times, cleanup responsibilities, and quiet hours. After the third conflict in a month, Amara decides a formal space agreement is needed.

Amara drafts a kitchen space agreement using the agreement-template, specifying: type=space, domain=SHUR Bali kitchen, affected parties=all 12 SHUR residents. She includes proposed quiet hours (10pm-7am), a cleanup-within-30-minutes rule, and a shared shelf allocation system. She sets a proposed review date of one year from ratification.

During the synergy check, Amara queries the agreement registry and finds no existing kitchen agreement. She does find a general SHUR common-space agreement (AGR-SHUR-2026-001) and reviews it for consistency — her kitchen agreement is more specific and complements, rather than contradicts, the common-space terms. She documents this relationship.

The agreement enters the Advice phase with a 7-day window. Eight of twelve residents provide input. Key advice: Resident Kaia wants quiet hours to start at 9pm, not 10pm, because she runs morning meditation sessions and needs early sleep. Resident Tomás, an AE member who does not live at SHUR but uses the kitchen for community cooking events twice a month, raises concerns about limiting event access. Amara documents each piece of advice and her response: she partially integrates Kaia's input by setting quiet hours at 9:30pm as a compromise, and she integrates Tomás's concern by exempting community events but requiring 48-hour advance notice and an 11pm hard stop.

The Consent phase convenes with 10 of 12 residents present (quorum met: 10/12 exceeds the 2/3 threshold). In Round 1: 8 consent, 1 stands aside (Jamal doesn't cook but has no objection), and 1 objects — Preethi objects that the community event exemption is too broad and could lead to nightly disruptions. In the integration round, Amara and Preethi find a third solution: events are limited to 2 per week and must end by 11pm. The modified proposal goes to Round 2: all 10 consent (Preethi's concern is addressed, Jamal still stands aside). Consent achieved.

The agreement is ratified with all positions recorded and registered as AGR-SHUR-2026-003. The output artifact includes: agreement ID, full text of kitchen rules, ratification record with all 10 participants' positions and timestamps, review date of March 2027, and the documented relationship to the parent common-space agreement.

Edge case: Tomás, the non-resident AE member, was consulted during the advice phase as an impacted party. He was not included in the consent round because the deciding body is SHUR residents (the parties bound by daily kitchen use). His input was integrated into the agreement, and he is listed as an advisory participant in the ratification record.

## Stress-Test Results

### 1. Capital Influx

A wealthy donor offers OmniOne $500,000 contingent on creating a space agreement that gives their affiliated permaculture project exclusive access to the SHUR workshop space for five years. The proposal enters the normal agreement-creation process — the donor's financial leverage does not grant them proposal-routing privileges. During the synergy check, the proposer discovers an existing access agreement that grants all AE members shared workshop access. The capture resistance check flags the exclusivity clause as a capital capture risk: a single donor is attempting to convert financial contribution into governance authority over a shared resource. During the advice phase, multiple SHUR residents and AE members point out that exclusive access contradicts the UAF's stewardship principles. The consent phase proceeds without the funding condition influencing the quorum threshold or process timeline. The affected parties evaluate the agreement on its structural merits. The donor's offer is documented in the advice log as context, not as a factor in the consent decision. The agreement, if consented to, would need to address the conflict with the existing access agreement through proper channels.

### 2. Emergency Crisis

A severe flood damages the SHUR Bali main building, displacing 8 residents who need immediate temporary housing arrangements with neighboring communities. Three AE members invoke the provisional emergency rules, declaring an emergency that requires a temporary shelter agreement within 24 hours. The agreement-creation process runs at emergency compression: the advice window is 24 hours (not 7 days), and the consent quorum cannot drop below 50% of affected parties. The proposer drafts a temporary access agreement granting displaced residents access to two partner community spaces. Despite the urgency, a formal consent round occurs — 6 of 8 displaced residents participate (75%, meeting the emergency 50% minimum). All consent. The agreement is registered with an automatic 30-day expiry and a flag for post-emergency review. When the flood waters recede, the agreement-review skill is triggered to either sunset the temporary arrangement or convert it into a longer-term access agreement through normal process.

### 3. Leadership Charisma Capture

A charismatic OmniOne leader, respected for founding one of the most successful AZPOs, proposes a new organizational agreement that would centralize resource allocation decisions under a single "Resource Council" they would chair. They frame objections from smaller circles as "not understanding the big picture" and privately pressure hesitant participants to withdraw their concerns. The agreement-creation process structurally resists this: during the consent phase, every objection is formally recorded before any discussion occurs — once recorded, an objection cannot be erased, only addressed through an integration round. The facilitator (who must be neutral and cannot be the proposer) explicitly states that objections are valued structural contributions. When two participants raise objections about centralization contradicting NEOS's distributed authority principle, the integration rounds require the proposer to substantively modify the proposal, not just reframe objections as misunderstandings. Social pressure to withdraw objections is itself flagged as a capture risk by the facilitator. After three integration rounds fail to resolve the core objection (centralized resource authority contradicts scoped authority), the proposal escalates to GAIA Level 4 coaching.

### 4. High Conflict / Polarization

Two factions within the OmniOne AE have deeply opposed views on a new stewardship agreement for intellectual property. Faction A wants all emergent works to be fully open-source with no restrictions. Faction B wants creators to retain commercial rights with a revenue-sharing model back to the ecosystem. Both factions draft competing agreements. During the synergy check, the conflict is identified and the two proposals are flagged as mutually exclusive. The process requires reconciliation before either can proceed to consent. At GAIA Level 4, a coach maps the tension: Faction A's core concern is preventing privatization of collective work; Faction B's core concern is incentivizing high-quality contributions. The coach facilitates a "Doing Both Solution" — emergent works are open-source by default with a creator opt-in commercial license that returns 30% of revenue to the ecosystem commons. This third solution addresses both factions' core concerns and enters the consent phase as a unified proposal. Both factions participate in consent, and the integration rounds fine-tune the revenue percentage.

### 5. Large-Scale Replication

OmniOne grows from 50 members in one location to 5,000 members across 15 SHUR locations and 80 circles. Agreement creation scales through domain-scoped routing: a kitchen agreement at SHUR Costa Rica involves only the 20 residents of that location, not all 5,000 members. The synergy check becomes more critical at scale — with hundreds of active agreements, the registry query prevents duplication and conflict. Cross-circle agreements are routed through domain matching rather than manual identification, using the registry's domain taxonomy. Ecosystem-level agreements (requiring OSC involvement) remain rare — most governance happens at the circle and AZPO level. The agreement-template.yaml structure remains the same at every scale; what changes is the routing logic and the size of the affected-parties list. Facilitator capacity scales through a train-the-trainer model within each circle, ensuring every SHUR location has multiple trained facilitators.

### 6. External Legal Pressure

The Indonesian government issues a regulation requiring all co-living spaces to register formal tenancy agreements that include government-mandated clauses about occupancy limits and reporting requirements. This external mandate does not automatically become a NEOS agreement — it enters the ecosystem as information, not as a binding commitment. A SHUR steward proposes a new access agreement that incorporates the required legal clauses alongside NEOS's own stewardship principles. The proposal goes through the full ACT process: during the advice phase, participants distinguish between legal compliance (non-negotiable for the physical jurisdiction) and governance principles (NEOS-internal). The consent phase proceeds normally. The resulting agreement satisfies the legal requirement for the Bali jurisdiction while preserving NEOS principles. Crucially, this agreement applies only to SHUR Bali — it does not modify the UAF or create a precedent that all SHUR locations must adopt the same terms. Members may individually comply with their local laws without those requirements becoming ecosystem-wide agreements.

### 7. Sudden Exit of 30% of Participants

Following a contentious decision about OmniOne's expansion strategy, 15 of 50 members exit within a two-week period. Existing agreements remain valid — they were legitimately created through the full ACT process and the departure of some parties does not retroactively invalidate consent. However, the agreement-review skill is triggered for every agreement where departed members constituted more than 25% of the affected parties. Quorum thresholds adapt to the current participant count: an agreement that originally had 20 affected parties and now has 14 recalculates its 2/3 quorum based on 14, not 20. Agreements where all affected parties have departed enter automatic review — a steward is assigned from the nearest related circle. The agreement registry flags all entries associated with departed members for stewardship transition review. New members joining after the exodus inherit the existing agreement structure through normal UAF onboarding and are not bound by agreements outside their assigned domains.
