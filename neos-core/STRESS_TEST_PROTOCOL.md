# NEOS Stress-Test Protocol

Every NEOS skill is tested against 7 scenarios that represent the most common governance failure modes. This document defines each scenario, its evaluation criteria, and the methodology for applying it.

Stress-test results appear in each skill's SKILL.md as full narrative paragraphs -- not bullet lists, not checklists. A strong stress-test response walks through the specific mechanisms in the skill that activate under pressure, names the structural safeguards, and demonstrates that governance integrity holds.

---

## Methodology

### How to Apply a Scenario to a Skill

1. Read the skill's step-by-step process (section E) and authority boundaries (section G).
2. Introduce the scenario's setup conditions into the skill's operating context.
3. Apply the listed pressures to each step of the skill's process.
4. Trace the skill's response: which mechanisms activate, which sections are relevant, what output changes.
5. Evaluate against the criteria below.

### How to Evaluate the Response

A skill **passes** a scenario when:
- Structural integrity is maintained (the skill's process completes or degrades gracefully).
- No hidden authority emerges (all decisions trace to named, bounded authority).
- No capture vector succeeds (capital, charisma, emergency, or informal capture is blocked).
- Exit remains possible (no participant is trapped by the scenario's pressures).
- The output artifact remains traceable and registered.

A skill **fails** a scenario when:
- The process breaks down without a defined fallback.
- Authority concentrates beyond stated boundaries.
- A capture vector succeeds unopposed.
- Exit becomes structurally impossible or punitive.
- The output artifact is lost, unregistered, or untraceable.

### How to Document a Stress-Test Result

Write a full narrative paragraph of at least 5 sentences for each scenario. The paragraph must:
- Name the specific setup conditions as they apply to this skill.
- Walk through which mechanisms in the skill activate under the scenario's pressures.
- Identify the structural safeguards by name (referencing sections G, H, I, or other skills).
- State the outcome: what the skill produces, what it prevents, how it degrades if needed.
- Conclude with the governance state after the pressure resolves.

Do not write abstract summaries. Do not list bullets. Narrate the scenario playing out against the skill's actual structure.

---

## The 7 Scenarios

### 1. Capital Influx

**Setup conditions:** A major external funder offers substantial resources to the ecosystem, conditioned on governance changes that would grant the funder disproportionate influence. The funder's resources exceed the ecosystem's current annual budget. Multiple participants advocate accepting the offer.

**Pressures applied:** Financial pressure on resource-constrained participants. Social pressure from those who want the funding. Narrative framing that positions refusal as impractical or idealistic. Attempts to fast-track governance changes to meet funder timelines.

**Evaluation criteria:** The skill maintains separation between economic contribution and governance authority. Consent processes operate at standard pace regardless of funder urgency. The Agreement Field registers any changes transparently. No participant gains authority through financial leverage. Current-See allocation remains equal regardless of contribution.

**Strong response example:** The skill routes the funder's conditions through the standard ACT process. The consent phase surfaces objections to authority distortion. The agreement-registry records the full terms. Capital capture indicators in section H activate, flagging the proposal for safeguard review.

**Weak response example:** The skill allows expedited processing due to financial urgency. Consent thresholds are informally relaxed. The funder's conditions are partially implemented before full ACT completion. No capture check activates.

### 2. Emergency Crisis

**Setup conditions:** A sudden, severe event threatens the ecosystem's physical safety or operational continuity. The event demands immediate action within hours, not days. Normal consent timelines are impractical. Key participants are unavailable.

**Pressures applied:** Time compression on all governance processes. Reduced participation due to crisis response demands. Emotional urgency that frames deliberation as dangerous delay. Pressure to grant broad, undefined authority to whoever steps up.

**Evaluation criteria:** The skill operates under compressed timelines defined in Layer VIII, not under suspended governance. Emergency authority is bounded by pre-authorization protocols. All actions taken under emergency authority are logged for post-crisis review. Authority auto-reverts when the crisis ends. Consent is maintained even at maximum compression -- the bar lowers from full deliberation to "no reasoned objection within compressed window," not to unilateral action.

**Strong response example:** The skill compresses its timeline per the emergency expediting rules. Pre-authorized actors operate within defined boundaries. Every emergency action produces a traceable record. Post-emergency review is automatically scheduled. Authority reverts on the hard expiration timestamp.

**Weak response example:** The skill is suspended during the crisis. A self-appointed leader makes decisions without defined authority. No records are kept. After the crisis, expanded authority persists because no one formally revokes it.

### 3. Leadership Charisma Capture

**Setup conditions:** A highly charismatic, well-respected participant consistently steers governance outcomes through personal influence rather than structural process. The participant holds no formal authority beyond their role but informally dominates deliberation. Other participants defer to this person's judgment rather than engaging with the process independently.

**Pressures applied:** Social pressure to conform with the charismatic leader's position. Reluctance to raise objections against a popular figure. Gradual normalization of process shortcuts when the leader advocates for them. Framing dissent as obstructionism or disloyalty.

**Evaluation criteria:** The skill's consent phase protects anonymous or written objection channels. Authority boundary checks in section G prevent any individual from acting beyond their stated scope. The skill does not allow reputation or social standing to modify process requirements. Capture-pattern-recognition indicators for charismatic capture activate when one participant dominates outcomes across multiple decisions.

**Strong response example:** The skill requires written objections evaluated on structural merit, not social standing. The authority boundary check confirms the charismatic leader operates within their defined domain. Section H's charismatic capture protections ensure process integrity regardless of who advocates for or against a proposal.

**Weak response example:** The skill's consent phase relies entirely on live verbal deliberation where social dynamics dominate. No structural check prevents a popular figure from informally expanding their authority. Objections against the leader's preferred outcome are socially costly and structurally unprotected.

### 4. High Conflict / Polarization

**Setup conditions:** The ecosystem splits into two entrenched factions with incompatible positions on a governance question. Both factions hold legitimate concerns grounded in different values. Communication has deteriorated into positional argumentation. Participants begin refusing to engage with members of the opposing faction.

**Pressures applied:** Emotional intensity that frames compromise as betrayal. Pressure to force a binary vote rather than seek integrative solutions. Withdrawal threats from both sides. Escalating accusations that undermine trust in the governance process itself.

**Evaluation criteria:** The skill routes the conflict through structured escalation (GAIA levels in OmniOne) rather than allowing it to stall or rupture. NVC dialogue and coaching intervention (Layer VI) are available as referenced escalation paths. The skill does not force binary outcomes -- it creates space for third solutions. The consent process distinguishes between "I object on structural grounds" and "I disagree on values," treating only the former as blocking.

**Strong response example:** The skill's process stalls at the consent phase when objections accumulate. The failure containment logic (section I) routes to escalation triage. Coaching intervention creates space for third solutions. The original proposal is amended to integrate concerns from both factions. The process completes with a registered agreement.

**Weak response example:** The skill forces a majority vote to break the deadlock. The losing faction exits. No coaching or mediation pathway activates. The resulting agreement lacks legitimacy with half the affected participants.

### 5. Large-Scale Replication

**Setup conditions:** The ecosystem grows from 50 active participants to 5,000 across dozens of ETHOS spanning multiple geographic locations. The volume of proposals, agreements, and decisions increases by two orders of magnitude. Not every participant can engage with every governance action.

**Pressures applied:** Information overload on participants. Consent fatigue from excessive decision volume. Coordination overhead between ETHOS. Pressure to centralize decision-making for efficiency. Divergent interpretations of skills across locations.

**Evaluation criteria:** The skill scales through domain-scoped action -- participants engage only with decisions in their domain. The agreement-registry and decision-record systems handle high volume through semantic tagging and precedent search (Layer IX). Cross-ETHOS coordination (Layer V) manages inter-unit effects without requiring global participation. The skill's process does not require all participants to participate in every instance.

**Strong response example:** The skill operates within domain scope, routing decisions to affected participants only. The registry handles volume through structured metadata. Precedent search reduces redundant deliberation. Cross-ETHOS effects trigger notification rather than global consent. New ETHOS adopt the skill by configuring their own domain contracts.

**Weak response example:** The skill requires ecosystem-wide consent for every decision. Participation rates collapse under volume. Informal shortcuts emerge to manage overload. The registry becomes unusable without search and tagging.

### 6. External Legal Pressure

**Setup conditions:** A government authority issues a legal mandate that conflicts with the ecosystem's governance agreements. The mandate targets specific participants or the ecosystem's legal entity (e.g., the stewarding non-profit). Compliance is legally required for individuals subject to that jurisdiction. Non-compliance carries enforcement risk.

**Pressures applied:** Legal liability on individual participants and the stewarding entity. Pressure to override governance process to comply quickly. Tension between individual legal obligations and collective agreements. Potential for the legal mandate to require changes that violate NEOS principles (e.g., granting authority to an external body).

**Evaluation criteria:** The skill distinguishes between individual legal compliance (which participants handle personally) and ecosystem-level governance changes (which follow the standard ACT process). The Universal Agreement Field's sovereignty principle acknowledges external legal reality without subordinating governance to it. Agreements made under legal duress are registered with that context. The skill does not pretend external law does not exist, nor does it automatically comply without deliberation.

**Strong response example:** The skill routes the legal mandate through the standard process. Individual participants comply with their personal legal obligations. The ecosystem evaluates whether a governance change is necessary, using the ACT protocol. Any change made under legal pressure is registered with full context, including the external mandate. The agreement-versioning system preserves the pre-pressure state.

**Weak response example:** The skill bypasses governance process to comply immediately. The legal mandate is implemented without consent. No record preserves the context of the change. The ecosystem's agreements are permanently altered by external pressure without deliberation.

### 7. Sudden Exit of 30% of Participants

**Setup conditions:** Thirty percent of the ecosystem's active participants exit within a short period (days to weeks). The departing participants include key role-holders, domain stewards, and participants with institutional knowledge. Multiple ETHOS lose quorum simultaneously. In-progress agreements and decisions are partially complete.

**Pressures applied:** Quorum failure across multiple domains. Loss of institutional knowledge. Orphaned roles and unfulfilled commitments. Pressure to consolidate authority among remaining participants. Emotional strain and morale loss on those who stay.

**Evaluation criteria:** The skill adapts quorum requirements to the current participant count rather than failing silently. Orphaned roles trigger the role-transfer and role-sunset processes (Layer II). In-progress outputs remain valid until formally reviewed -- they do not auto-invalidate. Commitment-unwinding (Layer X) manages departing participants' obligations. The skill does not require retroactive consent from participants who have left.

**Strong response example:** The skill detects quorum failure and activates fallback procedures from section I. Orphaned roles enter the role-transfer queue. In-progress decisions are paused, not voided, and resume once quorum is restored or adapted. The agreement-registry flags affected agreements for review. Departing participants receive portable records of their governance history.

**Weak response example:** The skill silently fails when quorum is not met. Orphaned roles remain vacant with no transfer process. In-progress decisions are voided, requiring full restart. Remaining participants informally absorb authority without structural assignment.

---

## Integration with Skill Development

Every skill's SKILL.md must contain a "Stress-Test Results" section with narrative paragraphs for all 7 scenarios. During skill development:

1. Write the skill's core process (sections A through L) first.
2. Apply each scenario using the methodology above.
3. Write the narrative stress-test results.
4. If a scenario reveals a structural weakness, revise the skill's process before finalizing.
5. The validation script (`scripts/validate_skill.py`) checks for the presence and minimum length of all 7 stress-test narratives.

Stress-test results are not decorative. They are structural verification that the skill holds under real-world governance pressures.
