# Onboarding Consent Ceremony — Facilitator Checklist

**Skill:** member-lifecycle (Layer II)
**Purpose:** Step-by-step guide for facilitators conducting the UAF consent ceremony. Follow every step in order. Do not skip or compress steps.

---

## Pre-Session Preparation (Before the Walkthrough)

- [ ] Confirm the prospective member's identity and contact information.
- [ ] Retrieve the current ratified UAF document (confirm version number and ratification date).
- [ ] Send the UAF document to the prospective member at least 24 hours before the walkthrough session, so they can read it in advance.
- [ ] Confirm the session is private or semi-private (not a high-pressure group setting). The prospective member must be able to ask questions freely.
- [ ] Set the lifecycle record status to `onboarding` and log the session date.
- [ ] Prepare the section-by-section consent form (one row per UAF section).
- [ ] Prepare your profile proposal (Co-creator, Builder, Collaborator, or TownHall) with a brief rationale you can share if asked.

---

## The Walkthrough Session

**Your role:** Process guide. You clarify and explain. You do not modify UAF provisions, grant exceptions, or pressure the prospective member toward any answer.

- [ ] Open by stating: "This session is a walkthrough, not the consent session. You will have at least 48 hours after today before we record your consent. There is no pressure to decide anything today."
- [ ] Walk through each UAF section in order:
  - [ ] Read the section title and a brief summary of its commitment.
  - [ ] Invite questions. Answer from the document. If you do not know the answer, say so and commit to finding it before the consent session.
  - [ ] If the member raises a concern, note it without resolving it under time pressure. "Let's note that and you can sit with it during the reflection period."
- [ ] At the end of the walkthrough, summarize any open questions or concerns noted during the session.
- [ ] Record the walkthrough end time. This is the `cooling_off_start` timestamp.
- [ ] Inform the member: "The cooling-off period begins now. We cannot schedule the consent session for at least 48 hours. I will follow up in 2 days."
- [ ] Provide the member with:
  - The UAF document (if not already sent)
  - Any clarification documents referenced during the session
  - Your contact information for questions during the reflection period
  - The list of open questions noted during the session

---

## During the Cooling-Off Period (48 Hours Minimum)

- [ ] Do not contact the member to ask if they have decided. You may respond to inbound questions from the member.
- [ ] If the member reaches out with additional questions, answer from the document and record the exchange in the lifecycle record notes.
- [ ] Prepare the consent session agenda: one row per UAF section, space for explicit consent or objection, space for notes.
- [ ] Confirm with the relevant council (AE or TH) that they are available to run a brief consent round on the profile proposal after the consent session.

---

## The Consent Session

**Minimum elapsed time:** 48 hours after `cooling_off_start`. Do not schedule before this window closes.

- [ ] Record the `cooling_off_end` timestamp at the start of this session.
- [ ] Confirm the member received the UAF and had adequate time to reflect.
- [ ] Address any open questions from the walkthrough before beginning section-by-section consent.
- [ ] Section-by-section consent process:
  - [ ] State the section name.
  - [ ] Ask: "Do you consent to this section, or do you have a reasoned objection?"
  - [ ] If consent: mark `consented: true`. Move to the next section.
  - [ ] If objection: record the objection verbatim in the notes field. Do not dismiss or minimize.
    - [ ] Assess whether the objection is a clarification need (information gap) or a fundamental incompatibility (cannot consent under any condition).
    - [ ] If clarification need: provide the information. Ask again. If resolved, mark `consented: true` with resolution note.
    - [ ] If fundamental incompatibility: mark `consented: false`. Do not proceed past this section without council review.
    - [ ] If any section remains `consented: false` after discussion: pause the consent ceremony. Notify the relevant council with the full objection record. Await council assessment before proceeding.
- [ ] If all sections receive `consented: true`: move to profile assignment.
- [ ] If the council assesses an incompatibility as non-fundamental: document the assessment, allow the onboarding to proceed with the objection noted as a UAF review item.
- [ ] If the council assesses the incompatibility as fundamental: close the onboarding flow. Record status as `prospective` (dormant). Forward the objection to the UAF review queue. Inform the prospective member of the outcome and the UAF review process.

---

## Profile Assignment

- [ ] State your profile proposal and brief rationale to the member.
- [ ] Ask the relevant council to run a consent round on the profile proposal.
  - AE runs consent for: Co-creator, Builder, Collaborator
  - TH runs consent for: TownHall profile
- [ ] Record the profile, the council that consented, and the consent date in the lifecycle record.
- [ ] If the council raises an objection to the proposed profile: discuss alternatives. The facilitator may revise the proposal. A second consent round on the revised proposal is acceptable in the same session.

---

## Completion and Registry Entry

- [ ] Confirm all of the following are documented in the lifecycle record:
  - [ ] `facilitator` name and role
  - [ ] `uaf_version_consented` (exact version string)
  - [ ] `consent_date` (today's date)
  - [ ] `cooling_off_start` and `cooling_off_end` (both recorded, >= 48h apart)
  - [ ] `section_consents` with an entry for each UAF section
  - [ ] `profile`, `profile_proposed_by`, `profile_consented_by`, `profile_consent_date`
- [ ] Set `current_status` to `active` in the lifecycle record.
- [ ] Add the first `status_transitions` entry: `onboarding → active`, with today's date and trigger `onboarding_complete`.
- [ ] Register the consent record in the agreement registry (cross-reference the UAF agreement ID).
- [ ] Inform the member that they are now active, explain what active status means, and share the inactivity threshold so they know what ongoing participation requires.
- [ ] Welcome the member to the ecosystem.

---

## Notes for Common Situations

**Member cannot attend in person:** The walkthrough and consent sessions may be conducted remotely (video call). Screen-share the UAF document. Record the session if the member consents to recording. The 48-hour cooling-off period applies identically. Digital consent confirmation (written message or electronic signature) is acceptable.

**Member disappears after walkthrough:** If the member does not respond to follow-up contact within 30 days of the walkthrough, revert status to `prospective` (dormant). Note in the lifecycle record. The member may re-initiate onboarding at any time with a fresh walkthrough session.

**Group onboarding sessions:** Multiple prospective members may attend the same walkthrough session. Each member must have their own individual consent session after the cooling-off period -- group consent is not accepted. Each member has their own lifecycle record.

**Re-onboarding after exit:** A returning member who previously exited must complete a full onboarding ceremony for the current UAF version. Their prior consent record (archived) is not reactivated. A new onboarding record is created.
