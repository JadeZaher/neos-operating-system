---
name: nvc-dialogue
description: "Apply Nonviolent Communication in high-tension governance conversations -- transform evaluations into observations, blame into needs, and demands into requests so that conflict becomes navigable."
layer: 6
version: 0.1.0
depends_on: [domain-mapping]
---

# nvc-dialogue

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

NVC dialogue applies identically across ETHOS because it is a communication protocol, not a governance structure. When cross-ETHOS conversations require NVC support, the facilitator can come from either ETHOS or from a neutral facilitation pool. NVC dialogue records from cross-ETHOS interactions are stored in both ETHOS' records with linked entries. The NVC framework's portability is a strength for cross-unit interactions: the observation/feeling/need/request structure works regardless of cultural differences between ETHOS. When a NEOS ecosystem adapts NVC for its cultural context (different emotional vocabularies, different communication norms), the adaptation is documented in the ecosystem's configuration, not in the skill itself.
