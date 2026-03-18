# Specification: Layer VI -- Conflict and Repair

## Track ID
`conflict_repair_20260302`

## Overview

This track builds **Layer VI (Conflict and Repair)** of the NEOS governance stack: the skill layer that governs how harm is addressed, conflicts are resolved, and relationships are repaired within and across ETHOS -- all without coercive authority, punitive mechanisms, or forced reconciliation. The layer encompasses restorative harm circles, NVC-grounded dialogue, formalized repair agreements, escalation triage, coaching interventions, and community impact assessment.

Conflict is not a system failure. It is the signal that governance structures need attention. This layer treats conflict as diagnostic information rather than deviant behavior, and provides structural protocols that transform conflict into governance improvement.

**Total skills:** 6
**Layers:** VI (Conflict and Repair)
**Dependencies:** foundation_20260301 (Layers I, III), authority_role_20260302 (Layer II)

## Background

### Why Conflict and Repair Is a Governance Layer

Every governance system generates conflict. The question is not whether conflict will occur but whether the system has structural pathways to address it. Systems without explicit conflict protocols develop implicit ones -- usually dominated by whoever has the most social capital, the loudest voice, or the willingness to escalate furthest. NEOS replaces implicit conflict dynamics with explicit, structured, consent-based processes.

This layer is distinct from Layer V's polycentric-conflict-navigation, which handles structural disputes between ETHOS about authority, agreements, and resources. Layer VI handles interpersonal harm, intra-ETHOS disputes, behavioral conflicts, skill-gap tensions, and community-affecting incidents.

### Theoretical Foundations

**Transformative Justice (TJ):** Responds to harm without relying on state mechanisms (police, courts, prisons). Emphasizes community accountability -- the community takes responsibility for addressing the conditions that allowed harm to occur, not just the individual who caused it. TJ asks: what conditions created this harm, and how do we change those conditions? This maps directly to NEOS's "solutionary culture" orientation.

**Restorative Justice:** Centers the experience of the person harmed. The goal is repair -- of relationships, of trust, of the conditions that allowed harm -- not punishment. Restorative circles bring together the person harmed, the person who caused harm, and affected community members to collectively determine what repair looks like.

**Nonviolent Communication (NVC -- Marshall Rosenberg):** A communication framework based on observations (not evaluations), feelings, needs, and requests. NVC is particularly valuable in high-tension governance conversations where participants conflate their feelings about a situation with structural observations about governance processes.

**Ostrom Principle 6 -- Accessible Conflict Resolution:** Conflict resolution mechanisms must be low-cost, accessible, and fast relative to the stakes. If conflict resolution is bureaucratic, slow, or requires specialized expertise, people will avoid it and conflicts will fester.

**Teal Three-Level Escalation (Frederic Laloux):** Direct dialogue between parties, then peer mediation if direct dialogue fails, then panel if mediation fails. This graduated approach respects the parties' ability to resolve their own conflicts before involving the broader community.

### OmniOne Context

OmniOne's "Solutionary Culture" framework orients all conflict toward finding better solutions rather than assigning blame. The field agreement establishes "Mutual Purpose and Mutual Respect" as foundational commitments. Key OmniOne-specific mechanisms:

- **Coaching as distinct from mediation:** When conflict stems from a skill gap rather than a values conflict, coaching is the appropriate intervention -- not a restorative circle. A member who disrupts meetings because they lack facilitation skills needs coaching, not conflict resolution.
- **"All but one by consensus can remove someone":** The extreme measure in OmniOne governance. This is a structural safeguard of last resort, not a normal conflict outcome. It requires near-unanimous consensus and is fundamentally different from majority-vote removal.
- **Relocation process:** When a member cannot work with their team, relocation to another circle or ETHOS is explored before any discussion of removal. The system seeks fit, not punishment.

### Design Principles for This Layer

**Use:** Three-tier escalation without coercive authority (direct dialogue, peer mediation, facilitated panel). Harm-centered framing (start from the experience of the person harmed). Community as affected party (harm to individuals affects the community's trust and agreements). Repair agreements as governance artifacts (repair outcomes are tracked, versioned, and reviewable like any other agreement). Coaching escalation as a distinct pathway for skill-gap conflicts.

**Avoid:** Forced reconciliation (no one can be compelled to forgive or reconcile -- repair of the governance system does not require personal reconciliation). Anonymous complaints without follow-through (anonymous reports must still be investigated, but anonymity does not create obligation to act without verification). Punitive framing in restorative language (using restorative circle structure to impose punishment). Expertise gatekeeping (conflict resolution should not require certified professionals for most cases -- Ostrom's accessibility principle).

---

## Functional Requirements

### FR-1: Harm Circle (`harm-circle`)

**Description:** Convene and facilitate restorative circles to address harm within the ecosystem. Harm circles bring together the person harmed, the person who caused harm (if willing), and affected community members to understand what happened, identify needs, and determine repair actions. The process centers the experience of the person harmed while maintaining structural accountability.

**Acceptance Criteria:**
- AC-1.1: The skill defines all required inputs (harm report, affected parties, convener identity, facilitation plan, safety assessment for the person harmed).
- AC-1.2: The step-by-step process covers preparation (individual conversations with all parties before the circle), circle facilitation (structured rounds: what happened, how it affected people, what is needed for repair), repair agreement drafting, and follow-up.
- AC-1.3: The output artifact is a harm circle record documenting the process (not private disclosures), the repair agreement, and the follow-up schedule.
- AC-1.4: The authority boundary check ensures the facilitator has process authority only (managing the circle), not outcome authority (determining the repair). The circle cannot impose sanctions or punishments -- only repair agreements that all parties consent to.
- AC-1.5: The capture resistance check addresses scenarios where the person who caused harm is a high-status community member, where the harm circle is weaponized for interpersonal revenge, and where pressure is applied to the person harmed to accept insufficient repair.
- AC-1.6: An OmniOne walkthrough demonstrates a harm circle convened after a TH member's contributions were repeatedly dismissed in circle meetings, including the preparation conversations, the circle itself, and the repair agreement.
- AC-1.7: All 7 stress-test scenarios documented with full narrative results.

**Priority:** P0 -- Anchor skill for conflict and repair.

### FR-2: NVC Dialogue (`nvc-dialogue`)

**Description:** Apply Nonviolent Communication principles in high-tension governance conversations. This skill is a communication protocol that can be applied within any governance interaction -- harm circles, ACT processes, cross-ETHOS negotiations, or informal conflict. It teaches the structural distinction between observations and evaluations, feelings and thoughts, needs and strategies, and requests and demands.

**Acceptance Criteria:**
- AC-2.1: The skill defines the four NVC components (observation, feeling, need, request) with governance-specific examples showing how each transforms a governance conversation.
- AC-2.2: The step-by-step process covers NVC application in three contexts: conflict dialogue (two parties in tension), group facilitation (circle discussion with emerging conflict), and written communication (proposals, feedback, objections).
- AC-2.3: The output artifact is an NVC dialogue record documenting the observations, feelings, needs, and requests surfaced, plus any agreements reached.
- AC-2.4: The authority boundary check ensures NVC facilitators cannot use the framework to invalidate participants' experiences ("you are evaluating, not observing" used to dismiss legitimate concerns).
- AC-2.5: The capture resistance check addresses NVC being used as a tone-policing mechanism (requiring NVC compliance as a precondition for being heard) and charismatic communicators using NVC fluency to dominate conversations.
- AC-2.6: An OmniOne walkthrough demonstrates NVC dialogue applied to a heated ACT consent phase where an AE member feels their objection is being dismissed as "blocking progress."
- AC-2.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Communication foundation for all other conflict skills.

### FR-3: Repair Agreement (`repair-agreement`)

**Description:** Formalize conflict outcomes into trackable, versioned governance agreements. When a harm circle, mediation, coaching intervention, or direct dialogue produces an outcome, the repair agreement skill transforms that outcome into a proper agreement with clear commitments, timelines, review dates, and accountability structures. Repair agreements are registered in the agreement registry like any other agreement.

**Acceptance Criteria:**
- AC-3.1: The skill defines repair agreement types (behavioral commitment, structural change, resource restitution, role adjustment, relationship boundary, community practice change) with requirements for each.
- AC-3.2: The step-by-step process covers agreement drafting (from conflict resolution outcome), consent from all parties, registration in agreement registry, follow-up check-ins, and completion or renewal.
- AC-3.3: The output artifact is a versioned repair agreement with unique ID, parties, commitments, timelines, follow-up schedule, completion criteria, and link to the originating conflict process.
- AC-3.4: The authority boundary check ensures repair agreements cannot impose obligations on non-consenting parties and cannot override existing agreements without going through the amendment process.
- AC-3.5: The capture resistance check addresses scenarios where repair agreements are used to extract ongoing concessions from the person who caused harm, and where powerful parties negotiate repair agreements that protect their position.
- AC-3.6: An OmniOne walkthrough demonstrates a repair agreement formalized after a coaching intervention: a circle steward who was making unilateral decisions commits to specific consultation practices, with check-ins at 30, 60, and 90 days.
- AC-3.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on FR-1 and FR-2 establishing the conflict resolution processes that produce repair outcomes.

### FR-4: Escalation Triage (`escalation-triage`)

**Description:** Assess which tier of conflict protocol applies to a given situation. Not every conflict needs a harm circle. Some conflicts are best resolved through direct dialogue. Some are skill-gap issues requiring coaching, not mediation. Some affect the entire community and require broader assessment. This skill provides a triage framework that routes conflicts to the appropriate tier and process.

**Acceptance Criteria:**
- AC-4.1: The skill defines the triage dimensions (severity, scope of impact, parties involved, root cause type, urgency, safety considerations) with decision criteria for each.
- AC-4.2: The step-by-step process covers intake (receiving a conflict report or observation), assessment (evaluating triage dimensions), routing recommendation (which tier and process), and handoff to the appropriate skill.
- AC-4.3: The output artifact is an escalation triage record documenting the situation assessment, triage dimensions evaluated, routing decision, and rationale.
- AC-4.4: The authority boundary check ensures the triager has assessment and recommendation authority but cannot override the affected parties' preferences for process (if parties want direct dialogue, the triager cannot force them into a harm circle).
- AC-4.5: The capture resistance check addresses triagers consistently routing conflicts involving powerful members to lower tiers (minimizing) and triagers routing conflicts involving marginalized members to higher tiers (dramatizing).
- AC-4.6: An OmniOne walkthrough demonstrates the triage process for three different situations: a minor disagreement between two TH members (routed to direct dialogue), a recurring pattern of one AE member dominating meetings (routed to coaching-intervention), and a breach of the field agreement by an OSC member (routed to harm-circle with community-impact-assessment).
- AC-4.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Required for routing. Built alongside FR-1 and FR-2 so the triage can reference the processes it routes to.

### FR-5: Coaching Intervention (`coaching-intervention`)

**Description:** Design coaching responses for conflicts that stem from skill gaps rather than values conflicts or intentional harm. When a participant disrupts governance processes due to lack of facilitation skills, communication skills, or governance knowledge, the appropriate response is coaching rather than a restorative circle. This skill defines how coaching needs are identified, coaches are selected, coaching plans are designed, and outcomes are assessed.

**Acceptance Criteria:**
- AC-5.1: The skill defines the distinction between coaching-eligible conflicts (skill gap, knowledge gap, behavioral pattern without harm intent) and non-coaching conflicts (intentional harm, values conflict, structural dispute) with clear decision criteria.
- AC-5.2: The step-by-step process covers coaching need identification (often from escalation triage), coach selection (someone with relevant skills, not the person's direct authority), coaching plan design (specific skills to develop, timeline, check-ins), coaching execution, and outcome assessment.
- AC-5.3: The output artifact is a coaching plan and outcome report documenting the identified gaps, the coaching approach, check-in results, and assessment of whether the gaps have been addressed.
- AC-5.4: The authority boundary check ensures coaching is voluntary (a participant cannot be forced to accept coaching) but the consequences of declining coaching when it was recommended can be defined (the underlying conflict remains unresolved and may escalate through normal channels).
- AC-5.5: The capture resistance check addresses coaching being used as a soft punishment ("you need coaching" as a status demotion), coaches imposing their own governance preferences rather than building skills, and coaching recommendations being consistently directed at marginalized members.
- AC-5.6: An OmniOne walkthrough demonstrates a coaching intervention for an AE member whose circle stewardship style is too directive: they make decisions without consulting their circle, not from malice but from a previous organizational culture where stewards decided unilaterally. Walk through the full coaching arc from identification to behavioral change.
- AC-5.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on FR-4 (escalation triage) to route conflicts to coaching.

### FR-6: Community Impact Assessment (`community-impact-assessment`)

**Description:** Facilitate ETHOS-wide or ecosystem-wide processing of conflicts that affect the broader community, not just the directly involved parties. When harm occurs that shakes community trust, when a pattern of conflict reveals systemic issues, or when a repair agreement has implications for how the community operates, this skill provides a structured process for the community to process the impact, identify systemic changes needed, and integrate those changes into governance.

**Acceptance Criteria:**
- AC-6.1: The skill defines the triggers for community impact assessment (harm affecting more than the direct parties, pattern of similar conflicts, conflict revealing a structural gap, repair agreement with community-wide implications).
- AC-6.2: The step-by-step process covers assessment convening (who calls it, who participates, what is shared and what is kept private), community processing session (structured dialogue about impact, not about blame), systemic analysis (what conditions created this situation), recommendation generation (governance changes, agreement amendments, structural modifications), and routing recommendations through ACT.
- AC-6.3: The output artifact is a community impact assessment report documenting the impact scope, community processing outcomes, systemic findings, and recommended governance changes with links to the relevant ACT processes for implementing them.
- AC-6.4: The authority boundary check ensures the assessment process cannot override the privacy of individuals involved in the underlying conflict (what was disclosed in a harm circle stays in the harm circle -- the community assessment addresses the systemic impact, not private details).
- AC-6.5: The capture resistance check addresses the assessment being used to re-litigate an already-resolved conflict, powerful community members steering systemic findings to protect their interests, and assessment fatigue (too many assessments diluting their impact).
- AC-6.6: An OmniOne walkthrough demonstrates a community impact assessment convened after a pattern of three similar conflicts revealed that the AE circle's decision-making process had a structural gap -- proposals were being consented to without adequate advice phases. Walk through the community processing, the systemic finding, and the resulting governance amendment proposal routed through ACT.
- AC-6.7: All 7 stress-test scenarios documented.

**Priority:** P2 -- The most complex skill, depends on all other Layer VI skills being operational.

---

## Non-Functional Requirements

### NFR-1: No Coercive Authority

No skill in this layer may impose outcomes on non-consenting parties. Harm circles produce repair agreements by consent. Coaching is voluntary. Community impact assessments produce recommendations that route through ACT, not mandates. The only exception is the "all but one by consensus" removal process, which is a structural safeguard of last resort documented in the authority layer, not a conflict resolution mechanism.

### NFR-2: Harm-Centered Framing

All conflict skills must center the experience of the person harmed. This means: the person harmed has primary voice in defining what repair looks like, no one can tell the person harmed that their experience is invalid, and repair agreements must address the harm described by the person harmed (not only the harm acknowledged by the person who caused harm).

### NFR-3: Privacy Protection

Conflict processes involve sensitive personal information. Each skill must define what is documented (process, agreements, systemic findings) and what is kept private (personal disclosures, emotional processing, individual statements unless the person consents to their inclusion). Community impact assessments must explicitly address the boundary between systemic analysis and private details.

### NFR-4: Modularity

Each skill must function independently. A participant or AI agent reading a single SKILL.md must be able to understand and execute the described process without requiring other Layer VI skills to be loaded.

### NFR-5: Line Limit

Each SKILL.md must be under 500 lines. Supporting material (NVC guides, harm circle facilitation guides, coaching frameworks) goes in `references/` or `assets/`.

### NFR-6: Portability

Every skill is NEOS-generic at its structural level. OmniOne-specific details (Solutionary Culture, field agreement, specific removal processes) appear as clearly marked examples and configuration blocks.

### NFR-7: Accessibility

Following Ostrom Principle 6, conflict resolution must be low-cost, accessible, and fast relative to the stakes. Skills must not require certified professionals for routine operation (though expertise is available for complex cases). The triage process must not create a bureaucratic barrier to accessing conflict resolution.

### NFR-8: Validation

Every SKILL.md must pass automated validation via `scripts/validate_skill.py`.

---

## User Stories

### US-1: Participant Seeks Repair After Harm
**As** a TH member whose contributions have been repeatedly dismissed in circle meetings,
**I want** a structured process where I can describe the harm, have it acknowledged, and agree on repair actions,
**So that** I can continue participating without the pattern repeating.

**Given** the member has experienced a pattern of harm,
**When** they request a harm circle through the escalation triage process,
**Then** a facilitated circle is convened, repair actions are agreed upon, and follow-up is scheduled.

### US-2: AI Agent Assists NVC Dialogue
**As** an AI agent assisting a participant in a high-tension governance conversation,
**I want** to help the participant distinguish observations from evaluations and needs from strategies,
**So that** the conversation can stay productive rather than escalating into blame.

**Given** a governance conversation is becoming heated,
**When** the AI agent applies the nvc-dialogue skill,
**Then** it can help the participant reframe their communication in observation/feeling/need/request format.

### US-3: Facilitator Triages a Conflict
**As** a circle facilitator who has received a conflict report,
**I want** a clear triage framework that tells me whether this needs direct dialogue, coaching, a harm circle, or a community assessment,
**So that** I can route the conflict to the appropriate process without over- or under-responding.

**Given** a conflict report has been received,
**When** the facilitator applies the escalation-triage skill,
**Then** they receive a clear routing recommendation with rationale for the appropriate tier and process.

### US-4: Coach Addresses a Skill Gap
**As** a member identified as needing coaching for governance skills,
**I want** a coaching process that respects my autonomy, focuses on building specific skills, and does not feel like punishment,
**So that** I can improve my participation without stigma.

**Given** the escalation triage has identified a coaching need,
**When** the coaching-intervention skill is applied,
**Then** a voluntary coaching plan is designed with clear skill targets, timeline, and check-ins.

### US-5: Community Processes Systemic Impact
**As** a TH member aware of a pattern of similar conflicts in our ETHOS,
**I want** a structured process for the community to examine what systemic conditions created the pattern,
**So that** governance changes can be proposed through ACT rather than the same conflicts recurring.

**Given** a pattern of similar conflicts has been identified,
**When** the community-impact-assessment skill is applied,
**Then** systemic findings are documented and governance change recommendations are routed through ACT.

### US-6: Ecosystem Architect Configures Conflict Protocols
**As** an ecosystem architect adapting NEOS for a new community,
**I want** conflict and repair skills that are generic enough to configure for my community's values and practices,
**So that** I can establish conflict resolution without importing OmniOne-specific cultural frameworks.

**Given** the architect has a community with different conflict resolution traditions,
**When** they review the Layer VI skills and replace OmniOne example blocks,
**Then** the skills function correctly with their community's conflict resolution configuration.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-06-conflict/
    README.md
    harm-circle/
      SKILL.md
      assets/
        harm-circle-template.yaml
        preparation-guide.md
      references/
        restorative-justice-primer.md
      scripts/
    nvc-dialogue/
      SKILL.md
      assets/
        nvc-reference-card.md
        dialogue-record-template.yaml
      references/
      scripts/
    repair-agreement/
      SKILL.md
      assets/
        repair-agreement-template.yaml
      references/
      scripts/
    escalation-triage/
      SKILL.md
      assets/
        triage-assessment-template.yaml
        triage-decision-matrix.yaml
      references/
      scripts/
    coaching-intervention/
      SKILL.md
      assets/
        coaching-plan-template.yaml
        coaching-outcome-template.yaml
      references/
      scripts/
    community-impact-assessment/
      SKILL.md
      assets/
        impact-assessment-template.yaml
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name
description: "Pushy description..."
layer: 6
version: 0.1.0
depends_on: []
---
```

### Build Order Rationale

Skills are built to establish the foundational processes before the routing and integration skills:
1. `harm-circle` -- Anchor skill, defines the core restorative process
2. `nvc-dialogue` -- Communication foundation used by all other skills
3. `escalation-triage` -- Routes conflicts to appropriate processes (requires knowing what processes exist)
4. `repair-agreement` -- Formalizes outcomes from harm circles and other processes
5. `coaching-intervention` -- Distinct pathway for skill-gap conflicts (requires triage to route to it)
6. `community-impact-assessment` -- Broadest scope, requires all other processes to be defined

### Cross-Layer References

Each skill will reference skills from earlier layers:
- `agreement-creation` -- Repair agreements are agreements
- `agreement-registry` -- Repair agreements are registered
- `act-consent-phase` -- Community impact assessment recommendations route through ACT
- `authority-assignment` -- Facilitators, coaches, and triagers are roles with scoped authority
- `proposal-creation` -- Systemic change recommendations become proposals

For Layer V interaction:
- `polycentric-conflict-navigation` -- Layer V handles structural inter-ETHOS conflicts; Layer VI handles interpersonal and intra-ETHOS conflicts. Clear boundary between the two.

---

## Out of Scope

- **Specific OmniOne removal processes** -- The "all but one by consensus" removal mechanism is referenced as context but not designed in this layer. Removal authority belongs to Layer II.
- **Therapeutic or clinical services** -- The skills define governance conflict resolution, not therapy. When a conflict involves mental health needs beyond governance scope, the skill should note the limitation and suggest referral to appropriate support.
- **Legal dispute resolution** -- NEOS conflict resolution is non-sovereign. When conflicts have legal implications, the skills should note the boundary between governance resolution and legal proceedings.
- **Layer VII (Safeguard) integration** -- Systemic capture detection that involves conflict patterns is referenced but belongs to Layer VII.
- **Training curriculum** -- The skills define what NVC dialogue and harm circle facilitation look like, not a training program for developing these capacities.

---

## Open Questions

1. **Mandatory vs. voluntary harm circles**: Can a harm circle be required, or is it always voluntary for all parties? Recommendation: voluntary for the person who caused harm (they cannot be compelled to attend), but the harm circle can proceed without them with appropriate modifications. The person harmed always has the choice of whether to participate.

2. **Confidentiality scope in community impact assessments**: How much detail from individual conflicts can be shared in community-wide processing? Recommendation: systemic patterns and structural findings are shared, individual identities and private disclosures are not, unless the individuals consent.

3. **Coach qualification requirements**: Must coaches have formal training, or can peer coaching be sufficient? Recommendation: peer coaching is sufficient for most governance skill gaps (Ostrom accessibility principle), with formal coach involvement available for complex cases. Define a minimum preparation guide in `references/`.

4. **Repair agreement enforcement**: What happens when a party does not fulfill their repair agreement commitments? Recommendation: graduated response (reminder, check-in conversation, agreement review, escalation to next conflict tier). Repair agreements cannot be enforced through coercive means.

5. **Relocation vs. removal boundary**: When does a "cannot work with this team" situation cross from relocation to removal consideration? Recommendation: relocation is always explored first. Removal consideration requires documented evidence that the member cannot work with any available team/circle, not just the current one. This boundary is defined in Layer II but referenced here.
