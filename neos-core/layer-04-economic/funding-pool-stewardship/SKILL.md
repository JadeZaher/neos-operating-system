---
name: funding-pool-stewardship
description: "Create and govern funding pools that hold ecosystem resources -- define boundaries, inflow sources, outflow rules, steward accountability, and transparency schedules so every pool operates as a living agreement rather than an opaque treasury."
layer: 4
version: 0.1.0
depends_on: [agreement-creation, role-assignment, agreement-review]
---

# funding-pool-stewardship

## C. Trigger Conditions

- A circle identifies the need for a dedicated resource pool to fund its operations or projects
- The ecosystem establishes a new strategic priority requiring dedicated funding
- Two or more ETHOS agree to create a shared pool for cross-unit collaboration
- A project receives dedicated funding that requires ring-fenced governance
- An existing pool's governance agreement reaches its review date
- A pool steward rotates out and a new steward must be appointed with defined authority
- An emergency reserve is established or replenished following a drawdown event
- A pool's inflow sources change materially, requiring governance agreement amendment

## D. Required Inputs

- **Pool name and type**: descriptive name and category (circle_operational, ecosystem_strategic, cross_ethos_shared, project_specific, emergency_reserve) (mandatory, provided by the proposing circle or steward)
- **Governing circle**: which circle holds governance authority over the pool (mandatory, must be a circle with domain authority per domain-mapping)
- **Domain boundary**: what resources the pool covers and what falls outside it (mandatory, defined by the proposing circle)
- **Steward nominees**: one or more individuals proposed to manage day-to-day pool operations (mandatory, with role and authority scope for each)
- **Inflow sources**: where the pool's resources come from -- contributions, allocations from parent pools, grants, transfers (mandatory, at least one source)
- **Outflow rules**: thresholds for steward discretion, circle consent, and ecosystem consent (mandatory, with defaults from pool-governance-template.yaml)
- **Transparency schedule**: frequency of balance reporting, transaction log access rules, and audit cycle (mandatory)
- **Review date**: when the pool governance agreement will be reviewed (mandatory, maximum interval 12 months)
- **Sunset conditions**: what conditions trigger pool closure or merger (optional but recommended)

## E. Step-by-Step Process

1. **Identify pool need.** A circle or group of stewards identifies that a resource pool is needed. The proposer checks the agreement registry for existing pools that might already serve the need. If an existing pool covers the domain, the proposer considers amending that pool's governance rather than creating a new one.
2. **Draft pool governance agreement.** The proposer fills out `assets/pool-governance-template.yaml` with all required fields. The governance agreement specifies pool type, boundaries, inflow sources, outflow rules, steward roles, transparency schedule, review date, and sunset conditions. Because every pool is an agreement, the proposer invokes the agreement-creation skill from Layer I to structure the document.
3. **Nominate stewards.** The proposer identifies steward candidates using the role-assignment skill from Layer II. Each steward receives a defined authority scope: the maximum discretionary disbursement threshold (default 5% of pool balance), reporting obligations, and rotation date. No steward serves indefinitely -- maximum term is 12 months before mandatory review.
4. **Route to ACT.** The pool governance agreement enters the ACT process:
   - *Circle operational pool*: circle-level consent (standard 14-day timeline).
   - *Ecosystem strategic pool*: ecosystem-level consent with OSC involvement (21-day timeline).
   - *Cross-ETHOS shared pool*: consent from each participating ETHOS (21-day timeline, parallel processing).
   - *Project-specific pool*: consent from the sponsoring circle (14-day timeline).
   - *Emergency reserve pool*: ecosystem-level consent with OSC involvement (21-day timeline).
5. **Enter Advice phase.** Per act-advice-phase: the pool proposal is announced to all affected participants. Advice covers: whether the pool boundaries overlap with existing pools, whether the inflow sources are sustainable, whether the outflow thresholds are appropriate, and whether the steward nominees are suitable.
6. **Enter Consent phase.** Per act-consent-phase: the proposal (modified by advice) is presented to the deciding body. Objections trigger integration rounds. Common objections include boundary overlap with existing pools, excessive steward discretion thresholds, and insufficient transparency schedules.
7. **Activate pool.** Upon consent, the pool governance agreement is registered in the agreement registry. The steward accepts their role formally using the role-assignment skill. The pool's initial balance and inflow schedule are recorded. The transparency schedule begins immediately.
8. **Operate and report.** The steward manages the pool according to the governance agreement: processing resource requests within their discretionary authority, routing larger requests to ACT, publishing balance reports on the transparency schedule, and maintaining the transaction log.
9. **Review cycle.** At the review date, the agreement-review skill from Layer I triggers a full review of the pool governance agreement. The review examines: pool utilization, steward performance, inflow sustainability, outflow patterns, and whether the pool's boundaries still match ecosystem needs.
10. **Sunset or renew.** If the pool's purpose is fulfilled, its resources are depleted, or the governing circle decides it is no longer needed, the pool enters a sunset process: outstanding commitments are honored, remaining resources transfer to a parent pool or are redistributed, and the governance agreement is closed in the registry.

## F. Output Artifact

A pool governance document following `assets/pool-governance-template.yaml`. The document contains: pool ID, pool name and type, governing circle, domain boundary, steward roster with authority scopes and rotation dates, inflow sources with types and frequencies, outflow rules with threshold tiers, prohibited uses, transparency schedule (balance reporting frequency, transaction log access, audit cycle), review date, sunset conditions, status, creation date, version, and parent agreement ID linking to the Layer I agreement. The document is registered in the agreement registry and accessible to every ecosystem participant. Balance reports and transaction logs are published according to the transparency schedule.

## G. Authority Boundary Check

- **No steward** can disburse above their discretionary threshold without circle consent. The default threshold is 5% of pool balance; the pool governance agreement may set a different threshold, but never above 25%.
- **No single person** can create a funding pool unilaterally. Pool creation requires ACT consent from the governing circle at minimum.
- **No steward** can modify the pool's governance rules (inflow sources, outflow thresholds, boundaries) without running the agreement amendment process through ACT.
- **Stewards** manage operations within their defined scope; they do not own the pool or have preferential access to its resources.
- **OSC** has oversight authority over ecosystem strategic pools and emergency reserves but cannot override circle-level pool governance without invoking the full escalation path.
- **Cross-ETHOS pool stewards** require consent from all participating ETHOS for changes that affect shared governance rules. Unilateral changes by one ETHOS are structurally blocked.
- Authority scopes are time-limited. Steward appointments include a rotation date (maximum 12 months). Reappointment requires a new consent round.

## H. Capture Resistance Check

**Capital capture.** A single donor provides 80% of a pool's inflow and leverages that dependency to influence allocation decisions. The skill resists this by requiring inflow source diversity as an advice-phase review point. When any single source exceeds 50% of pool inflow, the transparency report flags it as a concentration risk. The pool governance agreement can set maximum single-source percentages. Regardless of contribution size, the donor receives no additional governance authority over the pool -- outflow decisions follow ACT process with equal participant weight.

**Charismatic capture.** A popular steward accumulates informal authority beyond their defined scope, making discretionary decisions that technically require circle consent. The skill resists this through mandatory transparency: every disbursement is logged and visible, the discretionary threshold is a hard number (not a judgment call), and any circle member can challenge a steward's action within 7 days. The rotation requirement prevents stewards from becoming permanent fixtures.

**Emergency capture.** A crisis is used to justify creating a new pool or expanding an existing pool's scope without proper consent. Emergency reserve pools exist precisely to handle crises through pre-consented governance rules. Creating a new pool under emergency conditions still requires consent -- at minimum, compressed-timeline consent with 50% quorum. Post-emergency review examines whether the emergency framing was justified.

**Informal capture.** A steward maintains an unregistered "side fund" or processes disbursements outside the pool governance framework. The skill prevents this because the transparency schedule requires regular balance reporting, the transaction log is accessible to all participants, and the commons-monitoring skill tracks flow patterns that would reveal off-book transactions.

## I. Failure Containment Logic

- **Pool creation consent fails**: the proposal is denied with documented rationale. The proposer may revise boundaries, steward nominees, or governance rules and resubmit after a 14-day cooling period. The ecosystem continues operating with existing pools.
- **Steward appointment fails**: the pool cannot activate without at least one consented steward. The governing circle must nominate alternative candidates. The pool proposal remains in "proposed" status until a steward achieves consent.
- **Balance reporting missed**: the commons-monitoring skill flags the missed report. First miss: reminder to steward. Second consecutive miss: circle notification. Third consecutive miss: steward authority is suspended pending review. The pool continues operating with disbursements requiring circle-level consent for all amounts.
- **Inflow source dries up**: the steward reports the inflow change immediately. The governing circle reviews whether the pool remains viable. If the pool cannot sustain its commitments, outstanding obligations are prioritized and new disbursements are paused until the governance agreement is amended.
- **Steward misconduct**: any circle member can raise a formal concern through the agreement-review skill. The steward's discretionary authority is suspended during investigation. If the concern is substantiated, the steward is replaced through the role-assignment process. Resources misallocated through misconduct are recovered through the graduated response ladder.

## J. Expiry / Review Condition

- Pool governance agreements have a mandatory review date, maximum 12 months from creation or last review. The agreement-review skill triggers the review process.
- Steward appointments expire at their rotation date. Reappointment requires a new consent round -- there is no automatic renewal.
- Emergency reserve pools are reviewed after every drawdown event, regardless of the scheduled review date.
- Project-specific pools expire when the project reaches its defined end date. Remaining resources revert to the parent pool or are redistributed per the sunset conditions.
- Missed reviews trigger an escalation sequence: notification at review date, formal warning at review date + 14 days, steward authority suspension at review date + 30 days. The pool's status changes to "under_review" and remains there until the review is completed.

## K. Exit Compatibility Check

When a pool steward exits the ecosystem:
- The steward's authority transfers immediately to a designated successor or reverts to the governing circle. No gap in pool governance occurs -- the circle assumes collective stewardship during transition.
- The steward completes a final balance report and transaction reconciliation within the 30-day wind-down period.
- The exiting steward's access to pool disbursement mechanisms is revoked upon exit notification.
- Outstanding stewardship commitments made by the exiting steward (reports owed, reviews pending) transfer to the successor or governing circle.
- The exit does not affect the pool's governance agreement, inflow sources, or outflow rules. The pool continues operating under its consented governance structure.

When a significant contributor to pool inflows exits:
- The pool steward reports the expected inflow reduction to the governing circle within 7 days.
- The governing circle assesses pool viability and may trigger an early review of the governance agreement.

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS shared pools require governance agreements consented by all participating ETHOS. Changes to shared pool governance require consent from every participating unit.
- Each ETHOS maintains its own circle operational pools. These do not require cross-unit notification unless a disbursement affects another ETHOS's domain.
- When an ETHOS creates a pool that overlaps in domain with another ETHOS's existing pool, the advice phase must include notification to the overlapping ETHOS. Boundary conflicts are resolved before pool activation.
- Pool governance agreements for cross-ETHOS pools are registered in every participating ETHOS's agreement registry with synchronized status.
- Ecosystem strategic pools are governed at the ecosystem level and accessible to all ETHOS through the resource-request skill. Individual ETHOS cannot restrict other ETHOS' access to ecosystem pools.
- Cross-ecosystem pool sharing (between separate NEOS ecosystems) uses the inter-unit coordination protocol (Layer V, deferred).
