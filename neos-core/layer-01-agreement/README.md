# Layer I: Agreement Layer

The Agreement Layer defines how binding commitments are created, modified, reviewed, and tracked within the ecosystem. It is the governance bedrock: without explicit, traceable agreements, all other coordination devolves into informal authority.

## Skills

| Skill | Description | Dependencies |
|-------|-------------|-------------|
| **agreement-creation** | Create new binding agreements through structured, consent-based process | None |
| **universal-agreement-field** | The root agreement all participants consent to upon entry | agreement-creation |
| **agreement-amendment** | Modify existing agreements through proper ACT process | agreement-creation, act-advice-phase, act-consent-phase, act-test-phase |
| **agreement-review** | Periodic review cycle — renew, revise, or sunset | agreement-creation, agreement-amendment, agreement-registry |
| **agreement-registry** | Single source of truth for all active agreements | agreement-creation, agreement-amendment, agreement-review |

## Skill Relationships

```
universal-agreement-field (root agreement)
        |
        | (created via)
        v
agreement-creation -----> agreement-registry <----- agreement-review
        ^                        ^                        |
        |                        |                        | (triggers)
        |                   (writes to)                   v
        |                        |                 agreement-amendment
        +------------------------+---- (also writes to registry)
```

## Interaction with Layer III (ACT Decision Engine)

Agreements and decisions are co-dependent:
- **Agreements are created through ACT decisions.** Every agreement passes through the ACT cycle (Advice, Consent, Test) before it becomes binding.
- **ACT decisions produce agreements.** The output of a successful ACT cycle is a registered agreement.
- **Agreements define who participates in ACT.** The affected-parties list for any ACT process is determined by existing agreements.

## Key Design Decisions

- **Consent vs. consensus**: Standard agreements use consent mode ("no reasoned objection"). UAF amendments and ecosystem-level decisions use consensus mode ("all actively agree").
- **Expiry by default**: Every agreement has a mandatory review date. No agreement is permanent without periodic revalidation.
- **Registry as single source of truth**: If it is not in the registry, it is not an agreement. Informal commitments have no standing.
- **Hierarchy with override rule**: Universal, Ecosystem, Access, Stewardship, AZPO Agreement Field, Culture Code, Personal. No lower-level agreement may contradict a higher-level one.

## Dependencies

Authority scopes referenced in this layer's skills are formally defined by the domain-mapping skill in Layer II (Authority & Role). When this layer's skills reference "authorized participant" or "authorized body," the formal definition of that authority exists in the domain contract created through the domain-mapping skill and the role-assignment skill.
