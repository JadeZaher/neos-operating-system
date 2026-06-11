"""scratch/codegen — SKILL.md → Python Tool Codegen Pipeline.

Submodules:
    parser/     — Parse SKILL.md → SkillSpec IR
    ir/         — Dataclass definitions for SkillSpec
    generator/  — Emit Python tool defs + Pydantic schemas from IR
    validators/ — Drift detection between SKILL.md and hand-written tools
    manifest/   — YAML/TOML mapping skill_id → generated tool path
    generated/  — Output directory for generated tool files

Usage:
    python -m scratch.codegen pilot     # Run full pilot on 3 target skills
    python -m scratch.codegen parse <path>
    python -m scratch.codegen generate <skill_name>
    python -m scratch.codegen drift
    python -m scratch.codegen manifest
"""
