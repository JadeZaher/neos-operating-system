# Codegen Pilot Progress Log

## 2026-06-10T08:15 — Phase 1: Fixes Applied
- **Skills processed**: 3 (proposal-creation, emergency-criteria-design, voluntary-exit)
- **Blockers**: None

### Fixes Applied
- [x] Gap #1: Type inference heuristics — `proposer_identity` was `uuid`, now `str` (added `_NON_ID_PATTERNS` and `_TYPE_PATTERNS`)
- [x] Gap #2: Optional input detection — now scans full section D for contextual phrases ("may be", "if needed", etc.)
- [x] Gap #3: Capture vector regex — now handles "Charismatic capture / proposal fatigue." with slashes in header
- [x] Gap #7: AST-based ToolDef extraction — replaced regex with `ast.parse()` walker; handles `AnnAssign` (type-annotated) assignments and nested braces
- [x] Added `[aliases]` table to manifest — 54 kebab→snake_case mappings matched to actual governance_tools.py names

## 2026-06-10T08:30 — Phase 2: Generation
- **Skills generated**: 13 total (3 pilot + 10 new)
- **Drift findings**: 
  - 54 skills checked, 0 clean, 54 drifted
  - 3 orphan tools (list_domains, list_ecosystems, search_proposals)
  - 888 total issues (1 error, 512 warnings)
  - AST extraction: 29 of 29 tools successfully parsed
- **Blockers**: None

### Generated Files
- agreement_creation.py: 7 inputs, 9 steps
- agreement_amendment.py: 6 inputs, 5 steps
- domain_mapping.py: 0 inputs (parser gap), 6 steps
- domain_review.py: 5 inputs, 6 steps
- role_assignment.py: 6 inputs, 8 steps
- role_sunset.py: 6 inputs, 6 steps
- act_consent_phase.py: 0 inputs (parser gap), 7 steps
- decision_record.py: 7 inputs, 9 steps
- escalation_triage.py: 5 inputs, 6 steps
- governance_health_audit.py: 8 inputs, 10 steps

### Key Findings from 13-Skill Drift
1. **proposal-creation → create_proposal**: 19% description overlap, 8 param mismatches, naming drift (proposer_identity vs proposer)
2. **emergency-criteria-design → declare_emergency**: 15% overlap, skills have 6 inputs vs tool has 3
3. **voluntary-exit → create_exit_record**: 12% overlap, skill uses `departing_member_identity` vs tool uses `member_name`
4. **repair-agreement → create_repair_agreement**: 4% overlap, serious parameter drift (7 inputs missing from tool)
5. **agreement-registry → search_agreements**: 30% overlap, 5 tool-only params not in SKILL.md

## 2026-06-10T08:45 — Phase 3: PILOT_REPORT.md Updated
- Full 13-skill drift report embedded
- Coverage stats updated
- All files inventoried
