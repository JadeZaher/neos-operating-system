---
skill: agreement-review
type: rationale
---

# agreement-review — Rationale & Design Notes

## A. Structural Problem It Solves

Without periodic review, agreements become stale, outdated, or misaligned with current conditions. Members operate under terms written for a context that no longer exists, and no one has the authority or mechanism to revisit them. This skill ensures every agreement is regularly re-validated against current conditions and either renewed (still relevant), revised (needs changes), or sunset (no longer serves its purpose). It prevents governance decay where the written rules diverge from the lived reality.

## B. Domain Scope

Any active agreement in the agreement registry that has a review date. This includes all agreement types: space agreements, access agreements, organizational agreement fields, stewardship agreements, culture codes, and the UAF. The UAF has its own review provisions (annual, never auto-expires) but the review process itself uses this skill.

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
