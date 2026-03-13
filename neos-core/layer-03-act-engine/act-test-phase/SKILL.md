---
name: act-test-phase
description: "Run the Test phase of the ACT process -- implement the consented proposal on a reversible, time-limited basis with defined success criteria, midpoint check-in, and structured review leading to adoption, extension, modification, or revert."
layer: 3
version: 0.1.0
depends_on: [act-consent-phase, proposal-creation, domain-mapping]
---

# act-test-phase

## A. Structural Problem It Solves

Without structured testing, decisions become permanent by default — once consented to, a change persists indefinitely because there is no mechanism to revisit it. Momentum replaces evaluation, and "we already decided this" becomes a shield against improvement. This skill ensures every consented change is implemented reversibly, with defined success criteria established before implementation begins and a mandatory review point where the change is evaluated on evidence, not inertia. It prevents the "we never revisited that decision" failure mode.

## B. Domain Scope

Any proposal that has achieved consent or consensus through the act-consent-phase skill. The test phase applies to all proposal types, though the test parameters (duration, criteria, review body) scale with the proposal's scope and impact. Some proposals may skip the test phase by explicit consent of the deciding body — typically renewals of proven patterns or minor procedural adjustments. The decision to skip must be recorded in the consent record.

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

Authority scope is defined by the domain contract (see domain-mapping skill, Layer II). The acting participant's role-assignment record establishes their authority within the relevant domain.

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

- Cross-AZPO tests require each AZPO to independently evaluate success within their own domain. One AZPO can revert the change in their domain without affecting the other AZPO's ongoing test.
- The test report includes domain-specific sections for each affected AZPO, with each AZPO's review body contributing their evaluation.
- Federation extensibility: when two ecosystems share a governance space and test a joint change, each ecosystem evaluates independently and both must adopt for the change to persist in the shared space.

## OmniOne Walkthrough

The OmniOne AE has consented to test a new formula for distributing community development funds across circles. The current system divides funds equally; the proposed formula weights allocation by active member count (60%) and project milestone completion (40%). Test parameters are set before implementation:

- **Duration**: 90 days
- **Midpoint check-in**: Day 45
- **Success criteria**: (1) No circle loses more than 15% of its current funding level, (2) Aggregate project completion rates increase by at least 10%, (3) No circle raises a formal objection during the test period
- **Review body**: The 5 AE circle leads plus the proposer
- **Revert procedure**: Restore the equal distribution formula and recalculate any allocations made during the test period

Implementation begins on March 1. The new formula is applied to the Q2 allocation cycle. At the Day 45 midpoint check-in, the review body discovers that the Education circle's allocation dropped by 22% — exceeding the 15% threshold in Criterion 1. The review body documents the finding but does not end the test. Instead, the proposer implements a temporary floor: no circle's allocation may drop below 85% of its pre-test level during the remaining test period. This floor is documented as a mid-test adjustment.

At Day 90 (May 30), the review body convenes for the full review:
- **Criterion 1**: Partially met — the initial breach was corrected at midpoint, and no circle fell below the 85% floor after the adjustment
- **Criterion 2**: Met — aggregate project completion rates increased 14%
- **Criterion 3**: Met — no formal objections were raised during the test period

The review body deliberates. The formula shows clear improvement in project completion but the initial funding floor breach revealed a design flaw. Decision: **Adopt with modification** — the formula becomes permanent with the 85% funding floor built in as a permanent safeguard. The modified formula enters the agreement registry as a permanent agreement (AGR-OMNI-2026-028).

Edge case: If the midpoint had revealed a 40% funding drop for the Education circle (a severe threshold breach causing direct harm to the mentorship program), any 3 AE members could have triggered an emergency revert. The emergency revert would restore equal distribution immediately, with ratification by the full review body within 48 hours.

## Stress-Test Results

### 1. Capital Influx

A test of a new project funding model is underway when a major donor offers to fund the project directly, bypassing the test. The review body evaluates: the donor's offer is separate from the test. The test continues on its own terms with its own success criteria. The donor's funding is documented as external context but does not influence whether the test's formula meets its success criteria. If the test succeeds and is adopted, the donor's funding can be integrated through normal resource allocation proposals. If the test fails and reverts, the donor's offer stands independently. The test's integrity is maintained by evaluating it against its pre-defined criteria, not against alternative funding sources.

### 2. Emergency Crisis

A natural disaster strikes during a 90-day test of new emergency response protocols. The irony is not lost — the test is testing the very protocols needed for the current crisis. The review body conducts an accelerated review: the crisis itself provides real-world evidence for the success criteria. If the protocols performed well during the actual emergency, the review body may adopt permanently based on demonstrated effectiveness. If the protocols failed during the crisis, the revert is obvious and immediate. The crisis compresses the test timeline but provides higher-quality evidence than a normal test period would. The emergency does not bypass the review requirement — it accelerates it.

### 3. Leadership Charisma Capture

A charismatic leader's proposal is in the test phase and showing mixed results. The leader campaigns to "just adopt it" without waiting for the full review — "the evidence is already clear, waiting is bureaucratic." The auto-review mechanism prevents this: the test has a defined end date and only the review body can determine the outcome. The leader cannot unilaterally declare success. If the leader is on the review body, they have one voice among several. The success criteria were defined before the test began and cannot be retroactively adjusted to favor adoption. The review body evaluates evidence, not enthusiasm.

### 4. High Conflict / Polarization

A test of a new meeting format generates polarized reactions. Half the affected participants report improved engagement; the other half report feeling excluded by the new format. The success criteria include "participant satisfaction above 70% in post-meeting surveys." At review, satisfaction is at 55% — criterion not met. The review body faces a choice: the format clearly works for some but not others. Decision: modify and re-test with a hybrid approach that incorporates elements preferred by each faction. The modified proposal returns to advice with the test report as evidence. The polarization is addressed through structural iteration, not through one faction overriding the other.

### 5. Large-Scale Replication

At 5,000 members, a test of a new inter-circle resource sharing protocol runs simultaneously across 12 circles. Each circle tracks its own success criteria within its domain. At review, 10 circles report criteria met, 2 circles report criteria not met due to their unique resource constraints. The review body decides: adopt for the 10 circles where criteria are met, modify and re-test for the 2 where they are not. Cross-circle tests at scale require domain-specific evaluation — a one-size-fits-all determination would miss local conditions. The test report includes 12 domain-specific sections, and the review body's decision is granular rather than binary.

### 6. External Legal Pressure

During a test of a new data-sharing agreement between circles, a regulatory body requests access to the data being shared under the test. The test itself is not affected — data-sharing continues per the test parameters. If the regulation requires modifications to how data is shared, this is treated as an external constraint, not as a test failure. The review body evaluates the test against its original success criteria. If regulatory compliance requires permanent changes to the data-sharing protocol, those changes are proposed separately through normal ACT process. The test's internal evaluation remains independent of external regulatory interaction.

### 7. Sudden Exit of 30% of Participants

During a 90-day test of a new resource distribution formula, 5 of 15 affected AE members exit OmniOne. The 30% exit threshold triggers an automatic emergency review within 14 days. The review body convenes early and evaluates: is the mass exit related to the test? Exit interviews (where provided) reveal that 3 of the 5 departed members were unhappy with the new formula's impact on their circles. The review body determines the test itself is a contributing factor. Decision: revert to the pre-test distribution and propose a modified formula through a new full ACT cycle that addresses the departed members' concerns — even though they are no longer present, their feedback indicates a structural flaw. The test report documents the mass exit, its apparent relationship to the test, and the decision to revert. The revert procedure restores equal distribution and recalculates any allocations made during the test period.
