---
name: agreement-review
description: "Run the periodic review cycle for any agreement -- evaluating current relevance, checking for staleness or conflict, and producing a review outcome: renew as-is, revise through amendment, or sunset with graceful deprecation."
layer: 1
version: 0.1.0
depends_on: [agreement-creation, agreement-amendment, agreement-registry, domain-mapping]
---

# agreement-review

## A. Structural Problem It Solves

Without periodic review, agreements become stale, outdated, or misaligned with current conditions. Members operate under terms written for a context that no longer exists, and no one has the authority or mechanism to revisit them. This skill ensures every agreement is regularly re-validated against current conditions and either renewed (still relevant), revised (needs changes), or sunset (no longer serves its purpose). It prevents governance decay where the written rules diverge from the lived reality.

## B. Domain Scope

Any active agreement in the agreement registry that has a review date. This includes all agreement types: space agreements, access agreements, organizational agreement fields, stewardship agreements, culture codes, and the UAF. The UAF has its own review provisions (annual, never auto-expires) but the review process itself uses this skill.

## C. Trigger Conditions

- **Scheduled review date arrives**: every agreement has a review date set during creation or the last review cycle
- **Participant request**: any affected party can request an early review at any time with stated rationale
- **Threshold event**: a significant change triggers automatic review — 30% participant exit, a major policy change affecting the agreement's domain, a conflict formally attributed to the agreement's provisions, or an amendment to a higher-level agreement in the hierarchy

## D. Required Inputs

- **The agreement** to be reviewed, retrieved from the agreement registry with its full version history
- **Current participant feedback**: input from affected parties about whether the agreement is working as intended
- **Conflict or issue log**: any formally documented conflicts, complaints, or issues arising from the agreement's provisions
- **Registry data**: the agreement's amendment history, linked agreements, and usage patterns

## E. Step-by-Step Process

1. **Convene review body.** The review body consists of the currently affected parties (not necessarily the original ratifiers — if participants have changed, the current affected parties review). If the original ratifiers have all departed, the nearest related circle assigns a review body.
2. **Evaluate.** The review body assesses the agreement against three questions:
   - *Relevance*: Is this agreement still needed? Has the context it was written for changed?
   - *Appropriateness*: Are the terms still appropriate for current conditions? Do the commitments match current capacity and resources?
   - *Consistency*: Does the agreement conflict with any higher-level agreement, any newer agreement in the same domain, or any policy change since the last review?
3. **Determine outcome.** Three possible outcomes:
   - **Renew as-is**: the agreement is still relevant and appropriate. Set a new review date per the agreement type's default interval.
   - **Revise**: specific provisions need updating. This triggers the agreement-amendment skill with the identified changes. The review body provides the amendment proposer with specific revision requests.
   - **Sunset**: the agreement is no longer needed. Trigger graceful deprecation: 60-day notice to all affected parties, transition plan for any dependencies (agreements that reference this one), and archive in the registry with "sunset" status.
4. **Record.** Produce a review record per `assets/review-record-template.yaml` documenting the evaluation, outcome, and follow-up actions.
5. **Update registry.** The agreement's next review date is updated (if renewed), or the amendment process is initiated (if revised), or the sunset timeline begins (if sunset).

## F. Output Artifact

A review record per `assets/review-record-template.yaml` containing: review ID, agreement ID and version, review type (scheduled/requested/threshold_event), trigger description, review body composition, date, evaluation findings (relevance, appropriateness, consistency), outcome decision, next review date (if renewed), follow-up actions with responsible parties and deadlines.

## G. Authority Boundary Check

- The **review body** has authority to evaluate and decide the outcome (renew, revise, sunset) but cannot directly modify the agreement text — revisions go through the agreement-amendment skill with its own ACT process.
- **Sunset authority** scales with agreement level: circle-level agreements can be sunset by the circle. Cross-circle agreements require consent from all affected circles. The UAF cannot be sunset — it can only be revised.
- The review body **cannot skip the review** — if the review date arrives and no one convenes the body, the automatic escalation process triggers (see Section J of agreement-creation).
- A **single participant cannot force a sunset** through a review request. The review body evaluates collectively. If the requesting participant's concern is not shared by the review body, the outcome is renewal.

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

## H. Capture Resistance Check

**Capital capture.** A funded agreement is up for review. The funder pressures the review body to renew without revision despite known issues. The review body's evaluation is structural — they assess relevance, appropriateness, and consistency regardless of funding. If the agreement has issues, the honest outcome is "revise," and the funder's financial contribution does not override the evaluation.

**Neglect capture.** An agreement that benefits certain parties is never reviewed because those parties prevent the review body from convening. The automatic escalation process prevents this: missed review dates trigger notifications that expand from the review body to the broader affected parties, and eventually to all ecosystem participants. An agreement that persistently avoids review becomes visible.

**Sunset avoidance.** An outdated agreement is renewed repeatedly because "it's not hurting anything." The review body must actively evaluate against the three questions. A review that simply rubber-stamps renewal without evaluation is procedurally defective. The review record must contain substantive evaluation findings, not just the outcome.

## I. Failure Containment Logic

- **Review body cannot convene**: escalation follows the pattern defined in universal-agreement-field Section J — 7-day notice to review body members, then 30-day broader escalation to all affected parties (who may convene a special session), then a visible flag on the registry entry until the review is completed. The agreement remains active during the delay.
- **Review outcome is disputed**: if review body members disagree on the outcome (some want renewal, others want sunset), the decision follows a consent check. Objections to the outcome trigger integration rounds per the act-consent-phase pattern.
- **Sunset creates dependency issues**: if other agreements reference the agreement being sunset, those dependent agreements are notified during the 60-day sunset period and must be reviewed themselves to remove or update the dependency.
- **Missed review is discovered retroactively** (the review date passed months ago without notice): the review is conducted immediately upon discovery. The agreement is not retroactively invalidated — it remained in effect, and the review evaluates its current state.

## J. Expiry / Review Condition

- Review intervals are set during agreement creation and confirmed/adjusted at each review cycle.
- Default intervals by type: space (annual), access (6 months), organizational (2 years), UAF (annual), culture code (at circle discretion, minimum annual).
- Missed reviews trigger the automatic escalation process. Agreements are never auto-invalidated by a missed review — they remain in effect with a visible flag.
- The review skill itself has no separate expiry — it is invoked each time a review is due.

## K. Exit Compatibility Check

- If **review body members exit** before the scheduled review, replacements are drawn from the current affected parties. The review proceeds with the reconstituted body.
- If the **original proposer/author exits**, the review body still convenes as scheduled. Authorship does not affect the review process.
- **Mass exit** (30%+) is itself a threshold-event trigger: the review is convened immediately to evaluate whether the mass departure changes the agreement's relevance or appropriateness.

## L. Cross-Unit Interoperability Impact

- Cross-AZPO agreements are reviewed by a body that includes representatives from each affected AZPO. Each AZPO must agree on the review outcome.
- If one AZPO wants to sunset an agreement that another AZPO still needs, the agreement is revised to narrow scope rather than fully sunset. The departing AZPO's obligations under the agreement cease through proper amendment.
- Registry synchronization: when a cross-AZPO agreement is reviewed, the review record is entered in all affected registries.

## OmniOne Walkthrough

The SHUR Bali kitchen space agreement (AGR-SHUR-2026-003, ratified March 2026) reaches its one-year review date in March 2027. The original 12-member review body has changed: 3 residents have moved out and been replaced by 4 new residents (SHUR expanded). The review body consists of the 13 current SHUR residents.

Facilitator Amara (who originally proposed the agreement) convenes the review. She pulls the agreement from the registry: version 1.0.0, zero amendments, two documented conflicts over the past year — both about the community event exemption clause.

The review body evaluates:
- *Relevance*: Yes, kitchen coordination is still needed. If anything, it is more needed with 13 residents than 12.
- *Appropriateness*: Mostly. The quiet hours (9:30pm) work well. The cleanup-within-30-minutes rule works. But the community event exemption (2 per week, end by 11pm) has generated friction — two documented conflicts where events exceeded the time or frequency limit with no consequence.
- *Consistency*: No conflict with higher-level agreements. The general SHUR common-space agreement (AGR-SHUR-2026-001) is compatible.

The review body's outcome: **Revise**. Specific revision request: the community event clause needs enforcement mechanisms — what happens when an event exceeds its limits? The review body recommends: events that exceed time or frequency limits without prior exception approval result in the organizer losing event-scheduling privileges for 30 days.

The review triggers the agreement-amendment skill. An amendment proposal is drafted with the specific revision. Adding a new enforcement consequence (30-day privilege loss) is a substantive change — it introduces a new form of sanction, not merely a clarification of existing text — and must go through a full ACT cycle with all current residents. After consent, the agreement version increments to 1.1.0 and the next review date is set for March 2028.

Edge case: One of the new residents (who was not part of the original ratification) asks: "Why should I be bound by an agreement I didn't consent to?" The answer: when they joined SHUR, they consented to existing space agreements as part of the access agreement. The kitchen agreement was in the registry and presented during their onboarding. Their review participation is their ongoing voice in the agreement's evolution.

## Stress-Test Results

### 1. Capital Influx

A donor-funded co-working agreement at SHUR is up for review. The donor's organization has been using the space heavily and wants the agreement renewed without revision. Several non-donor-affiliated residents have concerns about equitable access being diminished. The review body evaluates access data and finds that donor-affiliated projects occupy the space 60% of available hours. The appropriateness question reveals an imbalance. Outcome: revise — the amendment will cap any single project's space usage at 40% and create a booking system. The donor's financial contribution does not override the structural evaluation.

### 2. Emergency Crisis

An earthquake damages the SHUR Bali building. Multiple space agreements are immediately affected. The threshold-event trigger activates automatic reviews for all SHUR space agreements. The emergency review body convenes within 48 hours. For undamaged spaces: renew as-is. For damaged spaces: sunset the current agreement (the space is temporarily unusable) and note that new agreements will be created when the space is restored. For shared infrastructure: revise to reflect temporary capacity constraints. The review process runs under compressed emergency timelines but follows the same evaluation structure.

### 3. Leadership Charisma Capture

A respected circle lead has authored many of the circle's agreements. During review, they advocate strongly for renewal without revision — "these agreements are working fine, let's not fix what isn't broken." Other review body members have concerns but defer to the lead's confidence. The review process requires substantive evaluation documented in the review record. A review that consists only of "the author says it's fine" is procedurally defective. The facilitator ensures each of the three evaluation questions is discussed and documented, surfacing the other members' concerns even if the lead disagrees.

### 4. High Conflict / Polarization

A review of a resource-sharing agreement reveals deep polarization: half the review body wants to sunset the agreement entirely (it is causing more conflict than it resolves), and the other half wants to renew (the underlying need for resource sharing is real). The outcome decision follows a consent check: the sunset faction objects to renewal, the renewal faction objects to sunset. Through integration, the review body finds a third outcome: revise — the fundamental resource-sharing framework is preserved but the specific allocation mechanism (the source of conflict) is replaced. The amendment goes through full ACT with the specific revision.

### 5. Large-Scale Replication

At scale with 500+ active agreements, review scheduling becomes a governance function in itself. The registry tracks all review dates and sends automatic notifications 30 days before each review. Reviews are distributed across the year rather than clustered. Each circle manages reviews for its own agreements. Cross-circle agreements are reviewed by a standing cross-circle review calendar. The review record template is the same regardless of scale. At high volume, the review body pattern shifts from ad-hoc convening to scheduled review sessions — circles block time monthly for agreement reviews.

### 6. External Legal Pressure

A regulatory change makes an existing data-handling agreement non-compliant. This is a threshold-event trigger: the regulatory change materially affects the agreement's provisions. The review convenes immediately. The evaluation is clear: the agreement must be revised to comply with the regulation. The review body outcome: revise, with the specific legal compliance changes identified. The amendment goes through normal ACT process. If the regulation has an immediate compliance deadline, the emergency amendment provision applies — the change is made under compressed timeline with 30-day auto-expiry, followed by a normal-process permanent amendment.

### 7. Sudden Exit of 30% of Participants

The mass departure triggers automatic threshold-event reviews for every agreement where departed members constituted a significant portion of the affected parties. The review body for each agreement is reconstituted from current participants. Some agreements are still relevant for the remaining members (renew with updated review body). Others have lost their primary purpose (sunset — e.g., a collaboration agreement between two circles where one circle dissolved). The review process handles mass departure as a structural event, not a crisis: each agreement is individually evaluated on its current merits. The review records document the departure as context for the evaluation, ensuring the decision trail is complete.
