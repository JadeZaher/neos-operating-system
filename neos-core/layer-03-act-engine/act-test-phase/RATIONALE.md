---
skill: act-test-phase
type: rationale
---

# act-test-phase — Rationale & Design Notes

## A. Structural Problem It Solves

Without structured testing, decisions become permanent by default — once consented to, a change persists indefinitely because there is no mechanism to revisit it. Momentum replaces evaluation, and "we already decided this" becomes a shield against improvement. This skill ensures every consented change is implemented reversibly, with defined success criteria established before implementation begins and a mandatory review point where the change is evaluated on evidence, not inertia. It prevents the "we never revisited that decision" failure mode.

## B. Domain Scope

Any proposal that has achieved consent or consensus through the act-consent-phase skill. The test phase applies to all proposal types, though the test parameters (duration, criteria, review body) scale with the proposal's scope and impact. Some proposals may skip the test phase by explicit consent of the deciding body — typically renewals of proven patterns or minor procedural adjustments. The decision to skip must be recorded in the consent record.

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
