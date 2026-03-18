---
name: access-economy-transition
description: "Manage the staged transition from currency-dependent resource exchange to access-based resource flow -- assess readiness, run pilots, govern the pace of change, and protect the ecosystem from both premature leaps and captured stagnation."
layer: 4
version: 0.1.0
depends_on: [resource-request, funding-pool-stewardship, commons-monitoring, act-consent-phase]
---

# access-economy-transition

## A. Structural Problem It Solves

Every intentional community that aspires to move beyond conventional economics faces the same trap: either they leap too fast into alternative economics and collapse when participants cannot meet basic needs, or they stagnate in conventional economics because those who benefit from the status quo block transition. Without a structured transition process, the shift from currency-based exchange to access-based resource flow becomes a matter of ideology rather than governance -- champions push, skeptics resist, and the ecosystem oscillates between premature experiments and fearful reversals. Access-economy-transition solves this by defining discrete stages with measurable readiness criteria, consent-based advancement, mandatory pilot testing before ecosystem-wide adoption, and explicit rollback procedures that honor both ambition and caution. The skill ensures that no circle is forced to advance faster than its capacity and no faction can block transition to protect economic advantage.

## B. Domain Scope

This skill applies to any circle or ETHOS assessing, proposing, or executing a transition between economic stages. The four stages are: Stage 1 (currency-dependent) where accepted currencies are the primary medium of exchange, Stage 2 (hybrid) where accepted currencies and Current-Sees operate in parallel with defined exchange relationships, Stage 3 (Current-See primary) where Current-Sees serve as the primary coordination mechanism with accepted currencies used only for external transactions, and Stage 4 (access economy) where resources flow by need and stewardship rather than exchange. The skill governs transitions between adjacent stages only -- no stage can be skipped. Each ETHOS and circle may operate at a different stage. Out of scope: designing the Current-See protocol itself (that is OmniOne-specific infrastructure), managing external fundraising or currency acquisition (outside NEOS scope), and defining what the access economy looks like in full maturity (the skill governs transition, not destination).

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

## OmniOne Walkthrough

The SHUR Bali community within OmniOne has operated at Stage 2 (hybrid currency/Current-See) for 14 months. Leilani, an OSC member and SHUR steward, initiates a transition readiness assessment to evaluate whether SHUR Bali is ready to advance to Stage 3 (Current-See primary). She registers the request in the agreement registry with rationale: "SHUR Bali's internal transactions have been predominantly Current-See-based for three quarters. I believe we may be ready to formalize this as our primary economic mode."

The assessment team is assembled through role-assignment: Naveen (Infrastructure circle, transition advocate), Dayo (Agriculture circle, neutral), and Priya (Economics circle, explicitly skeptical about transition pace). The team collects data over 21 days.

Commons health data from the last two quarterly reports shows: SHUR Bali's internal resource flows are 72% Current-See-based and 28% accepted currency. Flow rates are stable. No concentration flags. Sustainability projections are positive -- Current-See pools are replenishing at a healthy rate.

The participant survey achieves a 78% response rate (39 of 50 SHUR Bali members). Results: 68% express confidence in advancing to Stage 3. However, 22% express concern about meeting external obligations (rent to non-OmniOne landlords, imported materials, medical expenses) without accepted currency. The remaining 10% are neutral.

The external dependency analysis identifies three critical currency-required obligations: monthly land lease payments to a Balinese land trust ($2,400/month), imported permaculture supplies ($600/quarter), and medical emergency access ($1,000 reserve minimum). These total approximately $4,200/quarter that cannot currently be met through Current-Sees.

The assessment team evaluates readiness criteria for Stage 2 to 3:
- 80%+ internal transactions using Current-Sees: measured at 72%. **Not met.** Gap: 8 percentage points, primarily in the Construction and Technology domains where external vendors require currency.
- Basic needs met through ecosystem resource flows: partially met. Housing, food, and community services are covered. Medical emergencies and external obligations are not.
- External transaction pathway established: **Not met.** No dedicated interface mechanism exists for converting ecosystem resources to accepted currency for external obligations.
- 75%+ participant confidence: measured at 68%. **Not met.** Gap: 7 percentage points, concentrated among participants with external financial obligations.

The assessment team drafts the transition assessment: **not ready for Stage 3**. Three of four readiness criteria are unmet. The report identifies specific gaps and recommends:
1. Establish an External Interface Circle dedicated to managing currency-required obligations on behalf of SHUR Bali participants
2. Create a currency bridge fund within the existing pool structure to cover essential external obligations during transition
3. Pilot Current-See primary in the Agriculture and Community domains (where external dependencies are lowest) while maintaining hybrid in Construction and Technology

Leilani presents the assessment at a SHUR Bali community review session. Naveen presents the positive indicators -- 72% Current-See usage is strong progress. Priya presents the gaps without framing them as permanent barriers. Discussion reveals that several participants assumed the transition would eliminate currency needs entirely rather than creating a managed interface. The community agrees that the External Interface Circle is a prerequisite for Stage 3 readiness.

Rather than waiting for another annual assessment, the community decides to act on the recommendations immediately and requests a follow-up assessment in 6 months. The agreement registry records the assessment, the community discussion, and the action plan.

Edge case: During the community review, Kai (a newer participant) argues that the 75% confidence threshold is paternalistic and that the 68% who support transition should not be held back by the cautious 22%. Priya responds that the readiness criteria exist to protect the 22% -- transition that leaves a fifth of participants unable to meet basic needs is structural harm, not progress. The facilitator notes that Kai's concern is heard but the threshold is part of the consented transition framework. Kai may propose amending the threshold through ACT if he believes it should change, but cannot override it for this assessment.

## Stress-Test Results

### 1. Capital Influx

A wealthy donor offers OmniOne $500,000 on the condition that the ecosystem accelerate its transition to Stage 3 within 12 months. The donation would fund the External Interface Circle, the currency bridge fund, and pilot programs. The access-economy-transition skill prevents conditional acceleration: transition pace is governed by readiness criteria, not funding availability. The donation is welcome through the resource-request and funding-pool-stewardship skills, but the condition is rejected. Money can fund the infrastructure that enables transition; it cannot substitute for the participant confidence, internal transaction patterns, and external dependency management that readiness criteria measure. The assessment team evaluates readiness independently of funding availability. If the infrastructure funded by the donation helps the ecosystem meet readiness criteria faster, the timeline naturally compresses -- but the criteria themselves do not change because money is available.

### 2. Emergency Crisis

The Indonesian rupiah loses 30% of its value in a currency crisis, making accepted-currency transactions within OmniOne dramatically more expensive. Several participants argue this is the moment to emergency-advance to Stage 3. The skill requires that a currency crisis trigger a readiness assessment, not automatic advancement. The emergency assessment (compressed to 14 days) evaluates whether the ecosystem's Current-See infrastructure can absorb the functions currently served by the destabilized currency. If the assessment shows readiness, a compressed pilot (minimum 90 days, not waived) tests the transition under crisis conditions. If the assessment shows the ecosystem is not ready, rushing to Stage 3 would compound the currency crisis with governance crisis. The skill protects the ecosystem from panic-driven transitions that sound urgent but lack infrastructure.

### 3. Leadership Charisma Capture

Rani, a visionary founder, delivers an inspiring speech at TH about the access economy as OmniOne's destiny and calls for immediate advancement to Stage 3 across the entire ecosystem. Her speech generates excitement and several circles begin informally operating at Stage 3 without formal assessment. The skill addresses this through two mechanisms. First, the mandatory readiness assessment: Rani's speech does not satisfy quantitative criteria. Enthusiasm is not participant confidence measured by structured survey; inspiration is not 80% Current-See transaction rates measured by commons monitoring. Second, the commons-monitoring skill detects informal stage advancement (circles whose resource flow patterns do not match their formal stage) and flags them for formal assessment. Informal transitions lack rollback protections and governance safeguards. The facilitator at the next ecosystem governance review ensures Rani's vision is honored as aspiration while the assessment process is honored as the pathway to get there.

### 4. High Conflict / Polarization

SHUR Bali is deeply divided about whether to advance from Stage 2 to Stage 3. The Agriculture circle (strongly in favor) argues that their domain is already operating at Stage 3 in practice. The Technology circle (strongly opposed) argues that their external vendor relationships make Stage 3 impossible. The conflict intensifies when the Agriculture circle accuses the Technology circle of protecting its members' currency income. At GAIA Level 4, a coach facilitates a third-solution exploration. The resulting proposal: domain-specific transition. The Agriculture circle formally advances to Stage 3 for agricultural resource flows, while the Technology circle remains at Stage 2 for technology procurement. A shared interface mechanism handles cross-domain transactions between circles at different stages. The pilot tests this domain-specific approach for 6 months. The coach ensures neither circle frames the other's position as ideological failure -- the Technology circle's external dependencies are structural realities, and the Agriculture circle's readiness is a genuine achievement.

### 5. Large-Scale Replication

OmniOne scales to 5,000 participants across 15 SHUR locations, each at different economic stages. SHUR Bali operates at Stage 3. SHUR Costa Rica operates at Stage 2. SHUR Portugal operates at Stage 1. The access-economy-transition skill accommodates this heterogeneity by design: each location's transition is governed by its own readiness assessment, pilot testing, and consent process. Cross-location transactions use the lower-stage defaults (currency for Stage 1 transactions, hybrid for Stage 2). The ecosystem-level transition trajectory is tracked by the OSC, which publishes an annual transition status report showing each location's stage, readiness trends, and pilot outcomes. Lessons learned from early-transitioning locations feed into assessment criteria refinements for later-transitioning locations. No location is pressured to match the pace of the most advanced location.

### 6. External Legal Pressure

Portuguese regulations require all economic exchanges within organizations to be denominated in euros and reported for tax purposes. This creates a structural barrier for SHUR Portugal's advancement beyond Stage 1. The skill accommodates this through the external dependency analysis: Portuguese legal requirements are a legitimate structural constraint, not a failure of readiness. The assessment team documents the legal barrier and recommends: maintain Stage 1 as the formal stage, but pilot Current-See coordination for non-monetary resource flows (time exchanges, expertise sharing, space access) that may not trigger the euro-denomination requirement. The legal constraint at SHUR Portugal does not affect SHUR Bali's transition to Stage 3. The UAF sovereignty principle holds: each location absorbs its own legal environment without propagating constraints across the ecosystem.

### 7. Sudden Exit of 30% of Participants

After 1,500 of 5,000 OmniOne members depart, several locations that were piloting Stage 3 transitions lose critical mass. The skill's response is structural. First, all active pilots trigger mandatory reassessment: do success criteria still make sense with the reduced participant base? Does the participant survey that supported the original assessment still represent current membership? Pilots where the departure drops the participant base below 50% of the original assessment's survey respondents are paused for reassessment. Second, rollback triggers are evaluated: if a pilot defined "membership drops below X" as a rollback trigger, the rollback activates automatically per the pre-consented conditions. Third, locations that were not yet piloting continue at their current stage -- the mass departure does not create pressure to accelerate or decelerate transition. The assessment process resumes on its regular cycle with the smaller membership base. Some locations may find that the departure of currency-economy-oriented participants actually improves their readiness metrics -- the assessment captures this honestly rather than treating departure as uniformly negative.
