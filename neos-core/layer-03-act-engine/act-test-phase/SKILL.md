---
name: act-test-phase
description: "Run the Test phase of the ACT process -- implement the consented proposal on a reversible, time-limited basis with defined success criteria, midpoint check-in, and structured review leading to adoption, extension, modification, or revert."
layer: 3
version: 0.1.0
depends_on: [act-consent-phase, proposal-creation, domain-mapping]
---

# act-test-phase

## C. Trigger Conditions

- The consent phase completes with a positive outcome (consented or consensus_reached)
- The consent record specifies that the test phase applies (not explicitly waived)
- The proposer and review body agree on test parameters before implementation begins

## D. Required Inputs

- The **consented proposal** with the final version from the consent phase
- **Test duration**: how long the change will be tested (proposed in the original proposal, confirmed during consent)
- **Success criteria**: measurable conditions that determine whether the change achieves its intended purpose (must be defined BEFORE the test starts)
- **Review body**: who evaluates the test at its conclusion (typically the same body that consented)
- **Revert procedure**: what specific actions restore the pre-test state if the change is reverted

## E. Step-by-Step Process

1. **Define test parameters.** Before implementation, the proposer and review body confirm: test duration, success criteria (specific and measurable), midpoint check-in date (mandatory for tests over 60 days), revert procedure, and review body composition.
2. **Implement.** The consented change is put into effect on a reversible basis. The implementation start date is recorded.
3. **Monitor.** During the test period, affected parties may report observations to the review body. Observations are documented but do not trigger early termination (except in emergency, see Section G).
4. **Midpoint check-in** (for tests over 60 days). The review body convenes to evaluate early signals. They may flag concerns and request the proposer to document adjustments, but they cannot end the test early unless emergency provisions apply. The midpoint check-in is documented.
5. **Review.** At the test end date, the review body convenes and evaluates each success criterion against evidence gathered during the test. Four outcomes are possible:
   - **Adopt permanently**: the change has met all or substantially all success criteria. It enters the agreement registry as a permanent agreement via agreement-creation.
   - **Extend test**: the test shows promise but needs more time. Maximum one extension, up to the original test duration. A new end date is set.
   - **Modify and re-test**: identified issues require changes. The proposal returns to the advice phase with specific modifications and a new test period.
   - **Revert**: the change has not met success criteria or has caused harm. The pre-test state is restored per the documented revert procedure.
6. **Auto-safety.** If the review date passes without the review body convening: automatic 30-day extension with escalation notice sent to all affected parties. If the review body still does not convene after the 30-day extension, the change auto-reverts to the pre-test state. This ensures no test becomes permanent by neglect.

## F. Output Artifact

A test report following `assets/test-report-template.yaml` containing: proposal ID, test start and end dates, midpoint check-in date and findings (if applicable), revert procedure, each success criterion with met/not-met determination and supporting evidence, review body composition, review date, observations during the test period, the review body's outcome decision, any modifications or extension details, and the agreement registry ID if adopted permanently.

## G. Authority Boundary Check

- The **review body cannot extend tests indefinitely** — maximum one extension, for a total test period of 2x the original duration. After that, the test must result in adoption, modification, or revert.
- **Emergency revert** can be triggered by any 3 circle members acting jointly if the test is causing active harm. The emergency revert must be ratified by the full review body within 48 hours — if not ratified, the test resumes.
- **No individual** can unilaterally declare a test successful or failed. The review body evaluates collectively against the pre-defined success criteria.
- The review body **cannot change the success criteria after the test begins** — the criteria established before implementation are the criteria used for evaluation. If the criteria prove inadequate, the appropriate response is "modify and re-test" with better criteria.
- Authority scopes are formally defined by the domain-mapping and role-assignment skills in Layer II (Authority & Role).

## H. Capture Resistance Check

**Sunk cost capture.** "We already invested resources in this change — we can't revert." Revert is always a structural option regardless of investment. The test report evaluates against success criteria, not against investment. Sunk cost reasoning is documented as a capture risk if raised during the review.

**Authority creep.** Temporary authority granted during a test becomes de facto permanent because "it's working fine." The auto-revert mechanism ensures every test has a hard end date. If the review body does not convene, the change reverts automatically. There is no path from "test" to "permanent" that bypasses an explicit review decision.

**Emergency capture during test.** A crisis during the test period is used to argue the change should become permanent without review — "we can't go back to the old way during a crisis." Emergency does not suspend the review requirement. If a crisis prevents the review from occurring on schedule, the 30-day auto-extension provides buffer. The change still requires explicit adoption to become permanent.

## I. Failure Containment Logic

- **Success criteria are unclear or unmeasurable**: the review body must define specific, measurable criteria BEFORE the test begins. "It works well" is not a criterion. "Project completion rates increase by at least 10%" is. If criteria cannot be defined clearly, the test cannot start — the proposal returns to advice for criteria refinement.
- **Review body cannot convene**: the 30-day auto-extension provides buffer. If the review body still cannot convene after the extension, the change auto-reverts. The ecosystem cannot have perpetual tests.
- **Partial success** (some criteria met, others not): the review body chooses between "adopt with noted exceptions" (the unmet criteria become follow-up action items) or "modify and re-test" (the proposal returns to advice with specific changes targeting the unmet criteria).
- **Test causes unexpected harm**: any affected party can request an emergency review. Three circle members acting jointly can trigger an emergency revert, subject to ratification by the full review body within 48 hours.

## J. Expiry / Review Condition

- Tests expire on their documented end date. Extended tests expire on the new end date.
- Maximum total test duration: 2x the original test period (original + one extension of equal length).
- After expiry without review: 30-day auto-extension with escalation notice, then auto-revert.
- Emergency tests (those arising from emergency proposals) have a maximum total duration of 60 days (30 + 30 extension), after which they auto-revert regardless.

## K. Exit Compatibility Check

- If **review body members exit** during the test period, replacements are drawn from the affected parties list. The replacement members review the full test documentation before participating in the review.
- If the **proposer exits**, the test continues — another impacted party adopts stewardship of the test and its review. The test's success criteria and parameters do not change.
- If **30% of affected parties exit** during the test period, an automatic emergency review is triggered. The review body convenes within 14 days to evaluate whether the mass exit is related to the test and whether continuation is appropriate.

## L. Cross-Unit Interoperability Impact

- Cross-ETHOS tests require each ETHOS to independently evaluate success within their own domain. One ETHOS can revert the change in their domain without affecting the other ETHOS's ongoing test.
- The test report includes domain-specific sections for each affected ETHOS, with each ETHOS's review body contributing their evaluation.
