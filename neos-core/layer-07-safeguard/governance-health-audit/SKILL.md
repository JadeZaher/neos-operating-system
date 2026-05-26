---
name: governance-health-audit
description: "Conduct a structured, quantified review of governance health indicators across an ETHOS or ecosystem -- run this whenever decision patterns, participation, or resource flows need independent assessment."
layer: 7
version: 0.1.0
depends_on: [agreement-registry, domain-mapping, role-assignment]
---

# governance-health-audit

## C. Trigger Conditions

- **Scheduled audit**: every quarter by default (configurable per ETHOS, minimum frequency: semi-annual)
- **Threshold trigger**: any governance health indicator crosses from healthy to warning or from warning to critical, as reported by independent-monitoring data
- **Participant request**: any ecosystem member requests an audit of their ETHOS or circle, with a minimum of 3 co-signers to prevent frivolous requests
- **Post-emergency review**: following any emergency declaration (Layer VIII), an audit is triggered within 30 days of the emergency's conclusion
- **Mass exit trigger**: when 20% or more of an ETHOS's participants exit within a 30-day period, an automatic audit is triggered

## D. Required Inputs

- **Audit scope**: the ETHOS name or "ecosystem" designation, with the domain boundary confirmed via domain-mapping
- **Time period**: the start and end dates of the period under review (default: previous quarter)
- **Governance data report**: raw data collected by the independent-monitoring skill, covering the audit period
- **Decision logs**: all ACT process records for the scope and period, including proposal authorship, consent positions, objection records, and integration outcomes
- **Resource allocation records**: all resource flows within the scope, including funding sources, disbursements, and allocation decisions
- **Participation records**: meeting attendance, decision participation rates, and engagement metrics for the scope and period
- **Role-assignment records**: current and historical role assignments, including leadership tenure data
- **Prior audit report** (if available): the previous Governance Health Report for trend comparison

## E. Step-by-Step Process

1. **Confirm audit scope and authority.** The audit initiator confirms the scope (ETHOS or ecosystem) and verifies their authority to request an audit within that domain via the domain-mapping skill. The initiator is not the auditor -- separation of request and execution prevents self-assessment.
2. **Appoint audit team.** The audit team consists of at least two participants who do not hold leadership roles within the audited scope. If no qualified participants are available within the scope, the team draws from adjacent ETHOS. Appointment follows the role-assignment skill process.
3. **Collect governance data.** The audit team receives the Governance Data Report from the independent monitor (per the independent-monitoring skill). The team does not collect raw data themselves -- this separation prevents data selection bias.
4. **Score each indicator.** The team evaluates each of the 8 governance health indicators defined in `assets/indicator-definitions.yaml` against the collected data, recording the measured value and assigning a status (healthy, warning, or critical) based on the defined thresholds.
5. **Calculate trends.** For each indicator, compare the current score to the prior audit's score. Record the trend as improving, stable, or degrading. If no prior audit exists, mark trend as "baseline."
6. **Identify triggered safeguards.** Cross-reference indicator scores against the safeguard trigger registry (per safeguard-trigger-design). Any trigger whose threshold is crossed is listed with the specific indicator data that activated it.
7. **Draft recommendations.** The audit team writes structural recommendations based on the indicator scores. Recommendations are advisory -- they do not carry authority to mandate changes. Recommendations reference specific skills (e.g., "initiate structural-diversity-maintenance review for proposal authorship").
8. **Compile report.** Assemble the Governance Health Report using `assets/governance-health-report-template.yaml`, including all indicator scores, trends, triggered safeguards, and recommendations.
9. **Publish to all ecosystem members.** The report is published to every member within the audit scope and to the OSC. Publication cannot be suppressed by leadership of the audited body. Any suppression attempt is itself logged as a critical governance health event.
10. **Schedule next audit.** Record the next scheduled audit date (default: one quarter from publication).

## F. Output Artifact

A Governance Health Report following `assets/governance-health-report-template.yaml`. The report contains: report ID, audit scope, audit period, auditor identities, data source references, all 8 indicator scores with measured values and status, trend comparisons to prior audit, list of triggered safeguards with threshold data, structural recommendations, publication date and scope, and next audit due date. The report is accessible to all ecosystem members within the audit scope and cannot be restricted to leadership.

## G. Authority Boundary Check

- **Any ecosystem member** (with 3 co-signers) can request an audit within their ETHOS's domain
- **The audit team** has authority to access governance data within the defined scope but cannot access data outside the domain boundary established by domain-mapping
- **No individual or body** can suppress, delay, or redact an audit report -- suppression attempts are logged as governance health events
- **The audit team** produces data and recommendations, never directives -- they cannot mandate governance changes
- **Leadership of the audited body** cannot appoint the audit team, serve on the audit team, or approve the report before publication
- **OSC** receives all audit reports but does not gate their publication
- Authority scopes are formally defined by the domain-mapping and role-assignment skills (Layer II)

## H. Capture Resistance Check

**Capital capture.** The audit measures resource concentration directly (indicator GHI-03). A funding source that provides more than 30% of resources triggers a warning, and more than 50% triggers critical status. The audit team cannot be funded by the body being audited -- their participation is a governance contribution, not a paid engagement. Funding sources cannot condition contributions on audit outcomes or suppress unfavorable findings.

**Charismatic capture.** The audit measures proposal authorship diversity (GHI-01) and approval rate equity (GHI-02), both of which degrade when a single personality dominates governance. The structural separation between data collection (independent monitor) and data interpretation (audit team) prevents a charismatic leader from influencing the narrative. The audit team must include participants from outside the audited body's immediate social network when possible.

**Emergency capture.** Post-emergency audits are mandatory (triggered within 30 days of emergency conclusion). The audit examines whether emergency authority was returned after the crisis and whether emergency declarations increased in frequency -- both indicators of emergency capture as documented in Layer VIII interaction.

**Informal capture.** The audit's indicator framework makes governance patterns visible that would otherwise remain informal. Declining participation, narrowing proposal authorship, and rising leadership tenure are all measurable even when no formal rule has been broken. The audit converts invisible degradation into documented evidence.

## I. Failure Containment Logic

- **Data unavailable**: if the independent monitor has not produced a Governance Data Report for the audit period, the audit team documents the gap, escalates to the OSC for monitor accountability review, and conducts the audit with available data while noting limitations
- **Audit team cannot be formed**: if no qualified non-leadership participants are available, the audit draws from adjacent ETHOS or, as a last resort, the OSC appoints temporary auditors from outside the ecosystem
- **Indicator scoring disagreement**: if audit team members disagree on an indicator score, both assessments are recorded in the report with the reasoning for each -- the report does not suppress minority interpretations
- **Report suppression attempted**: the suppression attempt itself is recorded as a critical governance event, the report is published through alternative channels (direct to ecosystem members), and the suppression is flagged in the next audit
- **Stale or manipulated data**: if the audit team suspects data integrity issues, they document the concern, request a data verification process through the independent-monitoring skill, and publish the report with integrity caveats

## J. Expiry / Review Condition

Governance Health Reports do not expire -- they are historical records. The audit schedule itself is reviewed annually by the audited body through the ACT process. The minimum audit frequency is semi-annual; no body can consent to eliminate audits entirely. If a scheduled audit is missed, an automatic escalation notice is sent to all ecosystem members within the scope and to the OSC. The audit schedule resumes at the next quarter boundary. Indicator definitions and thresholds in `assets/indicator-definitions.yaml` are reviewed annually and updated through the ACT consent process.

## K. Exit Compatibility Check

When a participant who served on an audit team exits the ecosystem, their past audit contributions remain part of the published record -- audit reports are not retracted. If the exiting participant is a currently appointed auditor mid-cycle, the remaining team continues and a replacement is appointed through the role-assignment skill. If the exiting participant was the sole auditor, a new audit team is appointed before the current cycle's report is due. Exiting participants retain no ongoing obligation related to audit findings, but their data contributions during the audit period remain in the published reports.

## L. Cross-Unit Interoperability Impact

Audit reports for one ETHOS are published to all ecosystem members, not just that ETHOS's members, enabling cross-unit visibility into governance health. When an ecosystem-wide audit is conducted, all ETHOS provide data through their independent monitors. Cross-ETHOS comparison is informational, not competitive -- reports note structural differences between ETHOS that affect indicator scores (e.g., a new ETHOS may have lower cross-unit engagement simply because it has fewer established relationships). When two NEOS ecosystems federate (Layer V, deferred), governance health audit protocols may be shared to enable cross-ecosystem transparency, but audit authority remains scoped to each ecosystem's domain.
