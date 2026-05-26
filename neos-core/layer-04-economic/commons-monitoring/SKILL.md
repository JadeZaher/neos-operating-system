---
name: commons-monitoring
description: "Track resource flows across funding pools and commons resources, detect over-draw or concentration, and trigger graduated community responses -- monitoring by the community, not external auditors or opaque algorithms."
layer: 4
version: 0.1.0
depends_on: [funding-pool-stewardship, domain-mapping]
---

# commons-monitoring

## C. Trigger Conditions

- A funding pool's transparency schedule specifies a reporting cycle (weekly, monthly, quarterly)
- A pool balance crosses a defined threshold (low balance warning, high concentration alert)
- A single circle or participant's cumulative resource draw exceeds the concentration threshold (default: 30% of any pool's total outflows in a reporting period)
- A steward's discretionary disbursements approach the cumulative pattern threshold (total discretionary spending exceeds 15% of pool balance in a reporting period)
- A pool steward misses a scheduled balance report
- The governing body requests an ad-hoc commons health assessment
- An emergency drawdown triggers mandatory post-emergency monitoring
- A new reporting period begins per the ecosystem monitoring calendar

## D. Required Inputs

- **Pool data**: current balances, inflow records, outflow records, and governance agreements for all monitored pools (mandatory, sourced from pool stewards' transparency reports)
- **Transaction logs**: individual disbursement records with amounts, recipients, dates, and authorization levels (mandatory, sourced from pool stewards)
- **Monitoring calendar**: the schedule of reporting cycles, review sessions, and threshold check dates (mandatory, derived from pool governance agreements)
- **Threshold configuration**: defined thresholds for each monitoring dimension -- flow rate limits, concentration ceilings, reciprocity bands, sustainability projections, accessibility benchmarks (mandatory, set in pool governance agreements with ecosystem defaults)
- **Monitor roster**: the community members assigned to monitoring roles for the current rotation (mandatory, assigned through role-assignment with mandatory rotation)
- **Previous reports**: prior commons health reports for trend comparison (recommended, sourced from the agreement registry)

## E. Step-by-Step Process

1. **Collect pool data.** At each reporting cycle, monitors gather balance reports and transaction logs from all pool stewards. Stewards provide data according to their pool's transparency schedule. Monitors verify data completeness -- any pool that has not reported triggers a missing-report alert per the failure containment logic.
2. **Calculate monitoring dimensions.** Monitors compute the five dimensions for each pool and across the ecosystem:
   - *Flow rate*: total inflows and outflows for the period, compared to prior periods. Flag if outflow rate exceeds inflow rate for two consecutive periods.
   - *Concentration*: percentage of total outflows directed to each circle or participant. Flag if any single recipient exceeds 30% of a pool's outflows or 20% of ecosystem-wide outflows.
   - *Reciprocity*: ratio of resources received to resources contributed for each circle. Flag if any circle's receive-to-contribute ratio exceeds 3:1 for two consecutive periods.
   - *Sustainability*: projected pool depletion date based on current draw rate. Flag if any pool is projected to deplete within two reporting periods.
   - *Accessibility*: percentage of eligible participants who have submitted at least one resource request in the past two reporting periods. Flag if accessibility drops below 40%.
3. **Identify threshold breaches.** Monitors compile a list of all threshold breaches detected in step 2. Each breach is documented with: which threshold, which pool or circle, the measured value, the threshold value, and the trend direction (worsening, stable, improving).
4. **Gather community observations.** Monitors solicit qualitative observations from ecosystem participants: are there resource access barriers not captured in quantitative data? Are there patterns of informal resource allocation that bypass the formal process? Are specific pools or stewards consistently receiving complaints? Community observations are recorded alongside quantitative findings.
5. **Draft commons health report.** Monitors compile findings into the `assets/commons-health-report-template.yaml`. The report includes: executive summary, dimension-by-dimension analysis for each pool, threshold breach details, community observations, trend comparisons with previous reports, and recommended actions. Recommended actions follow the graduated response ladder (see step 7).
6. **Community review session.** The commons health report is presented at a community review session open to all ecosystem participants. The session is facilitated (not led by monitors) to prevent monitors from framing findings in ways that serve particular interests. Participants discuss findings, challenge interpretations, and propose additional actions. The facilitator ensures discussion remains focused on resource patterns, not individual blame.
7. **Graduated response activation.** When threshold breaches are confirmed, the graduated response ladder activates:
   - *Level 1 -- Notification*: the affected circle or steward is notified of the breach and asked to provide context. No action is required beyond acknowledgment. Timeline: 7 days.
   - *Level 2 -- Review*: if the breach persists or worsens in the next reporting period, the governing circle reviews the affected pool's governance agreement and the pattern causing the breach. Timeline: 14 days.
   - *Level 3 -- Restriction*: if the breach continues after review, the governing body may impose temporary restrictions -- reduced discretionary thresholds, additional reporting requirements, or mandatory consent for all disbursements. Restrictions are time-limited (maximum 90 days) and reviewed at expiry.
   - *Level 4 -- Formal investigation*: if restrictions do not resolve the pattern, a formal investigation is triggered through the agreement-review skill. The investigation examines whether the pool's governance structure is adequate, whether steward misconduct occurred, or whether the ecosystem's threshold configuration needs adjustment.
8. **Update monitoring configuration.** After the community review, monitors and the governing body may adjust threshold configurations based on lessons learned. Threshold changes follow the agreement amendment process through ACT.

## F. Output Artifact

A commons health report following `assets/commons-health-report-template.yaml`. The report contains: report ID, reporting period, monitor roster, executive summary, pool-by-pool dimension analysis (flow rate, concentration, reciprocity, sustainability, accessibility), threshold breach records with severity and trend, community observations, comparison with previous reporting period, recommended actions mapped to the graduated response ladder, community review session notes, and the next reporting date. The report is registered in the agreement registry and accessible to every ecosystem participant. No commons health report is confidential -- full transparency is the structural default.

## G. Authority Boundary Check

- **Monitors observe and report; they do not decide.** Monitors compile data, calculate dimensions, and draft reports. They do not have authority to restrict pool access, modify governance agreements, or sanction participants. Monitoring informs decisions; it does not make them.
- **No monitor** can unilaterally trigger graduated responses above Level 1 (notification). Level 2 and above require governing body action through the consent process.
- **Monitors cannot access individual financial records** beyond what appears in pool transaction logs. Personal finances, compensation details, and non-pool resource flows are outside monitoring scope.
- **The community review session facilitator** ensures monitors do not steer the discussion toward predetermined conclusions. The facilitator is a different person from the monitors.
- **Monitor rotation is mandatory.** No individual or group monitors the same pools for more than two consecutive reporting periods. Rotation prevents monitors from developing relationships with stewards that compromise objectivity.
- **Threshold configurations** are set through ACT consent, not by monitors. Monitors may recommend threshold changes, but implementation requires governing body approval.

## H. Capture Resistance Check

**Capital capture.** A major contributor pressures monitors to exclude their circle's resource draw from concentration analysis, arguing that their contributions justify higher draw rates. The skill prevents this because monitoring dimensions apply equally to all pools and participants regardless of contribution level. Contribution size is not a factor in any threshold calculation. The commons health report publishes all data -- monitors cannot selectively omit findings without the omission being visible to every participant who reads the report.

**Charismatic capture.** A respected leader pressures the community review session to dismiss a threshold breach affecting their circle as "not a real concern." The facilitator ensures the session follows structured discussion: the data is presented before interpretation, every participant can submit written responses before open discussion, and the graduated response ladder activates based on measured thresholds, not on the session's emotional temperature. The leader's social influence cannot override a quantitative threshold breach.

**Emergency capture.** A crisis is invoked to suspend monitoring: "We are dealing with an emergency, we do not have time for reports." The skill requires that emergency drawdowns trigger additional monitoring, not less. Post-emergency monitoring is mandatory and examines whether the emergency disbursement was appropriate in amount and use. Suspending monitoring during a crisis is the precise moment when capture is most likely.

**Informal capture.** Monitors develop informal relationships with stewards they oversee and begin softening findings or delaying reports. Mandatory rotation after two consecutive periods disrupts relationship-based capture. The community review session provides a structural check: participants who interact with the affected pools can flag discrepancies between the report's findings and their lived experience.

## I. Failure Containment Logic

- **Pool steward fails to report**: monitors flag the missing report immediately. Level 1 notification goes to the steward with a 7-day deadline. If the deadline passes, Level 2 triggers a governing circle review of the steward's performance. Two consecutive missed reports escalate to Level 3 with temporary steward authority suspension.
- **Monitor fails to complete report**: the monitoring calendar assigns backup monitors. If the primary monitor misses the reporting deadline by 7 days, the backup monitor takes over. Persistent monitor failure triggers a role-assignment review.
- **Community review session has low attendance**: the session proceeds with whoever attends, but findings that trigger Level 2+ responses require a minimum attendance threshold (default: 25% of the pool's governing circle). If attendance is below threshold, Level 2+ actions are deferred until a follow-up session achieves quorum.
- **Threshold configuration produces false positives**: if a threshold is breached repeatedly but the community review consistently finds no actual problem, the monitoring configuration is reviewed. Thresholds may be adjusted upward through the ACT amendment process. Monitors document the pattern to support the adjustment proposal.
- **Data integrity concerns**: if monitors suspect that transaction log data is incomplete or inaccurate, they flag the concern in the report and recommend a Level 4 formal investigation of the affected pool's record-keeping practices.

## J. Expiry / Review Condition

- Commons health reports do not expire. They remain in the agreement registry as permanent records for trend analysis.
- The monitoring calendar is reviewed annually as part of the ecosystem governance review. The review examines: reporting frequency adequacy, threshold appropriateness, monitor rotation effectiveness, and community review session participation.
- Graduated response restrictions (Level 3) expire at their defined end date (maximum 90 days). Expiring restrictions trigger a review: was the restriction effective? Should it be renewed, modified, or allowed to lapse?
- Monitor assignments rotate every two reporting periods (default: every 6 months for quarterly reporting cycles). Rotation dates are tracked through the role-assignment skill.
- Threshold configurations are reviewed whenever a pool governance agreement is reviewed, and whenever the monitoring data reveals that thresholds need recalibration.

## K. Exit Compatibility Check

When a monitor exits the ecosystem:
- The monitoring responsibilities transfer immediately to the backup monitor or the next person in the rotation schedule.
- Reports in progress transfer to the successor. The departing monitor completes a handover document summarizing data collected so far and any patterns observed.
- The departing monitor's past reports remain valid and unchanged in the agreement registry.

When a pool steward who is subject to active monitoring exits:
- The commons-monitoring skill flags the transition as a data continuity risk. The successor steward must produce a reconciliation report within 30 days of assuming the role.
- Active graduated responses targeting the departing steward are reassessed: if the response targeted individual behavior, it may be closed; if it targeted structural patterns, it continues under the successor.

When 30%+ of participants exit:
- Monitoring continues with reduced scope. Pools that lose stewards are flagged for immediate data collection before transition gaps create blind spots.
- Threshold calculations adjust to the new participant count. Concentration thresholds recalibrate based on the smaller ecosystem.

## L. Cross-Unit Interoperability Impact

- Each ETHOS runs its own commons monitoring for its circle-level pools. Ecosystem-level monitoring aggregates data across all ETHOS.
- Cross-ETHOS shared pools are monitored jointly by monitors from each participating ETHOS. The reporting cycle follows the pool's governance agreement, which all ETHOS consented to.
- Ecosystem-level commons health reports synthesize findings from all ETHOS-level reports. The ecosystem report identifies cross-unit patterns: resource concentration in specific locations, reciprocity imbalances between ETHOS, and sustainability risks that span multiple units.
- Monitor rotation across ETHOS prevents geographic capture: monitors from SHUR Bali may rotate to monitor SHUR Portugal pools, and vice versa. Cross-ETHOS monitoring provides fresh perspective.
