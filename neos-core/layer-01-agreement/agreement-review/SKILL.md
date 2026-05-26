---
name: agreement-review
description: "Run the periodic review cycle for any agreement -- evaluating current relevance, checking for staleness or conflict, and producing a review outcome: renew as-is, revise through amendment, or sunset with graceful deprecation."
layer: 1
version: 0.1.0
depends_on: [agreement-creation, agreement-amendment, agreement-registry, domain-mapping]
---

# agreement-review

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

- Cross-ETHOS agreements are reviewed by a body that includes representatives from each affected ETHOS. Each ETHOS must agree on the review outcome.
- If one ETHOS wants to sunset an agreement that another ETHOS still needs, the agreement is revised to narrow scope rather than fully sunset. The departing ETHOS's obligations under the agreement cease through proper amendment.
- Registry synchronization: when a cross-ETHOS agreement is reviewed, the review record is entered in all affected registries.
