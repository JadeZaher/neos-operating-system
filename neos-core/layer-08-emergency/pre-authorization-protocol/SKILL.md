---
name: pre-authorization-protocol
description: "Define emergency roles with pre-consented authority scopes, hard ceilings, and auto-expiration before any crisis arrives -- so the ecosystem never improvises power during fear."
layer: 8
version: 0.1.0
depends_on: [emergency-criteria-design, role-assignment, authority-boundary-negotiation]
---

# pre-authorization-protocol

## C. Trigger Conditions

- **Post-criteria installation**: after emergency criteria are installed via emergency-criteria-design, pre-authorization design follows to define who acts when those criteria are triggered
- **Role vacancy**: when a pre-authorized emergency role holder exits the ecosystem or becomes unavailable, a replacement must be designated through the ACT process
- **Post-emergency review recommendation**: when a post-emergency review identifies gaps in pre-authorized roles or authority scopes
- **Scheduled review**: pre-authorization registries are reviewed annually, aligned with emergency criteria review
- **Authority scope change**: when an ETHOS's governance structure changes (new domains, new resources, new operational scope), pre-authorized roles may need recalibration

## D. Required Inputs

- **Emergency Criteria Registry**: the active criteria that pre-authorized roles will respond to (from emergency-criteria-design)
- **Role framework**: the ecosystem's role-assignment structure (Layer II), defining how roles are created and filled
- **Authority boundary definitions**: the ecosystem's authority-boundary-negotiation framework (Layer II), defining how authority scopes are set
- **Resource inventory**: the ETHOS's available resources (financial, physical, operational) that emergency roles may need to access
- **ACT process access**: all pre-authorizations must be consented to through the Advice-Consent-Test protocol (Layer III)
- **Irreducible constraints list**: the boundaries that no emergency authority can cross, defined in `assets/irreducible-constraints.yaml`

## E. Step-by-Step Process

1. **Identify required emergency roles.** For each active emergency criterion, identify the operational roles needed for effective crisis response. Typical roles include Safety Coordinator (physical safety crises), Resource Coordinator (financial crises), Communications Coordinator (all crises), and Legal Liaison (external legal threats). Each role maps to one or more emergency criteria. Timeline: 2-5 days.
2. **Define authority scope per role.** For each role, specify exactly what the role holder can do during an active emergency: decisions they can make, resources they can access, communications they can issue, and contracts they can execute. Authority scopes must follow the minimum necessary authority principle -- the smallest scope required for effective crisis response.
3. **Set hard ceilings.** Each role includes quantified limits: maximum spending authority (e.g., "up to $5,000 per decision without additional consent"), maximum commitment duration (e.g., "contracts up to 30 days"), maximum scope (e.g., "facility safety decisions only, not programmatic decisions"). Ceilings are absolute -- they cannot be exceeded during an emergency, even with good intentions.
4. **Define auto-expiration.** Each pre-authorization includes an automatic expiration timer that begins when the emergency is declared. Default: role authority expires when exit criteria are met OR at maximum duration, whichever comes first. Authority cannot extend beyond the emergency criteria's maximum duration without emergency ACT consent (per crisis-coordination).
5. **Verify irreducible constraints.** Cross-reference each role's authority scope against the irreducible constraints in `assets/irreducible-constraints.yaml`. No pre-authorization can grant authority to: amend the UAF, dissolve an ETHOS, expel a member, or modify emergency criteria during an active emergency. Any proposed authority that touches these constraints is rejected at the design stage.
6. **Designate role holders and alternates.** Identify primary and alternate holders for each role. Role holders must be ecosystem members in good standing. No individual holds more than one emergency role (separation of emergency powers). The criteria designer cannot be the emergency role holder for their own criteria (separation of design and execution).
7. **Enter ACT Advice phase.** Share the pre-authorization design with affected stakeholders. Advisors evaluate: Is the authority scope sufficient for effective response? Are the ceilings appropriate? Do irreducible constraints hold? Are role holders appropriately independent? Timeline: 5-10 days.
8. **Enter ACT Consent phase.** Present the pre-authorization for consent. Consent means "no reasoned objection." Objections must reference specific structural concerns. Timeline: 5-7 days.
9. **Install in Pre-Authorization Registry.** Upon consent, register each role with unique ID, authority scope, ceilings, auto-expiration rules, irreducible constraints acknowledgment, role holders, and status "standby." The registry is published to all ecosystem members.
10. **Conduct readiness drill.** Within 30 days of installation, conduct a tabletop drill where role holders walk through a simulated emergency scenario using their pre-authorized authority. Document gaps and adjust through ACT process.

## F. Output Artifact

A Pre-Authorization Registry entry following `assets/pre-authorization-template.yaml`. Each entry contains: role ID, role name, associated emergency criteria IDs, authority scope (decisions, resources, communications, contracts), hard ceilings (spending, duration, scope), auto-expiration rules, irreducible constraints acknowledgment, primary holder, alternate holder(s), installed-by reference (ACT decision ID), installation date, review date, activation history, and status (standby/active/expired). The full registry is accessible to all ecosystem members.

## G. Authority Boundary Check

- **Pre-authorized roles** can only exercise authority that was explicitly consented to during the ACT process -- no implied or expanded authority
- **No role holder** can exceed their defined ceilings, even in genuine crisis conditions -- ceiling violation is itself a governance event logged for post-emergency review
- **No emergency authority** can cross irreducible constraints: UAF amendment, ETHOS dissolution, member expulsion, criteria modification during emergency
- **Role holders** cannot appoint additional emergency roles or expand their own authority scope during an emergency
- **The ACT consent process** determines all pre-authorizations -- no individual or leadership body can pre-authorize emergency roles unilaterally
- **Auto-expiration** is structural, not discretionary -- authority ceases when the timer runs regardless of the role holder's assessment

## H. Capture Resistance Check

**Capital capture.** Spending ceilings prevent emergency roles from redirecting resources to favored interests. The Resource Coordinator has a hard dollar cap per decision and cannot enter long-term financial commitments under emergency authority. Pre-authorization is designed during calm conditions when funders have no crisis leverage over the design process. No emergency role can create new funding obligations beyond the defined ceiling.

**Charismatic capture.** The separation of emergency powers -- no individual holds more than one role -- prevents a charismatic leader from concentrating emergency authority. Role holders are designated through ACT consent, not by leadership appointment. A beloved leader can serve as one emergency role holder but cannot accumulate multiple roles or expand the scope of their single role.

**Emergency capture.** Auto-expiration timers are the primary defense. Pre-authorized authority has a hard structural end point that no individual decision can extend. The irreducible constraints prevent the most dangerous forms of emergency overreach: no UAF amendment means no permanent rule changes under emergency authority; no ETHOS dissolution means no structural destruction during crisis; no criteria modification means the rules governing the emergency cannot be changed by those operating under emergency authority.

**Informal capture.** All pre-authorizations are formally registered, publicly visible, and installed through ACT consent. There are no informal emergency powers, no "understood" authority, and no "someone has to make the call" justifications. If an authority was not pre-consented, it does not exist during an emergency.

## I. Failure Containment Logic

- **Role holder unavailable during emergency**: the designated alternate activates immediately. If no alternate is available, the OSC designates a temporary holder from the eligible member pool for the duration of the emergency only
- **Authority scope proves insufficient**: the role holder operates within their defined scope and logs unaddressable situations for the deferred decision queue (per crisis-coordination). Scope expansion requires emergency ACT consent, not unilateral expansion
- **Ceiling exceeded in good faith**: the ceiling violation is logged as a governance event. The excess action stands (it cannot be undone during crisis) but is reviewed during post-emergency review with the role holder bearing the burden of justification
- **Irreducible constraint violated**: the violation is immediately flagged to all ecosystem members and the OSC. The violating action is reversed as soon as safely possible. The role holder's pre-authorization is suspended pending post-emergency review
- **Multiple emergencies requiring the same role**: each emergency activates its own pre-authorization track. If the same individual holds roles for overlapping emergencies, their alternate activates for the second emergency to prevent authority concentration

## J. Expiry / Review Condition

Pre-authorizations are reviewed annually, aligned with the emergency criteria review cycle. The review evaluates: Are role holders still active members? Are authority scopes appropriately calibrated? Are ceilings realistic? Have any post-emergency reviews recommended changes? Role holders who have served for more than two consecutive annual cycles are rotated through the role-assignment process. Pre-authorizations do not auto-expire between reviews -- they remain on standby. If a review is missed, automatic escalation notifies all ecosystem members. Retired pre-authorizations are preserved in the registry with their activation history.

## K. Exit Compatibility Check

When a pre-authorized role holder exits the ecosystem, their alternate becomes the primary holder and a new alternate is designated through the role-assignment process within 30 days. If both the primary and alternate exit, the pre-authorization enters "vacant" status and an expedited ACT process fills the role. Exiting role holders have no ongoing obligation related to pre-authorizations. During an active emergency, if the current role holder exits, their alternate assumes authority immediately -- no gap in emergency response capability. Past activation records for departed role holders remain in the registry.

## L. Cross-Unit Interoperability Impact

Pre-authorization registries for each ETHOS are published to all ecosystem members, enabling cross-unit visibility into emergency preparedness. ETHOS in similar contexts can share role templates and authority scope definitions while customizing ceilings and holders locally. During an ecosystem-level emergency (e.g., OSC incapacity), ecosystem-wide pre-authorizations activate alongside ETHOS-level ones. Cross-ETHOS mutual aid agreements can include pre-authorized resource sharing during emergencies, designed through joint ACT process. When one ETHOS's emergency affects adjacent ETHOS, the affected ETHOS' own pre-authorized roles activate independently within their domains.
