---
skill: commons-monitoring
type: rationale
---

# commons-monitoring — Rationale & Design Notes

## A. Structural Problem It Solves

Without systematic monitoring, resource flows become invisible. A single circle might draw 60% of ecosystem resources without anyone noticing until the other circles' pools are depleted. A steward might make a pattern of borderline-discretionary disbursements that individually fall below scrutiny thresholds but collectively constitute a capture pattern. Resource concentration, reciprocity imbalances, and unsustainable draw rates go undetected until crisis forces a reactive response. Commons-monitoring prevents this by making resource flows visible, measurable, and community-reviewed. Following Ostrom's Principle 4, monitoring is performed by community members who have direct stake in the commons -- not by external auditors who lack context or by algorithms that lack accountability. The skill defines what gets monitored, who monitors it, how often, what thresholds trigger what responses, and how the community reviews monitoring data without allowing monitors to become gatekeepers.

## B. Domain Scope

This skill applies to all funding pools, resource flows, and commons assets within the ecosystem. Monitoring dimensions include: flow rate (how fast resources move through pools), concentration (whether resources accumulate in specific circles or individuals), reciprocity (whether resource flows are balanced across the ecosystem), sustainability (whether draw rates can be maintained over time), and accessibility (whether all eligible participants can effectively access resources). The skill covers both quantitative monitoring (balance tracking, flow analysis, threshold detection) and qualitative monitoring (community observations, pattern recognition, stewardship quality). Out of scope: individual behavior surveillance (monitoring tracks resource flows, not people), governance decision quality assessment (that belongs to agreement-review in Layer I), and systemic capture detection at the ecosystem level (Layer VII Safeguard, deferred). The skill monitors the economic commons; it does not police participants.

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

OmniOne scales to 5,000 participants, 80 circles, and 150+ active funding pools. Commons monitoring scales through nested reporting: each ETHOS's monitors produce ETHOS-level reports, and ecosystem-level monitors synthesize these into an ecosystem health report. No single monitor pair oversees 150 pools. The monitoring calendar staggers reporting cycles so ecosystem monitors receive a steady stream of ETHOS reports rather than 80 reports on the same day. Threshold configurations vary by pool type and size -- a circle operational pool with $2,000 uses different absolute thresholds than an ecosystem strategic pool with $200,000, though percentage thresholds remain consistent. The agreement registry tracks monitoring data with consistent metadata across all pools, enabling trend analysis at every scale. Monitor rotation at scale draws from a larger pool of trained monitors, reducing rotation burden on any individual.

### 6. External Legal Pressure

The Indonesian government requires all organizations managing collective funds to submit annual financial reports to the local tax authority. The commons health report already contains most of the required data in a structured format. The SHUR Bali steward creates a compliance export that maps commons health report data to the government's reporting template. The compliance export includes only financial data from SHUR Bali pools -- Current-See flows and non-financial resource flows are excluded as they have no legal reporting obligation. The compliance requirement does not alter the commons monitoring process itself. OmniOne does not grant the tax authority access to the full commons health report or the monitoring dimension analysis -- the compliance export contains only what is legally required. The UAF sovereignty principle ensures that Indonesian regulatory requirements do not propagate to monitoring practices in other jurisdictions.

### 7. Sudden Exit of 30% of Participants

After 1,500 members exit OmniOne, the commons-monitoring skill triggers an immediate ecosystem-wide resource health assessment -- this is a structural trigger, not a discretionary decision. Monitors compile an emergency interim report focusing on: which pools lost their stewards (and therefore their reporting sources), which pools experienced sudden inflow reductions, and which threshold calculations need recalibration for the smaller ecosystem. Concentration thresholds recalibrate: a circle that previously drew 25% of ecosystem resources might now draw 35% simply because the denominator shrank. Monitors distinguish between genuine concentration increases and mathematical artifacts of reduced ecosystem size. The interim report identifies pools at risk of insolvency due to lost inflows and recommends governance reviews for those pools. The report also tracks whether the mass departure clustered in specific circles or locations, revealing whether certain parts of the ecosystem are disproportionately affected. Regular quarterly monitoring resumes on schedule with the smaller participant base, using recalibrated thresholds.
