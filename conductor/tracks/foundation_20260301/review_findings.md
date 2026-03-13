# Review Findings: Foundation Track (foundation_20260301)

## Status: AMENDMENTS REQUIRED

The spec and plan are structurally sound but have critical gaps from source material.

## Critical Amendments (Must Fix Before Implementation)

### 1. Add "Source Concepts Deferred" section to spec
The following source concepts are NOT in this track and must be explicitly acknowledged:
- **Current-Sees** (influence currencies) — deferred to Layer IV
- **Inactive Member Protocol** (1-month rule) — deferred to Layer II
- **Removal Protocol** ("all but one by consensus") — deferred to Layer VI
- **IP Framework** (original/emergent/shared works) — partially in UAF, fully in Layer IV
- **Solutionary Culture methodology** — deferred to Layer VI, referenced in ACT
- **NEXUS onboarding process** — deferred to Layer II
- **Trunk Council transition** — OmniOne config, not NEOS core
- **Lawful Formation** alternative — flagged as open question
- **Agreement hierarchy** (Universal > Ecosystem > Access > Stewardship > ETHOS > Culture Code > Personal) — MUST be added to UAF skill, not deferred

### 2. Fix GAIA model discrepancies
- Acknowledge "Next Steps Process" (source position 3) — either incorporate or document exclusion rationale
- Add "Doing Both Solution" at Level 5 as an explicit resolution option
- Attribute Value Decision Model to "Futurist Playground"
- Define Wisdom Council composition as an open question
- Clarify relationship between Level 1 consensus and consent-as-default

### 3. Add source document references to plan tasks
Every content-creation task must reference which source files to load:
- `fieldagreementexample.md` for UAF tasks
- `EcoSystemPlanTempalte.md` for agreement structure
- Source docx content for council structures and process

### 4. Define provisional emergency expediting rules
Stress tests require emergency handling. Add minimum provisions:
- Reduced advice window (24h for emergency)
- Minimum quorum floor (cannot go below 50% even in emergency)
- Auto-revert after 30-day emergency window
- Layer VIII will formalize; these are provisional

### 5. Define agreement hierarchy in UAF skill
The fractalization order from source docs is load-bearing:
Universal > Ecosystem > Access > Stewardship > ETHOS > Culture Code > Personal

## Additional Open Questions to Add

- OQ-5: Agreement hierarchy conflict resolution
- OQ-6: Current-See integration with ACT (extensibility points)
- OQ-7: Emergency expediting authority
- OQ-8: Inactive member threshold (1 month per source docs)
- OQ-9: Agreement language standard ("I agree to..." format)
- OQ-10: Synergy check scope and mechanism
- OQ-11: Wisdom Council composition
- OQ-12: "Lawful Formation" alternative decision path
- OQ-13: "Preference Decisions" vs "Solution Decisions" distinction

## Inconsistencies Found

1. GAIA level numbering doesn't match source (missing Next Steps Process)
2. Field agreement example references "Moneyless Society" — predecessor org, plan should flag
3. "ETHOS" used in source but not defined in terminology — needs ETHOS-to-AZPO mapping
4. Plan Verification 3 says "5 completed skills" but lists 6
5. `scripts/` dir in tech-stack but not in spec file structure

## Structural Weaknesses

1. No onboarding consent ceremony defined (chicken-and-egg with UAF)
2. No agreement conflict detection in registry
3. 500-line limit may be unachievable with full narrative stress tests — recommend overflow to references/
4. Quorum adaptation after mass exit undefined
5. Domain concept used everywhere but never formally defined (Layer II dependency)
6. Each skill independently defines authority model — risk of inconsistency

## Recommendations

1. Add a shared "Provisional Authority Assumptions" section to spec that all 11 skills reference
2. Consider adding agreement-conflict-resolution as a 12th skill or substantial subsection of agreement-registry
3. Formalize synergy check as a canonical subsection within proposal-creation
4. Allow stress-test overflow to `references/stress-tests.md` if 500-line limit is threatened
