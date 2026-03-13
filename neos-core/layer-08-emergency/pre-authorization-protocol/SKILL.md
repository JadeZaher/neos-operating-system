---
name: pre-authorization-protocol
description: "Define emergency roles with pre-consented authority scopes, hard ceilings, and auto-expiration before any crisis arrives -- so the ecosystem never improvises power during fear."
layer: 8
version: 0.1.0
depends_on: [emergency-criteria-design, role-assignment, authority-boundary-negotiation]
---

# pre-authorization-protocol

## A. Structural Problem It Solves

When a crisis hits, governance systems face a structural dilemma: normal deliberative processes are too slow for urgent action, but ad hoc authority is the gateway to capture. Every authoritarian consolidation in history began with a "temporary" grant of emergency power that was neither clearly scoped nor structurally constrained. The solution is advance consent -- the ecosystem defines emergency roles, authority scopes, spending ceilings, and expiration timers during calm conditions, through normal ACT process, before any crisis arrives. Pre-authorization separates the question of "who can act in an emergency" from the emotional pressure of the emergency itself. The ecosystem consents to bounded authority in advance, so that when a crisis arrives, the response is structural execution of a pre-consented plan, not improvised power granted under fear.

## B. Domain Scope

This skill applies to any AZPO or ecosystem that has defined emergency criteria (per emergency-criteria-design). Pre-authorized roles are scoped to the domain boundary defined by domain-mapping (Layer II) -- roles designed for SHUR Bali operate only within Bali's governance domain. The skill covers the design, consent, and registry of pre-authorized emergency roles, not the activation of those roles during a crisis (that is crisis-coordination) or the reversion of authority after a crisis (that is emergency-reversion). Out of scope: this skill does not define how emergency decisions are made -- it defines who holds what bounded authority and for how long.

## C. Trigger Conditions

- **Post-criteria installation**: after emergency criteria are installed via emergency-criteria-design, pre-authorization design follows to define who acts when those criteria are triggered
- **Role vacancy**: when a pre-authorized emergency role holder exits the ecosystem or becomes unavailable, a replacement must be designated through the ACT process
- **Post-emergency review recommendation**: when a post-emergency review identifies gaps in pre-authorized roles or authority scopes
- **Scheduled review**: pre-authorization registries are reviewed annually, aligned with emergency criteria review
- **Authority scope change**: when an AZPO's governance structure changes (new domains, new resources, new operational scope), pre-authorized roles may need recalibration

## D. Required Inputs

- **Emergency Criteria Registry**: the active criteria that pre-authorized roles will respond to (from emergency-criteria-design)
- **Role framework**: the ecosystem's role-assignment structure (Layer II), defining how roles are created and filled
- **Authority boundary definitions**: the ecosystem's authority-boundary-negotiation framework (Layer II), defining how authority scopes are set
- **Resource inventory**: the AZPO's available resources (financial, physical, operational) that emergency roles may need to access
- **ACT process access**: all pre-authorizations must be consented to through the Advice-Consent-Test protocol (Layer III)
- **Irreducible constraints list**: the boundaries that no emergency authority can cross, defined in `assets/irreducible-constraints.yaml`

## E. Step-by-Step Process

1. **Identify required emergency roles.** For each active emergency criterion, identify the operational roles needed for effective crisis response. Typical roles include Safety Coordinator (physical safety crises), Resource Coordinator (financial crises), Communications Coordinator (all crises), and Legal Liaison (external legal threats). Each role maps to one or more emergency criteria. Timeline: 2-5 days.
2. **Define authority scope per role.** For each role, specify exactly what the role holder can do during an active emergency: decisions they can make, resources they can access, communications they can issue, and contracts they can execute. Authority scopes must follow the minimum necessary authority principle -- the smallest scope required for effective crisis response.
3. **Set hard ceilings.** Each role includes quantified limits: maximum spending authority (e.g., "up to $5,000 per decision without additional consent"), maximum commitment duration (e.g., "contracts up to 30 days"), maximum scope (e.g., "facility safety decisions only, not programmatic decisions"). Ceilings are absolute -- they cannot be exceeded during an emergency, even with good intentions.
4. **Define auto-expiration.** Each pre-authorization includes an automatic expiration timer that begins when the emergency is declared. Default: role authority expires when exit criteria are met OR at maximum duration, whichever comes first. Authority cannot extend beyond the emergency criteria's maximum duration without emergency ACT consent (per crisis-coordination).
5. **Verify irreducible constraints.** Cross-reference each role's authority scope against the irreducible constraints in `assets/irreducible-constraints.yaml`. No pre-authorization can grant authority to: amend the UAF, dissolve an AZPO, expel a member, or modify emergency criteria during an active emergency. Any proposed authority that touches these constraints is rejected at the design stage.
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
- **No emergency authority** can cross irreducible constraints: UAF amendment, AZPO dissolution, member expulsion, criteria modification during emergency
- **Role holders** cannot appoint additional emergency roles or expand their own authority scope during an emergency
- **The ACT consent process** determines all pre-authorizations -- no individual or leadership body can pre-authorize emergency roles unilaterally
- **Auto-expiration** is structural, not discretionary -- authority ceases when the timer runs regardless of the role holder's assessment

## H. Capture Resistance Check

**Capital capture.** Spending ceilings prevent emergency roles from redirecting resources to favored interests. The Resource Coordinator has a hard dollar cap per decision and cannot enter long-term financial commitments under emergency authority. Pre-authorization is designed during calm conditions when funders have no crisis leverage over the design process. No emergency role can create new funding obligations beyond the defined ceiling.

**Charismatic capture.** The separation of emergency powers -- no individual holds more than one role -- prevents a charismatic leader from concentrating emergency authority. Role holders are designated through ACT consent, not by leadership appointment. A beloved leader can serve as one emergency role holder but cannot accumulate multiple roles or expand the scope of their single role.

**Emergency capture.** Auto-expiration timers are the primary defense. Pre-authorized authority has a hard structural end point that no individual decision can extend. The irreducible constraints prevent the most dangerous forms of emergency overreach: no UAF amendment means no permanent rule changes under emergency authority; no AZPO dissolution means no structural destruction during crisis; no criteria modification means the rules governing the emergency cannot be changed by those operating under emergency authority.

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

Pre-authorization registries for each AZPO are published to all ecosystem members, enabling cross-unit visibility into emergency preparedness. AZPOs in similar contexts can share role templates and authority scope definitions while customizing ceilings and holders locally. During an ecosystem-level emergency (e.g., OSC incapacity), ecosystem-wide pre-authorizations activate alongside AZPO-level ones. Cross-AZPO mutual aid agreements can include pre-authorized resource sharing during emergencies, designed through joint ACT process. When one AZPO's emergency affects adjacent AZPOs, the affected AZPOs' own pre-authorized roles activate independently within their domains.

## OmniOne Walkthrough

It is March 2026, and SHUR Bali has installed five emergency criteria (per the emergency-criteria-design walkthrough). The team now designs pre-authorized roles for crisis response. Ketut, Ratu, and Nadia lead the design process.

**Role identification.** The team maps three emergency roles to the criteria registry: (1) Safety Coordinator -- activates for physical safety and infrastructure failure criteria; (2) Resource Coordinator -- activates for resource crisis criteria; (3) Communications Coordinator -- activates for all criteria categories.

**Safety Coordinator design.** Authority scope: evacuate the SHUR facility, arrange temporary shelter, authorize emergency repairs, coordinate with local emergency services. Hard ceilings: spending up to $3,000 per decision without additional consent, contracts up to 14 days, scope limited to physical safety decisions (no programmatic, financial restructuring, or governance decisions). Auto-expiration: authority expires when the triggering criterion's exit threshold is met or at the criterion's maximum duration.

**Resource Coordinator design.** Authority scope: release emergency reserves, renegotiate payment schedules with vendors, authorize essential operating expenditures, request emergency contributions from the ecosystem. Hard ceilings: spending up to $5,000 per decision, total emergency spending not to exceed 50% of quarterly reserves, contracts up to 30 days. Auto-expiration: aligned with resource crisis criterion maximum duration (30 days).

**Communications Coordinator design.** Authority scope: issue official statements on behalf of the AZPO, communicate with external authorities, coordinate member communications. Hard ceilings: no financial authority, no authority to make commitments on behalf of the AZPO beyond factual status updates, no authority to negotiate with external parties. Auto-expiration: aligned with the triggering criterion's duration.

**Irreducible constraints verification.** All three roles are checked against the constraints in `assets/irreducible-constraints.yaml`: none can amend the UAF, dissolve SHUR Bali, expel members, or modify emergency criteria. The Resource Coordinator's spending ceiling is explicitly below the threshold that would require UAF-level financial restructuring.

**Role holder designation.** Ratu (facilities steward, with construction experience) is designated Safety Coordinator with Dewa as alternate. Nadia (AE liaison, with financial background) is designated Resource Coordinator with Farid as alternate. Tomasz (TH member, journalist background) is designated Communications Coordinator with Sari as alternate. No individual holds more than one role.

**ACT process.** During the Advice phase, Yuki (cross-AZPO advisor from Costa Rica) notes that the Safety Coordinator's $3,000 ceiling may be too low for emergency shelter arrangements in Bali: "In our experience, emergency lodging for 38 people costs $150-200 per night." The team revises the ceiling to $5,000 per decision. During Consent, Ketut confirms no reasoned objections. All three pre-authorizations are installed in the registry.

**Edge case.** During the tabletop drill, the team simulates a scenario where flooding damages the SHUR facility and a vendor demands $8,000 for emergency water delivery. The Resource Coordinator's ceiling is $5,000 per decision. Nadia cannot authorize the full amount unilaterally. She authorizes $5,000 and logs the remaining $3,000 in the deferred decision queue for emergency ACT consent among available members. The drill reveals that the compressed ACT timeline (per crisis-coordination) can process such decisions within 24 hours, making the ceiling operationally viable without exposing the ecosystem to uncapped spending.

## Stress-Test Results

### 1. Capital Influx

A major funder offers to "sponsor" SHUR Bali's emergency preparedness by funding a full-time paid Emergency Director role with expanded authority. The pre-authorization protocol prevents this: emergency roles are defined through ACT consent with bounded authority scopes, hard ceilings, and auto-expiration. A funder cannot install a role that bypasses the consent process. The proposed Emergency Director role would violate the separation of emergency powers (one person, multiple authority domains) and would lack auto-expiration (permanent role). The ecosystem can accept the funding for emergency preparedness training and supplies, but the governance structure of emergency roles remains under ACT consent, not funder design. The pre-authorization registry makes the actual authority structure visible to all members, preventing any quiet expansion of a funder-sponsored role beyond its consented scope.

### 2. Emergency Crisis

A volcanic eruption triggers the physical safety criterion. The Safety Coordinator (Ratu) activates immediately under pre-authorized authority: she evacuates the facility, arranges temporary shelter at a hotel complex, and coordinates with Bali's BPBD emergency service. Every decision falls within her authority scope and under her $5,000 ceiling. The Resource Coordinator (Nadia) activates for the financial dimension: she releases emergency reserves for shelter costs and food. The Communications Coordinator (Tomasz) issues member updates and coordinates with the OSC. No role holder makes decisions outside their scope. When the hotel manager offers a discounted long-term lease "while you rebuild," Nadia declines -- her authority covers contracts up to 30 days, and a long-term lease exceeds her scope. The lease proposal goes into the deferred decision queue. The auto-expiration timer starts at declaration and the ecosystem knows exactly when authority will cease, removing the ambiguity that enables emergency capture.

### 3. Leadership Charisma Capture

Surya, the beloved founding member, is not designated for any emergency role -- she serves as a regular TH member during crises. During a crisis, Surya naturally begins directing operations because members defer to her judgment. The pre-authorization structure makes this visible: Surya has no emergency authority. Any decision Surya makes carries no institutional weight during the emergency -- only the designated role holders' decisions are logged as authorized emergency actions. If members follow Surya's informal direction instead of the authorized Safety Coordinator's instructions, the structural conflict is documented in the crisis operations log. Post-emergency review examines whether informal authority displaced pre-authorized authority. The pre-authorization framework does not prevent charismatic influence during a crisis, but it creates a structural record that makes the displacement visible and addressable, rather than invisible and normalized.

### 4. High Conflict / Polarization

During a resource crisis, the two SHUR Bali factions disagree on how the Resource Coordinator should use emergency reserves. Faction A wants reserves directed toward the partnership that caused the polarization; Faction B wants reserves used only for essential operations. The pre-authorization resolves this: the Resource Coordinator's authority scope specifies "essential operating expenditures," not discretionary programmatic spending. The partnership funding decision falls outside the emergency scope and goes into the deferred decision queue for normal ACT process after the emergency. Both factions can verify this against the published pre-authorization registry. The Resource Coordinator's authority is defined by the pre-consented scope, not by which faction's argument is more persuasive. The hard ceiling prevents either faction from using the emergency to redirect significant resources toward their preferred outcome.

### 5. Large-Scale Replication

As OmniOne scales to 12 SHUR locations, each AZPO designs pre-authorized roles calibrated to its local context. Bali's Safety Coordinator has a $5,000 ceiling reflecting local costs; Costa Rica's has $7,000 reflecting different economic conditions. The pre-authorization template (`assets/pre-authorization-template.yaml`) ensures structural consistency while allowing local calibration. Cross-AZPO mutual aid pre-authorizations allow Safety Coordinators to request assistance from adjacent AZPOs during emergencies. At ecosystem scale, the OSC maintains visibility into all pre-authorization registries to identify gaps -- an AZPO without a designated Communications Coordinator, for instance. The role designation and ACT consent process scales with the participant base because each AZPO manages its own registry. No central authority designates emergency roles across the ecosystem.

### 6. External Legal Pressure

Indonesian authorities demand that SHUR Bali's emergency roles comply with national disaster preparedness regulations, including a requirement that the Safety Coordinator hold a government-issued certification. The pre-authorization framework can accommodate this: the role designation criteria are updated through ACT process to include the certification requirement. The authority scope, ceilings, and auto-expiration remain governed by the ecosystem's own pre-authorization design. If the government demands authority scopes that exceed the ecosystem's irreducible constraints -- for example, authority to "take all necessary measures" without defined ceilings -- the ecosystem designs a compliance interface that maps broad government language to specific, bounded NEOS authority scopes. External requirements are met through additional documentation and role qualification criteria, not by expanding emergency authority beyond the consented scope.

### 7. Sudden Exit of 30% of Participants

Twelve members exit, including Dewa (Safety Coordinator alternate) and Farid (Resource Coordinator alternate). The pre-authorization registry immediately shows two roles with no designated alternates. An expedited ACT process fills the alternate positions from the remaining 26 members within 14 days. If an emergency occurs during the gap, the primary role holders activate without alternates. If a primary role holder also departed, the OSC designates a temporary holder from the eligible member pool. The pre-authorization ceilings and authority scopes remain unchanged -- they are institutional parameters, not personal grants. The mass exit does not invalidate existing pre-authorizations. The annual review recalibrates ceilings if the resource base has changed significantly due to departures.
