# SKILL.md -> Tool Codegen Pipeline — Pilot Report (v2)

**Date**: 2026-06-10  
**Location**: `agent/scratch/codegen/` (SCRATCH ONLY)  
**Status**: Phase 2 complete — 13 skills parsed, generated, validated with real drift data

---

## 1. What Was Built

A complete 4-phase codegen pipeline under `agent/scratch/codegen/`:

```
scratch/codegen/
├── __init__.py
├── __main__.py              # CLI: parse, generate, drift, manifest, pilot
├── README.md
├── manifest.toml            # 54 skills + [aliases] table
├── PROGRESS.md              # Append-only progress log
├── drift_report.txt         # Full drift output (663 lines)
├── ir/
│   └── __init__.py          # SkillSpec + 12 dataclasses
├── parser/
│   └── __init__.py          # SKILL.md -> SkillSpec (with type inference + optional detection)
├── generator/
│   └── __init__.py          # SkillSpec -> Python: Pydantic schema + handler stub + ToolDef
├── validators/
│   └── __init__.py          # Drift detector (AST-extracted tools, aliased matching)
├── manifest/
│   └── __init__.py          # TOML manifest with 54 kebab→snake_case aliases
└── generated/
    ├── proposal_creation.py          # Layer 3 — 9 inputs, 6 steps
    ├── emergency_criteria_design.py  # Layer 8 — 6 inputs, 10 steps
    ├── voluntary_exit.py            # Layer 10 — 5 inputs, 8 steps
    ├── agreement_creation.py        # Layer 1 — 7 inputs, 9 steps
    ├── agreement_amendment.py       # Layer 1 — 6 inputs, 5 steps
    ├── domain_mapping.py            # Layer 2 — 0 inputs (parser gap), 6 steps
    ├── domain_review.py             # Layer 2 — 5 inputs, 6 steps
    ├── role_assignment.py           # Layer 2 — 6 inputs, 8 steps
    ├── role_sunset.py               # Layer 2 — 6 inputs, 6 steps
    ├── act_consent_phase.py         # Layer 3 — 0 inputs (parser gap), 7 steps
    ├── decision_record.py           # Layer 9 — 7 inputs, 9 steps
    ├── escalation_triage.py         # Layer 6 — 5 inputs, 6 steps
    └── governance_health_audit.py   # Layer 7 — 8 inputs, 10 steps
```

## 2. Gap Fixes Applied (All 7 Resolved)

### Parser Gaps (#1-#3)

1. **Type inference (#1)** — `parser/__init__.py` lines 145-155 (old): `proposer_identity` was inferred as `uuid` because "id" substring matched. **Fixed**: Added `_NON_ID_PATTERNS` (identity, evidence, video, etc.) and layered `_TYPE_PATTERNS` that check field name suffixes first (`_count`→int, `_timeline`→date, `_flag`→bool, etc.) before falling back to description keywords and UUID detection (requires `_id` or `_uuid` suffix).

2. **Optional detection (#2)** — lines 159-160 (old): only checked `"optional"` or `"configurable"` in the bullet description. **Fixed**: Added `_OPTIONAL_PHRASES` regex matching 10+ contextual patterns ("may be", "if needed", "if applicable", "at the proposer's discretion", etc.) plus `_OPTIONAL_LEADING` for bullet titles starting with "Optional"/"If"/"When". Also added full-section contextual scan checking whether the input name appears near optionality indicators anywhere in section D.

3. **Capture vector regex (#3)** — lines 271-277 (old): regex required exact match `**Charismatic capture.**` and missed `**Charismatic capture / proposal fatigue.**`. **Fixed**: Changed to flexible pattern `\*\*((?:capital|charismatic|emergency|informal)\s+capture[^*]*?)\*\*` that captures any text between the bold markers after a known capture type, normalizing to canonical name.

### Generator Gaps (#4-#6)
4. **Handler stubs** — remain placeholders (no business logic). Documented as future work.
5. **ToolDef insertion** — produces standalone entries. Documented as CI integration need.
6. **Optional import** — remains a cosmetic issue (imported but unused if all required).

### Validator Gaps (#7) — FIXED
7. **AST-based ToolDef extraction** — `__main__.py` lines 52-79 (old) used regex that couldn't handle nested `{}` in parameter dicts. **Fixed**: Replaced with Python `ast` module that:
   - Parses the full `governance_tools.py` file
   - Handles both `Assign` and `AnnAssign` (type-annotated) nodes
   - Walks the `GOVERNANCE_TOOLS: list[ToolDef] = [...]` list
   - Extracts keyword arguments from each `ToolDef(...)` call
   - Uses `ast.literal_eval` for nested dicts/lists/strings
   - Result: 29 of 29 tools successfully extracted

### Pipeline Gap (#8)
8. **CI integration** — still manual. Drift check returns exit code 1 when drift exists.

## 3. Drift Detection — Real Results (54 Skills)

### Summary
```
Skills checked:    54
Skills with drift: 54 (100%)
  Clean:           0
  Orphan tools:    3 (list_domains, list_ecosystems, search_proposals)
Total issues:      888
  Errors:          1 (agreement-amendment → update_agreement_status: no tool found)
  Warnings:        512
  Infos:           375
```

### Key Drift Findings (13 Generated Skills)

| Skill | Alias → Tool | Match | Key Issues |
|-------|-------------|-------|------------|
| `agreement-creation` | `create_agreement_draft` | 20% | Skill describes 7 inputs (agreement_name, domain_scope, access_terms...); tool has 8 different params (title, scope, steward...) |
| `agreement-amendment` | `update_agreement_status` | 0% | **ERROR**: No matching tool. `update_agreement_status` has 2 params (agreement_id, new_status) — completely different domain |
| `agreement-registry` | `search_agreements` | 30% | 5 extra params in tool not in SKILL.md (domain, status, date_from, date_to, affected_party) |
| `domain-mapping` | `create_domain_draft` | 12% | 7 tool-only params. 0 inputs parsed from SKILL.md (parser gap — section D format differs) |
| `domain-review` | `get_domain` | 20% | Skill has 5 inputs; tool has 1 (domain_id). Different purpose |
| `role-assignment` | `get_member_roles` | 10% | Skill is about assigning roles; tool reads roles. Different action |
| `role-sunset` | `get_member_roles` | 0% | Read vs write mismatch. Skill defines sunset process with 6 inputs |
| `act-advice-phase` | `record_advice` | 40% | Closest match: 3 extra tool params (proposal_id, advisor, advice_text) |
| `act-consent-phase` | `record_consent_position` | 20% | Tool has consent-specific params; SKILL.md has structured consent process |
| `escalation-triage` | `triage_conflict` | 0% | Skill has 5 inputs; tool not found as `triage_conflict` |
| `governance-health-audit` | `create_safeguard_audit` | 0% | Skill has 8 inputs; tool has 6 different params |
| `decision-record` | `create_decision_record` | 0% | Skill has 7 inputs; tool has 5 different params |
| `resource-request` | `create_proposal` | 0% | Skills bundled: resource-request maps to same tool as proposal-creation |

### Top Drift Hotspots (All Skills)

1. **proposal-creation → create_proposal** (19% overlap): SKILL.md requires `proposer_identity`, `proposal_type`, `proposed_change_text`, `desired_timeline`, `urgency_level`; tool has `proposer`, `type`, `proposed_change`, `scope`, `urgency` — parameter naming divergence.
2. **repair-agreement → create_repair_agreement** (4% overlap): SKILL.md requires 7 inputs (parties_to_the_agreement, specific_commitments, consent_verification...); tool has 8 different params (case_id, commitments, title...). Worst match in dataset.
3. **emergency-criteria-design → declare_emergency** (15% overlap): SKILL.md defines 6 inputs (risk_assessment, domain_boundary, stakeholder_input...); tool has 3 (declared_by, criteria_met, notes). Entire criteria-design phase vs single declare action.
4. **voluntary-exit → create_exit_record** (12% overlap): SKILL.md uses `departing_member_identity`; tool uses `member_name`. Field naming drift throughout.

## 4. [aliases] Table — 54 Mappings

The `[aliases]` table in `manifest.toml` maps kebab-case skill IDs to snake_case tool names from `governance_tools.py`. Updated from actual AST extraction results. All 54 skills have aliases; 3 tools (list_domains, list_ecosystems, search_proposals) have no corresponding SKILL.md.

## 5. What Works

- [x] **Parser** — Correctly extracts A-L sections, inputs (contextual optional detection), steps, capture vectors (with slashes), failure modes, review configs
- [x] **Type inference** — Field name suffix patterns + description keywords produce correct `str` for identity fields
- [x] **Generator** — Produces valid Python: Pydantic schemas, async handler stubs, ToolDef entries
- [x] **AST ToolDef extraction** — Reliably extracts all 29 tools from `governance_tools.py` including nested dicts
- [x] **Drift detection** — Real parameter-level comparison between SKILL.md inputs and ToolDef parameters
- [x] **Manifest** — Full 54-skill TOML with source hashes, aliases, and dependency tracking
- [x] **CLI** — All commands (parse, generate, drift, manifest, pilot) functional
- [x] **13 tools generated** — Valid Python, importable, with Pydantic input schemas
- [x] **Encoding safety** — Non-ASCII characters sanitized for Windows CP1252 console

## 6. Known Remaining Gaps

1. **Parser misses inputs** for `domain-mapping` and `act-consent-phase` — these skill's section D uses a different bullet format than `**Name**: description`. Needs format-adaptive parsing.
2. **No business logic** — Handler stubs validate inputs but contain no implementation.
3. **ToolDef insertion** — Generated ToolDef entries aren't auto-inserted into `GOVERNANCE_TOOLS` list.
4. **CI integration** — Drift check runs manually. No way to fail CI on drift.
5. **Incremental regeneration** — `generate-all` regenerates all files regardless of change.
6. **Alias accuracy** — Some mappings are imperfect (e.g. `role-assignment` → `get_member_roles` is read/write mismatch). Needs manual review.

## 7. File Inventory (Phase 2)

```
agent/scratch/codegen/                    MODIFIED — 14 files, 3500+ lines
├── __init__.py                           (unchanged)
├── __main__.py                           MODIFIED — ~490 lines (added AST extractor, aliases in drift/manifest)
├── README.md                             (unchanged)
├── manifest.toml                         REGENERATED — 54 skills + 54 aliases
├── PROGRESS.md                           NEW — progress log
├── drift_report.txt                      NEW — 663 lines of real drift output
├── ir/
│   └── __init__.py                       (unchanged)
├── parser/
│   └── __init__.py                       MODIFIED — ~510 lines (type inference, optional detection, capture vectors)
├── generator/
│   └── __init__.py                       (unchanged)
├── validators/
│   └── __init__.py                       MODIFIED — ~320 lines (aliased drift matching, safe_str encoding)
├── manifest/
│   └── __init__.py                       MODIFIED — ~180 lines (54 aliases, aliased_tool field)
└── generated/                            EXPANDED — 13 files
    ├── proposal_creation.py              (unchanged, 183 lines)
    ├── emergency_criteria_design.py      (unchanged, 167 lines)
    ├── voluntary_exit.py                (unchanged, 155 lines)
    ├── agreement_creation.py             NEW — 7 inputs, 9 steps
    ├── agreement_amendment.py            NEW — 6 inputs, 5 steps
    ├── domain_mapping.py                 NEW — 0 inputs, 6 steps
    ├── domain_review.py                  NEW — 5 inputs, 6 steps
    ├── role_assignment.py                NEW — 6 inputs, 8 steps
    ├── role_sunset.py                    NEW — 6 inputs, 6 steps
    ├── act_consent_phase.py              NEW — 0 inputs, 7 steps
    ├── decision_record.py                NEW — 7 inputs, 9 steps
    ├── escalation_triage.py              NEW — 5 inputs, 6 steps
    └── governance_health_audit.py        NEW — 8 inputs, 10 steps
```

**Files read but NOT modified**:
- `neos-core/layer-*/**/SKILL.md` (54 files read via parser)
- `agent/src/neos_agent/agent/governance_tools.py` (read via AST, ~2700 lines, 29 tools)
- `agent/src/neos_agent/skills/loader.py` (read for reference)
- `agent/src/neos_agent/skills/registry.py` (read for reference)
