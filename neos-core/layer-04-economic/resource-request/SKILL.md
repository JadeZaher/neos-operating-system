---
name: resource-request
description: "Request resources from ecosystem funding pools -- financial, physical, time, access, or expertise -- through a structured ACT process that prevents self-approval and separates economic need from governance authority."
layer: 4
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, domain-mapping]
---

# resource-request

## C. Trigger Conditions

- A participant identifies a resource need that cannot be met from personal or already-allocated resources
- A circle identifies an operational expense that requires funding pool disbursement
- A project reaches a milestone that triggers a pre-approved resource release
- An emergency creates urgent resource needs that invoke compressed timelines
- A cross-ETHOS collaboration requires resource commitments from multiple pools
- A stewardship review reveals that a previously allocated resource needs renewal or expansion

## D. Required Inputs

- **Requester identity**: name, role, and domain scope (provided by the requester, verified against role-assignment records)
- **Resource type**: financial, physical asset, time allocation, access permission, or expertise (mandatory, selected from defined categories)
- **Amount or scope**: quantified need -- currency amount, asset description, hours, access duration, or expertise scope (mandatory)
- **Funding pool target**: which pool the request draws from (mandatory, must be a pool the requester's domain can access)
- **Rationale**: why this resource is needed and how it serves the circle or ecosystem purpose (mandatory, minimum 3 sentences)
- **Timeline**: when the resource is needed and for how long (mandatory, with start and end dates)
- **Stewardship commitment**: what the requester commits to regarding resource use, reporting, and return (mandatory)
- **Domain scope**: the boundary within which the resource will be used (mandatory, must fall within requester's domain per domain-mapping)

## E. Step-by-Step Process

1. **Identify need.** The requester determines that a resource is needed and that no existing allocation or personal resource covers it. The requester checks the agreement registry for any standing resource agreements that might already address the need.
2. **Draft request.** The requester fills out the `assets/resource-request-template.yaml` with all required fields. The rationale must connect the resource need to the circle's or ecosystem's stated purpose. Timeline must include both start and end dates.
3. **Authority boundary check.** The requester confirms their domain scope allows access to the target funding pool. If the pool is outside the requester's domain, the request routes through cross-unit coordination (see Section L). Self-approval is structurally blocked: the requester cannot serve as the sole decision-maker on their own request.
4. **Route to ACT level.** Based on the request amount relative to the target pool and the pool's governance rules:
   - *Below 5% of pool balance*: pool steward reviews and decides within steward discretion (48-hour timeline). Steward documents rationale.
   - *5-25% of pool balance*: circle-level ACT consent process with all circle members as deciding body (standard 14-day timeline).
   - *Above 25% of pool balance*: ecosystem-level ACT consent with OSC involvement (standard 21-day timeline).
   - Thresholds are configurable per pool governance agreement; defaults above apply when no pool-specific thresholds exist.
5. **Enter Advice phase.** Per the act-advice-phase skill: the request is announced to all affected parties. The advice window opens for input on feasibility, alignment, and alternative approaches. The requester documents all advice received and their response to each item.
6. **Enter Consent phase.** Per the act-consent-phase skill: the request (modified by advice) is presented to the deciding body. Positions are recorded. Objections trigger integration rounds. The requester cannot vote on their own request but participates in discussion.
7. **Decision recorded.** The ACT decision is recorded in the request document: approved, denied, or modified. If modified, the requester reviews and accepts or withdraws the request. If denied, the rationale is documented and the requester may resubmit with modifications after a 14-day cooling period.
8. **Fulfillment.** Approved requests are fulfilled by the pool steward within the agreed timeline. The steward updates the request status to "in progress" and then "fulfilled" with the actual disbursement details.
9. **Stewardship reporting.** The requester reports on resource use according to the stewardship commitment. Reports are visible to all pool participants. Failure to report triggers the graduated response ladder (see commons-monitoring).

## F. Output Artifact

A versioned resource request document following `assets/resource-request-template.yaml`. The document contains: unique request ID, requester identity and role, resource type and amount, target funding pool, rationale, timeline, stewardship commitment, domain scope, ACT routing level, full decision record (advice summary, consent positions, objections and integrations), fulfillment status and dates, and review date. The document is registered in the agreement registry alongside the funding pool's records. All request documents are accessible to every participant in the ecosystem -- no resource request is confidential.

## G. Authority Boundary Check

- **No participant** can approve their own resource request, regardless of role or seniority. A steward requesting from their own pool must have another authorized participant or the circle decide.
- **Pool stewards** have discretionary authority only below the pool's defined threshold (default: 5% of pool balance). Above that threshold, the circle or ecosystem decides through ACT.
- **Circle members** decide on requests between 5-25% of their circle's pool through circle-level consent.
- **Ecosystem-level requests** (above 25% of any pool, or drawing from ecosystem strategic pool) require OSC involvement.
- **Facilitators** manage the ACT process but cannot approve or deny requests on content grounds.
- **Cross-domain requests** require consent from both the requester's circle and the target pool's governing circle.
- Authority scopes are formally defined by the domain-mapping and role-assignment skills (Layer II). The requester's domain contract establishes which pools they can access.

## H. Capture Resistance Check

**Capital capture.** A major donor conditions future funding on their preferred participant receiving a resource allocation. The skill prevents this because: every request enters the same ACT process regardless of donor preferences, the request rationale is evaluated on its connection to ecosystem purpose, and donor conditions that influence allocation are flagged as a capture vector during the advice phase. Financial contribution creates no priority in the request queue.

**Charismatic capture.** A popular leader's resource request receives less scrutiny than others. The consent phase structurally equalizes this: every request must meet the same documentation requirements, the deciding body evaluates the written rationale (not just the verbal pitch), and the facilitator ensures objections are recorded before social dynamics can suppress them. High-status requesters do not receive expedited routing.

**Emergency capture.** A crisis is invoked to bypass the request process and access pool resources unilaterally. Emergency timelines compress the ACT process (24-hour advice, expedited consent) but do not eliminate it. Emergency requests still require a formal consent round with minimum 50% quorum. Emergency allocations auto-expire in 30 days and trigger post-emergency review.

**Informal capture.** "I already spoke to the steward and they said it was fine" is not a resource request. No disbursement occurs without a registered request document. Verbal agreements about resource access have no standing in the governance system.

## I. Failure Containment Logic

- **Consent fails** (objections cannot be integrated): the request is denied with documented rationale. The requester may resubmit with modifications after a 14-day cooling period. The request does not escalate to a higher body automatically -- the requester may invoke proposal-resolution if they believe the process was flawed.
- **Quorum not met**: the consent timeline extends by 7 days. The quorum threshold is never lowered. If quorum is still not met after extension, the request is tabled and the pool governance agreement is reviewed for scope accuracy.
- **Steward discretion disputed**: any circle member can challenge a steward's discretionary approval within 7 days, triggering a full circle-level consent process. The resource is held pending the challenge outcome.
- **Fulfillment delayed**: if the pool cannot fulfill an approved request within the agreed timeline, the steward notifies the requester and the request enters a renegotiation window. The requester may modify scope, timeline, or withdraw.
- **Stewardship reporting failure**: triggers graduated response -- reminder at 7 days overdue, circle notification at 14 days, restriction on future requests at 30 days, formal review at 60 days. No single failure results in permanent exclusion.

## J. Expiry / Review Condition

- **Pending requests** that receive no ACT decision within 60 days are flagged for the pool steward and the requester. They do not auto-expire but enter a mandatory review to determine if the need still exists.
- **Approved requests** that remain unfulfilled after 90 days trigger a steward accountability review.
- **Stewardship commitments** have review dates set at the time of approval (default: 6 months for financial, 3 months for physical assets, per-use for access permissions). Minimum review interval: 3 months.
- **Recurring resource needs** may establish standing request agreements through the agreement-creation skill, with built-in review dates rather than repeated individual requests.
- Missed review triggers a sunset warning to the requester and pool steward. The resource commitment enters a 30-day grace period for review before status changes to "under review."

## K. Exit Compatibility Check

When a requester exits the ecosystem:
- **Unfulfilled requests** are cancelled. No obligation remains on either side.
- **In-progress allocations** enter a 30-day wind-down. Physical assets must be returned. Financial resources already disbursed for completed work are not clawed back; resources for incomplete work are returned to the pool.
- **Stewardship commitments** transfer to a designated successor or revert to the pool steward. The commons-monitoring skill tracks the transition.
- **Original works** produced with allocated resources remain the creator's intellectual property. The ecosystem retains rights specified in the original stewardship commitment.
- Exit does not retroactively invalidate the decision record. Approved requests remain in the registry as historical records.

## L. Cross-Unit Interoperability Impact

- Resource requests that target pools governed by a different ETHOS require **cross-unit notification** before entering the advice phase. The target ETHOS must acknowledge the request before it can proceed.
- The target ETHOS's pool governance rules apply to the decision process, not the requester's home ETHOS rules.
- Cross-ETHOS requests are registered in both ETHOS' records with linked entries and synchronized status updates.
- When a resource request spans multiple pools across ETHOS, each pool processes its portion independently. Partial approval from one pool does not obligate another.
- Cross-ecosystem resource requests (between separate NEOS ecosystems) use the inter-unit coordination protocol (Layer V, deferred). This skill's routing logic can extend to include cross-ecosystem routing when Layer V is available.
