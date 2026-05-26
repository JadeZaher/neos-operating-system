---
name: re-entry-integration
description: "Execute a structured return for a former member who chooses to rejoin -- run this whenever someone comes back, ensuring they consent to current agreements, carry their historical context, and integrate without preferential treatment or second-class status."
layer: 10
version: 0.1.0
depends_on: [voluntary-exit, portable-record, member-lifecycle]
---

# re-entry-integration

## C. Trigger Conditions

- **Former member request**: a former member contacts any steward or governance facilitator expressing intent to rejoin
- **ETHOS invitation**: an ETHOS identifies a former member whose skills or experience match a current need and extends an invitation (the former member retains full right to decline)
- **Post-dissolution return**: a member who departed during ETHOS dissolution seeks to join a successor or different ETHOS within the same ecosystem
- **Federation transfer**: a member of a federated NEOS ecosystem requests transfer to another federated ecosystem (treated as a new entry with portable record context)

## D. Required Inputs

- **Former member identity**: confirmed identity of the person requesting re-entry, matched against the departure record in governance memory
- **Portable governance record**: the member's portable record from their previous membership (generated during departure or requested from archive)
- **Departure record**: the original Departure Record filed during the member's exit, including departure reason, commitment unwinding status, and re-entry eligibility
- **Current agreement set**: the ecosystem's current foundational agreements (UAF and any ETHOS-specific agreements) for the member to review and consent to
- **Change summary**: a documented summary of significant governance changes since the member's departure (agreement amendments, structural changes, new or dissolved ETHOS, policy updates)

## E. Step-by-Step Process

1. **Receive re-entry request.** The former member contacts any steward or governance facilitator. The facilitator acknowledges the request within 48 hours and assigns a re-entry coordinator. The coordinator is drawn from the receiving ETHOS (unlike departure coordinators, who are drawn from outside).
2. **Verify departure record and eligibility.** The re-entry coordinator retrieves the former member's Departure Record from governance memory (Layer IX). The record confirms: the member departed through the voluntary-exit process, re-entry eligibility was not explicitly declined by the member, and no unresolved governance matters bar re-entry. If the departure record shows unresolved commitment-unwinding items, the coordinator assesses whether they affect re-entry eligibility.
3. **Verify portable record.** If the returning member presents a portable governance record, the coordinator verifies its integrity using the embedded verification hash against archived registry data. Verified records inform the integration process. Unverifiable or absent records do not block re-entry -- the member simply enters without historical context weighting.
4. **Present current agreements and change summary.** The coordinator presents the ecosystem's current foundational agreements and the change summary documenting what has changed since the member's departure. The returning member reviews these at their own pace. The coordinator is available for questions but does not pressure a timeline.
5. **Obtain consent to current agreements.** The returning member must explicitly consent to all current foundational agreements (e.g., the UAF as currently amended). Consent is to the current version, not the version the member originally signed. If the member objects to specific terms, they may raise objections through the standard ACT process -- but they cannot rejoin under the old terms. Consent is documented.
6. **Determine integration pathway.** Based on the member's portable record, their current interests, and the ecosystem's current needs, the coordinator and the member agree on an integration plan: which ETHOS and circle to join, whether previous role experience qualifies them for immediate role consideration (but not automatic reinstatement), and a 30-day orientation period during which the member participates in governance before taking on formal roles.
7. **Formalize re-entry.** The re-entry coordinator files a Re-Entry Record using `assets/re-entry-record-template.yaml`. The record documents the verification results, consents given, integration pathway, and links to both the departure record and portable record. The returning member is formally added to the ecosystem membership roster and the receiving ETHOS.
8. **Communicate re-entry.** A factual notice is published to the receiving ETHOS and relevant circles: the member's name, return date, and assigned circle. Previous role tenure is noted as historical context, not as a status marker. The member enters the ecosystem as a full member, not on probation.

## F. Output Artifact

A Re-Entry Record following `assets/re-entry-record-template.yaml`. The record contains: re-entry ID, member identity, departure record reference, portable record reference (if available), verification results, change summary acknowledgment date, agreements consented to (with version numbers), integration pathway (receiving ETHOS, circle, orientation period), coordinator identity, and effective re-entry date. The record is accessible to the returning member and ecosystem governance records.

## G. Authority Boundary Check

- **Any former member** can request re-entry at any time, subject to this process
- **Re-entry cannot be denied arbitrarily** -- rejection requires a stated reason, and the stated reason is subject to challenge through Layer VI conflict resolution
- **Legitimate rejection reasons** include: unresolved governance matters from original departure, the member explicitly declined re-entry eligibility during departure, or the member was removed through a Layer VI process with documented re-entry conditions
- **No individual or body** can fast-track re-entry by skipping current-agreement consent -- not the OSC, not a circle steward, not a personal relationship
- **Previous role tenure** is acknowledged but does not guarantee role reinstatement -- roles are filled through the standard role-assignment process
- **The 30-day orientation period** is standard for all returning members regardless of their previous tenure or status -- it is anti-preferential, not punitive

## H. Capture Resistance Check

**Loyalty capture.** The consent-to-current-agreements requirement prevents returning members from creating a two-tier governance structure where some members operate under old agreements. Every returning member consents to the same agreements as every current member. No one gets grandfathered-in terms.

**Preferential re-entry capture.** The standardized 30-day orientation period applies equally to a founding member returning after three years and a recent member returning after six months. The process does not include a "fast track" for important people. Previous role tenure informs the role-assignment process but does not bypass it.

**Gatekeeping capture.** Re-entry cannot be denied without a stated reason subject to Layer VI challenge. No individual steward, coordinator, or council can quietly block a former member's return. The process is transparent and the rejection-appeal pathway is structural, not social.

**Information capture.** The change summary requirement ensures returning members are not disadvantaged by missing context. The ecosystem is obligated to provide a clear accounting of what changed during the member's absence, not to test whether the member can figure it out on their own.

## I. Failure Containment Logic

- **Departure record missing**: if governance memory does not contain the former member's departure record (e.g., due to system migration or data loss), the coordinator reconstructs the departure context from available records and the member's portable record; absence of a departure record does not block re-entry
- **Portable record unverifiable**: the re-entry proceeds without historical context weighting; the member enters as if their portable record is informational only -- no verification means no formal credit, but also no penalty
- **Member objects to current agreements**: the member may raise objections through the standard ACT process; their re-entry is paused (not denied) until the objection is resolved through integration or the member withdraws the objection
- **Receiving ETHOS at capacity**: if the ETHOS the member wishes to join has a membership cap, the member may join a waitlist or choose a different ETHOS; capacity limits are not used as pretextual rejection -- they must be documented and consistently applied
- **Coordinator conflict of interest**: if the assigned coordinator has a prior relationship with the returning member that could affect objectivity (positive or negative), a replacement coordinator is assigned from a different circle within the receiving ETHOS

## J. Expiry / Review Condition

Re-Entry Records do not expire -- they are permanent governance records. Re-entry eligibility does not expire by default unless the departing member's original foundational agreement specified a re-entry window. The re-entry process is reviewed annually through the ACT consent process to ensure the orientation period, consent requirements, and change-summary practices remain appropriate. If a pattern of re-entry friction is identified (e.g., returning members consistently report inadequate change summaries), the process is amended through the standard governance cycle.

## K. Exit Compatibility Check

This skill closes the exit loop. The voluntary-exit skill creates the right to leave; this skill creates the right to return. Together, they ensure that departure is never permanent unless the member chooses permanence. The Departure Record's re-entry eligibility field feeds directly into this skill's verification step. The portable record generated during departure becomes the primary input for integration planning during re-entry. The skill ensures that exit and re-entry form a coherent lifecycle, not a one-way door.

## L. Cross-Unit Interoperability Impact

When a former member returns to a different ETHOS than the one they left, the re-entry process is identical -- the receiving ETHOS processes the re-entry using the same template. Cross-ecosystem re-entry (joining a different NEOS ecosystem) follows the same process with the portable record serving as the primary historical context. The receiving ecosystem decides how much weight to give the portable record independently -- a member's experience in OmniOne does not automatically translate to seniority in a different NEOS ecosystem. The standardized Re-Entry Record format enables receiving ecosystems to understand how re-entry was processed in source ecosystems, building cross-ecosystem trust in governance record integrity.
