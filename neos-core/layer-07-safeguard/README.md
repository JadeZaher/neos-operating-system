# Layer VII: Safeguard & Capture Detection

## Overview

Capture -- the process by which a governance system is co-opted by narrow interests despite its formal rules -- is the central failure mode NEOS exists to resist. Every earlier layer contains ad hoc capture resistance checks within individual skills. Layer VII elevates capture detection from a per-skill afterthought to a structural, continuous, measurable discipline.

This layer draws on Robert Michels' Iron Law of Oligarchy (organizations inevitably concentrate power unless structurally resisted), V-Dem Democracy Indicators (measurable governance health signals), and cooperative governance research identifying four systemic capture types. The skills in this layer do not make governance decisions -- they observe, measure, and trigger safeguards when governance health degrades.

## The Four Capture Types

| Type | Mechanism | Key Indicators |
|------|-----------|----------------|
| **Capital** | A funding source gains disproportionate influence over governance outcomes | Resource concentration (GHI-03), funding-conditional proposal bias, self-censorship in funder-related discussions |
| **Charisma** | A personality becomes psychologically unsafe to challenge | Approval rate disparity (GHI-02), objection withdrawal patterns (GHI-06), proposal authorship concentration (GHI-01) |
| **Emergency** | Temporary authority becomes permanent through repeated invocation or scope creep | Emergency declaration frequency, scope creep patterns, post-emergency authority return delays |
| **Ossification** | Leadership calcifies regardless of formal rotation rules | Leadership tenure (GHI-05), non-leadership participation decline (GHI-04), approval rate inequity |

## Architecture: Observation, Analysis, Response

Layer VII follows a three-stage architecture that structurally separates data from interpretation from action. This separation prevents any single function from controlling the full pipeline from observation to governance response.

```
OBSERVATION          ANALYSIS              RESPONSE
    |                    |                     |
independent-     governance-health-    safeguard-trigger-
monitoring       audit                 design
    |                    |                     |
  collects         interprets            activates
  raw data         indicators            bounded
  publishes        scores health         interventions
    |                    |                     |
    |            capture-pattern-      structural-diversity-
    |            recognition           maintenance
    |                    |                     |
    |              diagnoses             proactively
    |              capture types         maintains conditions
    |              with confidence       that resist capture
    |              scores                |
    v                    v                     v
  DATA               DIAGNOSIS            ACTION
  (no interpretation)  (no authority)       (bounded, consented, sunset)
```

**Observation** (independent-monitoring): Raw data collection by a rotating, structurally independent role. The monitor collects and publishes data with no interpretation, no trend analysis, and no recommendations.

**Analysis** (governance-health-audit + capture-pattern-recognition): Structured interpretation of governance data against defined indicators and capture signatures. The analysis skills produce reports and recommendations, never directives.

**Response** (safeguard-trigger-design + structural-diversity-maintenance): Automatic trigger activation when thresholds are crossed, plus proactive interventions to maintain diversity conditions. All responses are bounded, consented-to, and have sunset dates.

## Skill Index

| # | Skill | Purpose | Dependencies |
|---|-------|---------|-------------|
| 1 | [governance-health-audit](governance-health-audit/SKILL.md) | Quantified review of 8 governance health indicators across an AZPO or ecosystem | agreement-registry, domain-mapping, role-assignment |
| 2 | [capture-pattern-recognition](capture-pattern-recognition/SKILL.md) | Diagnose the four capture types from governance data with evidence-based confidence scores | governance-health-audit, domain-mapping |
| 3 | [safeguard-trigger-design](safeguard-trigger-design/SKILL.md) | Design, install, and maintain automatic thresholds that activate governance interventions | capture-pattern-recognition, act-consent-phase, agreement-creation |
| 4 | [independent-monitoring](independent-monitoring/SKILL.md) | Structurally separated data collection and publication -- raw data, no interpretation | governance-health-audit, role-assignment, domain-mapping |
| 5 | [structural-diversity-maintenance](structural-diversity-maintenance/SKILL.md) | Proactive maintenance of conditions that resist capture: authorship diversity, approval equity, funding distribution, leadership rotation, participation breadth | governance-health-audit, capture-pattern-recognition, domain-mapping |

## Design Principles

**No hidden authority.** Monitoring and audit skills observe and recommend. They do not decide. Safeguard triggers activate defined processes, not undefined "corrective actions." The independent monitor has no decision power.

**Anti-weaponization.** Every detection claim requires evidence-based thresholds with specific indicator data. The layer structurally separates observation (data) from accusation (interpretation) from intervention (action). Capture assessments describe structural conditions, not personal intentions.

**Expiry by default.** Safeguard triggers have review dates. The independent monitor role has term limits. Governance health audit schedules are renewable, not permanent. All structural interventions from diversity maintenance have sunset dates.

**Consent, not imposition.** Safeguard triggers are installed through the ACT process. Structural interventions require consent before implementation. No skill in this layer can impose governance changes unilaterally.

## Relationship to Other Layers

- **Layer I (Agreement):** Safeguard triggers are installed through the agreement process. Governance health audits examine agreement compliance.
- **Layer II (Authority):** Capture detection monitors authority concentration. The independent monitor role is defined through authority structures.
- **Layer III (ACT Engine):** Safeguard trigger installation uses the ACT process. Decision pattern analysis examines ACT logs.
- **Layer IV (Economic):** Capital capture detection examines resource flows defined in economic agreements.
- **Layer VI (Conflict):** Capture accusations that cannot be resolved through data may escalate to conflict resolution processes.
- **Layer VIII (Emergency):** Layer VII detects when emergency authority is being abused. Layer VIII defines how emergency authority operates. The two layers form a check-and-balance pair: Layer VIII grants constrained emergency powers, Layer VII monitors whether those constraints hold.
- **Layer IX (Memory):** Governance health data depends on decision logs and agreement versioning maintained by the memory layer.

## Cross-Layer References

All governance health indicators (GHI-01 through GHI-08) are defined in `governance-health-audit/assets/indicator-definitions.yaml`. Capture type signatures are defined in `capture-pattern-recognition/assets/capture-assessment-template.yaml`. The starter safeguard trigger set is defined in `safeguard-trigger-design/assets/trigger-registry-template.yaml`.
