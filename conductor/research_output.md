I now have sufficient research across all 8 layers. Let me compile the comprehensive synthesis.

---

# NEOS Governance Skill Stack: Research Findings for Layers II–X

## Query: External frameworks, patterns, and anti-patterns for designing 8 governance layers in a non-sovereign coordination architecture

---

## Layer II: Authority & Role

### Most Relevant Frameworks

**Sociocracy 3.0 (S3) — Primary**

S3's domain model is the most directly applicable framework. A domain is defined as "a distinct area of responsibility and authority" specified by an explicit contract between delegator and delegatee. The eleven elements that define a domain are: purpose, key responsibilities, customers and deliverables, dependencies, external constraints, key challenges, key resources, delegator responsibilities, required competencies, key metrics, and an evaluation schedule. Critically, S3 mandates that delegatees may do whatever serves the domain's purpose within defined constraints — authority is wide within its scope, not narrow — and that violating another role's explicit domain is structurally disallowed.

S3 prevents ossification through mandatory evaluation schedules: weekly metric checks, monthly retrospectives, and quarterly peer reviews. Domains are explicitly designed to evolve.

**Links**: [Domains and Delegation — S3](https://patterns.sociocracy30.org/domain.html) | [Clarify and Develop Domains — S3](https://patterns.sociocracy30.org/clarify-and-develop-domains.html)

**Holacracy — Secondary**

Holacracy separates roles from people (one person can hold multiple roles), and defines a role by: name, purpose, domains (exclusive control), and accountabilities (ongoing activities). Circles are self-governing groups of roles. Authority is granted blanket unless explicitly restricted by policy — the inverse of most hierarchical systems. Governance meetings use integrative decision-making to update role and policy definitions through consent.

**Link**: [Holacracy Constitution v5.0](https://www.holacracy.org/constitution/5-0/)

**Laloux's Teal Organizations — Contextual**

Teal adds the "advice process": anyone can make any decision within their domain as long as they consult those affected and those with relevant expertise. Authority is not positional — it flows to whoever has the most expertise, passion, or interest for a given situation. Conflict resolution escalates from direct conversation to peer mediation to a panel, always handled closest to the point of friction.

**Link**: [Teal Organisation — Wikipedia](https://en.wikipedia.org/wiki/Teal_organisation)

### Key Design Patterns to Adopt

- **Domain-as-contract**: Every role in NEOS should have an explicit domain definition with all eleven S3 elements, not a loose job description.
- **Blanket authority within scope**: Roles act freely within their domain without needing permission; restrictions are listed explicitly, not implied.
- **Advice process**: Role-holders consult before acting on decisions that affect others' domains, but retain final authority in their own scope.
- **Evaluation cadence**: Every domain has a scheduled review date, preventing roles from fossilizing through neglect.
- **Separation of role and person**: NEOS ETHOS should track roles as entities distinct from the members filling them, allowing easy transfer or dissolution.

### Anti-Patterns to Avoid

- **Permission-seeking default**: If roles must ask permission to act, you have re-created hierarchy with extra steps. Authority must be presumed, not granted per-action.
- **Undifferentiated domains**: Two roles covering the same area with no explicit boundary is a recipe for either conflict or avoidance. Gaps and overlaps must be named and resolved in governance.
- **Permanent role tenure**: Roles that cannot be updated, dissolved, or transferred calcify. Build in sunset review requirements.
- **Authority creep by precedent**: A role acting outside its domain once and not being challenged sets an informal precedent. Track boundary incidents explicitly.

### OmniOne-Specific Considerations

NEOS ETHOS (Autonomous Zone of Participatory Operations) need a domain registry — a live document mapping every active role's scope, authority limits, dependencies, and next review date. Councils (the multi-stakeholder deliberative bodies) should function as domain delegators for ETHOS-level roles, with SHUR network nodes as potential domain auditors. Current-Sees (influence currencies) should not be attached to roles directly — attaching status currency to a named role creates incentives for role hoarding.

### Suggested Skills for Layer II

1. **Domain Mapping** — Defining the eleven S3 elements for a new or existing role; identifying gaps and overlaps in a domain map.
2. **Authority Boundary Negotiation** — Working across roles to resolve domain overlap through structured integrative discussion.
3. **Advice Process Facilitation** — Consulting affected parties before domain-crossing decisions; documenting the consultation.
4. **Role Transfer Protocol** — Handing off a role between members without losing institutional knowledge or continuity.
5. **Domain Review Facilitation** — Running the scheduled evaluation of whether a domain's definition still fits its context.
6. **Role Sunset Assessment** — Determining when a role should be dissolved rather than merely unfilled.

---

## Layer III: ACT Decision Engine (existing — included for context only)

Not part of this research scope. Already specified in foundation track.

---

## Layer IV: Economic Coordination

### Most Relevant Frameworks

**Elinor Ostrom's Commons Governance — Primary**

Ostrom's eight design principles are foundational for any non-market, non-state resource allocation system. The directly applicable principles for NEOS are:

1. Clearly defined boundaries of who has access to what.
2. Rules matched to local context, not universal templates.
3. Participatory rule-making by those governed.
4. Community-accountable monitoring.
5. Graduated sanctions (not binary inclusion/exclusion).
6. Accessible, low-cost conflict resolution.
7. External legitimacy for self-governance rights.
8. Nested governance for cross-scale resource issues.

Ostrom demonstrated empirically that shared resources can be sustainably managed without privatization or top-down state control — precisely the model NEOS requires.

**Links**: [Ostrom's 8 Rules — Earthbound Report](https://earthbound.report/2018/01/15/elinor-ostroms-8-rules-for-managing-the-commons/) | [Polycentric Governance of Complex Economic Systems](https://web.pdx.edu/~nwallace/EHP/OstromPolyGov.pdf)

**Participatory Budgeting (Porto Alegre Model) — Secondary**

PB gives sub-jurisdictions (neighborhoods, teams) authority over broader budget allocation, not just their local slice. Since 1989 it has spread to 7,000+ cities. The key mechanisms: neighborhood popular assemblies propose needs, delegate representatives negotiate cross-unit priorities, and final allocation is decided collectively with full visibility. Bologna's extension of PB produced "pacts for shared management of commons" signed by 500+ civic organizations — an exact analog to ETHOS funding pools.

**Link**: [Participatory Budgeting — Wikipedia](https://en.wikipedia.org/wiki/Participatory_budgeting)

**Commons-Based Peer Production (Benkler) — Tertiary**

Benkler's CBPP model explains how non-monetary motivations (intrinsic satisfaction, social status, reputational recognition) can coordinate large-scale production without market pricing. Peer governance must: (a) keep contribution open to all with relevant capacity; (b) elicit prosocial motivations; (c) permit coordination without undermining those motivations. Critically, Benkler notes that introducing monetary incentives into peer production degrades intrinsic motivation — this is directly relevant to Current-Sees design.

**Link**: [Commons-Based Peer Production — Wikipedia](https://en.wikipedia.org/wiki/Commons-based_peer_production)

**HYPHA DHO Tools — Applied Reference**

HYPHA uses a three-token system: utility tokens (value created), cash tokens (liquid redemption), and voice tokens (governance weight). Circles have spending caps and financial boundaries. Decisions use consent-based sense-making. Their key innovation is pushing resource decisions to the edges — circles manage their own treasury allocations within caps set by broader governance.

**Link**: [Hypha DAO Features](https://hypha.earth/features/) | [HYPHA DHO Tools — SEEDS](https://explore.joinseeds.earth/4.-organisation-tools-daos-and-dhos/doing-a-dho-and-dao)

### How Non-Token Systems Handle Resource Allocation Without Market Pricing

Three proven approaches from the research:

1. **Time-banking and contribution tracking**: Track labor hours or effort as the unit of account. Hours contributed entitle members to equivalent access. Used in community land trusts and worker cooperatives. Avoids financialization while maintaining reciprocity.
2. **Needs-based direct allocation**: Communities assess stated needs against available resources and allocate on need + contribution history. Used in intentional communities (Twin Oaks model). Requires high trust and small-enough scale.
3. **Rotating stewardship pools**: Funds are held in pools governed by the circle closest to the relevant activity, with broader bodies setting total pool sizes. This is the PB model applied at organizational scale.

For NEOS specifically, Current-Sees as "influence currencies" map to Benkler's reputational/social motivation system — but only if they remain non-liquid. The moment Current-Sees can be exchanged for material resources, they become a market pricing mechanism with all the competitive distortions that entails.

### Key Design Patterns to Adopt

- **Nested funding pools**: Global NEOS pool sets ETHOS-level caps; ETHOS set circle-level caps; circles allocate to individuals. Each level governs its own domain.
- **Participatory allocation assemblies**: Major funding decisions should involve those most affected (Ostrom Principle 3), not just representatives.
- **Graduated access tiers**: Resource access tied to contribution history (not token balance), with graduated tiers: new member access, sustaining member access, steward access.
- **Monitoring with full transparency**: All resource flows visible to all members — this is Ostrom Principle 4 applied.
- **H.A.R.T. as a graduated sanction tool**: Position H.A.R.T. (Human Accountability and Resource Tracking, per OmniOne docs) as the monitoring layer for Ostrom's Principle 4 and 5 combined.

### Anti-Patterns to Avoid

- **Tokenizing influence before it's stable**: Premature financialization of Current-Sees will create speculative behavior and undermine their legitimacy as governance signals.
- **Majority-controlled pooling**: If one ETHOS or coalition controls the majority of a funding pool, the commons degrades to private control with communal aesthetics.
- **Zero-sum framing**: Resource allocation processes that pit ETHOS against each other destroy inter-unit trust. The process itself must generate integrative solutions.
- **Complexity at the expense of transparency**: Any member should be able to understand and audit how resources flow. Opaque allocation formulas create power asymmetries.

### Suggested Skills for Layer IV

1. **Funding Pool Stewardship** — Managing a circle's resource allocation: tracking inflows, stewarding outflows, maintaining transparency logs.
2. **Participatory Allocation Facilitation** — Running a PB-style allocation assembly within an ETHOS or between ETHOS.
3. **Commons Monitoring** — Applying Ostrom's Principle 4: tracking resource use patterns and detecting over-draw or under-contribution.
4. **Current-See Literacy** — Understanding what Current-Sees measure, what they do not measure, and when using them distorts rather than informs decisions.
5. **Graduated Sanction Application** — Applying Ostrom's Principle 5: graduated response to resource misuse, from acknowledgment to reduced access to formal review.

---

## Layer V: Inter-Unit Coordination

### Most Relevant Frameworks

**Ostrom's Polycentric Governance — Primary**

Polycentric systems have multiple semi-autonomous centers of decision-making that take each other into account in competitive and cooperative relationships while being capable of resolving conflicts. The key property: units must interact, negotiate, and coordinate — polycentricity is not fragmentation but structured interdependence. Ostrom's Principle 8 (nested governance) is the specific design pattern: some things managed locally, others needing regional cooperation, with governance spanning scales.

Real-world examples from research: river basin management across state lines uses inter-state water commissions plus local irrigation districts; wildfire management uses an "all lands management" approach crossing jurisdictional boundaries. Both demonstrate cross-boundary coordination without a singular commanding authority.

**Links**: [Polycentric Systems of Governance — Carlisle 2019](https://onlinelibrary.wiley.com/doi/10.1111/psj.12212) | [Building Blocks of Polycentric Governance — Morrison 2023](https://onlinelibrary.wiley.com/doi/10.1111/psj.12492)

**The Ottoman Millet System — Analogical Reference**

The millet system granted distinct religious/cultural communities (millets) internal autonomy over education, law, family matters, and tax collection, while remaining nominal subjects of the Ottoman sovereign. The NEOS analogy inverts this: ETHOS are like millets but with no sovereign above them. The millet model's lesson is that strong internal autonomy combined with explicit inter-community protocols can sustain multi-community coexistence. Its failure mode — that communities could not negotiate between themselves without appealing to the Ottoman center — is exactly what NEOS must design away from.

**Link**: [The Ottoman Millet System — Wikipedia](https://en.wikipedia.org/wiki/Millet_(Ottoman_Empire)) | [Non-Territorial Autonomy — Tandfonline](https://www.tandfonline.com/doi/full/10.1080/17449057.2015.1101845)

**Holochain Agent-Centric Architecture — Technical Reference**

Holochain's design gives each agent its own sovereign source chain while enabling coordination through a Distributed Hash Table (DHT). Inter-agent coordination happens through: mutual signing of multi-party interactions (both parties record the transaction on their respective chains), bridging between hApps (translating one context into another), and importing validated datasets across applications. This is a technical architecture that mirrors NEOS's governance need: ETHOS-level sovereignty with protocols for cross-ETHOS transactions that don't require a central ledger.

**Link**: [Holochain White Paper Alpha](https://www.holochain.org/documents/holochain-white-paper-alpha.pdf) | [Holochain — P2P Foundation](https://wiki.p2pfoundation.net/Holochain)

**Federated Governance Model — Structural Reference**

Federated models decouple policy-setting from execution: a central governance layer sets interoperability standards and shared principles, while constituent units pursue autonomous strategies within those standards. The key design: economies of scale at the federation level (shared infrastructure, protocols, dispute resolution), autonomy at the unit level (local resource management, local rules, local culture).

**Link**: [Federated Governance Model — Emergent Mind](https://www.emergentmind.com/topics/federated-governance-model)

### Key Design Patterns to Adopt

- **Mutual-signature cross-ETHOS agreements**: Any resource transfer or shared commitment between ETHOS requires explicit consent from both units, recorded in both units' governance logs. No unilateral extraction.
- **Inter-ETHOS liaison roles**: Dedicated roles (not ad-hoc representatives) responsible for maintaining cross-unit coordination protocols and monitoring shared resource flows.
- **Interoperability standards at the SHUR layer**: The SHUR (Shared Human Utility Resources) network should define the protocols for how ETHOS exchange resources, not the content of what they exchange.
- **Graduated engagement tiers**: ETHOS should be able to engage at different intensities — information sharing, resource sharing, joint decision-making — without being forced into full federation.
- **Intermediate collaborative forums**: The research on polycentric governance identifies "intermediate collaborative forums" as essential for coordinating across units without centralizing authority. NEOS Councils may serve this function.

### Anti-Patterns to Avoid

- **Hub-and-spoke inter-unit coordination**: If all cross-ETHOS requests must route through a central node (even nominally neutral), that node becomes de facto sovereign. Build direct peer-to-peer protocols.
- **Silent defaults**: If an ETHOS does not explicitly respond to a cross-unit request, that silence should not be interpreted as consent. Default to non-action.
- **Jurisdiction ambiguity**: Shared resources without a clearly assigned custodian degrade toward either conflict or abandonment. Every shared resource needs a named steward role.
- **Millet failure mode**: Designing inter-ETHOS coordination that only works when mediated by a third ETHOS or council — this recreates the Ottoman center dependency.

### Suggested Skills for Layer V

1. **Cross-ETHOS Request Protocol** — Initiating, formatting, tracking, and closing a resource request or coordination ask across ETHOS boundaries.
2. **Shared Resource Stewardship** — Managing a resource owned jointly by two or more ETHOS: governance rules, usage tracking, conflict handling.
3. **Federation Agreement Design** — Drafting a bilateral or multilateral agreement between ETHOS that defines mutual obligations, exit terms, and dispute resolution.
4. **Inter-Unit Liaison Practice** — Maintaining ongoing coordination relationships across ETHOS boundaries: regular check-ins, signal sharing, escalation.
5. **Polycentric Conflict Navigation** — Resolving disputes where two ETHOS' legitimate authority claims conflict, without recourse to a central arbiter.

---

## Layer VI: Conflict & Repair

### Most Relevant Frameworks

**Transformative Justice — Primary**

Transformative justice (TJ) is a political framework for responding to harm without creating more harm or relying on state punitive mechanisms. As defined by Mia Mingus, TJ responses: do not rely on the state; do not reinforce oppressive norms or vigilantism; and actively cultivate healing, accountability, resilience, and safety for all parties. Community accountability processes involve the whole community as impacted by harm — not just direct parties — and collectively address the conditions that enabled the harm.

This is the correct framework for NEOS because punitive enforcement is unavailable (non-sovereign) and because transformative justice addresses systemic conditions, not just individual incidents.

**Links**: [Transformative Approaches to Conflict — The Commons Library](https://commonslibrary.org/transformative-approaches-to-conflict-resolution/) | [Transformative Justice — NYSCASA](https://nyscasa.org/get-info/transformative-justice/)

**Restorative Justice + NVC — Secondary**

Restorative justice asks "how do we repair the harm?" rather than "how do we punish the wrongdoer?" Marshall Rosenberg's Nonviolent Communication provides the relational skill layer: empathy, active listening, needs-based communication. Practitioners like Dominic Barter have integrated NVC directly into restorative circles. The five Rs of restorative justice — relationship, respect, responsibility, repair, reintegration — map directly onto the stages of a NEOS conflict resolution process.

**Link**: [NVC Restorative Justice — PuddleDancer Press](https://nonviolentcommunication.com/learn-nonviolent-communication/nvc-restorative-justice/)

**Ostrom Principle 6 — Structural Reference**

Ostrom's sixth design principle is that conflict resolution mechanisms must be "informal, cheap, and straightforward" — accessible to everyone without requiring external institutions. This is a direct design constraint for Layer VI: NEOS conflict resolution must not require specialized expertise or escalation to external bodies to initiate.

**Teal's Three-Level Escalation — Process Reference**

Laloux's teal model: (1) direct conversation between parties; (2) peer mediation with a nominated colleague; (3) panel of relevant peers. Notably, the panel has no punitive authority — its role is facilitative, not judicial. This maps well to NEOS's non-coercive constraint.

**Link**: [Teal Organisation — Wikipedia](https://en.wikipedia.org/wiki/Teal_organisation)

### Key Design Patterns to Adopt

- **Three-tier escalation without coercive authority at any tier**: Tier 1 (direct dialogue), Tier 2 (invited peer witness), Tier 3 (community circle). No tier has the authority to punish — each has the authority to name what happened and propose repair.
- **Harm-centered framing**: Conflict protocols should begin with the question "what harm occurred and for whom?" not "who was wrong?" This shifts from adjudication to repair.
- **Community as affected party**: Following TJ principles, the ETHOS or circle in which the conflict occurred is treated as a party to the harm, not merely a bystander.
- **Repair agreements as formal governance artifacts**: Repair agreements should be logged in the NEOS governance memory system (Layer IX), creating accountability and precedent.
- **Coaching escalation**: The "Solutionary Culture" framing in OmniOne docs suggests coaching as a distinct intervention — not therapy, not mediation, but structured support for building the skills the conflict revealed were missing.

### Anti-Patterns to Avoid

- **Forced reconciliation**: Requiring parties to perform forgiveness or resolution before they are ready destroys trust in the process. Repair takes time; the process should hold space, not demand outcomes.
- **Anonymous complaint channels without follow-through**: Harm reporting mechanisms that don't guarantee a response or process are worse than nothing — they signal that the system does not take harm seriously.
- **Punitive framing in restorative language**: Calling something "restorative" while structuring it as a hearing with verdicts is a category error that will corrode trust.
- **Expertise gatekeeping**: If only trained facilitators can initiate a conflict process, most conflicts will go unaddressed. Tier 1 must require zero credentials.

### OmniOne-Specific Considerations

The "Solutionary Culture" framework in OmniOne docs implies that conflict is treated as a signal of systemic gaps, not individual failure. This aligns with TJ's systemic orientation. NEOS should distinguish between: (a) interpersonal harm requiring NVC-based repair circles; (b) role/domain disputes requiring governance-level resolution; (c) systemic harm requiring community-wide deliberation. These have different protocols and different escalation paths.

### Suggested Skills for Layer VI

1. **Harm Circle Facilitation** — Convening and holding a restorative circle: setting conditions, holding space, guiding toward repair agreements without forcing conclusions.
2. **NVC-Based Dialogue** — Applying NVC in high-tension conversations: expressing needs without accusation, receiving the other's experience without defense.
3. **Repair Agreement Drafting** — Formalizing the outcomes of a conflict process into a concrete, trackable agreement with accountability built in.
4. **Escalation Triage** — Assessing which tier of the conflict protocol is appropriate and how to move between tiers when needed.
5. **Coaching Intervention Design** — Identifying when a conflict reflects a skill gap and designing a coaching response rather than a mediation response.
6. **Community Impact Assessment** — Facilitating the broader ETHOS's processing of a conflict that affected the community, not just the direct parties.

---

## Layer VII: Safeguard & Capture Detection

### Most Relevant Frameworks

**The Iron Law of Oligarchy (Michels) — Diagnostic Framework**

Robert Michels (1911) argued that any democratic organization inevitably concentrates power in the hands of a minority. The mechanisms: leaders develop specialized knowledge and communication skills unavailable to ordinary members; members become psychologically dependent on leadership; the organizational need for efficiency creates pressure to defer to those "who know." The law is most operative in large, complex, formally democratic organizations.

Critically, the research identifies conditions that resist oligarchization: engaged member community, independent information/media, tradition of transparency, unbiased elections administration, rotating leadership, and collective decision-making norms. These are not guarantees — they are friction against a thermodynamic tendency.

**Link**: [Iron Law of Oligarchy — Wikipedia](https://en.wikipedia.org/wiki/Iron_law_of_oligarchy) | [The Iron Law of What Again? — Leach 2005](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.0735-2751.2005.00256.x)

**Three Capture Types (from NEOS framing) — Structural Analysis**

NEOS identifies three capture vectors:

1. **Capital capture**: A funding source (or ETHOS with disproportionate resource access) gains de facto veto power through economic dependency.
2. **Charisma capture**: A single personality becomes so central to identity and decision-making that challenging them becomes psychologically unsafe. The research confirms: "when movements become monopolized by one personality, energy orbits charisma rather than purpose."
3. **Emergency capture**: Temporary crisis authority becomes permanent through institutional habit and the difficulty of unwinding emergency norms.

**Link**: [Charismatic Authority — Wikipedia](https://en.wikipedia.org/wiki/Charismatic_authority)

**V-Dem Democracy Indicators — Measurement Reference**

The Varieties of Democracy (V-Dem) project tracks presidentialism index (concentration of power in one person), breadth of democratic institutions, and co-option of opposition as measurable indicators of democratic degradation. These translate into NEOS-specific metrics.

**Link**: [Democracy Indices — Wikipedia](https://en.wikipedia.org/wiki/Democracy_indices)

### Detectable Indicators of Capture

Synthesizing from Michels, V-Dem, and the charisma capture research:

**Capital capture signals**:
- One funding source constitutes more than X% of a unit's total resources.
- Resource requests from certain entities are approved at systematically higher rates.
- Members self-censor proposals that might displease major funders.

**Charisma capture signals**:
- Objections to a specific individual's proposals are withdrawn more often than average.
- Decision records show one person's positions being adopted without modification at high rates.
- New members are onboarded primarily through one individual's personal network.
- The departure of one person would be widely described as "existential" for the unit.

**Emergency capture signals**:
- Emergency protocols are invoked more frequently over time, not less.
- The threshold for declaring emergency becomes subjectively applied rather than criterion-based.
- Post-emergency reviews do not occur or do not result in authority reversion.

**Structural ossification signals (Michels mechanism)**:
- Leadership roles have not changed hands in more than two review cycles.
- Governance meeting attendance by non-leadership members is declining.
- Proposals originating outside leadership are approved at a statistically lower rate.

### Key Design Patterns to Adopt

- **Automated diversity audits**: NEOS governance logs (Layer IX) should generate periodic reports on decision patterns, proposal authorship, proposal approval rates, and resource flow concentration.
- **Capture triggers**: Define specific measurable thresholds that automatically activate a safeguard review — not discretionary, not human-initiated.
- **Structural separation of information and authority**: Whoever controls the information about the system must not also hold primary decision authority. Independent monitoring.
- **Mandatory leadership rotation**: Design roles with maximum tenure; configure the system so role continuity beyond the tenure limit requires explicit community re-authorization, not just the absence of a challenge.
- **Dissent channels with teeth**: It must be structurally safe (no reputational or resource cost) to formally register an objection to a leadership decision.

### Anti-Patterns to Avoid

- **Capture detection by those who would be detected**: Asking a council to assess whether that council is captured is structurally incompetent. Capture detection requires independent monitoring.
- **False positives as a weapon**: Safeguard mechanisms that can be weaponized to harass legitimate leaders are as dangerous as no safeguard at all. Thresholds must be objective.
- **Culture of suspicion**: Permanent surveillance that treats every leader as a potential captor destroys the trust necessary for governance. Capture detection should be systemic, not interpersonal.

### Suggested Skills for Layer VII

1. **Governance Health Audit** — Running a structured review of decision patterns, resource flows, and participation rates to detect concentration signals.
2. **Capture Pattern Recognition** — Identifying the behavioral signatures of capital, charisma, and emergency capture in real governance data.
3. **Safeguard Trigger Design** — Establishing measurable, objective thresholds that automatically activate safeguard protocols.
4. **Independent Monitoring Role** — Filling the monitoring function: collecting and publishing governance data without interpretation or authority.
5. **Structural Diversity Maintenance** — Actively recruiting diverse proposal authorship, decision participation, and funding sources to maintain the structural resistance to oligarchization.

---

## Layer VIII: Emergency Handling

### Most Relevant Frameworks

**Agamben's State of Exception — Diagnostic Warning**

Giorgio Agamben argues that emergency powers — designed as temporary — have become the "normal paradigm of government" in modernity. The problem is not the existence of emergency provisions but the structural tendency for emergency measures to create institutional habits that prove difficult to unwind. Once emergency powers are normalized, they no longer fulfill their assigned function. This is the precise failure mode NEOS must engineer against.

**Links**: [State of Exception — Wikipedia](https://en.wikipedia.org/wiki/State_of_exception) | [COVID-19 Emergency Legislation and Sunset Clauses](https://blogs.ed.ac.uk/covid19perspectives/2020/05/11/covid-19-emergency-legislation-and-sunset-clauses-by-sean-molloy/)

**Sunset Clause Design — Applied Reference**

Legislative research on COVID-era emergency laws demonstrates that automatic sunset periods — where emergency powers expire unless affirmatively renewed — are more effective than sunset clauses requiring active legislative action to end them. The design principle: reversion should be the default, continuation should require effort. This inverts the typical bureaucratic inertia.

**Circuit Breaker Pattern (distributed systems) — Technical Analogy**

The circuit breaker pattern from software engineering offers an exact governance parallel. A circuit breaker has three states: Closed (normal operations), Open (emergency mode, alternative protocols active), and Half-Open (experimental restoration of normal operations, monitored). Transitions are triggered by measurable thresholds, not by human judgment. Once the failure condition clears, the system automatically attempts to restore normal operations, monitoring for recurrence.

Applied to NEOS: emergency governance mode triggers when measurable crisis conditions are met; auto-reversion to normal mode happens when those conditions clear; a half-open monitoring period validates that the crisis has truly passed before full restoration.

**Links**: [Circuit Breaker — Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html) | [Circuit Breaker Pattern — Wikipedia](https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern) | [Circuit Breaker — Azure Architecture](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)

**Cooperative Emergency Protocol Design — Practical Reference**

The research on cooperative emergency management points to continuity of operations planning as the starting point: define what "essential functions" must continue, who has authority over each, and what happens if normal processes are unavailable. The key cooperative adaptation: essential function authority should be pre-distributed (not centralized in crisis), so that the emergency response itself is still polycentric.

### Key Design Patterns to Adopt

- **Criterion-based emergency declaration**: Emergency mode activates when specified objective criteria are met — not at any person's discretion. Criteria should be measurable, external, and agreed in advance.
- **Pre-authorized emergency roles**: Specific roles with specific expanded authority, pre-defined before any crisis. No improvised authority grants during the emergency.
- **Auto-reversion timer**: Emergency authority expires automatically after a defined period. Continuation requires affirmative renewal through normal governance processes — not just the absence of a vote to end it.
- **Minimum necessary authority principle**: Emergency roles receive the minimum expansion needed to address the specific crisis, not general emergency powers.
- **Mandatory post-emergency review**: Once emergency mode ends, a structured review of what triggered it, how authority was used, and whether reversion was complete is required before the emergency infrastructure can be activated again.
- **Circuit breaker states as governance states**: Map the three circuit breaker states (Closed/Open/Half-Open) onto NEOS governance: Normal, Crisis, Recovery. Different protocols apply in each.

### Anti-Patterns to Avoid

- **Vague crisis definitions**: "The situation is serious" is not a trigger criterion. Vague triggers give discretionary authority to declare emergencies, which is itself a capture vector.
- **Centralized emergency authority**: Concentrating all emergency authority in one person or body recreates hierarchy under crisis conditions. Pre-distributed polycentric emergency authority is harder to design but essential.
- **Permanent emergency infrastructure**: Emergency coordination channels, tools, and roles that persist between emergencies normalize crisis governance. They should be archived, not maintained.
- **Agamben's trap**: Treating the resolution of one emergency as justification for maintaining expanded authority "just in case." Each emergency ends; its authority ends with it.

### OmniOne-Specific Considerations

NEOS, as non-sovereign infrastructure, cannot rely on external enforcement even during emergencies. This means emergency protocols must be designed around coordination, not command. The circuit breaker analogy is apt: when a crisis disrupts normal ETHOS coordination, the system should degrade gracefully to a predefined emergency coordination mode rather than improvising centralized authority. The SHUR network as infrastructure layer should have predefined emergency routing protocols that activate without requiring governance decisions.

### Suggested Skills for Layer VIII

1. **Emergency Criteria Design** — Specifying objective, measurable trigger criteria for emergency mode activation, for a specific ETHOS or for NEOS-wide conditions.
2. **Pre-Authorization Protocol Writing** — Drafting the emergency role definitions, authority scopes, and expiration conditions that govern crisis response.
3. **Crisis Coordination Facilitation** — Running a governance process under emergency conditions: faster, more constrained, with explicit authority boundaries.
4. **Emergency Reversion Management** — Managing the transition back from emergency mode: verifying criteria clearance, restoring normal governance, archiving emergency infrastructure.
5. **Post-Emergency Review Facilitation** — Running the mandatory retrospective: what triggered the emergency, how authority was used, whether reversion was complete.

---

## Layer IX: Memory & Traceability

### Most Relevant Frameworks

**Stare Decisis / Legal Precedent System — Primary Structural Reference**

The legal system's precedent architecture provides the most developed model for searchable governance memory. Key features:

- **Ratio decidendi** (the holding): The specific reasoning that creates binding precedent, separated from obiter dicta (non-binding commentary). In NEOS terms: the decision principle, distinct from the context and discussion.
- **Hierarchical precedent**: Decisions from higher-authority bodies bind lower ones. For NEOS: decisions made at the Council level bind ETHOS interpretations of the same principle.
- **Selective publication**: Not every decision merits archiving as precedent — a publication decision distinguishes routine operations from governance-shaping decisions.
- **Evolution through overruling**: Precedents can be explicitly overturned with justification. The overturning is itself a governance artifact. This prevents ossification without eliminating memory.

**Links**: [Stare Decisis — LII Cornell](https://www.law.cornell.edu/wex/stare_decisis) | [Precedent — Wikipedia](https://en.wikipedia.org/wiki/Precedent)

**DAO On-Chain Governance Memory — Applied Reference**

DAOs provide the most operational model for digital governance traceability. Key mechanisms:

- **On-chain voting records**: Every proposal, vote, and execution recorded as a blockchain transaction — immutable and publicly auditable.
- **Governance forums as deliberative record**: Off-chain deliberation captured in governance forums (Snapshot, Discourse) alongside on-chain votes creates a two-layer record: reasoning (off-chain) + decision (on-chain).
- **Governor contracts**: Smart contracts that record proposals, voting periods, quorum requirements, and execution in a standardized format, enabling downstream query and analysis.
- **Dynamic precedent systems**: The DevDAO precedent model allows members to re-evaluate existing precedents, with affirmation making a template canonical for future decisions.

**Links**: [DAO Governance Review — ScienceDirect 2025](https://www.sciencedirect.com/science/article/abs/pii/S0929119925000021) | [Demystifying the DAO Governance Process — arXiv](https://arxiv.org/html/2403.11758v1)

**Agreement Versioning — Software Development Analogy**

Version control systems (Git) provide the pattern for agreement versioning: every change is recorded with author, timestamp, change description, and prior state. Agreements should be versioned the same way: the current version links to all previous versions, with change justifications preserved.

### Key Design Patterns to Adopt

- **Two-layer memory**: Deliberation layer (reasoning, objections raised, amendments proposed) plus Decision layer (final text, vote record, signatories). Both are preserved; they are linked but distinct.
- **Ratio/context separation**: Every recorded decision should explicitly tag its holding (the principle that applies to future cases) separately from the contextual details of the specific case.
- **Precedent classification**: Not every decision is precedent. A classification system identifies: routine operations records (archived but not searchable as precedent), governance decisions (searchable, citable), and constitutional-level decisions (binding on all ETHOS interpretations).
- **Semantic tagging for search**: Decisions should be tagged with domain, ETHOS, date, type, and linked to any decisions they modify or supersede. This enables query: "show me all decisions about resource allocation in agricultural ETHOS since year 3."
- **Mandatory overrule documentation**: When a decision supersedes a prior decision, the new decision must explicitly cite what it overrules and why. Silent overruling is prohibited.

### Anti-Patterns to Avoid

- **Everything is precedent**: If all decisions are precedent, none are. Precision in classification matters more than comprehensiveness.
- **Proprietary or inaccessible archives**: Governance memory locked in one vendor, platform, or format is memory that cannot be trusted. Open formats, portable storage.
- **Memory without search**: Archives that cannot be queried are historical curiosities, not governance infrastructure.
- **Retroactive editing**: The temptation to clean up governance records for consistency or aesthetics must be structurally prevented. Append-only or cryptographically verifiable records.

### Suggested Skills for Layer IX

1. **Decision Record Writing** — Writing governance decision records that capture holding, context, dissenting positions, and implementation notes in a structured, searchable format.
2. **Precedent Search and Application** — Querying the governance memory system and applying relevant precedents to current decisions.
3. **Semantic Tagging** — Applying the classification and tagging schema to new decisions for archival and retrieval.
4. **Agreement Versioning** — Managing the versioned history of a living agreement: tracking changes, justifying amendments, linking to superseded versions.
5. **Precedent Challenge Process** — Formally challenging an existing precedent: identifying its basis, articulating the grounds for revision, and guiding the re-evaluation process.

---

## Layer X: Exit & Portability

### Most Relevant Frameworks

**Hirschman's Exit, Voice, and Loyalty — Primary Analytical Frame**

Hirschman's 1970 framework identifies three responses to organizational decline: Exit (leave), Voice (advocate for change from within), and Loyalty (stay despite dissatisfaction, out of attachment). The critical design insight for NEOS: when exit is costly or difficult, members are forced to use Voice — but if Voice is also suppressed, members become trapped and resentful. Conversely, when exit is too easy, members leave rather than investing in repair, degrading the Voice function.

The NEOS design challenge is to make exit genuinely available (low cost, dignified, with full data portability) while making Voice effective enough that members prefer to use it. Loyalty should be an earned attachment, not a trapped dependency.

**Link**: [Exit, Voice, and Loyalty — Wikipedia](https://en.wikipedia.org/wiki/Exit,_Voice,_and_Loyalty)

**GDPR Right to Data Portability — Legal Reference**

GDPR Article 20 establishes the right to receive personal data in a structured, commonly used, machine-readable format, and to transmit it to another controller. For NEOS, the design principle is: all data generated by a member's participation — contribution records, agreements signed, decisions participated in, resources allocated — belongs to that member and must be exportable in a portable format upon request.

**Links**: [Art. 20 GDPR — gdpr-info.eu](https://gdpr-info.eu/art-20-gdpr/) | [Data Portability — Wikipedia](https://en.wikipedia.org/wiki/Data_portability)

**Platform Cooperative Exit-to-Community Model — Applied Reference**

The "Exit to Community" movement in platform cooperativism provides a design pattern for organizational transitions: converting a company from investor-owned to member-owned is modeled as a dignified exit from one governance structure that is also an entry into another. Applied to NEOS: member departure from an ETHOS should be designed as an exit-to-elsewhere, not an exit-to-void. The departing member's record, contributions, and commitments travel with them.

**Links**: [Exit to Community — Noema](https://www.noemamag.com/exit-to-community/) | [Platform Cooperative — Wikipedia](https://en.wikipedia.org/wiki/Platform_cooperative)

**Twin Oaks Dissolution Protocol — Intentional Community Reference**

Twin Oaks community requires a two-thirds-plus-one supermajority vote with 10-50 days advance notice for community dissolution. Upon dissolution, assets are liquidated and debts settled before any distribution. The precedent: community dissolution is a governance act with specific procedural requirements, not a spontaneous event. Individual member departure is a lighter version of the same principle: formal notice, asset and commitment unwinding, and a clean record of what was contributed and what was honored.

**Link**: [Twin Oaks Bylaws](https://www.twinoaks.org/policies/bylaws)

**Graceful Degradation Design — Technical Principle**

Graceful degradation in systems design means: when a component fails or exits, the remaining system continues functioning at reduced but acceptable capacity, rather than collapsing. For NEOS ETHOS: the departure of any member, role-holder, or even a sub-circle should trigger defined handoff protocols that maintain continuity. No single departure should be catastrophic. This requires designed redundancy: critical roles shared by at least two members, all critical knowledge in governance memory, all commitments documented before departure.

### Key Design Patterns to Adopt

- **Exit-as-right, not exit-as-failure**: The NEOS architecture should treat member departure as a normal lifecycle event, not a governance crisis. Normalized exit reduces the social cost of leaving, which makes Voice more credible (members who stay are there by genuine choice).
- **Full data export on request**: All of a member's records — decision participation, agreements signed, contributions made, resources allocated — must be exportable in a portable format within a defined timeframe. This is non-negotiable.
- **Commitment unwinding protocol**: Before a member exits, outstanding commitments (ongoing roles, pending decisions, resource obligations) must be explicitly handed off, suspended, or closed. This is the governance equivalent of two weeks' notice.
- **Knowledge transfer requirement**: Role-holders exiting critical functions must complete a knowledge transfer before exit is finalized. Governance memory (Layer IX) is the tool — exit completion is linked to documentation completeness.
- **Community departure ritual**: Acknowledge the contribution of departing members in a structured way. Dignified exit reduces resentment and maintains the reputational value of having been part of NEOS.
- **Re-entry provision**: Design exit protocols that leave the door open for re-entry. Returning members should be able to pick up their portable record and re-establish standing without starting from zero.

### Anti-Patterns to Avoid

- **Exit as punishment**: Treating departure as betrayal, or making the exit process painful, produces the worst outcome: members who stay trapped and resentful rather than genuinely committed.
- **Data hostage-taking**: Refusing to export member data, or exporting it in proprietary formats that require specific tools to read, violates data sovereignty and creates vendor-like lock-in in a governance context.
- **Silent departure**: When a member exits without a formal process, critical knowledge, relationships, and commitments evaporate. Governance systems should not allow silent exits from roles with responsibilities.
- **Dissolution without precedent**: Community or ETHOS dissolution without documented protocol leads to chaos and contested claims. The dissolution procedure must be written before it is needed.

### OmniOne-Specific Considerations

In NEOS, members' participation histories — including Current-See records, agreements signed, decisions participated in, and any conflict/repair records — constitute a governance reputation that belongs to the member, not the ETHOS. This portable reputation is an asset in the NEOS ecosystem: a member re-entering or moving between ETHOS should be able to present their governance history as context for re-establishing relationships. The SHUR network should enable cross-ETHOS reputation portability without centralizing that data.

### Suggested Skills for Layer X

1. **Voluntary Exit Protocol Facilitation** — Managing the member exit process: identifying outstanding commitments, coordinating handoffs, completing data export, and acknowledging contribution.
2. **Commitment Unwinding** — Systematically mapping and closing or transferring a departing member's active obligations across roles, agreements, and resource accountabilities.
3. **Portable Record Maintenance** — Maintaining a member's participation record in exportable format; understanding what data is portable and what remains with the ETHOS.
4. **ETHOS Dissolution Governance** — Running the formal process for dissolving an ETHOS: supermajority vote, asset and commitment resolution, archiving, and graceful handoff to the broader NEOS network.
5. **Re-entry Integration** — Welcoming a returning member: reviewing their portable history, negotiating re-entry terms, and re-establishing their standing within the ETHOS.

---

## Cross-Layer Synthesis: Design Principles for the Whole Stack

Across all eight layers, four meta-patterns emerge from the research:

**1. Default to autonomy, not permission**
From Holacracy's blanket authority to Ostrom's right-to-organize, every durable self-governance system grants wide authority within scope rather than narrow permission-by-request. NEOS layers should encode what is restricted, not what is allowed.

**2. Make reversion the default**
From circuit breakers to sunset clauses to domain review schedules, durable systems make continuation require effort and reversion automatic. Emergency authority, temporary roles, and experimental policies should expire by default.

**3. Memory is governance infrastructure, not administrative overhead**
Legal stare decisis, DAO on-chain records, and agreement versioning all treat governance memory as a structural component, not a clerical function. Decisions are only as trustworthy as their documentation.

**4. Exit quality determines voice quality**
Hirschman's core insight: if exit is genuinely available and dignified, Voice becomes more credible and more effective. Members who stay in a NEOS ETHOS should be there by genuine choice. That choice is only meaningful if the alternative is real.

---

## References

- [Holacracy Constitution v5.0](https://www.holacracy.org/constitution/5-0/) — Complete authority model with role, circle, and domain definitions.
- [Holacracy Organization Structure](https://www.holacracy.org/how-it-works/organizational-structure/) — Circle governance overview.
- [Domains and Delegation — Sociocracy 3.0](https://patterns.sociocracy30.org/domain.html) — Domain definition and delegation principles.
- [Clarify and Develop Domains — Sociocracy 3.0](https://patterns.sociocracy30.org/clarify-and-develop-domains.html) — The 11-element domain description and review cadences.
- [Consent Decision-Making — Sociocracy 3.0](https://patterns.sociocracy30.org/consent-decision-making.html) — Consent vs. consensus distinction.
- [Sociocracy 3.0 Practical Guide](https://sociocracy30.org/guide/) — Full framework reference.
- [Teal Organisation — Wikipedia](https://en.wikipedia.org/wiki/Teal_organisation) — Laloux's three pillars and conflict resolution model.
- [Ostrom's 8 Rules for Managing the Commons — Earthbound Report](https://earthbound.report/2018/01/15/elinor-ostroms-8-rules-for-managing-the-commons/) — All eight principles with context.
- [Polycentric Governance of Complex Economic Systems — Ostrom PDF](https://web.pdx.edu/~nwallace/EHP/OstromPolyGov.pdf) — Core polycentric theory.
- [Polycentric Systems of Governance — Carlisle 2019](https://onlinelibrary.wiley.com/doi/10.1111/psj.12212) — Theoretical model of polycentric commons governance.
- [Building Blocks of Polycentric Governance — Morrison 2023](https://onlinelibrary.wiley.com/doi/10.1111/psj.12492) — Empirical analysis of polycentric coordination mechanisms.
- [Participatory Budgeting — Wikipedia](https://en.wikipedia.org/wiki/Participatory_budgeting) — Porto Alegre model and global spread.
- [Participatory Budgeting Project — About PB](https://www.participatorybudgeting.org/about-pb/) — Applied PB implementation guidance.
- [Commons-Based Peer Production — Wikipedia](https://en.wikipedia.org/wiki/Commons-based_peer_production) — Benkler's CBPP model and governance requirements.
- [Peer Production and Cooperation — Benkler](https://www.benkler.org/Peer%20production%20and%20cooperation%2009.pdf) — Original source on prosocial motivation and governance.
- [Hypha DAO Features](https://hypha.earth/features/) — Three-token system and circle treasury model.
- [HYPHA DHO Tools — SEEDS Explorer](https://explore.joinseeds.earth/4.-organisation-tools-daos-and-dhos/doing-a-dho-and-dao) — DHO role definition and resource allocation mechanics.
- [Transformative Approaches to Conflict — The Commons Library](https://commonslibrary.org/transformative-approaches-to-conflict-resolution/) — TJ as governance framework.
- [Transformative Justice — NYSCASA](https://nyscasa.org/get-info/transformative-justice/) — TJ principles and community accountability.
- [NVC Restorative Justice — PuddleDancer Press](https://nonviolentcommunication.com/learn-nonviolent-communication/nvc-restorative-justice/) — NVC and restorative justice integration.
- [Conflict Resolution Accountability Framework — Punch Up Collective](https://www.punchupcollective.org/conflict-resolution-accountability-framework/) — Applied TJ framework for organizations.
- [Iron Law of Oligarchy — Wikipedia](https://en.wikipedia.org/wiki/Iron_law_of_oligarchy) — Michels' original thesis and mechanisms.
- [The Iron Law of What Again? — Leach 2005, Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.0735-2751.2005.00256.x) — Reconceptualization and counterexamples.
- [Charismatic Authority — Wikipedia](https://en.wikipedia.org/wiki/Charismatic_authority) — Weber's type theory and succession problem.
- [Democracy Indices — Wikipedia](https://en.wikipedia.org/wiki/Democracy_indices) — V-Dem and measurable democratic quality indicators.
- [State of Exception — Wikipedia](https://en.wikipedia.org/wiki/State_of_exception) — Agamben's thesis and critiques.
- [COVID-19 Emergency Legislation and Sunset Clauses — Edinburgh](https://blogs.ed.ac.uk/covid19perspectives/2020/05/11/covid-19-emergency-legislation-and-sunset-clauses-by-sean-molloy/) — Sunset clause design principles.
- [Circuit Breaker — Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html) — Original software pattern description.
- [Circuit Breaker Pattern — Wikipedia](https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern) — Three-state model.
- [Circuit Breaker — Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) — Implementation reference.
- [DAO Governance Review — ScienceDirect 2025](https://www.sciencedirect.com/science/article/abs/pii/S0929119925000021) — Current state of DAO governance research.
- [Demystifying the DAO Governance Process — arXiv](https://arxiv.org/html/2403.11758v1) — Proposal lifecycle and on-chain record structure.
- [Stare Decisis — LII Cornell](https://www.law.cornell.edu/wex/stare_decisis) — Legal precedent system overview.
- [Precedent — Wikipedia](https://en.wikipedia.org/wiki/Precedent) — Ratio decidendi, obiter dicta, and precedent hierarchy.
- [Exit, Voice, and Loyalty — Wikipedia](https://en.wikipedia.org/wiki/Exit,_Voice,_and_Loyalty) — Hirschman's framework.
- [Art. 20 GDPR — gdpr-info.eu](https://gdpr-info.eu/art-20-gdpr/) — Right to data portability legal text.
- [Data Portability — Wikipedia](https://en.wikipedia.org/wiki/Data_portability) — Portability frameworks and interoperability requirements.
- [Exit to Community — Noema Magazine](https://www.noemamag.com/exit-to-community/) — Platform cooperative exit model.
- [Platform Cooperative — Wikipedia](https://en.wikipedia.org/wiki/Platform_cooperative) — Member ownership and dissolution governance.
- [Twin Oaks Community Bylaws](https://www.twinoaks.org/policies/bylaws) — Intentional community dissolution protocol.
- [Ottoman Millet System — Wikipedia](https://en.wikipedia.org/wiki/Millet_(Ottoman_Empire)) — Non-territorial autonomy model.
- [Non-Territorial Autonomy — Tandfonline](https://www.tandfonline.com/doi/full/10.1080/17449057.2015.1101845) — Contemporary applications of millet-style autonomy.
- [Holochain White Paper Alpha](https://www.holochain.org/documents/holochain-white-paper-alpha.pdf) — Agent-centric architecture and DHT coordination.
- [Holochain — P2P Foundation Wiki](https://wiki.p2pfoundation.net/Holochain) — Architecture overview and inter-agent bridging.