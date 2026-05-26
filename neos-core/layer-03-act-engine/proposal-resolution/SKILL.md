---
name: proposal-resolution
description: "Resolve stalled proposals through the GAIA 6-level escalation -- from in-circle consensus through coaching, alignment sense-making, and value-based decision resolution -- with clear entry criteria, process, and handoff at each level."
layer: 3
version: 0.1.0
depends_on: [proposal-creation, act-advice-phase, act-consent-phase, act-test-phase, consensus-check, domain-mapping]
---

# proposal-resolution

## C. Trigger Conditions

- A proposal stalls at the advice phase: contradictory advice cannot be integrated and the proposer cannot proceed
- The consent phase exhausts its maximum integration rounds (3 for normal, 2 for emergency) without resolving all objections
- Test phase results are disputed: the review body cannot agree on the outcome (adopt vs. revert)
- A facilitator determines that a proposal has been cycling between ACT phases without progress

## D. Required Inputs

- The **proposal** with its current status and full history
- The **advice log** (if applicable) showing unresolved contradictions
- The **consent record** (if applicable) showing unresolved objections with stated reasons
- The **test report** (if applicable) showing disputed results
- The **specific point of stalling**: what exactly could not be resolved at the previous level

## E. Step-by-Step Process

The GAIA 6-level escalation (attributed to the Futurist Playground Value Decision Model, adapted for NEOS):

**Level 1: Consensus.** All agree within the scope of the Master Plan or Sub Master Plan.
- *Entry*: the proposal is within a single circle's domain and aligned with existing plans
- *Process*: circle discussion using the consensus-check skill. If all agree, the proposal is resolved
- *Exit*: consensus achieved → resolved. Not achieved → escalate to Level 2

**Level 2: Culture Code.** Circle-internal decision using the circle's own chosen process.
- *Entry*: Level 1 fails, or the proposal is purely internal to the circle's operations
- *Process*: the circle uses whatever decision process they have agreed to in their culture code (may differ from standard ACT)
- *Exit*: resolved internally → done. Decision touches the larger collective → escalate to Level 3

**Level 3: Advice Process + Panel of Experts.** Pre-proposal synergy check, then formal proposal for alignment.
- *Entry*: the proposal affects parties beyond the originating circle, or Level 2 cannot resolve because the issue extends beyond circle boundaries
- *Process*: formal advice phase with expert panel input. The panel consists of participants with relevant domain expertise who are not parties to the proposal. The panel provides structural analysis, not a ruling
- *Exit*: advice integrated and proposal ready for consent → return to act-consent-phase. Cannot be integrated → escalate to Level 4

**Level 4: Coaching.** Finding a third solution between competing options.
- *Entry*: Level 3 produces irreconcilable competing options — the advice phase revealed a genuine tension that cannot be resolved by choosing one side
- *Process*: a neutral coach (not a party to the proposal) maps the competing positions against three domains:
  - *Collective domain*: what serves the whole ecosystem
  - *Community domain*: what serves the affected circle or ETHOS
  - *Private domain*: what serves individual participants
  The coach facilitates synthesis — a "Doing Both Solution" that addresses the core concerns of both positions without simply compromising between them. The coach has process authority to restructure the conversation but has zero authority over the outcome
- *Exit*: third solution found → return to act-consent-phase with the synthesized proposal. No synthesis possible → escalate to Level 5

**Level 5: Alignment Sense Making.** Check against policies, agreements, values.
- *Entry*: Level 4 coaching does not produce a resolution. The proposal has been through at least 3 levels of structured deliberation
- *Process*: the proposal is evaluated against the full policy framework — existing agreements, the UAF, ecosystem values, and precedent. A designated body (may be the steward council or a convened Wisdom Council — see OQ-11) compares the proposal's impact against structural principles. The body may delegate the proposal to a circle with specific domain agency if one exists. The evaluation asks: "Does this proposal align with what we have already agreed to?"
- *Exit*: aligned proposal produced → return to act-consent-phase. Alignment cannot be determined → escalate to Level 6

**Level 6: Decision Resolution.** Value decision model comparison chart.
- *Entry*: all other levels have been exhausted. The proposal has been through consensus, culture code, advice with experts, coaching, and alignment review
- *Process*: a structured comparison chart (Futurist Playground attribution) evaluating:
  - Values alignment: how does each option align with ecosystem founding values?
  - Affected parties impact: who benefits, who is burdened, and is the burden proportionate?
  - Precedent analysis: what decisions has the ecosystem made in similar situations?
  - Long-term impact: what are the second and third-order consequences?
  The deciding body (OSC for ecosystem-level proposals, the originating council for domain-level proposals) reviews the comparison chart and makes a final determination: adopt, modify, or reject
- *Exit*: determination is final for this proposal cycle. If rejected, the proposer may submit a substantially different proposal through a new ACT cycle

## F. Output Artifact

A decision resolution record per `assets/decision-resolution-template.yaml` containing: resolution ID, proposal ID, the level at which resolution was achieved, the full escalation history (each level attempted, entry date, exit date, outcome, notes), and — if Level 6 was reached — the comparison chart and the deciding body's determination with full rationale.

## G. Authority Boundary Check

- **No GAIA level can be skipped** except by consent of all affected parties. A proposer cannot jump directly from Level 1 to Level 6 to reach a body they believe will be sympathetic.
- The **Level 6 deciding body** must include representatives from all affected domains. No domain may be excluded from the final determination.
- **No individual can unilaterally resolve** a proposal at any level. Even the coach at Level 4 has process authority only — they facilitate, they do not decide.
- The **Wisdom Council** at Level 5 (if convened) must not include parties to the proposal under review. Impartiality at this level is structurally required.
- Authority scopes are formally defined by the domain-mapping and role-assignment skills in Layer II (Authority & Role).

## H. Capture Resistance Check

**Forced escalation.** A powerful individual forces rapid escalation to Level 6, bypassing the lower levels where consent-based process might not favor their position. Each escalation requires documented failure at the current level — the consent record showing unresolved objections, the coaching report showing no synthesis achieved. Skipping levels requires consent of ALL affected parties, not just the escalating party.

**Level 6 stacking.** Influential participants stack the Level 6 deciding body with allies. The body must include representatives from all affected domains — domain representation is structural, not discretionary. The deciding body's composition is determined by the proposal's scope, not by the proposer's preferences.

**Coaching capture.** The coach at Level 4 steers the "third solution" toward a pre-determined outcome. The coach has process authority only and the synthesized proposal must still return to the consent phase where all affected parties can consent, stand aside, or object. The coach cannot produce a binding outcome — they produce a proposal that still requires consent.

**Resolution fatigue.** After multiple escalation levels, participants give up and accept whatever is proposed. The escalation process documents everything — if consent is achieved through fatigue rather than genuine agreement, the consent record will show a pattern of stand-asides increasing at each level. A high stand-aside count is itself a signal that the resolution may not be durable.

## I. Failure Containment Logic

- **Level 6 produces a rejected determination**: the proposal is formally rejected. The proposer may submit a substantially different proposal through a new ACT cycle, but the same proposal cannot re-enter the system.
- **No level achieves resolution and the proposal is abandoned**: the existing state remains unchanged. The full escalation history is archived as precedent for future similar proposals.
- **Escalation process stalls** (no one convenes the next level): the proposal-creation stall rules apply — 30-day reminder, 60-day archive. The escalation does not auto-resolve; it simply stops and the status quo prevails.
- **Deciding body at Level 6 is deadlocked**: the deciding body must reach a determination. If they cannot agree, the proposal is rejected by default — the existing state is preserved. This prevents indefinite deliberation from becoming a governance black hole.

## J. Expiry / Review Condition

- Proposals in the GAIA escalation follow the same activity-based expiry rules: 30 days of inactivity triggers a reminder, 60 days triggers archival.
- Emergency proposals escalate through GAIA levels under compressed timelines but cannot skip levels unless all affected parties consent.
- The GAIA model itself can be amended through normal ACT process if the ecosystem determines that the escalation structure needs modification.

## K. Exit Compatibility Check

- If the **proposer exits** during escalation, the proposal may be adopted by another impacted party. The escalation continues from the current level.
- If the **coach exits** at Level 4, a replacement coach is found. Coaching notes from the previous coach are provided to the replacement.
- If a **deciding body member exits** during Level 6 deliberation, a replacement from the affected domain is appointed before the determination proceeds.
- Mass exit may itself resolve the proposal (if the departing parties were the primary objectors) or render it moot (if the departing parties were the primary beneficiaries).

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS proposals that escalate through GAIA levels involve representatives from each affected ETHOS at every level. The escalation is not conducted separately per ETHOS — it is a unified escalation with multi-ETHOS representation.
- The resolution record is entered in all affected ETHOS' registries.
