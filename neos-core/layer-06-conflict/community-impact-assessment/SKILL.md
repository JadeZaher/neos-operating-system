---
name: community-impact-assessment
description: "Facilitate ETHOS-wide or ecosystem-wide processing when harm extends beyond direct parties -- surface systemic patterns, identify structural gaps, and route governance change recommendations through ACT so that recurring conflicts become structural improvements."
layer: 6
version: 0.1.0
depends_on: [harm-circle, proposal-creation, act-consent-phase, agreement-amendment]
---

# community-impact-assessment

## C. Trigger Conditions

- A harm circle finding identifies a structural gap that contributed to the harm
- A pattern of three or more similar conflicts within an ETHOS is identified through triage record analysis
- A repair agreement includes a structural change commitment with community-wide implications
- An escalation-triage assessment routes a situation to Tier 4 (community assessment)
- A single incident affects community-wide trust in governance processes (high-severity, broad-scope triage assessment)
- A coaching intervention reveals a widespread skill gap suggesting a systemic onboarding or training deficiency

## D. Required Inputs

- **Triggering evidence**: the conflict records, triage assessments, harm circle findings, or pattern analysis that triggered the assessment. Format: linked record IDs and a summary of the systemic concern.
- **Scope determination**: whether the assessment is ETHOS-wide or ecosystem-wide, based on where the impact has been felt. Verified against domain-mapping.
- **Privacy boundaries**: explicit identification of what information from underlying conflicts can be shared in the community process and what must remain private. Individual harm circle disclosures are private by default.
- **Convener identity**: who is calling the assessment -- typically a facilitator, steward, or the escalation-triage process. The convener must not be a party to any of the underlying conflicts.
- **Participant list**: who participates in the community processing session. For ETHOS-wide assessments, all ETHOS members are invited. For ecosystem-wide assessments, representatives from each affected ETHOS participate.

## E. Step-by-Step Process

1. **Receive the trigger and confirm scope.** The convener reviews the triggering evidence and confirms that the situation meets the threshold for community impact assessment: harm extends beyond direct parties, a pattern exists, or a structural gap has been identified. The convener determines the scope (ETHOS-wide or ecosystem-wide) and documents the rationale. Timeline: within 7 days of the triggering event or pattern identification.
2. **Establish privacy boundaries.** The convener works with the facilitators of the underlying conflict processes (harm circles, coaching interventions) to define what information can be shared with the community. The principle: systemic findings are shared (what structural gap exists, what pattern was identified); individual details are private (who was involved, what was said in harm circles). Individual participants in underlying conflicts may consent to sharing their experience, but this is never required. The privacy boundary is documented before any community session.
3. **Prepare the systemic analysis.** The convener and a small analysis team (2-3 people with governance knowledge and no involvement in the underlying conflicts) review the triggering evidence and prepare a systemic analysis. The analysis identifies: the pattern or structural gap, the governance mechanisms that failed or were absent, the conditions that allowed the pattern to persist, and preliminary hypotheses about what structural changes could address it. The analysis is shared with participants in advance of the community session.
4. **Facilitate the community processing session.** The convener facilitates a structured community dialogue. The session has three phases. Phase 1 -- Impact: participants share how the systemic issue has affected them and the community's trust in governance. This is not a re-litigation of individual conflicts; it is an expression of community impact. Phase 2 -- Systemic Analysis: the analysis team presents their findings and hypotheses. Participants discuss, challenge, and refine the analysis. Phase 3 -- Recommendations: participants collectively generate governance change recommendations that address the structural gap. Recommendations are framed as proposals, not mandates.
5. **Document the assessment report.** The convener creates the community impact assessment report using impact-assessment-template.yaml. The report documents: the triggering evidence (with privacy protections), the scope, the community processing session outcomes, the systemic findings, and the specific governance change recommendations. The report distinguishes between findings (what was identified) and recommendations (what changes are proposed).
6. **Route recommendations through ACT.** Each governance change recommendation is formalized as a proposal through proposal-creation and enters the standard ACT process (advice, consent, test). The community impact assessment report is linked to each proposal as supporting evidence. The proposals are not fast-tracked -- they go through the same consent process as any other governance change, ensuring community-wide buy-in.
7. **Follow up on implementation.** The convener tracks whether the recommended proposals are submitted, processed through ACT, and implemented. If proposals are rejected through the consent process, the convener documents the rationale and assesses whether the systemic gap remains unaddressed. Unaddressed systemic gaps are flagged for the next quarterly Layer VI review.

## F. Output Artifact

A community impact assessment report following `assets/impact-assessment-template.yaml`, containing: unique assessment ID, date, convener identity, scope (ETHOS-wide or ecosystem-wide), triggering evidence with privacy-protected summaries, privacy boundary documentation, systemic analysis findings, community processing session record (impact statements summarized, analysis discussion, recommendations), each governance change recommendation with rationale and ACT proposal link, implementation tracking, and linked records. The report is accessible to all participants in the community processing session and to the governance bodies responsible for processing the recommendations.

## G. Authority Boundary Check

- The **convener** has assessment and facilitation authority. They convene the process, manage the community session, and ensure the report is completed. The convener cannot impose governance changes -- recommendations must go through ACT.
- The **community processing session** has deliberative authority. Participants discuss, analyze, and generate recommendations. The session cannot pass binding decisions -- its output is recommendations that enter the ACT process as proposals.
- **Individual privacy is protected** by the convener's authority boundary. The convener cannot disclose private details from underlying conflict processes, even if participants in the community session request them. The privacy boundary established in step 2 is the convener's mandate.
- The **analysis team** has analytical authority -- they review evidence and present hypotheses. They cannot pre-determine the recommendations; those emerge from the community processing session.
- **No participant** in the community session can use the session to re-litigate an already-resolved individual conflict. The convener redirects re-litigation attempts to the systemic dimension: "We are examining the structural conditions, not re-opening the individual situation."

## H. Capture Resistance Check

**Capital capture.** A systemic finding implicates governance processes that benefit a major funder. The funder pressures the convener to narrow the assessment scope or soften the findings. The structural safeguard is the community processing session: findings are generated and validated collectively, not by the convener alone. The funder participates as one voice among many. If the funder attempts to derail the session, the convener names the dynamic and ensures all participants have equal voice. The assessment report documents any capture attempts.

**Charismatic capture.** A charismatic leader steers the community processing session toward findings that protect their governance philosophy, dismissing recommendations that would change processes they championed. The structured three-phase session format provides the safeguard: the impact phase ensures all voices are heard before analysis begins, the systemic analysis is prepared by an independent team (not the charismatic leader), and recommendations emerge from collective deliberation. The convener monitors for dominance and applies equal-voice facilitation.

**Emergency capture.** A crisis is used to prevent or defer community impact assessment -- "we have bigger problems right now." Emergency deferral is legitimate for active crises but is time-bounded: the assessment is deferred for the duration of the emergency plus 30 days for stabilization, then proceeds. The deferral is documented and cannot be extended indefinitely. Crises that were themselves caused by the systemic gap being assessed are explicitly not grounds for deferral.

**Informal capture.** "We already talked about this informally and everyone is fine" is used to prevent a formal assessment. The convener verifies this claim by checking the pattern evidence: if three similar conflicts occurred and all were "resolved informally," the systemic question remains. Informal resolution of individual conflicts does not address the structural conditions that produced the pattern. The assessment proceeds based on the pattern evidence, not on claims of informal resolution.

## I. Failure Containment Logic

- **Community session attendance is low**: the convener assesses whether the low attendance reflects assessment fatigue, lack of awareness, or active avoidance. The session can proceed with any number of participants, but low attendance is documented and the findings note the limitation. A follow-up session may be scheduled with broader outreach.
- **Re-litigation dominates the session**: the convener pauses and reinforces the systemic framing. If re-litigation persists, the convener documents the dynamic and continues with participants who engage with the systemic analysis. The underlying individual conflict processes are not reopened by the community session.
- **No consensus on systemic findings**: disagreement about systemic findings is documented in the report as competing analyses. Multiple recommendations may emerge from different analyses, each entering ACT as separate proposals. The community decides through the consent process which changes to adopt.
- **Recommendations are rejected through ACT**: the convener documents the rejections and their rationale. If the systemic gap remains unaddressed, the documentation serves as input for future assessments and pattern analysis. Rejected recommendations are not re-submitted without new evidence.
- **Assessment reveals harm beyond Layer VI scope**: if the assessment identifies patterns that suggest systemic capture (Layer VII) or structural inter-ETHOS disputes (Layer V), the convener routes those findings to the appropriate layer and documents the handoff.

## J. Expiry / Review Condition

Community impact assessment reports do not expire -- they are permanent governance records that inform pattern analysis and future assessments. Implementation tracking for recommendations is reviewed at 30, 60, and 90 days after the ACT process completes. If recommended proposals were adopted, the assessment tracks whether the implemented changes actually address the identified structural gap. If the same pattern recurs after implementation, a follow-up assessment is triggered. The community-impact-assessment skill itself is reviewed annually as part of the Layer VI review cycle. Quarterly pattern analysis across all conflict records (triage assessments, harm circles, coaching plans) identifies whether new community impact assessments should be convened. Minimum review interval for implementation tracking: 30 days.

## K. Exit Compatibility Check

When a participant exits during an active community impact assessment, the assessment continues -- the systemic analysis is not dependent on any individual's participation. The exiting participant's contributions to the community processing session remain part of the record (they participated while a member). If the **convener** exits, a replacement is assigned within 14 days. If the exiting participant was a party to one of the underlying conflicts, the privacy boundaries for that conflict are maintained regardless of exit. The exiting participant's departure may itself become data for the systemic analysis if it is related to the structural gap being examined.

## L. Cross-Unit Interoperability Impact

Ecosystem-wide community impact assessments require coordination across ETHOS. The convener is selected from a neutral position or from an ETHOS not directly implicated in the findings. Each affected ETHOS sends representatives to the community processing session. The assessment report is distributed to all affected ETHOS. Recommendations that require changes in multiple ETHOS go through each ETHOS's ACT process independently -- the community impact assessment cannot impose changes across units. Cross-ETHOS pattern analysis is conducted by comparing conflict records across units using standardized triage and harm circle template data. If the assessment identifies a pattern unique to one ETHOS, that ETHOS conducts its own ETHOS-level assessment rather than processing it at ecosystem scale. Cross-ecosystem community impact assessments (between different NEOS ecosystems) are deferred to Layer V's inter-ecosystem coordination protocol.
