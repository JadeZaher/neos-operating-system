---
name: independent-monitoring
description: "Establish and operate the independent monitor role -- a rotating, structurally separated function that collects and publishes raw governance health data without interpretation or decision authority."
layer: 7
version: 0.1.0
depends_on: [governance-health-audit, role-assignment, domain-mapping]
---

# independent-monitoring

## A. Structural Problem It Solves

Every governance health assessment depends on data, and whoever controls the data controls the narrative. When the same body that makes governance decisions also collects governance data, selection bias is inevitable: inconvenient indicators are measured less frequently, unflattering data is contextualized into irrelevance, and declining metrics are attributed to "measurement error" rather than systemic problems. Robert Michels observed that information asymmetry is one of the primary mechanisms by which leadership entrenches -- leaders know more than members, and that knowledge gap sustains their position. This skill breaks the information monopoly by establishing a structurally independent data collection function. The independent monitor collects raw governance data and publishes it without interpretation, ensuring that audit teams and capture assessors work from data they did not select, filter, or contextualize. The separation of data collection from data interpretation is the structural foundation on which every other Layer VII skill depends.

## B. Domain Scope

This skill applies to any ETHOS or ecosystem where governance health indicators are monitored. The monitor's data collection covers all 8 governance health indicators defined in `assets/indicator-definitions.yaml` (governance-health-audit): proposal authorship, approval rates, resource concentration, participation trends, leadership tenure, objection integration, review compliance, and cross-unit engagement. The domain boundary follows domain-mapping (Layer II) -- a monitor for SHUR Bali collects data within SHUR Bali's governance records only. Out of scope: the monitor does not interpret data (that is governance-health-audit), does not diagnose capture patterns (that is capture-pattern-recognition), and does not design or activate safeguards (that is safeguard-trigger-design). The monitor's authority is limited to collection and publication of raw data.

## C. Trigger Conditions

- **Scheduled collection**: monthly by default (configurable per ETHOS, minimum frequency: quarterly), aligned with governance data availability cycles
- **Audit preparation**: at least 14 days before a scheduled governance-health-audit, the monitor produces a comprehensive Governance Data Report for the audit period
- **On-demand request**: the audit team or capture assessment team requests specific data outside the regular collection cycle, with the request logged publicly
- **Post-emergency data collection**: following any emergency declaration (Layer VIII), the monitor collects governance data for the emergency period within 14 days of emergency conclusion
- **Monitor rotation**: when a new monitor assumes the role, a handoff data collection verifies continuity with the outgoing monitor's records

## D. Required Inputs

- **Data collection schedule**: the frequency and scope of data collection, defined per ETHOS and approved through the ACT process
- **Data source access**: authorized access to decision logs, proposal registries, resource allocation records, participation records, role-assignment records, and ACT process logs within the monitor's domain
- **Indicator definitions**: the 8 governance health indicators and their measurement formulas from `assets/indicator-definitions.yaml`
- **Prior data reports**: the previous Governance Data Report for continuity verification and trend baseline
- **Collection procedures**: standardized data extraction methods defined in `assets/governance-data-report-template.yaml` to ensure consistency across monitors and rotation cycles

## E. Step-by-Step Process

1. **Appoint the monitor.** The independent monitor is appointed through the role-assignment skill (Layer II). Eligibility requirements: the monitor must not hold a leadership role within the monitored scope, must not have held leadership within the monitored scope during the past 2 cycles, and must not be a current member of the OSC. The monitor is drawn from the general participant pool, prioritizing participants who have not recently served. Appointment follows the ACT consent process. Timeline: appointment confirmed at least 14 days before the monitor's term begins.
2. **Define term and rotation.** The monitor serves a 6-month term (configurable, minimum 3 months, maximum 12 months). Terms include a 1-month overlap with the incoming monitor for handoff training and data continuity verification. No participant serves consecutive monitor terms for the same scope. The rotation schedule is published to all ecosystem members.
3. **Collect data per schedule.** At each collection cycle, the monitor extracts raw data for each of the 8 governance health indicators from the defined data sources. The monitor records the measured value for each indicator exactly as calculated from the source data, with no rounding, adjustment, or contextual annotation. Each data point includes: indicator ID, measurement date, raw value, data source reference, and the monitor's identity.
4. **Verify data integrity.** The monitor cross-checks each data point against the source records. If a data point cannot be verified (source record missing, calculation ambiguous, or access denied), the monitor records the gap with the reason. Data integrity issues are flagged but do not prevent publication -- gaps are visible, not hidden.
5. **Compile the Governance Data Report.** The monitor assembles raw data into the Governance Data Report using `assets/governance-data-report-template.yaml`. The report contains: all indicator measurements, data source references, data gaps with explanations, collection date, monitor identity, and verification status for each data point. The report contains no interpretation, no trend analysis, no recommendations, and no commentary.
6. **Publish to all ecosystem members.** The Governance Data Report is published to every member within the monitor's domain and to the OSC. Publication is automatic upon compilation -- the monitor cannot withhold or delay publication. Any withholding attempt is logged as a critical governance health event.
7. **Respond to data requests.** When an audit team or capture assessment team requests specific data outside the regular cycle, the monitor collects and publishes it within 7 days. All data requests and responses are logged publicly.
8. **Handoff to incoming monitor.** During the 1-month overlap period, the outgoing monitor trains the incoming monitor on data sources, collection procedures, and access protocols. The incoming monitor independently replicates the most recent data collection and compares results with the outgoing monitor's report. Discrepancies are documented and resolved before the outgoing monitor's term ends.

## F. Output Artifact

A Governance Data Report following `assets/governance-data-report-template.yaml`. The report contains: report ID, collection scope, collection period, monitor identity, collection date, and for each of the 8 indicators: indicator ID, indicator name, raw measured value, measurement formula applied, data source reference, verification status (verified/unverified/gap), and gap explanation if applicable. The report explicitly excludes interpretation, trend analysis, and recommendations. It is accessible to all ecosystem members within the monitor's domain and cannot be restricted to leadership.

## G. Authority Boundary Check

- **The monitor** has authority to access governance data within the defined scope but cannot access data outside the domain boundary established by domain-mapping
- **The monitor** collects and publishes data. The monitor has no authority to interpret data, diagnose capture patterns, recommend actions, or make governance decisions based on the data collected
- **No individual or body** can suppress, delay, or redact a Governance Data Report -- suppression attempts are logged as critical governance health events
- **Leadership of the monitored body** cannot appoint the monitor, remove the monitor mid-term (except through a formal accountability review via ACT), or approve the report before publication
- **The monitor** cannot be instructed to "contextualize" or "explain" data points -- the structural prohibition on interpretation is the monitor's primary independence protection
- **The OSC** receives all data reports but does not gate their publication or direct the monitor's collection activities

## H. Capture Resistance Check

**Capital capture.** The monitor's role is unpaid governance service -- funding sources cannot condition contributions on favorable monitoring outcomes. The monitor collects resource concentration data (GHI-03) from financial records that exist independently of the monitor's role. A funder who attempts to restrict the monitor's access to financial data triggers a critical governance health event. The structural separation between data collection and interpretation means that even if a funder could influence the monitor, the monitor cannot contextualize data favorably.

**Charismatic capture.** The monitor collects approval rate data (GHI-02) and objection patterns (GHI-06) from ACT process logs -- data that exists regardless of any individual's social influence. A charismatic leader cannot prevent the collection of their proposal approval rate. The prohibition on interpretation means the monitor cannot frame data to protect a popular leader. The rotation requirement prevents the monitor from developing a personal loyalty to the monitored body's leadership over time.

**Emergency capture.** The monitor collects data during emergency periods just as during normal operations. Emergency authority does not include authority over the monitor's data collection. The post-emergency data collection trigger ensures that governance data from the emergency period is captured and published even if normal collection cycles were disrupted.

**Informal capture.** The monitor's rotation schedule, term limits, and structural prohibition on interpretation prevent the monitor from becoming an informal information gatekeeper. The 1-month handoff overlap ensures institutional knowledge transfers without creating dependency on any individual monitor. The public logging of all data requests prevents informal data access arrangements.

## I. Failure Containment Logic

- **Monitor absent or incapacitated**: the backup monitor (appointed simultaneously with the primary monitor via role-assignment) assumes data collection responsibilities immediately. If no backup exists, the OSC appoints a temporary monitor from outside the monitored scope within 14 days
- **Data source access denied**: the monitor documents the access denial publicly, escalates to the domain steward, and if unresolved within 7 days, escalates to the OSC. The denial is recorded as a governance health event and the affected indicator is marked "gap -- access denied" in the data report
- **Data integrity concern**: if the monitor discovers evidence of data manipulation in source records (e.g., deleted decision logs, altered participation records), the monitor publishes the concern in the data report with specific evidence. The monitor does not investigate -- investigation authority belongs to governance-health-audit and capture-pattern-recognition
- **Monitor produces inaccurate data**: any ecosystem member can challenge a data point by referencing the source record. Challenged data points are re-verified by the backup monitor. Confirmed errors are corrected in a published addendum. Persistent inaccuracy triggers an accountability review of the monitor through the ACT process
- **Monitor attempts interpretation**: if a data report contains editorial commentary, trend analysis, or recommendations, any ecosystem member can flag the violation. The interpretive content is removed, the data is republished as raw data, and the monitor receives a formal reminder of role boundaries

## J. Expiry / Review Condition

The monitor's term expires at the end of the defined period (default: 6 months). Terms do not auto-renew -- the next monitor is appointed through the role-assignment skill. Governance Data Reports do not expire -- they are historical records. The data collection schedule is reviewed annually through the ACT process. The minimum collection frequency (quarterly) cannot be reduced below this floor. If a scheduled collection is missed, an automatic escalation notice is sent to all ecosystem members and the backup monitor is activated. The monitor role definition itself (eligibility requirements, authority boundaries, term limits) is reviewed every two years through the ACT process, or sooner if a structural concern is raised.

## K. Exit Compatibility Check

When the current monitor exits the ecosystem, the backup monitor assumes primary responsibilities immediately. The exiting monitor's data reports remain valid historical records. If the exiting monitor is mid-collection-cycle, the backup monitor completes the cycle using the same data sources and procedures. If both the primary and backup monitors exit simultaneously, the OSC appoints a temporary monitor within 14 days. The 30-day wind-down period applies: the exiting monitor completes any in-progress data collection before departure. Data collection procedures and source access documentation transfer to the backup or replacement monitor. No data reports are retracted due to monitor departure.

## L. Cross-Unit Interoperability Impact

Each ETHOS has its own independent monitor, collecting data within its domain boundary. Governance Data Reports from all ETHOS are published to all ecosystem members, enabling cross-unit data visibility. The standardized indicator definitions (`assets/indicator-definitions.yaml`) ensure that data from different ETHOS is comparable. When an ecosystem-wide audit is conducted, the ecosystem-level audit team aggregates ETHOS-level data reports. Cross-ETHOS data comparison is informational -- structural differences between ETHOS affect indicator values. The monitor for one ETHOS cannot collect data from another ETHOS's domain without a cross-domain data request through domain-mapping. When two NEOS ecosystems federate (Layer V, deferred), independent monitoring protocols may be shared to enable cross-ecosystem data transparency, but each ecosystem's monitors operate under their own appointment and accountability structures.

## OmniOne Walkthrough

It is January 2026, and the Bali SHUR ETHOS needs to appoint its first independent monitor for the year. The prior monitor, Wayan, has completed a 6-month term and is entering the 1-month handoff overlap. The role-assignment process produces a candidate: Ratu, a TH member who has been active in SHUR Bali for two years, holds no leadership role, and has not served on the OSC. Ratu's appointment enters the ACT consent phase. Ketut, the circle steward, asks during advice: "Can Ratu access the financial records she needs?" The financial steward confirms access. Consent is achieved with no objections.

Ratu begins her term on January 15. During the 1-month overlap, Wayan walks Ratu through the data collection procedures: how to extract proposal data from the decision log, how to calculate the approval rate ratio, how to access resource allocation records from the financial steward's quarterly report, and how to verify participation data against meeting attendance logs. Ratu independently replicates Wayan's December data collection. Her numbers match on 7 of 8 indicators; on GHI-08 (Cross-Unit Engagement), Ratu counts 6 cross-circle interactions while Wayan counted 5. They trace the discrepancy: Wayan excluded an informal cross-circle conversation that did not produce a decision; Ratu included it. They document the counting rule clarification (cross-unit interactions require a recorded outcome, not just a conversation) and align on the standard. Wayan's term ends February 15.

For Q1 2026, Ratu collects data monthly (January, February, March). Each month she extracts raw values for all 8 indicators, records them in the Governance Data Report template, verifies each data point against source records, and publishes to all 38 SHUR Bali members and the OSC. Her March report includes:

- GHI-01: 12 unique authors / 28 proposals = 43% (data source: proposal registry, verified)
- GHI-02: Non-leadership approval 72%, leadership approval 88%, ratio 0.82 (data source: decision logs, verified)
- GHI-03: GEV provides 35% of resources (data source: financial quarterly report, verified)
- GHI-04: Average participation 82%, prior period 85%, change -3% (data source: attendance logs, verified)
- GHI-05: Circle steward Ketut at 3 consecutive cycles (data source: role-assignment records, verified)
- GHI-06: 8/11 objections integrated = 73% (data source: ACT consent logs, verified)
- GHI-07: 14/18 agreements reviewed on time = 78% (data source: agreement registry, verified)
- GHI-08: 5 cross-circle interactions (data source: cross-unit coordination logs, verified)

Ratu publishes these numbers with no commentary, no trend analysis, and no recommendations. The audit team (Farid and Yuki) will interpret this data during the Q1 governance health audit.

**Edge case.** In February, Ketut asks Ratu to "add a note explaining that the participation dip is seasonal because many members travel during February." Ratu declines: "My role is to publish raw data without interpretation. The audit team can evaluate seasonal patterns when they interpret the report." Ketut's request and Ratu's refusal are both logged. This is not a conflict -- it is the structural boundary functioning as designed. Ratu does not have the authority to add context even if the context is accurate, because allowing contextual annotation would create a pathway for editorial influence.

## Stress-Test Results

### 1. Capital Influx

A major funder announces a $2 million annual contribution to SHUR Bali, conditional on priority placement for the funder's sustainability curriculum. The independent monitor, Ratu, collects resource allocation data as usual. GHI-03 shows the funder now provides 58% of total resources -- the raw number is published to all members without annotation. The funder's representative contacts Ratu and asks her to "provide context that the funding is a temporary transitional arrangement." Ratu declines -- her role prohibits interpretation or contextual framing. The request and refusal are logged. When the audit team later examines the data, they have clean, uncontextualized numbers showing a funding concentration that crossed into critical territory. The funder cannot influence the data by influencing the monitor because the monitor structurally cannot contextualize. If the funder attempts to restrict Ratu's access to financial records, the access denial is itself published as a governance health event. The structural separation between collection and interpretation means the funder would need to capture both the monitor and the audit team -- two independent functions with different appointment processes.

### 2. Emergency Crisis

A volcanic eruption forces SHUR Bali into emergency operations for six weeks. Normal data collection cycles are disrupted -- the March monthly collection does not occur because members are evacuated. Ratu documents the gap: "March data collection not completed. Reason: emergency evacuation, no access to governance records. Gap period: March 1-April 15." When conditions stabilize, the post-emergency data collection trigger activates. Ratu collects data for the entire emergency period (retroactively from available records) within 14 days of emergency conclusion. The data reveals 14 decisions made under emergency authority, all logged in the emergency decision register. Ratu publishes the raw data: how many decisions, what resources were allocated, which participants were involved, and which decisions fell within or outside the declared emergency scope. She does not assess whether the emergency authority was appropriate -- that is for the audit and capture assessment teams. The emergency did not suspend monitoring; it delayed it. The data gap is visible, documented, and bounded.

### 3. Leadership Charisma Capture

Surya, a beloved OSC member, learns that Ratu's data collection reveals an objection withdrawal pattern around Surya's proposals (GHI-06 data shows 80% withdrawal rate on Surya's proposals vs. 27% on others). Surya privately asks Ratu: "These numbers lack context. People withdraw objections because I address their concerns informally before the formal round -- could you note that?" Ratu declines: interpretation is outside her authority. She publishes the raw withdrawal rates. Surya then suggests at a TH meeting that "perhaps the monitor should have more context-setting authority so the data is not misleading." The proposal to expand the monitor's authority enters the ACT process. During consent, three members object: "Allowing the monitor to contextualize data creates exactly the editorial influence the role is designed to prevent." The proposal fails. The structural boundary holds because it is protected by the same ACT consent process that governs all governance changes. Surya's social influence, which can shape individual conversations, cannot override the structural prohibition embedded in the skill definition.

### 4. High Conflict / Polarization

SHUR Bali is divided over accepting a corporate partnership. Both factions scrutinize Ratu's data reports for ammunition. Faction A notices that GHI-04 (participation) is declining and argues that Faction B's obstructionism is driving people away. Faction B notices that GHI-01 (proposal diversity) is declining and argues that Faction A's dominance of the proposal process is excluding other voices. Both factions demand that Ratu "explain" the data in their favor. Ratu publishes the raw numbers for both indicators without explanation. The data report is a neutral artifact that both factions can cite without the report itself taking sides. When the audit team interprets the data, they note that both indicators are degrading -- a sign that polarization is harming governance health regardless of which faction is "right." Ratu's structural inability to interpret prevents the data from being weaponized at the collection stage. The GAIA Level 4 escalation process addresses the underlying conflict while Ratu continues to collect and publish data on its governance health effects.

### 5. Large-Scale Replication

OmniOne grows to 5,000 members across 15 SHUR locations and 80 circles. Each ETHOS appoints its own independent monitor through its own role-assignment process. The standardized indicator definitions in `assets/indicator-definitions.yaml` ensure that all monitors collect the same 8 indicators using the same measurement formulas. Data reports across all ETHOS use the same template, enabling ecosystem-level aggregation. The OSC receives reports from all 15 monitors. Inconsistencies between ETHOS in data collection methodology are identified during the annual monitor role review and corrected through updated collection procedures. The monitor pool scales with the participant base -- larger ETHOS have more eligible candidates for rotation. Cross-ETHOS monitor exchanges (a monitor from one location conducting a verification audit of another location's data) are encouraged but not required. The monitoring function remains locally operated and globally visible.

### 6. External Legal Pressure

Indonesian authorities request access to SHUR Bali's governance data as part of a regulatory compliance review. A government liaison asks Ratu to produce a "summary report with relevant context" for the regulator. Ratu can provide the published Governance Data Report -- it is already a public document. However, she cannot produce a contextual summary because her role prohibits interpretation. The ecosystem can designate a separate compliance liaison (not the monitor) to produce regulatory documentation derived from the published data. The UAF sovereignty principle holds: the monitor's structural independence is not compromised for external compliance. The data is public; the interpretation is not the monitor's function. If the regulator's request creates pressure to modify the monitor's data collection to exclude sensitive indicators, this pressure is documented as a governance health event, and the indicator definitions remain governed by the ecosystem's own ACT process, not external mandate.

### 7. Sudden Exit of 30% of Participants

Following a contentious OSC decision, 12 of 38 SHUR Bali members exit within two weeks. Ratu continues data collection on schedule. The departures immediately affect several indicators: GHI-01 drops because active proposers left, GHI-04 shows a sharp participation decline, GHI-07 degrades because agreement stewards departed. Ratu publishes the raw data showing these changes without interpreting whether the departures represent a governance crisis, a healthy correction, or a temporary fluctuation. The audit team and capture assessment team interpret the significance. If Ratu herself was among the departing members, the backup monitor assumes primary responsibilities immediately and completes the current collection cycle. The 1-month overlap protocol means the backup monitor has already verified their ability to replicate the data collection process. The mass exit trigger also fires an automatic governance health audit, which the new or continuing monitor supports with expedited data collection. Data continuity is maintained through the structural redundancy of the backup monitor system.
