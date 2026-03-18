---
name: capture-pattern-recognition
description: "Analyze governance health data for the four capture types -- capital, charisma, emergency, ossification -- and produce an evidence-based Capture Assessment Report with confidence scores and recommended responses."
layer: 7
version: 0.1.0
depends_on: [governance-health-audit, domain-mapping]
---

# capture-pattern-recognition

## A. Structural Problem It Solves

Governance capture rarely announces itself. A funding source quietly becomes indispensable. A charismatic leader accumulates unchallenged influence. Emergency authority silently becomes permanent. Leadership calcifies while formal rotation rules stay on the books. Robert Michels documented the Iron Law of Oligarchy: organizations trend toward power concentration unless structurally resisted. Raw governance health data (produced by the governance-health-audit skill) reveals symptoms, but symptoms require interpretation through known capture signatures to become actionable diagnoses. Without a structured pattern-matching framework, ecosystems either miss capture entirely or respond to subjective impressions with accusations that damage trust. This skill converts raw indicators into specific, evidence-based capture pattern diagnoses with measurable confidence levels -- turning "something feels off" into "capital concentration has crossed the warning threshold for two consecutive quarters with a medium confidence score."

## B. Domain Scope

This skill applies wherever a governance-health-audit has produced indicator data -- any ETHOS or the full ecosystem. The analysis examines the same governance data as the audit (decision logs, resource allocation records, participation records, proposal registries, role-assignment histories) but interprets it through capture-type signature lenses rather than individual indicator thresholds. The domain boundary follows the domain-mapping skill (Layer II): a capture assessment of SHUR Bali examines only SHUR Bali data. Out of scope: this skill diagnoses capture patterns but does not design or activate safeguard responses (that is the safeguard-trigger-design skill) and does not collect raw data (that is the independent-monitoring skill). The skill explicitly does not assign blame to individuals -- it identifies structural conditions, not personal intentions.

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

When a participant who served on an assessment team exits the ecosystem, their contributions remain in published reports. If the exiting participant is a currently appointed assessor mid-cycle, the remaining team continues and a replacement is appointed via role-assignment. If a participant whose behavior contributed to a capture pattern exits, the structural conditions documented in the assessment remain valid -- capture is about system patterns, not individual presence. Exiting participants retain no ongoing obligation related to assessment findings. The 30-day wind-down period applies to any in-progress assessment participation.

## L. Cross-Unit Interoperability Impact

Capture Assessment Reports for one ETHOS are published to all ecosystem members, enabling cross-unit visibility into capture risks. When correlated indicator degradation appears across multiple ETHOS, an ecosystem-level assessment aggregates ETHOS-level findings. Cross-ETHOS comparisons are informational, not competitive -- structural differences between ETHOS (size, age, domain complexity) affect capture risk profiles. When two NEOS ecosystems federate (Layer V, deferred), capture assessment protocols may be shared to enable cross-ecosystem pattern detection, but assessment authority remains scoped to each ecosystem's domain. A capture pattern detected in one ETHOS may prompt preventive assessments in structurally similar ETHOS.

## OmniOne Walkthrough

It is April 2026, and the Q1 Governance Health Report for OmniOne's Bali SHUR ETHOS has just been published. Three indicators are at warning: GHI-01 (Proposal Authorship Diversity at 43%), GHI-05 (Leadership Tenure at 3 cycles for steward Ketut), and GHI-02 (Approval Rate by Author Role showing a new pattern around OSC member Surya, whose proposals pass at 96% while the general approval rate is 71%). Lina, an AE member, requests a capture assessment with co-signers Dewa, Sari, and Tomasz, specifying "potential charisma capture" as the concern.

The assessment team is appointed: Farid, a TH member with no leadership role in SHUR Bali, and Yuki, an AE member from SHUR Costa Rica who served on the recent governance health audit. Neither reports to Surya or sits in Surya's social circle.

Farid and Yuki screen all four capture types against the Q1 data:

**Capital capture**: GHI-03 at 35% (warning but stable). No conditional funding patterns detected. Confidence: **Low**. Benign explanation: GEV's funding share is structural to the project's early stage.

**Charisma capture**: GHI-02 shows Surya's proposals pass at 96% vs. 71% general rate (ratio: 0.74, warning). GHI-06 reveals that 4 of 5 objections to Surya's proposals were withdrawn before integration (80% withdrawal rate, against a 27% withdrawal rate for other proposers). GHI-01 is at warning but not specific to Surya. Two indicators at warning with a distinctive withdrawal pattern. Confidence: **Medium**. Benign explanation evaluated: Surya may simply write better proposals. However, the objection withdrawal disparity is not explained by proposal quality -- it suggests social pressure. Benign explanation rated "partial, insufficient to reduce confidence."

**Emergency capture**: No emergency declarations in the audit period. Confidence: **Low**.

**Ossification capture**: GHI-05 at 3 cycles for Ketut (warning). Single indicator, trend stable. Confidence: **Low**. Benign explanation: Ketut is the only qualified candidate during a transition period. Rated "plausible but requires monitoring."

**Edge case**: During analysis, Yuki notes that Surya recently mentored 4 new TH members who all voted to support Surya's latest proposal. Is mentorship a charisma capture vector or a healthy community investment? The team documents this as a "structural ambiguity" -- mentorship is positive, but if mentees consistently defer to their mentor in governance, it creates a dependency pattern. They recommend monitoring mentee voting independence as an additional indicator for the next audit cycle.

Farid and Yuki compile the Capture Assessment Report (CAR-SHUR-2026-Q1). For charisma capture (medium confidence), they recommend activating the "objection withdrawal monitoring" safeguard trigger and initiating a structural-diversity-maintenance review focused on proposal authorship. They explicitly note: "This assessment describes structural conditions. It is not an accusation against any individual. Surya's contributions to the ecosystem are not in question; the governance pattern around Surya's proposals warrants structural attention." The report is published to all 38 SHUR Bali members and the OSC on April 12, 2026.

## Stress-Test Results

### 1. Capital Influx

A venture foundation offers OmniOne $3 million annually, channeled through SHUR Bali, contingent on adopting the foundation's impact measurement framework for all project evaluations. The next capture assessment screens capital capture indicators: GHI-03 (Resource Concentration) jumps from 35% to 72%, deep in critical territory. The assessment team also examines proposal patterns and discovers that since the funding announcement, 4 proposals related to the funder's framework passed with zero objections, while 2 proposals for alternative frameworks were tabled without discussion. This creates a secondary indicator: funding-conditional proposal bias. The team scores capital capture at high confidence -- two critical indicators with a causal mechanism visible in the decision logs. Benign explanation evaluated: the foundation's framework may genuinely be superior. However, the absence of any comparative discussion and the correlation between funding and approval patterns weaken this explanation. The assessment recommends immediate activation of the capital capture safeguard trigger and a funding diversification campaign through structural-diversity-maintenance. The report is published to all members, making the dependency pattern visible even to members who were not aware of the funding conditions. The venture foundation cannot suppress or modify the assessment.

### 2. Emergency Crisis

A severe flooding event forces SHUR Bali to operate under emergency authority for eight weeks. A small leadership group makes 22 rapid decisions during the emergency. When conditions stabilize, the mandatory post-emergency capture assessment examines emergency capture indicators: declaration frequency (1 event, not elevated), scope creep (5 of 22 decisions extended beyond immediate flood response into long-term infrastructure planning), and authority return timeline (emergency authority was formally returned 3 weeks after conditions normalized, with leadership citing "ongoing instability"). The team scores emergency capture at medium confidence -- scope creep and delayed authority return are both warning indicators, and the "ongoing instability" justification is subjective rather than tied to measurable conditions. Benign explanation evaluated: infrastructure decisions during an emergency may have been genuinely urgent. The team rates this "partially plausible" because some infrastructure decisions were time-sensitive but others could have waited for normal ACT process. The assessment recommends activating the emergency scope review trigger and initiating normal ACT process for the 5 out-of-scope decisions. The compressed emergency timeline did not suspend the assessment obligation -- it simply delayed it until safe assembly was possible.

### 3. Leadership Charisma Capture

Arjuna, a founding member of OmniOne and beloved community figure, has served on the OSC for five consecutive cycles. Arjuna's proposals pass at 97% with minimal modification. When a new TH member, Mei, raises an objection to one of Arjuna's proposals, three other members privately message her suggesting she "trust the process" and withdraw. The capture assessment detects this through multiple indicators: GHI-02 shows a 0.52 ratio (critical), GHI-05 shows 5 consecutive cycles (critical), GHI-06 shows that objections to Arjuna's proposals are withdrawn at 85% vs. 30% for others. The team scores charisma capture at high confidence -- three indicators in critical territory with a degrading trend over four quarters. The benign explanation that "Arjuna simply makes good proposals" cannot account for the objection withdrawal disparity, which indicates social pressure rather than proposal quality. The assessment explicitly notes that this is not a judgment of Arjuna's character -- it describes structural conditions around Arjuna's role that have created an environment where dissent is suppressed. The recommendation activates the leadership review trigger and recommends structural interventions to normalize objection-raising. Because the assessment team was appointed independently of Arjuna and worked from independently collected data, the social pressure that silenced Mei cannot silence the structural assessment.

### 4. High Conflict / Polarization

Two factions within SHUR Bali are polarized over accepting a cryptocurrency-based donation system. Faction A sees financial innovation; Faction B sees ideological compromise. Both factions request capture assessments targeting the other -- Faction A claims Faction B is engaged in "ossification capture" by blocking innovation, while Faction B claims Faction A is enabling "capital capture" by corporate crypto interests. The assessment team screens both claims against measurable indicators. For capital capture: no external crypto entity has provided funding, no conditional donations exist, GHI-03 is stable. Confidence: low. For ossification capture: leadership has rotated on schedule, proposal diversity is healthy, GHI-05 is in healthy range. Confidence: low. The real governance health issue is declining participation (GHI-04 at -22%, critical) and degraded objection integration (GHI-06 at 38%, critical) -- both signs that polarization is suppressing governance health regardless of which faction is "right." The assessment documents the governance degradation without validating either faction's capture narrative, recommends GAIA Level 4 coaching to address the underlying conflict, and notes that weaponized capture claims that lack indicator evidence should be redirected to conflict resolution (Layer VI). The assessment serves as a structural mirror, reflecting measurable governance health data rather than amplifying either faction's accusations.

### 5. Large-Scale Replication

OmniOne scales from 50 members in one location to 5,000 members across 15 SHUR locations and 80 circles. Capture assessment scales through domain-scoped execution: each ETHOS conducts its own assessments based on its own audit data. The capture signature definitions in `assets/capture-assessment-template.yaml` remain consistent across all locations, enabling meaningful cross-ETHOS comparison. The OSC reviews all capture assessments and identifies systemic patterns -- if 10 of 15 locations show medium or high confidence for the same capture type, that signals an ecosystem-level structural vulnerability rather than local anomalies. Assessment teams are drawn from local participant pools with cross-ETHOS members when needed, scaling assessor supply with the participant base. At ecosystem scale, a meta-assessment annually aggregates ETHOS-level findings. The assessment template remains identical at every scale; what changes is the volume of data, the number of parallel assessments, and the importance of cross-ETHOS pattern detection. No single assessment team needs to understand the entire ecosystem -- each works within its domain boundary.

### 6. External Legal Pressure

Indonesian regulatory authorities request access to OmniOne's internal governance assessments as part of a compliance review for co-living operations. A government liaison suggests that capture assessment language be "softened" to avoid regulatory misinterpretation. The capture assessment skill's publication requirement prevents selective editing: the full report goes to all ecosystem members as written. However, the ecosystem can produce a separate compliance summary that translates structural governance terminology into regulatory language without modifying the internal assessment. The assessment itself is not altered for external consumption. The UAF sovereignty principle holds: external legal requirements are met through additional documentation, not by compromising capture assessment integrity. The assessment team documents the regulatory pressure as context so future assessments can track whether external compliance requirements are influencing internal governance patterns -- regulatory pressure that causes self-censorship in capture reporting is itself a form of capture. Individual members comply with local laws as individuals; the ecosystem's assessment process is governed by its own agreements.

### 7. Sudden Exit of 30% of Participants

Following a contentious OSC decision to restructure ETHOS boundaries, 14 of 42 SHUR Bali members exit within three weeks. The mass exit triggers both an automatic governance health audit and a subsequent capture assessment. The assessment reveals compounding indicators: GHI-01 drops to critical as several active proposers departed, GHI-04 shows -33% participation decline (critical), and GHI-05 shows that the leadership structure is unchanged despite losing a third of the community (ossification indicator). The team evaluates all four capture types. Ossification capture scores medium -- leadership unchanged through a crisis that demanded structural adaptation. Capital capture scores low. Charisma capture scores low -- the departures were not caused by a personality but by a structural decision. Emergency capture scores low. The assessment recommends activating the ossification safeguard trigger and initiating leadership rotation review. It documents that the mass exit has reduced the participant base below the threshold where current governance structures are proportionate -- 5 circles for 28 remaining members may need consolidation. Existing capture assessments remain valid historical records. The assessment recalibrates its baseline to the current participant count and recommends more frequent monitoring (monthly rather than quarterly) until membership stabilizes.
