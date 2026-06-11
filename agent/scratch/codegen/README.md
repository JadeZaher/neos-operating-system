# SKILL.md -> Tool Codegen Pipeline

> Location: `agent/scratch/codegen/` — SCRATCH ONLY. No production modifications.

## Overview

This pipeline converts NEOS governance SKILL.md files into Python tool functions
with Pydantic input schemas, closing the architectural gap between the 54 skill
documents and the 29 hand-written tools in `governance_tools.py`.

## Architecture

```
SKILL.md ──> parser/ ──> SkillSpec IR ──> generator/ ──> *.py (tool + schema)
                  │                                        │
                  └────────> validators/ <──────────────────┘
                               │
                               ▼
                          Drift Report
```

### Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `ir/` | `ir/__init__.py` | Dataclasses: `SkillSpec`, `InputSpec`, `StepSpec`, `OutputSpec`, `ConstraintSpec`, etc. |
| `parser/` | `parser/__init__.py` | Parses SKILL.md frontmatter + sections C-L into `SkillSpec` IR |
| `generator/` | `generator/__init__.py` | Emits Python tool def + Pydantic schema + handler stub + ToolDef entry |
| `validators/` | `validators/__init__.py` | Drift detection: compares `SkillSpec` IR against existing `ToolDef` entries |
| `manifest/` | `manifest/__init__.py` | Builds TOML manifest mapping skill_id -> generated tool path with hashes |
| `generated/` | `generated/` | Output directory for generated `.py` files |
| `__main__.py` | `__main__.py` | CLI driver: `parse`, `generate`, `drift`, `manifest`, `pilot` |

## IR Shape

The canonical intermediate representation is `SkillSpec` (see `ir/__init__.py`):

```python
@dataclass
class SkillSpec:
    # Frontmatter
    name: str               # e.g. "proposal-creation"
    description: str        # from frontmatter description field
    layer: int              # 1-10
    version: str            # "0.1.0"
    depends_on: list[str]   # dependency skill names
    source_path: str        # absolute path to SKILL.md

    # Sections (C through L)
    trigger_conditions: list[str]           # Section C
    inputs: list[InputSpec]                 # Section D
    steps: list[StepSpec]                   # Section E
    outputs: OutputSpec                     # Section F
    constraints: ConstraintSpec             # Section G
    capture_vectors: list[CaptureVector]    # Section H
    failure_modes: list[FailureMode]        # Section I
    review_config: ReviewConfig             # Section J
    exit_rules: ExitRule                    # Section K
    interop_rules: InteropRule              # Section L

    # Computed
    tool_name -> str           # "proposal_creation"
    schema_class_name -> str   # "ProposalCreationInput"
    required_inputs -> list[InputSpec]
    optional_inputs -> list[InputSpec]
    as_generated_tool() -> dict  # ToolDef-compatible dict
```

## Quick Start

```bash
# Run the full pilot on 3 target skills
cd agent/
python -m scratch.codegen pilot

# Parse a single skill and inspect IR
python -m scratch.codegen parse ../../neos-core/layer-03-act-engine/proposal-creation/SKILL.md

# Generate one tool
python -m scratch.codegen generate proposal-creation

# Generate all 54 tools
python -m scratch.codegen generate-all

# Run drift detection (54 skills vs 29 tools)
python -m scratch.codegen drift

# Build manifest
python -m scratch.codegen manifest
```

## Generated Output

Each generated tool file (e.g., `generated/proposal_creation.py`) contains:

1. **Pydantic Input Schema** — `ProposalCreationInput(BaseModel)` with all inputs from Section D
2. **Async Handler Stub** — `async def proposal_creation(args, db, ecosystem_ids)` with:
   - Required-field validation
   - Ecosystem ID resolution
   - TODO block listing all steps from Section E
   - Placeholder return with skill metadata
3. **ToolDef Entry** — Ready to insert into `GOVERNANCE_TOOLS` list
4. **Helper function** — `get_proposal_creation_tooldef()`

## Drift Detection

The validator compares each `SkillSpec` (from SKILL.md) against any existing
`ToolDef` (from `governance_tools.py`) and reports:

| Category | Severity | What it catches |
|----------|----------|-----------------|
| `missing_tool` | ERROR | SKILL.md exists but no corresponding tool function |
| `orphan_tool` | INFO | Tool function exists but no SKILL.md |
| `param_mismatch` | WARNING | Section D input not in tool params, or vice versa |
| `field_mismatch` | WARNING | Required/optional mismatch between spec and tool |
| `missing_schema` | INFO | Tool has no Pydantic schema for its inputs |

### Pilot Drift Findings

For the 3 pilot skills, the drift detector correctly identifies:

- **proposal-creation**: No direct tool mapping. Existing code uses `create_proposal` (tool #7)
  which has different parameter structure and combined responsibilities.
- **emergency-criteria-design**: No direct tool mapping. Existing code has
  `declare_emergency` (tool #18) which is a different skill.
- **voluntary-exit**: No direct tool mapping. Existing code has
  `create_exit_record` (tool #19) which overlaps but has different naming.

This confirms the architectural gap: **29 tools loosely mirror 54 skills with
no automated link between them.**

## Incremental Rollout Plan

### Phase 1 (Current — Pilot)
- [x] IR dataclasses for all SKILL.md sections
- [x] Parser producing full SkillSpec from markdown
- [x] Generator emitting Pydantic schemas + handler stubs
- [x] Drift detector with severity levels
- [x] Manifest builder with source hashes
- [x] Pilot on 3 skills (proposal-creation, emergency-criteria-design, voluntary-exit)

### Phase 2 (Next)
- [ ] Align naming: map existing tools to SKILL.md names via `manifest.toml` aliases
- [ ] Generate Pydantic schemas for all 54 skills
- [ ] Add CI check: `python -m scratch.codegen drift --ci` fails on ERROR-level drift
- [ ] Improve parser: detect "optional" inputs from context, parse timeline values

### Phase 3 (Production)
- [ ] Replace hand-written parameter blocks with generated Pydantic schemas
- [ ] Add `@generated_from(skill="proposal-creation", hash="abc123")` decorator
- [ ] Auto-update tools when SKILL.md changes (git hook or CI)
- [ ] Full 1:1 coverage: 54 skills -> 54 generated tools

### Phase 4 (Autonomous)
- [ ] LLM-assisted handler implementation from StepSpec descriptions
- [ ] Roundtrip: code change -> SKILL.md update
- [ ] Runtime validation: tool calls checked against current SkillSpec at startup

## Dependencies

- Python 3.11+ (uses `from __future__ import annotations`, `str | None` syntax)
- `pydantic` (for generated schemas; already in NEOS agent dependencies)
- No additional packages needed for the scratch pipeline

## Constraints

- **SCRATCH ONLY**: All code lives under `agent/scratch/codegen/`. Nothing modifies
  production paths (`agent/src/neos_agent/`).
- The parser reuses patterns from `neos_agent.skills.loader` but is standalone.
- Generated code uses `try/except ImportError` for production deps, so it works
  in isolation for scratch testing.
