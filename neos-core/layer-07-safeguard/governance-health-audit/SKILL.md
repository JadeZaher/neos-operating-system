---
name: governance-health-audit
description: "Conduct a structured, quantified review of governance health indicators across an ETHOS or ecosystem -- run this whenever decision patterns, participation, or resource flows need independent assessment."
layer: 7
version: 0.1.0
depends_on: [agreement-registry, domain-mapping, role-assignment]
---

# governance-health-audit

## A. Structural Problem It Solves

Governance systems degrade invisibly. Decision-making concentrates, participation narrows, objections disappear, and leadership calcifies -- all while formal rules remain unchanged on paper. Robert Michels documented this as the Iron Law of Oligarchy: every organization trends toward power concentration unless structurally resisted. Without a measurable, periodic health check, ecosystems cannot distinguish between healthy governance and governance that has been quietly captured. This skill provides the structural discipline of quantified governance assessment, turning subjective impressions into indicator-based evidence that the entire ecosystem can see, interpret, and act on.

## B. Domain Scope

This skill applies to any ETHOS or the full ecosystem where governance decisions are made and recorded. The audit examines decision logs, resource allocation records, participation records, proposal registries, and role-assignment histories. It operates within the boundary defined by the domain-mapping skill (Layer II) -- an audit of the Bali SHUR ETHOS examines only Bali SHUR governance data, not the entire OmniOne ecosystem, unless the scope is explicitly set to ecosystem-wide. Out of scope: the audit does not interpret data into capture diagnoses (that is the capture-pattern-recognition skill) and does not design or activate safeguards (that is the safeguard-trigger-design skill).

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

## OmniOne Walkthrough

It is the end of Q1 2026, and the Bali SHUR ETHOS is due for its quarterly governance health audit. Lina, an AE member, initiates the audit request along with three TH co-signers: Dewa, Sari, and Tomasz. The scope is confirmed as "SHUR Bali" via the domain-mapping registry, covering all governance activity from January through March 2026.

The audit team is appointed: Farid, a TH member who does not hold any leadership role in SHUR Bali, and Yuki, an AE member from the SHUR Costa Rica ETHOS who volunteered for cross-unit audit service. Neither Farid nor Yuki reports to or socializes primarily with SHUR Bali leadership, satisfying the independence requirement.

Farid and Yuki receive the Q1 Governance Data Report from Ratu, the current independent monitor for SHUR Bali. The report contains raw data on all 8 indicators. They score each indicator against the thresholds in `assets/indicator-definitions.yaml`:

- **GHI-01 Proposal Authorship Diversity**: 12 unique authors out of 28 proposals = 43%. Status: **warning** (threshold: 40-59%).
- **GHI-02 Approval Rate by Author Role**: Non-leadership approval rate 72%, leadership approval rate 88%. Ratio: 0.82. Status: **healthy**.
- **GHI-03 Resource Concentration Index**: GEV provides 35% of SHUR Bali resources. Status: **warning** (threshold: 30-49%).
- **GHI-04 Participation Trend**: Average participation down 3% from Q4 2025. Status: **healthy**.
- **GHI-05 Leadership Tenure**: Circle steward Ketut has served 3 consecutive cycles. Status: **warning** (threshold: 3 cycles).
- **GHI-06 Objection Integration Rate**: 8 of 11 objections resulted in proposal modification = 73%. Status: **healthy**.
- **GHI-07 Review Compliance Rate**: 14 of 18 agreements reviewed on time = 78%. Status: **warning** (threshold: 60-84%).
- **GHI-08 Cross-Unit Engagement**: 5 cross-circle interactions this quarter. Status: **healthy**.

Farid and Yuki note that GHI-01 and GHI-05 are both in warning territory and trending in the same direction -- a small group is authoring most proposals and the same person keeps leading. They cross-reference the safeguard trigger registry and find that the "proposal concentration" trigger threshold is 35% or fewer unique authors. At 43%, it has not fired, but the trend is concerning.

**Edge case**: During compilation, Yuki discovers that 3 proposals were submitted by an AE member who resigned mid-quarter. Should those proposals count? The team decides yes -- the audit measures governance patterns during the period, and removing data from departed members would distort the record. They note the resignation in the report context.

The team compiles the Governance Health Report (GHR-SHUR-2026-Q1), recording overall health as "mixed" (4 healthy, 4 warning, 0 critical). They recommend initiating a structural-diversity-maintenance review for proposal authorship and flagging Ketut's leadership tenure for the next role-assignment review. The report is published to all 38 SHUR Bali members and to the OSC on April 3, 2026. Next audit: July 2026.

## Stress-Test Results

### 1. Capital Influx

A tech philanthropist offers OmniOne $2 million in annual funding, channeled primarily through the Bali SHUR ETHOS, contingent on SHUR adopting the funder's proprietary sustainability curriculum. The next quarterly governance health audit detects the shift immediately: GHI-03 (Resource Concentration Index) jumps from 35% to 68%, crossing into critical territory. The audit team documents the concentration, notes the conditional nature of the funding, and flags the associated safeguard trigger for capital capture. The audit report is published to all ecosystem members, making the funding dependency visible to everyone -- not just leadership who negotiated the deal. The report recommends activating the capital capture safeguard trigger and initiating a funding diversification campaign through structural-diversity-maintenance. Because the audit team is structurally independent of SHUR leadership (who may have been involved in the funding negotiation), the report cannot be softened or delayed to protect the relationship. The philanthropist's representatives cannot suppress or modify the audit findings.

### 2. Emergency Crisis

A volcanic eruption near the Bali SHUR location forces emergency evacuation and temporary suspension of normal governance processes for six weeks. During the emergency, a small leadership group makes rapid resource allocation decisions under emergency authority (Layer VIII). Once the emergency concludes, the mandatory post-emergency audit triggers within 30 days. The audit team examines the emergency period's governance data: How many decisions were made under emergency authority? Were emergency declarations properly scoped? Was authority returned to normal processes after the crisis? The audit finds that 14 decisions were made under emergency authority, all properly documented, but that 3 decisions extended beyond the original emergency scope (facility improvements unrelated to evacuation). These scope extensions are flagged as warning indicators for emergency capture. The audit report recommends a review of the 3 out-of-scope decisions through normal ACT process. Critically, the compressed emergency timeline did not suspend the audit obligation -- it merely delayed it until conditions permitted safe assembly.

### 3. Leadership Charisma Capture

A beloved founding member of OmniOne, Surya, has been the de facto leader of SHUR Bali for three years. Surya is warm, visionary, and deeply respected -- and Surya's proposals pass without modification 95% of the time. The quarterly audit captures this pattern through multiple indicators: GHI-02 (Approval Rate by Author Role) shows a ratio of 0.58 because Surya's proposals pass at 98% while other members' proposals pass at 57%. GHI-05 (Leadership Tenure) shows Surya at 6 consecutive cycles, well into critical territory. GHI-06 (Objection Integration Rate) shows that objections to Surya's proposals are withdrawn before integration rounds 80% of the time -- a pattern invisible without data. The audit team documents these patterns without accusing Surya of wrongdoing -- the indicators describe structural conditions, not intentions. The report publishes to all members, making the pattern visible. Because the audit team was appointed independently (Surya had no role in their selection), and because the data came from the independent monitor (not from anyone Surya could influence), the charisma capture pattern is documented through structure, not through the social courage of any individual challenger.

### 4. High Conflict / Polarization

Two factions within SHUR Bali are deeply divided over whether to accept a corporate partnership for land development. Faction A sees economic sustainability; Faction B sees a betrayal of regenerative principles. Both factions attempt to influence the audit by lobbying the audit team to interpret indicators in ways that support their position. The audit's structural design resists this: the audit team scores indicators using predefined thresholds from `assets/indicator-definitions.yaml`, not subjective assessments. The data shows declining participation (GHI-04 at -18%, nearing critical) and reduced objection integration (GHI-06 at 45%, warning) -- both signs that the polarization is degrading governance health regardless of which faction is "right." The audit report documents the governance health degradation without taking sides on the substantive issue. It recommends GAIA Level 4 coaching to address the underlying polarization and notes that declining participation means fewer voices are shaping decisions. The audit serves as a neutral mirror, reflecting governance health data that both factions can reference without the data itself becoming a weapon for either side.

### 5. Large-Scale Replication

OmniOne grows from 50 members in one SHUR location to 4,000 members across 12 SHUR locations and 60 circles. The governance health audit scales through domain-scoped execution: each ETHOS conducts its own quarterly audit with its own audit team and independent monitor. Indicator definitions and thresholds remain consistent across all locations (the same `indicator-definitions.yaml`), enabling meaningful comparison without requiring centralized audit authority. The OSC receives all audit reports and can identify systemic patterns -- if 8 of 12 locations show declining proposal authorship diversity, that signals an ecosystem-level structural issue rather than a local anomaly. Audit teams are drawn from the local participant pool with cross-ETHOS members when needed, scaling the auditor supply with the participant base. The audit report template remains identical at every scale; what changes is the volume of data and the number of parallel audits running each quarter. A meta-audit at the ecosystem level aggregates ETHOS-level reports annually.

### 6. External Legal Pressure

The Indonesian government requires all co-living operations to submit annual governance reports to a regulatory body. A government liaison suggests that the SHUR Bali governance health audit could serve as the compliance report if "sensitive internal metrics" are redacted. The audit skill's publication requirement prevents selective redaction: the full report goes to all ecosystem members. However, the ecosystem can produce a separate compliance summary derived from the audit data, containing only information required by the regulator. The audit itself is not modified for external consumption. The UAF sovereignty principle holds: external legal requirements are met through additional documentation, not by compromising the internal governance health audit's completeness or transparency. Individual members comply with local laws as individuals; the ecosystem's audit process is governed by its own agreements, not by external mandates. The audit documents the regulatory pressure as context so future audits can track whether external compliance requirements are influencing internal governance decisions.

### 7. Sudden Exit of 30% of Participants

Following a contentious OSC decision to restructure ETHOS boundaries, 12 of 38 SHUR Bali members exit within two weeks. The mass exit trigger (20% threshold) fires immediately, initiating an automatic governance health audit outside the normal quarterly schedule. The audit reveals cascading indicator impacts: GHI-01 (Proposal Authorship Diversity) drops to critical as several active proposers departed. GHI-04 (Participation Trend) shows a -35% decline, deep in critical territory. GHI-07 (Review Compliance Rate) degrades because several agreement stewards left without completing scheduled reviews. The audit team recalibrates quorum calculations to the current 26-member base and identifies 7 agreements where departed members constituted more than 25% of affected parties, flagging each for review through the agreement-review skill. The audit report documents the governance health impact of the mass exit and recommends immediate structural interventions: proposal encouragement for remaining members (via structural-diversity-maintenance), emergency stewardship reassignment for orphaned agreements, and a community dialogue to address the underlying grievance that caused the exodus. Existing governance structures remain valid -- the audit confirms that prior decisions were legitimately made and are not retroactively invalidated by departures.
