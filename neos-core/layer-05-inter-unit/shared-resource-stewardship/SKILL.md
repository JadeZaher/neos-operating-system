---
name: shared-resource-stewardship
description: "Govern jointly-held resources across multiple ETHOS -- shared pools, infrastructure, repositories, and services -- through multi-party consent with rotating stewardship and equitable access rules."
layer: 5
version: 0.1.0
depends_on: [cross-ethos-request, agreement-creation, funding-pool-stewardship, role-assignment]
---

# shared-resource-stewardship

## A. Structural Problem It Solves

When multiple ETHOS share resources without formal governance, the largest contributor tends to claim control, or the resource falls into a governance vacuum where no one is accountable. Informal sharing works until the first disagreement -- then whoever has more power or history with the resource dictates terms. This skill ensures shared resources have explicit governance agreements that all participating ETHOS ratified through their own processes, with rotating stewardship that prevents any single ETHOS from entrenching control. Contribution does not equal governance authority.

## B. Domain Scope

This skill applies to any resource jointly held by two or more ETHOS:

- **Shared funding pools** -- financial reserves governed by multiple ETHOS for mutual benefit
- **Shared physical infrastructure** -- co-located facilities, equipment, or land managed across ETHOS boundaries
- **Shared knowledge repositories** -- documentation, training modules, governance templates maintained collectively
- **Shared services** -- facilitation pools, training programs, technical support operated across units

The skill does not cover resources held by a single ETHOS (use funding-pool-stewardship from Layer IV) or personal property of individual participants.

## C. Trigger Conditions

- Two or more ETHOS identify a resource they want to share rather than duplicate
- An existing informally-shared resource needs governance formalization
- A federation agreement calls for the establishment of a shared resource
- A cross-ETHOS request reveals a resource that would benefit from joint stewardship

## D. Required Inputs

- **Participating ETHOS** -- all units that will share governance of the resource (mandatory)
- **Resource description** -- what the resource is, its current state, and its purpose (mandatory)
- **Resource type** -- pool, infrastructure, repository, or service (mandatory)
- **Proposed governance structure** -- stewardship model, access rules, contribution commitments, reporting schedule (mandatory)
- **Proposed review cycle** -- when the governance agreement will be reviewed (mandatory; minimum: annual)
- **Exit terms** -- what happens when an ETHOS withdraws (mandatory; default: 90-day notice with contribution wind-down)

## E. Step-by-Step Process

1. **Propose shared resource.** One or more ETHOS submit a cross-ETHOS request (per cross-ethos-request skill) proposing the establishment of a jointly governed resource.
2. **Negotiate governance terms.** Each participating ETHOS runs an internal advice phase on the proposal. Key terms are negotiated collaboratively: stewardship rotation, access rules, contribution commitments, reporting cadence, and exit provisions.
3. **Draft governance agreement.** The proposing parties draft a shared resource governance agreement using `assets/shared-resource-agreement-template.yaml`, incorporating negotiated terms.
4. **Each ETHOS ratifies through consent.** Every participating ETHOS runs its own consent round. No ETHOS is bound until it has completed its own ACT process. If one ETHOS's consent fails, the process returns to negotiation to address that ETHOS's concerns.
5. **Appoint first steward.** The governance agreement specifies which ETHOS provides the first steward. The appointed steward is confirmed through the role-assignment skill in their home ETHOS. A successor from a different ETHOS is named per the rotation schedule.
6. **Operate with reporting.** The steward manages day-to-day operations within the governance agreement's terms and produces regular reports visible to all participating ETHOS.
7. **Review at defined intervals.** All participating ETHOS review the governance agreement at the scheduled review date. Amendments follow the same multi-party consent process as establishment.

## F. Output Artifact

A shared resource governance agreement following `assets/shared-resource-agreement-template.yaml`, containing: agreement ID, resource name and description, resource type, participating ETHOS, access tiers, contribution commitments per ETHOS, stewardship rotation schedule, reporting cadence, review date, exit terms, and ratification records from each ETHOS. Registered in every participating ETHOS's agreement registry with linked entries.

## G. Authority Boundary Check

- **No single ETHOS controls** the shared resource regardless of contribution level. Contribution size does not grant proportional governance authority.
- **Steward authority** is limited to operational management within the governance agreement's terms. Strategic decisions (access rule changes, contribution adjustments, sunset) require consent from all participating ETHOS.
- **All participating ETHOS** must consent to governance agreement amendments. One ETHOS cannot unilaterally change access rules, contribution requirements, or stewardship terms.
- **The steward's home ETHOS** does not receive preferential access or reporting by virtue of hosting the steward role.

## H. Capture Resistance Check

**Contribution-proportional control.** A larger contributor claims more governance authority based on financial or material contribution. Resistance: the governance agreement explicitly states that governance authority is equal across participating ETHOS regardless of contribution level. Contribution commitments are documented but do not translate into differential governance rights.

**Steward capture.** The steward favors their home ETHOS in resource allocation, access decisions, or information sharing. Resistance: rotating stewardship limits any home-ETHOS advantage to the steward's term. Reporting requirements make allocation patterns visible to all ETHOS. Any ETHOS may request a steward review if favoritism is observed.

**Information asymmetry.** One ETHOS gains exclusive knowledge of the resource's state and uses it to shape governance decisions. Resistance: all participating ETHOS receive the same reporting data. Access to raw resource information is specified in the governance agreement and must be equitable.

**Free-rider dynamics.** An ETHOS benefits from the shared resource without meeting its contribution commitments. Resistance: contribution commitments are explicit with consequence clauses (review trigger, access suspension pending remediation). Persistent free-riding is treated as grounds for exit review.

## I. Failure Containment Logic

- **One ETHOS fails consent during ratification:** The process returns to negotiation to address that ETHOS's concerns. The agreement does not take effect until all participating ETHOS consent. Other ETHOS' prior consent holds but may be reaffirmed if negotiations exceed 90 days.
- **ETHOS withdraws from arrangement:** Per exit terms (default: 90-day notice, contribution wind-down). Access rights sunset at end of notice period. Resource continues under remaining participants' governance, triggering a review.
- **Steward misconduct:** Any participating ETHOS may request a steward review. If misconduct is confirmed, an interim steward from a different ETHOS is appointed pending full rotation.
- **Resource depleted or destroyed:** All participating ETHOS convene an emergency decision on next steps: reconstitute, wind down, or transfer remaining assets per exit terms.
- **Negotiation stalls:** Any participating ETHOS may withdraw from negotiations with documentation. This does not obligate remaining parties.

## J. Expiry / Review Condition

- **Annual review minimum.** The governance agreement must state a review date no more than 12 months from ratification.
- **Missed review:** Agreement enters a 60-day grace period. After 60 days without review, status changes to "under review" -- operational stewardship continues but no strategic decisions may be made.
- **Governance agreements do not auto-expire.** The resource continues under existing terms until review produces a new agreement or sunset decision.
- **Steward rotation:** Configurable per agreement; recommended 12-month terms with no ETHOS holding consecutive steward terms.

## K. Exit Compatibility Check

- **Exiting ETHOS's contributions** are handled per exit terms (default: contribution wind-down over notice period, no clawback of previously contributed resources)
- **Exiting ETHOS's access** ceases at end of notice period; content they contributed remains under the resource's governance (individual original works revert to creators per UAF)
- **In-progress stewardship** by an exiting ETHOS's member: steward completes handoff within notice period or resigns with interim appointment
- **Resource continues** under remaining participants' governance; review is triggered to assess terms for the smaller participant set
- **Last ETHOS standing:** If all but one ETHOS withdraws, the resource must either wind down or be formally transferred to the remaining ETHOS through a new governance process

## L. Cross-Unit Interoperability Impact

This skill is itself a cross-unit interoperability mechanism. It defines how ETHOS govern resources in the space between them. Outputs are registered in every participating ETHOS's agreement registry with linked entries. The skill references cross-ethos-request for initial proposals and federation-agreement for formalizing the broader relationship that shared resource governance is often embedded within. New ETHOS joining an existing arrangement follow the same ratification process and the existing agreement is amended to include them.

## OmniOne Walkthrough

Camille, Governance circle steward at the Bali SHUR, has spent six months documenting consent round facilitation, escalation protocols, and TH member onboarding guides. She realizes this material would benefit other SHURs and proposes a shared governance knowledge repository. The Costa Rica SHUR, where Rafael coordinates the Governance circle, is simultaneously developing conflict resolution modules.

**Proposal.** Camille drafts a cross-ETHOS request from Bali's Governance circle to Costa Rica: "We propose establishing a shared knowledge repository for governance best practices." Bali's circle gives consent. The request is sent to Rafael.

**Costa Rica advice.** Rafael runs a 7-day advice window. Lucia raises a concern that "shared repository" is too vague -- she wants clarity on who can add, edit, and version content. Rafael transmits this with a counter-proposal: the repository should be bidirectional with explicit read-access and edit-access tiers.

**Three negotiation rounds.** Camille and Rafael hold three joint drafting sessions over four weeks. Round 1: they agree on resource type (knowledge repository), contribution model (two modules per quarter per SHUR), and annual review. Access tiers remain unresolved -- Bali wants open editing; Costa Rica wants designated contributors. Round 2: Camille proposes three tiers -- all TH/AE get read access; up to five designated contributors per SHUR get edit access; the steward gets admin access. Rafael accepts but wants a 30-day review window before adaptations of flagged modules. Round 3: both agree on the full model plus a "review-before-adapt" flag.

**Each SHUR runs consent.** Bali: 8 of 9 participate, all consent. Costa Rica: 7 members. In Round 1, 5 consent, 1 stands aside, and Lucia objects -- the "up to 5 contributors" clause does not specify selection method. Integration round: Camille and Rafael add a clause requiring open nomination with consent of the Governance circle. Round 2: all 7 consent.

**First steward.** Camille is appointed steward (12-month term). Rafael is named successor. Monthly reporting begins.

**Edge case: Mexico joins six months later.** Mexico's Governance circle coordinator Pilar contacts Camille about joining. Onboarding follows the same process: Mexico submits a cross-ETHOS request to both Bali and Costa Rica. Mexico's contribution commitment is set at one module per quarter (given they are newer). All three SHURs run consent on the amendment. The governance agreement is updated with Mexico as a third participant, and the steward succession extends to include Pilar after Rafael's term.

**Output.** `SRS-OMNI-2026-001`, registered in both registries with linked entries. Resource: "OmniOne Governance Knowledge Repository." Access tiers, contribution commitments, steward rotation, reporting schedule, and review date documented.

## Stress-Test Results

### 1. Capital Influx

A philanthropic foundation offers $200,000 to the OmniOne governance repository on condition that their research institute gets permanent editorial control and priority publication rights. Camille documents the offer as a capital capture vector in the negotiation record. During Bali's advice phase, Priya points out that permanent editorial control is exactly the structural capture the governance agreement prevents -- contribution does not equal governance authority. Costa Rica's advice phase reaches the same conclusion independently. The grant can be accepted without governance strings only if the foundation waives governance rights in writing. If they decline, the grant is declined. The governance structure is not modified to accommodate a funder.

### 2. Emergency Crisis

A cyberattack destroys the primary server hosting the repository. Camille invokes emergency procedures, notifying both SHURs within 24 hours. Restoration from backup falls within the steward's operational mandate and proceeds immediately. An emergency consent round (24-hour advice, 50% quorum) authorizes additional infrastructure spending beyond the steward's operational budget. Emergency decisions are logged and reviewed at the next reporting cycle. Strategic decisions about permanently changing the hosting model follow the full consent process.

### 3. Leadership Charisma Capture

Camille is widely respected and well-liked. As her term nears its end, community members informally lobby for an extension rather than rotating to Rafael. Rafael raises it formally in the steward report: "Rotation is a capture-resistance mechanism, not a preference." The governance agreement's rotation clause is unambiguous -- amending the succession requires ETHOS-level consent from all participants, submitted 60 days before the transition. When Bali's circle raises the extension formally, Costa Rica notes they did not consent to indefinite Bali stewardship. The rotation proceeds as planned. No individual's reputation overrides a written consent commitment.

### 4. High Conflict

After Mexico joins, a dispute emerges over editorial standards. Bali publishes rough drafts; Mexico applies peer review before publication. The disagreement escalates when Pilar flags Bali modules as "draft quality." Both SHURs bring the conflict to their circles. Rather than one standard winning, a joint advice phase surfaces the core tension. The integration produces a dual-track model: "Working Draft" and "Reviewed" status are both legitimate, clearly labeled. The amendment goes through three-ETHOS ratification and is consented to unanimously.

### 5. Large-Scale Replication

OmniOne expands to 15 SHURs with five shared repositories across different domains. Each follows its own governance agreement with its own participant set. The skill scales because each agreement is self-contained. At 8+ participating ETHOS, parallel advice phases for amendments require clear communication protocols handled by the liaison network. The consent requirement for each ETHOS remains unchanged regardless of scale.

### 6. External Legal Pressure

Indonesia's data sovereignty regulation requires digital repositories holding Indonesian resident data to be hosted locally or registered with a government authority. Camille proposes an amendment: Bali-specific data moves to an Indonesian-hosted mirror while the shared repository continues for non-Bali content. The amendment goes through all-ETHOS consent. Costa Rica wants assurance Bali members retain full access. Mexico has no objection. The regulation is complied with locally without becoming an ecosystem-wide governance change.

### 7. Sudden Exit of 30% of Participants

Three of ten participating SHURs announce withdrawal following a strategic disagreement. Each submits 90-day notice per exit terms. Access continues through the notice period. Contributions wind down on schedule. The remaining seven SHURs convene a mandatory review to assess: steward succession (does the rotation still work?), contribution adequacy, and quorum viability. All seven run consent on a revised governance agreement. The resource continues without interruption.
