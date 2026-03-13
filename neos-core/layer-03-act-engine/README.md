# Layer III: ACT Decision Engine

The ACT Decision Engine defines how proposals are created, debated, consented to, tested, and resolved through the Advice-Consent-Test process with GAIA 6-level escalation. It is the mechanism through which the ecosystem changes: every structural modification to agreements, processes, resources, or authority passes through this engine.

## Skills

| Skill | Description | Dependencies |
|-------|-------------|-------------|
| **proposal-creation** | Create and submit formal proposals with synergy check and routing | None |
| **act-advice-phase** | Gather and document input from all impacted parties | proposal-creation |
| **act-consent-phase** | Record positions, integrate objections, achieve consent or consensus | act-advice-phase, proposal-creation |
| **act-test-phase** | Implement changes reversibly with success criteria and review | act-consent-phase, proposal-creation |
| **consensus-check** | Utility skill for verifying group agreement in consent or consensus mode | proposal-creation |
| **proposal-resolution** | GAIA 6-level escalation for stalled proposals | All ACT phase skills, consensus-check |

## Skill Relationships

```
proposal-creation --> act-advice-phase --> act-consent-phase --> act-test-phase
                                                |
                                          consensus-check (utility)
                                                |
                                       proposal-resolution
                                       (GAIA 6-level escalation)
                                          |  |  |  |  |  |
                                         L1 L2 L3 L4 L5 L6
```

## The ACT Cycle

```
Proposal --> Synergy Check --> Advice --> Consent --> Test --> Agreement
                                  ^          |                    |
                                  |     (objections)              |
                                  +--- Integration Rounds         |
                                  |          |                    |
                                  |     (exhausted)               |
                                  |          v                    |
                                  |   GAIA Escalation             |
                                  |     (Levels 1-6)              |
                                  |          |                    |
                                  +----------+       (registers in)
                                                          v
                                                   Agreement Registry
```

## Interaction with Layer I (Agreement Layer)

- **ACT produces agreements.** Successful proposals become agreements registered through agreement-creation.
- **Agreements define ACT participants.** Who participates in a consent round is determined by the affected-parties list, derived from existing agreements.
- **Agreement amendments flow through ACT.** Modifying any agreement requires a proposal that passes through the ACT cycle.

## Key Design Decisions

- **Consent vs. consensus**: Two distinct modes with different structural rules. Consent is the default ("no reasoned objection"). Consensus is required for UAF/OSC-level decisions ("all actively agree").
- **GAIA escalation**: Six levels from in-circle consensus to value-based decision resolution. No level can be skipped without consent of all affected parties.
- **Maximum integration rounds**: 3 for normal urgency, 2 for emergency. After maximum rounds, proposals escalate rather than cycle indefinitely.
- **Auto-revert**: Test phase changes auto-revert if the review body does not convene. No decision becomes permanent by neglect.
- **Reversibility**: Every consented change is tested before permanent adoption. The bar for permanence is evidence, not momentum.

## Dependencies

Authority scopes referenced in this layer's skills are formally defined by the domain-mapping skill in Layer II (Authority & Role). ACT decisions serve as the mechanism for creating, assigning, and reviewing authority — every domain creation, role assignment, and domain review passes through an ACT process.

## GAIA 6-Level Model

1. **Consensus** — All agree within Master Plan scope
2. **Culture Code** — Circle-internal using chosen process
3. **Advice + Panel** — Synergy check plus expert panel input
4. **Coaching** — Finding third solutions between competing options
5. **Alignment Sense Making** — Check against policies, agreements, values
6. **Decision Resolution** — Value comparison chart with final determination
