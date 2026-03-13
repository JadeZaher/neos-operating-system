# Implementation Plan: Layer VI -- Conflict and Repair

## Overview

This plan builds 6 governance skills for NEOS Layer VI (Conflict and Repair), organized into 5 phases. The build order establishes the core restorative processes first (harm circle, NVC dialogue), then the routing mechanism (escalation triage), then the formalization and specialized processes (repair agreement, coaching intervention), and finally the broadest-scope skill (community impact assessment).

**Total skills:** 6
**Total phases:** 5
**Estimated scope:** 25-35 hours of focused implementation

### Build Order Rationale

Layer VI has a distinct structure compared to earlier layers. The harm circle and NVC dialogue skills are co-foundational -- harm circles use NVC principles, and NVC is applied in contexts beyond harm circles. Escalation triage must know what processes exist to route to, so it comes after the core processes are defined. Repair agreements formalize outcomes from multiple processes. Coaching intervention is a distinct pathway that triage routes to. Community impact assessment is the broadest skill, referencing all others.

### Commit Strategy

- One commit per completed skill: `neos(layer-06): Add <skill-name> skill`
- Layer-level commit when all skills are done: `neos(layer-06): Complete layer 06 - Conflict and Repair`

### Dependencies

This track assumes the following are complete or in progress:
- Layer I skills (agreement-creation, agreement-amendment, agreement-registry) from `foundation_20260301`
- Layer III skills (proposal-creation, act-advice-phase, act-consent-phase) from `foundation_20260301`
- Layer II skills (authority-assignment, role-definition) from `authority_role_20260302`

Note: Layer VI does NOT depend on Layer IV (Economic) or Layer V (Inter-Unit) for its core skills. Layer V's polycentric-conflict-navigation handles structural inter-AZPO conflicts; Layer VI handles interpersonal and intra-AZPO conflicts. These are parallel, not sequential.

---

## Phase 1: Scaffolding and Core Processes

**Goal:** Create the Layer VI directory structure and build the two co-foundational skills -- harm-circle and nvc-dialogue -- that define the core conflict resolution processes all other Layer VI skills reference or build upon.

### Tasks

- [ ] **Task 1.1: Create Layer VI directory scaffolding**
  Create the full `neos-core/layer-06-conflict/` directory tree:
  ```
  neos-core/
    layer-06-conflict/
      README.md
      harm-circle/            (SKILL.md, assets/, references/, scripts/)
      nvc-dialogue/            (same structure)
      repair-agreement/        (same structure)
      escalation-triage/       (same structure)
      coaching-intervention/   (same structure)
      community-impact-assessment/ (same structure)
  ```
  Each skill directory gets empty `SKILL.md`, empty `assets/`, `references/`, and `scripts/` subdirectories.
  **Acceptance:** All directories exist. `find neos-core/layer-06-conflict -name SKILL.md | wc -l` returns 6.

- [ ] **Task 1.2: Draft harm-circle SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without structured harm response, communities default to one of three failure modes: ignoring harm (which compounds it), informal justice (dominated by social capital), or punitive response (which re-creates the coercive authority NEOS exists to prevent). This skill provides a restorative process that centers the person harmed, holds space for accountability, and produces repair agreements -- all without punishment, coercion, or forced reconciliation.
  - **B. Domain Scope:** Any situation where a participant has experienced harm within the ecosystem context. Harm includes: violations of agreements (field agreement, space agreements, role agreements), patterns of behavior that undermine another's participation (repeated dismissal, exclusion, intimidation), and actions that damage trust within a circle or AZPO.
  - **C. Trigger Conditions:** A participant reports harm (self-initiated), a facilitator or steward observes harm patterns, escalation triage routes a conflict to the harm circle process, or a repair agreement review reveals unresolved harm.
  - **D. Required Inputs:** Harm description (from the person harmed's perspective), identification of parties (person harmed, person who caused harm, affected community members), facilitator selection (mutually agreed or assigned through authority-assignment), safety assessment (is it safe for all parties to be in the same space?), relevant agreements that may have been violated.
  - **E. Step-by-Step Process:** Preparation phase (facilitator has individual conversations with each party to understand their experience, assess readiness, and set expectations -- this phase cannot be skipped), circle convening (structured rounds: Round 1 -- what happened from each person's perspective, Round 2 -- how it affected people, Round 3 -- what is needed for repair), repair agreement drafting (specific, actionable commitments with timelines), follow-up scheduling (check-in dates to verify repair commitments are being met).
  - **F. Output Artifact:** Harm circle record documenting: date, facilitator, participants (with consent for inclusion), summary of the process (not private disclosures), repair agreement with specific commitments and timelines, and follow-up schedule. The repair agreement is separately registered through the repair-agreement skill.
  **Acceptance:** Sections A-F substantive, restorative process clearly structured.

- [ ] **Task 1.3: Draft harm-circle SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G. Authority Boundary Check:** Facilitator has process authority only (managing the circle's structure and flow), not outcome authority (determining what repair looks like). The circle cannot impose sanctions, punishments, or removal -- only repair agreements that all parties consent to. If the person who caused harm refuses to participate, the circle can still proceed to address the person harmed's needs and the community impact, but cannot impose commitments on the absent party. No one can be forced to forgive, reconcile, or express emotions they do not feel.
  - **H. Capture Resistance Check:** Status protection (high-status person who caused harm receives lighter treatment or the harm is minimized), weaponization (harm circle convened in bad faith to damage someone's reputation), pressure on the person harmed (community members pressuring quick forgiveness or minimizing the harm), facilitator bias (facilitator with a prior relationship to one party steering the outcome), and solutionary bypass (framing harmful behavior as "just a misunderstanding" to avoid accountability).
  - **I. Failure Containment Logic:** Person who caused harm refuses to participate (circle proceeds without them, focusing on the person harmed's needs and community impact; repair agreement addresses what the community can do, not what the absent party commits to). Circle becomes unsafe (facilitator has authority to pause or end the circle at any point; parties can resume individually or reconvene later). No repair agreement reached (document the attempt, offer alternative processes, do not force an outcome). Repair agreement violated (trigger follow-up review, escalate through triage if needed).
  - **J. Expiry / Review Condition:** Harm circle records are retained permanently (for pattern tracking in community impact assessments). Repair agreements have explicit review dates (typically 30-90 days). Follow-up check-ins are mandatory, not optional.
  - **K. Exit Compatibility Check:** If the person who caused harm exits the ecosystem, remaining repair commitments are documented and closed. Community-facing aspects of the repair continue (structural changes, agreement amendments). If the person harmed exits, their privacy protections remain in effect indefinitely.
  - **L. Cross-Unit Interoperability Impact:** When harm crosses AZPO boundaries (a member of one AZPO harms a member of another), facilitator selection should be from a third AZPO if possible. Repair agreements may need consent from both AZPOs if they include structural changes. This is the boundary with Layer V's polycentric-conflict-navigation: if the underlying issue is structural between AZPOs, route to Layer V; if it is interpersonal between individuals who happen to be in different AZPOs, use this skill.
  **Acceptance:** Sections G-L structurally precise, maintaining restorative framing throughout.

- [ ] **Task 1.4: Write harm-circle OmniOne walkthrough and stress tests**
  - Walkthrough: A TH member (Rina) reports that her contributions in circle meetings have been repeatedly dismissed by a senior AE member (Marcus). Walk through: trigger (Rina reports the pattern to the circle facilitator), escalation triage (facilitator assesses -- this is a harm pattern, not a one-time disagreement, routes to harm circle), preparation (facilitator meets individually with Rina -- learns she has stopped contributing in meetings, meets with Marcus -- he was unaware of the pattern and is willing to participate, meets with two other circle members who witnessed the pattern), circle convening (Round 1: Rina describes three specific instances where her proposals were interrupted or redirected; Marcus acknowledges he tends to redirect discussions when he sees a faster path; witnesses share that they noticed the pattern and it affected their own willingness to speak up), Round 2 (Rina shares that she feels invisible and is considering leaving the circle; Marcus feels defensive but recognizes the impact), Round 3 (Rina needs: acknowledgment that the pattern was harmful, a structural change in meeting facilitation, a specific commitment from Marcus; Marcus agrees to all three), repair agreement drafted (Marcus commits to a "pause and invite" practice, the circle adds a speaking protocol, follow-up in 30 days). Edge case: what if Marcus had refused to participate? The circle would proceed with Rina and the witnesses, producing a community repair plan (the speaking protocol) without requiring Marcus's consent.
  - All 7 stress-test scenarios with full narrative paragraphs.
  **Acceptance:** Walkthrough demonstrates complete harm circle process with OmniOne roles. Stress tests are substantive.

- [ ] **Task 1.5: Finalize harm-circle SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter:
    ```yaml
    ---
    name: harm-circle
    description: "Convene a restorative circle to address harm -- center the person harmed, create space for accountability, and produce a consent-based repair agreement without punishment or forced reconciliation."
    layer: 6
    version: 0.1.0
    depends_on: [agreement-creation, authority-assignment]
    ---
    ```
  - Create `assets/harm-circle-template.yaml` and `assets/preparation-guide.md`.
  - Create `references/restorative-justice-primer.md` (brief reference on RJ principles for facilitators).
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Task 1.6: Draft nvc-dialogue SKILL.md -- full skill (sections A-L)**
  Build the complete `nvc-dialogue` skill:
  - **A.** In governance conversations, participants frequently conflate observations with evaluations ("you always block progress" vs. "in the last three meetings, you raised objections to all proposals"), feelings with thoughts ("I feel you are being unfair" vs. "I feel frustrated"), needs with strategies ("I need you to stop" vs. "I need to feel heard"), and requests with demands ("you must change" vs. "would you be willing to try a different approach?"). This skill provides a communication protocol that structurally separates these categories, transforming governance conversations from blame-and-defend cycles into needs-based dialogue.
  - **B.** Any governance conversation where tension, conflict, or miscommunication is present or anticipated. Applied within harm circles, ACT consent phases (especially when objections are contentious), cross-AZPO negotiations, coaching conversations, and informal conflict dialogue.
  - **C.** A governance conversation becomes heated or unproductive, a facilitator identifies blame/defend patterns, a participant requests NVC support, or escalation triage recommends NVC-supported dialogue.
  - **D.** The situation description, participating parties, facilitation support (if applicable), and the governance context (what decision, agreement, or conflict is at stake).
  - **E.** Three application contexts: (1) Conflict dialogue -- facilitator guides each party through observation/feeling/need/request, surfaces underlying needs, explores strategies that meet multiple needs; (2) Group facilitation -- facilitator helps a circle separate observations from evaluations when discussing a contentious proposal; (3) Written communication -- participant rewrites a proposal objection or feedback using NVC structure.
  - **F.** NVC dialogue record documenting observations, feelings, needs, and requests surfaced by each party, any agreements reached, and next steps.
  - **G-L.** Full structural sections addressing facilitator authority limits (NVC facilitators guide communication, not outcomes), capture resistance (NVC used as tone-policing, NVC fluency as social capital), failure modes (participant refuses NVC framing, NVC surfaces irreconcilable needs), expiry (NVC dialogue records linked to their governance context), exit compatibility, and cross-unit application.
  **Acceptance:** All 12 sections substantive. NVC presented as a tool, not a requirement.

- [ ] **Task 1.7: Write nvc-dialogue OmniOne walkthrough and stress tests**
  - Walkthrough: During an ACT consent phase for a proposal to restructure the AE circle's meeting schedule, one member (Kai) raises an objection that others perceive as blocking. The facilitator applies NVC. Walk through: the facilitator pauses the consent round and asks Kai to describe what they observed (specific schedule changes that conflict with their commitments), how they feel about it (anxious about losing connection to the circle), what they need (to maintain meaningful participation), and what they request (a modified schedule that preserves one shared time slot). Other members then share their observations, feelings, and needs. The group discovers that Kai's underlying need (connection) and the proposer's underlying need (efficiency) are not actually in conflict -- a modified proposal addresses both. Edge case: another member (Priya) says "I feel that Kai is being selfish." The facilitator gently notes this is a thought/evaluation, not a feeling, and asks Priya what she feels underneath that evaluation (frustrated, worried about the circle's productivity). This surfaces Priya's needs without dismissing her experience.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates NVC in a real governance context. Stress tests are substantive.

- [ ] **Task 1.8: Finalize nvc-dialogue SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: []`
  - Create `assets/nvc-reference-card.md` (quick reference for the four NVC components with governance examples) and `assets/dialogue-record-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 1: Run validate_skill.py against harm-circle and nvc-dialogue. Verify harm-circle references NVC principles without requiring nvc-dialogue to be loaded. Confirm neither skill imposes outcomes through coercive authority.** [checkpoint marker]

---

## Phase 2: Escalation Triage

**Goal:** Build the escalation triage skill that routes conflicts to the appropriate tier and process, serving as the intake and assessment layer for all Layer VI conflict resolution.

### Tasks

- [ ] **Task 2.1: Draft escalation-triage SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Without triage, every conflict gets the same response -- either too much (a full harm circle for a minor disagreement) or too little (a casual conversation for a serious harm pattern). Over-response creates process fatigue and discourages reporting. Under-response allows harm to compound. This skill provides a proportionate routing mechanism that matches conflict intensity to resolution process.
  - **B. Domain Scope:** Any conflict, harm report, or governance tension within the ecosystem. The triage skill is the entry point for Layer VI.
  - **C. Trigger Conditions:** A participant reports a conflict or harm experience, a facilitator or steward observes a pattern, a monitor (from Layer IV commons monitoring or equivalent) flags a pattern, or a previous repair agreement review reveals unresolved issues.
  - **D. Required Inputs:** Conflict description (from reporter's perspective), parties involved, severity indicators, scope of impact (individual, circle, AZPO, ecosystem), duration (one-time incident, recurring pattern, systemic issue), urgency level, safety considerations.
  - **E. Step-by-Step Process:** Intake (receive report, ensure reporter feels heard), assessment (evaluate along triage dimensions: severity, scope, root cause type, urgency, safety), routing decision (map assessment to appropriate process -- see triage matrix below), handoff (warm handoff to the routed process with relevant context, maintaining reporter's privacy preferences), documentation (triage record for pattern tracking).
  Triage matrix:
  - Minor disagreement, interpersonal, one-time: Direct dialogue (self-managed, optionally with NVC support)
  - Skill gap causing governance disruption: Coaching intervention
  - Harm pattern affecting individual: Harm circle
  - Harm pattern with community-wide impact: Harm circle + community impact assessment
  - Structural dispute between AZPOs: Route to Layer V polycentric-conflict-navigation
  - **F.** Escalation triage record documenting the assessment, dimensions evaluated, routing decision, and rationale.
  **Acceptance:** Sections A-F substantive, triage matrix clearly defined.

- [ ] **Task 2.2: Draft escalation-triage SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G.** Triager has assessment and recommendation authority but cannot override the affected parties' preferences for process (if parties want direct dialogue, the triager cannot force them into a harm circle). Triager cannot investigate -- they assess and route, they do not gather evidence or make findings. If the triager has a conflict of interest (personal relationship with involved parties), they must recuse and hand off to another triager.
  - **H.** Minimization bias (consistently routing conflicts involving powerful members to lower tiers), dramatization bias (routing conflicts involving marginalized members to higher tiers to appear responsive), gatekeeping (triager using their role to control who gets access to conflict resolution), routing as punishment (assigning someone to coaching as a status signal), and triage fatigue (triager becoming desensitized to harm reports).
  - **I.** No triager available (any facilitator can perform basic triage using the triage matrix; formal triager appointment is preferred but not blocking). Reporter disagrees with routing (reporter can request re-assessment or choose direct dialogue regardless of routing). Multiple conflicts routed simultaneously (prioritize by safety considerations, then severity).
  - **J.** Triage records reviewed quarterly to check for patterns (e.g., are certain types of conflict being consistently misrouted?). Triager role reviewed annually.
  - **K.** When a triager exits, pending triage cases are handed off with documentation. The triage matrix persists regardless of who fills the role.
  - **L.** Cross-AZPO conflicts are triaged with awareness of Layer V -- the triager must assess whether the conflict is interpersonal (Layer VI) or structural (Layer V) and route accordingly. When unclear, preference goes to starting with Layer VI (address the human impact first) with a note that structural dimensions may need Layer V attention.
  **Acceptance:** Sections G-L structurally precise, maintaining the boundary between assessment and investigation.

- [ ] **Task 2.3: Write escalation-triage OmniOne walkthrough and stress tests**
  - Walkthrough: Three situations arrive at triage in the same week. (1) Two TH members disagree about meeting time preferences -- triager assesses: minor, interpersonal, one-time, no harm pattern. Routing: direct dialogue with NVC support offered. (2) An AE member has been dominating circle meetings for three months, multiple members are affected -- triager assesses: recurring pattern, skill gap (the member comes from a corporate background where assertive participation is valued), medium severity, circle-scoped. Routing: coaching intervention, with note that if coaching does not resolve within 60 days, re-triage may route to harm circle. (3) An OSC member violated the field agreement's mutual respect commitment during a public TH meeting -- triager assesses: specific harm to several participants, high-status person involved, community-wide impact due to the public setting. Routing: harm circle for the directly affected participants, plus community impact assessment for the broader TH. Edge case: what if the OSC member is the person who usually serves as triager? The triager recuses; the next available triager handles the case.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates triage of three distinct situations with clear routing rationale.

- [ ] **Task 2.4: Finalize escalation-triage SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter:
    ```yaml
    ---
    name: escalation-triage
    description: "Assess incoming conflicts and harm reports to determine the appropriate tier and process -- direct dialogue, coaching, harm circle, or community assessment -- routing proportionately to the situation's severity and scope."
    layer: 6
    version: 0.1.0
    depends_on: [authority-assignment]
    ---
    ```
  - Create `assets/triage-assessment-template.yaml` and `assets/triage-decision-matrix.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 2: Run validate_skill.py against escalation-triage. Verify triage routes reference harm-circle, nvc-dialogue, and coaching-intervention by name. Confirm the triager has no investigation or outcome authority.** [checkpoint marker]

---

## Phase 3: Repair Agreements and Coaching

**Goal:** Build the repair-agreement and coaching-intervention skills that formalize conflict outcomes and provide the distinct coaching pathway for skill-gap conflicts.

### Tasks

- [ ] **Task 3.1: Draft repair-agreement SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A.** Without formalized repair agreements, conflict resolution outcomes evaporate. People leave a harm circle feeling resolved, but without documented commitments, timelines, and follow-up, the same patterns recur. This skill transforms conflict resolution outcomes into proper governance artifacts -- trackable, versioned, and reviewed -- just like any other agreement in the ecosystem.
  - **B.** Any conflict resolution process that produces an outcome requiring ongoing commitments. Repair agreement types: behavioral commitment (specific practice change), structural change (governance process modification), resource restitution (return or reallocation of resources), role adjustment (change in role, scope, or authority), relationship boundary (defined terms for interaction between parties), community practice change (AZPO-wide process modification).
  - **C.** A harm circle, coaching intervention, mediation, or direct dialogue produces an outcome that includes commitments requiring tracking.
  - **D.** Conflict resolution outcome record (from the originating process), parties' consented commitments, proposed timelines, proposed follow-up schedule, proposed completion criteria.
  - **E.** Draft repair agreement from conflict resolution outcome, verify all parties consent to the specific commitments (not just the general intent), register in agreement registry, schedule follow-up check-ins, conduct check-ins, assess completion or renewal.
  - **F.** Versioned repair agreement with unique ID, linked to originating conflict process, with specific commitments, timelines, follow-up schedule, completion criteria, and current status.
  **Acceptance:** Sections A-F substantive, emphasizing that repair agreements are governance artifacts.

- [ ] **Task 3.2: Draft repair-agreement SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G.** Repair agreements can only contain commitments that the committing party consented to. They cannot impose obligations on non-parties. They cannot override existing agreements (if a structural change is needed, it routes through the agreement-amendment skill). They cannot include open-ended or vague commitments ("be more respectful" is not a valid commitment; "use the speaking protocol in circle meetings" is).
  - **H.** Extraction (repair agreements used to extract ongoing concessions -- the stronger party negotiates favorable terms under the guise of repair), performative compliance (committing to repair actions without genuine intent, running out the clock on follow-up), power-preserving repair (repair agreement structured to protect the position of the person who caused harm), and escalation threats (using the possibility of further escalation to pressure the person who caused harm into overly broad commitments).
  - **I.** Party does not fulfill commitments (graduated response: reminder, check-in conversation, repair agreement review, potential re-triage to a higher conflict tier). Party contests the repair agreement after signing (trigger agreement review, explore whether consent was genuine). Follow-up check-in not conducted (automatic notification, extend timeline, do not void the agreement).
  - **J.** Follow-up check-ins at defined intervals (recommended 30, 60, 90 days). Repair agreements auto-complete when all completion criteria are met and confirmed at a check-in. Repair agreements that are not completed within their timeline trigger a review.
  - **K.** If a committing party exits, their commitments under the repair agreement are documented as unfulfilled and closed. Community-facing commitments (structural changes) continue and are reassigned if needed.
  - **L.** Cross-AZPO repair agreements (when the conflict crossed AZPO boundaries) are registered in both AZPOs' agreement registries and follow-up responsibility is assigned to both.
  **Acceptance:** Sections G-L structurally precise, preventing both under-enforcement and over-enforcement.

- [ ] **Task 3.3: Write repair-agreement OmniOne walkthrough and stress tests**
  - Walkthrough: Following a coaching intervention, a circle steward (Dani) who had been making unilateral decisions commits to specific changes. Walk through: coaching outcome (Dani understands the issue and wants to change), repair agreement drafting (three specific commitments: 1. Consult circle before any decision above a defined threshold, 2. Post a weekly summary of pending decisions for circle input, 3. Attend two facilitation skill sessions), timeline (90 days), follow-up schedule (30-day check-in with circle, 60-day self-assessment, 90-day circle review), completion criteria (all three commitments demonstrated consistently for 30 consecutive days), registration in agreement registry. At the 30-day check-in: Dani has been consulting on large decisions but still making small ones unilaterally. The circle discusses the threshold definition -- it was too vague. The repair agreement is amended to specify a clear threshold. Edge case: what if Dani feels the repair agreement is being used to micromanage them? The follow-up process includes Dani's perspective, and if the commitments feel disproportionate, the agreement can be reviewed through the same process that created it.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough shows repair agreement as a living document with genuine follow-up.

- [ ] **Task 3.4: Finalize repair-agreement SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: [agreement-creation, agreement-registry, harm-circle]`
  - Create `assets/repair-agreement-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Task 3.5: Draft coaching-intervention SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Not all governance conflict is harm-based. Some conflicts arise because a participant lacks specific skills -- facilitation, consent-based decision-making, NVC communication, or domain knowledge. Routing skill-gap conflicts to restorative circles is disproportionate and can stigmatize the participant. Ignoring skill gaps leads to recurring governance disruption. This skill provides a distinct pathway that builds capacity rather than assigning blame.
  - **B. Domain Scope:** Any situation where governance disruption stems from a skill or knowledge gap rather than intentional harm or values conflict. Common skill gaps: facilitation (dominating or failing to manage discussion), consent-based process (defaulting to command-and-control from prior organizational experience), communication (aggressive or unclear governance communication), domain knowledge (making governance decisions without understanding the domain's agreements and protocols).
  - **C. Trigger Conditions:** Escalation triage routes a conflict to coaching, a circle identifies a recurring pattern of governance disruption linked to a skill gap, or a participant self-identifies a skill gap and requests coaching.
  - **D. Required Inputs:** Skill gap description (what specific skills are missing and how the gap manifests in governance), identified participant (with their awareness and consent), coach selection criteria (relevant skills, no direct authority relationship), proposed coaching timeline.
  - **E. Step-by-Step Process:** Skill gap identification and framing (focus on specific behaviors, not character), participant engagement (voluntary -- the participant must consent to coaching), coach selection (someone with relevant skills who is not the participant's direct steward or authority), coaching plan design (specific skills to develop, practice opportunities, check-in schedule), coaching sessions (structured skill-building, not therapy), progress check-ins, outcome assessment (has the skill gap been addressed? Can the participant now engage governance processes effectively?).
  - **F.** Coaching plan with skill targets and timeline, plus coaching outcome report documenting the process and assessment.
  **Acceptance:** Sections A-F substantive, clearly distinguishing coaching from punishment.

- [ ] **Task 3.6: Draft coaching-intervention SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G.** Coaching is voluntary -- a participant cannot be compelled to accept coaching. However, the consequences of declining coaching can be defined: the underlying governance disruption remains unaddressed and may be re-triaged to a higher conflict tier. Coaches have guidance authority (skill-building), not governance authority (they cannot make decisions on behalf of the participant or change the participant's role). Coaching recommendations cannot be used as evidence in removal proceedings.
  - **H.** Coaching as soft punishment ("you need coaching" used to signal that someone is deficient), coach imposing preferences (using coaching to instill their own governance style rather than building general skills), targeting patterns (coaching recommendations consistently directed at newer members, women, or marginalized participants while similar gaps in established members are overlooked), coaching avoidance (powerful members declining coaching and suffering no consequences while less powerful members feel pressured to accept).
  - **I.** Participant declines coaching (document the declined recommendation, re-triage if governance disruption continues). Coaching does not resolve the gap (extend timeline with modified plan, or re-triage to explore whether the issue is actually a values conflict rather than a skill gap). Coach-participant relationship breaks down (replace coach, do not abandon the process). No qualified coach available (use peer coaching with a structured guide from `references/`, or temporarily use external expertise).
  - **J.** Coaching plans have defined timelines (recommended 60-90 days). Outcome assessment conducted at timeline end. If successful, no further action. If partially successful, extension option. Coaching records retained for pattern tracking (anonymized) but not attached to the participant's governance record permanently.
  - **K.** If the participant exits during coaching, the process ends and the coaching record is closed. If the coach exits, a replacement is appointed and the coaching plan continues.
  - **L.** Cross-AZPO coaching (participant in one AZPO receiving coaching from someone in another AZPO) is permitted and sometimes preferable (provides outside perspective). The coaching plan is shared with the participant's home AZPO for transparency but the coaching relationship remains between coach and participant.
  **Acceptance:** Sections G-L structurally precise, protecting participant autonomy throughout.

- [ ] **Task 3.7: Write coaching-intervention OmniOne walkthrough and stress tests**
  - Walkthrough: An AE member (Luca) whose circle stewardship style is too directive -- they make decisions without consulting their circle, not from malice but from a previous corporate career where managers decided and teams executed. Walk through: identification (three circle members raise the pattern at different times; the facilitator notices it too), triage (routing: skill gap, not harm -- though circle members are frustrated, Luca's intent is not to override but to be efficient), engagement (facilitator discusses the coaching recommendation with Luca; Luca is initially defensive -- "I am just trying to get things done" -- but agrees to coaching after seeing specific examples of decisions made without consultation), coach selection (an experienced steward from a different circle, not Luca's direct colleagues), coaching plan (three skills: consent-based decision-making, advice-seeking, facilitating rather than directing; four sessions over 8 weeks; practice opportunity: Luca facilitates one circle meeting using consent process with coach observing), progress (at 4-week check-in, Luca has improved on advice-seeking but still defaults to directing under time pressure; coach adjusts plan to include time-pressure scenarios), outcome assessment (at 8 weeks, Luca consistently seeks advice and uses consent for decisions, though still occasionally slips under stress; circle reports significant improvement; coaching marked as successful with a 30-day follow-up check-in). Edge case: what if Luca had declined coaching? The facilitator would document the declined recommendation. If Luca's directive style continued to disrupt the circle, the issue would be re-triaged -- potentially to a harm circle if circle members reported the pattern as harmful.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough shows full coaching arc with realistic complexity.

- [ ] **Task 3.8: Finalize coaching-intervention SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: [escalation-triage, authority-assignment]`
  - Create `assets/coaching-plan-template.yaml` and `assets/coaching-outcome-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 3: Run validate_skill.py against repair-agreement and coaching-intervention. Verify repair-agreement references the originating conflict processes correctly. Verify coaching-intervention maintains voluntariness throughout. Confirm neither skill imposes outcomes through coercive authority.** [checkpoint marker]

---

## Phase 4: Community Impact Assessment

**Goal:** Build the community-impact-assessment skill -- the broadest-scope skill in Layer VI -- that enables AZPO-wide processing of community-affecting conflicts and routes systemic findings into governance improvement through ACT.

### Tasks

- [ ] **Task 4.1: Draft community-impact-assessment SKILL.md -- sections A through F**
  Fill in the first 6 sections:
  - **A. Structural Problem It Solves:** Individual conflict resolution addresses the specific harm between specific parties. But some conflicts reveal systemic issues -- patterns in governance structure, gaps in agreements, or cultural dynamics that create conditions for recurring harm. Without a mechanism to process community-wide impact, the same types of conflicts keep recurring because the structural conditions that generate them are never addressed. This skill bridges the gap between individual repair and systemic improvement.
  - **B. Domain Scope:** Any conflict or pattern of conflicts that has implications beyond the directly involved parties. Applies when: harm affects community trust broadly, a pattern of similar conflicts emerges, a conflict reveals a structural gap in agreements or processes, or a repair agreement has community-wide implications (e.g., changing a circle's decision process).
  - **C. Trigger Conditions:** Escalation triage routes a conflict as having community-wide impact, a harm circle reveals systemic conditions, a monitor or facilitator identifies a pattern of similar conflicts (three or more similar conflicts within a review cycle), or a circle requests community processing of a conflict's broader implications.
  - **D. Required Inputs:** Conflict summary (systemic dimensions only, not private details), scope of community impact, previous conflict records (anonymized if necessary), relevant agreements and governance structures, participating community members.
  - **E. Step-by-Step Process:** Assessment convening (steward or facilitator calls the assessment, defines scope and participation, establishes privacy boundaries between individual conflict and systemic analysis), community processing session (structured dialogue: what patterns do we see, how do these patterns affect our community, what conditions create these patterns -- this is NOT about the specific individuals), systemic analysis (identify structural gaps, agreement gaps, process gaps), recommendation generation (propose specific governance changes), routing through ACT (recommendations become proposals that go through the standard ACT process).
  - **F.** Community impact assessment report documenting: impact scope, community processing outcomes, systemic findings, recommended governance changes, and links to the ACT proposals for implementing them.
  **Acceptance:** Sections A-F substantive, clearly separating systemic analysis from individual conflict details.

- [ ] **Task 4.2: Draft community-impact-assessment SKILL.md -- sections G through L**
  Complete remaining sections:
  - **G.** The assessment process has convening and facilitation authority but not decision authority. Recommendations route through ACT -- the assessment does not directly change governance. The privacy boundary between individual conflict and systemic analysis is structural and non-negotiable: what was disclosed in a harm circle stays in the harm circle. The assessment works with patterns, not private details. The convener cannot use the assessment to re-litigate an individual conflict that has already been resolved.
  - **H.** Re-litigation (using the assessment to revisit and overturn a harm circle's outcome), steering (powerful community members directing systemic findings toward conclusions that protect their interests), over-assessment (convening too many assessments, creating process fatigue and diluting their impact), under-assessment (avoiding assessments of systemic issues that implicate leadership), and abstraction capture (keeping findings so high-level that no actionable recommendations emerge).
  - **I.** Community participation is low (extend invitation, lower the quorum for the processing session, but do not proceed with fewer than a defined minimum -- recommended 1/3 of affected community). Systemic findings are contested (present competing analyses, route all to ACT as alternative proposals). Recommendations fail in ACT (document the findings for future reference, revisit at next assessment cycle).
  - **J.** Community impact assessments are conducted as needed (not on a fixed schedule). Assessment reports are retained permanently for longitudinal pattern tracking. Recommended governance changes that pass through ACT have their own review dates per the standard ACT test phase.
  - **K.** If a significant portion of the community exits, triggering a community impact assessment may itself be warranted (30% exit threshold). Assessment records persist regardless of community composition changes.
  - **L.** Cross-AZPO community impact assessments (when a pattern spans multiple AZPOs) require representatives from all affected AZPOs. Facilitation rotates. Recommendations may include federation agreement amendments (routed through Layer V's federation-agreement skill).
  **Acceptance:** Sections G-L structurally precise, maintaining the privacy boundary throughout.

- [ ] **Task 4.3: Write community-impact-assessment OmniOne walkthrough and stress tests**
  - Walkthrough: After three separate conflicts within the AE circle over six months -- all involving proposals that were consented to without adequate advice phases -- the facilitator identifies a pattern and requests a community impact assessment. Walk through: convening (the AE circle steward calls the assessment, inviting all AE members; the three original conflicts are referenced by pattern description only, no individual names or private details), community processing session (members discuss what they have observed: proposals moving too fast, advice phase feeling perfunctory, newer members not speaking up during advice, time pressure consistently cited as justification for abbreviated advice), systemic analysis (the group identifies three structural factors: no minimum advice phase duration in their circle agreement, no requirement to document which parties were consulted, and a cultural norm of "bias toward action" that overrides thoroughness), recommendation generation (three proposals: 1. Amend the circle agreement to set a 5-day minimum advice phase, 2. Require an advice log documenting who was consulted, 3. Add a "thoroughness check" to the consent phase facilitation script), routing through ACT (all three recommendations become proposals in the circle's ACT process, with the advice phase amendment being the highest priority). Edge case: one of the participants in the assessment was involved in one of the original three conflicts and begins to re-litigate their specific case. The facilitator redirects to the systemic focus and offers to schedule a separate check-in for the individual's remaining concerns.
  - All 7 stress-test scenarios.
  **Acceptance:** Walkthrough demonstrates systemic analysis without re-litigating individual conflicts.

- [ ] **Task 4.4: Finalize community-impact-assessment SKILL.md and create assets**
  - Assemble SKILL.md with frontmatter: `depends_on: [harm-circle, escalation-triage, proposal-creation, act-advice-phase]`
  - Create `assets/impact-assessment-template.yaml`.
  - Run `validate_skill.py`.
  **Acceptance:** SKILL.md passes validation. Under 500 lines.

- [ ] **Verification 4: Run validate_skill.py against community-impact-assessment. Verify the privacy boundary between individual conflict and systemic analysis is explicit. Confirm recommendations route through ACT, not direct governance change.** [checkpoint marker]

---

## Phase 5: Layer Integration and Finalization

**Goal:** Finalize the layer with a README, cross-skill consistency review, and quality gates.

### Tasks

- [ ] **Task 5.1: Write Layer VI README.md**
  Create `neos-core/layer-06-conflict/README.md` summarizing:
  - Layer purpose and relationship to NEOS principles (solutionary culture, no coercive authority, consent-based)
  - All 6 skills with brief descriptions and relationships
  - Theoretical foundations mapping (Transformative Justice, Restorative Justice, NVC, Ostrom Principle 6, Teal three-level escalation)
  - The three-tier escalation model as implemented across skills
  - The coaching-vs-repair distinction
  - Cross-layer dependencies (Layers I, II, III) and the boundary with Layer V (structural inter-AZPO conflicts)
  - OmniOne configuration notes (Solutionary Culture, field agreement commitments, removal process reference)
  - Privacy protections summary
  **Acceptance:** README accurately summarizes the layer, its design philosophy, and the privacy framework.

- [ ] **Task 5.2: Cross-skill review and quality gates**
  Review all 6 skills against the per-skill checklist:
  - [ ] All 12 sections (A-L) present and substantive
  - [ ] OmniOne walkthrough included with specific roles
  - [ ] At least one edge case documented per skill
  - [ ] Stress-tested against all 7 scenarios
  - [ ] No hidden coercive authority
  - [ ] No forced reconciliation
  - [ ] No punitive framing in restorative language
  - [ ] Exit compatibility confirmed
  - [ ] Cross-unit interoperability impact stated
  - [ ] Privacy protections explicitly defined
  - [ ] Harm-centered framing maintained
  Additionally:
  - Verify the escalation triage correctly references all processes it routes to
  - Verify repair-agreement integrates with the agreement registry from Layer I
  - Verify the boundary between Layer VI (interpersonal/intra-AZPO) and Layer V (structural inter-AZPO) is clear in every skill
  - Verify NVC is presented as a tool, not a mandatory communication style
  - Verify coaching is presented as capacity-building, not punishment
  - Verify terminology matches product-guidelines.md throughout
  - Verify no skill exceeds 500 lines
  **Acceptance:** All 6 skills pass all quality gates. Layer is internally consistent.

- [ ] **Verification 5: Run validate_skill.py against entire layer-06-conflict/ directory. All 6 skills pass. README exists. Cross-references verified. Layer is complete.** [checkpoint marker]
