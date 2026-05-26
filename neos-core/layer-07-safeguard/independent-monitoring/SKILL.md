---
name: independent-monitoring
description: "Establish and operate the independent monitor role -- a rotating, structurally separated function that collects and publishes raw governance health data without interpretation or decision authority."
layer: 7
version: 0.1.0
depends_on: [governance-health-audit, role-assignment, domain-mapping]
---

# independent-monitoring

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
