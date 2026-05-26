---
name: post-emergency-review
description: "Conduct a mandatory retrospective of every emergency -- decision by decision, against authorization scope -- by a review body that excludes anyone who held emergency authority during the crisis."
layer: 8
version: 0.1.0
depends_on: [emergency-reversion, governance-health-audit]
---

# post-emergency-review

## C. Trigger Conditions

- **Emergency reversion**: every emergency reversion triggers a mandatory post-emergency review, scheduled within 14 days of the reversion trigger
- **Non-occurrence escalation**: if a post-emergency review has not been scheduled within 14 days of reversion, automatic escalation notifies all ecosystem members and the OSC. Continued non-occurrence triggers a Layer VII safeguard
- **Cross-emergency pattern review**: when 3 or more emergencies occur within a 12-month period, a meta-review is triggered examining patterns across all emergencies

## D. Required Inputs

- **Crisis Operations Log**: the complete decision record from the emergency (from crisis-coordination)
- **Reversion Record**: the complete reversion documentation including decision inventory and ratification outcomes (from emergency-reversion)
- **Pre-authorization registry**: the authority scopes, ceilings, and constraints that governed the emergency roles (from pre-authorization-protocol)
- **Emergency criteria**: the criteria that triggered the emergency, including entry/exit thresholds (from emergency-criteria-design)
- **Post-Emergency Review template**: the structured report template (from `assets/post-emergency-review-template.yaml`)
- **Review checklist**: the structured evaluation framework (from `assets/review-checklist.yaml`)

## E. Step-by-Step Process

1. **Appoint review body.** The review body consists of at least three ecosystem members who did not hold any emergency role during the reviewed emergency. If the emergency involved all qualified members, the review body draws from adjacent ETHOS. Appointment follows the role-assignment skill process. The review body cannot include the circle steward who confirmed the emergency declaration.
2. **Confirm independence.** Each review body member confirms they held no emergency role, made no emergency decisions, and have no direct financial interest in the review outcome. Independence declarations are logged in the review report.
3. **Review emergency declaration.** The review body evaluates: Was the entry criterion properly triggered? Did the data source confirm the threshold crossing? Was the declaration timely? Was the circuit breaker transition properly logged? This is not a judgment on whether the emergency was "justified" -- it is a verification that the criteria-based declaration process was followed.
4. **Evaluate each decision against authorization scope.** For every decision in the Crisis Operations Log, the review body assesses: (a) Was the decision within the role holder's pre-authorized scope? (b) Was the decision within the role holder's hard ceilings? (c) Was the decision properly classified (immediate/short-cycle/deferred)? (d) Was the 24-hour reporting requirement met for immediate decisions? (e) Were irreducible constraints respected?
5. **Assess ceiling utilization.** Review total spending and commitment against pre-authorized ceilings. Document any ceiling violations with the role holder's stated justification. Evaluate whether ceiling violations were proportionate to the crisis need, regardless of outcome quality.
6. **Review the deferred decision queue.** Evaluate whether decisions were appropriately classified as deferred or whether crisis-relevant decisions were improperly deferred (leaving needs unaddressed) or non-crisis decisions were improperly classified as immediate (scope creep).
7. **Evaluate reversion compliance.** Review whether authority cessation was immediate upon the reversion trigger. Document any authority continuation attempts. Evaluate whether the ratification process was completed within the 30-day window. Identify any auto-reverted decisions and their consequences.
8. **Assess exit criteria application.** Evaluate whether exit criteria were properly monitored and whether the reversion trigger fired at the correct time. If the auto-reversion timer expired before exit criteria were met, evaluate whether the maximum duration was appropriate.
9. **Draft recommendations.** The review body produces structural recommendations through the normal ACT process. Recommendations may include: adjustments to emergency criteria thresholds, modifications to pre-authorization scopes or ceilings, changes to compressed ACT timelines, additional training for role holders, new criteria for risks identified during the emergency. Recommendations are advisory -- the review body has no directive authority.
10. **Publish the Post-Emergency Review Report.** The report is published to all ecosystem members and the OSC. Publication cannot be suppressed or delayed by leadership or by former emergency role holders. The report becomes a permanent governance record.

## F. Output Artifact

A Post-Emergency Review Report following `assets/post-emergency-review-template.yaml`. The report contains: review ID, emergency ID reference, review body composition with independence declarations, declaration compliance assessment, decision-by-decision evaluation against authorization scope, ceiling utilization analysis, deferred decision queue assessment, reversion compliance evaluation, exit criteria application assessment, structural recommendations, and publication date. The report is accessible to all ecosystem members.

## G. Authority Boundary Check

- **The review body** produces recommendations, never directives -- it cannot mandate governance changes
- **No individual or body** can suppress, delay, or redact the review report
- **Former emergency role holders** cannot serve on the review body, influence the review body's composition, or approve the report before publication
- **The review body** evaluates decisions against pre-authorized scope, not against outcomes -- good results do not validate scope violations
- **The OSC** receives the report but does not gate its publication or modify its findings
- **Non-occurrence of the review** triggers Layer VII safeguard escalation -- the review cannot be quietly abandoned

## H. Capture Resistance Check

**Capital capture.** The review examines all resource decisions for alignment with pre-authorized scope and ceilings. Emergency funding arrangements are evaluated for whether they created undisclosed obligations or dependencies. A funder who provided emergency resources cannot influence the review body's composition or findings. Financial decisions made under crisis pressure receive the same structural scrutiny as any other emergency decision.

**Charismatic capture.** The exclusion of emergency role holders from the review body is the primary structural defense. A beloved leader who performed heroically during the emergency cannot assess their own decisions. The review evaluates decisions against scope, not against character or outcomes. If the community perceives the review as "ungrateful," the structural mandate holds: the review is not optional, regardless of how well the emergency was handled. Good performance deserves acknowledgment, but acknowledgment does not replace structural accountability.

**Emergency capture.** The review specifically examines whether emergency authority was properly bounded, properly ceased, and properly reverted. Patterns of scope creep, ceiling violations, authority continuation, or exit criteria manipulation are documented. When the same individual holds emergency roles across multiple emergencies, the cross-emergency pattern review examines whether the individual is accumulating informal emergency expertise that resists rotation.

**Informal capture.** The review body's independence requirement and the mandatory publication of findings ensure that the review is not captured by those being reviewed. The structured checklist in `assets/review-checklist.yaml` prevents the review from becoming a subjective narrative that the most persuasive member controls.

## I. Failure Containment Logic

- **Review body cannot be formed**: if no qualified non-role-holder members are available, the review draws from adjacent ETHOS or, as a last resort, the OSC appoints temporary reviewers from outside the ecosystem
- **Role holder disagrees with review findings**: the role holder's response is included in the published report as an appendix, but cannot delay or modify the review body's findings
- **Review identifies illegal activity**: the review body documents the finding and recommends legal consultation through normal governance. The review body does not have investigative or enforcement authority
- **Community pressure to skip review**: the mandatory trigger prevents skipping. If ecosystem members attempt to consent to waiving the review, the consent itself is structurally invalid -- the review mandate is embedded in the emergency governance framework, not subject to per-instance consent
- **Review delayed beyond 30 days**: the non-occurrence safeguard triggers Layer VII escalation. The OSC is notified. The review proceeds as soon as possible but its recommendations may be less actionable if significant time has passed

## J. Expiry / Review Condition

Post-Emergency Review Reports do not expire -- they are permanent historical records. The review process itself is not subject to periodic review because it is triggered by emergency reversion, not by schedule. The review checklist in `assets/review-checklist.yaml` is reviewed annually alongside emergency criteria and pre-authorization reviews to ensure evaluation criteria remain appropriate. If the ecosystem has not experienced an emergency in two years, the review checklist is reviewed through a tabletop exercise to confirm readiness.

## K. Exit Compatibility Check

When a member of the review body exits the ecosystem mid-review, the remaining members continue and a replacement is appointed if the body falls below three members. Completed review reports authored by departed members remain valid. When a former emergency role holder exits during the review period, the review proceeds -- their decisions are evaluated against scope regardless of their presence. The departing role holder's written response (if any) is included in the report. Past review reports involving departed members remain in the governance record.

## L. Cross-Unit Interoperability Impact

Post-Emergency Review Reports for each ETHOS are published to all ecosystem members, enabling cross-unit learning from emergency experiences. When an emergency affected multiple ETHOS, each conducts its own review independently, and the OSC may commission a cross-ETHOS synthesis report. Review recommendations that have implications beyond the ETHOS's domain (e.g., "ecosystem-level pre-authorization coordination needed") are forwarded to the OSC for ecosystem-wide consideration. At federation scale, post-emergency review reports may be shared between ecosystems as learning resources, with identifying details anonymized if requested.
