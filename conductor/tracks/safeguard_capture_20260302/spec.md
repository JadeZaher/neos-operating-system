# Specification: Safeguard & Capture Detection (Layer VII)

## Track ID
`safeguard_capture_20260302`

## Overview

This track builds the five skills of **Layer VII: Safeguard & Capture Detection**. Capture -- the process by which a governance system is co-opted by narrow interests despite its formal rules -- is the central failure mode NEOS exists to resist. Every earlier layer contains ad hoc capture resistance checks within individual skills. This layer elevates capture detection from a per-skill afterthought to a structural, continuous, measurable discipline.

The layer draws on Robert Michels' Iron Law of Oligarchy (organizations inevitably concentrate power unless structurally resisted), V-Dem Democracy Indicators (measurable governance health signals), and cooperative governance research on capital, charisma, emergency, and ossification capture types. The skills in this layer do not make governance decisions -- they observe, measure, and trigger safeguards when governance health degrades.

This track depends on most earlier layers being conceptually complete: agreements (Layer I) define what to monitor, authority (Layer II) defines who holds power that might concentrate, decisions (Layer III) define the processes that might be subverted, economics (Layer IV) defines the resource flows that might create leverage, and conflict resolution (Layer VI) defines the escalation paths that might be captured.

## Background

### The Iron Law and How to Break It

Michels observed that every organization, no matter how democratic its founding, tends toward oligarchy: leaders accumulate information advantages, communication bottlenecks, and social capital that make them increasingly difficult to replace. The conditions that resist this are well-documented: engaged membership, independent information flows, transparency of decision patterns, rotating leadership, and collective decision-making. NEOS embeds these conditions structurally. This layer monitors whether they are actually functioning.

### Four Capture Types

1. **Capital Capture**: A funding source gains disproportionate influence over governance outcomes. Indicators: one source provides more than X% of resources, systematic bias in approving funder-aligned proposals, self-censorship in discussions touching funder interests.

2. **Charisma Capture**: A personality becomes psychologically unsafe to challenge. Indicators: objection withdrawal patterns when a specific person advocates, one person's proposals adopted without substantive modification, onboarding that depends on personal relationship with the leader rather than structural process.

3. **Emergency Capture**: Temporary authority becomes permanent through repeated invocation or scope creep. Indicators: increasing frequency of emergency declarations, subjective threshold application, missing post-emergency reviews.

4. **Ossification Capture**: Leadership calcifies regardless of formal rotation rules. Indicators: unchanged leadership beyond two review cycles, declining non-leadership attendance, lower approval rate for proposals authored by non-leadership members.

### Design Patterns vs. Anti-Patterns

**Effective patterns**: Automated diversity audits on proposal authorship and approval rates, capture triggers with measurable thresholds that auto-activate safeguards, structural separation between information collection and authority, mandatory leadership rotation with real enforcement, dissent channels that produce structural responses rather than social consequences.

**Anti-patterns to avoid**: Self-assessment of capture (asking the captured body "are you captured?"), false positives weaponized as political tools, creating a culture of suspicion that undermines trust.

### Relationship to Layer VIII (Emergency Handling)

Layer VII detects when emergency authority is being abused. Layer VIII defines how emergency authority operates. The two layers form a check-and-balance pair: Layer VIII grants constrained emergency powers, Layer VII monitors whether those constraints hold. This track builds the detection and safeguard side; the emergency_handling track builds the operational side.

---

## Functional Requirements

### FR-1: Governance Health Audit (`governance-health-audit`)

**Description:** Enable any authorized participant or automated process to conduct a structured review of governance health indicators across an ETHOS or the full ecosystem. The audit examines decision patterns, resource flows, participation rates, proposal diversity, and leadership tenure to produce a quantified governance health report.

**Acceptance Criteria:**
- AC-1.1: The skill defines all required inputs (audit scope -- ETHOS or ecosystem, time period, data sources including decision logs, resource allocation records, participation records, and proposal registry).
- AC-1.2: The step-by-step process specifies at least 8 measurable indicators drawn from V-Dem methodology: proposal authorship diversity, approval rate by author role, resource concentration index, participation trend, leadership tenure, objection integration rate, review compliance rate, and cross-unit engagement frequency.
- AC-1.3: Each indicator has a defined "healthy range," "warning threshold," and "critical threshold" with specific numeric or percentage-based criteria.
- AC-1.4: The output artifact is a Governance Health Report with indicator scores, trend data (comparison to previous audit), and triggered safeguard recommendations.
- AC-1.5: The authority boundary check prevents audit results from being suppressed by the body being audited -- audit reports are published to all ecosystem members, not just leadership.
- AC-1.6: The capture resistance check addresses the anti-pattern of self-assessment: the skill structurally separates audit data collection from audit interpretation.
- AC-1.7: An OmniOne walkthrough demonstrates a quarterly governance health audit of the Bali SHUR ETHOS.
- AC-1.8: All 7 stress-test scenarios are documented with full narrative results.

**Priority:** P0 -- Foundational skill for the entire layer.

### FR-2: Capture Pattern Recognition (`capture-pattern-recognition`)

**Description:** Provide a structured framework for identifying the four capture types (capital, charisma, emergency, ossification) from governance data. This skill converts raw governance health data into specific capture pattern diagnoses with confidence levels and recommended responses.

**Acceptance Criteria:**
- AC-2.1: The skill defines signature indicators for each of the four capture types, with at least 3 measurable indicators per type.
- AC-2.2: Each indicator has a detection threshold expressed as a measurable criterion (e.g., "one funding source provides more than 40% of total resources for 2 or more consecutive quarters").
- AC-2.3: The step-by-step process includes a pattern-matching methodology that evaluates governance health audit data against capture signatures, producing a confidence score (low/medium/high) for each capture type.
- AC-2.4: The output artifact is a Capture Assessment Report that identifies detected patterns, confidence levels, contributing evidence, and recommended safeguard activations.
- AC-2.5: The failure containment logic addresses false positives: the skill distinguishes between structural capture indicators and benign explanations (e.g., a single funding source may be temporary during a fundraising transition, not capture).
- AC-2.6: The capture resistance check addresses the anti-pattern of weaponized accusations: the skill requires evidence-based claims with specific indicator thresholds met, not subjective impressions.
- AC-2.7: An OmniOne walkthrough demonstrates detecting potential charisma capture around a popular OSC member whose proposals consistently pass without modification.
- AC-2.8: All 7 stress-test scenarios documented.

**Priority:** P0 -- Core analytical skill.

### FR-3: Safeguard Trigger Design (`safeguard-trigger-design`)

**Description:** Enable the ecosystem to define, install, and maintain measurable safeguard triggers -- automatic thresholds that activate specific governance interventions when crossed. Triggers are the structural mechanism that converts passive monitoring into active defense.

**Acceptance Criteria:**
- AC-3.1: The skill defines the anatomy of a safeguard trigger: the monitored indicator, the threshold value, the safeguard action, the notification recipients, and the review timeline.
- AC-3.2: The step-by-step process walks through designing a new trigger using the ACT process (triggers must be consented to before installation, not imposed).
- AC-3.3: The skill provides a starter set of recommended triggers for each capture type (at least 2 triggers per capture type, 8 total minimum).
- AC-3.4: Each trigger's safeguard action is defined as a specific, bounded intervention (e.g., "initiate mandatory leadership review" not "fix the problem").
- AC-3.5: The output artifact is a Safeguard Trigger Registry entry with the trigger definition, installation date, activation history, and current status.
- AC-3.6: The authority boundary check ensures triggers cannot be silently disabled by the body they monitor -- trigger modification requires the same ACT process as trigger installation.
- AC-3.7: An OmniOne walkthrough demonstrates the AE designing and installing a capital capture trigger based on funding concentration thresholds.
- AC-3.8: All 7 stress-test scenarios documented.

**Priority:** P0 -- Mechanism that makes detection actionable.

### FR-4: Independent Monitoring (`independent-monitoring`)

**Description:** Establish a structural role and process for collecting, maintaining, and publishing governance health data independently of the bodies being monitored. The monitor collects data and publishes it without interpretation; interpretation is the domain of the governance-health-audit and capture-pattern-recognition skills.

**Acceptance Criteria:**
- AC-4.1: The skill defines the independent monitor role: appointment process (rotated, never held by current leadership), authority scope (data collection and publication only, no decision authority), term limits, and accountability structure.
- AC-4.2: The step-by-step process specifies data collection procedures for each governance health indicator: what data, from what source, at what frequency, in what format.
- AC-4.3: The output artifact is a published Governance Data Report -- raw data with no editorial interpretation, available to all ecosystem members.
- AC-4.4: The authority boundary check prevents the monitor from being given interpretation or recommendation authority -- the role is structurally limited to data.
- AC-4.5: The failure containment logic addresses what happens when the monitor is absent, compromised, or produces inaccurate data (backup monitors, data verification process, correction protocol).
- AC-4.6: The capture resistance check addresses the risk of the monitoring role itself being captured -- term limits, rotation, and the structural prohibition on interpretation authority prevent this.
- AC-4.7: An OmniOne walkthrough demonstrates a rotating TH member serving as independent monitor for the OSC, collecting and publishing decision pattern data for the quarter.
- AC-4.8: All 7 stress-test scenarios documented.

**Priority:** P1 -- Important infrastructure, depends on FR-1 defining what to monitor.

### FR-5: Structural Diversity Maintenance (`structural-diversity-maintenance`)

**Description:** Define active practices for maintaining diverse proposal authorship, decision participation, funding sources, and leadership composition. This skill moves beyond detection to proactive structural maintenance -- ensuring the conditions that resist capture are continuously renewed rather than assumed.

**Acceptance Criteria:**
- AC-5.1: The skill defines diversity dimensions to maintain: proposal authorship distribution, approval rate equity across author roles, funding source diversification, leadership rotation compliance, participation breadth, and information access equality.
- AC-5.2: The step-by-step process specifies periodic diversity reviews (distinct from governance health audits -- these are proactive interventions, not diagnostic assessments).
- AC-5.3: The skill defines structural interventions for each diversity dimension when it degrades: proposal encouragement programs for underrepresented groups, funding diversification campaigns, leadership rotation enforcement, participation accessibility improvements.
- AC-5.4: The output artifact is a Structural Diversity Report with current metrics, trend analysis, and intervention recommendations.
- AC-5.5: The authority boundary check prevents diversity maintenance from becoming a gatekeeping function -- interventions encourage and enable, they do not filter or block.
- AC-5.6: The capture resistance check addresses the risk of diversity maintenance itself being captured as a compliance exercise that produces reports but no structural change.
- AC-5.7: An OmniOne walkthrough demonstrates a diversity review revealing that 80% of proposals in the past quarter were authored by the same 3 AE members, and the structural intervention to broaden authorship.
- AC-5.8: All 7 stress-test scenarios documented.

**Priority:** P1 -- Proactive complement to reactive detection skills.

---

## Non-Functional Requirements

### NFR-1: Modularity

Each skill must function independently. A participant reading governance-health-audit should be able to conduct an audit without loading capture-pattern-recognition. Skills reference each other by name but do not require co-loading.

### NFR-2: Line Limit

Each SKILL.md must be under 500 lines. Indicator definition tables, threshold calibrations, and trigger templates go in `assets/`.

### NFR-3: Portability

All skills are NEOS-generic at the structural level. OmniOne-specific configurations (specific threshold values, specific role names, specific review cadences) appear as clearly marked examples that another ecosystem can replace.

### NFR-4: No Hidden Authority

The monitoring and audit skills must not create hidden authority. The independent monitor has no decision power. The audit produces data and recommendations, not directives. Safeguard triggers activate defined processes, not undefined "corrective actions."

### NFR-5: Anti-Weaponization

Capture detection tools must not be weaponizable as political instruments. Every detection claim must be evidence-based with specific thresholds met. The skills must structurally separate observation (data) from accusation (interpretation) from intervention (action).

### NFR-6: Expiry by Default

Safeguard triggers have review dates. The independent monitor role has term limits. Governance health audit schedules are renewable, not permanent. All structural interventions recommended by diversity maintenance have sunset dates.

### NFR-7: Validation

Every SKILL.md must pass automated validation via `scripts/validate_skill.py`.

---

## User Stories

### US-1: AI Agent Conducts a Governance Health Audit
**As** an AI agent assisting an ETHOS steward,
**I want** to collect governance health indicators and produce a structured report,
**So that** the ETHOS has quantified visibility into whether its governance is healthy or degrading.

**Given** the AI agent has access to decision logs, participation records, and resource allocation data,
**When** it follows the governance-health-audit skill process,
**Then** it produces a Governance Health Report with scored indicators, trend comparisons, and safeguard recommendations.

### US-2: Participant Investigates a Capture Concern
**As** a TH member who suspects that a particular leader has too much unchallenged influence,
**I want** a structured, evidence-based way to evaluate whether charisma capture is occurring,
**So that** my concern is addressed through data rather than accusation.

**Given** the participant has a subjective concern about influence concentration,
**When** they request a capture pattern assessment using governance health data,
**Then** the capture-pattern-recognition skill produces a Capture Assessment Report with specific indicator evidence and a confidence score, separating data from interpretation.

### US-3: Ecosystem Architect Installs Safeguard Triggers
**As** an ecosystem architect configuring NEOS for a new community,
**I want** to install measurable safeguard triggers that auto-activate governance interventions,
**So that** capture resistance is structural and automatic, not dependent on individual vigilance.

**Given** the architect has reviewed the recommended starter triggers,
**When** they follow the safeguard-trigger-design skill to customize and install triggers through the ACT process,
**Then** a Safeguard Trigger Registry is established with configured triggers, thresholds, and safeguard actions.

### US-4: Independent Monitor Publishes Governance Data
**As** a rotating TH member serving as independent monitor,
**I want** clear instructions for collecting and publishing governance data without editorial interpretation,
**So that** all ecosystem members have access to raw governance health information.

**Given** the monitor has been appointed through the defined rotation process,
**When** they follow the independent-monitoring skill procedures,
**Then** a Governance Data Report is published to all members with raw data, no interpretation, and full transparency.

### US-5: Circle Responds to a Triggered Safeguard
**As** a circle whose capital capture trigger has been activated,
**I want** to understand what the trigger means, what evidence activated it, and what process follows,
**So that** the response is proportionate, structural, and not punitive.

**Given** a safeguard trigger has crossed its threshold,
**When** the affected circle reviews the trigger activation notice,
**Then** they see the specific indicator data, the threshold that was crossed, the defined safeguard action, and the review timeline.

### US-6: Ecosystem Runs Structural Diversity Maintenance
**As** an ecosystem steward noticing declining participation diversity,
**I want** structural interventions to broaden proposal authorship and decision participation,
**So that** governance remains resilient to concentration rather than waiting for capture to occur.

**Given** governance health data shows declining diversity in proposal authorship,
**When** the steward follows the structural-diversity-maintenance skill,
**Then** specific, bounded interventions are recommended with implementation plans and sunset dates.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-07-safeguard/
    README.md
    governance-health-audit/
      SKILL.md
      assets/
        governance-health-report-template.yaml
        indicator-definitions.yaml
      references/
      scripts/
    capture-pattern-recognition/
      SKILL.md
      assets/
        capture-assessment-template.yaml
        capture-signatures.yaml
      references/
      scripts/
    safeguard-trigger-design/
      SKILL.md
      assets/
        trigger-registry-template.yaml
        starter-triggers.yaml
      references/
      scripts/
    independent-monitoring/
      SKILL.md
      assets/
        governance-data-report-template.yaml
        data-collection-schedule.yaml
      references/
      scripts/
    structural-diversity-maintenance/
      SKILL.md
      assets/
        diversity-report-template.yaml
        intervention-catalog.yaml
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name
description: "..."
layer: 7
version: 0.1.0
depends_on: []
---
```

### Cross-Layer Dependencies

Layer VII skills reference but do not require:
- **Layer I (Agreement):** Safeguard triggers are installed through the agreement process. Governance health audits examine agreement compliance.
- **Layer II (Authority):** Capture detection monitors authority concentration. Independent monitoring role is defined through authority structures.
- **Layer III (ACT Engine):** Safeguard trigger installation uses ACT process. Decision pattern analysis examines ACT logs.
- **Layer IV (Economic):** Capital capture detection examines resource flows.
- **Layer VI (Conflict):** Capture accusations that cannot be resolved through data may escalate to conflict resolution.
- **Layer IX (Memory):** Governance health data depends on decision logs and agreement versioning.

### Indicator Calibration Note

Specific numeric thresholds for governance health indicators (e.g., "one funding source above 40%") are placed in `assets/` configuration files, not hardcoded into SKILL.md. This allows ecosystem-specific calibration. OmniOne defaults are provided as clearly marked examples.

---

## Out of Scope

- **Emergency handling mechanics** -- Layer VIII defines how emergency authority operates. This track only detects when emergency authority is being abused.
- **Conflict resolution processes** -- Layer VI handles disputes. This track may identify capture patterns that lead to disputes but does not resolve them.
- **Software implementation** -- No databases, dashboards, or automated monitoring software. The skills define processes for human and AI agent execution.
- **Specific OmniOne policy decisions** -- The skills define how to detect capture, not what specific thresholds OmniOne should set (those are configuration).
- **Cultural change programs** -- The skills define structural interventions, not workshops, training, or belief-change initiatives.

---

## Open Questions

1. **Threshold calibration methodology**: How should an ecosystem determine its initial indicator thresholds? The skills define the structure but the specific numbers (e.g., "40% funding concentration") are configuration. Should there be a calibration process skill, or is this handled through the ACT process for trigger installation?

2. **Audit frequency**: Quarterly audits are suggested as a default, but new or small ecosystems may need more frequent monitoring. Should the skill define adaptive frequency based on ecosystem size and age?

3. **Monitor rotation cadence**: How frequently should the independent monitor role rotate? Too fast loses institutional knowledge of data collection; too slow risks the monitor developing blind spots or relationships that compromise independence. Recommendation: 6-month terms with 1-month overlap for handoff.

4. **Cross-ecosystem capture comparison**: When multiple ecosystems run NEOS, can governance health data be compared across ecosystems without creating competitive dynamics? Deferred to Layer V (Inter-Unit Coordination) considerations.
