# Layer V -- Inter-Unit Coordination

## Purpose

Layer V governs how autonomous units (AZPOs) coordinate with each other without requiring centralized mediation or hub-and-spoke authority. While Layers I through IV govern how things work *within* an AZPO or within the ecosystem as a single entity, Layer V governs the relationships *between* autonomous units that each have their own agreements, authority structures, decision processes, and resource pools.

This is the hardest governance problem in any non-sovereign system. Without a central arbiter, cross-unit disputes can escalate indefinitely or result in fragmentation. Layer V provides enough structure for productive coordination while respecting the autonomy that makes AZPOs meaningful.

**The "No Sultan" Principle:** The Ottoman millet system allowed communities internal autonomy while sharing a common framework -- but it required a central authority (the Sultan) to resolve inter-community disputes. NEOS explicitly rejects this. Layer V provides shared coordination protocols without any apex authority. All coordination is lateral. All resolution is mutual. No body can impose outcomes on an AZPO.

## Skills

| Skill | Description | Priority |
|-------|-------------|----------|
| [cross-azpo-request](cross-azpo-request/) | Initiate and track requests across AZPO boundaries through dual-consent routing | P0 (anchor) |
| [shared-resource-stewardship](shared-resource-stewardship/) | Govern jointly-held resources with rotating stewardship and equitable access | P0 |
| [federation-agreement](federation-agreement/) | Draft, negotiate, and ratify bilateral/multilateral inter-AZPO agreements | P1 |
| [inter-unit-liaison](inter-unit-liaison/) | Maintain cross-AZPO coordination through designated roles with mandate boundaries | P1 |
| [polycentric-conflict-navigation](polycentric-conflict-navigation/) | Resolve structural disputes through three-tier lateral resolution | P1 (capstone) |

### Skill Relationships

```
cross-azpo-request (anchor)
    |
    +-- shared-resource-stewardship (uses request format for proposals)
    |
    +-- federation-agreement (uses request format for initiation)
    |       |
    |       +-- inter-unit-liaison (operates within federation framework)
    |
    +-- polycentric-conflict-navigation (capstone -- resolves disputes from all above)
```

Each skill builds on the patterns established by earlier skills in the build order. The cross-azpo-request skill defines the fundamental interaction shape; all other skills reference its dual-consent routing.

## Theoretical Foundations

**Ostrom's Polycentric Governance.** Multiple governing authorities at different scales, each with defined scope, operating independently but coordinating through shared protocols. The key insight: governance does not require a single center -- it requires clear boundaries, shared protocols, and accessible dispute resolution.

**Ottoman Millet System (Analogy with Critical Modification).** Each community governs its internal affairs while sharing a coordination framework. NEOS borrows the structural pattern (internal autonomy plus shared coordination protocols) but explicitly rejects the millet system's central authority. There is no apex sovereign in NEOS.

**Holochain Agent-Centric Architecture.** Each agent maintains a sovereign source chain while participating in shared protocols. Sovereign agents coordinating through shared protocols without a central server maps directly to NEOS's AZPO coordination model.

**Federated Governance Models.** Swiss cantons, EU subsidiarity, ActivityPub, Matrix protocol. Key structural elements: bilateral/multilateral agreements between autonomous units, shared interoperability standards, and graduated engagement tiers.

## Graduated Engagement Tiers

Inter-AZPO relationships operate across four engagement levels:

| Tier | Description | Commitments |
|------|-------------|-------------|
| **Observe** | Mutual acknowledgment, no commitments | None -- AZPOs recognize each other's existence |
| **Cooperate** | Case-by-case collaboration through requests | Respond to requests, designate inbound contact |
| **Federate** | Formal agreement with shared protocols | Maintain liaisons, honor protocols, regular reporting |
| **Integrate** | Deep structural integration | Shared governance bodies, pooled resources, joint decisions |

New AZPO relationships default to "observe." Tier transitions require federation agreement amendment ratified by all participating AZPOs. Tier *reduction* is a legitimate governance choice, not a penalty.

## Cross-Layer Dependencies

Layer V references skills from earlier layers:

- **Layer I (Agreement):** `agreement-creation` -- federation agreements are agreements; `agreement-registry` -- cross-AZPO records are registered
- **Layer II (Authority & Role):** `role-assignment` -- liaisons are roles with scoped authority; `domain-mapping` -- authority boundaries between AZPOs
- **Layer III (ACT Engine):** `act-consent-phase` -- all cross-AZPO decisions use consent; `act-advice-phase` -- parallel advice phases across AZPOs
- **Layer IV (Economic Coordination):** `funding-pool-stewardship` -- shared resource pools reference pool governance; `resource-request` -- cross-AZPO resource requests reference the request pattern

These are informational references, not loading dependencies. Each Layer V skill functions independently.

## OmniOne Configuration

OmniOne's multi-site SHUR network (Bali, Costa Rica, Mexico, Brazil) creates natural inter-unit coordination needs:

- **Different SHURs** may have different space agreements, resource pools, and circle structures but share the Universal Agreement Field and NEOS coordination protocols
- **TH, AE, and OSC** provide ecosystem-wide coordination surfaces but do not override individual SHUR or AZPO autonomy
- **Cross-SHUR coordination** uses the skills in this layer for formal interactions; informal communication continues freely
- **Traveling members** who participate in multiple SHURs encounter the boundary protocols defined here

## Design Principles

1. **No apex authority.** All coordination is lateral between AZPOs.
2. **Dual-consent.** Every cross-AZPO action requires consent from all participating AZPOs through their own ACT processes.
3. **Silence is not consent.** Non-response does not create obligation.
4. **Graduated engagement.** Not every relationship needs deep federation. The tier system supports relationships from minimal to deep.
5. **Agree to disagree.** Unresolved conflicts are legitimate outcomes, not failures. AZPOs may reduce engagement rather than accept imposed terms.
6. **Mandatory rotation.** Liaison roles rotate to prevent information concentration and informal power accumulation.
7. **Structural over personal.** Protocols, not personalities, govern inter-unit coordination.
