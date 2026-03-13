---
name: nvc-dialogue
description: "Apply Nonviolent Communication in high-tension governance conversations -- transform evaluations into observations, blame into needs, and demands into requests so that conflict becomes navigable."
layer: 6
version: 0.1.0
depends_on: [domain-mapping]
---

# nvc-dialogue

## A. Structural Problem It Solves

Governance conversations collapse when participants conflate their feelings about a situation with structural observations, when evaluations masquerade as facts, and when unspoken needs drive surface-level disagreements. Without a communication protocol, high-tension moments default to whoever argues most forcefully or whoever shuts down first. This skill provides a structural framework based on Marshall Rosenberg's Nonviolent Communication that separates observations from evaluations, feelings from thoughts, needs from strategies, and requests from demands. It transforms conflict from a win/lose dynamic into a diagnostic process where participants can identify what they actually need and make actionable requests. The framework applies within harm circles, ACT processes, cross-AZPO negotiations, and any governance conversation where tension is rising.

## B. Domain Scope

This skill applies to any governance conversation within the ecosystem where tension, disagreement, or conflict is present or emerging. It functions as a communication protocol layered onto existing governance processes, not a standalone conflict resolution mechanism. NVC dialogue applies within: harm circles (as the communication structure for rounds), ACT consent phases (reframing objections from attacks into needs-based contributions), cross-AZPO negotiations, circle meetings, and informal governance conversations between participants. Out of scope: NVC is not therapy, not a substitute for harm circles when structural harm has occurred, and not a tool for avoiding accountability by redirecting attention to feelings.

## C. Trigger Conditions

- A facilitator observes a governance conversation becoming evaluative rather than observational
- A participant requests NVC support during a heated interaction
- A harm circle convener applies NVC structure to the circle's rounds
- An ACT consent phase encounters objections framed as personal attacks rather than structural concerns
- A mediator in a Tier 2 peer mediation applies NVC to help parties surface underlying needs
- A written proposal or objection contains evaluative language that could escalate conflict

## D. Required Inputs

- **Conversation context**: the governance process where NVC is being applied (harm circle, ACT phase, mediation, informal dialogue)
- **Participants**: the people in the conversation, their roles, and the power dynamics present
- **Presenting conflict**: the surface-level disagreement or tension that prompted NVC application
- **Facilitator/guide identity**: who is applying the NVC framework -- may be a dedicated NVC facilitator, the process facilitator, an AI agent, or a participant self-applying
- **Domain reference**: the governance domain where the conversation is occurring, verified against domain-mapping

## E. Step-by-Step Process

1. **Identify the need for NVC.** The facilitator or participant recognizes that the conversation contains evaluative language, blame framing, or unspoken needs driving surface disagreement. The facilitator names the shift: "I notice we are moving from observations to evaluations. Let me offer a structure that might help."
2. **Separate observation from evaluation.** The facilitator helps participants restate their concerns as specific, observable behaviors rather than character judgments. Example transformation: "You always dominate meetings" becomes "In the last three meetings, you spoke for 15 of the 30 minutes while five other members each spoke for 3 minutes or less."
3. **Surface feelings.** The facilitator invites participants to name their feelings about the observation -- not thoughts disguised as feelings. "I feel that you are being unfair" is a thought. "I feel frustrated and unheard" is a feeling. The facilitator gently redirects thought-feelings to actual feelings.
4. **Identify underlying needs.** The facilitator helps participants articulate the needs behind their feelings. Feelings point to needs: frustration often points to a need for fairness or inclusion; anxiety often points to a need for safety or predictability. The facilitator asks: "What need of yours is not being met in this situation?"
5. **Formulate requests.** The facilitator helps participants transform their needs into concrete, actionable, present-tense requests. A request must be specific, doable, and refusable (if it cannot be refused, it is a demand). Example: "I request that speaking time in our meetings be tracked and distributed so that no one speaks for more than 5 minutes before others have had a turn."
6. **Document the dialogue.** The facilitator records the observations, feelings, needs, and requests surfaced during the dialogue using the dialogue-record-template.yaml. Any agreements reached are documented separately through the repair-agreement or agreement-creation skill.
7. **Integrate into the governance process.** The NVC-reframed contributions re-enter the governance process they came from. In an ACT consent phase, the reframed objection replaces the original evaluative one. In a harm circle, the NVC-structured statements become part of the circle record.

## F. Output Artifact

An NVC dialogue record following `assets/dialogue-record-template.yaml`, containing: dialogue ID, date, governance context (which process the dialogue occurred within), participants, the presenting conflict, the NVC transformations documented (original statement, observation, feeling, need, request for each participant), any agreements or commitments that emerged, and the facilitator's notes. The record serves as both a process artifact and a reference for follow-up conversations.

## G. Authority Boundary Check

- The **NVC facilitator** has communication-support authority only. They help participants reframe statements; they cannot invalidate a participant's experience by declaring "that is an evaluation, not an observation" as a way to dismiss legitimate concerns.
- **No participant** can be required to use NVC as a precondition for being heard. NVC is offered as a tool, not imposed as a compliance standard. A participant who cannot or will not use NVC framing still has full standing to participate in governance processes.
- The **facilitator cannot use NVC structure to silence** participants whose communication style is less polished. Requiring "proper NVC form" before accepting an objection is a capture vector, not a governance protection.
- Authority scope is verified against domain-mapping: the NVC facilitator operates within the governance process they are supporting, not beyond it.

## H. Capture Resistance Check

**Capital capture.** A financially influential participant uses polished NVC language to frame their position as "needs-based" while subtly pressuring others to yield. The facilitator watches for asymmetric fluency: when one participant uses NVC flawlessly while the other struggles, the facilitator provides equal support to the less fluent participant rather than rewarding rhetorical skill. Financial status does not grant communication authority.

**Charismatic capture.** A charismatic leader uses NVC fluency to dominate conversations by appearing more "evolved" or "nonviolent" than other participants, creating a dynamic where disagreeing with the charismatic person feels like being "violent." The facilitator ensures NVC is applied to all participants equally, including the charismatic one. When a charismatic participant's "request" functions as a social demand (people feel unable to refuse because of the person's status), the facilitator names the power dynamic.

**Emergency capture.** Crisis framing is used to bypass NVC process: "We do not have time for feelings, we need to act." Even under compressed timelines, the observation/needs/request structure takes minutes, not hours. The facilitator offers the abbreviated form: one observation, one need, one request per participant, documented and revisited post-crisis.

**Informal capture.** NVC becomes a tone-policing mechanism: participants are told their concerns are invalid because they were not expressed "nonviolently." The skill explicitly prohibits this use. NVC is a tool for the speaker to clarify their own communication, not a standard imposed on others. Any use of NVC to silence, dismiss, or gatekeep is flagged as a capture vector.

## I. Failure Containment Logic

- **Participant refuses NVC framing**: the governance process continues without NVC. The participant's contributions are accepted in their natural form. The facilitator may privately offer to help reframe after the meeting if the participant is interested.
- **NVC reveals irreconcilable needs**: the dialogue is documented and the underlying conflict escalates per escalation-triage. NVC surfaces the disagreement clearly; it does not guarantee resolution.
- **Facilitator applies NVC unevenly** (helping one party but not the other): any participant can flag uneven application. The facilitator adjusts or is replaced. Uneven NVC application is itself a form of bias.
- **NVC is weaponized as tone-policing**: the governance process pauses, the facilitator names the dynamic, and the conversation resumes with explicit permission for participants to communicate in their natural style. The incident is documented.
- **NVC stalls the process** (endless needs-exploration without reaching requests): the facilitator sets a time boundary and moves the conversation to the request phase. Needs that remain unclear are documented for follow-up.

## J. Expiry / Review Condition

NVC dialogue records do not expire. They serve as reference documents for ongoing relationships and governance patterns. If the dialogue was part of a harm circle or ACT process, the record's review cycle follows the parent process. If the dialogue surfaced needs that were not yet addressed, those needs are flagged in the record and trigger a follow-up conversation at 30 days. The NVC skill itself is reviewed annually as part of Layer VI's overall review cycle. Minimum review interval for unresolved needs documented in a dialogue record: 30 days.

## K. Exit Compatibility Check

When a participant exits the ecosystem, NVC dialogue records involving that participant remain valid as governance records. Commitments made during NVC-facilitated conversations follow the standard exit protocol: in-progress commitments get a 30-day wind-down, personal reconciliation elements cease, and structural agreements made during the dialogue persist. The exiting participant's NVC-documented needs and requests are archived -- they do not create ongoing obligations for the remaining community. If the exiting participant was an NVC facilitator, their facilitation role is reassigned within 14 days.

## L. Cross-Unit Interoperability Impact

NVC dialogue applies identically across AZPOs because it is a communication protocol, not a governance structure. When cross-AZPO conversations require NVC support, the facilitator can come from either AZPO or from a neutral facilitation pool. NVC dialogue records from cross-AZPO interactions are stored in both AZPOs' records with linked entries. The NVC framework's portability is a strength for cross-unit interactions: the observation/feeling/need/request structure works regardless of cultural differences between AZPOs. When a NEOS ecosystem adapts NVC for its cultural context (different emotional vocabularies, different communication norms), the adaptation is documented in the ecosystem's configuration, not in the skill itself.

## OmniOne Walkthrough

During an ACT consent phase for a proposal to restructure the AE circle's meeting schedule, tension erupts. Kofi, an AE member, objects to the proposal and says: "This proposal is disrespectful to everyone who actually does the work around here. The people pushing this have no idea what our daily operations look like, and they are just playing governance games." Saba, the proposal author and a TH member, responds: "That is exactly the kind of gatekeeping that prevents new members from contributing. You always shut down ideas from people outside your circle."

The facilitator, Ines, recognizes the conversation has shifted from structural objection to personal evaluation. She pauses the consent phase and offers NVC support. "I notice strong feelings in the room. Before we continue with the consent process, I want to offer a structure that might help us hear what is underneath these positions. Kofi, would you be willing to try restating your concern starting with what you have specifically observed?"

Kofi, with Ines's guidance, restates: "In the last two proposals about AE scheduling, the advice phase did not include any AE members who work the morning operations shift. The proposals were drafted without consulting the people whose daily schedule would change." (Observation.) "I feel frustrated and anxious." (Feeling.) "I need to know that decisions about our work schedule involve the people doing the work." (Need.) "I request that any proposal affecting AE operations include a mandatory advice consultation with at least three members who work the affected shifts." (Request.)

Saba, also guided by Ines, restates: "In the last three meetings, when I or other TH members have brought scheduling proposals, Kofi has used the phrase 'people who actually do the work' four times, which I experience as implying that TH members do not contribute meaningfully." (Observation.) "I feel dismissed and unwelcome." (Feeling.) "I need to be recognized as a legitimate contributor to governance processes that affect the whole community." (Need.) "I request that objections focus on the proposal's content rather than questioning the proposer's standing to propose." (Request.)

Edge case: Ines notices that Kofi is more comfortable with NVC framing than Saba -- Kofi has attended NVC workshops before. Ines spends extra time supporting Saba's reframing rather than letting Kofi's fluency dominate. She also checks that Kofi's "request" is genuinely refusable and not a demand disguised in NVC language. The consent phase resumes with both reframed contributions integrated: Kofi's objection becomes a concrete amendment (mandatory AE shift-worker consultation) rather than a blanket rejection, and Saba's proposal is modified to include the consultation step. The dialogue record is filed as NVC-AE-2026-003, linked to the ACT process record.

## Stress-Test Results

### 1. Capital Influx

A large grant is conditioned on OmniOne adopting a specific program structure. During the ACT consent phase, a donor-aligned participant uses fluent NVC to frame the grant conditions as "community needs" -- "I observe that our funding is limited. I feel concerned. I need financial sustainability. I request we accept the grant conditions." The NVC facilitator recognizes that the "need" is actually a strategy (accepting specific grant conditions) disguised as a universal need (financial sustainability). The facilitator separates the need from the strategy: "Financial sustainability is a shared need. The specific grant conditions are one strategy to meet that need. Are there other strategies?" This reframing opens the conversation to alternative funding approaches without dismissing the financial concern. The NVC structure prevents capital from converting financial leverage into rhetorical authority by maintaining the distinction between needs (universal) and strategies (debatable).

### 2. Emergency Crisis

A natural disaster forces OmniOne into rapid decision-making about resource allocation. Participants are stressed, sleep-deprived, and speaking in evaluative shorthand. A facilitator applies abbreviated NVC: each participant states one observation, one need, and one request before the group decides. The compressed NVC round takes 15 minutes with 8 participants. Despite the emergency, the structure prevents the loudest or most panicked voice from dominating resource allocation. Post-crisis, the full NVC dialogue records are reviewed to identify needs that were deferred under emergency compression. The review triggers follow-up conversations for any deferred needs within 30 days of the crisis ending. Emergency does not erase the requirement to hear all participants; it compresses the time in which hearing happens.

### 3. Leadership Charisma Capture

A charismatic OmniOne founder uses impeccable NVC language in every conversation, creating a dynamic where disagreeing with the founder feels "violent" by comparison. Other participants struggle to articulate objections because the founder's communication is so polished that opposition seems unreasonable. The NVC facilitator addresses the asymmetry directly: "I notice that one participant's NVC fluency may be creating a dynamic where others feel their communication style is inadequate. NVC is a tool for clarity, not a ranking system. Everyone's contribution has equal standing regardless of how it is framed." The facilitator provides active support to less fluent participants and explicitly names when the founder's "requests" carry implicit social pressure. The skill's prohibition on using NVC as a tone-policing mechanism is the structural safeguard -- disagreement expressed in plain, direct language is equally valid.

### 4. High Conflict / Polarization

Two factions in an OmniOne AZPO are polarized over resource allocation priorities -- one faction wants investment in physical infrastructure, the other in digital tools. The conversation has devolved into mutual accusations of "not understanding the real needs of the community." The NVC facilitator applies the framework to both factions simultaneously. Each faction's representative states observations (specific resource gaps they have experienced), feelings (frustration, anxiety about community direction), needs (physical safety, operational efficiency), and requests (specific budget allocations). The NVC process reveals that both factions share underlying needs for operational effectiveness and community resilience -- their disagreement is at the strategy level, not the needs level. This realization, surfaced through NVC's needs/strategy distinction, opens space for a "Doing Both Solution" per GAIA Level 4 coaching. The facilitator routes the reframed positions back into the ACT process where they can be integrated as concrete amendments.

### 5. Large-Scale Replication

As OmniOne scales to 5,000 participants across 15 locations, NVC facilitation capacity must scale proportionally. Each SHUR location trains at least two NVC-fluent facilitators through a peer-learning model. NVC dialogue records use a standardized template across all locations, enabling pattern analysis (are certain types of conflicts recurring across locations?). AI agents assist by flagging evaluative language in written proposals and suggesting NVC reframes before conversations escalate. The NVC skill's simplicity (four components: observation, feeling, need, request) makes it highly replicable -- it does not require certified professionals for routine application. Complex cases (deeply entrenched polarization, cross-cultural communication barriers) can escalate to experienced NVC practitioners. The dialogue-record-template.yaml remains identical at every scale; what changes is the volume of records and the value of cross-location pattern analysis.

### 6. External Legal Pressure

A government regulation requires OmniOne to document all "dispute resolution proceedings" for regulatory compliance. NVC dialogue records, which document observations, feelings, needs, and requests, are examined by regulators. The records demonstrate a structured, voluntary communication process -- not coerced mediation. The NVC skill's documentation standard (process, not private disclosures) means the records contain the structural transformation (evaluative statement to NVC-reframed contribution) without exposing private emotional content beyond what participants consented to share. If regulators require additional documentation, those requirements enter the ecosystem through agreement-creation as jurisdictional compliance. The NVC process itself does not change to satisfy external requirements -- it already documents what happened and what was agreed, which satisfies most regulatory transparency standards.

### 7. Sudden Exit of 30% of Participants

After a mass departure, the remaining community is emotionally raw. Governance conversations are charged with grief, blame, and anxiety. NVC becomes especially valuable in this context -- it helps remaining participants distinguish between their feelings about the departure (grief, betrayal, relief) and their observations about governance gaps created by the exit (specific roles unfilled, specific agreements without stewards). The facilitator applies NVC to community processing sessions, helping participants articulate needs (stability, trust, clarity about what happens next) and make requests (review of agreements, reassignment of roles, community dialogue about the departure's causes). NVC dialogue records from this period become critical governance artifacts -- they document the community's processing and the specific needs that emerged, informing the governance adaptation that follows a mass exit. Existing NVC dialogue records involving departed members remain valid; they are not retroactively modified.
