---
name: universal-agreement-field
description: "The root agreement every ecosystem participant consents to upon entry -- defines baseline commitments for accountability, processes, conflict, stewardship, and sovereignty that all other agreements inherit from."
layer: 1
version: 0.1.0
depends_on: [agreement-creation, consensus-check, domain-mapping]
---

# universal-agreement-field

## C. Trigger Conditions

- **Ecosystem formation**: creating the initial UAF (one-time founding event, uses agreement-creation with consensus of all founding members)
- **Participant onboarding**: presenting the existing UAF for individual consent as a condition of ecosystem entry
- **Periodic review**: annual review by the steward council, per Section J
- **Amendment proposal**: a proposed change to the UAF routes through agreement-amendment with the OSC consensus requirement

## D. Required Inputs

- For **initial creation**: the ecosystem's founding values, field agreement reference documents, identified domains of commitment (accountability, processes, conflict, stewardship, sovereignty), and the consent of all founding members in consensus mode
- For **onboarding**: the current ratified UAF document, the new participant's identity, a trained onboarding facilitator, and a 48-hour minimum reflection period
- For **amendment**: the proposed change, the OSC membership roster, and a consensus check per the consensus-check skill

## E. Step-by-Step Process

**Initial creation (ecosystem founding):**
1. Founding council drafts UAF from founding values and reference documents, using `assets/uaf-template.md`
2. Structured review: each section is discussed, revised, and tested against the 7 stress scenarios
3. Consensus of ALL founding members (not consent — consensus mode applies to the UAF)
4. Registration as agreement #001 in the agreement registry
5. Integration into the ecosystem's onboarding process

**Participant onboarding:**
1. Present the current ratified UAF document to the new participant
2. Trained facilitator walks through each section, inviting questions
3. Provide a minimum 48-hour reflection period — the participant takes the document home, reflects, and returns
4. Record explicit consent: the participant signs the consent record with the UAF version number and date
5. Register the individual's consent in the member record
6. Participant may withdraw consent within 7 days of signing (cooling-off provision)

**Amendment:** follows the agreement-amendment skill with the additional requirement that UAF amendments require OSC consensus (not consent). See agreement-amendment for the full process.

## F. Output Artifact

The UAF document itself — a versioned, structured agreement following `assets/uaf-template.md` with six sections: Agreements and Accountability, Processes, Conflict, Stewardship and Contribution, Sovereignty and Evolution, Sovereignty Freedom and Responsibility. Plus: the agreement hierarchy definition and individual consent records for each participant. The UAF is registered as the first entry in the agreement registry (AGR-[ECOSYSTEM]-001).

## G. Authority Boundary Check

- **Only the steward council (OSC in OmniOne) by consensus** can amend the UAF. No individual, circle, or council below the steward council can modify the root agreement.
- New participants consent to the UAF as a **condition of entry** — they do not negotiate its terms individually. If a prospective participant cannot consent, they do not join. They may propose amendments through normal channels after joining.
- The UAF **cannot be suspended**, even during emergencies. Emergency provisions may compress timelines for other agreements, but the UAF's commitments remain in force at all times.
- Onboarding facilitators have process authority (guiding the walkthrough) but cannot waive, modify, or reinterpret UAF provisions for individual participants.

## H. Capture Resistance Check

**Capital capture.** A major donor pressures the steward council to weaken the UAF's stewardship commitments — specifically, to allow private retention of emergent works. The consensus requirement means every steward council member must actively agree to the change. A single dissenting member blocks the amendment. The donor's financial contribution does not modify the consensus threshold or grant them a seat on the council.

**Charismatic capture.** A respected founder begins reinterpreting UAF provisions informally — telling new members "what the UAF really means" in ways that expand their own authority. Without a formal amendment, no reinterpretation has standing. The UAF text is the authority, not any individual's explanation. The onboarding process uses the document itself, not oral tradition.

**Emergency capture.** A crisis is invoked to temporarily "suspend" UAF provisions — "we need to bypass the conflict resolution process because there's no time." The UAF cannot be suspended. Emergency provisions compress timelines for operational agreements but never override the UAF's baseline commitments. Any action taken "in suspension of the UAF" has no legitimacy.

## I. Failure Containment Logic

- **Participant claims they did not understand a UAF provision**: the onboarding process requires explicit facilitator walkthrough of each section, a 48-hour reflection period, and a 7-day cooling-off window after signing. If these were followed and documented, the consent stands. If they were not followed, the onboarding process was defective and must be repeated.
- **UAF provision conflicts with local law**: the legal compliance clause takes precedence for that specific jurisdiction. The UAF provision is NOT suspended globally — it remains in effect for all other jurisdictions. A note is added to the registry documenting the jurisdiction-specific exception.
- **Steward council cannot reach consensus on an amendment**: the existing UAF remains unchanged. The proposed amendment may be revised and re-proposed, or the council may seek coaching at GAIA Level 4.

## J. Expiry / Review Condition

The UAF undergoes mandatory annual review by the steward council. The UAF **never auto-expires** — it persists until formally amended. A missed annual review triggers an escalation notice to all steward council members within 7 days. If the review is still not conducted within 30 days of the scheduled date, the escalation expands to all ecosystem participants, who may convene a special session. The UAF remains in full effect during any review delay.

## K. Exit Compatibility Check

When a participant exits the ecosystem, their UAF obligations cease immediately with these exceptions:
- **Stewarded asset return**: any assets held in stewardship under UAF-defined responsibilities must be returned or transferred within the 30-day wind-down period
- **In-progress commitments**: obligations actively underway get a 30-day handoff period
- **Original works**: the departing participant retains full rights to their individual creations

The participant's consent record is archived (not deleted) in the registry with an exit date. They are not bound by future UAF amendments after their exit. If they rejoin, they consent to the then-current UAF version.

## L. Cross-Unit Interoperability Impact

When the ecosystem federates with another NEOS ecosystem, each ecosystem's UAF remains sovereign. Cross-ecosystem interactions are governed by inter-unit agreements (Layer V, deferred), not by merging or subordinating UAFs. A participant in both ecosystems consents to both UAFs independently. If the two UAFs contain conflicting provisions, the inter-unit agreement must explicitly address the conflict — neither UAF automatically overrides the other. This skill notes the extensibility point: the onboarding process can be extended to present multiple UAFs when a participant joins a federated ecosystem.
