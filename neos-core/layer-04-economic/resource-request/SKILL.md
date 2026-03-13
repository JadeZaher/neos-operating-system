---
name: resource-request
description: "Request resources from ecosystem funding pools -- financial, physical, time, access, or expertise -- through a structured ACT process that prevents self-approval and separates economic need from governance authority."
layer: 4
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, domain-mapping]
---

# resource-request

## A. Structural Problem It Solves

Without a formal resource request process, resources flow through informal channels: whoever knows the right people, asks at the right moment, or holds social capital gets funded while others wait. This informality breeds resentment, concentrates resources among insiders, and makes accountability impossible because no one can trace why a particular allocation was made. The resource-request skill ensures every resource need enters a transparent pipeline with a traceable decision record. It structurally separates the act of requesting from the act of approving, preventing self-approval and ensuring that economic contribution does not translate into preferential resource access. Every resource request is an agreement: the requester commits to stewardship of the resource, and the ecosystem commits to providing it.

## B. Domain Scope

This skill applies to any participant requesting resources from any funding pool within the ecosystem. Resource types include financial disbursements, physical asset loans, time allocations from shared labor pools, access permissions to spaces or tools, and expertise commitments from other participants. The skill covers requests at every scale: circle operational pools, cross-AZPO shared pools, ecosystem strategic pools, project-specific pools, and emergency reserves. Out of scope: how funding pools are created and governed (see funding-pool-stewardship), how pools are collectively allocated in bulk (see participatory-allocation), and how external resources enter the ecosystem (external fundraising is outside NEOS scope). The requester must operate within a domain defined by domain-mapping (Layer II) and cannot request resources from pools outside their domain without cross-unit routing.

## C. Trigger Conditions

- A participant identifies a resource need that cannot be met from personal or already-allocated resources
- A circle identifies an operational expense that requires funding pool disbursement
- A project reaches a milestone that triggers a pre-approved resource release
- An emergency creates urgent resource needs that invoke compressed timelines
- A cross-AZPO collaboration requires resource commitments from multiple pools
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

- Resource requests that target pools governed by a different AZPO require **cross-unit notification** before entering the advice phase. The target AZPO must acknowledge the request before it can proceed.
- The target AZPO's pool governance rules apply to the decision process, not the requester's home AZPO rules.
- Cross-AZPO requests are registered in both AZPOs' records with linked entries and synchronized status updates.
- When a resource request spans multiple pools across AZPOs, each pool processes its portion independently. Partial approval from one pool does not obligate another.
- Cross-ecosystem resource requests (between separate NEOS ecosystems) use the inter-unit coordination protocol (Layer V, deferred). This skill's routing logic can extend to include cross-ecosystem routing when Layer V is available.

## OmniOne Walkthrough

Keoni, an AE member in the Education circle, needs $800 to attend a regenerative governance training in Costa Rica. The training aligns with the Education circle's purpose of building governance capacity within OmniOne. Keoni opens the resource-request-template and fills in: requester=Keoni, role=AE, domain=Education circle, resource_type=financial, amount=$800, funding_pool_target=Education Circle Operational Pool (current balance: $6,200), rationale="Three-day regenerative governance intensive directly builds facilitation capacity for our circle. I commit to running two internal workshops sharing what I learn within 60 days of return." Timeline: May 15-18, 2026. Stewardship commitment: workshop delivery plus a written summary shared with the ecosystem.

Keoni runs the synergy check and finds no existing training fund agreement, but does find a standing Education circle agreement (AGR-EDU-2026-004) that allocates $2,000 annually for professional development. Her $800 request falls within that allocation. She documents the relationship.

The $800 is 12.9% of the $6,200 pool balance, routing the request to circle-level ACT consent. Keoni announces the request to all 9 Education circle members with a 14-day advice window. During advice, Farid (another AE member) suggests Keoni also bring back printed materials for the circle library. Lina (the circle's pool steward) notes that $800 is the largest single training request this quarter and asks Keoni to confirm the training provider's legitimacy. Keoni integrates both: she adds a materials budget line of $50 (total now $850) and provides the training provider's website and references from past OmniOne members who attended.

The consent phase convenes with 8 of 9 members present (quorum met). Keoni participates in discussion but does not record a position on her own request. Round 1: 6 consent, 1 stands aside (Dayo is supportive but has no strong opinion), 1 objects -- Maren objects that the circle already sent one member to a training last month and questions whether two trainings in two months is sustainable for the pool. In the integration round, Keoni and Maren examine the pool's annual training allocation: $2,000 allocated, $400 spent last month, $850 requested now, leaving $750 for the remaining 8 months. Maren's concern is valid. The third solution: Keoni reduces her request to $700 (economy flight instead of direct) and commits to a more detailed stewardship report. Round 2: all 7 deciding members consent (Dayo still stands aside). Consent achieved.

Lina, the pool steward, fulfills the request within 5 business days, updating the request status to "fulfilled." Keoni attends the training and delivers her two workshops within 45 days. Her stewardship report is registered alongside the original request. The $700 allocation is visible to every OmniOne participant.

Edge case: Before Keoni submitted, she considered requesting from the Ecosystem Strategic Pool instead, which would have covered the full $800 without straining her circle's budget. However, the strategic pool is governed by the OSC and requires ecosystem-level consent -- a 21-day process for a domain that extends beyond her circle. Keoni chose the circle pool because the training directly serves her circle's purpose, keeping the request within the appropriate domain boundary.

## Stress-Test Results

### 1. Capital Influx

A cryptocurrency entrepreneur joins OmniOne and donates $50,000 to the Education circle's operational pool, then submits a resource request for $15,000 to fund a blockchain governance curriculum they want to develop. The donation triples the pool balance, but the request still routes based on percentage thresholds -- $15,000 is now 10% of the inflated $150,000 pool, routing to circle-level consent rather than the ecosystem level it would have reached under the original balance. The advice phase flags this as a capital capture risk: the donor is requesting resources from a pool they just funded, creating a self-dealing dynamic even though the pool is collectively governed. Circle members evaluate the curriculum proposal on its educational merit and alignment with the circle's purpose, not on the donor's financial contribution. Several members raise objections about the curriculum's narrow focus on blockchain governance when the circle's scope is broader. The donor's $50,000 contribution does not grant them 111 additional Current-Sees, additional consent weight, or priority in the request queue. The request is evaluated identically to Keoni's $700 training request. If the donor threatens to withdraw funding over a denial, that threat is documented as a capture attempt and the circle's decision stands.

### 2. Emergency Crisis

A tropical storm destroys equipment at the SHUR Bali permaculture farm, and the Agriculture circle needs $3,000 immediately to replace irrigation infrastructure before the planting season window closes in 10 days. Three AE members invoke the provisional emergency rules. The resource request enters emergency compression: the advice window is 24 hours instead of 14 days, and the consent quorum drops to a minimum of 50% of the circle. The requester still cannot self-approve. The pool steward still documents the request using the standard template, but with an emergency flag and the compressed timeline. Six of ten Agriculture circle members participate in the emergency consent round within 18 hours -- all consent. The $3,000 is disbursed within 24 hours. The emergency allocation auto-expires in 30 days and triggers a post-emergency review where the circle evaluates whether the emergency process was justified and whether the resources were used as committed. The post-emergency review also checks whether the emergency was used to bypass normal scrutiny of the request's merits.

### 3. Leadership Charisma Capture

Rani, a founding member of OmniOne widely respected for her vision and persuasiveness, submits a resource request for $5,000 from the Ecosystem Strategic Pool to fund a personal retreat she frames as "visionary planning for OmniOne's next phase." Rani's social capital means many participants hesitate to question her requests. The resource-request skill structurally resists this: the written rationale must connect the resource to ecosystem purpose with the same specificity required of any participant. During the advice phase, the facilitator ensures all participants can submit written feedback before any group discussion, preventing Rani's presence from suppressing honest input. In the consent phase, every position is recorded before discussion begins -- objections lodged cannot be withdrawn under social pressure. Two OSC members object that the retreat's deliverables are vague and that personal planning does not meet the strategic pool's purpose criteria. The integration rounds require Rani to produce specific, measurable deliverables -- not reframe objections as "lacking vision." After two integration rounds, Rani modifies the request to include a co-facilitated strategic planning session with three other stewards and a written output shared with the ecosystem. The modified request achieves consent.

### 4. High Conflict / Polarization

The Technology circle is deeply split on a $10,000 resource request to license proprietary project management software. Faction A argues the ecosystem should only use open-source tools consistent with commons values. Faction B argues the proprietary tool saves hundreds of hours annually and pragmatism should override ideology. The request enters the consent phase and receives three objections from Faction A, each citing the UAF's commitment to commons-based infrastructure. The integration rounds surface the core tension: efficiency versus principle. At GAIA Level 4, a coach maps both factions' concerns and facilitates a third-solution exploration. The resulting proposal: allocate $4,000 to a 90-day pilot of the proprietary tool while simultaneously allocating $2,000 to evaluate open-source alternatives. After the pilot, the circle runs a structured comparison using pre-agreed criteria. This third solution enters consent with both factions' core concerns addressed -- principle is honored through the parallel evaluation, and pragmatism is honored through the immediate pilot. The coach ensures neither faction's framing dominates the final proposal.

### 5. Large-Scale Replication

OmniOne scales to 5,000 participants across 15 SHUR locations and 80 circles. Resource requests scale through domain-scoped routing: a request from the Agriculture circle at SHUR Costa Rica involves only that circle's pool and members, not all 5,000 participants. The request template remains identical at every scale. What changes is the routing: with 80 circles each managing their own operational pools, most requests resolve at the circle level without ecosystem involvement. The pool steward discretion threshold (5% of pool) handles routine small requests without convening full consent processes. Cross-AZPO requests increase in frequency as circles collaborate across locations, but each request routes through the established cross-unit protocol rather than requiring a new process. The agreement registry tracks thousands of resource requests with consistent metadata, enabling pattern analysis through the commons-monitoring skill. Facilitator capacity scales through trained facilitators in each circle -- no single facilitator bottleneck exists.

### 6. External Legal Pressure

Indonesian tax authorities require OmniOne to document all financial disbursements exceeding 5,000,000 IDR (approximately $300) with tax-compliant receipts and reporting. This external mandate does not change the resource-request process -- it adds a compliance layer. The pool steward at SHUR Bali adds a compliance checklist to the fulfillment step: disbursements above the threshold include tax documentation alongside the standard stewardship commitment. The request template gains an optional compliance_notes field for jurisdiction-specific requirements. This compliance applies only to SHUR Bali -- it does not modify the global resource-request process or create ecosystem-wide tax reporting obligations. Individual requesters in Indonesia comply with their local tax law; requesters in Costa Rica or Portugal follow their own jurisdictions. The UAF's sovereignty principle holds: external legal requirements are absorbed at the local level without distorting the governance structure.

### 7. Sudden Exit of 30% of Participants

Following a disagreement about OmniOne's expansion into urban communities, 1,500 of 5,000 members exit within three weeks. Resource requests in progress face immediate impact: pending requests from departed members are cancelled, approved-but-unfulfilled requests from departed members are voided with resources returned to pools. Stewardship commitments from departed members enter the 30-day wind-down -- physical assets are returned, financial resources for incomplete work revert to pools, and ongoing stewardship transfers to designated successors or pool stewards. Pool balances drop as some departing members had contributed to pool inflows. Quorum thresholds for pending requests recalculate based on current membership: a circle that had 20 members and now has 14 recalculates its 2/3 quorum requirement on 14, not 20. The commons-monitoring skill triggers an ecosystem-wide review of all active resource commitments to assess sustainability at the reduced scale. Existing approved and fulfilled requests remain valid -- the departure does not retroactively invalidate legitimate decisions.
