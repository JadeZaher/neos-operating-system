---
name: emergency-criteria-design
description: "Define objective, measurable emergency criteria with matching exit conditions -- run this before any crisis arrives so the ecosystem never debates whether an emergency is real while one is happening."
layer: 8
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, safeguard-trigger-design]
---

# emergency-criteria-design

## A. Structural Problem It Solves

Every governance system faces genuine crises -- natural disasters, funding collapses, infrastructure failures, external legal threats. The structural danger is not the crisis itself but the moment of declaration: who decides that an emergency exists, and by what standard? Without pre-defined, measurable criteria, emergency declarations become subjective judgments made by whoever holds the most influence in the moment of fear. Giorgio Agamben documented how the "state of exception" -- the power to declare emergency -- is the most dangerous authority in any political system, because it suspends all other rules. NEOS resists this by requiring that emergency criteria be designed during calm conditions, consented to through the ACT process, and defined with objective thresholds that leave no room for interpretive manipulation. The ecosystem decides in advance what constitutes an emergency, so that no individual or body gains the power to declare one based on subjective assessment.

## B. Domain Scope

This skill applies to any ETHOS or ecosystem that needs to define conditions under which normal governance processes compress or temporarily restructure. Emergency criteria are scoped to the domain boundary defined by domain-mapping (Layer II) -- criteria designed for SHUR Bali address Bali-specific risks, not the entire OmniOne ecosystem, unless explicitly scoped to ecosystem level. The skill covers the design and installation of criteria, not the activation of emergency authority (that is pre-authorization-protocol) or the conduct of crisis operations (that is crisis-coordination). Out of scope: this skill does not define what actions are taken during an emergency -- it defines only the measurable conditions under which emergency status begins and ends.

## C. Trigger Conditions

- **New ecosystem setup**: when an ETHOS or ecosystem establishes its governance structure, emergency criteria design is part of initial configuration
- **Risk assessment update**: when the ecosystem identifies a new category of risk not covered by existing criteria (e.g., a new SHUR location in an earthquake-prone region)
- **Post-emergency review recommendation**: when a post-emergency review identifies gaps in existing criteria (e.g., criteria existed for natural disaster but not for pandemic)
- **Scheduled review**: emergency criteria are reviewed annually through the ACT process to ensure continued relevance
- **Near-miss event**: when conditions approach but do not cross an existing threshold, prompting evaluation of whether criteria are appropriately calibrated

## D. Required Inputs

- **Risk assessment**: a structured identification of credible emergency scenarios for the ETHOS's domain, informed by geographic, financial, legal, and operational context
- **Existing criteria registry**: all currently active emergency criteria for the scope, to prevent duplication and ensure coherence
- **Safeguard trigger registry**: active Layer VII triggers that may interact with emergency thresholds (per safeguard-trigger-design)
- **ACT process access**: criteria must be designed and installed through the Advice-Consent-Test protocol (Layer III)
- **Domain boundary**: the scope boundary from domain-mapping, confirming which ETHOS or ecosystem the criteria apply to
- **Stakeholder input**: affected participants who will provide consent during installation

## E. Step-by-Step Process

1. **Conduct risk assessment.** The criteria designer identifies credible emergency scenarios for the ETHOS's domain across five starter categories: physical safety, resource crisis, governance incapacity, external legal threat, and infrastructure failure. Each scenario must be grounded in the ETHOS's actual context -- geographic hazards, funding structure, regulatory environment, and operational dependencies. Timeline: 3-7 days.
2. **Define entry criteria.** For each identified scenario, specify the measurable threshold that constitutes an emergency declaration. Entry criteria must be objective and externally verifiable: "Category 3+ cyclone within 50km of SHUR facility" not "severe weather." Each criterion specifies the data source, measurement method, and threshold value.
3. **Define matching exit criteria.** Every entry criterion must have an equally measurable exit condition. Exit criteria define when the emergency ends, not when leadership decides it ends. Example: entry = "flooding reaches ground floor of SHUR facility"; exit = "water level below ground floor for 48 consecutive hours AND structural safety inspection passed." Exit criteria must be at least as specific as entry criteria.
4. **Define maximum duration.** Each criterion includes a maximum emergency duration after which the emergency automatically enters the reversion process (per emergency-reversion), regardless of whether exit criteria have been met. This prevents indefinite emergencies. Default maximum: 30 days, extendable only through emergency ACT consent (per crisis-coordination).
5. **Map to circuit breaker states.** Each criterion maps to the circuit breaker model: Closed (normal operations), Open (emergency active), Half-Open (recovery/reversion). The entry criterion triggers Closed-to-Open transition. The exit criterion plus reversion process triggers Open-to-Half-Open. The post-emergency review completion triggers Half-Open-to-Closed.
6. **Cross-reference safeguard triggers.** Review existing Layer VII safeguard triggers for interactions. Emergency criteria should not conflict with or duplicate safeguard triggers. Emergency criteria that address governance incapacity should reference the governance health indicators that signal incapacity.
7. **Enter ACT Advice phase.** Share the criteria design with affected stakeholders for advice per act-advice-phase. Advisors evaluate: Are the thresholds appropriate? Are exit criteria equally measurable? Is the maximum duration reasonable? Are any credible risks missing? Timeline: 5-10 days.
8. **Enter ACT Consent phase.** Present the criteria for consent per act-consent-phase. Consent means "no reasoned objection." Objections must reference specific structural concerns. Timeline: 5-7 days.
9. **Install in Emergency Criteria Registry.** Upon consent, register each criterion with a unique ID, category, entry threshold, exit threshold, maximum duration, installation date, and status "active." The registry is published to all ecosystem members.
10. **Schedule review.** Set annual review date. Criteria that have never been activated receive additional scrutiny -- they may be over-specified for risks that have not materialized, or they may be correctly calibrated for rare events.

## F. Output Artifact

An Emergency Criteria Registry entry following `assets/emergency-criteria-template.yaml`. Each entry contains: criterion ID, category (physical safety, resource crisis, governance incapacity, external legal threat, or infrastructure failure), criterion name, entry threshold (measurable), exit threshold (measurable), data source, maximum duration, circuit breaker transition mapping, installed-by reference (ACT decision ID), installation date, review date, activation history, and status. The full registry is accessible to all ecosystem members.

## G. Authority Boundary Check

- **Any ecosystem member** can propose new emergency criteria through the ACT process
- **The ACT consent process** determines whether criteria are installed -- no individual or leadership body can define emergency criteria unilaterally
- **No individual or body** can declare an emergency outside the criteria registry -- the criteria are the sole basis for emergency declaration
- **Emergency criteria cannot be created or modified during an active emergency** -- this is an irreducible constraint that prevents self-serving criteria manipulation
- **The OSC** receives the criteria registry but does not gate its content
- **Exit criteria carry equal weight to entry criteria** -- leadership cannot extend an emergency by ignoring exit conditions

## H. Capture Resistance Check

**Capital capture.** Resource crisis criteria include thresholds for funding concentration and sudden loss, making the ecosystem's financial vulnerabilities visible and pre-addressed. A funder who threatens withdrawal cannot create an emergency declaration unless the funding loss crosses the pre-defined threshold. The criteria are designed during calm conditions when funders have no leverage over the design process.

**Charismatic capture.** Governance incapacity criteria include measurable indicators for decision-making concentration and participation collapse, drawn from Layer VII governance health indicators. A charismatic leader cannot declare a "governance emergency" to consolidate authority -- the criteria are objective and pre-consented. The leader's subjective assessment of crisis carries no more weight than any other member's.

**Emergency capture.** This skill is the primary defense against emergency capture. By requiring pre-defined, measurable, consented-to criteria with matching exit conditions and maximum durations, the skill eliminates the subjective declaration power that Agamben identified as the foundation of emergency capture. No one gains the authority to decide what constitutes an emergency -- the criteria decide.

**Informal capture.** All criteria are formally registered, publicly visible, and installed through ACT consent. There are no informal or undocumented emergency conditions. If a situation arises that does not match any registered criterion, it is not an emergency under NEOS governance -- it is an urgent situation that must be addressed through normal (possibly expedited) governance processes.

## I. Failure Containment Logic

- **Novel crisis not covered by existing criteria**: the ecosystem addresses the situation through normal governance processes, even if expedited. After resolution, a post-event review designs new criteria for the novel scenario through ACT process
- **Criteria threshold ambiguous in practice**: if the data source or measurement method produces unclear results during a potential emergency, the most conservative interpretation applies (i.e., if unclear whether threshold is crossed, treat as not crossed). Ambiguity is documented for criteria refinement
- **Exit criteria met but conditions feel unsafe**: the exit criteria govern, not subjective assessment. If the feeling of unsafety persists after exit criteria are met, a new risk assessment can identify the gap and propose additional criteria through normal ACT process
- **Criteria registry becomes stale**: if annual review is missed, an automatic escalation notifies all ecosystem members and the OSC. Stale criteria remain active but are flagged as requiring review
- **Multiple criteria triggered simultaneously**: each criterion operates independently. Multiple simultaneous emergencies activate multiple pre-authorized response tracks. The crisis-coordination skill handles operational coordination across concurrent emergencies

## J. Expiry / Review Condition

Emergency criteria do not expire but are reviewed annually through the ACT process. The review evaluates: Have risk conditions changed? Were any criteria activated, and if so, were the thresholds appropriate? Are exit criteria sufficiently measurable? Has the maximum duration proven adequate? Criteria that have never been activated in three years receive enhanced scrutiny -- either the risk has not materialized (acceptable) or the threshold is too high (needs recalibration). The annual review follows the same ACT Advice-Consent process as initial installation. Criteria cannot be retired silently -- retirement requires ACT consent and is logged in the registry.

## K. Exit Compatibility Check

When a participant who designed or championed emergency criteria exits the ecosystem, the criteria remain active -- they are institutional safeguards, not personal preferences. If the exiting participant was the sole domain expert for a criterion's risk category (e.g., the only member with structural engineering knowledge for infrastructure failure criteria), the ecosystem identifies a replacement knowledge source during the 30-day wind-down period. Criteria registry entries authored by departed members remain valid. During a mass exit (20%+ of participants), all criteria are flagged for expedited review to ensure thresholds remain appropriate for the reduced membership.

## L. Cross-Unit Interoperability Impact

Emergency criteria registries for each ETHOS are published to all ecosystem members, enabling cross-unit visibility into what risks each location has prepared for. ETHOS in similar geographic or operational contexts can share criteria templates -- SHUR locations in tropical regions may share natural disaster criteria while customizing thresholds to local conditions. Ecosystem-level criteria (e.g., governance incapacity across the OSC) are designed through ecosystem-wide ACT process, not by any single ETHOS. When two NEOS ecosystems federate (Layer V, deferred), emergency criteria frameworks may be shared as templates, but each ecosystem installs and manages its own criteria through its own ACT process.

## OmniOne Walkthrough

It is February 2026, and the OSC has directed all SHUR locations to design emergency criteria as part of their governance foundation. The Bali SHUR team -- Ketut (circle steward), Ratu (facilities steward), and Nadia (AE liaison) -- leads the criteria design process for SHUR Bali.

**Risk assessment.** The team identifies five scenarios grounded in Bali's context: (1) natural disaster -- Bali sits in a seismically active zone with monsoon flooding risk; (2) funding loss -- GEV provides 35% of SHUR Bali's operating budget, creating a single-source dependency; (3) governance incapacity -- with 38 members, quorum loss from illness or travel could paralyze decision-making; (4) external legal threat -- Indonesian co-living regulations are evolving and could impose sudden compliance demands; (5) infrastructure failure -- the SHUR facility depends on a single well for water and a solar-battery system for power.

**Criteria design -- natural disaster.** Entry criterion: "Indonesian BMKG issues a Level 3 or higher alert for Bali region (earthquake, volcanic eruption, flooding) OR physical damage to SHUR facility renders any residential or common space unsafe for occupancy as confirmed by two independent assessments." Exit criterion: "BMKG alert downgraded below Level 3 for 48 consecutive hours AND facility safety inspection passed by qualified assessor AND all displaced members have confirmed safe shelter." Maximum duration: 14 days, extendable through emergency ACT consent.

**Criteria design -- funding loss.** Entry criterion: "Confirmed loss of funding constituting 25% or more of the ETHOS's quarterly operating budget with less than 60 days notice AND no replacement funding source identified." Exit criterion: "Replacement funding secured covering at least 75% of the shortfall OR operating costs reduced through consented restructuring to match available resources." Maximum duration: 30 days.

**ACT process.** The five criteria enter the Advice phase. Dewa, the financial steward, advises that the funding loss threshold of 25% may be too low for an early-stage ecosystem: "We should set it at 30% to avoid triggering emergency protocols for normal funding variability." Tomasz, a TH member, notes that the infrastructure failure criterion should specify "sustained" failure: "A 4-hour power outage is not an emergency." The team revises: infrastructure failure entry criterion now requires "sustained failure exceeding 48 hours." During Consent, Sari objects to the governance incapacity criterion: "Quorum loss from travel is predictable and should be handled through delegation, not emergency declaration." The team integrates by adding a qualifier: governance incapacity requires "inability to achieve quorum for 14 consecutive days despite delegation attempts." Consent achieved for all five criteria.

**Edge case.** Six months later, a moderate earthquake (magnitude 4.2) shakes Bali. BMKG issues a Level 2 alert, below the Level 3 threshold. Some members feel unsafe and want to declare an emergency. The criteria are clear: Level 2 does not cross the threshold. The ecosystem responds through normal governance -- Ratu arranges a voluntary safety inspection, Ketut calls an expedited TH meeting to discuss preparedness. No emergency is declared, no emergency authority is activated, and no precedent is set for subjective declaration. The near-miss is documented for the annual criteria review, where the team can evaluate whether Level 2 should be added as a criterion.

## Stress-Test Results

### 1. Capital Influx

A cryptocurrency foundation offers OmniOne $3 million in annual funding through SHUR Bali, contingent on the facility hosting quarterly "blockchain governance" workshops. The funding would constitute 60% of SHUR Bali's operating budget. The resource crisis criterion has a pre-defined entry threshold of 30% funding loss with less than 60 days notice. This criterion was designed during calm conditions through ACT consent -- the crypto foundation had no influence over its design. If the foundation later threatens to withdraw funding unless the workshops continue, the ecosystem has a clear, pre-consented threshold for when that withdrawal constitutes an emergency versus a normal budget adjustment. The criteria prevent the foundation from manufacturing urgency: a 60% funding source threatening withdrawal is alarming, but the emergency is defined by the measurable threshold, not by the funder's leverage. Meanwhile, the Layer VII capital capture trigger fires independently on the 60% concentration. The criteria and safeguard systems operate in parallel, each addressing different structural risks from the same funding relationship.

### 2. Emergency Crisis

A volcanic eruption forces evacuation of the Bali SHUR facility. The entry criterion -- BMKG Level 3+ alert for Bali region -- is unambiguously met. The emergency declaration is not a judgment call; it is a measurable threshold crossing. The circuit breaker transitions from Closed to Open. Pre-authorized emergency roles activate (per pre-authorization-protocol). The exit criterion is equally clear: BMKG alert below Level 3 for 48 consecutive hours, facility safety inspection passed, all displaced members confirmed safe. During the crisis, some members argue that the emergency should continue even after the alert is downgraded because "aftershocks are possible." The criteria are clear: the exit threshold is the BMKG alert level and safety inspection, not subjective risk assessment. The maximum duration of 14 days provides a hard backstop. When the alert is downgraded and the inspection passes on day 9, the reversion process begins regardless of anyone's subjective assessment that more time is needed. If aftershock risk is a genuine concern, a new risk category can be proposed through normal ACT process after the emergency concludes.

### 3. Leadership Charisma Capture

Surya, the beloved founding member, is deeply concerned about what she perceives as declining community cohesion. She proposes declaring a "governance emergency" to restructure decision-making processes under temporary centralized authority. The governance incapacity criterion requires measurable conditions: inability to achieve quorum for 14 consecutive days despite delegation attempts. Current governance data shows quorum is being met, proposals are being processed, and participation is stable. Surya's subjective assessment of "declining cohesion" does not cross any registered threshold. The criteria prevent a charismatic leader from converting personal concern into emergency authority. Surya can propose changes through normal ACT process -- she can even propose new criteria for community cohesion as a risk category. But she cannot declare an emergency based on her assessment alone, regardless of how much the community respects her judgment. The criteria are the authority, not the person.

### 4. High Conflict / Polarization

Two factions within SHUR Bali are deeply divided over a proposed partnership. Faction A argues that the conflict constitutes a "governance emergency" because proposals are stalling and participation is declining. Faction B argues the conflict is healthy democratic tension. The governance incapacity criterion provides the objective test: has the ETHOS been unable to achieve quorum for 14 consecutive days despite delegation attempts? The answer is no -- quorum is being met, even though meetings are contentious. Participation has declined 12%, but the governance incapacity threshold specifies quorum failure, not participation decline (participation decline is handled by Layer VII safeguard triggers, not emergency criteria). The criteria prevent either faction from escalating a political conflict into an emergency declaration that would suspend normal governance -- exactly the scenario Agamben warned about. The conflict is addressed through GAIA escalation (Layer VI) and normal ACT process, not through emergency authority.

### 5. Large-Scale Replication

OmniOne scales to 4,000 members across 12 SHUR locations. Each location designs emergency criteria specific to its geographic, financial, and operational context through local ACT processes. The starter criteria categories (physical safety, resource crisis, governance incapacity, external legal threat, infrastructure failure) provide a consistent framework, while thresholds are locally calibrated. A SHUR in Costa Rica designs earthquake criteria with different seismic thresholds than Bali. A SHUR in Portugal focuses on wildfire and drought criteria. The criteria template (`assets/emergency-criteria-template.yaml`) ensures structural consistency across locations while allowing contextual customization. Ecosystem-level criteria are designed through ecosystem-wide ACT process for risks that affect the entire network (e.g., the OSC becoming incapacitated). The OSC reviews all location-level criteria registries annually to identify gaps -- a SHUR in a flood-prone area without flooding criteria receives a recommendation, not a mandate.

### 6. External Legal Pressure

The Indonesian government passes a regulation requiring all co-living organizations to designate a "crisis management officer" with unilateral emergency declaration authority. This directly conflicts with NEOS principles: emergency declaration in NEOS is criteria-based, not person-based. The ecosystem responds by designating a compliance liaison who can interface with government requirements while the internal governance structure maintains criteria-based declaration. The liaison can report to authorities that an emergency has been declared, but the declaration itself is triggered by the criteria registry, not by the liaison's judgment. If the government insists on individual declaration authority, the ecosystem documents the external requirement, designs criteria that are triggered by the government's own declaration (making the external mandate a data source rather than an authority source), and ensures that NEOS exit criteria and maximum durations still apply. The criteria framework absorbs the external pressure without granting any individual the subjective declaration power that NEOS structurally resists.

### 7. Sudden Exit of 30% of Participants

Twelve of 38 SHUR Bali members exit within two weeks following a contentious OSC decision. The governance incapacity criterion has a quorum-based threshold: inability to achieve quorum for 14 consecutive days despite delegation attempts. With 26 remaining members, quorum can still be achieved -- the criterion does not fire. However, the mass exit triggers a Layer VII automatic governance health audit (mass exit trigger at 20% threshold). The criteria registry is flagged for expedited review: are the thresholds still appropriate for 26 members? The funding loss criterion may need recalibration if departing members were significant contributors. The governance incapacity quorum threshold is recalculated against the 26-member base. The review proceeds through normal ACT process with the remaining members. Existing criteria remain active during the review. The mass exit is painful but does not constitute an emergency under the pre-consented criteria -- it is addressed through normal governance processes, preventing anyone from using the departure as justification for seizing emergency authority.
