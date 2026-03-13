---
name: cross-azpo-request
description: "Initiate and track requests across AZPO boundaries -- resource, information, collaboration, or service requests -- through dual-consent routing that respects both units' autonomy."
layer: 5
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, role-assignment]
---

# cross-azpo-request

## A. Structural Problem It Solves

Without a formal cross-unit request process, coordination between AZPOs depends on personal connections, informal channels, or implicit hierarchy. Whoever knows someone in the other unit gets their needs met; everyone else waits. This skill ensures every cross-AZPO interaction has a traceable origin, dual-consent routing, and transparent status tracking. It prevents larger or wealthier AZPOs from leveraging informal pressure and ensures silence is never treated as consent. Every cross-unit request passes through this process or it does not exist as a governance-recognized interaction.

## B. Domain Scope

This skill applies to any interaction where a participant or body in one AZPO needs something from another AZPO. Request types include:

- **Resource requests** -- financial contributions, physical assets, expertise, or personnel time
- **Information requests** -- governance documents, process templates, operational data
- **Collaboration proposals** -- joint projects, co-development initiatives, shared learning
- **Service requests** -- facilitation support, training delivery, technical assistance
- **Member transfer requests** -- participant mobility between AZPOs

The skill does not cover intra-AZPO requests (use internal ACT processes) or interpersonal requests between members of different AZPOs that do not involve AZPO-level commitments.

## C. Trigger Conditions

- A participant identifies a need that can only be met by another AZPO's resources, knowledge, or capacity
- A circle's work requires coordination with a circle in another AZPO
- A federation agreement triggers a specific cross-unit action
- A shared resource stewardship arrangement generates a request between participating AZPOs
- A liaison identifies a coordination opportunity that requires formal request routing

## D. Required Inputs

- **Requester identity** -- who is proposing, their role, and their circle membership (mandatory)
- **Originating AZPO** -- the AZPO from which the request originates (mandatory)
- **Target AZPO** -- the AZPO to which the request is directed (mandatory)
- **Request type** -- resource, information, collaboration, service, or member transfer (mandatory)
- **Request content** -- specific description of what is being requested (mandatory)
- **Rationale** -- why this request is needed and what problem it addresses (mandatory)
- **Desired timeline** -- when the requester needs a response and fulfillment (mandatory)
- **Authority basis** -- what gives the requester standing to make this request (mandatory)
- **Outbound authorization record** -- evidence that the originating AZPO has consented to sending this request (mandatory)

## E. Step-by-Step Process

1. **Identify need.** The requester determines that a need exists which can only be met by another AZPO. The requester confirms no existing federation agreement or standing arrangement already covers this need.
2. **Draft request.** The requester completes the cross-azpo-request template (`assets/cross-azpo-request-template.yaml`), filling in all required fields including request type, content, rationale, timeline, and authority basis. The draft receives a stub ID: `XAZR-[OriginAZPO]-[TargetAZPO]-[YYYY]-[Seq]`.
3. **Obtain outbound authorization.** The requester presents the draft to their circle or steward for outbound consent. The consent threshold depends on request type: circle-level consent for resource and collaboration requests, steward authorization for information requests, full AZPO-level consent for member transfers. The authorization record is appended to the request.
4. **Transmit to target AZPO.** The authorized request is sent to the target AZPO's designated inbound contact. If no inbound contact is designated, the request goes to the target AZPO's steward. Status updates to `submitted`.
5. **Target AZPO acknowledges.** The inbound contact confirms receipt within 7 days. Status updates to `acknowledged`. If no acknowledgment within 7 days, the requester may send a single follow-up.
6. **Target AZPO routes internally.** The inbound contact routes the request to the relevant circle or body within the target AZPO. That body runs its own ACT process: advice phase (gather input from affected members), consent phase (decide whether to fulfill, modify, or decline). Status updates to `processing`.
7. **Response returned.** The target AZPO sends a documented response: fulfilled, fulfilled with conditions, counter-proposal, declined with rationale, or deferred with timeline. Status updates to `responded`.
8. **Requester AZPO processes response.** The originating AZPO reviews the response. If conditions or a counter-proposal are included, the originating circle runs its own consent round on those terms. If accepted, status updates to `completed`. If the counter-proposal requires further negotiation, a new request cycle begins.
9. **Registration.** The completed request record is registered in both AZPOs' agreement registries with linked entries and a review date if ongoing commitments were created.

## F. Output Artifact

A cross-AZPO request record following `assets/cross-azpo-request-template.yaml`, containing: unique request ID, originating AZPO, target AZPO, requester identity, request type, request content, rationale, desired timeline, authority basis, outbound authorization record, status (submitted/acknowledged/processing/responded/completed/withdrawn), target AZPO's internal routing record, response documentation, conditions or counter-proposals, resolution timeline, and review date if applicable. The record is registered in both AZPOs' agreement registries.

## G. Authority Boundary Check

- **Requester standing:** The requester must hold membership in the originating AZPO plus circle-level or steward authorization for the request type. No individual may send cross-AZPO requests without their own AZPO's outbound authorization.
- **No compulsion:** No AZPO can compel another AZPO to respond, act, or fulfill a request. The target AZPO processes the request through its own governance. The originating AZPO has zero authority over the target's internal process.
- **No bypass:** Cross-AZPO requests from ecosystem-level bodies (OSC, TH) follow the same process. OSC membership does not grant the right to bypass another AZPO's consent process.
- **Scope limits:** A request record does not constitute an ongoing agreement. Ongoing commitments require formalization through the federation-agreement skill.

## H. Capture Resistance Check

**Size pressure.** A larger AZPO submits a high volume of requests that overwhelms a smaller AZPO's processing capacity. Resistance: each AZPO controls its own inbound processing cadence. Request volume does not create obligation to respond faster. The smaller AZPO may set processing limits and communicate expected response timelines without this being treated as non-cooperation.

**Wealth pressure.** A wealthier AZPO conditions cooperation on financial contribution or frames requests as economically beneficial to pressure acceptance. Resistance: the target AZPO's consent process evaluates requests on governance merits, not financial incentives. Funding conditions attached to requests are documented as capture vectors during the advice phase.

**Urgency manipulation.** A requester frames a routine request as an emergency to bypass normal processing timelines. Resistance: emergency threshold is assessed independently by the target AZPO's inbound contact. Urgency declared by the requester is not sufficient. Emergency requests still require a formal consent round.

**Reciprocity pressure.** Past cooperation is cited as creating obligation for the current request. Resistance: each request is evaluated on its own merits. Prior cooperation creates no current obligation. Reciprocity reasoning flagged during advice must be set aside in the consent decision.

## I. Failure Containment Logic

- **No response within timeline:** The requester may send one formal follow-up after the deadline. If a liaison exists, the liaison escalates through inter-unit-liaison channels. If still no response, the request status is set to `stale`. The originating AZPO cannot force a response. They may reduce their engagement tier or initiate polycentric-conflict-navigation if the non-response reflects a structural problem.
- **Request declined:** The originating AZPO may modify the request based on the stated rationale and resubmit once. A second decline is final. The originating AZPO accepts or seeks the need elsewhere.
- **Counter-proposal deadlock:** If neither side accepts the other's terms after one round of counter-proposals, the request is closed as concluded without agreement. This is a legitimate outcome.
- **Unintended obligation:** A completed request is cited as creating ongoing commitments not explicitly agreed to. Either AZPO may invoke a scope review. Ongoing commitments require a federation-agreement, not a request record.
- **Outbound authorization fails:** The originating circle declines to authorize. The request is not sent. The requester may revise and seek internal authorization again.

## J. Expiry / Review Condition

- Open requests with no response after 30 days are marked `stale` and the requester is notified
- Requests in `processing` for more than 45 days without status update trigger an inquiry to the target AZPO
- Completed requests creating ongoing commitments must have a review date set at completion (recommended: 6 months)
- All request records are retained in both registries indefinitely as documentation

## K. Exit Compatibility Check

- **Requester exits originating AZPO:** Open requests are voided unless the originating AZPO designates a new requester within 14 days. The target AZPO is notified.
- **Inbound contact exits target AZPO:** The target AZPO reassigns to a new contact. Processing continues.
- **Originating AZPO dissolves:** All outbound requests close with documentation. Target AZPOs are notified within 7 days.
- **Target AZPO dissolves:** All inbound requests close with documentation. Originating AZPOs seek needs elsewhere.
- **Completed requests:** Records and outcomes survive exit. Ongoing commitments terminate unless explicitly transferred.

## L. Cross-Unit Interoperability Impact

This skill is the cross-unit interaction primitive for all of Layer V. Every other Layer V skill that requires one AZPO to initiate action with another uses this skill's request format and dual-consent routing pattern. The shared-resource-stewardship skill uses it for initial resource proposals. The federation-agreement skill uses it for negotiation initiation. The inter-unit-liaison skill uses it as the fallback when no liaison is available. Polycentric conflict navigation references request records that reveal structural incompatibilities.

Request records are registered in both participating AZPOs' agreement registries with linked entries. If a cross-AZPO registry exists, records are indexed there as well.

## OmniOne Walkthrough

Devi, Education circle lead at the Bali SHUR, has been developing a restorative conflict curriculum for new member onboarding. During a cross-SHUR learning exchange, she discovers that the Costa Rica SHUR's Education circle -- led by Rosa -- has already built a highly regarded conflict resolution training module. Devi wants to adapt it for Bali's context.

**Trigger.** Devi brings the idea to the Bali Education circle's weekly sync. The circle agrees the Costa Rica module would accelerate their curriculum work. They reach consent to authorize Devi to draft a cross-AZPO request.

**Drafting.** Devi fills out the template: request type = information + collaboration, content = access to Costa Rica's conflict resolution training module (curriculum, facilitator guide, case scenarios) plus permission to adapt for Bali's context, rationale = Bali's next member cohort begins in six weeks, timeline = response within 14 days. She assigns draft ID `XAZR-BaliSHUR-CostaRicaSHUR-2026-004`.

**Outbound authorization.** Devi presents the draft to the Bali Education circle. Six of seven members participate. During advice, Kenji wants the request to include an attribution commitment. Devi adds it. Consent: all six consent. Authorization recorded.

**Transmission.** Devi sends the request to Mateo, Costa Rica's inbound contact. Mateo acknowledges within two days. Status: `acknowledged`.

**Costa Rica routing.** Mateo routes the request to Rosa and the Education circle. Rosa opens a 5-day advice window. Lucia raises a concern: the module is still evolving, and an in-progress adaptation could produce inconsistency. She proposes that Bali submit adaptations for a 14-day review before deployment. Andres suggests co-developing the module together. Both inputs are documented.

In the consent round, Lucia's review clause is integrated as a condition. Andres's co-development idea becomes an optional counter-proposal. All five members consent. Status: `responded`.

**Response to Bali.** Mateo sends the response: access granted with the adaptation review condition, plus a counter-proposal for co-development.

**Edge case: counter-proposal routing.** Devi brings both elements to the Bali Education circle. The review condition is accepted (consistent with Kenji's attribution concern). On the co-development counter-proposal, the circle authorizes Devi to send a follow-up request (`XAZR-BaliSHUR-CostaRicaSHUR-2026-005`) asking Andres to draft a scope document. This new request follows the same routing from Step 1.

**Closure.** The original request is marked `completed`. Request record `XAZR-BaliSHUR-CostaRicaSHUR-2026-004` is registered in both registries with the accepted condition and a 3-month review date.

## Stress-Test Results

### 1. Capital Influx

The Bali SHUR receives a large external grant that makes it the most resourced AZPO in OmniOne. When Bali submits a request to Costa Rica for facilitation support, the request includes a generous stipend offer -- significantly above Costa Rica's standard rate. Costa Rica's Education circle notices the financial framing during their advice phase. Rosa flags it as wealth pressure: the circle should evaluate whether the work fits their capacity and priorities, not whether the stipend is attractive. The consent round evaluates the request on governance merits. Costa Rica sets the stipend at their standard rate, not Bali's offered amount, to prevent a financial dependency dynamic. The response documents the rate adjustment. Bali's circle accepts. The wealth pressure dynamic is logged in the request record as a reference for future interactions.

### 2. Emergency Crisis

A wildfire forces the Costa Rica SHUR to evacuate 18 members. Costa Rica's steward submits an emergency cross-AZPO request to Bali for financial support from their commons fund. Bali's steward confirms the emergency threshold is met and convenes an emergency quorum within four hours. The advice window compresses to 60 minutes. Wayan asks about liquidity -- confirmed sufficient. The consent round runs: four consent, one stands aside, one requests a 20% reduction with a 30-day review. Modification integrated. Response sent within six hours. The request record documents the emergency declaration, compressed timeline, and review date. Post-crisis, both SHURs assess whether a standing mutual-aid protocol should be formalized through the federation-agreement skill.

### 3. Leadership Charisma Capture

Nia, an OSC member and OmniOne co-founder, informally asks Mexico SHUR's steward Rodrigo to "lend" two permaculture practitioners to a Bali project. Rodrigo feels social pressure to agree -- Nia's stature makes refusal feel like obstruction. But Rodrigo recognizes this requires Mexico's own authorization process regardless of who is asking. He routes it through cross-azpo-request. When Mexico's Permaculture circle reviews, one member notes that losing two practitioners for three months strains Mexico's own work. The consent round produces a counter-proposal: one practitioner for six weeks with a reciprocal exchange. The process does not have an "expedited by prominent member" track. Nia's status is documented as context but plays no role in the consent decision.

### 4. High Conflict

The Bali and Mexico SHURs have a deep philosophical disagreement about financial contribution models. When Mexico submits a request for Bali's space agreement templates, the request arrives in a charged relational context. Bali's Housing circle lead, Putu, notes that sharing templates could be used adversarially at ecosystem forums. Three members want to decline; two want to share with conditions. During the consent round, an objection surfaces: declining to share governance documents because of philosophical tension sets a dangerous precedent. The integration round finds a third path: share the templates with a framing document explaining the principles behind Bali's approach. Consent achieved. The philosophical conflict does not block a legitimate information request.

### 5. Large-Scale Replication

OmniOne grows to 15 SHURs and 80 circles across four continents. Cross-AZPO requests multiply to 30-50 per month. Each SHUR designates a trained inbound contact who processes requests weekly. The unique ID format scales with annual sequence resets per AZPO pair. High-volume pairs establish standing federation agreements that pre-authorize certain request types, reducing per-request ACT overhead. Low-frequency pairs use the full process. No central routing body is created -- each AZPO manages its own queues. The skill's governance structure remains unchanged; what scales is the administrative support layer.

### 6. External Legal Pressure

Indonesia issues a regulation requiring co-living spaces to document all "resource transfer agreements" with international partners. The Bali SHUR's legal steward advises that cross-AZPO request records already function as documentation and could satisfy the requirement with a compliance notation field. Bali adds this field through their own ACT process -- a Bali-specific measure, not an ecosystem mandate. Other SHURs are informed but not required to adopt it. The skill's portability principle is maintained: Bali's compliance layer is configuration, not a protocol change.

### 7. Sudden Exit of 30% of Participants

Following a contentious expansion decision, 12 of 40 participants exit across three SHURs. The request registry shows 11 open requests. For each, the relevant AZPO reviews whether the exiting participant was the requester or inbound contact. Requests with departed requesters get a 14-day hold; originating AZPOs designate replacements or close the requests. Requests with departed contacts are reassigned to backups. No completed request records are invalidated. Affected AZPOs notify cross-AZPO partners to expect slower response times for 30 days while they stabilize. The 30% departure triggers review of all standing federation agreements and liaison roles involving departed participants.
