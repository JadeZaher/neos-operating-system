---
name: domain-mapping
description: "Define or refine a governance domain using the 11-element contract -- purpose, responsibilities, customers, deliverables, dependencies, constraints, challenges, resources, delegator responsibilities, competencies, metrics, evaluation schedule -- so that authority scope is explicit, bounded, and reviewable."
layer: 2
version: 0.1.0
depends_on: []
---

# domain-mapping

## A. Structural Problem It Solves

Without formal domain definitions, authority is assumed, informal, and inconsistent. Participants act beyond their intended scope — not out of malice but because no boundary was ever drawn. When disputes arise, there is no structural reference to adjudicate; the conflict becomes personal rather than procedural. This skill provides the canonical schema for defining what authority looks like, who holds it, and what it cannot do. Every governance action in NEOS traces back to a domain contract. Without this skill, all other authority claims are provisional guesses.

## B. Domain Scope

Any circle, role, or structural body that exercises governance authority within the ecosystem. This includes new circles being formed, existing roles that have been operating without formal domain contracts, and any body whose scope is contested or ambiguous. Domain-mapping applies to every AZPO and crosses AZPO boundaries when cross-unit dependencies exist. Out of scope: the assignment of a specific person to a defined domain (that is role-assignment), and the resolution of overlapping claims between already-defined domains (that is authority-boundary-negotiation).

## C. Trigger Conditions

- A new circle or role is formed through an ACT consent process and requires a formal domain contract before operating
- An existing role or circle has been functioning without a documented domain and needs structural legitimacy
- A domain-review evaluation recommends refinement of an existing domain contract
- An authority-boundary-negotiation requires formal amendment of one or both domain contracts involved
- The founding body of a new ecosystem defines the initial domain structure (consensus process, one-time event)

## D. Required Inputs

- **Delegating body identity:** the circle or council that holds authority to create this domain (mandatory)
- **Proposed domain purpose:** a plain-language statement of why this domain exists and what it is responsible for (mandatory)
- **Ecosystem context:** parent domain, adjacent domains, known dependencies (mandatory — at minimum, "no known dependencies" must be stated explicitly)
- **Draft constraint list:** initial list of what this domain cannot do, even within its scope (mandatory — vague or absent constraints flag provisional status)
- **Proposed steward candidate:** the person or group being assigned (optional at creation — domains may be created before a steward is assigned)

## E. Step-by-Step Process

1. **Identify need.** The delegating body confirms that no existing domain contract covers the proposed scope. Query the domain registry for related domains before drafting.
2. **Draft all 11 elements.** Fill in each element of the domain contract (see Section F and the asset template). For each element, consult existing domain contracts to identify dependencies and potential overlaps. Vague constraints must be made specific — "act in the ecosystem's interest" is not a constraint.
3. **Adjacent domain review.** Present the draft to all stewards of adjacent domains for structural feedback. This is not a consent round — it is a dependencies and overlap check. Any overlap identified is documented and routed to authority-boundary-negotiation before the consent round proceeds.
4. **Delegating body consent round.** The delegating body runs an ACT consent process on the complete domain contract. The question posed: "Does this domain contract clearly bound authority in a way no one has a reasoned objection to?" Adjacent domain stewards' feedback is included in the advice record.
5. **Registration.** The completed, consented domain contract is entered in the domain registry with a unique domain ID, version 1.0.0, status "active," and a linked evaluation schedule.
6. **Notification.** All adjacent and dependent domains are notified. Cross-AZPO dependencies trigger notification to those AZPOs' registries as well.

## F. Output Artifact

A versioned domain contract document following `assets/domain-contract-template.yaml`. The contract contains: domain ID, version (starting at 1.0.0), status, creation date, delegating body, all 11 elements filled, current steward (null if vacant), assignment history, and amendment history. The domain contract is the single source of truth for what this domain can and cannot do. Every downstream skill that references authority — role-assignment, domain-review, role-sunset — reads from this document.

**The 11 elements:**
1. **Purpose** — why this domain exists; the governance function it performs
2. **Key responsibilities** — what the domain must do; the actions it is accountable for
3. **Customers** — who the domain serves; participants or bodies that depend on its outputs
4. **Deliverables** — the concrete outputs others can expect from this domain
5. **Dependencies** — other domains or resources this domain requires to function
6. **Constraints** — what this domain explicitly cannot do, even within its scope
7. **Challenges** — known risks, tensions, or structural difficulties
8. **Resources** — what the domain can draw on: budget, time, information, tools
9. **Delegator responsibilities** — what the delegating body owes this domain: information access, non-interference, evaluation support
10. **Competencies** — what the steward must understand or be able to do
11. **Metrics + evaluation schedule** — how effectiveness is measured and when the domain is formally reviewed

## G. Authority Boundary Check

Only a delegating body can create a domain through an ACT consent process. No individual can self-declare a domain — a domain created outside this process has no standing in the governance system. A domain holder cannot expand their own domain; scope expansion requires the delegating body to consent to amended domain contract elements. Minor updates (metric adjustments, resource changes) use circle-level consent. Structural changes (purpose, key responsibilities, constraints) use the full ACT process.

**Meta-authority:** The founding body of a new ecosystem (analogous to OmniOne's OSC) defines the initial domain structure through consensus before this skill is operative. Once the initial structure exists, all subsequent domain creation follows this skill. This makes the skill self-referentially consistent: the authority to define authority is explicitly stated rather than assumed.

## H. Capture Resistance Check

**Authority creep by precedent.** A domain holder acts beyond their defined constraints repeatedly and, when unchallenged, cites this as established practice. The constraints element explicitly bounds authority — precedent does not amend constraints. The domain-review cycle catches drift by comparing actual behavior against the contract.

**Charismatic capture through vague constraints.** A trusted leader defines their domain with deliberately broad language ("do whatever is needed for ecosystem health") to maximize discretion. Adjacent domain stewards flag overlap risk during the review step. The ACT advice phase requires constraint specificity. Any domain with constraints that do not exclude specific actions is flagged for revision before consent proceeds.

**Domain hoarding.** One body creates many domains to consolidate influence. The domain registry tracks domains-per-delegating-body. Domain-review evaluations include a load assessment — a delegating body stewarding more domains than it can meaningfully evaluate is flagged for restructuring.

## I. Failure Containment Logic

**Incomplete domain contract.** Any missing element at consent time flags the domain as "provisional." A provisional domain may operate for 30 days but must complete all elements or revert to its delegating body for holding. Provisional status is visible in the registry.

**Contested domain.** Two bodies simultaneously claim authority to create a domain over the same scope. Neither contract proceeds to consent. The conflict routes to authority-boundary-negotiation, which produces a resolution before either domain can be finalized.

**Abandoned domain.** A steward stops fulfilling responsibilities without triggering a formal exit. The domain-review process catches this at the evaluation date. If responsibilities are visibly unmet before that date, the delegating body can call an emergency review and route to role-transfer or role-sunset.

**Adjacent domain review stalls.** If an adjacent domain steward fails to engage within 14 days, the delegating body may proceed to consent with the stall documented. The non-responsive steward's domain is flagged for a boundary review at its next evaluation.

## J. Expiry / Review Condition

Every domain contract must include an evaluation schedule (element 11). The default cadence is 6 months. Domains without an evaluation schedule are flagged as incomplete in the registry and cannot hold "active" status. If the evaluation date passes without a review being convened, the domain enters a 30-day grace period with an escalation notice to the delegating body. After 30 days, domain status changes to "under_review" with a registry flag. Domain contracts do not auto-expire — expiry without review is a governance failure, not a design feature.

## K. Exit Compatibility Check

When a domain steward exits the ecosystem, the domain enters "vacant" status immediately — it does not dissolve. The delegating body holds 30 days to assign a new steward via role-assignment or trigger role-sunset. During the vacant window, the delegating body holds temporary stewardship for urgent matters only, with all such actions documented in the amendment history. The exiting steward must produce a handover inventory: pending commitments, active agreements held by the domain, and relationship context for adjacent domains. If the steward exits without producing this inventory, the delegating body initiates a 14-day reconstruction period before operating in the domain.

## L. Cross-Unit Interoperability Impact

Domains within one AZPO may have dependencies on domains in another AZPO. Cross-unit dependencies must be listed explicitly in the dependencies element — "no cross-AZPO dependencies" must be stated rather than omitted. When a domain is created or refined in one AZPO, all cross-AZPO dependent domains are notified before the consent round concludes. Cross-AZPO domain conflicts follow the authority-boundary-negotiation process with facilitators drawn from neither AZPO. Resolution records are registered in both AZPOs' registries. Cross-ecosystem domain dependencies follow the same structure with an additional inter-ecosystem notification step when Layer V federation is available.

## OmniOne Walkthrough

The Agents of the Ecosystem (AE) decides to create a new Economics circle. Mireille, an AE facilitator, confirms that no existing domain contract covers economics coordination — the registry shows only a general "AE operations" domain that explicitly lists economics as out-of-scope pending a dedicated circle.

Mireille leads the AE through drafting all 11 elements:

- **Purpose:** Steward the ecosystem's economic coordination — resource allocation, funding pool management, and economic policy proposals.
- **Key responsibilities:** Manage funding requests from AZPOs and circles; maintain economic transparency through monthly reporting; propose resource distribution changes to the AE; coordinate with OSC on ecosystem-level economic policy.
- **Customers:** All participants and AZPOs requesting or receiving resources; the OSC for economic policy input.
- **Deliverables:** Monthly economic transparency reports; funding request decisions within 14 days of submission; annual economic policy proposal to the OSC.
- **Dependencies:** OSC for ecosystem-level economic policy approval; agreement registry (layer-01) for tracking economic agreements; Trunk Council for access to foundation financial records during OmniOne's formation phase.
- **Constraints:** Cannot approve funding above 10% of the total resource pool without OSC consent. Cannot create economic agreements that contradict the UAF. Cannot grant Current-See advantages to any role. Cannot negotiate with external funders without AE awareness.
- **Challenges:** Balancing rapid resource access with accountability; maintaining transparency at scale; preventing capital capture from large donors; operating while Trunk Council retains some economic authority during formation.
- **Resources:** Access to ecosystem financial records; one dedicated weekly meeting slot in the AE calendar; 5% of annual pool for operational costs.
- **Delegator responsibilities:** AE provides timely information on ecosystem-level economic decisions; does not intervene in Economics circle decisions below the 10% threshold; convenes the 6-month evaluation promptly.
- **Competencies:** Understanding of commons-based economics; facilitation of financial transparency processes; familiarity with ACT Engine for funding decisions.
- **Metrics + evaluation schedule:** Time-to-decision on funding requests (target: 14 days); participant satisfaction with economic transparency (quarterly survey, target: 80%); percentage of funding cycles completed on time. Evaluation every 6 months, first evaluation September 2026.

During the adjacent domain review, Kofi, steward of the Partnerships circle, raises a flag: a draft line reading "coordinate with external partners on economic matters" overlaps with Partnerships' responsibility to manage all external relationships. Rather than blocking the consent round, the AE refines the Economics domain contract — external economic coordination becomes a dependency on the Partnerships circle rather than a key responsibility. Economics circle will submit external funding coordination requests through Partnerships; Partnerships will not block them without cause.

The AE runs a consent round. All seven members consent. The domain contract is registered as DOM-AE-ECON-001 v1.0.0, status active, cross-dependency to DOM-AE-PRTN-001 documented. An authority-boundary-negotiation between Economics and Partnerships is scheduled for Month 2 to formalize the coordination protocol.

**Output artifact:** `DOM-AE-ECON-001.yaml` — all 11 elements complete, version 1.0.0, status active, evaluation September 2026, cross-dependency to DOM-AE-PRTN-001, amendment history empty.

## Stress-Test Results

Full narrative paragraphs are in `references/stress-tests.md`. Summaries below demonstrate the specific mechanisms that activate under each condition.

### 1. Capital Influx

A major donor conditions funding on a "Donor Relations" domain with broad constraints giving their representative resource allocation influence. The constraints element requires specificity — "act in the donor's interest" fails the structural test. Adjacent domain stewards flag the contradiction with the UAF during the review step. Three AE members raise objections during the consent round. Integration rounds narrow the domain to "manage donor communication and reporting" with an explicit constraint against modifying resource allocation in response to donor preferences. The steward competency requirement (element 10) requires governance literacy, structurally excluding the donor's representative from the role. Capital leverage cannot override structural consent. See `references/stress-tests.md` §1.

### 2. Emergency Crisis

A regional crisis requires an "Emergency Coordination" domain within 24 hours. The OSC invokes the provisional emergency protocol: all 11 elements are drafted at minimum specification — purpose, key responsibilities, and constraints are non-negotiable even at speed. The domain enters provisional status immediately, enabling the steward to act. The constraints element explicitly states: the steward cannot override existing domain authority without the affected steward's consent or OSC escalation. A mandatory full review is triggered at crisis stabilization or the 30-day mark. See `references/stress-tests.md` §2.

### 3. Leadership Charisma Capture

A charismatic OSC member proposes a personal domain with constraints reading "whatever is needed for ecosystem cohesion." Adjacent domain stewards flag the vagueness. The ACT advice phase surfaces three specific constraint gaps. Two members raise formal objections in the consent round — the constraints do not exclude scope expansion by precedent. Integration rounds require the proposer to enumerate specific excluded actions. After two rounds the constraints are specific enough to pass consent. The proposer's charisma accelerated the drafting but could not bypass the consent structure's specificity requirement. See `references/stress-tests.md` §3.

### 4. High Conflict / Polarization

Two AE factions submit competing draft domain contracts for economics — one centralized, one distributed. The registry flags both drafts as claiming the same scope. Neither proceeds to consent. GAIA Level 4 coaching maps the structural concern behind each position: centralists fear fragmented accountability; distributionists fear capture. The coach surfaces a federated model: sub-domains per AZPO for local decisions plus a cross-AZPO Economics Coordination domain for inter-AZPO allocation. Three domain contracts replace the two contested ones. Both factions participate in consent. See `references/stress-tests.md` §4.

### 5. Large-Scale Replication

OmniOne grows from 5 domains to 200 across 15 AZPOs. Domain contracts are self-documenting; the dependencies element creates a navigable registry graph. Nested delegation keeps any single delegating body's domain count manageable. The 6-month evaluation cadence prevents stale domains from accumulating. At 200 domains the registry shows 180 active, 8 under_review, 7 provisional, 5 vacant — all statuses are visible, no domains are hidden or informally operated. See `references/stress-tests.md` §5.

### 6. External Legal Pressure

A government requires a "compliance officer" role with unilateral override authority — incompatible with NEOS consent principles. A "Regulatory Compliance" domain is created with a key responsibility for legal reporting. The constraints element explicitly states: the steward cannot override domain decisions unilaterally; regulatory concerns enter the ACT process or escalate to OSC. The government's requirement is satisfied by the domain's existence and the steward's individual legal accountability; the unilateral authority is structurally absent from the contract. See `references/stress-tests.md` §6.

### 7. Sudden Exit of 30%

Thirty percent of domain stewards exit simultaneously. Every affected domain enters "vacant" status immediately. Delegating bodies convene an emergency triage: domains are ranked by operational criticality. Essential domains are prioritized for 30-day emergency assignment from remaining active members. Non-essential domains are fast-tracked through role-sunset if responsibilities can be absorbed by adjacent domains. The 30-day vacant window prevents paralysis — the ecosystem operates through delegating-body temporary stewardship while assignments are finalized. Domain contracts remain valid throughout; vacancy is a stewardship gap, not a governance gap. See `references/stress-tests.md` §7.
