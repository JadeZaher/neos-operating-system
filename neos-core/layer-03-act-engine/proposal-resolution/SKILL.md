---
name: proposal-resolution
description: "Resolve stalled proposals through the GAIA 6-level escalation -- from in-circle consensus through coaching, alignment sense-making, and value-based decision resolution -- with clear entry criteria, process, and handoff at each level."
layer: 3
version: 0.1.0
depends_on: [proposal-creation, act-advice-phase, act-consent-phase, act-test-phase, consensus-check, domain-mapping]
---

# proposal-resolution

## A. Structural Problem It Solves

Without a defined escalation path, stalled proposals either die quietly (the proposer gives up) or are resolved through informal power (someone with enough social capital forces an outcome). This skill provides six levels of escalation, each with clear entry criteria, defined process, and handoff conditions to the next level. It ensures that even the most contentious proposals have a legitimate resolution path. No proposal should be abandoned because "we just couldn't agree" — the GAIA model always provides a next step.

## B. Domain Scope

Any proposal that has not been resolved at the standard ACT level — where the advice phase produced irreconcilable input, the consent phase exhausted its maximum integration rounds, or the test phase results are disputed. The skill operates across all proposal types and all scope levels, with the resolution body scaling to match the proposal's impact.

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

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

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
- Federation extensibility: cross-ecosystem proposals that reach Level 6 require a deciding body with representation from both ecosystems. This coordination is deferred to Layer V but the structural slot exists in the Level 6 process.

## OmniOne Walkthrough

A contentious proposal to restructure how OmniOne's emergency fund is allocated generates sustained disagreement. Currently, each circle receives an equal share of the emergency pool. The proposal would allocate based on documented risk exposure (circles operating physical spaces get more because their emergencies cost more).

**Level 3 (Advice + Panel):** During the advice phase, two AE circles give contradictory advice. The Infrastructure circle supports risk-based allocation (they manage SHUR buildings with high emergency costs). The Education circle opposes it (they have lower risk exposure but have had two unexpected emergencies in the past year that exceeded their equal share). The proposer cannot integrate both positions.

**Level 4 (Coaching):** A neutral coach, Sana, maps the tension. She identifies that both circles share a concern about emergency preparedness — they disagree on the mechanism. Infrastructure's core concern: they consistently underfund building maintenance emergencies. Education's core concern: unexpected emergencies happen to any circle, and risk-based allocation punishes circles for having historically lower risk profiles. Sana facilitates a "Doing Both Solution": risk-based allocation for the first 70% of the emergency fund (addressing Infrastructure's building maintenance needs), with the remaining 30% held as a universal pool available to any circle for unexpected emergencies (addressing Education's concern about unpredictable needs). This third solution does not simply split the difference — it creates a two-pool structure that serves both purposes.

The synthesized proposal returns to the consent phase. Consent is achieved with one stand-aside (a small circle that has never used emergency funds and has no strong position).

**What if Level 4 had failed:** If coaching had not produced a synthesis, the proposal would escalate to Level 5 (Alignment Sense Making). The OSC would evaluate the proposal against existing stewardship agreements and the UAF's equity principles. If Level 5 could not resolve, Level 6 would produce a structured comparison chart: values alignment (both equity and preparedness are ecosystem values), affected parties impact (infrastructure circles benefit from risk-based, smaller circles benefit from universal pool), precedent (no prior emergency fund restructuring), long-term impact (does the change scale well?). The OSC would make a final determination.

Edge case: An AE member tries to skip from Level 3 directly to Level 6, arguing "we all know this will end up at the OSC anyway." The skip-level rule requires consent of ALL affected parties. The Infrastructure and Education circles both refuse to skip — they want the coaching process to explore synthesis first. The escalation proceeds through Level 4 as designed.

## Stress-Test Results

### 1. Capital Influx

A donor-influenced proposal reaches GAIA escalation when the consent phase produces objections about the donor's conditions. At Level 4, the coach identifies that the core tension is between gratitude for the donation and structural resistance to conditional giving. The third solution: accept the donation unconditionally and create a stewardship agreement for the funded project that follows normal governance — the donor is welcome to participate as a steward but does not receive special authority. If coaching fails, Level 5 evaluates the proposal against the UAF's "Capital does not equal Power" principle and finds the conditional terms incompatible. The proposal is modified to remove the conditions. The donor may still contribute but without governance privileges attached.

### 2. Emergency Crisis

An emergency proposal reaches Level 3 escalation because the compressed advice phase produced irreconcilable input about evacuation priorities. Emergency escalation follows the same levels but under compressed timelines: Level 4 coaching runs in a single intensive session (4 hours rather than the typical week). Level 5 alignment check is conducted by available OSC members via emergency communication. The compressed timeline does not skip levels — it compresses each level's process. The resolution must still be legitimate, and emergency decisions are flagged for post-emergency review when normal timelines resume.

### 3. Leadership Charisma Capture

A charismatic leader's proposal has been rejected at Level 3 (advice contradicts the proposal) and Level 4 (coaching found no viable third solution). The leader attempts to force escalation to Level 6, where they have significant influence over the OSC. The forced-escalation prevention requires documented failure at each level — the leader must demonstrate that Level 5 alignment review was attempted and failed. At Level 5, the Wisdom Council (composed of participants who are NOT parties to the proposal) provides an independent structural evaluation. If the Wisdom Council finds the proposal misaligned with existing agreements, escalation to Level 6 becomes a harder case for the leader. The multi-level structure ensures that charismatic influence encounters structural checks at every stage.

### 4. High Conflict / Polarization

A deeply polarizing proposal about OmniOne's expansion strategy escalates through all 6 GAIA levels. Half the ecosystem wants rapid expansion (new SHUR locations in 3 countries); the other half wants consolidation (strengthen existing Bali operations before expanding). Level 4 coaching produces a sequenced approach (consolidate for 6 months, then expand one location as a pilot) but one faction rejects the compromise. Level 5 alignment review finds that both approaches are consistent with the Master Plan's vision — the plan supports both growth and sustainability. At Level 6, the OSC produces the comparison chart: values alignment (both serve the mission), affected parties impact (rapid expansion spreads resources thin; consolidation delays new communities), precedent (no prior expansion decision at this scale), long-term impact (sequencing reduces risk). The OSC determines: adopt the sequenced approach with a specific 6-month consolidation timeline and a defined pilot location. The determination is final for this proposal cycle.

### 5. Large-Scale Replication

At 5,000 members, GAIA escalation handles volume through domain scoping. Most proposals that escalate do so within their circle or ETHOS — they never reach Level 5 or 6 because the coaching process at Level 4 resolves most tensions. Ecosystem-level escalations to Level 5-6 remain rare (perhaps 2-3 per year) because most governance happens at lower scope. The coaching capacity scales through trained coaches in each ETHOS. The OSC's Level 6 function is reserved for truly ecosystem-wide decisions where lower-level synthesis has been exhausted.

### 6. External Legal Pressure

A regulatory compliance proposal escalates because participants disagree about how to implement the required changes. At Level 4, the coach identifies that the legal requirement is non-negotiable for the relevant jurisdiction — the coaching question is not whether to comply but how. The third solution addresses the how: minimal-footprint compliance that satisfies the regulation while preserving maximum governance autonomy. Level 5 alignment review confirms the approach is consistent with the UAF's legal compliance provisions. The resolution demonstrates that external pressure does not bypass the GAIA process — it becomes input to the process, and the ecosystem decides how to respond through its own governance structure.

### 7. Sudden Exit of 30% of Participants

A mass departure itself may resolve some stalled proposals: if the departing members were the primary objectors, the consent phase may succeed with the remaining participants. Alternatively, if the departing members were the primary proposers, the proposal may be archived if no one adopts it. For escalated proposals still in process, the GAIA levels continue with recalculated participant lists. If the mass exit was triggered by a specific proposal in escalation, this is documented as critical context at whatever GAIA level the proposal currently occupies. The deciding body at any level must consider whether the exodus represents a structural signal about the proposal's viability.
