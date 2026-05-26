---
name: capture-pattern-recognition
description: "Analyze governance health data for the four capture types -- capital, charisma, emergency, ossification -- and produce an evidence-based Capture Assessment Report with confidence scores and recommended responses."
layer: 7
version: 0.1.0
depends_on: [governance-health-audit, domain-mapping]
---

# capture-pattern-recognition

## C. Trigger Conditions

- **Post-audit analysis**: automatically triggered when a Governance Health Report contains any indicator at warning or critical status
- **Scheduled review**: quarterly, following each governance-health-audit cycle (configurable per ETHOS, minimum semi-annual)
- **Participant concern**: any ecosystem member requests a capture assessment with 3 co-signers, specifying the suspected capture type and the evidence prompting the concern
- **Safeguard trigger activation**: when any safeguard trigger fires (per safeguard-trigger-design), a capture assessment is initiated to determine whether the trigger reflects a genuine capture pattern or an isolated anomaly
- **Cross-audit pattern**: when two or more ETHOS show correlated indicator degradation in the same quarter, an ecosystem-level capture assessment is triggered

## D. Required Inputs

- **Governance Health Report**: the most recent audit report for the scope, including all 8 indicator scores and trends (from governance-health-audit)
- **Historical audit data**: prior Governance Health Reports for the same scope (minimum 2 quarters for trend analysis; if unavailable, note as "insufficient baseline")
- **Capture signature definitions**: the 4 capture type profiles with their indicator signatures from `assets/capture-assessment-template.yaml`
- **Contextual data**: any ecosystem events that may explain indicator changes without capture (e.g., planned leadership transition, fundraising campaign, seasonal participation dip)
- **Prior capture assessments**: previous Capture Assessment Reports for the same scope, if any, for pattern continuity tracking
- **Safeguard trigger registry**: current active triggers and their activation history (from safeguard-trigger-design)

## E. Step-by-Step Process

1. **Confirm assessment scope and authority.** The assessment initiator specifies the scope (ETHOS or ecosystem) and confirms authority within the domain via domain-mapping. The initiator does not conduct the assessment -- separation of request and analysis prevents motivated interpretation.
2. **Appoint assessment team.** The team consists of at least two participants who do not hold leadership roles within the assessed scope. At least one team member must have completed a prior governance-health-audit within the ecosystem. Appointment follows the role-assignment skill.
3. **Gather inputs.** The team collects the current and historical Governance Health Reports, contextual data from ecosystem records, and the current safeguard trigger registry. The team does not collect raw data -- they work from published audit reports and independent monitor data.
4. **Screen each capture type.** For each of the four capture types (capital, charisma, emergency, ossification), the team evaluates the relevant indicator subset against the capture signature defined in `assets/capture-assessment-template.yaml`. Each capture type has 3 or more signature indicators with specific thresholds.
5. **Score confidence.** For each capture type, assign a confidence score: **Low** (1 indicator at warning, others healthy, benign explanation plausible), **Medium** (2+ indicators at warning or 1 at critical, trend is degrading, benign explanation weakened), **High** (2+ indicators at critical or 3+ at warning with degrading trend across 2+ quarters, benign explanations insufficient). Record the specific evidence supporting the score.
6. **Evaluate benign explanations.** For every indicator that contributes to a medium or high confidence score, the team documents at least one plausible benign explanation and evaluates whether it accounts for the data. If a benign explanation fully accounts for the indicator, the confidence score is reduced by one level. This step prevents false positives from becoming accusations.
7. **Cross-reference capture types.** Evaluate whether multiple capture types are co-occurring (e.g., capital capture enabling charisma capture). Document any interactions between capture patterns.
8. **Draft recommendations.** For each capture type scoring medium or high, recommend specific safeguard activations by reference to the safeguard-trigger-design skill. Recommendations are advisory and structural -- they reference specific triggers to activate, not individuals to blame.
9. **Compile the Capture Assessment Report.** Assemble the report using `assets/capture-assessment-template.yaml`, including all four capture type evaluations, confidence scores, evidence summaries, benign explanation evaluations, cross-type interactions, and recommendations.
10. **Publish to all ecosystem members.** The report is published to everyone within the assessment scope and to the OSC. Publication cannot be suppressed by the body being assessed. Any suppression attempt is logged as a critical governance health event and itself triggers a high-confidence indicator for the relevant capture type.

## F. Output Artifact

A Capture Assessment Report following `assets/capture-assessment-template.yaml`. The report contains: report ID, assessment scope, assessment period, assessor identities, source Governance Health Report references, and for each of the four capture types: relevant indicator scores with measured values, capture signature match evaluation, confidence score (low/medium/high), contributing evidence summary, benign explanation evaluation, and recommended safeguard activations. The report also includes a cross-type interaction analysis and an overall capture risk summary. The report is accessible to all ecosystem members within the assessment scope and cannot be restricted to leadership.

## G. Authority Boundary Check

- **Any ecosystem member** (with 3 co-signers) can request a capture assessment within their ETHOS's domain
- **The assessment team** interprets published governance data but cannot access raw data outside the domain boundary established by domain-mapping
- **No individual or body** can suppress, delay, or redact a Capture Assessment Report -- suppression attempts are logged as governance health events
- **The assessment team** produces diagnoses and recommendations, never directives -- they cannot mandate governance changes or remove individuals from roles
- **Leadership of the assessed body** cannot appoint the assessment team, serve on the team, or approve the report before publication
- **Capture assessments do not constitute accusations** -- they describe structural conditions. Any participant who uses a capture assessment to pursue personal grievances rather than structural remedies is referred to conflict resolution (Layer VI)

## H. Capture Resistance Check

**Capital capture.** The assessment examines resource concentration (GHI-03), funding-conditional proposal patterns, and self-censorship indicators. The assessment team cannot be funded by the body being assessed. A capital capture confidence score requires measurable threshold crossings, not subjective impressions about funder influence. The skill prevents capital interests from suppressing unfavorable findings by mandating publication to all members.

**Charismatic capture.** The assessment examines approval rate disparity (GHI-02), objection withdrawal patterns (GHI-06), and proposal authorship concentration (GHI-01). The structural separation between data collection (independent monitor), data interpretation (audit team), and pattern analysis (assessment team) creates three layers of independence that no single personality can dominate. The skill requires evidence-based thresholds, preventing charismatic leaders from dismissing assessments as "jealousy" or "political."

**Emergency capture.** The assessment examines emergency declaration frequency, scope creep patterns, and post-emergency authority return timelines. It cross-references Layer VIII emergency records to determine whether emergency powers are being routinely invoked or retained beyond their stated scope. The assessment team operates outside emergency authority chains.

**Informal capture.** The assessment's four-type framework makes capture patterns visible that would otherwise remain informal. The requirement for measurable indicators and specific thresholds prevents the assessment itself from becoming an informal power tool -- you cannot "capture assess" someone based on a feeling.

## I. Failure Containment Logic

- **Insufficient data**: if fewer than 2 quarters of Governance Health Reports exist, the assessment proceeds as a "baseline capture scan" with all confidence scores capped at low, noting the data limitation
- **Assessment team cannot be formed**: if no qualified non-leadership participants are available, the assessment draws from adjacent ETHOS or, as a last resort, the OSC appoints temporary assessors from outside the ecosystem
- **Disagreement on confidence scores**: if team members disagree, both assessments are recorded with reasoning -- the report does not suppress minority interpretations
- **Benign explanation dispute**: if the team cannot agree on whether a benign explanation is sufficient, the higher confidence score is published with the disagreement documented
- **Weaponization attempt**: if a capture assessment is requested to target a specific individual rather than investigate structural conditions, the assessment team documents the concern, proceeds with structural analysis only, and refers the interpersonal conflict to Layer VI
- **Report suppression attempted**: the suppression is itself recorded as high-confidence evidence for the relevant capture type, and the report is published through alternative channels

## J. Expiry / Review Condition

Capture Assessment Reports do not expire -- they are historical records of structural conditions at a point in time. The assessment methodology (capture signatures and thresholds in `assets/capture-assessment-template.yaml`) is reviewed annually through the ACT consent process. If a capture type scores high for two consecutive assessments and no safeguard has been activated, the assessment automatically escalates to the OSC for structural review. Assessment frequency follows the governance-health-audit schedule by default (quarterly). Confidence scores from prior assessments inform but do not predetermine future scores -- each assessment evaluates current data independently.

## K. Exit Compatibility Check

When a participant who served on an assessment team exits the ecosystem, their contributions remain in published reports. If the exiting participant is a currently appointed assessor mid-cycle, the remaining team continues and a replacement is appointed via role-assignment. If a participant whose behavior contributed to a capture pattern exits, the structural conditions documented in the assessment remain valid -- capture is about system patterns, not individual presence. Exiting participants retain no ongoing obligation related to assessment findings.

## L. Cross-Unit Interoperability Impact

Capture Assessment Reports for one ETHOS are published to all ecosystem members, enabling cross-unit visibility into capture risks. When correlated indicator degradation appears across multiple ETHOS, an ecosystem-level assessment aggregates ETHOS-level findings. Cross-ETHOS comparisons are informational, not competitive -- structural differences between ETHOS (size, age, domain complexity) affect capture risk profiles. When two NEOS ecosystems federate (Layer V, deferred), capture assessment protocols may be shared to enable cross-ecosystem pattern detection, but assessment authority remains scoped to each ecosystem's domain. A capture pattern detected in one ETHOS may prompt preventive assessments in structurally similar ETHOS.
