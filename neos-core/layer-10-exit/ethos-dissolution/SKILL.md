---
name: ethos-dissolution
description: "Execute the orderly dissolution of an entire ETHOS -- run this when a unit can no longer sustain operations, ensuring assets are settled, members transition, and governance records are permanently archived."
layer: 10
version: 0.1.0
depends_on: [voluntary-exit, commitment-unwinding, agreement-amendment]
---

# ethos-dissolution

## A. Structural Problem It Solves

Organizations that cannot die become zombies. When dissolution is impossible or excessively painful, failing units persist as governance dead weight -- consuming resources, blocking decisions, and trapping members in non-functional structures. Traditional organizations handle dissolution through top-down executive decisions or bankruptcy proceedings, both of which strip members of agency. NEOS requires a structured collective exit process that respects member sovereignty: no external body can unilaterally dissolve an ETHOS, and no ETHOS can dissolve without accounting for its commitments, assets, and members. This skill provides the ordered process that makes collective exit as dignified and operationally clean as individual exit.

## B. Domain Scope

This skill applies to the dissolution of any ETHOS within a NEOS ecosystem. The scope covers the full dissolution lifecycle: trigger assessment, dissolution proposal, impact assessment, consent round, asset disposition, commitment settlement, member transition, and record archival. It interacts with voluntary-exit (for individual member transitions), commitment-unwinding (for settling all ETHOS-level commitments), and agreement-amendment (for modifying ecosystem-level agreements that reference the dissolving ETHOS). Out of scope: individual member departure (that is voluntary-exit), ecosystem-level dissolution (which would require dissolution of all constituent ETHOS), and ETHOS restructuring or merger (which is an agreement-amendment process, not dissolution).

## C. Trigger Conditions

- **Supermajority consent**: 2/3 of the ETHOS's active members consent to dissolution through a formal proposal process
- **Governance incapacity**: the ETHOS cannot achieve quorum for 3 consecutive scheduled governance sessions (configurable per ETHOS, minimum 2 sessions)
- **Ecosystem-level intervention**: the full ecosystem ACT process (not any single body) determines that an ETHOS must dissolve -- this is an extreme measure requiring extended advice process, ecosystem-wide consent round, and documented evidence of sustained governance failure or harm
- **Zero membership**: all ETHOS members have individually departed through the voluntary-exit skill, leaving no active participants

## D. Required Inputs

- **Dissolution trigger documentation**: evidence of which trigger condition has been met (supermajority consent record, quorum failure log, ecosystem ACT decision, or membership roster showing zero active members)
- **ETHOS asset inventory**: a complete accounting of all resources, property, agreements, roles, and commitments held by or within the ETHOS
- **Member roster**: the current list of active ETHOS members, with their commitment inventories
- **Affected agreements list**: all ecosystem-level agreements that reference the dissolving ETHOS as a party or domain
- **Stakeholder impact assessment**: identification of all circles, members, and external relationships affected by the dissolution

## E. Step-by-Step Process

1. **Confirm dissolution trigger.** The dissolution initiator presents evidence that one of the four trigger conditions has been met. For supermajority consent, the initiator submits a formal dissolution proposal through the ACT process with extended advice period (minimum 21 days, double the standard). For governance incapacity, the quorum failure log is verified against meeting records. For ecosystem intervention, the ecosystem-wide ACT decision is referenced. For zero membership, the membership roster is confirmed empty.
2. **Conduct impact assessment.** A dissolution coordinator (appointed from outside the dissolving ETHOS) assesses the dissolution's impact: which ecosystem agreements reference this ETHOS, which cross-ETHOS commitments exist, which members will need to transition, and what assets require disposition. The assessment is published to all ecosystem members within 14 days.
3. **Execute consent round.** For supermajority-triggered dissolution, a formal consent round is conducted with a 14-day window. Each ETHOS member may consent, object (with a reasoned objection that must be integrated), or stand aside. The 2/3 threshold applies to those who participate (stand-asides are excluded from the count). For other triggers, the consent round confirms member awareness and records preferences for asset disposition and member transition.
4. **Settle debts and obligations.** All outstanding debts, contractual obligations, and economic commitments are settled first. This follows the commitment-unwinding skill's economic protocols, applied at the ETHOS level rather than the individual level. Creditors and obligation holders are paid or have their claims formally transferred.
5. **Return stewarded resources.** Resources that the ETHOS stewards on behalf of the ecosystem or external parties are returned to their source or transferred to a designated receiving body. Physical assets, shared spaces, and equipment are inventoried and distributed per the consent round's disposition preferences.
6. **Distribute remaining assets.** After debts are settled and stewarded resources returned, any remaining assets are distributed according to the disposition plan established during the consent round. Default: remaining assets transfer to the ecosystem's common resource pool. The dissolving ETHOS's members may propose alternative distributions (e.g., seed funding for successor ETHOS) through the consent round.
7. **Transition all members.** Each member of the dissolving ETHOS is offered three options: transfer to another existing ETHOS within the ecosystem, initiate formation of a new ETHOS, or depart the ecosystem through the voluntary-exit skill. Each transitioning member receives a portable record. Members who do not choose within 30 days are contacted individually; if unreachable for an additional 14 days, they are processed as ecosystem departures.
8. **Amend affected agreements.** All ecosystem-level agreements that reference the dissolving ETHOS as a party or domain are amended through the agreement-amendment skill to remove the ETHOS reference. Agreements that cannot function without the ETHOS are flagged for ecosystem-level review.
9. **Archive governance records.** The ETHOS's complete governance history -- decision logs, agreements, role records, governance health audits, and the dissolution record itself -- is archived in the ecosystem's governance memory (Layer IX). Archives are permanent and accessible to all ecosystem members and former ETHOS members.
10. **File Dissolution Record.** The dissolution coordinator compiles the Dissolution Record using `assets/dissolution-record-template.yaml`, documenting the trigger, consent results, asset disposition, member transitions, and archival references. The record is published to all ecosystem members.

## F. Output Artifact

A Dissolution Record following `assets/dissolution-record-template.yaml`. The record contains: dissolution ID, ETHOS identity, dissolution trigger type and evidence, consent round results, asset disposition summary (debts settled, resources returned, remaining assets distributed), member transition summary (transfers, new ETHOS, departures), affected agreements amended, governance archive reference, coordinator identity, and effective dissolution date. The record is permanent and accessible to all ecosystem members.

## G. Authority Boundary Check

- **No external body can unilaterally dissolve an ETHOS** -- not the OSC, not GEV, not any individual leader
- **Ecosystem-level intervention** requires the full ecosystem ACT process with extended advice and ecosystem-wide consent -- it is not a shortcut for any council or leadership body
- **The dissolution coordinator** facilitates the process but cannot override member consent on asset disposition or transition choices
- **Individual members** retain their right to voluntary exit at any point during the dissolution process -- they need not wait for dissolution to complete
- **Creditors and obligation holders** have priority in asset disposition (debts before distribution) but cannot block the dissolution process itself
- **OSC** is notified and may participate in the consent round but has no veto power over dissolution

## H. Capture Resistance Check

**Dissolution suppression.** The governance incapacity trigger prevents a minority from keeping a non-functional ETHOS alive by blocking dissolution proposals. If the ETHOS cannot achieve quorum, dissolution proceeds regardless of minority objection. The zero-membership trigger is automatic -- no one needs to propose dissolution of an empty unit.

**Forced dissolution.** The ecosystem-intervention trigger requires the most rigorous process in NEOS: extended advice, ecosystem-wide consent, and documented evidence. No single body, leader, or council can force dissolution. The full ACT process ensures that dissolution-as-punishment is structurally infeasible without broad ecosystem agreement.

**Asset capture.** The ordered disposition process (debts first, stewarded resources second, remaining assets third) prevents any party from capturing dissolution assets. The consent round determines distribution, not any individual decision-maker. Default distribution to the common pool prevents asset concentration.

**Member coercion.** Every member has three transition options plus the unconditional right to depart. No member is forced into a specific receiving ETHOS or required to join a successor organization. The 30-day transition window with individual outreach prevents members from being silently dropped.

## I. Failure Containment Logic

- **Consent round fails to reach 2/3**: the dissolution proposal is archived and may be resubmitted after 90 days; the ETHOS continues operating under existing governance
- **Asset inventory reveals hidden debts**: the dissolution coordinator pauses asset distribution until debts are verified and settled; the dissolution timeline extends by up to 30 days for debt verification
- **Members refuse to choose transition option**: after 30 days plus 14-day outreach, unreachable members are processed as ecosystem departures with portable records generated from available data
- **Ecosystem agreements cannot be amended**: agreements that critically depend on the dissolving ETHOS are escalated to the OSC for emergency stewardship until the ecosystem can restructure through normal governance
- **Dissolution coordinator becomes unavailable**: a replacement coordinator is appointed from outside the dissolving ETHOS through the role-assignment skill

## J. Expiry / Review Condition

Dissolution Records do not expire -- they are permanent governance records. The dissolution skill itself is reviewed annually through the ACT consent process. The governance incapacity trigger's quorum failure threshold (default: 3 consecutive sessions) is configurable per ETHOS through its foundational agreement. The ecosystem-intervention trigger's requirements (extended advice, ecosystem-wide consent) cannot be relaxed -- they are structural minimums that protect ETHOS sovereignty.

## K. Exit Compatibility Check

This skill is the collective exit process for ETHOS. It ensures that every individual member's exit rights are preserved during collective dissolution: each member transitions through one of three options, with voluntary-exit as the fallback. The dissolution process generates portable records for all members and archives governance history so that departing members retain access to their participation records. No commitment or obligation survives the dissolution in a way that binds former members.

## L. Cross-Unit Interoperability Impact

When an ETHOS dissolves, cross-ETHOS agreements that included the dissolving unit are amended to remove it. Members who transfer to other ETHOS carry their portable records and may have role experience recognized by the receiving ETHOS. The dissolution's impact on ecosystem-level governance metrics (participation rates, proposal diversity) is captured by the next governance health audit. If the dissolved ETHOS was the last unit in a geographic region, the ecosystem may initiate a new ETHOS formation process -- but this is a separate governance action, not part of the dissolution. The Dissolution Record format is standardized across all NEOS ecosystems for interoperability.

## OmniOne Walkthrough

The SHUR Bali Learning Garden ETHOS, a small unit focused on permaculture education, has dwindled to 4 active members: Putu, Komang, Made, and Nyoman. The ETHOS was founded with 12 members two years ago but has struggled with member retention as the permaculture program shifted to a different Bali location. For the past two months, the ETHOS has failed to achieve its 3-person quorum for governance sessions because Made has been traveling and Nyoman has reduced participation.

Putu recognizes the situation and submits a formal dissolution proposal through the ACT process. The extended advice period runs for 21 days. During this time, Komang reaches out to all former members and the OSC to explore alternatives. No viable restructuring option emerges -- the remaining members agree the ETHOS has fulfilled its purpose and cannot sustain operations.

The OSC appoints Wayan, an AE member from the larger SHUR Bali ETHOS, as dissolution coordinator. Wayan is not a member of the Learning Garden and has no stake in its assets.

Wayan conducts the impact assessment: the Learning Garden holds a shared tool library (valued at $2,400), a small seed bank stewarded on behalf of the ecosystem, 3 active agreements (a space-sharing agreement with the main SHUR, a composting partnership with a local farm, and the ETHOS's foundational agreement), and an outstanding commitment of 200 Current-Sees earmarked for a seed-saving workshop that was never delivered.

The consent round is conducted: Putu, Komang, and Nyoman consent to dissolution. Made, reached by message during travel, also consents. The 4/4 result exceeds the 2/3 threshold.

Wayan processes asset disposition. The 200 Current-Sees earmarked for the undelivered workshop return to the ecosystem resource pool. The seed bank transfers to the main SHUR Bali's garden program. The tool library is divided: Putu and Komang (who are transferring to the main SHUR) take the tools they will use in their new circles; remaining tools enter the ecosystem's shared equipment pool. The space-sharing agreement is amended to remove the Learning Garden as a party. The composting partnership is terminated with 30-day notice to the local farm, as documented in the partnership terms.

Member transitions: Putu and Komang transfer to the main SHUR Bali ETHOS, joining the Food Systems Circle. Made, still traveling, decides to depart the ecosystem entirely -- her voluntary exit is processed with a portable record. Nyoman chooses to help form a new ETHOS focused on water systems, submitting a formation proposal to the ecosystem.

**Edge case**: During asset disposition, Wayan discovers that the Learning Garden informally hosted a community seed library that neighboring non-member farmers rely on. This is not a formal governance commitment, but it has real community impact. Wayan documents the informal relationship in the dissolution record and the main SHUR Bali ETHOS agrees to continue hosting the seed library as part of their community relations. The dissolution does not abandon informal community commitments -- but neither does it force any receiving body to accept them.

Wayan files Dissolution Record DISS-LG-2026-001 and archives the Learning Garden's two-year governance history in ecosystem memory. All four members receive copies of the record and their portable governance records.

## Stress-Test Results

### 1. Capital Influx

A major funder who specifically funded the dissolving ETHOS demands return of unspent funds as a condition of continued ecosystem-wide funding. The dissolution skill's ordered asset disposition handles this: debts and obligations are settled first. If the funding agreement included a return-on-dissolution clause, the funds are returned per the agreement terms. If the funder's demand goes beyond the original agreement, it is treated as a new negotiation handled by the ecosystem's resource steward (Layer IV), not as a dissolution blocker. The dissolution proceeds on its timeline regardless of the funder's broader leverage. The dissolution record documents the funding settlement, providing a clear record that the ecosystem fulfilled its obligations. The funder's attempt to condition ecosystem-wide funding on a single ETHOS's dissolution outcome is flagged as a capital capture risk for governance health assessment.

### 2. Emergency Crisis

A natural disaster destroys the physical infrastructure of a SHUR location, and the ETHOS's members are scattered. The governance incapacity trigger activates naturally: the ETHOS cannot achieve quorum because members are displaced. The dissolution process adapts to emergency conditions: the impact assessment is abbreviated, member outreach uses all available channels, and the consent round extends to 30 days to accommodate members in crisis. Asset disposition prioritizes emergency needs -- shared resources go to displaced members first, formal settlement follows when conditions stabilize. Members who cannot be reached within the extended timeline are processed as emergency departures with portable records generated from available data. The dissolution record notes emergency conditions throughout, providing context for future reference.

### 3. Leadership Charisma Capture

A charismatic ETHOS founder refuses to accept dissolution, arguing that the unit embodies a unique vision that the ecosystem will lose. The founder uses personal influence to pressure members to vote against dissolution. The dissolution skill resists this through structural protections: the consent round uses the standard ACT process with a structurally independent coordinator. The founder's voice is one among the membership -- their charisma does not translate into veto power. If the 2/3 threshold is not met, the proposal fails on its merits (or the founder's persuasion), and the ETHOS continues. But if governance incapacity triggers dissolution (the ETHOS cannot achieve quorum because discouraged members stop attending), the founder's refusal is irrelevant -- the structural trigger overrides individual resistance. The dissolution record documents participation patterns, making any charismatic suppression of dissolution visible to governance health audit.

### 4. High Conflict / Polarization

Two factions within an ETHOS disagree fundamentally about its direction, and one faction submits a dissolution proposal to force a reset. The extended advice period (21 days, double standard) gives both factions time to explore alternatives: restructuring, splitting into two ETHOS, or amending the foundational agreement. If no alternative resolves the conflict and 2/3 consent to dissolution, the process proceeds. During asset disposition, factional tensions surface in competing claims. The dissolution coordinator -- structurally independent of both factions -- applies the ordered disposition protocol: debts first, stewarded resources second, remaining assets per consent round preferences. The consent round's asset distribution vote prevents either faction from unilaterally capturing dissolution assets. Members from both factions receive equal transition options and portable records.

### 5. Large-Scale Replication

At ecosystem scale with 12 SHUR locations and 60 circles, ETHOS dissolution becomes a periodic event rather than a crisis. The standardized dissolution process means every dissolution follows the same template: trigger verification, impact assessment, consent round, ordered disposition, member transition, record archival. The ecosystem develops institutional knowledge about dissolution -- which transition patterns work best, how to handle cross-ETHOS asset transfers, and what signs predict ETHOS decline. Dissolution records accumulate in ecosystem memory, enabling pattern analysis: if multiple ETHOS in the same region dissolve within a short period, it signals a systemic issue. The dissolution skill scales without modification -- the same process applies to a 4-person study circle and a 200-person regional SHUR.

### 6. External Legal Pressure

A government regulator requires formal notification when a registered organization dissolves. The Dissolution Record provides the structured documentation needed for regulatory compliance. The ecosystem's legal entity (GEV) translates the governance dissolution record into whatever legal filings the jurisdiction requires. The governance process itself is not modified for legal compliance -- the dissolution proceeds according to NEOS protocols, and legal compliance is a parallel track handled by the legal entity. If the regulator requires a different dissolution procedure than NEOS prescribes (e.g., a government-mandated wind-down period), the legal entity negotiates compliance while the governance dissolution runs on its own timeline. Members comply with local laws individually; the ecosystem's governance dissolution is governed by its own agreements.

### 7. Sudden Exit of 30% of Participants

A mass departure triggers governance incapacity in a small ETHOS: with only 6 members remaining out of 20, the ETHOS cannot achieve quorum for 3 consecutive sessions. The governance incapacity trigger fires automatically. The dissolution coordinator processes the dissolution with the 6 remaining members, who were unable to sustain the ETHOS's operations. Asset disposition addresses the accumulated commitments of both the individually departed members (already processed through voluntary-exit) and the collective ETHOS assets. The 6 remaining members transition through the standard three options. The dissolution record notes the mass departure as context, linking to the individual departure records and the governance health audit that was triggered by the mass exit. The sequential cascade -- mass individual exit, governance incapacity, ETHOS dissolution -- is documented as a connected governance event across all three records.
