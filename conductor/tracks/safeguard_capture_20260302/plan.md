# Implementation Plan: Safeguard & Capture Detection (Layer VII)

## Overview

This plan builds 5 governance skills for Layer VII plus layer-level integration, organized into 4 phases. The build order starts with the diagnostic foundation (governance health audit), moves to analytical skills (capture pattern recognition, safeguard triggers), then to supporting infrastructure (independent monitoring, structural diversity maintenance), and concludes with layer integration and cross-layer verification.

**Total skills:** 5
**Total phases:** 4
**Estimated scope:** 20-28 hours of focused implementation

### Build Order Rationale

Governance health audit is the anchor skill -- it defines what indicators exist and how they are measured. Capture pattern recognition depends on those indicators to match signatures. Safeguard trigger design depends on both (indicators to monitor, patterns to detect). Independent monitoring defines who collects the data that feeds audits. Structural diversity maintenance is the proactive complement and is built last because it references all other skills' outputs.

### Commit Strategy

- One commit per completed skill: `neos(layer-07): Add <skill-name> skill`
- Layer-level commit: `neos(layer-07): Complete layer 07 - Safeguard & Capture Detection`

---

## Phase 1: Scaffolding and Anchor Skill

**Goal:** Create the Layer VII directory structure and build the anchor skill (governance-health-audit) that defines the indicator framework all other skills depend on.

### Tasks

- [ ] **Task 1.1: Create Layer VII directory scaffolding**
  Create the full directory tree:
  ```
  neos-core/
    layer-07-safeguard/
      README.md (empty placeholder)
      governance-health-audit/   (SKILL.md, assets/, references/, scripts/)
      capture-pattern-recognition/ (same structure)
      safeguard-trigger-design/    (same structure)
      independent-monitoring/      (same structure)
      structural-diversity-maintenance/ (same structure)
  ```
  Each skill directory gets empty `SKILL.md`, empty `assets/`, `references/`, and `scripts/` subdirectories.
  **Acceptance:** All directories exist. `find neos-core/layer-07-safeguard -name SKILL.md | wc -l` returns 5.

- [ ] **Task 1.2: Draft governance-health-audit SKILL.md -- sections A through F**
  Using the SKILL_TEMPLATE.md, fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without structured governance health measurement, capture and degradation are invisible until crisis. This skill makes governance health quantifiable, comparable over time, and actionable before failure occurs.
  - **B. Domain Scope:** Any AZPO, circle, or the full ecosystem. The audit adapts its indicator set to the scope of the body being audited.
  - **C. Trigger Conditions:** Scheduled quarterly audit date arrives, a participant requests an early audit citing specific concerns, a safeguard trigger recommends a focused audit, or a threshold event occurs (e.g., 30% participant exit).
  - **D. Required Inputs:** Audit scope (AZPO/circle/ecosystem), time period, decision logs from the ACT engine, participation records, resource allocation records, proposal registry data, leadership tenure records, agreement review compliance data.
  - **E. Step-by-Step Process:** Define scope and period, collect data for each indicator (8 minimum: proposal authorship diversity, approval rate by author role, resource concentration index, participation trend, leadership tenure, objection integration rate, review compliance rate, cross-unit engagement frequency), score each indicator against healthy/warning/critical thresholds, compare to previous audit for trend analysis, generate safeguard recommendations for any indicator at warning or critical, publish report to all ecosystem members.
  - **F. Output Artifact:** Governance Health Report containing: audit metadata (scope, period, auditor), indicator scores with evidence, trend data, triggered safeguard recommendations, and raw data appendix.
  Write with full substance, active voice, no placeholders.
  **Acceptance:** Sections A-F are substantive (3+ lines each), terminology matches product-guidelines.md.

- [ ] **Task 1.3: Draft governance-health-audit SKILL.md -- sections G through L**
  Complete the remaining structural sections:
  - **G. Authority Boundary Check:** The audit produces a report and recommendations. It does not produce directives. No audit finding grants any body the authority to override normal governance processes. Recommendations are implemented through the standard ACT process. Audit data cannot be suppressed by the body being audited.
  - **H. Capture Resistance Check:** Address self-assessment anti-pattern (the audit must use independently collected data, not self-reported data from the body being audited). Address weaponization (audit findings are data with thresholds, not accusations). Address capture of the audit process itself (auditor rotation, structural separation of data collection from interpretation).
  - **I. Failure Containment Logic:** What happens when: data is incomplete (audit proceeds with available data, noting gaps -- gaps themselves are an indicator), auditor is unavailable (backup auditor from rotation list), indicators contradict each other (report all, do not resolve -- resolution is the domain of capture-pattern-recognition), audit is repeatedly skipped (automatic escalation to ecosystem-level notice).
  - **J. Expiry / Review Condition:** Audit schedule is renewable annually through consent. Indicator definitions are reviewed annually. Threshold calibrations are reviewed with each audit based on trend data. The audit process itself is auditable.
  - **K. Exit Compatibility Check:** When a participant exits, their historical participation data remains in audit records (anonymized if requested). The exit itself triggers a threshold check: does this exit push any indicator toward warning or critical?
  - **L. Cross-Unit Interoperability Impact:** Each AZPO conducts its own audits. Ecosystem-level audits aggregate AZPO data. Cross-AZPO comparison is published as relative indicators, not rankings.
  **Acceptance:** Sections G-L are substantive and structurally precise.

- [ ] **Task 1.4: Write governance-health-audit OmniOne walkthrough**
  Write a full narrative walkthrough:
  - Scenario: Quarterly governance health audit of the Bali SHUR AZPO conducted by the current rotating monitor (a TH member).
  - Walk through: Audit trigger (scheduled quarterly date), data collection (ACT decision logs show 47 decisions this quarter, participation records from circle meetings, resource allocation from Economics circle, proposal registry), indicator scoring (proposal authorship: 4 of 12 members authored 85% of proposals -- WARNING; approval rate equity: proposals from non-leadership approved at 61% vs. leadership at 94% -- WARNING; participation trend: meeting attendance down 15% from last quarter -- HEALTHY range but trending; resource concentration: balanced across 3 funding sources -- HEALTHY; leadership tenure: same circle lead for 3 review cycles -- WARNING; objection integration rate: 73% of objections were integrated -- HEALTHY; review compliance: 2 of 8 agreements overdue for review -- WARNING; cross-unit engagement: 3 inter-AZPO interactions this quarter -- HEALTHY).
  - Edge case: The current rotating monitor discovers that their own circle has the lowest participation score. They must still publish this data without editorial commentary.
  - End with the output artifact: the Governance Health Report with 3 warning indicators and the recommended safeguard activations (mandatory leadership review, proposal encouragement program, agreement review catch-up).
  **Acceptance:** Walkthrough names specific roles, shows complete flow with realistic data, includes edge case, ends with artifact.

- [ ] **Task 1.5: Write governance-health-audit stress-test results (all 7 scenarios)**
  Write full narrative stress tests (not brief summaries):
  1. **Capital Influx:** A $2M donation arrives from a single source, now providing 65% of ecosystem resources. The governance health audit's resource concentration indicator immediately hits CRITICAL. Walk through how the audit report triggers a capital capture safeguard without blocking the donation itself -- the safeguard initiates a mandatory funding diversification review, not a rejection of funds.
  2. **Emergency Crisis:** A natural disaster disrupts the SHUR. Emergency authority has been invoked 4 times in 3 months. The audit's emergency invocation frequency indicator hits WARNING. Walk through how the audit remains operational during crisis (simplified data collection, maintained publication) and flags emergency capture risk.
  3. **Leadership Charisma Capture:** A popular OSC member's proposals pass at 100% approval with zero modifications for 6 consecutive months. The audit's approval rate equity indicator hits CRITICAL. Walk through how the audit provides data-based evidence without accusation.
  4. **High Conflict / Polarization:** Two factions within the AZPO are blocking each other's proposals. The audit shows objection integration rate dropping to 20% and participation splitting into two non-overlapping groups. Walk through how the audit identifies the pattern and recommends conflict resolution referral.
  5. **Large-Scale Replication:** The ecosystem grows from 50 to 5,000 members across 40 AZPOs. Walk through how the audit process scales: AZPO-level audits remain manageable, ecosystem-level audit aggregates AZPO reports, indicator thresholds may need recalibration for larger populations.
  6. **External Legal Pressure:** A government regulator demands access to governance audit data. Walk through the boundary: audit data is published to members by default, external disclosure is governed by the ecosystem's external relations agreements, not by the audit skill itself.
  7. **Sudden Exit of 30%:** 15 of 50 participants leave in a single month. The audit's participation trend indicator hits CRITICAL. Multiple agreement review dates are now past due because review bodies have lost quorum. Walk through how the emergency audit trigger activates and the report identifies cascading governance health impacts.
  **Acceptance:** Each scenario is a full narrative paragraph (5+ sentences).

- [ ] **Task 1.6: Finalize governance-health-audit SKILL.md and create assets**
  Assemble SKILL.md from Tasks 1.2-1.5 with YAML frontmatter:
  ```yaml
  ---
  name: governance-health-audit
  description: "Run a structured governance health audit -- measure decision patterns, resource flows, participation rates, leadership tenure, and proposal diversity against quantified thresholds to detect degradation before it becomes capture."
  layer: 7
  version: 0.1.0
  depends_on: []
  ---
  ```
  Create `assets/governance-health-report-template.yaml` (audit metadata, 8+ indicator entries with score/evidence/threshold/status, trend comparison, safeguard recommendations).
  Create `assets/indicator-definitions.yaml` (each indicator: name, description, data source, calculation method, healthy range, warning threshold, critical threshold).
  Run `validate_skill.py` against the completed SKILL.md.
  **Acceptance:** SKILL.md passes validation. Under 500 lines. Both asset files complete.

- [ ] **Verification 1: Run validate_skill.py against governance-health-audit. Confirm pass. Review indicator definitions for measurability -- every indicator must be calculable from data that earlier layers produce. Verify no hidden authority in audit recommendations.** [checkpoint marker]

---

## Phase 2: Analytical Skills

**Goal:** Build capture pattern recognition and safeguard trigger design. After this phase, the ecosystem can detect capture patterns from audit data and install automatic safeguards.

### Tasks

- [ ] **Task 2.1: Draft capture-pattern-recognition SKILL.md -- sections A through F**
  - **A:** Governance health audits produce indicator data, but indicators alone do not diagnose capture. This skill provides the analytical framework to match indicator patterns to specific capture types (capital, charisma, emergency, ossification), distinguishing structural capture from benign explanations.
  - **B:** Any governance health audit data set, whether AZPO-level or ecosystem-level. The skill operates on audit outputs, not raw data.
  - **C:** A governance health audit report contains one or more indicators at WARNING or CRITICAL, a participant submits a formal capture concern with specific evidence, or a safeguard trigger requests a focused capture assessment.
  - **D:** The governance health audit report, historical audit data for trend analysis, the capture signature definitions (from assets), and any contextual information provided by the requesting party.
  - **E:** Load capture signatures for all four types, evaluate each signature against audit data, for each matched signature assess confidence level (low: 1 indicator at warning; medium: 2+ indicators at warning or 1 at critical; high: 2+ indicators at critical or sustained critical across 2+ audit periods), generate benign explanation check for each match (is there a non-capture explanation?), produce Capture Assessment Report.
  - **F:** Capture Assessment Report: detected patterns, confidence levels, contributing indicator evidence, benign explanation assessment, recommended safeguard activations.
  Reference governance-health-audit by name.
  **Acceptance:** Sections A-F complete, all four capture types addressed with distinct signatures.

- [ ] **Task 2.2: Draft capture-pattern-recognition SKILL.md -- sections G through L, walkthrough, and stress tests**
  - **G:** The capture assessment produces analysis and recommendations. It does not produce verdicts. No capture finding grants authority to remove leaders, block funding, or override decisions. All recommended responses go through standard ACT process.
  - **H:** Address weaponization (assessment requires specific indicator thresholds, not subjective impressions; the benign explanation check forces consideration of non-capture reasons). Address the assessor being captured (rotation, structural separation, any ecosystem member can request a second assessment). Address avoidance (declining to run an assessment when indicators warrant it is itself a capturable behavior -- automatic assessment triggered by threshold crossing).
  - **I-L:** Full structural sections appropriate to capture detection.
  - Walkthrough: A popular OSC member's proposals pass at 100% approval for 6 months. A TH member requests a capture assessment. The assessment finds: charisma capture signature matches at MEDIUM confidence (approval rate equity at CRITICAL, but objection integration rate is HEALTHY -- people may simply agree with the proposals). Benign explanation: the proposals addressed widely supported needs. Assessment recommends: anonymous proposal trial for next quarter (proposals presented without author names) to test whether the pattern is content-driven or personality-driven.
  - All 7 stress tests as full narratives specific to capture detection.
  **Acceptance:** Passes validation. Under 500 lines. Benign explanation check is structurally required, not optional.

- [ ] **Task 2.3: Create capture-pattern-recognition assets**
  Create `assets/capture-assessment-template.yaml` (assessment metadata, per-type entries with signature, matched indicators, confidence, benign explanation, recommendation).
  Create `assets/capture-signatures.yaml` (4 capture types, each with: name, description, indicator signatures with thresholds, typical benign explanations, recommended responses).
  **Acceptance:** Both templates complete and referenced in SKILL.md.

- [ ] **Task 2.4: Draft safeguard-trigger-design SKILL.md -- full skill**
  Build the complete safeguard trigger design skill:
  - **A:** Detection without response is surveillance. This skill converts passive monitoring into active structural defense by defining measurable thresholds that auto-activate specific governance interventions.
  - **B:** Any governance context where measurable indicators can be monitored and bounded interventions can be pre-defined.
  - **C:** An ecosystem is establishing its initial safeguard infrastructure, a governance health audit identifies a gap in safeguard coverage, or a capture assessment recommends a new trigger.
  - **D:** The indicator to monitor, the proposed threshold, the proposed safeguard action, the proposed notification recipients, and the proposed review timeline.
  - **E:** Draft trigger specification, submit through ACT process (triggers are agreements -- they bind the ecosystem to automatic responses, so they require consent), install in the Safeguard Trigger Registry, define monitoring cadence, define activation protocol (when threshold is crossed: notification is sent, safeguard action initiates, review timeline starts).
  - **F:** Safeguard Trigger Registry entry.
  - **G:** Triggers cannot be silently disabled. Modification or removal requires the same ACT process as installation. Triggers monitor; they do not override. The safeguard action is always a defined process (review, assessment, intervention proposal), never a unilateral authority expansion.
  - **H:** Address trigger capture (installing weak triggers that never fire), address trigger weaponization (installing over-sensitive triggers to harass political opponents), address trigger fatigue (too many triggers causing alarm exhaustion).
  - **I-L:** Full structural sections.
  - Starter triggers: Capital capture (funding concentration > 40% for 2+ quarters triggers mandatory diversification review), charisma capture (one person's proposal approval rate > 95% for 2+ quarters triggers anonymous proposal trial), emergency capture (emergency declaration frequency > 2 per quarter triggers emergency protocol review), ossification (leadership tenure > 2 review cycles without rotation triggers mandatory leadership review).
  - Walkthrough: The AE designs a capital capture trigger. They propose the trigger through ACT process. During consent, one member objects that the 40% threshold is too low for a young ecosystem with limited funding sources. Integration: threshold is set at 60% for the first year, then auto-adjusts to 40%. Trigger installed.
  - All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. Starter triggers are concrete with specific thresholds.

- [ ] **Task 2.5: Create safeguard-trigger-design assets**
  Create `assets/trigger-registry-template.yaml` (trigger ID, indicator monitored, threshold, safeguard action, notification recipients, installed date, review date, activation history, status).
  Create `assets/starter-triggers.yaml` (8+ pre-defined triggers across 4 capture types with configurable thresholds).
  **Acceptance:** Both templates complete.

- [ ] **Verification 2: Run validate_skill.py against all 3 completed skills. Confirm all pass. Verify coherence: capture-pattern-recognition references governance-health-audit outputs. Safeguard-trigger-design references both. Capture signatures in assets align with indicator definitions. Starter triggers reference specific indicators.** [checkpoint marker]

---

## Phase 3: Supporting Infrastructure Skills

**Goal:** Build independent monitoring and structural diversity maintenance. After this phase, all 5 Layer VII skills are complete.

### Tasks

- [ ] **Task 3.1: Draft independent-monitoring SKILL.md -- full skill**
  Build the complete independent monitoring skill:
  - **A:** If the body being monitored controls its own monitoring data, governance health assessments are compromised at the source. This skill establishes a structurally independent data collection role that cannot be captured by the bodies it monitors.
  - **B:** Any AZPO or ecosystem-level body that is subject to governance health audits. The monitor role exists alongside -- not within -- the monitored body's authority structure.
  - **C:** A new monitoring term begins (rotation), a governance health audit is scheduled, an ad hoc data collection request is made.
  - **D:** Access to decision logs, participation records, resource allocation data, proposal registry, agreement review status. The monitor does not need to attend decision meetings (to preserve independence) but must have access to their records.
  - **E:** Appointment (rotated from eligible pool -- any TH member not currently in leadership of the monitored body, 6-month term, 1-month handoff overlap), data collection (weekly: decision log entries, participation counts, proposal submissions; monthly: resource flow summaries, agreement status updates; quarterly: full data compilation for governance health audit), publication (Governance Data Report published to all ecosystem members, no editorial interpretation, correction protocol for errors), handoff (documented data collection procedures, access transfers, pending items list).
  - **F:** Governance Data Report (raw data, no interpretation), Handoff Document (at term end).
  - **G:** Monitor has data collection and publication authority only. No decision authority, no interpretation authority, no recommendation authority. If a monitor observes something concerning, they publish the data -- they do not diagnose.
  - **H:** Address monitor capture (term limits and rotation prevent relationship capture; prohibition on interpretation prevents authority creep; the monitor role is structurally boring by design -- it collects and publishes, nothing more). Address monitor intimidation (data publication is automatic -- suppressing it requires removing the monitor through ACT process, which is visible to all members).
  - **I-L:** Full structural sections.
  - Walkthrough: A TH member begins their 6-month term as independent monitor for the OSC. First month: they receive handoff from previous monitor, gain access to OSC decision logs and resource records, follow the data collection schedule. Mid-term: the OSC chair asks the monitor to delay publishing a data report that shows declining participation. The monitor publishes on schedule -- the role has no discretion on publication timing. Edge case: the monitor discovers a data discrepancy between the official decision log and meeting minutes. They publish both data sets with a note about the discrepancy, without interpreting which is correct.
  - All 7 stress tests with specific attention to: Scenario 1 (Capital Influx -- does the monitor track funding source data?), Scenario 3 (Charisma Capture -- can the charismatic leader influence the monitor's data collection?), Scenario 7 (30% exit -- is the monitor role itself affected by exit?).
  **Acceptance:** Passes validation. Under 500 lines. Monitor authority is strictly limited to data collection and publication.

- [ ] **Task 3.2: Create independent-monitoring assets**
  Create `assets/governance-data-report-template.yaml` (report period, data categories, raw data entries per indicator, data source references, discrepancy notes).
  Create `assets/data-collection-schedule.yaml` (weekly/monthly/quarterly tasks with specific data points, sources, and formats).
  **Acceptance:** Both templates complete.

- [ ] **Task 3.3: Draft structural-diversity-maintenance SKILL.md -- full skill**
  Build the complete structural diversity maintenance skill:
  - **A:** Detection without prevention means capture is only addressed after it has occurred. This skill proactively maintains the structural conditions that resist capture: diverse proposal authorship, broad participation, funding diversification, and leadership rotation compliance.
  - **B:** Any AZPO or ecosystem where governance health audit data reveals declining diversity on any dimension, or as a proactive periodic practice.
  - **C:** A governance health audit report identifies declining diversity on any dimension, a safeguard trigger fires on a diversity-related indicator, or the scheduled diversity review date arrives (recommended: semi-annually).
  - **D:** Governance health audit data (proposal authorship distribution, participation breadth, funding source count, leadership rotation compliance), historical trend data, and the current intervention catalog.
  - **E:** Review current diversity metrics across all dimensions (authorship, participation, funding, leadership rotation, information access), compare to previous period and healthy thresholds, for each dimension below threshold: select intervention from catalog, propose intervention through ACT process (interventions are temporary agreements with sunset dates), implement consented interventions, track effectiveness at next review. Diversity dimensions defined:
    1. Proposal authorship: percentage of members who have authored at least one proposal in the review period
    2. Approval equity: approval rate variance across author role categories
    3. Funding diversification: number of funding sources and maximum concentration percentage
    4. Leadership rotation: percentage of leadership roles that have rotated within their defined term
    5. Participation breadth: percentage of members who have participated in at least one decision in the review period
    6. Information access: percentage of governance data reports actually distributed to and accessed by members
  - **F:** Structural Diversity Report with current metrics, trend analysis, recommended interventions, and effectiveness tracking from previous interventions.
  - **G:** Diversity maintenance recommends and enables. It does not filter, block, or quota. No intervention can prevent a qualified member from authoring proposals, holding leadership, or participating. Interventions create pathways for underrepresented groups, they do not restrict overrepresented groups.
  - **H:** Address diversity theater (producing reports without structural change -- the skill requires intervention proposals with ACT process, not just reports). Address diversity as gatekeeping (ensuring interventions are enabling, not restrictive). Address capture of the diversity process itself (rotation of reviewers, all intervention proposals go through standard ACT).
  - **I-L:** Full structural sections.
  - Walkthrough: Semi-annual diversity review of the Bali SHUR AZPO. Data shows: proposal authorship concentrated -- 3 of 12 members authored 85% of proposals. Approval equity is fine. Funding is diversified. Leadership has rotated. But participation breadth is declining -- only 7 of 12 members participated in any decision last quarter. Intervention recommended: proposal mentorship program (experienced authors pair with new members for one proposal cycle), participation accessibility review (are meeting times/formats excluding some members?). Both interventions are proposed through ACT, consented with one modification (mentorship is opt-in, not assigned), implemented with 6-month sunset. Edge case: one of the 3 prolific authors objects that the mentorship program implies their proposals were illegitimate. The skill's framing addresses this: the intervention broadens participation, it does not delegitimize existing contributions.
  - All 7 stress tests.
  **Acceptance:** Passes validation. Under 500 lines. Interventions are enabling, not restrictive. All interventions have sunset dates.

- [ ] **Task 3.4: Create structural-diversity-maintenance assets**
  Create `assets/diversity-report-template.yaml` (report period, 6 diversity dimensions with current metrics and thresholds, trend comparison, active interventions with effectiveness tracking, new intervention recommendations).
  Create `assets/intervention-catalog.yaml` (catalog of structural interventions organized by diversity dimension, each with: description, implementation steps, ACT level required, recommended duration, effectiveness indicators).
  **Acceptance:** Both templates complete.

- [ ] **Verification 3: Run validate_skill.py against all 5 completed skills. All must pass. Verify that the data flow is coherent: independent-monitoring produces raw data, governance-health-audit scores it, capture-pattern-recognition analyzes it, safeguard-trigger-design responds to it, structural-diversity-maintenance proactively maintains it. No circular authority dependencies.** [checkpoint marker]

---

## Phase 4: Layer Integration and Cross-Layer Verification

**Goal:** Write the Layer VII README, verify cross-layer references, and confirm all quality gates pass.

### Tasks

- [ ] **Task 4.1: Write layer-07-safeguard README.md**
  Write the layer README summarizing:
  - Layer purpose: Continuous governance health monitoring and capture resistance
  - The 5 skills and their relationships (data flow diagram in text)
  - Cross-layer dependencies (which earlier layer outputs feed into Layer VII)
  - How to use the layer: the recommended cadence (independent monitoring ongoing, governance health audit quarterly, capture pattern recognition on-demand and at warning thresholds, safeguard trigger review annually, diversity maintenance semi-annually)
  **Acceptance:** README accurately describes all 5 skills and their relationships.

- [ ] **Task 4.2: Cross-layer reference verification**
  Review all 5 SKILL.md files for:
  - References to Layer I-VI skills use correct skill names
  - No circular authority dependencies (Layer VII monitors, it does not decide)
  - Capture resistance checks in Layer VII skills address the meta-problem (who watches the watchers)
  - Exit compatibility (what happens to monitoring when members exit)
  - Cross-unit interoperability (AZPO-level vs. ecosystem-level monitoring)
  **Acceptance:** All cross-references verified. No orphan references.

- [ ] **Task 4.3: Run full validation and quality gate review**
  Run `validate_skill.py` against all 5 skills. Review against the per-skill checklist:
  - [ ] All 12 sections (A-L) present and substantive
  - [ ] OmniOne walkthrough included with specific roles
  - [ ] At least one edge case documented per skill
  - [ ] Stress-tested against 7 scenarios
  - [ ] No hidden sovereign authority
  - [ ] Exit compatibility confirmed
  - [ ] Cross-unit interoperability impact stated
  And the per-layer checklist:
  - [ ] All 5 skills complete
  - [ ] Skills cross-reference each other correctly
  - [ ] Layer README summarizes skills and relationships
  - [ ] No circular authority dependencies
  **Acceptance:** All checks pass. Layer VII is complete.

- [ ] **Verification 4: Final layer review. All 5 skills pass validation. README is complete. Cross-layer references are accurate. The layer can be read end-to-end as a coherent governance health monitoring system. Commit: `neos(layer-07): Complete layer 07 - Safeguard & Capture Detection`** [checkpoint marker]
