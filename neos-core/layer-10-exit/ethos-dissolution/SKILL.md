---
name: ethos-dissolution
description: "Execute the orderly dissolution of an entire ETHOS -- run this when a unit can no longer sustain operations, ensuring assets are settled, members transition, and governance records are permanently archived."
layer: 10
version: 0.1.0
depends_on: [voluntary-exit, commitment-unwinding, agreement-amendment]
---

# ethos-dissolution

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
