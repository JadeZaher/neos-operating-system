---
name: skill-name-here
description: "Pushy description that errs toward triggering this skill -- describe the governance function it performs."
layer: 0
version: 0.1.0
depends_on: []
---

# skill-name-here

## A. Structural Problem It Solves

Describe the governance failure mode this skill prevents.
What happens when this function is handled informally or not at all?
How does this skill ensure structural clarity, traceability, and legitimacy?

## B. Domain Scope

Define where this skill applies -- which domains, agreement types, participant roles.
State the boundaries: what is inside scope and what is explicitly outside scope.
Reference the agreement hierarchy if relevant to scope determination.

## C. Trigger Conditions

List the specific conditions that activate this skill.
Include both routine triggers (scheduled events) and exceptional triggers (threshold events, participant requests).
Reference the provisional emergency expediting rules if emergency triggers apply.

## D. Required Inputs

Enumerate all inputs the skill needs to operate.
For each input, state who provides it and what format it takes.
Distinguish between mandatory inputs and optional/configurable inputs.

## E. Step-by-Step Process

Walk through the complete process from trigger to output.
Number each step. State who acts, what they do, and what conditions gate the next step.
Reference other skills by name where handoffs occur (e.g., "enters Advice phase per act-advice-phase skill").
Include routing logic for decisions that depend on scope or type.
State the timeline for each step (default and emergency).

## F. Output Artifact

Describe the document or record this skill produces.
Reference the asset template in the assets/ directory.
State what fields the artifact must contain and who can access it.

## G. Authority Boundary Check

State who has authority to perform each step and the limits of that authority.
Define what no one is authorized to do unilaterally.
Map authority levels: circle-internal, cross-circle, ecosystem-level, OSC consensus.
Reference the provisional authority model (pending Layer II formalization).

## H. Capture Resistance Check

Address each capture vector:
Capital capture -- how does the skill prevent financial leverage from distorting outcomes?
Charismatic capture -- how does the skill protect against personality-driven override of process?
Emergency capture -- how does the skill prevent crisis framing from bypassing structural safeguards?
Informal capture -- how does the skill prevent unregistered or assumed agreements?

## I. Failure Containment Logic

Define what happens when each step fails.
State fallback procedures for: consent failure, quorum failure, process stalls, ambiguous outcomes.
Ensure failures are contained locally and do not cascade to other skills or domains.
Reference escalation paths where applicable.

## J. Expiry / Review Condition

State the default review interval for outputs of this skill.
Define what happens when a review date is missed (escalation, not auto-invalidation).
State whether outputs ever auto-expire and under what conditions.
All intervals are configurable but must have mandatory minimums.

## K. Exit Compatibility Check

Define what happens to this skill's outputs when a participant exits.
State which obligations cease, which transfer, and which survive exit.
Address the 30-day wind-down period for in-progress commitments.
State that participants retain rights to their original works.

## L. Cross-Unit Interoperability Impact

Define how this skill's outputs interact with other ETHOS.
State notification requirements for cross-unit effects.
Define how outputs are registered across multiple units.
Note the extensibility point for cross-ecosystem federation (Layer V, deferred).

## OmniOne Walkthrough

Write a full narrative walkthrough using OmniOne's specific roles and structure.
Name specific roles (TH member, AE member, OSC, GEV) and give characters names.
Show the complete flow from trigger through output.
Include at least one edge case or complication.
End with the output artifact produced.
Use "I agree to..." language where commitments are made.

## Stress-Test Results

### 1. Capital Influx

Write a full narrative paragraph (5+ sentences) describing how this skill handles a scenario where significant external capital creates pressure to distort governance outcomes.
Walk through the specific mechanisms in this skill that prevent capture.
Name the structural safeguards that activate.

### 2. Emergency Crisis

Write a full narrative paragraph describing how this skill operates under emergency conditions.
Reference the provisional emergency expediting rules.
Show that consent is maintained even at maximum timeline compression.

### 3. Leadership Charisma Capture

Write a full narrative paragraph describing how this skill prevents a charismatic leader from overriding structural process.
Show the specific consent-phase protections.
Address social pressure dynamics.

### 4. High Conflict / Polarization

Write a full narrative paragraph describing how this skill handles deeply polarized positions.
Reference the GAIA escalation levels.
Show how third solutions emerge through coaching.

### 5. Large-Scale Replication

Write a full narrative paragraph describing how this skill scales from 50 to 5,000 participants.
Address domain-scoped action and registry-based routing.
Show that not all participants engage with every instance.

### 6. External Legal Pressure

Write a full narrative paragraph describing how this skill handles external legal mandates.
Reference the UAF sovereignty principle.
Show the distinction between individual legal compliance and ecosystem-level agreements.

### 7. Sudden Exit of 30% of Participants

Write a full narrative paragraph describing how this skill handles mass departure.
Address quorum adaptation, orphaned outputs, and automatic review triggers.
Show that existing outputs remain valid until formally reviewed.
