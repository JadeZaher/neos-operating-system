---
name: federation-agreement
description: "Draft, negotiate, and ratify bilateral or multilateral agreements between ETHOS -- defining terms, shared protocols, dispute handling, and graduated engagement tiers -- through each ETHOS's own ACT process."
layer: 5
version: 0.1.0
depends_on: [cross-ethos-request, agreement-creation, act-consent-phase]
---

# federation-agreement

## A. Structural Problem It Solves

Without formal federation agreements, inter-ETHOS relationships are ad hoc -- built on personal connections and informal understandings that create inconsistency and ambiguity about what each unit has committed to. When relationships sour, there is no documented basis for accountability. This skill ensures multi-unit relationships are documented, mutually ratified, version-controlled, and reviewable -- the same structural discipline applied to intra-ETHOS agreements extended to the inter-unit level. It also prevents early agreements from becoming de facto standards that constrain later-joining ETHOS.

## B. Domain Scope

This skill applies to any ongoing relationship between two or more ETHOS that goes beyond one-time requests. Federation agreement types include:

- **Bilateral cooperation** -- two ETHOS formalizing a specific coordination relationship
- **Multilateral protocol** -- three or more ETHOS establishing shared procedures for a domain
- **Service-level agreement** -- one ETHOS providing ongoing services to another with defined standards
- **Mutual recognition** -- ETHOS formally acknowledging each other's governance processes and outputs
- **Graduated engagement compact** -- ETHOS defining their current and intended engagement tier

One-time interactions use the cross-ethos-request skill. Federation agreements formalize ongoing patterns.

## C. Trigger Conditions

- Two or more ETHOS decide to formalize an ongoing coordination relationship
- An existing informal cross-ETHOS arrangement needs structural grounding
- Cross-ETHOS request volume between ETHOS warrants standing protocols
- ETHOS want to define or change their engagement tier
- A shared resource stewardship arrangement requires a broader relationship framework

## D. Required Inputs

- **Participating ETHOS** -- all units involved in the agreement (mandatory)
- **Agreement type** -- bilateral cooperation, multilateral protocol, service-level, mutual recognition, or graduated engagement compact (mandatory)
- **Proposed terms** -- the substantive commitments each ETHOS would make (mandatory)
- **Negotiation mandate from each ETHOS** -- what each ETHOS's negotiators can and cannot agree to (mandatory)
- **Desired engagement tier** -- observe, cooperate, federate, or integrate (mandatory)
- **Proposed review schedule** -- when the agreement will be reviewed (mandatory)

## E. Step-by-Step Process

1. **Initiate.** One or more ETHOS propose formalizing their relationship through a cross-ETHOS request. The proposal states the desired agreement type and engagement tier.
2. **Define negotiation mandates.** Each participating ETHOS defines what its negotiators can agree to, explore, and commit to -- and what requires the full ETHOS's consent before the negotiator can accept. The mandate is approved through each ETHOS's own ACT process.
3. **Parallel advice phases.** Each ETHOS runs an internal advice phase to gather member input on the proposed terms. Advice is shared across ETHOS to inform negotiation.
4. **Collaborative drafting.** Negotiators from all participating ETHOS meet to draft the agreement using `assets/federation-agreement-template.yaml`. Drafting may be collaborative (simultaneous) or sequential (each ETHOS adds provisions). Disagreements are documented and negotiated within mandate limits.
5. **Mandate check.** If negotiation produces terms outside any negotiator's mandate, that negotiator pauses and returns to their ETHOS for mandate expansion or modification. No negotiator may accept terms beyond their mandate.
6. **Each ETHOS ratifies through consent.** The finalized draft is presented to each participating ETHOS for an independent consent round. If one ETHOS's consent fails, the process returns to Step 4 with the objecting ETHOS's concerns documented.
7. **Mutual registration.** The ratified agreement is registered in every participating ETHOS's agreement registry with linked entries and mutual ratification records.
8. **Review schedule begins.** The agreement's review cycle activates per the agreed schedule.

## F. Output Artifact

A federation agreement following `assets/federation-agreement-template.yaml`, containing: agreement ID, type, participating ETHOS, engagement tier, substantive terms, each ETHOS's negotiation mandate records, ratification records from each ETHOS, review schedule, amendment procedures, exit terms, and dispute resolution path. Registered in all participating ETHOS' registries.

## G. Authority Boundary Check

- **Negotiators operate within mandates.** Each ETHOS's negotiators can only agree to terms within their documented mandate. Commitments made outside the mandate are void until ratified by the home ETHOS.
- **No ETHOS can impose terms** on another. Every term requires mutual consent through each ETHOS's own ACT process.
- **Ratification is independent.** Each ETHOS runs its own consent round. One ETHOS's ratification does not bind another.
- **Amendment authority** follows the same process as original ratification -- all participating ETHOS must consent.
- **Engagement tier changes** require formal amendment, not unilateral declaration.

## H. Capture Resistance Check

**Power asymmetry.** A wealthier or larger ETHOS dictates terms during negotiation, leveraging its size to pressure smaller ETHOS into unfavorable provisions. Resistance: negotiation mandates are defined internally before negotiation begins, preventing mandate creep under social pressure. Each ETHOS's consent round evaluates terms independently. Size asymmetry is documented as context in the advice phase.

**Urgency pressure.** One ETHOS rushes ratification by framing delay as threatening the relationship. Resistance: each ETHOS controls its own consent timeline. No ETHOS can set deadlines for another's internal process. Urgency is documented but does not compress another ETHOS's consent process.

**Precedent capture.** Early agreements become de facto standards that constrain later-joining ETHOS. Resistance: new ETHOS joining an existing multilateral agreement negotiate their own terms and may propose amendments as a condition of joining. No ETHOS is bound by agreements it did not ratify through its own process.

**Informal capture.** Negotiators develop personal relationships that produce informal understandings outside the documented agreement. Resistance: only documented terms in the registered agreement are binding. Informal understandings have no governance standing.

## I. Failure Containment Logic

- **Negotiation stalls:** Any ETHOS may pause or withdraw from negotiation with documentation. Withdrawal does not create an obligation. The remaining ETHOS may continue with a reduced participant set.
- **Ratification fails in one ETHOS:** The process returns to drafting to address that ETHOS's concerns. Other ETHOS' prior ratification holds but may require reaffirmation if more than 90 days pass.
- **Mandate exceeded:** Commitments made outside mandate are void. The affected ETHOS runs an internal review and either expands the mandate or the term is removed from the draft.
- **Agreement violated:** The aggrieved ETHOS may invoke dispute resolution per the agreement's terms, escalating to polycentric-conflict-navigation if needed.
- **Engagement tier mismatch:** If one ETHOS wants to deepen engagement but another does not, the agreement reflects the lower tier. Deeper engagement requires mutual consent.

## J. Expiry / Review Condition

- **Review schedule:** Configurable per agreement. Bilateral cooperation agreements default to annual review. Multilateral protocols default to 18-month review. Minimum: 6 months.
- **Missed review:** Agreement enters a 60-day grace period. After 60 days, status changes to "under review" in all registries. The agreement remains operational but cannot be cited as authority for new commitments until reviewed.
- **Amendments:** Follow the same multi-party ratification process as the original agreement. Minor clarifications may use a simplified consent process if all participating ETHOS agree.
- **Federation agreements do not auto-expire** unless explicitly time-limited at ratification.

## K. Exit Compatibility Check

- **Unilateral exit:** Any ETHOS may exit a federation agreement with documented notice (default: 90 days). The exit does not invalidate the agreement for remaining participants.
- **Multilateral impact:** When one ETHOS exits a multilateral agreement, the remaining ETHOS convene a review to assess whether the agreement still functions. If not, they may wind down or restructure.
- **Obligations cease:** The exiting ETHOS's commitments under the agreement end at the close of the notice period. In-progress commitments receive a 30-day wind-down.
- **No retaliation clause:** Exit from a federation agreement does not trigger penalties or reduced standing in other agreements. Each agreement is structurally independent.

## L. Cross-Unit Interoperability Impact

Federation agreements are the primary mechanism for formalizing inter-ETHOS relationships. They reference cross-ethos-request (how the initial proposal was made), shared-resource-stewardship (how shared resources are governed within the federation framework), and inter-unit-liaison (how ongoing coordination roles are maintained). Changes to federation agreements must be announced to all participating ETHOS' registries simultaneously. New ETHOS joining a multilateral agreement negotiate and ratify on the same terms as the original parties.

### Graduated Engagement Tiers

Federation agreements operate within four engagement tiers (see `assets/engagement-tiers.yaml`):

- **Observe:** Mutual acknowledgment. No commitments. ETHOS recognize each other's existence and legitimacy. Default tier for new ETHOS relationships.
- **Cooperate:** Case-by-case collaboration through cross-ETHOS requests. No standing commitments. Each interaction is individually authorized.
- **Federate:** Formal agreement with shared protocols, regular coordination, and designated liaisons. Standing commitments and shared governance structures for specific domains.
- **Integrate:** Deep structural integration with shared governance bodies, joint decision-making on defined domains, and pooled resources. Highest commitment tier.

Transitions between tiers require a federation agreement amendment ratified by all participating ETHOS.

## OmniOne Walkthrough

Three SHUR communities -- Bali, Costa Rica, and Mexico -- decide to formalize a member transfer protocol. Currently, members who want to move between SHURs navigate an ad hoc process that varies each time.

**Initiation.** Amara, Bali's TH steward, submits a cross-ETHOS request to both Costa Rica and Mexico proposing a multilateral protocol for member transfers. Both SHURs acknowledge.

**Mandate definition.** Each SHUR's circle defines negotiation limits. Bali: negotiators can agree to notice periods between 14-45 days and housing arrangements up to 30 days. Costa Rica: negotiators can agree to notice periods of 21-60 days and require housing confirmation before transfer approval. Mexico: negotiators want maximum flexibility -- notice periods of 7-30 days, reflecting their more mobile community.

**Parallel advice.** Each SHUR gathers member input. Bali's members want clarity on resource access during transition. Costa Rica's members emphasize housing security. Mexico's members prioritize speed and simplicity.

**Collaborative drafting.** Amara, Diego (Costa Rica), and Valentina (Mexico) hold a joint drafting session. They draft a multilateral protocol covering: notice period, housing arrangements, resource access transition, and agreement field recognition.

**Negotiation.** The first draft proposes a 30-day notice period. Valentina objects -- Mexico's community is more transient, and 30 days is excessive. She proposes 14 days. Diego counters that 14 days is too short for Costa Rica to arrange housing. Compromise: 21-day standard notice with a flexibility clause allowing 14 days when documented circumstances warrant it (family emergency, employment change). All three negotiators confirm this falls within their mandates.

**Ratification.** Each SHUR runs consent. Bali: all members consent. Mexico: all consent. Costa Rica: in Round 1, 5 consent but Soren objects -- the housing guarantee language is too vague. He wants explicit commitment that the receiving SHUR confirms a housing arrangement before the transfer is approved. Integration round: the draft is amended to require housing confirmation within 10 days of transfer application. Round 2: all 7 Costa Rica members consent.

**Registration.** The "OmniOne Inter-SHUR Member Transfer Protocol" is registered in all three SHURs' registries as `FED-OMNI-2026-002`, with engagement tier set to "federate" for this domain. Review date: 12 months.

**Edge case.** Amara later realizes that Brazil's new SHUR wants to join the protocol. Brazil negotiates its own terms -- they propose a 28-day notice period for their larger community. The amendment process requires consent from all four SHURs. Brazil's terms are integrated without changing the existing parties' provisions (Brazil adds a SHUR-specific notice period). All four SHURs ratify the amendment.

## Stress-Test Results

### 1. Capital Influx

A well-funded ETHOS proposes a federation agreement with three smaller ETHOS, offering significant resource contributions in exchange for favorable coordination terms. During the mandate definition phase, each smaller ETHOS defines what it can accept independently, before the joint negotiation begins. This structural separation ensures the funded ETHOS's offer does not shape the mandates. During negotiation, one smaller ETHOS's negotiator flags a term that would give the funded ETHOS priority access to shared governance data. The term is rejected because it violates the equal governance principle. The funded ETHOS's contribution is documented as resource commitment, not governance authority. The resulting agreement treats all parties equally regardless of financial capacity.

### 2. Emergency Crisis

A regional disaster affects two of three SHURs in a multilateral federation agreement. The unaffected SHUR proposes an emergency amendment to redirect shared coordination resources toward disaster response. Emergency consent runs under compressed timelines (24-hour advice, 50% quorum) in each affected SHUR. The amendment is ratified within 48 hours. It includes a 30-day automatic expiry with a provision for full-process renewal if needed. The emergency does not justify bypassing any ETHOS's consent -- even under compression, each SHUR's internal process runs independently.

### 3. Leadership Charisma Capture

A charismatic ecosystem leader pressures all SHURs to ratify a federation agreement quickly, framing delay as "blocking community unity." Two SHURs consent quickly; the third, Mexico, has unresolved concerns about a provision on governance data sharing. The leader publicly characterizes Mexico's deliberation as obstruction. Mexico's steward responds by documenting the social pressure dynamic and reaffirming that each ETHOS controls its own consent timeline. Mexico takes an additional two weeks and produces a substantive amendment that all three SHURs ultimately adopt. The structural protection is that no external timeline pressure can compress an ETHOS's internal consent process.

### 4. High Conflict

Two ETHOS with fundamentally different governance philosophies -- one prioritizing individual autonomy, the other collective stewardship -- attempt to draft a federation agreement. Initial drafting sessions produce incompatible provisions. Rather than forcing compromise, the negotiators identify domains of genuine shared interest (member mobility, emergency mutual aid) and draft a narrower agreement covering only those domains. The engagement tier is set to "cooperate" rather than "federate," reflecting the honest scope of alignment. This is a structural success, not a failure -- the graduated engagement tiers allow productive relationships at appropriate depths.

### 5. Large-Scale Replication

OmniOne grows to 15 SHURs. The network has 12 active federation agreements of various types. Managing this complexity requires: a shared registry index (maintained by volunteer liaisons, not a central authority) for discoverability; domain-specific agreements rather than omnibus arrangements; and a maximum recommended participant count of 8 ETHOS per multilateral agreement to keep consent rounds manageable. ETHOS with less interaction remain at the "observe" or "cooperate" tier. The engagement tier system prevents premature formalization where it is not needed.

### 6. External Legal Pressure

A government regulation requires formalized inter-organizational agreements to be registered with a regulatory body. One ETHOS adds a regulatory compliance field to its registry copy of the federation agreement. This is a local configuration -- the compliance field appears only in that ETHOS's registry entry. Other ETHOS are informed but not required to mirror it. The federation agreement's content is not modified for regulatory compliance; only the registry metadata changes. Compliance requirements remain jurisdiction-specific.

### 7. Sudden Exit of 30% of Participants

Three of ten ETHOS in a multilateral protocol announce exit simultaneously. Each files 90-day notice per the agreement's exit terms. The remaining seven ETHOS convene a mandatory review within 30 days. The review assesses: quorum viability (can seven ETHOS sustain the protocol?), commitment adequacy (do the remaining contributions cover operational needs?), and scope appropriateness (should the protocol be narrowed?). The seven ETHOS ratify an amended agreement reflecting the new participant set. The protocol continues without interruption for the remaining parties.
