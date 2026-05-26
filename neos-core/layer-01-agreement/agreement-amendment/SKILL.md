---
name: agreement-amendment
description: "Modify an existing agreement through proper process -- classifying the amendment type, routing through the appropriate ACT level, and producing a versioned amendment record that maintains the full change history."
layer: 1
version: 0.1.0
depends_on: [agreement-creation, act-advice-phase, act-consent-phase, act-test-phase, domain-mapping]
---

# agreement-amendment

## C. Trigger Conditions

- A participant identifies that an existing agreement needs modification due to outdated terms, new circumstances, identified gaps, or conflict with another agreement
- The agreement-review skill produces a "revise" outcome, triggering this skill with specific changes identified
- A conflict resolution process identifies an agreement provision as the source of tension
- An agreement at a higher level in the hierarchy is amended, requiring lower-level agreements to be checked for consistency

## D. Required Inputs

- **Amendment proposer**: identity, role, and authority scope
- **Parent agreement ID**: the specific agreement being amended, with its current version number
- **Amendment type**: minor_clarification, substantive_change, scope_expansion, or scope_reduction
- **Proposed changes**: in diff format — what the text currently says and what it will say after amendment
- **Rationale**: why the change is needed, what problem it addresses, what happens if the agreement remains as-is
- **Affected parties**: all parties currently bound by the agreement plus any new parties affected by the amendment

## E. Step-by-Step Process

1. **Classify amendment type.** The proposer identifies the amendment type. The facilitator verifies the classification — a proposer cannot classify a scope expansion as a minor clarification to avoid fuller process.
2. **Route to minimum ACT level** based on type:
   - *Minor clarification* (fixing ambiguous language): circle-level consent of parties bound by the agreement. Advice phase is abbreviated (3 days).
   - *Substantive change* (modifying terms): full ACT cycle with all affected parties.
   - *Scope expansion* (adding parties or domains): full ACT cycle including both current and proposed-new affected parties.
   - *Scope reduction* (narrowing applicability): full ACT cycle with parties who will lose coverage — they must consent to the change.
   - *UAF amendment*: OSC consensus mode (all steward council members must actively agree). No abbreviated process regardless of amendment type.
3. **Run appropriate ACT phases.** Per the act-advice-phase, act-consent-phase, and act-test-phase skills. The test phase applies to substantive changes and scope changes; minor clarifications may skip testing by consent.
4. **Produce amendment record.** Per `assets/amendment-record-template.yaml`: amendment ID, parent agreement ID, amendment type, proposer, diff of changes, rationale, ACT level used, consent record ID, new agreement version number.
5. **Update registry.** The agreement in the registry is updated to the new version with the amendment record linked. The prior version is archived (not deleted) in the version history.

## F. Output Artifact

An amendment record per `assets/amendment-record-template.yaml` linked to the parent agreement, plus the updated agreement document with incremented version number. The registry reflects: the new version, the amendment date, the amendment type, and a link to the full amendment record including the consent record from the ACT process.

## G. Authority Boundary Check

- **Amendment scope cannot exceed the amending body's domain.** A circle cannot amend an ecosystem-level agreement. An ETHOS cannot amend another ETHOS's agreement field.
- **UAF amendments require OSC consensus** — this cannot be delegated to any sub-body. The highest-bar decision process applies to the highest-level agreement.
- **Amendment cannot create authority** that the original agreement did not grant. If the original agreement defines circle-level authority, an amendment cannot expand that to ecosystem-level authority without going through the appropriate ecosystem-level ACT process.
- **The proposer cannot reclassify** the amendment type after ACT routing — if the facilitator determines a "minor clarification" is actually a substantive change, the process escalates to the appropriate level.

## H. Capture Resistance Check

**Capital capture.** A donor pressures amendment of an accountability agreement to weaken oversight of funded projects. The full ACT process ensures all affected parties evaluate the amendment on structural merits. The donor's financial contribution does not modify the consent threshold or grant them special standing in the consent round.

**Amendment laundering.** A series of "minor clarifications" that cumulatively constitute a substantive change. The facilitator tracks amendment history and may reclassify an amendment as substantive if the cumulative effect crosses the threshold. The registry's version history makes the pattern visible.

**Emergency amendment.** A crisis is used to push through amendments under compressed timelines. Emergency timelines apply but the consent round cannot be eliminated. Emergency amendments auto-expire per provisional emergency rules and must be re-proposed through normal process for permanent effect.

## I. Failure Containment Logic

- **Consent fails on amendment**: the existing agreement remains unchanged. The amendment proposal may be revised and re-proposed.
- **Amendment creates conflict with higher-level agreement**: identified during synergy check or advice phase. The amendment cannot proceed until the conflict is resolved — either by amending the higher-level agreement first (through its own process) or by modifying the proposed amendment to be consistent.
- **Partial ratification** (some affected parties consent, others object): the amendment does not take effect. It returns to advice with the objectors' specific concerns documented.
- **Amendment proposer loses authority** (role change during process): another party within the domain may adopt the amendment proposal per standard adoption rules.

## J. Expiry / Review Condition

- Amendments do not have separate review dates — they modify the parent agreement, which retains its own review schedule.
- If an amendment expands the agreement's scope, the parent agreement's review date may be brought forward by the review body.
- Emergency amendments auto-expire in 30 days and must be re-proposed through normal process for permanence.

## K. Exit Compatibility Check

- If the amendment proposer exits, the amendment process continues if adopted by another party. The amendment's merit does not depend on the proposer's ongoing participation.
- If parties affected by the amendment exit, the amendment's affected-party list is re-evaluated. If the amendment becomes moot (e.g., scope reduction for parties who have all departed), it may be archived.
- Amendments ratified before a participant's exit remain in effect for remaining parties.

## L. Cross-Unit Interoperability Impact

- Amendments to agreements that span multiple ETHOS require consent from each affected ETHOS's deciding body.
- When a parent agreement is amended, the registry notifies all ETHOS that hold linked entries (child agreements that reference the parent).
- Cross-ecosystem agreement amendments follow inter-unit coordination (Layer V, deferred). Both ecosystems must consent through their own processes.
