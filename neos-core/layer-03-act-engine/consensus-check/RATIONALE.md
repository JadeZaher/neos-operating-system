---
skill: consensus-check
type: rationale
---

# consensus-check — Rationale & Design Notes

## A. Structural Problem It Solves

Other skills reference "check for consent" or "verify consensus" without defining the mechanics. How exactly do you determine whether a group agrees? What happens when someone is absent? What counts as a quorum? What is the difference between "no one objects" and "everyone agrees"? This utility skill provides the reusable, precise procedure for both consent and consensus checks, ensuring that every skill that needs group agreement uses the same structural rules. It prevents the "we thought we agreed" ambiguity.

## B. Domain Scope

Any decision point in any skill that requires verification of group agreement. Called by: act-consent-phase (as its core mechanism), agreement-amendment (for UAF changes requiring OSC consensus), proposal-resolution (at GAIA Level 1 for in-circle consensus), and any future skill that needs a formal group agreement check. This is a utility skill — it does not stand alone as a governance process but is invoked by other skills.

## OmniOne Walkthrough

The OSC needs to check consensus on a proposed UAF amendment that would add a new commitment about digital privacy practices. The OSC has 6 members. Consensus mode applies (UAF amendment = highest bar).

The facilitator, Yara (an AE member trained in process facilitation, not an OSC member herself), schedules the consensus check. At the scheduled time, 5 of 6 OSC members are present. Member #6, Desta, is traveling and sends a message: "I support the amendment but can't attend." Under consensus mode rules, Desta's remote support is NOT sufficient — consensus requires presence (physical or virtual) and an actively stated position. The check cannot proceed. Yara reschedules for two days later when Desta can join via video call.

At the rescheduled meeting, all 6 OSC members are present (Desta via video). Yara reads the proposed amendment text and asks each member to state their position. Members 1-4 agree. Member 5, Kofi, disagrees: "The proposed language is too broad — it would prevent any data sharing between circles, which would break our collaborative resource tracking system. I need the language narrowed to specify external data sharing only." Desta, who previously expressed support, now agrees with Kofi's concern after hearing it articulated.

Consensus is not achieved (2 disagreements). The result is recorded: 4 agree, 2 disagree (with reasons). The invoking skill (agreement-amendment) receives the "not achieved" result. The amendment proposer now has clear feedback: narrow the privacy commitment to external data sharing. They revise the amendment text and request a new consensus check at the next OSC meeting.

At the next meeting, all 6 are present. The revised amendment specifies "external data sharing with non-ecosystem entities." All 6 agree. Consensus achieved. The record documents both the failed check and the successful one, creating a complete deliberation trail.

## Stress-Test Results

### 1. Capital Influx

A donor who funds a significant portion of OmniOne's infrastructure is present during a consent check on a resource allocation proposal. Their "consent" carries the same structural weight as any other participant's — the consensus-check skill does not weight positions by financial contribution. The weighting_model field in the consent record is set to "equal" by default. If a future layer introduces configurable weighting (e.g., Current-See integration from Layer IV), the extensibility point exists in the template but is not active in this version. The donor's financial position creates social pressure but not structural privilege.

### 2. Emergency Crisis

An emergency consent check runs under compressed timelines — the scheduling window is 24 hours instead of the normal week. The quorum requirements do not change: 2/3 for consent mode, 100% for consensus mode. If consensus mode is required (UAF amendment during crisis), ALL members must still be present. The emergency may justify video attendance where in-person was the norm, but it does not justify proxy, absence, or lowered thresholds. If a consensus check cannot be conducted under emergency conditions (members unreachable), the amendment cannot proceed — the existing agreement stands.

### 3. Leadership Charisma Capture

A charismatic leader serves as facilitator for a consent check on their own proposal. This is a process violation — the facilitator must not have a stake in the outcome. Any participant can challenge the facilitator's neutrality and request a replacement. If the leader is both proposer and facilitator, the check is invalid. The skill requires a neutral facilitator precisely to prevent the person with the most social influence from controlling the polling process. A captured facilitator might subtly pressure participants, skip hesitant members, or misrecord positions — all prevented by the requirement of individual polling with written records.

### 4. High Conflict / Polarization

A consent check on a polarizing proposal reveals 6 consents, 2 stand-asides, and 3 objections. The objections are substantive and grounded. Consent is not achieved. The record documents all positions clearly, giving the invoking skill (act-consent-phase) the specific information needed for integration rounds. The polarization is visible in the record — both factions' positions are documented with equal weight. The consensus-check skill does not resolve the polarization; it accurately measures and records it for the integration process to address.

### 5. Large-Scale Replication

At 5,000 members, consent checks happen dozens of times weekly across 80 circles. Each check follows the same structural rules regardless of circle size. A 5-person circle has a 2/3 quorum of 4. An 80-person cross-circle body has a 2/3 quorum of 54. The mechanics scale linearly — larger groups take longer to poll but the rules are identical. The record template handles any number of participants. Persistent quorum failures in larger groups signal that the affected-parties list may be too broad and should be refined.

### 6. External Legal Pressure

A government subpoenas consensus check records as part of an investigation into the ecosystem's governance. The records are factual documents — they show who participated and what positions they took. The skill does not change its mechanics in response to external observation. If participants are concerned about their positions being disclosed, they may still exercise their full rights (consent, stand-aside, objection) — the structural protections exist within the governance system regardless of external scrutiny. The facilitator informs participants of any known disclosure requirements before the check begins.

### 7. Sudden Exit of 30% of Participants

After a mass departure, several scheduled consensus checks lose participants. For consent mode: quorum is recalculated against the current participant list. If the remaining participants meet the 2/3 threshold, the check proceeds. For consensus mode: if any departing member was part of the deciding body (e.g., an OSC member), the body's composition must be reconstituted before consensus checks can proceed. The departure of an OSC member during a UAF amendment process halts the consensus check until the vacancy is filled through the ecosystem's succession mechanism. This prevents consensus from being achieved by attrition.
