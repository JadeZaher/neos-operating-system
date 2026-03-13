# NEOS Structural Principles

These 10 principles are non-negotiable architecture. They define the structural invariants that every NEOS skill enforces. An ecosystem may configure its own roles, thresholds, and terminology, but it cannot violate these principles and remain NEOS-compatible.

OmniOne-specific configurations (Current-See amounts, SHUR structure, specific role names like OSC or AE) are ecosystem choices, not principles. The principles below apply to any ecosystem running NEOS.

---

## 1. Consent Over Consensus

**Definition:** Standard decisions pass when no participant raises a reasoned, domain-relevant objection -- not when everyone enthusiastically agrees.

**Structural mechanism:** The ACT Decision Engine (Layer III) separates the advice phase from the consent phase. During consent, each affected participant states whether they have a reasoned objection. Silence after the defined response window counts as no objection. Consensus is reserved for foundational decisions (e.g., OSC-level or Master Plan changes in OmniOne).

**Implementing skills:** act-consent-phase, consensus-check, proposal-resolution

**This principle is violated when:** a decision requires unanimous enthusiasm, when a participant's preference (rather than a reasoned objection) blocks a proposal, or when consent is bypassed entirely.

## 2. Defined Domains

**Definition:** Authority exists only within explicitly stated boundaries. No one holds implied, inherited, or unbounded authority.

**Structural mechanism:** Layer II requires every Circle to have a domain contract specifying what it can decide, what it cannot decide, and how boundary disputes are resolved. The domain-mapping skill produces a written domain contract. Authority boundary negotiation handles overlaps.

**Implementing skills:** domain-mapping, domain-review, authority-boundary-negotiation

**This principle is violated when:** a Circle makes decisions outside its stated domain, when authority is assumed rather than documented, or when domain boundaries are left undefined.

## 3. Structural Exit Right

**Definition:** Any participant can exit any agreement, role, or ecosystem at any time. Exit is never structurally punitive.

**Structural mechanism:** Layer X provides a complete exit pathway: voluntary-exit initiates departure, commitment-unwinding resolves outstanding obligations within a 30-day wind-down period, portable-record exports the participant's governance history. Participants retain rights to their original works. No financial penalty attaches to exit itself.

**Implementing skills:** voluntary-exit, commitment-unwinding, portable-record, re-entry-integration

**This principle is violated when:** exit requires permission, when leaving triggers financial penalties beyond legitimate obligation fulfillment, or when a participant's governance history is withheld.

## 4. Auto-Reversion of Emergency Authority

**Definition:** Any authority expansion granted during an emergency automatically expires. No crisis creates permanent exceptions.

**Structural mechanism:** Layer VIII requires every emergency authority grant to include a hard expiration timestamp. The emergency-reversion skill enforces automatic reversion when the timer expires. Post-emergency review audits every action taken under expanded authority. Pre-authorization defines what emergency actors may and may not do before a crisis occurs.

**Implementing skills:** emergency-reversion, pre-authorization-protocol, post-emergency-review, crisis-coordination

**This principle is violated when:** emergency authority persists after the crisis ends, when reversion requires an affirmative decision rather than happening automatically, or when emergency actions escape post-crisis review.

## 5. Capture Resistance

**Definition:** The governance structure actively resists four capture types: capital capture, charismatic capture, emergency capture, and informal capture.

**Structural mechanism:** Layer VII provides continuous monitoring. The capture-pattern-recognition skill defines detection indicators for each capture type. Governance-health-audit runs periodic assessments. Safeguard-trigger-design creates automatic alerts when capture indicators cross thresholds. Every skill includes a Capture Resistance Check (section H) addressing all four vectors.

**Implementing skills:** capture-pattern-recognition, governance-health-audit, safeguard-trigger-design, independent-monitoring, structural-diversity-maintenance

**This principle is violated when:** capital contribution translates into governance authority, when a single personality routinely overrides process, when crisis framing bypasses structural safeguards, or when unregistered agreements operate outside the Agreement Field.

## 6. Agreement Field Transparency

**Definition:** All agreements governing a space or interaction are registered, traceable, and accessible to affected participants.

**Structural mechanism:** Layer I requires every agreement to pass through agreement-creation (producing a structured document), registration in the agreement-registry (making it discoverable), and periodic agreement-review (ensuring continued relevance). The universal-agreement-field skill defines what constitutes the complete set of active agreements for any domain. Layer IX provides agreement-versioning so every change is traceable.

**Implementing skills:** agreement-creation, agreement-registry, agreement-review, universal-agreement-field, agreement-versioning

**This principle is violated when:** agreements exist outside the registry, when affected participants cannot access the agreements governing them, or when changes to agreements are not recorded.

## 7. No Hidden Authority

**Definition:** Every authority scope is stated and bounded. Every step requiring a judgment call names who holds that authority and its limits.

**Structural mechanism:** Every skill includes an Authority Boundary Check (section G) that maps each step to a named authority level. Layer II ensures roles are formally assigned (role-assignment), regularly reviewed (domain-review), and sunset when no longer needed (role-sunset). Authority that is not explicitly granted does not exist.

**Implementing skills:** role-assignment, role-sunset, domain-review, member-lifecycle

**This principle is violated when:** someone exercises authority that is not documented in their role or domain contract, when a governance step does not name the responsible authority, or when informal leadership replaces structural accountability.

## 8. Graceful Degradation

**Definition:** No single point of failure can collapse the governance system. Failure stays local.

**Structural mechanism:** Skills function independently -- each produces its own output artifact and defines its own failure containment logic (section I). AZPOs operate autonomously within their domains, so one AZPO's failure does not cascade to others. Layer X ensures that even mass departure (30% sudden exit) triggers quorum adaptation rather than system collapse.

**Implementing skills:** All skills via section I (Failure Containment Logic), azpo-dissolution, voluntary-exit

**This principle is violated when:** a single role's vacancy halts governance, when one AZPO's failure cascades across the ecosystem, or when the system requires full participation to function.

## 9. Governance Memory

**Definition:** Decisions are recorded, precedent is searchable, and governance history is preserved across time.

**Structural mechanism:** Layer IX requires every significant decision to produce a decision-record. Semantic-tagging makes records discoverable by context. Precedent-search allows participants to find how similar situations were handled before. Precedent-challenge allows outdated precedent to be formally revisited. Agreement-versioning tracks every change to every agreement.

**Implementing skills:** decision-record, semantic-tagging, precedent-search, precedent-challenge, agreement-versioning

**This principle is violated when:** decisions are made without records, when participants cannot find how prior similar situations were resolved, or when governance history is lost, deleted, or inaccessible.

## 10. Modularity

**Definition:** Every skill functions independently. No skill requires another skill to be installed to operate, though skills may reference each other by name.

**Structural mechanism:** Each skill has its own YAML frontmatter, its own sections A through L, its own output artifact, and its own failure containment. The `depends_on` field in frontmatter lists references, not hard dependencies. An ecosystem can adopt Layer I without Layer IV. Skills communicate through named references and shared artifact formats, not tight coupling.

**Implementing skills:** All skills (enforced by SKILL_TEMPLATE.md structure)

**This principle is violated when:** a skill cannot produce its output without another skill being present, when removing one layer breaks unrelated layers, or when skills share hidden state rather than referencing each other by name.

---

## Applying These Principles

When building or evaluating a NEOS skill, check every principle:

1. Does the skill's consent mechanism use consent (not consensus) for standard decisions?
2. Does the skill operate within a defined domain and state its boundaries?
3. Does the skill preserve the participant's right to exit without punishment?
4. Does any emergency authority the skill grants auto-revert?
5. Does the skill's section H address all four capture vectors?
6. Are all agreements the skill produces registered and traceable?
7. Does the skill's section G name every authority and its limits?
8. Does the skill's section I contain failure locally?
9. Does the skill produce a decision record or traceable artifact?
10. Does the skill function without requiring other skills to be installed?

A skill that fails any of these checks requires revision before it is NEOS-compatible.
