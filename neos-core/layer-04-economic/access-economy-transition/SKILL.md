---
name: access-economy-transition
description: "Manage the staged transition from currency-dependent resource exchange to access-based resource flow -- assess readiness, run pilots, govern the pace of change, and protect the ecosystem from both premature leaps and captured stagnation."
layer: 4
version: 0.1.0
depends_on: [resource-request, funding-pool-stewardship, commons-monitoring, act-consent-phase]
---

# access-economy-transition

## C. Trigger Conditions

- A circle or ETHOS identifies that it may be ready to advance to the next economic stage
- A scheduled transition readiness review reaches its due date (default: annual for each circle)
- Commons monitoring data reveals that a circle is functionally operating at a different stage than its formal designation
- A pilot program reaches its evaluation milestone
- A rollback trigger is activated (defined in the original transition proposal)
- An ecosystem-level transition conversation is initiated by the OSC or by participant petition (minimum 20% of ecosystem membership)
- External economic conditions change materially (currency instability, regulatory shifts) affecting the viability of the current stage

## D. Required Inputs

- **Current stage assessment**: the circle or ETHOS's current formal economic stage and the date it entered that stage (mandatory, sourced from the agreement registry)
- **Readiness indicators**: measurable criteria for advancement to the next stage (mandatory, defined in the transition framework with ecosystem defaults)
- **Commons health data**: recent commons monitoring reports showing resource flow patterns, sustainability metrics, and accessibility data for the circle (mandatory, sourced from commons-monitoring)
- **Participant survey**: structured assessment of participant confidence in advancing, specific concerns, and unmet needs at the current stage (mandatory, minimum 60% response rate from affected participants)
- **Pilot proposal** (if advancing): description of the pilot program, scope, timeline, success criteria, rollback triggers, and resource requirements (mandatory for any stage advancement)
- **External dependency analysis**: assessment of how the transition affects relationships with external entities (suppliers, legal jurisdictions, partner organizations) that operate in currency economies (mandatory)

## E. Step-by-Step Process

1. **Initiate readiness assessment.** A circle steward, ETHOS coordinator, or participant group requests a transition readiness assessment. The request specifies: current stage, target stage (must be adjacent), and the rationale for considering advancement. The request is registered in the agreement registry.
2. **Gather readiness data.** The assessment team (assigned through role-assignment, minimum 3 members including at least one skeptic of the proposed transition) collects:
   - Commons health data from the most recent two monitoring reports
   - Participant survey responses (60% minimum response rate required)
   - External dependency analysis
   - Current-stage performance metrics: how well does the circle function at its current stage?
3. **Evaluate readiness criteria.** The assessment team evaluates the circle against stage-specific readiness criteria:
   - *Stage 1 to 2 (currency to hybrid)*: functioning pool governance, active resource-request process, at least one Current-See type in use, 70%+ participant familiarity with Current-See mechanics, no critical commons health flags.
   - *Stage 2 to 3 (hybrid to Current-See primary)*: 80%+ of internal transactions successfully using Current-Sees, participant basic needs met through ecosystem resource flows, external transaction pathway established for currency-required obligations, 75%+ participant confidence in advancement.
   - *Stage 3 to 4 (Current-See primary to access economy)*: resource flows governed entirely by need and stewardship assessment, no participant reports unmet basic needs due to resource access barriers, commons monitoring shows sustainable and equitable resource distribution for 4+ consecutive quarters, 80%+ participant confidence, external obligations managed through a dedicated interface circle.
4. **Draft transition assessment.** The assessment team produces a transition stage assessment document using `assets/transition-assessment-template.yaml`. The document reports: each readiness criterion, current measurement, whether it is met, overall readiness determination, and recommended next steps. If readiness is not met, the document identifies the specific gaps and recommends actions to close them.
5. **Community review.** The transition assessment is presented to all affected participants at a community review session. The facilitator ensures both advancement advocates and skeptics have equal voice. The assessment team answers questions about methodology and findings.
6. **Propose pilot (if readiness criteria met).** If the assessment shows readiness, the advancement advocates draft a pilot proposal. The pilot must define: scope (which resource types or domains transition first), timeline (minimum 90 days, maximum 12 months), success criteria (measurable outcomes that must be achieved for the pilot to be considered successful), rollback triggers (specific conditions that force the pilot to halt and the circle to revert), and resource requirements.
7. **Pilot consent through ACT.** The pilot proposal enters the ACT process at the circle level for circle-specific transitions, or at the ecosystem level for ETHOS-wide or ecosystem-wide transitions. The consent phase must address objections from participants who are concerned about the transition's impact on their ability to meet basic needs. No pilot proceeds over a reasoned objection that the transition threatens participant welfare.
8. **Execute pilot.** The pilot operates for its defined duration. Commons monitoring tracks pilot-specific metrics alongside regular reporting. The pilot steward publishes monthly progress reports comparing actual outcomes to success criteria.
9. **Evaluate pilot.** At the pilot's end date, the assessment team evaluates outcomes against success criteria. The evaluation is presented at a community review session. If success criteria are met and no rollback triggers activated, the circle may propose full adoption.
10. **Full adoption or rollback.** Full adoption requires a fresh consent round (not an extension of the pilot consent). The adoption proposal includes: the scope of full transition, timeline for remaining domains to transition, support resources for participants who need additional time, and ongoing monitoring commitments. If the pilot failed to meet success criteria, the circle reverts to its previous stage. Rollback is not failure -- it is the governance system functioning correctly.

## F. Output Artifact

A transition stage assessment document following `assets/transition-assessment-template.yaml`. The document contains: assessment ID, circle or ETHOS name, current stage, target stage, assessment date, assessment team roster, readiness criteria evaluation (criterion-by-criterion with measurements and met/unmet status), participant survey summary, commons health data summary, external dependency analysis, overall readiness determination, recommended next steps, pilot proposal (if applicable) with scope, timeline, success criteria, and rollback triggers, and the next scheduled assessment date. The document is registered in the agreement registry and accessible to every ecosystem participant.

## G. Authority Boundary Check

- **No circle** can be compelled to advance stages by ecosystem-level decision. Advancement is always initiated by the circle itself. The ecosystem can encourage, provide resources, and share best practices, but the consent of the transitioning circle is structurally required.
- **No individual** can block a transition that has achieved consent by invoking personal preference. Objections must be reasoned and specific -- "I prefer currency" is not a reasoned objection; "The participant survey shows 40% of members cannot meet rent obligations through Current-Sees" is.
- **The assessment team** evaluates readiness but does not decide whether to proceed. The decision belongs to the affected circle through the ACT consent process.
- **OSC** has oversight of ecosystem-wide transition trajectory but cannot override circle-level transition decisions. OSC may raise concerns through the advice phase and may object in consent rounds for ecosystem-level proposals.
- **Pilot stewards** manage pilot operations within the defined scope. They cannot expand the pilot's scope, extend its timeline, or modify success criteria without a new consent round.
- **Rollback authority** is distributed: any participant in the pilot scope can invoke a rollback trigger if the predefined conditions are met. Rollback does not require a consent round -- the triggers are pre-consented as part of the pilot approval.

## H. Capture Resistance Check

**Capital capture.** Participants who hold significant accepted-currency assets resist transition because it reduces the relative value of their holdings within the ecosystem. The skill prevents stagnation-by-capture through mandatory annual readiness reviews: the circle cannot simply avoid the question. The assessment team must include at least one transition advocate, preventing capture of the assessment process by status-quo beneficiaries. The consent process requires that objections to advancement identify specific structural concerns, not preservation of personal economic advantage. "My currency savings become less useful" is not a reasoned objection to a transition that the community is ready for.

**Charismatic capture.** A visionary leader pushes for premature transition, painting caution as lack of courage. The skill resists this through mandatory readiness criteria: enthusiasm does not satisfy a quantitative threshold. The participant survey captures individual confidence levels, not group sentiment influenced by a charismatic pitch. The assessment team includes at least one skeptic who structurally represents caution. The pilot requirement means even a consented transition must prove itself at small scale before adoption.

**Emergency capture.** An economic crisis (currency devaluation, banking disruption) is used to justify emergency stage advancement without proper assessment. The skill requires that emergency economic conditions trigger a readiness assessment, not automatic advancement. Emergency conditions may accelerate the assessment timeline but cannot bypass the pilot requirement. A currency crisis does not mean the ecosystem is ready for Current-See primary economics -- it means the assessment needs to happen quickly with honest evaluation of whether the alternative infrastructure is ready.

**Informal capture.** A circle operates at a higher stage informally without going through the formal transition process. This creates risk because the governance safeguards, rollback triggers, and monitoring commitments are absent. The commons-monitoring skill detects stage-reality mismatches: if a circle formally at Stage 1 shows resource flow patterns characteristic of Stage 2, the monitoring report flags it and recommends formal assessment. Informal transitions have no governance legitimacy and no rollback protection.

## I. Failure Containment Logic

- **Readiness assessment shows not ready**: the assessment documents specific gaps and recommends targeted actions. The circle remains at its current stage with no stigma. A follow-up assessment is scheduled (default: 6 months). Not-ready is information, not failure.
- **Participant survey response rate below 60%**: the assessment cannot proceed. The circle extends the survey period by 14 days and addresses participation barriers. If the rate remains below 60%, the assessment is postponed and the low engagement itself becomes a finding (a circle that cannot engage 60% of its members in economic transition questions may not be ready for transition).
- **Pilot fails to meet success criteria**: the circle reverts to its previous stage. The pilot evaluation documents what worked, what did not, and what would need to change before reattempting. The failed pilot's data enters the commons monitoring record for future assessment teams to reference.
- **Rollback trigger activated mid-pilot**: the pilot halts immediately. Resources allocated to the pilot are wound down per the pilot proposal's rollback procedures. Participants affected by the rollback receive transitional support (currency-bridge funding, temporary resource access) for 30 days.
- **Consent fails for pilot or adoption**: the proposal is denied with documented rationale. The circle may revise the proposal and resubmit after a 30-day cooling period. The cooling period prevents the same proposal from being immediately re-presented with minor cosmetic changes.

## J. Expiry / Review Condition

- Transition stage assessments are valid for 12 months. After 12 months without action, a new assessment is required before proposing advancement. Economic conditions change; readiness measured a year ago may no longer reflect current reality.
- Pilot approvals specify a timeline with a hard end date. Pilots that exceed their timeline without evaluation trigger a mandatory review. The pilot does not auto-extend -- a new consent round is required for extension.
- Each circle's formal stage designation is reviewed annually as part of the ecosystem governance review. The review confirms that the circle's formal stage matches its operational reality.
- Rollback triggers have no expiry within the pilot period. Once the pilot transitions to full adoption, the rollback triggers are replaced by the ongoing monitoring thresholds defined in the adoption agreement.
- Ecosystem-level transition trajectory (the overall pace and direction of the ecosystem's economic evolution) is reviewed by the OSC annually, with findings shared at TH.

## K. Exit Compatibility Check

When a participant exits during an active transition pilot:
- The participant's obligations within the pilot wind down over 30 days. Resources allocated to them through the pilot revert to the pool.
- The participant's exit does not invalidate the pilot. The assessment team notes the departure and evaluates whether it affects pilot metrics.
- If the departing participant holds a critical pilot role (pilot steward, assessment team member), a replacement is appointed through role-assignment within 14 days.

When a significant portion of participants (20%+) exit during a transition:
- The pilot triggers a mandatory reassessment of its success criteria and rollback triggers. The reduced participant base may affect the pilot's viability.
- The transition assessment is invalidated if the participant survey that supported it no longer represents the current membership (response base drops below 50% of current members).
- The governing circle decides through consent whether to continue, modify, or halt the pilot based on the reassessment.

When a participant exits who opposes the transition:
- Exit does not count as consent for the transition. The consent record reflects only active participants' positions.
- If the departing opponent's objection was the basis for a modification to the pilot, that modification remains in effect.

## L. Cross-Unit Interoperability Impact

- Each ETHOS operates at its own economic stage. SHUR Bali might be at Stage 2 while SHUR Portugal remains at Stage 1. The transition skill supports this heterogeneity by design.
- Cross-ETHOS transactions between units at different stages use the higher-stage unit's mechanisms where both parties consent, or the lower-stage unit's mechanisms as the default. A Stage 2 ETHOS transacting with a Stage 1 ETHOS uses currency by default, with Current-Sees as an option if both parties agree.
- Ecosystem-level transition proposals (moving the entire ecosystem's baseline stage) require consent from every ETHOS. No ETHOS can be forced to advance by ecosystem-level decision.
- Pilot programs may operate across ETHOS if all affected units consent. Cross-ETHOS pilots provide valuable data on inter-stage transaction handling.
- The inter-unit coordination protocol (Layer V, deferred) will define how economic stage differences are managed in cross-ecosystem federation.
