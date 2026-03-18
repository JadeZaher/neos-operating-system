# Specification: Authority & Role Layer (Layer II)

## Track ID
`authority_role_20260302`

## Overview

This track builds **Layer II (Authority & Role)** of the NEOS governance stack: the layer that defines how authority is scoped, how roles are created and assigned, and how domain boundaries are maintained. Every other NEOS layer references authority and roles but the foundation track (Layer I + Layer III) deferred their formal definition. Without Layer II, authority scopes are stated ad-hoc within each skill, creating inconsistency risk -- a structural weakness identified in the foundation track review. This track resolves that weakness by providing the canonical authority model that all other layers reference.

The primary framework is **Sociocracy 3.0's domain model** with its 11-element domain contract: purpose, key responsibilities, customers, deliverables, dependencies, constraints, challenges, resources, delegator responsibilities, competencies, metrics, and evaluation schedule. Secondary influences are **Holacracy** (role does not equal person, blanket authority within scope, governance meetings for role/policy updates) and **Laloux Teal** (advice process, authority flows to expertise).

This track produces 7 governance skills, supporting asset templates, and an authority integration phase that updates the foundation skills to reference the now-formal authority model.

## Background

### Why Authority & Role Is Next

The foundation track review (foundation_20260301) identified a critical structural weakness: "Each skill independently defines authority model -- risk of inconsistency." The review also flagged that the "domain concept is used everywhere but never formally defined (Layer II dependency)." Additionally, the inactive member protocol (1-month no-show rule from OmniOne source docs), onboarding consent ceremony, and member status transitions were all deferred to Layer II. These are not optional features -- they are load-bearing structural elements that the foundation layer assumes exist.

Layer II occupies position 2 in the workflow track ordering because agreements and decisions (Layers I and III) cannot function reliably without formal authority scopes. A participant cannot know whether they have the right to create an agreement, propose a change, or consent to a decision without knowing their domain boundaries.

### Design Patterns (From Research)

**Domain-as-contract**: Authority is not a vague grant. It is a structured contract with 11 defined elements. If an element is missing, the domain is incomplete and must be refined before authority is exercised.

**Blanket authority within scope**: Within their domain, a steward has full authority to act without seeking permission. This eliminates the anti-pattern of permission-seeking default, where every action requires upward approval.

**Advice process**: Authority holders seek advice from those impacted before making domain-internal decisions. Advice is non-binding but must be demonstrably sought. This connects directly to the ACT Engine's Advice phase.

**Evaluation cadence**: Every domain has a scheduled review. Authority does not become permanent by default. This connects to the agreement-review skill's expiry model.

**Separation of role and person**: A role is a structural element with defined authority. A person is assigned to a role but is not the role. Multiple people can share a role. One person can hold multiple roles. When a person leaves, the role persists and is reassigned.

### Anti-Patterns to Guard Against

**Permission-seeking default**: If every action requires approval from above, the system collapses into hierarchy. Layer II must make blanket authority the norm, not the exception.

**Undifferentiated domains**: If domains overlap without explicit negotiation, authority disputes become personal conflicts. The authority-boundary-negotiation skill addresses this directly.

**Permanent role tenure**: Without review cycles, roles accumulate to individuals who hold them longest. The domain-review and role-sunset skills prevent this.

**Authority creep by precedent**: When someone exercises authority beyond their domain and no one objects, the expanded scope becomes assumed. The domain-mapping skill's constraint element and the domain-review cycle catch this.

### OmniOne Specifics

- **Councils**: Town Hall (TH), Agents of the Ecosystem (AE), OMNI Steward Council (OSC), Green Earth Vision (GEV)
- **Current-Sees**: Influence currencies -- explicitly NOT attached to roles. 111 per person, equal when affected. (Current-Sees are deferred to Layer IV; this track must ensure roles do not grant Current-See advantages.)
- **Inactive member protocol**: 1 month of no participation triggers inactive status. Inactive members lose active decision-making participation but retain their agreements and can reactivate.
- **Access levels**: Builders have commenting access. Co-creators have editing access. These are role-adjacent but defined by member profile, not by domain authority.
- **Trunk Council**: Temporary key-holding body during OmniOne's formation phase. Holds authority that will be distributed as the ecosystem matures. Must be modeled as a time-limited domain with explicit sunset.
- **Profiles**: Co-creator, Builder, Collaborator, TownHall -- these are participation tiers, not roles in the S3 sense. The member-lifecycle skill must distinguish between profiles (participation level) and roles (authority scope).

---

## Functional Requirements

### FR-1: Domain Mapping (`domain-mapping`)

**Description:** Enable any authorized body to define or refine a domain using the 11-element S3 domain contract. This is the anchor skill for Layer II -- it establishes what a domain looks like structurally and provides the canonical schema that all other authority-related skills reference. A domain is the invisible boundary within which a circle or steward can make decisions.

**Acceptance Criteria:**
- AC-1.1: The skill defines all 11 domain elements with clear descriptions: purpose, key responsibilities, customers (who the domain serves), deliverables, dependencies (on other domains), constraints (what the domain CANNOT do), challenges (known risks), resources (what the domain can draw on), delegator responsibilities (what the body that created this domain owes it), competencies (what the steward needs), metrics (how effectiveness is measured), and evaluation schedule.
- AC-1.2: The step-by-step process covers both new domain creation and domain refinement for an existing role or circle.
- AC-1.3: The output artifact is a complete domain contract document with all 11 elements filled.
- AC-1.4: The authority boundary check specifies who can create domains (a delegating body through an ACT consent process) and who can modify them (the delegating body or the domain holder through the domain-review cycle).
- AC-1.5: The capture resistance check addresses authority creep -- a domain holder gradually expanding their scope beyond what was defined, relying on precedent rather than formal amendment.
- AC-1.6: An OmniOne walkthrough demonstrates defining the domain for a new Economics circle within the AE, showing all 11 elements filled with concrete OmniOne content.
- AC-1.7: All 7 stress-test scenarios are documented with full narrative results.

**Priority:** P0 -- Anchor skill, built first. Every other Layer II skill depends on knowing what a domain looks like.

### FR-2: Authority Boundary Negotiation (`authority-boundary-negotiation`)

**Description:** Resolve overlapping or ambiguous domain boundaries between two or more roles or circles through structured integrative discussion. When two domains claim authority over the same area, this skill provides the process for negotiating a clear boundary without defaulting to hierarchy or informal power.

**Acceptance Criteria:**
- AC-2.1: The skill defines trigger conditions: explicit boundary dispute, ambiguity discovered during an ACT process, overlap flagged during domain-review, conflict arising from competing domain claims.
- AC-2.2: The step-by-step process includes: identifying the specific overlap, convening affected domain holders, mapping each domain's claim using the 11-element contract, identifying the structural source of overlap (shared responsibility, unclear constraint, missing dependency), integrative discussion to find a resolution that preserves both domains' core purposes, formal amendment of the affected domain contracts.
- AC-2.3: The output artifact is a boundary resolution record documenting the overlap, the discussion, the resolution, and the amended domain contracts.
- AC-2.4: The failure containment logic defines escalation when integrative discussion fails -- the dispute routes to the delegating body that created the overlapping domains, or to GAIA Level 4 (Coaching) if the delegating bodies themselves conflict.
- AC-2.5: The capture resistance check addresses power asymmetry -- a larger or more established domain pressuring a smaller one to cede territory.
- AC-2.6: An OmniOne walkthrough demonstrates a boundary dispute between the Economics circle and the Stewardship circle over who has authority to approve resource allocation above a certain threshold.
- AC-2.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Required immediately after domain-mapping to handle the inevitable overlaps that arise when domains are first defined.

### FR-3: Role Assignment (`role-assignment`)

**Description:** Assign a person to a defined role (domain) with scoped authority. The skill enforces the separation of role and person: the domain exists independently, and a person is assigned as its steward. Assignment requires consent from the assigning body and acceptance by the assignee.

**Acceptance Criteria:**
- AC-3.1: The skill defines required inputs: the domain contract (from domain-mapping), the candidate person, the assigning body, the assignment duration (default: until next domain-review), and any role-specific onboarding requirements.
- AC-3.2: The step-by-step process includes: verify domain contract is complete, verify candidate meets competency requirements (section K of domain contract), candidate reviews the domain contract and accepts or negotiates, assigning body runs a consent process (or consensus for OSC-level roles), assignment is registered with start date and review date.
- AC-3.3: The output artifact is a role assignment record linking a person to a domain contract with a defined term.
- AC-3.4: The authority boundary check specifies that only the delegating body (the body that created the domain) can assign its steward. Self-assignment is not permitted. Dual-role holding is permitted but must be flagged for conflict-of-interest review.
- AC-3.5: The capture resistance check addresses: role accumulation by a single person (maximum role count per person, recommended cap defined per ecosystem), and informal role-holding (someone acting as steward without formal assignment).
- AC-3.6: An OmniOne walkthrough demonstrates assigning a Co-creator to the newly defined Economics circle steward role, including competency verification and the consent round.
- AC-3.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Domains are useless without people assigned to steward them.

### FR-4: Role Transfer (`role-transfer`)

**Description:** Hand off a role from one steward to another without losing continuity. Transfer includes knowledge transfer, authority handover, pending commitment inventory, and formal re-assignment through the assigning body.

**Acceptance Criteria:**
- AC-4.1: The skill defines transfer triggers: voluntary step-down, scheduled rotation, domain-review recommendation, inactive status of current steward, role-sunset decision that creates a successor role.
- AC-4.2: The step-by-step process includes: outgoing steward creates a handover document (pending commitments, active agreements held, decision context, relationship map), incoming steward reviews domain contract and handover, overlap period (recommended: 2 weeks minimum), assigning body consents to the transfer, formal reassignment with updated registry entry.
- AC-4.3: The output artifact is a transfer record documenting: outgoing steward, incoming steward, handover document summary, pending commitments transferred, consent record from assigning body.
- AC-4.4: The failure containment logic addresses: involuntary transfer (steward objects to being replaced -- routes to authority-boundary-negotiation or GAIA escalation), no qualified successor (domain enters "vacant" status with temporary stewardship by delegating body), incomplete handover (mandatory minimum handover checklist before transfer is finalized).
- AC-4.5: An OmniOne walkthrough demonstrates a scheduled rotation of the OSC meeting facilitator role, including the 2-week overlap period and the handover of pending agenda items.
- AC-4.6: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on role-assignment existing.

### FR-5: Domain Review (`domain-review`)

**Description:** Run a scheduled evaluation of an existing domain definition to determine whether the domain is still needed, properly scoped, and effectively stewarded. This is the authority layer's equivalent of the agreement-review skill.

**Acceptance Criteria:**
- AC-5.1: The skill defines review triggers: scheduled evaluation date (from the domain contract's evaluation schedule element), request from the domain steward, request from the delegating body, threshold event (30% participant exit, major restructuring, boundary dispute pattern).
- AC-5.2: The step-by-step process includes: convene the review body (delegating body + domain steward + affected domains), evaluate each of the 11 domain elements against current conditions, evaluate the steward's effectiveness against the domain's metrics, determine outcome: reaffirm (set new review date), refine (amend domain contract elements), reassign (trigger role-transfer), merge (combine with another domain), sunset (trigger role-sunset).
- AC-5.3: The output artifact is a domain review record documenting the evaluation of each element, the steward effectiveness assessment, and the outcome decision.
- AC-5.4: The authority boundary check specifies that the review body must include the delegating body -- the domain steward cannot self-review without oversight. External reviewers from adjacent domains are recommended but not required.
- AC-5.5: The capture resistance check addresses: stewards who resist review to maintain authority, delegating bodies that use review as a tool for political removal, and review fatigue (too-frequent reviews disrupting productive work).
- AC-5.6: An OmniOne walkthrough demonstrates a 6-month domain review of the Community Engagement circle, revealing that one key responsibility has drifted to another circle. Outcome: refine the domain contract to match actual practice, plus trigger authority-boundary-negotiation for the drifted responsibility.
- AC-5.7: All 7 stress-test scenarios documented.

**Priority:** P1 -- Depends on domain-mapping and role-assignment existing.

### FR-6: Role Sunset (`role-sunset`)

**Description:** Determine when a role (domain) should be dissolved and execute the dissolution process. Roles are not permanent by default. When a domain's purpose is fulfilled, its scope has been absorbed by other domains, or it no longer serves the ecosystem, it must be formally sunset rather than left vacant indefinitely.

**Acceptance Criteria:**
- AC-6.1: The skill defines sunset triggers: domain-review recommends sunset, the domain's purpose has been achieved, all key responsibilities have been formally transferred to other domains, the domain has been vacant for longer than 2 review cycles, the delegating body consents to dissolution.
- AC-6.2: The step-by-step process includes: verify all pending commitments are resolved or transferred, verify all agreements held by this domain are reassigned to successor domains or sunset through the agreement-review skill, notify all dependent domains, delegating body runs a consent process for dissolution, domain contract is archived (not deleted) with sunset date and rationale, former steward's assignment record is updated.
- AC-6.3: The output artifact is a sunset record documenting: the domain contract (archived), the reason for sunset, the disposition of all responsibilities and agreements, and the consent record.
- AC-6.4: The failure containment logic addresses: premature sunset (domain is dissolved but its responsibilities were not fully transferred -- automatic reactivation if orphaned responsibilities are discovered within 90 days), contested sunset (steward or dependent domains object -- routes to GAIA escalation).
- AC-6.5: An OmniOne walkthrough demonstrates sunsetting the temporary Trunk Council key-holding role as OmniOne matures and distributes authority to permanent circles.
- AC-6.6: All 7 stress-test scenarios documented.

**Priority:** P1 -- Completes the role lifecycle.

### FR-7: Member Lifecycle (`member-lifecycle`)

**Description:** Manage the status transitions of ecosystem participants: onboarding consent ceremony (entry), active participation, inactive status (triggered by 1-month no-show), reactivation, and exit. This skill provides the structural mechanism for tracking who is a participant, what their current status is, and what happens at each transition. It bridges between the UAF (Layer I) consent at entry and the formal exit process (Layer X).

**Acceptance Criteria:**
- AC-7.1: The skill defines the lifecycle states: prospective (has expressed interest, not yet consented), onboarding (in consent ceremony process), active (consented to UAF, participating), inactive (1 month without participation, notified), reactivating (inactive member returning to active), exiting (voluntary exit in progress), exited (left the ecosystem).
- AC-7.2: The onboarding consent ceremony process includes: receive UAF document, facilitated walkthrough of each UAF section, explicit consent to each section (not blanket consent), cooling-off period (48 hours minimum between walkthrough and final consent), consent recorded in agreement registry, profile assignment (Co-creator, Builder, Collaborator, TownHall).
- AC-7.3: The inactive member protocol specifies: after 1 calendar month of no participation in any governance process (no consent rounds, no advice given, no proposals submitted, no meeting attendance), the member is automatically flagged, notification is sent with 14-day response window, if no response the member transitions to inactive status. Inactive members: retain all their existing agreements, lose active decision-making participation (cannot consent, object, or vote), are not counted toward quorum, can reactivate by notifying and attending one governance session.
- AC-7.4: The distinction between profiles (participation tiers) and roles (authority scopes) is explicitly stated. Profile changes do not automatically grant or remove domain authority. Role assignments are governed by role-assignment skill, not by profile status.
- AC-7.5: The exit compatibility check integrates with the exit provisions already defined in foundation skills (UAF exit clause, agreement obligation wind-down).
- AC-7.6: An OmniOne walkthrough demonstrates: (a) a new member going through the onboarding consent ceremony for OmniOne, including the facilitated UAF walkthrough and cooling-off period; (b) a member becoming inactive after 1 month of absence, receiving notification, and then reactivating 3 months later.
- AC-7.7: All 7 stress-test scenarios documented.

**Priority:** P0 -- Required for the authority model to know who is a participant and what their status is. The foundation track's UAF skill assumes an onboarding ceremony exists.

---

## Non-Functional Requirements

### NFR-1: Modularity
Each skill must function independently. A participant or AI agent reading a single SKILL.md must be able to understand and execute the described process without requiring other SKILL.md files to be loaded. Skills may reference each other by name but must not depend on another skill being "installed."

### NFR-2: Line Limit
Each SKILL.md must be under 500 lines. Stress-test narratives may overflow to `references/stress-tests.md` if the 500-line limit is threatened, per the foundation review recommendation.

### NFR-3: Portability
Every skill is NEOS-generic at its structural level. OmniOne-specific details appear as clearly marked examples, defaults, or configuration blocks. The 11-element domain contract is NEOS core; OmniOne's council structure and profiles are configuration.

### NFR-4: No Hidden Authority
If a step in any skill requires someone to make a judgment call, that person's authority scope must be explicitly stated. The domain-mapping skill itself defines the schema for stating authority -- Layer II must be self-referentially consistent. The domain-mapping skill must define its own meta-authority (who has authority to define authority).

### NFR-5: Reversibility Default
All role assignments and domain definitions are reversible. Sunset is the most irreversible action in this layer and requires consent from the delegating body. Archived domain contracts can be reactivated within 90 days.

### NFR-6: Expiry by Default
Every domain contract must have an evaluation schedule. Every role assignment must have a review date. The default evaluation cadence is 6 months. Domains without evaluation schedules are flagged as incomplete.

### NFR-7: Validation
Every SKILL.md must pass automated validation via `scripts/validate_skill.py` (built in the foundation track). The same 12-section structure (A-L), OmniOne walkthrough, and 7 stress-test requirements apply.

### NFR-8: Foundation Integration
After all Layer II skills are complete, the foundation track's skills must be updated to reference Layer II's formal authority model rather than their current ad-hoc authority statements. This is an explicit deliverable of this track.

---

## User Stories

### US-1: Circle Defines Its Domain
**As** a newly formed circle within an ETHOS,
**I want** a structured process for defining our domain with clear boundaries, responsibilities, and constraints,
**So that** every member of the ecosystem knows what we are responsible for and what we cannot do.

**Given** the circle has been created through an ACT consent process,
**When** the circle follows the domain-mapping skill to define all 11 elements,
**Then** a complete domain contract is produced, registered, and referenceable by other skills.

### US-2: AI Agent Determines Authority Scope
**As** an AI agent assisting a participant who wants to make a decision,
**I want** to look up the participant's assigned roles and their domain contracts,
**So that** I can tell the participant whether their proposed action is within their authority scope or requires escalation.

**Given** the participant has an assigned role with a domain contract,
**When** the AI agent reads the domain-mapping skill and the participant's role assignment record,
**Then** it can determine the authority boundary and advise accordingly.

### US-3: Steward Navigates a Boundary Dispute
**As** a circle steward whose domain overlaps with another circle,
**I want** a structured negotiation process that does not default to hierarchy,
**So that** the boundary is resolved through integrative discussion rather than political maneuvering.

**Given** two domain contracts claim authority over the same area,
**When** the stewards follow the authority-boundary-negotiation skill,
**Then** a boundary resolution record is produced and both domain contracts are amended.

### US-4: New Member Joins the Ecosystem
**As** a prospective member who wants to join OmniOne,
**I want** a clear onboarding process that explains what I am consenting to,
**So that** my entry is informed, recorded, and structurally legitimate.

**Given** the prospective member has expressed interest,
**When** they follow the member-lifecycle onboarding consent ceremony,
**Then** they have reviewed and explicitly consented to each section of the UAF, their consent is recorded, and they receive a profile assignment.

### US-5: Inactive Member Returns
**As** a member who has been inactive for 3 months due to travel,
**I want** to reactivate my participation without losing my existing agreements or starting over,
**So that** I can resume governance participation smoothly.

**Given** the member transitioned to inactive status after 1 month of no participation,
**When** they notify the ecosystem and attend one governance session,
**Then** their status returns to active, their agreements are still in force, and their quorum eligibility is restored.

### US-6: Ecosystem Sunsets a Temporary Role
**As** the OSC responding to ecosystem maturation,
**I want** to dissolve the temporary Trunk Council key-holding role now that permanent circles can hold those responsibilities,
**So that** temporary authority does not become permanent.

**Given** the Trunk Council's domain-review indicates all responsibilities can be transferred,
**When** the OSC follows the role-sunset skill,
**Then** the domain contract is archived, all responsibilities are reassigned, and no orphaned authority remains.

### US-7: Facilitator Assigns a Role
**As** a circle facilitator running a governance meeting,
**I want** clear instructions for assigning a new steward to a vacant role,
**So that** the assignment is legitimate, the candidate has consented, and the authority scope is explicit from day one.

**Given** a domain contract exists for a vacant role,
**When** the facilitator follows the role-assignment skill,
**Then** a candidate is nominated, competencies are verified, the candidate reviews and accepts the domain contract, the assigning body consents, and the assignment is registered.

---

## Technical Considerations

### File Structure

```
neos-core/
  layer-02-authority/
    README.md
    domain-mapping/
      SKILL.md
      assets/
        domain-contract-template.yaml
      references/
      scripts/
    authority-boundary-negotiation/
      SKILL.md
      assets/
        boundary-resolution-template.yaml
      references/
      scripts/
    role-assignment/
      SKILL.md
      assets/
        role-assignment-template.yaml
      references/
      scripts/
    role-transfer/
      SKILL.md
      assets/
        transfer-record-template.yaml
        handover-checklist.md
      references/
      scripts/
    domain-review/
      SKILL.md
      assets/
        domain-review-template.yaml
      references/
      scripts/
    role-sunset/
      SKILL.md
      assets/
        sunset-record-template.yaml
      references/
      scripts/
    member-lifecycle/
      SKILL.md
      assets/
        lifecycle-record-template.yaml
        onboarding-checklist.md
      references/
      scripts/
```

### YAML Frontmatter Schema

```yaml
---
name: skill-name          # kebab-case, matches directory name
description: "..."        # Pushy description that errs toward triggering
layer: 2                  # Integer layer number
version: 0.1.0            # Semver
depends_on: []            # List of skill names this skill references
---
```

### Interleaving Strategy

Skills are built in this order to ground cross-references:
1. `domain-mapping` (anchor) -- defines what a domain looks like; all other skills reference this
2. `member-lifecycle` (P0) -- defines who is a participant; needed before roles can be assigned
3. `role-assignment` (P0) -- assigns people to domains; references domain-mapping and member-lifecycle
4. `authority-boundary-negotiation` (P0) -- resolves overlaps; references domain-mapping
5. `role-transfer` -- hands off roles; references role-assignment
6. `domain-review` -- evaluates domains; references domain-mapping and role-assignment
7. `role-sunset` -- dissolves domains; references domain-review and role-transfer

### Authority Integration Strategy

After all 7 Layer II skills are built, a dedicated integration phase updates the 11 foundation skills (Layer I + Layer III) to replace ad-hoc authority statements with references to the formal authority model. This includes:
- Replacing inline authority boundary descriptions with references to domain contracts
- Adding `depends_on: [domain-mapping]` to foundation skills' frontmatter where authority checks are performed
- Updating the foundation Layer READMEs to note the dependency on Layer II

---

## Out of Scope

- **Current-Sees** -- Influence currencies are deferred to Layer IV (Economic Coordination). This track ensures that roles do not grant Current-See advantages but does not define the Current-See system.
- **Removal protocol** ("all but one by consensus") -- Deferred to Layer VI (Conflict & Repair). Member-lifecycle handles voluntary exit and inactivity, not involuntary removal.
- **NEXUS onboarding process** -- The full NEXUS onboarding spans multiple layers. Member-lifecycle handles the consent ceremony component only.
- **Software implementation** -- No databases, APIs, or UIs. Domain contracts are document-level governance specifications.
- **OmniOne-specific council definitions** -- The skills define how to create and manage domains/roles. The specific domains for TH, AE, OSC, and GEV are OmniOne configuration, not NEOS core skills. The OmniOne walkthroughs show how these councils use the skills.
- **IP Framework** -- Intellectual property governance is deferred to Layer IV, though the domain contract's "deliverables" element may reference IP outputs.

---

## Open Questions

1. **Maximum role count per person**: Should NEOS core define a maximum number of roles one person can hold, or leave this as ecosystem configuration? Recommendation: define a recommended cap (3 active steward roles) in the skill but mark it as configurable.

2. **Domain contract amendment process**: When a domain contract element needs updating outside of the scheduled review, does it route through the full ACT process or through a lighter amendment process? Recommendation: minor updates (metrics adjustment, resource change) use circle consent; structural changes (purpose, key responsibilities, constraints) use full ACT.

3. **Competency verification mechanism**: The role-assignment skill requires competency verification against the domain contract's competency element. Who verifies? Recommendation: the delegating body verifies, with input from the outgoing steward if applicable. No external certification required.

4. **Inactive member threshold variability**: The OmniOne source docs specify 1 month. Should NEOS core allow ecosystems to configure this threshold? Recommendation: yes, with a minimum floor of 2 weeks and maximum ceiling of 3 months.

5. **Meta-authority for domain-mapping**: Who has the authority to define the very first domains in a new ecosystem? Recommendation: the founding body (analogous to OSC) defines the initial domain structure through a consensus process, then the domain-mapping skill governs all subsequent domain creation.

6. **Dual-role conflict of interest**: When one person holds two roles with potential domain overlap, who flags the conflict? Recommendation: the role-assignment skill requires a conflict-of-interest disclosure at assignment time, and domain-review checks for accumulated conflicts.

7. **Profile-to-role relationship**: OmniOne defines profiles (Co-creator, Builder, Collaborator, TownHall) that carry access levels (commenting vs. editing). How do these interact with domain authority? Recommendation: profiles govern platform access; domain authority governs governance decisions. A Builder (commenting access) who is assigned a steward role has full governance authority within that domain regardless of their profile's platform access level.
