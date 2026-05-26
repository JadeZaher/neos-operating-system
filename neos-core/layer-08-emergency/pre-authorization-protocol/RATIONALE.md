---
skill: pre-authorization-protocol
type: rationale
---

# pre-authorization-protocol — Rationale & Design Notes

## A. Structural Problem It Solves

When a crisis hits, governance systems face a structural dilemma: normal deliberative processes are too slow for urgent action, but ad hoc authority is the gateway to capture. Every authoritarian consolidation in history began with a "temporary" grant of emergency power that was neither clearly scoped nor structurally constrained. The solution is advance consent -- the ecosystem defines emergency roles, authority scopes, spending ceilings, and expiration timers during calm conditions, through normal ACT process, before any crisis arrives. Pre-authorization separates the question of "who can act in an emergency" from the emotional pressure of the emergency itself. The ecosystem consents to bounded authority in advance, so that when a crisis arrives, the response is structural execution of a pre-consented plan, not improvised power granted under fear.

## B. Domain Scope

This skill applies to any ETHOS or ecosystem that has defined emergency criteria (per emergency-criteria-design). Pre-authorized roles are scoped to the domain boundary defined by domain-mapping (Layer II) -- roles designed for SHUR Bali operate only within Bali's governance domain. The skill covers the design, consent, and registry of pre-authorized emergency roles, not the activation of those roles during a crisis (that is crisis-coordination) or the reversion of authority after a crisis (that is emergency-reversion). Out of scope: this skill does not define how emergency decisions are made -- it defines who holds what bounded authority and for how long.

## OmniOne Walkthrough

It is March 2026, and SHUR Bali has installed five emergency criteria (per the emergency-criteria-design walkthrough). The team now designs pre-authorized roles for crisis response. Ketut, Ratu, and Nadia lead the design process.

**Role identification.** The team maps three emergency roles to the criteria registry: (1) Safety Coordinator -- activates for physical safety and infrastructure failure criteria; (2) Resource Coordinator -- activates for resource crisis criteria; (3) Communications Coordinator -- activates for all criteria categories.

**Safety Coordinator design.** Authority scope: evacuate the SHUR facility, arrange temporary shelter, authorize emergency repairs, coordinate with local emergency services. Hard ceilings: spending up to $3,000 per decision without additional consent, contracts up to 14 days, scope limited to physical safety decisions (no programmatic, financial restructuring, or governance decisions). Auto-expiration: authority expires when the triggering criterion's exit threshold is met or at the criterion's maximum duration.

**Resource Coordinator design.** Authority scope: release emergency reserves, renegotiate payment schedules with vendors, authorize essential operating expenditures, request emergency contributions from the ecosystem. Hard ceilings: spending up to $5,000 per decision, total emergency spending not to exceed 50% of quarterly reserves, contracts up to 30 days. Auto-expiration: aligned with resource crisis criterion maximum duration (30 days).

**Communications Coordinator design.** Authority scope: issue official statements on behalf of the ETHOS, communicate with external authorities, coordinate member communications. Hard ceilings: no financial authority, no authority to make commitments on behalf of the ETHOS beyond factual status updates, no authority to negotiate with external parties. Auto-expiration: aligned with the triggering criterion's duration.

**Irreducible constraints verification.** All three roles are checked against the constraints in `assets/irreducible-constraints.yaml`: none can amend the UAF, dissolve SHUR Bali, expel members, or modify emergency criteria. The Resource Coordinator's spending ceiling is explicitly below the threshold that would require UAF-level financial restructuring.

**Role holder designation.** Ratu (facilities steward, with construction experience) is designated Safety Coordinator with Dewa as alternate. Nadia (AE liaison, with financial background) is designated Resource Coordinator with Farid as alternate. Tomasz (TH member, journalist background) is designated Communications Coordinator with Sari as alternate. No individual holds more than one role.

**ACT process.** During the Advice phase, Yuki (cross-ETHOS advisor from Costa Rica) notes that the Safety Coordinator's $3,000 ceiling may be too low for emergency shelter arrangements in Bali: "In our experience, emergency lodging for 38 people costs $150-200 per night." The team revises the ceiling to $5,000 per decision. During Consent, Ketut confirms no reasoned objections. All three pre-authorizations are installed in the registry.

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

As OmniOne scales to 12 SHUR locations, each ETHOS designs pre-authorized roles calibrated to its local context. Bali's Safety Coordinator has a $5,000 ceiling reflecting local costs; Costa Rica's has $7,000 reflecting different economic conditions. The pre-authorization template (`assets/pre-authorization-template.yaml`) ensures structural consistency while allowing local calibration. Cross-ETHOS mutual aid pre-authorizations allow Safety Coordinators to request assistance from adjacent ETHOS during emergencies. At ecosystem scale, the OSC maintains visibility into all pre-authorization registries to identify gaps -- an ETHOS without a designated Communications Coordinator, for instance. The role designation and ACT consent process scales with the participant base because each ETHOS manages its own registry. No central authority designates emergency roles across the ecosystem.

### 6. External Legal Pressure

Indonesian authorities demand that SHUR Bali's emergency roles comply with national disaster preparedness regulations, including a requirement that the Safety Coordinator hold a government-issued certification. The pre-authorization framework can accommodate this: the role designation criteria are updated through ACT process to include the certification requirement. The authority scope, ceilings, and auto-expiration remain governed by the ecosystem's own pre-authorization design. If the government demands authority scopes that exceed the ecosystem's irreducible constraints -- for example, authority to "take all necessary measures" without defined ceilings -- the ecosystem designs a compliance interface that maps broad government language to specific, bounded NEOS authority scopes. External requirements are met through additional documentation and role qualification criteria, not by expanding emergency authority beyond the consented scope.

### 7. Sudden Exit of 30% of Participants

Twelve members exit, including Dewa (Safety Coordinator alternate) and Farid (Resource Coordinator alternate). The pre-authorization registry immediately shows two roles with no designated alternates. An expedited ACT process fills the alternate positions from the remaining 26 members within 14 days. If an emergency occurs during the gap, the primary role holders activate without alternates. If a primary role holder also departed, the OSC designates a temporary holder from the eligible member pool. The pre-authorization ceilings and authority scopes remain unchanged -- they are institutional parameters, not personal grants. The mass exit does not invalidate existing pre-authorizations. The annual review recalibrates ceilings if the resource base has changed significantly due to departures.
