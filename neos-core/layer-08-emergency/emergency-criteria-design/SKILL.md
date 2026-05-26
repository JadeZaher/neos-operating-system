---
name: emergency-criteria-design
description: "Define objective, measurable emergency criteria with matching exit conditions -- run this before any crisis arrives so the ecosystem never debates whether an emergency is real while one is happening."
layer: 8
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, safeguard-trigger-design]
---

# emergency-criteria-design

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

When a participant who designed or championed emergency criteria exits the ecosystem, the criteria remain active -- they are institutional safeguards, not personal preferences. If the exiting participant was the sole domain expert for a criterion's risk category (e.g., the only member with structural engineering knowledge for infrastructure failure criteria), the ecosystem identifies a replacement knowledge source. Criteria registry entries authored by departed members remain valid. During a mass exit (20%+ of participants), all criteria are flagged for expedited review to ensure thresholds remain appropriate for the reduced membership.

## L. Cross-Unit Interoperability Impact

Emergency criteria registries for each ETHOS are published to all ecosystem members, enabling cross-unit visibility into what risks each location has prepared for. ETHOS in similar geographic or operational contexts can share criteria templates -- SHUR locations in tropical regions may share natural disaster criteria while customizing thresholds to local conditions. Ecosystem-level criteria (e.g., governance incapacity across the OSC) are designed through ecosystem-wide ACT process, not by any single ETHOS. When two NEOS ecosystems federate (Layer V, deferred), emergency criteria frameworks may be shared as templates, but each ecosystem installs and manages its own criteria through its own ACT process.
