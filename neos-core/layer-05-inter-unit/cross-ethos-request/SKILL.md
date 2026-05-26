---
name: cross-ethos-request
description: "Initiate and track requests across ETHOS boundaries -- resource, information, collaboration, or service requests -- through dual-consent routing that respects both units' autonomy."
layer: 5
version: 0.1.0
depends_on: [agreement-creation, act-consent-phase, role-assignment]
---

# cross-ethos-request

## C. Trigger Conditions

- A participant identifies a need that can only be met by another ETHOS's resources, knowledge, or capacity
- A circle's work requires coordination with a circle in another ETHOS
- A federation agreement triggers a specific cross-unit action
- A shared resource stewardship arrangement generates a request between participating ETHOS
- A liaison identifies a coordination opportunity that requires formal request routing

## D. Required Inputs

- **Requester identity** -- who is proposing, their role, and their circle membership (mandatory)
- **Originating ETHOS** -- the ETHOS from which the request originates (mandatory)
- **Target ETHOS** -- the ETHOS to which the request is directed (mandatory)
- **Request type** -- resource, information, collaboration, service, or member transfer (mandatory)
- **Request content** -- specific description of what is being requested (mandatory)
- **Rationale** -- why this request is needed and what problem it addresses (mandatory)
- **Desired timeline** -- when the requester needs a response and fulfillment (mandatory)
- **Authority basis** -- what gives the requester standing to make this request (mandatory)
- **Outbound authorization record** -- evidence that the originating ETHOS has consented to sending this request (mandatory)

## E. Step-by-Step Process

1. **Identify need.** The requester determines that a need exists which can only be met by another ETHOS. The requester confirms no existing federation agreement or standing arrangement already covers this need.
2. **Draft request.** The requester completes the cross-ethos-request template (`assets/cross-ethos-request-template.yaml`), filling in all required fields including request type, content, rationale, timeline, and authority basis. The draft receives a stub ID: `XAZR-[OriginETHOS]-[TargetETHOS]-[YYYY]-[Seq]`.
3. **Obtain outbound authorization.** The requester presents the draft to their circle or steward for outbound consent. The consent threshold depends on request type: circle-level consent for resource and collaboration requests, steward authorization for information requests, full ETHOS-level consent for member transfers. The authorization record is appended to the request.
4. **Transmit to target ETHOS.** The authorized request is sent to the target ETHOS's designated inbound contact. If no inbound contact is designated, the request goes to the target ETHOS's steward. Status updates to `submitted`.
5. **Target ETHOS acknowledges.** The inbound contact confirms receipt within 7 days. Status updates to `acknowledged`. If no acknowledgment within 7 days, the requester may send a single follow-up.
6. **Target ETHOS routes internally.** The inbound contact routes the request to the relevant circle or body within the target ETHOS. That body runs its own ACT process: advice phase (gather input from affected members), consent phase (decide whether to fulfill, modify, or decline). Status updates to `processing`.
7. **Response returned.** The target ETHOS sends a documented response: fulfilled, fulfilled with conditions, counter-proposal, declined with rationale, or deferred with timeline. Status updates to `responded`.
8. **Requester ETHOS processes response.** The originating ETHOS reviews the response. If conditions or a counter-proposal are included, the originating circle runs its own consent round on those terms. If accepted, status updates to `completed`. If the counter-proposal requires further negotiation, a new request cycle begins.
9. **Registration.** The completed request record is registered in both ETHOS' agreement registries with linked entries and a review date if ongoing commitments were created.

## F. Output Artifact

A cross-ETHOS request record following `assets/cross-ethos-request-template.yaml`, containing: unique request ID, originating ETHOS, target ETHOS, requester identity, request type, request content, rationale, desired timeline, authority basis, outbound authorization record, status (submitted/acknowledged/processing/responded/completed/withdrawn), target ETHOS's internal routing record, response documentation, conditions or counter-proposals, resolution timeline, and review date if applicable. The record is registered in both ETHOS' agreement registries.

## G. Authority Boundary Check

- **Requester standing:** The requester must hold membership in the originating ETHOS plus circle-level or steward authorization for the request type. No individual may send cross-ETHOS requests without their own ETHOS's outbound authorization.
- **No compulsion:** No ETHOS can compel another ETHOS to respond, act, or fulfill a request. The target ETHOS processes the request through its own governance. The originating ETHOS has zero authority over the target's internal process.
- **No bypass:** Cross-ETHOS requests from ecosystem-level bodies (OSC, TH) follow the same process. OSC membership does not grant the right to bypass another ETHOS's consent process.
- **Scope limits:** A request record does not constitute an ongoing agreement. Ongoing commitments require formalization through the federation-agreement skill.

## H. Capture Resistance Check

**Size pressure.** A larger ETHOS submits a high volume of requests that overwhelms a smaller ETHOS's processing capacity. Resistance: each ETHOS controls its own inbound processing cadence. Request volume does not create obligation to respond faster. The smaller ETHOS may set processing limits and communicate expected response timelines without this being treated as non-cooperation.

**Wealth pressure.** A wealthier ETHOS conditions cooperation on financial contribution or frames requests as economically beneficial to pressure acceptance. Resistance: the target ETHOS's consent process evaluates requests on governance merits, not financial incentives. Funding conditions attached to requests are documented as capture vectors during the advice phase.

**Urgency manipulation.** A requester frames a routine request as an emergency to bypass normal processing timelines. Resistance: emergency threshold is assessed independently by the target ETHOS's inbound contact. Urgency declared by the requester is not sufficient. Emergency requests still require a formal consent round.

**Reciprocity pressure.** Past cooperation is cited as creating obligation for the current request. Resistance: each request is evaluated on its own merits. Prior cooperation creates no current obligation. Reciprocity reasoning flagged during advice must be set aside in the consent decision.

## I. Failure Containment Logic

- **No response within timeline:** The requester may send one formal follow-up after the deadline. If a liaison exists, the liaison escalates through inter-unit-liaison channels. If still no response, the request status is set to `stale`. The originating ETHOS cannot force a response. They may reduce their engagement tier or initiate polycentric-conflict-navigation if the non-response reflects a structural problem.
- **Request declined:** The originating ETHOS may modify the request based on the stated rationale and resubmit once. A second decline is final. The originating ETHOS accepts or seeks the need elsewhere.
- **Counter-proposal deadlock:** If neither side accepts the other's terms after one round of counter-proposals, the request is closed as concluded without agreement. This is a legitimate outcome.
- **Unintended obligation:** A completed request is cited as creating ongoing commitments not explicitly agreed to. Either ETHOS may invoke a scope review. Ongoing commitments require a federation-agreement, not a request record.
- **Outbound authorization fails:** The originating circle declines to authorize. The request is not sent. The requester may revise and seek internal authorization again.

## J. Expiry / Review Condition

- Open requests with no response after 30 days are marked `stale` and the requester is notified
- Requests in `processing` for more than 45 days without status update trigger an inquiry to the target ETHOS
- Completed requests creating ongoing commitments must have a review date set at completion (recommended: 6 months)
- All request records are retained in both registries indefinitely as documentation

## K. Exit Compatibility Check

- **Requester exits originating ETHOS:** Open requests are voided unless the originating ETHOS designates a new requester within 14 days. The target ETHOS is notified.
- **Inbound contact exits target ETHOS:** The target ETHOS reassigns to a new contact. Processing continues.
- **Originating ETHOS dissolves:** All outbound requests close with documentation. Target ETHOS are notified within 7 days.
- **Target ETHOS dissolves:** All inbound requests close with documentation. Originating ETHOS seek needs elsewhere.
- **Completed requests:** Records and outcomes survive exit. Ongoing commitments terminate unless explicitly transferred.

## L. Cross-Unit Interoperability Impact

This skill is the cross-unit interaction primitive for all of Layer V. Every other Layer V skill that requires one ETHOS to initiate action with another uses this skill's request format and dual-consent routing pattern. The shared-resource-stewardship skill uses it for initial resource proposals. The federation-agreement skill uses it for negotiation initiation. The inter-unit-liaison skill uses it as the fallback when no liaison is available. Polycentric conflict navigation references request records that reveal structural incompatibilities.

Request records are registered in both participating ETHOS' agreement registries with linked entries. If a cross-ETHOS registry exists, records are indexed there as well.
