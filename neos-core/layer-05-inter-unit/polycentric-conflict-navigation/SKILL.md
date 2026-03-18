---
name: polycentric-conflict-navigation
description: "Resolve structural disputes between ETHOS -- authority overlaps, agreement contradictions, resource competition, and boundary disputes -- through a three-tier lateral resolution protocol that preserves every unit's autonomy."
layer: 5
version: 0.1.0
depends_on: [cross-ethos-request, federation-agreement, inter-unit-liaison, act-consent-phase]
---

# polycentric-conflict-navigation

## A. Structural Problem It Solves

When two autonomous units have conflicting authority claims, contradictory agreements, or competing resource interests, there is no sovereign authority to resolve the dispute. Without a structural protocol, conflicts either escalate indefinitely, result in ecosystem fragmentation, or are resolved by whoever has more power -- the antithesis of polycentric governance. This skill provides a three-tier lateral resolution protocol that preserves both units' autonomy while creating pathways to agreement. The millet system lesson applies: shared protocols without a Sultan. No body, individual, or ETHOS can impose resolution on another.

## B. Domain Scope

This skill applies to structural conflicts between two or more ETHOS. Conflict types include:

- **Authority overlap** -- both ETHOS claim governance authority over the same domain or decision
- **Agreement contradiction** -- ETHOS A's agreements conflict with ETHOS B's in their intersection
- **Resource competition** -- both ETHOS need the same limited resource and their claims are incompatible
- **Boundary dispute** -- unclear which ETHOS's rules apply in a shared or overlapping space
- **Protocol divergence** -- ETHOS follow incompatible processes for the same coordination need

This is distinct from Layer VI (Conflict and Repair), which handles interpersonal and intra-ETHOS conflict. This skill handles structural conflicts between autonomous units that each have legitimate governance authority within their own domains.

## C. Trigger Conditions

- An ETHOS identifies that another ETHOS's actions or agreements conflict with its own governance structures
- A cross-ETHOS request reveals incompatible expectations between two ETHOS
- A liaison reports a structural incompatibility between participating ETHOS
- A participant operating in both ETHOS encounters contradictory governance requirements
- A federation agreement review surfaces unresolved structural tensions

## D. Required Inputs

- **Affected ETHOS** -- all units involved in the structural conflict (mandatory)
- **Conflict description** -- specific claims from each side, documented neutrally (mandatory)
- **Conflict type** -- authority overlap, agreement contradiction, resource competition, boundary dispute, or protocol divergence (mandatory)
- **Supporting documentation** -- relevant agreements, authority scopes, resource records (mandatory)
- **Desired resolution timeline** -- when the affected ETHOS want resolution, understanding this is aspirational (mandatory)

## E. Step-by-Step Process

### Tier 1: Direct Negotiation

1. **Identify and document conflict.** The ETHOS that identifies the conflict formally documents it using `assets/conflict-resolution-record-template.yaml`. Both ETHOS' claims are stated in the record.
2. **Designate representatives.** Each affected ETHOS designates a representative with mandate to negotiate (but not to commit without ETHOS consent).
3. **Direct dialogue.** Representatives meet and share their ETHOS's position, interests, and constraints. The dialogue seeks mutual solutions through good-faith engagement.
4. **Outcome.** If a resolution emerges, it is documented and submitted to each ETHOS for ratification through their own ACT process. If no resolution within 30 days, either ETHOS may request escalation to Tier 2.

### Tier 2: Facilitated Dialogue

5. **Select neutral facilitator.** Each ETHOS proposes three candidates from other ETHOS (not from the affected ETHOS). Overlapping names are selected. If no overlap, both lists are combined and random selection is used.
6. **Facilitated dialogue.** The neutral party facilitates but does NOT decide. They have process authority only -- managing the conversation, surfacing underlying interests, and helping parties see structural solutions. They have zero outcome authority.
7. **Outcome.** If a resolution emerges, it is documented and submitted to each ETHOS for ratification. If no resolution within 45 days, either ETHOS may request escalation to Tier 3 or choose to conclude without agreement (see Step 9).

### Tier 3: Structural Resolution

8. **Federation agreement amendment or new agreement.** If Tiers 1-2 did not produce resolution because the conflict stems from a structural gap (no protocol exists for the situation), the affected ETHOS draft a federation agreement amendment or new agreement that addresses the underlying structural incompatibility. This uses the full federation-agreement skill process with negotiation, drafting, and per-ETHOS ratification.

### Legitimate Conclusion Without Resolution

9. **Agree to disagree.** At any tier, both ETHOS may conclude that no mutually acceptable resolution exists. This is a legitimate outcome, not a failure. The ETHOS may choose to reduce their engagement tier (from federate to cooperate, or cooperate to observe). The conflict resolution record documents the disagreement, the good-faith process, and the resulting relationship adjustment.

## F. Output Artifact

A polycentric conflict resolution record following `assets/conflict-resolution-record-template.yaml`, containing: conflict ID, affected ETHOS, conflict type, description with each ETHOS's claims, supporting documentation references, resolution tier reached, facilitator identity and selection method (if Tier 2+), outcome agreement or documented disagreement, any federation agreement amendments, ratification records from each ETHOS, and review date (6 months post-resolution).

## G. Authority Boundary Check

- **No ETHOS, body, or individual can impose a resolution.** All resolutions require mutual consent through each ETHOS's own ACT process.
- **Neutral facilitators (Tier 2)** have process authority only -- managing dialogue structure, time, and flow. They have zero outcome authority. They cannot propose solutions as binding.
- **Resolution outcomes** require ratification through each affected ETHOS's consent round. No shortcut exists.
- **If no resolution is reached,** ETHOS may reduce their engagement tier rather than being forced into a resolution they did not consent to. This is structurally protected as a legitimate choice.
- **Ecosystem-level bodies (OSC, TH)** do not serve as appellate courts. They may offer facilitation but cannot impose outcomes on ETHOS.

## H. Capture Resistance Check

**Size leverage.** A larger ETHOS pressures a smaller one through implied consequences of non-resolution ("if you don't agree, we'll reduce resource sharing"). Resistance: each ETHOS evaluates resolutions through its own consent process. Implied threats are documented as capture vectors. The option to reduce engagement tier protects the smaller ETHOS from being forced into unfavorable terms by economic dependency.

**Facilitator bias.** The Tier 2 neutral party develops structural bias toward one side -- perhaps the ETHOS they interact with more, or the ETHOS whose governance philosophy they share. Resistance: the dual-list selection process surfaces mutually acceptable facilitators. Either ETHOS may request facilitator replacement if bias is demonstrated. Facilitator conduct is documented in the resolution record.

**Resolution fatigue.** One side capitulates to end the process rather than genuinely consenting. Resistance: each ETHOS's ratification runs through a full ACT consent round with objection rights. Facilitators are trained to distinguish genuine consent from exhaustion. If resolution fatigue is suspected, the process pauses for a cooling period (recommended: 14 days).

**Precedent weaponization.** Past resolutions are cited to constrain future autonomy ("you agreed to X last time, so you must agree to X now"). Resistance: each conflict is documented and resolved independently. Prior resolution records are context, not binding precedent. Each ETHOS retains full autonomy in future disputes.

**Escalation avoidance.** ETHOS avoid Tier 2 or 3 because the process feels too burdensome, letting conflicts fester. Resistance: the three-tier model is designed to be progressively deeper, not progressively punitive. Tier 1 is lightweight. Liaison roles can flag festering conflicts. The skill explicitly affirms that using the process is preferable to unresolved structural tension.

## I. Failure Containment Logic

- **No resolution reached:** ETHOS may agree to disagree and reduce engagement tier. This is documented as a legitimate outcome. The conflict resolution record captures the good-faith process and the resulting relationship adjustment.
- **Neutral party unavailable:** Extend Tier 1 direct negotiation with documented good-faith attempts. If facilitator selection repeatedly fails, the ETHOS may jointly request ecosystem-level facilitation resources (but not imposed outcomes).
- **Resolution agreement violated:** The aggrieved ETHOS may trigger a review, returning the conflict to the appropriate tier. The violation is documented in the resolution record.
- **One ETHOS refuses to participate:** Non-participation is documented. The requesting ETHOS may unilaterally adjust their engagement tier. Non-participation does not grant the non-participating ETHOS veto power over the other's governance adjustments.

## J. Expiry / Review Condition

- **Post-resolution review:** Conflict resolution records are reviewed 6 months after resolution to check whether the outcome is holding. If the resolution has broken down, the conflict may be re-opened at the appropriate tier.
- **Federation agreement amendments** triggered by conflict resolution follow the federation agreement's own review cycle.
- **Conflict resolution records** are retained indefinitely as documentation. They do not expire.
- **"Agree to disagree" outcomes** are reviewed at 12 months to assess whether circumstances have changed enough to re-attempt resolution.

## K. Exit Compatibility Check

- **ETHOS exits during navigation:** The process concludes with documentation. The conflict resolution record captures the state at exit. Remaining ETHOS adjust their governance as needed.
- **ETHOS dissolves:** All active conflict navigation processes involving the dissolved ETHOS are closed with documentation.
- **Participant exits but ETHOS continues:** The ETHOS designates a new representative. The process continues.
- **Completed resolutions survive exit.** Federation agreement amendments produced through this process remain binding on the ETHOS that ratified them, regardless of individual participant departures.

## L. Cross-Unit Interoperability Impact

This skill is the capstone cross-unit mechanism for Layer V. It handles the structural disputes that emerge from all the coordination structures defined in the other Layer V skills. It references cross-ethos-request (how conflicts are identified through incompatible requests), federation-agreement (how structural resolutions are formalized), and inter-unit-liaison (how liaisons flag emerging conflicts before they escalate). The conflict resolution record is registered in all affected ETHOS' agreement registries. Structural resolutions that produce federation agreement amendments are registered per the federation-agreement skill's procedures.

## OmniOne Walkthrough

Maria, a TH member, splits her time between the Bali and Costa Rica SHURs -- three months in each annually. She encounters a governance contradiction: Bali's space agreement sets quiet hours at 9:30pm, while Costa Rica's sets them at 10:30pm. When Maria is in Costa Rica but participates in a Bali circle meeting at 10pm local time, she violates Bali's quiet hours rule according to Bali's space agreement -- but she is physically in Costa Rica where 10pm is well within quiet hours. No protocol exists for this situation.

**Tier 1: Direct Negotiation.** Putu (Bali's Space circle representative) and Diego (Costa Rica's Space circle representative) meet to discuss. Bali's position: their space agreement applies to any member participating in Bali circle activities, regardless of physical location. Costa Rica's position: the physical location's space agreement governs, since the member is in Costa Rica's physical space. After two meetings over three weeks, no resolution -- the disagreement is fundamental about whether "space agreements follow the person" or "space agreements follow the place."

**Escalation to Tier 2.** Putu requests facilitated dialogue. Each SHUR proposes three candidates: Bali proposes Valentina (Mexico), Kenji (Brazil), and Amara (Brazil). Costa Rica proposes Valentina (Mexico), Soren (Mexico), and Pilar (Mexico). Overlap: Valentina from Mexico. She is selected as facilitator.

**Facilitated dialogue.** Valentina facilitates three sessions over four weeks. She surfaces the underlying issue: no protocol exists for members who are present in multiple SHURs. The quiet-hours conflict is a symptom, not the root problem. The root is: which SHUR's agreement field governs a member who is physically in one SHUR but participating in another's governance activities?

**Resolution.** Through facilitation, a structural solution emerges: a "visiting member" protocol as a federation agreement amendment. Key provisions: when a member is physically present in a SHUR, that SHUR's space agreements govern physical behavior (noise, common spaces, schedules). When a member participates remotely in another SHUR's governance, the remote SHUR's governance protocols apply to the governance process but the physical SHUR's space rules apply to the physical environment. A visiting member who spends more than 30 consecutive days in a SHUR is subject to that SHUR's full space agreement.

**Ratification.** Both SHURs run consent. Bali's Space circle: 8 members, all consent after advice round where one member asks for clarity on the 30-day threshold. Costa Rica: 6 members, 5 consent, one proposes reducing the threshold to 14 days. Integration round: Bali counters that 14 days is too short for visitors to learn the space agreement. Compromise at 21 days for short visits, 30 days for full integration. Round 2: all 6 consent.

The federation agreement amendment is registered in both SHURs' registries. Maria's situation is immediately clarified.

**Edge case: facilitator bias.** During dialogue, Putu notices that Valentina knows Diego personally from a prior cross-SHUR project. Putu raises this concern formally. Valentina discloses the relationship and offers to recuse. Both ETHOS discuss: the relationship is professional, not personal, and Valentina has been evenhanded in facilitation. They agree she should continue but the disclosure is documented in the resolution record. If Putu had pressed for replacement, a new selection process would have begun.

## Stress-Test Results

### 1. Capital Influx

A wealthy ETHOS has a boundary dispute with a smaller ETHOS over access to a shared facility. During Tier 1 negotiation, the wealthy ETHOS implies that an unfavorable resolution could affect their resource-sharing commitments. The smaller ETHOS's negotiator documents this as size leverage in the conflict resolution record. At Tier 2, the facilitator explicitly names the economic dynamic and ensures the dialogue focuses on the structural merits of each position. The smaller ETHOS's consent round evaluates the proposed resolution independently of economic implications. The option to reduce engagement tier protects the smaller ETHOS from being forced into terms by financial dependency -- if the resolution is unfavorable, they can step back to "cooperate" tier and maintain autonomy.

### 2. Emergency Crisis

Two SHURs have an unresolved authority overlap about which SHUR coordinates disaster response for a shared geographic area. An earthquake strikes. The existing Tier 1 negotiation is suspended. Both SHURs invoke emergency protocols and coordinate ad hoc for immediate response. Post-crisis, the conflict navigation resumes with additional urgency and context. The emergency revealed exactly why the authority overlap needed resolution. The post-crisis Tier 2 facilitation produces a joint emergency response protocol as a federation agreement amendment. Both SHURs ratify under standard (not emergency) timelines -- the crisis is over and the resolution needs to be durable, not rushed.

### 3. Leadership Charisma Capture

A charismatic ecosystem leader publicly advocates for one ETHOS's position in a boundary dispute, characterizing the other ETHOS as "prioritizing rules over community." The social pressure is significant. During Tier 2 facilitated dialogue, the facilitator names the external pressure and ensures both ETHOS' positions are evaluated on structural merits. The consent round in the pressured ETHOS includes explicit recognition that external advocacy does not factor into the consent decision. The structural protection is the consent round itself -- each participant records their position independently. Objections are formally recorded before any discussion, preventing social pressure from suppressing dissent.

### 4. High Conflict

Two ETHOS have fundamental governance disagreements -- one operates by deep consensus on all decisions, the other uses lighter consent-based processes. Their federation agreement requires joint decisions on shared infrastructure. The deep-consensus ETHOS finds the consent-based ETHOS's decisions insufficiently deliberated. The consent-based ETHOS finds the other's process paralyzingly slow. Tier 1 negotiation fails -- the disagreement is philosophical. Tier 2 facilitation surfaces the core tension: both processes are legitimate NEOS governance modes, and neither can be imposed on the other. The structural resolution: the federation agreement is amended to specify which ETHOS's decision mode applies to which shared infrastructure decisions, with a default to the lighter mode for operational decisions and the deeper mode for strategic decisions. Both ETHOS consent. If they had not found a resolution, they could have reduced their engagement tier -- a legitimate structural choice.

### 5. Large-Scale Replication

OmniOne grows to 15 SHURs. Multiple structural conflicts emerge simultaneously: boundary disputes between adjacent SHURs, protocol divergence between SHURs that developed independently, and resource competition for shared ecosystem funds. Each conflict follows its own resolution track independently. Facilitator pools deepen as more SHURs provide candidates. A pattern emerges where common structural gaps (like the visiting member scenario) produce federation agreement templates that new SHURs can adopt or adapt. The skill scales because each conflict is self-contained and uses the same three-tier structure. No central conflict court is created.

### 6. External Legal Pressure

A government agency asserts regulatory authority over a domain that two SHURs' governance also covers, creating a three-way authority overlap. The two SHURs use this skill to resolve their mutual overlap, then jointly engage with the regulatory requirement through their respective legal stewards. The government's mandate is treated as a constraint that both SHURs must accommodate individually (per their jurisdictions), not as a resolution to their structural dispute. Each SHUR's compliance is handled locally. The resolution between the two SHURs addresses the governance overlap independent of the external requirement.

### 7. Sudden Exit of 30% of Participants

Mass departure occurs during an active Tier 2 facilitation between two SHURs. Three representatives from one SHUR exit simultaneously. The SHUR designates replacements for the conflict navigation process. The process pauses for 14 days while new representatives are briefed using the documented conflict resolution record. The facilitator re-establishes context with the new representatives. The process continues. If one ETHOS has too few remaining members to meaningfully participate, the process pauses until that ETHOS stabilizes. The conflict resolution record preserves the state so no progress is lost. If the departures make the conflict moot (e.g., the disputed resource is no longer shared), the process concludes with documentation.
