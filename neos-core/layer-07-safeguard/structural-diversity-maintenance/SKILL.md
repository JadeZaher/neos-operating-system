---
name: structural-diversity-maintenance
description: "Proactively maintain the structural conditions that resist governance capture -- diverse proposal authorship, equitable approval rates, distributed funding, leadership rotation, and broad participation -- through bounded interventions with sunset dates."
layer: 7
version: 0.1.0
depends_on: [governance-health-audit, capture-pattern-recognition, domain-mapping]
---

# structural-diversity-maintenance

## A. Structural Problem It Solves

Detection is necessary but not sufficient. The governance-health-audit skill measures governance health. The capture-pattern-recognition skill diagnoses capture patterns. The safeguard-trigger-design skill activates interventions when thresholds are crossed. But all of these are reactive -- they respond to degradation after it occurs. Robert Michels observed that oligarchy succeeds not through a single dramatic seizure but through gradual erosion of the conditions that resist it: participation narrows, proposal authorship concentrates, leadership calcifies, and by the time indicators cross critical thresholds, the structural damage is deep. This skill moves upstream. It proactively maintains the conditions that make capture structurally difficult: diverse proposal authorship, equitable approval rates, distributed funding sources, regular leadership rotation, and broad participation. The distinction matters: detection asks "has capture occurred?" while structural diversity maintenance asks "are the conditions that prevent capture being actively renewed?"

## B. Domain Scope

This skill applies to any AZPO or ecosystem where governance diversity can be measured and maintained. It examines the same governance data as the audit skill (decision logs, resource allocation, participation records, proposal registries, role-assignment histories) but through a proactive lens -- identifying where diversity is eroding before it crosses safeguard trigger thresholds. The domain boundary follows domain-mapping (Layer II). Out of scope: this skill does not diagnose capture (that is capture-pattern-recognition), does not collect raw data (that is independent-monitoring), and does not activate safeguard triggers (that is safeguard-trigger-design). This skill designs and recommends structural interventions that encourage and enable diversity -- it does not filter, block, or gatekeep governance participation.

## C. Trigger Conditions

- **Scheduled review**: semi-annually by default (configurable per AZPO, minimum annually), offset from governance-health-audit to create a continuous improvement cycle
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

1. **Confirm review scope and authority.** The review initiator confirms the scope (AZPO or ecosystem) and authority within the domain via domain-mapping. Diversity reviews can be initiated by any ecosystem member without co-signers -- proactive maintenance is a standing invitation, not a threshold-gated process. Timeline: confirmation within 3 days.
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

Structural Diversity Reports from all AZPOs are published to the ecosystem, enabling cross-unit learning about effective interventions. When one AZPO develops a successful intervention (e.g., a proposal mentorship program that increased authorship diversity by 20%), the intervention template is shared for other AZPOs to adapt through their own ACT processes. Cross-AZPO diversity comparison is informational -- structural differences between AZPOs (size, age, cultural context) affect diversity metrics. The OSC reviews ecosystem-wide diversity trends annually and may recommend coordinated interventions for systemic patterns. When two NEOS ecosystems federate (Layer V, deferred), diversity maintenance practices may be shared, but each ecosystem designs and implements its own interventions through its own ACT process.

## OmniOne Walkthrough

It is July 2026, and the Q1 Governance Health Report for SHUR Bali flagged GHI-01 (Proposal Authorship Diversity) at warning: 43%, with only 12 unique authors among 28 proposals. A deeper look reveals that 22 of the 28 proposals were authored by just 3 AE members: Nadia, Dewa, and Ketut. The remaining 16 active members of SHUR Bali submitted only 6 proposals combined, and 22 members submitted none. Lina, an AE member who has never authored a proposal, requests a structural diversity review.

The review team is appointed: Sari, a TH member who has authored 2 proposals (representing active but not dominant participation), and Marcus, a recently joined AE member who has not yet participated in governance (representing the underrepresented perspective). The team assesses the five diversity dimensions:

- **Proposal authorship distribution**: 3 of 38 members author 79% of proposals. Heavily concentrated. Trend: degrading from Q4 2025 (52% concentration).
- **Approval rate equity**: Ratio 0.82, healthy. No significant disparity between roles.
- **Funding source diversification**: GEV at 35%, warning but stable. No immediate intervention needed.
- **Leadership rotation**: Ketut at 3 cycles, warning. Flagged but addressed separately by role-assignment review.
- **Participation breadth**: Meeting attendance stable at 82%, but proposal participation (authoring, formal commenting) is only 32%.

The team identifies the erosion pattern: proposal authorship is concentrated not because other members are excluded, but because the proposal process is intimidating. SHUR Bali's proposals have averaged 8 pages with financial projections, reference citations, and impact assessments. New and less experienced members perceive a quality bar that discourages contribution. Additionally, Nadia, Dewa, and Ketut are experienced professionals who set an unintentional norm of "proposals look like consulting reports."

The team designs two structural interventions:

**Intervention 1: Proposal Mentorship Program.** Pair each willing first-time proposer with an experienced author for one proposal cycle. The mentor helps structure the proposal but does not co-author it. Success criteria: 5 new unique authors submit proposals in the next quarter. Sunset date: January 2027 (6 months). Responsible steward: Sari.

**Intervention 2: Simplified Proposal Template.** Create a 1-page "quick proposal" template for low-complexity decisions (resource requests under 500 Current-Sees, scheduling changes, process adjustments). This lowers the perceived quality bar without lowering the governance standard. Success criteria: 10 quick proposals submitted in the next quarter. Sunset date: January 2027 (6 months). Responsible steward: Marcus.

Both interventions enter the ACT process. During consent, Nadia objects to the simplified template: "Lower-quality proposals will waste everyone's time." Sari integrates: the quick template includes a scope limiter -- it can only be used for decisions within defined categories, and any member can request a full proposal if the decision scope exceeds the template's bounds. Nadia withdraws the objection. Both interventions achieve consent and are registered.

**Edge case.** By October 2026, the mentorship program has produced 4 new unique authors (below the goal of 5), but the quick proposal template has produced 14 submissions (exceeding the goal of 10). However, 8 of the 14 quick proposals were submitted by Dewa and Ketut, who discovered the template was easier to use for their routine requests. The intervention increased proposal volume but did not diversify authorship as intended. The review team documents this in the mid-cycle effectiveness check and proposes a modification: quick proposals from members who have authored 5+ proposals in the past year do not count toward the diversity metric. The modification enters ACT and achieves consent. The intervention continues with the adjusted success criteria.

## Stress-Test Results

### 1. Capital Influx

A corporate foundation offers SHUR Bali $4 million annually, making them the source of 62% of all resources. The structural diversity review examines funding source diversification (GHI-03 at critical) and designs a proactive intervention: a community-funded resource pool where every AZPO member contributes in-kind services or Current-Sees to create an independent resource base. The intervention does not restrict the corporate funding -- it creates alternatives. The review team also recommends a grant writing support program to help SHUR Bali apply for 3 additional independent funding sources. Both interventions have 6-month sunset dates and measurable success criteria (community pool reaches 15% of total resources; 2 new independent grants secured). The corporate foundation cannot block these interventions because they do not reduce corporate funding -- they dilute its structural influence by growing the total resource base. If the foundation threatens to withdraw funding unless the diversification campaign stops, that threat is itself documented as evidence of capital capture, strengthening the case for diversification.

### 2. Emergency Crisis

A severe earthquake disrupts SHUR Bali for two months. During the emergency, governance participation narrows to a core group of 8 members who can physically convene. When conditions normalize, the post-emergency diversity review reveals: participation breadth dropped from 82% to 21% during the emergency and has only recovered to 55%. Proposal authorship collapsed to the 8-member core group. Leadership rotation was suspended. The review team designs three interventions: a re-engagement campaign inviting all members to a participatory restart meeting, a rotating "emergency debrief" series where different members share their experiences (distributing the narrative across the community rather than concentrating it with emergency leadership), and a simplified proposal process for the recovery period to encourage broad participation. All interventions have 4-month sunset dates (shorter than default because recovery conditions change rapidly). The emergency compressed diversity; the interventions expand it back to pre-emergency levels without penalizing those who stepped up during the crisis.

### 3. Leadership Charisma Capture

SHUR Bali's diversity review reveals that Surya, a beloved founding member, has authored or co-authored 40% of all proposals in the past year. The review team's intervention does not target Surya -- it addresses the structural conditions that concentrate authorship. The proposal mentorship program pairs 6 members with experienced mentors (not Surya, to avoid deepening the dependency). The review also recommends "proposal writing circles" -- small groups that collaboratively develop proposals, distributing authorship and building capacity. The interventions encourage new authors without restricting Surya's right to propose. Over two quarters, unique authorship increases from 30% to 52%. Surya's absolute proposal count does not decrease, but other members' counts increase, shifting the distribution. The structural diversity approach addresses charisma capture without confrontation -- no one accused Surya of anything; the system simply invested in broadening the conditions that concentration had eroded.

### 4. High Conflict / Polarization

SHUR Bali is polarized over accepting a mining company's remediation partnership. The diversity review reveals that polarization has produced a participation drop (GHI-04 at -18%), with members from both factions disengaging from governance processes they perceive as dominated by the other faction. Proposal authorship has narrowed to faction leaders. The review team designs interventions that address participation breadth without taking sides: a "topic-free governance day" where proposals unrelated to the mining partnership are prioritized (restoring the experience of productive governance), a facilitated cross-faction dialogue using GAIA Level 3 coaching principles, and a proposal co-authorship program that pairs members from different factions on shared-interest proposals. All interventions have 4-month sunset dates. The interventions do not resolve the substantive conflict -- that is Layer VI's domain. They maintain the structural diversity conditions that prevent the conflict from permanently degrading governance capacity. If polarization causes one faction to dominate and the other to disengage entirely, the diversity skill identifies this as a structural emergency and escalates to the OSC.

### 5. Large-Scale Replication

OmniOne scales to 5,000 members across 15 SHUR locations. Each AZPO conducts its own diversity reviews and designs locally appropriate interventions. The five diversity dimensions remain consistent across all locations, enabling ecosystem-level comparison. The OSC reviews cross-AZPO diversity data annually and identifies systemic patterns: if 10 of 15 locations show declining proposal authorship diversity, the pattern suggests a structural issue in the NEOS proposal process itself, not local anomalies. Ecosystem-level interventions (e.g., updating the standard proposal template, creating a cross-AZPO mentorship network) are recommended for the ACT process. Intervention templates that prove effective at one location are shared as replicable patterns for other locations to adapt. At scale, diversity maintenance becomes a network learning function -- each AZPO experiments locally and the ecosystem learns collectively. The intervention registry format is standardized, enabling automated diversity trend tracking across the federation.

### 6. External Legal Pressure

Indonesian authorities require all co-living organizations to demonstrate "equitable governance" for regulatory compliance. A government liaison requests that SHUR Bali's Structural Diversity Report serve as the compliance document. The report is already public and can be shared with regulators. However, the regulator requests specific demographic diversity metrics (gender, age, nationality) that are not part of the NEOS governance diversity framework, which focuses on structural governance diversity (authorship, approval equity, participation) rather than demographic categories. The ecosystem can produce a separate compliance supplement derived from voluntarily disclosed demographic data without modifying the internal diversity framework. The UAF sovereignty principle holds: external requirements are met through additional documentation, not by altering the structural diversity definition to match regulatory categories. The review team documents the regulatory request as context so future reviews can track whether compliance requirements are reshaping internal governance priorities -- regulatory-driven diversity metrics that replace structural governance metrics would be a form of capture.

### 7. Sudden Exit of 30% of Participants

Following a contentious restructuring decision, 13 of 40 SHUR Bali members exit within two weeks. The mass exit triggers an immediate diversity review. The review reveals cascading impacts: proposal authorship diversity drops to critical (the departed group included 5 of 12 regular proposers), participation breadth drops to 68% of the reduced base, and funding diversification worsens because 2 independent grant contacts were among the departed. The review team designs emergency interventions: an accelerated proposal mentorship program (2-month sunset) to rebuild authorship capacity among remaining members, a community re-engagement dialogue to address the underlying grievance, and a funding recovery plan to replace lost grant relationships. Crucially, the interventions address the structural gaps without attempting to prevent the departures or delegitimize the concerns that motivated them. The diversity skill does not judge whether the mass exit was justified -- it assesses the structural diversity impact and designs interventions to restore the conditions that resist capture in the smaller community. All interventions are calibrated to the current 27-member base, not the prior 40-member base, acknowledging the ecosystem's new reality.
