---
skill: agreement-creation
type: rationale
---

# agreement-creation — Rationale & Design Notes

## A. Structural Problem It Solves

Without a formal creation process, agreements emerge informally and unevenly — whoever has social capital or persistence sets the terms, and others discover their obligations after the fact. This skill ensures every agreement has a traceable origin, a defined scope, and a legitimate ratification process. It prevents hidden agreements, unilateral imposition, and the "we all assumed we agreed" failure mode that corrodes trust in governance systems. Every binding commitment in the ecosystem passes through this process or it does not exist.

## B. Domain Scope

This skill applies to any domain where binding commitments between participants are needed. Agreement types follow the hierarchy (no lower-level agreement may contradict a higher-level one):

1. **Universal Agreement Field (UAF)** — root agreement, all participants
2. **Ecosystem Agreement** — e.g., OmniOne Master Plan
3. **Access Agreement** — e.g., SHUR space agreements
4. **Stewardship Agreement** — role-specific commitments
5. **ETHOS Agreement Field** — organizational unit agreements (called "ETHOS" in OmniOne)
6. **Culture Code** — circle-internal norms
7. **Personal Commitments** — individual-level agreements

The skill covers creation of agreements at every level. UAF creation is rare (typically only at ecosystem founding) — most UAF changes use the agreement-amendment skill.

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

A charismatic OmniOne leader, respected for founding one of the most successful ETHOS, proposes a new organizational agreement that would centralize resource allocation decisions under a single "Resource Council" they would chair. They frame objections from smaller circles as "not understanding the big picture" and privately pressure hesitant participants to withdraw their concerns. The agreement-creation process structurally resists this: during the consent phase, every objection is formally recorded before any discussion occurs — once recorded, an objection cannot be erased, only addressed through an integration round. The facilitator (who must be neutral and cannot be the proposer) explicitly states that objections are valued structural contributions. When two participants raise objections about centralization contradicting NEOS's distributed authority principle, the integration rounds require the proposer to substantively modify the proposal, not just reframe objections as misunderstandings. Social pressure to withdraw objections is itself flagged as a capture risk by the facilitator. After three integration rounds fail to resolve the core objection (centralized resource authority contradicts scoped authority), the proposal escalates to GAIA Level 4 coaching.

### 4. High Conflict / Polarization

Two factions within the OmniOne AE have deeply opposed views on a new stewardship agreement for intellectual property. Faction A wants all emergent works to be fully open-source with no restrictions. Faction B wants creators to retain commercial rights with a revenue-sharing model back to the ecosystem. Both factions draft competing agreements. During the synergy check, the conflict is identified and the two proposals are flagged as mutually exclusive. The process requires reconciliation before either can proceed to consent. At GAIA Level 4, a coach maps the tension: Faction A's core concern is preventing privatization of collective work; Faction B's core concern is incentivizing high-quality contributions. The coach facilitates a "Doing Both Solution" — emergent works are open-source by default with a creator opt-in commercial license that returns 30% of revenue to the ecosystem commons. This third solution addresses both factions' core concerns and enters the consent phase as a unified proposal. Both factions participate in consent, and the integration rounds fine-tune the revenue percentage.

### 5. Large-Scale Replication

OmniOne grows from 50 members in one location to 5,000 members across 15 SHUR locations and 80 circles. Agreement creation scales through domain-scoped routing: a kitchen agreement at SHUR Costa Rica involves only the 20 residents of that location, not all 5,000 members. The synergy check becomes more critical at scale — with hundreds of active agreements, the registry query prevents duplication and conflict. Cross-circle agreements are routed through domain matching rather than manual identification, using the registry's domain taxonomy. Ecosystem-level agreements (requiring OSC involvement) remain rare — most governance happens at the circle and ETHOS level. The agreement-template.yaml structure remains the same at every scale; what changes is the routing logic and the size of the affected-parties list. Facilitator capacity scales through a train-the-trainer model within each circle, ensuring every SHUR location has multiple trained facilitators.

### 6. External Legal Pressure

The Indonesian government issues a regulation requiring all co-living spaces to register formal tenancy agreements that include government-mandated clauses about occupancy limits and reporting requirements. This external mandate does not automatically become a NEOS agreement — it enters the ecosystem as information, not as a binding commitment. A SHUR steward proposes a new access agreement that incorporates the required legal clauses alongside NEOS's own stewardship principles. The proposal goes through the full ACT process: during the advice phase, participants distinguish between legal compliance (non-negotiable for the physical jurisdiction) and governance principles (NEOS-internal). The consent phase proceeds normally. The resulting agreement satisfies the legal requirement for the Bali jurisdiction while preserving NEOS principles. Crucially, this agreement applies only to SHUR Bali — it does not modify the UAF or create a precedent that all SHUR locations must adopt the same terms. Members may individually comply with their local laws without those requirements becoming ecosystem-wide agreements.

### 7. Sudden Exit of 30% of Participants

Following a contentious decision about OmniOne's expansion strategy, 15 of 50 members exit within a two-week period. Existing agreements remain valid — they were legitimately created through the full ACT process and the departure of some parties does not retroactively invalidate consent. However, the agreement-review skill is triggered for every agreement where departed members constituted more than 25% of the affected parties. Quorum thresholds adapt to the current participant count: an agreement that originally had 20 affected parties and now has 14 recalculates its 2/3 quorum based on 14, not 20. Agreements where all affected parties have departed enter automatic review — a steward is assigned from the nearest related circle. The agreement registry flags all entries associated with departed members for stewardship transition review. New members joining after the exodus inherit the existing agreement structure through normal UAF onboarding and are not bound by agreements outside their assigned domains.
