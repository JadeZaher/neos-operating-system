# Layer IV: Economic Coordination

Layer IV governs how resources flow through the ecosystem without conflating economic contribution with governance authority. Every economic action in NEOS is an agreement. Every resource allocation is a decision. Every funding pool has scoped authority. This layer builds on agreements (Layer I), authority and roles (Layer II), and the ACT decision engine (Layer III) to create economic governance that is transparent, participatory, and structurally resistant to capture.

## Design Philosophy

Capital is the most common vector for governance capture. In traditional organizations, whoever controls the money controls the decisions. In token-governed DAOs, wealth equals voting power. Layer IV exists to prevent this failure mode by structurally separating economic contribution from governance authority. Financial contribution creates no additional decision-making weight. Current-Sees are distributed equally (111 per person) regardless of economic contribution level.

The layer draws on three theoretical foundations:
- **Elinor Ostrom's 8 Principles for Commons Governance** -- community monitoring, graduated sanctions, nested enterprises
- **Porto Alegre Participatory Budgeting** -- structured assembly processes for collective resource allocation
- **Commons-Based Peer Production (Benkler)** -- contribution tracked without commodification

## Skill Index

| Skill | Description | Key Dependencies |
|-------|-------------|-----------------|
| [resource-request](resource-request/SKILL.md) | Request resources from funding pools through ACT process | agreement-creation, act-consent-phase, domain-mapping |
| [funding-pool-stewardship](funding-pool-stewardship/SKILL.md) | Create and govern funding pools as living agreements | agreement-creation, role-assignment, agreement-review |
| [participatory-allocation](participatory-allocation/SKILL.md) | Run consent-based participatory budgeting assemblies | resource-request, funding-pool-stewardship, act-consent-phase, consensus-check |
| [commons-monitoring](commons-monitoring/SKILL.md) | Track resource flows and trigger graduated community responses | funding-pool-stewardship, domain-mapping |
| [access-economy-transition](access-economy-transition/SKILL.md) | Manage staged transition from currency to access economy | resource-request, funding-pool-stewardship, commons-monitoring, act-consent-phase |

## Skill Flow

```
resource-request ─────────────┐
       │                      │
       v                      v
funding-pool-stewardship ──> participatory-allocation
       │                      │
       v                      v
commons-monitoring <──────────┘
       │
       v
access-economy-transition
```

Resources enter through **resource-request**. Pools are governed by **funding-pool-stewardship**. Collective allocation happens through **participatory-allocation**. Flows are tracked by **commons-monitoring**. Long-range economic evolution is managed by **access-economy-transition**.

## Ostrom Principles Mapping

| Ostrom Principle | Layer IV Implementation |
|------------------|----------------------|
| 1. Clearly defined boundaries | Every funding pool has explicit domain boundaries, eligible participants, and resource scope defined in its governance agreement |
| 2. Congruence with local conditions | Pool governance rules are configured per circle/ETHOS; thresholds, inflow sources, and outflow rules match local context |
| 3. Collective-choice arrangements | Participatory allocation assemblies ensure those affected by resource rules participate in making them |
| 4. Monitoring by community members | Commons monitoring is performed by rotating community members, not external auditors or algorithms |
| 5. Graduated sanctions | Commons monitoring triggers a 4-level graduated response: notification, review, restriction, investigation |
| 6. Accessible conflict resolution | Resource disputes route through GAIA escalation levels; third-solution rounds in allocation assemblies |
| 7. Recognition of self-governance | External legal requirements are absorbed locally; no external authority overrides pool governance |
| 8. Nested enterprises | Pools operate at circle, ETHOS, and ecosystem levels with consistent governance at each scale |

## Cross-Layer References

**Layer I (Agreement)**
- `agreement-creation` -- Every funding pool is an agreement; pool creation invokes this skill
- `agreement-review` -- Pool governance agreements have mandatory review cycles

**Layer II (Authority & Role)**
- `role-assignment` -- Pool stewards, monitors, facilitators, and assessment team members are assigned through this skill
- `domain-mapping` -- Resource requests must fall within the requester's domain; pool boundaries align with domain boundaries

**Layer III (ACT Decision Engine)**
- `act-consent-phase` -- Resource requests, pool creation, allocation decisions, and transition proposals all use consent-based decision-making
- `act-advice-phase` -- Every economic proposal passes through advice before consent
- `consensus-check` -- Ecosystem-level economic decisions (OSC, Master Plan) use consensus

**Layer VII (Safeguard) -- Deferred**
- Systemic capture detection at the ecosystem level will integrate with commons-monitoring data when Layer VII is built

## OmniOne Economic Context

OmniOne uses **Current-Sees** as influence currencies distributed equally (111 per person). Types include NEXUS Alpha, TH, AE, OSC, GEV, Mission-Metrics, Energy, Reputation, Contribution, and Time Bank. The **H.A.R.T.** (Holistic Allocation of Resources and Treasuries) system governs resource distribution across pools. OmniOne's long-term trajectory moves through four stages: currency-dependent, hybrid, Current-See primary, and access economy.

## Asset Templates

| Template | Location | Purpose |
|----------|----------|---------|
| resource-request-template.yaml | resource-request/assets/ | Individual resource request document |
| pool-governance-template.yaml | funding-pool-stewardship/assets/ | Funding pool governance agreement |
| allocation-record-template.yaml | participatory-allocation/assets/ | Participatory allocation assembly record |
| commons-health-report-template.yaml | commons-monitoring/assets/ | Quarterly commons health report |
| transition-assessment-template.yaml | access-economy-transition/assets/ | Economic stage transition assessment |
