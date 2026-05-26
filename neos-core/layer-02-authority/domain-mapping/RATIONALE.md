---
skill: domain-mapping
type: rationale
---

# domain-mapping — Rationale & Design Notes

## A. Structural Problem It Solves

Without formal domain definitions, authority is assumed, informal, and inconsistent. Participants act beyond their intended scope — not out of malice but because no boundary was ever drawn. When disputes arise, there is no structural reference to adjudicate; the conflict becomes personal rather than procedural. This skill provides the canonical schema for defining what authority looks like, who holds it, and what it cannot do. Every governance action in NEOS traces back to a domain contract. Without this skill, all other authority claims are provisional guesses.

## B. Domain Scope

Any circle, role, or structural body that exercises governance authority within the ecosystem. This includes new circles being formed, existing roles that have been operating without formal domain contracts, and any body whose scope is contested or ambiguous. Domain-mapping applies to every ETHOS and crosses ETHOS boundaries when cross-unit dependencies exist. Out of scope: the assignment of a specific person to a defined domain (that is role-assignment), and the resolution of overlapping claims between already-defined domains (that is authority-boundary-negotiation).

## OmniOne Walkthrough

The Agents of the Ecosystem (AE) decides to create a new Economics circle. Mireille, an AE facilitator, confirms that no existing domain contract covers economics coordination — the registry shows only a general "AE operations" domain that explicitly lists economics as out-of-scope pending a dedicated circle.

Mireille leads the AE through drafting all 11 elements:

- **Purpose:** Steward the ecosystem's economic coordination — resource allocation, funding pool management, and economic policy proposals.
- **Key responsibilities:** Manage funding requests from ETHOS and circles; maintain economic transparency through monthly reporting; propose resource distribution changes to the AE; coordinate with OSC on ecosystem-level economic policy.
- **Customers:** All participants and ETHOS requesting or receiving resources; the OSC for economic policy input.
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

Two AE factions submit competing draft domain contracts for economics — one centralized, one distributed. The registry flags both drafts as claiming the same scope. Neither proceeds to consent. GAIA Level 4 coaching maps the structural concern behind each position: centralists fear fragmented accountability; distributionists fear capture. The coach surfaces a federated model: sub-domains per ETHOS for local decisions plus a cross-ETHOS Economics Coordination domain for inter-ETHOS allocation. Three domain contracts replace the two contested ones. Both factions participate in consent. See `references/stress-tests.md` §4.

### 5. Large-Scale Replication

OmniOne grows from 5 domains to 200 across 15 ETHOS. Domain contracts are self-documenting; the dependencies element creates a navigable registry graph. Nested delegation keeps any single delegating body's domain count manageable. The 6-month evaluation cadence prevents stale domains from accumulating. At 200 domains the registry shows 180 active, 8 under_review, 7 provisional, 5 vacant — all statuses are visible, no domains are hidden or informally operated. See `references/stress-tests.md` §5.

### 6. External Legal Pressure

A government requires a "compliance officer" role with unilateral override authority — incompatible with NEOS consent principles. A "Regulatory Compliance" domain is created with a key responsibility for legal reporting. The constraints element explicitly states: the steward cannot override domain decisions unilaterally; regulatory concerns enter the ACT process or escalate to OSC. The government's requirement is satisfied by the domain's existence and the steward's individual legal accountability; the unilateral authority is structurally absent from the contract. See `references/stress-tests.md` §6.

### 7. Sudden Exit of 30%

Thirty percent of domain stewards exit simultaneously. Every affected domain enters "vacant" status immediately. Delegating bodies convene an emergency triage: domains are ranked by operational criticality. Essential domains are prioritized for 30-day emergency assignment from remaining active members. Non-essential domains are fast-tracked through role-sunset if responsibilities can be absorbed by adjacent domains. The 30-day vacant window prevents paralysis — the ecosystem operates through delegating-body temporary stewardship while assignments are finalized. Domain contracts remain valid throughout; vacancy is a stewardship gap, not a governance gap. See `references/stress-tests.md` §7.
