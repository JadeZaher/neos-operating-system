---
name: commons-monitoring
description: "Track resource flows across funding pools and commons resources, detect over-draw or concentration, and trigger graduated community responses -- monitoring by the community, not external auditors or opaque algorithms."
layer: 4
version: 0.1.0
depends_on: [funding-pool-stewardship, domain-mapping]
---

# commons-monitoring

## A. Structural Problem It Solves

Without systematic monitoring, resource flows become invisible. A single circle might draw 60% of ecosystem resources without anyone noticing until the other circles' pools are depleted. A steward might make a pattern of borderline-discretionary disbursements that individually fall below scrutiny thresholds but collectively constitute a capture pattern. Resource concentration, reciprocity imbalances, and unsustainable draw rates go undetected until crisis forces a reactive response. Commons-monitoring prevents this by making resource flows visible, measurable, and community-reviewed. Following Ostrom's Principle 4, monitoring is performed by community members who have direct stake in the commons -- not by external auditors who lack context or by algorithms that lack accountability. The skill defines what gets monitored, who monitors it, how often, what thresholds trigger what responses, and how the community reviews monitoring data without allowing monitors to become gatekeepers.

## B. Domain Scope

This skill applies to all funding pools, resource flows, and commons assets within the ecosystem. Monitoring dimensions include: flow rate (how fast resources move through pools), concentration (whether resources accumulate in specific circles or individuals), reciprocity (whether resource flows are balanced across the ecosystem), sustainability (whether draw rates can be maintained over time), and accessibility (whether all eligible participants can effectively access resources). The skill covers both quantitative monitoring (balance tracking, flow analysis, threshold detection) and qualitative monitoring (community observations, pattern recognition, stewardship quality). Out of scope: individual behavior surveillance (monitoring tracks resource flows, not people), governance decision quality assessment (that belongs to agreement-review in Layer I), and systemic capture detection at the ecosystem level (Layer VII Safeguard, deferred). The skill monitors the economic commons; it does not police participants.

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

- Each AZPO runs its own commons monitoring for its circle-level pools. Ecosystem-level monitoring aggregates data across all AZPOs.
- Cross-AZPO shared pools are monitored jointly by monitors from each participating AZPO. The reporting cycle follows the pool's governance agreement, which all AZPOs consented to.
- Ecosystem-level commons health reports synthesize findings from all AZPO-level reports. The ecosystem report identifies cross-unit patterns: resource concentration in specific locations, reciprocity imbalances between AZPOs, and sustainability risks that span multiple units.
- Monitor rotation across AZPOs prevents geographic capture: monitors from SHUR Bali may rotate to monitor SHUR Portugal pools, and vice versa. Cross-AZPO monitoring provides fresh perspective.
- Cross-ecosystem commons monitoring (between separate NEOS ecosystems) uses the inter-unit coordination protocol (Layer V, deferred).

## OmniOne Walkthrough

It is the end of Q1 2026 and the quarterly commons monitoring cycle begins. The monitor rotation has assigned Kai (an AE member from the Technology circle) and Soleil (a TH member) as the monitoring pair for this quarter. Neither Kai nor Soleil is a pool steward for any of the pools they monitor -- the rotation ensured separation.

Kai and Soleil collect balance reports and transaction logs from all 12 active funding pools across OmniOne. Eleven stewards submit on time. The Agriculture circle steward, Ravi, misses the 7-day reporting deadline. Kai sends a Level 1 notification to Ravi and the Agriculture circle, documenting the missed report.

Dimension calculations reveal the following:
- **Flow rate**: Ecosystem-wide outflows exceeded inflows by 8% this quarter -- the first quarter this has occurred. The Education circle pool shows a 22% outflow-to-inflow imbalance for the second consecutive quarter, triggering the two-period flag.
- **Concentration**: The Infrastructure circle drew 40% of the Ecosystem Strategic Pool's outflows this quarter, breaching the 30% concentration threshold. This is driven by a single large allocation for renewable energy installation at SHUR Bali.
- **Reciprocity**: All circles fall within the 3:1 receive-to-contribute ratio. No flags.
- **Sustainability**: The Education circle pool is projected to deplete in 5 months at current draw rate. The Ecosystem Strategic Pool is sustainable for 18+ months.
- **Accessibility**: 62% of eligible participants submitted at least one resource request in the past two quarters. Above the 40% threshold, but down from 71% last quarter.

Kai and Soleil draft the commons health report. They flag two primary concerns: the Infrastructure circle's 40% concentration in the strategic pool, and the Education circle's sustainability trajectory. They gather community observations: three participants mention that the resource-request process feels cumbersome for small requests, which may explain the accessibility decline.

The community review session convenes at TH with 45 of 120 active participants attending (37.5%, above the 25% minimum). Kai presents the quantitative findings. Soleil presents the community observations. The facilitator, Amara, ensures discussion stays on patterns rather than blaming the Infrastructure circle.

Discussion reveals that the Infrastructure circle's 40% draw reflects a one-time capital expenditure for the SHUR Bali solar installation, not a recurring pattern. The Infrastructure circle steward, Naveen, presents the project's timeline showing the expenditure is complete and will not recur next quarter. The community review session concludes that Level 1 notification is sufficient: the Infrastructure circle acknowledges the concentration, and the community accepts the one-time nature of the expenditure. If concentration persists next quarter, it escalates to Level 2.

The Education circle sustainability concern triggers Level 2: the Education circle's governing body reviews their pool governance agreement and identifies that two standing allocations from previous participatory assemblies are consuming resources faster than inflows replenish them. The circle commits to renegotiating one standing allocation at their next assembly.

The accessibility decline prompts a recommendation (not a graduated response): the ecosystem reviews whether the resource-request process for small amounts (under 2% of pool balance) can be streamlined. This recommendation enters the agreement registry as an action item for the next ecosystem governance review.

Ravi submits the Agriculture circle's late report 5 days after the Level 1 notification. The data is complete and shows no threshold breaches. The late report is noted in the commons health report but does not escalate further.

## Stress-Test Results

### 1. Capital Influx

A philanthropic foundation grants OmniOne $200,000, deposited into the Ecosystem Strategic Pool. The next quarterly monitoring report shows a dramatic shift in flow rate and concentration metrics. The pool balance has quintupled, distorting percentage-based thresholds: previously significant disbursements now register as tiny percentages. Monitors flag this as a threshold recalibration event. The community review session examines whether existing thresholds remain meaningful at the new pool size. The session recommends adjusting concentration thresholds to use both percentage and absolute amount triggers -- a disbursement of $30,000 to a single circle triggers review regardless of percentage. The threshold adjustment enters ACT for consent. The monitoring report also tracks whether the influx correlates with changes in proposal patterns: are participants requesting larger amounts now that the pool is bigger? Are new participants suddenly interested in the strategic pool? These pattern observations feed into the next quarter's analysis without requiring immediate action.

### 2. Emergency Crisis

A fire at SHUR Bali destroys shared workshop facilities. The emergency reserve pool disburses $12,000 within 48 hours through the compressed resource-request process. The commons-monitoring skill triggers mandatory post-emergency monitoring. Monitors compile a special report within 14 days examining: was the $12,000 amount appropriate for the damage? Were the emergency funds used for their stated purpose? Did the emergency disbursement bypass any governance safeguards that should have applied? The post-emergency report finds that $10,500 was used for immediate repairs and $1,500 for temporary workspace rental -- both aligned with the emergency request. The report also assesses whether the emergency reserve pool needs replenishment and recommends a special inflow allocation from the ecosystem strategic pool. At no point does the emergency justify suspending regular quarterly monitoring. The next quarterly report includes the emergency disbursement in its flow analysis.

### 3. Leadership Charisma Capture

Marcus, a charismatic circle steward, has been making a pattern of discretionary disbursements that individually fall below the 5% threshold but collectively total 14% of pool balance this quarter. The commons-monitoring skill catches this through the cumulative pattern threshold (15%). The quarterly report flags Marcus's circle as approaching the cumulative discretionary threshold. At the community review session, Marcus argues persuasively that each individual disbursement was justified and that the pattern is coincidental. The facilitator ensures the session evaluates the quantitative pattern, not Marcus's persuasive explanation. The graduated response activates at Level 1: notification and request for context. Marcus provides transaction-by-transaction justification. At the next quarter, if cumulative discretionary disbursements again approach the threshold, Level 2 triggers a governance review of the pool's discretionary threshold -- regardless of how convincingly Marcus explains each transaction.

### 4. High Conflict / Polarization

Two factions within OmniOne disagree about whether the commons health report should include data on individual participant resource draws or only circle-level aggregates. Privacy advocates argue that individual-level data enables social shaming. Transparency advocates argue that circle-level data hides concentration within circles. The conflict threatens to derail the community review session. The facilitator invokes GAIA Level 3 structured dialogue: each faction states the other's position before advancing their own. At Level 4, a coach facilitates a third-solution exploration. The resulting compromise: the commons health report publishes circle-level aggregates as the default view, but individual-level data is available upon request to any participant through the transparency log. Threshold triggers operate on both levels -- a circle-level concentration breach and an individual-level concentration breach can both trigger the graduated response. The coach ensures neither faction frames the resolution as a win or loss.

### 5. Large-Scale Replication

OmniOne scales to 5,000 participants, 80 circles, and 150+ active funding pools. Commons monitoring scales through nested reporting: each AZPO's monitors produce AZPO-level reports, and ecosystem-level monitors synthesize these into an ecosystem health report. No single monitor pair oversees 150 pools. The monitoring calendar staggers reporting cycles so ecosystem monitors receive a steady stream of AZPO reports rather than 80 reports on the same day. Threshold configurations vary by pool type and size -- a circle operational pool with $2,000 uses different absolute thresholds than an ecosystem strategic pool with $200,000, though percentage thresholds remain consistent. The agreement registry tracks monitoring data with consistent metadata across all pools, enabling trend analysis at every scale. Monitor rotation at scale draws from a larger pool of trained monitors, reducing rotation burden on any individual.

### 6. External Legal Pressure

The Indonesian government requires all organizations managing collective funds to submit annual financial reports to the local tax authority. The commons health report already contains most of the required data in a structured format. The SHUR Bali steward creates a compliance export that maps commons health report data to the government's reporting template. The compliance export includes only financial data from SHUR Bali pools -- Current-See flows and non-financial resource flows are excluded as they have no legal reporting obligation. The compliance requirement does not alter the commons monitoring process itself. OmniOne does not grant the tax authority access to the full commons health report or the monitoring dimension analysis -- the compliance export contains only what is legally required. The UAF sovereignty principle ensures that Indonesian regulatory requirements do not propagate to monitoring practices in other jurisdictions.

### 7. Sudden Exit of 30% of Participants

After 1,500 members exit OmniOne, the commons-monitoring skill triggers an immediate ecosystem-wide resource health assessment -- this is a structural trigger, not a discretionary decision. Monitors compile an emergency interim report focusing on: which pools lost their stewards (and therefore their reporting sources), which pools experienced sudden inflow reductions, and which threshold calculations need recalibration for the smaller ecosystem. Concentration thresholds recalibrate: a circle that previously drew 25% of ecosystem resources might now draw 35% simply because the denominator shrank. Monitors distinguish between genuine concentration increases and mathematical artifacts of reduced ecosystem size. The interim report identifies pools at risk of insolvency due to lost inflows and recommends governance reviews for those pools. The report also tracks whether the mass departure clustered in specific circles or locations, revealing whether certain parts of the ecosystem are disproportionately affected. Regular quarterly monitoring resumes on schedule with the smaller participant base, using recalibrated thresholds.
