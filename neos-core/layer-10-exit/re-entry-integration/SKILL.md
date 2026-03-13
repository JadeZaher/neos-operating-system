---
name: re-entry-integration
description: "Execute a structured return for a former member who chooses to rejoin -- run this whenever someone comes back, ensuring they consent to current agreements, carry their historical context, and integrate without preferential treatment or second-class status."
layer: 10
version: 0.1.0
depends_on: [voluntary-exit, portable-record, member-lifecycle]
---

# re-entry-integration

## A. Structural Problem It Solves

Returning members fall into a structural gap. New-member onboarding assumes no history; veteran-member processes assume continuity. A returning member has governance experience but missed potentially significant changes -- agreements may have been amended, roles restructured, circles dissolved or created. Without a dedicated re-entry process, ecosystems default to one of two failure modes: treating the returning member as a stranger (wasting their experience and signaling that departure is permanent) or treating them as if they never left (skipping consent to changed agreements and creating governance liability). This skill bridges the gap with a structured process that honors the member's history while requiring explicit consent to the ecosystem's current state.

## B. Domain Scope

This skill applies to any former ecosystem member who requests to rejoin, whether returning to the same AZPO, a different AZPO, or the ecosystem at large. The scope covers: re-entry request, record verification, current-agreement review, consent to current agreements, role integration, and the formal re-entry record. It interacts with the voluntary-exit skill (which originally processed the departure), the portable-record skill (which provides the member's governance history), and the member-lifecycle skill (which manages ongoing membership transitions). Out of scope: initial onboarding of members who have never participated (that is the member-lifecycle skill's territory), and forced re-admission of expelled or conflicted members (which requires Layer VI resolution first).

## C. Trigger Conditions

- **Former member request**: a former member contacts any steward or governance facilitator expressing intent to rejoin
- **AZPO invitation**: an AZPO identifies a former member whose skills or experience match a current need and extends an invitation (the former member retains full right to decline)
- **Post-dissolution return**: a member who departed during AZPO dissolution seeks to join a successor or different AZPO within the same ecosystem
- **Federation transfer**: a member of a federated NEOS ecosystem requests transfer to another federated ecosystem (treated as a new entry with portable record context)

## D. Required Inputs

- **Former member identity**: confirmed identity of the person requesting re-entry, matched against the departure record in governance memory
- **Portable governance record**: the member's portable record from their previous membership (generated during departure or requested from archive)
- **Departure record**: the original Departure Record filed during the member's exit, including departure reason, commitment unwinding status, and re-entry eligibility
- **Current agreement set**: the ecosystem's current foundational agreements (UAF and any AZPO-specific agreements) for the member to review and consent to
- **Change summary**: a documented summary of significant governance changes since the member's departure (agreement amendments, structural changes, new or dissolved AZPOs, policy updates)

## E. Step-by-Step Process

1. **Receive re-entry request.** The former member contacts any steward or governance facilitator. The facilitator acknowledges the request within 48 hours and assigns a re-entry coordinator. The coordinator is drawn from the receiving AZPO (unlike departure coordinators, who are drawn from outside).
2. **Verify departure record and eligibility.** The re-entry coordinator retrieves the former member's Departure Record from governance memory (Layer IX). The record confirms: the member departed through the voluntary-exit process, re-entry eligibility was not explicitly declined by the member, and no unresolved governance matters bar re-entry. If the departure record shows unresolved commitment-unwinding items, the coordinator assesses whether they affect re-entry eligibility.
3. **Verify portable record.** If the returning member presents a portable governance record, the coordinator verifies its integrity using the embedded verification hash against archived registry data. Verified records inform the integration process. Unverifiable or absent records do not block re-entry -- the member simply enters without historical context weighting.
4. **Present current agreements and change summary.** The coordinator presents the ecosystem's current foundational agreements and the change summary documenting what has changed since the member's departure. The returning member reviews these at their own pace. The coordinator is available for questions but does not pressure a timeline.
5. **Obtain consent to current agreements.** The returning member must explicitly consent to all current foundational agreements (e.g., the UAF as currently amended). Consent is to the current version, not the version the member originally signed. If the member objects to specific terms, they may raise objections through the standard ACT process -- but they cannot rejoin under the old terms. Consent is documented.
6. **Determine integration pathway.** Based on the member's portable record, their current interests, and the ecosystem's current needs, the coordinator and the member agree on an integration plan: which AZPO and circle to join, whether previous role experience qualifies them for immediate role consideration (but not automatic reinstatement), and a 30-day orientation period during which the member participates in governance before taking on formal roles.
7. **Formalize re-entry.** The re-entry coordinator files a Re-Entry Record using `assets/re-entry-record-template.yaml`. The record documents the verification results, consents given, integration pathway, and links to both the departure record and portable record. The returning member is formally added to the ecosystem membership roster and the receiving AZPO.
8. **Communicate re-entry.** A factual notice is published to the receiving AZPO and relevant circles: the member's name, return date, and assigned circle. Previous role tenure is noted as historical context, not as a status marker. The member enters the ecosystem as a full member, not on probation.

## F. Output Artifact

A Re-Entry Record following `assets/re-entry-record-template.yaml`. The record contains: re-entry ID, member identity, departure record reference, portable record reference (if available), verification results, change summary acknowledgment date, agreements consented to (with version numbers), integration pathway (receiving AZPO, circle, orientation period), coordinator identity, and effective re-entry date. The record is accessible to the returning member and ecosystem governance records.

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
- **Receiving AZPO at capacity**: if the AZPO the member wishes to join has a membership cap, the member may join a waitlist or choose a different AZPO; capacity limits are not used as pretextual rejection -- they must be documented and consistently applied
- **Coordinator conflict of interest**: if the assigned coordinator has a prior relationship with the returning member that could affect objectivity (positive or negative), a replacement coordinator is assigned from a different circle within the receiving AZPO

## J. Expiry / Review Condition

Re-Entry Records do not expire -- they are permanent governance records. Re-entry eligibility does not expire by default unless the departing member's original foundational agreement specified a re-entry window. The re-entry process is reviewed annually through the ACT consent process to ensure the orientation period, consent requirements, and change-summary practices remain appropriate. If a pattern of re-entry friction is identified (e.g., returning members consistently report inadequate change summaries), the process is amended through the standard governance cycle.

## K. Exit Compatibility Check

This skill closes the exit loop. The voluntary-exit skill creates the right to leave; this skill creates the right to return. Together, they ensure that departure is never permanent unless the member chooses permanence. The Departure Record's re-entry eligibility field feeds directly into this skill's verification step. The portable record generated during departure becomes the primary input for integration planning during re-entry. The skill ensures that exit and re-entry form a coherent lifecycle, not a one-way door.

## L. Cross-Unit Interoperability Impact

When a former member returns to a different AZPO than the one they left, the re-entry process is identical -- the receiving AZPO processes the re-entry using the same template. Cross-ecosystem re-entry (joining a different NEOS ecosystem) follows the same process with the portable record serving as the primary historical context. The receiving ecosystem decides how much weight to give the portable record independently -- a member's experience in OmniOne does not automatically translate to seniority in a different NEOS ecosystem. The standardized Re-Entry Record format enables receiving ecosystems to understand how re-entry was processed in source ecosystems, building cross-ecosystem trust in governance record integrity.

## OmniOne Walkthrough

Eighteen months after departing OmniOne's Bali SHUR, Rina contacts Wayan, an AE governance facilitator, expressing her wish to rejoin. She has been living in Costa Rica, participated briefly in a NEOS-governed cooperative there, and now returns to Bali. She carries her portable governance record from her original OmniOne departure (PGR-OMNI-2026-RINA).

Wayan acknowledges within 24 hours and assigns Sari, an AE member in the Food Systems Circle, as Rina's re-entry coordinator. Sari is part of the receiving AZPO and has no prior close relationship with Rina.

Sari retrieves Departure Record DR-SHUR-2026-031 from governance memory. The record confirms: Rina departed voluntarily, all commitments were fully unwound, re-entry eligibility is "indefinite," and no unresolved governance matters exist. Sari verifies Rina's portable record using the embedded hash -- the hash validates against archived registry data. Rina's 14 months of governance experience (2 circle roles, 4 proposals, 18 ACT decisions) are confirmed as authentic.

Sari prepares a change summary covering the 18 months since Rina's departure. Significant changes include: the UAF was amended twice (once to add a digital-privacy clause, once to update the resource allocation formula), the Welcome Circle merged with the Outreach Circle to form the Community Engagement Circle, two new circles were formed (Water Systems and Digital Infrastructure), and 8 new members joined while 5 departed. Sari presents the current UAF (version 3.2) and the change summary to Rina.

Rina reviews the documents over four days. She notices the digital-privacy clause is new and asks Sari to explain the rationale. Sari connects Rina with the clause's original proposer for context. Rina is satisfied and consents to UAF v3.2 and all current AZPO-specific agreements. Her consent is documented.

**Edge case**: Rina discovers that the resource allocation formula change reduced the per-person Current-See allocation from 111 to 95, a change she would have objected to as a member. Sari explains that the change went through a full ACT consent process during Rina's absence. Rina may raise the issue as a new proposal once she is a member, but she cannot condition her re-entry on reverting the change. She consents to the current terms and plans to propose an amendment through the standard ACT process after her orientation period.

Sari and Rina agree on an integration pathway: Rina joins the Community Engagement Circle (the successor to her former Welcome Circle), where her communications experience is directly relevant. Her previous tenure as Comms Steward is noted in her re-entry record as historical context. She enters a 30-day orientation period during which she participates in circle governance, attends two TH sessions, and reviews recent decision logs. After orientation, Rina may be nominated for roles through the standard role-assignment process -- her experience informs the nomination but does not guarantee any specific role.

Sari files Re-Entry Record RER-SHUR-2027-008. A factual notice is posted: "Rina has rejoined the Bali SHUR and is joining the Community Engagement Circle. She previously served as Comms Steward (2025-2026) and returns with 14 months of verified governance experience." No fanfare, no editorial -- just governance facts.

## Stress-Test Results

### 1. Capital Influx

A major funder offers to sponsor the return of several former members who left during a previous funding dispute, conditioning the sponsorship on their immediate reinstatement to leadership roles. The re-entry skill is structurally immune to this pressure: every returning member follows the same process (record verification, current-agreement consent, 30-day orientation, standard role-assignment). The funder cannot purchase role reinstatement. Each sponsored member goes through re-entry individually, consents to current agreements, and competes for roles on equal footing with current members. The funder's condition is documented as a potential capital capture incident for governance health assessment. The members themselves are not penalized for the funder's attempt -- their re-entry is processed normally regardless of who sponsored their return.

### 2. Emergency Crisis

Following a major disaster, multiple former members offer to return and help with recovery. The re-entry skill accommodates urgency: the 30-day orientation period can overlap with emergency response participation, and current-agreement consent can be expedited (but not waived) through accelerated review. Returning members who participate in emergency response do so as provisional members during their re-entry processing, with full membership formalized once consent is documented. The emergency does not justify skipping the consent step -- members who return to a changed ecosystem must still consent to its current agreements. Post-emergency, re-entry records are completed and filed with "emergency re-entry" notation.

### 3. Leadership Charisma Capture

A beloved founding member who departed two years ago announces their return. Community excitement creates pressure to skip the standard process: "They founded this place, they don't need orientation!" The re-entry skill's anti-preferential structure holds: the 30-day orientation period is mandatory regardless of previous tenure, current-agreement consent is required regardless of who wrote the original agreements, and role assignment follows the standard process regardless of the member's reputation. The coordinator processes the re-entry identically to any other returning member. The standardized process protects the returning member too -- they are not burdened with expectations of immediate leadership and have time to understand how the ecosystem evolved in their absence.

### 4. High Conflict / Polarization

A former member whose departure was connected to a factional dispute requests re-entry. One faction welcomes the return; the other views it as a factional power play. The re-entry skill neutralizes this through structural processing: re-entry cannot be denied arbitrarily, so the opposing faction cannot block the return without a stated reason subject to Layer VI challenge. The stated reason must be a legitimate governance concern (e.g., unresolved commitments from original departure), not factional preference. The returning member consents to current agreements -- including any agreements shaped by the faction they disagreed with -- establishing a clean governance foundation. The 30-day orientation period provides a cooling-off buffer. The re-entry record documents the factual process, not the political dynamics.

### 5. Large-Scale Replication

At scale with 4,000 members, re-entry becomes a regular governance operation. The standardized process handles volume without modification: each re-entry is independent, coordinators are drawn from receiving AZPOs, and change summaries are maintained as living documents updated with each significant governance change. Automated portable record verification scales linearly with re-entry volume. The ecosystem develops a library of change summaries covering different departure periods, reducing coordinator effort for each individual re-entry. Cross-AZPO re-entry (returning to a different AZPO than the one departed) uses the same process with the receiving AZPO's coordinator. The re-entry record format is identical across all locations, enabling ecosystem-wide analysis of return patterns.

### 6. External Legal Pressure

Immigration authorities question a returning member's right to rejoin the ecosystem as part of a visa review, claiming the member's departure constitutes a break in community ties. The Re-Entry Record and portable governance record provide structured documentation of the member's governance history and formal return. The ecosystem's legal entity (GEV) presents these records as evidence of ongoing community connection through documented governance participation. The re-entry process itself is not modified for immigration purposes -- it runs on its governance timeline regardless of external legal proceedings. If the member's visa is denied, their re-entry record remains valid and they may complete integration when legal circumstances permit.

### 7. Sudden Exit of 30% of Participants

After a mass departure, several former members reconsider and request re-entry within weeks. The re-entry skill processes each return individually. The change summary for these rapid returns is minimal (little has changed in the brief period since departure), but current-agreement consent is still required -- the ecosystem may have made emergency amendments during the mass departure's aftermath. The 30-day orientation period helps returning members understand the post-departure dynamics and rebuild relationships with the reconstituted community. The re-entry records document the rapid departure-and-return pattern, providing data for governance health analysis. If the mass re-entry indicates that the original cause of departure was resolved (or that members departed reactively), this pattern becomes visible in the ecosystem's governance record and informs future conflict resolution approaches.
