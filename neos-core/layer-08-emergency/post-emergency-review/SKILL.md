---
name: post-emergency-review
description: "Conduct a mandatory retrospective of every emergency -- decision by decision, against authorization scope -- by a review body that excludes anyone who held emergency authority during the crisis."
layer: 8
version: 0.1.0
depends_on: [emergency-reversion, governance-health-audit]
---

# post-emergency-review

## A. Structural Problem It Solves

Emergency authority is granted with compressed accountability. Decisions are made under time pressure, with reduced participation, and under emotional strain. Without a structured, mandatory retrospective, these decisions become unchallenged precedent: "We did it during the last emergency, so it must be acceptable." Over time, each emergency expands the informal understanding of what emergency authority permits. The post-emergency review is the structural mechanism that prevents this accretion. It is mandatory -- it cannot be skipped, deferred indefinitely, or waived because the emergency was "handled well." The review body excludes anyone who held emergency roles, eliminating self-assessment. Each decision is evaluated against its pre-authorized scope, not against the outcome. Good outcomes do not retroactively validate scope violations. The review produces recommendations through normal ACT process, never directives, ensuring that the accountability mechanism does not itself become an authority capture vector.

## B. Domain Scope

This skill applies after every emergency reversion (per emergency-reversion), during the Half-Open (Recovery) state of the circuit breaker. The review examines the complete Crisis Operations Log and Reversion Record for the concluded emergency. It operates within the domain boundary defined by domain-mapping (Layer II) -- a review of a SHUR Bali emergency examines only SHUR Bali's emergency decisions. Out of scope: the review does not conduct ongoing governance health monitoring (that is governance-health-audit, Layer VII) and does not design or modify emergency criteria (that is emergency-criteria-design). The review produces recommendations; implementation requires separate ACT processes.

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

## OmniOne Walkthrough

It is mid-July 2026. The Bali flooding emergency concluded on July 1, and the post-emergency review has been scheduled for July 12. The review body is appointed: Lina (AE member, did not hold any emergency role), Dewa (TH member, served as Safety Coordinator alternate but was not activated), and Yuki (AE member from SHUR Costa Rica, providing cross-ETHOS perspective). Wait -- Dewa was the designated alternate for Safety Coordinator. Was he activated? Review of the Crisis Operations Log confirms Dewa was not activated because Ratu (primary) was available throughout. Dewa is eligible for the review body. All three confirm independence.

**Declaration review.** The review body examines the June 15 declaration. Entry criterion ECR-SHUR-PS-01 required BMKG Level 3+ alert OR facility damage confirmed by two assessments. Both conditions were met. The declaration was logged at 14:00, approximately 2 hours after the second assessment was completed. The review body notes the 2-hour gap and recommends that future declarations include a target response time in the criteria design.

**Decision-by-decision evaluation.** The review body works through all 23 decisions from the Crisis Operations Log using the checklist in `assets/review-checklist.yaml`:

- 18 immediate decisions: all within Ratu's (Safety) and Nadia's (Resource) pre-authorized scopes. All reported within 24 hours. 17 within ceiling. 1 ceiling violation: Nadia exceeded her $5,000-per-decision ceiling by $800 for emergency water delivery on day 8.
- 3 short-cycle decisions: all properly processed with 24-hour advice and 12-hour consent. Participant counts: 18, 15, and 12 members respectively.
- 1 deferred decision: solar panel repair. Properly classified -- not a crisis response.

**Ceiling violation assessment.** The review body examines Nadia's $800 ceiling overage. Nadia's stated justification: the sole available water supplier quoted $5,800, and the alternative was no potable water for 32 members. The review body evaluates against scope (Resource Coordinator's authority covers essential operating expenditures -- water qualifies) and proportionality (the overage was 16% above ceiling, for a genuine basic need with no alternative supplier). The review body notes that the ceiling was appropriate for most decisions but did not account for monopoly supplier pricing during a crisis. Recommendation: increase the Resource Coordinator's per-decision ceiling to $7,000, to be processed through normal ACT consent.

**Reversion compliance.** The review body confirms that authority ceased at 14:01 on July 1, within one minute of the reversion trigger. They note Ratu's post-reversion request to retain Safety Coordinator authority (documented in the Reversion Record). The request was properly denied. Recommendation: include explicit guidance in pre-authorization training that authority cessation is structural and non-negotiable.

**Exit criteria assessment.** Exit criteria were met on July 1 (day 16 of a 14-day maximum, with a 4-day extension approved through emergency ACT consent). The extension was properly processed and consented. The actual reversion occurred 2 days before the extended deadline. The review body notes that the original 14-day maximum was nearly insufficient and recommends evaluating whether flooding events should have a 21-day default maximum.

**Edge case.** During the review, Ratu submits a written response disputing the review body's characterization of her post-reversion authority request. She argues she was "asking a question, not demanding authority." The review body includes Ratu's response as an appendix to the report but does not modify their finding. The finding states facts: Ratu contacted Ketut requesting continued authority; Ketut denied the request; the Reversion Record documents both. Ratu's intent is not the review body's concern -- the structural pattern is.

The Post-Emergency Review Report (PER-SHUR-2026-001) is published to all 38 members and the OSC on July 18. Three recommendations enter normal ACT process: ceiling adjustment, declaration response time, and maximum duration review.

## Stress-Test Results

### 1. Capital Influx

During the post-emergency review, the review body discovers that the Resource Coordinator accepted $15,000 from a cryptocurrency foundation during the emergency with a verbal agreement to "discuss future collaboration." The review evaluates this against the Resource Coordinator's authority scope: accepting emergency donations is within scope, but creating future obligations is not. The verbal agreement constitutes a scope boundary issue. The review body recommends that future pre-authorization training explicitly address conditional funding acceptance during emergencies. The recommendation enters normal ACT process. The review body does not punish the Resource Coordinator -- it documents the structural gap and proposes a structural fix. The foundation cannot influence the review body's findings because the body is composed of members who had no role in the emergency and no relationship to the funding decision.

### 2. Emergency Crisis

The flooding emergency review demonstrates the full post-emergency review cycle: appointment of independent review body, declaration compliance check, decision-by-decision evaluation, ceiling analysis, reversion compliance, and exit criteria assessment. The review identifies three actionable recommendations (ceiling, response time, duration) that enter normal ACT process. The review body's independence from emergency operations ensures that even a well-handled emergency receives structural scrutiny. The review is not punitive -- it is diagnostic. It asks "did the structure work?" not "were the people good?" This framing allows the ecosystem to improve its emergency governance without creating a culture where emergency role holders fear retrospective judgment.

### 3. Leadership Charisma Capture

After an emergency where Surya informally directed operations despite holding no emergency role, the post-emergency review identifies the pattern: several members followed Surya's recommendations over the authorized Safety Coordinator's instructions. The review body documents this as a structural finding, not a personal accusation. Recommendation: future emergency communications should clearly identify which directives come from authorized role holders and which are member advice. Surya is not censured -- the review body has no punitive authority. But the pattern is documented in the permanent governance record, making it visible for future audits. If Surya's informal authority displacement recurs across multiple emergencies, the cross-emergency pattern review will identify it as a systemic issue requiring structural intervention.

### 4. High Conflict / Polarization

The two polarized factions attempt to influence the post-emergency review. Faction A argues the review should praise the Resource Coordinator for accepting the crypto foundation's funding during the crisis. Faction B argues the review should condemn it. The review body evaluates against authorization scope, not factional preference: accepting emergency donations was within scope; creating future obligations was not. The structured checklist prevents the review from becoming a political judgment. Both factions receive the same published report with the same structural findings. The review body's independence from both factions (none served as emergency role holders) and the structured evaluation framework prevent the review from being captured by either side's narrative. Recommendations enter normal ACT process where both factions can participate in deliberation.

### 5. Large-Scale Replication

At scale with 12 SHUR locations, post-emergency reviews occur independently per ETHOS. The review report template and checklist are identical across all locations, enabling cross-ETHOS learning. The OSC commissions annual meta-reviews synthesizing findings across all emergencies ecosystem-wide. Common patterns emerge: ceiling violations are most common in resource crisis emergencies, declaration timing is slowest in governance incapacity emergencies, and reversion compliance is highest in natural disaster emergencies (because exit criteria are least ambiguous). These ecosystem-level insights inform annual reviews of emergency criteria, pre-authorization scopes, and compressed timelines. The post-emergency review scales through local execution with centralized synthesis.

### 6. External Legal Pressure

Indonesian regulators request access to the Post-Emergency Review Report as evidence of "adequate governance oversight." The report is a published document -- sharing it does not compromise internal governance. However, the regulators suggest that future reviews should be conducted by "certified external auditors" rather than internal members. The ecosystem evaluates this through normal ACT process: external auditors could provide additional professional perspective, but they cannot replace the independence requirement (exclusion of emergency role holders) or the structural mandate (mandatory, non-waivable). The ecosystem can invite external observers to future reviews while maintaining its own review body composition rules. External requirements supplement internal governance; they do not replace it. The review documents the regulatory request as context for future review design.

### 7. Sudden Exit of 30% of Participants

Twelve members exit after the emergency, three of whom were on the post-emergency review body shortlist. The review body appointment draws from the remaining 26 members, still finding three qualified members who did not hold emergency roles. If the departures had included all non-role-holding members, the review would draw from adjacent ETHOS. The departures reduce the diversity of perspectives available to the review body, which is noted in the report. The review proceeds with the available body. Departed members who held emergency roles have their decisions reviewed without their presence -- the review evaluates decisions against scope, not against the decision-maker's current membership status. If departed members submit written responses, those responses are included as appendices. The permanent governance record ensures that emergency accountability is not erased by subsequent departures.
