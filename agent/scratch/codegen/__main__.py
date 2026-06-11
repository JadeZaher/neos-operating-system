"""SKILL.md -> Tool codegen pipeline.

Usage:
    # Parse a single skill
    python -m scratch.codegen parse path/to/SKILL.md

    # Generate tool file
    python -m scratch.codegen generate proposal-creation

    # Generate all tools from all discovered SKILL.md files
    python -m scratch.codegen generate-all --skill-root ../../neos-core

    # Run drift detection
    python -m scratch.codegen drift --skill-root ../../neos-core --tool-file path/to/governance_tools.py

    # Build manifest
    python -m scratch.codegen manifest --skill-root ../../neos-core
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

from .ir import SkillSpec
from .parser import parse_skill_file
from .generator import generate_tool_file
from .validators import (
    DriftReport,
    check_skill_drift,
    check_all_drift,
    format_drift_report,
    format_summary,
)
from .manifest import build_manifest, build_skill_index

# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------


def discover_skill_files(root: Path) -> list[Path]:
    """Find all SKILL.md files under a root directory."""
    return sorted(root.rglob("SKILL.md"))


# ---------------------------------------------------------------------------
# Existing tool extractor
# ---------------------------------------------------------------------------

def extract_tools_from_module(module_path: Path) -> dict[str, dict]:
    """Parse governance_tools.py to extract ToolDef entries as dicts.

    Uses Python's AST module to parse the file and extract ToolDef
    keyword arguments, handling nested braces, lists, and dicts that
    regex cannot correctly match.

    Strategy:
      1. Parse the file with ast.parse()
      2. Walk the AST to find `GOVERNANCE_TOOLS = [...]`
      3. For each `ToolDef(...)` Call node, extract keyword args
      4. Use ast.literal_eval for literal values (str, int, bool, dict, list)
    """
    content = module_path.read_text(encoding="utf-8")
    tools: dict[str, dict] = {}

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"  [WARN] AST parse error: {e}")
        return tools

    # Find the GOVERNANCE_TOOLS assignment (handles both plain Assign
    # and annotated AnnAssign forms).
    gov_list: list[ast.Call] | None = None
    for node in ast.walk(tree):
        target = None
        value = None
        if isinstance(node, ast.Assign) and node.targets:
            target = node.targets[0]
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        if target is not None and isinstance(target, ast.Name) and target.id == "GOVERNANCE_TOOLS":
            if isinstance(value, ast.List):
                gov_list = [
                    elt for elt in value.elts
                    if isinstance(elt, ast.Call)
                ]
            break

    if gov_list is None:
        print("  [WARN] Could not find GOVERNANCE_TOOLS list in AST.")
        return tools

    for call_node in gov_list:
        # Verify it's a ToolDef call
        if not (isinstance(call_node.func, ast.Name) and call_node.func.id == "ToolDef"):
            continue

        kwargs: dict[str, Any] = {}
        for kw in call_node.keywords:
            key = kw.arg if kw.arg else ""
            value = _ast_to_value(kw.value)
            kwargs[key] = value

        name = kwargs.get("name", "")
        if name:
            tools[name] = {
                "name": name,
                "description": kwargs.get("description", ""),
                "parameters": kwargs.get("parameters", {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }),
            }

    return tools


def _ast_to_value(node: ast.expr) -> Any:
    """Convert an AST expression node to a Python value.

    Handles: str, int, float, bool, None, list, dict, Name (handler refs).
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_ast_to_value(elt) for elt in node.elts]
    if isinstance(node, ast.Dict):
        result: dict[str, Any] = {}
        for k, v in zip(node.keys, node.values):
            key = _ast_to_value(k) if k else ""
            result[str(key)] = _ast_to_value(v)
        return result
    if isinstance(node, ast.Name):
        # Handler references like `handler=create_proposal` — return as str
        return node.id
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _ast_to_value(node.operand)
        return -inner if isinstance(inner, (int, float)) else inner
    # Fallback: try unparse + literal_eval for complex expressions
    try:
        source = ast.unparse(node)
        return ast.literal_eval(source)
    except Exception:
        return ast.unparse(node) if hasattr(ast, 'unparse') else str(node)


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"


def cmd_parse(path: str) -> int:
    """Parse a single SKILL.md and print IR as JSON."""
    spec = parse_skill_file(path)
    out = {
        "name": spec.name,
        "description": spec.description,
        "layer": spec.layer,
        "version": spec.version,
        "depends_on": spec.depends_on,
        "source_path": spec.source_path,
        "trigger_count": len(spec.trigger_conditions),
        "input_count": len(spec.inputs),
        "step_count": len(spec.steps),
        "inputs": [
            {"name": i.name, "type": i.type_hint, "required": i.required, "desc": i.description[:80]}
            for i in spec.inputs
        ],
        "steps": [
            {"num": s.number, "title": s.title, "timeline": s.timeline, "refs": s.references}
            for s in spec.steps
        ],
        "output_template": spec.outputs.template_ref,
        "constraints_count": len(spec.constraints.rules) + len(spec.constraints.unilateral_no_gos),
        "capture_vectors": [v.name for v in spec.capture_vectors],
        "failure_modes": [f.trigger[:60] for f in spec.failure_modes],
        "review_interval": spec.review_config.review_interval,
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_generate(skill_name: str, skill_root: str) -> int:
    """Generate a tool file for one skill."""
    root = Path(skill_root)
    found = None
    for path in discover_skill_files(root):
        spec = parse_skill_file(path)
        if spec.name == skill_name:
            found = spec
            break

    if found is None:
        print(f"{FAIL} Skill '{skill_name}' not found in {skill_root}")
        return 1

    code = generate_tool_file(found)
    out_dir = Path(__file__).parent / "generated"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{found.tool_name}.py"
    out_path.write_text(code, encoding="utf-8")
    print(f"{OK} Generated {out_path}")
    print(f"  Tool name: {found.tool_name}")
    print(f"  Schema class: {found.schema_class_name}")
    print(f"  Inputs: {len(found.inputs)} ({len(found.required_inputs)} required)")
    print(f"  Steps: {len(found.steps)}")
    return 0


def cmd_generate_all(skill_root: str) -> int:
    """Generate tools for all discovered SKILL.md files."""
    root = Path(skill_root)
    files = discover_skill_files(root)
    generated = 0
    errors = 0
    out_dir = Path(__file__).parent / "generated"
    out_dir.mkdir(exist_ok=True)

    for path in files:
        try:
            spec = parse_skill_file(path)
            code = generate_tool_file(spec)
            out_path = out_dir / f"{spec.tool_name}.py"
            out_path.write_text(code, encoding="utf-8")
            generated += 1
            print(f"  {OK} {spec.name} -> {out_path.name}")
        except Exception as e:
            errors += 1
            print(f"  {FAIL} {path}: {e}")

    print(f"\nGenerated: {generated} | Errors: {errors}")
    return 0 if errors == 0 else 1


def cmd_drift(skill_root: str, tool_file: str) -> int:
    """Run drift detection across all skills vs. existing tools."""
    root = Path(skill_root)
    tf_path = Path(tool_file)
    if not tf_path.exists():
        print(f"{FAIL} Tool file not found: {tool_file}")
        return 1

    # Parse all skills
    specs: list[SkillSpec] = []
    for path in discover_skill_files(root):
        try:
            specs.append(parse_skill_file(path))
        except Exception as e:
            print(f"  {WARN} Skipping {path}: {e}")

    # Extract existing tools
    existing_tools = extract_tools_from_module(tf_path)
    print(f"Existing tools found: {len(existing_tools)}")
    print(f"Skills discovered:     {len(specs)}")
    print()

    # Load aliases from manifest
    from .manifest import _KNOWN_ALIASES
    aliases = _KNOWN_ALIASES
    print(f"Aliases configured:    {len(aliases)}")
    print()

    # Run drift checks with aliases
    reports, orphans = check_all_drift(specs, existing_tools, aliases=aliases)

    # Print per-skill details for skills with drift
    drifted = [r for r in reports if not r.is_clean]
    print(f"Skills with drift: {len(drifted)}/{len(reports)}")
    print()
    for report in drifted:
        print(format_drift_report(report, verbose=True))
        print()

    # Print summary
    print(format_summary(reports, orphans))
    return 1 if drifted or orphans else 0


def cmd_manifest(skill_root: str) -> int:
    """Build the manifest TOML."""
    root = Path(skill_root)
    specs: list[SkillSpec] = []
    for path in discover_skill_files(root):
        try:
            specs.append(parse_skill_file(path))
        except Exception as e:
            print(f"  {WARN} Skipping {path}: {e}")

    generated_dir = Path(__file__).parent / "generated"
    from .manifest import _KNOWN_ALIASES
    toml_content = build_manifest(specs, generated_dir, aliases=_KNOWN_ALIASES)
    manifest_path = Path(__file__).parent / "manifest.toml"
    manifest_path.write_text(toml_content, encoding="utf-8")
    print(f"{OK} Manifest written to {manifest_path}")
    print(f"  Skills: {len(specs)}")
    print(f"  Aliases: {len(_KNOWN_ALIASES)}")
    return 0


def cmd_pilot() -> int:
    """Run the pilot on 3 target skills end-to-end."""
    neos_core = Path(__file__).parent.parent.parent.parent / "neos-core"
    skill_names = ["proposal-creation", "emergency-criteria-design", "voluntary-exit"]

    print("=" * 60)
    print("PILOT: SKILL.md -> Tool Codegen Pipeline")
    print("=" * 60)
    print(f"Skills: {skill_names}")
    print(f"Skills root: {neos_core}")
    print()

    specs: list[SkillSpec] = []

    # Phase 1: Parse
    print("PHASE 1: PARSE")
    print("-" * 40)
    for name in skill_names:
        for path in discover_skill_files(neos_core):
            try:
                spec = parse_skill_file(path)
                if spec.name == name:
                    specs.append(spec)
                    print(f"  {OK} {name}")
                    print(f"    Layer {spec.layer} | {len(spec.inputs)} inputs | {len(spec.steps)} steps")
                    print(f"    Dependencies: {spec.depends_on}")
                    break
            except Exception as e:
                pass
        else:
            print(f"  {FAIL} {name} not found")
    print()

    # Phase 2: Generate
    print("PHASE 2: GENERATE")
    print("-" * 40)
    out_dir = Path(__file__).parent / "generated"
    out_dir.mkdir(exist_ok=True)
    generated_files: list[Path] = []
    for spec in specs:
        code = generate_tool_file(spec)
        out_path = out_dir / f"{spec.tool_name}.py"
        out_path.write_text(code, encoding="utf-8")
        generated_files.append(out_path)
        lines = code.count("\n")
        print(f"  {OK} {spec.name} -> {out_path.name} ({lines} lines)")
        print(f"    Tool: {spec.tool_name}()")
        print(f"    Schema: {spec.schema_class_name}")
    print()

    # Phase 3: Validate (drift detection)
    print("PHASE 3: DRIFT DETECTION")
    print("-" * 40)
    tool_file = (
        Path(__file__).parent.parent.parent / "src" / "neos_agent" / "agent" / "governance_tools.py"
    )
    if tool_file.exists():
        from .manifest import _KNOWN_ALIASES
        existing_tools = extract_tools_from_module(tool_file)
        for spec in specs:
            target_tool = _KNOWN_ALIASES.get(spec.name, spec.tool_name)
            tool_def = existing_tools.get(target_tool)
            report = check_skill_drift(spec, tool_def)
            report.tool_name = target_tool
            print(format_drift_report(report, verbose=True))
            print()
    else:
        print(f"  {WARN} Tool file not found at expected path: {tool_file}")
        print("     Skipping drift detection -- no existing tools to compare against.")
        print()
        print("  SKILL.md cross-validation (IR completeness check):")
        for spec in specs:
            gaps: list[str] = []
            if not spec.inputs:
                gaps.append("no inputs parsed")
            if not spec.steps:
                gaps.append("no steps parsed")
            if not spec.trigger_conditions:
                gaps.append("no triggers parsed")
            if not spec.constraints.rules and not spec.constraints.unilateral_no_gos:
                gaps.append("no constraints parsed")
            if gaps:
                print(f"  {WARN} {spec.name}: {', '.join(gaps)}")
            else:
                print(f"  {OK} {spec.name}: full IR coverage")
    print()

    # Phase 4: Build manifest
    print("PHASE 4: MANIFEST")
    print("-" * 40)
    toml_content = build_manifest(specs, out_dir)
    manifest_path = Path(__file__).parent / "manifest.toml"
    manifest_path.write_text(toml_content, encoding="utf-8")
    print(f"  {OK} Manifest written to {manifest_path}")
    print(f"    {len(specs)} skills mapped")
    print()

    print("=" * 60)
    print("PILOT COMPLETE")
    print(f"  Parsed:     {len(specs)} skills")
    print(f"  Generated:  {len(generated_files)} tool files")
    print(f"  Manifest:   {manifest_path}")
    print(f"  Output dir: {out_dir}")
    print("=" * 60)
    return 0


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0

    cmd = args[0]

    if cmd == "parse" and len(args) >= 2:
        return cmd_parse(args[1])

    if cmd == "generate" and len(args) >= 2:
        skill_root = args[2] if len(args) >= 3 else str(
            Path(__file__).parent.parent.parent.parent / "neos-core"
        )
        return cmd_generate(args[1], skill_root)

    if cmd == "generate-all":
        skill_root = args[1] if len(args) >= 2 else str(
            Path(__file__).parent.parent.parent.parent / "neos-core"
        )
        return cmd_generate_all(skill_root)

    if cmd == "drift":
        skill_root = args[1] if len(args) >= 2 else str(
            Path(__file__).parent.parent.parent.parent / "neos-core"
        )
        tool_file = args[2] if len(args) >= 3 else str(
            Path(__file__).parent.parent.parent / "src" / "neos_agent" / "agent" / "governance_tools.py"
        )
        return cmd_drift(skill_root, tool_file)

    if cmd == "manifest":
        skill_root = args[1] if len(args) >= 2 else str(
            Path(__file__).parent.parent.parent.parent / "neos-core"
        )
        return cmd_manifest(skill_root)

    if cmd == "pilot":
        return cmd_pilot()

    print(f"Unknown command: {cmd}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
