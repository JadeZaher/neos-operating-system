# Specification: Emergency Handling (Layer VIII)

## Track ID
`emergency_handling_20260302`

## Overview

This track builds the five skills of **Layer VIII: Emergency Handling**. Emergencies require faster decisions with fewer consultation rounds, which means temporary authority expansion. The central design challenge is Agamben's State of Exception: emergency powers, once granted, tend to become permanent. Every mechanism in this layer is engineered to make permanence structurally impossible.

The layer draws on Agamben's political philosophy (emergency authority is the primary vector through which governance systems lose their democratic character), sunset clause research from COVID-era governance studies (auto-expire is more effective than active-end because inertia favors continuation), and the circuit breaker pattern from distributed systems (Closed/Normal, Open/Crisis, Half-Open/Recovery, with transitions governed by measurable criteria rather than human judgment).

This track depends on Layer II (Authority & Role) for defining authority expansion scope, Layer VII (Safeguard & Capture Detection) for monitoring whether emergency authority is being abused, and Layer I (Agreement) for the emergency protocol being itself an agreement that can be reviewed and amended.

## Background

### Agamben's Warning and the Engineering Response

Giorgio Agamben demonstrated that the "state of exception" -- governance operating outside its normal rules -- is the mechanism through which democratic systems most commonly degrade into authoritarian ones. The exception starts as temporary and bounded but persists through a combination of genuine ongoing risk, institutional inertia, and the psychological comfort of centralized decision-making. NEOS treats this not as a political risk to be managed culturally but as a structural failure mode to be engineered against. Every emergency mechanism in this layer has auto-reversion built in at the architectural level.

### Circuit Breaker Pattern

Borrowed from distributed systems engineering, the circuit breaker provides the state machine for emergency governance:

- **Closed (Normal):** Standard governance processes operate. ACT cycle runs at normal cadence. Authority is distributed according to normal role definitions.
- **Open (Crisis):** Emergency criteria have been met. Pre-authorized emergency roles activate. Decision timelines compress. Authority expands within pre-defined scopes. Auto-reversion timer starts immediately upon entry.
- **Half-Open (Recovery):** The acute crisis has passed. Governance is transitioning back to normal. Expanded authority is being wound down. Mandatory post-emergency review is scheduled. This state cannot be skipped.

State transitions are governed by measurable criteria, not human judgment. A human can declare that criteria are met, but the criteria themselves are pre-defined and objective.

### Sunset Clause Research

COVID-era governance research demonstrated that auto-expiring emergency provisions are significantly more likely to actually expire than provisions that require active revocation. The reason is institutional inertia: it takes effort to extend emergency provisions (good), but it also takes effort to revoke them (bad, because the default becomes continuation). NEOS inverts the default: emergency authority expires automatically unless actively renewed through a constrained process.

### Cooperative Continuity-of-Operations

Cooperative governance models provide practical precedent for emergency operations: essential functions must be pre-identified, emergency authority must be pre-distributed (not concentrated on whoever happens to be available), and polycentric emergency response (multiple nodes can act independently) is more resilient than centralized command.

---

## Functional Requirements

### FR-1: Emergency Criteria Design (`emergency-criteria-design`)

**Description:** Enable the ecosystem to define objective, measurable criteria that constitute an emergency warranting governance mode change. Criteria must be specific enough to prevent subjective invocation while flexible enough to cover genuine emergencies. This skill produces the trigger conditions for entering emergency mode.

**Acceptance Criteria:**
- AC-1.1: The skill defines the anatomy of an emergency criterion: the observable condition, the measurement method, the threshold that constitutes emergency, the verification process, and the expiry condition (when does the emergency end by the same measurement?).
- AC-1.2: The step-by-step process walks through designing emergency criteria using the ACT process (criteria are agreements that bind the ecosystem to specific triggers).
- AC-1.3: The skill provides a starter set of emergency criteria categories: physical safety threat, resource crisis (funding loss exceeding X% within Y timeframe), governance incapacity (decision-making bodies unable to achieve quorum for Z consecutive sessions), external legal threat requiring immediate response, and infrastructure failure.
- AC-1.4: Each criterion has a corresponding exit condition that is equally measurable -- the emergency ends when the condition reverses, not when someone decides it has ended.
- AC-1.5: The output artifact is an Emergency Criteria Registry entry with the criterion definition, installation date, and activation history.
- AC-1.6: The authority boundary check ensures criteria cannot be designed so broadly that normal disagreements qualify as emergencies.
- AC-1.7: The capture resistance check addresses Agamben's trap: vague crisis definitions that allow emergency invocation at leadership discretion.
- AC-1.8: An OmniOne walkthrough demonstrates the OSC designing emergency criteria for the Bali SHUR, including a physical safety criterion (natural disaster) and a resource crisis criterion (loss of primary funding).
- AC-1.9: All 7 stress-test scenarios documented.

**Priority:** P0 -- Must exist before any emergency can be declared.

### FR-2: Pre-Authorization Protocol (`pre-authorization-protocol`)

**Description:** Enable the ecosystem to define emergency roles with pre-authorized authority scopes and automatic expiration before any emergency occurs. Pre-authorization ensures that emergency response is distributed across defined roles rather than concentrated on whoever seizes initiative during crisis.

**Acceptance Criteria:**
- AC-2.1: The skill defines the anatomy of a pre-authorized emergency role: the role title, the activating criterion (from emergency-criteria-design), the authority scope (what the role can decide unilaterally during emergency), the authority ceiling (what the role cannot decide even during emergency), the maximum duration, and the accountability requirements during and after the emergency.
- AC-2.2: The step-by-step process walks through defining emergency roles through the ACT process (pre-authorization is a form of advance consent -- the ecosystem consents in advance to specific authority expansions under specific conditions).
- AC-2.3: The skill defines the principle of minimum necessary authority: each emergency role receives only the authority required for its specific function, not general authority over the affected domain.
- AC-2.4: The output artifact is a Pre-Authorization Registry entry with the role definition, authorized scope, ceiling, duration, and the consent record that established it.
- AC-2.5: The authority boundary check specifies irreducible constraints: no emergency role can amend the UAF, dissolve an ETHOS, expel a member, or modify the emergency criteria themselves.
- AC-2.6: The capture resistance check addresses: emergency authority concentration (no single role receives all emergency authority -- distribute across multiple roles), authority scope creep during crisis (the ceiling is enforced regardless of circumstances), and the "just in case" trap (maintaining emergency infrastructure beyond its defined duration).
- AC-2.7: An OmniOne walkthrough demonstrates the AE defining pre-authorized emergency roles for a SHUR facility crisis: a Safety Coordinator (authority: evacuation decisions, temporary facility closure), a Resource Coordinator (authority: emergency fund release up to defined cap), and a Communications Coordinator (authority: external communications within defined parameters).
- AC-2.8: All 7 stress-test scenarios documented.

**Priority:** P0 -- Must exist before any emergency role can activate.

### FR-3: Crisis Coordination (`crisis-coordination`)

**Description:** Define the operational governance process during an active emergency. This skill describes how decisions are made faster and under greater constraints during the Open (Crisis) state of the circuit breaker. It is the runtime execution skill -- what happens between emergency declaration and emergency reversion.

**Acceptance Criteria:**
- AC-3.1: The skill defines the compressed decision timeline for each emergency authority scope: immediate decisions (Safety Coordinator acts, reports within 24 hours), short-cycle decisions (Resource Coordinator proposes, abbreviated 24-hour advice window, emergency consent round), and deferred decisions (anything outside pre-authorized scope waits for recovery or uses normal ACT process).
- AC-3.2: The step-by-step process maps the circuit breaker Open state: verify emergency criteria are met, activate pre-authorized roles, start auto-reversion timer, compress ACT timelines for in-scope decisions, maintain decision logging (even compressed logs), restrict authority to pre-authorized ceilings, monitor for exit criteria being met.
- AC-3.3: The output artifact is a Crisis Operations Log recording all decisions made under emergency authority, who made them, under what authorization, and the evidence that the decision was within scope.
- AC-3.4: The authority boundary check specifies that crisis coordination cannot override the irreducible constraints from pre-authorization (no UAF amendment, no expulsion, no criteria modification). If a situation requires authority beyond the pre-authorized scope, the skill defines the emergency-expansion request process (which requires abbreviated consent from a defined body, not unilateral expansion).
- AC-3.5: The capture resistance check addresses: crisis decision-making becoming normalized (the compressed timeline is structurally uncomfortable by design -- it should feel different from normal governance), emergency decisions becoming precedent (crisis decisions do not set precedent for normal operations -- they are explicitly tagged as emergency context).
- AC-3.6: An OmniOne walkthrough demonstrates crisis coordination during a Bali flooding event: Safety Coordinator orders temporary evacuation (within authority), Resource Coordinator releases emergency funds for temporary housing (within authority, within cap), a question arises about whether to terminate a vendor contract (outside pre-authorized scope -- deferred to recovery phase), Communications Coordinator issues a public statement (within parameters). Auto-reversion timer is running. Edge case: the flooding persists beyond the initial emergency duration -- the skill defines the extension process (abbreviated consent, not automatic extension).
- AC-3.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Operational core of emergency handling.

### FR-4: Emergency Reversion (`emergency-reversion`)

**Description:** Manage the transition from emergency mode back to normal governance. This skill defines the Half-Open (Recovery) state of the circuit breaker: winding down emergency authority, restoring normal decision timelines, transitioning crisis decisions to permanent resolution or reversal, and ensuring the recovery state cannot be skipped.

**Acceptance Criteria:**
- AC-4.1: The skill defines the reversion trigger: emergency exit criteria are met (measurable condition reverses), OR the auto-reversion timer expires, OR the ecosystem consents to early reversion.
- AC-4.2: The step-by-step process maps the Half-Open state: deactivate emergency roles (authority expansion ceases immediately upon entering Recovery), restore normal ACT timelines, review all crisis decisions (each must be ratified through normal process, modified, or reversed), transfer ongoing crisis needs to normal governance structures, schedule mandatory post-emergency review.
- AC-4.3: The output artifact is a Reversion Record documenting: the reversion trigger, the date and time authority was restored, the list of crisis decisions pending normal ratification, and the post-emergency review date.
- AC-4.4: The authority boundary check specifies that no emergency role retains any expanded authority after entering Recovery. The role holders return to their normal authority scope immediately. If they believe continued authority is needed, they must propose it through normal ACT process.
- AC-4.5: The failure containment logic defines what happens when: reversion is resisted (any ecosystem member can invoke the auto-reversion timer -- if it has expired, emergency authority ceases regardless of leadership preference), crisis decisions cannot be ratified (they automatically revert to pre-crisis state unless actively ratified within 30 days of recovery start), the post-emergency review is not scheduled (automatic escalation to ecosystem-level notice).
- AC-4.6: The capture resistance check addresses Agamben's core warning: the transition from exception back to normality is where capture most commonly occurs. The skill makes recovery a mandatory state (cannot transition directly from Crisis to Normal), makes authority restoration automatic (not discretionary), and makes post-emergency review non-optional.
- AC-4.7: An OmniOne walkthrough demonstrates reversion after the Bali flooding event: water recedes (exit criterion met), emergency roles deactivate, Recovery state begins. Crisis decisions reviewed: evacuation decision ratified (it was correct), emergency fund expenditure reviewed and approved, the deferred vendor contract question now enters normal ACT process. Post-emergency review scheduled for 2 weeks out. Edge case: one emergency role holder argues that continued authority is needed because "aftershocks might occur." The skill's structure prevents this -- authority has already ceased, and a new emergency would require meeting the criteria again.
- AC-4.8: All 7 stress-test scenarios documented.

**Priority:** P0 -- Without reversion, emergency handling is incomplete and dangerous.

### FR-5: Post-Emergency Review (`post-emergency-review`)

**Description:** Run the mandatory retrospective on every use of emergency authority. This skill produces the learning record that improves future emergency handling and provides accountability for emergency decisions. The review cannot be skipped, deferred indefinitely, or conducted by the body that held emergency authority.

**Acceptance Criteria:**
- AC-5.1: The skill defines review scope: every decision made under emergency authority, every pre-authorized role activation, the timeliness and appropriateness of emergency declaration and reversion, the adequacy of pre-authorized scopes, and whether any irreducible constraints were tested or breached.
- AC-5.2: The step-by-step process specifies: convene review body (must include participants who were affected by emergency decisions but did not hold emergency authority), review the Crisis Operations Log entry by entry, evaluate each decision against its authorization scope, evaluate overall emergency response effectiveness, identify criteria that need refinement, identify pre-authorization gaps or excesses, produce Post-Emergency Review Report, submit recommendations through normal ACT process.
- AC-5.3: The review body cannot include anyone who held a pre-authorized emergency role during the emergency being reviewed. This structural separation prevents self-assessment.
- AC-5.4: The output artifact is a Post-Emergency Review Report documenting: emergency timeline, decision-by-decision review, authority compliance assessment, criteria adequacy assessment, recommendations for criteria/pre-authorization modification, and a public summary accessible to all ecosystem members.
- AC-5.5: The authority boundary check specifies that the review produces a report and recommendations, not directives. Recommendations are implemented through normal ACT process. The review body has no authority to punish, reward, or override normal governance based on its findings.
- AC-5.6: The capture resistance check addresses: review capture by emergency role holders (they are excluded from the review body), review suppression (the review is mandatory and its non-occurrence triggers an automatic safeguard from Layer VII), and review weaponization (the review evaluates structural decisions against defined scopes, not personal performance).
- AC-5.7: An OmniOne walkthrough demonstrates the post-emergency review of the Bali flooding response, conducted by TH members who did not hold emergency roles, reviewing the Crisis Operations Log, finding that the Resource Coordinator exceeded their spending cap by 12% (recommendation: increase the cap or add an abbreviated consent requirement for overages), and that the emergency criteria worked well but the exit criteria were met 2 days before reversion actually occurred (recommendation: add a mandatory exit-check cadence of 48 hours during crisis).
- AC-5.8: All 7 stress-test scenarios documented.

**Priority:** P0 -- The review is what prevents emergency capture from compounding across episodes.

---

## Non-Functional Requirements

### NFR-1: Modularity

Each skill must function independently. A participant reading crisis-coordination should be able to run governance during an emergency without loading emergency-reversion. Skills reference each other by name but do not require co-loading.

### NFR-2: Line Limit

Each SKILL.md must be under 500 lines. Circuit breaker state diagrams, emergency criteria examples, and pre-authorization templates go in `assets/`.

### NFR-3: Portability

All skills are NEOS-generic at the structural level. OmniOne-specific configurations (specific emergency criteria thresholds, specific role names like OSC/AE/TH, specific SHUR scenarios) appear as clearly marked examples that another ecosystem can replace.

### NFR-4: Auto-Reversion as Architectural Default

Every emergency authority expansion must have an auto-reversion mechanism. The default must be "authority expires" not "authority continues." Extension requires active consent, not passive continuation.

### NFR-5: Mandatory Recovery State

The circuit breaker Half-Open (Recovery) state cannot be skipped. Governance cannot transition directly from Crisis to Normal. This non-functional requirement ensures that every emergency use is followed by a structured wind-down.

### NFR-6: No Hidden Authority

Emergency roles, their scopes, and their ceilings are defined in advance through ACT process and published to all ecosystem members. No emergency authority exists that was not pre-consented to.

### NFR-7: Validation

Every SKILL.md must pass automated validation via `scripts/validate_skill.py`.

---

## User Stories

### US-1: Ecosystem Architect Designs Emergency Criteria
**As** an ecosystem architect setting up NEOS for a new community,
**I want** to define objective, measurable emergency criteria with matching exit conditions,
**So that** emergency mode can only be entered and exited based on verifiable conditions, not subjective judgment.

**Given** the architect has identified the community's primary risk categories,
**When** they follow the emergency-criteria-design skill process through ACT,
**Then** an Emergency Criteria Registry is established with specific, measurable trigger and exit conditions for each risk category.

### US-2: AI Agent Activates Emergency Protocol
**As** an AI agent assisting during a crisis event,
**I want** to determine whether emergency criteria are met and which pre-authorized roles should activate,
**So that** I can guide participants through the correct emergency response process.

**Given** an event has occurred that may constitute an emergency,
**When** the AI agent evaluates the event against the Emergency Criteria Registry,
**Then** it can confirm whether criteria are met, identify the pre-authorized roles that activate, and outline the compressed decision timeline.

### US-3: Emergency Role Holder Makes Crisis Decision
**As** a Safety Coordinator activated during a facility crisis,
**I want** clear boundaries on what I can and cannot decide unilaterally,
**So that** I act decisively within my scope without overstepping.

**Given** the emergency has been declared and pre-authorized roles are active,
**When** the Safety Coordinator faces a decision,
**Then** they can check their pre-authorization definition for authority scope, ceiling, and duration to determine whether the decision is within their unilateral authority or must be deferred.

### US-4: Ecosystem Reverts from Emergency Mode
**As** an ecosystem transitioning out of a crisis,
**I want** a structured reversion process that automatically restores normal authority,
**So that** emergency powers do not persist beyond the crisis.

**Given** the emergency exit criteria have been met or the auto-reversion timer has expired,
**When** the ecosystem follows the emergency-reversion skill,
**Then** emergency authority ceases immediately, normal timelines are restored, crisis decisions are queued for ratification, and a post-emergency review is scheduled.

### US-5: Review Body Conducts Post-Emergency Review
**As** a group of affected participants reviewing an emergency response,
**I want** to evaluate every emergency decision against its authorization scope,
**So that** the ecosystem learns from the emergency and improves its preparedness.

**Given** an emergency has concluded and recovery is complete,
**When** the review body follows the post-emergency-review skill,
**Then** a Post-Emergency Review Report is produced with decision-by-decision analysis, authority compliance assessment, and actionable recommendations submitted through normal ACT process.

### US-6: Participant Challenges Emergency Duration
**As** a TH member who believes the emergency has passed but emergency authority is still active,
**I want** to invoke the auto-reversion mechanism,
**So that** emergency authority cannot persist beyond the defined exit criteria.

**Given** the participant observes that emergency exit criteria appear to be met,
**When** they invoke the exit-criteria check defined in the emergency-criteria-design skill,
**Then** the criteria are evaluated against current conditions, and if met, reversion begins regardless of whether emergency role holders agree.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-08-emergency/
    README.md
    emergency-criteria-design/
      SKILL.md
      assets/
        emergency-criteria-template.yaml
        starter-criteria.yaml
      references/
      scripts/
    pre-authorization-protocol/
      SKILL.md
      assets/
        pre-authorization-template.yaml
        irreducible-constraints.yaml
      references/
      scripts/
    crisis-coordination/
      SKILL.md
      assets/
        crisis-operations-log-template.yaml
        compressed-act-timelines.yaml
      references/
      scripts/
    emergency-reversion/
      SKILL.md
      assets/
        reversion-record-template.yaml
        circuit-breaker-states.yaml
      references/
      scripts/
    post-emergency-review/
      SKILL.md
      assets/
        post-emergency-review-template.yaml
        review-checklist.yaml
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name
description: "..."
layer: 8
version: 0.1.0
depends_on: []
---
```

### Cross-Layer Dependencies

Layer VIII skills reference but do not require:
- **Layer I (Agreement):** Emergency criteria and pre-authorizations are agreements established through the agreement creation process.
- **Layer II (Authority):** Emergency roles are defined through authority structures. Pre-authorization extends normal authority scope temporarily.
- **Layer III (ACT Engine):** Emergency criteria installation uses ACT process. Crisis coordination compresses ACT timelines.
- **Layer VII (Safeguard):** Safeguard triggers monitor for emergency capture (repeated invocation, scope creep, missing post-emergency reviews). Layer VII is the watchdog for Layer VIII.
- **Layer IX (Memory):** Crisis Operations Logs and Post-Emergency Review Reports become part of the governance memory for precedent and learning.

### Circuit Breaker State Machine

The circuit breaker state machine is documented in `assets/circuit-breaker-states.yaml` as a reference artifact. The three states (Closed/Normal, Open/Crisis, Half-Open/Recovery) and their transition criteria provide the conceptual backbone for the layer. Each skill maps to one or more state transitions:
- emergency-criteria-design: defines Closed-to-Open transition criteria
- pre-authorization-protocol: defines what activates at the Open transition
- crisis-coordination: defines operations during Open state
- emergency-reversion: defines Open-to-Half-Open and Half-Open-to-Closed transitions
- post-emergency-review: operates during Half-Open state and must complete before Closed is fully restored

---

## Out of Scope

- **Physical emergency response** -- NEOS handles governance during emergencies, not emergency operations (fire suppression, medical response, evacuation logistics).
- **Insurance, legal liability, or financial risk management** -- These are operational concerns, not governance skills.
- **Ongoing risk assessment** -- Layer VII handles continuous monitoring. This track handles the response when monitoring identifies a crisis.
- **Conflict resolution during emergencies** -- If interpersonal conflicts arise during crisis, they are deferred to Layer VI (Conflict & Repair) during recovery.
- **Software implementation** -- No automated circuit breakers, timers, or monitoring dashboards. The skills define processes for human and AI agent execution.

---

## Open Questions

1. **Auto-reversion timer duration**: What is the default maximum duration for emergency authority before auto-reversion? The spec recommends this be configurable per emergency criterion, with a hard maximum cap (e.g., 90 days) that cannot be exceeded without a full ecosystem-level ACT process. But what should the hard maximum be?

2. **Emergency extension limits**: Can an emergency be extended, and if so, how many times? Recommendation: maximum 1 extension of up to 50% of original duration, requiring abbreviated consent of a body that includes non-role-holders.

3. **Overlapping emergencies**: What happens when a new emergency criterion is met while an existing emergency is active? Recommendation: each emergency activates its own pre-authorized roles independently. If role conflicts arise, the crisis-coordination skill defines a priority order based on physical safety first, then resource preservation, then governance continuity.

4. **Emergency during emergency review**: What happens if a new emergency occurs during the post-emergency review of a previous one? The review is paused (not cancelled) and resumes during the next recovery period. The new emergency's review scope includes the impact on the interrupted review.
