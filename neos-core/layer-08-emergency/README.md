# Layer VIII: Emergency Handling

## Overview

Every governance system will face genuine crises -- natural disasters, funding collapses, infrastructure failures, external legal threats. The structural danger is never the crisis itself but what happens to authority during and after the crisis. Giorgio Agamben documented how the "state of exception" is the most dangerous power in any political system: the authority to suspend normal rules, exercised by those who benefit from the suspension, with no structural mechanism forcing a return to normal. Every authoritarian consolidation in modern history began with a "temporary" emergency that became permanent.

NEOS addresses this through a circuit breaker model inspired by electrical engineering and resilience design. Normal governance (Closed) transitions to emergency governance (Open) only when pre-defined, measurable criteria are crossed. Emergency governance operates within pre-consented authority boundaries with hard ceilings and auto-expiration timers. Recovery (Half-Open) is mandatory and cannot be skipped. Post-emergency review is structural, not optional. The result: an emergency governance framework that enables rapid response while making capture structurally impossible.

## The Circuit Breaker Model

```
                    Entry criteria
                    threshold crossed
                         |
                         v
    +--------+      +--------+      +-----------+
    |        | ---> |        | ---> |           |
    | CLOSED |      |  OPEN  |      | HALF-OPEN |
    | Normal |      | Emerg. |      | Recovery  |
    |        | <--- |        |      |           |
    +--------+      +--------+      +-----------+
         ^                               |
         |                               |
         +-------------------------------+
              Review complete +
              ratifications processed

    CLOSED: Normal ACT process. Emergency roles on standby.
    OPEN:   Compressed timelines. Pre-authorized roles active.
            Auto-reversion timer running. Decisions logged.
    HALF-OPEN: Normal governance restored. Authority ceased.
               Crisis decisions queued for ratification.
               Post-emergency review mandatory.

    PROHIBITED: Open -> Closed (cannot skip recovery)
    PROHIBITED: Half-Open -> Open (unless NEW criterion triggers)
```

## Agamben Resistance by Design

Carl Schmitt defined sovereignty as "who decides the exception." Agamben showed how this power, once granted, resists return. NEOS eliminates the Schmittian sovereign from emergency governance through five structural mechanisms:

1. **Criteria-based declaration**: No person decides whether an emergency exists. Pre-defined, measurable, consented-to criteria decide. The criteria are designed during calm conditions through normal ACT process.

2. **Pre-consented authority**: Emergency roles, scopes, ceilings, and timers are designed and consented to before any crisis. No one improvises power during fear.

3. **Irreducible constraints**: Four boundaries that no emergency authority can cross: no UAF amendment, no AZPO dissolution, no member expulsion, no criteria modification during emergency. These protect permanent governance architecture from temporary authority.

4. **Auto-reversion**: Every emergency has a hard end date. The timer starts at declaration and cannot be paused. Authority ceases immediately upon reversion. The Half-Open recovery state cannot be skipped.

5. **Mandatory independent review**: Every emergency is reviewed by members who did not hold emergency roles. Decisions are evaluated against scope, not outcomes. Non-occurrence triggers Layer VII safeguard escalation.

## Skill Flow

The five skills operate in sequence, each building on the previous:

```
 [1] emergency-criteria-design
      |
      | Defines WHAT constitutes an emergency
      | (entry thresholds, exit thresholds, max duration)
      v
 [2] pre-authorization-protocol
      |
      | Defines WHO acts and with WHAT authority
      | (roles, scopes, ceilings, auto-expiration)
      v
 [3] crisis-coordination
      |
      | Governs HOW decisions are made during crisis
      | (immediate / short-cycle / deferred timelines)
      v
 [4] emergency-reversion
      |
      | Manages the RETURN to normal governance
      | (authority cessation, ratification, recovery state)
      v
 [5] post-emergency-review
      |
      | Ensures ACCOUNTABILITY after every emergency
      | (independent review, scope evaluation, recommendations)
      v
     [Back to normal -- circuit breaker Closed]
```

## Skill Index

| # | Skill | Purpose | Dependencies |
|---|-------|---------|-------------|
| 1 | [emergency-criteria-design](emergency-criteria-design/SKILL.md) | Define objective, measurable emergency criteria with matching exit conditions | agreement-creation, act-consent-phase, safeguard-trigger-design |
| 2 | [pre-authorization-protocol](pre-authorization-protocol/SKILL.md) | Pre-authorize emergency roles with bounded authority, hard ceilings, and auto-expiration | emergency-criteria-design, role-assignment, authority-boundary-negotiation |
| 3 | [crisis-coordination](crisis-coordination/SKILL.md) | Operate compressed decision timelines during an active emergency | pre-authorization-protocol, act-advice-phase |
| 4 | [emergency-reversion](emergency-reversion/SKILL.md) | Return governance from emergency to normal through mandatory recovery state | crisis-coordination, emergency-criteria-design |
| 5 | [post-emergency-review](post-emergency-review/SKILL.md) | Mandatory retrospective by independent review body after every emergency | emergency-reversion, governance-health-audit |

## Design Principles

**Criteria over judgment.** Emergency declaration is a threshold crossing, not a leadership decision. No individual or body gains the power to decide what constitutes an emergency.

**Advance consent over improvised authority.** Every emergency role, scope, and ceiling is designed and consented to during calm conditions. Crisis response executes a pre-consented plan, not an improvised power structure.

**Minimum necessary authority.** Emergency roles receive the smallest scope required for effective crisis response. Hard ceilings are absolute. Authority cannot be expanded during a crisis without compressed ACT consent.

**Structural reversion over voluntary return.** Authority ceases automatically. The timer is structural, not discretionary. The recovery state is mandatory, not optional. Decisions auto-revert if not ratified.

**Independent accountability over self-assessment.** Post-emergency review excludes anyone who held emergency authority. Decisions are evaluated against scope, not outcomes. Good results do not validate scope violations.

## Relationship to Other Layers

- **Layer I (Agreement):** Emergency criteria and pre-authorizations are installed as agreements through the ACT process. The UAF is protected by irreducible constraints during emergencies.
- **Layer II (Authority):** Emergency roles are defined through the role-assignment and authority-boundary-negotiation skills. Pre-authorized authority scopes must be consistent with the ecosystem's authority framework.
- **Layer III (ACT Engine):** Emergency criteria installation, pre-authorization consent, and post-emergency ratification all use the ACT process. Crisis-coordination defines compressed ACT timelines for emergency conditions.
- **Layer IV (Economic):** Resource Coordinator ceilings interact with economic agreements. Emergency spending is tracked against the ecosystem's financial structure.
- **Layer VI (Conflict):** Post-emergency disputes that cannot be resolved through review recommendations may escalate to GAIA conflict resolution processes.
- **Layer VII (Safeguard):** Layer VII detects when emergency authority is being abused (emergency capture triggers). Layer VIII defines how emergency authority operates. Post-emergency review triggers a Layer VII governance health audit. Non-occurrence of post-emergency review triggers a Layer VII safeguard.
- **Layer IX (Memory):** Crisis Operations Logs, Reversion Records, and Post-Emergency Review Reports are permanent governance records maintained by the memory layer.

## Cross-Layer References

Emergency criteria are registered per `emergency-criteria-design/assets/emergency-criteria-template.yaml`. Starter criteria for new ecosystems are in `emergency-criteria-design/assets/starter-criteria.yaml`. Pre-authorized roles are registered per `pre-authorization-protocol/assets/pre-authorization-template.yaml`. Irreducible constraints are defined in `pre-authorization-protocol/assets/irreducible-constraints.yaml`. Crisis decision logs follow `crisis-coordination/assets/crisis-operations-log-template.yaml`. Compressed timelines are defined in `crisis-coordination/assets/compressed-act-timelines.yaml`. Circuit breaker states are formally defined in `emergency-reversion/assets/circuit-breaker-states.yaml`. Post-emergency review reports follow `post-emergency-review/assets/post-emergency-review-template.yaml`. The review checklist is in `post-emergency-review/assets/review-checklist.yaml`.
