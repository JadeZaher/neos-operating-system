# Layer VI: Conflict and Repair

Conflict is not a system failure. It is the signal that governance structures need attention. Layer VI provides the structural protocols that transform conflict into governance improvement -- without coercive authority, punitive mechanisms, or forced reconciliation.

## Purpose

Every governance system generates conflict. The question is not whether conflict will occur but whether the system has structural pathways to address it. Systems without explicit conflict protocols develop implicit ones -- usually dominated by whoever has the most social capital, the loudest voice, or the willingness to escalate furthest. Layer VI replaces implicit conflict dynamics with explicit, structured, consent-based processes.

## Distinction from Layer V

Layer V (Polycentric Governance) handles **structural disputes between AZPOs** -- conflicts about authority boundaries, resource allocation between units, and domain overlap. Layer VI handles **interpersonal harm, intra-AZPO disputes, behavioral conflicts, skill-gap tensions, and community-affecting incidents**. The boundary is clear: if the dispute is about which AZPO has authority over a domain, it belongs in Layer V. If the dispute is about how people within or across AZPOs treat each other, it belongs in Layer VI.

## Three-Tier Escalation Model

Layer VI implements a graduated escalation model inspired by Laloux's Teal three-level approach:

```
Tier 1: Direct Dialogue
  Parties resolve directly, with optional NVC support.
  Low severity, limited scope, no safety concern.
       |
       | (unresolved or insufficient)
       v
Tier 2: Coaching Intervention
  Skill-gap conflicts receive targeted coaching.
  Root cause is competency, not values or intent.
       |
       | (not a skill gap, or harm occurred)
       v
Tier 3: Harm Circle
  Facilitated restorative circle for harm repair.
  Pattern of behavior, agreement breach, or trust damage.
       |
       | (systemic impact beyond direct parties)
       v
Tier 4: Community Impact Assessment
  AZPO-wide or ecosystem-wide processing of systemic patterns.
  Structural gaps revealed, governance changes recommended via ACT.
```

The escalation-triage skill determines which tier applies. Parties are never forced into a higher tier than they consent to, but the triager documents cases where a lower tier is chosen against recommendation.

## Skill Index

| Skill | Purpose | Priority |
|-------|---------|----------|
| [harm-circle](harm-circle/SKILL.md) | Convene restorative circles to address harm and produce repair agreements | P0 |
| [nvc-dialogue](nvc-dialogue/SKILL.md) | Apply Nonviolent Communication in high-tension governance conversations | P0 |
| [escalation-triage](escalation-triage/SKILL.md) | Assess and route conflicts to the appropriate resolution tier | P0 |
| [repair-agreement](repair-agreement/SKILL.md) | Formalize conflict outcomes into trackable, versioned governance agreements | P1 |
| [coaching-intervention](coaching-intervention/SKILL.md) | Design coaching responses for skill-gap conflicts | P1 |
| [community-impact-assessment](community-impact-assessment/SKILL.md) | Process systemic harm patterns and generate governance change recommendations | P2 |

## Theoretical Foundations

- **Transformative Justice**: Responds to harm without relying on state mechanisms. The community takes responsibility for addressing the conditions that allowed harm to occur.
- **Restorative Justice**: Centers the experience of the person harmed. The goal is repair of relationships, trust, and conditions -- not punishment.
- **Nonviolent Communication (Marshall Rosenberg)**: Separates observations from evaluations, feelings from thoughts, needs from strategies, and requests from demands.
- **Ostrom Principle 6**: Conflict resolution mechanisms must be low-cost, accessible, and fast relative to the stakes.
- **Laloux Teal Escalation**: Direct dialogue between parties, then peer mediation, then panel. Graduated approach respects parties' ability to resolve their own conflicts.

## Design Decisions

**Harm-centered framing.** All conflict skills center the experience of the person harmed. The person harmed has primary voice in defining what repair looks like. No one can tell the person harmed that their experience is invalid.

**No forced reconciliation.** No one can be compelled to forgive or reconcile. Repair of the governance system does not require personal reconciliation. The system repairs structural trust; individuals choose whether to repair personal trust.

**Coaching as a distinct pathway.** Skill gaps are not character flaws. When someone disrupts governance due to a lack of facilitation skills, the appropriate response is coaching, not a restorative circle. Conflating skill gaps with values conflicts erodes trust in both processes.

**Repair agreements as governance artifacts.** Repair outcomes are tracked, versioned, and reviewable like any other agreement. They are registered in the agreement registry and follow the same lifecycle as other agreements.

**Privacy protection.** What is documented: process, agreements, systemic findings. What is kept private: personal disclosures, emotional processing, individual statements (unless the person consents). Community impact assessments explicitly separate systemic analysis from individual details.

**No coercive authority.** No skill in this layer imposes outcomes on non-consenting parties. Harm circles produce repair agreements by consent. Coaching is voluntary. Community impact assessments produce recommendations that route through ACT, not mandates.

## Cross-Layer References

| Referenced Skill | Layer | How It Connects |
|-----------------|-------|-----------------|
| agreement-creation | I | Repair agreements are created as governance agreements |
| agreement-registry | I | Repair agreements are registered and tracked |
| agreement-amendment | I | Community impact assessment recommendations may amend existing agreements |
| act-consent-phase | III | Governance change recommendations route through ACT |
| proposal-creation | III | Systemic findings become formal proposals |
| role-assignment | II | Coaches, facilitators, and triagers are assigned roles with scoped authority |
| role-assignment | II | Authority boundaries for all conflict roles are defined |
| domain-mapping | II | Conflict scope is verified against domain boundaries |
| polycentric-conflict-navigation | V | Layer V handles structural inter-AZPO disputes; Layer VI handles interpersonal |

## File Structure

```
layer-06-conflict/
  README.md                                   # This file
  harm-circle/
    SKILL.md                                  # Restorative circle process
    assets/harm-circle-template.yaml          # Circle record template
  nvc-dialogue/
    SKILL.md                                  # NVC communication protocol
  escalation-triage/
    SKILL.md                                  # Conflict routing and assessment
    assets/triage-assessment-template.yaml    # Triage record template
  repair-agreement/
    SKILL.md                                  # Repair agreement formalization
    assets/repair-agreement-template.yaml     # Agreement template
  coaching-intervention/
    SKILL.md                                  # Skill-gap coaching process
    assets/coaching-plan-template.yaml        # Coaching plan and outcome template
  community-impact-assessment/
    SKILL.md                                  # Systemic impact processing
    assets/impact-assessment-template.yaml    # Assessment report template
```
