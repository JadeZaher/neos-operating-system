---
name: structural-diversity-maintenance
description: "Proactively maintain the structural conditions that resist governance capture -- diverse proposal authorship, equitable approval rates, distributed funding, leadership rotation, and broad participation -- through bounded interventions with sunset dates."
layer: 7
version: 0.1.0
depends_on: [governance-health-audit, capture-pattern-recognition, domain-mapping]
---

# structural-diversity-maintenance

## C. Trigger Conditions

- **Scheduled review**: semi-annually by default (configurable per ETHOS, minimum annually), offset from governance-health-audit to create a continuous improvement cycle
- **Post-audit recommendation**: when a Governance Health Report recommends a diversity review for any indicator
- **Post-assessment recommendation**: when a Capture Assessment Report identifies structural diversity gaps contributing to capture risk
- **Proactive threshold**: when any diversity dimension drops to within 10% of its warning threshold (before the threshold is actually crossed), a proactive review is triggered
- **Post-intervention review**: when a structural intervention reaches its sunset date, a review evaluates its effectiveness and determines renewal, modification, or retirement

## D. Required Inputs

- **Governance Health Report**: the most recent audit data for the scope, particularly indicators GHI-01 (proposal authorship diversity), GHI-02 (approval rate equity), GHI-03 (resource concentration), GHI-04 (participation trend), and GHI-05 (leadership tenure)
- **Historical diversity data**: at least 2 quarters of governance data for trend analysis (if unavailable, note as "insufficient baseline")
- **Active intervention registry**: all currently active structural interventions within the scope, with their sunset dates and effectiveness metrics
- **Capture Assessment Reports**: recent capture assessments for the scope, to ensure diversity maintenance addresses identified capture vulnerabilities
- **Participant feedback**: qualitative input from ecosystem members about barriers to participation, proposal authorship, and leadership candidacy (collected through surveys or facilitated discussions, not mandatory)

## E. Step-by-Step Process

1. **Confirm review scope and authority.** The review initiator confirms the scope (ETHOS or ecosystem) and authority within the domain via domain-mapping. Diversity reviews can be initiated by any ecosystem member without co-signers -- proactive maintenance is a standing invitation, not a threshold-gated process. Timeline: confirmation within 3 days.
2. **Appoint review team.** The team consists of at least two participants from diverse positions within the ecosystem (not all leadership, not all the same circle). At least one member should be from a group underrepresented in the current governance data. Appointment follows the role-assignment skill.
3. **Assess each diversity dimension.** The team evaluates the five core diversity dimensions against current governance data:
   - **Proposal authorship distribution**: What percentage of proposals come from unique authors? Is authorship concentrating or broadening? (References GHI-01)
   - **Approval rate equity**: Are proposals from different roles/groups approved at similar rates? (References GHI-02)
   - **Funding source diversification**: How many independent funding sources exist? Is any source approaching concentration thresholds? (References GHI-03)
   - **Leadership rotation compliance**: Are leadership roles rotating per agreed schedules? Are the same individuals cycling through multiple leadership positions? (References GHI-05)
   - **Participation breadth**: What percentage of eligible members actively participate in governance? Is participation narrowing? (References GHI-04)
4. **Identify erosion patterns.** For each dimension showing decline or approaching warning thresholds, the team identifies the structural conditions causing the erosion. Structural conditions include: time-zone barriers, language barriers, meeting scheduling patterns, information access gaps, onboarding gaps, proposal complexity norms, and informal social networks that concentrate influence.
5. **Design structural interventions.** For each identified erosion pattern, the team designs a bounded intervention that encourages or enables diversity without filtering or blocking. Interventions must meet four criteria: (a) they encourage or enable, never filter or block, (b) they have a defined sunset date (default: 6 months, maximum 12 months), (c) they have measurable success criteria, and (d) they are installed through the ACT consent process. Examples: proposal mentorship for first-time authors, rotating meeting times across time zones, translation support for multilingual ecosystems, leadership shadowing programs, information digest publications.
6. **Enter ACT process for intervention installation.** Each proposed intervention goes through Advice and Consent phases. During consent, participants evaluate whether the intervention is proportionate, non-gatekeeping, and has appropriate success criteria and sunset date. Timeline: 5-10 days advice, 5-7 days consent.
7. **Implement interventions.** Approved interventions are registered in the active intervention registry with: intervention ID, target dimension, action description, responsible steward, start date, sunset date, success criteria, and effectiveness metrics.
8. **Monitor effectiveness.** At each subsequent governance data collection cycle, the review team (or their successors) evaluate whether the intervention is producing measurable improvement on its target dimension. Effectiveness data is included in the Structural Diversity Report.
9. **Compile the Structural Diversity Report.** Assemble the report using `assets/diversity-report-template.yaml`, including all dimension assessments, erosion patterns, active interventions with effectiveness data, new intervention recommendations, and sunset review outcomes.
10. **Publish and schedule next review.** The report is published to all ecosystem members. The next review is scheduled per the default cadence (semi-annual) or earlier if intervention sunset dates require it.

## F. Output Artifact

A Structural Diversity Report following `assets/diversity-report-template.yaml`. The report contains: report ID, review scope, review period, review team identities, and for each of the five diversity dimensions: current metric, trend (improving/stable/degrading), proximity to warning threshold, identified erosion patterns, and active or recommended interventions. The report also includes: active intervention registry with effectiveness metrics, interventions reaching sunset (with renewal/modification/retirement recommendations), and new intervention proposals. The report is accessible to all ecosystem members.

## G. Authority Boundary Check

- **Any ecosystem member** can request a diversity review without co-signers -- the bar is intentionally lower than audit or assessment requests because proactive maintenance benefits from broad initiation
- **The review team** assesses diversity dimensions and recommends interventions but cannot mandate governance changes
- **All structural interventions** require ACT consent before implementation -- the review team proposes, the ecosystem consents
- **Interventions encourage and enable, never filter or block** -- no intervention can restrict who may propose, who may participate, or who may lead. Interventions remove barriers; they do not create new barriers
- **All interventions have sunset dates** -- no permanent structural modifications through this skill. If an intervention should become permanent, it is formalized through the agreement-creation skill (Layer I)
- **The review team** cannot claim authority over governance composition or outcomes -- diversity is maintained through structural conditions, not quotas or mandates

## H. Capture Resistance Check

**Capital capture.** Funding source diversification is a core dimension. The skill proactively monitors funding concentration before it reaches safeguard trigger thresholds and recommends diversification campaigns. Interventions might include: grant writing support for alternative funding sources, community contribution programs, or in-kind resource sharing. The skill does not restrict any funding source -- it encourages alternatives. A major funder cannot prevent a diversification campaign because the campaign does not reduce their funding; it increases the total funding pool.

**Charismatic capture.** Proposal authorship diversity and approval rate equity directly address the conditions that enable charisma capture. When a single personality dominates proposal authorship, the skill recommends proposal mentorship programs that help other members develop and submit proposals. When approval rates are skewed, the skill recommends process reviews that examine why some proposers' work receives less scrutiny. These interventions address structural conditions without targeting any individual.

**Emergency capture.** The skill monitors participation breadth, which degrades during and after emergencies when normal governance is compressed and fewer voices are heard. Post-emergency diversity reviews assess whether emergency-period governance concentration has become structural and recommend participation re-engagement interventions.

**Informal capture.** The skill addresses the structural conditions that enable informal capture: information access inequality, onboarding gaps that create dependency relationships, and meeting norms that favor certain communication styles. Interventions like information digests, structured onboarding, and rotating facilitation reduce the informal advantages that enable invisible power concentration.

## I. Failure Containment Logic

- **Insufficient data**: if fewer than 2 quarters of governance data exist, the review proceeds as a "baseline diversity scan" with intervention recommendations focused on establishing measurement infrastructure rather than corrective actions
- **Review team cannot be formed**: if no diverse review team can be assembled (itself a diversity indicator), the skill escalates to the OSC with the recommendation that diversity has degraded to a level requiring ecosystem-level attention
- **Intervention fails consent**: if a proposed intervention cannot achieve consent, the review team documents the objections, revises the intervention, or proposes an alternative. The underlying diversity concern remains documented in the report regardless of intervention outcome
- **Intervention produces no measurable improvement**: if an intervention reaches its sunset date with no measurable improvement, it is retired by default. The review team may propose a modified version through a new ACT process, but failed interventions do not auto-renew
- **Diversity maintenance becomes compliance theater**: if the review team identifies that diversity reports are being produced but interventions are not being implemented, they escalate to the OSC and flag the pattern in the report as "process without substance" -- itself a form of ossification capture
- **Gatekeeping risk**: if any proposed intervention could be interpreted as filtering or blocking (e.g., "only new members can propose this quarter"), the consent phase must explicitly evaluate the gatekeeping risk and the intervention must be redesigned to encourage rather than restrict

## J. Expiry / Review Condition

Structural Diversity Reports are historical records and do not expire. All structural interventions have mandatory sunset dates (default: 6 months). When an intervention's sunset date arrives, a review evaluates effectiveness against the defined success criteria. Interventions that have met their goals are retired with documentation. Interventions that show partial progress may be renewed for one additional term through ACT consent. Interventions that show no progress are retired. The diversity review schedule itself is reviewed annually through the ACT process. The minimum review frequency (annual) cannot be reduced below this floor. If a scheduled review is missed, an automatic escalation notice is sent to all ecosystem members.

## K. Exit Compatibility Check

When a participant who served on a diversity review team exits, their contributions remain in published reports. If the exiting participant was responsible for stewarding an active intervention, the stewardship transfers to a replacement appointed via role-assignment within the 30-day wind-down period. Active interventions do not expire when their steward exits -- they continue to their sunset date. If a mass exit disproportionately affects a specific group (e.g., all members from a particular background or role), the skill triggers an immediate diversity review to assess the structural impact and recommend interventions that address the resulting gaps. Exiting participants retain no ongoing obligation related to diversity maintenance.

## L. Cross-Unit Interoperability Impact

Structural Diversity Reports from all ETHOS are published to the ecosystem, enabling cross-unit learning about effective interventions. When one ETHOS develops a successful intervention (e.g., a proposal mentorship program that increased authorship diversity by 20%), the intervention template is shared for other ETHOS to adapt through their own ACT processes. Cross-ETHOS diversity comparison is informational -- structural differences between ETHOS (size, age, cultural context) affect diversity metrics. The OSC reviews ecosystem-wide diversity trends annually and may recommend coordinated interventions for systemic patterns. When two NEOS ecosystems federate (Layer V, deferred), diversity maintenance practices may be shared, but each ecosystem designs and implements its own interventions through its own ACT process.
